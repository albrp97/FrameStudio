from __future__ import annotations

import math
from typing import Any, Callable

from .model import SegmentTimeline
from .timeline_geometry import (
    SELECTED_CLIP_BORDER_COLOR,
    TIMELINE_DEFAULT_ZOOM,
    TIMELINE_FIT_WINDOW_SECONDS,
    TIMELINE_HEIGHT,
    TIMELINE_HORIZONTAL_PADDING,
    TIMELINE_MAX_ZOOM,
    TIMELINE_MIN_PIXELS_PER_SECOND,
    TIMELINE_MIN_ZOOM,
    TIMELINE_RULER_HEIGHT,
    TIMELINE_TRACK_HEIGHT,
    TIMELINE_TRACK_Y,
    TIMELINE_ZOOM_LEVELS,
    TimelineClipGeometry,
    clamp_timeline_zoom,
    hit_test_timeline_segment,
    layout_timeline_segments,
    next_timeline_zoom,
    timeline_content_width,
    timeline_pixels_per_second,
    timeline_position_from_x,
    timeline_tick_interval,
    timeline_zoom_for_window,
    timeline_zoom_label,
)
from .timeline_rendering import (
    draw_clip,
    draw_playhead,
    draw_ruler,
    draw_text,
    draw_track,
    rounded_rectangle,
)

__all__ = [
    "SELECTED_CLIP_BORDER_COLOR",
    "TIMELINE_HEIGHT",
    "TIMELINE_HORIZONTAL_PADDING",
    "TIMELINE_DEFAULT_ZOOM",
    "TIMELINE_FIT_WINDOW_SECONDS",
    "TIMELINE_MAX_ZOOM",
    "TIMELINE_MIN_PIXELS_PER_SECOND",
    "TIMELINE_MIN_ZOOM",
    "TIMELINE_RULER_HEIGHT",
    "TIMELINE_TRACK_HEIGHT",
    "TIMELINE_TRACK_Y",
    "TIMELINE_ZOOM_LEVELS",
    "TimelineClipGeometry",
    "clamp_timeline_zoom",
    "create_timeline_canvas",
    "hit_test_timeline_segment",
    "layout_timeline_segments",
    "next_timeline_zoom",
    "timeline_content_width",
    "timeline_pixels_per_second",
    "timeline_position_from_x",
    "timeline_tick_interval",
    "timeline_zoom_for_window",
    "timeline_zoom_label",
]


