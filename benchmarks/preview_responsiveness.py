#!/usr/bin/env python3
"""Measure editor preview responsiveness with deterministic pointer-like traces."""

from __future__ import annotations

import argparse
import json
import math
import platform
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any

from framestudio.ffmpeg_playback import (
    FfmpegComposedPlaybackBackend,
    FfmpegPlaybackBackend,
    VideoFrame,
)
from framestudio.model import Segment

TRACE = (
    ("cursor", 0.10),
    ("cursor", 0.20),
    ("cursor", 0.30),
    ("click", 0.50),
    ("seek", 0.70),
    ("scroll", 0.40),
    ("scroll", 0.60),
    ("click", 0.20),
)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, action="append", required=True)
    parser.add_argument("--duration", type=float, required=True)
    parser.add_argument("--frame-rate", type=float, default=10.0)
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def _make_backend(
    sources: tuple[Path, ...],
    duration: float,
    frame_rate: float,
    cache_size: int,
    on_frame,
    on_error,
    ffmpeg_path: str = "ffmpeg",
):
    common = {
        "width": 160,
        "height": 90,
        "frame_rate": frame_rate,
        "duration_seconds": duration,
        "on_frame": on_frame,
        "on_error": on_error,
        "on_end": lambda: None,
        "preview_cache_size": cache_size,
        "ffmpeg_path": ffmpeg_path,
    }
    if len(sources) == 1:
        return FfmpegPlaybackBackend(sources[0], **common)
    blocks = []
    offset = 0.0
    block_duration = duration / len(sources)
    for index in range(len(sources)):
        blocks.append(
            Segment.create(
                0.0,
                block_duration,
                source_id=f"source-{index + 1}",
                timeline_start_seconds=offset,
                timeline_end_seconds=offset + block_duration,
            )
        )
        offset += block_duration
    return FfmpegComposedPlaybackBackend(
        tuple((f"source-{index + 1}", source) for index, source in enumerate(sources)),
        tuple(blocks),
        **common,
    )


def _run_trace(
    sources: tuple[Path, ...],
    duration: float,
    frame_rate: float,
    cache_size: int,
    repetitions: int,
) -> dict[str, Any]:
    frames: list[tuple[float, VideoFrame]] = []
    frames_lock = threading.Lock()
    errors: list[str] = []
    frame_ready = threading.Event()

    def on_frame(frame: VideoFrame) -> None:
        with frames_lock:
            frames.append((time.monotonic(), frame))
        frame_ready.set()

    backend = _make_backend(
        sources,
        duration,
        frame_rate,
        cache_size,
        on_frame,
        errors.append,
    )
    samples: list[dict[str, Any]] = []
    try:
        for repetition in range(repetitions):
            for action, position_fraction in TRACE:
                target = min(duration, max(0.0, duration * position_fraction))
                with frames_lock:
                    before = len(frames)
                frame_ready.clear()
                requested_at = time.monotonic()
                backend.request_preview(target)
                received = frame_ready.wait(timeout=20)
                latency_ms = None
                displayed_position = None
                decoded_position = None
                with frames_lock:
                    sample_frames = frames[before:]
                if received and sample_frames:
                    delivered_at, frame = sample_frames[-1]
                    latency_ms = round((delivered_at - requested_at) * 1000, 3)
                    displayed_position = frame.position_seconds
                    decoded_position = frame.decoded_position_seconds
                samples.append(
                    {
                        "repetition": repetition + 1,
                        "action": action,
                        "requested_position_seconds": round(target, 6),
                        "displayed_position_seconds": displayed_position,
                        "decoded_position_seconds": decoded_position,
                        "latency_ms": latency_ms,
                        "failure": None if received else "frame timeout",
                    }
                )
        rapid_positions = [duration * fraction for fraction in (0.05, 0.15, 0.25, 0.35, 0.45)]
        rapid_start = len(frames)
        frame_ready.clear()
        rapid_started_at = time.monotonic()
        for target in rapid_positions:
            backend.request_preview(target)
        rapid_deadline = time.monotonic() + 20.0
        newest_request_rendered = False
        rapid_frames: list[tuple[float, VideoFrame]] = []
        while time.monotonic() < rapid_deadline:
            with frames_lock:
                rapid_frames = list(frames[rapid_start:])
                newest_request_rendered = bool(rapid_frames) and math.isclose(
                    rapid_frames[-1][1].position_seconds,
                    rapid_positions[-1],
                    rel_tol=0.0,
                    abs_tol=1e-6,
                )
            if newest_request_rendered:
                break
            frame_ready.wait(timeout=min(0.05, max(0.0, rapid_deadline - time.monotonic())))
            frame_ready.clear()
        rapid_received = newest_request_rendered
        return {
            "cache_size": cache_size,
            "samples": samples,
            "rapid_pointer": {
                "submitted_requests": len(rapid_positions),
                "visible_frames": len(rapid_frames),
                "last_requested_position_seconds": rapid_positions[-1],
                "newest_request_rendered": newest_request_rendered,
                "last_displayed_position_seconds": (
                    rapid_frames[-1][1].position_seconds if rapid_frames else None
                ),
                "last_decoded_position_seconds": (
                    rapid_frames[-1][1].decoded_position_seconds if rapid_frames else None
                ),
                "latency_ms": (
                    round((rapid_frames[-1][0] - rapid_started_at) * 1000, 3)
                    if rapid_received and rapid_frames
                    else None
                ),
            },
            "errors": errors,
            "backend_preview_stats": backend.preview_stats(),
            "successful_samples": sum(sample["latency_ms"] is not None for sample in samples),
            "failed_samples": sum(sample["latency_ms"] is None for sample in samples),
            "latency_ms": [
                sample["latency_ms"] for sample in samples if sample["latency_ms"] is not None
            ],
        }
    finally:
        backend.close()


