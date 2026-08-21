"""Focused local video editor foundation."""

from .model import (
    Project,
    ProjectValidationError,
    Segment,
    SegmentTimeline,
    SourceReference,
    SourceStatus,
)

__all__ = [
    "Project",
    "ProjectValidationError",
    "Segment",
    "SegmentTimeline",
    "SourceReference",
    "SourceStatus",
]
