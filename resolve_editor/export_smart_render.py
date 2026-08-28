from __future__ import annotations

import math
import os
import shutil
import threading
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from fractions import Fraction
from pathlib import Path
from typing import Any

from .audio import AudioDecision, audio_filter
from .composition_render import segment_video_filters
from .export_process import (
    output_format,
    partial_path,
    run_ffmpeg,
    segment_is_full_source,
)
from .export_types import (
    _BOUNDARY_TOLERANCE,
    ExportExecutionError,
    ExportPlan,
    ExportPlanningError,
    ExportProgress,
    ExportProgressCallback,
    OutputPolicy,
)
from .fps_policy import SourceRateDecision, canonical_rate
from .media import MediaProbe, MediaProbeError, probe_media
from .model import Segment
from .upscale_policy import (
    DEFAULT_UPSCALE_MODEL,
    UpscaleDecision,
    UpscalePolicy,
)


@dataclass(frozen=True)
class PreparedMaster:
    path: Path
    probe: MediaProbe
    base_rate: Fraction


@dataclass(frozen=True)
class PreparedSource:
    source_id: str
    segment_index: int
    path: Path
    probe: MediaProbe
    source_rate: Fraction


def _scaled_progress_callback(
    callback: ExportProgressCallback | None,
    *,
    start_percent: float,
    end_percent: float,
) -> ExportProgressCallback | None:
    if callback is None:
        return None

    def forward(progress: ExportProgress) -> None:
        fraction = max(0.0, min(1.0, progress.percent / 100.0))
        callback(
            replace(
                progress,
                percent=start_percent + (end_percent - start_percent) * fraction,
            )
        )

    return forward


def _rate_expression(rate: Fraction | int | float | str) -> str:
    value = canonical_rate(rate)
    return f"{value.numerator}/{value.denominator}"


def _seconds(value: float, label: str, *, positive: bool = False) -> str:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ExportExecutionError(f"{label} must be a finite number")
    parsed = float(value)
    if not math.isfinite(parsed) or parsed < 0 or (positive and parsed <= 0):
        requirement = "greater than zero" if positive else "finite and non-negative"
        raise ExportExecutionError(f"{label} must be {requirement}")
    return f"{parsed:.6f}"


def build_lossless_cut_command(
    source: Path,
    destination: Path,
    *,
    start_seconds: float,
    duration_seconds: float,
    has_audio: bool,
    ffmpeg_path: str = "ffmpeg",
) -> list[str]:
    command = [
        ffmpeg_path,
        "-hide_banner",
        "-loglevel",
        "error",
        "-nostdin",
        "-y",
        "-ss",
        _seconds(start_seconds, "Cut start"),
        "-i",
        str(source),
        "-t",
        _seconds(duration_seconds, "Cut duration", positive=True),
        "-map",
        "0:v:0",
    ]
    if has_audio:
        command.extend(["-map", "0:a:0"])
    command.extend(
        [
            "-c",
            "copy",
            "-avoid_negative_ts",
            "make_zero",
            "-f",
            output_format(destination),
            str(destination),
        ]
    )
    return command


def build_concat_copy_command(
    list_path: Path,
    destination: Path,
    *,
    has_audio: bool,
    ffmpeg_path: str = "ffmpeg",
) -> list[str]:
    command = [
        ffmpeg_path,
        "-hide_banner",
        "-loglevel",
        "error",
        "-nostdin",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(list_path),
        "-map",
        "0:v:0",
    ]
    if has_audio:
        command.extend(["-map", "0:a:0"])
    command.extend(
        [
            "-c",
            "copy",
            "-avoid_negative_ts",
            "make_zero",
            "-movflags",
            "+faststart",
            "-f",
            output_format(destination),
            str(destination),
        ]
    )
    return command


def build_video_only_copy_command(
    source: Path,
    destination: Path,
    *,
    ffmpeg_path: str = "ffmpeg",
) -> list[str]:
    return [
        ffmpeg_path,
        "-hide_banner",
        "-loglevel",
        "error",
        "-nostdin",
        "-y",
        "-i",
        str(source),
        "-map",
        "0:v:0",
        "-an",
        "-c:v",
        "copy",
        "-avoid_negative_ts",
        "make_zero",
        "-movflags",
        "+faststart",
        "-f",
        output_format(destination),
        str(destination),
    ]


def _decision_status_and_gain(
    decision: AudioDecision | Mapping[str, Any] | None,
) -> tuple[str, float]:
    if isinstance(decision, AudioDecision):
        return decision.status, decision.gain_db
    if isinstance(decision, Mapping):
        status = decision.get("status")
        gain = decision.get("gain_db", 0.0)
        normalized_status = status if isinstance(status, str) else "not-applicable"
        normalized_gain = (
            float(gain) if isinstance(gain, (int, float)) and not isinstance(gain, bool) else 0.0
        )
        return normalized_status, normalized_gain
    return "not-applicable", 0.0


