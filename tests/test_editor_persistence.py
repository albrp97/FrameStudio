import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from resolve_editor.model import Project
from resolve_editor.persistence import (
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
    def test_save_and_load_round_trip(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            project = make_project(root)
            project.set_playhead(4.5)
            project.segment_timeline.split(4.5)
            project.segment_timeline.delete_segment(project.segment_timeline.segments[1].segment_id)
            destination = root / "edit.resolve.json"

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
            destination = root / "edit.resolve.json"
            destination.write_text('{"previous": true}\n', encoding="utf-8")

            with patch(
                "resolve_editor.persistence.os.replace",
                side_effect=OSError("replace failed"),
            ):
                with self.assertRaises(ProjectPersistenceError):
                    save_project(project, destination)

            self.assertEqual(
                destination.read_text(encoding="utf-8"),
                '{"previous": true}\n',
            )
            self.assertEqual(list(root.glob(".edit.resolve.json.partial-*")), [])

    def test_invalid_json_is_reported(self):
        with TemporaryDirectory() as temporary_directory:
            destination = Path(temporary_directory) / "edit.resolve.json"
            destination.write_text("{not json", encoding="utf-8")

            with self.assertRaises(ProjectPersistenceError):
                load_project(destination)


if __name__ == "__main__":
    unittest.main()
