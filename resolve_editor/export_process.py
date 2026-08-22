from __future__ import annotations

import math
import subprocess
import time
import uuid
from pathlib import Path

from .export_types import (
    _BOUNDARY_TOLERANCE,
    ExportExecutionError,
    ExportPlan,
    ExportProgress,
    ExportProgressCallback,
    parse_ffmpeg_progress_values,
)
from .media import MediaProbe
from .model import Segment


def output_format(path: Path) -> str:
    return "matroska" if path.suffix.lower() in {".mkv", ".matroska"} else "mp4"


def partial_path(destination: Path) -> Path:
    suffix = destination.suffix or ".mp4"
    return destination.with_name(f".{destination.name}.partial-{uuid.uuid4().hex}{suffix}")


def remove_partial(path: Path) -> OSError | None:
    try:
        path.unlink()
    except FileNotFoundError:
        return None
    except OSError as error:
        return error
    return None


def emit_export_progress(
    callback: ExportProgressCallback | None,
    *,
    stage: str,
    current_seconds: float,
    total_duration_seconds: float,
    frame: int,
    total_frames: int,
    fps: float | None,
    started: float,
    percent_override: float | None = None,
) -> None:
    if callback is None:
        return
    total_duration = max(0.0, float(total_duration_seconds))
    current = max(0.0, min(total_duration, float(current_seconds)))
    fraction = current / total_duration if total_duration else 0.0
    percent = percent_override if percent_override is not None else fraction * 100.0
    percent = max(0.0, min(100.0, percent))
    elapsed = max(0.0, time.monotonic() - started)
    eta = (
        elapsed * (1.0 - fraction) / fraction
        if fraction > 0.0 and percent < 100.0
        else 0.0
        if percent >= 100.0
        else None
    )
    total = max(0, int(total_frames))
    callback(
        ExportProgress(
            stage=stage,
            percent=percent,
            frame=max(0, min(total, int(frame))),
            total_frames=total,
            fps=fps,
            elapsed_seconds=elapsed,
            eta_seconds=eta,
        )
    )


def run_ffmpeg(
    command: list[str],
    *,
    progress_callback: ExportProgressCallback | None = None,
    stage: str = "encoding",
    command_duration_seconds: float = 0.0,
    progress_offset_seconds: float = 0.0,
    progress_total_duration_seconds: float = 0.0,
    command_total_frames: int = 0,
    progress_total_frames: int = 0,
    frame_offset: int = 0,
    started: float | None = None,
) -> None:
    if progress_callback is None:
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,
            )
        except OSError as error:
            raise ExportExecutionError(f"Could not start FFmpeg: {command[0]}") from error
        if result.returncode != 0:
            detail = result.stderr.strip() or "FFmpeg failed without a diagnostic"
            raise ExportExecutionError(detail)
        return

    if not command:
        raise ExportExecutionError("FFmpeg command is empty")
    progress_command = [
        *command[:-1],
        "-progress",
        "pipe:1",
        "-stats_period",
        "0.25",
        "-nostats",
        command[-1],
    ]
    try:
        process = subprocess.Popen(
            progress_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
    except OSError as error:
        raise ExportExecutionError(f"Could not start FFmpeg: {command[0]}") from error

    progress_values: dict[str, str] = {}
    tail: list[str] = []
    progress_started = time.monotonic() if started is None else started
    try:
        if process.stdout is None:
            raise ExportExecutionError("FFmpeg progress pipe is unavailable")
        for raw_line in process.stdout:
            line = raw_line.strip()
            if not line:
                continue
            if "=" not in line:
                tail.append(line)
                tail = tail[-8:]
                continue
            key, value = line.split("=", 1)
            if key not in {
                "frame",
                "fps",
                "out_time_us",
                "out_time_ms",
                "out_time",
                "speed",
                "progress",
            }:
                continue
            progress_values[key] = value
            if key != "progress":
                continue
            sample = parse_ffmpeg_progress_values(progress_values)
            local_time = sample.out_time_seconds
            if sample.done and command_duration_seconds > 0:
                local_time = command_duration_seconds
            command_duration = max(0.0, command_duration_seconds)
            if command_duration:
                local_time = min(command_duration, local_time)
            total_duration = progress_total_duration_seconds or command_duration
            local_fraction = local_time / command_duration if command_duration > 0 else 0.0
            local_frame = sample.frame
            if sample.done and command_total_frames > 0:
                local_frame = command_total_frames
            elif local_frame <= 0 and command_total_frames > 0:
                local_frame = round(local_fraction * command_total_frames)
            emit_export_progress(
                progress_callback,
                stage=stage,
                current_seconds=progress_offset_seconds + local_time,
                total_duration_seconds=total_duration,
                frame=frame_offset + local_frame,
                total_frames=progress_total_frames or command_total_frames,
                fps=sample.fps,
                started=progress_started,
                percent_override=(
                    100.0
                    if sample.done and progress_offset_seconds + local_time >= total_duration
                    else None
                ),
            )
    except KeyboardInterrupt:
        process.terminate()
        process.wait()
        raise
    finally:
        if process.stdout is not None:
            process.stdout.close()
    return_code = process.wait()
    if return_code != 0:
        detail = "\n".join(tail) or "FFmpeg failed without a diagnostic"
        raise ExportExecutionError(detail)


def expected_export_frames(plan: ExportPlan, source_probe: MediaProbe) -> int:
    return max(
        1,
        round(plan.expected_duration_seconds * source_probe.frame_rate_value),
    )


def segment_is_full_source(
    segment: Segment,
    source_duration_seconds: float,
) -> bool:
    return math.isclose(
        segment.start_seconds,
        0.0,
        abs_tol=_BOUNDARY_TOLERANCE,
    ) and math.isclose(
        segment.end_seconds,
        source_duration_seconds,
        abs_tol=_BOUNDARY_TOLERANCE,
    )
