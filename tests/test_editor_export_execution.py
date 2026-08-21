import shutil
import subprocess
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from resolve_editor.export import (
    ExportExecutionError,
    execute_export,
    plan_export,
)
from resolve_editor.media import probe_media
from resolve_editor.model import SegmentTimeline


@unittest.skipUnless(
    shutil.which("ffmpeg") and shutil.which("ffprobe"),
    "FFmpeg and ffprobe are required",
)
class EditorExportExecutionTests(unittest.TestCase):
    def make_source(self, root: Path) -> Path:
        source = root / "source.mp4"
        subprocess.run(
            [
                "ffmpeg",
                "-hide_banner",
                "-loglevel",
                "error",
                "-f",
                "lavfi",
                "-i",
                "testsrc=size=64x64:rate=10",
                "-f",
                "lavfi",
                "-i",
                "sine=frequency=880:sample_rate=48000",
                "-t",
                "1",
                "-c:v",
                "libx264",
                "-g",
                "5",
                "-pix_fmt",
                "yuv420p",
                "-c:a",
                "aac",
                "-shortest",
                str(source),
            ],
            check=True,
        )
        return source

    def test_fallback_export_is_verified_and_preserves_source(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = self.make_source(root)
            source_before = source.read_bytes()
            probe = probe_media(source)
            timeline = SegmentTimeline(probe.duration_seconds)
            timeline.split(0.5)
            timeline.delete_segment(timeline.segments[1].segment_id)
            destination = root / "edited.mp4"
            plan = plan_export(
                probe,
                timeline,
                destination,
                keyframe_timestamps=(),
            )
            progress = []

            result = execute_export(
                plan,
                progress_callback=progress.append,
            )

            self.assertEqual(result, destination)
            self.assertTrue(destination.is_file())
            self.assertEqual(source.read_bytes(), source_before)
            output = probe_media(destination)
            self.assertAlmostEqual(output.duration_seconds, 0.5, delta=0.15)
            self.assertEqual(output.width, probe.width)
            self.assertEqual(output.height, probe.height)
            self.assertIsNotNone(output.audio_codec)
            self.assertEqual(progress[-1].stage, "complete")
            self.assertTrue(any(item.fps is not None for item in progress))

    def test_stream_copy_export_is_verified(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = self.make_source(root)
            probe = probe_media(source)
            timeline = SegmentTimeline(probe.duration_seconds)
            destination = root / "copied.mp4"
            plan = plan_export(
                probe,
                timeline,
                destination,
                keyframe_timestamps=(),
            )

            self.assertEqual(plan.route, "stream-copy")
            result = execute_export(plan)

            self.assertEqual(result, destination)
            output = probe_media(destination)
            self.assertAlmostEqual(
                output.duration_seconds,
                probe.duration_seconds,
                delta=0.15,
            )

    def test_export_reports_progress_metrics(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = self.make_source(root)
            probe = probe_media(source)
            timeline = SegmentTimeline(probe.duration_seconds)
            destination = root / "progress.mp4"
            plan = plan_export(
                probe,
                timeline,
                destination,
                keyframe_timestamps=(),
            )
            progress = []

            execute_export(plan, progress_callback=progress.append)

            self.assertTrue(progress)
            self.assertEqual(progress[0].stage, "starting")
            self.assertEqual(progress[-1].stage, "complete")
            self.assertEqual(progress[-1].percent, 100.0)
            self.assertGreater(progress[-1].total_frames, 0)
            self.assertTrue(any(item.fps is not None for item in progress))
            self.assertTrue(any(item.stage == "verifying" for item in progress))

    def test_failed_export_keeps_existing_destination_and_cleans_partial(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = self.make_source(root)
            probe = probe_media(source)
            timeline = SegmentTimeline(probe.duration_seconds)
            timeline.split(0.5)
            destination = root / "edited.mp4"
            destination.write_bytes(b"last valid output")
            plan = plan_export(
                probe,
                timeline,
                destination,
                keyframe_timestamps=(),
            )

            with self.assertRaises(ExportExecutionError):
                execute_export(plan, ffmpeg_path="/missing/ffmpeg")

            self.assertEqual(
                destination.read_bytes(),
                b"last valid output",
            )
            self.assertEqual(
                list(root.glob(".edited.mp4.partial-*")),
                [],
            )


if __name__ == "__main__":
    unittest.main()
