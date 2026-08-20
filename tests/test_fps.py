import unittest
from fractions import Fraction
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from resolve_fps import (
    build_encode_command,
    build_rve_custom_encoder,
    default_output,
    parse_arguments,
    progress_line,
    rve_base_frame_count,
    rve_interpolation_factor,
    run_pipeline,
    target_frame_count,
)


class FpsTests(unittest.TestCase):
    def test_target_frame_count_preserves_rational_duration(self):
        self.assertEqual(
            target_frame_count(
                Fraction(30000, 1001),
                900,
                Fraction(60, 1),
            ),
            1802,
        )

    def test_single_input_output_name(self):
        output = default_output(
            [Path("/tmp/source.mp4")],
            Path("/tmp"),
            "4.26",
            Fraction(60, 1),
        )
        self.assertEqual(output, Path("/tmp/source-rife4.26-60fps.mp4"))

    def test_encode_command_copies_audio(self):
        command = build_encode_command(
            Path("source.mp4"),
            Path("output.partial.mp4"),
            "h264_nvenc",
        )
        self.assertIn("-c:a", command)
        self.assertEqual(command[command.index("-c:a") + 1], "copy")
        self.assertEqual(command[command.index("-qp") + 1], "18")

    def test_rve_is_the_default_engine(self):
        self.assertEqual(parse_arguments([]).engine, "rve")

    def test_rve_uses_factor_two_and_pads_duration_preserving_output(self):
        source_rate = Fraction(30000, 1001)
        target_rate = Fraction(60, 1)
        self.assertEqual(rve_interpolation_factor(source_rate, target_rate), 2)
        self.assertEqual(
            rve_base_frame_count(source_rate, 900, target_rate),
            1800,
        )
        command = build_rve_custom_encoder(1802, 1800)
        self.assertIn("tpad=stop_mode=clone:stop=2", command)
        self.assertIn("-frames:v 1802", command)

    def test_progress_line_contains_pacman_metrics(self):
        line = progress_line(50, 100, 0.0, now=10.0)
        self.assertIn("50.00%", line)
        self.assertIn("frame 50/100", line)
        self.assertIn("elapsed 00:00:10", line)
        self.assertIn("ETA 00:00:10", line)
        self.assertIn("C", line)

    def test_single_input_skips_concat(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = root / "source.mp4"
            output = root / "output.mp4"
            source.touch()
            arguments = parse_arguments(
                [str(source), "--output", str(output), "--engine", "vs-rife"]
            )
            with (
                patch(
                    "resolve_fps.probe_video",
                    return_value=(Fraction(30000, 1001), 900),
                ),
                patch("resolve_fps.concatenate") as concatenate,
                patch("resolve_fps.run_interpolation") as run_interpolation,
            ):
                run_pipeline([source], root, arguments)
            concatenate.assert_not_called()
            run_interpolation.assert_called_once()


if __name__ == "__main__":
    unittest.main()
