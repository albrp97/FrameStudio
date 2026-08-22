import shutil
import subprocess
import threading
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from resolve_editor.ffmpeg_playback import FfmpegPlaybackBackend, VideoFrame
from resolve_editor.model import Segment


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
        from resolve_editor.ffmpeg_playback import FfmpegComposedPlaybackBackend

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


if __name__ == "__main__":
    unittest.main()
