from __future__ import annotations

import hashlib
import shutil
import subprocess
import tempfile
import unittest
import uuid
from pathlib import Path
from typing import Any

from framestudio.composed_playback import FfmpegSynchronizedPlaybackBackend
from framestudio.media import probe_media
from framestudio.model import Project, ProjectValidationError, VisualTransform
from framestudio.persistence import load_project, save_project
from framestudio.timeline import (
    TIMELINE_HORIZONTAL_PADDING,
    layout_timeline_segments,
    layout_timeline_tracks,
    timeline_pixels_per_second,
    timeline_x_from_ticks,
)

try:
    from test_phase010_functionality import _pump_events
except ModuleNotFoundError:
    from tests.test_phase010_functionality import _pump_events

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def _gtk_runtime() -> tuple[Any, Any, Any, Any]:
    try:
        import gi

        gi.require_version("Gdk", "4.0")
        gi.require_version("Gio", "2.0")
        gi.require_version("Gtk", "4.0")
        from gi.repository import Gdk, Gio, GLib, Gtk
    except (ImportError, ValueError) as error:
        raise AssertionError("GTK 4 and PyGObject are required") from error
    return Gdk, Gio, GLib, Gtk


def _screen_coordinates(
    geometry: str,
    relative: tuple[float, float],
) -> tuple[int, int]:
    values = {
        key: int(value)
        for key, value in (
            line.split("=", 1)
            for line in geometry.splitlines()
            if "=" in line and line.split("=", 1)[0] in {"X", "Y"}
        )
    }
    return round(values["X"] + relative[0]), round(values["Y"] + relative[1])