def _format_audio_decision(
    decision: AudioDecision | Mapping[str, Any] | None,
) -> AudioDecision | Mapping[str, Any] | None:
    return decision


def _upscale_policy(plan: ExportPlan) -> UpscalePolicy | None:
    value = plan.upscale_policy
    if value is None:
        return None
    if isinstance(value, UpscalePolicy):
        return value
    try:
        return UpscalePolicy.from_dict(value)
    except (TypeError, ValueError) as error:
        raise ExportExecutionError(
            f"Enhanced export upscale policy is invalid: {error}",
        ) from error


def _upscale_decisions(plan: ExportPlan) -> dict[str, UpscaleDecision]:
    decisions: dict[str, UpscaleDecision] = {}
    for item in plan.upscale_decisions:
        if isinstance(item, UpscaleDecision):
            decisions[item.source_id] = item
            continue
        try:
            decisions[item["source_id"]] = UpscaleDecision(
                source_id=item["source_id"],
                source_width=int(item["source_width"]),
                source_height=int(item["source_height"]),
                orientation=item["orientation"],
                source_short_side=int(item["source_short_side"]),
                target_width=int(item["target_width"]),
                target_height=int(item["target_height"]),
                action=item["action"],
                eligible=bool(item["eligible"]),
                reason=item["reason"],
                model=item.get("model"),
            )
        except (KeyError, TypeError, ValueError) as error:
            raise ExportExecutionError("Enhanced export upscale decisions are invalid") from error
    return decisions


def _restoration_arguments(
    backend_kwargs: Mapping[str, object],
    *,
    policy: UpscalePolicy,
    model: str,
):
    import argparse

    from resolve_fps import (
        DEFAULT_FPS_PYTHON,
        DEFAULT_FPS_SITE,
        DEFAULT_RVE_ROOT,
        DEFAULT_RVE_SHIMS,
    )

    backend = policy.backend.casefold().strip()
    if not backend.startswith("rve"):
        raise ExportExecutionError(
            f"Upscale backend {policy.backend!r} is not supported; "
            "the production path requires the validated RVE runtime",
        )
    return argparse.Namespace(
        force=True,
        python=backend_kwargs.get("fps_python", DEFAULT_FPS_PYTHON),
        site_packages=backend_kwargs.get("site_packages", DEFAULT_FPS_SITE),
        rve_root=backend_kwargs.get("rve_root", DEFAULT_RVE_ROOT),
        rve_shims=backend_kwargs.get("rve_shims", DEFAULT_RVE_SHIMS),
        encoder=backend_kwargs.get("encoder", "h264_nvenc"),
        restoration_model=model,
    )


def _run_source_restoration(
    probe: MediaProbe,
    destination: Path,
    *,
    policy: UpscalePolicy,
    model: str,
    backend_kwargs: Mapping[str, object],
    ffprobe_path: str,
    cancel_event: threading.Event | None,
) -> MediaProbe:
    from resolve_fps import (
        DEFAULT_RVE_RESTORATION_MODEL,
        probe_video,
        run_restoration_rve,
    )

    source_rate, source_frames = probe_video(probe.path)
    model_path = (
        DEFAULT_RVE_RESTORATION_MODEL
        if model.casefold() == DEFAULT_UPSCALE_MODEL.casefold()
        else Path(model)
    )
    arguments = _restoration_arguments(
        backend_kwargs,
        policy=policy,
        model=model,
    )
    try:
        run_restoration_rve(
            probe.path,
            destination,
            source_rate,
            source_frames,
            arguments,
            restoration_model=model_path,
            cancel_event=cancel_event,
        )
    except (OSError, RuntimeError) as error:
        raise ExportExecutionError(
            f"Upscale restoration backend {policy.backend!r} failed: {error}",
        ) from error
    try:
        restored = probe_media(destination, ffprobe_path)
    except MediaProbeError as error:
        raise ExportExecutionError(
            f"Restored source could not be inspected: {error}",
        ) from error
    if canonical_rate(restored.frame_rate) != source_rate:
        raise ExportExecutionError("Upscale restoration changed the source frame rate")
    if (restored.width, restored.height) != (probe.width, probe.height):
        raise ExportExecutionError("Upscale restoration changed the source dimensions")
    return restored


