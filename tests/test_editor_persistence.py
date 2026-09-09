import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

from framestudio.app_project import (
    autosave_current_project,
    recover_autosave,
)
from framestudio.fps_policy import FrameRatePolicy
from framestudio.model import Project
from framestudio.operations import apply_visual_transform, enable_triplicate
from framestudio.persistence import (
    ProjectPersistenceError,
    autosave_exists,
    autosave_path,
    load_autosave,
    load_project,
    save_autosave,
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
    def _recovery_window(self, current_project=None):
        window = Mock()
        window.project = current_project
        window.project_path = Path("/tmp/user-selected.framestudio.json")
        window.controller = None
        window.segment_timeline = None
        window._export_in_progress = False
        window._source_load_in_progress = False
        window._show_error = Mock()
        window._set_status = Mock()
        return window

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

    def test_appended_source_preserves_existing_cuts_through_save_and_reopen(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            project = make_project(root)
            project.timeline.split(4.0)
            deleted_id = project.timeline.segments[1].segment_id
            project.timeline.set_deleted(deleted_id, True)
            added_path = root / "added.mp4"
            added_path.write_bytes(b"added")
            added = Project.create(
                added_path,
                {
                    "duration_seconds": 3.0,
                    "width": 180,
                    "height": 320,
                    "frame_rate": "30/1",
                    "video_codec": "h264",
                    "audio_codec": None,
                    "format_name": "mp4",
                },
            )
            project.append_sources((added.source,))
            destination = root / "expanded.framestudio.json"

            save_project(project, destination)
            restored = load_project(destination)

            self.assertEqual(restored.schema_version, 3)
            self.assertEqual(len(restored.sources), 2)
            self.assertTrue(restored.timeline.find(deleted_id).deleted)
            self.assertEqual(restored.timeline.blocks[-1].source_id, restored.sources[1].source_id)
            self.assertEqual(restored.timeline.edited_duration_seconds, 7.0)

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

    def test_autosave_uses_one_xdg_state_path_and_round_trips(self):
        with TemporaryDirectory() as temporary_directory:
            with patch.dict("os.environ", {"XDG_STATE_HOME": temporary_directory}):
                project = make_project(Path(temporary_directory))

                saved = save_autosave(project)
                restored = load_autosave()

                self.assertEqual(
                    saved,
                    Path(temporary_directory) / "framestudio" / "autosave.framestudio.json",
                )
                self.assertEqual(autosave_path(), saved)
                self.assertTrue(autosave_exists())
                self.assertEqual(restored.to_dict(), project.to_dict())

    def test_recovery_attaches_valid_autosave_without_changing_project_path(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            with patch.dict("os.environ", {"XDG_STATE_HOME": temporary_directory}):
                project = make_project(root)
                save_autosave(project)
                window = self._recovery_window(object())

                def attach_recovered_project(target_window, _project, project_path):
                    target_window.project_path = project_path

                with (
                    patch(
                        "framestudio.app_project.attach_project",
                        side_effect=attach_recovered_project,
                    ) as attach,
                    patch("framestudio.app_project._start_audio_analysis") as analyze,
                ):
                    self.assertFalse(recover_autosave(window, object()))

                attach.assert_called_once()
                self.assertIs(attach.call_args.args[0], window)
                recovered = attach.call_args.args[1]
                self.assertEqual(recovered.to_dict(), project.to_dict())
                self.assertIsNone(attach.call_args.args[2])
                analyze.assert_called_once()
                self.assertEqual(
                    window.project_path,
                    Path("/tmp/user-selected.framestudio.json"),
                )
                window._show_error.assert_not_called()

    def test_recovery_rejects_missing_source_and_keeps_current_project(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            with patch.dict("os.environ", {"XDG_STATE_HOME": temporary_directory}):
                project = make_project(root)
                save_autosave(project)
                source_path = root / "source.mp4"
                source_path.unlink()
                current_project = object()
                window = self._recovery_window(current_project)

                with patch("framestudio.app_project.attach_project") as attach:
                    self.assertFalse(recover_autosave(window, object()))

                attach.assert_not_called()
                self.assertIs(window.project, current_project)
                window._show_error.assert_called_once()
                self.assertIn("missing", str(window._show_error.call_args.args[0]).lower())

    def test_recovery_rejects_changed_source_and_keeps_current_project(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            with patch.dict("os.environ", {"XDG_STATE_HOME": temporary_directory}):
                project = make_project(root)
                save_autosave(project)
                source_path = root / "source.mp4"
                source_path.write_bytes(b"changed")
                current_project = object()
                window = self._recovery_window(current_project)

                with patch("framestudio.app_project.attach_project") as attach:
                    self.assertFalse(recover_autosave(window, object()))

                attach.assert_not_called()
                self.assertIs(window.project, current_project)
                window._show_error.assert_called_once()
                self.assertIn("changed", str(window._show_error.call_args.args[0]).lower())

    def test_autosave_failure_is_reported(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            with patch.dict("os.environ", {"XDG_STATE_HOME": temporary_directory}):
                window = self._recovery_window(make_project(root))

                with patch(
                    "framestudio.app_project.save_autosave",
                    side_effect=ProjectPersistenceError("disk full"),
                ):
                    self.assertFalse(autosave_current_project(window))

                window._show_error.assert_called_once()
                self.assertIn("Autosave failed", window._show_error.call_args.args[0])

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
