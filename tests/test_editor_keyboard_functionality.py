from __future__ import annotations

import os
import unittest
import uuid
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from framestudio.app import create_editor_application
from framestudio.media import probe_media
from framestudio.model import Project
from framestudio.persistence import load_project
from tests.test_editor_track_drag_functionality import _gtk_runtime, _make_video
from tests.test_phase010_functionality import _pump_events


class EditorKeyboardFunctionalityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.Gdk, _gio, cls.GLib, cls.Gtk = _gtk_runtime()
        if not cls.Gtk.init_check():
            raise unittest.SkipTest("GTK display is required")

    def setUp(self):
        self.temporary = TemporaryDirectory(prefix="framestudio-keyboard-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.environment = patch.dict(os.environ, XDG_STATE_HOME=str(self.root / "state"))
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.source = self.root / "source.mp4"
        _make_video(self.source, "blue", duration=4.0)
        self.source_bytes = self.source.read_bytes()
        self.application, factory = create_editor_application(
            application_id=f"io.github.framestudio.keyboard.a{uuid.uuid4().hex}"
        )
        self.assertTrue(self.application.register(None))
        self.window = factory(self.application)
        self.addCleanup(self.close_window)
        controllers = self.window.observe_controllers()
        self.keyboard = next(
            controllers.get_item(index)
            for index in range(controllers.get_n_items())
            if isinstance(controllers.get_item(index), self.Gtk.EventControllerKey)
        )

    def close_window(self):
        self.window.close()
        self.application.quit()
        _pump_events(self.GLib, 10)

    def attach(self, *, absolute=False, mixed=False):
        metadata = probe_media(self.source).metadata()
        if absolute:
            project = Project.create_synchronized_multi(((self.source, metadata),))
        elif mixed:
            other = self.root / "other.mp4"
            other.write_bytes(self.source.read_bytes())
            project = Project.create_multi(((self.source, metadata), (other, metadata)))
        else:
            project = Project.create(self.source, metadata)
        self.persisted_timeline = Project.from_dict(project.to_dict()).timeline.to_dict()
        self.window._attach_project(project, self.root / "edit.framestudio.json")
        self.window.grab_focus()
        _pump_events(self.GLib, 10)
        return project.timeline.to_dict()

    def key(self, keyval, modifiers=0):
        return self.keyboard.emit("key-pressed", keyval, 0, self.Gdk.ModifierType(modifiers))

    def test_arrows_seek_one_second_and_clamp_in_both_timing_modes(self):
        for absolute in (False, True):
            with self.subTest(absolute=absolute):
                self.attach(absolute=absolute)
                self.assertTrue(self.key(self.Gdk.KEY_Right))
                self.assertAlmostEqual(self.window.project.playhead_seconds, 1.0, places=5)
                self.assertTrue(self.key(self.Gdk.KEY_Left))
                self.assertAlmostEqual(self.window.project.playhead_seconds, 0.0, places=5)
                self.assertTrue(self.key(self.Gdk.KEY_Left))
                self.assertEqual(self.window.project.playhead_seconds, 0.0)
                self.window._seek_timeline(3.75)
                self.assertTrue(self.key(self.Gdk.KEY_Right))
                self.assertAlmostEqual(
                    self.window.project.playhead_seconds, 4.0 - 1.0 / 12.0, places=5
                )
                self.assertIsNone(self.window.controller.snapshot().error)

    def test_b_splits_undo_with_control_and_super_and_persist_exact_timeline(self):
        for absolute, mixed in ((False, False), (False, True), (True, False)):
            with self.subTest(absolute=absolute, mixed=mixed):
                before = self.attach(absolute=absolute, mixed=mixed)
                selection = self.window.selected_segment_ids
                focus = self.window.selected_segment_id
                for position in (1.0, 2.0):
                    self.window._seek_timeline(position)
                    self.assertTrue(self.key(self.Gdk.KEY_b))
                self.assertEqual(len(self.window.project.timeline.segment_items), 4 if mixed else 3)
                for modifier in (
                    self.Gdk.ModifierType.CONTROL_MASK,
                    self.Gdk.ModifierType.SUPER_MASK,
                ):
                    self.assertTrue(self.key(self.Gdk.KEY_z, modifier))
                self.assertEqual(self.window.project.timeline.to_dict(), before)
                self.assertEqual(self.window.selected_segment_ids, selection)
                self.assertEqual(self.window.selected_segment_id, focus)
                self.window._on_save_clicked(None)
                reopened = load_project(self.root / "edit.framestudio.json")
                self.assertEqual(reopened.timeline.to_dict(), self.persisted_timeline)
                self.assertEqual(self.source.read_bytes(), self.source_bytes)

    def test_split_undo_does_not_swallow_text_entry_or_undo_across_projects(self):
        self.attach()
        self.window._seek_timeline(1.0)
        self.key(self.Gdk.KEY_b)
        self.window.focus_zoom_spin.grab_focus()
        self.assertFalse(self.key(self.Gdk.KEY_z, self.Gdk.ModifierType.CONTROL_MASK))
        before = self.attach()
        self.key(self.Gdk.KEY_z, self.Gdk.ModifierType.SUPER_MASK)
        self.assertEqual(self.window.project.timeline.to_dict(), before)

    def test_undo_is_locked_during_export_and_other_edits_invalidate_splits(self):
        self.attach(absolute=True)
        self.window._seek_timeline(1.0)
        self.key(self.Gdk.KEY_b)
        split_timeline = self.window.project.timeline.to_dict()
        self.window._export_in_progress = True
        self.assertTrue(self.key(self.Gdk.KEY_z, self.Gdk.ModifierType.CONTROL_MASK))
        self.assertEqual(self.window.project.timeline.to_dict(), split_timeline)
        self.window._export_in_progress = False
        self.key(self.Gdk.KEY_Delete)
        edited = self.window.project.timeline.to_dict()
        self.key(self.Gdk.KEY_z, self.Gdk.ModifierType.CONTROL_MASK)
        self.assertEqual(self.window.project.timeline.to_dict(), edited)
        self.assertIn("No split or removal", self.window.status_label.get_text())

    def test_control_z_undoes_removal_and_shift_z_does_not_undo_split(self):
        before = self.attach(absolute=True)
        self.window._seek_timeline(1.0)
        self.key(self.Gdk.KEY_b)
        split_timeline = self.window.project.timeline.to_dict()
        self.assertFalse(
            self.key(
                self.Gdk.KEY_Z,
                self.Gdk.ModifierType.CONTROL_MASK | self.Gdk.ModifierType.SHIFT_MASK,
            )
        )
        self.assertEqual(self.window.project.timeline.to_dict(), split_timeline)
        self.key(self.Gdk.KEY_BackSpace)
        self.assertEqual(len(self.window.project.timeline.segment_items), 1)
        self.key(self.Gdk.KEY_z, self.Gdk.ModifierType.CONTROL_MASK)
        self.assertEqual(self.window.project.timeline.to_dict(), split_timeline)
        self.assertNotEqual(self.window.project.timeline.to_dict(), before)

    def test_split_history_is_bounded_and_a_rejected_split_keeps_history(self):
        self.attach(absolute=True)
        for index in range(1, 22):
            self.window._seek_timeline(index / 10.0)
            self.key(self.Gdk.KEY_b)
        self.assertEqual(len(self.window._split_history), 20)
        self.assertEqual(len(self.window.project.timeline.segment_items), 22)
        self.key(self.Gdk.KEY_b)
        self.assertEqual(len(self.window._split_history), 20)
        for _ in range(20):
            self.key(self.Gdk.KEY_z, self.Gdk.ModifierType.CONTROL_MASK)
        self.assertEqual(len(self.window.project.timeline.segment_items), 2)
        self.assertEqual(len(self.window._split_history), 0)
        before = self.window.project.timeline.to_dict()
        self.key(self.Gdk.KEY_z, self.Gdk.ModifierType.CONTROL_MASK)
        self.assertEqual(self.window.project.timeline.to_dict(), before)
