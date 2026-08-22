from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path

from .export_ffmpeg import (
    execute_fallback,
    execute_mixed_fallback,
    execute_stream_copy,
    expected_mixed_export_frames,
)
from .export_process import (
    emit_export_progress,
    expected_export_frames,
    partial_path,
    remove_partial,
)
from .export_types import (
    _DURATION_TOLERANCE,
    ExportExecutionError,
    ExportPlan,
    ExportProgressCallback,
)
from .media import MediaProbe, MediaProbeError, probe_media


def verify_mixed_export_output(
    plan: ExportPlan,
    candidate: Path,
    *,
    ffmpeg_path: str,
    ffprobe_path: str,
) -> MediaProbe:
    policy = plan.output_policy
    if policy is None:
        raise ExportExecutionError("Mixed export is missing its output policy")
    if not candidate.is_file() or candidate.stat().st_size <= 0:
        raise ExportExecutionError("FFmpeg did not create a non-empty output")
    try:
        output_probe = probe_media(candidate, ffprobe_path)
        _, frame_rate = expected_mixed_export_frames(plan)
    except (MediaProbeError, ExportExecutionError) as error:
        raise ExportExecutionError(
            f"Mixed export output could not be inspected: {error}"
        ) from error
    duration_tolerance = max(_DURATION_TOLERANCE, 2.0 / frame_rate)
    if abs(output_probe.duration_seconds - plan.expected_duration_seconds) > duration_tolerance:
        raise ExportExecutionError("Mixed export duration does not match the edited duration")
    if (output_probe.width, output_probe.height) != (policy.width, policy.height):
        raise ExportExecutionError("Mixed export dimensions do not match the output policy")
    if output_probe.has_audio_stream != policy.audio_stream_present:
        raise ExportExecutionError("Mixed export audio presence does not match the output policy")
    if policy.audio_stream_present:
        if output_probe.audio_sample_rate != policy.audio_sample_rate:
            raise ExportExecutionError("Mixed export sample rate does not match the output policy")
        if output_probe.audio_channels != policy.audio_channels:
            raise ExportExecutionError(
                "Mixed export channel count does not match the output policy"
            )
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
            f"Could not start FFmpeg for mixed output validation: {ffmpeg_path}"
        ) from error
    if result.returncode != 0:
        detail = result.stderr.strip() or "Mixed export decode validation failed"
        raise ExportExecutionError(detail)
    return output_probe


def execute_mixed_export(
    plan: ExportPlan,
    *,
    ffmpeg_path: str,
    ffprobe_path: str,
    progress_callback: ExportProgressCallback | None,
) -> Path:
    if plan.route != "fallback":
        raise ExportExecutionError("Mixed-source exports must use the fallback route")
    source_paths = tuple(path.expanduser().resolve() for path in plan.source_paths)
    destination = plan.destination.expanduser()
    if not source_paths:
        raise ExportExecutionError("Mixed export has no source paths")
    if destination.resolve() in source_paths:
        raise ExportExecutionError("Export destination must differ from every source")
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        source_stats = tuple(path.stat() for path in source_paths)
        probes = tuple(probe_media(path, ffprobe_path) for path in source_paths)
    except (OSError, MediaProbeError) as error:
        raise ExportExecutionError(f"Could not prepare mixed export: {error}") from error
    started = time.monotonic()
    total_frames, _frame_rate = expected_mixed_export_frames(plan)
    emit_export_progress(
        progress_callback,
        stage="starting",
        current_seconds=0.0,
        total_duration_seconds=plan.expected_duration_seconds,
        frame=0,
        total_frames=total_frames,
        fps=None,
        started=started,
    )
    partial = partial_path(destination)
    try:
        execute_mixed_fallback(
            plan,
            probes,
            partial,
            ffmpeg_path,
            progress_callback=progress_callback,
            started=started,
        )
        emit_export_progress(
            progress_callback,
            stage="verifying",
            current_seconds=plan.expected_duration_seconds,
            total_duration_seconds=plan.expected_duration_seconds,
            frame=total_frames,
            total_frames=total_frames,
            fps=None,
            started=started,
            percent_override=99.0,
        )
        verify_mixed_export_output(
            plan,
            partial,
            ffmpeg_path=ffmpeg_path,
            ffprobe_path=ffprobe_path,
        )
        for path, original_stat in zip(source_paths, source_stats, strict=True):
            current_stat = path.stat()
            if (
                current_stat.st_size != original_stat.st_size
                or current_stat.st_mtime_ns != original_stat.st_mtime_ns
            ):
                raise ExportExecutionError(
                    f"Source changed during export; output was not published: {path.name}"
                )
        os.replace(partial, destination)
        emit_export_progress(
            progress_callback,
            stage="complete",
            current_seconds=plan.expected_duration_seconds,
            total_duration_seconds=plan.expected_duration_seconds,
            frame=total_frames,
            total_frames=total_frames,
            fps=None,
            started=started,
            percent_override=100.0,
        )
    except (ExportExecutionError, MediaProbeError, OSError) as error:
        cleanup_error = remove_partial(partial)
        message = f"Could not export {destination.name}: {error}"
        if cleanup_error is not None:
            message += f"; could not remove partial output: {cleanup_error}"
        raise ExportExecutionError(message) from error
    return destination