def _rounded_frame_count(exact: Fraction) -> int:
    return max(
        0,
        (exact.numerator + exact.denominator // 2) // exact.denominator,
    )


def _segment_frame_count(duration_seconds: float, rate: Fraction) -> int:
    return max(1, _rounded_frame_count(Fraction(str(duration_seconds)) * rate))


def _segment_frame_counts(
    segments: Sequence[Segment],
    rate: Fraction,
) -> tuple[int, ...]:
    """Allocate frames from cumulative boundaries without losing segment time."""
    counts: list[int] = []
    cumulative = Fraction(0, 1)
    previous_boundary = 0
    for segment in segments:
        cumulative += Fraction(str(segment.duration_seconds)) * rate
        boundary = _rounded_frame_count(cumulative)
        counts.append(boundary - previous_boundary)
        previous_boundary = boundary

    target_total = max(len(counts), _rounded_frame_count(cumulative))
    for index, count in enumerate(counts):
        counts[index] = max(1, count)
    excess = sum(counts) - target_total
    while excess > 0:
        candidate = max(
            (index for index, count in enumerate(counts) if count > 1),
            key=lambda index: counts[index],
            default=None,
        )
        if candidate is None:
            break
        counts[candidate] -= 1
        excess -= 1
    return tuple(counts)


def build_source_normalization_command(
    source: Path,
    destination: Path,
    segments: Sequence[Segment],
    *,
    target_rate: Fraction | int | float | str,
    policy: OutputPolicy,
    audio_decision: AudioDecision | Mapping[str, Any] | None,
    has_audio: bool,
    ffmpeg_path: str = "ffmpeg",
    preserve_resolution: bool = False,
    content_width: int | None = None,
    content_height: int | None = None,
) -> list[str]:
    if not segments:
        raise ExportExecutionError("Source normalization requires at least one segment")
    rate = _rate_expression(target_rate)
    frame_counts = _segment_frame_counts(segments, canonical_rate(target_rate))
    filters: list[str] = []
    video_labels: list[str] = []
    for index, segment in enumerate(segments):
        if segment.deleted:
            raise ExportExecutionError("Deleted segments cannot be normalized")
        output_label = f"[v{index}]"
        video_filters = segment_video_filters(
            "[0:v:0]",
            segment,
            policy.width,
            policy.height,
            output_label,
            frame_rate=rate,
            preserve_resolution=preserve_resolution,
            content_width=content_width,
            content_height=content_height,
        )
        if not video_filters[-1].endswith(output_label):
            raise ExportExecutionError("Source normalization video filter has no output label")
        video_filters[-1] = (
            video_filters[-1][: -len(output_label)] + f",trim=end_frame={frame_counts[index]},"
            f"setpts=PTS-STARTPTS{output_label}"
        )
        filters.extend(video_filters)
        video_labels.append(output_label)

    audio_labels: list[str] = []
    if policy.audio_stream_present:
        if has_audio:
            normalized_audio = "[normalized_audio]"
            filters.append(
                f"[0:a:0]{audio_filter(_format_audio_decision(audio_decision))}{normalized_audio}"
            )
            if len(segments) == 1:
                audio_labels.append(normalized_audio)
            else:
                split_labels = [f"[normalized_audio_{index}]" for index in range(len(segments))]
                filters.append(
                    f"{normalized_audio}asplit={len(split_labels)}{''.join(split_labels)}"
                )
                audio_labels.extend(split_labels)
        else:
            for index, segment in enumerate(segments):
                filters.append(
                    f"anullsrc=channel_layout=stereo:sample_rate={policy.audio_sample_rate},"
                    f"atrim=duration={segment.duration_seconds:.6f},"
                    f"asetpts=PTS-STARTPTS[a{index}]"
                )
                audio_labels.append(f"[a{index}]")

    if policy.audio_stream_present:
        for index, (_video_label, audio_label) in enumerate(
            zip(video_labels, audio_labels, strict=True)
        ):
            filters.append(
                f"{audio_label}atrim=start={segments[index].start_seconds:.6f}:"
                f"duration={segments[index].duration_seconds:.6f},"
                f"asetpts=PTS-STARTPTS[aout_{index}]"
            )
            audio_labels[index] = f"[aout_{index}]"
        filters.append(
            "".join(
                f"{video_labels[index]}{audio_labels[index]}" for index in range(len(video_labels))
            )
            + f"concat=n={len(video_labels)}:v=1:a=1[outv][outa]"
        )
    else:
        filters.append("".join(video_labels) + f"concat=n={len(video_labels)}:v=1:a=0[outv]")

    command = [
        ffmpeg_path,
        "-hide_banner",
        "-loglevel",
        "error",
        "-nostdin",
        "-y",
        "-i",
        str(source),
        "-filter_complex",
        ";".join(filters),
        "-map",
        "[outv]",
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
            "-movflags",
            "+faststart",
            "-shortest",
            "-avoid_negative_ts",
            "make_zero",
            "-f",
            policy.container,
            str(destination),
        ]
    )
    return command


