import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from framestudio.export_panel import (
    fps_panel_rows,
    prepare_export_panel,
    upscale_panel_rows,
)
from framestudio.fps_policy import rate_choice_labels
from framestudio.interpolation import BackendValidation
from framestudio.model import Project


def make_project(root: Path) -> Project:
    source = root / "source.mp4"
    source.write_bytes(b"fixture")
    return Project.create(
        source,
        {
            "duration_seconds": 10.0,
            "width": 320,
            "height": 180,
            "frame_rate": "10/1",
            "video_codec": "h264",
            "audio_codec": None,
            "format_name": "mp4",
        },
    )


def make_multi_project(root: Path) -> Project:
    entries = []
    for name, width, height in (
        ("eligible-landscape.mp4", 640, 360),
        ("eligible-portrait.mp4", 720, 1280),
        ("ineligible-landscape.mp4", 1920, 1080),
    ):
        source = root / name
        source.write_bytes(b"fixture")
        entries.append(
            (
                source,
                {
                    "duration_seconds": 10.0,
                    "width": width,
                    "height": height,
                    "frame_rate": "30/1",
                    "video_codec": "h264",
                    "audio_codec": None,
                    "format_name": "mp4",
                },
            )
        )
    return Project.create_multi(entries)


def make_mixed_rate_project(root: Path) -> Project:
    entries = []
    for name, frame_rate in (
        ("source-30.mp4", "30/1"),
        ("source-60.mp4", "60/1"),
        ("source-120.mp4", "120/1"),
    ):
        source = root / name
        source.write_bytes(b"fixture")
        entries.append(
            (
                source,
                {
                    "duration_seconds": 10.0,
                    "width": 640,
                    "height": 360,
                    "frame_rate": frame_rate,
                    "video_codec": "h264",
                    "audio_codec": None,
                    "format_name": "mp4",
                },
            )
        )
    return Project.create_multi(entries)


def unavailable_rve_validation(
    backend,
    *,
    source_rate,
    target_rate,
    ffmpeg_path,
):
    if backend.startswith("rve"):
        return BackendValidation(
            backend=backend,
            available=False,
            artifact_status="blocked",
            reason="RVE Python environment is unavailable",
            target_rate=target_rate,
        )
    return BackendValidation(
        backend=backend,
        available=True,
        artifact_status="validated-fallback",
        reason="Explicit FFmpeg minterpolate fallback",
        runtime="FFmpeg",
        input_format="native decoded frames",
        target_rate=target_rate,
    )