def verify_export_output(
    plan: ExportPlan,
    source_probe: MediaProbe,
    candidate: Path,
    *,
    ffmpeg_path: str = "ffmpeg",
    ffprobe_path: str = "ffprobe",
) -> MediaProbe:
    if not candidate.is_file() or candidate.stat().st_size <= 0:
        raise ExportExecutionError("FFmpeg did not create a non-empty output")
    try:
        output_probe = probe_media(candidate, ffprobe_path)
    except MediaProbeError as error:
        raise ExportExecutionError(f"Export output could not be probed: {error}") from error
    try:
        frame_rate = source_probe.frame_rate_value
    except MediaProbeError as error:
        raise ExportExecutionError(
            f"Source frame rate is invalid during output validation: {error}"
        ) from error
    duration_tolerance = max(_DURATION_TOLERANCE, 2.0 / frame_rate)
    if abs(output_probe.duration_seconds - plan.expected_duration_seconds) > duration_tolerance:
        raise ExportExecutionError("Export duration does not match the edited duration")
    expected_dimensions = (
        (plan.output_policy.width, plan.output_policy.height)
        if plan.output_policy is not None
        else (source_probe.width, source_probe.height)
    )
    if (output_probe.width, output_probe.height) != expected_dimensions:
        raise ExportExecutionError("Export dimensions do not match the project output policy")
    if output_probe.has_audio_stream != source_probe.has_audio_stream:
        raise ExportExecutionError("Export audio stream presence does not match the source")
    if (
        output_probe.has_audio_stream
        and plan.output_policy is not None
        and (plan.route == "fallback" or plan.audio_decisions)
        and (
            output_probe.audio_sample_rate != plan.output_policy.audio_sample_rate
            or output_probe.audio_channels != plan.output_policy.audio_channels
        )
    ):
        raise ExportExecutionError("Export audio format does not match the output policy")
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
            f"Could not start FFmpeg for output validation: {ffmpeg_path}"
        ) from error
    if result.returncode != 0:
        detail = result.stderr.strip() or "Output decode validation failed"
        raise ExportExecutionError(detail)
    return output_probe


def execute_export(
    plan: ExportPlan,
    *,
    ffmpeg_path: str = "ffmpeg",
    ffprobe_path: str = "ffprobe",
    progress_callback: ExportProgressCallback | None = None,
) -> Path:
    if plan.source_paths:
        return execute_mixed_export(
            plan,
            ffmpeg_path=ffmpeg_path,
            ffprobe_path=ffprobe_path,
            progress_callback=progress_callback,
        )
    if plan.route not in {"stream-copy", "fallback"}:
        raise ExportExecutionError(f"Unsupported export route: {plan.route}")
    source = plan.source.expanduser().resolve()
    destination = plan.destination.expanduser()
    if destination.resolve() == source:
        raise ExportExecutionError("Export destination must differ from the source")
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        source_stat = source.stat()
    except OSError as error:
        raise ExportExecutionError(f"Could not prepare export paths: {error}") from error
    try:
        source_probe = probe_media(source, ffprobe_path)
    except MediaProbeError as error:
        raise ExportExecutionError(f"Could not inspect export source: {error}") from error
    started = time.monotonic()
    total_frames = expected_export_frames(plan, source_probe)
    emit_export_progress(
        progress_callback,
        stage="starting",
        current_seconds=0.0,
        total_duration_seconds=plan.expected_duration_seconds,
        frame=0,
        total_frames=total_frames,
        fps=None,
        started=started,
    )
    partial = partial_path(destination)
    try:
        if plan.route == "stream-copy":
            execute_stream_copy(
                plan,
                source_probe,
                partial,
                ffmpeg_path,
                progress_callback=progress_callback,
                started=started,
            )
        else:
            execute_fallback(
                plan,
                source_probe,
                partial,
                ffmpeg_path,
                progress_callback=progress_callback,
                started=started,
            )
        emit_export_progress(
            progress_callback,
            stage="verifying",
            current_seconds=plan.expected_duration_seconds,
            total_duration_seconds=plan.expected_duration_seconds,
            frame=total_frames,
            total_frames=total_frames,
            fps=None,
            started=started,
            percent_override=99.0,
        )
        verify_export_output(
            plan,
            source_probe,
            partial,
            ffmpeg_path=ffmpeg_path,
            ffprobe_path=ffprobe_path,
        )
        current_source_stat = source.stat()
        if (
            current_source_stat.st_size != source_stat.st_size
            or current_source_stat.st_mtime_ns != source_stat.st_mtime_ns
        ):
            raise ExportExecutionError("Source changed during export; output was not published")
        os.replace(partial, destination)
        emit_export_progress(
            progress_callback,
            stage="complete",
            current_seconds=plan.expected_duration_seconds,
            total_duration_seconds=plan.expected_duration_seconds,
            frame=total_frames,
            total_frames=total_frames,
            fps=None,
            started=started,
            percent_override=100.0,
        )
    except (ExportExecutionError, MediaProbeError, OSError) as error:
        cleanup_error = remove_partial(partial)
        message = f"Could not export {destination.name}: {error}"
        if cleanup_error is not None:
            message += f"; could not remove partial output: {cleanup_error}"
        raise ExportExecutionError(message) from error
    return destination