def _source_id(plan: ExportPlan, index: int) -> str:
    if plan.source_ids:
        if index >= len(plan.source_ids):
            raise ExportExecutionError("Enhanced export source identities do not match probes")
        return plan.source_ids[index]
    identifiers = [source_id for source_id, _decision in plan.audio_decisions]
    identifiers.extend(
        decision.source_id for decision in plan.rate_decisions if hasattr(decision, "source_id")
    )
    unique = tuple(dict.fromkeys(identifiers))
    if len(unique) == 1:
        return unique[0]
    return "source"


def _segment_source_id(
    plan: ExportPlan,
    segment: Segment,
    decision_ids: Sequence[str],
) -> str:
    if segment.source_id:
        return segment.source_id
    if len(decision_ids) == 1:
        return decision_ids[0]
    if len(plan.source_ids) == 1:
        return plan.source_ids[0]
    raise ExportExecutionError("Enhanced export segment has no source identity")


def _source_segments(
    plan: ExportPlan,
    source_id: str,
) -> tuple[Segment, ...]:
    segments = (
        tuple(segment for segment in plan.segments if segment.source_id == source_id)
        if plan.source_paths
        else tuple(plan.segments)
    )
    active = tuple(segment for segment in segments if not segment.deleted)
    if not active:
        raise ExportExecutionError(f"Enhanced export has no active segments for source {source_id}")
    return active


def _audio_decision(
    plan: ExportPlan,
    source_id: str,
) -> AudioDecision | Mapping[str, Any] | None:
    decisions = dict(plan.audio_decisions)
    if source_id in decisions:
        return decisions[source_id]
    if len(decisions) == 1:
        return next(iter(decisions.values()))
    return None


def _format_tokens(value: str) -> set[str]:
    return {item.strip().casefold() for item in value.split(",") if item.strip()}


def _audio_requires_normalization(
    decision: AudioDecision | Mapping[str, Any] | None,
) -> bool:
    status, gain = _decision_status_and_gain(decision)
    if status in {"not-applicable", "silent"}:
        return False
    if status == "ready" and math.isfinite(gain):
        return abs(gain) >= 0.01
    return decision is not None


def _can_reuse_source(
    probe: MediaProbe,
    segments: Sequence[Segment],
    *,
    policy: OutputPolicy,
    base_rate: Fraction,
    audio_decision: AudioDecision | Mapping[str, Any] | None,
    multiple_sources: bool,
) -> bool:
    if multiple_sources:
        return False
    return _can_reuse_source_at_rate(
        probe,
        segments,
        policy=policy,
        target_rate=base_rate,
        audio_decision=audio_decision,
    )


def _can_reuse_source_at_rate(
    probe: MediaProbe,
    segments: Sequence[Segment],
    *,
    policy: OutputPolicy,
    target_rate: Fraction,
    audio_decision: AudioDecision | Mapping[str, Any] | None,
) -> bool:
    if any(segment.has_visual_modifications for segment in segments):
        return False
    if len(segments) != 1 or not segment_is_full_source(
        segments[0],
        probe.duration_seconds,
    ):
        return False
    if (probe.width, probe.height) != (policy.width, policy.height):
        return False
    try:
        source_rate = canonical_rate(probe.frame_rate)
    except ValueError:
        return False
    if source_rate != canonical_rate(target_rate):
        return False
    if probe.video_codec.casefold() != "h264":
        return False
    if not _format_tokens(probe.format_name).intersection({"mp4", "mov", "matroska", "mkv"}):
        return False
    if policy.video_codec.casefold() != "libx264" or policy.container.casefold() != "mp4":
        return False
    if policy.audio_stream_present != probe.has_audio_stream:
        return False
    if probe.has_audio_stream:
        if (
            probe.audio_codec is None
            or policy.audio_codec is None
            or probe.audio_codec.casefold() != policy.audio_codec.casefold()
            or probe.audio_sample_rate != policy.audio_sample_rate
            or probe.audio_channels != policy.audio_channels
        ):
            return False
        if _audio_requires_normalization(audio_decision):
            return False
    return True


def _segment_preparation_progress(
    callback: ExportProgressCallback | None,
    *,
    start_percent: float,
    end_percent: float,
    stage: str,
) -> ExportProgressCallback | None:
    if callback is None:
        return None

    def forward(progress: ExportProgress) -> None:
        local_fraction = max(0.0, min(1.0, progress.percent / 30.0))
        callback(
            replace(
                progress,
                stage=stage,
                percent=start_percent + (end_percent - start_percent) * local_fraction,
            )
        )

    return forward


