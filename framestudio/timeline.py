from __future__ import annotations

import math
from dataclasses import replace
from typing import Any, Callable

from .model import ProjectValidationError, SegmentTimeline
from .model_timeline import TimelineTrack, _earliest_fit
from .model_types import ticks_to_seconds
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
    TimelineTrackGeometry,
    clamp_timeline_zoom,
    hit_test_timeline_segment,
    layout_timeline_segments,
    layout_timeline_tracks,
    next_timeline_zoom,
    timeline_content_height,
    timeline_content_width,
    timeline_drag_ticks_from_x,
    timeline_pixels_per_second,
    timeline_position_from_x,
    timeline_tick_interval,
    timeline_ticks_from_x,
    timeline_track_id_at_y,
    timeline_x_from_ticks,
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
    "TimelineTrack",
    "TimelineTrackGeometry",
    "clamp_timeline_zoom",
    "create_timeline_canvas",
    "hit_test_timeline_segment",
    "layout_timeline_segments",
    "layout_timeline_tracks",
    "next_timeline_zoom",
    "timeline_content_height",
    "timeline_content_width",
    "timeline_drag_ticks_from_x",
    "timeline_pixels_per_second",
    "timeline_position_from_x",
    "timeline_ticks_from_x",
    "timeline_track_id_at_y",
    "timeline_tick_interval",
    "timeline_zoom_for_window",
    "timeline_zoom_label",
    "timeline_x_from_ticks",
]


