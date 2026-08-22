from __future__ import annotations

import math
from dataclasses import dataclass

from .model import SegmentTimeline

TIMELINE_HORIZONTAL_PADDING = 12.0
TIMELINE_MIN_PIXELS_PER_SECOND = 8.0
TIMELINE_HEIGHT = 124
TIMELINE_RULER_HEIGHT = 34.0
TIMELINE_TRACK_Y = 44.0
TIMELINE_TRACK_HEIGHT = 54.0
TIMELINE_MIN_ZOOM = 1.0
TIMELINE_MAX_ZOOM = 12.0
SELECTED_CLIP_BORDER_COLOR = (
    246.0 / 255.0,
    193.0 / 255.0,
    119.0 / 255.0,
    1.0,
)
TIMELINE_ZOOM_LEVELS = (
    1.0,
    1.25,
    1.5,
    2.0,
    3.0,
    4.0,
    6.0,
    8.0,
    12.0,
)


@dataclass(frozen=True)
class TimelineClipGeometry:
    segment_id: str
    index: int
    start_seconds: float
    end_seconds: float
    timeline_start_seconds: float
    timeline_end_seconds: float
    source_id: str | None
    deleted: bool
    x: float
    width: float
    color_index: int = 0

    @property
    def end_x(self) -> float:
        return self.x + self.width


def _positive_float(value: float, label: str) -> float:
    parsed = float(value)
    if not math.isfinite(parsed) or parsed <= 0:
        raise ValueError(f"{label} must be greater than zero")
    return parsed


def clamp_timeline_zoom(zoom: float) -> float:
    parsed = _positive_float(zoom, "Timeline zoom")
    return max(TIMELINE_MIN_ZOOM, min(TIMELINE_MAX_ZOOM, parsed))


def next_timeline_zoom(zoom: float, direction: int) -> float:
    if direction not in (-1, 1):
        raise ValueError("Timeline zoom direction must be -1 or 1")
    current = clamp_timeline_zoom(zoom)
    if direction > 0:
        for level in TIMELINE_ZOOM_LEVELS:
            if level > current + 1e-9:
                return level
        return TIMELINE_MAX_ZOOM
    for level in reversed(TIMELINE_ZOOM_LEVELS):
        if level < current - 1e-9:
            return level
    return TIMELINE_MIN_ZOOM


def timeline_zoom_label(zoom: float) -> str:
    return f"{clamp_timeline_zoom(zoom) * 100:.0f}%"


def timeline_pixels_per_second(
    duration_seconds: float,
    viewport_width: float,
    zoom: float,
) -> float:
    duration = _positive_float(duration_seconds, "Timeline duration")
    viewport = _positive_float(viewport_width, "Timeline viewport width")
    usable_width = max(
        1.0,
        viewport - TIMELINE_HORIZONTAL_PADDING * 2,
    )
    return max(
        usable_width / duration,
        TIMELINE_MIN_PIXELS_PER_SECOND,
    ) * clamp_timeline_zoom(zoom)


def timeline_content_width(
    duration_seconds: float,
    viewport_width: float,
    zoom: float,
) -> float:
    viewport = _positive_float(viewport_width, "Timeline viewport width")
    pixels_per_second = timeline_pixels_per_second(
        duration_seconds,
        viewport,
        zoom,
    )
    return max(
        viewport,
        TIMELINE_HORIZONTAL_PADDING * 2
        + _positive_float(duration_seconds, "Timeline duration") * pixels_per_second,
    )


def layout_timeline_segments(
    timeline: SegmentTimeline,
    viewport_width: float,
    zoom: float,
) -> tuple[TimelineClipGeometry, ...]:
    timeline.validate()
    pixels_per_second = timeline_pixels_per_second(
        timeline.timeline_duration_seconds,
        viewport_width,
        zoom,
    )
    return tuple(
        TimelineClipGeometry(
            segment_id=segment.segment_id,
            index=index,
            start_seconds=segment.start_seconds,
            end_seconds=segment.end_seconds,
            timeline_start_seconds=segment.timeline_start,
            timeline_end_seconds=segment.timeline_end,
            source_id=segment.source_id,
            deleted=segment.deleted,
            x=TIMELINE_HORIZONTAL_PADDING + segment.timeline_start * pixels_per_second,
            width=max(
                1.0,
                (segment.timeline_end - segment.timeline_start) * pixels_per_second,
            ),
            color_index=segment.color_slot,
        )
        for index, segment in enumerate(timeline.segment_items)
    )


def timeline_position_from_x(
    x: float,
    duration_seconds: float,
    viewport_width: float,
    zoom: float,
) -> float:
    duration = _positive_float(duration_seconds, "Timeline duration")
    pixels_per_second = timeline_pixels_per_second(
        duration,
        viewport_width,
        zoom,
    )
    position = (float(x) - TIMELINE_HORIZONTAL_PADDING) / pixels_per_second
    return max(0.0, min(duration, position))


def hit_test_timeline_segment(
    clips: tuple[TimelineClipGeometry, ...],
    x: float,
) -> TimelineClipGeometry | None:
    position = float(x)
    for index, clip in enumerate(clips):
        if clip.x <= position < clip.end_x:
            return clip
        if index == len(clips) - 1 and math.isclose(
            position,
            clip.end_x,
            rel_tol=0.0,
            abs_tol=1e-9,
        ):
            return clip
    return None


def timeline_tick_interval(
    duration_seconds: float,
    pixels_per_second: float,
) -> float:
    duration = _positive_float(duration_seconds, "Timeline duration")
    pixels_per_second = _positive_float(
        pixels_per_second,
        "Timeline pixels per second",
    )
    target_seconds = 90.0 / pixels_per_second
    magnitude = float(10 ** math.floor(math.log10(target_seconds)))
    for multiplier in (1.0, 2.0, 5.0, 10.0):
        interval = multiplier * magnitude
        if interval >= target_seconds:
            return min(interval, duration)
    return duration
