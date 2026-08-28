from __future__ import annotations

import threading
import time
from fractions import Fraction
from pathlib import Path

from .export_ffmpeg import (
    execute_fallback,
    execute_mixed_fallback,
    execute_stream_copy,
    expected_mixed_export_frames,
)
from .export_interpolation import execute_enhanced_export, probe_frame_count
from .export_process import (
    emit_export_progress,
    expected_export_frames,
    partial_path,
    prepare_export_sources,
    publish_verified_export,
    remove_partial,
    validate_decoded_output,
)
from .export_types import (
    _DURATION_TOLERANCE,
    ExportExecutionError,
    ExportPlan,
    ExportProgressCallback,
)
from .interpolation_artifacts import run_artifact_gate
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
        expected_frames, frame_rate = expected_mixed_export_frames(plan)
    except (MediaProbeError, ExportExecutionError) as error:
        raise ExportExecutionError(
            f"Mixed export output could not be inspected: {error}"
        ) from error
    duration_tolerance = max(_DURATION_TOLERANCE, 2.0 / frame_rate)
    if abs(output_probe.duration_seconds - plan.expected_duration_seconds) > duration_tolerance:
        raise ExportExecutionError("Mixed export duration does not match the edited duration")
    if (output_probe.width, output_probe.height) != (policy.width, policy.height):
        raise ExportExecutionError("Mixed export dimensions do not match the output policy")
    try:
        actual_rate = Fraction(output_probe.frame_rate)
        expected_rate = Fraction(policy.frame_rate)
    except (ValueError, ZeroDivisionError) as error:
        raise ExportExecutionError("Mixed export frame rate metadata is invalid") from error
    if actual_rate != expected_rate:
        raise ExportExecutionError("Mixed export frame rate does not match the output policy")
    actual_frames = probe_frame_count(candidate, ffprobe_path)
    if actual_frames != expected_frames:
        raise ExportExecutionError("Mixed export frame count does not match the selected target")
    if plan.route == "enhanced":
        run_artifact_gate(
            candidate,
            expected_frames,
            ffmpeg_path=ffmpeg_path,
            label="enhanced mixed output",
        )
    if output_probe.has_audio_stream != policy.audio_stream_present:
        raise ExportExecutionError("Mixed export audio presence does not match the output policy")
    if policy.audio_stream_present:
        if output_probe.audio_sample_rate != policy.audio_sample_rate:
            raise ExportExecutionError("Mixed export sample rate does not match the output policy")
        if output_probe.audio_channels != policy.audio_channels:
            raise ExportExecutionError(
                "Mixed export channel count does not match the output policy"
            )
    validate_decoded_output(candidate, ffmpeg_path, label="mixed output")
    return output_probe


def execute_mixed_export(
    plan: ExportPlan,
    *,
    ffmpeg_path: str,
    ffprobe_path: str,
    progress_callback: ExportProgressCallback | None,
    cancel_event: threading.Event | None = None,
    cancellation_lock: threading.Lock | None = None,
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
    except OSError as error:
        raise ExportExecutionError(f"Could not prepare mixed export: {error}") from error
    source_stats, probes = prepare_export_sources(
        source_paths,
        ffprobe_path,
        label="mixed export",
    )
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
            cancel_event=cancel_event,
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
        if cancel_event is not None and cancel_event.is_set():
            raise ExportExecutionError("Export cancelled")
        verify_mixed_export_output(
            plan,
            partial,
            ffmpeg_path=ffmpeg_path,
            ffprobe_path=ffprobe_path,
        )
        publish_verified_export(
            partial,
            destination,
            source_paths,
            source_stats,
            cancel_event=cancel_event,
            progress_callback=progress_callback,
            expected_duration_seconds=plan.expected_duration_seconds,
            total_frames=total_frames,
            started=started,
            cancellation_lock=cancellation_lock,
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
    if plan.frame_rate_policy is not None and plan.output_policy is not None:
        try:
            actual_rate = Fraction(output_probe.frame_rate)
            expected_rate = Fraction(plan.output_policy.frame_rate)
        except (ValueError, ZeroDivisionError) as error:
            raise ExportExecutionError("Export frame rate metadata is invalid") from error
        if actual_rate != expected_rate:
            raise ExportExecutionError("Export frame rate does not match the selected target")
        if plan.route == "enhanced":
            actual_frames = probe_frame_count(candidate, ffprobe_path)
            expected_frames = max(
                1,
                (
                    Fraction(str(plan.expected_duration_seconds)) * expected_rate + Fraction(1, 2)
                ).numerator
                // (
                    (
                        Fraction(str(plan.expected_duration_seconds)) * expected_rate
                        + Fraction(1, 2)
                    ).denominator
                ),
            )
            if actual_frames != expected_frames:
                raise ExportExecutionError(
                    "Enhanced export frame count does not match the selected target"
                )
            run_artifact_gate(
                candidate,
                expected_frames,
                ffmpeg_path=ffmpeg_path,
                label="enhanced output",
            )
    validate_decoded_output(candidate, ffmpeg_path, label="output")
    return output_probe


def execute_export(
    plan: ExportPlan,
    *,
    ffmpeg_path: str = "ffmpeg",
    ffprobe_path: str = "ffprobe",
    progress_callback: ExportProgressCallback | None = None,
    cancel_event: threading.Event | None = None,
    cancellation_lock: threading.Lock | None = None,
) -> Path:
    if cancel_event is not None and cancel_event.is_set():
        raise ExportExecutionError("Export cancelled")
    if plan.route == "enhanced":
        return execute_enhanced_export(
            plan,
            ffmpeg_path=ffmpeg_path,
            ffprobe_path=ffprobe_path,
            progress_callback=progress_callback,
            verify_single_output=verify_export_output,
            verify_mixed_output=verify_mixed_export_output,
            cancel_event=cancel_event,
            cancellation_lock=cancellation_lock,
        )
    if plan.source_paths:
        return execute_mixed_export(
            plan,
            ffmpeg_path=ffmpeg_path,
            ffprobe_path=ffprobe_path,
            progress_callback=progress_callback,
            cancel_event=cancel_event,
            cancellation_lock=cancellation_lock,
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
                cancel_event=cancel_event,
            )
        else:
            execute_fallback(
                plan,
                source_probe,
                partial,
                ffmpeg_path,
                progress_callback=progress_callback,
                started=started,
                cancel_event=cancel_event,
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
        if cancel_event is not None and cancel_event.is_set():
            raise ExportExecutionError("Export cancelled")
        verify_export_output(
            plan,
            source_probe,
            partial,
            ffmpeg_path=ffmpeg_path,
            ffprobe_path=ffprobe_path,
        )
        publish_verified_export(
            partial,
            destination,
            (source,),
            (source_stat,),
            cancel_event=cancel_event,
            progress_callback=progress_callback,
            expected_duration_seconds=plan.expected_duration_seconds,
            total_frames=total_frames,
            started=started,
            cancellation_lock=cancellation_lock,
        )
    except (ExportExecutionError, MediaProbeError, OSError) as error:
        cleanup_error = remove_partial(partial)
        message = f"Could not export {destination.name}: {error}"
        if cleanup_error is not None:
            message += f"; could not remove partial output: {cleanup_error}"
        raise ExportExecutionError(message) from error
    return destination
