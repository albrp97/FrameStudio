from __future__ import annotations

import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

try:
    from test_editor_timeline import (
        FakeDrawingArea as TimelineFakeDrawingArea,
    )
    from test_editor_timeline import (
        FakeGesture,
    )
except ModuleNotFoundError:
    from tests.test_editor_timeline import (
        FakeDrawingArea as TimelineFakeDrawingArea,
    )
    from tests.test_editor_timeline import (
        FakeGesture,
    )

from framestudio.app_timeline_actions import on_timeline_segment_dropped
from framestudio.app_tracks import (
    _on_conversion_response,
    attach_editing_only,
    on_timeline_scroll_editing_only,
)
from framestudio.export_types import ExportPlanningError
from framestudio.model import (
    Project,
    ProjectValidationError,
    Segment,
    SegmentTimeline,
    TimelineTrack,
    VisualTransform,
)
from framestudio.playback import PlaybackController
from framestudio.timeline import (
    TIMELINE_HORIZONTAL_PADDING,
    TIMELINE_TRACK_HEIGHT,
    TimelineClipGeometry,
    create_timeline_canvas,
    hit_test_timeline_segment,
    layout_timeline_segments,
    layout_timeline_tracks,
    timeline_content_width,
    timeline_drag_ticks_from_x,
    timeline_pixels_per_second,
    timeline_position_from_x,
    timeline_ticks_from_x,
    timeline_x_from_ticks,
)


class FakeDrawingArea(TimelineFakeDrawingArea):
    def set_sensitive(self, _sensitive):
        pass


class FakeGtk:
    DrawingArea = FakeDrawingArea
    GestureClick = FakeGesture
    GestureDrag = FakeGesture


def canonical_block(
    segment_id: str,
    *,
    track_id: str,
    timeline_start_ticks: int,
    timeline_end_ticks: int,
    deleted: bool = False,
) -> Segment:
    return Segment.from_canonical_dict(
        {
            "segment_id": segment_id,
            "block_id": f"block-{segment_id}",
            "track_id": track_id,
            "source_id": "source-1",
            "source_start_ticks": timeline_start_ticks,
            "source_end_ticks": timeline_end_ticks,
            "timeline_start_ticks": timeline_start_ticks,
            "timeline_end_ticks": timeline_end_ticks,
            "deleted": deleted,
            "state": {},
            "color_index": None,
            "visual_transform": VisualTransform().to_dict(),
            "triplicate": None,
        },
        expected_track_id=track_id,
    )


def synchronized_timeline() -> SegmentTimeline:
    return SegmentTimeline.from_tracks(
        (
            TimelineTrack(
                "track-1",
                (
                    canonical_block(
                        "first",
                        track_id="track-1",
                        timeline_start_ticks=0,
                        timeline_end_ticks=2_000_000,
                    ),
                ),
            ),
            TimelineTrack(
                "track-2",
                (
                    canonical_block(
                        "occupied",
                        track_id="track-2",
                        timeline_start_ticks=3_000_000,
                        timeline_end_ticks=5_000_000,
                    ),
                ),
            ),
        ),
        source_durations={"source-1": 10.0},
        active_track_id="track-1",
    )