def prepare_enhanced_sources(
    plan: ExportPlan,
    probes: Sequence[MediaProbe],
    decisions: Mapping[str, SourceRateDecision],
    temporary: Path,
    *,
    ffmpeg_path: str,
    ffprobe_path: str,
    progress_callback: ExportProgressCallback | None,
    started: float,
    cancel_event: threading.Event | None,
    backend_kwargs: Mapping[str, object] | None = None,
) -> tuple[PreparedSource, ...]:
    """Prepare each retained timeline segment without changing its source rate."""
    policy = plan.output_policy
    if policy is None:
        raise ExportExecutionError("Enhanced export is missing its output policy")
    if not probes:
        raise ExportExecutionError("Enhanced export has no source probes")
    if plan.source_paths and len(plan.source_ids) != len(probes):
        raise ExportExecutionError("Enhanced export source identities do not match probes")

    decision_ids = tuple(decisions)
    upscale_policy = _upscale_policy(plan)
    upscale_decisions = _upscale_decisions(plan)
    use_preserve_resolution = upscale_policy is not None and upscale_policy.enhancement_enabled
    restoration_options = backend_kwargs or {}
    source_probes = (
        dict(zip(plan.source_ids, probes, strict=True))
        if plan.source_paths
        else {_segment_source_id(plan, plan.segments[0], decision_ids): probes[0]}
    )
    active_segments = tuple(segment for segment in plan.segments if not segment.deleted)
    if not active_segments:
        raise ExportExecutionError("Enhanced export has no active segments")

    prepared: list[PreparedSource] = []
    total_segments = len(active_segments)
    progress_total = max(1.0, plan.expected_duration_seconds)
    progress_offset = 0.0
    for segment_index, segment in enumerate(active_segments):
        if cancel_event is not None and cancel_event.is_set():
            raise ExportExecutionError("Export cancelled")
        source_id = _segment_source_id(plan, segment, decision_ids)
        probe = source_probes.get(source_id)
        decision = decisions.get(source_id)
        if probe is None or decision is None:
            raise ExportExecutionError(
                f"Enhanced export has no probe or rate decision for source {source_id}"
            )
        source_rate = canonical_rate(probe.frame_rate)
        if source_rate != decision.source_rate:
            raise ExportExecutionError(
                f"Enhanced export rate decision does not match source {source_id}"
            )
        if decision.action == "unsupported":
            raise ExportExecutionError(
                f"Enhanced export cannot process source {source_id}: {decision.reason}"
            )
        preparation_rate = (
            source_rate
            if decision.action in {"interpolate", "passthrough"}
            else decision.target_rate
        )
        audio_decision = _audio_decision(plan, source_id)
        has_visual_modifications = segment.has_visual_modifications
        full_selection = segment_is_full_source(segment, probe.duration_seconds)
        cut_path = probe.path
        cut_probe = probe
        selected_segment = segment
        if (
            not full_selection
            and not has_visual_modifications
            and _can_losslessly_select(
                probe,
                (segment,),
                ffprobe_path=ffprobe_path,
            )
        ):
            cut_path = temporary / f"segment-{segment_index}-cut.mp4"
            cut_probe = _execute_lossless_selection(
                probe,
                (segment,),
                cut_path,
                temporary,
                include_audio=policy.audio_stream_present,
                ffmpeg_path=ffmpeg_path,
                ffprobe_path=ffprobe_path,
                progress_callback=_segment_preparation_progress(
                    progress_callback,
                    start_percent=30.0 * segment_index / total_segments,
                    end_percent=30.0 * (segment_index + 1) / total_segments,
                    stage=f"preparing segment {segment_index + 1}/{total_segments}",
                ),
                started=started,
                progress_offset_seconds=progress_offset,
                progress_total_duration_seconds=progress_total,
                cancel_event=cancel_event,
            )
            selected_segment = Segment.create(0.0, segment.duration_seconds)

        restoration_decision = upscale_decisions.get(source_id)
        should_restore = (
            upscale_policy is not None
            and upscale_policy.enhancement_enabled
            and restoration_decision is not None
            and restoration_decision.eligible
        )
        if (
            upscale_policy is not None
            and upscale_policy.enhancement_enabled
            and restoration_decision is not None
            and restoration_decision.eligible
        ):
            restoration_source = cut_path
            restoration_probe = cut_probe
            restoration_path = temporary / f"segment-{segment_index}-restored.mp4"
            restored_probe = _run_source_restoration(
                restoration_probe,
                restoration_path,
                policy=upscale_policy,
                model=restoration_decision.model or upscale_policy.model,
                backend_kwargs=restoration_options,
                ffprobe_path=ffprobe_path,
                cancel_event=cancel_event,
            )
            cut_path = restoration_path
            cut_probe = restored_probe
            if restoration_source == probe.path:
                selected_segment = segment
            else:
                selected_segment = Segment.create(0.0, segment.duration_seconds)

        content_width: int | None = None
        content_height: int | None = None
        if use_preserve_resolution:
            if restoration_decision is not None and restoration_decision.eligible:
                content_width = restoration_decision.target_width
                content_height = restoration_decision.target_height
            else:
                content_width = cut_probe.width
                content_height = cut_probe.height

        if (
            not _can_reuse_source_at_rate(
                cut_probe,
                (selected_segment,),
                policy=policy,
                target_rate=preparation_rate,
                audio_decision=audio_decision,
            )
            or should_restore
            or use_preserve_resolution
        ):
            normalized_path = temporary / f"segment-{segment_index}-prepared.mp4"
            normalization_source = cut_path
            normalization_segments = (selected_segment,)
            if cut_path == probe.path:
                normalization_source = probe.path
                normalization_segments = (segment,)
            normalized_probe = _execute_source_normalization(
                normalization_source,
                normalized_path,
                normalization_segments,
                target_rate=preparation_rate,
                policy=policy,
                audio_decision=audio_decision,
                has_audio=cut_probe.has_audio_stream,
                ffmpeg_path=ffmpeg_path,
                ffprobe_path=ffprobe_path,
                preserve_resolution=use_preserve_resolution,
                content_width=content_width,
                content_height=content_height,
                progress_callback=_segment_preparation_progress(
                    progress_callback,
                    start_percent=30.0 * segment_index / total_segments,
                    end_percent=30.0 * (segment_index + 1) / total_segments,
                    stage=f"preparing segment {segment_index + 1}/{total_segments}",
                ),
                started=started,
                progress_offset_seconds=progress_offset,
                progress_total_duration_seconds=progress_total,
                cancel_event=cancel_event,
            )
            prepared_path = normalized_path
            prepared_probe = normalized_probe
        else:
            prepared_path = cut_path
            prepared_probe = cut_probe
        prepared.append(
            PreparedSource(
                source_id=source_id,
                segment_index=segment_index,
                path=prepared_path,
                probe=prepared_probe,
                source_rate=source_rate,
            )
        )
        progress_offset += segment.duration_seconds
    return tuple(prepared)


