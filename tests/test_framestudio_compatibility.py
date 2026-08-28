import importlib
import os
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from framestudio.export_naming import LEGACY_PROJECT_SUFFIX, PROJECT_SUFFIX
from framestudio.model import Project
from framestudio.persistence import load_project, save_project
from framestudio_media import (
    FAST_VIDEO_SUFFIX,
    GENERATED_SUFFIXES,
    LEGACY_FAST_VIDEO_SUFFIX,
)


class FrameStudioCompatibilityTests(unittest.TestCase):
    def test_legacy_editor_namespace_forwards_to_canonical_modules(self):
        importlib.import_module("resolve_editor")

        for module_name in (
            "app",
            "cli",
            "export",
            "model",
            "persistence",
            "preview_strategy",
        ):
            self.assertIs(
                importlib.import_module(f"resolve_editor.{module_name}"),
                importlib.import_module(f"framestudio.{module_name}"),
            )

    def test_legacy_script_modules_forward_to_canonical_modules(self):
        for legacy_name, canonical_name in (
            ("resolve_media", "framestudio_media"),
            ("resolve_concat", "framestudio_concat"),
            ("resolve_fps", "framestudio_fps"),
        ):
            self.assertIs(
                importlib.import_module(legacy_name),
                importlib.import_module(canonical_name),
            )

    def test_legacy_project_suffix_remains_loadable(self):
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
                    "audio_codec": None,
                    "format_name": "mp4",
                },
            )
            legacy_path = root / f"edit{LEGACY_PROJECT_SUFFIX}"

            save_project(project, legacy_path)

            self.assertEqual(load_project(legacy_path).project_id, project.project_id)
            self.assertEqual(PROJECT_SUFFIX, ".framestudio.json")

    def test_new_media_outputs_use_framestudio_and_legacy_outputs_are_recognized(self):
        self.assertEqual(FAST_VIDEO_SUFFIX, ".framestudio-ready.mxf")
        self.assertIn(LEGACY_FAST_VIDEO_SUFFIX, GENERATED_SUFFIXES)

    def test_media_tui_uses_framestudio_name_with_legacy_class_alias(self):
        media = importlib.import_module("framestudio_media")
        self.assertIs(media.ResolveTUI, media.FrameStudioTUI)

    def test_canonical_and_legacy_entrypoints_report_framestudio(self):
        for script in ("framestudio.py", "resolve_editor.py"):
            result = subprocess.run(
                [sys.executable, script, "--version"],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("framestudio", result.stdout.casefold())

    def test_global_workflow_subcommands_forward_to_canonical_modules(self):
        from framestudio.entrypoint import main

        for command, module_name in (
            ("media", "framestudio_media"),
            ("concat", "framestudio_concat"),
            ("fps", "framestudio_fps"),
        ):
            with self.subTest(command=command):
                module = importlib.import_module(module_name)
                with patch.object(module, "main", return_value=23) as workflow_main:
                    self.assertEqual(main([command, "--dry-run"]), 23)
                    workflow_main.assert_called_once_with(
                        ["--dry-run"],
                        prog=f"framestudio {command}",
                    )

    def test_global_workflow_help_uses_framestudio_command_name(self):
        environment = os.environ.copy()
        environment.pop("FORCE_COLOR", None)
        for command in ("media", "concat", "fps"):
            with self.subTest(command=command):
                result = subprocess.run(
                    [sys.executable, "framestudio.py", command, "--help"],
                    env=environment,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn(f"usage: framestudio {command}", result.stdout)

    def test_global_editor_help_uses_framestudio_command_name(self):
        environment = os.environ.copy()
        environment.pop("FORCE_COLOR", None)
        result = subprocess.run(
            [sys.executable, "framestudio.py", "--help"],
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("usage: framestudio ", result.stdout)

    def test_install_creates_only_the_unified_global_command(self):
        obsolete_names = (
            "framestudio-media",
            "framestudio-concat",
            "framestudio-fps",
            "framestudio-editor",
            "resolve-editor",
            "resolve-media",
            "resolve-concat",
            "resolve-fps",
        )
        repository = Path(__file__).resolve().parents[1]
        with TemporaryDirectory() as temporary_directory:
            home = Path(temporary_directory)
            bin_directory = home / "bin"
            bin_directory.mkdir()
            for name in obsolete_names:
                (bin_directory / name).write_text("obsolete\n")

            environment = os.environ.copy()
            environment["HOME"] = str(home)
            result = subprocess.run(
                [str(repository / "install.sh")],
                cwd=repository,
                env=environment,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(
                {path.name for path in bin_directory.iterdir()},
                {"framestudio"},
            )
            version = subprocess.run(
                [str(bin_directory / "framestudio"), "--version"],
                cwd=Path("/"),
                env=environment,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(version.returncode, 0, version.stderr)
            self.assertIn("framestudio", version.stdout.casefold())
