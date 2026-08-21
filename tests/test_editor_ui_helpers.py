import unittest
from pathlib import Path

from resolve_editor.app import (
    _metadata_float,
    create_play_pause_key_controller,
    format_export_progress_label,
    format_output_duration_label,
    format_segment_label,
    frame_step_direction,
    frame_step_position,
    is_delete_key,
    is_fit_zoom_key,
    is_frame_step_key,
    is_play_pause_key,
    segment_action_state,
    timeline_scroll_mode,
    timeline_scroll_position,
    toggle_segment_deleted_state,
    validate_source_selection,
)
from resolve_editor.export import ExportProgress
from resolve_editor.model import SegmentTimeline
from resolve_editor.ui import format_duration


class EditorUiHelperTests(unittest.TestCase):
    def test_format_duration_is_readable(self):
        self.assertEqual(format_duration(0), "00:00")
        self.assertEqual(format_duration(65.25), "01:05")
        self.assertEqual(format_duration(3661.9), "01:01:01")

    def test_metadata_float_accepts_rational_frame_rate(self):
        self.assertEqual(_metadata_float({"frame_rate": "10/1"}, "frame_rate"), 10.0)

    def test_source_selection_accepts_one_source_for_current_phase(self):
        selected = validate_source_selection([Path("/tmp/one.mp4")])

        self.assertEqual(selected, (Path("/tmp/one.mp4"),))

    def test_source_selection_rejects_multiple_sources_until_supported(self):
        with self.assertRaisesRegex(ValueError, "one source video per project"):
            validate_source_selection([Path("/tmp/one.mp4"), Path("/tmp/two.mp4")])

    def test_source_selection_uses_the_configured_phase_limit(self):
        selected = validate_source_selection(
            [Path("/tmp/one.mp4"), Path("/tmp/two.mp4")],
            max_sources=2,
        )

        self.assertEqual(
            selected,
            (Path("/tmp/one.mp4"), Path("/tmp/two.mp4")),
        )

    def test_timeline_scroll_moves_the_playhead_in_both_directions(self):
        self.assertEqual(timeline_scroll_position(10.0, -1.0, 60.0), 11.0)
        self.assertEqual(timeline_scroll_position(10.0, 1.0, 60.0), 9.0)

    def test_timeline_scroll_stays_within_the_duration(self):
        self.assertEqual(timeline_scroll_position(0.0, 1.0, 60.0), 0.0)
        self.assertEqual(timeline_scroll_position(60.0, -1.0, 60.0), 60.0)

    def test_space_is_the_play_pause_key(self):
        self.assertTrue(is_play_pause_key(ord(" ")))
        self.assertFalse(is_play_pause_key(ord("p")))

    def test_delete_is_the_clip_delete_key(self):
        self.assertTrue(is_delete_key(0xFFFF))
        self.assertTrue(is_delete_key(0xFF9F))
        self.assertFalse(is_delete_key(0xFF08))

    def test_left_and_right_are_frame_step_keys(self):
        self.assertTrue(is_frame_step_key(0xFF51))
        self.assertTrue(is_frame_step_key(0xFF53))
        self.assertEqual(frame_step_direction(0xFF51), -1)
        self.assertEqual(frame_step_direction(0xFF53), 1)
        self.assertIsNone(frame_step_direction(0xFF52))

    def test_frame_step_moves_one_source_frame_and_clamps(self):
        self.assertAlmostEqual(
            frame_step_position(1.0, 1, 30.0, 60.0),
            1.0 + (1.0 / 30.0),
        )
        self.assertEqual(
            frame_step_position(0.0, -1, 30.0, 60.0),
            0.0,
        )
        self.assertEqual(
            frame_step_position(60.0, 1, 30.0, 60.0),
            60.0,
        )

    def test_output_duration_label_describes_final_video_length(self):
        self.assertEqual(
            format_output_duration_label(65.25),
            "Final output: 01:05",
        )

    def test_delete_toggles_selected_clip_between_included_and_deleted(self):
        timeline = SegmentTimeline(12.5)
        segment_id = timeline.segments[0].segment_id

        self.assertTrue(toggle_segment_deleted_state(timeline, segment_id))
        self.assertTrue(timeline.segments[0].deleted)
        self.assertFalse(toggle_segment_deleted_state(timeline, segment_id))
        self.assertFalse(timeline.segments[0].deleted)

    def test_control_scroll_zoom_and_alt_or_horizontal_scroll_navigate(self):
        self.assertEqual(
            timeline_scroll_mode(0.0, -1.0, 4, 4, 8, 1),
            "zoom",
        )
        self.assertEqual(
            timeline_scroll_mode(0.0, 1.0, 8, 4, 8, 1),
            "viewport",
        )
        self.assertEqual(
            timeline_scroll_mode(1.0, 0.0, 0, 4, 8, 1),
            "viewport",
        )
        self.assertEqual(
            timeline_scroll_mode(0.0, 1.0, 0, 4, 8, 1),
            "playhead",
        )
        self.assertEqual(
            timeline_scroll_mode(0.0, 0.0, 0, 4, 8, 1),
            "none",
        )

    def test_control_zero_is_the_fit_zoom_shortcut(self):
        self.assertTrue(is_fit_zoom_key(ord("0"), 4, 4))
        self.assertFalse(is_fit_zoom_key(ord("0"), 0, 4))
        self.assertFalse(is_fit_zoom_key(ord("1"), 4, 4))

    def test_export_progress_label_includes_all_requested_metrics(self):
        progress = ExportProgress(
            stage="encoding",
            percent=42.0,
            frame=42,
            total_frames=300,
            fps=30.0,
            elapsed_seconds=5.0,
            eta_seconds=7.5,
        )

        label = format_export_progress_label(progress)

        self.assertIn("42.0%", label)
        self.assertIn("frame 42/300", label)
        self.assertIn("30.0 fps", label)
        self.assertIn("ETA 00:07", label)

    def test_space_controller_captures_before_focused_controls(self):
        import gi

        gi.require_version("Gtk", "4.0")
        from gi.repository import Gtk

        controller = create_play_pause_key_controller(
            Gtk,
            lambda *_args: True,
        )

        self.assertEqual(
            controller.get_propagation_phase(),
            Gtk.PropagationPhase.CAPTURE,
        )

    def test_segment_label_shows_ordered_bounds_and_state(self):
        timeline = SegmentTimeline(12.5)
        timeline.split(4.5)

        self.assertEqual(
            format_segment_label(1, timeline.segments[1]),
            "Segment 2: 00:04 - 00:12 (Active)",
        )

        timeline.delete_segment(timeline.segments[1].segment_id)
        self.assertEqual(
            format_segment_label(1, timeline.segments[1]),
            "Segment 2: 00:04 - 00:12 (Deleted)",
        )

    def test_segment_action_state_matches_selected_segment(self):
        timeline = SegmentTimeline(12.5)
        active_id = timeline.segments[0].segment_id

        self.assertEqual(
            segment_action_state(timeline, active_id),
            (True, False),
        )
        timeline.delete_segment(active_id)
        self.assertEqual(
            segment_action_state(timeline, active_id),
            (False, True),
        )
        self.assertEqual(segment_action_state(timeline, None), (False, False))


if __name__ == "__main__":
    unittest.main()