def _run_failure_probe(
    sources: tuple[Path, ...],
    duration: float,
    frame_rate: float,
) -> dict[str, Any]:
    errors: list[str] = []
    backend = _make_backend(
        sources,
        duration,
        frame_rate,
        cache_size=0,
        on_frame=lambda _frame: None,
        on_error=errors.append,
        ffmpeg_path="ffmpeg-preview-benchmark-missing",
    )
    try:
        backend.request_preview(0.25)
        deadline = time.monotonic() + 3
        while not errors and time.monotonic() < deadline:
            time.sleep(0.01)
        return {
            "reported": bool(errors),
            "errors": errors,
            "stats": backend.preview_stats(),
        }
    finally:
        backend.close()


def summarize_preview_benchmark(result: dict[str, Any]) -> dict[str, Any]:
    """Return a terminal status from preview trace and decoder-failure gates."""

    conditions = result.get("conditions", {})
    conditions_passed = bool(conditions) and all(
        item.get("failed_samples", 0) == 0
        and not item.get("errors")
        and (
            "rapid_pointer" not in item
            or (
                item["rapid_pointer"].get("latency_ms") is not None
                and item["rapid_pointer"].get("newest_request_rendered", False)
            )
        )
        for item in conditions.values()
    )
    failure_probe_passed = bool(result.get("failure_probe", {}).get("reported"))
    return {
        "status": "passed" if conditions_passed and failure_probe_passed else "failed",
        "conditions_passed": conditions_passed,
        "failure_probe_passed": failure_probe_passed,
    }


def main() -> int:
    arguments = parse_arguments()
    if arguments.duration <= 0 or arguments.frame_rate <= 0:
        raise SystemExit("--duration and --frame-rate must be positive")
    if arguments.repetitions <= 0:
        raise SystemExit("--repetitions must be positive")
    sources = tuple(path.expanduser().resolve() for path in arguments.source)
    missing = [path.name for path in sources if not path.is_file()]
    if missing:
        raise SystemExit(f"Source media not found: {', '.join(missing)}")

    result = {
        "harness": "benchmarks/preview_responsiveness.py",
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "ffmpeg": _ffmpeg_version(),
        "source_names": [path.name for path in sources],
        "duration_seconds": arguments.duration,
        "frame_rate": arguments.frame_rate,
        "trace": [{"action": action, "position_fraction": fraction} for action, fraction in TRACE],
        "failure_probe": _run_failure_probe(sources, arguments.duration, arguments.frame_rate),
        "conditions": {
            "cold": _run_trace(
                sources,
                arguments.duration,
                arguments.frame_rate,
                cache_size=0,
                repetitions=1,
            ),
            "repeated_current_no_cache": _run_trace(
                sources,
                arguments.duration,
                arguments.frame_rate,
                cache_size=0,
                repetitions=arguments.repetitions,
            ),
            "cold_cached_candidate": _run_trace(
                sources,
                arguments.duration,
                arguments.frame_rate,
                cache_size=8,
                repetitions=1,
            ),
            "warm_cached_candidate": _run_trace(
                sources,
                arguments.duration,
                arguments.frame_rate,
                cache_size=8,
                repetitions=arguments.repetitions,
            ),
        },
    }
    result["status"] = summarize_preview_benchmark(result)["status"]
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(arguments.output)
    return 0 if result["status"] == "passed" else 1


def _ffmpeg_version() -> str:
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return "unavailable"
    return result.stdout.splitlines()[0] if result.stdout else f"exit {result.returncode}"


if __name__ == "__main__":
    raise SystemExit(main())
