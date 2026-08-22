import shutil
import subprocess
import threading
import time
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from resolve_editor.ffmpeg_playback import (
    FfmpegComposedPlaybackBackend,
    FfmpegPlaybackBackend,
    VideoFrame,
)
from resolve_editor.model import Segment
from resolve_editor.playback import PlaybackBackendError


@unittest.skipUnless(shutil.which("ffmpeg"), "ffmpeg is required")
class FfmpegPlaybackTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        self.source = self.root / "source.mp4"
        subprocess.run(
            [
                "ffmpeg",
                "-hide_banner",
                "-loglevel",
                "error",
                "-f",
                "lavfi",
                "-i",
                "testsrc=size=16x16:rate=10",
                "-t",
                "0.5",
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                str(self.source),
            ],
            check=True,
        )

    def tearDown(self):
        self.temporary_directory.cleanup()

    def test_seek_presents_a_frame_and_playback_emits_frames(self):
        frames = []
        ended = threading.Event()
        errors = []
        backend = FfmpegPlaybackBackend(
            self.source,
            16,
            16,
            10.0,
            0.5,
            frames.append,
            errors.append,
            ended.set,
        )

        backend.seek(0.2)
        self.assertEqual(len(frames), 1)
        self.assertEqual(len(frames[0].data), 16 * 16 * 4)
        self.assertAlmostEqual(backend.current_position(), 0.2)

        backend.play()
        self.assertTrue(ended.wait(timeout=3))
        backend.stop()

        self.assertGreater(len(frames), 1)
        self.assertEqual(errors, [])

    def test_playback_delivers_frames_at_real_time_after_seek(self):
        frames = []
        ended = threading.Event()
        backend = FfmpegPlaybackBackend(
            self.source,
            16,
            16,
            10.0,
            0.5,
            lambda frame: frames.append((time.monotonic(), frame.position_seconds)),
            lambda _message: None,
            ended.set,
        )

        try:
            backend.seek(0.2)
            frames.clear()
            backend.play()

            deadline = time.monotonic() + 3
            while len(frames) < 3 and time.monotonic() < deadline:
                time.sleep(0.01)

            self.assertGreaterEqual(len(frames), 3)
            self.assertGreaterEqual(frames[1][0] - frames[0][0], 0.05)
            self.assertGreaterEqual(frames[2][0] - frames[1][0], 0.05)
        finally:
            backend.close()

    def test_pause_and_resume_hold_and_restart_frame_delivery(self):
        frames = []
        backend = FfmpegPlaybackBackend(
            self.source,
            16,
            16,
            10.0,
            0.5,
            lambda frame: frames.append(frame),
            lambda _message: None,
            lambda: None,
        )

        try:
            backend.play()
            deadline = time.monotonic() + 3
            while len(frames) < 3 and time.monotonic() < deadline:
                time.sleep(0.01)

            self.assertGreaterEqual(len(frames), 3)
            backend.pause()
            paused_count = len(frames)
            paused_position = backend.current_position()
            time.sleep(0.15)

            self.assertEqual(len(frames), paused_count)
            self.assertAlmostEqual(backend.current_position(), paused_position)

            backend.play()
            deadline = time.monotonic() + 3
            while len(frames) <= paused_count and time.monotonic() < deadline:
                time.sleep(0.01)

            self.assertGreater(len(frames), paused_count)
        finally:
            backend.close()

    def test_seek_scales_and_letterboxes_into_requested_canvas(self):
        frames = []
        backend = FfmpegPlaybackBackend(
            self.source,
            32,
            16,
            10.0,
            0.5,
            frames.append,
            lambda _message: None,
            lambda: None,
        )

        try:
            backend.seek(0.2)
            self.assertEqual(len(frames), 1)
            self.assertEqual((frames[0].width, frames[0].height), (32, 16))
            self.assertEqual(len(frames[0].data), 32 * 16 * 4)
        finally:
            backend.close()

    def test_preview_requests_only_deliver_the_latest_position(self):
        class PreviewBackend(FfmpegPlaybackBackend):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.first_started = threading.Event()
                self.release_first = threading.Event()

            def _decode_preview_frame(self, position_seconds):
                if position_seconds == 0.1:
                    self.first_started.set()
                    self.release_first.wait(timeout=3)
                return VideoFrame(
                    b"\0" * self.frame_size,
                    self.width,
                    self.height,
                    position_seconds,
                )

        frames = []
        backend = PreviewBackend(
            self.source,
            16,
            16,
            10.0,
            0.5,
            frames.append,
            lambda _message: None,
            lambda: None,
        )

        try:
            backend.request_preview(0.1)
            self.assertTrue(backend.first_started.wait(timeout=3))
            backend.request_preview(0.4)
            backend.release_first.set()

            deadline = threading.Event()
            for _ in range(30):
                if frames:
                    break
                deadline.wait(0.1)

            self.assertEqual([frame.position_seconds for frame in frames], [0.4])
        finally:
            backend.close()

    def test_request_preview_delivers_a_real_frame_asynchronously(self):
        frames = []
        frame_ready = threading.Event()

        def on_frame(frame):
            frames.append(frame)
            frame_ready.set()

        backend = FfmpegPlaybackBackend(
            self.source,
            16,
            16,
            10.0,
            0.5,
            on_frame,
            lambda _message: None,
            lambda: None,
        )

        try:
            backend.request_preview(0.2)

            self.assertTrue(frame_ready.wait(timeout=3))
            self.assertEqual(len(frames[0].data), 16 * 16 * 4)
            self.assertAlmostEqual(frames[0].position_seconds, 0.2)
        finally:
            backend.close()

    def test_composed_backend_accepts_one_source_blocks_without_source_ids(self):
        backend = FfmpegComposedPlaybackBackend(
            (("source", self.source),),
            (Segment.create(0.0, 0.5),),
            16,
            16,
            10.0,
            0.5,
            lambda _frame: None,
            lambda _message: None,
            lambda: None,
        )

        try:
            command = backend._command(0.0, realtime=False, frame_count=1)
        finally:
            backend.close()

        self.assertIn("[0:v:0]trim=start=0.000000:duration=0.500000", " ".join(command))

    def test_composed_audio_command_reuses_decisions_by_source(self):
        first = self.root / "first.mp4"
        second = self.root / "second.mp4"
        first.write_bytes(b"fixture")
        second.write_bytes(b"fixture")
        backend = FfmpegComposedPlaybackBackend(
            (("first", first), ("second", second)),
            (
                Segment.create(
                    0.0,
                    0.5,
                    source_id="first",
                    timeline_start_seconds=0.0,
                    timeline_end_seconds=0.5,
                ),
                Segment.create(
                    0.0,
                    0.5,
                    source_id="second",
                    timeline_start_seconds=0.5,
                    timeline_end_seconds=1.0,
                ),
            ),
            16,
            16,
            10.0,
            1.0,
            lambda _frame: None,
            lambda _message: None,
            lambda: None,
            audio_decisions={
                "first": {"status": "ready", "gain_db": 2.0},
                "second": {"status": "ready", "gain_db": -3.0},
            },
        )

        try:
            command = backend._audio_command(0.25, realtime=False)
        finally:
            backend.close()

        rendered = " ".join(command)
        self.assertIn("[0:a:0]atrim=start=0.000000:duration=0.500000", rendered)
        self.assertIn("volume=2.00dB", rendered)
        self.assertIn("[1:a:0]atrim=start=0.000000:duration=0.500000", rendered)
        self.assertIn("volume=-3.00dB", rendered)
        self.assertLess(rendered.index("-ss 0.250000"), rendered.index("-f s16le"))

    def test_audio_preview_is_disabled_for_sources_without_audio(self):
        backend = FfmpegPlaybackBackend(
            self.source,
            16,
            16,
            10.0,
            0.5,
            lambda _frame: None,
            lambda _message: None,
            lambda: None,
            audio_decision={"status": "not-applicable", "gain_db": 0.0},
        )

        try:
            self.assertFalse(backend._has_audio_preview())
        finally:
            backend.close()

    def test_audio_preview_requires_ffplay_when_audio_is_enabled(self):
        backend = FfmpegPlaybackBackend(
            self.source,
            16,
            16,
            10.0,
            0.5,
            lambda _frame: None,
            lambda _message: None,
            lambda: None,
            audio_decision={"status": "ready", "gain_db": 0.0},
        )

        try:
            with patch("resolve_editor.ffmpeg_playback.shutil.which", return_value=None):
                with self.assertRaisesRegex(PlaybackBackendError, "ffplay is required"):
                    backend._start_audio_preview_locked(0.0)
        finally:
            backend.close()


if __name__ == "__main__":
    unittest.main()
