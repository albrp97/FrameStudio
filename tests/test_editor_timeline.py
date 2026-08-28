import unittest

from resolve_editor.app import is_split_key
from resolve_editor.model import Segment, SegmentTimeline
from resolve_editor.timeline import (
    SELECTED_CLIP_BORDER_COLOR,
    TimelineClipGeometry,
    clamp_timeline_zoom,
    create_timeline_canvas,
    hit_test_timeline_segment,
    layout_timeline_segments,
    next_timeline_zoom,
    timeline_content_width,
    timeline_position_from_x,
)


class FakeDrawingArea:
    def __init__(self):
        self.controllers = []

    def set_focusable(self, _focusable):
        pass

    def set_hexpand(self, _expand):
        pass

    def set_vexpand(self, _expand):
        pass

    def set_draw_func(self, _draw):
        pass

    def add_controller(self, controller):
        self.controllers.append(controller)

    def set_size_request(self, _width, _height):
        pass

    def queue_draw(self):
        pass

    def grab_focus(self):
        pass


class FakeGesture:
    def __init__(self, state=0):
        self.state = state

    def set_button(self, _button):
        pass

    def set_exclusive(self, _exclusive):
        pass

    def connect(self, _signal, _callback):
        pass

    def get_current_event_state(self):
        return self.state


class FakeContext:
    def __init__(self):
        self.colors = []
        self.line_widths = []

    def set_source_rgba(self, red, green, blue, alpha):
        self.colors.append((red, green, blue, alpha))

    def set_source_rgb(self, *_values):
        pass

    def set_line_width(self, width):
        self.line_widths.append(width)

    def new_sub_path(self):
        pass

    def arc(self, *_values):
        pass

    def close_path(self):
        pass

    def fill_preserve(self):
        pass

    def stroke(self):
        pass

    def rectangle(self, *_values):
        pass

    def fill(self):
        pass

    def save(self):
        pass

    def clip(self):
        pass

    def restore(self):
        pass

    def move_to(self, *_values):
        pass

    def line_to(self, *_values):
        pass


class FakeGtk:
    DrawingArea = FakeDrawingArea
    GestureClick = FakeGesture
    GestureDrag = FakeGesture


