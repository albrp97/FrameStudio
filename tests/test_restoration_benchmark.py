import unittest
from fractions import Fraction
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from benchmarks.restoration_benchmark import (
    EXPECTED_CANDIDATE_NAMES,
    _external_candidate_result,
    build_ffmpeg_command,
    choose_windows,
    discover_runtime,
    load_manifest,
    redact_command,
    run_benchmark,
    verify_output,
)


class RestorationBenchmarkContractTests(unittest.TestCase):
    def test_manifest_contains_all_requested_candidates(self):
        manifest = load_manifest(Path("benchmarks/restoration_candidates.json"))
        names = {candidate["name"] for candidate in manifest["candidates"]}

        self.assertTrue(EXPECTED_CANDIDATE_NAMES.issubset(names))
        self.assertEqual(
            manifest["candidate_statuses"],
            [
                "passed",
                "failed",
                "unavailable",
                "excluded-license",
                "not-comparable",
            ],
        )

    def test_manifest_pins_the_documented_video2x_configuration(self):
        manifest = load_manifest(Path("benchmarks/restoration_candidates.json"))
        candidate = next(
            item for item in manifest["candidates"] if item["id"] == "video2x-realesrgan"
        )

        self.assertEqual(candidate["version"], "6.4.0")
        self.assertEqual(candidate["backend"], "ncnn/Vulkan")
        self.assertEqual(candidate["underlying_model"], "realesr-animevideov3")
        self.assertFalse(candidate["underlying_model_required"])
        self.assertEqual(candidate["configuration"]["mode"], "filtering/upscale only")
        self.assertEqual(candidate["configuration"]["scaling_factor"], 4)
        self.assertEqual(candidate["configuration"]["device"], 0)
        self.assertEqual(candidate["configuration"]["hwaccel"], "none")
        self.assertEqual(candidate["configuration"]["codec"], "h264_nvenc")
        self.assertEqual(
            candidate["configuration"]["encoder_options"],
            {"cq": 18, "preset": "p5"},
        )
        self.assertEqual(candidate["configuration"]["max_b_frames"], 0)
        self.assertEqual(
            candidate["runtime_probe"]["executable_paths"],
            ["~/.cache/resolve-fps/benchmark-tools/Video2X-6.4.0-x86_64.AppImage"],
        )

    def test_candidate_result_retains_pinned_runtime_configuration(self):
        manifest = load_manifest(Path("benchmarks/restoration_candidates.json"))
        candidate = next(
            item for item in manifest["candidates"] if item["id"] == "video2x-realesrgan"
        )

        result = _external_candidate_result(candidate)

        self.assertEqual(result["version"], "6.4.0")
        self.assertEqual(result["backend"], "ncnn/Vulkan")
        self.assertEqual(result["underlying_model"], "realesr-animevideov3")
        self.assertEqual(result["configuration"]["codec"], "h264_nvenc")

    def test_runtime_probe_finds_configured_executable_path(self):
        with TemporaryDirectory() as temporary_directory:
            executable = Path(temporary_directory) / "Video2X.AppImage"
            executable.write_text("#!/bin/sh\n", encoding="utf-8")
            executable.chmod(0o700)

            result = discover_runtime(
                {
                    "runtime_probe": {
                        "executables": [],
                        "executable_paths": [str(executable)],
                        "modules": [],
                        "weight_patterns": [],
                    }
                }
            )

        self.assertEqual(result["executable_paths"], ["Video2X.AppImage"])

    def test_fixture_windows_are_deterministic_and_non_overlapping(self):
        first = choose_windows(60.0)
        second = choose_windows(60.0)

        self.assertEqual(first, second)
        self.assertEqual(len(first), 3)
        for previous, current in zip(first, first[1:], strict=False):
            self.assertGreaterEqual(
                current["start_seconds"],
                previous["end_seconds"] + 0.5,
            )

    def test_fixture_windows_support_four_requested_segments(self):
        windows = choose_windows(853.64375, count=4)

        self.assertEqual(len(windows), 4)
        self.assertEqual(
            [window["index"] for window in windows],
            [1.0, 2.0, 3.0, 4.0],
        )
        for previous, current in zip(windows, windows[1:], strict=False):
            self.assertGreaterEqual(
                current["start_seconds"],
                previous["end_seconds"] + 0.5,
            )

    def test_output_command_preserves_native_frame_rate(self):
        command = build_ffmpeg_command(
            "",
            Path("fixture.mp4"),
            Path("output.partial.mp4"),
            ffmpeg="ffmpeg",
            video_encoder="libx264",
        )

        self.assertIn("-fps_mode", command)
        self.assertEqual(command[command.index("-fps_mode") + 1], "passthrough")
        self.assertNotIn("minterpolate", command)
        self.assertNotIn("-r", command)

    def test_warm_runs_require_at_least_one_repeat(self):
        with self.assertRaisesRegex(ValueError, "at least one"):
            run_benchmark(warm_runs=0)

    def test_redacted_command_hides_private_paths(self):
        command = redact_command(
            ["/home/tester/private/source.mp4", "/home/tester/private/output.mp4"],
            {"/home/tester/private": "<PRIVATE>"},
        )

        self.assertEqual(command, ("<PRIVATE>/source.mp4", "<PRIVATE>/output.mp4"))

    def test_output_verification_checks_every_common_contract_field(self):
        fixture = {
            "duration_seconds": 2.0,
            "fps": "30000/1001",
            "frame_count": 60,
            "audio": True,
        }
        metrics = {
            "duration_seconds": 2.0,
            "width": 1920,
            "height": 1080,
            "fps": "30000/1001",
            "frame_count": 60,
            "video_codec": "h264",
            "pixel_format": "yuv420p",
            "audio": True,
            "audio_codec": "aac",
            "audio_sample_rate": 48000,
            "audio_channels": 2,
            "container": "mov,mp4,m4a,3gp,3g2,mj2",
        }

        verification = verify_output(metrics, fixture)

        self.assertTrue(verification["passed"])
        self.assertTrue(all(verification["checks"].values()))

    def test_output_verification_rejects_frame_rate_or_frame_count_changes(self):
        fixture = {
            "duration_seconds": 2.0,
            "fps": str(Fraction(30, 1)),
            "frame_count": 60,
            "audio": False,
        }
        metrics = {
            "duration_seconds": 2.0,
            "width": 1920,
            "height": 1080,
            "fps": "60",
            "frame_count": 120,
            "video_codec": "h264",
            "pixel_format": "yuv420p",
            "audio": False,
            "audio_codec": "",
            "audio_sample_rate": None,
            "audio_channels": None,
            "container": "mov,mp4",
        }

        verification = verify_output(metrics, fixture)

        self.assertFalse(verification["passed"])
        self.assertFalse(verification["checks"]["fps_matches"])
        self.assertFalse(verification["checks"]["frame_count_matches"])

    def test_unavailable_external_candidate_is_retained_with_reason(self):
        candidate = {
            "id": "realesrgan-x4plus",
            "name": "RealESRGAN x4plus",
            "category": "single-frame-model",
            "runner": "external",
            "adapter": "video-frame-adapter-required",
            "license": {"name": "BSD-3-Clause", "status": "verified"},
        }
        with patch(
            "benchmarks.restoration_benchmark.discover_runtime",
            return_value={
                "python": "python3",
                "executables": [],
                "modules": [],
                "weight_count": 0,
                "weight_names": [],
            },
        ):
            result = _external_candidate_result(candidate)

        self.assertEqual(result["status"], "unavailable")
        self.assertTrue(result["reason"])

    def test_unverified_external_candidate_is_license_excluded(self):
        candidate = {
            "id": "nomos2",
            "name": "Nomos2",
            "category": "single-frame-model",
            "runner": "external",
            "adapter": "pinned-checkpoint-adapter-required",
            "license": {"name": "unknown", "status": "unverified"},
        }
        with patch(
            "benchmarks.restoration_benchmark.discover_runtime",
            return_value={
                "python": "python3",
                "executables": ["nomos2"],
                "modules": [],
                "weight_count": 1,
                "weight_names": ["nomos2.pth"],
            },
        ):
            result = _external_candidate_result(candidate)

        self.assertEqual(result["status"], "excluded-license")
        self.assertIn("license", result["reason"])


if __name__ == "__main__":
    unittest.main()
