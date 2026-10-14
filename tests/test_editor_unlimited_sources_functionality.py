import shutil
import subprocess
import time
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

from framestudio.app import create_editor_application
from framestudio.persistence import load_autosave, load_project


class UnlimitedSourcesFunctionalityTests(unittest.TestCase):
    def test_gui_import_append_save_and_reopen_above_32_sources(self):
        import gi

        gi.require_version("Gtk", "4.0")
        from gi.repository import Gio, GLib, Gtk

        self.assertTrue(Gtk.init_check(), "GTK display is required")
        with TemporaryDirectory(prefix="framestudio-unlimited-sources-") as temporary:
            root = Path(temporary)
            with patch.dict("os.environ", {"XDG_STATE_HOME": str(root / "state")}):
                fixture = root / "fixture.mp4"
                subprocess.run(
                    [
                        "ffmpeg",
                        "-hide_banner",
                        "-loglevel",
                        "error",
                        "-f",
                        "lavfi",
                        "-i",
                        "color=c=blue:s=64x64:r=10:d=0.2",
                        "-c:v",
                        "libx264",
                        "-pix_fmt",
                        "yuv420p",
                        str(fixture),
                    ],
                    check=True,
                    capture_output=True,
                )
                original_bytes = fixture.read_bytes()
                paths = tuple(root / f"clip-{index:03d}.mp4" for index in range(66))
                for path in paths:
                    shutil.copyfile(fixture, path)
                application, window_factory = create_editor_application()
                application.set_application_id(
                    f"io.github.framestudio.editor.test_{root.name.replace('-', '_')}"
                )
                application.set_flags(application.get_flags() | Gio.ApplicationFlags.NON_UNIQUE)
                self.assertTrue(application.register(None))
                window = window_factory(application)
                try:
                    self._select_files(window, paths[:40], Gio)
                    self._wait_for_load(window, GLib, 40)
                    self.assertEqual(
                        {Path(source.path) for source in window.project.sources},
                        set(paths[:40]),
                    )
                    original_blocks = tuple(window.project.timeline.blocks)
                    self._select_files(window, paths[40:65], Gio)
                    self._wait_for_load(window, GLib, 65)
                    self.assertEqual(
                        tuple(window.project.timeline.blocks[:40]),
                        original_blocks,
                    )
                    self.assertEqual(
                        {Path(source.path) for source in window.project.sources},
                        set(paths[:65]),
                    )
                    self.assertEqual(len(window.project.timeline.blocks), 65)
                    self.assertEqual(len(load_autosave().sources), 65)
                    self._select_files(window, paths[65:], Gio)
                    self._wait_for_load(window, GLib, 66)
                    self.assertEqual(Path(window.project.sources[-1].path), paths[-1])
                    project_path = root / "large.framestudio.json"
                    window._save_to(project_path)
                    persisted = load_project(project_path)
                    self.assertEqual(len(persisted.sources), 66)
                    window._load_project_path(project_path)
                    self.assertEqual(window.project.to_dict(), persisted.to_dict())
                    self.assertNotIn("Error:", window.status_label.get_text())
                    self._select_files(window, (paths[0], paths[0]), Gio)
                    self.assertIn("only be added once", window.status_label.get_text())
                    self.assertEqual(window.project.to_dict(), persisted.to_dict())
                    self.assertFalse(window._source_load_in_progress)
                    for path in paths:
                        self.assertEqual(path.read_bytes(), original_bytes)
                finally:
                    window.close()
                    application.quit()

    @staticmethod
    def _select_files(window, paths, gio):
        selected_files = gio.ListStore.new(gio.File)
        for path in paths:
            selected_files.append(gio.File.new_for_path(str(path)))
        dialog = SimpleNamespace(open_multiple_finish=lambda _result: selected_files)
        window._on_source_dialog_done(dialog, None, None)

    def _wait_for_load(self, window, glib, expected_count):
        deadline = time.monotonic() + 30
        context = glib.MainContext.default()
        while time.monotonic() < deadline:
            if context.pending():
                context.iteration(False)
            if (
                window.project is not None
                and len(window.project.sources) == expected_count
                and not window._source_load_in_progress
            ):
                return
            if not window._source_load_in_progress:
                self.fail(window.status_label.get_text())
            time.sleep(0.01)
        self.fail(f"Expected {expected_count} sources; status={window.status_label.get_text()!r}")
