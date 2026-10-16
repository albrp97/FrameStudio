from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import unittest
import uuid
from pathlib import Path
from typing import Any

from framestudio.composition import TriplicateGroup, VisualTransform
from framestudio.media import probe_media
from framestudio.model import Project
from framestudio.persistence import load_project, save_project
from framestudio.timeline import layout_timeline_segments, layout_timeline_tracks
from tests.test_editor_ripple_removal import _block, isolated_directory
from tests.test_editor_ripple_removal_functionality import _make_media, _sha256
from tests.test_editor_track_drag_functionality import _gtk_runtime, _screen_coordinates
from tests.test_phase010_functionality import _pump_events

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
FFMPEG = shutil.which("ffmpeg")
FFPROBE = shutil.which("ffprobe")
XDOTool = shutil.which("xdotool")


def _generated_removal_project(root: Path) -> tuple[Project, Path, Path]:
    source_a = _make_media(
        root,
        "ticket111-source-a.mp4",
        "testsrc=size=320x180",
        3.0,
    )
    source_b = _make_media(
        root,
        "ticket111-source-b.mp4",
        "color=c=blue:size=640x360",
        3.0,
    )
    project = Project.create_synchronized_multi(
        (
            (source_a, probe_media(source_a).metadata()),
            (source_b, probe_media(source_b).metadata()),
        ),
        project_id="ticket111-removal-controls",
    )
    timeline = project.timeline
    timeline.add_track("track-2")
    source_a_id = project.sources[0].source_id
    source_b_id = project.sources[1].source_id
    surviving_transform = VisualTransform(zoom=1.35, offset_x=24.0, offset_y=-12.0)
    excluded_transform = VisualTransform(zoom=1.6, offset_x=-30.0, offset_y=15.0)
    surviving_triplicate = TriplicateGroup.create(
        surviving_transform,
        group_id="ticket111-surviving-triplicate",
    )
    removed_triplicate = TriplicateGroup.create(
        excluded_transform,
        group_id="ticket111-removed-triplicate",
    )
    excluded_triplicate = TriplicateGroup.create(
        excluded_transform,
        group_id="ticket111-excluded-triplicate",
    )
    timeline.replace_track_blocks(
        "track-1",
        (
            _block(
                "a",
                source_a_id,
                0,
                1_000_000,
                0,
                1_000_000,
                "track-1",
                color_index=0,
                state={"role": "survivor-a", "opaque": {"values": [1, 2]}},
                transform=surviving_transform,
                triplicate=surviving_triplicate,
            ),
            _block(
                "b",
                source_a_id,
                1_000_000,
                2_000_000,
                2_000_000,
                3_000_000,
                "track-1",
                color_index=1,
                state={"role": "remove-b", "opaque": {"values": ["before"]}},
                transform=excluded_transform,
                triplicate=removed_triplicate,
            ),
            _block(
                "c",
                source_a_id,
                2_000_000,
                3_000_000,
                4_000_000,
                5_000_000,
                "track-1",
                deleted=True,
                color_index=2,
                state={"role": "excluded-c", "opaque": {"values": ["keep"]}},
                transform=excluded_transform,
                triplicate=excluded_triplicate,
            ),
        ),
    )
    timeline.replace_track_blocks(
        "track-2",
        (
            _block(
                "independent",
                source_b_id,
                0,
                1_000_000,
                1_000_000,
                2_000_000,
                "track-2",
                color_index=3,
                state={"role": "independent-track"},
                transform=surviving_transform,
            ),
        ),
    )
    project.set_playhead(4.5)
    timeline.validate()
    return project, source_a, source_b


def _run_cli_process(*arguments: str) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            [sys.executable, "framestudio.py", *arguments],
            cwd=REPOSITORY_ROOT,
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
    except subprocess.TimeoutExpired as error:
        raise AssertionError(
            f"public CLI removal command hung after 30 seconds: {arguments!r}",
        ) from error


