import io
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from framestudio.cli import (
    CLI_CONTRACT_VERSION,
    cli_main,
    error_payload,
    project_payload,
    success_payload,
)
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
            "audio_codec": "aac",
            "format_name": "mp4",
        },
    )


class EditorCliContractTests(unittest.TestCase):
    def test_success_payload_is_versioned_and_machine_readable(self):
        payload = success_payload("inspect", {"value": 1})

        self.assertEqual(
            payload,
            {
                "ok": True,
                "contract_version": CLI_CONTRACT_VERSION,
                "command": "inspect",
                "value": 1,
            },
        )

    def test_error_payload_is_structured_without_success_fields(self):
        payload = error_payload(
            "invalid_arguments",
            "Project is required",
            {"field": "project"},
        )

        self.assertEqual(payload["ok"], False)
        self.assertEqual(payload["contract_version"], CLI_CONTRACT_VERSION)
        self.assertEqual(payload["error"]["code"], "invalid_arguments")
        self.assertEqual(payload["error"]["message"], "Project is required")
        self.assertEqual(payload["error"]["details"], {"field": "project"})
        self.assertNotIn("result", payload)

    def test_project_payload_redacts_absolute_paths_by_default(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            project = make_project(root)

            payload = project_payload(
                project,
                root / "edit.framestudio.json",
                include_paths=False,
            )
            serialized = json.dumps(payload)

            self.assertEqual(payload["project_path"], "edit.framestudio.json")
            self.assertEqual(payload["source"]["path"], "source.mp4")
            self.assertEqual(payload["source"]["uri"], "source.mp4")
            self.assertTrue(payload["source"]["path_redacted"])
            self.assertNotIn(str(root), serialized)
            self.assertEqual(
                payload["timeline"]["edited_duration_seconds"],
                10.0,
            )
            self.assertEqual(len(payload["timeline"]["segments"]), 1)
            self.assertTrue(payload["upscale_policy"]["enhancement_enabled"])
            self.assertEqual(
                payload["upscale_policy"]["decisions"][0]["action"],
                "enhance",
            )

    def test_project_payload_can_explicitly_include_full_paths(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            project = make_project(root)

            payload = project_payload(
                project,
                root / "edit.framestudio.json",
                include_paths=True,
            )

            self.assertEqual(
                payload["project_path"],
                str((root / "edit.framestudio.json").resolve()),
            )
            self.assertEqual(payload["source"]["path"], str(project.source.path))
            self.assertFalse(payload["source"]["path_redacted"])

    def test_invalid_cli_arguments_are_json_errors_on_stderr(self):
        stdout = io.StringIO()
        stderr = io.StringIO()

        result = cli_main(["inspect"], stdout=stdout, stderr=stderr)

        self.assertEqual(result, 2)
        self.assertEqual(stdout.getvalue(), "")
        payload = json.loads(stderr.getvalue())
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["error"]["code"], "invalid_arguments")


if __name__ == "__main__":
    unittest.main()
