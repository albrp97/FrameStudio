import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from framestudio.app_playback import handle_backend_warning
from framestudio.app_project import attach_project, refresh_playback_backend
from framestudio.model import Project


class PreviewWarningPriorityTests(unittest.TestCase):
    def test_current_warning_is_recorded_without_overwriting_errors_or_stale_generations(self):
        for status, generation, shown in (
            ("Paused", 7, True),
            ("Error: invalid frame_rate", 7, False),
            ("Paused", 6, False),
        ):
            with self.subTest(status=status, generation=generation):
                window = SimpleNamespace(
                    _playback_generation=7,
                    status_label=SimpleNamespace(get_text=lambda status=status: status),
                    _set_status=MagicMock(),
                )
                self.assertFalse(
                    handle_backend_warning(window, "Exact FFmpeg fallback", generation)
                )
                if shown:
                    window._set_status.assert_called_once_with("Warning: Exact FFmpeg fallback")
                else:
                    window._set_status.assert_not_called()
                self.assertEqual(
                    getattr(window, "_last_playback_warning", None),
                    "Exact FFmpeg fallback" if generation == 7 else None,
                )


class SequentialRoutingTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        paths = [root / f"source-{index}.mp4" for index in range(3)]
        for path in paths:
            path.write_bytes(b"fixture")
        metadata = {
            "duration_seconds": 8.0,
            "width": 1920,
            "height": 1080,
            "frame_rate": "30/1",
            "video_codec": "h264",
            "audio_stream_present": False,
        }
        self.project = Project.create_multi(tuple((path, metadata) for path in paths))
        self.window = SimpleNamespace(
            backend=None,
            controller=None,
            project=None,
            project_path=None,
            segment_timeline=None,
            source_frame_rate=30.0,
            timeline_canvas=MagicMock(),
            audio_status_label=MagicMock(),
            play_button=MagicMock(),
            _stop_backend=MagicMock(),
            _on_frame=MagicMock(),
            _on_backend_error=MagicMock(),
            _on_backend_end=MagicMock(),
            _on_backend_warning=MagicMock(),
            _update_selected_clip_label=MagicMock(),
            _update_playback_controls=MagicMock(),
            _update_segment_controls=MagicMock(),
        )

    def test_import_uses_active_interval_backend_without_changing_timeline_mapping(self):
        timeline = self.project.timeline
        timeline.set_deleted(timeline.segment_items[1].segment_id, True)
        self.project.set_playhead(18.0)
        with (
            patch("framestudio.app_project.FfmpegComposedPlaybackBackend") as old,
            patch("framestudio.app_project.FfmpegSequentialPlaybackBackend", create=True) as active,
        ):
            attach_project(self.window, self.project, None)
            old.assert_not_called()
            active.assert_called_once()
            layout = active.call_args.args[2]
            self.assertEqual(layout.timing_mode, "legacy-ripple")
            self.assertEqual(layout.final_duration_seconds, 16.0)
            self.assertEqual(len(layout.included_blocks), 2)
            self.assertAlmostEqual(self.window.controller.snapshot().position_seconds, 10.0)
            active.return_value.seek.assert_called_once_with(10.0)
            self.assertEqual(self.project.playhead_seconds, 18.0)
            self.assertEqual(self.project.timeline.timing_mode, "legacy-ripple")

    def test_refresh_uses_same_active_route_and_preserves_live_output_position(self):
        with (
            patch("framestudio.app_project.FfmpegComposedPlaybackBackend") as old,
            patch("framestudio.app_project.FfmpegSequentialPlaybackBackend", create=True) as active,
        ):
            attach_project(self.window, self.project, None)
            self.window.backend.current_position.return_value = 10.25
            refresh_playback_backend(self.window, force=True)
            old.assert_not_called()
            self.assertEqual(active.call_count, 2)
            self.assertEqual(self.window.controller.snapshot().position_seconds, 10.25)
            self.assertEqual(self.project.playhead_seconds, 10.25)


if __name__ == "__main__":
    unittest.main()
