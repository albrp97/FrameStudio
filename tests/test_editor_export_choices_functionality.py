from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import threading
import unittest
import uuid
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, cast
from unittest.mock import patch

from framestudio.app import create_editor_application
from framestudio.fps_policy import FrameRatePolicy
from framestudio.media import probe_media
from framestudio.model import Project
from framestudio.output_plan import (
    COMBINED_OUTPUT_MODE,
    FINAL_ONLY_OUTPUT_MODE,
    SOURCE_ONLY_OUTPUT_MODE,
    plan_project_outputs,
    resolve_output_selection,
    set_output_selection,
)
from framestudio.persistence import load_project, save_project
from tests import test_phase010_functionality as phase010_functionality
from tests.test_editor_source_outputs_functionality import (
    REPOSITORY_ROOT,
    _make_project,
    _sha256,
)
from tests.test_phase010_functionality import _pump_events, _visible_widget_text


def _portable_frame_rate_policy() -> FrameRatePolicy:
    return FrameRatePolicy(
        choice="custom",
        target_rate=24,
        custom_rate=24,
        enhancement_enabled=True,
        backend="ffmpeg-minterpolate",
    )


class EditorExportChoiceCliFunctionalityTests(unittest.TestCase):
    def setUp(self) -> None:
        if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
            self.skipTest("FFmpeg and ffprobe are required for TICKET114 functionality")
        self.runtime = TemporaryDirectory(
            dir=REPOSITORY_ROOT.parent,
            prefix="ticket114-export-choice-",
        )
        self.addCleanup(self.runtime.cleanup)
        self.root = Path(self.runtime.name)
        self.project, self.source_paths = _make_project(self.root / "fixtures")
        self.project.set_frame_rate_policy(_portable_frame_rate_policy())
        self.project.output_settings.pop("output_selection", None)
        self.project_path = self.root / "project.framestudio.json"
        save_project(self.project, self.project_path)

    def _run_cli(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(REPOSITORY_ROOT / "framestudio.py"),
                *arguments,
            ],
            cwd=REPOSITORY_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

    @staticmethod
    def _json_lines(value: str) -> list[dict[str, Any]]:
        return [
            cast(dict[str, Any], json.loads(line))
            for line in value.splitlines()
            if line.strip().startswith("{")
        ]

    def _success_payload(self, result: subprocess.CompletedProcess[str]) -> dict[str, Any]:
        payloads = [
            payload
            for payload in self._json_lines(result.stdout)
            if payload.get("command") == "export" and payload.get("ok") is True
        ]
        self.assertTrue(payloads, result.stdout)
        return payloads[-1]

    def _error_payload(self, result: subprocess.CompletedProcess[str]) -> dict[str, Any]:
        payloads = self._json_lines(result.stderr)
        self.assertTrue(payloads, result.stderr)
        return payloads[-1]

    def test_public_source_only_override_renders_verified_reels_without_final_consumer(self):
        source_hashes = {path: _sha256(path) for path in self.source_paths}
        final_destination = self.root / "published" / "edited.mp4"
        result = self._run_cli(
            "export",
            str(self.project_path),
            "--output",
            str(final_destination),
            "--output-mode",
            SOURCE_ONLY_OUTPUT_MODE,
            "--fps-choice",
            "custom",
            "--custom-fps",
            "24",
            "--enhance-fps",
            "--fps-backend",
            "ffmpeg-minterpolate",
            "--no-upscale-enhancement",
            "--ffmpeg",
            shutil.which("ffmpeg") or "ffmpeg",
            "--ffprobe",
            shutil.which("ffprobe") or "ffprobe",
            "--full-paths",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = self._success_payload(result)
        export = payload["export"]
        self.assertTrue(export["verified"])
        self.assertNotIn("final", export)
        self.assertEqual(export["output_plan"]["mode"], SOURCE_ONLY_OUTPUT_MODE)
        self.assertEqual(len(export["source_outputs"]), 6)
        self.assertEqual(
            {
                (
                    item["identity"]["track_id"],
                    item["identity"]["source_id"],
                )
                for item in export["source_outputs"]
            },
            {
                ("Track/One", "source-a"),
                ("Track/One", "source-b"),
                ("Track:Two", "source-a"),
                ("Track:Two", "source-c"),
                ("Track Three", "source-b"),
                ("Track-Four", "source-c"),
            },
        )
        for item in export["source_outputs"]:
            self.assertTrue(item["verified"])
            destination = Path(item["request"]["destination"])
            self.assertTrue(destination.is_file())
            verification = item["verification"]
            self.assertTrue(verification["content_sha256"])
            media = probe_media(destination)
            self.assertEqual((media.width, media.height), (1920, 1080))
            self.assertEqual(media.frame_rate, "24/1")
            self.assertTrue(media.has_audio_stream)
        self.assertFalse(final_destination.exists())
        self.assertEqual(
            {path: _sha256(path) for path in self.source_paths},
            source_hashes,
        )

    def test_public_mode_choices_route_plans_and_leave_persisted_selection_unchanged(self):
        set_output_selection(self.project, mode=COMBINED_OUTPUT_MODE)
        save_project(self.project, self.project_path)

        expected_source_count = {
            FINAL_ONLY_OUTPUT_MODE: 0,
            COMBINED_OUTPUT_MODE: 6,
            SOURCE_ONLY_OUTPUT_MODE: 6,
        }
        for mode, source_count in expected_source_count.items():
            result = self._run_cli(
                "export-plan",
                str(self.project_path),
                "--output",
                str(self.root / f"{mode}.mp4"),
                "--output-mode",
                mode,
                "--full-paths",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = self._json_lines(result.stdout)[-1]
            output_plan = payload["export"]["output_plan"]
            self.assertEqual(output_plan["mode"], mode)
            self.assertEqual(len(output_plan["source_outputs"]), source_count)
            self.assertEqual(
                output_plan["final"] is not None,
                mode in {FINAL_ONLY_OUTPUT_MODE, COMBINED_OUTPUT_MODE},
            )

        self.assertEqual(
            resolve_output_selection(load_project(self.project_path)).mode,
            COMBINED_OUTPUT_MODE,
        )

        invalid = load_project(self.project_path)
        invalid.output_settings["output_selection"] = {
            "include_final": False,
            "include_source_outputs": False,
        }
        invalid_path = self.root / "invalid-selection.framestudio.json"
        save_project(invalid, invalid_path)
        before = invalid_path.read_bytes()
        rejected = self._run_cli(
            "export-plan",
            str(invalid_path),
            "--output",
            str(self.root / "invalid.mp4"),
        )
        self.assertNotEqual(rejected.returncode, 0)
        error = self._error_payload(rejected)
        self.assertFalse(error["ok"])
        self.assertEqual(error["error"]["code"], "export_planning")
        self.assertIn("At least one output", error["error"]["message"])
        self.assertEqual(invalid_path.read_bytes(), before)

    def test_combined_multitrack_plan_and_render_publish_verified_outputs(self):
        set_output_selection(self.project, mode=COMBINED_OUTPUT_MODE)
        save_project(self.project, self.project_path)
        destination = self.root / "published" / "combined.mp4"

        planned = self._run_cli(
            "export-plan",
            str(self.project_path),
            "--output",
            str(destination),
            "--full-paths",
        )
        self.assertEqual(planned.returncode, 0, planned.stderr)
        plan_payload = self._json_lines(planned.stdout)[-1]["export"]["output_plan"]
        self.assertEqual(plan_payload["mode"], COMBINED_OUTPUT_MODE)
        self.assertIsNotNone(plan_payload["final"])
        self.assertEqual(len(plan_payload["source_outputs"]), 6)

        rendered = self._run_cli(
            "export",
            str(self.project_path),
            "--output",
            str(destination),
            "--output-mode",
            COMBINED_OUTPUT_MODE,
            "--fps-choice",
            "custom",
            "--custom-fps",
            "24",
            "--enhance-fps",
            "--fps-backend",
            "ffmpeg-minterpolate",
            "--no-upscale-enhancement",
            "--ffmpeg",
            shutil.which("ffmpeg") or "ffmpeg",
            "--ffprobe",
            shutil.which("ffprobe") or "ffprobe",
            "--full-paths",
        )
        self.assertEqual(rendered.returncode, 0, rendered.stderr)
        payload = self._success_payload(rendered)
        export = payload["export"]
        self.assertTrue(export["verified"])
        self.assertTrue(export["complete"])
        self.assertFalse(export["partial_success"])
        self.assertIsNotNone(export["final"])
        self.assertTrue(export["final"]["verified"])
        self.assertTrue(export["final"]["verification"]["content_sha256"])
        self.assertTrue(destination.is_file())
        final_media = probe_media(destination)
        self.assertEqual((final_media.width, final_media.height), (1920, 1080))
        self.assertEqual(final_media.frame_rate, "24/1")
        self.assertTrue(final_media.has_audio_stream)
        self.assertEqual(len(export["source_outputs"]), 6)
        for item in export["source_outputs"]:
            self.assertTrue(item["verified"])
            self.assertTrue(item["verification"]["content_sha256"])
            self.assertTrue(Path(item["request"]["destination"]).is_file())

    def test_empty_same_source_track_is_omitted_from_source_only_plan(self):
        project = load_project(self.project_path)
        source_hashes = {path: _sha256(path) for path in self.source_paths}
        track_two = project.timeline.track_by_id("Track:Two")
        removed_ids = tuple(block.segment_id for block in track_two.blocks)
        receipt = project.timeline.remove_blocks(removed_ids)
        self.assertEqual(receipt.removed_segment_ids, removed_ids)
        self.assertEqual(project.timeline.track_by_id("Track:Two").blocks, ())
        project.duration_seconds = project.timeline.timeline_duration_seconds
        project.validate()
        set_output_selection(project, mode=SOURCE_ONLY_OUTPUT_MODE)
        project_path = self.root / "empty-extra-track.framestudio.json"
        save_project(project, project_path)

        destination = self.root / "published" / "empty-extra-track.mp4"
        before_media = set(self.root.rglob("*.mp4"))
        planned = self._run_cli(
            "export-plan",
            str(project_path),
            "--output",
            str(destination),
            "--full-paths",
        )
        self.assertEqual(planned.returncode, 0, planned.stderr)
        payload = self._json_lines(planned.stdout)[-1]["export"]["output_plan"]
        self.assertEqual(payload["mode"], SOURCE_ONLY_OUTPUT_MODE)
        self.assertIsNone(payload["final"])
        outputs = payload["source_outputs"]
        identities = [
            (item["identity"]["track_id"], item["identity"]["source_id"]) for item in outputs
        ]
        self.assertEqual(
            identities,
            [
                ("Track/One", "source-a"),
                ("Track/One", "source-b"),
                ("Track Three", "source-b"),
                ("Track-Four", "source-c"),
            ],
        )
        self.assertNotIn(("Track:Two", "source-a"), identities)
        self.assertNotIn(("Track:Two", "source-c"), identities)
        self.assertTrue(all("Track:Two" not in item["destination"] for item in outputs))
        self.assertFalse(destination.exists())
        self.assertFalse((self.root / "published" / "empty-extra-track-sources").exists())
        self.assertEqual(set(self.root.rglob("*.mp4")), before_media)
        self.assertEqual(
            {path: _sha256(path) for path in self.source_paths},
            source_hashes,
        )

    def test_excluded_only_edit_rejects_source_choice_without_publication(self):
        excluded = load_project(self.project_path)
        for track in excluded.timeline.tracks or ():
            excluded.timeline.replace_track_blocks(
                track.track_id,
                tuple(replace(block, deleted=True) for block in track.blocks),
            )
        excluded.duration_seconds = excluded.timeline.timeline_duration_seconds
        set_output_selection(excluded, mode=SOURCE_ONLY_OUTPUT_MODE)
        excluded_path = self.root / "excluded-only.framestudio.json"
        save_project(excluded, excluded_path)

        destination = self.root / "published" / "excluded-only.mp4"
        rejected = self._run_cli(
            "export-plan",
            str(excluded_path),
            "--output",
            str(destination),
        )
        self.assertNotEqual(rejected.returncode, 0)
        error = self._error_payload(rejected)
        self.assertFalse(error["ok"])
        self.assertEqual(error["error"]["code"], "export_planning")
        self.assertIn("empty edit", error["error"]["message"].lower())
        self.assertFalse(destination.exists())
        self.assertFalse((self.root / "published" / "excluded-only-sources").exists())


class EditorExportChoiceGtkFunctionalityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        try:
            import gi

            gi.require_version("Gio", "2.0")
            gi.require_version("Gtk", "4.0")
            from gi.repository import Gio, GLib, Gtk
        except (ImportError, ValueError) as error:
            raise AssertionError("GTK 4 and PyGObject are required") from error
        if not Gtk.init_check():
            raise AssertionError("GTK 4 could not initialize on the test display")
        cls.Gio = Gio
        cls.GLib = GLib
        cls.Gtk = Gtk

    def setUp(self) -> None:
        if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
            self.skipTest("FFmpeg and ffprobe are required for TICKET114 GTK functionality")
        self.runtime = TemporaryDirectory(
            dir=REPOSITORY_ROOT.parent,
            prefix="ticket114-export-choice-gtk-",
        )
        self.addCleanup(self.runtime.cleanup)
        self.root = Path(self.runtime.name)
        self.state_root = self.root / "xdg-state"
        self.state_root.mkdir()
        self.previous_xdg_state_home = os.environ.get("XDG_STATE_HOME")
        os.environ["XDG_STATE_HOME"] = str(self.state_root)
        self.addCleanup(
            self._restore_xdg_state_home,
            self.previous_xdg_state_home,
        )
        self.project, self.source_paths = _make_project(self.root / "fixtures")
        self.project.set_frame_rate_policy(_portable_frame_rate_policy())
        self.project.output_settings.pop("output_selection", None)
        self.project_path = self.root / "project.framestudio.json"
        save_project(self.project, self.project_path)

        self.application, window_factory = create_editor_application(
            project_path=self.project_path,
            application_id=f"io.github.framestudio.ticket114.a{uuid.uuid4().hex}",
        )
        self.application.set_flags(
            self.application.get_flags() | self.Gio.ApplicationFlags.NON_UNIQUE,
        )
        self.addCleanup(self._quit_application)
        self.assertTrue(self.application.register(None))
        self.window = window_factory(self.application)
        self.addCleanup(self._close_panel)
        self.addCleanup(self._close_window)
        self._wait_until(
            lambda: (
                self.window.project is not None
                and not self.window._source_load_in_progress
                and self.window.project_path == self.project_path
            ),
            "production GTK project load did not complete",
        )

    def _restore_xdg_state_home(self, previous: str | None) -> None:
        if previous is None:
            os.environ.pop("XDG_STATE_HOME", None)
        else:
            os.environ["XDG_STATE_HOME"] = previous

    def _quit_application(self) -> None:
        application = getattr(self, "application", None)
        if application is not None:
            application.quit()

    def _close_window(self) -> None:
        window = getattr(self, "window", None)
        if window is not None:
            window.close()
            _pump_events(self.GLib, 10)

    def _close_panel(self) -> None:
        panel = getattr(self.window, "export_planning_window", None)
        if panel is not None:
            panel.close()
            _pump_events(self.GLib, 10)

    def _wait_until(
        self,
        predicate,
        message: str,
        rounds: int = 500,
    ) -> None:
        phase010_functionality.Phase010FunctionalityTests._wait_until(
            self,
            predicate,
            message,
            rounds=rounds,
        )

    def _open_panel(self):
        self._close_panel()
        planner_button = getattr(self.window, "export_button", None)
        self.assertIsInstance(
            planner_button,
            self.Gtk.Button,
            "main Export video control must be a native Gtk.Button",
        )
        if not isinstance(planner_button, self.Gtk.Button):
            return None
        self.assertTrue(
            planner_button.get_sensitive(),
            "main Export video planner button must stay sensitive so invalid "
            "choices can be repaired",
        )
        planner_button.emit("clicked")
        self._wait_until(
            lambda: (
                getattr(self.window, "export_planning_window", None) is not None
                and self.window.export_planning_window.get_visible()
            ),
            "production export-choice panel did not open",
        )
        return self.window.export_planning_window

    def _required_control(self, panel: Any, name: str):
        present = hasattr(panel, name)
        self.assertTrue(
            present,
            f"export-choice panel must expose native control {name!r}",
        )
        if not present:
            return None
        control = getattr(panel, name)
        self.assertIsNotNone(control, f"export-choice control {name!r} is None")
        return control

    def _summary_counts_or_none(self, panel: Any) -> tuple[int, int] | None:
        text = " | ".join(_visible_widget_text(panel))
        folder_match = re.search(
            r"\bfolders?\b[^0-9]{0,12}(\d+)|(\d+)[^A-Za-z0-9]{0,12}\bfolders?\b",
            text,
            flags=re.IGNORECASE,
        )
        pair_match = re.search(
            r"\bpairs?\b[^0-9]{0,12}(\d+)|(\d+)[^A-Za-z0-9]{0,12}\bpairs?\b",
            text,
            flags=re.IGNORECASE,
        )
        if folder_match is None or pair_match is None:
            return None
        folder_count = int(folder_match.group(1) or folder_match.group(2))
        pair_count = int(pair_match.group(1) or pair_match.group(2))
        return folder_count, pair_count

    def _assert_summary_counts(
        self,
        panel: Any,
        expected: tuple[int, int],
    ) -> None:
        counts = self._summary_counts_or_none(panel)
        self.assertIsNotNone(
            counts,
            "visible export summary must expose folder and pair counts; "
            f"text={_visible_widget_text(panel)!r}",
        )
        self.assertEqual(counts, expected)

    def _set_mode(
        self,
        panel: Any,
        *,
        include_final: bool,
        include_source_outputs: bool,
    ) -> None:
        final_toggle = self._required_control(panel, "final_output_toggle")
        source_toggle = self._required_control(panel, "source_output_toggle")
        if final_toggle is None or source_toggle is None:
            return
        self.assertIsInstance(final_toggle, self.Gtk.CheckButton)
        self.assertIsInstance(source_toggle, self.Gtk.CheckButton)
        if include_source_outputs:
            source_toggle.set_active(True)
        if include_final:
            final_toggle.set_active(True)
        else:
            final_toggle.set_active(False)
        if not include_source_outputs:
            source_toggle.set_active(False)
        _pump_events(self.GLib, 20)

    def _save_variant(self, populated_tracks: int) -> Path:
        variant = load_project(self.project_path)
        tracks = variant.timeline.tracks or ()
        for index, track in enumerate(tracks):
            if index >= populated_tracks:
                variant.timeline.replace_track_blocks(track.track_id, ())
        variant.duration_seconds = variant.timeline.timeline_duration_seconds
        variant.validate()
        path = self.root / f"tracks-{populated_tracks}.framestudio.json"
        save_project(variant, path)
        return path

    def _load_variant(self, path: Path) -> None:
        self._close_panel()
        self.window._load_project_path(path)
        self._wait_until(
            lambda: (
                self.window.project is not None
                and self.window.project_path == path
                and not self.window._source_load_in_progress
            ),
            f"production GTK did not load {path.name}",
        )

    def _find_widget(self, widget: Any, predicate):
        if predicate(widget):
            return widget
        child = widget.get_first_child()
        while child is not None:
            found = self._find_widget(child, predicate)
            if found is not None:
                return found
            child = child.get_next_sibling()
        return None

    def _find_button(self, widget: Any, label: str):
        return self._find_widget(
            widget,
            lambda current: (isinstance(current, self.Gtk.Button) and current.get_label() == label),
        )

    def _find_check_button(self, widget: Any, label: str):
        return self._find_widget(
            widget,
            lambda current: (
                isinstance(current, self.Gtk.CheckButton) and current.get_label() == label
            ),
        )

    def _required_check_button(self, panel: Any, label: str):
        control = self._find_check_button(panel, label)
        self.assertIsNotNone(
            control,
            f"export panel must expose native check button {label!r}",
        )
        if control is None:
            return None
        self.assertIsInstance(control, self.Gtk.CheckButton)
        self.assertTrue(
            control.get_sensitive(),
            f"export panel check button {label!r} must remain user-operable",
        )
        return control

    def _required_render_button(self, panel: Any):
        render_button = self._find_button(panel, "Start export")
        self.assertIsNotNone(
            render_button,
            "export-choice panel must expose its native Render/Start export button",
        )
        if render_button is None:
            return None
        self.assertIsInstance(render_button, self.Gtk.Button)
        return render_button

    def _export_filename(self, panel: Any) -> str:
        entry = self._find_widget(
            panel,
            lambda current: (
                isinstance(current, self.Gtk.Entry)
                and current.get_text()
                .strip()
                .casefold()
                .endswith(
                    (".mkv", ".mov", ".mp4", ".webm"),
                )
            ),
        )
        if entry is not None:
            return entry.get_text().strip()
        self.fail("export panel did not expose a populated output filename entry")

    def _assert_enhancement_summary_rows(self, panel: Any) -> None:
        fps_toggle = self._required_check_button(
            panel,
            "Enhance sources below the target rate",
        )
        upscale_toggle = self._required_check_button(
            panel,
            "Upscale eligible videos (SuperUltraCompact)",
        )
        if fps_toggle is None or upscale_toggle is None:
            return
        text = " | ".join(_visible_widget_text(panel))
        for label in ("FPS enhancement", "Upscale enhancement"):
            self.assertRegex(
                text,
                rf"{re.escape(label)}\s*\|\s*(?:On|Off)\b",
                f"visible export summary must retain {label!r}; text={text!r}",
            )
        for label in ("Videos to FPS enhance", "Videos to upscale"):
            self.assertRegex(
                text,
                rf"{re.escape(label)}\s*\|\s*\d+\b",
                f"visible export summary must retain numeric {label!r}; text={text!r}",
            )

    def _has_invalid_choice_message(self, panel: Any) -> bool:
        text = " ".join(_visible_widget_text(panel)).lower()
        return (
            "at least one output" in text
            or ("select" in text and "output" in text)
            or ("output" in text and "required" in text)
        )

    def _wait_for_export_plan(self, panel: Any) -> None:
        try:
            self._wait_until(
                lambda: "Estimated processing time" in _visible_widget_text(panel),
                "production GTK export plan did not finish preparing",
                rounds=3000,
            )
        except AssertionError as error:
            raise AssertionError(
                f"{error}; panel text={_visible_widget_text(panel)!r}",
            ) from error

    def test_native_planner_reuses_preflight_and_applies_latest_filename_and_active_counts(self):
        project = self.window.project
        project.set_frame_rate_policy(
            FrameRatePolicy(
                choice="60", target_rate=60, enhancement_enabled=True, backend="rve-4.26"
            )
        )
        omitted_id = project.sources[2].source_id
        for block in tuple(project.timeline.segment_items):
            if block.source_id == omitted_id:
                project.timeline.set_deleted(block.segment_id, True)
        source_hashes = {path: _sha256(path) for path in self.source_paths}
        before_outputs = set(self.root.rglob("*.mp4"))
        model = self.root / "model.pkl"
        model.touch()
        defaults = {
            "fps_python": Path(sys.executable),
            "site_packages": self.root,
            "rve_model": model,
            "rve_root": self.root,
            "rve_shims": self.root,
        }
        started = threading.Event()
        release = threading.Event()

        def preflight(*_args, **_kwargs):
            started.set()
            if not release.wait(timeout=10):
                raise RuntimeError("Functionality fixture preflight was not released")
            return None

        with (
            patch("framestudio.interpolation._rve_defaults", return_value=defaults),
            patch("framestudio_fps.rve_unavailable_reason", side_effect=preflight) as check,
        ):
            panel = self._open_panel()
            try:
                self._wait_until(started.is_set, "planner did not start its runtime preflight")
                entry = self._find_widget(
                    panel,
                    lambda current: (
                        isinstance(current, self.Gtk.Entry) and current.get_text().endswith(".mp4")
                    ),
                )
                self.assertIsNotNone(entry)
                for index in range(20):
                    entry.set_text(f"typing-{index}.mp4")
            finally:
                release.set()
            self._wait_for_export_plan(panel)
            self.assertEqual(check.call_count, 1)
            self.assertEqual(self._export_filename(panel), "typing-19.mp4")
            grid = self._find_widget(panel, lambda current: isinstance(current, self.Gtk.Grid))
            rows = {}
            index = 0
            while grid.get_child_at(0, index) is not None:
                rows[grid.get_child_at(0, index).get_text()] = grid.get_child_at(
                    1, index
                ).get_text()
                index += 1
            self.assertEqual(rows["Videos to FPS enhance"], "2")
            self.assertEqual(rows["Videos to upscale"], "2")
            self.assertTrue(self._required_render_button(panel).get_sensitive())
            entry.set_text("final-choice.mp4")
            self._wait_for_export_plan(panel)
            self.assertEqual(check.call_count, 1)
            self.assertTrue(self._required_render_button(panel).get_sensitive())
        self.assertEqual(set(self.root.rglob("*.mp4")), before_outputs)
        self.assertEqual({path: _sha256(path) for path in self.source_paths}, source_hashes)

    def test_native_output_controls_default_and_update_counts_for_one_to_four_tracks(self):
        expected_pairs = (2, 4, 5, 6)
        for populated_tracks, pair_count in enumerate(expected_pairs, start=1):
            self._load_variant(self._save_variant(populated_tracks))
            panel = self._open_panel()
            final_toggle = self._required_control(panel, "final_output_toggle")
            source_toggle = self._required_control(panel, "source_output_toggle")
            if final_toggle is None or source_toggle is None:
                return
            self.assertIsInstance(final_toggle, self.Gtk.CheckButton)
            self.assertIsInstance(source_toggle, self.Gtk.CheckButton)
            self.assertTrue(final_toggle.get_active())
            self.assertFalse(source_toggle.get_active())
            self.assertEqual(
                resolve_output_selection(self.window.project).mode,
                FINAL_ONLY_OUTPUT_MODE,
            )
            self._assert_enhancement_summary_rows(panel)
            default_render_button = self._required_render_button(panel)
            if default_render_button is not None:
                self._wait_for_export_plan(panel)
                self._wait_until(
                    default_render_button.get_sensitive,
                    "default final-only export did not enable its Render button",
                )

            self._set_mode(
                panel,
                include_final=True,
                include_source_outputs=True,
            )
            self.assertEqual(
                resolve_output_selection(self.window.project).mode,
                COMBINED_OUTPUT_MODE,
            )
            expected_counts = (populated_tracks, pair_count)
            self._wait_until(
                lambda panel=panel, expected=expected_counts: (
                    self._summary_counts_or_none(panel) == expected
                ),
                f"export summary did not update for {populated_tracks} populated tracks",
            )
            self._assert_enhancement_summary_rows(panel)

    def test_native_output_choice_persists_and_neither_blocks_without_publication(self):
        panel = self._open_panel()
        self._wait_for_export_plan(panel)
        self._set_mode(
            panel,
            include_final=False,
            include_source_outputs=True,
        )
        self._wait_until(
            lambda: (
                isinstance(self.window.project, Project)
                and self.window.project.output_settings.get("output_selection", {}).get("mode")
                == SOURCE_ONLY_OUTPUT_MODE
            ),
            "source-only GUI choice was not applied to the project state",
        )
        self._assert_enhancement_summary_rows(panel)
        source_only_render_button = self._required_render_button(panel)
        if source_only_render_button is not None:
            self._wait_until(
                source_only_render_button.get_sensitive,
                "source-only choice incorrectly disabled the Render button",
            )
            self.assertTrue(source_only_render_button.get_sensitive())
        self._close_panel()

        persisted_path = self.root / "persisted-source-only.framestudio.json"
        self.window._save_to(persisted_path)
        persisted = load_project(persisted_path)
        self.assertEqual(
            resolve_output_selection(persisted).mode,
            SOURCE_ONLY_OUTPUT_MODE,
        )
        self._load_variant(persisted_path)

        panel = self._open_panel()
        final_toggle = self._required_control(panel, "final_output_toggle")
        source_toggle = self._required_control(panel, "source_output_toggle")
        if final_toggle is None or source_toggle is None:
            return
        self.assertFalse(final_toggle.get_active())
        self.assertTrue(source_toggle.get_active())
        self._assert_enhancement_summary_rows(panel)

        before_settings = deepcopy(self.window.project.output_settings)
        before_media = set(self.root.rglob("*.mp4"))
        source_toggle.set_active(False)
        self._wait_until(
            lambda: self._has_invalid_choice_message(panel),
            "neither-output selection did not show an explicit visible error",
        )
        self.assertEqual(self.window.project.output_settings, before_settings)
        self.assertEqual(set(self.root.rglob("*.mp4")), before_media)
        render_button = self._required_render_button(panel)
        if render_button is not None:
            self.assertFalse(render_button.get_sensitive())
        self.assertTrue(
            panel.get_visible(),
            "invalid output choice must leave the planner open for recovery",
        )
        planner_button = getattr(self.window, "export_button", None)
        self.assertIsInstance(planner_button, self.Gtk.Button)
        if isinstance(planner_button, self.Gtk.Button):
            self.assertTrue(
                planner_button.get_sensitive(),
                "main Export video planner button must remain enabled after "
                "invalid output selection",
            )

    def test_native_source_only_render_completes_and_resets_export_state(self):
        panel = self._open_panel()
        self._wait_for_export_plan(panel)
        fps_toggle = self._required_check_button(
            panel,
            "Enhance sources below the target rate",
        )
        upscale_toggle = self._required_check_button(
            panel,
            "Upscale eligible videos (SuperUltraCompact)",
        )
        if fps_toggle is None or upscale_toggle is None:
            return
        fps_toggle.set_active(False)
        upscale_toggle.set_active(False)
        _pump_events(self.GLib, 20)
        self._wait_for_export_plan(panel)
        fps_toggle.set_active(True)
        _pump_events(self.GLib, 20)
        self._wait_for_export_plan(panel)
        self._set_mode(
            panel,
            include_final=False,
            include_source_outputs=True,
        )
        self._wait_until(
            lambda: (resolve_output_selection(self.window.project).mode == SOURCE_ONLY_OUTPUT_MODE),
            "native source-only selection was not applied before rendering",
        )
        render_button = self._required_render_button(panel)
        if render_button is None:
            return
        self._wait_until(
            render_button.get_sensitive,
            "native source-only Render button did not become sensitive",
        )
        destination = self.project_path.parent / self._export_filename(panel)
        output_plan = plan_project_outputs(
            self.window.project,
            destination,
            mode=SOURCE_ONLY_OUTPUT_MODE,
        )
        source_hashes = {path: _sha256(path) for path in self.source_paths}
        render_button.emit("clicked")
        self._wait_until(
            lambda: (
                not self.window._export_in_progress
                and "Exported 6 source output(s)" in self.window.status_label.get_text()
            ),
            "native source-only render did not complete successfully",
            rounds=6000,
        )
        self.assertFalse(self.window._export_in_progress)
        self.assertIsNone(self.window._export_cancel_event)
        self.assertIsNone(self.window._export_project_snapshot)
        self.assertFalse(self.window.cancel_export_button.get_visible())
        self.assertTrue(self.window.export_button.get_sensitive())
        self.assertFalse(destination.exists())
        self.assertIsNotNone(output_plan.source_output_root)
        batch_result = self.window._last_export_batch_result
        self.assertIsNotNone(batch_result)
        self.assertTrue(batch_result.complete)
        self.assertEqual(len(batch_result.results), 6)
        self.assertTrue(all(result.state.value == "verified" for result in batch_result.results))
        for request in output_plan.source_outputs:
            self.assertTrue(
                request.destination.is_file(),
                f"native source-only output missing: {request.destination}",
            )
            media = probe_media(request.destination)
            self.assertEqual((media.width, media.height), (1920, 1080))
            self.assertEqual(media.frame_rate, "24/1")
            self.assertTrue(media.has_audio_stream)
        self.assertEqual(
            {path: _sha256(path) for path in self.source_paths},
            source_hashes,
        )


if __name__ == "__main__":
    unittest.main()
