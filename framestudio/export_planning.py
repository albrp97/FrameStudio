from __future__ import annotations

import json
import math
import subprocess
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from .audio import AudioDecision
from .export_types import (
    _BOUNDARY_TOLERANCE,
    _DURATION_TOLERANCE,
    _FAST_AUDIO_CODECS,
    _FAST_CONTAINERS,
    _FAST_VIDEO_CODECS,
    ExportPlan,
    ExportPlanningError,
    OutputPolicy,
    resolve_output_policy,
)
from .fps_policy import (
    FrameRatePolicy,
    FrameRatePolicyError,
    ResolvedFrameRatePolicy,
    resolved_from_policy,
)
from .media import MediaProbe
from .model import Segment, SegmentTimeline
from .upscale_policy import (
    ResolvedUpscalePolicy,
    UpscalePolicy,
    UpscalePolicyError,
)
from .upscale_policy import (
    resolved_from_policy as resolved_upscale_from_policy,
)


def format_name_tokens(format_name: str) -> set[str]:
    return {token.strip().lower() for token in format_name.split(",") if token.strip()}


def probe_keyframe_timestamps(
    source: Path,
    ffprobe_path: str,
) -> tuple[float, ...]:
    try:
        result = subprocess.run(
            [
                ffprobe_path,
                "-v",
                "error",
                "-select_streams",
                "v:0",
                "-skip_frame",
                "nokey",
                "-show_frames",
                "-show_entries",
                "frame=best_effort_timestamp_time",
                "-of",
                "json",
                str(source),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError as error:
        raise ExportPlanningError(
            f"ffprobe is not installed or not on PATH: {ffprobe_path}"
        ) from error
    if result.returncode != 0:
        detail = result.stderr.strip() or "ffprobe could not read keyframes"
        raise ExportPlanningError(f"Could not inspect keyframes for {source.name}: {detail}")
    try:
        data = json.loads(result.stdout)
        frames = data["frames"]
    except (KeyError, TypeError, json.JSONDecodeError) as error:
        raise ExportPlanningError(
            f"ffprobe returned invalid keyframe data for {source.name}"
        ) from error
    if not isinstance(frames, list):
        raise ExportPlanningError(f"ffprobe returned invalid keyframe data for {source.name}")
    timestamps: list[float] = []
    for frame in frames:
        if not isinstance(frame, dict):
            raise ExportPlanningError(f"ffprobe returned invalid keyframe data for {source.name}")
        value = frame.get("best_effort_timestamp_time")
        if value is None:
            continue
        try:
            timestamp = float(value)
        except ValueError as error:
            raise ExportPlanningError(
                f"ffprobe returned an invalid keyframe timestamp for {source.name}"
            ) from error
        if not math.isfinite(timestamp) or timestamp < 0:
            raise ExportPlanningError(
                f"ffprobe returned an invalid keyframe timestamp for {source.name}"
            )
        timestamps.append(timestamp)
    return tuple(timestamps)


def validated_keyframes(
    keyframe_timestamps: Sequence[float],
) -> tuple[float, ...]:
    validated: list[float] = []
    for timestamp in keyframe_timestamps:
        if (
            not isinstance(timestamp, (int, float))
            or isinstance(timestamp, bool)
            or not math.isfinite(float(timestamp))
            or float(timestamp) < 0
        ):
            raise ExportPlanningError("Keyframe timestamps must be finite non-negative numbers")
        validated.append(float(timestamp))
    return tuple(validated)


def boundary_is_keyframe(
    boundary: float,
    keyframes: Sequence[float],
) -> bool:
    return any(
        math.isclose(
            boundary,
            keyframe,
            rel_tol=0.0,
            abs_tol=_BOUNDARY_TOLERANCE,
        )
        for keyframe in keyframes
    )


def internal_boundaries(
    segments: Sequence[Segment],
    source_duration_seconds: float,
) -> tuple[float, ...]:
    boundaries: set[float] = set()
    for segment in segments:
        if segment.start_seconds > _BOUNDARY_TOLERANCE:
            boundaries.add(segment.start_seconds)
        if segment.end_seconds < source_duration_seconds - _BOUNDARY_TOLERANCE:
            boundaries.add(segment.end_seconds)
    return tuple(sorted(boundaries))


def _persisted_audio_decision(
    decision: AudioDecision | Mapping[str, Any],
) -> AudioDecision | dict[str, Any]:
    return decision if isinstance(decision, AudioDecision) else dict(decision)


def _resolved_frame_rate_policy(
    metadata: Sequence[Mapping[str, Any]],
    policy: (FrameRatePolicy | ResolvedFrameRatePolicy | Mapping[str, Any] | None),
) -> ResolvedFrameRatePolicy | None:
    if policy is None:
        return None
    try:
        if isinstance(policy, ResolvedFrameRatePolicy):
            resolved = policy
        else:
            normalized = (
                policy if isinstance(policy, FrameRatePolicy) else FrameRatePolicy.from_dict(policy)
            )
            resolved = resolved_from_policy(metadata, normalized)
    except FrameRatePolicyError as error:
        raise ExportPlanningError(f"Invalid frame-rate policy: {error}") from error
    if resolved.has_unsupported_sources:
        unsupported = "; ".join(
            f"{item.source_id}: {item.reason}"
            for item in resolved.decisions
            if item.action == "unsupported"
        )
        raise ExportPlanningError(
            "Frame-rate enhancement is not supported for the selected sources: " + unsupported
        )
    return resolved


def _resolved_upscale_policy(
    metadata: Sequence[Mapping[str, Any]],
    policy: UpscalePolicy | ResolvedUpscalePolicy | Mapping[str, Any] | None,
) -> ResolvedUpscalePolicy:
    try:
        if policy is None:
            return resolved_upscale_from_policy(metadata, UpscalePolicy())
        if isinstance(policy, ResolvedUpscalePolicy):
            return policy
        normalized = (
            policy if isinstance(policy, UpscalePolicy) else UpscalePolicy.from_dict(policy)
        )
        return resolved_upscale_from_policy(metadata, normalized)
    except UpscalePolicyError as error:
        raise ExportPlanningError(f"Invalid upscale policy: {error}") from error


def plan_export(
    media: MediaProbe,
    timeline: SegmentTimeline,
    destination: Path,
    *,
    keyframe_timestamps: Sequence[float] | None = None,
    ffprobe_path: str = "ffprobe",
    audio_decision: AudioDecision | Mapping[str, Any] | None = None,
    audio_source_id: str = "source",
    frame_rate_policy: (
        FrameRatePolicy | ResolvedFrameRatePolicy | Mapping[str, Any] | None
    ) = None,
    upscale_policy: UpscalePolicy | ResolvedUpscalePolicy | Mapping[str, Any] | None = None,
) -> ExportPlan:
    timeline.validate()
    if not math.isclose(
        media.duration_seconds,
        timeline.source_duration_seconds,
        rel_tol=0.0,
        abs_tol=_DURATION_TOLERANCE,
    ):
        raise ExportPlanningError("Source duration does not match the project timeline")
    source = media.path.expanduser().resolve()
    output = Path(destination).expanduser()
    if output.resolve() == source:
        raise ExportPlanningError("Export destination must differ from the source")
    active_segments = tuple(segment for segment in timeline.segment_items if not segment.deleted)
    if not active_segments or timeline.edited_duration_seconds <= 0:
        raise ExportPlanningError("Cannot export an empty edit")
    persisted_audio_decision = (
        None if audio_decision is None else _persisted_audio_decision(audio_decision)
    )

    source_metadata = {
        **media.metadata(),
        "source_id": audio_source_id,
    }
    resolved_fps_policy = _resolved_frame_rate_policy(
        (source_metadata,),
        frame_rate_policy,
    )
    resolved_upscale_policy = _resolved_upscale_policy(
        (source_metadata,),
        upscale_policy,
    )
    output_policy = resolve_output_policy(
        [source_metadata],
        target_rate=(None if resolved_fps_policy is None else resolved_fps_policy.target_rate),
    )
    fallback_reasons: list[str] = []
    if any(segment.has_visual_modifications for segment in active_segments):
        fallback_reasons.append("visual focus or triplicate composition requires decoded rendering")
    if (media.width, media.height) != (output_policy.width, output_policy.height):
        fallback_reasons.append("source dimensions do not match the fixed 1920x1080 project canvas")
    formats = format_name_tokens(media.format_name)
    if not formats.intersection(_FAST_CONTAINERS):
        fallback_reasons.append("source container is not in the conservative stream-copy policy")
    if media.video_codec.lower() not in _FAST_VIDEO_CODECS:
        fallback_reasons.append(f"video codec {media.video_codec} is not in the stream-copy policy")
    audio_is_eligible = (
        media.audio_codec in _FAST_AUDIO_CODECS
        if media.has_audio_stream
        else media.audio_codec is None
    )
    if not audio_is_eligible:
        fallback_reasons.append(f"audio codec {media.audio_codec} is not in the stream-copy policy")
    if media.has_audio_stream and audio_decision is not None:
        if media.audio_sample_rate not in (None, 48000):
            fallback_reasons.append(
                "audio sample rate does not match the established 48000 Hz profile"
            )
        if media.audio_channels not in (None, 2):
            fallback_reasons.append(
                "audio channel count does not match the established stereo profile"
            )
    if audio_decision is not None and media.has_audio_stream:
        decision_status = (
            audio_decision.status
            if isinstance(audio_decision, AudioDecision)
            else audio_decision.get("status")
        )
        decision_gain = (
            audio_decision.gain_db
            if isinstance(audio_decision, AudioDecision)
            else audio_decision.get("gain_db", 0.0)
        )
        if decision_status == "ready" and isinstance(decision_gain, (int, float)):
            if math.isfinite(float(decision_gain)) and abs(float(decision_gain)) >= 0.01:
                fallback_reasons.append("source-level audio normalization requires decoding")
        elif decision_status not in {"not-applicable", "silent"}:
            fallback_reasons.append(
                f"source-level audio decision is {decision_status or 'pending'}"
            )
    if resolved_fps_policy is not None:
        decision = resolved_fps_policy.decisions[0]
        if decision.action == "interpolate":
            fallback_reasons.append("validated frame-rate enhancement is required for this source")
        elif decision.action in {"convert", "convert-down"}:
            fallback_reasons.append("selected target frame rate differs from the source rate")
    if resolved_upscale_policy.has_eligible_sources:
        fallback_reasons.append(
            "validated SuperUltraCompact spatial enhancement is required for eligible sources"
        )

    boundaries = internal_boundaries(
        active_segments,
        timeline.source_duration_seconds,
    )
    keyframes: tuple[float, ...] = ()
    if boundaries:
        if keyframe_timestamps is None:
            keyframes = probe_keyframe_timestamps(source, ffprobe_path)
        else:
            keyframes = validated_keyframes(keyframe_timestamps)
        if not keyframes or any(
            not boundary_is_keyframe(boundary, keyframes) for boundary in boundaries
        ):
            fallback_reasons.append("one or more cut boundaries are not keyframe-aligned")

    plan_audio_decisions = (
        () if persisted_audio_decision is None else ((audio_source_id, persisted_audio_decision),)
    )
    plan_frame_rate_policy = None if resolved_fps_policy is None else resolved_fps_policy.policy
    plan_rate_decisions = () if resolved_fps_policy is None else resolved_fps_policy.decisions
    if not fallback_reasons:
        if boundaries:
            reason = "All retained cut boundaries are keyframe-aligned for stream copy"
        else:
            reason = "No internal cut boundaries require re-encoding"
        return ExportPlan(
            route="stream-copy",
            source=source,
            destination=output,
            segments=active_segments,
            expected_duration_seconds=timeline.edited_duration_seconds,
            reason=reason,
            output_policy=output_policy,
            audio_decisions=plan_audio_decisions,
            frame_rate_policy=plan_frame_rate_policy,
            rate_decisions=plan_rate_decisions,
            upscale_policy=resolved_upscale_policy.policy,
            upscale_decisions=resolved_upscale_policy.decisions,
        )

    route = (
        "enhanced"
        if (
            resolved_upscale_policy.has_eligible_sources
            or (
                resolved_fps_policy is not None
                and any(item.action == "interpolate" for item in resolved_fps_policy.decisions)
            )
        )
        else "fallback"
    )
    return ExportPlan(
        route=route,
        source=source,
        destination=output,
        segments=active_segments,
        expected_duration_seconds=timeline.edited_duration_seconds,
        reason="; ".join(fallback_reasons),
        fallback_video_codec="libx264",
        fallback_audio_codec="aac" if media.has_audio_stream else None,
        fallback_container="mp4",
        fallback_pixel_format="yuv420p",
        output_policy=output_policy,
        audio_decisions=plan_audio_decisions,
        frame_rate_policy=plan_frame_rate_policy,
        rate_decisions=plan_rate_decisions,
        upscale_policy=resolved_upscale_policy.policy,
        upscale_decisions=resolved_upscale_policy.decisions,
    )


def plan_mixed_export(
    sources: Sequence[MediaProbe],
    timeline: SegmentTimeline,
    destination: Path,
    *,
    policy: OutputPolicy | None = None,
    source_ids: Sequence[str] | None = None,
    audio_decisions: Mapping[
        str,
        AudioDecision | Mapping[str, Any],
    ]
    | None = None,
    frame_rate_policy: (
        FrameRatePolicy | ResolvedFrameRatePolicy | Mapping[str, Any] | None
    ) = None,
    upscale_policy: UpscalePolicy | ResolvedUpscalePolicy | Mapping[str, Any] | None = None,
) -> ExportPlan:
    """Plan a composed export for a timeline that references several sources."""
    timeline.validate()
    if not timeline.mixed_source:
        raise ExportPlanningError("Mixed export requires a mixed-source timeline")
    probes = tuple(sources)
    if not probes:
        raise ExportPlanningError("At least one source is required for mixed export")
    active_segments = tuple(segment for segment in timeline.segment_items if not segment.deleted)
    if not active_segments or timeline.edited_duration_seconds <= 0:
        raise ExportPlanningError("Cannot export an empty edit")
    if source_ids is None:
        source_ids = tuple(
            segment.source_id for segment in active_segments if segment.source_id is not None
        )
        source_ids = tuple(dict.fromkeys(source_ids))
    ids = tuple(source_ids)
    if len(ids) != len(probes):
        raise ExportPlanningError("Mixed export source identities do not match probes")
    source_by_id = dict(zip(ids, probes, strict=True))
    for segment in active_segments:
        source_id = segment.source_id
        if source_id is None or source_id not in source_by_id:
            raise ExportPlanningError(
                f"Timeline block references an unavailable source: {source_id}"
            )
        probe = source_by_id[source_id]
        if segment.end_seconds > probe.duration_seconds + _DURATION_TOLERANCE:
            raise ExportPlanningError(
                f"Timeline block exceeds source duration: {segment.segment_id}"
            )
    active_source_ids = tuple(
        dict.fromkeys(
            segment.source_id for segment in active_segments if segment.source_id is not None
        )
    )
    active_probes = tuple(source_by_id[source_id] for source_id in active_source_ids)
    source_metadata = tuple(
        {
            **probe.metadata(),
            "source_id": source_id,
        }
        for source_id, probe in zip(active_source_ids, active_probes, strict=True)
    )
    resolved_fps_policy = _resolved_frame_rate_policy(
        source_metadata,
        frame_rate_policy,
    )
    resolved_upscale_policy = _resolved_upscale_policy(
        source_metadata,
        upscale_policy,
    )
    resolved_policy = (
        resolve_output_policy(
            source_metadata,
            target_rate=(None if resolved_fps_policy is None else resolved_fps_policy.target_rate),
        )
        if policy is None
        else policy
    )
    output = Path(destination).expanduser()
    source_paths = tuple(probe.path.expanduser().resolve() for probe in active_probes)
    if output.resolve() in source_paths:
        raise ExportPlanningError("Export destination must differ from every source")
    decision_items = tuple(
        (
            source_id,
            _persisted_audio_decision(audio_decisions[source_id]),
        )
        for source_id in active_source_ids
        if audio_decisions is not None and source_id in audio_decisions
    )
    composition_reason = (
        "; visual focus or triplicate composition is rendered per segment"
        if any(segment.has_visual_modifications for segment in active_segments)
        else ""
    )
    rate_reason = ""
    if resolved_fps_policy is not None:
        if any(item.action == "interpolate" for item in resolved_fps_policy.decisions):
            rate_reason = "; validated frame-rate enhancement is required for eligible sources"
        elif any(
            item.action in {"convert", "convert-down"} for item in resolved_fps_policy.decisions
        ):
            rate_reason = "; selected target frame rate requires conversion"
    upscale_reason = ""
    if resolved_upscale_policy.has_eligible_sources:
        upscale_reason = (
            "; validated SuperUltraCompact spatial enhancement is required for eligible sources"
        )
    return ExportPlan(
        route=(
            "enhanced"
            if resolved_upscale_policy.has_eligible_sources
            or (rate_reason and "enhancement" in rate_reason)
            else "fallback"
        ),
        source=source_paths[0],
        destination=output,
        segments=active_segments,
        expected_duration_seconds=timeline.edited_duration_seconds,
        reason=(
            f"Mixed-source composition requires normalization: {resolved_policy.reason}"
            f"{composition_reason}"
            f"{rate_reason}"
            f"{upscale_reason}"
        ),
        fallback_video_codec=resolved_policy.video_codec,
        fallback_audio_codec=resolved_policy.audio_codec,
        fallback_container=resolved_policy.container,
        fallback_pixel_format=resolved_policy.pixel_format,
        source_paths=source_paths,
        source_ids=active_source_ids,
        output_policy=resolved_policy,
        audio_decisions=decision_items,
        frame_rate_policy=(None if resolved_fps_policy is None else resolved_fps_policy.policy),
        rate_decisions=(() if resolved_fps_policy is None else resolved_fps_policy.decisions),
        upscale_policy=resolved_upscale_policy.policy,
        upscale_decisions=resolved_upscale_policy.decisions,
    )
