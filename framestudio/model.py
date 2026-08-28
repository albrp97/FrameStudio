"""Stable public facade for the editor project domain."""

from .composition import (
    CANVAS_HEIGHT,
    CANVAS_WIDTH,
    COMPOSITION_SCHEMA_VERSION,
    MAX_OFFSET_X,
    MAX_OFFSET_Y,
    MAX_ZOOM,
    MIN_ZOOM,
    TRIPLICATE_BACKGROUND,
    TRIPLICATE_LAYOUT,
    TRIPLICATE_ROLES,
    TRIPLICATE_SLOT_WIDTH,
    TriplicateGroup,
    TriplicateInstance,
    VisualTransform,
    focus_offset_bounds,
)
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
from .upscale_policy import (
    ResolvedUpscalePolicy,
    UpscaleDecision,
    UpscalePolicy,
    UpscalePolicyError,
)

ProjectTimeline = SegmentTimeline

__all__ = [
    "LEGACY_SCHEMA_VERSION",
    "ONE_SOURCE_SCHEMA_VERSION",
    "PROJECT_TIMEBASE",
    "SCHEMA_VERSION",
    "CANVAS_HEIGHT",
    "CANVAS_WIDTH",
    "COMPOSITION_SCHEMA_VERSION",
    "MAX_OFFSET_X",
    "MAX_OFFSET_Y",
    "MAX_ZOOM",
    "MIN_ZOOM",
    "TRIPLICATE_BACKGROUND",
    "TRIPLICATE_LAYOUT",
    "TRIPLICATE_ROLES",
    "TRIPLICATE_SLOT_WIDTH",
    "Project",
    "ProjectTimeline",
    "ProjectValidationError",
    "ResolvedUpscalePolicy",
    "Segment",
    "SegmentTimeline",
    "SourceReference",
    "SourceStatus",
    "TriplicateGroup",
    "TriplicateInstance",
    "UpscaleDecision",
    "UpscalePolicy",
    "UpscalePolicyError",
    "VisualTransform",
    "focus_offset_bounds",
    "seconds_to_ticks",
    "ticks_to_seconds",
]
