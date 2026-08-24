from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path

from .audio import (
    AUDIO_POLICY_VERSION,
    AudioDecision,
    analyze_source_audio,
    audio_decision_is_stale,
    pending_audio_decision,
)
from .composition import VisualTransform
from .export import (
    ExportPlan,
    plan_export,
    plan_mixed_export,
    resolve_output_policy,
)
from .media import probe_media
from .model import (
    Project,
    ProjectValidationError,
    Segment,
    SegmentTimeline,
    SourceReference,
)


def create_project_from_source(
    source_path: Path,
    *,
    ffprobe_path: str = "ffprobe",
) -> Project:
    media = probe_media(source_path, ffprobe_path)
    return Project.create(source_path, media.metadata())


def create_project_from_sources(
    source_paths: Sequence[Path],
    *,
    ffprobe_path: str = "ffprobe",
) -> Project:
    paths = tuple(Path(path).expanduser() for path in source_paths)
    if not paths:
        raise ProjectValidationError("At least one source is required")
    probes = tuple(probe_media(path, ffprobe_path) for path in paths)
    return Project.create_multi(
        tuple((probe.path, probe.metadata()) for probe in probes),
    )


def export_destination_conflicts_with_project(
    project_path: Path | None,
    destination: Path,
) -> bool:
    if project_path is None:
        return False
    return destination.expanduser().resolve() == project_path.expanduser().resolve()


def split_segment(
    timeline: SegmentTimeline,
    position_seconds: float,
    *,
    segment_id: str | None = None,
    coordinate: str = "source",
) -> tuple[Segment, Segment]:
    if segment_id is not None:
        return timeline.split_block(
            segment_id,
            position_seconds,
            coordinate=coordinate,
        )
    if timeline.mixed_source:
        for segment in timeline.segment_items:
            if segment.timeline_start < position_seconds < segment.timeline_end:
                return timeline.split_block(
                    segment.segment_id,
                    position_seconds,
                    coordinate="timeline",
                )
        raise ProjectValidationError("Split position must be strictly inside one timeline block")
    if timeline.has_explicit_timeline:
        for segment in timeline.segment_items:
            if segment.timeline_start < position_seconds < segment.timeline_end:
                return timeline.split_block(
                    segment.segment_id,
                    position_seconds,
                    coordinate="timeline",
                )
        raise ProjectValidationError("Split position must be strictly inside one timeline block")
    return timeline.split(position_seconds)


def set_segment_deleted(
    timeline: SegmentTimeline,
    segment_id: str,
    deleted: bool,
) -> bool:
    timeline.set_deleted(segment_id, deleted)
    return deleted


def toggle_segment_deleted(
    timeline: SegmentTimeline,
    segment_id: str,
) -> bool:
    for segment in timeline.segment_items:
        if segment.segment_id == segment_id:
            return set_segment_deleted(
                timeline,
                segment_id,
                not segment.deleted,
            )
    raise ProjectValidationError(f"Unknown segment_id: {segment_id}")


def move_segment(
    project: Project,
    segment_id: str,
    direction: str | int,
) -> bool:
    return project.timeline.move_block(segment_id, direction)


def move_segments(
    project: Project,
    segment_ids: Sequence[str],
    direction: str | int,
) -> bool:
    return project.timeline.move_blocks(segment_ids, direction)


def copy_segments(
    project: Project,
    segment_ids: Sequence[str],
) -> tuple[Segment, ...]:
    return project.timeline.copy_blocks(segment_ids)


def paste_segments(
    project: Project,
    segments: Sequence[Segment],
    *,
    at_index: int | None = None,
    at_seconds: float | None = None,
) -> tuple[Segment, ...]:
    pasted = project.timeline.paste_blocks(
        segments,
        at_index=at_index,
        at_seconds=at_seconds,
    )
    project.duration_seconds = project.timeline.timeline_duration_seconds
    project.set_playhead(project.playhead_seconds)
    project.validate()
    return pasted


def paste_segments_after_selection(
    project: Project,
    segments: Sequence[Segment],
    selected_segment_id: str | None,
) -> tuple[Segment, ...]:
    if selected_segment_id is None:
        raise ProjectValidationError("Select a clip before pasting blocks")
    for index, segment in enumerate(project.timeline.segment_items):
        if segment.segment_id == selected_segment_id:
            return paste_segments(project, segments, at_index=index + 1)
    raise ProjectValidationError(f"Unknown segment_id: {selected_segment_id}")


