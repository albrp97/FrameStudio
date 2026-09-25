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

from framestudio.export_process import ensure_exact_video_frame_count, probe_frame_count


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

    def ensure_frame_count(self, clip: Path, target: int, *, has_audio: bool = False):
        return ensure_exact_video_frame_count(
            clip,
            target,
            frame_rate=Fraction(10, 1),
            video_codec="libx264",
            pixel_format="yuv420p",
            container="mp4",
            has_audio=has_audio,
            audio_codec="aac" if has_audio else None,
            audio_sample_rate=48000,
            audio_channels=2,
            ffmpeg_path="ffmpeg",
            ffprobe_path="ffprobe",
        )

    def test_pads_a_clip_that_is_one_frame_short_of_its_target(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            clip = self.make_clip(root, name="short.mp4", rate=10, duration=1.0)
            natural_frames = probe_frame_count(clip)
            target = natural_frames + 1

            result = self.ensure_frame_count(clip, target)

            self.assertEqual(probe_frame_count(clip), target)
            self.assertEqual(result.frame_rate, "10/1")

    def test_trims_a_clip_that_is_one_frame_over_its_target_with_audio(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            clip = self.make_clip(root, name="long.mp4", rate=10, duration=1.0, with_audio=True)
            natural_frames = probe_frame_count(clip)
            target = natural_frames - 1

            result = self.ensure_frame_count(clip, target, has_audio=True)

            self.assertEqual(probe_frame_count(clip), target)
            self.assertAlmostEqual(result.duration_seconds, target / 10, delta=0.15)
            self.assertTrue(result.audio_codec)

    def test_is_a_no_op_when_the_clip_already_matches_its_target(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            clip = self.make_clip(root, name="exact.mp4", rate=10, duration=1.0)
            before_bytes = clip.read_bytes()
            natural_frames = probe_frame_count(clip)

            self.ensure_frame_count(clip, natural_frames)

            self.assertEqual(clip.read_bytes(), before_bytes)


if __name__ == "__main__":
    unittest.main()
