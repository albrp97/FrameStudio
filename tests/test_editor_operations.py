import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from resolve_editor.export import ExportPlan
from resolve_editor.fps_policy import FrameRatePolicy
from resolve_editor.media import MediaProbe
from resolve_editor.model import Project, ProjectValidationError
from resolve_editor.operations import (
    copy_segments,
    create_project_from_source,
    export_destination_conflicts_with_project,
    paste_segments_after_selection,
    plan_project_export,
    set_segment_deleted,
    split_segment,
    toggle_segment_deleted,
)


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


def make_probe(root: Path) -> MediaProbe:
    return MediaProbe(
        path=root / "source.mp4",
        duration_seconds=10.0,
        width=320,
        height=180,
        frame_rate="10/1",
        video_codec="h264",
        audio_codec=None,
        format_name="mp4",
    )


class EditorOperationsTests(unittest.TestCase):
    def test_export_destination_conflict_uses_resolved_project_paths(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            project_path = root / "edit.resolve.json"
            project_path.write_text("project", encoding="utf-8")

            self.assertTrue(
                export_destination_conflicts_with_project(
                    project_path,
                    root / "." / "edit.resolve.json",
                )
            )
            self.assertFalse(
                export_destination_conflicts_with_project(
                    None,
                    project_path,
                )
            )
            self.assertFalse(
                export_destination_conflicts_with_project(
                    project_path,
                    root / "edited.mp4",
                )
            )

    def test_create_project_from_source_uses_the_shared_probe_boundary(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = root / "source.mp4"
            source.write_bytes(b"fixture")

            with patch(
                "resolve_editor.operations.probe_media",
                return_value=make_probe(root),
            ) as probe:
                project = create_project_from_source(source)

            probe.assert_called_once_with(source, "ffprobe")
            self.assertEqual(project.source.metadata["width"], 320)
            self.assertEqual(project.duration_seconds, 10.0)

    def test_split_and_deletion_operations_use_timeline_invariants(self):
        with TemporaryDirectory() as temporary_directory:
            project = make_project(Path(temporary_directory))
            first, second = split_segment(project.segment_timeline, 4.0)

            self.assertEqual((first.start_seconds, first.end_seconds), (0.0, 4.0))
            self.assertEqual((second.start_seconds, second.end_seconds), (4.0, 10.0))
            self.assertTrue(
                set_segment_deleted(
                    project.segment_timeline,
                    second.segment_id,
                    True,
                )
            )
            self.assertTrue(project.segment_timeline.segments[1].deleted)
            self.assertFalse(
                toggle_segment_deleted(
                    project.segment_timeline,
                    second.segment_id,
                )
            )
            self.assertFalse(project.segment_timeline.segments[1].deleted)

            with self.assertRaises(ProjectValidationError):
                split_segment(project.segment_timeline, 0.0)

    def test_paste_after_selection_inserts_after_the_selected_block(self):
        with TemporaryDirectory() as temporary_directory:
            project = make_project(Path(temporary_directory))
            project.timeline.split(3.0)
            project.timeline.split(6.0)
            before_ids = [segment.segment_id for segment in project.timeline.segments]
            selected = project.timeline.segments[1]
            copied = copy_segments(project, [selected.segment_id])

            pasted = paste_segments_after_selection(
                project,
                copied,
                selected.segment_id,
            )

            self.assertEqual(len(pasted), 1)
            self.assertEqual(
                [segment.segment_id for segment in project.timeline.segments],
                [before_ids[0], before_ids[1], pasted[0].segment_id, before_ids[2]],
            )
            self.assertEqual(pasted[0].timeline_start, 6.0)
            self.assertEqual(pasted[0].timeline_end, 9.0)

    def test_project_export_planning_is_a_shared_boundary(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            project = make_project(root)
            expected = ExportPlan(
                route="stream-copy",
                source=root / "source.mp4",
                destination=root / "edited.mp4",
                segments=tuple(project.segment_timeline.segments),
                expected_duration_seconds=10.0,
                reason="shared plan",
            )

            with (
                patch(
                    "resolve_editor.operations.probe_media",
                    return_value=make_probe(root),
                ),
                patch(
                    "resolve_editor.operations.plan_export",
                    return_value=expected,
                ) as plan,
            ):
                actual = plan_project_export(
                    project,
                    root / "edited.mp4",
                )

            self.assertEqual(actual, expected)
            plan.assert_called_once()

    def test_mixed_project_planning_leaves_target_rate_resolution_to_mixed_planner(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            first_path = root / "first.mp4"
            second_path = root / "second.mp4"
            first_path.write_bytes(b"first")
            second_path.write_bytes(b"second")
            project = Project.create_multi(
                (
                    (
                        first_path,
                        {
                            "duration_seconds": 2.0,
                            "width": 320,
                            "height": 180,
                            "frame_rate": "10/1",
                            "video_codec": "h264",
                            "audio_codec": None,
                            "format_name": "mp4",
                        },
                    ),
                    (
                        second_path,
                        {
                            "duration_seconds": 2.0,
                            "width": 320,
                            "height": 180,
                            "frame_rate": "20/1",
                            "video_codec": "h264",
                            "audio_codec": None,
                            "format_name": "mp4",
                        },
                    ),
                )
            )
            project.set_frame_rate_policy(
                FrameRatePolicy(
                    choice="custom",
                    custom_rate="30/1",
                    target_rate="30/1",
                )
            )
            expected = ExportPlan(
                route="fallback",
                source=first_path,
                destination=root / "edited.mp4",
                segments=tuple(project.timeline.segment_items),
                expected_duration_seconds=4.0,
                reason="shared mixed plan",
            )

            with (
                patch(
                    "resolve_editor.operations.probe_media",
                    side_effect=(
                        make_probe(root),
                        make_probe(root),
                    ),
                ),
                patch(
                    "resolve_editor.operations.ensure_project_audio_analysis",
                    return_value={},
                ),
                patch(
                    "resolve_editor.operations.plan_mixed_export",
                    return_value=expected,
                ) as plan,
            ):
                actual = plan_project_export(
                    project,
                    root / "edited.mp4",
                )

            self.assertEqual(actual, expected)
            self.assertNotIn("policy", plan.call_args.kwargs)


if __name__ == "__main__":
    unittest.main()
