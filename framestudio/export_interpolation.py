from __future__ import annotations

import json
import math
import os
import shutil
import subprocess
import tempfile
import threading
import time
from collections.abc import Sequence
from dataclasses import replace
from fractions import Fraction
from functools import partial as bind_partial
from pathlib import Path
from typing import Callable

from .export_ffmpeg import execute_fallback, execute_mixed_fallback
from .export_process import (
    emit_export_progress,
    partial_path,
    prepare_export_sources,
    publish_verified_export,
    remove_partial,
    run_ffmpeg,
    segment_is_full_source,
)
from .export_smart_render import (
    _write_concat_list,
    build_concat_copy_command,
    build_video_only_copy_command,
    prepare_enhanced_master,
    prepare_enhanced_sources,
)
from .export_types import (
    _DURATION_TOLERANCE,
    ExportExecutionError,
    ExportPlan,
    ExportProgress,
    ExportProgressCallback,
    OutputPolicy,
)
from .fps_policy import (
    FrameRatePolicy,
    SourceRateDecision,
    canonical_rate,
    target_frame_count,
)
from .interpolation import run_source_interpolation
from .interpolation_artifacts import run_artifact_gate
from .media import MediaProbe, MediaProbeError, probe_media
from .upscale_policy import UpscaleDecision

VerifySingle = Callable[..., MediaProbe]
VerifyMixed = Callable[..., MediaProbe]


def probe_frame_count(path: Path, ffprobe_path: str = "ffprobe") -> int:
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
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
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


def _policy(plan: ExportPlan) -> FrameRatePolicy:
    value = plan.frame_rate_policy
    if isinstance(value, FrameRatePolicy):
        return value
    if isinstance(value, dict):
        try:
            return FrameRatePolicy.from_dict(value)
        except ValueError as error:
            raise ExportExecutionError(f"Enhanced export policy is invalid: {error}") from error
    if plan.output_policy is not None:
        try:
            target_rate = canonical_rate(plan.output_policy.frame_rate)
            return FrameRatePolicy(
                choice="custom",
                custom_rate=target_rate,
                target_rate=target_rate,
                enhancement_enabled=False,
                backend="ffmpeg-minterpolate",
            )
        except ValueError as error:
            raise ExportExecutionError(
                f"Enhanced export output frame rate is invalid: {error}",
            ) from error
    raise ExportExecutionError("Enhanced export is missing its frame-rate policy")


def _decision_by_id(plan: ExportPlan) -> dict[str, SourceRateDecision]:
    decisions: dict[str, SourceRateDecision] = {}
    for item in plan.rate_decisions:
        if isinstance(item, SourceRateDecision):
            decisions[item.source_id] = item
            continue
        try:
            decisions[item["source_id"]] = SourceRateDecision(
                source_id=item["source_id"],
                source_rate=canonical_rate(item["source_rate"]),
                target_rate=canonical_rate(item["target_rate"]),
                action=item["action"],
                eligible=bool(item["eligible"]),
                reason=item["reason"],
            )
        except (KeyError, TypeError, ValueError) as error:
            raise ExportExecutionError("Enhanced export rate decisions are invalid") from error
    return decisions


def _effective_decisions(
    plan: ExportPlan,
    probes: Sequence[MediaProbe],
) -> dict[str, SourceRateDecision]:
    decisions = _decision_by_id(plan)
    if decisions:
        return decisions
    policy = _policy(plan)
    source_ids = (
        plan.source_ids
        if plan.source_paths
        else (
            (
                plan.upscale_decisions[0].source_id
                if isinstance(plan.upscale_decisions[0], UpscaleDecision)
                else plan.upscale_decisions[0].get("source_id", "source")
            )
            if plan.upscale_decisions
            else "source",
        )
    )
    if len(source_ids) != len(probes):
        raise ExportExecutionError("Enhanced export source identities do not match probes")
    result: dict[str, SourceRateDecision] = {}
    for source_id, probe in zip(source_ids, probes, strict=True):
        source_rate = canonical_rate(probe.frame_rate)
        target_rate = policy.target_rate
        if source_rate == target_rate:
            action = "passthrough"
            reason = "source is already at the output frame rate"
        elif source_rate < target_rate:
            action = "convert"
            reason = "output frame rate conversion is required; FPS enhancement is disabled"
        else:
            action = "convert-down"
            reason = "output frame rate conversion is required"
        result[source_id] = SourceRateDecision(
            source_id=source_id,
            source_rate=source_rate,
            target_rate=target_rate,
            action=action,
            eligible=False,
            reason=reason,
        )
    return result


