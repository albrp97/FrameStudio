#!/usr/bin/env python3
"""Measure cache-disabled exact seeks, including different physical inputs.

Run from the repository root with ``python -m benchmarks.seek_performance``.
The harness owns the exclusive lock; do not wrap it in another flock.
The existing high-detail fixtures must already exist in --fixtures.
Candidates are experiments, not automatically selected production settings.
CUDA is opt-in with --candidates cuda and requires a functioning NVIDIA setup.
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import math
import shutil
import subprocess
import threading
import time
from bisect import bisect_left
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path

from benchmarks.playback_performance import make_layout
from framestudio.composed_playback import FfmpegSynchronizedPlaybackBackend
from framestudio.ffmpeg_playback import VideoFrame
from framestudio.layout_plan import LayoutInterval, LayoutPlan
from framestudio.playback import PlaybackBackendError


class Candidate(str, Enum):
    CURRENT = "current"
    OUTPUT = "output-one"
    FILTER = "filter-two"
    INPUT = "input-eight"
    PROBE = "bounded-probe"
    SIMPLE = "single-slot"
    CUDA = "cuda"


DEFAULT_CANDIDATES = tuple(candidate for candidate in Candidate if candidate != Candidate.CUDA)


@dataclass(frozen=True)
class Options:
    fixtures: Path
    lock: Path
    output: Path
    repetitions: int = 3
    candidates: tuple[Candidate, ...] = DEFAULT_CANDIDATES


@dataclass(frozen=True)
class Distribution:
    p50: float
    p95: float
    pmax: float


@dataclass(frozen=True)
class Sample:
    target_seconds: float
    source_seconds: float
    reference_frame_source_pts: float
    source_path: str
    latency_ms: float
    reference_latency_ms: float
    pixel_sha256: str
    reference_sha256: str
    exact_reference_equal: bool
    command: list[str]


@dataclass(frozen=True)
class Receipt:
    requested_position_seconds: float
    actual_position_seconds: float
    decoded_position_seconds: float | None
    reference_frame_source_pts: float
    latency_ms: float
    synchronous_request_ms: float
    pixel_sha256: str
    exact_reference_equal: bool


@dataclass(frozen=True)
class Run:
    candidate: Candidate
    cold_samples: list[Sample]
    cold_latency_ms: dict[str, Distribution]
    latest_requests: list[Receipt]
    preview_stats: dict[str, int]


@dataclass(frozen=True)
class SourceTimeline:
    frame_pts: tuple[float, ...]
    keyframe_pts: tuple[float, ...]

    def frame_at(self, source_position: float) -> float:
        index = bisect_left(self.frame_pts, source_position)
        if index == len(self.frame_pts):
            raise ValueError("Requested position is beyond the fixture's final frame")
        return self.frame_pts[index]


def probe_timeline(source: Path) -> SourceTimeline:
    result = subprocess.run(
        [
            resolve_executable("ffprobe"),
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "frame=key_frame,best_effort_timestamp_time",
            "-of",
            "csv=p=0",
            str(source),
        ],
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
    )
    frames: list[float] = []
    keyframes: list[float] = []
    for line in result.stdout.splitlines():
        fields = line.split(",")
        if len(fields) >= 2 and fields[0] in ("0", "1"):
            position = float(fields[1])
            frames.append(position)
            if fields[0] == "1":
                keyframes.append(position)
    if not frames or not keyframes:
        raise ValueError("Fixture has no observable frame/keyframe timestamps")
    return SourceTimeline(tuple(frames), tuple(keyframes))


def distribution(values: list[float]) -> Distribution:
    ordered = sorted(values)
    if not ordered:
        raise ValueError("A latency distribution requires samples")
    return Distribution(
        ordered[math.ceil(len(ordered) * 0.50) - 1],
        ordered[math.ceil(len(ordered) * 0.95) - 1],
        ordered[-1],
    )


def resolve_executable(name: str) -> str:
    executable = shutil.which(name)
    if executable is None:
        raise RuntimeError(f"Required executable not found: {name}")
    return executable


def candidate_command(command: list[str], candidate: Candidate) -> list[str]:
    result = command[:]
    if candidate == Candidate.OUTPUT:
        result[-1:-1] = ["-threads:v", "1"]
    elif candidate == Candidate.FILTER:
        result[1:1] = ["-filter_complex_threads", "2"]
    elif candidate in (Candidate.INPUT, Candidate.PROBE, Candidate.CUDA):
        options = {
            Candidate.INPUT: ["-threads", "8"],
            Candidate.PROBE: ["-analyzeduration", "1", "-probesize", "32768", "-fpsprobesize", "0"],
            Candidate.CUDA: ["-hwaccel", "cuda"],
        }[candidate]
        for index in reversed([i for i, value in enumerate(result) if value == "-i"]):
            result[index:index] = options
    return result


class ExperimentBackend(FfmpegSynchronizedPlaybackBackend):
    def __init__(
        self,
        sources: tuple[tuple[str, Path], ...],
        layout: LayoutPlan,
        executable: str,
        candidate: Candidate = Candidate.CURRENT,
    ) -> None:
        self.candidate = candidate
        self.received: list[VideoFrame] = []
        self.errors: list[str] = []
        self.frame_ready = threading.Condition()
        super().__init__(
            sources,
            layout,
            layout.canvas.width,
            layout.canvas.height,
            30.0,
            self._receive,
            self._error,
            lambda: None,
            ffmpeg_path=executable,
            preview_cache_size=0,
        )

    def _receive(self, frame: VideoFrame) -> None:
        with self.frame_ready:
            self.received.append(frame)
            self.frame_ready.notify_all()

    def _error(self, message: str) -> None:
        with self.frame_ready:
            self.errors.append(message)
            self.frame_ready.notify_all()

    def _frame_command(self, position_seconds: float, interval: LayoutInterval) -> list[str]:
        command = super()._frame_command(position_seconds, interval)
        if self.candidate == Candidate.SIMPLE:
            command = self._single_slot_command(command, interval)
        return candidate_command(command, self.candidate)

    def _single_slot_command(self, command: list[str], interval: LayoutInterval) -> list[str]:
        if len(interval.slots) != 1:
            return command
        slot = interval.slots[0]
        crop = slot.crop
        if slot.triplicate_crops or crop is None or slot.slot != self._layout.canvas:
            return command
        # The overlay negotiates yuv420p even for a full opaque slot. Retain
        # that conversion: omitting it changes pixels, not just graph cost.
        graph = (
            "[0:v:0]trim=start=0:duration=0.05,setpts=PTS-STARTPTS[source_0];"
            + self._crop_filter("[source_0]", crop, "[slot_0]")
            + ";[slot_0]format=yuv420p,format=rgba[output]"
        )
        result = command[:]
        result[result.index("-filter_complex") + 1] = graph
        return result

    def wait_for_position(self, target: float, timeout: float = 20.0) -> VideoFrame:
        with self.frame_ready:
            ready = self.frame_ready.wait_for(
                lambda: bool(self.errors)
                or any(frame.position_seconds == target for frame in self.received),
                timeout,
            )
            if self.errors:
                raise PlaybackBackendError("; ".join(self.errors))
            if not ready:
                raise TimeoutError(f"No preview at {target}")
            return next(
                frame for frame in reversed(self.received) if frame.position_seconds == target
            )

    def command_at(self, target: float) -> tuple[list[str], Path, float]:
        interval = self._interval_at(target)
        if interval is None or interval.is_black:
            raise ValueError("A measured cold seek must address physical media")
        block = interval.slots[0].block
        source_path = dict(self._source_items)[block.source_id]
        source_position = block.source_range.source_tick_at(round(target * 1_000_000)) / 1_000_000
        return self._frame_command(target, interval), source_path, source_position


def exact_output(command: list[str], frame_size: int) -> tuple[bytes, float]:
    started = time.perf_counter()
    result = subprocess.run(command, capture_output=True, check=True, timeout=20)
    latency = (time.perf_counter() - started) * 1000
    if len(result.stdout) != frame_size:
        raise AssertionError(f"Expected {frame_size} bytes, received {len(result.stdout)}")
    return result.stdout, latency


def measure_cold(
    backend: ExperimentBackend,
    reference: ExperimentBackend,
    targets: tuple[float, ...],
    references: dict[float, str],
    repetitions: int,
    timelines: dict[Path, SourceTimeline],
) -> list[Sample]:
    samples: list[Sample] = []
    for _repetition in range(repetitions):
        for target in targets:
            command, source, source_position = backend.command_at(target)
            # Interleave the reference and candidate rather than relying on a
            # historical timing. Both are cold decoder/frame-cache requests.
            reference_command, _, _ = reference.command_at(target)
            reference_output, reference_ms = exact_output(reference_command, reference.frame_size)
            reference_hash = hashlib.sha256(reference_output).hexdigest()
            references[target] = reference_hash
            if backend.candidate == Candidate.CURRENT:
                output, elapsed = reference_output, reference_ms
            else:
                output, elapsed = exact_output(command, backend.frame_size)
            pixel_hash = hashlib.sha256(output).hexdigest()
            samples.append(
                Sample(
                    target,
                    source_position,
                    timelines[source].frame_at(source_position),
                    str(source),
                    elapsed,
                    reference_ms,
                    pixel_hash,
                    reference_hash,
                    pixel_hash == reference_hash,
                    command,
                )
            )
    return samples


def measure_requests(
    backend: ExperimentBackend,
    references: dict[float, str],
    timelines: dict[Path, SourceTimeline],
) -> list[Receipt]:
    receipts: list[Receipt] = []
    for target in (0.033, 2.033, 1.733, 3.733):
        with backend.frame_ready:
            backend.received.clear()
        # A burst alternates physical paths and ends at the measured target.
        # There is no debounce/sleep hiding synchronous request blocking.
        started = time.perf_counter()
        blocking: list[float] = []
        for position in (1.2, 3.2, 0.4, 2.4, 1.6, 3.6, target):
            before = time.perf_counter()
            backend.request_preview(position)
            blocking.append((time.perf_counter() - before) * 1000)
        latest_requested_at = before
        frame = backend.wait_for_position(target)
        elapsed = (time.perf_counter() - latest_requested_at) * 1000
        if time.perf_counter() - started > 20:
            raise TimeoutError("Scrub burst exceeded its bound")
        _command, source_path, source_position = backend.command_at(target)
        receipts.append(
            Receipt(
                target,
                frame.position_seconds,
                frame.decoded_position_seconds,
                timelines[source_path].frame_at(source_position),
                elapsed,
                max(blocking),
                hashlib.sha256(frame.data).hexdigest(),
                hashlib.sha256(frame.data).hexdigest() == references[target],
            )
        )
    return receipts


def benchmark(options: Options) -> dict[str, object]:
    paths = tuple(
        options.fixtures / f"high-detail-{width}x{height}.mp4"
        for width, height in ((1920, 1080), (3840, 2160))
    )
    for path in paths:
        if not path.is_file():
            raise FileNotFoundError(path)
    before = {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
    timelines = {path: probe_timeline(path) for path in paths}
    sources, layout = make_layout(paths[0], 1920, 1080, alternate_source=(paths[1], 3840, 2160))
    executable = resolve_executable("ffmpeg")
    targets = (0.033, 2.033, 1.733, 3.733, 1.999, 2.0, 4.033, 6.033)
    references: dict[float, str] = {}
    runs: list[Run] = []
    reference = ExperimentBackend(sources, layout, executable)
    try:
        for candidate in options.candidates:
            backend = ExperimentBackend(sources, layout, executable, candidate)
            try:
                samples = measure_cold(
                    backend, reference, targets, references, options.repetitions, timelines
                )
                requests = measure_requests(backend, references, timelines)
                runs.append(
                    Run(
                        candidate,
                        samples,
                        {
                            path.name: distribution(
                                [
                                    sample.latency_ms
                                    for sample in samples
                                    if sample.source_path == str(path)
                                ]
                            )
                            for path in paths
                        },
                        requests,
                        backend.preview_stats(),
                    )
                )
            finally:
                backend.close()
    finally:
        reference.close()
    after = {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
    if before != after:
        raise AssertionError("Source bytes changed")
    return {
        "baseline": "current starting file snapshot, not Git HEAD",
        "ffmpeg": executable,
        "cache_entries": 0,
        "canvas": [1920, 1080],
        "synthetic_sources": len(sources),
        "synthetic_duration_seconds": layout.final_duration_seconds,
        "source_sha256_before": before,
        "source_sha256_after": after,
        "source_timestamps": {str(path): asdict(timeline) for path, timeline in timelines.items()},
        "runs": [asdict(run) for run in runs],
        "limitations": [
            "Decoder and frame caches are cold; OS file cache is not purged.",
            "Only two physical fixtures; 200-source/40h scale is synthetic metadata.",
            "Pixels are compared with unmodified exact FFmpeg commands, not approximate keyframes.",
            "Backend delivery is measured, not GTK painting.",
            "decoded_position_seconds is backend metadata, not independently measured source PTS.",
            "Candidate mismatch is reported, never accepted as exact or deployed.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixtures", type=Path, required=True)
    parser.add_argument("--lock", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument(
        "--candidates",
        nargs="+",
        choices=[candidate.value for candidate in Candidate],
        default=[candidate.value for candidate in DEFAULT_CANDIDATES],
    )
    args = parser.parse_args()
    if args.repetitions < 1:
        parser.error("--repetitions must be positive")
    options = Options(
        args.fixtures,
        args.lock,
        args.output,
        args.repetitions,
        tuple(Candidate(candidate) for candidate in args.candidates),
    )
    options.lock.parent.mkdir(parents=True, exist_ok=True)
    options.output.parent.mkdir(parents=True, exist_ok=True)
    with options.lock.open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        report = benchmark(options)
        options.output.write_text(json.dumps(report, indent=2) + "\n")
    print(options.output)


if __name__ == "__main__":
    main()
