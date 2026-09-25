from __future__ import annotations

import json
import math
import os
import subprocess
import threading
import time
import uuid
from collections.abc import Callable, Sequence
from dataclasses import replace
from fractions import Fraction
from pathlib import Path
from typing import Protocol

from .export_types import (
    _BOUNDARY_TOLERANCE,
    ExportExecutionError,
    ExportPlan,
    ExportProgress,
    ExportProgressCallback,
    OutputPolicy,
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


def make_progress_heartbeat(
    callback: ExportProgressCallback | None,
    *,
    stage: str,
    total_frames: int,
    started: float,
    percent: float,
    frame: int | None = None,
) -> Callable[[], None] | None:
    if callback is None:
        return None
    heartbeat_frame = total_frames if frame is None else frame
    heartbeat_frame = max(0, min(max(0, total_frames), heartbeat_frame))

    def heartbeat() -> None:
        callback(
            ExportProgress(
                stage=stage,
                percent=max(0.0, min(100.0, percent)),
                frame=heartbeat_frame,
                total_frames=max(0, total_frames),
                fps=None,
                elapsed_seconds=max(0.0, time.monotonic() - started),
                eta_seconds=None,
            )
        )

    return heartbeat


def make_output_validation_heartbeats(
    callback: ExportProgressCallback | None,
    *,
    total_frames: int,
    started: float,
) -> tuple[Callable[[], None] | None, Callable[[], None] | None]:
    return (
        make_progress_heartbeat(
            callback,
            stage="verifying output",
            total_frames=total_frames,
            started=started,
            percent=99.0,
        ),
        make_progress_heartbeat(
            callback,
            stage="checking cached output",
            total_frames=total_frames,
            started=started,
            percent=0.0,
            frame=0,
        ),
    )


def emit_verification_progress(
    plan: ExportPlan,
    total_frames: int,
    progress_callback: ExportProgressCallback | None,
    started: float,
) -> None:
    duration = plan.expected_duration_seconds
    emit_export_progress(
        progress_callback,
        stage="verifying",
        current_seconds=duration,
        total_duration_seconds=duration,
        frame=total_frames,
        total_frames=total_frames,
        fps=None,
        started=started,
        percent_override=99.0,
    )


def monotonic_progress_callback(
    callback: ExportProgressCallback | None,
) -> ExportProgressCallback | None:
    if callback is None:
        return None
    last_percent = 0.0
    last_frame = 0

    def forward(progress: ExportProgress) -> None:
        nonlocal last_frame, last_percent
        percent = max(last_percent, progress.percent)
        frame = max(last_frame, progress.frame)
        last_percent = percent
        last_frame = frame
        if percent != progress.percent or frame != progress.frame:
            progress = replace(progress, percent=percent, frame=frame)
        callback(progress)

    return forward


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
    heartbeat_callback: Callable[[], None] | None = None,
    heartbeat_interval_seconds: float = 5.0,
) -> None:
    try:
        result = _run_command_with_heartbeat(
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
            heartbeat_callback=heartbeat_callback,
            heartbeat_interval_seconds=heartbeat_interval_seconds,
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


def _run_command_with_heartbeat(
    command: list[str],
    *,
    heartbeat_callback: Callable[[], None] | None,
    heartbeat_interval_seconds: float,
) -> subprocess.CompletedProcess[str]:
    if heartbeat_callback is None:
        return subprocess.run(command, capture_output=True, text=True, check=False)
    if not math.isfinite(heartbeat_interval_seconds) or heartbeat_interval_seconds <= 0.0:
        raise ValueError("Heartbeat interval must be a positive finite number")
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        while True:
            try:
                stdout, stderr = process.communicate(timeout=heartbeat_interval_seconds)
            except subprocess.TimeoutExpired:
                heartbeat_callback()
            else:
                return subprocess.CompletedProcess(command, process.returncode, stdout, stderr)
    except BaseException:
        if process.poll() is None:
            try:
                process.terminate()
            except ProcessLookupError:
                pass
            try:
                process.communicate(timeout=_PROCESS_TERMINATION_TIMEOUT_SECONDS)
            except subprocess.TimeoutExpired:
                try:
                    process.kill()
                except ProcessLookupError:
                    pass
                process.communicate()
        raise


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


def probe_frame_count(
    path: Path,
    ffprobe_path: str = "ffprobe",
    *,
    heartbeat_callback: Callable[[], None] | None = None,
    heartbeat_interval_seconds: float = 5.0,
) -> int:
    command = [
        ffprobe_path,
        "-v",
        "error",
        "-count_frames",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=nb_read_frames",
        "-of",
        "json",
        str(path),
    ]
    try:
        result = _run_command_with_heartbeat(
            command,
            heartbeat_callback=heartbeat_callback,
            heartbeat_interval_seconds=heartbeat_interval_seconds,
        )
    except OSError as error:
        raise ExportExecutionError(
            f"Could not start ffprobe for frame counting: {ffprobe_path}"
        ) from error
    if result.returncode != 0:
        detail = result.stderr.strip() or "ffprobe could not count video frames"
        raise ExportExecutionError(detail)
    try:
        value = json.loads(result.stdout)["streams"][0]["nb_read_frames"]
        count = int(value)
    except (KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError) as error:
        raise ExportExecutionError(f"Could not count frames in {path.name}") from error
    if count <= 0:
        raise ExportExecutionError(f"Frame count is invalid for {path.name}")
    return count


def ensure_exact_video_frame_count(
    destination: Path,
    expected_frames: int,
    *,
    frame_rate: Fraction,
    video_codec: str,
    pixel_format: str,
    container: str,
    has_audio: bool,
    audio_codec: str | None,
    audio_sample_rate: int,
    audio_channels: int,
    ffmpeg_path: str,
    ffprobe_path: str,
    heartbeat_callback: Callable[[], None] | None = None,
    heartbeat_interval_seconds: float = 5.0,
) -> MediaProbe:
    """Repair a rendered clip whose frame count drifted from its rounded target.

    Frame-accurate seeking and constant-rate conversion can legitimately land
    one or more frames short (or, rarely, over) of the exact frame count
    implied by rounding a segment's duration to the output frame rate.
    Interpolated segments already enforce their target frame count, but
    passthrough/converted segments did not, so this closes that gap in place
    by cloning or trimming the trailing frame(s) before the drift can
    accumulate into a final "frame count does not match" export failure.
    """
    actual_frames = probe_frame_count(
        destination,
        ffprobe_path,
        heartbeat_callback=heartbeat_callback,
        heartbeat_interval_seconds=heartbeat_interval_seconds,
    )
    if actual_frames == expected_frames:
        return probe_media(destination, ffprobe_path)
    deficit = expected_frames - actual_frames
    corrected = destination.with_name(
        f".{destination.name}.frame-fix-{uuid.uuid4().hex}{destination.suffix}"
    )
    command = [
        ffmpeg_path,
        "-hide_banner",
        "-loglevel",
        "error",
        "-nostdin",
        "-y",
        "-i",
        str(destination),
    ]
    if deficit > 0:
        video_expr = f"[0:v]tpad=stop_mode=clone:stop={deficit}[v]"
        pad_seconds = deficit / float(frame_rate)
    else:
        video_expr = f"[0:v]trim=end_frame={expected_frames},setpts=PTS-STARTPTS[v]"
        pad_seconds = 0.0
    if has_audio:
        audio_expr = f"[0:a]apad=pad_dur={pad_seconds:.6f}[a]" if deficit > 0 else "[0:a]anull[a]"
        command.extend(
            ["-filter_complex", f"{video_expr};{audio_expr}", "-map", "[v]", "-map", "[a]"]
        )
    else:
        command.extend(["-filter_complex", video_expr, "-map", "[v]"])
    command.extend(
        [
            "-frames:v",
            str(expected_frames),
            "-c:v",
            video_codec,
            "-preset",
            "medium",
            "-crf",
            "18",
            "-pix_fmt",
            pixel_format,
        ]
    )
    if has_audio:
        command.extend(
            [
                "-c:a",
                audio_codec or "aac",
                "-b:a",
                "192k",
                "-ar",
                str(audio_sample_rate),
                "-ac",
                str(audio_channels),
            ]
        )
    command.append("-movflags")
    command.append("+faststart")
    if deficit < 0:
        command.append("-shortest")
    command.extend(["-f", container, str(corrected)])
    try:
        result = _run_command_with_heartbeat(
            command,
            heartbeat_callback=heartbeat_callback,
            heartbeat_interval_seconds=heartbeat_interval_seconds,
        )
    except OSError as error:
        corrected.unlink(missing_ok=True)
        raise ExportExecutionError(
            f"Could not start FFmpeg to correct frame count: {ffmpeg_path}"
        ) from error
    if result.returncode != 0:
        corrected.unlink(missing_ok=True)
        detail = result.stderr.strip() or "FFmpeg frame-count correction failed"
        raise ExportExecutionError(detail)
    if not corrected.is_file() or corrected.stat().st_size <= 0:
        corrected.unlink(missing_ok=True)
        raise ExportExecutionError(
            f"Frame count correction did not create an output for {destination.name}"
        )
    corrected_frames = probe_frame_count(
        corrected,
        ffprobe_path,
        heartbeat_callback=heartbeat_callback,
        heartbeat_interval_seconds=heartbeat_interval_seconds,
    )
    if corrected_frames != expected_frames:
        corrected.unlink(missing_ok=True)
        raise ExportExecutionError(
            f"Frame count correction for {destination.name} still does not match the target "
            f"({corrected_frames} != {expected_frames})"
        )
    os.replace(corrected, destination)
    try:
        return probe_media(destination, ffprobe_path)
    except MediaProbeError as error:
        raise ExportExecutionError(f"Corrected source could not be inspected: {error}") from error


def ensure_video_frame_count_for_policy(
    destination: Path,
    expected_frames: int,
    *,
    frame_rate: Fraction,
    policy: OutputPolicy,
    ffmpeg_path: str,
    ffprobe_path: str,
    heartbeat_callback: Callable[[], None] | None = None,
    heartbeat_interval_seconds: float = 5.0,
) -> MediaProbe:
    return ensure_exact_video_frame_count(
        destination,
        expected_frames,
        frame_rate=frame_rate,
        video_codec=policy.video_codec,
        pixel_format=policy.pixel_format,
        container=policy.container,
        has_audio=policy.audio_stream_present,
        audio_codec=policy.audio_codec,
        audio_sample_rate=policy.audio_sample_rate,
        audio_channels=policy.audio_channels,
        ffmpeg_path=ffmpeg_path,
        ffprobe_path=ffprobe_path,
        heartbeat_callback=heartbeat_callback,
        heartbeat_interval_seconds=heartbeat_interval_seconds,
    )
