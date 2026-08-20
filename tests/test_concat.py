import unittest
from fractions import Fraction
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from resolve_concat import (
    AudioStats,
    Clip,
    audio_gain_db,
    build_normalized_part_command,
    build_normalized_command,
    can_stream_copy,
    common_resolution,
    effective_jobs,
    find_selected_inputs,
    h264_level,
    nominal_rate,
    parse_arguments,
    run_normalization,
)


def clip(name, fps="30000/1001", profile="High", width=1920, height=1080):
    return Clip(
        path=Path(name),
        duration=10.0,
        video={
            "codec_name": "h264",
            "profile": profile,
            "pix_fmt": "yuv420p",
            "width": str(width),
            "height": str(height),
            "r_frame_rate": fps,
            "time_base": "1/30000",
            "codec_tag_string": "avc1",
        },
        audio={
            "codec_name": "aac",
            "sample_rate": "48000",
            "channels": 2,
            "channel_layout": "stereo",
            "time_base": "1/48000",
            "codec_tag_string": "mp4a",
        },
    )


class ConcatTests(unittest.TestCase):
    def test_no_input_argument_opens_tui_mode(self):
        arguments = parse_arguments([])
        self.assertIsNone(arguments.input_dir)

    def test_selected_inputs_are_sorted_and_exclude_output(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            first = root / "b.mp4"
            second = root / "a.mp4"
            output = root / "joined.mp4"
            first.touch()
            second.touch()
            output.touch()
            self.assertEqual(
                find_selected_inputs([first, output, second], output),
                [second, first],
            )

    def test_lowest_frame_rate_is_selected(self):
        clips = [clip("30.mp4", "30/1"), clip("2997.mp4")]
        self.assertEqual(min((nominal_rate(item) for item in clips), key=float), Fraction(30000, 1001))

    def test_most_common_resolution_is_selected(self):
        clips = [clip("one.mp4"), clip("two.mp4"), clip("three.mp4", width=1280, height=720)]
        self.assertEqual(common_resolution(clips), (1920, 1080))

    def test_stream_copy_requires_matching_parameters(self):
        clips = [clip("one.mp4"), clip("two.mp4")]
        self.assertTrue(can_stream_copy(clips, Fraction(30000, 1001), (1920, 1080)))
        self.assertFalse(
            can_stream_copy(
                [clip("one.mp4"), clip("two.mp4", fps="30/1")],
                Fraction(30000, 1001),
                (1920, 1080),
            )
        )
        self.assertFalse(
            can_stream_copy(
                [clip("one.mp4"), clip("two.mp4", profile="Main")],
                Fraction(30000, 1001),
                (1920, 1080),
            )
        )

    def test_stream_copy_rejects_non_universal_video(self):
        non_universal = clip("hevc.mp4")
        non_universal.video["codec_name"] = "hevc"
        self.assertFalse(
            can_stream_copy([non_universal], Fraction(30000, 1001), (1920, 1080))
        )

    def test_audio_gain_balances_targets(self):
        gain = audio_gain_db(
            AudioStats(peak_db=-6.0, mean_rms_db=-34.0, median_db=-54.0)
        )
        self.assertAlmostEqual(gain, 1.5)

    def test_audio_gain_respects_peak_cap(self):
        gain = audio_gain_db(
            AudioStats(peak_db=2.0, mean_rms_db=-40.0, median_db=-60.0)
        )
        self.assertAlmostEqual(gain, -3.0)

    def test_normalized_command_uses_universal_profile(self):
        source = Path("fixture.mp4")
        command = build_normalized_command(
            [clip("fixture.mp4")],
            Path("fixture.partial.mp4"),
            Fraction(30000, 1001),
            (1920, 1080),
            "libx264",
            {source: 1.5},
        )
        self.assertIn("slow", command)
        self.assertIn("20", command)
        self.assertIn("aac_low", command)
        self.assertIn("192k", command)
        self.assertIn("avc1", command)
        self.assertTrue(any("volume=1.50dB" in item for item in command))
        self.assertEqual(h264_level((1920, 1080), Fraction(30000, 1001)), "4.2")

    def test_parallel_worker_count_is_bounded(self):
        self.assertIn(effective_jobs(0, 6), (1, 2, 3))
        self.assertEqual(effective_jobs(2, 6), 2)
        self.assertEqual(effective_jobs(10, 2), 2)

    def test_normalized_part_command_matches_universal_profile(self):
        command = build_normalized_part_command(
            clip("fixture.mp4"),
            Path("part.mp4"),
            Fraction(30000, 1001),
            (1920, 1080),
            "h264_nvenc",
            1.5,
        )
        self.assertIn("h264_nvenc", command)
        self.assertIn("p6", command)
        self.assertIn("aac_low", command)
        self.assertIn("90000", command)
        self.assertIn("-shortest", command)
        self.assertTrue(any("volume=1.50dB" in item for item in command))

    def test_parallel_normalization_cleans_parts_after_success(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            parts_directory = root / "parts"
            parts_directory.mkdir()
            with (
                patch("resolve_concat.tempfile.mkdtemp", return_value=str(parts_directory)),
                patch("resolve_concat.run_parallel_commands"),
                patch("resolve_concat.run_ffmpeg"),
            ):
                run_normalization(
                    [clip("fixture.mp4")],
                    root / "output.mp4",
                    root / "output.partial.mp4",
                    Fraction(30000, 1001),
                    (1920, 1080),
                    "h264_nvenc",
                    {},
                    "parallel",
                    1,
                    10.0,
                    False,
                )
            self.assertFalse(parts_directory.exists())

    def test_parallel_normalization_cleans_parts_after_failure(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            parts_directory = root / "parts"
            parts_directory.mkdir()
            with (
                patch("resolve_concat.tempfile.mkdtemp", return_value=str(parts_directory)),
                patch(
                    "resolve_concat.run_parallel_commands",
                    side_effect=RuntimeError("worker failed"),
                ),
            ):
                with self.assertRaisesRegex(RuntimeError, "worker failed"):
                    run_normalization(
                        [clip("fixture.mp4")],
                        root / "output.mp4",
                        root / "output.partial.mp4",
                        Fraction(30000, 1001),
                        (1920, 1080),
                        "h264_nvenc",
                        {},
                        "parallel",
                        1,
                        10.0,
                        False,
                    )
            self.assertFalse(parts_directory.exists())


if __name__ == "__main__":
    unittest.main()
