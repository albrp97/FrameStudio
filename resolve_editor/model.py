"""Stable public facade for the editor project domain."""

from .model_project import Project
from .model_timeline import SegmentTimeline
from .model_types import (
    LEGACY_SCHEMA_VERSION,
    ONE_SOURCE_SCHEMA_VERSION,
    PROJECT_TIMEBASE,
    SCHEMA_VERSION,
    ProjectValidationError,
    Segment,
    SourceReference,
    SourceStatus,
    seconds_to_ticks,
    ticks_to_seconds,
)

ProjectTimeline = SegmentTimeline

__all__ = [
    "LEGACY_SCHEMA_VERSION",
    "ONE_SOURCE_SCHEMA_VERSION",
    "PROJECT_TIMEBASE",
    "SCHEMA_VERSION",
    "Project",
    "ProjectTimeline",
    "ProjectValidationError",
    "Segment",
    "SegmentTimeline",
    "SourceReference",
    "SourceStatus",
    "seconds_to_ticks",
    "ticks_to_seconds",
]
