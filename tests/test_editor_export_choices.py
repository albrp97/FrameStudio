from __future__ import annotations

import io
import json
import shutil
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from framestudio.cli import cli_main
from framestudio.cli_parser import build_cli_parser
from framestudio.cli_types import CliError
from framestudio.model import Project
from framestudio.output_plan import (
    FINAL_ONLY_OUTPUT_MODE,
    SOURCE_ONLY_OUTPUT_MODE,
    resolve_output_selection,
)
from framestudio.persistence import load_project, save_project
from tests.test_editor_source_outputs_functionality import _make_constant_source


class EditorExportChoiceTests(unittest.TestCase):
    def setUp(self) -> None:
        if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
            self.skipTest("FFmpeg and ffprobe are required for output-choice planning")
        self.runtime = TemporaryDirectory(
            dir=Path(__file__).resolve().parent,
            prefix=".ticket114-export-choice-",
        )
        self.addCleanup(self.runtime.cleanup)
        self.root = Path(self.runtime.name)
        self.source = self.root / "source.mp4"
        _make_constant_source(
            self.source,
            color="red",
            frame_rate=24,
            width=320,
            height=180,
            frequencies=(440, 880),
            duration=1.0,
        )

    def _save_project(self, project_id: str) -> Path:
        project = Project.create(
            self.source,
            {
                "duration_seconds": 1.0,
                "width": 320,
                "height": 180,
                "frame_rate": "24/1",
                "video_codec": "h264",
                "audio_codec": "aac",
                "format_name": "mp4",
            },
            project_id=project_id,
        )
        project_path = self.root / f"{project_id}.framestudio.json"
        save_project(project, project_path)
        return project_path

    def _parse_output_mode(self, command: str, mode: str):
        arguments = [
            command,
            "project.framestudio.json",
            "--output-mode",
            mode,
        ]
        if command == "export":
            arguments.extend(("--output", "edited.mp4"))
        try:
            return build_cli_parser().parse_args(arguments)
        except CliError as error:
            self.fail(
                f"public {command} CLI must accept --output-mode {mode!r}: {error.message}",
            )

    def test_public_export_and_plan_commands_accept_all_output_modes(self):
        for command in ("export", "export-plan"):
            for mode in ("final-only", "combined", "source-only"):
                arguments = self._parse_output_mode(command, mode)
                self.assertEqual(arguments.output_mode, mode)

    def test_public_parser_rejects_neither_output_mode_explicitly(self):
        with self.assertRaises(CliError) as context:
            build_cli_parser().parse_args(
                [
                    "export-plan",
                    "project.framestudio.json",
                    "--output-mode",
                    "neither",
                ],
            )
        self.assertEqual(context.exception.code, "invalid_arguments")
        self.assertIn("--output-mode", context.exception.message)
        self.assertIn("neither", context.exception.message)

    def test_mode_override_is_plan_visible_without_mutating_persisted_choice(self):
        project_path = self._save_project("ticket114-output-choice")
        stdout = io.StringIO()
        stderr = io.StringIO()
        result = cli_main(
            [
                "export-plan",
                str(project_path),
                "--output",
                str(self.root / "source-only.mp4"),
                "--output-mode",
                SOURCE_ONLY_OUTPUT_MODE,
                "--full-paths",
            ],
            stdout=stdout,
            stderr=stderr,
        )

        self.assertEqual(result, 0, stderr.getvalue())
        self.assertEqual(stderr.getvalue(), "")
        payload = json.loads(stdout.getvalue())
        self.assertTrue(payload["ok"])
        self.assertEqual(
            payload["export"]["output_plan"]["mode"],
            SOURCE_ONLY_OUTPUT_MODE,
        )
        self.assertIsNone(payload["export"]["output_plan"]["final"])
        self.assertEqual(
            resolve_output_selection(load_project(project_path)).mode,
            FINAL_ONLY_OUTPUT_MODE,
        )

    def test_persisted_neither_choice_returns_structured_error_without_mutation(self):
        project_path = self._save_project("ticket114-invalid-choice")
        project = load_project(project_path)
        project.output_settings["output_selection"] = {
            "include_final": False,
            "include_source_outputs": False,
        }
        save_project(project, project_path)
        before = project_path.read_bytes()

        stdout = io.StringIO()
        stderr = io.StringIO()
        result = cli_main(
            [
                "export-plan",
                str(project_path),
                "--output",
                str(self.root / "invalid.mp4"),
            ],
            stdout=stdout,
            stderr=stderr,
        )

        self.assertNotEqual(result, 0)
        self.assertEqual(stdout.getvalue(), "")
        payload = json.loads(stderr.getvalue())
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["error"]["code"], "export_planning")
        self.assertIn("At least one output", payload["error"]["message"])
        self.assertEqual(project_path.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