def create_timeline_canvas(gtk_module: Any) -> Any:
    class TimelineCanvas(gtk_module.DrawingArea):
        def __init__(
            self,
            on_seek: Callable[[float], None] | None = None,
            on_segment_selected: Callable[[str], None] | None = None,
            on_selection_changed: Callable[[tuple[str, ...]], None] | None = None,
            on_segment_dropped: Callable[[str, int, str], None] | None = None,
            on_invalid_drop: Callable[[str], None] | None = None,
            on_track_activated: Callable[[str], None] | None = None,
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
            self._on_segment_dropped = on_segment_dropped
            self._on_invalid_drop = on_invalid_drop
            self._on_track_activated = on_track_activated
            self._selection_modifier_mask = int(selection_modifier_mask)
            self._range_selection_modifier_mask = int(range_selection_modifier_mask)
            self._drag_start_x: float | None = None
            self._drag_start_y: float | None = None
            self._drag_mode: str | None = None
            self._drag_segment_id: str | None = None
            self._drag_pointer_offset_ticks = 0
            self._drag_preview: tuple[int, str | None] | None = None
            self._drag_happened = False
            self._drag_committed = False
            self._pressed_selection_additive = False
            self._pressed_selection_range = False
            self._pressed_selection_deferred = False
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
            self._drag_gesture.connect("cancel", self._on_drag_cancel)
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

        def get_track_ids(self) -> tuple[str, ...]:
            if self._timeline is None:
                return ()
            return tuple(row.track_id for row in layout_timeline_tracks(self._timeline))

        def get_playhead_seconds(self) -> float:
            return self._playhead_seconds

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
            track_count = (
                len(layout_timeline_tracks(self._timeline)) if self._timeline is not None else 1
            )
            self.set_size_request(
                max(1, math.ceil(self.get_content_width())),
                math.ceil(timeline_content_height(track_count)),
            )
            self.queue_draw()

        def _on_pressed(
            self,
            gesture,
            _n_press: int,
            x: float,
            y: float,
        ) -> None:
            self._drag_happened = False
            self._drag_committed = False
            self._pressed_selection_additive = self._is_additive_selection(gesture)
            self._pressed_selection_range = self._is_range_selection(gesture)
            update_selection = True
            self._pressed_selection_deferred = False
            if (
                self._timeline is not None
                and self._timeline.timing_mode == "absolute"
                and not self._pressed_selection_additive
                and not self._pressed_selection_range
            ):
                clip = hit_test_timeline_segment(
                    layout_timeline_segments(
                        self._timeline,
                        self._viewport_width,
                        self._zoom,
                    ),
                    x,
                    y,
                )
                update_selection = clip is None or clip.segment_id not in self._selected_segment_ids
                self._pressed_selection_deferred = not update_selection
            self._seek_from_x(
                x,
                y=y,
                notify=False,
                update_selection=update_selection,
                additive=self._pressed_selection_additive,
            )
            if self._timeline is not None and self._timeline.timing_mode == "absolute":
                track_id = timeline_track_id_at_y(self._timeline, y)
                if track_id is not None and self._on_track_activated is not None:
                    self._on_track_activated(track_id)

        def _on_released(
            self,
            _gesture,
            _n_press: int,
            x: float,
            y: float,
        ) -> None:
            if not self._drag_happened and not self._drag_committed:
                self._seek_from_x(
                    x,
                    y=y,
                    notify=True,
                    update_selection=self._pressed_selection_deferred,
                    additive=self._pressed_selection_additive,
                )
            self._drag_happened = False
            self._drag_committed = False
            self._pressed_selection_additive = False
            self._pressed_selection_range = False
            self._pressed_selection_deferred = False

        def _on_drag_begin(
            self,
            gesture,
            start_x: float,
            start_y: float,
        ) -> None:
            self._drag_happened = True
            self._drag_committed = False
            self._drag_start_x = start_x
            self._drag_start_y = start_y
            self._drag_mode = None
            self._drag_segment_id = None
            self._drag_preview = None
            if self._timeline is not None and self._timeline.timing_mode == "absolute":
                clips = layout_timeline_segments(
                    self._timeline,
                    self._viewport_width,
                    self._zoom,
                )
                clip = hit_test_timeline_segment(clips, start_x, start_y)
                if clip is not None:
                    self._drag_mode = "segment"
                    self._drag_segment_id = clip.segment_id
                    pointer_ticks = timeline_drag_ticks_from_x(
                        start_x,
                        self._timeline.timeline_duration_seconds,
                        self._viewport_width,
                        self._zoom,
                    )
                    self._drag_pointer_offset_ticks = (
                        pointer_ticks - self._timeline.find(clip.segment_id).timeline_start_ticks
                    )
                    self.queue_draw()
                    return
            self._pressed_selection_additive = self._is_additive_selection(gesture)
            self._pressed_selection_range = self._is_range_selection(gesture)
            self._drag_mode = "seek"
            self._seek_from_x(
                start_x,
                y=start_y,
                notify=True,
                update_selection=False,
                additive=self._pressed_selection_additive,
            )

        def _on_drag_update(
            self,
            _gesture,
            offset_x: float,
            offset_y: float,
        ) -> None:
            if self._drag_mode == "segment" and self._drag_start_x is not None:
                self._update_segment_drag(offset_x, offset_y)
            elif self._drag_start_x is not None:
                self._seek_from_x(
                    self._drag_start_x + offset_x,
                    y=(self._drag_start_y or 0.0) + offset_y,
                    notify=True,
                    update_selection=False,
                    additive=self._pressed_selection_additive,
                )

        def _on_drag_end(
            self,
            _gesture,
            offset_x: float,
            offset_y: float,
        ) -> None:
            drag_committed = abs(offset_x) > 1.0 or abs(offset_y) > 1.0
            self._drag_committed = drag_committed
            self._drag_happened = drag_committed
            if self._drag_mode == "segment":
                if drag_committed:
                    self._update_segment_drag(offset_x, offset_y)
                    self._finish_segment_drag()
            elif self._drag_start_x is not None:
                self._seek_from_x(
                    self._drag_start_x + offset_x,
                    y=(self._drag_start_y or 0.0) + offset_y,
                    notify=True,
                    update_selection=False,
                    additive=self._pressed_selection_additive,
                )
            self._clear_drag_state(reset_drag_happened=False)

        def _on_drag_cancel(self, _gesture, _event=None) -> None:
            self._drag_committed = self._drag_happened
            self._clear_drag_state()
            self.queue_draw()

        def _clear_drag_state(self, *, reset_drag_happened: bool = True) -> None:
            self._drag_start_x = None
            self._drag_start_y = None
            self._drag_mode = None
            self._drag_segment_id = None
            self._drag_preview = None
            self._drag_pointer_offset_ticks = 0
            self._pressed_selection_additive = False
            self._pressed_selection_range = False
            if reset_drag_happened:
                self._drag_happened = False

        def _segment_drag_target(
            self,
            offset_x: float,
            offset_y: float,
        ) -> tuple[int, str | None] | None:
            if self._timeline is None or self._drag_start_x is None or self._drag_start_y is None:
                return None
            target_x = self._drag_start_x + offset_x
            target_y = self._drag_start_y + offset_y
            target_track_id = timeline_track_id_at_y(self._timeline, target_y)
            target_pointer_ticks = timeline_drag_ticks_from_x(
                target_x,
                self._timeline.timeline_duration_seconds,
                self._viewport_width,
                self._zoom,
            )
            requested_start_ticks = max(
                0,
                target_pointer_ticks - self._drag_pointer_offset_ticks,
            )
            if target_track_id is not None and self._drag_segment_id is not None:
                try:
                    moving_segment = self._timeline.find(self._drag_segment_id)
                    destination = self._timeline.track_by_id(target_track_id)
                except ProjectValidationError:
                    target_track_id = None
                else:
                    duration_ticks = (
                        moving_segment.timeline_end_ticks - moving_segment.timeline_start_ticks
                    )
                    occupied = tuple(
                        block
                        for block in destination.blocks
                        if block.segment_id != moving_segment.segment_id
                    )
                    requested_start_ticks = _earliest_fit(
                        requested_start_ticks,
                        duration_ticks,
                        occupied,
                    )
            return (
                requested_start_ticks,
                target_track_id,
            )

        def _update_segment_drag(self, offset_x: float, offset_y: float) -> None:
            target = self._segment_drag_target(offset_x, offset_y)
            self._drag_preview = target if target is not None else None
            self.queue_draw()

        def _finish_segment_drag(self) -> None:
            target = self._drag_preview
            segment_id = self._drag_segment_id
            if segment_id is None or target is None or target[1] is None:
                if self._on_invalid_drop is not None:
                    self._on_invalid_drop("Invalid drop: choose a timeline track row")
                self.queue_draw()
                return
            if self._on_segment_dropped is not None:
                self._on_segment_dropped(segment_id, target[0], target[1])
            self.queue_draw()

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
            y: float | None = None,
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
            clip = hit_test_timeline_segment(
                clips,
                x,
                y if self._timeline.timing_mode == "absolute" else None,
            )
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
            rows = layout_timeline_tracks(self._timeline)
            self._draw_track(context, width, rows)
            clips = layout_timeline_segments(
                self._timeline,
                self._viewport_width,
                self._zoom,
            )
            clips = self._clips_with_drag_preview(clips, rows)
            for clip in clips:
                self._draw_clip(context, clip)
            self._draw_playhead(context, pixels_per_second, rows)

        def _draw_ruler(
            self,
            context,
            duration_seconds: float,
            pixels_per_second: float,
            width: int,
        ) -> None:
            draw_ruler(context, duration_seconds, pixels_per_second, width)

        def _draw_track(
            self,
            context,
            width: int,
            rows: tuple[TimelineTrackGeometry, ...] | list[TimelineTrackGeometry] = (),
        ) -> None:
            draw_track(context, width, rows)

        def _draw_clip(self, context, clip: TimelineClipGeometry) -> None:
            draw_clip(context, clip, self._selected_segment_ids)

        def _draw_playhead(
            self,
            context,
            pixels_per_second: float,
            rows: tuple[TimelineTrackGeometry, ...] | list[TimelineTrackGeometry] = (),
        ) -> None:
            draw_playhead(context, self._playhead_seconds, pixels_per_second, rows)

        def _clips_with_drag_preview(
            self,
            clips: tuple[TimelineClipGeometry, ...],
            rows: tuple[TimelineTrackGeometry, ...],
        ) -> tuple[TimelineClipGeometry, ...]:
            if (
                self._drag_segment_id is None
                or self._drag_preview is None
                or self._timeline is None
            ):
                return clips
            target_ticks, target_track_id = self._drag_preview
            if target_track_id is None:
                return clips
            target_row = next(
                (row for row in rows if row.track_id == target_track_id),
                None,
            )
            if target_row is None:
                return clips
            pixels_per_second = timeline_pixels_per_second(
                self._timeline.timeline_duration_seconds,
                self._viewport_width,
                self._zoom,
            )
            return tuple(
                replace(
                    clip,
                    x=TIMELINE_HORIZONTAL_PADDING
                    + ticks_to_seconds(target_ticks) * pixels_per_second,
                    track_id=target_track_id,
                    track_index=target_row.index,
                    y=target_row.y + 20.0,
                )
                if clip.segment_id == self._drag_segment_id
                else clip
                for clip in clips
            )

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
