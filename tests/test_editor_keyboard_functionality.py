from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
import unittest
import uuid
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from framestudio.app import create_editor_application
from framestudio.media import probe_media
from framestudio.model import Project
from framestudio.persistence import load_project
from tests.test_editor_track_drag_functionality import (
    _gtk_runtime,
    _make_video,
    _screen_coordinates,
)
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

    def test_playback_selection_follows_segment_boundary_and_paused_seek(self):
        for absolute in (False, True):
            with self.subTest(absolute=absolute):
                self.attach(absolute=absolute)
                self.window._seek_timeline(1.0)
                self.key(self.Gdk.KEY_b)
                first, second = self.window.project.timeline.segment_items
                self.window._seek_timeline(0.5)
                self.assertEqual(self.window.selected_segment_id, first.segment_id)
                self.window._on_play_clicked(None)
                deadline = time.monotonic() + 8
                while time.monotonic() < deadline:
                    _pump_events(self.GLib, 1)
                    if self.window.project.playhead_seconds >= 1.25:
                        break
                self.assertGreaterEqual(self.window.project.playhead_seconds, 1.25)
                self.assertEqual(self.window.selected_segment_id, second.segment_id)
                self.assertEqual(
                    self.window.timeline_canvas.get_selected_segment_ids(), (second.segment_id,)
                )
                self.window._on_play_clicked(None)
                self.window._seek_timeline(0.25)
                self.assertEqual(self.window.selected_segment_id, first.segment_id)
                self.assertEqual(self.source.read_bytes(), self.source_bytes)

    def test_paused_deleted_clip_stays_selected_until_playback_resumes(self):
        self.attach()
        self.window._seek_timeline(1.0)
        self.key(self.Gdk.KEY_b)
        first, second = self.window.project.timeline.segment_items
        self.key(self.Gdk.KEY_Delete)
        self.window._seek_timeline(0.25)
        self.assertEqual(self.window.selected_segment_id, second.segment_id)
        self.assertLess(self.window.project.playhead_seconds, 1.0)
        self.window._on_play_clicked(None)
        self.assertEqual(self.window.selected_segment_id, first.segment_id)
        self.window._on_play_clicked(None)

    def test_real_pointer_click_in_shaded_start_snaps_and_outside_seeks_normally(self):
        display = self.Gdk.Display.get_default()
        if "x11" not in type(display).__name__.lower() or shutil.which("xdotool") is None:
            self.skipTest("Real pointer coverage requires X11 and xdotool")
        for absolute in (False, True):
            for zoom in (1.0, 12.0, 461.32):
                with self.subTest(absolute=absolute, zoom=zoom):
                    self._check_real_pointer_snapping(absolute=absolute, zoom=zoom)

    def test_real_pointer_click_with_small_hand_movement_still_snaps_at_extreme_zoom(self):
        display = self.Gdk.Display.get_default()
        if "x11" not in type(display).__name__.lower() or shutil.which("xdotool") is None:
            self.skipTest("Real pointer coverage requires X11 and xdotool")
        for absolute in (False, True):
            with self.subTest(absolute=absolute):
                self._check_real_pointer_snapping(absolute=absolute, zoom=461.32, jitter=3)

    def test_native_wayland_badge_snapping_and_control_click_bulk_selection(self):
        if (
            "wayland" not in type(self.Gdk.Display.get_default()).__name__.lower()
            or not os.environ.get("YDOTOOL_SOCKET")
            or shutil.which("ydotool") is None
            or shutil.which("hyprctl") is None
        ):
            self.skipTest("Native pointer coverage requires Wayland, Hyprland and a ydotool socket")

        def command(*arguments):
            return subprocess.run(
                arguments, capture_output=True, text=True, check=True, timeout=10
            ).stdout

        def move_pointer(x, y):
            canvas = self.window.timeline_canvas
            relative = canvas.translate_coordinates(self.window, x, y)
            clients = json.loads(command("hyprctl", "clients", "-j"))
            client = next(item for item in clients if item["title"] == self.window.get_title())
            target_x = round(client["at"][0] + relative[0])
            target_y = round(client["at"][1] + relative[1])
            for _ in range(50):
                cursor = json.loads(command("hyprctl", "cursorpos", "-j"))
                delta_x, delta_y = target_x - cursor["x"], target_y - cursor["y"]
                if abs(delta_x) <= 1 and abs(delta_y) <= 1:
                    break
                step_x = int(delta_x / 2) or (1 if delta_x > 0 else -1 if delta_x < 0 else 0)
                step_y = int(delta_y / 2) or (1 if delta_y > 0 else -1 if delta_y < 0 else 0)
                command("ydotool", "mousemove", "-x", str(step_x), "-y", str(step_y))
                _pump_events(self.GLib, 1)
            else:
                self.fail(
                    f"Native pointer could not reach clip at {(target_x, target_y)}; "
                    f"last cursor was {(cursor['x'], cursor['y'])}"
                )

        def click_clip(segment_id, *, badge=False, control=False):
            canvas = self.window.timeline_canvas
            for _ in range(10):
                clip = next(item for item in canvas._layout() if item.segment_id == segment_id)
                self.window.timeline_viewport.get_hadjustment().set_value(max(0, clip.x - 80))
                canvas.queue_draw()
                _pump_events(self.GLib, 10)
                clip = next(item for item in canvas._layout() if item.segment_id == segment_id)
                relative = canvas.translate_coordinates(self.window, clip.x + 8, clip.y + 14)
                if 0 <= relative[0] < self.window.get_width():
                    break
            else:
                self.fail("GTK did not bring the requested clip into the visible viewport")
            move_pointer(clip.x + 8, clip.y - 4 if badge else clip.y + 14)
            if control:
                command("ydotool", "key", "29:1")
            try:
                command("ydotool", "click", "0xC0")
                _pump_events(self.GLib, 20)
            finally:
                if control:
                    command("ydotool", "key", "29:0")
            return clip

        for absolute in (False, True):
            with self.subTest(absolute=absolute):
                self.attach(absolute=absolute)
                self.window.set_title(f"FrameStudio native pointer {uuid.uuid4().hex}")
                for position in (1.137, 2.137):
                    self.window._seek_timeline(position)
                    self.key(self.Gdk.KEY_b)
                first, second, third = self.window.project.timeline.segment_items
                self.window.timeline_canvas.set_zoom(461.32)
                _pump_events(self.GLib, 10)
                for badge in (False, True):
                    with self.subTest(badge=badge):
                        clip = click_clip(second.segment_id, badge=badge)
                        self.assertEqual(
                            self.window.timeline_canvas.get_playhead_seconds(),
                            clip.timeline_start_seconds,
                        )
                click_clip(first.segment_id)
                click_clip(second.segment_id, badge=True, control=True)
                self.assertEqual(
                    set(self.window.selected_segment_ids), {first.segment_id, second.segment_id}
                )
                if not absolute:
                    self.key(self.Gdk.KEY_Right, self.Gdk.ModifierType.SHIFT_MASK)
                    self.assertEqual(
                        tuple(
                            item.segment_id for item in self.window.project.timeline.segment_items
                        ),
                        (third.segment_id, first.segment_id, second.segment_id),
                    )
                    self.assertEqual(
                        set(self.window.selected_segment_ids),
                        {first.segment_id, second.segment_id},
                    )
                else:
                    self.window.project.timeline.add_track("track-2")
                    self.window._refresh_timeline()
                    canvas = self.window.timeline_canvas
                    canvas.set_zoom(1)
                    self.window.timeline_viewport.get_hadjustment().set_value(0)
                    _pump_events(self.GLib, 15)
                    clip = next(
                        item for item in canvas._layout() if item.segment_id == first.segment_id
                    )
                    x, y = clip.x + clip.width / 2, clip.y + clip.height / 2
                    target_y = canvas._layout_rows[1].y + 30
                    before_drag = self.window.project.timeline.to_dict()
                    move_pointer(x, y)
                    command("ydotool", "click", "0x40")
                    try:
                        _pump_events(self.GLib, 5)
                        move_pointer(x, target_y)
                        _pump_events(self.GLib, 10)
                        previews = canvas._clips_with_drag_preview(
                            canvas._layout(), canvas._layout_rows
                        )
                        self.assertEqual(
                            {
                                item.track_id
                                for item in previews
                                if item.segment_id in (first.segment_id, second.segment_id)
                            },
                            {"track-2"},
                        )
                        self.assertEqual(self.window.project.timeline.to_dict(), before_drag)
                        expected_placements = {
                            segment_id: start
                            for segment_id, start, _track_id in canvas._drag_placements
                        }
                    finally:
                        command("ydotool", "click", "0x80")
                    _pump_events(self.GLib, 20)
                    for original in (first, second):
                        moved = self.window.project.timeline.find(original.segment_id)
                        self.assertEqual(moved.track_id, "track-2")
                        self.assertEqual(
                            moved.timeline_start_ticks, expected_placements[original.segment_id]
                        )
                        self.assertEqual(moved.source_start_ticks, original.source_start_ticks)
                        self.assertEqual(moved.source_end_ticks, original.source_end_ticks)
                    self.assertEqual(
                        self.window.project.timeline.find(first.segment_id).timeline_start_ticks
                        - first.timeline_start_ticks,
                        self.window.project.timeline.find(second.segment_id).timeline_start_ticks
                        - second.timeline_start_ticks,
                    )
                    self.assertEqual(self.window.project.timeline.find(third.segment_id), third)
                    self.assertEqual(
                        set(self.window.selected_segment_ids),
                        {first.segment_id, second.segment_id},
                    )
                    destination = self.root / "grouped.framestudio.json"
                    self.window._save_to(destination)
                    self.assertEqual(
                        load_project(destination).timeline.to_dict(),
                        self.window.project.timeline.to_dict(),
                    )
                click_clip(third.segment_id, control=True)
                self.assertEqual(len(self.window.selected_segment_ids), 3)
                click_clip(first.segment_id, control=True)
                self.assertEqual(
                    set(self.window.selected_segment_ids), {second.segment_id, third.segment_id}
                )
                self.key(self.Gdk.KEY_Delete)
                self.assertFalse(self.window.project.timeline.find(first.segment_id).deleted)
                self.assertTrue(self.window.project.timeline.find(second.segment_id).deleted)
                self.assertTrue(self.window.project.timeline.find(third.segment_id).deleted)
                self.assertEqual(self.source.read_bytes(), self.source_bytes)

    def _check_real_pointer_snapping(self, *, absolute, zoom, jitter=0):
        self.attach(absolute=absolute)
        self.window._seek_timeline(2.137)
        self.key(self.Gdk.KEY_b)
        timeline_before = self.window.project.timeline.to_dict()
        canvas = self.window.timeline_canvas
        canvas.set_zoom(zoom)
        second_id = self.window.selected_segment_id
        self.window.set_title(f"FrameStudio snap {uuid.uuid4().hex}")
        _pump_events(self.GLib, 20)
        clip = next(item for item in canvas._layout() if item.segment_id == second_id)
        self.window.timeline_viewport.get_hadjustment().set_value(max(0, clip.x - 80))
        _pump_events(self.GLib, 10)

        def xdotool(*arguments):
            result = subprocess.run(
                ["xdotool", *arguments], capture_output=True, text=True, check=True, timeout=10
            )
            return result.stdout.strip()

        window_id = xdotool("search", "--onlyvisible", "--name", self.window.get_title())
        xdotool("windowfocus", "--sync", window_id)
        for inside, bypass in ((True, False), (False, False), (True, True)):
            clip = next(item for item in canvas._layout() if item.segment_id == second_id)
            self.window.timeline_viewport.get_hadjustment().set_value(max(0, clip.x - 80))
            _pump_events(self.GLib, 10)
            x = clip.x + (clip.snap_width / 2 if inside else clip.snap_width + 4)
            y = clip.y + clip.height / 2
            relative = canvas.translate_coordinates(self.window, x, y)
            self.assertGreater(relative[0], 0)
            self.assertLess(relative[0], self.window.get_width())
            point = _screen_coordinates(
                xdotool("getwindowgeometry", "--shell", window_id), relative
            )
            xdotool("mousemove", "--sync", str(point[0]), str(point[1]))
            if bypass:
                xdotool("keydown", "Super_L")
            try:
                if jitter:
                    xdotool("mousedown", "1")
                    _pump_events(self.GLib, 2)
                    xdotool("mousemove", "--sync", str(point[0] + jitter), str(point[1]))
                    _pump_events(self.GLib, 2)
                    xdotool("mouseup", "1")
                else:
                    xdotool("click", "1")
                _pump_events(self.GLib, 20)
            finally:
                if bypass:
                    xdotool("keyup", "Super_L")
            self.assertEqual(self.window.selected_segment_id, second_id)
            if inside and not bypass:
                self.assertEqual(self.window.project.playhead_seconds, clip.timeline_start_seconds)
                self.assertEqual(canvas.get_playhead_seconds(), clip.timeline_start_seconds)
            else:
                self.assertGreater(
                    self.window.project.playhead_seconds,
                    clip.timeline_start_seconds,
                    f"inside={inside}, bypass={bypass}, zoom={zoom}, absolute={absolute}",
                )
            self.assertEqual(self.window.project.timeline.to_dict(), timeline_before)
            self.assertEqual(self.source.read_bytes(), self.source_bytes)

    def test_selection_tracks_active_row_and_does_not_select_deleted_or_empty_intervals(self):
        self.attach(absolute=True)
        timeline = self.window.project.timeline
        first = timeline.segment_items[0]
        other_id = timeline.add_track("track-2")
        timeline.paste_blocks((first,), at_ticks=1_000_000, target_track_id=other_id)
        self.window._refresh_timeline()
        timeline = self.window.project.timeline
        other = timeline.track_by_id(other_id).blocks[0]
        self.window._on_track_activated(other_id)
        self.window._seek_timeline(0.5)
        self.assertEqual(self.window.selected_segment_ids, ())
        self.window._seek_timeline(1.5)
        self.assertEqual(self.window.selected_segment_id, other.segment_id)
        self.window._on_track_activated("track-1")
        self.window._seek_timeline(1.5)
        self.assertEqual(self.window.selected_segment_id, first.segment_id)

    def test_playback_skips_deleted_middle_clip_and_selects_next_included_clip(self):
        self.attach()
        for position in (1, 2):
            self.window._seek_timeline(position)
            self.key(self.Gdk.KEY_b)
        first, deleted, last = self.window.project.timeline.segment_items
        self.window.timeline_canvas._select_clip(
            deleted.segment_id, additive=False, range_selection=False
        )
        self.key(self.Gdk.KEY_Delete)
        self.window._seek_timeline(0.75)
        self.assertEqual(self.window.selected_segment_id, deleted.segment_id)
        self.window._on_play_clicked(None)
        self.assertEqual(self.window.selected_segment_id, first.segment_id)
        deadline = time.monotonic() + 8
        while time.monotonic() < deadline:
            _pump_events(self.GLib, 1)
            if self.window.project.playhead_seconds >= 2.25:
                break
        self.assertGreaterEqual(self.window.project.playhead_seconds, 2.25)
        self.assertEqual(self.window.selected_segment_id, last.segment_id)
        self.window._on_play_clicked(None)
        self.assertTrue(self.window.project.timeline.find(deleted.segment_id).deleted)
