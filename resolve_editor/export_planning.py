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
from .media import MediaProbe
from .model import Segment, SegmentTimeline


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


def plan_export(
    media: MediaProbe,
    timeline: SegmentTimeline,
    destination: Path,
    *,
    keyframe_timestamps: Sequence[float] | None = None,
    ffprobe_path: str = "ffprobe",
    audio_decision: AudioDecision | Mapping[str, Any] | None = None,
    audio_source_id: str = "source",
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

    output_policy = resolve_output_policy([media.metadata()])
    fallback_reasons: list[str] = []
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
            audio_decisions=(
                ()
                if persisted_audio_decision is None
                else ((audio_source_id, persisted_audio_decision),)
            ),
        )

    return ExportPlan(
        route="fallback",
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
        audio_decisions=(
            ()
            if persisted_audio_decision is None
            else ((audio_source_id, persisted_audio_decision),)
        ),
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
) -> ExportPlan:
    """Plan a composed export for a timeline that references several sources."""
    timeline.validate()
    if not timeline.mixed_source:
        raise ExportPlanningError("Mixed export requires a mixed-source timeline")
    probes = tuple(sources)
    if not probes:
        raise ExportPlanningError("At least one source is required for mixed export")
    resolved_policy = (
        resolve_output_policy([probe.metadata() for probe in probes]) if policy is None else policy
    )
    if source_ids is None:
        source_ids = tuple(
            segment.source_id for segment in timeline.segment_items if segment.source_id is not None
        )
        source_ids = tuple(dict.fromkeys(source_ids))
    ids = tuple(source_ids)
    if len(ids) != len(probes):
        raise ExportPlanningError("Mixed export source identities do not match probes")
    source_by_id = dict(zip(ids, probes, strict=True))
    active_segments = tuple(segment for segment in timeline.segment_items if not segment.deleted)
    if not active_segments or timeline.edited_duration_seconds <= 0:
        raise ExportPlanningError("Cannot export an empty edit")
    for segment in active_segments:
        if segment.source_id not in source_by_id:
            raise ExportPlanningError(
                f"Timeline block references an unavailable source: {segment.source_id}"
            )
        probe = source_by_id[segment.source_id]
        if segment.end_seconds > probe.duration_seconds + _DURATION_TOLERANCE:
            raise ExportPlanningError(
                f"Timeline block exceeds source duration: {segment.segment_id}"
            )
    output = Path(destination).expanduser()
    source_paths = tuple(probe.path.expanduser().resolve() for probe in probes)
    if output.resolve() in source_paths:
        raise ExportPlanningError("Export destination must differ from every source")
    decision_items = tuple(
        (
            source_id,
            _persisted_audio_decision(audio_decisions[source_id]),
        )
        for source_id in ids
        if audio_decisions is not None and source_id in audio_decisions
    )
    return ExportPlan(
        route="fallback",
        source=source_paths[0],
        destination=output,
        segments=active_segments,
        expected_duration_seconds=timeline.edited_duration_seconds,
        reason=(f"Mixed-source composition requires normalization: {resolved_policy.reason}"),
        fallback_video_codec=resolved_policy.video_codec,
        fallback_audio_codec=resolved_policy.audio_codec,
        fallback_container=resolved_policy.container,
        fallback_pixel_format=resolved_policy.pixel_format,
        source_paths=source_paths,
        source_ids=ids,
        output_policy=resolved_policy,
        audio_decisions=decision_items,
    )