def _needs_normalization(
    probe: MediaProbe,
    segments: Sequence[Segment],
    *,
    policy: OutputPolicy,
    base_rate: Fraction,
    audio_decision: AudioDecision | Mapping[str, Any] | None,
    multiple_sources: bool,
) -> bool:
    if _can_reuse_source(
        probe,
        segments,
        policy=policy,
        base_rate=base_rate,
        audio_decision=audio_decision,
        multiple_sources=multiple_sources,
    ):
        return False
    return True


def _write_concat_list(paths: Sequence[Path], destination: Path) -> None:
    lines = []
    for path in paths:
        escaped = str(path).replace("'", "'\\''")
        lines.append(f"file '{escaped}'\n")
    try:
        destination.write_text("".join(lines), encoding="utf-8")
    except OSError as error:
        raise ExportExecutionError(f"Could not write the concat list: {error}") from error


def _execute_lossless_selection(
    probe: MediaProbe,
    segments: Sequence[Segment],
    destination: Path,
    temporary: Path,
    *,
    include_audio: bool | None = None,
    ffmpeg_path: str,
    ffprobe_path: str,
    progress_callback: ExportProgressCallback | None,
    started: float,
    progress_offset_seconds: float,
    progress_total_duration_seconds: float,
    cancel_event: threading.Event | None,
) -> MediaProbe:
    if len(segments) == 1 and segment_is_full_source(
        segments[0],
        probe.duration_seconds,
    ):
        return probe
    has_audio = (
        probe.has_audio_stream
        if include_audio is None
        else include_audio and probe.has_audio_stream
    )
    selected_duration = sum(segment.duration_seconds for segment in segments)
    parts_directory = temporary / f"{destination.stem}-parts"
    parts_directory.mkdir(parents=True, exist_ok=True)
    part_paths: list[Path] = []
    try:
        offset = 0.0
        for index, segment in enumerate(segments):
            part = parts_directory / f"part-{index}.mp4"
            command = build_lossless_cut_command(
                probe.path,
                part,
                start_seconds=segment.start_seconds,
                duration_seconds=segment.duration_seconds,
                has_audio=has_audio,
                ffmpeg_path=ffmpeg_path,
            )
            run_ffmpeg(
                command,
                progress_callback=_scaled_progress_callback(
                    progress_callback,
                    start_percent=0.0,
                    end_percent=30.0,
                ),
                stage=f"cut {index + 1}/{len(segments)}",
                command_duration_seconds=segment.duration_seconds,
                progress_offset_seconds=progress_offset_seconds + offset,
                progress_total_duration_seconds=progress_total_duration_seconds,
                started=started,
                cancel_event=cancel_event,
            )
            part_paths.append(part)
            offset += segment.duration_seconds
        if len(part_paths) == 1:
            os.replace(part_paths[0], destination)
        else:
            list_path = parts_directory / "concat-list.txt"
            _write_concat_list(part_paths, list_path)
            command = build_concat_copy_command(
                list_path,
                destination,
                has_audio=has_audio,
                ffmpeg_path=ffmpeg_path,
            )
            run_ffmpeg(
                command,
                progress_callback=_scaled_progress_callback(
                    progress_callback,
                    start_percent=0.0,
                    end_percent=30.0,
                ),
                stage="assembling lossless cuts",
                command_duration_seconds=selected_duration,
                progress_offset_seconds=progress_offset_seconds,
                progress_total_duration_seconds=progress_total_duration_seconds,
                started=started,
                cancel_event=cancel_event,
            )
        try:
            return probe_media(destination, ffprobe_path)
        except MediaProbeError as error:
            raise ExportExecutionError(
                f"Lossless cut output could not be inspected: {error}"
            ) from error
    finally:
        shutil.rmtree(parts_directory, ignore_errors=True)


