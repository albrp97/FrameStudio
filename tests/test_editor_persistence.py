import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from framestudio.fps_policy import FrameRatePolicy
from framestudio.model import Project
from framestudio.operations import apply_visual_transform, enable_triplicate
from framestudio.persistence import (
    ProjectPersistenceError,
    load_project,
    save_project,
)


def make_project(root):
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


class EditorPersistenceTests(unittest.TestCase):
    def test_frame_rate_policy_survives_save_and_reopen(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            project = make_project(root)
            project.set_frame_rate_policy(
                FrameRatePolicy(
                    choice="custom",
                    custom_rate="60/1",
                    target_rate="60/1",
                    enhancement_enabled=True,
                )
            )
            destination = root / "edit.framestudio.json"

            save_project(project, destination)
            restored = load_project(destination)

            self.assertEqual(
                restored.get_frame_rate_policy().to_dict(),
                project.get_frame_rate_policy().to_dict(),
            )
            self.assertTrue(restored.get_frame_rate_policy().enhancement_enabled)

    def test_projects_without_fps_settings_default_to_sixty_and_enhanced_policy(self):
        with TemporaryDirectory() as temporary_directory:
            project = make_project(Path(temporary_directory))

            policy = project.get_frame_rate_policy()

            self.assertEqual(policy.choice, "60")
            self.assertTrue(policy.enhancement_enabled)
            self.assertEqual(policy.target_rate, 60)

    def test_malformed_persisted_fps_policy_is_rejected(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            project = make_project(root)
            destination = root / "edit.framestudio.json"
            save_project(project, destination)
            payload = json.loads(destination.read_text(encoding="utf-8"))
            payload["output_settings"]["frame_rate_policy"] = {
                "version": 1,
                "choice": "custom",
                "target_rate": "0/1",
                "enhancement_enabled": True,
            }
            destination.write_text(json.dumps(payload), encoding="utf-8")

            with self.assertRaises(ProjectPersistenceError):
                load_project(destination)

    def test_save_and_load_round_trip(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            project = make_project(root)
            project.set_playhead(4.5)
            project.segment_timeline.split(4.5)
            project.segment_timeline.delete_segment(project.segment_timeline.segments[1].segment_id)
            destination = root / "edit.framestudio.json"

            save_project(project, destination)
            restored = load_project(destination)

            self.assertEqual(restored.to_dict(), project.to_dict())
            self.assertEqual(
                restored.segment_timeline.edited_duration_seconds,
                4.5,
            )
            self.assertTrue(destination.is_file())

    def test_failed_atomic_replace_keeps_previous_project(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            project = make_project(root)
            destination = root / "edit.framestudio.json"
            destination.write_text('{"previous": true}\n', encoding="utf-8")

            with patch(
                "framestudio.persistence.os.replace",
                side_effect=OSError("replace failed"),
            ):
                with self.assertRaises(ProjectPersistenceError):
                    save_project(project, destination)

            self.assertEqual(
                destination.read_text(encoding="utf-8"),
                '{"previous": true}\n',
            )
            self.assertEqual(list(root.glob(".edit.framestudio.json.partial-*")), [])

    def test_invalid_json_is_reported(self):
        with TemporaryDirectory() as temporary_directory:
            destination = Path(temporary_directory) / "edit.framestudio.json"
            destination.write_text("{not json", encoding="utf-8")

            with self.assertRaises(ProjectPersistenceError):
                load_project(destination)

    def test_zoom_dependent_focus_bounds_and_triplicate_survive_round_trip(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            project = make_project(root)
            segment_id = project.timeline.segments[0].segment_id
            apply_visual_transform(
                project,
                [segment_id],
                zoom=4.0,
                offset_x=2880.0,
                offset_y=-1620.0,
            )
            enable_triplicate(project, [segment_id])
            destination = root / "focus.framestudio.json"

            save_project(project, destination)
            restored = load_project(destination)

            segment = restored.timeline.segments[0]
            self.assertEqual(segment.visual_transform.zoom, 4.0)
            self.assertEqual(segment.visual_transform.offset_x, 2880.0)
            self.assertEqual(segment.visual_transform.offset_y, -1620.0)
            self.assertIsNotNone(segment.triplicate)
            self.assertEqual(segment.triplicate.shared_transform, segment.visual_transform)

    def test_default_zoom_triplicate_horizontal_offset_survives_round_trip(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            project = make_project(root)
            segment_id = project.timeline.segments[0].segment_id
            apply_visual_transform(
                project,
                [segment_id],
                zoom=1.0,
                offset_x=-640.0,
                offset_y=0.0,
            )
            enable_triplicate(project, [segment_id])
            destination = root / "default-zoom-focus.framestudio.json"

            save_project(project, destination)
            restored = load_project(destination)

            segment = restored.timeline.segments[0]
            self.assertEqual(
                segment.visual_transform,
                project.timeline.segments[0].visual_transform,
            )
            self.assertIsNotNone(segment.triplicate)
            self.assertEqual(segment.triplicate.shared_transform, segment.visual_transform)


if __name__ == "__main__":
    unittest.main()
