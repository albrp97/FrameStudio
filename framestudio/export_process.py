from __future__ import annotations

import math
import os
import subprocess
import threading
import time
import uuid
from collections.abc import Sequence
from fractions import Fraction
from pathlib import Path
from typing import Protocol

from .export_types import (
    _BOUNDARY_TOLERANCE,
    ExportExecutionError,
    ExportPlan,
    ExportProgress,
    ExportProgressCallback,
    parse_ffmpeg_progress_values,
)
from .media import MediaProbe, MediaProbeError, probe_media
from .model import Segment


class _ManagedProcess(Protocol):
    def poll(self) -> int | None: ...

    def terminate(self) -> None: ...

    def kill(self) -> None: ...

    def wait(self, timeout: float | None = None) -> int: ...


_PROCESS_TERMINATION_TIMEOUT_SECONDS = 5.0


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


def prepare_export_sources(
    source_paths: Sequence[Path],
    ffprobe_path: str,
    *,
    label: str,
) -> tuple[tuple[os.stat_result, ...], tuple[MediaProbe, ...]]:
    try:
        source_stats = tuple(path.stat() for path in source_paths)
        probes = tuple(probe_media(path, ffprobe_path) for path in source_paths)
    except (OSError, MediaProbeError) as error:
        raise ExportExecutionError(f"Could not prepare {label}: {error}") from error
    return source_stats, probes


def validate_decoded_output(
    candidate: Path,
    ffmpeg_path: str,
    *,
    label: str,
) -> None:
    try:
        result = subprocess.run(
            [
                ffmpeg_path,
                "-hide_banner",
                "-loglevel",
                "error",
                "-xerror",
                "-nostdin",
                "-i",
                str(candidate),
                "-map",
                "0",
                "-f",
                "null",
                "-",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as error:
        raise ExportExecutionError(
            f"Could not start FFmpeg for {label} validation: {ffmpeg_path}"
        ) from error
    if result.returncode != 0:
        detail = result.stderr.strip() or f"{label.capitalize()} decode validation failed"
        raise ExportExecutionError(detail)


def verify_source_preservation(
    source_paths: Sequence[Path],
    source_stats: Sequence[os.stat_result],
) -> None:
    for path, original_stat in zip(source_paths, source_stats, strict=True):
        current_stat = path.stat()
        if (
            current_stat.st_size != original_stat.st_size
            or current_stat.st_mtime_ns != original_stat.st_mtime_ns
        ):
            raise ExportExecutionError(
                f"Source changed during export; output was not published: {path.name}"
            )


def publish_verified_export(
    partial: Path,
    destination: Path,
    source_paths: Sequence[Path],
    source_stats: Sequence[os.stat_result],
    *,
    cancel_event: threading.Event | None,
    progress_callback: ExportProgressCallback | None,
    expected_duration_seconds: float,
    total_frames: int,
    started: float,
    cancellation_lock: threading.Lock | None = None,
) -> None:
    def publish() -> None:
        if cancel_event is not None and cancel_event.is_set():
            raise ExportExecutionError("Export cancelled")
        verify_source_preservation(source_paths, source_stats)
        if cancel_event is not None and cancel_event.is_set():
            raise ExportExecutionError("Export cancelled")
        os.replace(partial, destination)

    if cancellation_lock is None:
        publish()
    else:
        with cancellation_lock:
            publish()
    emit_export_progress(
        progress_callback,
        stage="complete",
        current_seconds=expected_duration_seconds,
        total_duration_seconds=expected_duration_seconds,
        frame=total_frames,
        total_frames=total_frames,
        fps=None,
        started=started,
        percent_override=100.0,
    )


def _terminate_process(process: _ManagedProcess) -> None:
    if process.poll() is not None:
        return
    try:
        process.terminate()
    except ProcessLookupError:
        return
    try:
        process.wait(timeout=_PROCESS_TERMINATION_TIMEOUT_SECONDS)
        return
    except subprocess.TimeoutExpired:
        pass
    try:
        process.kill()
    except ProcessLookupError:
        return
    try:
        process.wait(timeout=_PROCESS_TERMINATION_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired as error:
        raise ExportExecutionError("FFmpeg did not terminate after cancellation") from error


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
    cancel_event: threading.Event | None = None,
) -> None:
    if cancel_event is not None and cancel_event.is_set():
        raise ExportExecutionError("Export cancelled")
    if progress_callback is None and cancel_event is None:
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
    cancellation_stop = threading.Event()
    cancellation_watcher: threading.Thread | None = None
    termination_errors: list[ExportExecutionError] = []

    if cancel_event is not None:

        def watch_cancellation() -> None:
            while not cancellation_stop.wait(0.05):
                if not cancel_event.is_set():
                    continue
                try:
                    _terminate_process(process)
                except ExportExecutionError as error:
                    termination_errors.append(error)
                return

        cancellation_watcher = threading.Thread(
            target=watch_cancellation,
            name="framestudio-editor-ffmpeg-cancel",
            daemon=True,
        )
        cancellation_watcher.start()

    try:
        if process.stdout is None:
            raise ExportExecutionError("FFmpeg progress pipe is unavailable")
        for raw_line in process.stdout:
            if cancel_event is not None and cancel_event.is_set():
                raise ExportExecutionError("Export cancelled")
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
        if termination_errors:
            raise termination_errors[0]
        if cancel_event is not None and cancel_event.is_set():
            raise ExportExecutionError("Export cancelled")
        return_code = process.wait()
    except KeyboardInterrupt:
        _terminate_process(process)
        raise
    finally:
        cancellation_stop.set()
        if cancellation_watcher is not None:
            cancellation_watcher.join(timeout=_PROCESS_TERMINATION_TIMEOUT_SECONDS + 1.0)
        if process.stdout is not None:
            process.stdout.close()
        if process.poll() is None:
            _terminate_process(process)
    if return_code != 0:
        detail = "\n".join(tail) or "FFmpeg failed without a diagnostic"
        raise ExportExecutionError(detail)


def expected_export_frames(plan: ExportPlan, source_probe: MediaProbe) -> int:
    try:
        rate = (
            Fraction(plan.output_policy.frame_rate)
            if plan.output_policy is not None
            else Fraction(source_probe.frame_rate)
        )
        duration = Fraction(str(plan.expected_duration_seconds))
    except (ValueError, ZeroDivisionError) as error:
        raise ExportExecutionError("Export frame-rate metadata is invalid") from error
    exact_frames = duration * rate
    return max(
        1,
        (exact_frames.numerator + exact_frames.denominator // 2) // exact_frames.denominator,
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
