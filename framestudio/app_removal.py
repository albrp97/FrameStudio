from __future__ import annotations

from collections.abc import Sequence

from .model import Project, ProjectValidationError, Segment, SegmentTimeline
from .operations import remove_blocks, undo_removed_blocks
from .removal_history import RemovalReceipt, RemovalUndoResult

__all__ = [
    "remove_selected_blocks",
    "toggle_selected_exclusion",
    "undo_last_removal",
]


def _timeline_for(project: Project) -> SegmentTimeline:
    timeline = project.segment_timeline
    if timeline is None:
        raise ProjectValidationError("Project segment timeline is required")
    return timeline


def _selected_segments(
    project: Project,
    selected_segment_ids: Sequence[str],
) -> tuple[Segment, ...]:
    timeline = _timeline_for(project)
    selected_ids = tuple(selected_segment_ids)
    if not selected_ids:
        raise ProjectValidationError("Select at least one clip")
    if len(set(selected_ids)) != len(selected_ids):
        raise ProjectValidationError("Selected clip identifiers must be unique")
    return tuple(timeline.find(segment_id) for segment_id in selected_ids)


def remove_selected_blocks(
    project: Project,
    selected_segment_ids: Sequence[str],
    *,
    focused_segment_id: str | None = None,
) -> RemovalReceipt:
    """Remove selected blocks through the bounded T110 removal receipt boundary."""
    selected = _selected_segments(project, selected_segment_ids)
    selected_ids = tuple(segment.segment_id for segment in selected)
    focused = focused_segment_id
    if focused is not None and focused not in selected_ids:
        raise ProjectValidationError("Focused clip must be part of the selection")
    if project.timeline.tracks is None:
        project._migrate_legacy_to_v4()
    return remove_blocks(
        project,
        selected_ids,
        selection_ids=selected_ids,
        focused_segment_id=focused,
    )


def undo_last_removal(
    project: Project,
    receipt: RemovalReceipt,
) -> RemovalUndoResult:
    """Undo one valid in-memory removal receipt, never a serialized history token."""
    _timeline_for(project)
    return undo_removed_blocks(project, receipt)


def toggle_selected_exclusion(
    project: Project,
    selected_segment_ids: Sequence[str],
) -> bool:
    """Preserve blocks while toggling their existing Delete exclusion state."""
    selected = _selected_segments(project, selected_segment_ids)
    deleted = not all(segment.deleted for segment in selected)
    timeline = _timeline_for(project)
    for segment in selected:
        timeline.set_deleted(segment.segment_id, deleted)
    project.validate()
    return deleted
