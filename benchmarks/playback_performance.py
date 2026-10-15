#!/usr/bin/env python3
"""Bounded real-decoder benchmarks; synthetic project size is not media duration.

Run from the repository root with ``python -m benchmarks.playback_performance``.
The caller supplies an exclusive-lock path so concurrent workers cannot distort
measurements. Fixtures and JSON are written only below the supplied directory.
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import math
import os
import platform
import shutil
import subprocess
import threading
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import TypedDict

from framestudio.composed_playback import FfmpegSynchronizedPlaybackBackend
from framestudio.composition import VisualTransform
from framestudio.ffmpeg_playback import FfmpegPlaybackBackend, VideoFrame
from framestudio.layout_plan import (
    FramingDomain,
    LayoutInterval,
    LayoutPlan,
    PixelRect,
    PlannedBlock,
    SlotPlan,
    SourceGeometry,
    SourceRangePlan,
    plan_crop,
)
from framestudio.playback import PlaybackBackendError


@dataclass(frozen=True)
class _FrameReceipt:
    width: int
    height: int
    position_seconds: float
    frame_bytes: int


class _PlaybackOptions(TypedDict):
    width: int
    height: int
    frame_rate: float
    on_frame: Callable[[VideoFrame], None]
    on_error: Callable[[str], None]
    on_end: Callable[[], None]
    preview_cache_size: int
    ffmpeg_path: str


class _SeekSample(TypedDict):
    repetition: int
    target: float
    position: float
    dimensions: list[int]
    frame_bytes: int
    latency_ms: float


class _PlaybackMetrics(TypedDict):
    window_seconds: float
    target_fps: int
    delivered_frames: int
    delivered_fps: float
    first_frame_ms: float | None
    gap_ms: dict[str, float | None]
    gaps_over_1p5_frame_periods: int
    estimated_undelivered_frames: int
    max_sample_age_ms: float
    frames: list[tuple[float, float]]
    transition_frames: list[tuple[float, float]]


class BenchmarkRun(TypedDict):
    synchronized: bool
    effective_commands: dict[str, list[str]]
    per_frame_reference: bool
    decoder_threads_override: int
    filter_threads_override: int
    output_size: list[int]
    samples: list[_SeekSample]
    seek_latency_ms: dict[str, float | None]
    playback: _PlaybackMetrics
    errors: list[str]
    preview_stats: dict[str, int]
    playback_stats: dict[str, int] | None
    source_sha256: str
    source_hashes: dict[str, str]
    mixed_source_size: list[int] | None
    source_preserved: bool


class _FixtureMetadata(TypedDict):
    generation_command: list[str]
    probe: object


class _FixtureRun(TypedDict):
    source_size: list[int]
    fixture: _FixtureMetadata
    runs: list[BenchmarkRun]


@dataclass(frozen=True)
class _CandidateSettings:
    decoder_threads: int
    filter_threads: int
    per_frame_reference: bool = False


def percentile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    return ordered[max(0, math.ceil(len(ordered) * fraction) - 1)]


def summarize(values: list[float]) -> dict[str, float | None]:
    return {"p50": percentile(values, 0.5), "p95": percentile(values, 0.95)}


def make_layout(
    source: Path,
    source_width: int,
    source_height: int,
    width: int = 1920,
    height: int = 1080,
    alternate_source: tuple[Path, int, int] | None = None,
) -> tuple[tuple[tuple[str, Path], ...], LayoutPlan]:
    """200 logical sources/40h metadata, but only first 6s are real-media samples."""
    canvas = PixelRect(0, 0, width, height)
    sources = tuple(
        (f"source-{index}", alternate_source[0] if alternate_source and index % 2 else source)
        for index in range(200)
    )
    blocks = []
    intervals = []
    start = 0
    for index, (source_id, _path) in enumerate(sources):
        # First three blocks are real 2s trims. Remaining lengths are metadata
        # load only: the encoded fixture is deliberately not claimed to be 40h.
        duration = 2_000_000 if index < 3 else 720_000_000
        if index == 199:
            duration = 144_000_000_000 - start
        geometry = SourceGeometry(
            source_id,
            alternate_source[1] if alternate_source and index % 2 else source_width,
            alternate_source[2] if alternate_source and index % 2 else source_height,
        )
        block = PlannedBlock(
            f"segment-{index}",
            f"block-{index}",
            "track-1",
            0,
            source_id,
            geometry,
            SourceRangePlan(0, duration, start, start + duration),
            VisualTransform(),
            False,
        )
        blocks.append(block)
        intervals.append(
            LayoutInterval(
                start,
                start + duration,
                (block,),
                (SlotPlan(block, canvas, plan_crop(geometry, canvas)),),
            )
        )
        start += duration
    return sources, LayoutPlan(
        canvas,
        "absolute",
        FramingDomain.FINAL_SLOT,
        start,
        tuple([0] + [interval.end_tick for interval in intervals]),
        tuple(blocks),
        tuple(intervals),
    )


def _executable(name: str) -> str:
    executable = shutil.which(name)
    if executable is None:
        raise RuntimeError(f"{name} is required for the playback benchmark but was not found")
    return executable


def fixture(directory: Path, width: int, height: int) -> tuple[Path, _FixtureMetadata]:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"high-detail-{width}x{height}.mp4"
    command = [
        _executable("ffmpeg"),
        "-hide_banner",
        "-loglevel",
        "error",
        "-nostdin",
        "-f",
        "lavfi",
        "-i",
        f"testsrc2=size={width}x{height}:rate=30:duration=8",
        "-vf",
        "noise=alls=8:allf=t+u:all_seed=42",
        "-c:v",
        "libx264",
        "-preset",
        "fast",
        "-crf",
        "22",
        "-threads",
        "4",
        "-g",
        "120",
        "-keyint_min",
        "120",
        "-sc_threshold",
        "0",
        "-bf",
        "3",
        "-pix_fmt",
        "yuv420p",
        "-an",
        str(path),
    ]
    if not path.exists():
        subprocess.run(command, check=True, capture_output=True, timeout=180)
    metadata: object = json.loads(
        subprocess.check_output(
            [
                _executable("ffprobe"),
                "-v",
                "error",
                "-show_streams",
                "-show_format",
                "-of",
                "json",
                str(path),
            ]
        )
    )
    return path, {"generation_command": command, "probe": metadata}


def candidate_command(command: list[str], decoder_threads: int, filter_threads: int) -> list[str]:
    result = command[:]
    if decoder_threads:
        indexes = [index for index, item in enumerate(result) if item == "-i"]
        for index in reversed(indexes):
            result[index:index] = ["-threads", str(decoder_threads)]
    if filter_threads:
        result[1:1] = [
            "-filter_threads",
            str(filter_threads),
            "-filter_complex_threads",
            str(filter_threads),
        ]
    return result


class _CandidateSingleBackend(FfmpegPlaybackBackend):
    def __init__(
        self, source: Path, options: _PlaybackOptions, settings: _CandidateSettings
    ) -> None:
        self.settings = settings
        super().__init__(source, duration_seconds=8.0, **options)

    def _command(
        self, position_seconds: float, *, realtime: bool, frame_count: int | None = None
    ) -> list[str]:
        return candidate_command(
            super()._command(position_seconds, realtime=realtime, frame_count=frame_count),
            self.settings.decoder_threads,
            self.settings.filter_threads,
        )


class _CandidateSynchronizedBackend(FfmpegSynchronizedPlaybackBackend):
    def __init__(
        self,
        sources: Sequence[tuple[str, Path]],
        layout: LayoutPlan,
        options: _PlaybackOptions,
        settings: _CandidateSettings,
    ) -> None:
        self.settings = settings
        super().__init__(sources, layout, **options)

    def _frame_command(self, position_seconds: float, interval: LayoutInterval) -> list[str]:
        return candidate_command(
            super()._frame_command(position_seconds, interval),
            self.settings.decoder_threads,
            self.settings.filter_threads,
        )

    def _read_realtime_frame(
        self,
        position_seconds: float,
        interval: LayoutInterval,
        cancel_check: Callable[[], bool] | None,
    ) -> VideoFrame:
        if not self.settings.per_frame_reference:
            return super()._read_realtime_frame(position_seconds, interval, cancel_check)
        # Reproduce the pre-change decode-per-clock-sample path without
        # modifying methods on the production backend instance.
        output, detail = self._run_decode_command(
            self._frame_command(position_seconds, interval),
            cancel_check=cancel_check,
            process_attribute="_realtime_decode_process",
        )
        if len(output) != self.frame_size:
            raise PlaybackBackendError(
                detail.decode(errors="replace") or "Incomplete reference frame"
            )
        return VideoFrame(output, self.width, self.height, position_seconds, position_seconds)


def _effective_commands(
    backend: FfmpegPlaybackBackend, per_frame_reference: bool
) -> dict[str, list[str]]:
    if isinstance(backend, FfmpegSynchronizedPlaybackBackend):
        preview_interval = backend._interval_at(0.1)
        initial_interval = backend._interval_at(0.0)
        if preview_interval is None or initial_interval is None:
            raise ValueError("Benchmark layout must cover its initial preview samples")
        return {
            "preview": backend._frame_command(0.1, preview_interval),
            "continuous": (
                backend._frame_command(0.0, initial_interval)
                if per_frame_reference
                else backend._video_command(0.0, initial_interval, continuous=True)
            ),
        }
    return {
        "preview": backend._command(0.1, realtime=False, frame_count=1),
        "continuous": backend._command(0.0, realtime=True),
    }


def _playback_metrics(
    frames: list[tuple[float, _FrameReceipt]], started: float, synchronized: bool
) -> _PlaybackMetrics:
    playback_frames = [(at - started, frame.position_seconds) for at, frame in frames]
    gaps = [
        (right[0] - left[0]) * 1000
        for left, right in zip(playback_frames, playback_frames[1:], strict=False)
    ]
    return {
        "window_seconds": 4.5,
        "target_fps": 30,
        "delivered_frames": len(playback_frames),
        "delivered_fps": len(playback_frames) / 4.5,
        "first_frame_ms": playback_frames[0][0] * 1000 if playback_frames else None,
        "gap_ms": summarize(gaps),
        "gaps_over_1p5_frame_periods": sum(gap > 1000 / 30 * 1.5 for gap in gaps),
        "estimated_undelivered_frames": max(0, 135 - len(playback_frames)),
        "max_sample_age_ms": max(
            ((at - position) * 1000 for at, position in playback_frames),
            default=0,
        ),
        "frames": playback_frames,
        "transition_frames": [
            (at, position)
            for at, position in playback_frames
            if synchronized and (abs(position - 2) < 0.25 or abs(position - 4) < 0.25)
        ],
    }


def measure(
    source: Path,
    source_width: int,
    source_height: int,
    *,
    synchronized: bool,
    repeats: int,
    decoder_threads: int = 0,
    filter_threads: int = 0,
    width: int = 1920,
    height: int = 1080,
    per_frame_reference: bool = False,
    alternate_source: tuple[Path, int, int] | None = None,
) -> BenchmarkRun:
    frames: list[tuple[float, _FrameReceipt]] = []
    ready = threading.Event()
    errors: list[str] = []

    def receive(frame: VideoFrame) -> None:
        frames.append(
            (
                time.monotonic(),
                _FrameReceipt(frame.width, frame.height, frame.position_seconds, len(frame.data)),
            )
        )
        ready.set()

    common: _PlaybackOptions = dict(
        width=width,
        height=height,
        frame_rate=30.0,
        on_frame=receive,
        on_error=errors.append,
        on_end=lambda: None,
        preview_cache_size=0,
        ffmpeg_path=_executable("ffmpeg"),
    )
    settings = _CandidateSettings(decoder_threads, filter_threads, per_frame_reference)
    backend: FfmpegPlaybackBackend
    if synchronized:
        sources, layout = make_layout(
            source, source_width, source_height, width, height, alternate_source
        )
        backend = _CandidateSynchronizedBackend(sources, layout, common, settings)
    else:
        backend = _CandidateSingleBackend(source, common, settings)
    commands = _effective_commands(backend, per_frame_reference)
    samples: list[_SeekSample] = []
    before_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    source_hashes = {str(source): before_hash}
    if alternate_source is not None and synchronized:
        source_hashes[str(alternate_source[0])] = hashlib.sha256(
            alternate_source[0].read_bytes()
        ).hexdigest()
    try:
        for repetition in range(repeats):
            for target in (0.1, 1.1, 1.9, 2.1, 3.1, 4.1):
                ready.clear()
                before = len(frames)
                started = time.monotonic()
                backend.request_preview(target)
                if not ready.wait(15):
                    raise RuntimeError(f"Preview timeout: {errors}")
                delivered_at, frame = frames[before]
                samples.append(
                    {
                        "repetition": repetition,
                        "target": target,
                        "position": frame.position_seconds,
                        "dimensions": [frame.width, frame.height],
                        "frame_bytes": frame.frame_bytes,
                        "latency_ms": (delivered_at - started) * 1000,
                    }
                )
        backend.stop()
        backend._position_seconds = 0.0
        frames.clear()
        started = time.monotonic()
        backend.play()
        time.sleep(4.5)
        backend.stop()
        latencies = [sample["latency_ms"] for sample in samples]
        return {
            "synchronized": synchronized,
            "effective_commands": commands,
            "per_frame_reference": per_frame_reference,
            "decoder_threads_override": decoder_threads,
            "filter_threads_override": filter_threads,
            "output_size": [width, height],
            "samples": samples,
            "seek_latency_ms": summarize(latencies),
            "playback": _playback_metrics(frames, started, synchronized),
            "errors": errors,
            "preview_stats": backend.preview_stats(),
            "playback_stats": (
                backend.playback_stats()
                if isinstance(backend, FfmpegSynchronizedPlaybackBackend)
                else None
            ),
            "source_sha256": before_hash,
            "source_hashes": source_hashes,
            "mixed_source_size": list(alternate_source[1:]) if alternate_source else None,
            "source_preserved": all(
                digest == hashlib.sha256(Path(path).read_bytes()).hexdigest()
                for path, digest in source_hashes.items()
            ),
        }
    finally:
        backend.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--lock", type=Path, required=True)
    parser.add_argument("--repeats", type=int, default=2)
    parser.add_argument("--decoder-threads", type=int, default=0)
    parser.add_argument("--filter-threads", type=int, default=0)
    parser.add_argument("--width", type=int, default=1920)
    parser.add_argument("--height", type=int, default=1080)
    parser.add_argument("--per-frame-reference", action="store_true")
    parser.add_argument("--mixed-sources", action="store_true")
    args = parser.parse_args()
    args.directory.mkdir(parents=True, exist_ok=True)
    with args.lock.open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        results: list[_FixtureRun] = []
        result: dict[str, object] = {
            "hardware": {
                "platform": platform.platform(),
                "cpu": platform.processor(),
                "cpu_affinity": sorted(os.sched_getaffinity(0)),
                "lscpu": subprocess.check_output([_executable("lscpu")], text=True),
                "ffmpeg": subprocess.check_output([_executable("ffmpeg"), "-version"], text=True),
            },
            "baseline_commit": subprocess.check_output(
                [_executable("git"), "rev-parse", "HEAD"], text=True
            ).strip(),
            "settings": vars(args)
            | {
                "directory": str(args.directory),
                "output": str(args.output),
                "lock": str(args.lock),
            },
            "metadata_project": {
                "logical_source_count": 200,
                "duration_hours": 40,
                "real_fixture_seconds_each": 8,
                "real_decoded_timeline_window_seconds": 4.5,
                "note": "Synthetic source identities/durations; not 40h of encoded media.",
            },
            "results": results,
        }
        for width, height in ((1920, 1080), (3840, 2160)):
            source, metadata = fixture(args.directory, width, height)
            alternate_source = None
            if args.mixed_sources:
                other_width, other_height = (3840, 2160) if width == 1920 else (1920, 1080)
                other, _other_metadata = fixture(args.directory, other_width, other_height)
                alternate_source = (other, other_width, other_height)
            entry: _FixtureRun = {"source_size": [width, height], "fixture": metadata, "runs": []}
            for synchronized in (False, True):
                entry["runs"].append(
                    measure(
                        source,
                        width,
                        height,
                        synchronized=synchronized,
                        repeats=args.repeats,
                        decoder_threads=args.decoder_threads,
                        filter_threads=args.filter_threads,
                        width=args.width,
                        height=args.height,
                        per_frame_reference=args.per_frame_reference,
                        alternate_source=alternate_source if synchronized else None,
                    )
                )
            results.append(entry)
            args.output.write_text(json.dumps(result, indent=2) + "\n")
        fcntl.flock(lock, fcntl.LOCK_UN)


if __name__ == "__main__":
    main()
