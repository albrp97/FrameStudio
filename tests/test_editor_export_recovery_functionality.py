import hashlib
import json
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace

from framestudio.export_journal import journal_path
from framestudio.media import probe_media
from framestudio.model import Project
from framestudio.persistence import save_project
from tests.test_editor_source_outputs_functionality import _make_constant_source


class ExportRecoveryFunctionalityTests(unittest.TestCase):
    def test_gtk_displays_distinct_overall_and_current_operation_bars(self):
        import gi

        gi.require_version("Gtk", "4.0")
        from gi.repository import Gtk

        from framestudio.app_export import update_export_progress
        from framestudio.export_types import ExportProgress

        if not Gtk.init_check():
            self.skipTest("GTK display is unavailable")
        window = SimpleNamespace(
            export_progress_bar=Gtk.ProgressBar(),
            export_current_progress_bar=Gtk.ProgressBar(),
            export_progress_label=Gtk.Label(),
        )
        update_export_progress(
            window,
            ExportProgress(
                stage="interpolation",
                percent=80,
                frame=63,
                total_frames=100,
                fps=10,
                elapsed_seconds=2,
                eta_seconds=1,
                overall_percent=40,
                overall_elapsed_seconds=125,
                overall_eta_seconds=35,
                current_percent=63,
                output_index=2,
                output_count=3,
            ),
        )
        self.assertAlmostEqual(window.export_progress_bar.get_fraction(), 0.4)
        self.assertAlmostEqual(window.export_current_progress_bar.get_fraction(), 0.63)
        self.assertEqual(
            window.export_progress_bar.get_text(),
            "Overall 40.0% | elapsed 02:05 | ETA 00:35",
        )
        self.assertEqual(window.export_current_progress_bar.get_text(), "Current operation 63.0%")
        self.assertIn("Output 2/3", window.export_progress_label.get_text())

    def test_real_combined_cli_export_has_global_and_local_progress_and_cleans_journal(self):
        with TemporaryDirectory(prefix="framestudio-global-progress-") as directory:
            root = Path(directory)
            source = root / "input.mp4"
            _make_constant_source(
                source,
                color="red",
                frame_rate=30,
                width=320,
                height=180,
                frequencies=(440, 880),
                duration=0.5,
            )
            original = hashlib.sha256(source.read_bytes()).hexdigest()
            project = Project.create_synchronized_multi(((source, probe_media(source).metadata()),))
            project_path = root / "edit.framestudio.json"
            save_project(project, project_path)
            destination = root / "output.mp4"
            result = subprocess.run(
                [
                    sys.executable,
                    "framestudio.py",
                    "export",
                    str(project_path),
                    "--output",
                    str(destination),
                    "--output-mode",
                    "combined",
                    "--no-enhance-fps",
                    "--no-upscale-enhancement",
                    "--human-progress",
                ],
                capture_output=True,
                text=True,
                timeout=90,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            events = [json.loads(line) for line in result.stdout.splitlines()]
            updates = [event["progress"] for event in events if event.get("event") == "progress"]
            percentages = [update["overall_percent"] for update in updates]
            self.assertEqual(percentages, sorted(percentages))
            self.assertEqual(percentages[-1], 100)
            self.assertTrue(all(p < 100 for p in percentages[:-1]))
            self.assertTrue(all(p["current_percent"] is not None for p in updates))
            self.assertEqual(max(p["output_count"] for p in updates), 2)
            self.assertIn("Overall ", result.stderr)
            self.assertIn("current ", result.stderr)
            self.assertEqual(result.stderr.count("Export complete."), 1)
            outputs = events[-1]["export"]["results"]
            self.assertEqual(len(outputs), 2)
            self.assertTrue(all(item["verified"] for item in outputs))
            self.assertFalse(journal_path(destination).exists())
            self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), original)
            self.assertAlmostEqual(probe_media(destination).duration_seconds, 0.5, delta=0.1)
