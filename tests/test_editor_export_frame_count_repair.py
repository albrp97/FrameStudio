"""Functionality tests for exact frame-count enforcement in exports.

These tests reproduce the real-world failure reported by a user: a mixed
enhanced export finishing all rendering stages and then failing verification
with "Mixed export frame count does not match the selected target" because a
passthrough/converted segment's cut landed one frame short of its rounded
target while interpolated segments already enforced their exact target.
"""

import shutil
import subprocess
import unittest
from fractions import Fraction
from pathlib import Path
from tempfile import TemporaryDirectory

from framestudio.export import execute_export, plan_mixed_export
from framestudio.export_process import ensure_exact_video_frame_count, probe_frame_count
from framestudio.fps_policy import FrameRatePolicy
from framestudio.media import probe_media
from framestudio.model import Segment, SegmentTimeline
from framestudio.upscale_policy import UpscalePolicy


@unittest.skipUnless(
    shutil.which("ffmpeg") and shutil.which("ffprobe"),
    "FFmpeg and ffprobe are required",
)
class EnsureExactVideoFrameCountTests(unittest.TestCase):
    def make_clip(
        self,
        root: Path,
        *,
        name: str,
        rate: int = 10,
        duration: float = 1.0,
        with_audio: bool = False,
    ) -> Path:
        clip = root / name
        command = [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "lavfi",
            "-i",
            f"testsrc=size=64x64:rate={rate}",
        ]
        if with_audio:
            command.extend(["-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000"])
        command.extend(["-t", str(duration), "-c:v", "libx264", "-g", "1", "-pix_fmt", "yuv420p"])
        if with_audio:
            command.extend(["-c:a", "aac", "-shortest"])
        command.append(str(clip))
        subprocess.run(command, check=True)
        return clip

    def test_pads_a_clip_that_is_one_frame_short_of_its_target(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            clip = self.make_clip(root, name="short.mp4", rate=10, duration=1.0)
            natural_frames = probe_frame_count(clip)
            target = natural_frames + 1

            result = ensure_exact_video_frame_count(
                clip,
                target,
                frame_rate=Fraction(10, 1),
                video_codec="libx264",
                pixel_format="yuv420p",
                container="mp4",
                has_audio=False,
                audio_codec=None,
                audio_sample_rate=48000,
                audio_channels=2,
                ffmpeg_path="ffmpeg",
                ffprobe_path="ffprobe",
            )

            self.assertEqual(probe_frame_count(clip), target)
            self.assertEqual(result.frame_rate, "10/1")

    def test_trims_a_clip_that_is_one_frame_over_its_target_with_audio(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            clip = self.make_clip(
                root, name="long.mp4", rate=10, duration=1.0, with_audio=True
            )
            natural_frames = probe_frame_count(clip)
            target = natural_frames - 1

            result = ensure_exact_video_frame_count(
                clip,
                target,
                frame_rate=Fraction(10, 1),
                video_codec="libx264",
                pixel_format="yuv420p",
                container="mp4",
                has_audio=True,
                audio_codec="aac",
                audio_sample_rate=48000,
                audio_channels=2,
                ffmpeg_path="ffmpeg",
                ffprobe_path="ffprobe",
            )

            self.assertEqual(probe_frame_count(clip), target)
            self.assertAlmostEqual(result.duration_seconds, target / 10, delta=0.15)
            self.assertTrue(result.audio_codec)

    def test_is_a_no_op_when_the_clip_already_matches_its_target(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            clip = self.make_clip(root, name="exact.mp4", rate=10, duration=1.0)
            before_bytes = clip.read_bytes()
            natural_frames = probe_frame_count(clip)

            ensure_exact_video_frame_count(
                clip,
                natural_frames,
                frame_rate=Fraction(10, 1),
                video_codec="libx264",
                pixel_format="yuv420p",
                container="mp4",
                has_audio=False,
                audio_codec=None,
                audio_sample_rate=48000,
                audio_channels=2,
                ffmpeg_path="ffmpeg",
                ffprobe_path="ffprobe",
            )

            self.assertEqual(clip.read_bytes(), before_bytes)


@unittest.skipUnless(
    shutil.which("ffmpeg") and shutil.which("ffprobe"),
    "FFmpeg and ffprobe are required",
)
class MixedEnhancedExportExactFrameCountTests(unittest.TestCase):
    def make_source(
        self,
        root: Path,
        *,
        name: str,
        rate: int,
        frequency: int,
        duration: float,
    ) -> Path:
        source = root / name
        subprocess.run(
            [
                "ffmpeg",
                "-hide_banner",
                "-loglevel",
                "error",
                "-f",
                "lavfi",
                "-i",
                f"testsrc=size=320x180:rate={rate}",
                "-f",
                "lavfi",
                "-i",
                f"sine=frequency={frequency}:sample_rate=48000",
                "-t",
                str(duration),
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

    def test_mixed_export_with_interpolated_and_passthrough_segments_hits_exact_target(self):
        """Reproduces the reported bug: one segment needs interpolation to
        reach the target rate while a sibling segment is already at the
        target rate (passthrough). Before the fix, the passthrough segment
        could land one frame short of its rounded target while the
        interpolated segment enforced its own exact target, so the final
        assembled output failed verification with a frame-count mismatch.
        """
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            # Needs interpolation up to the 20fps target.
            first_path = self.make_source(
                root, name="first.mp4", rate=10, frequency=440, duration=0.5
            )
            # Already at the 20fps target: passthrough segment.
            second_path = self.make_source(
                root, name="second.mp4", rate=20, frequency=880, duration=0.5
            )
            first = probe_media(first_path)
            second = probe_media(second_path)
            first_id = "first"
            second_id = "second"
            timeline = SegmentTimeline.from_blocks(
                (
                    Segment.create(
                        0.0,
                        0.5,
                        source_id=first_id,
                        timeline_start_seconds=0.0,
                        timeline_end_seconds=0.5,
                    ),
                    Segment.create(
                        0.0,
                        0.5,
                        source_id=second_id,
                        timeline_start_seconds=0.5,
                        timeline_end_seconds=1.0,
                    ),
                ),
                duration_seconds=1.0,
                source_durations={
                    first_id: first.duration_seconds,
                    second_id: second.duration_seconds,
                },
            )
            policy = FrameRatePolicy(
                choice="custom",
                custom_rate="20/1",
                target_rate="20/1",
                enhancement_enabled=True,
                backend="ffmpeg-minterpolate",
            )
            plan = plan_mixed_export(
                (first, second),
                timeline,
                root / "mixed-enhanced.mp4",
                source_ids=(first_id, second_id),
                audio_decisions={
                    first_id: {"status": "ready", "gain_db": 1.0},
                    second_id: {"status": "ready", "gain_db": -1.0},
                },
                frame_rate_policy=policy,
                upscale_policy=UpscalePolicy(enhancement_enabled=False),
            )

            result = execute_export(plan)

            output = probe_media(result)
            self.assertEqual(output.frame_rate, "20/1")
            # The exact assertion that used to fail verification: the total
            # frame count must match the rounded target (20 frames @ 20fps
            # for a 1.0s timeline), regardless of which segments needed
            # interpolation and which were passthrough.
            self.assertEqual(probe_frame_count(result), 20)


if __name__ == "__main__":
    unittest.main()
