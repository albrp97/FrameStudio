import unittest
from fractions import Fraction
from pathlib import Path
from tempfile import TemporaryDirectory

from resolve_editor.export_estimates import (
    RVE_CALIBRATION,
    SourceWorkload,
    estimate_export,
    estimate_project_export,
)
from resolve_editor.export_naming import (
    ExportDestinationError,
    collision_safe_destination,
    smart_export_name,
    validate_export_destination,
)
from resolve_editor.fps_policy import resolve_frame_rate_policy
from resolve_editor.model import Project


class EditorExportPlanningTests(unittest.TestCase):
    def test_smart_name_includes_target_and_backend_only_for_enhanced_output(self):
        policy = resolve_frame_rate_policy(
            ({"source_id": "source", "frame_rate": "30000/1001"},),
            choice="60",
            enhancement_enabled=True,
        ).policy

        self.assertEqual(
            smart_export_name(
                ("portrait.mp4",),
                policy=policy,
                backend="rve-4.26",
            ),
            "portrait-edited-rife4.26-60fps.mp4",
        )
        ordinary = resolve_frame_rate_policy(
            ({"source_id": "source", "frame_rate": "30/1"},),
            choice="highest",
            enhancement_enabled=False,
        ).policy
        self.assertEqual(
            smart_export_name(("portrait.mp4",), policy=ordinary),
            "portrait-edited.mp4",
        )

    def test_collision_safe_destination_never_reuses_existing_output(self):
        with TemporaryDirectory() as temporary_directory:
            folder = Path(temporary_directory)
            first = folder / "edit.mp4"
            second = folder / "edit-1.mp4"
            first.write_bytes(b"existing")
            second.write_bytes(b"existing")

            result = collision_safe_destination(folder, "edit.mp4")

            self.assertEqual(result, folder / "edit-2.mp4")
            self.assertFalse(result.exists())

    def test_destination_validation_rejects_project_source_directory_and_invalid_suffix(self):
        with TemporaryDirectory() as temporary_directory:
            folder = Path(temporary_directory)
            project = folder / "edit.resolve.json"
            source = folder / "source.mp4"
            project.write_bytes(b"project")
            source.write_bytes(b"source")

            for destination in (
                project,
                source,
                folder,
                folder / "output.txt",
            ):
                with self.assertRaises(ExportDestinationError):
                    validate_export_destination(
                        destination,
                        project_path=project,
                        source_paths=(source,),
                    )

    def test_estimator_uses_rational_frames_and_zero_interpolation_when_disabled(self):
        workload = (
            SourceWorkload(
                source_id="source",
                duration_seconds=30.0,
                source_rate=Fraction(30000, 1001),
                source_frames=900,
            ),
        )
        enhanced_policy = resolve_frame_rate_policy(
            ({"source_id": "source", "frame_rate": "30000/1001"},),
            choice="60",
            enhancement_enabled=True,
        )
        ordinary_policy = resolve_frame_rate_policy(
            ({"source_id": "source", "frame_rate": "30000/1001"},),
            choice="60",
            enhancement_enabled=False,
        )

        enhanced = estimate_export(
            workload,
            enhanced_policy,
            calibration=RVE_CALIBRATION,
        )
        ordinary = estimate_export(
            workload,
            ordinary_policy,
            calibration=RVE_CALIBRATION,
        )

        self.assertEqual(enhanced.source_frames, 900)
        self.assertEqual(enhanced.target_frames, 1802)
        self.assertGreater(enhanced.interpolation_seconds, 0.0)
        self.assertEqual(ordinary.interpolation_seconds, 0.0)
        self.assertLess(ordinary.total_seconds, enhanced.total_seconds)

    def test_estimator_returns_low_confidence_range_without_calibration(self):
        workload = (
            SourceWorkload(
                source_id="source",
                duration_seconds=10.0,
                source_rate=Fraction(30, 1),
            ),
        )
        policy = resolve_frame_rate_policy(
            ({"source_id": "source", "frame_rate": "30/1"},),
            choice="60",
            enhancement_enabled=True,
        )

        estimate = estimate_export(workload, policy, calibration=None)

        self.assertEqual(estimate.confidence, "low")
        self.assertIsNone(estimate.total_seconds)
        self.assertIsNotNone(estimate.lower_seconds)
        self.assertIsNotNone(estimate.upper_seconds)
        self.assertLess(estimate.lower_seconds, estimate.upper_seconds)

    def test_project_estimate_accounts_for_full_source_enhancement_and_edited_output(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = root / "source.mp4"
            source.write_bytes(b"fixture")
            project = Project.create(
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
            project.timeline.split(5.0)
            project.timeline.delete_segment(project.timeline.segments[1].segment_id)
            policy = resolve_frame_rate_policy(
                ({"source_id": "source", "frame_rate": "10/1"},),
                choice="custom",
                custom_rate="20/1",
                enhancement_enabled=True,
                backend="ffmpeg-minterpolate",
            )

            estimate = estimate_project_export(project, policy)

        self.assertEqual(estimate.source_frames, 100)
        self.assertEqual(estimate.target_frames, 100)
        self.assertEqual(estimate.eligible_source_frames, 100)
        self.assertEqual(estimate.eligible_target_frames, 200)
        self.assertEqual(estimate.enhancement_duration_seconds, 10.0)
        self.assertEqual(estimate.edited_duration_seconds, 5.0)


if __name__ == "__main__":
    unittest.main()