def _validated_visual_transform(
    *,
    zoom: object,
    offset_x: object,
    offset_y: object,
) -> VisualTransform:
    try:
        return VisualTransform.clamped(
            zoom=zoom,
            offset_x=offset_x,
            offset_y=offset_y,
        )
    except ValueError as error:
        raise ProjectValidationError(str(error)) from error


def apply_visual_transform(
    project: Project,
    segment_ids: Sequence[str],
    *,
    zoom: object = 1.0,
    offset_x: object = 0.0,
    offset_y: object = 0.0,
) -> VisualTransform:
    transform = _validated_visual_transform(
        zoom=zoom,
        offset_x=offset_x,
        offset_y=offset_y,
    )
    project.timeline.set_visual_transform(segment_ids, transform)
    project.validate()
    return transform


def copy_visual_transform(
    project: Project,
    source_segment_id: str,
    destination_segment_ids: Sequence[str],
) -> VisualTransform:
    source = project.timeline.find(source_segment_id)
    transform = source.visual_transform
    project.timeline.set_visual_transform(destination_segment_ids, transform)
    project.validate()
    return transform


def clean_visual_modifications(
    project: Project,
    segment_ids: Sequence[str],
) -> None:
    project.timeline.clean_visual_modifications(segment_ids)
    project.validate()


def enable_triplicate(
    project: Project,
    segment_ids: Sequence[str],
) -> None:
    project.timeline.enable_triplicate(segment_ids)
    project.validate()


def disable_triplicate(
    project: Project,
    segment_ids: Sequence[str],
) -> None:
    project.timeline.disable_triplicate(segment_ids)
    project.validate()


def relink_project_source(
    project: Project,
    source_id: str,
    candidate_path: Path,
    metadata: Mapping[str, object] | None = None,
) -> SourceReference:
    return project.relink_source(source_id, candidate_path, metadata)


def analyze_project_audio(
    project: Project,
    *,
    ffmpeg_path: str = "ffmpeg",
) -> dict[str, AudioDecision]:
    decisions: dict[str, AudioDecision] = {}
    for source in project.sources or (project.source,):
        decision = analyze_source_audio(source, ffmpeg_path=ffmpeg_path)
        project.set_source_audio_settings(source.source_id, decision.to_dict())
        decisions[source.source_id] = decision
    project.validate()
    return decisions


def ensure_project_audio_analysis(
    project: Project,
    *,
    ffmpeg_path: str = "ffmpeg",
) -> dict[str, dict[str, object]]:
    decisions: dict[str, dict[str, object]] = {}
    for source in project.sources or (project.source,):
        settings = project.source_audio_settings(source.source_id)
        status = settings.get("status")
        if (
            status not in {"ready", "silent", "unsupported", "failed", "not-applicable"}
            or settings.get("policy_version") != AUDIO_POLICY_VERSION
            or audio_decision_is_stale(source, settings)
        ):
            decision = analyze_source_audio(source, ffmpeg_path=ffmpeg_path)
            settings = decision.to_dict()
            project.set_source_audio_settings(source.source_id, settings)
        decisions[source.source_id] = settings
    project.validate()
    return decisions


def plan_project_export(
    project: Project,
    destination: Path,
    *,
    ffprobe_path: str = "ffprobe",
    ffmpeg_path: str = "ffmpeg",
) -> ExportPlan:
    if project.segment_timeline is None:
        raise ValueError("Project segment timeline is required")
    audio_decisions = ensure_project_audio_analysis(
        project,
        ffmpeg_path=ffmpeg_path,
    )
    if project.segment_timeline.mixed_source:
        probes = tuple(
            probe_media(Path(source.path), ffprobe_path) for source in project.sources or ()
        )
        policy = resolve_output_policy(
            [probe.metadata() for probe in probes],
        )
        return plan_mixed_export(
            probes,
            project.segment_timeline,
            destination,
            policy=policy,
            source_ids=tuple(source.source_id for source in project.sources or ()),
            audio_decisions=audio_decisions,
        )
    media = probe_media(Path(project.source.path), ffprobe_path)
    timeline = SegmentTimeline.from_segments(
        project.segment_timeline.source_duration_seconds,
        project.segment_timeline.segment_items,
    )
    source_id = project.source.source_id
    return plan_export(
        media,
        timeline,
        destination,
        ffprobe_path=ffprobe_path,
        audio_source_id=source_id,
        audio_decision=audio_decisions.get(
            source_id,
            pending_audio_decision(project.source).to_dict(),
        ),
    )
