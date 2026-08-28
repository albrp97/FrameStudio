"""Focused local video editor foundation."""

from .audio import (
    AUDIO_POLICY_VERSION,
    LEGACY_AUDIO_POLICY,
    AudioDecision,
    AudioPolicy,
    AudioStats,
    analyze_audio,
    audio_gain_db,
)
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
    "AUDIO_POLICY_VERSION",
    "AudioDecision",
    "AudioPolicy",
    "AudioStats",
    "LEGACY_AUDIO_POLICY",
    "ProjectValidationError",
    "Segment",
    "SegmentTimeline",
    "ProjectTimeline",
    "SourceReference",
    "SourceStatus",
    "seconds_to_ticks",
    "ticks_to_seconds",
    "analyze_audio",
    "audio_gain_db",
]