def _make_video(destination: Path, color: str, duration: float = 2.0) -> None:
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        raise AssertionError("ffmpeg is required for GTK track-drag functionality")
    result = subprocess.run(
        [
            ffmpeg,
            "-hide_banner",
            "-loglevel",
            "error",
            "-nostdin",
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"color=c={color}:size=320x180:rate=12",
            "-t",
            str(duration),
            "-an",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            str(destination),
        ],
        cwd=str(REPOSITORY_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise AssertionError(f"Could not create fixture {destination.name}: {result.stderr}")


class TrackDragFunctionalityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Gdk, Gio, GLib, Gtk = _gtk_runtime()
        if not Gtk.init_check():
            raise AssertionError("GTK 4 could not initialize on the test display")
        display = Gdk.Display.get_default()
        cls.Gio = Gio
        cls.Gdk = Gdk
        cls.GLib = GLib
        cls.Gtk = Gtk
        cls.display_name = "" if display is None else display.get_name()
        cls.display_backend = "" if display is None else type(display).__name__

    def setUp(self):
        self.runtime = tempfile.TemporaryDirectory(
            prefix="phase010-ticket117-",
            dir=str(REPOSITORY_ROOT.parent),
        )
        self.addCleanup(self.runtime.cleanup)
        root = Path(self.runtime.name)
        self.source_a = root / "track-a.mp4"
        self.source_b = root / "track-b.mp4"
        _make_video(self.source_a, "red")
        _make_video(self.source_b, "blue")
        self.source_hashes = {
            self.source_a: hashlib.sha256(self.source_a.read_bytes()).hexdigest(),
            self.source_b: hashlib.sha256(self.source_b.read_bytes()).hexdigest(),
        }

    def _wait_until(self, predicate, message: str, rounds: int = 500) -> None:
        for _ in range(rounds):
            _pump_events(self.GLib, 1)
            if predicate():
                return
        raise AssertionError(f"{message}; status={self.window.status_label.get_text()!r}")

    def _assert_synchronized_preview(self, window: Any) -> None:
        self.assertIsInstance(window.backend, FfmpegSynchronizedPlaybackBackend)
        self.assertIsNotNone(window.controller)
        self.assertTrue(window.play_button.get_sensitive())
        self.assertFalse(window.backend.audio_preview_enabled)

    def _open_window(self, project_path: Path):
        from framestudio.app import create_editor_application

        application_id = f"io.github.framestudio.ticket117.a{uuid.uuid4().hex}"
        self.window_title = f"FrameStudio T117 {uuid.uuid4().hex}"
        self.application, factory = create_editor_application(
            project_path=project_path,
            application_id=application_id,
        )
        self.addCleanup(self.application.quit)
        self.assertTrue(self.application.register(None))
        self.window = factory(self.application)
        self.window.set_title(self.window_title)
        self.window.present()
        self.addCleanup(self.window.close)
        self._wait_until(
            lambda: self.window.project is not None and not self.window._source_load_in_progress,
            "production GTK project load did not complete",
        )
        return self.window

    def _pointer_blocker(self) -> str | None:
        if "x11" not in (f"{self.display_name} {self.display_backend}".lower()):
            return (
                "true pointer injection blocked: GTK display is "
                f"{self.display_name or 'unknown'}, not X11; no ydotool daemon socket"
            )
        if shutil.which("xdotool") is None:
            return "true pointer injection blocked: xdotool is unavailable"
        return None

    def _xdotool(self, *arguments: str) -> str:
        result = subprocess.run(
            ["xdotool", *arguments],
            cwd=str(REPOSITORY_ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise AssertionError(f"xdotool {' '.join(arguments)} failed: {result.stderr.strip()}")
        return result.stdout

    def _pointer_window_id(self) -> str:
        output = self._xdotool(
            "search",
            "--onlyvisible",
            "--name",
            self.window_title,
        )
        window_ids = tuple(line.strip() for line in output.splitlines() if line.strip())
        if len(window_ids) != 1:
            raise AssertionError(f"Expected one uniquely titled GTK window, found {window_ids!r}")
        return window_ids[0]

    def _pointer_screen_point(self, widget: Any, x: float, y: float) -> tuple[int, int]:
        relative = widget.translate_coordinates(self.window, x, y)
        if relative is None:
            raise AssertionError("GTK could not translate timeline coordinates to window space")
        geometry = self._xdotool(
            "getwindowgeometry",
            "--shell",
            self._pointer_window_id(),
        )
        return _screen_coordinates(geometry, relative)

    def _pointer_click(
        self,
        widget: Any,
        x: float,
        y: float,
        *,
        control: bool = False,
    ) -> None:
        window_id = self._pointer_window_id()
        self._xdotool("windowfocus", "--sync", window_id)
        screen_x, screen_y = self._pointer_screen_point(widget, x, y)
        self._xdotool("mousemove", "--sync", str(screen_x), str(screen_y))
        if control:
            self._xdotool("keyup", "Control_L", "Shift_L")
            self._xdotool("keydown", "Control_L")
            try:
                _pump_events(self.GLib, 5)
                self._xdotool("mousedown", "1", "mouseup", "1")
                _pump_events(self.GLib, 5)
            finally:
                self._xdotool("keyup", "Control_L")
        else:
            self._xdotool("keyup", "Control_L", "Shift_L")
            self._xdotool("mousedown", "1", "mouseup", "1")
        _pump_events(self.GLib, 10)

    def _pointer_drag(
        self,
        widget: Any,
        start: tuple[float, float],
        target: tuple[float, float],
        *,
        while_held: Any | None = None,
    ) -> None:
        window_id = self._pointer_window_id()
        self._xdotool("windowfocus", "--sync", window_id)
        start_x, start_y = self._pointer_screen_point(widget, *start)
        target_x, target_y = self._pointer_screen_point(widget, *target)
        self._xdotool("mousemove", "--sync", str(start_x), str(start_y))
        self._xdotool("mousedown", "1")
        _pump_events(self.GLib, 5)
        self._xdotool("mousemove", "--sync", str(target_x), str(target_y))
        actual_position = self._xdotool("getmouselocation")
        if f"x:{target_x} y:{target_y}" not in actual_position:
            raise AssertionError(
                f"pointer did not reach target ({target_x}, {target_y}): {actual_position}"
            )
        _pump_events(self.GLib, 20)
        routed_position = self._xdotool("getmouselocation")
        if f"x:{target_x} y:{target_y}" not in routed_position:
            self._xdotool("mouseup", "1")
            self.skipTest(
                "true pointer injection blocked: compositor reset the XTest pointer "
                f"after GTK dispatch ({routed_position.strip()})"
            )
        if getattr(widget, "_drag_mode", None) != "segment":
            self._xdotool("mouseup", "1")
            self.skipTest(
                "true pointer injection blocked: GTK did not route the physical "
                f"press to a timeline segment (mode={getattr(widget, '_drag_mode', None)!r})"
            )
        if while_held is not None:
            while_held()
        self._xdotool("mouseup", "1")
        _pump_events(self.GLib, 20)

    def _gesture_drag(self, clip_id: str, target_x: float, target_y: float) -> None:
        canvas = self.window.timeline_canvas
        geometry = next(
            item
            for item in layout_timeline_segments(
                self.window.segment_timeline,
                canvas._viewport_width,
                canvas.get_zoom(),
            )
            if item.segment_id == clip_id
        )
        start_x = geometry.x + geometry.width / 2.0
        start_y = geometry.y + geometry.height / 2.0
        drag = canvas._drag_gesture
        drag.emit("drag-begin", start_x, start_y)
        drag.emit("drag-update", target_x - start_x, target_y - start_y)
        drag.emit("drag-end", target_x - start_x, target_y - start_y)
        _pump_events(self.GLib, 20)

    def _pointer_click_segment(
        self,
        canvas: Any,
        segment_id: str,
        *,
        control: bool = False,
    ) -> None:
        geometry = next(
            item
            for item in layout_timeline_segments(
                self.window.project.timeline,
                canvas._viewport_width,
                canvas.get_zoom(),
            )
            if item.segment_id == segment_id
        )
        self._pointer_click(
            canvas,
            geometry.x + geometry.width / 2.0,
            geometry.y + geometry.height / 2.0,
            control=control,
        )

    def test_real_gtk_track_lifecycle_confirmation_drag_and_synchronized_preview(self):
        from framestudio.model import Project

        legacy = Project.create(
            self.source_a,
            probe_media(self.source_a).metadata(),
            project_id="ticket117-legacy",
        )
        first, second = legacy.timeline.split(1.0)
        legacy.timeline.set_visual_transform([second.segment_id], VisualTransform(zoom=1.2))
        legacy_path = Path(self.runtime.name) / "legacy.framestudio.json"
        save_project(legacy, legacy_path)

        window = self._open_window(legacy_path)
        self.assertEqual(window.timeline_canvas.get_track_ids(), ("track-1",))
        self.assertIsNotNone(window.controller)

        window.add_track_button.emit("clicked")
        self._wait_until(
            lambda: getattr(window, "_track_confirmation_dialog", None) is not None,
            "track conversion confirmation did not appear",
        )
        dialog = window._track_confirmation_dialog
        dialog.response(1)
        self._wait_until(
            lambda: window.project.timeline.timing_mode == "absolute",
            "legacy timeline was not explicitly converted",
        )
        self._assert_synchronized_preview(window)
        self.assertNotIn("preview unavailable", window.status_label.get_text().lower())

        for _ in range(3):
            window.add_track_button.emit("clicked")
        _pump_events(self.GLib, 10)
        self.assertEqual(
            window.project.timeline.track_ids, ("track-1", "track-2", "track-3", "track-4")
        )
        self.assertEqual(
            [row.track_id for row in layout_timeline_tracks(window.project.timeline)],
            ["track-1", "track-2", "track-3", "track-4"],
        )
        with self.assertRaises(ProjectValidationError):
            window.project.timeline.add_track("track-5")
        window.add_track_button.emit("clicked")
        self.assertIn("at most", window.status_label.get_text().lower())

        window.track_selector.set_selected(1)
        _pump_events(self.GLib, 10)
        self.assertEqual(window.project.timeline.active_track_id, "track-2")

        before_import = {
            segment.segment_id: segment.visual_transform
            for segment in window.project.timeline.blocks
        }
        window._load_source((self.source_b,))
        self._wait_until(
            lambda: any(
                segment.source_id != window.project.source.source_id
                for segment in window.project.timeline.blocks
            ),
            "source import did not complete on the active track",
        )
        imported = next(
            segment
            for segment in window.project.timeline.blocks
            if segment.source_id != window.project.source.source_id
        )
        self.assertEqual(imported.track_id, "track-2")
        window.remove_track_button.emit("clicked")
        self.assertIn("empty tracks", window.status_label.get_text().lower())
        self.assertEqual(
            window.project.timeline.track_ids,
            ("track-1", "track-2", "track-3", "track-4"),
        )
        for segment_id, transform in before_import.items():
            self.assertEqual(window.project.timeline.find(segment_id).visual_transform, transform)

        window.timeline_canvas.set_zoom(0.5)
        first_id = window.project.timeline.blocks[0].segment_id
        first_geometry = next(
            item
            for item in layout_timeline_segments(
                window.project.timeline,
                window.timeline_canvas._viewport_width,
                window.timeline_canvas.get_zoom(),
            )
            if item.segment_id == first_id
        )
        target_row = layout_timeline_tracks(window.project.timeline)[1]
        target_x = first_geometry.x + first_geometry.width + 80.0
        self._gesture_drag(
            first_id,
            target_x,
            target_row.y + target_row.height / 2.0,
        )
        moved = window.project.timeline.find(first_id)
        self.assertEqual(moved.track_id, "track-2")
        self._assert_synchronized_preview(window)
        self.assertNotIn("preview unavailable", window.status_label.get_text().lower())

        moved_start = moved.timeline_start_ticks
        window.timeline_canvas.set_zoom(2.0)
        self._gesture_drag(
            first_id,
            target_x + 40.0,
            target_row.y + target_row.height / 2.0,
        )
        self.assertGreaterEqual(
            window.project.timeline.find(first_id).timeline_start_ticks,
            moved_start,
        )

        # Invalid row drops and explicit GTK gesture cancellation leave state intact.
        before_invalid = window.project.timeline.to_dict()
        geometry = next(
            item
            for item in layout_timeline_segments(
                window.project.timeline,
                window.timeline_canvas._viewport_width,
                window.timeline_canvas.get_zoom(),
            )
            if item.segment_id == first_id
        )
        drag = window.timeline_canvas._drag_gesture
        start_x = geometry.x + geometry.width / 2.0
        start_y = geometry.y + geometry.height / 2.0
        drag.emit("drag-begin", start_x, start_y)
        drag.emit("drag-update", 10.0, -start_y - 20.0)
        drag.emit("drag-end", 10.0, -start_y - 20.0)
        self.assertEqual(window.project.timeline.to_dict(), before_invalid)
        self.assertIn("invalid drop", window.status_label.get_text().lower())

        drag.emit("drag-begin", start_x, start_y)
        drag.emit("drag-update", 100.0, 10.0)
        drag.emit("cancel", None)
        self.assertEqual(window.project.timeline.to_dict(), before_invalid)

        project_path = Path(self.runtime.name) / "dragged.framestudio.json"
        window._save_to(project_path)
        restored = load_project(project_path)
        self.assertEqual(restored.to_dict(), window.project.to_dict())
        for path, digest in self.source_hashes.items():
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), digest)

    def test_real_gtk_invalid_fps_confirmation_keeps_legacy_attachment(self):
        from framestudio.model import Project

        legacy = Project.create(
            self.source_a,
            probe_media(self.source_a).metadata(),
            project_id="ticket117-invalid-fps",
        )
        legacy_path = Path(self.runtime.name) / "invalid-fps-legacy.framestudio.json"
        save_project(legacy, legacy_path)

        window = self._open_window(legacy_path)
        selected_ids = window.selected_segment_ids
        controller = window.controller
        backend = window.backend
        window.project.source.metadata["frame_rate"] = "not-a-rate"

        window.add_track_button.emit("clicked")
        self._wait_until(
            lambda: getattr(window, "_track_confirmation_dialog", None) is not None,
            "invalid-FPS conversion confirmation did not appear",
        )
        window._track_confirmation_dialog.response(1)
        _pump_events(self.GLib, 20)

        self.assertEqual(window.project.timeline.timing_mode, "legacy-ripple")
        self.assertIs(window.controller, controller)
        self.assertIs(window.backend, backend)
        self.assertEqual(window.selected_segment_ids, selected_ids)
        self.assertIn("frame_rate", window.status_label.get_text())

    def test_real_gtk_synchronized_normal_wheel_seeks_with_preview_backend(self):
        project = Project.create_synchronized(
            self.source_a,
            probe_media(self.source_a).metadata(),
            project_id="ticket117-wheel-seek",
        )
        path = Path(self.runtime.name) / "wheel-seek.framestudio.json"
        save_project(project, path)

        window = self._open_window(path)
        self._assert_synchronized_preview(window)
        controller = window.timeline_scroll_controller
        controller.emit("scroll", 0.0, -1.0)
        _pump_events(self.GLib, 10)

        duration = window.project.timeline.timeline_duration_seconds
        self.assertEqual(window.project.playhead_seconds, duration)
        self.assertEqual(window.timeline_canvas.get_playhead_seconds(), duration)
        self._assert_synchronized_preview(window)
        self.assertEqual(window.controller.snapshot().position_seconds, duration)

    def test_absolute_project_load_uses_synchronized_preview_adapter(self):
        absolute_path = Path(self.runtime.name) / "absolute.framestudio.json"
        project = Project.create_synchronized(
            self.source_a,
            probe_media(self.source_a).metadata(),
            project_id="ticket117-absolute-load",
        )
        project.timeline.add_track("track-2")
        save_project(project, absolute_path)

        window = self._open_window(absolute_path)
        self.assertEqual(window.project.timeline.timing_mode, "absolute")
        self._assert_synchronized_preview(window)
        self.assertEqual(window.timeline_canvas.get_track_ids(), ("track-1", "track-2"))
        self.assertEqual(window.timeline_canvas.get_playhead_seconds(), 0.0)

    def test_real_gtk_drag_beyond_endpoint_persists_active_track_and_sources(self):
        project = Project.create_synchronized(
            self.source_a,
            probe_media(self.source_a).metadata(),
            project_id="ticket117-beyond-endpoint",
        )
        project.timeline.add_track("track-2")
        initial_segment = project.timeline.blocks[0]
        segment_duration_ticks = (
            initial_segment.timeline_end_ticks - initial_segment.timeline_start_ticks
        )
        initial_path = Path(self.runtime.name) / "beyond-endpoint-initial.framestudio.json"
        save_project(project, initial_path)

        window = self._open_window(initial_path)
        canvas = window.timeline_canvas
        source_hash = hashlib.sha256(self.source_a.read_bytes()).hexdigest()

        track_two = layout_timeline_tracks(window.project.timeline)[1]
        canvas._click_gesture.emit(
            "pressed",
            1,
            TIMELINE_HORIZONTAL_PADDING + 4.0,
            track_two.y + 4.0,
        )
        canvas._click_gesture.emit(
            "released",
            1,
            TIMELINE_HORIZONTAL_PADDING + 4.0,
            track_two.y + 4.0,
        )
        _pump_events(self.GLib, 10)
        self.assertEqual(window.project.timeline.active_track_id, "track-2")
        self.assertEqual(window.track_selector.get_selected(), 1)

        requested_starts = (7_000_000, 12_000_000)
        for zoom, requested_start_ticks in zip(
            (0.5, 2.0),
            requested_starts,
            strict=True,
        ):
            canvas.set_zoom(zoom)
            pointer_offset_ticks = segment_duration_ticks // 2
            pointer_target_ticks = requested_start_ticks + pointer_offset_ticks
            pixels_per_second = timeline_pixels_per_second(
                window.project.timeline.timeline_duration_seconds,
                canvas._viewport_width,
                canvas.get_zoom(),
            )
            target_x = (
                TIMELINE_HORIZONTAL_PADDING
                + (pointer_target_ticks / 1_000_000.0) * pixels_per_second
            )
            target_row = layout_timeline_tracks(window.project.timeline)[1]
            self._gesture_drag(
                initial_segment.segment_id,
                target_x,
                target_row.y + target_row.height / 2.0,
            )
            moved = window.project.timeline.find(initial_segment.segment_id)
            self.assertEqual(moved.timeline_start_ticks, requested_start_ticks)
            self.assertEqual(
                window.project.timeline.timeline_duration_seconds,
                (requested_start_ticks + segment_duration_ticks) / 1_000_000.0,
            )

        project_path = Path(self.runtime.name) / "beyond-endpoint.framestudio.json"
        window._save_to(project_path)
        restored = load_project(project_path)
        self.assertEqual(restored.timeline.active_track_id, "track-2")
        self.assertEqual(
            restored.timeline.find(initial_segment.segment_id).timeline_start_ticks,
            requested_starts[-1],
        )
        self.assertEqual(
            restored.timeline.timeline_duration_seconds,
            (requested_starts[-1] + segment_duration_ticks) / 1_000_000.0,
        )
        self.assertEqual(hashlib.sha256(self.source_a.read_bytes()).hexdigest(), source_hash)

        reopened = self._open_window(project_path)
        self.assertEqual(reopened.project.timeline.active_track_id, "track-2")
        self.assertEqual(reopened.track_selector.get_selected(), 1)
        self.assertEqual(
            reopened.project.timeline.find(initial_segment.segment_id).timeline_start_ticks,
            requested_starts[-1],
        )

    def test_real_pointer_drag_exercises_chain_exclusion_selection_and_persistence(self):
        blocker = self._pointer_blocker()
        if blocker is not None:
            self.skipTest(blocker)

        project = Project.create_synchronized(
            self.source_a,
            probe_media(self.source_a).metadata(),
            project_id="ticket117-real-pointer",
        )
        timeline = project.timeline
        moving = timeline.blocks[0]
        timeline.add_track("track-2")
        timeline.add_track("track-3")
        timeline.add_track("track-4")
        timeline.set_visual_transform(
            [moving.segment_id],
            VisualTransform(zoom=1.35, offset_x=18.0, offset_y=-12.0),
        )
        moving_transform = timeline.find(moving.segment_id).visual_transform
        chain_a = timeline.paste_blocks(
            timeline.copy_blocks([moving.segment_id]),
            at_ticks=2_000_000,
            target_track_id="track-2",
        )[0]
        chain_b = timeline.paste_blocks(
            timeline.copy_blocks([moving.segment_id]),
            at_ticks=4_000_000,
            target_track_id="track-2",
        )[0]
        timeline.set_deleted(chain_a.segment_id, True)
        unaffected = timeline.paste_blocks(
            timeline.copy_blocks([moving.segment_id]),
            at_ticks=1_000_000,
            target_track_id="track-3",
        )[0]
        timeline.set_active_track("track-2")
        original_unaffected = timeline.find(unaffected.segment_id)
        original_chain = (
            timeline.find(chain_a.segment_id),
            timeline.find(chain_b.segment_id),
        )
        source_hashes = dict(self.source_hashes)
        project_path = Path(self.runtime.name) / "real-pointer.framestudio.json"
        save_project(project, project_path)

        window = self._open_window(project_path)
        canvas = window.timeline_canvas
        canvas.set_zoom(1.0)
        press_states: list[int] = []
        canvas._click_gesture.connect(
            "pressed",
            lambda gesture, _count, _x, _y: press_states.append(
                int(gesture.get_current_event_state()),
            ),
        )
        rows = layout_timeline_tracks(window.project.timeline)
        moving_geometry = next(
            item
            for item in layout_timeline_segments(
                window.project.timeline,
                canvas._viewport_width,
                canvas.get_zoom(),
            )
            if item.segment_id == moving.segment_id
        )
        target_row = rows[1]
        target_pointer_ticks = 2_000_000
        target_x = timeline_x_from_ticks(
            target_pointer_ticks,
            window.project.timeline.timeline_duration_seconds,
            canvas._viewport_width,
            canvas.get_zoom(),
        )
        drag_start = (
            moving_geometry.x + moving_geometry.width / 2.0,
            moving_geometry.y + moving_geometry.height / 2.0,
        )
        drag_target = (
            target_x,
            target_row.y + target_row.height / 2.0,
        )
        self._pointer_click(canvas, *drag_start)
        self.assertEqual(
            window.selected_segment_id,
            moving.segment_id,
            f"pointer start={drag_start!r} screen="
            f"{self._pointer_screen_point(canvas, *drag_start)!r}",
        )

        def assert_chain_preview() -> None:
            self.assertEqual(
                canvas._drag_preview,
                (6_000_000, "track-2"),
                (
                    f"drag target={drag_target!r} screen="
                    f"{self._pointer_screen_point(canvas, *drag_target)!r} "
                    f"start-screen={self._pointer_screen_point(canvas, *drag_start)!r} "
                    f"canvas={canvas.get_width()}x{canvas.get_height()} "
                    f"rows={rows!r}"
                ),
            )
            preview = next(
                item
                for item in canvas._clips_with_drag_preview(
                    layout_timeline_segments(
                        window.project.timeline,
                        canvas._viewport_width,
                        canvas.get_zoom(),
                    ),
                    layout_timeline_tracks(window.project.timeline),
                )
                if item.segment_id == moving.segment_id
            )
            pixels_per_second = timeline_pixels_per_second(
                window.project.timeline.timeline_duration_seconds,
                canvas._viewport_width,
                canvas.get_zoom(),
            )
            self.assertEqual(
                round(
                    (preview.x - TIMELINE_HORIZONTAL_PADDING) / pixels_per_second * 1_000_000,
                ),
                6_000_000,
            )

        self._pointer_drag(
            canvas,
            drag_start,
            drag_target,
            while_held=assert_chain_preview,
        )
        moved = window.project.timeline.find(moving.segment_id)
        self.assertEqual((moved.track_id, moved.timeline_start_ticks), ("track-2", 6_000_000))
        self.assertEqual(window.project.timeline.timeline_duration_seconds, 8.0)
        self.assertEqual(moved.visual_transform, moving_transform)
        self.assertEqual(
            (
                window.project.timeline.find(chain_a.segment_id),
                window.project.timeline.find(chain_b.segment_id),
            ),
            original_chain,
        )
        self.assertEqual(window.project.timeline.find(unaffected.segment_id), original_unaffected)
        self.assertEqual(
            window.project.playhead_seconds,
            canvas.get_playhead_seconds(),
        )
        self.assertIn(
            moving.segment_id,
            window.selected_segment_ids,
            f"selected after first pointer drag: {window.selected_segment_ids!r}; "
            f"moving={moving.segment_id!r}; blocks="
            f"{[(item.segment_id, item.track_id, item.timeline_start_ticks) for item in window.project.timeline.blocks]!r}; "
            f"drag_happened={canvas._drag_happened!r}; drag_mode={canvas._drag_mode!r}",
        )
        chain_b_geometry = next(
            item
            for item in layout_timeline_segments(
                window.project.timeline,
                canvas._viewport_width,
                canvas.get_zoom(),
            )
            if item.segment_id == chain_b.segment_id
        )
        self._pointer_click(
            canvas,
            chain_b_geometry.x + chain_b_geometry.width / 2.0,
            chain_b_geometry.y + chain_b_geometry.height / 2.0,
            control=True,
        )
        if not press_states or not press_states[-1] & int(self.Gdk.ModifierType.CONTROL_MASK):
            self.skipTest(
                "true pointer modifier injection blocked: XTest Control_L was not "
                "observed by GTK for Ctrl-click multi-selection"
            )
        self.assertEqual(
            set(window.selected_segment_ids),
            {moving.segment_id, chain_b.segment_id},
        )

        moving_geometry = next(
            item
            for item in layout_timeline_segments(
                window.project.timeline,
                canvas._viewport_width,
                canvas.get_zoom(),
            )
            if item.segment_id == moving.segment_id
        )
        free_gap_target = timeline_x_from_ticks(
            1_000_000,
            window.project.timeline.timeline_duration_seconds,
            canvas._viewport_width,
            canvas.get_zoom(),
        )
        self._pointer_drag(
            canvas,
            (
                moving_geometry.x + moving_geometry.width / 2.0,
                moving_geometry.y + moving_geometry.height / 2.0,
            ),
            (free_gap_target, target_row.y + target_row.height / 2.0),
        )
        self.assertEqual(window.project.timeline.find(moving.segment_id).timeline_start_ticks, 0)
        self.assertEqual(
            set(window.selected_segment_ids),
            {moving.segment_id, chain_b.segment_id},
        )
        self.assertEqual(window.project.timeline.find(unaffected.segment_id), original_unaffected)

        self._pointer_click_segment(canvas, moving.segment_id)
        self.assertEqual(tuple(window.selected_segment_ids), (moving.segment_id,))
        self._xdotool("key", "ctrl+c")
        self._wait_until(
            lambda: bool(window._segment_clipboard),
            "copy hotkey did not populate clipboard",
        )
        copied_count = len(window.project.timeline.blocks)
        self._xdotool("key", "ctrl+v")
        self._wait_until(
            lambda: len(window.project.timeline.blocks) > copied_count,
            "paste hotkey did not add blocks",
        )

        pasted_id = window.selected_segment_id
        self.assertIsNotNone(pasted_id)
        count_before_split = len(window.project.timeline.blocks)
        self._pointer_click_segment(canvas, moving.segment_id)
        self.assertEqual(tuple(window.selected_segment_ids), (moving.segment_id,))
        self._xdotool("key", "b")
        self._wait_until(
            lambda: len(window.project.timeline.blocks) > count_before_split,
            "split hotkey did not split",
        )
        self.assertEqual(
            len(window.project.timeline.blocks),
            count_before_split + 1,
            f"split hotkey did not split; status={window.status_label.get_text()!r}; "
            f"selected={window.selected_segment_ids!r}; primary={window.selected_segment_id!r}; "
            f"playhead={window.project.playhead_seconds!r}; "
            f"canvas_playhead={canvas.get_playhead_seconds()!r}; "
            f"mouse={self._xdotool('getmouselocation').strip()!r}; "
            f"segment={window.project.timeline.find(pasted_id).to_dict()!r}",
        )

        split_geometry = next(
            item
            for item in layout_timeline_segments(
                window.project.timeline,
                canvas._viewport_width,
                canvas.get_zoom(),
            )
            if item.segment_id == window.selected_segment_id
        )
        invalid_y = rows[0].y - 10.0
        before_invalid_drop = window.project.timeline.to_dict()
        self._pointer_drag(
            canvas,
            (
                split_geometry.x + split_geometry.width / 2.0,
                split_geometry.y + split_geometry.height / 2.0,
            ),
            (split_geometry.x + split_geometry.width / 2.0, invalid_y),
        )
        self.assertEqual(window.project.timeline.to_dict(), before_invalid_drop)
        self.assertIn("invalid drop", window.status_label.get_text().lower())

        window._save_to(project_path)
        restored = load_project(project_path)
        self.assertEqual(restored.to_dict(), window.project.to_dict())
        for path, digest in source_hashes.items():
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), digest)


if __name__ == "__main__":
    unittest.main()
