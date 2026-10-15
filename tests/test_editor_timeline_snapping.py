from __future__ import annotations

import unittest
from dataclasses import replace
from unittest.mock import patch

from framestudio.model import SegmentTimeline
from framestudio.timeline import create_timeline_canvas
from framestudio.timeline_geometry import TIMELINE_HORIZONTAL_PADDING
from framestudio.timeline_rendering import draw_clip
from tests.test_editor_timeline import FakeContext, FakeGesture, FakeGtk


class TimelineSnappingTests(unittest.TestCase):
    def canvas(self, duration=10.0):
        seeks = []
        canvas = create_timeline_canvas(FakeGtk)(
            on_seek=seeks.append,
            snap_bypass_modifier_mask=64,
        )
        timeline = SegmentTimeline(duration)
        timeline.split(duration / 2)
        canvas.set_timeline(timeline)
        return canvas, seeks

    def click(self, canvas, x, y, *, state=0):
        gesture = FakeGesture(state=state)
        canvas._on_pressed(gesture, 1, x, y)
        canvas._on_released(gesture, 1, x, y)

    def test_click_snaps_inside_visible_zone_and_super_bypasses_at_each_zoom(self):
        canvas, seeks = self.canvas()
        for viewport in (100, 800):
            canvas.set_viewport_width(viewport)
            for zoom in (0.5, 1.0, 4.0, 40.0):
                with self.subTest(viewport=viewport, zoom=zoom):
                    canvas.set_zoom(zoom)
                    clip = canvas._layout()[1]
                    self.assertAlmostEqual(clip.snap_width, min(16.0, clip.width * 0.1))
                    x, y = clip.x + clip.snap_width / 2, clip.y + 10
                    self.click(canvas, x, y)
                    self.assertEqual(seeks[-1], 5.0)
                    self.click(canvas, x, y, state=64)
                    self.assertGreater(seeks[-1], 5.0)
                    self.click(canvas, clip.x + clip.snap_width + 0.01, y)
                    self.assertGreater(seeks[-1], 5.0)

    def test_subpixel_zone_never_extends_beyond_real_clip_duration(self):
        canvas, seeks = self.canvas(duration=0.002)
        canvas.set_viewport_width(1.0)
        clip = canvas._layout()[0]
        real_width = canvas._layout()[1].x - clip.x
        self.assertLess(real_width, 1.0)
        self.assertAlmostEqual(clip.snap_width, real_width * 0.1)
        self.assertLessEqual(clip.x + clip.snap_width, canvas._layout()[1].x)
        self.click(canvas, clip.x + real_width / 2, clip.y + 10)
        self.assertGreater(seeks[-1], 0)
        self.assertLess(seeks[-1], 0.001)
        second = canvas._layout()[1]
        self.click(canvas, second.x + second.snap_width / 2, second.y + 10)
        self.assertEqual(seeks[-1], 0.001)

    def test_ruler_and_scrub_drag_remain_unsnapped(self):
        canvas, seeks = self.canvas()
        clip = canvas._layout()[1]
        x = clip.x + clip.snap_width / 2
        self.click(canvas, x, 10)
        self.assertGreater(seeks[-1], 5.0)
        gesture = FakeGesture()
        canvas._on_drag_begin(gesture, x, 10)
        canvas._on_drag_update(gesture, 0.01, 0)
        self.assertGreater(seeks[-1], 5.0)

    def test_click_on_number_badge_above_shaded_start_still_snaps(self):
        canvas, seeks = self.canvas()
        clip = canvas._layout()[1]
        self.click(canvas, clip.x + 8, clip.y - 4)
        self.assertEqual(seeks[-1], 5)
        self.click(canvas, clip.x + 8, clip.y - 4, state=64)
        self.assertGreater(seeks[-1], 5)
        self.assertFalse(clip.contains_point(clip.x + 8, clip.y - 10))
        self.assertFalse(clip.contains_point(clip.x + 40, clip.y - 4))

    def test_stationary_click_with_drag_gesture_still_snaps_at_1200_percent_zoom(self):
        for pressed_first in (False, True):
            for release_first in (False, True):
                for state in (0, 64):
                    with self.subTest(
                        pressed_first=pressed_first, release_first=release_first, state=state
                    ):
                        canvas, seeks = self.canvas()
                        canvas.set_zoom(12)
                        clip = canvas._layout()[1]
                        x, y = clip.x + clip.snap_width / 2, clip.y + clip.height / 2
                        gesture = FakeGesture(state=state)
                        if pressed_first:
                            canvas._on_pressed(gesture, 1, x, y)
                            canvas._on_drag_begin(gesture, x, y)
                        else:
                            canvas._on_drag_begin(gesture, x, y)
                            canvas._on_pressed(gesture, 1, x, y)
                        if release_first:
                            canvas._on_released(gesture, 1, x, y)
                            canvas._on_drag_end(gesture, 0, 0)
                        else:
                            canvas._on_drag_end(gesture, 0, 0)
                            canvas._on_released(gesture, 1, x, y)
                        self.assertTrue(seeks)
                        if state:
                            self.assertGreater(seeks[-1], 5)
                        else:
                            self.assertEqual(seeks[-1], 5)
                        self.assertEqual(canvas.get_playhead_seconds(), seeks[-1])

    def test_visible_highlight_matches_snap_width_and_stays_inside_clip(self):
        canvas, _seeks = self.canvas()
        clip = canvas._layout()[0]
        context = FakeContext()
        with (
            patch.object(context, "rectangle", wraps=context.rectangle) as rectangle,
            patch("framestudio.timeline_rendering.draw_text"),
        ):
            draw_clip(context, clip)
        self.assertTrue(
            any(
                call.args == (clip.x, clip.y, clip.snap_width, clip.height)
                for call in rectangle.call_args_list
            )
        )
        self.assertIn((1.0, 1.0, 1.0, 0.16), context.colors)
        self.assertGreaterEqual(clip.x, TIMELINE_HORIZONTAL_PADDING)

    def test_click_jitter_snaps_but_real_scrub_returning_to_start_does_not(self):
        canvas, seeks = self.canvas()
        canvas.set_zoom(12)
        clip = canvas._layout()[1]
        x, y = clip.x + clip.snap_width / 2, clip.y + clip.height / 2
        gesture = FakeGesture()
        canvas._on_drag_begin(gesture, x, y)
        canvas._on_drag_update(gesture, 3, 0)
        canvas._on_drag_end(gesture, 3, 0)
        self.assertEqual(seeks[-1], 5)

        canvas._on_drag_begin(gesture, x, y)
        canvas._on_drag_update(gesture, 30, 0)
        canvas._on_drag_update(gesture, 0, 0)
        canvas._on_drag_end(gesture, 0, 0)
        canvas._on_released(gesture, 1, x, y)
        self.assertGreater(seeks[-1], 5)

    def test_click_uses_widget_drag_threshold_instead_of_a_fixed_pixel_cutoff(self):
        canvas, seeks = self.canvas()
        canvas.set_zoom(12)
        clip = canvas._layout()[1]
        x, y = clip.x + 2, clip.y + clip.height / 2
        gesture = FakeGesture()
        with patch.object(canvas, "drag_check_threshold", return_value=False) as threshold:
            canvas._on_drag_begin(gesture, x, y)
            canvas._on_drag_update(gesture, 10, 0)
            canvas._on_drag_end(gesture, 10, 0)
        threshold.assert_called_with(0, 0, 10, 0)
        self.assertEqual(seeks[-1], 5)

    def test_highlight_is_visibly_lighter_in_rendered_clip_pixels(self):
        import cairo

        canvas, _seeks = self.canvas()
        clip = replace(canvas._layout()[0], width=80, timeline_width=80, y=20, height=30)
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 120, 80)
        draw_clip(cairo.Context(surface), clip)
        surface.flush()
        pixels = bytes(surface.get_data())
        y = int(clip.y + 14)
        lighter = y * surface.get_stride() + int(clip.x + 4) * 4
        normal = y * surface.get_stride() + int(clip.x + 30) * 4
        for channel in range(3):
            self.assertGreater(pixels[lighter + channel], pixels[normal + channel])


