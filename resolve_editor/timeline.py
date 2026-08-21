from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Callable

from .model import SegmentTimeline
from .ui import format_duration

TIMELINE_HORIZONTAL_PADDING = 12.0
TIMELINE_MIN_PIXELS_PER_SECOND = 8.0
TIMELINE_HEIGHT = 124
TIMELINE_RULER_HEIGHT = 34.0
TIMELINE_TRACK_Y = 44.0
TIMELINE_TRACK_HEIGHT = 54.0
TIMELINE_MIN_ZOOM = 1.0
TIMELINE_MAX_ZOOM = 12.0
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
    deleted: bool
    x: float
    width: float

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
        timeline.source_duration_seconds,
        viewport_width,
        zoom,
    )
    return tuple(
        TimelineClipGeometry(
            segment_id=segment.segment_id,
            index=index,
            start_seconds=segment.start_seconds,
            end_seconds=segment.end_seconds,
            deleted=segment.deleted,
            x=TIMELINE_HORIZONTAL_PADDING + segment.start_seconds * pixels_per_second,
            width=max(
                1.0,
                (segment.end_seconds - segment.start_seconds) * pixels_per_second,
            ),
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


def create_timeline_canvas(gtk_module: Any) -> Any:
    class TimelineCanvas(gtk_module.DrawingArea):
        def __init__(
            self,
            on_seek: Callable[[float], None] | None = None,
            on_segment_selected: Callable[[str], None] | None = None,
        ) -> None:
            super().__init__()
            self._timeline: SegmentTimeline | None = None
            self._selected_segment_id: str | None = None
            self._playhead_seconds = 0.0
            self._zoom = TIMELINE_MIN_ZOOM
            self._viewport_width = 800.0
            self._on_seek = on_seek
            self._on_segment_selected = on_segment_selected
            self._drag_start_x: float | None = None
            self._drag_happened = False
            self.set_focusable(True)
            self.set_hexpand(False)
            self.set_vexpand(False)
            self.set_draw_func(self._draw)
            self._click_gesture = gtk_module.GestureClick()
            self._click_gesture.set_button(1)
            self._click_gesture.set_exclusive(False)
            self._click_gesture.connect("pressed", self._on_pressed)
            self._click_gesture.connect("released", self._on_released)
            self.add_controller(self._click_gesture)
            self._drag_gesture = gtk_module.GestureDrag()
            self._drag_gesture.set_button(1)
            self._drag_gesture.connect("drag-begin", self._on_drag_begin)
            self._drag_gesture.connect("drag-update", self._on_drag_update)
            self._drag_gesture.connect("drag-end", self._on_drag_end)
            self.add_controller(self._drag_gesture)
            self._recalculate_content_size()

        def set_timeline(
            self,
            timeline: SegmentTimeline | None,
            selected_segment_id: str | None = None,
        ) -> None:
            self._timeline = timeline
            self._selected_segment_id = selected_segment_id
            if timeline is not None:
                self._playhead_seconds = max(
                    0.0,
                    min(
                        timeline.source_duration_seconds,
                        self._playhead_seconds,
                    ),
                )
            else:
                self._playhead_seconds = 0.0
            self._recalculate_content_size()

        def set_viewport_width(self, width: float) -> None:
            parsed = max(1.0, float(width))
            if math.isclose(parsed, self._viewport_width, rel_tol=0.0, abs_tol=0.5):
                return
            self._viewport_width = parsed
            self._recalculate_content_size()

        def set_playhead(self, position_seconds: float) -> None:
            if self._timeline is None:
                self._playhead_seconds = max(0.0, float(position_seconds))
            else:
                self._playhead_seconds = max(
                    0.0,
                    min(
                        self._timeline.source_duration_seconds,
                        float(position_seconds),
                    ),
                )
            self.queue_draw()

        def set_selected_segment(self, segment_id: str | None) -> None:
            self._selected_segment_id = segment_id
            self.queue_draw()

        def set_zoom(self, zoom: float) -> None:
            parsed = clamp_timeline_zoom(zoom)
            if math.isclose(parsed, self._zoom, rel_tol=0.0, abs_tol=1e-9):
                return
            self._zoom = parsed
            self._recalculate_content_size()

        def zoom_in(self) -> None:
            self.set_zoom(next_timeline_zoom(self._zoom, 1))

        def zoom_out(self) -> None:
            self.set_zoom(next_timeline_zoom(self._zoom, -1))

        def fit_to_view(self) -> None:
            self.set_zoom(TIMELINE_MIN_ZOOM)

        def get_zoom(self) -> float:
            return self._zoom

        def get_content_width(self) -> float:
            if self._timeline is None:
                return self._viewport_width
            return timeline_content_width(
                self._timeline.source_duration_seconds,
                self._viewport_width,
                self._zoom,
            )

        def has_horizontal_overflow(self) -> bool:
            return self.get_content_width() > self._viewport_width + 1.0

        def _recalculate_content_size(self) -> None:
            self.set_size_request(
                max(1, math.ceil(self.get_content_width())),
                TIMELINE_HEIGHT,
            )
            self.queue_draw()

        def _on_pressed(
            self,
            _gesture,
            _n_press: int,
            x: float,
            _y: float,
        ) -> None:
            self._drag_happened = False
            self._seek_from_x(x, notify=False)

        def _on_released(
            self,
            _gesture,
            _n_press: int,
            x: float,
            _y: float,
        ) -> None:
            if not self._drag_happened:
                self._seek_from_x(x, notify=True)
            self._drag_happened = False

        def _on_drag_begin(
            self,
            _gesture,
            start_x: float,
            _start_y: float,
        ) -> None:
            self._drag_happened = True
            self._drag_start_x = start_x
            self._seek_from_x(start_x, notify=True)

        def _on_drag_update(
            self,
            _gesture,
            offset_x: float,
            _offset_y: float,
        ) -> None:
            if self._drag_start_x is not None:
                self._seek_from_x(
                    self._drag_start_x + offset_x,
                    notify=True,
                )

        def _on_drag_end(
            self,
            _gesture,
            _offset_x: float,
            _offset_y: float,
        ) -> None:
            if self._drag_start_x is not None:
                self._seek_from_x(
                    self._drag_start_x + _offset_x,
                    notify=True,
                )
            self._drag_start_x = None

        def _seek_from_x(self, x: float, *, notify: bool) -> None:
            if self._timeline is None:
                return
            self.grab_focus()
            clips = layout_timeline_segments(
                self._timeline,
                self._viewport_width,
                self._zoom,
            )
            clip = hit_test_timeline_segment(clips, x)
            if clip is not None and clip.segment_id != self._selected_segment_id:
                self._selected_segment_id = clip.segment_id
                if self._on_segment_selected is not None:
                    self._on_segment_selected(clip.segment_id)
            position = timeline_position_from_x(
                x,
                self._timeline.source_duration_seconds,
                self._viewport_width,
                self._zoom,
            )
            self.set_playhead(position)
            if notify and self._on_seek is not None:
                self._on_seek(position)
            self.queue_draw()

        def _draw(self, _area, context, width: int, height: int) -> None:
            context.set_source_rgb(0.055, 0.063, 0.10)
            context.paint()
            if self._timeline is None:
                self._draw_text(
                    context,
                    "Select a video to build the timeline",
                    16.0,
                    24.0,
                    0.65,
                    0.68,
                    0.78,
                    14.0,
                )
                return

            pixels_per_second = timeline_pixels_per_second(
                self._timeline.source_duration_seconds,
                self._viewport_width,
                self._zoom,
            )
            self._draw_ruler(
                context,
                self._timeline.source_duration_seconds,
                pixels_per_second,
                width,
            )
            self._draw_track(context, width)
            clips = layout_timeline_segments(
                self._timeline,
                self._viewport_width,
                self._zoom,
            )
            for clip in clips:
                self._draw_clip(context, clip)
            self._draw_playhead(context, pixels_per_second)

        def _draw_ruler(
            self,
            context,
            duration_seconds: float,
            pixels_per_second: float,
            width: int,
        ) -> None:
            self._draw_text(
                context,
                "ORIGINAL SOURCE",
                TIMELINE_HORIZONTAL_PADDING,
                15.0,
                0.55,
                0.62,
                0.78,
                10.0,
            )
            interval = timeline_tick_interval(
                duration_seconds,
                pixels_per_second,
            )
            current = 0.0
            while current <= duration_seconds + 1e-9:
                x = TIMELINE_HORIZONTAL_PADDING + current * pixels_per_second
                if x > width + 1.0:
                    break
                context.set_source_rgba(0.55, 0.60, 0.72, 0.55)
                context.set_line_width(1.0)
                context.move_to(x, 24.0)
                context.line_to(x, TIMELINE_TRACK_Y - 4.0)
                context.stroke()
                self._draw_text(
                    context,
                    format_duration(current),
                    x + 3.0,
                    31.0,
                    0.56,
                    0.61,
                    0.72,
                    10.0,
                )
                current += interval

        def _draw_track(self, context, width: int) -> None:
            context.set_source_rgba(0.09, 0.105, 0.16, 0.96)
            context.rectangle(
                TIMELINE_HORIZONTAL_PADDING,
                TIMELINE_TRACK_Y,
                max(1.0, width - TIMELINE_HORIZONTAL_PADDING * 2),
                TIMELINE_TRACK_HEIGHT,
            )
            context.fill()
            context.set_source_rgba(0.35, 0.39, 0.52, 0.65)
            context.set_line_width(1.0)
            context.rectangle(
                TIMELINE_HORIZONTAL_PADDING,
                TIMELINE_TRACK_Y,
                max(1.0, width - TIMELINE_HORIZONTAL_PADDING * 2),
                TIMELINE_TRACK_HEIGHT,
            )
            context.stroke()

        def _draw_clip(self, context, clip: TimelineClipGeometry) -> None:
            y = TIMELINE_TRACK_Y + 3.0
            height = TIMELINE_TRACK_HEIGHT - 6.0
            if clip.deleted:
                fill = (0.22, 0.12, 0.18, 0.96)
                border = (0.82, 0.28, 0.38, 0.95)
            else:
                palette = (
                    (0.45, 0.29, 0.22),
                    (0.28, 0.46, 0.25),
                    (0.21, 0.38, 0.54),
                    (0.42, 0.30, 0.52),
                )
                red, green, blue = palette[clip.index % len(palette)]
                fill = (red, green, blue, 0.96)
                border = (0.72, 0.79, 0.92, 0.82)

            self._rounded_rectangle(
                context,
                clip.x,
                y,
                clip.width,
                height,
                5.0,
            )
            context.set_source_rgba(*fill)
            context.fill_preserve()
            context.set_source_rgba(*border)
            context.set_line_width(2.0 if clip.segment_id == self._selected_segment_id else 1.0)
            context.stroke()

            if clip.deleted:
                context.save()
                context.rectangle(clip.x, y, clip.width, height)
                context.clip()
                context.set_source_rgba(0.90, 0.34, 0.42, 0.48)
                context.set_line_width(1.0)
                offset = -height
                while offset < clip.width + height:
                    context.move_to(clip.x + offset, y + height)
                    context.line_to(clip.x + offset + height, y)
                    context.stroke()
                    offset += 10.0
                context.restore()

            if clip.width >= 22.0:
                bubble_x = min(
                    clip.x + 12.0,
                    clip.end_x - 11.0,
                )
                context.set_source_rgba(0.08, 0.09, 0.14, 0.92)
                context.arc(bubble_x, y, 9.0, 0.0, math.tau)
                context.fill()
                self._draw_text(
                    context,
                    str(clip.index + 1),
                    bubble_x - 3.0,
                    y + 3.5,
                    0.92,
                    0.94,
                    1.0,
                    10.0,
                )

            if clip.width >= 74.0:
                label = "DELETED" if clip.deleted else "INCLUDED"
                self._draw_text(
                    context,
                    label,
                    clip.x + 8.0,
                    y + 34.0,
                    0.94,
                    0.95,
                    1.0,
                    9.0,
                )
            if clip.width >= 126.0:
                self._draw_text(
                    context,
                    f"{format_duration(clip.start_seconds)} - {format_duration(clip.end_seconds)}",
                    clip.x + 8.0,
                    y + height - 7.0,
                    0.78,
                    0.82,
                    0.92,
                    9.0,
                )

            if clip.index > 0:
                context.set_source_rgba(0.84, 0.88, 0.98, 0.62)
                context.set_line_width(1.0)
                context.move_to(clip.x, TIMELINE_TRACK_Y - 5.0)
                context.line_to(clip.x, TIMELINE_TRACK_Y + 2.0)
                context.stroke()

        def _draw_playhead(self, context, pixels_per_second: float) -> None:
            x = TIMELINE_HORIZONTAL_PADDING + self._playhead_seconds * pixels_per_second
            context.set_source_rgba(0.96, 0.97, 1.0, 0.95)
            context.set_line_width(1.5)
            context.move_to(x, TIMELINE_RULER_HEIGHT - 4.0)
            context.line_to(x, TIMELINE_TRACK_Y + TIMELINE_TRACK_HEIGHT + 7.0)
            context.stroke()
            context.set_source_rgba(0.95, 0.28, 0.34, 1.0)
            context.move_to(x - 6.0, 23.0)
            context.line_to(x + 6.0, 23.0)
            context.line_to(x, 31.0)
            context.close_path()
            context.fill()

        @staticmethod
        def _rounded_rectangle(context, x, y, width, height, radius) -> None:
            radius = min(radius, width / 2.0, height / 2.0)
            context.new_sub_path()
            context.arc(
                x + width - radius,
                y + radius,
                radius,
                -math.pi / 2,
                0,
            )
            context.arc(
                x + width - radius,
                y + height - radius,
                radius,
                0,
                math.pi / 2,
            )
            context.arc(
                x + radius,
                y + height - radius,
                radius,
                math.pi / 2,
                math.pi,
            )
            context.arc(
                x + radius,
                y + radius,
                radius,
                math.pi,
                math.pi * 1.5,
            )
            context.close_path()

        @staticmethod
        def _draw_text(
            context,
            text: str,
            x: float,
            y: float,
            red: float,
            green: float,
            blue: float,
            size: float,
        ) -> None:
            context.set_source_rgb(red, green, blue)
            context.select_font_face("Sans")
            context.set_font_size(size)
            context.move_to(x, y)
            context.show_text(text)

    return TimelineCanvas
