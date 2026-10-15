import random
import unittest
from dataclasses import FrozenInstanceError
from unittest.mock import PropertyMock, patch

import cairo

from framestudio import timeline_geometry as geometry
from framestudio.model import Segment, SegmentTimeline
from framestudio.timeline import create_timeline_canvas

try:
    from test_editor_timeline import FakeGtk
    from test_editor_track_drag import synchronized_timeline
except ModuleNotFoundError:
    from tests.test_editor_timeline import FakeGtk
    from tests.test_editor_track_drag import synchronized_timeline


def clip(index, x, width=1.0, y=64.0, height=28.0):
    return geometry.TimelineClipGeometry(
        segment_id=f"segment-{index}",
        index=index,
        start_seconds=0.0,
        end_seconds=1.0,
        timeline_start_seconds=0.0,
        timeline_end_seconds=1.0,
        source_id=None,
        deleted=index % 3 == 0,
        x=x,
        width=width,
        y=y,
        height=height,
    )


def scan_visible(clips, bounds):
    left, top, right, bottom = bounds
    return tuple(
        item
        for item in clips
        if item.end_x + 12 >= left
        and item.x - 12 <= right
        and item.end_y + 12 >= top
        and item.y - 12 <= bottom
    )


def reference_draw(canvas, context, width, height):
    """The pre-index draw path, retained only as an independent test oracle."""
    context.set_source_rgb(0.055, 0.063, 0.10)
    context.paint()
    scale = geometry.timeline_pixels_per_second(
        canvas._timeline_duration_seconds(), canvas._viewport_width, canvas._zoom
    )
    canvas._draw_ruler(
        context,
        max(canvas._timeline_duration_seconds(), canvas._fit_window_seconds or 0),
        scale,
        width,
    )
    rows = canvas._layout_rows
    canvas._draw_track(context, width, rows)
    clips = canvas._clips_with_drag_preview(canvas._layout(), rows)
    for item in scan_visible(clips, context.clip_extents()):
        canvas._draw_clip(context, item)
    canvas._draw_playhead(context, scale, rows)


def render(canvas, bounds, reference=False):
    left, top, right, bottom = bounds
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, int(right - left), int(bottom - top))
    context = cairo.Context(surface)
    context.translate(-left, -top)
    if reference:
        reference_draw(canvas, context, int(canvas.get_content_width()), 500)
    else:
        canvas._draw_contents(context, int(canvas.get_content_width()), 500)
    surface.flush()
    return bytes(surface.get_data())


class TimelineViewIndexTests(unittest.TestCase):
    def index(self, clips):
        return geometry.TimelineViewIndex.from_clips(clips)

    def test_unsorted_overlaps_minimum_width_and_inclusive_halo_boundaries(self):
        clips = (
            clip(0, 900, 1),
            clip(1, 0, 1000),
            clip(2, 111, 1),
            clip(3, 88, 1),
            clip(4, 112.001, 1),
            clip(5, 86.999, 1),
            clip(6, 100, 1, y=104),
            clip(7, 100, 1, y=104.001),
            clip(8, 100, 1, y=23.999),
            clip(9, 100, 1, y=24),
        )
        bounds = (100, 64, 100, 92)
        expected = scan_visible(clips, bounds)
        self.assertEqual(tuple(item.index for item in expected), (1, 2, 3, 6, 9))
        self.assertEqual(self.index(clips).query(*bounds), expected)

    def test_random_unsorted_multiple_rows_match_scan_in_original_input_order(self):
        rng = random.Random(1234)
        clips = [
            clip(
                index,
                rng.uniform(-50, 2000),
                rng.choice((1, 3, 50, 800)),
                y=rng.choice((64, 118, 172, 300)),
                height=rng.choice((20, 28, 60)),
            )
            for index in range(600)
        ]
        rng.shuffle(clips)
        clips = tuple(clips)
        index = self.index(clips)
        for _ in range(100):
            left, top = rng.uniform(-100, 2100), rng.uniform(0, 400)
            bounds = (left, top, left + rng.uniform(0, 100), top + rng.uniform(0, 80))
            self.assertEqual(index.query(*bounds), scan_visible(clips, bounds))

    def test_empty_and_immutable_snapshot(self):
        index = self.index(())
        self.assertEqual(index.query(0, 0, 800, 124), ())
        self.assertIsNone(index.clip_for_segment("absent"))
        clips = [clip(0, 10)]
        index = self.index(clips)
        clips.clear()
        self.assertEqual(index.query(0, 0, 800, 124), (clip(0, 10),))
        with self.assertRaises(FrozenInstanceError):
            index.rows = ()
        with self.assertRaises(TypeError):
            index._clips_by_segment["replacement"] = clip(1, 20)

    def test_narrow_query_does_not_read_all_clip_ends(self):
        clips = tuple(clip(index, index * 10.0) for index in range(10000))
        index = self.index(clips)
        original = geometry.TimelineClipGeometry.end_x.fget
        reads = []

        def end_x(item):
            reads.append(item.segment_id)
            return original(item)

        with patch.object(geometry.TimelineClipGeometry, "end_x", property(end_x)):
            actual = index.query(50000, 64, 50010, 92)
        self.assertEqual(actual, scan_visible(clips, (50000, 64, 50010, 92)))
        self.assertLessEqual(len(reads), 5)

    def test_vertical_query_does_not_visit_offscreen_rows(self):
        clips = tuple(clip(index, 0, y=index * 54.0) for index in range(10000))
        index = self.index(clips)
        with patch.object(
            geometry.TimelineClipGeometry, "end_x", new_callable=PropertyMock, return_value=1
        ) as end_x:
            actual = index.query(0, 270000, 1, 270028)
        self.assertEqual(actual, (clips[5000],))
        self.assertLessEqual(end_x.call_count, 2)