class EditorExportPanelTests(unittest.TestCase):
    def test_default_panel_policy_is_sixty_with_enhancement_enabled(self):
        with TemporaryDirectory() as temporary_directory:
            state = prepare_export_panel(
                make_project(Path(temporary_directory)),
                Path(temporary_directory),
                project_path=Path(temporary_directory) / "edit.framestudio.json",
            )

        self.assertTrue(state.valid)
        self.assertEqual(state.policy.policy.choice, "60")
        self.assertTrue(state.policy.policy.enhancement_enabled)
        self.assertIsNotNone(state.upscale_policy)
        self.assertTrue(state.upscale_policy.policy.enhancement_enabled)

    def test_panel_reports_source_level_videos_to_upscale_count(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            state = prepare_export_panel(
                make_multi_project(root),
                root,
                choice="lowest",
                enhancement_enabled=False,
                upscale_enabled=True,
                backend="ffmpeg-minterpolate",
                project_path=root / "edit.framestudio.json",
            )

        rows = dict(state.display_rows)
        self.assertEqual(rows["Videos to upscale"], "2")
        self.assertEqual(state.summary["upscale"]["eligible_source_count"], 2)
        self.assertEqual(state.summary["upscale"]["source_count"], 3)

    def test_panel_reports_source_level_videos_to_fps_enhance_count(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            state = prepare_export_panel(
                make_mixed_rate_project(root),
                root,
                choice="60",
                enhancement_enabled=True,
                upscale_enabled=False,
                backend="ffmpeg-minterpolate",
                project_path=root / "edit.framestudio.json",
            )

        rows = dict(state.display_rows)
        self.assertEqual(rows["Videos to FPS enhance"], "1")
        self.assertEqual(state.summary["fps"]["eligible_source_count"], 1)
        self.assertEqual(state.summary["fps"]["source_count"], 3)

    def test_pending_fps_rows_report_source_count_before_export_plan_finishes(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            rows = dict(
                fps_panel_rows(
                    make_mixed_rate_project(root),
                    choice="60",
                    enhancement_enabled=True,
                    backend="ffmpeg-minterpolate",
                )
            )

        self.assertEqual(rows["FPS enhancement"], "On")
        self.assertEqual(rows["Videos to FPS enhance"], "1")

    def test_pending_fps_rows_report_zero_when_disabled(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            rows = dict(
                fps_panel_rows(
                    make_mixed_rate_project(root),
                    choice="60",
                    enhancement_enabled=False,
                    backend="ffmpeg-minterpolate",
                )
            )

        self.assertEqual(rows["FPS enhancement"], "Off")
        self.assertEqual(rows["Videos to FPS enhance"], "0")

    def test_pending_upscale_rows_report_count_before_export_plan_finishes(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            rows = dict(upscale_panel_rows(make_multi_project(root), enabled=True))

        self.assertEqual(rows["Upscale enhancement"], "On")
        self.assertEqual(rows["Upscale model"], "SuperUltraCompact")
        self.assertEqual(rows["Videos to upscale"], "2")

    def test_pending_upscale_rows_report_zero_when_disabled(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            rows = dict(upscale_panel_rows(make_project(root), enabled=False))

        self.assertEqual(rows["Upscale enhancement"], "Off")
        self.assertEqual(rows["Videos to upscale"], "0")
        self.assertNotIn("Upscale model", rows)

    def test_panel_reports_zero_videos_to_upscale_when_none_are_eligible(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = root / "source.mp4"
            source.write_bytes(b"fixture")
            project = Project.create(
                source,
                {
                    "duration_seconds": 10.0,
                    "width": 1920,
                    "height": 1080,
                    "frame_rate": "10/1",
                    "video_codec": "h264",
                    "audio_codec": None,
                    "format_name": "mp4",
                },
            )
            state = prepare_export_panel(
                project,
                root,
                choice="lowest",
                enhancement_enabled=False,
                upscale_enabled=True,
                backend="ffmpeg-minterpolate",
                project_path=root / "edit.framestudio.json",
            )

        self.assertEqual(dict(state.display_rows)["Videos to upscale"], "0")

    def test_rate_choice_labels_include_resolved_input_rates(self):
        labels = rate_choice_labels(
            (
                {"source_id": "one", "frame_rate": "30000/1001"},
                {"source_id": "two", "frame_rate": "60/1"},
            )
        )

        self.assertEqual(labels[0], "Lowest input FPS (29.97 FPS)")
        self.assertEqual(labels[1], "Highest input FPS (60 FPS)")

    def test_panel_state_contains_smart_name_estimate_and_target_summary(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            state = prepare_export_panel(
                make_project(root),
                root,
                choice="60",
                enhancement_enabled=False,
                backend="ffmpeg-minterpolate",
                project_path=root / "edit.framestudio.json",
            )

        self.assertTrue(state.valid)
        self.assertEqual(state.filename, "edit-edited.mp4")
        self.assertEqual(state.summary["target_rate"], "60")
        self.assertEqual(state.summary["input_count"], 1)
        self.assertGreater(state.estimate["total_seconds"], 0.0)
        self.assertGreater(state.estimate["estimated_output_size_bytes"], 0)
        self.assertTrue(
            {"Final duration", "Estimated processing time", "Estimated output size"}.issubset(
                {label for label, _value in state.display_rows}
            )
        )
        self.assertNotIn("Assumptions", {label for label, _value in state.display_rows})

    def test_panel_state_uses_a_new_name_for_a_collision(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            (root / "edit-edited-ffmpeg-minterpolate-60fps.mp4").write_bytes(b"existing")

            with patch(
                "framestudio.export_panel.validate_interpolation_backend",
                side_effect=unavailable_rve_validation,
            ):
                state = prepare_export_panel(
                    make_project(root),
                    root,
                    project_path=root / "edit.framestudio.json",
                )

        self.assertTrue(state.valid)
        self.assertEqual(state.filename, "edit-edited-ffmpeg-minterpolate-60fps-1.mp4")
        self.assertFalse(state.destination.exists())

    def test_missing_default_backend_selects_validated_ffmpeg_fallback(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)

            with patch(
                "framestudio.export_panel.validate_interpolation_backend",
                side_effect=unavailable_rve_validation,
            ):
                state = prepare_export_panel(
                    make_project(root),
                    root,
                    choice="60",
                    enhancement_enabled=True,
                    project_path=root / "edit.framestudio.json",
                )

        self.assertTrue(state.valid)
        self.assertEqual(state.policy.policy.backend, "ffmpeg-minterpolate")
        self.assertEqual(state.backend_validation[0].artifact_status, "validated-fallback")
        self.assertIn("fallback", (state.notice or "").lower())

    def test_fallback_notice_names_the_requested_backend(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)

            with patch(
                "framestudio.export_panel.validate_interpolation_backend",
                side_effect=unavailable_rve_validation,
            ):
                state = prepare_export_panel(
                    make_project(root),
                    root,
                    choice="60",
                    enhancement_enabled=True,
                    backend="rve-custom",
                    project_path=root / "edit.framestudio.json",
                )

        self.assertTrue(state.valid)
        self.assertIn("rve-custom is unavailable", state.notice or "")

    def test_explicit_ffmpeg_fallback_uses_low_confidence_estimate(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            state = prepare_export_panel(
                make_project(root),
                root,
                choice="60",
                enhancement_enabled=True,
                backend="ffmpeg-minterpolate",
                project_path=root / "edit.framestudio.json",
            )

        self.assertTrue(state.valid)
        self.assertEqual(state.estimate["confidence"], "low")
        self.assertIsNone(state.estimate["calibration_name"])
        self.assertIsNone(state.estimate["total_seconds"])
        self.assertLess(
            state.estimate["lower_seconds"],
            state.estimate["upper_seconds"],
        )


if __name__ == "__main__":
    unittest.main()
