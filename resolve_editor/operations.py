from __future__ import annotations

from pathlib import Path

from .export import ExportPlan, plan_export
from .media import probe_media
from .model import (
    Project,
    ProjectValidationError,
    Segment,
    SegmentTimeline,
)


def create_project_from_source(
    source_path: Path,
    *,
    ffprobe_path: str = "ffprobe",
) -> Project:
    media = probe_media(source_path, ffprobe_path)
    return Project.create(source_path, media.metadata())


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
) -> tuple[Segment, Segment]:
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


def plan_project_export(
    project: Project,
    destination: Path,
    *,
    ffprobe_path: str = "ffprobe",
) -> ExportPlan:
    if project.segment_timeline is None:
        raise ValueError("Project segment timeline is required")
    media = probe_media(Path(project.source.path), ffprobe_path)
    timeline = SegmentTimeline.from_segments(
        project.segment_timeline.source_duration_seconds,
        project.segment_timeline.segment_items,
    )
    return plan_export(
        media,
        timeline,
        destination,
        ffprobe_path=ffprobe_path,
    )