class TimelineSelectionFollowTests(unittest.TestCase):
    def test_ctrl_click_preserves_selection_through_seek_follow_callbacks(self):
        canvas = create_timeline_canvas(FakeGtk)(
            selection_modifier_mask=4,
            on_seek=lambda position: canvas.follow_playhead(position, playing=False),
        )
        timeline = SegmentTimeline(10)
        timeline.split(5)
        first, second = timeline.segment_items
        canvas.set_timeline(timeline, first.segment_id)
        second_clip = canvas._layout()[1]
        x, y = second_clip.x + 20, second_clip.y + 10
        control = FakeGesture(state=4)
        canvas._on_drag_begin(control, x, y)
        canvas._on_pressed(control, 1, x, y)
        canvas._on_released(control, 1, x, y)
        canvas._on_drag_end(control, 0, 0)
        self.assertEqual(
            set(canvas.get_selected_segment_ids()), {first.segment_id, second.segment_id}
        )
        first_clip = canvas._layout()[0]
        x, y = first_clip.x + 20, first_clip.y + 10
        canvas._on_drag_begin(control, x, y)
        canvas._on_pressed(control, 1, x, y)
        canvas._on_drag_end(control, 0, 0)
        canvas._on_released(control, 1, x, y)
        self.assertEqual(canvas.get_selected_segment_ids(), (second.segment_id,))
        canvas.follow_playhead(1, playing=True)
        self.assertEqual(canvas.get_selected_segment_ids(), (first.segment_id,))

    def test_follow_uses_index_and_only_notifies_when_selection_changes(self):
        selected = []
        canvas = create_timeline_canvas(FakeGtk)(on_selection_changed=selected.append)
        timeline = SegmentTimeline(10.0)
        timeline.split(5)
        first, second = timeline.segment_items
        canvas.set_timeline(timeline, first.segment_id)
        canvas.follow_playhead(5.0, playing=True)
        self.assertEqual(canvas.get_selected_segment_ids(), (second.segment_id,))
        self.assertEqual(selected, [(second.segment_id,)])
        with patch(
            "framestudio.timeline.layout_timeline_segments",
            side_effect=AssertionError("Playback must reuse layout geometry"),
        ):
            canvas.follow_playhead(5.1, playing=True)
        self.assertEqual(selected, [(second.segment_id,)])
        canvas.follow_playhead(10.0, playing=True)
        self.assertEqual(canvas.get_selected_segment_ids(), (second.segment_id,))

    def test_deleted_selection_is_preserved_only_while_paused(self):
        canvas = create_timeline_canvas(FakeGtk)()
        timeline = SegmentTimeline(10.0)
        timeline.split(5)
        first, second = timeline.segment_items
        timeline.set_deleted(first.segment_id, True)
        canvas.set_timeline(timeline, first.segment_id)
        canvas.follow_playhead(6, playing=False)
        self.assertEqual(canvas.get_selected_segment_ids(), (first.segment_id,))
        canvas.follow_playhead(6, playing=True)
        self.assertEqual(canvas.get_selected_segment_ids(), (second.segment_id,))

    def test_paused_multiselection_survives_until_playback_starts(self):
        canvas = create_timeline_canvas(FakeGtk)()
        timeline = SegmentTimeline(10.0)
        timeline.split(5)
        ids = tuple(segment.segment_id for segment in timeline.segment_items)
        canvas.set_timeline(timeline, ids[-1], ids)
        canvas.follow_playhead(6, playing=False)
        self.assertEqual(canvas.get_selected_segment_ids(), ids)
        canvas.follow_playhead(6, playing=True)
        self.assertEqual(canvas.get_selected_segment_ids(), (ids[-1],))

    def test_large_project_follow_reuses_geometry_and_notifies_only_at_boundaries(self):
        from tests.test_editor_large_timeline_performance import large_timeline

        changes = []
        canvas = create_timeline_canvas(FakeGtk)(on_selection_changed=changes.append)
        timeline = large_timeline()
        canvas.set_timeline(timeline, timeline.segment_items[0].segment_id)
        with (
            patch(
                "framestudio.timeline.layout_timeline_segments",
                side_effect=AssertionError("Following must not rebuild a 200-clip layout"),
            ),
            patch.object(
                timeline, "validate", side_effect=AssertionError("Must reuse validated timeline")
            ),
        ):
            for position in range(0, 144_000, 144):
                canvas.follow_playhead(position, playing=True)
        self.assertEqual(len(changes), 199)
        self.assertEqual(
            canvas.get_selected_segment_ids(), (timeline.segment_items[-1].segment_id,)
        )