class EditorRemovalControlsFunctionalityTests(unittest.TestCase):
    def _assert_media_tools(self) -> None:
        self.assertIsNotNone(FFMPEG, "ffmpeg is required for TICKET-111 media preflight")
        self.assertIsNotNone(FFPROBE, "ffprobe is required for TICKET-111 media preflight")

    def test_generated_media_fixture_preflight_is_independent_of_removal_controls(self):
        self._assert_media_tools()
        with isolated_directory() as root:
            project, source_a, source_b = _generated_removal_project(root)
            project_path = root / "preflight.framestudio.json"
            source_hashes = {
                source_a: _sha256(source_a),
                source_b: _sha256(source_b),
            }

            self.assertGreater(probe_media(source_a).duration_seconds, 2.0)
            self.assertGreater(probe_media(source_b).duration_seconds, 2.0)
            project.timeline.validate()
            save_project(project, project_path)
            reopened = load_project(project_path)

            self.assertEqual(reopened.timeline.to_dict(), project.timeline.to_dict())
            self.assertEqual(_sha256(source_a), source_hashes[source_a])
            self.assertEqual(_sha256(source_b), source_hashes[source_b])

    def test_public_cli_removal_persists_reopens_and_reports_invalid_inputs(self):
        self._assert_media_tools()
        with isolated_directory() as root:
            project, source_a, source_b = _generated_removal_project(root)
            project_path = root / "cli-input.framestudio.json"
            output_path = root / "cli-removed.framestudio.json"
            save_project(project, project_path)
            source_hashes = {
                source_a: _sha256(source_a),
                source_b: _sha256(source_b),
            }

            result = _run_cli_process(
                "remove",
                str(project_path),
                "--segment",
                "b",
                "--output",
                str(output_path),
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stderr, "")
            payload: dict[str, Any] = json.loads(result.stdout)
            self.assertTrue(payload["ok"])
            self.assertEqual(payload["command"], "remove")
            self.assertEqual(payload["operation"]["removed_segment_ids"], ["b"])
            self.assertNotIn("receipt", payload["operation"])
            self.assertNotIn("undo_token", payload["operation"])
            self.assertTrue(output_path.is_file())

            reopened = load_project(output_path)
            self.assertNotIn("b", {block.segment_id for block in reopened.timeline.blocks})
            self.assertEqual(
                reopened.timeline.find("c").timeline_start_ticks,
                3_000_000,
            )
            self.assertEqual(
                reopened.timeline.find("independent").timeline_start_ticks,
                1_000_000,
            )
            self.assertEqual(
                reopened.timeline.find("a").visual_transform,
                project.timeline.find("a").visual_transform,
            )
            self.assertEqual(
                reopened.timeline.find("c").deleted,
                project.timeline.find("c").deleted,
            )
            self.assertEqual(_sha256(source_a), source_hashes[source_a])
            self.assertEqual(_sha256(source_b), source_hashes[source_b])

            before_invalid = project_path.read_bytes()
            invalid_id = _run_cli_process(
                "remove",
                str(project_path),
                "--segment",
                "does-not-exist",
            )
            self.assertNotEqual(invalid_id.returncode, 0)
            invalid_id_error: dict[str, Any] = json.loads(invalid_id.stderr)
            self.assertEqual(invalid_id_error["error"]["code"], "invalid_operation")
            self.assertEqual(project_path.read_bytes(), before_invalid)

            invalid_project = root / "invalid.framestudio.json"
            invalid_project.write_text("{not-json", encoding="utf-8")
            invalid_file = _run_cli_process(
                "remove",
                str(invalid_project),
                "--segment",
                "b",
            )
            self.assertNotEqual(invalid_file.returncode, 0)
            invalid_file_error: dict[str, Any] = json.loads(invalid_file.stderr)
            self.assertIn(
                invalid_file_error["error"]["code"],
                {"invalid_project", "project_io", "invalid_json"},
            )


class NativeRemovalControlsFunctionalityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        Gdk, Gio, GLib, Gtk = _gtk_runtime()
        if not Gtk.init_check():
            raise AssertionError("GTK 4 could not initialize on the TICKET-111 test display")
        display = Gdk.Display.get_default()
        cls.Gdk = Gdk
        cls.Gio = Gio
        cls.GLib = GLib
        cls.Gtk = Gtk
        cls.display_name = "" if display is None else display.get_name()
        cls.display_backend = "" if display is None else type(display).__name__
        if "x11" not in f"{cls.display_name} {cls.display_backend}".lower():
            raise AssertionError(
                "TICKET-111 requires an X11 display for physical XTest keyboard events; "
                f"got {cls.display_name or 'unknown'} / {cls.display_backend or 'unknown'}",
            )
        if XDOTool is None:
            raise AssertionError("xdotool is required for physical XTest keyboard events")

    def setUp(self) -> None:
        self._assert_media_tools()
        self.runtime_context = isolated_directory()
        self.root = self.runtime_context.__enter__()
        self.addCleanup(self._close_runtime)
        self.state_root = self.root / "xdg-state"
        self.state_root.mkdir()
        self.previous_xdg_state_home = os.environ.get("XDG_STATE_HOME")
        os.environ["XDG_STATE_HOME"] = str(self.state_root)
        self.addCleanup(self._restore_xdg_state_home)
        self.project, self.source_a, self.source_b = _generated_removal_project(self.root)
        self.project_path = self.root / "gtk-input.framestudio.json"
        save_project(self.project, self.project_path)
        self.source_hashes = {
            self.source_a: _sha256(self.source_a),
            self.source_b: _sha256(self.source_b),
        }
        self.application = None
        self.window = None

    def _assert_media_tools(self) -> None:
        self.assertIsNotNone(FFMPEG, "ffmpeg is required for TICKET-111 GTK media")
        self.assertIsNotNone(FFPROBE, "ffprobe is required for TICKET-111 GTK media")

    def _restore_xdg_state_home(self) -> None:
        if self.previous_xdg_state_home is None:
            os.environ.pop("XDG_STATE_HOME", None)
        else:
            os.environ["XDG_STATE_HOME"] = self.previous_xdg_state_home

    def _close_runtime(self) -> None:
        if self.window is not None:
            planner = getattr(self.window, "export_planning_window", None)
            if planner is not None:
                planner.close()
        if self.window is not None:
            self.window.close()
        if self.application is not None:
            self.application.quit()
        self.runtime_context.__exit__(None, None, None)

    def _wait_until(self, predicate, message: str, rounds: int = 500) -> None:
        for _ in range(rounds):
            _pump_events(self.GLib, 1)
            if predicate():
                return
        status = ""
        if self.window is not None and hasattr(self.window, "status_label"):
            status = self.window.status_label.get_text()
        raise AssertionError(f"{message}; status={status!r}")

    def _open_window(self, *, source_path: Path | None = None) -> Any:
        from framestudio.app import create_editor_application

        application_id = f"io.github.framestudio.ticket111.a{uuid.uuid4().hex}"
        self.window_title = f"FrameStudio T111 {uuid.uuid4().hex}"
        self.application, factory = create_editor_application(
            project_path=self.project_path if source_path is None else None,
            source_path=source_path,
            application_id=application_id,
        )
        self.assertTrue(self.application.register(None))
        self.window = factory(self.application)
        self.window.set_title(self.window_title)
        self.window.present()
        self._wait_until(
            lambda: self.window.project is not None and not self.window._source_load_in_progress,
            "production GTK project load did not complete",
        )
        if source_path is None:
            self.assertEqual(self.window.project.timeline.timing_mode, "absolute")
        return self.window

    def _xdotool(self, *arguments: str) -> str:
        assert XDOTool is not None
        try:
            result = subprocess.run(
                [XDOTool, *arguments],
                cwd=REPOSITORY_ROOT,
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
            )
        except subprocess.TimeoutExpired as error:
            raise AssertionError(f"xdotool hung: {' '.join(arguments)}") from error
        if result.returncode != 0:
            raise AssertionError(
                f"xdotool {' '.join(arguments)} failed: {result.stderr.strip()}",
            )
        return result.stdout

    def _window_id(self, title: str | None = None) -> str:
        output = self._xdotool(
            "search",
            "--onlyvisible",
            "--name",
            title or self.window_title,
        )
        window_ids = tuple(line.strip() for line in output.splitlines() if line.strip())
        self.assertEqual(
            len(window_ids),
            1,
            f"expected one uniquely titled TICKET-111 window, found {window_ids!r}",
        )
        return window_ids[0]

    def _screen_point(
        self,
        widget: Any,
        x: float,
        y: float,
        *,
        target_window: Any | None = None,
        window_title: str | None = None,
    ) -> tuple[int, int]:
        native = target_window or self.window
        relative = widget.translate_coordinates(native, x, y)
        self.assertIsNotNone(relative)
        geometry = self._xdotool(
            "getwindowgeometry",
            "--shell",
            self._window_id(window_title),
        )
        return _screen_coordinates(
            geometry, relative, surface_transform=native.get_surface_transform()
        )

    def _physical_click(
        self,
        widget: Any,
        x: float,
        y: float,
        *,
        target_window: Any | None = None,
        window_title: str | None = None,
        control: bool = False,
    ) -> None:
        window_id = self._window_id(window_title)
        self._xdotool("windowfocus", "--sync", window_id)
        screen_x, screen_y = self._screen_point(
            widget,
            x,
            y,
            target_window=target_window,
            window_title=window_title,
        )
        self._xdotool("keyup", "Control_L", "Shift_L", "Alt_L")
        self._xdotool("mousemove", str(screen_x), str(screen_y))
        self.assertEqual(
            _screen_coordinates(
                self._xdotool("getmouselocation", "--shell"),
                (0.0, 0.0),
            ),
            (screen_x, screen_y),
            "physical pointer did not reach the click target",
        )
        if control:
            self._xdotool("keydown", "Control_L")
        try:
            self._xdotool("mousedown", "1")
            self._xdotool("mouseup", "1")
        finally:
            if control:
                self._xdotool("keyup", "Control_L")
        _pump_events(self.GLib, 10)

    def _physical_key(self, key: str, *, window_title: str | None = None) -> None:
        self._xdotool("windowfocus", "--sync", self._window_id(window_title))
        self._xdotool("keyup", "Control_L", "Shift_L", "Alt_L")
        self._xdotool("key", "--clearmodifiers", key)
        _pump_events(self.GLib, 10)

    def _segment_geometry(self, segment_id: str) -> Any:
        canvas = self.window.timeline_canvas
        return next(
            geometry
            for geometry in layout_timeline_segments(
                self.window.segment_timeline,
                canvas._viewport_width,
                canvas.get_zoom(),
            )
            if geometry.segment_id == segment_id
        )

    def _click_segment(self, segment_id: str, *, control: bool = False) -> None:
        canvas = self.window.timeline_canvas
        geometry = self._segment_geometry(segment_id)
        self._physical_click(
            canvas,
            geometry.x + geometry.width / 2.0,
            geometry.y + geometry.height / 2.0,
            control=control,
        )
        self.assertIn(segment_id, self.window.selected_segment_ids)

    def _click_widget_center(self, widget: Any) -> None:
        self.assertTrue(widget.get_visible())
        self._physical_click(
            widget,
            widget.get_width() / 2.0,
            widget.get_height() / 2.0,
        )

    def _required_window_widget(self, name: str) -> Any:
        widget = getattr(self.window, name, None)
        self.assertIsNotNone(
            widget,
            f"TICKET-111 production contract requires window.{name}",
        )
        return widget

    def _widget_children(self, widget: Any) -> list[Any]:
        children = []
        child = widget.get_first_child()
        while child is not None:
            children.append(child)
            child = child.get_next_sibling()
        return children

    def _walk_widgets(self, root: Any):
        yield root
        for child in self._widget_children(root):
            yield from self._walk_widgets(child)

    def _find_labeled_planner_row(self, planner: Any, label_text: str) -> tuple[Any, list[Any]]:
        for widget in self._walk_widgets(planner):
            children = self._widget_children(widget)
            if any(
                isinstance(child, self.Gtk.Label) and child.get_text().strip() == label_text
                for child in children
            ):
                return widget, children
        self.fail(f"TICKET-111 export planner has no {label_text!r} row")

    def _open_native_export_planner(self) -> Any:
        export_button = self._required_window_widget("export_button")
        self.assertTrue(export_button.get_sensitive())
        self._click_widget_center(export_button)
        self._wait_until(
            lambda: getattr(self.window, "export_planning_window", None) is not None,
            "main export button did not open the native export planner",
        )
        planner = self.window.export_planning_window
        self.assertTrue(planner.get_visible())
        self.planner_title = f"FrameStudio T111 Planner {uuid.uuid4().hex}"
        planner.set_title(self.planner_title)
        _pump_events(self.GLib, 10)
        self._window_id(self.planner_title)
        return planner

    def test_real_gtk_backspace_ripple_selection_geometry_and_runtime_undo(self):
        window = self._open_window()
        canvas = window.timeline_canvas
        self._click_segment("b")
        self.assertEqual(window.selected_segment_id, "b")
        before_timeline = window.project.timeline.to_dict()
        before_c_transform = window.project.timeline.find("c").visual_transform
        before_track_rows = tuple(
            (row.track_id, row.y, row.height)
            for row in layout_timeline_tracks(window.segment_timeline)
        )
        before_c = self._segment_geometry("c")
        before_independent_ticks = (
            window.project.timeline.find("independent").timeline_start_ticks,
            window.project.timeline.find("independent").timeline_end_ticks,
        )
        before_output = window.timeline_output_label.get_text()
        before_content_width = canvas.get_content_width()

        self._physical_key("BackSpace")
        self._wait_until(
            lambda: "b" not in {block.segment_id for block in window.project.timeline.blocks},
            "physical Backspace did not remove the selected block",
        )

        self.assertNotIn("b", window.selected_segment_ids)
        self.assertNotEqual(window.selected_segment_id, "b")
        self.assertLess(window.project.timeline.timeline_duration_seconds, 5.0)
        self.assertNotEqual(window.timeline_output_label.get_text(), before_output)
        self.assertLessEqual(canvas.get_content_width(), before_content_width)
        after_c = self._segment_geometry("c")
        after_independent = self._segment_geometry("independent")
        self.assertGreater(after_c.width, 0.0)
        self.assertLess(after_c.x, before_c.x)
        self.assertGreater(after_independent.width, 0.0)
        self.assertEqual(
            (
                window.project.timeline.find("independent").timeline_start_ticks,
                window.project.timeline.find("independent").timeline_end_ticks,
            ),
            before_independent_ticks,
        )
        self.assertEqual(
            window.project.timeline.find("c").visual_transform,
            before_c_transform,
        )
        self.assertTrue(window.project.timeline.find("c").deleted)
        self.assertEqual(
            tuple(
                (row.track_id, row.y, row.height)
                for row in layout_timeline_tracks(window.segment_timeline)
            ),
            before_track_rows,
        )

        undo_button = self._required_window_widget("undo_removal_button")
        self.assertTrue(undo_button.get_sensitive())
        self._click_widget_center(undo_button)
        self._wait_until(
            lambda: window.project.timeline.to_dict() == before_timeline,
            "Undo did not restore the exact removal state",
        )
        self.assertEqual(window.selected_segment_ids, ("b",))
        self.assertEqual(window.selected_segment_id, "b")
        self.assertFalse(undo_button.get_sensitive())
        self.assertEqual(_sha256(self.source_a), self.source_hashes[self.source_a])
        self.assertEqual(_sha256(self.source_b), self.source_hashes[self.source_b])

    def test_real_gtk_fresh_legacy_source_backspace_and_undo_preserve_timing_mode(self):
        window = self._open_window(source_path=self.source_a)
        self.assertEqual(window.project.timeline.timing_mode, "legacy-ripple")
        first = window.project.timeline.segment_items[0]
        geometry = self._segment_geometry(first.segment_id)
        canvas = window.timeline_canvas
        self._physical_click(
            canvas,
            geometry.x + geometry.width / 3.0,
            geometry.y + geometry.height / 2.0,
        )
        self._physical_key("b")
        self._wait_until(
            lambda: len(window.project.timeline.segment_items) == 2,
            "first physical split did not complete",
        )
        last = window.project.timeline.segment_items[-1]
        self._click_segment(last.segment_id)
        self._physical_key("b")
        self._wait_until(
            lambda: len(window.project.timeline.segment_items) == 3,
            "second physical split did not complete",
        )
        before_timeline = Project.from_dict(window.project.to_dict()).timeline.to_dict()
        middle = window.project.timeline.segment_items[1]
        self._click_segment(middle.segment_id)
        self._physical_key("BackSpace")
        self._wait_until(
            lambda: len(window.project.timeline.segment_items) == 2,
            "fresh legacy-source Backspace did not remove the middle clip",
        )
        self.assertEqual(window.project.timeline.timing_mode, "legacy-ripple")
        self.assertNotIn(middle.segment_id, window.selected_segment_ids)
        self._click_widget_center(self._required_window_widget("undo_removal_button"))
        self._wait_until(
            lambda: window.project.timeline.to_dict() == before_timeline,
            "fresh legacy-source Undo did not restore exact timeline state",
        )
        self.assertEqual(window.project.timeline.timing_mode, "legacy-ripple")
        self.assertEqual(_sha256(self.source_a), self.source_hashes[self.source_a])

    def test_real_gtk_remove_all_clears_preview_and_undo_restores_playback(self):
        window = self._open_window()
        source_ids = tuple(source.source_id for source in window.project.sources)
        selected_ids = tuple(block.segment_id for block in window.project.timeline.blocks)
        self._click_segment(selected_ids[0])
        for segment_id in selected_ids[1:]:
            self._click_segment(segment_id, control=True)
        self.assertEqual(set(window.selected_segment_ids), set(selected_ids))
        before_timeline = window.project.timeline.to_dict()

        self._physical_key("BackSpace")
        self._wait_until(
            lambda: not window.project.timeline.blocks,
            "physical Backspace did not remove all selected blocks",
        )
        self.assertIsNone(window.backend)
        self.assertIsNone(window.controller)
        self.assertIsNone(window.selected_segment_id)
        self.assertEqual(window.selected_segment_ids, ())
        self.assertIsNone(window.preview.get_paintable())
        self.assertFalse(window.play_button.get_sensitive())
        self.assertEqual(tuple(source.source_id for source in window.project.sources), source_ids)
        undo_button = self._required_window_widget("undo_removal_button")
        self.assertTrue(undo_button.get_sensitive())

        self._click_widget_center(undo_button)
        self._wait_until(
            lambda: window.project.timeline.to_dict() == before_timeline,
            "Undo did not restore all removed blocks",
        )
        self.assertIsNotNone(window.backend)
        self.assertIsNotNone(window.controller)
        self.assertTrue(window.play_button.get_sensitive())
        self.assertIsNotNone(window.preview.get_paintable())
        for source, digest in self.source_hashes.items():
            self.assertEqual(_sha256(source), digest)

    def test_real_gtk_backspace_supports_bounded_sequential_undo(self):
        window = self._open_window()
        before_timeline = window.project.timeline.to_dict()

        self._click_segment("b")
        self._physical_key("BackSpace")
        self._wait_until(
            lambda: "b" not in {block.segment_id for block in window.project.timeline.blocks},
            "first physical Backspace did not remove block b",
        )
        after_first_timeline = window.project.timeline.to_dict()

        self._click_segment("c")
        self._physical_key("BackSpace")
        self._wait_until(
            lambda: "c" not in {block.segment_id for block in window.project.timeline.blocks},
            "second physical Backspace did not remove block c",
        )
        self.assertEqual(len(window.removal_history.values()), 2)
        self.assertTrue(self._required_window_widget("undo_removal_button").get_sensitive())

        undo_button = self._required_window_widget("undo_removal_button")
        self._click_widget_center(undo_button)
        self._wait_until(
            lambda: window.project.timeline.to_dict() == after_first_timeline,
            "first bounded Undo did not restore only the latest removal",
        )
        self.assertTrue(
            undo_button.get_sensitive(),
            f"remaining removal receipts={len(window.removal_history.values())}",
        )
        self.assertEqual(window.selected_segment_ids, ("c",))

        self._click_widget_center(undo_button)
        self._wait_until(
            lambda: window.project.timeline.to_dict() == before_timeline,
            "second bounded Undo did not restore the earlier removal",
        )
        self.assertFalse(undo_button.get_sensitive())
        self.assertEqual(window.selected_segment_ids, ("b",))
        self.assertEqual(_sha256(self.source_a), self.source_hashes[self.source_a])
        self.assertEqual(_sha256(self.source_b), self.source_hashes[self.source_b])

    def test_real_gtk_delete_restore_and_text_entry_keyboard_isolation(self):
        window = self._open_window()
        before_c = self._segment_geometry("c")
        before_timeline = window.project.timeline.to_dict()

        self._click_segment("c")
        self.assertTrue(window.project.timeline.find("c").deleted)
        self._physical_key("Delete")
        self._wait_until(
            lambda: not window.project.timeline.find("c").deleted,
            "physical Delete did not restore the excluded block",
        )
        restored_c = self._segment_geometry("c")
        self.assertEqual(restored_c.x, before_c.x)
        self.assertEqual(restored_c.width, before_c.width)
        self.assertIn("c", {block.segment_id for block in window.project.timeline.blocks})
        restored_timeline = window.project.timeline.to_dict()
        self.assertNotEqual(restored_timeline, before_timeline)

        self._physical_key("Delete")
        self._wait_until(
            lambda: window.project.timeline.find("c").deleted,
            "physical Delete did not retain the excluded block",
        )
        self.assertEqual(self._segment_geometry("c").x, before_c.x)
        self.assertEqual(self._segment_geometry("c").width, before_c.width)
        self.assertEqual(window.project.timeline.find("c").timeline_start_ticks, 4_000_000)
        self.assertEqual(window.project.timeline.to_dict(), before_timeline)

        planner = self._open_native_export_planner()
        _, filename_children = self._find_labeled_planner_row(planner, "Filename")
        filename_entry = next(
            (child for child in filename_children if isinstance(child, self.Gtk.Entry)),
            None,
        )
        self.assertIsNotNone(filename_entry)
        self.assertIsInstance(filename_entry, self.Gtk.Entry)

        _, rate_children = self._find_labeled_planner_row(planner, "Output FPS")
        rate_dropdown = next(
            (child for child in rate_children if isinstance(child, self.Gtk.DropDown)),
            None,
        )
        self.assertIsNotNone(rate_dropdown)
        rate_dropdown.set_selected(2)
        _pump_events(self.GLib, 10)
        custom_fps_entry = next(
            (child for child in rate_children if isinstance(child, self.Gtk.Entry)),
            None,
        )
        self.assertIsNotNone(custom_fps_entry)
        self.assertIsInstance(custom_fps_entry, self.Gtk.Entry)
        self._wait_until(
            custom_fps_entry.get_sensitive,
            "native export planner custom FPS choice did not enable its actual entry",
        )

        for entry, value in (
            (filename_entry, "ticket111-name"),
            (custom_fps_entry, "29.97"),
        ):
            for key, position, expected_text in (
                ("BackSpace", -1, value[:-1]),
                ("Delete", 0, value[1:]),
            ):
                before_entry_project = window.project.to_dict()
                before_history = getattr(
                    window,
                    "removal_history",
                    getattr(window, "_removal_history", None),
                )
                entry.set_text(value)
                _pump_events(self.GLib, 10)
                cursor_position = len(value) if position == -1 else position
                entry.set_position(cursor_position)
                entry.select_region(cursor_position, cursor_position)
                self._xdotool(
                    "windowfocus",
                    "--sync",
                    self._window_id(self.planner_title),
                )
                entry.grab_focus()
                _pump_events(self.GLib, 5)
                entry.set_position(cursor_position)
                entry.select_region(cursor_position, cursor_position)
                self._physical_key(key, window_title=self.planner_title)
                self.assertEqual(entry.get_text(), expected_text)
                self.assertEqual(window.project.to_dict(), before_entry_project)
                self.assertIs(
                    getattr(
                        window,
                        "removal_history",
                        getattr(window, "_removal_history", None),
                    ),
                    before_history,
                )
        self.assertEqual(_sha256(self.source_a), self.source_hashes[self.source_a])
        self.assertEqual(_sha256(self.source_b), self.source_hashes[self.source_b])


if __name__ == "__main__":
    unittest.main()
