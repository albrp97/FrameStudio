import configparser
import importlib
import os
import shutil
import subprocess
import sys
import time
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
    def test_desktop_launcher_runs_updated_checkout_without_terminal_or_reinstall(self):
        import gi

        gi.require_version("Gio", "2.0")
        from gi.repository import Gio

        repository = Path(__file__).resolve().parents[1]
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            home = root / "home space $ \" ' ` \\ %"
            checkout = root / "checkout space $ \" ' ` \\ %"
            checkout.mkdir()
            installer = checkout / "install.sh"
            shutil.copy2(repository / "install.sh", installer)
            environment = os.environ.copy()
            environment["HOME"] = str(home)
            environment["XDG_DATA_HOME"] = str(home / "app data")
            result = subprocess.run(
                [str(installer)], env=environment, capture_output=True, text=True, check=False
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            desktop_path = home / "app data/applications/io.github.framestudio.editor.desktop"
            application = Gio.DesktopAppInfo.new_from_filename(str(desktop_path))
            self.assertIsNotNone(application)
            self.assertEqual(application.get_name(), "FrameStudio")
            self.assertFalse(application.get_boolean("Terminal"))
            record = root / "launched.txt"
            for revision in ("first", "updated"):
                (checkout / "framestudio.py").write_text(
                    f"from pathlib import Path\nPath({str(record)!r}).write_text({revision!r})\n"
                )
                self.assertTrue(application.launch([], Gio.AppLaunchContext()))
                deadline = time.monotonic() + 5.0
                while time.monotonic() < deadline:
                    if record.exists() and record.read_text() == revision:
                        break
                    time.sleep(0.01)
                self.assertTrue(record.exists(), "Desktop application never ran")
                self.assertEqual(record.read_text(), revision)

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
            environment["XDG_DATA_HOME"] = str(home / "app data")
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
            desktop_path = home / "app data/applications/io.github.framestudio.editor.desktop"
            self.assertTrue(desktop_path.is_file())
            desktop = configparser.ConfigParser(interpolation=None)
            desktop.read(desktop_path)
            entry = desktop["Desktop Entry"]
            self.assertEqual(entry["Name"], "FrameStudio")
            self.assertEqual(entry["Terminal"], "false")
            self.assertIn(str(bin_directory / "framestudio"), entry["Exec"])
            self.assertNotIn("TryExec", entry)