class EditorTrackDragTests(unittest.TestCase):
    def test_screen_coordinates_include_native_surface_translation(self):
        from tests.test_editor_track_drag_functionality import _screen_coordinates

        geometry = "X=100\nY=200\n"
        self.assertEqual(_screen_coordinates(geometry, (20, 30)), (120, 230))
        self.assertEqual(
            _screen_coordinates(geometry, (20, 30), surface_transform=(5, 5)),
            (125, 235),
        )

    def test_uncommitted_segment_press_snaps_before_release(self):
        for state in (0, 64):
            with self.subTest(state=state):
                seeks = []
                canvas = create_timeline_canvas(FakeGtk)(
                    on_seek=seeks.append,
                    snap_bypass_modifier_mask=64,
                )
                canvas.set_timeline(synchronized_timeline())
                canvas.set_zoom(461.32)
                clip = canvas._layout()[0]
                x, y = clip.x + clip.snap_width / 2, clip.y + clip.height / 2
                gesture = FakeGesture(state=state)
                canvas._on_drag_begin(gesture, x, y)
                canvas._on_pressed(gesture, 1, x, y)
                if state:
                    self.assertGreater(seeks[-1], clip.timeline_start_seconds)
                else:
                    self.assertEqual(seeks[-1], clip.timeline_start_seconds)

    def test_native_drag_begin_before_ctrl_press_does_not_toggle_selection_twice(self):
        drops: list[tuple[str, int, str]] = []
        canvas = create_timeline_canvas(FakeGtk)(
            selection_modifier_mask=4,
            on_segment_dropped=lambda *args: drops.append(args),
        )
        timeline = synchronized_timeline()
        canvas.set_viewport_width(640.0)
        canvas.set_timeline(timeline, "first", ("first",))
        clip = next(
            item
            for item in layout_timeline_segments(timeline, 640.0, 1.0)
            if item.segment_id == "occupied"
        )
        x, y = clip.x + clip.width / 2.0, clip.y + clip.height / 2.0
        control = FakeGesture(state=4)
        canvas._on_drag_begin(control, x, y)
        canvas._on_pressed(control, 1, x, y)
        self.assertEqual(set(canvas.get_selected_segment_ids()), {"first", "occupied"})
        canvas._on_drag_end(control, 0.0, 0.0)
        self.assertEqual(drops, [])

    def test_track_rows_and_absolute_clip_geometry_include_empty_rows(self):
        timeline = synchronized_timeline()
        rows = layout_timeline_tracks(timeline)
        clips = layout_timeline_segments(timeline, 640.0, 1.0)

        self.assertEqual([row.track_id for row in rows], ["track-1", "track-2"])
        self.assertEqual(rows[1].y - rows[0].y, TIMELINE_TRACK_HEIGHT)
        self.assertEqual(
            [(clip.segment_id, clip.track_id, clip.track_index) for clip in clips],
            [("first", "track-1", 0), ("occupied", "track-2", 1)],
        )
        self.assertNotEqual(clips[0].y, clips[1].y)
        self.assertEqual(
            hit_test_timeline_segment(
                clips,
                clips[1].x + 1.0,
                clips[1].y + clips[1].height / 2.0,
            ).segment_id,
            "occupied",
        )
        self.assertIsNone(
            hit_test_timeline_segment(
                clips,
                clips[1].x + 1.0,
                clips[0].y + clips[0].height / 2.0,
            )
        )

    def test_canvas_reports_absolute_drop_target_without_mutating_model(self):
        drops: list[tuple[str, int, str | None]] = []
        TimelineCanvas = create_timeline_canvas(FakeGtk)
        canvas = TimelineCanvas(on_segment_dropped=lambda *args: drops.append(args))
        timeline = synchronized_timeline()
        canvas.set_viewport_width(640.0)
        canvas.set_timeline(timeline)
        clips = layout_timeline_segments(timeline, 640.0, 1.0)
        first = clips[0]
        second_row = layout_timeline_tracks(timeline)[1]
        original = timeline.find("first")

        canvas._on_drag_begin(
            None,
            first.x + first.width / 2.0,
            first.y + first.height / 2.0,
        )
        canvas._on_drag_update(
            None,
            150.0,
            second_row.y + second_row.height / 2.0 - first.y - first.height / 2.0,
        )
        canvas._on_drag_end(
            None,
            150.0,
            second_row.y + second_row.height / 2.0 - first.y - first.height / 2.0,
        )

        self.assertEqual(len(drops), 1)
        self.assertEqual(drops[0][0], "first")
        self.assertEqual(drops[0][2], "track-2")
        self.assertGreaterEqual(drops[0][1], 0)
        self.assertEqual(timeline.find("first"), original)

    def test_legacy_canvas_keeps_empty_area_drag_seek_behavior(self):
        seeks: list[float] = []
        TimelineCanvas = create_timeline_canvas(FakeGtk)
        canvas = TimelineCanvas(on_seek=seeks.append)
        canvas.set_viewport_width(100.0)
        canvas.set_timeline(SegmentTimeline(10.0))

        canvas._on_drag_begin(None, 20.0, 0.0)
        canvas._on_drag_update(None, 10.0, 0.0)
        canvas._on_drag_end(None, 20.0, 0.0)

        self.assertEqual(len(seeks), 3)
        self.assertLess(seeks[0], seeks[1])
        self.assertLess(seeks[1], seeks[2])

    def test_drag_tick_mapping_is_unbounded_but_seek_mapping_stays_clamped(self):
        duration_seconds = 2.0
        viewport_width = 640.0
        zoom = 1.0
        target_ticks = 7_000_000
        target_x = timeline_x_from_ticks(
            target_ticks,
            duration_seconds,
            viewport_width,
            zoom,
        )

        self.assertEqual(
            timeline_ticks_from_x(
                target_x,
                duration_seconds,
                viewport_width,
                zoom,
            ),
            2_000_000,
        )
        self.assertEqual(
            timeline_drag_ticks_from_x(
                target_x,
                duration_seconds,
                viewport_width,
                zoom,
            ),
            target_ticks,
        )
        self.assertEqual(
            timeline_drag_ticks_from_x(
                -100.0,
                duration_seconds,
                viewport_width,
                zoom,
            ),
            0,
        )

    def test_empty_timeline_geometry_allows_zero_but_rejects_invalid_duration(self):
        self.assertEqual(timeline_content_width(0.0, 640.0, 1.0), 24.0)
        self.assertEqual(
            timeline_position_from_x(100.0, 0.0, 640.0, 1.0),
            0.0,
        )
        self.assertGreater(
            timeline_pixels_per_second(0.0, 640.0, 1.0),
            timeline_pixels_per_second(1.0, 640.0, 1.0),
        )
        for invalid_duration in (-1.0, float("nan"), float("inf")):
            with self.assertRaises(ValueError):
                timeline_pixels_per_second(invalid_duration, 640.0, 1.0)
            with self.assertRaises(ValueError):
                timeline_content_width(invalid_duration, 640.0, 1.0)

    def test_drag_preview_uses_first_fit_for_collision_chain_and_free_gap(self):
        timeline = SegmentTimeline.from_tracks(
            (
                TimelineTrack(
                    "track-1",
                    (
                        canonical_block(
                            "moving",
                            track_id="track-1",
                            timeline_start_ticks=0,
                            timeline_end_ticks=2_000_000,
                        ),
                    ),
                ),
                TimelineTrack(
                    "track-2",
                    (
                        canonical_block(
                            "chain-a",
                            track_id="track-2",
                            timeline_start_ticks=2_000_000,
                            timeline_end_ticks=4_000_000,
                        ),
                        canonical_block(
                            "chain-b",
                            track_id="track-2",
                            timeline_start_ticks=4_000_000,
                            timeline_end_ticks=6_000_000,
                        ),
                    ),
                ),
            ),
            source_durations={"source-1": 12.0},
            active_track_id="track-1",
        )
        TimelineCanvas = create_timeline_canvas(FakeGtk)
        canvas = TimelineCanvas()
        canvas.set_viewport_width(640.0)
        canvas.set_timeline(timeline)
        moving = next(
            clip
            for clip in layout_timeline_segments(timeline, 640.0, 1.0)
            if clip.segment_id == "moving"
        )
        destination_row = layout_timeline_tracks(timeline)[1]
        canvas._on_drag_begin(
            None,
            moving.x + moving.width / 2.0,
            moving.y + moving.height / 2.0,
        )
        pointer_offset_ticks = 1_000_000

        def update_preview(requested_start_ticks: int) -> tuple[int, ...]:
            pointer_target_ticks = requested_start_ticks + pointer_offset_ticks
            target_x = timeline_x_from_ticks(
                pointer_target_ticks,
                timeline.timeline_duration_seconds,
                640.0,
                1.0,
            )
            canvas._on_drag_update(
                None,
                target_x - (moving.x + moving.width / 2.0),
                destination_row.y + destination_row.height / 2.0 - (moving.y + moving.height / 2.0),
            )
            assert canvas._drag_preview is not None
            target_ticks, target_track_id = canvas._drag_preview
            assert target_track_id == "track-2"
            return target_ticks, tuple(
                int(
                    round(
                        (clip.x - TIMELINE_HORIZONTAL_PADDING)
                        / timeline_pixels_per_second(
                            timeline.timeline_duration_seconds,
                            640.0,
                            1.0,
                        )
                        * 1_000_000,
                    )
                )
                for clip in canvas._clips_with_drag_preview(
                    layout_timeline_segments(timeline, 640.0, 1.0),
                    layout_timeline_tracks(timeline),
                )
                if clip.segment_id == "moving"
            )

        self.assertEqual(update_preview(1_000_000), (6_000_000, (6_000_000,)))
        self.assertEqual(update_preview(8_000_000), (8_000_000, (8_000_000,)))

    def test_dragging_selected_member_preserves_multiselection_and_focus(self):
        project = Project.create_synchronized(
            Path(__file__),
            {
                "duration_seconds": 4.0,
                "frame_rate": "24/1",
            },
            project_id="selection-preservation",
        )
        first, second = project.timeline.split(2.0)
        window = SimpleNamespace(
            project=project,
            segment_timeline=project.timeline,
            selected_segment_id=second.segment_id,
            selected_segment_ids=(first.segment_id, second.segment_id),
            _refresh_timeline=lambda selected_id: setattr(
                window,
                "refreshed_selection_id",
                selected_id,
            ),
            _set_status=lambda message: setattr(window, "status", message),
            _show_error=lambda message: setattr(window, "error", message),
        )

        on_timeline_segment_dropped(
            window,
            first.segment_id,
            5_000_000,
            "track-1",
        )

        self.assertEqual(
            window.selected_segment_ids,
            (first.segment_id, second.segment_id),
        )
        self.assertEqual(window.selected_segment_id, second.segment_id)
        self.assertEqual(window.refreshed_selection_id, second.segment_id)
        self.assertEqual(project.timeline.find(first.segment_id).timeline_start_ticks, 5_000_000)
        self.assertEqual(project.timeline.find(second.segment_id).timeline_start_ticks, 7_000_000)

    def test_selected_group_preview_and_drop_include_every_selected_clip(self):
        project = Project.create_synchronized(
            Path(__file__), {"duration_seconds": 4, "frame_rate": "24/1"}
        )
        first, second = project.timeline.split(2)
        project.timeline.add_track("track-2")
        drops = []
        canvas = create_timeline_canvas(FakeGtk)(
            on_segment_dropped=lambda *arguments: drops.append(arguments)
        )
        canvas.set_timeline(
            project.timeline, second.segment_id, (first.segment_id, second.segment_id)
        )
        before = project.timeline.to_dict()
        clip = canvas._layout()[0]
        rows = layout_timeline_tracks(project.timeline)
        x, y = clip.x + clip.width / 2, clip.y + clip.height / 2
        offset_y = rows[1].y - rows[0].y
        canvas._on_drag_begin(FakeGesture(), x, y)
        canvas._on_pressed(FakeGesture(), 1, x, y)
        canvas._on_drag_update(FakeGesture(), 0, offset_y)
        preview = canvas._clips_with_drag_preview(canvas._layout(), rows)
        self.assertEqual({item.track_id for item in preview}, {"track-2"})
        self.assertEqual(project.timeline.to_dict(), before)
        canvas._set_selection((first.segment_id,), first.segment_id, notify=False)
        canvas._on_drag_end(FakeGesture(), 0, offset_y)
        self.assertEqual(drops[0][3], (first.segment_id, second.segment_id))

    def test_group_move_fits_every_member_together_and_is_atomic_on_invalid_track(self):
        project = Project.create_synchronized(
            Path(__file__), {"duration_seconds": 6, "frame_rate": "24/1"}
        )
        project.timeline.split(2)
        project.timeline.split(4)
        first, middle, last = project.timeline.segment_items
        project.timeline.add_track("track-2")
        occupied = project.timeline.paste_blocks(
            (middle,), at_ticks=3_000_000, target_track_id="track-2"
        )[0]
        project.timeline.set_deleted(occupied.segment_id, True)
        occupied = project.timeline.find(occupied.segment_id)
        selected = (first.segment_id, last.segment_id)
        before = project.timeline.to_dict()
        project.timeline.move_blocks_to_track(
            selected,
            anchor_segment_id=first.segment_id,
            timeline_start_ticks=0,
            target_track_id="track-2",
        )
        moved_first, moved_last = (project.timeline.find(item) for item in selected)
        self.assertEqual(moved_first.timeline_start_ticks, 1_000_000)
        self.assertEqual(moved_last.timeline_start_ticks, 5_000_000)
        self.assertEqual(project.timeline.find(occupied.segment_id), occupied)
        self.assertEqual(project.timeline.find(middle.segment_id), middle)
        self.assertEqual(moved_first.source_start_ticks, first.source_start_ticks)
        self.assertEqual(moved_last.source_end_ticks, last.source_end_ticks)
        committed = project.timeline.to_dict()
        self.assertNotEqual(committed, before)
        with self.assertRaises(ProjectValidationError):
            project.timeline.move_blocks_to_track(
                (middle.segment_id, moved_first.segment_id),
                anchor_segment_id=middle.segment_id,
                timeline_start_ticks=0,
                target_track_id="track-2",
            )
        self.assertEqual(project.timeline.to_dict(), committed)

    def test_group_anchored_on_later_clip_keeps_time_and_track_offsets_at_zero(self):
        project = Project.create_synchronized(
            Path(__file__), {"duration_seconds": 4, "frame_rate": "24/1"}
        )
        first, second = project.timeline.split(2)
        project.timeline.add_track("track-2")
        project.timeline.add_track("track-3")
        parallel = project.timeline.paste_blocks(
            (first,), at_ticks=3_000_000, target_track_id="track-2"
        )[0]
        project.timeline.move_blocks_to_track(
            (first.segment_id, parallel.segment_id),
            anchor_segment_id=parallel.segment_id,
            timeline_start_ticks=0,
            target_track_id="track-3",
        )
        moved_first = project.timeline.find(first.segment_id)
        moved_parallel = project.timeline.find(parallel.segment_id)
        self.assertEqual((moved_first.track_id, moved_first.timeline_start_ticks), ("track-2", 0))
        self.assertEqual(
            (moved_parallel.track_id, moved_parallel.timeline_start_ticks), ("track-3", 3_000_000)
        )
        self.assertEqual(project.timeline.find(second.segment_id), second)
        project.validate()

    def test_invalid_fps_confirmation_preserves_legacy_attachment_state(self):
        project = Project.create(
            Path(__file__),
            {
                "duration_seconds": 4.0,
                "frame_rate": "invalid",
            },
            project_id="invalid-fps-confirmation",
        )
        original_timing_mode = project.timeline.timing_mode
        backend = object()
        controller = object()

        class Dialog:
            def __init__(self):
                self.closed = False

            def close(self):
                self.closed = True

        dialog = Dialog()
        window = SimpleNamespace(
            project=project,
            segment_timeline=project.timeline,
            backend=backend,
            controller=controller,
            selected_segment_id=project.timeline.segments[0].segment_id,
            selected_segment_ids=(project.timeline.segments[0].segment_id,),
            _show_error=lambda message: setattr(window, "error", message),
        )

        _on_conversion_response(window, dialog, 1)

        self.assertTrue(dialog.closed)
        self.assertEqual(project.timeline.timing_mode, original_timing_mode)
        self.assertIs(window.backend, backend)
        self.assertIs(window.controller, controller)
        self.assertEqual(
            window.selected_segment_ids,
            (project.timeline.segments[0].segment_id,),
        )
        self.assertIn("frame_rate", window.error)

    def test_synchronized_scroll_seek_uses_playback_controller(self):
        project = Project.create_synchronized(
            Path(__file__),
            {
                "duration_seconds": 60.0,
                "frame_rate": "24/1",
            },
            project_id="editing-only-scroll",
        )

        class Adjustment:
            def __init__(self):
                self.value = 0.0

            def get_lower(self):
                return 0.0

            def get_upper(self):
                return 2000.0

            def get_page_size(self):
                return 400.0

            def get_value(self):
                return self.value

            def set_value(self, value):
                self.value = value

        class Label:
            def set_text(self, _text):
                pass

        class Canvas:
            def set_playhead(self, _position):
                pass

        class Gdk:
            class ModifierType:
                CONTROL_MASK = 1
                ALT_MASK = 2
                SHIFT_MASK = 4

        class ScrollController:
            def get_current_event_state(self):
                return 0

        adjustment = Adjustment()
        positions: list[float] = []
        backend = MagicMock()
        backend.request_preview.side_effect = positions.append
        window = SimpleNamespace(
            project=project,
            segment_timeline=project.timeline,
            timeline_viewport=SimpleNamespace(
                get_hadjustment=lambda: adjustment,
            ),
            position_label=Label(),
            timeline_canvas=Canvas(),
            backend=backend,
            controller=PlaybackController(backend, project.timeline.timeline_duration_seconds),
            _set_status=lambda _message: None,
            _zoom_timeline=lambda _direction: None,
            _update_playback_controls=lambda: None,
        )

        self.assertTrue(
            on_timeline_scroll_editing_only(
                window,
                ScrollController(),
                0.0,
                -1.0,
                Gdk,
            ),
        )
        self.assertEqual(project.playhead_seconds, 30.0)
        self.assertEqual(positions, [30.0])

    def test_editing_only_attachment_rejects_invalid_frame_rate_before_stopping_preview(self):
        project = Project.create_synchronized(
            Path(__file__),
            {
                "duration_seconds": 1.0,
                "width": 320,
                "height": 180,
                "frame_rate": "24/1",
            },
            project_id="invalid-frame-rate",
        )
        project.source.metadata["frame_rate"] = "not-a-rate"
        backend = object()
        controller = object()
        window = SimpleNamespace(backend=backend, controller=controller)

        with self.assertRaises(ExportPlanningError):
            attach_editing_only(window, project, None)

        self.assertIs(window.backend, backend)
        self.assertIs(window.controller, controller)

    def test_geometry_defaults_remain_compatible_with_existing_clip_rendering(self):
        clip = TimelineClipGeometry(
            segment_id="clip",
            index=0,
            start_seconds=0.0,
            end_seconds=1.0,
            timeline_start_seconds=0.0,
            timeline_end_seconds=1.0,
            source_id=None,
            deleted=False,
            x=10.0,
            width=16.0,
        )

        self.assertEqual(clip.track_id, "track-1")
        self.assertEqual(clip.track_index, 0)
        self.assertGreater(clip.height, 0.0)


if __name__ == "__main__":
    unittest.main()
