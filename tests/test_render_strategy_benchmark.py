import json
import unittest
from fractions import Fraction
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

from benchmarks.render_strategy_benchmark import (
    SourceSpec,
    StageResult,
    _concat_command,
    _prepare_command,
    _probe,
    _write_concat_list,
    build_comparison_report,
    cleanup_workdir,
    expected_frame_count,
    report_path,
    summarize_benchmark_gates,
    verify_output_integrity,
)


class RenderStrategyBenchmarkCalculationsTests(unittest.TestCase):
    def test_expected_frame_count_rounds_rational_duration_consistently(self):
        self.assertEqual(expected_frame_count(1.25, Fraction(20, 1)), 25)
        self.assertEqual(expected_frame_count(1.001, Fraction(60000, 1001)), 60)

    def test_report_contains_matched_protocol_and_separate_observations(self):
        sources = (
            SourceSpec("source_a", "landscape", 10, 1.0, 320, 180, True),
            SourceSpec("source_b", "landscape", 20, 1.0, 320, 180, True),
        )
        stage = StageResult(
            name="fixture",
            status="passed",
            wall_seconds=0.25,
            output_bytes=100,
        )
        report = build_comparison_report(
            sources=sources,
            target_rate=Fraction(20, 1),
            backend="ffmpeg-minterpolate",
            strategy_results={
                "A": {"status": "passed", "stages": [stage], "subjective_quality_notes": ""},
                "B": {"status": "blocked", "stages": [], "subjective_quality_notes": "not run"},
            },
            environment={"ffmpeg": "available", "ffprobe": "available"},
        )

        self.assertEqual(report["schema_version"], 1)
        self.assertEqual(report["protocol"]["target_fps"], "20/1")
        self.assertEqual(report["protocol"]["source_ids"], ["source_a", "source_b"])
        self.assertEqual(report["strategies"]["A"]["stages"][0]["wall_seconds"], 0.25)
        self.assertIn("subjective_quality_notes", report["strategies"]["A"])
        self.assertEqual(report["strategies"]["B"]["status"], "blocked")

    def test_report_contains_bounded_recommendation_and_quality_limits(self):
        report = build_comparison_report(
            sources=(
                SourceSpec("a", "landscape", 24, 40.0, 1920, 1080, True),
                SourceSpec("b", "landscape", 30, 40.0, 854, 480, True),
                SourceSpec("c", "portrait", 30, 40.0, 720, 1280, True),
            ),
            target_rate=Fraction(60, 1),
            backend="ffmpeg-minterpolate",
            strategy_results={
                "production_per_source_rve": {
                    "status": "passed",
                    "total_wall_seconds": 547.576,
                    "final_bytes": 46705617,
                },
                "concat_first_control": {
                    "status": "passed",
                    "total_wall_seconds": 7.7071,
                    "final_bytes": 43561775,
                },
            },
            environment={},
        )

        recommendation = report["comparison"]["recommendation"]
        self.assertEqual(
            recommendation["selected_strategy"],
            "production_per_source_rve",
        )
        self.assertIn("not quality-equivalent", recommendation["control_quality_limitation"])
        self.assertEqual(
            recommendation["controls"]["concat_first_control"]["total_wall_seconds"],
            7.7071,
        )

    def test_default_render_protocol_declares_1080p_60fps_output(self):
        sources = (
            SourceSpec("source_a", "landscape", 10, 1.2, 1920, 1080, True),
            SourceSpec("source_b", "landscape", 15, 1.2, 1920, 1080, True),
        )
        report = build_comparison_report(
            sources=sources,
            target_rate=Fraction(60, 1),
            backend="ffmpeg-minterpolate",
            strategy_results={"A": {"status": "passed"}, "B": {"status": "passed"}},
            environment={},
        )

        self.assertEqual(report["protocol"]["target_fps"], "60/1")
        self.assertEqual(report["protocol"]["output_profile"]["dimensions"], "1920x1080")

    def test_ticket_080_protocol_declares_retained_ranges_and_triplicate(self):
        sources = (
            SourceSpec("landscape_1080p24", "landscape", 24, 40.0, 1920, 1080, True),
            SourceSpec("landscape_480p30", "landscape", 30, 40.0, 854, 480, True),
            SourceSpec("portrait_720x1280_30", "portrait", 30, 40.0, 720, 1280, True),
        )
        report = build_comparison_report(
            sources=sources,
            target_rate=Fraction(60, 1),
            backend="ffmpeg-minterpolate",
            strategy_results={},
            environment={},
        )

        self.assertEqual(
            report["protocol"]["retained_ranges_seconds"]["portrait_720x1280_30"],
            {"start": 10.0, "duration": 10.0},
        )
        self.assertEqual(
            report["protocol"]["portrait_triplicate"]["layout"],
            "three equal side-by-side slots",
        )
        self.assertIn(
            "3x integer RVE oversampling",
            report["protocol"]["native_rve_24_to_60"],
        )

    def test_output_integrity_supports_explicit_thirty_second_edit(self):
        sources = (
            SourceSpec("a", "landscape", 24, 40.0, 1920, 1080, True),
            SourceSpec("b", "landscape", 30, 40.0, 854, 480, True),
            SourceSpec("c", "portrait", 30, 40.0, 720, 1280, True),
        )
        metrics = {
            "duration_seconds": 30.0,
            "width": 1920,
            "height": 1080,
            "fps": "60",
            "frames": 1800,
            "audio": True,
            "audio_codec": "aac",
            "audio_sample_rate": 48000,
            "audio_channels": 2,
            "video_codec": "h264",
            "pixel_format": "yuv420p",
            "container": "mov,mp4,m4a,3gp,3g2,mj2",
        }

        verification = verify_output_integrity(
            metrics,
            sources,
            Fraction(60, 1),
            expected_duration=30.0,
        )

        self.assertTrue(verification["passed"])
        self.assertEqual(verification["expected_frames"], 1800)

    def test_default_prepare_command_uses_1080p_canvas(self):
        command = _prepare_command(
            Path("source.mp4"),
            Path("prepared.mp4"),
            fps=10,
            ffmpeg="ffmpeg",
        )

        self.assertIn(
            "fps=10,scale=1920:1080:force_original_aspect_ratio=decrease,"
            "pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1",
            command,
        )

    def test_main_defaults_to_60fps_target(self):
        from benchmarks.render_strategy_benchmark import main

        failed_report = {
            "status": "failed",
            "strategies": {"A": {"status": "failed"}, "B": {"status": "failed"}},
            "environment": {"cleanup": {"passed": True}},
        }
        with (
            patch(
                "benchmarks.render_strategy_benchmark.run_benchmark",
                return_value=failed_report,
            ) as run_benchmark,
            patch("benchmarks.render_strategy_benchmark._write_markdown"),
            patch("sys.argv", ["render_strategy_benchmark"]),
        ):
            self.assertNotEqual(main(), 0)

        self.assertEqual(run_benchmark.call_args.kwargs["target_rate"], Fraction(60, 1))

    def test_report_path_redacts_absolute_paths(self):
        self.assertEqual(report_path(Path("/home/user/private/report.json")), "report.json")

    def test_output_integrity_gate_checks_all_protocol_metadata(self):
        sources = (
            SourceSpec("source_a", "landscape", 10, 1.0, 320, 180, True),
            SourceSpec("source_b", "landscape", 20, 1.0, 320, 180, True),
        )
        expected = {
            "duration_seconds": 2.0,
            "width": 320,
            "height": 180,
            "fps": "20",
            "frames": 40,
            "audio": True,
            "audio_sample_rate": 48000,
            "audio_channels": 2,
            "video_codec": "h264",
            "pixel_format": "yuv420p",
            "audio_codec": "aac",
            "container": "mov,mp4,m4a,3gp,3g2,mj2",
        }

        for field, value in (
            ("duration_seconds", 1.0),
            ("width", 640),
            ("height", 360),
            ("audio", False),
            ("audio_sample_rate", 44100),
            ("audio_channels", 1),
            ("video_codec", "mpeg4"),
            ("pixel_format", "yuv444p"),
            ("audio_codec", "opus"),
            ("container", "matroska,webm"),
        ):
            metrics = {**expected, field: value}
            verification = verify_output_integrity(metrics, sources, Fraction(20, 1))
            self.assertFalse(verification["passed"], field)
            self.assertFalse(verification[f"{field}_matches"], field)

    def test_cleanup_failure_is_reported_as_a_failed_gate(self):
        with patch(
            "benchmarks.render_strategy_benchmark.shutil.rmtree",
            side_effect=OSError("permission denied"),
        ):
            cleanup = cleanup_workdir(Path("/tmp/benchmark-work"), requested=True)

        self.assertFalse(cleanup["passed"])
        self.assertFalse(cleanup["workdir_removed"])
        self.assertEqual(cleanup["error"], "OSError")

    def test_global_benchmark_status_fails_on_source_or_cleanup_gate(self):
        strategies = {"A": {"status": "passed"}, "B": {"status": "passed"}}

        status = summarize_benchmark_gates(
            strategies,
            source_preservation={"passed": False},
            cleanup={"passed": True},
        )

        self.assertEqual(status["status"], "failed")
        self.assertFalse(status["source_preservation_passed"])
        self.assertTrue(status["cleanup_passed"])

    def test_benchmark_command_exits_nonzero_when_report_fails(self):
        from benchmarks.render_strategy_benchmark import main

        failed_report = {
            "status": "failed",
            "strategies": {"A": {"status": "failed"}, "B": {"status": "passed"}},
            "environment": {"cleanup": {"passed": True}},
        }
        with (
            patch(
                "benchmarks.render_strategy_benchmark.run_benchmark",
                return_value=failed_report,
            ),
            patch("benchmarks.render_strategy_benchmark._write_markdown"),
            patch(
                "sys.argv",
                ["render_strategy_benchmark", "--report", "/tmp/failed-report.json"],
            ),
        ):
            self.assertNotEqual(main(), 0)

    def test_missing_benchmark_tools_return_structured_failure(self):
        from benchmarks.render_strategy_benchmark import main

        with (
            patch(
                "benchmarks.render_strategy_benchmark._tool",
                return_value=None,
            ),
            patch("benchmarks.render_strategy_benchmark._write_markdown"),
            patch(
                "sys.argv",
                ["render_strategy_benchmark", "--report", "/tmp/blocked-report.json"],
            ),
        ):
            self.assertNotEqual(main(), 0)

    def test_malformed_ffprobe_output_becomes_a_controlled_probe_failure(self):
        malformed_outputs = (
            {
                "streams": [{"codec_type": "audio"}],
                "format": {"duration": "1.0"},
            },
            {
                "streams": [
                    {
                        "codec_type": "video",
                        "avg_frame_rate": "0/0",
                        "nb_frames": "1",
                        "width": 320,
                        "height": 180,
                    },
                ],
                "format": {"duration": "1.0"},
            },
        )

        for payload in malformed_outputs:
            with patch(
                "benchmarks.render_strategy_benchmark.subprocess.run",
                return_value=SimpleNamespace(
                    returncode=0,
                    stdout=json.dumps(payload),
                    stderr="",
                ),
            ):
                with self.assertRaises(ValueError):
                    _probe(Path("/tmp/malformed-output.mp4"), "ffprobe")

    def test_benchmark_rejects_non_positive_target_fps(self):
        from benchmarks.render_strategy_benchmark import main

        with (
            patch(
                "benchmarks.render_strategy_benchmark.run_benchmark",
            ) as run_benchmark,
            patch(
                "sys.argv",
                ["render_strategy_benchmark", "--target-fps", "0"],
            ),
        ):
            with self.assertRaises(SystemExit) as raised:
                main()

        self.assertEqual(raised.exception.code, 2)
        run_benchmark.assert_not_called()

    def test_concat_command_uses_inference_compatible_stream_copy(self):
        command = _concat_command(
            (Path("first.mp4"), Path("second.mp4")),
            Path("concat-list.txt"),
            Path("output.mp4"),
            "ffmpeg",
            target_rate=Fraction(30, 1),
            target_frames=72,
        )

        self.assertEqual(command[command.index("-f") + 1], "concat")
        self.assertEqual(command[command.index("-c") + 1], "copy")
        self.assertNotIn("-filter_complex", command)
        self.assertNotIn("ultrafast", command)
        self.assertNotIn("-crf", command)

    def test_concat_list_writes_all_inputs_for_stream_copy(self):
        with TemporaryDirectory() as temporary_directory:
            list_path = Path(temporary_directory) / "concat-list.txt"
            _write_concat_list(
                (Path("/tmp/first clip.mp4"), Path("/tmp/second.mp4")),
                list_path,
            )

            self.assertEqual(
                list_path.read_text(encoding="utf-8"),
                "file '/tmp/first clip.mp4'\nfile '/tmp/second.mp4'\n",
            )


if __name__ == "__main__":
    unittest.main()