class TimelineViewCanvasTests(unittest.TestCase):
    def setUp(self):
        self.canvas = create_timeline_canvas(FakeGtk)()
        self.timeline = SegmentTimeline.from_segments(
            1000.0,
            tuple(Segment.create(index, index + 1) for index in range(1000)),
        )
        self.canvas.set_timeline(self.timeline)
        self.canvas.set_zoom(100)

    def test_cached_draw_queries_index_without_iterating_full_layout(self):
        class NoIteration(tuple):
            def __iter__(self):
                raise AssertionError("draw must not iterate the full cached layout")

        expected = scan_visible(self.canvas._layout(), (30000, 0, 30800, 124))
        self.canvas._layout_clips = NoIteration(self.canvas._layout_clips)
        with patch.object(self.canvas, "_draw_clip") as draw:
            render(self.canvas, (30000, 0, 30800, 124))
        self.assertEqual(tuple(call.args[1] for call in draw.call_args_list), expected)

    def test_selection_playhead_and_scroll_reuse_index_and_full_model_selection(self):
        before = self.canvas._view_index
        ids = tuple(segment.segment_id for segment in self.timeline.segment_items)
        self.canvas.set_selected_segments((ids[0], ids[-1]))
        self.canvas.set_playhead(900)
        render(self.canvas, (30000, 0, 30800, 124))
        self.assertIs(self.canvas._view_index, before)
        self.assertEqual(self.canvas.get_selected_segment_ids(), (ids[0], ids[-1]))
        self.canvas._select_clip(ids[-1], additive=False, range_selection=True)
        self.assertEqual(self.canvas.get_selected_segment_ids(), (ids[-1],))
        self.canvas.set_selected_segment(ids[0])
        self.canvas._select_clip(ids[-1], additive=False, range_selection=True)
        self.assertEqual(self.canvas.get_selected_segment_ids(), ids)
        self.assertIs(self.canvas._view_index, before)

    def test_model_zoom_resize_new_timeline_and_clear_refresh_index(self):
        before = self.canvas._view_index
        self.timeline.set_deleted(self.timeline.segment_items[0].segment_id, True)
        self.canvas._layout()
        self.assertIsNot(self.canvas._view_index, before)
        self.assertTrue(
            self.canvas._view_index.clip_for_segment(
                self.timeline.segment_items[0].segment_id
            ).deleted
        )
        for operation in (
            lambda: self.canvas.set_zoom(200),
            lambda: self.canvas.set_viewport_width(1200),
            lambda: self.canvas.set_timeline(SegmentTimeline(1000)),
        ):
            before = self.canvas._view_index
            operation()
            self.assertIsNot(self.canvas._view_index, before)
            self.assert_index_matches_full_layout()
        self.canvas.set_timeline(None)
        self.assertEqual(self.canvas._view_index.query(0, 0, 100000, 10000), ())

    def test_tracks_activation_and_tuple_replacement_invalidate_index(self):
        timeline = synchronized_timeline()
        self.canvas.set_timeline(timeline)
        for operation in (
            lambda: timeline.add_track(),
            lambda: timeline.set_active_track("track-2"),
            lambda: setattr(timeline, "tracks", tuple(reversed(timeline.tracks))),
        ):
            before = self.canvas._view_index
            operation()
            self.canvas._layout()
            self.assertIsNot(self.canvas._view_index, before)
            self.assert_index_matches_full_layout()

    def test_legacy_segment_tuple_replacement_without_revision_rebuilds_index(self):
        before = self.canvas._view_index
        revision = self.timeline.revision
        self.timeline.segments = tuple(
            Segment.create(index, index + 2) for index in range(0, 1000, 2)
        )
        self.assertEqual(self.timeline.revision, revision)
        self.canvas._layout()
        self.assertIsNot(self.canvas._view_index, before)
        self.assert_index_matches_full_layout()

    def assert_index_matches_full_layout(self):
        self.assertEqual(
            self.canvas._view_index.query(-100, -100, float("inf"), float("inf")),
            self.canvas._layout(),
        )

    def test_exact_pixels_match_scan_for_scroll_selection_deleted_and_minwidth(self):
        self.timeline.set_deleted(self.timeline.segment_items[400].segment_id, True)
        self.canvas.set_selected_segment(self.timeline.segment_items[401].segment_id)
        for zoom, bounds in (
            (100, (30800, 0, 31600, 124)),
            (1, (0, 0, 800, 124)),
            (100, (30000, 70, 30800, 124)),
        ):
            self.canvas.set_zoom(zoom)
            self.assertEqual(render(self.canvas, bounds), render(self.canvas, bounds, True))

    def test_offscreen_drag_into_view_and_visible_drag_out_preserve_pixels_and_order(self):
        self.canvas.set_timeline(synchronized_timeline())
        self.canvas.set_zoom(10)
        before = self.canvas._view_index
        self.canvas._drag_segment_id = "occupied"
        self.canvas._drag_preview = (0, "track-1")
        self.canvas.set_selected_segments(("first", "occupied"))
        for bounds in ((0, 0, 800, 160), (4500, 0, 5300, 160), (0, 100, 800, 180)):
            with patch.object(self.canvas, "_draw_clip") as draw:
                render(self.canvas, bounds)
            expected = scan_visible(
                self.canvas._clips_with_drag_preview(
                    self.canvas._layout(), self.canvas._layout_rows
                ),
                bounds,
            )
            self.assertEqual(tuple(call.args[1] for call in draw.call_args_list), expected)
            self.assertEqual(render(self.canvas, bounds), render(self.canvas, bounds, True))
        self.canvas._drag_preview = (4_000_000, "track-2")
        self.canvas._drag_segment_id = "first"
        self.assertEqual(
            render(self.canvas, (0, 0, 800, 160)),
            render(self.canvas, (0, 0, 800, 160), True),
        )
        self.canvas._drag_preview = (0, None)
        self.assertEqual(
            render(self.canvas, (0, 0, 800, 160)),
            render(self.canvas, (0, 0, 800, 160), True),
        )
        self.canvas._clear_drag_state()
        self.assertIs(self.canvas._view_index, before)
        self.assertEqual(
            render(self.canvas, (0, 0, 800, 160)),
            render(self.canvas, (0, 0, 800, 160), True),
        )

    def test_drag_does_not_scan_full_layout(self):
        class NoIteration(tuple):
            def __iter__(self):
                raise AssertionError("drag preview must not scan the full cached layout")

        self.canvas._drag_segment_id = self.timeline.segment_items[-1].segment_id
        self.canvas._drag_preview = (0, "track-1")
        self.canvas._layout_clips = NoIteration(self.canvas._layout_clips)
        with patch.object(self.canvas, "_draw_clip") as draw:
            render(self.canvas, (0, 0, 800, 124))
        self.assertIn(
            self.canvas._drag_segment_id,
            tuple(call.args[1].segment_id for call in draw.call_args_list),
        )


if __name__ == "__main__":
    unittest.main()
