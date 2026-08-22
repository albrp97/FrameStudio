"""Focused local video editor foundation."""

from .model import (
    Project,
    ProjectTimeline,
    ProjectValidationError,
    Segment,
    SegmentTimeline,
    SourceReference,
    SourceStatus,
    seconds_to_ticks,
    ticks_to_seconds,
)

__all__ = [
    "Project",
    "ProjectValidationError",
    "Segment",
    "SegmentTimeline",
    "ProjectTimeline",
    "SourceReference",
    "SourceStatus",
    "seconds_to_ticks",
    "ticks_to_seconds",
]
