import threading
import unittest
from fractions import Fraction
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

from framestudio.export_types import ExportExecutionError
from framestudio.interpolation import (
    BackendValidation,
    build_ffmpeg_interpolation_command,
    run_source_interpolation,
    validate_interpolation_backend,
)
from framestudio.interpolation_artifacts import check_artifact_samples


class EditorInterpolationTests(unittest.TestCase):
    def test_artifact_gate_rejects_periodic_grid_samples(self):
        width = 64
        height = 36
        frame = bytes(
            channel
            for row in range(height)
            for column in range(width)
            for channel in ((255 if (row + column) % 2 else 0),) * 3
        )

        result = check_artifact_samples(
            (frame, frame),
            (b"encoded-frame-1", b"encoded-frame-2"),
            width=width,
            height=height,
        )

        self.assertEqual(result.status, "rejected")
        self.assertIn("periodic grid", result.reason)

    def test_ffmpeg_fallback_command_has_explicit_target_rate_and_frame_limit(self):
        command = build_ffmpeg_interpolation_command(
            Path("source.mp4"),
            Path("target.mp4"),
            Fraction(60, 1),
            1802,
            ffmpeg_path="ffmpeg",
        )

        self.assertIn("-frames:v", command)
        self.assertIn("1802", command)
        self.assertTrue(any("minterpolate=fps=60" in item for item in command))
        self.assertEqual(command[-1], "target.mp4")

    def test_ffmpeg_fallback_preserves_exact_rational_target_rate(self):
        command = build_ffmpeg_interpolation_command(
            Path("source.mp4"),
            Path("target.mp4"),
            Fraction(60000, 1001),
            1802,
        )

        filter_arguments = [
            value
            for index, value in enumerate(command)
            if index > 0 and command[index - 1] in {"-vf", "-filter_complex"}
        ]
        self.assertTrue(filter_arguments)
        self.assertTrue(any("fps=60000/1001" in value for value in filter_arguments))
        self.assertTrue(any("N/(60000/1001)/TB" in value for value in filter_arguments))

    def test_missing_rve_artifacts_are_blocked_before_processing(self):
        with TemporaryDirectory() as temporary_directory:
            result = validate_interpolation_backend(
                "rve-4.26",
                source_rate=Fraction(30000, 1001),
                target_rate=Fraction(60, 1),
                rve_root=Path(temporary_directory) / "missing-rve",
                rve_model=Path(temporary_directory) / "missing-model.pkl",
                fps_python=Path(temporary_directory) / "missing-python",
            )

        self.assertIsInstance(result, BackendValidation)
        self.assertFalse(result.available)
        self.assertEqual(result.artifact_status, "blocked")
        self.assertIn("RVE", result.reason)

    def test_rve_runtime_preflight_failure_blocks_editor_backend(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            fps_python = root / "python"
            site_packages = root / "site-packages"
            rve_model = root / "rife4.26.pkl"
            rve_root = root / "rve"
            fps_python.touch()
            site_packages.mkdir()
            rve_model.touch()
            rve_root.mkdir()
            with (
                patch("framestudio_fps.validate_rve_checkout"),
                patch(
                    "framestudio_fps.rve_unavailable_reason",
                    return_value="RVE CUDA/TensorRT preflight failed",
                ),
            ):
                result = validate_interpolation_backend(
                    "rve-4.26",
                    source_rate=Fraction(30, 1),
                    target_rate=Fraction(60, 1),
                    fps_python=fps_python,
                    site_packages=site_packages,
                    rve_model=rve_model,
                    rve_root=rve_root,
                )

        self.assertFalse(result.available)
        self.assertEqual(result.artifact_status, "blocked")
        self.assertIn("CUDA/TensorRT", result.reason)

    def test_explicit_ffmpeg_profile_is_available_without_rve_artifacts(self):
        result = validate_interpolation_backend(
            "ffmpeg-minterpolate",
            source_rate=Fraction(30, 1),
            target_rate=Fraction(60, 1),
        )

        self.assertTrue(result.available)
        self.assertEqual(result.artifact_status, "validated-fallback")

    def test_ffmpeg_profile_validates_the_requested_executable(self):
        with patch(
            "framestudio.interpolation.shutil.which",
            side_effect=lambda value: "/custom/ffmpeg" if value == "/custom/ffmpeg" else None,
        ):
            result = validate_interpolation_backend(
                "ffmpeg-minterpolate",
                source_rate=Fraction(30, 1),
                target_rate=Fraction(60, 1),
                ffmpeg_path="/custom/ffmpeg",
            )

        self.assertTrue(result.available)
        self.assertEqual(result.artifact_status, "validated-fallback")

    def test_ffmpeg_interpolation_forwards_progress_callback(self):
        def progress_callback(_progress):
            return None

        with (
            patch(
                "framestudio.interpolation.require_validated_backend",
                return_value=BackendValidation(
                    backend="ffmpeg-minterpolate",
                    available=True,
                    artifact_status="validated-fallback",
                    reason="test backend",
                    runtime="FFmpeg",
                    input_format="native decoded frames",
                    target_rate=Fraction(20, 1),
                ),
            ),
            patch("framestudio.export_process.run_ffmpeg") as run_ffmpeg,
        ):
            run_source_interpolation(
                Path("source.mp4"),
                Path("target.mp4"),
                source_rate=Fraction(10, 1),
                source_frames=10,
                target_rate=Fraction(20, 1),
                target_frames=20,
                backend="ffmpeg-minterpolate",
                artifact_gate=False,
                progress_callback=progress_callback,
            )

        self.assertIs(
            run_ffmpeg.call_args.kwargs["progress_callback"],
            progress_callback,
        )

    def test_rve_interpolation_forwards_cancel_event(self):
        cancel_event = threading.Event()
        with (
            patch(
                "framestudio.interpolation.require_validated_backend",
                return_value=BackendValidation(
                    backend="rve-4.26",
                    available=True,
                    artifact_status="validated",
                    reason="test backend",
                    target_rate=Fraction(60, 1),
                ),
            ),
            patch("framestudio_fps.run_interpolation_rve") as run_interpolation_rve,
        ):
            run_source_interpolation(
                Path("source.mp4"),
                Path("target.mp4"),
                source_rate=Fraction(30, 1),
                source_frames=30,
                target_rate=Fraction(60, 1),
                target_frames=60,
                backend="rve-4.26",
                artifact_gate=False,
                cancel_event=cancel_event,
            )

        self.assertIs(
            run_interpolation_rve.call_args.kwargs["cancel_event"],
            cancel_event,
        )

    def test_rve_interpolation_forwards_progress_to_export_callback(self):
        export_progress = Mock()
        with (
            patch(
                "framestudio.interpolation.require_validated_backend",
                return_value=BackendValidation(
                    backend="rve-4.26",
                    available=True,
                    artifact_status="validated",
                    reason="test backend",
                    target_rate=Fraction(60, 1),
                ),
            ),
            patch("framestudio_fps.run_interpolation_rve") as run_interpolation_rve,
        ):
            run_source_interpolation(
                Path("source.mp4"),
                Path("target.mp4"),
                source_rate=Fraction(30, 1),
                source_frames=30,
                target_rate=Fraction(60, 1),
                target_frames=60,
                backend="rve-4.26",
                artifact_gate=False,
                progress_callback=export_progress,
            )

        rve_progress = run_interpolation_rve.call_args.kwargs["progress_callback"]
        rve_progress(30, 60, 42.5)

        export_progress.assert_called_once()
        progress = export_progress.call_args.args[0]
        self.assertEqual(progress.stage, "interpolation")
        self.assertEqual(progress.percent, 50.0)
        self.assertEqual(progress.frame, 30)
        self.assertEqual(progress.total_frames, 60)
        self.assertEqual(progress.fps, 42.5)

    def test_rve_interpolation_defaults_to_gpu_encoder(self):
        with (
            patch(
                "framestudio.interpolation.require_validated_backend",
                return_value=BackendValidation(
                    backend="rve-4.26",
                    available=True,
                    artifact_status="validated",
                    reason="test backend",
                    target_rate=Fraction(60, 1),
                ),
            ),
            patch("framestudio_fps.run_interpolation_rve") as run_interpolation_rve,
        ):
            run_source_interpolation(
                Path("source.mp4"),
                Path("target.mp4"),
                source_rate=Fraction(30, 1),
                source_frames=30,
                target_rate=Fraction(60, 1),
                target_frames=60,
                backend="rve-4.26",
                artifact_gate=False,
            )

        arguments = run_interpolation_rve.call_args.args[6]
        self.assertEqual(arguments.encoder, "h264_nvenc")

    def test_unsafe_profile_is_not_silently_accepted(self):
        with patch(
            "framestudio.interpolation.validate_interpolation_backend",
            return_value=BackendValidation(
                backend="rve-4.26",
                available=True,
                artifact_status="rejected",
                reason="periodic grid artifact detected",
                model="4.26",
                precision="float16",
                runtime="TensorRT",
                input_format="RGBH",
                target_rate=Fraction(60, 1),
            ),
        ):
            from framestudio.interpolation import require_validated_backend

            with self.assertRaises(ExportExecutionError):
                require_validated_backend(
                    "rve-4.26",
                    source_rate=Fraction(30000, 1001),
                    target_rate=Fraction(60, 1),
                )

    def test_legacy_interpolation_failures_use_export_error_boundary(self):
        with (
            patch(
                "framestudio.interpolation.require_validated_backend",
                return_value=BackendValidation(
                    backend="vs-rife",
                    available=True,
                    artifact_status="validated",
                    reason="test backend",
                    target_rate=Fraction(60, 1),
                ),
            ),
            patch(
                "framestudio_fps.run_interpolation",
                side_effect=RuntimeError("legacy interpolation failed"),
            ),
        ):
            with self.assertRaisesRegex(ExportExecutionError, "legacy interpolation failed"):
                run_source_interpolation(
                    Path("source.mp4"),
                    Path("target.mp4"),
                    source_rate=Fraction(30, 1),
                    source_frames=30,
                    target_rate=Fraction(60, 1),
                    target_frames=60,
                    backend="vs-rife",
                    artifact_gate=False,
                )


if __name__ == "__main__":
    unittest.main()
