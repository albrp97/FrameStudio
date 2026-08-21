import unittest

from resolve_editor.app import is_split_key
from resolve_editor.model import SegmentTimeline
from resolve_editor.timeline import (
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
    def set_button(self, _button):
        pass

    def set_exclusive(self, _exclusive):
        pass

    def connect(self, _signal, _callback):
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

    def test_zoom_expands_content_width_and_has_ordered_levels(self):
        fit_width = timeline_content_width(60.0, 600.0, 1.0)
        zoomed_width = timeline_content_width(60.0, 600.0, 2.0)

        self.assertEqual(fit_width, 600.0)
        self.assertGreater(zoomed_width, fit_width)
        self.assertEqual(next_timeline_zoom(1.0, 1), 1.25)
        self.assertEqual(next_timeline_zoom(1.0, -1), 1.0)

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


if __name__ == "__main__":
    unittest.main()