def _execute_source_normalization(
    source: Path,
    destination: Path,
    segments: Sequence[Segment],
    *,
    target_rate: Fraction,
    policy: OutputPolicy,
    audio_decision: AudioDecision | Mapping[str, Any] | None,
    has_audio: bool,
    ffmpeg_path: str,
    ffprobe_path: str,
    preserve_resolution: bool,
    content_width: int | None,
    content_height: int | None,
    progress_callback: ExportProgressCallback | None,
    started: float,
    progress_offset_seconds: float,
    progress_total_duration_seconds: float,
    cancel_event: threading.Event | None,
) -> MediaProbe:
    partial = partial_path(destination)
    selected_duration = sum(segment.duration_seconds for segment in segments)
    command = build_source_normalization_command(
        source,
        partial,
        segments,
        target_rate=target_rate,
        policy=policy,
        audio_decision=audio_decision,
        has_audio=has_audio,
        ffmpeg_path=ffmpeg_path,
        preserve_resolution=preserve_resolution,
        content_width=content_width,
        content_height=content_height,
    )
    try:
        run_ffmpeg(
            command,
            progress_callback=_scaled_progress_callback(
                progress_callback,
                start_percent=0.0,
                end_percent=30.0,
            ),
            stage="normalizing source",
            command_duration_seconds=selected_duration,
            progress_offset_seconds=progress_offset_seconds,
            progress_total_duration_seconds=progress_total_duration_seconds,
            started=started,
            cancel_event=cancel_event,
        )
        if not partial.is_file() or partial.stat().st_size <= 0:
            raise ExportExecutionError("Source normalization did not create an output")
        os.replace(partial, destination)
        try:
            return probe_media(destination, ffprobe_path)
        except MediaProbeError as error:
            raise ExportExecutionError(
                f"Normalized source could not be inspected: {error}"
            ) from error
    finally:
        partial.unlink(missing_ok=True)


def _master_segments_duration(segments: Sequence[Segment]) -> float:
    return sum(segment.duration_seconds for segment in segments)


def _can_losslessly_select(
    probe: MediaProbe,
    segments: Sequence[Segment],
    *,
    ffprobe_path: str,
) -> bool:
    boundaries = {
        boundary
        for segment in segments
        for boundary in (segment.start_seconds, segment.end_seconds)
        if boundary > _BOUNDARY_TOLERANCE
        and boundary < probe.duration_seconds - _BOUNDARY_TOLERANCE
    }
    if not boundaries:
        return True
    try:
        from .export_planning import boundary_is_keyframe, probe_keyframe_timestamps

        keyframes = probe_keyframe_timestamps(probe.path, ffprobe_path)
    except (ExportPlanningError, OSError):
        return False
    return bool(keyframes) and all(
        boundary_is_keyframe(boundary, keyframes) for boundary in boundaries
    )


