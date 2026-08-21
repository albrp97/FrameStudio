import io
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from resolve_editor.cli import cli_main
from resolve_editor.model import Project
from resolve_editor.persistence import load_project, save_project


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


def run_cli(*arguments: str):
    stdout = io.StringIO()
    stderr = io.StringIO()
    result = cli_main(
        list(arguments),
        stdout=stdout,
        stderr=stderr,
    )
    return result, stdout, stderr


class EditorCliEditingTests(unittest.TestCase):
    def test_import_creates_a_project_using_probed_metadata(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = root / "source.mp4"
            source.write_bytes(b"fixture")
            project_path = root / "edit.resolve.json"

            with patch(
                "resolve_editor.cli.create_project_from_source",
                return_value=make_project(root),
            ):
                result, stdout, stderr = run_cli(
                    "import",
                    str(source),
                    "--project",
                    str(project_path),
                )

            self.assertEqual(result, 0)
            self.assertEqual(stderr.getvalue(), "")
            payload = json.loads(stdout.getvalue())
            self.assertTrue(payload["ok"])
            self.assertEqual(payload["command"], "import")
            self.assertTrue(project_path.is_file())
            restored = load_project(project_path)
            self.assertEqual(restored.source.metadata["width"], 320)
            self.assertEqual(
                payload["project"]["project_id"],
                restored.project_id,
            )

    def test_split_delete_restore_and_duration_round_trip_by_stable_ids(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            project_path = root / "edit.resolve.json"
            save_project(make_project(root), project_path)

            result, stdout, stderr = run_cli(
                "split",
                str(project_path),
                "--at",
                "4",
            )
            self.assertEqual(result, 0)
            self.assertEqual(stderr.getvalue(), "")
            split_payload = json.loads(stdout.getvalue())
            segments = split_payload["project"]["timeline"]["segments"]
            self.assertEqual(len(segments), 2)
            self.assertEqual(
                [segment["duration_seconds"] for segment in segments],
                [4.0, 6.0],
            )
            second_id = segments[1]["segment_id"]

            result, stdout, stderr = run_cli(
                "delete",
                str(project_path),
                "--segment",
                second_id,
            )
            self.assertEqual(result, 0)
            delete_payload = json.loads(stdout.getvalue())
            self.assertTrue(delete_payload["operation"]["deleted"])
            self.assertEqual(
                delete_payload["project"]["timeline"]["edited_duration_seconds"],
                4.0,
            )

            result, stdout, stderr = run_cli(
                "restore",
                str(project_path),
                "--segment",
                second_id,
            )
            self.assertEqual(result, 0)
            restore_payload = json.loads(stdout.getvalue())
            self.assertFalse(restore_payload["operation"]["deleted"])
            self.assertEqual(
                restore_payload["project"]["timeline"]["edited_duration_seconds"],
                10.0,
            )

            result, stdout, stderr = run_cli(
                "duration",
                str(project_path),
            )
            self.assertEqual(result, 0)
            duration_payload = json.loads(stdout.getvalue())
            self.assertEqual(duration_payload["duration_seconds"], 10.0)

    def test_repeated_delete_is_idempotent_and_does_not_change_segment_identity(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            project_path = root / "edit.resolve.json"
            project = make_project(root)
            project.segment_timeline.split(4.0)
            segment_id = project.segment_timeline.segments[1].segment_id
            save_project(project, project_path)

            first_result, first_stdout, _ = run_cli(
                "delete",
                str(project_path),
                "--segment",
                segment_id,
            )
            second_result, second_stdout, _ = run_cli(
                "delete",
                str(project_path),
                "--segment",
                segment_id,
            )

            self.assertEqual(first_result, 0)
            self.assertEqual(second_result, 0)
            first = json.loads(first_stdout.getvalue())
            second = json.loads(second_stdout.getvalue())
            self.assertEqual(first, second)
            restored = load_project(project_path)
            self.assertEqual(
                [segment.segment_id for segment in restored.segment_timeline.segments],
                [segment["segment_id"] for segment in first["project"]["timeline"]["segments"]],
            )
            self.assertTrue(
                restored.segment_timeline.segments[1].deleted,
            )

    def test_invalid_split_preserves_the_last_valid_project(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            project_path = root / "edit.resolve.json"
            save_project(make_project(root), project_path)
            before = project_path.read_bytes()

            result, stdout, stderr = run_cli(
                "split",
                str(project_path),
                "--at",
                "0",
            )

            self.assertEqual(result, 3)
            self.assertEqual(stdout.getvalue(), "")
            payload = json.loads(stderr.getvalue())
            self.assertEqual(payload["error"]["code"], "invalid_operation")
            self.assertEqual(project_path.read_bytes(), before)
            self.assertEqual(len(load_project(project_path).segment_timeline.segments), 1)

    def test_save_and_reopen_use_the_same_persisted_project_contract(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            project_path = root / "edit.resolve.json"
            copy_path = root / "copy.resolve.json"
            save_project(make_project(root), project_path)

            result, stdout, stderr = run_cli(
                "save",
                str(project_path),
                "--output",
                str(copy_path),
            )
            self.assertEqual(result, 0)
            self.assertEqual(stderr.getvalue(), "")
            saved = json.loads(stdout.getvalue())
            self.assertTrue(copy_path.is_file())

            result, stdout, stderr = run_cli("reopen", str(copy_path))
            self.assertEqual(result, 0)
            reopened = json.loads(stdout.getvalue())
            self.assertEqual(
                saved["project"]["project_id"],
                reopened["project"]["project_id"],
            )
            self.assertEqual(
                saved["project"]["timeline"],
                reopened["project"]["timeline"],
            )


if __name__ == "__main__":
    unittest.main()
