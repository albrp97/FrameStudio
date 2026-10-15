from __future__ import annotations

import math
from bisect import bisect_left, bisect_right
from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

from .model import SegmentTimeline
from .model_types import seconds_to_ticks, ticks_to_seconds

TIMELINE_HORIZONTAL_PADDING = 12.0
TIMELINE_MIN_PIXELS_PER_SECOND = 8.0
TIMELINE_HEIGHT = 124
TIMELINE_RULER_HEIGHT = 34.0
TIMELINE_TRACK_Y = 44.0
TIMELINE_TRACK_HEIGHT = 54.0
TIMELINE_TRACK_GAP = 0.0
TIMELINE_TRACK_HEADER_HEIGHT = 18.0
TIMELINE_CANVAS_BOTTOM_PADDING = 12.0
TIMELINE_MIN_ZOOM = 0.5
TIMELINE_DEFAULT_ZOOM = 1.0
TIMELINE_MAX_ZOOM = 12.0
SELECTED_CLIP_BORDER_COLOR = (
    246.0 / 255.0,
    193.0 / 255.0,
    119.0 / 255.0,
    1.0,
)
TIMELINE_ZOOM_LEVELS = (
    0.5,
    0.75,
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
TIMELINE_FIT_WINDOW_SECONDS = 30.0 * 60.0
TIMELINE_START_SNAP_FRACTION = 0.1
TIMELINE_START_SNAP_MAX_PIXELS = 16.0
TIMELINE_CLIP_BADGE_RADIUS = 9.0


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
    track_id: str = "track-1"
    track_index: int = 0
    y: float = TIMELINE_TRACK_Y + TIMELINE_TRACK_HEADER_HEIGHT + 2.0
    height: float = TIMELINE_TRACK_HEIGHT - TIMELINE_TRACK_HEADER_HEIGHT - 8.0
    timeline_width: float | None = None

    @property
    def snap_width(self) -> float:
        width = self.width if self.timeline_width is None else self.timeline_width
        return min(
            TIMELINE_START_SNAP_MAX_PIXELS,
            max(0.0, min(self.width, width)) * TIMELINE_START_SNAP_FRACTION,
        )

    @property
    def end_x(self) -> float:
        return self.x + self.width

    @property
    def end_y(self) -> float:
        return self.y + self.height

    @property
    def badge_center(self) -> tuple[float, float] | None:
        if self.width < 22.0:
            return None
        return min(self.x + 12.0, self.end_x - 11.0), self.y

    def contains_point(self, x: float, y: float) -> bool:
        if self.x <= x < self.end_x and self.y <= y < self.end_y:
            return True
        center = self.badge_center
        return center is not None and (
            (x - center[0]) ** 2 + (y - center[1]) ** 2 <= TIMELINE_CLIP_BADGE_RADIUS**2
        )


@dataclass(frozen=True)
class TimelineTrackGeometry:
    track_id: str
    index: int
    y: float
    height: float = TIMELINE_TRACK_HEIGHT
    active: bool = False

    @property
    def end_y(self) -> float:
        return self.y + self.height


@dataclass(frozen=True)
class _TimelineViewRow:
    top: float
    bottom: float
    entries: tuple[tuple[int, TimelineClipGeometry], ...]
    starts: tuple[float, ...]
    prefix_ends: tuple[float, ...]


@dataclass(frozen=True)
class TimelineViewIndex:
    """Immutable viewport lookup retaining the layout's original paint order."""

    rows: tuple[_TimelineViewRow, ...]
    tops: tuple[float, ...]
    prefix_bottoms: tuple[float, ...]
    _clips_by_segment: Mapping[str, TimelineClipGeometry]

    @classmethod
    def from_clips(cls, clips: tuple[TimelineClipGeometry, ...]) -> TimelineViewIndex:
        grouped: dict[tuple[float, float], list[tuple[int, TimelineClipGeometry]]] = {}
        by_segment: dict[str, TimelineClipGeometry] = {}
        for ordinal, clip in enumerate(clips):
            # Index the same expanded bounds used by the existing draw culling,
            # including one-pixel minimum widths, badges, and selected borders.
            grouped.setdefault((clip.y - 12, clip.end_y + 12), []).append((ordinal, clip))
            by_segment[clip.segment_id] = clip
        rows = []
        for (top, bottom), entries in sorted(grouped.items()):
            entries.sort(key=lambda entry: entry[1].x - 12)
            prefix_ends = []
            end = -math.inf
            for _ordinal, clip in entries:
                end = max(end, clip.end_x + 12)
                prefix_ends.append(end)
            rows.append(
                _TimelineViewRow(
                    top,
                    bottom,
                    tuple(entries),
                    tuple(clip.x - 12 for _ordinal, clip in entries),
                    tuple(prefix_ends),
                )
            )
        prefix_bottoms = []
        bottom = -math.inf
        for row in rows:
            bottom = max(bottom, row.bottom)
            prefix_bottoms.append(bottom)
        return cls(
            tuple(rows),
            tuple(row.top for row in rows),
            tuple(prefix_bottoms),
            MappingProxyType(by_segment),
        )

    def clip_for_segment(self, segment_id: str) -> TimelineClipGeometry | None:
        return self._clips_by_segment.get(segment_id)

    def query(
        self, left: float, top: float, right: float, bottom: float
    ) -> tuple[TimelineClipGeometry, ...]:
        visible = []
        first_row = bisect_left(self.prefix_bottoms, top)
        last_row = bisect_right(self.tops, bottom)
        for row in self.rows[first_row:last_row]:
            if row.bottom < top:
                continue
            first = bisect_left(row.prefix_ends, left)
            last = bisect_right(row.starts, right)
            for ordinal, clip in row.entries[first:last]:
                if clip.end_x + 12 >= left:
                    visible.append((ordinal, clip))
        visible.sort(key=lambda entry: entry[0])
        return tuple(clip for _ordinal, clip in visible)


def _positive_float(value: float, label: str) -> float:
    parsed = float(value)
    if not math.isfinite(parsed) or parsed <= 0:
        raise ValueError(f"{label} must be greater than zero")
    return parsed


def _nonnegative_finite_float(value: float, label: str) -> float:
    parsed = float(value)
    if not math.isfinite(parsed) or parsed < 0:
        raise ValueError(f"{label} must be finite and non-negative")
    return parsed


def clamp_timeline_zoom(zoom: float) -> float:
    parsed = _positive_float(zoom, "Timeline zoom")
    return max(TIMELINE_MIN_ZOOM, parsed)


def next_timeline_zoom(zoom: float, direction: int) -> float:
    if direction not in (-1, 1):
        raise ValueError("Timeline zoom direction must be -1 or 1")
    current = clamp_timeline_zoom(zoom)
    if direction > 0:
        for level in TIMELINE_ZOOM_LEVELS:
            if level > current + 1e-9:
                return level
        return current * 1.5
    for level in reversed(TIMELINE_ZOOM_LEVELS):
        if level < current - 1e-9:
            return level
    return TIMELINE_MIN_ZOOM


def timeline_zoom_label(zoom: float) -> str:
    return f"{_positive_float(zoom, 'Timeline zoom') * 100:.0f}%"


def timeline_zoom_for_window(
    duration_seconds: float,
    window_seconds: float,
) -> float:
    duration = _positive_float(duration_seconds, "Timeline duration")
    window = _positive_float(window_seconds, "Timeline fit window")
    return duration / window


def timeline_pixels_per_second(
    duration_seconds: float,
    viewport_width: float,
    zoom: float,
) -> float:
    duration = _nonnegative_finite_float(duration_seconds, "Timeline duration")
    viewport = _positive_float(viewport_width, "Timeline viewport width")
    usable_width = max(
        1.0,
        viewport - TIMELINE_HORIZONTAL_PADDING * 2,
    )
    scale_duration = max(duration, 1e-9)
    return (usable_width / scale_duration) * _positive_float(zoom, "Timeline zoom")


def timeline_content_width(
    duration_seconds: float,
    viewport_width: float,
    zoom: float,
) -> float:
    duration = _nonnegative_finite_float(duration_seconds, "Timeline duration")
    viewport = _positive_float(viewport_width, "Timeline viewport width")
    pixels_per_second = timeline_pixels_per_second(
        duration,
        viewport,
        zoom,
    )
    return max(
        TIMELINE_HORIZONTAL_PADDING * 2,
        duration * pixels_per_second + TIMELINE_HORIZONTAL_PADDING * 2,
    )


def timeline_content_height(track_count: int) -> float:
    if not isinstance(track_count, int) or isinstance(track_count, bool) or track_count < 1:
        raise ValueError("Timeline track count must be a positive integer")
    return (
        TIMELINE_TRACK_Y
        + track_count * TIMELINE_TRACK_HEIGHT
        + (track_count - 1) * TIMELINE_TRACK_GAP
        + TIMELINE_CANVAS_BOTTOM_PADDING
    )


def _track_ids(timeline: SegmentTimeline) -> tuple[str, ...]:
    if timeline.tracks is None:
        return ("track-1",)
    return timeline.track_ids


def layout_timeline_tracks(
    timeline: SegmentTimeline,
) -> tuple[TimelineTrackGeometry, ...]:
    track_ids = _track_ids(timeline)
    active_track_id = timeline.active_track_id
    return tuple(
        TimelineTrackGeometry(
            track_id=track_id,
            index=index,
            y=TIMELINE_TRACK_Y + index * (TIMELINE_TRACK_HEIGHT + TIMELINE_TRACK_GAP),
            active=active_track_id == track_id,
        )
        for index, track_id in enumerate(track_ids)
    )


def timeline_track_id_at_y(
    timeline: SegmentTimeline,
    y: float,
) -> str | None:
    position = float(y)
    for row in layout_timeline_tracks(timeline):
        if row.y <= position < row.end_y:
            return row.track_id
    return None


def timeline_track_index_at_y(
    timeline: SegmentTimeline,
    y: float,
) -> int | None:
    position = float(y)
    for row in layout_timeline_tracks(timeline):
        if row.y <= position < row.end_y:
            return row.index
    return None


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
    rows = layout_timeline_tracks(timeline)
    clips: list[TimelineClipGeometry] = []
    index = 0
    for row in rows:
        if timeline.tracks is None:
            segments = timeline.segment_items
        else:
            segments = timeline.track_by_id(row.track_id).blocks
        for segment in segments:
            clips.append(
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
                    timeline_width=(segment.timeline_end - segment.timeline_start)
                    * pixels_per_second,
                    color_index=segment.color_slot,
                    track_id=row.track_id,
                    track_index=row.index,
                    y=row.y + TIMELINE_TRACK_HEADER_HEIGHT + 2.0,
                    height=TIMELINE_TRACK_HEIGHT - TIMELINE_TRACK_HEADER_HEIGHT - 8.0,
                )
            )
            index += 1
    return tuple(clips)