def create_timeline_canvas(gtk_module: Any) -> Any:
    class TimelineCanvas(gtk_module.DrawingArea):
        def __init__(
            self,
            on_seek: Callable[[float], None] | None = None,
            on_segment_selected: Callable[[str], None] | None = None,
            on_selection_changed: Callable[[tuple[str, ...]], None] | None = None,
            selection_modifier_mask: int = 0,
            range_selection_modifier_mask: int = 0,
        ) -> None:
            super().__init__()
            self._timeline: SegmentTimeline | None = None
            self._selected_segment_id: str | None = None
            self._selected_segment_ids: tuple[str, ...] = ()
            self._playhead_seconds = 0.0
            self._zoom = TIMELINE_DEFAULT_ZOOM
            self._fit_window_seconds: float | None = None
            self._viewport_width = 800.0
            self._on_seek = on_seek
            self._on_segment_selected = on_segment_selected
            self._on_selection_changed = on_selection_changed
            self._selection_modifier_mask = int(selection_modifier_mask)
            self._range_selection_modifier_mask = int(range_selection_modifier_mask)
            self._drag_start_x: float | None = None
            self._drag_happened = False
            self._pressed_selection_additive = False
            self._pressed_selection_range = False
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
            selected_segment_ids: tuple[str, ...] | list[str] | None = None,
        ) -> None:
            self._timeline = timeline
            selected_ids: tuple[str, ...]
            if selected_segment_ids is None:
                selected_ids = () if selected_segment_id is None else (selected_segment_id,)
            else:
                selected_ids = tuple(selected_segment_ids)
            self._set_selection(selected_ids, selected_segment_id, notify=False)
            if timeline is not None:
                self._playhead_seconds = max(
                    0.0,
                    min(
                        timeline.timeline_duration_seconds,
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
                        self._timeline.timeline_duration_seconds,
                        float(position_seconds),
                    ),
                )
            self.queue_draw()

        def set_selected_segment(self, segment_id: str | None) -> None:
            self._set_selection(
                () if segment_id is None else (segment_id,),
                segment_id,
                notify=False,
            )
            self.queue_draw()

        def set_selected_segments(
            self,
            segment_ids: tuple[str, ...] | list[str],
            primary_segment_id: str | None = None,
        ) -> None:
            self._set_selection(
                tuple(segment_ids),
                primary_segment_id,
                notify=False,
            )
            self.queue_draw()

        def get_selected_segment_ids(self) -> tuple[str, ...]:
            return self._selected_segment_ids

        def set_zoom(self, zoom: float) -> None:
            parsed = clamp_timeline_zoom(zoom)
            if math.isclose(parsed, self._zoom, rel_tol=0.0, abs_tol=1e-9):
                self._fit_window_seconds = None
                return
            self._zoom = parsed
            self._fit_window_seconds = None
            self._recalculate_content_size()

        def zoom_in(self) -> None:
            self.set_zoom(next_timeline_zoom(self._zoom, 1))

        def zoom_out(self) -> None:
            self.set_zoom(next_timeline_zoom(self._zoom, -1))

        def fit_to_view(self) -> None:
            self.set_zoom(TIMELINE_DEFAULT_ZOOM)

        def fit_to_duration(
            self,
            window_seconds: float = TIMELINE_FIT_WINDOW_SECONDS,
        ) -> None:
            if self._timeline is None:
                return
            self._zoom = timeline_zoom_for_window(
                self._timeline.timeline_duration_seconds,
                window_seconds,
            )
            self._fit_window_seconds = float(window_seconds)
            self._recalculate_content_size()

        def get_zoom(self) -> float:
            return self._zoom

        def get_content_width(self) -> float:
            if self._timeline is None:
                return self._viewport_width
            width = timeline_content_width(
                self._timeline.timeline_duration_seconds,
                self._viewport_width,
                self._zoom,
            )
            if self._fit_window_seconds is not None:
                width = max(width, self._viewport_width)
            return width

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
            gesture,
            _n_press: int,
            x: float,
            _y: float,
        ) -> None:
            self._drag_happened = False
            self._pressed_selection_additive = self._is_additive_selection(gesture)
            self._pressed_selection_range = self._is_range_selection(gesture)
            self._seek_from_x(
                x,
                notify=False,
                update_selection=True,
                additive=self._pressed_selection_additive,
            )

        def _on_released(
            self,
            _gesture,
            _n_press: int,
            x: float,
            _y: float,
        ) -> None:
            if not self._drag_happened:
                self._seek_from_x(
                    x,
                    notify=True,
                    update_selection=False,
                    additive=self._pressed_selection_additive,
                )
            self._drag_happened = False
            self._pressed_selection_additive = False
            self._pressed_selection_range = False

        def _on_drag_begin(
            self,
            gesture,
            start_x: float,
            _start_y: float,
        ) -> None:
            self._drag_happened = True
            self._drag_start_x = start_x
            self._pressed_selection_additive = self._is_additive_selection(gesture)
            self._pressed_selection_range = self._is_range_selection(gesture)
            self._seek_from_x(
                start_x,
                notify=True,
                update_selection=False,
                additive=self._pressed_selection_additive,
            )

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
                    update_selection=False,
                    additive=self._pressed_selection_additive,
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
                    update_selection=False,
                    additive=self._pressed_selection_additive,
                )
            self._drag_start_x = None
            self._pressed_selection_additive = False
            self._pressed_selection_range = False

        def _is_additive_selection(self, gesture) -> bool:
            getter = getattr(gesture, "get_current_event_state", None)
            if getter is None or self._selection_modifier_mask == 0:
                return False
            return bool(int(getter()) & self._selection_modifier_mask)

        def _is_range_selection(self, gesture) -> bool:
            getter = getattr(gesture, "get_current_event_state", None)
            if getter is None or self._range_selection_modifier_mask == 0:
                return False
            return bool(int(getter()) & self._range_selection_modifier_mask)

        def _set_selection(
            self,
            segment_ids: tuple[str, ...],
            primary_segment_id: str | None,
            *,
            notify: bool,
        ) -> None:
            known_ids = (
                {segment.segment_id for segment in self._timeline.segment_items}
                if self._timeline is not None
                else set()
            )
            selected = tuple(
                segment_id for segment_id in dict.fromkeys(segment_ids) if segment_id in known_ids
            )
            primary = primary_segment_id if primary_segment_id in selected else None
            if primary is None and selected:
                primary = selected[-1]
            self._selected_segment_ids = selected
            self._selected_segment_id = primary
            if notify:
                if primary is not None and self._on_segment_selected is not None:
                    self._on_segment_selected(primary)
                if self._on_selection_changed is not None:
                    self._on_selection_changed(selected)

        def _select_clip(
            self,
            segment_id: str,
            *,
            additive: bool,
            range_selection: bool,
        ) -> None:
            if self._timeline is None:
                return
            timeline = self._timeline
            if range_selection:
                anchor_index = next(
                    (
                        index
                        for index, segment in enumerate(timeline.segment_items)
                        if segment.segment_id == self._selected_segment_id
                    ),
                    None,
                )
                target_index = next(
                    (
                        index
                        for index, segment in enumerate(timeline.segment_items)
                        if segment.segment_id == segment_id
                    ),
                    None,
                )
                if anchor_index is None or target_index is None:
                    self._set_selection((segment_id,), segment_id, notify=True)
                    return
                first = min(anchor_index, target_index)
                last = max(anchor_index, target_index)
                self._set_selection(
                    tuple(
                        segment.segment_id for segment in timeline.segment_items[first : last + 1]
                    ),
                    segment_id,
                    notify=True,
                )
                return
            if not additive:
                self._set_selection((segment_id,), segment_id, notify=True)
                return
            selected = list(self._selected_segment_ids)
            if segment_id in selected:
                selected.remove(segment_id)
            else:
                selected.append(segment_id)
            self._set_selection(tuple(selected), segment_id, notify=True)

        def _seek_from_x(
            self,
            x: float,
            *,
            notify: bool,
            update_selection: bool,
            additive: bool,
        ) -> None:
            if self._timeline is None:
                return
            self.grab_focus()
            clips = layout_timeline_segments(
                self._timeline,
                self._viewport_width,
                self._zoom,
            )
            clip = hit_test_timeline_segment(clips, x)
            if clip is not None and update_selection:
                self._select_clip(
                    clip.segment_id,
                    additive=additive,
                    range_selection=self._pressed_selection_range,
                )
            position = timeline_position_from_x(
                x,
                self._timeline.timeline_duration_seconds,
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
                self._timeline.timeline_duration_seconds,
                self._viewport_width,
                self._zoom,
            )
            self._draw_ruler(
                context,
                max(
                    self._timeline.timeline_duration_seconds,
                    self._fit_window_seconds or 0.0,
                ),
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
            draw_ruler(context, duration_seconds, pixels_per_second, width)

        def _draw_track(self, context, width: int) -> None:
            draw_track(context, width)

        def _draw_clip(self, context, clip: TimelineClipGeometry) -> None:
            draw_clip(context, clip, self._selected_segment_ids)

        def _draw_playhead(self, context, pixels_per_second: float) -> None:
            draw_playhead(context, self._playhead_seconds, pixels_per_second)

        @staticmethod
        def _rounded_rectangle(context, x, y, width, height, radius) -> None:
            rounded_rectangle(context, x, y, width, height, radius)

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
            draw_text(context, text, x, y, red, green, blue, size)

    return TimelineCanvas
