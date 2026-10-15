import threading
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock

from framestudio.app_playback import deliver_latest_frame, on_frame, request_timeline_preview
from framestudio.app_tracks import seek_editing_only
from framestudio.ffmpeg_playback import PlaybackBackendError, VideoFrame
from framestudio.model import SegmentTimeline
from framestudio.playback import PlaybackController, PlaybackState
from framestudio.timeline import create_timeline_canvas
from tests.test_editor_timeline import FakeGtk


class SeekDispatchTests(unittest.TestCase):
    def window(self):
        backend = MagicMock()
        timeline = SimpleNamespace(timing_mode="absolute", timeline_duration_seconds=60.0)
        project = SimpleNamespace(
            segment_timeline=timeline,
            timeline=timeline,
            playhead_seconds=0.0,
            set_playhead=MagicMock(),
        )
        project.set_playhead.side_effect = lambda position: setattr(
            project, "playhead_seconds", position
        )
        return SimpleNamespace(
            backend=backend,
            controller=PlaybackController(backend, 60),
            project=project,
            segment_timeline=timeline,
            timeline_canvas=MagicMock(),
            _update_playback_controls=MagicMock(),
            _show_error=MagicMock(),
            _frame_lock=threading.Lock(),
            _latest_frame=None,
            _latest_frame_generation=None,
            _frame_delivery_scheduled=False,
            _deliver_latest_frame=MagicMock(),
            _playback_generation=1,
            preview=MagicMock(),
            position_label=MagicMock(),
        )

    def test_absolute_seek_dispatches_preview_without_synchronous_seek(self):
        window = self.window()
        self.assertTrue(seek_editing_only(window, 31.6))
        window.backend.seek.assert_not_called()
        window.backend.request_preview.assert_called_once_with(31.6)
        self.assertEqual(window.controller.snapshot().position_seconds, 31.6)
        self.assertEqual(window.controller.snapshot().state, PlaybackState.PAUSED)
        window.project.set_playhead.assert_called_with(31.6)
        window.timeline_canvas.set_playhead.assert_called_with(31.6)

    def test_absolute_seek_preserves_ongoing_playback(self):
        window = self.window()
        window.controller.play()
        self.assertTrue(seek_editing_only(window, 15.7))
        self.assertEqual(window.controller.snapshot().state, PlaybackState.PLAYING)
        window.backend.pause.assert_called_once()
        self.assertEqual(window.backend.play.call_count, 2)
        window.backend.seek.assert_not_called()

    def test_queued_old_frame_and_callback_during_dispatch_cannot_paint(self):
        window = self.window()
        glib, gdk = MagicMock(), MagicMock()
        old = VideoFrame(bytes(4), 1, 1, 7.6, 7.6)
        on_frame(window, old, glib, 1)
        self.assertTrue(window._frame_delivery_scheduled)
        window.backend.request_preview.side_effect = lambda _: on_frame(window, old, glib, 1)
        request_timeline_preview(window, 15.7)
        self.assertFalse(deliver_latest_frame(window, gdk, glib))
        window.preview.set_paintable.assert_not_called()

    def test_synchronous_cache_hit_for_current_target_is_not_discarded(self):
        window = self.window()
        glib, gdk = MagicMock(), MagicMock()
        current = VideoFrame(bytes(4), 1, 1, 15.7, 15.7)
        window.backend.request_preview.side_effect = lambda _: on_frame(window, current, glib, 1)
        request_timeline_preview(window, 15.7)
        self.assertFalse(deliver_latest_frame(window, gdk, glib))
        window.preview.set_paintable.assert_called_once()

    def test_preview_failure_is_returned_and_visible(self):
        window = self.window()
        window.backend.request_preview.side_effect = PlaybackBackendError("decoder unavailable")
        self.assertFalse(seek_editing_only(window, 15.7))
        self.assertEqual(window.controller.snapshot().state, PlaybackState.ERROR)
        window._show_error.assert_called_once_with("decoder unavailable")

    def test_drag_deduplicates_only_within_one_gesture(self):
        positions = []
        canvas = create_timeline_canvas(FakeGtk)(on_seek=positions.append)
        canvas.set_timeline(SegmentTimeline(10))
        for _ in range(2):
            canvas._on_drag_begin(None, 20, 0)
            canvas._on_drag_update(None, 0, 0)
            canvas._on_drag_end(None, 0, 0)
        self.assertEqual(len(positions), 2)
        self.assertEqual(positions[0], positions[1])


if __name__ == "__main__":
    unittest.main()