def timeline_position_from_x(
    x: float,
    duration_seconds: float,
    viewport_width: float,
    zoom: float,
) -> float:
    duration = _nonnegative_finite_float(duration_seconds, "Timeline duration")
    position_x = float(x)
    if not math.isfinite(position_x):
        raise ValueError("Timeline x position must be finite")
    if duration <= 0.0:
        return 0.0
    pixels_per_second = timeline_pixels_per_second(
        duration,
        viewport_width,
        zoom,
    )
    position = (position_x - TIMELINE_HORIZONTAL_PADDING) / pixels_per_second
    return max(0.0, min(duration, position))


def timeline_ticks_from_x(
    x: float,
    duration_seconds: float,
    viewport_width: float,
    zoom: float,
) -> int:
    return seconds_to_ticks(
        timeline_position_from_x(
            x,
            duration_seconds,
            viewport_width,
            zoom,
        )
    )


def timeline_drag_ticks_from_x(
    x: float,
    duration_seconds: float,
    viewport_width: float,
    zoom: float,
) -> int:
    """Map a drag pointer to non-negative absolute ticks without an end clamp."""
    duration = _nonnegative_finite_float(duration_seconds, "Timeline duration")
    position_x = float(x)
    if not math.isfinite(position_x):
        raise ValueError("Timeline x position must be finite")
    pixels_per_second = timeline_pixels_per_second(
        duration,
        viewport_width,
        zoom,
    )
    position = max(0.0, (position_x - TIMELINE_HORIZONTAL_PADDING) / pixels_per_second)
    return seconds_to_ticks(position)


def timeline_x_from_ticks(
    ticks: int,
    duration_seconds: float,
    viewport_width: float,
    zoom: float,
) -> float:
    return TIMELINE_HORIZONTAL_PADDING + ticks_to_seconds(ticks) * timeline_pixels_per_second(
        duration_seconds,
        viewport_width,
        zoom,
    )


def hit_test_timeline_segment(
    clips: tuple[TimelineClipGeometry, ...],
    x: float,
    y: float | None = None,
) -> TimelineClipGeometry | None:
    position = float(x)
    for index, clip in enumerate(clips):
        if (
            clip.x <= position < clip.end_x
            if y is None
            else clip.contains_point(position, float(y))
        ):
            return clip
        if (
            index == len(clips) - 1
            and math.isclose(
                position,
                clip.end_x,
                rel_tol=0.0,
                abs_tol=1e-9,
            )
            and (y is None or clip.y <= float(y) <= clip.end_y)
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
