import io
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from resolve_editor.cli import cli_main
from resolve_editor.model import Project
from resolve_editor.persistence import save_project


def make_project(root: Path) -> Project:
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
    project.segment_timeline.split(4.0)
    project.segment_timeline.delete_segment(
        project.segment_timeline.segments[1].segment_id,
    )
    project.set_playhead(2.0)
    return project


class EditorCliInspectionTests(unittest.TestCase):
    def test_inspect_reports_stable_project_timeline_and_redacted_source(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            project_path = root / "edit.resolve.json"
            project = make_project(root)
            save_project(project, project_path)
            before = project_path.read_bytes()

            stdout = io.StringIO()
            stderr = io.StringIO()
            result = cli_main(
                ["inspect", str(project_path)],
                stdout=stdout,
                stderr=stderr,
            )
            first = json.loads(stdout.getvalue())

            stdout.seek(0)
            stdout.truncate(0)
            result_again = cli_main(
                ["inspect", str(project_path)],
                stdout=stdout,
                stderr=stderr,
            )
            second = json.loads(stdout.getvalue())

            self.assertEqual(result, 0)
            self.assertEqual(result_again, 0)
            self.assertEqual(stderr.getvalue(), "")
            self.assertEqual(first, second)
            self.assertEqual(first["command"], "inspect")
            inspected = first["project"]
            self.assertEqual(inspected["timeline"]["playhead_seconds"], 2.0)
            self.assertEqual(
                inspected["timeline"]["edited_duration_seconds"],
                4.0,
            )
            self.assertEqual(
                [segment["deleted"] for segment in inspected["timeline"]["segments"]],
                [False, True],
            )
            self.assertNotIn(str(root), stdout.getvalue())
            self.assertEqual(project_path.read_bytes(), before)

    def test_inspect_missing_project_returns_structured_error(self):
        stdout = io.StringIO()
        stderr = io.StringIO()

        result = cli_main(
            ["inspect", "/tmp/missing.resolve.json"],
            stdout=stdout,
            stderr=stderr,
        )

        self.assertEqual(result, 3)
        self.assertEqual(stdout.getvalue(), "")
        payload = json.loads(stderr.getvalue())
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["error"]["code"], "project_io")
        self.assertIn("does not exist", payload["error"]["message"])

    def test_inspect_missing_source_returns_structured_error(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            project_path = root / "edit.resolve.json"
            project = make_project(root)
            save_project(project, project_path)
            (root / "source.mp4").unlink()

            stdout = io.StringIO()
            stderr = io.StringIO()
            result = cli_main(
                ["inspect", str(project_path)],
                stdout=stdout,
                stderr=stderr,
            )

            self.assertEqual(result, 3)
            self.assertEqual(stdout.getvalue(), "")
            payload = json.loads(stderr.getvalue())
            self.assertEqual(payload["error"]["code"], "source_unavailable")
            self.assertIn("missing", payload["error"]["message"].lower())

    def test_analyze_audio_reports_and_persists_explicit_failure_state(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = root / "source.mp4"
            source.write_bytes(b"fixture")
            project = Project.create(
                source,
                {
                    "duration_seconds": 1.0,
                    "width": 320,
                    "height": 180,
                    "frame_rate": "10/1",
                    "video_codec": "h264",
                    "audio_codec": "aac",
                    "audio_stream_present": True,
                    "format_name": "mp4",
                },
            )
            project_path = root / "edit.resolve.json"
            save_project(project, project_path)
            stdout = io.StringIO()
            stderr = io.StringIO()

            result = cli_main(
                [
                    "analyze-audio",
                    str(project_path),
                    "--ffmpeg",
                    "/missing/ffmpeg",
                ],
                stdout=stdout,
                stderr=stderr,
            )

            payload = json.loads(stdout.getvalue())
            reopened = Project.from_dict(json.loads(project_path.read_text(encoding="utf-8")))

        self.assertEqual(result, 0)
        self.assertEqual(stderr.getvalue(), "")
        source_id = project.source.source_id
        self.assertEqual(payload["command"], "analyze-audio")
        self.assertEqual(payload["operation"]["statuses"][source_id], "failed")
        self.assertEqual(payload["project"]["audio_decisions"][source_id]["status"], "failed")
        self.assertEqual(
            reopened.source_audio_settings(source_id)["status"],
            "failed",
        )


if __name__ == "__main__":
    unittest.main()