def prepare_enhanced_master(
    plan: ExportPlan,
    probes: Sequence[MediaProbe],
    temporary: Path,
    *,
    ffmpeg_path: str,
    ffprobe_path: str,
    progress_callback: ExportProgressCallback | None,
    started: float,
    cancel_event: threading.Event | None,
) -> PreparedMaster:
    policy = plan.output_policy
    if policy is None:
        raise ExportExecutionError("Enhanced export is missing its output policy")
    if not probes:
        raise ExportExecutionError("Enhanced export has no source probes")
    base_rate = min(
        (canonical_rate(probe.frame_rate) for probe in probes),
        key=float,
    )
    multiple_sources = len(probes) > 1
    prepared_paths: list[Path] = []
    prepared_probes: list[MediaProbe] = []
    progress_offset = 0.0
    for index, probe in enumerate(probes):
        if cancel_event is not None and cancel_event.is_set():
            raise ExportExecutionError("Export cancelled")
        source_id = _source_id(plan, index)
        segments = _source_segments(plan, source_id)
        selected_duration = _master_segments_duration(segments)
        audio_decision = _audio_decision(plan, source_id)
        has_visual_modifications = any(segment.has_visual_modifications for segment in segments)
        full_selection = len(segments) == 1 and segment_is_full_source(
            segments[0],
            probe.duration_seconds,
        )
        cut_path = probe.path
        cut_probe = probe
        if (
            not full_selection
            and not has_visual_modifications
            and _can_losslessly_select(
                probe,
                segments,
                ffprobe_path=ffprobe_path,
            )
        ):
            cut_path = temporary / f"source-{index}-cut.mp4"
            cut_probe = _execute_lossless_selection(
                probe,
                segments,
                cut_path,
                temporary,
                include_audio=policy.audio_stream_present,
                ffmpeg_path=ffmpeg_path,
                ffprobe_path=ffprobe_path,
                progress_callback=progress_callback,
                started=started,
                progress_offset_seconds=progress_offset,
                progress_total_duration_seconds=plan.expected_duration_seconds,
                cancel_event=cancel_event,
            )
        needs_normalization = _needs_normalization(
            probe,
            segments,
            policy=policy,
            base_rate=base_rate,
            audio_decision=audio_decision,
            multiple_sources=multiple_sources,
        )
        if needs_normalization:
            normalized_path = temporary / f"source-{index}-prepared.mp4"
            normalization_segments = segments
            normalization_source = probe.path
            normalization_audio = probe.has_audio_stream
            if cut_path != probe.path and not has_visual_modifications:
                normalization_source = cut_path
                normalization_segments = (Segment.create(0.0, selected_duration),)
                normalization_audio = cut_probe.has_audio_stream
            normalized_probe = _execute_source_normalization(
                normalization_source,
                normalized_path,
                normalization_segments,
                target_rate=base_rate,
                policy=policy,
                audio_decision=audio_decision,
                has_audio=normalization_audio,
                ffmpeg_path=ffmpeg_path,
                ffprobe_path=ffprobe_path,
                preserve_resolution=False,
                content_width=None,
                content_height=None,
                progress_callback=progress_callback,
                started=started,
                progress_offset_seconds=progress_offset,
                progress_total_duration_seconds=plan.expected_duration_seconds,
                cancel_event=cancel_event,
            )
            prepared_paths.append(normalized_path)
            prepared_probes.append(normalized_probe)
        else:
            prepared_paths.append(cut_path)
            prepared_probes.append(cut_probe)
        progress_offset += selected_duration

    if len(prepared_paths) == 1:
        return PreparedMaster(
            path=prepared_paths[0],
            probe=prepared_probes[0],
            base_rate=base_rate,
        )

    list_path = temporary / "prepared-master-list.txt"
    master_path = temporary / "prepared-master.mp4"
    _write_concat_list(prepared_paths, list_path)
    partial = partial_path(master_path)
    try:
        command = build_concat_copy_command(
            list_path,
            partial,
            has_audio=policy.audio_stream_present,
            ffmpeg_path=ffmpeg_path,
        )
        master_frames = _segment_frame_count(plan.expected_duration_seconds, base_rate)
        run_ffmpeg(
            command,
            progress_callback=_scaled_progress_callback(
                progress_callback,
                start_percent=30.0,
                end_percent=35.0,
            ),
            stage="concatenating prepared sources",
            command_duration_seconds=plan.expected_duration_seconds,
            progress_offset_seconds=0.0,
            progress_total_duration_seconds=plan.expected_duration_seconds,
            command_total_frames=master_frames,
            progress_total_frames=master_frames,
            started=started,
            cancel_event=cancel_event,
        )
        if not partial.is_file() or partial.stat().st_size <= 0:
            raise ExportExecutionError("Prepared-source concatenation did not create an output")
        os.replace(partial, master_path)
        try:
            master_probe = probe_media(master_path, ffprobe_path)
        except MediaProbeError as error:
            raise ExportExecutionError(
                f"Prepared master could not be inspected: {error}"
            ) from error
    finally:
        partial.unlink(missing_ok=True)
    return PreparedMaster(
        path=master_path,
        probe=master_probe,
        base_rate=base_rate,
    )


__all__ = [
    "PreparedMaster",
    "PreparedSource",
    "build_concat_copy_command",
    "build_lossless_cut_command",
    "build_source_normalization_command",
    "build_video_only_copy_command",
    "prepare_enhanced_master",
    "prepare_enhanced_sources",
]