def _expected_frames(plan: ExportPlan) -> int:
    policy = _policy(plan)
    duration = Fraction(str(plan.expected_duration_seconds))
    exact = duration * policy.target_rate
    return max(
        1,
        (exact.numerator + exact.denominator // 2) // exact.denominator,
    )


def _interpolation_ranges(
    plan: ExportPlan,
    source_id: str,
    source_duration_seconds: float,
) -> tuple[tuple[float, float], ...] | None:
    if plan.source_paths:
        segments = tuple(segment for segment in plan.segments if segment.source_id == source_id)
    else:
        segments = plan.segments
    if not segments:
        return None
    boundaries = {0.0, source_duration_seconds}
    for segment in segments:
        boundaries.add(segment.start_seconds)
        boundaries.add(segment.end_seconds)
    ordered = sorted(boundaries)
    ranges = tuple(
        (start, end - start)
        for start, end in zip(ordered, ordered[1:], strict=False)
        if end > start
    )
    if len(ranges) <= 1:
        return None
    return ranges


def _forward_interpolation_progress(
    callback: ExportProgressCallback | None,
    progress: ExportProgress,
    *,
    stage: str,
    start_percent: float,
    end_percent: float,
) -> None:
    if callback is None:
        return
    local_fraction = max(0.0, min(1.0, progress.percent / 100.0))
    callback(
        replace(
            progress,
            stage=stage,
            percent=start_percent + (end_percent - start_percent) * local_fraction,
        )
    )


def can_publish_interpolated_source(
    plan: ExportPlan,
    source_probe: MediaProbe,
) -> bool:
    """Return whether interpolation already produced the complete output profile."""
    policy = plan.output_policy
    if (
        plan.source_paths
        or policy is None
        or plan.destination.suffix.casefold() != ".mp4"
        or len(plan.segments) != 1
        or not segment_is_full_source(plan.segments[0], source_probe.duration_seconds)
        or plan.segments[0].has_visual_modifications
        or policy.requires_normalization
        or policy.scaling_mode != "source-native"
        or (policy.width, policy.height) != (source_probe.width, source_probe.height)
        or policy.container.casefold() != "mp4"
        or policy.video_codec.casefold() != "libx264"
        or policy.pixel_format.casefold() != "yuv420p"
        or policy.audio_stream_present != source_probe.has_audio_stream
    ):
        return False
    if source_probe.has_audio_stream and (
        source_probe.audio_codec != "aac"
        or source_probe.audio_sample_rate != policy.audio_sample_rate
        or source_probe.audio_channels != policy.audio_channels
    ):
        return False
    for _source_id, decision in plan.audio_decisions:
        status = decision.status if hasattr(decision, "status") else decision.get("status")
        gain = decision.gain_db if hasattr(decision, "gain_db") else decision.get("gain_db", 0.0)
        if status not in {"not-applicable", "silent"} and (
            status != "ready"
            or not isinstance(gain, (int, float))
            or isinstance(gain, bool)
            or not math.isfinite(float(gain))
            or abs(float(gain)) >= 0.01
        ):
            return False
    return True


def _should_use_concat_first(
    plan: ExportPlan,
    source_probe: MediaProbe,
) -> bool:
    """Keep the historical selector explicit while defaulting to Strategy B."""
    return False


def _segment_target_frame_counts(
    segments: Sequence,
    target_rate: Fraction,
    total_frames: int,
) -> tuple[int, ...]:
    counts: list[int] = []
    cumulative = Fraction(0, 1)
    previous = 0
    for segment in segments:
        cumulative += Fraction(str(segment.duration_seconds)) * target_rate
        boundary = (cumulative.numerator + cumulative.denominator // 2) // cumulative.denominator
        counts.append(max(1, boundary - previous))
        previous = boundary
    while sum(counts) > total_frames:
        candidate = max(
            (index for index, count in enumerate(counts) if count > 1),
            key=lambda index: counts[index],
            default=None,
        )
        if candidate is None:
            break
        counts[candidate] -= 1
    if counts and sum(counts) < total_frames:
        counts[-1] += total_frames - sum(counts)
    return tuple(counts)


def _format_tokens(value: str) -> set[str]:
    return {token.strip().casefold() for token in value.split(",") if token.strip()}


def _stream_copy_compatible(
    probe: MediaProbe,
    policy: OutputPolicy,
) -> bool:
    video_codec_compatible = probe.video_codec.casefold() == policy.video_codec.casefold() or (
        policy.video_codec.casefold() == "libx264" and probe.video_codec.casefold() == "h264"
    )
    if (
        (probe.width, probe.height) != (policy.width, policy.height)
        or canonical_rate(probe.frame_rate) != canonical_rate(policy.frame_rate)
        or not video_codec_compatible
        or not _format_tokens(probe.format_name).intersection({"mp4", "mov"})
        or probe.has_audio_stream != policy.audio_stream_present
    ):
        return False
    if not policy.audio_stream_present:
        return True
    return (
        probe.audio_codec is not None
        and policy.audio_codec is not None
        and probe.audio_codec.casefold() == policy.audio_codec.casefold()
        and probe.audio_sample_rate == policy.audio_sample_rate
        and probe.audio_channels == policy.audio_channels
    )


def _stream_copy_join_is_valid(
    probe: MediaProbe,
    candidate: Path,
    policy: OutputPolicy,
    *,
    expected_duration_seconds: float,
    expected_frames: int,
    ffprobe_path: str,
) -> bool:
    if not _stream_copy_compatible(probe, policy):
        return False
    try:
        actual_frames = probe_frame_count(candidate, ffprobe_path)
        expected_rate = float(canonical_rate(policy.frame_rate))
    except ExportExecutionError:
        return False
    duration_tolerance = max(_DURATION_TOLERANCE, 2.0 / expected_rate)
    return (
        actual_frames == expected_frames
        and abs(probe.duration_seconds - expected_duration_seconds) <= duration_tolerance
    )


def _clip_concat_filter(
    probes: Sequence[MediaProbe],
    policy: OutputPolicy,
) -> str:
    filters: list[str] = []
    inputs: list[str] = []
    for index, probe in enumerate(probes):
        video_label = f"[v{index}]"
        filters.append(f"[{index}:v:0]fps={policy.frame_rate},setpts=PTS-STARTPTS{video_label}")
        inputs.append(video_label)
        if policy.audio_stream_present:
            audio_label = f"[a{index}]"
            if probe.has_audio_stream:
                filters.append(f"[{index}:a:0]asetpts=PTS-STARTPTS{audio_label}")
            else:
                filters.append(
                    f"anullsrc=channel_layout=stereo:sample_rate={policy.audio_sample_rate},"
                    f"atrim=duration={probe.duration_seconds:.6f},"
                    f"asetpts=PTS-STARTPTS{audio_label}"
                )
            inputs.append(audio_label)
    audio_count = 1 if policy.audio_stream_present else 0
    return (
        ";".join(filters)
        + ";"
        + "".join(inputs)
        + f"concat=n={len(probes)}:v=1:a={audio_count}[outv]"
        + ("" if not policy.audio_stream_present else "[outa]")
    )


def _execute_clip_concat_fallback(
    paths: Sequence[Path],
    probes: Sequence[MediaProbe],
    policy: OutputPolicy,
    partial: Path,
    *,
    ffmpeg_path: str,
    progress_callback: ExportProgressCallback | None,
    started: float,
    expected_duration_seconds: float,
    total_frames: int,
    cancel_event: threading.Event | None,
) -> None:
    command = [
        ffmpeg_path,
        "-hide_banner",
        "-loglevel",
        "error",
        "-nostdin",
        *sum((["-i", str(path)] for path in paths), []),
        "-filter_complex",
        _clip_concat_filter(probes, policy),
        "-map",
        "[outv]",
        "-r",
        policy.frame_rate,
        "-fps_mode",
        "cfr",
        "-c:v",
        policy.video_codec,
        "-preset",
        "medium",
        "-crf",
        "18",
        "-pix_fmt",
        policy.pixel_format,
    ]
    if policy.audio_stream_present:
        command.extend(
            [
                "-map",
                "[outa]",
                "-c:a",
                policy.audio_codec or "aac",
                "-b:a",
                "192k",
                "-ar",
                str(policy.audio_sample_rate),
                "-ac",
                str(policy.audio_channels),
            ]
        )
    command.extend(
        [
            "-t",
            f"{expected_duration_seconds:.6f}",
            "-movflags",
            "+faststart",
            "-shortest",
            "-avoid_negative_ts",
            "make_zero",
            "-f",
            policy.container,
            str(partial),
        ]
    )
    run_ffmpeg(
        command,
        progress_callback=(
            bind_partial(
                _forward_interpolation_progress,
                progress_callback,
                stage="composing enhanced segments",
                start_percent=90.0,
                end_percent=95.0,
            )
            if progress_callback is not None
            else None
        ),
        stage="composing enhanced segments",
        command_duration_seconds=expected_duration_seconds,
        progress_total_duration_seconds=expected_duration_seconds,
        command_total_frames=total_frames,
        progress_total_frames=total_frames,
        started=started,
        cancel_event=cancel_event,
    )


def _prepare_video_only_assembly_inputs(
    paths: Sequence[Path],
    probes: Sequence[MediaProbe],
    policy: OutputPolicy,
    temporary: Path,
    *,
    ffmpeg_path: str,
    ffprobe_path: str,
    progress_callback: ExportProgressCallback | None,
    started: float,
    expected_duration_seconds: float,
    total_frames: int,
    cancel_event: threading.Event | None,
) -> tuple[tuple[Path, ...], tuple[MediaProbe, ...]]:
    if policy.audio_stream_present or not any(probe.has_audio_stream for probe in probes):
        return tuple(paths), tuple(probes)
    prepared_paths: list[Path] = []
    prepared_probes: list[MediaProbe] = []
    total_segments = len(paths)
    progress_offset = 0.0
    for index, (path, probe) in enumerate(zip(paths, probes, strict=True)):
        if cancel_event is not None and cancel_event.is_set():
            raise ExportExecutionError("Export cancelled")
        if not probe.has_audio_stream:
            prepared_paths.append(path)
            prepared_probes.append(probe)
            progress_offset += probe.duration_seconds
            continue
        destination = temporary / f"video-only-segment-{index}.mp4"
        partial = partial_path(destination)
        command = build_video_only_copy_command(
            path,
            partial,
            ffmpeg_path=ffmpeg_path,
        )
        stage_start = 90.0 + 2.0 * index / total_segments
        stage_end = 90.0 + 2.0 * (index + 1) / total_segments
        try:
            run_ffmpeg(
                command,
                progress_callback=(
                    bind_partial(
                        _forward_interpolation_progress,
                        progress_callback,
                        stage=f"preparing video-only segment {index + 1}/{total_segments}",
                        start_percent=stage_start,
                        end_percent=stage_end,
                    )
                    if progress_callback is not None
                    else None
                ),
                stage=f"preparing video-only segment {index + 1}/{total_segments}",
                command_duration_seconds=probe.duration_seconds,
                progress_offset_seconds=progress_offset,
                progress_total_duration_seconds=expected_duration_seconds,
                command_total_frames=total_frames,
                progress_total_frames=total_frames,
                started=started,
                cancel_event=cancel_event,
            )
            if not partial.is_file() or partial.stat().st_size <= 0:
                raise ExportExecutionError(
                    f"Video-only preparation did not create segment {index + 1}"
                )
            os.replace(partial, destination)
            try:
                prepared_probe = probe_media(destination, ffprobe_path)
            except MediaProbeError as error:
                raise ExportExecutionError(
                    f"Video-only segment {index + 1} could not be inspected: {error}"
                ) from error
            prepared_paths.append(destination)
            prepared_probes.append(prepared_probe)
        finally:
            partial.unlink(missing_ok=True)
        progress_offset += probe.duration_seconds
    return tuple(prepared_paths), tuple(prepared_probes)


def _execute_enhanced_clip_assembly(
    paths: Sequence[Path],
    probes: Sequence[MediaProbe],
    policy: OutputPolicy,
    partial: Path,
    temporary: Path,
    *,
    ffmpeg_path: str,
    ffprobe_path: str,
    progress_callback: ExportProgressCallback | None,
    started: float,
    expected_duration_seconds: float,
    total_frames: int,
    cancel_event: threading.Event | None,
) -> None:
    if not paths:
        raise ExportExecutionError("Enhanced export produced no retained segments")
    assembly_paths, assembly_probes = _prepare_video_only_assembly_inputs(
        paths,
        probes,
        policy,
        temporary,
        ffmpeg_path=ffmpeg_path,
        ffprobe_path=ffprobe_path,
        progress_callback=progress_callback,
        started=started,
        expected_duration_seconds=expected_duration_seconds,
        total_frames=total_frames,
        cancel_event=cancel_event,
    )
    if len(assembly_paths) == 1:
        if assembly_paths[0].parent == temporary:
            os.replace(assembly_paths[0], partial)
        else:
            try:
                shutil.copyfile(assembly_paths[0], partial)
            except OSError as error:
                raise ExportExecutionError("Could not copy the enhanced output") from error
        return
    if all(_stream_copy_compatible(probe, policy) for probe in assembly_probes):
        list_path = temporary / "enhanced-segments-list.txt"
        _write_concat_list(assembly_paths, list_path)
        command = build_concat_copy_command(
            list_path,
            partial,
            has_audio=policy.audio_stream_present,
            ffmpeg_path=ffmpeg_path,
        )
        run_ffmpeg(
            command,
            progress_callback=(
                bind_partial(
                    _forward_interpolation_progress,
                    progress_callback,
                    stage="concatenating enhanced segments",
                    start_percent=90.0,
                    end_percent=95.0,
                )
                if progress_callback is not None
                else None
            ),
            stage="concatenating enhanced segments",
            command_duration_seconds=expected_duration_seconds,
            progress_total_duration_seconds=expected_duration_seconds,
            command_total_frames=total_frames,
            progress_total_frames=total_frames,
            started=started,
            cancel_event=cancel_event,
        )
        try:
            joined_probe = probe_media(partial, ffprobe_path)
        except MediaProbeError:
            partial.unlink(missing_ok=True)
        else:
            if _stream_copy_join_is_valid(
                joined_probe,
                partial,
                policy,
                expected_duration_seconds=expected_duration_seconds,
                expected_frames=total_frames,
                ffprobe_path=ffprobe_path,
            ):
                return
            partial.unlink(missing_ok=True)
    _execute_clip_concat_fallback(
        assembly_paths,
        assembly_probes,
        policy,
        partial,
        ffmpeg_path=ffmpeg_path,
        progress_callback=progress_callback,
        started=started,
        expected_duration_seconds=expected_duration_seconds,
        total_frames=total_frames,
        cancel_event=cancel_event,
    )


def _execute_per_source_enhanced_render(
    plan: ExportPlan,
    original_probes: Sequence[MediaProbe],
    decisions: dict[str, SourceRateDecision],
    *,
    temporary: Path,
    partial: Path,
    policy: FrameRatePolicy,
    options: dict[str, object],
    ffmpeg_path: str,
    ffprobe_path: str,
    progress_callback: ExportProgressCallback | None,
    started: float,
    total_frames: int,
    cancel_event: threading.Event | None,
) -> None:
    prepared_sources = prepare_enhanced_sources(
        plan,
        original_probes,
        decisions,
        temporary,
        ffmpeg_path=ffmpeg_path,
        ffprobe_path=ffprobe_path,
        progress_callback=progress_callback,
        started=started,
        cancel_event=cancel_event,
        backend_kwargs=options,
    )
    active_segments = tuple(segment for segment in plan.segments if not segment.deleted)
    if len(prepared_sources) != len(active_segments):
        raise ExportExecutionError("Enhanced source preparation changed the timeline")
    target_frames = _segment_target_frame_counts(
        active_segments,
        policy.target_rate,
        total_frames,
    )
    enhanced_paths: list[Path] = []
    enhanced_probes: list[MediaProbe] = []
    total_segments = len(prepared_sources)
    for index, prepared in enumerate(prepared_sources):
        if cancel_event is not None and cancel_event.is_set():
            raise ExportExecutionError("Export cancelled")
        decision = decisions.get(prepared.source_id)
        if decision is None:
            raise ExportExecutionError(
                f"Enhanced export has no rate decision for source {prepared.source_id}"
            )
        if decision.action == "interpolate":
            stage = f"interpolation segment {index + 1}/{total_segments}"
            stage_start = 30.0 + 60.0 * index / total_segments
            stage_end = 30.0 + 60.0 * (index + 1) / total_segments
            emit_export_progress(
                progress_callback,
                stage=stage,
                current_seconds=0.0,
                total_duration_seconds=plan.expected_duration_seconds,
                frame=0,
                total_frames=total_frames,
                fps=None,
                started=started,
                percent_override=stage_start,
            )
            interpolated = _interpolate_probe(
                prepared.probe,
                source_id=prepared.source_id,
                decision=decision,
                destination=temporary / f"enhanced-segment-{index}.mp4",
                ffprobe_path=ffprobe_path,
                ffmpeg_path=ffmpeg_path,
                backend_kwargs=dict(options),
                target_frames=target_frames[index],
                ranges=None,
                cancel_event=cancel_event,
                progress_callback=(
                    bind_partial(
                        _forward_interpolation_progress,
                        progress_callback,
                        stage=stage,
                        start_percent=stage_start,
                        end_percent=stage_end,
                    )
                    if progress_callback is not None
                    else None
                ),
                progress_stage=stage,
                progress_started=started,
            )
            enhanced_paths.append(interpolated.path)
            enhanced_probes.append(interpolated)
            emit_export_progress(
                progress_callback,
                stage=stage,
                current_seconds=0.0,
                total_duration_seconds=plan.expected_duration_seconds,
                frame=0,
                total_frames=total_frames,
                fps=None,
                started=started,
                percent_override=stage_end,
            )
            continue
        if decision.action not in {"passthrough", "convert", "convert-down"}:
            raise ExportExecutionError(
                f"Enhanced export action is unsupported for source {prepared.source_id}"
            )
        if canonical_rate(prepared.probe.frame_rate) != policy.target_rate:
            raise ExportExecutionError(
                f"Prepared source {prepared.source_id} is not at the target frame rate"
            )
        enhanced_paths.append(prepared.path)
        enhanced_probes.append(prepared.probe)

    output_policy = plan.output_policy
    if output_policy is None:
        raise ExportExecutionError("Enhanced export is missing its output policy")
    _execute_enhanced_clip_assembly(
        enhanced_paths,
        enhanced_probes,
        output_policy,
        partial,
        temporary,
        ffmpeg_path=ffmpeg_path,
        ffprobe_path=ffprobe_path,
        progress_callback=progress_callback,
        started=started,
        expected_duration_seconds=plan.expected_duration_seconds,
        total_frames=total_frames,
        cancel_event=cancel_event,
    )
    emit_export_progress(
        progress_callback,
        stage="publishing interpolated output",
        current_seconds=plan.expected_duration_seconds,
        total_duration_seconds=plan.expected_duration_seconds,
        frame=total_frames,
        total_frames=total_frames,
        fps=None,
        started=started,
        percent_override=95.0,
    )


def _execute_concat_first_enhanced_render(
    plan: ExportPlan,
    original_probes: Sequence[MediaProbe],
    *,
    temporary: Path,
    partial: Path,
    policy: FrameRatePolicy,
    options: dict[str, object],
    ffmpeg_path: str,
    ffprobe_path: str,
    progress_callback: ExportProgressCallback | None,
    started: float,
    total_frames: int,
    cancel_event: threading.Event | None,
) -> None:
    master = prepare_enhanced_master(
        plan,
        original_probes,
        temporary,
        ffmpeg_path=ffmpeg_path,
        ffprobe_path=ffprobe_path,
        progress_callback=progress_callback,
        started=started,
        cancel_event=cancel_event,
    )
    if master.base_rate >= policy.target_rate:
        raise ExportExecutionError(
            "Enhanced export target rate must be above the prepared master rate"
        )
    decision = SourceRateDecision(
        source_id="prepared-master",
        source_rate=master.base_rate,
        target_rate=policy.target_rate,
        action="interpolate",
        eligible=True,
        reason="prepared master uses the slowest selected input frame rate",
    )
    stage = "interpolation master"
    emit_export_progress(
        progress_callback,
        stage=stage,
        current_seconds=0.0,
        total_duration_seconds=plan.expected_duration_seconds,
        frame=0,
        total_frames=total_frames,
        fps=None,
        started=started,
        percent_override=35.0,
    )
    interpolated = _interpolate_probe(
        master.probe,
        source_id=decision.source_id,
        decision=decision,
        destination=temporary / "enhanced-master.mp4",
        ffprobe_path=ffprobe_path,
        ffmpeg_path=ffmpeg_path,
        backend_kwargs=dict(options),
        target_frames=total_frames,
        ranges=None,
        cancel_event=cancel_event,
        progress_callback=(
            bind_partial(
                _forward_interpolation_progress,
                progress_callback,
                stage=stage,
                start_percent=35.0,
                end_percent=95.0,
            )
            if progress_callback is not None
            else None
        ),
        progress_stage=stage,
        progress_started=started,
    )
    os.replace(interpolated.path, partial)
    emit_export_progress(
        progress_callback,
        stage="publishing interpolated output",
        current_seconds=plan.expected_duration_seconds,
        total_duration_seconds=plan.expected_duration_seconds,
        frame=total_frames,
        total_frames=total_frames,
        fps=None,
        started=started,
        percent_override=95.0,
    )


def _execute_legacy_enhanced_render(
    plan: ExportPlan,
    original_probes: Sequence[MediaProbe],
    decisions: dict[str, SourceRateDecision],
    *,
    temporary: Path,
    partial: Path,
    options: dict[str, object],
    ffmpeg_path: str,
    ffprobe_path: str,
    progress_callback: ExportProgressCallback | None,
    started: float,
    total_frames: int,
    cancel_event: threading.Event | None,
) -> None:
    prepared_probes: list[MediaProbe] = []
    for index, probe in enumerate(original_probes):
        if cancel_event is not None and cancel_event.is_set():
            raise ExportExecutionError("Export cancelled")
        source_id = (
            plan.source_ids[index]
            if plan.source_ids
            else next(
                (
                    item.source_id
                    for item in decisions.values()
                    if item.source_rate == canonical_rate(probe.frame_rate)
                ),
                "source",
            )
        )
        decision = decisions.get(source_id)
        if decision is None:
            decision = next(
                (
                    item
                    for item in decisions.values()
                    if item.source_rate == canonical_rate(probe.frame_rate)
                ),
                None,
            )
        if decision is None:
            raise ExportExecutionError(
                f"Enhanced export has no rate decision for source {source_id}"
            )
        if decision.action == "interpolate":
            ranges = _interpolation_ranges(
                plan,
                source_id,
                probe.duration_seconds,
            )
            stage = f"interpolation {index + 1}/{len(original_probes)}"
            stage_start_percent = 5.0 + 40.0 * index / len(original_probes)
            stage_end_percent = 5.0 + 40.0 * (index + 1) / len(original_probes)
            emit_export_progress(
                progress_callback,
                stage=stage,
                current_seconds=0.0,
                total_duration_seconds=plan.expected_duration_seconds,
                frame=0,
                total_frames=total_frames,
                fps=None,
                started=started,
                percent_override=stage_start_percent,
            )
            interpolated = _interpolate_probe(
                probe,
                source_id=source_id,
                decision=decision,
                destination=temporary / f"source-{index}.mp4",
                ffprobe_path=ffprobe_path,
                ffmpeg_path=ffmpeg_path,
                backend_kwargs=dict(options),
                ranges=ranges,
                cancel_event=cancel_event,
                progress_callback=(
                    bind_partial(
                        _forward_interpolation_progress,
                        progress_callback,
                        stage=stage,
                        start_percent=stage_start_percent,
                        end_percent=stage_end_percent,
                    )
                    if progress_callback is not None
                    else None
                ),
                progress_stage=stage,
                progress_started=started,
            )
            prepared_probes.append(interpolated)
            emit_export_progress(
                progress_callback,
                stage=stage,
                current_seconds=0.0,
                total_duration_seconds=plan.expected_duration_seconds,
                frame=0,
                total_frames=total_frames,
                fps=None,
                started=started,
                percent_override=stage_end_percent,
            )
        else:
            prepared_probes.append(probe)

    if (
        not plan.source_paths
        and len(original_probes) == 1
        and can_publish_interpolated_source(plan, original_probes[0])
    ):
        os.replace(prepared_probes[0].path, partial)
        emit_export_progress(
            progress_callback,
            stage="publishing interpolated output",
            current_seconds=plan.expected_duration_seconds,
            total_duration_seconds=plan.expected_duration_seconds,
            frame=total_frames,
            total_frames=total_frames,
            fps=None,
            started=started,
            percent_override=90.0,
        )
    elif plan.source_paths:
        prepared_plan = replace(
            plan,
            route="fallback",
            source=prepared_probes[0].path,
            source_paths=tuple(probe.path for probe in prepared_probes),
        )
        execute_mixed_fallback(
            prepared_plan,
            prepared_probes,
            partial,
            ffmpeg_path,
            progress_callback=progress_callback,
            started=started,
            cancel_event=cancel_event,
        )
    else:
        prepared_plan = replace(
            plan,
            route="fallback",
            source=prepared_probes[0].path,
            source_paths=(),
        )
        execute_fallback(
            prepared_plan,
            prepared_probes[0],
            partial,
            ffmpeg_path,
            progress_callback=progress_callback,
            started=started,
            cancel_event=cancel_event,
        )


def _interpolate_probe(
    probe: MediaProbe,
    *,
    source_id: str,
    decision: SourceRateDecision,
    destination: Path,
    ffprobe_path: str,
    ffmpeg_path: str,
    backend_kwargs: dict[str, object],
    target_frames: int | None = None,
    ranges: Sequence[tuple[float, float]] | None,
    cancel_event: threading.Event | None = None,
    progress_callback: ExportProgressCallback | None = None,
    progress_stage: str = "interpolation",
    progress_started: float | None = None,
) -> MediaProbe:
    if cancel_event is not None and cancel_event.is_set():
        raise ExportExecutionError("Export cancelled")
    source_frames = probe_frame_count(probe.path, ffprobe_path)
    if target_frames is None:
        target_frames = target_frame_count(
            decision.source_rate,
            source_frames,
            decision.target_rate,
        )
    elif (
        isinstance(target_frames, bool) or not isinstance(target_frames, int) or target_frames <= 0
    ):
        raise ExportExecutionError("Interpolation target frame count must be positive")
    backend = backend_kwargs.pop("backend", "rve-4.26")
    if not isinstance(backend, str):
        raise ExportExecutionError("Interpolation backend must be a string")
    run_source_interpolation(
        probe.path,
        destination,
        source_rate=decision.source_rate,
        source_frames=source_frames,
        target_rate=decision.target_rate,
        target_frames=target_frames,
        backend=backend,
        ffmpeg_path=ffmpeg_path,
        cancel_event=cancel_event,
        ranges=ranges,
        progress_callback=progress_callback,
        progress_stage=progress_stage,
        progress_started=progress_started,
        **backend_kwargs,
    )
    try:
        interpolated_probe = probe_media(destination, ffprobe_path)
    except MediaProbeError as error:
        raise ExportExecutionError(
            f"Interpolated source {source_id} could not be inspected: {error}"
        ) from error
    run_artifact_gate(
        destination,
        target_frames,
        ffmpeg_path=ffmpeg_path,
        label=f"interpolated source {source_id}",
    )
    return interpolated_probe


def execute_enhanced_export(
    plan: ExportPlan,
    *,
    ffmpeg_path: str,
    ffprobe_path: str,
    progress_callback: ExportProgressCallback | None,
    verify_single_output: VerifySingle,
    verify_mixed_output: VerifyMixed,
    backend_kwargs: dict[str, object] | None = None,
    cancel_event: threading.Event | None = None,
    cancellation_lock: threading.Lock | None = None,
) -> Path:
    if plan.route != "enhanced":
        raise ExportExecutionError("Enhanced export requires the enhanced route")
    policy = _policy(plan)
    destination = plan.destination.expanduser()
    source_paths = (
        tuple(path.expanduser().resolve() for path in plan.source_paths)
        if plan.source_paths
        else (plan.source.expanduser().resolve(),)
    )
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
    except OSError as error:
        raise ExportExecutionError(f"Could not prepare enhanced export: {error}") from error
    source_stats, original_probes = prepare_export_sources(
        source_paths,
        ffprobe_path,
        label="enhanced export",
    )
    decisions = _effective_decisions(plan, original_probes)
    has_upscale = any(
        item.eligible for item in plan.upscale_decisions if isinstance(item, UpscaleDecision)
    ) or any(
        isinstance(item, dict) and bool(item.get("eligible")) for item in plan.upscale_decisions
    )
    if not any(item.action == "interpolate" for item in decisions.values()) and not has_upscale:
        raise ExportExecutionError("Enhanced export has no eligible source ranges")
    started = time.monotonic()
    total_frames = _expected_frames(plan)
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
    options = dict(backend_kwargs or {})
    options.setdefault("backend", policy.backend)
    try:
        with tempfile.TemporaryDirectory(
            prefix=f".{destination.name}.interpolation-",
            dir=str(destination.parent),
        ) as temporary_directory:
            temporary = Path(temporary_directory)
            if _should_use_concat_first(plan, original_probes[0]):
                _execute_concat_first_enhanced_render(
                    plan,
                    original_probes,
                    temporary=temporary,
                    partial=partial,
                    policy=policy,
                    options=options,
                    ffmpeg_path=ffmpeg_path,
                    ffprobe_path=ffprobe_path,
                    progress_callback=progress_callback,
                    started=started,
                    total_frames=total_frames,
                    cancel_event=cancel_event,
                )
            else:
                _execute_per_source_enhanced_render(
                    plan,
                    original_probes,
                    decisions,
                    temporary=temporary,
                    partial=partial,
                    policy=policy,
                    options=options,
                    ffmpeg_path=ffmpeg_path,
                    ffprobe_path=ffprobe_path,
                    progress_callback=progress_callback,
                    started=started,
                    total_frames=total_frames,
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
        if plan.source_paths:
            verify_mixed_output(
                plan,
                partial,
                ffmpeg_path=ffmpeg_path,
                ffprobe_path=ffprobe_path,
            )
        else:
            verify_single_output(
                plan,
                original_probes[0],
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


__all__ = [
    "can_publish_interpolated_source",
    "execute_enhanced_export",
    "probe_frame_count",
]