class EditorTimelineTests(unittest.TestCase):
    def test_clip_layout_preserves_order_and_deleted_state(self):
        timeline = SegmentTimeline(60.0)
        timeline.split(20.0)
        deleted_id = timeline.segments[1].segment_id
        timeline.set_deleted(deleted_id, True)

        clips = layout_timeline_segments(timeline, 600.0, 1.0)

        self.assertEqual(
            [clip.segment_id for clip in clips],
            [segment.segment_id for segment in timeline.segments],
        )
        self.assertEqual([clip.index for clip in clips], [0, 1])
        self.assertFalse(clips[0].deleted)
        self.assertTrue(clips[1].deleted)
        self.assertLess(clips[0].x, clips[1].x)
        self.assertGreater(clips[0].width, 0.0)
        self.assertGreater(clips[1].width, 0.0)

    def test_clip_layout_exposes_stable_segment_color_slots(self):
        timeline = SegmentTimeline.from_segments(
            60.0,
            (
                Segment.create(0.0, 20.0, color_index=1),
                Segment.create(20.0, 60.0, color_index=2),
            ),
        )

        clips = layout_timeline_segments(timeline, 600.0, 1.0)

        self.assertEqual(
            [clip.color_index for clip in clips],
            [1, 2],
        )

    def test_zoom_expands_content_width_and_has_ordered_levels(self):
        fit_width = timeline_content_width(60.0, 600.0, 1.0)
        zoomed_width = timeline_content_width(60.0, 600.0, 2.0)

        self.assertEqual(fit_width, 600.0)
        self.assertGreater(zoomed_width, fit_width)
        self.assertEqual(next_timeline_zoom(1.0, 1), 1.25)
        self.assertEqual(next_timeline_zoom(1.0, -1), 0.75)
        self.assertEqual(clamp_timeline_zoom(0.5), 0.5)
        self.assertLess(
            timeline_content_width(120.0, 600.0, 0.5),
            timeline_content_width(120.0, 600.0, 1.0),
        )

    def test_default_zoom_fits_long_timelines_to_the_viewport(self):
        self.assertEqual(timeline_content_width(120.0, 600.0, 1.0), 600.0)
        self.assertEqual(timeline_content_width(3600.0, 600.0, 1.0), 600.0)
        TimelineCanvas = create_timeline_canvas(FakeGtk)
        canvas = TimelineCanvas()
        canvas.set_viewport_width(600.0)
        canvas.set_timeline(SegmentTimeline(120.0))
        self.assertFalse(canvas.has_horizontal_overflow())

    def test_hit_testing_and_position_mapping_use_source_time(self):
        timeline = SegmentTimeline(60.0)
        timeline.split(20.0)
        clips = layout_timeline_segments(timeline, 600.0, 2.0)

        selected = hit_test_timeline_segment(clips, clips[1].x + 2.0)

        self.assertIsNotNone(selected)
        self.assertEqual(selected.segment_id, timeline.segments[1].segment_id)
        self.assertEqual(
            timeline_position_from_x(
                clips[1].x,
                timeline.source_duration_seconds,
                600.0,
                2.0,
            ),
            20.0,
        )
        self.assertEqual(
            timeline_position_from_x(
                -100.0,
                timeline.source_duration_seconds,
                600.0,
                2.0,
            ),
            0.0,
        )
        self.assertEqual(
            timeline_position_from_x(
                100000.0,
                timeline.source_duration_seconds,
                600.0,
                2.0,
            ),
            60.0,
        )

    def test_b_key_is_the_split_shortcut(self):
        self.assertTrue(is_split_key(ord("b")))
        self.assertTrue(is_split_key(ord("B")))
        self.assertFalse(is_split_key(ord("s")))

    def test_drag_emits_intermediate_seek_requests(self):
        positions = []
        TimelineCanvas = create_timeline_canvas(FakeGtk)
        canvas = TimelineCanvas(on_seek=positions.append)
        canvas.set_viewport_width(100.0)
        canvas.set_timeline(SegmentTimeline(10.0))

        canvas._on_drag_begin(None, 20.0, 0.0)
        canvas._on_drag_update(None, 10.0, 0.0)
        canvas._on_drag_update(None, 20.0, 0.0)
        canvas._on_drag_end(None, 20.0, 0.0)

        self.assertEqual(len(positions), 4)
        self.assertLess(positions[0], positions[1])
        self.assertLess(positions[1], positions[2])
        self.assertEqual(positions[2], positions[3])

    def test_control_click_tracks_multiple_selected_clips(self):
        TimelineCanvas = create_timeline_canvas(FakeGtk)
        canvas = TimelineCanvas(selection_modifier_mask=1)
        canvas.set_viewport_width(100.0)
        timeline = SegmentTimeline(10.0)
        timeline.split(5.0)
        canvas.set_timeline(timeline)
        clips = layout_timeline_segments(timeline, 100.0, 1.0)

        canvas._on_pressed(FakeGesture(), 1, clips[0].x + 2.0, 0.0)
        canvas._on_released(FakeGesture(), 1, clips[0].x + 2.0, 0.0)
        canvas._on_pressed(
            FakeGesture(state=1),
            1,
            clips[1].x + 2.0,
            0.0,
        )
        canvas._on_released(
            FakeGesture(state=1),
            1,
            clips[1].x + 2.0,
            0.0,
        )

        self.assertEqual(
            canvas.get_selected_segment_ids(),
            (timeline.segments[0].segment_id, timeline.segments[1].segment_id),
        )

        canvas._on_pressed(
            FakeGesture(state=1),
            1,
            clips[0].x + 2.0,
            0.0,
        )
        canvas._on_released(
            FakeGesture(state=1),
            1,
            clips[0].x + 2.0,
            0.0,
        )

        self.assertEqual(
            canvas.get_selected_segment_ids(),
            (timeline.segments[1].segment_id,),
        )

    def test_shift_click_selects_an_inclusive_range_and_normal_click_clears_it(self):
        TimelineCanvas = create_timeline_canvas(FakeGtk)
        canvas = TimelineCanvas(
            selection_modifier_mask=1,
            range_selection_modifier_mask=2,
        )
        canvas.set_viewport_width(100.0)
        timeline = SegmentTimeline(10.0)
        for position in (2.0, 4.0, 6.0, 8.0):
            timeline.split(position)
        canvas.set_timeline(timeline)
        clips = layout_timeline_segments(timeline, 100.0, 1.0)

        canvas._on_pressed(FakeGesture(), 1, clips[1].x + 2.0, 0.0)
        canvas._on_released(FakeGesture(), 1, clips[1].x + 2.0, 0.0)
        canvas._on_pressed(
            FakeGesture(state=2),
            1,
            clips[4].x + 2.0,
            0.0,
        )
        canvas._on_released(
            FakeGesture(state=2),
            1,
            clips[4].x + 2.0,
            0.0,
        )

        self.assertEqual(
            canvas.get_selected_segment_ids(),
            tuple(segment.segment_id for segment in timeline.segments[1:]),
        )

        canvas._on_pressed(FakeGesture(), 1, clips[0].x + 2.0, 0.0)
        canvas._on_released(FakeGesture(), 1, clips[0].x + 2.0, 0.0)

        self.assertEqual(
            canvas.get_selected_segment_ids(),
            (timeline.segments[0].segment_id,),
        )

    def test_overlapping_drag_and_click_gestures_apply_modifier_selection_once(self):
        TimelineCanvas = create_timeline_canvas(FakeGtk)
        canvas = TimelineCanvas(
            selection_modifier_mask=1,
            range_selection_modifier_mask=2,
        )
        canvas.set_viewport_width(100.0)
        timeline = SegmentTimeline(10.0)
        for position in (2.0, 4.0, 6.0, 8.0):
            timeline.split(position)
        canvas.set_timeline(timeline)
        clips = layout_timeline_segments(timeline, 100.0, 1.0)

        def overlapping_click(x: float, state: int = 0) -> None:
            gesture = FakeGesture(state=state)
            canvas._on_drag_begin(gesture, x, 0.0)
            canvas._on_pressed(gesture, 1, x, 0.0)

        overlapping_click(clips[1].x + 2.0)
        overlapping_click(clips[4].x + 2.0, state=1)
        self.assertEqual(
            canvas.get_selected_segment_ids(),
            (timeline.segments[1].segment_id, timeline.segments[4].segment_id),
        )

        overlapping_click(clips[1].x + 2.0)
        overlapping_click(clips[4].x + 2.0, state=2)

        self.assertEqual(
            canvas.get_selected_segment_ids(),
            tuple(segment.segment_id for segment in timeline.segments[1:]),
        )

    def test_selected_clip_uses_the_eva_attention_orange_outline(self):
        TimelineCanvas = create_timeline_canvas(FakeGtk)
        canvas = TimelineCanvas()
        segment_id = "selected"
        canvas._selected_segment_ids = (segment_id,)
        context = FakeContext()
        clip = TimelineClipGeometry(
            segment_id=segment_id,
            index=0,
            start_seconds=0.0,
            end_seconds=1.0,
            timeline_start_seconds=0.0,
            timeline_end_seconds=1.0,
            source_id=None,
            deleted=False,
            x=10.0,
            width=16.0,
            color_index=0,
        )

        canvas._draw_clip(context, clip)

        self.assertIn(SELECTED_CLIP_BORDER_COLOR, context.colors)
        self.assertIn(3.0, context.line_widths)


if __name__ == "__main__":
    unittest.main()
