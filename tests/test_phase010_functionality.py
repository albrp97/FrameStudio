from __future__ import annotations

import hashlib
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from fractions import Fraction
from io import StringIO
from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch

from framestudio.app import create_editor_application
from framestudio.audio import (
    AUDIO_POLICY_VERSION,
    AudioDecision,
    pending_audio_decision,
)
from framestudio.persistence import autosave_path, load_autosave, load_project
from framestudio.timeline import (
    layout_timeline_segments,
    layout_timeline_tracks,
    timeline_x_from_ticks,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_PARENT = (
    Path(
        os.environ.get(
            "FRAMESTUDIO_PHASE010_ARTIFACT_DIR",
            str(REPOSITORY_ROOT / ".phase010-ticket109-artifacts"),
        ),
    )
    .expanduser()
    .resolve()
)


def _pump_events(glib: Any, rounds: int = 20) -> None:
    context = glib.MainContext.default()
    for _ in range(rounds):
        if context.pending():
            context.iteration(False)
        time.sleep(0.01)


def _visible_widget_text(widget: Any) -> list[str]:
    texts: list[str] = []
    if widget.get_visible():
        get_text = getattr(widget, "get_text", None)
        if callable(get_text):
            text = get_text()
            if text:
                texts.append(str(text))
    child = widget.get_first_child()
    while child is not None:
        texts.extend(_visible_widget_text(child))
        child = child.get_next_sibling()
    return texts


def _snapshot_widget(widget: Any, destination: Path, Gtk: Any) -> None:
    from gi.repository import GLib, Gsk

    # The software Cairo renderer avoids GL texture uploads, which abort the
    # process under the software GL stack used by CI.
    renderer = Gsk.CairoRenderer()
    if not renderer.realize(None):
        renderer = None
    try:
        _snapshot_widget_with_renderer(widget, destination, Gtk, GLib, renderer)
    finally:
        if renderer is not None:
            renderer.unrealize()


def _snapshot_widget_with_renderer(
    widget: Any,
    destination: Path,
    Gtk: Any,
    GLib: Any,
    renderer: Any,
) -> None:
    snapshot_widgets = [widget]
    child = getattr(widget, "get_child", lambda: None)()
    if child is not None:
        snapshot_widgets.append(child)
    for snapshot_widget in snapshot_widgets:
        paintable = Gtk.WidgetPaintable.new(snapshot_widget)
        for _ in range(600):
            _pump_events(GLib, 1)
            current_image = paintable.get_current_image()
            if current_image is not None and hasattr(current_image, "save_to_png"):
                if current_image.save_to_png(str(destination)):
                    return
            width = snapshot_widget.get_width()
            height = snapshot_widget.get_height()
            if width > 0 and height > 0:
                snapshot = Gtk.Snapshot.new()
                paintable.snapshot(snapshot, width, height)
                node = snapshot.to_node()
                if node is not None and renderer is not None:
                    texture = renderer.render_texture(node, None)
                    if texture is not None and texture.save_to_png(str(destination)):
                        return
    get_title = getattr(widget, "get_title", None)
    title = get_title() if callable(get_title) else None
    if title and shutil.which("xdotool") and shutil.which("import"):
        search = subprocess.run(
            ["xdotool", "search", "--onlyvisible", "--name", title],
            capture_output=True,
            text=True,
            check=False,
        )
        window_ids = tuple(line.strip() for line in search.stdout.splitlines() if line.strip())
        if search.returncode == 0 and len(window_ids) == 1:
            screenshot = subprocess.run(
                ["import", "-window", window_ids[0], str(destination)],
                capture_output=True,
                text=True,
                check=False,
            )
            if screenshot.returncode == 0 and destination.is_file():
                return
    raise AssertionError(
        "GTK produced no render node for the editor window after bounded frame wait"
    )


class GtkEventPumpTests(unittest.TestCase):
    def test_continuously_pending_context_yields_between_bounded_rounds(self):
        glib = Mock()
        context = glib.MainContext.default.return_value
        context.pending.return_value = True
        context.iteration.side_effect = [
            False,
            False,
            False,
            AssertionError("event pump did not yield between rounds"),
        ]

        with patch("tests.test_phase010_functionality.time.sleep") as sleep:
            _pump_events(glib, rounds=3)

        self.assertEqual(context.iteration.call_count, 3)
        self.assertEqual(sleep.call_count, 3)


class Phase010FunctionalityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            import gi

            gi.require_version("Gdk", "4.0")
            gi.require_version("Gtk", "4.0")
            from gi.repository import Gdk, Gio, GLib, Gtk
        except (ImportError, ValueError) as error:
            raise AssertionError("GTK 4 and PyGObject are required") from error
        if not Gtk.init_check():
            raise AssertionError("GTK 4 could not initialize on the test display")
        ARTIFACT_PARENT.mkdir(parents=True, exist_ok=True)
        cls.Gdk = Gdk
        cls.Gio = Gio
        cls.GLib = GLib
        cls.Gtk = Gtk

    @staticmethod
    def _create_fixture(destination: Path, video_source: str, frequency: str) -> None:
        ffmpeg = shutil.which("ffmpeg")
        if ffmpeg is None:
            raise AssertionError("ffmpeg is required for generated GTK functionality fixtures")
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
                video_source,
                "-f",
                "lavfi",
                "-i",
                f"sine=frequency={frequency}:sample_rate=48000",
                "-t",
                "1.0",
                "-shortest",
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-c:a",
                "aac",
                "-b:a",
                "64k",
                str(destination),
            ],
            cwd=str(REPOSITORY_ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise AssertionError(f"Could not create fixture {destination.name}: {result.stderr}")

    def _wait_until(self, predicate, message: str, rounds: int = 400) -> None:
        for _ in range(rounds):
            _pump_events(self.GLib, 1)
            if predicate():
                return
        status = getattr(self.window, "status_label", None)
        status_text = "" if status is None else status.get_text()
        raise AssertionError(f"{message}; last status={status_text!r}")

    def _timeline_click_position(self, segment_id: str) -> tuple[float, float]:
        canvas = self.window.timeline_canvas
        geometries = layout_timeline_segments(
            self.window.segment_timeline,
            canvas._viewport_width,
            canvas.get_zoom(),
        )
        clip = next(geometry for geometry in geometries if geometry.segment_id == segment_id)
        return clip.x + (clip.width / 2.0), 70.0

    def _click_timeline_segment(
        self,
        segment_id: str,
        *,
        control: bool = False,
        shift: bool = False,
    ) -> None:
        canvas = self.window.timeline_canvas
        x, y = self._timeline_click_position(segment_id)
        if control:
            # GI signal emission cannot carry a modifier-state event; use the
            # production selection path with the requested modifier state.
            canvas._select_clip(segment_id, additive=True, range_selection=False)
        elif shift:
            canvas._select_clip(segment_id, additive=False, range_selection=True)
        else:
            gesture = canvas._click_gesture
            gesture.reset()
            gesture.emit("pressed", 1, x, y)
            gesture.emit("released", 1, x, y)
            gesture.set_state(self.Gtk.EventSequenceState.NONE)
            gesture.reset()
        self._pump_display_events()

    def _pump_display_events(self) -> None:
        _pump_events(self.GLib, 10)

    def _restore_xdg_state_home(self, previous: str | None) -> None:
        if previous is None:
            os.environ.pop("XDG_STATE_HOME", None)
        else:
            os.environ["XDG_STATE_HOME"] = previous

    def _close_window(self) -> None:
        window = getattr(self, "window", None)
        if window is not None:
            window.close()
            self._pump_display_events()

    def _quit_application(self) -> None:
        application = getattr(self, "application", None)
        if application is not None:
            application.quit()

    def setUp(self):
        self.runtime_directory = tempfile.TemporaryDirectory(
            prefix="phase010-ticket109-runtime-",
            dir=str(REPOSITORY_ROOT.parent),
        )
        self.addCleanup(self.runtime_directory.cleanup)
        runtime_root = Path(self.runtime_directory.name)
        self.fixture_root = runtime_root / "fixtures"
        self.state_root = runtime_root / "xdg-state"
        self.fixture_root.mkdir()
        self.state_root.mkdir()
        self.artifact_root = Path(
            tempfile.mkdtemp(
                prefix="phase010-ticket109-run-",
                dir=str(ARTIFACT_PARENT),
            ),
        )
        self.source_a = self.fixture_root / "phase010_fixture_a.mp4"
        self.source_b = self.fixture_root / "phase010_fixture_b.mp4"
        self._create_fixture(
            self.source_a,
            "testsrc2=size=320x180:rate=12",
            "440",
        )
        self._create_fixture(
            self.source_b,
            "color=c=blue:size=640x360:rate=24",
            "660",
        )
        self.previous_xdg_state_home = os.environ.get("XDG_STATE_HOME")
        self.addCleanup(self._restore_xdg_state_home, self.previous_xdg_state_home)
        os.environ["XDG_STATE_HOME"] = str(self.state_root)
        self.application, self.window_factory = create_editor_application()
        self.addCleanup(self._quit_application)
        self.application.set_application_id(
            f"io.github.framestudio.editor.test_{runtime_root.name.replace('-', '_')}",
        )
        self.application.set_flags(
            self.application.get_flags() | self.Gio.ApplicationFlags.NON_UNIQUE,
        )
        self.assertTrue(self.application.register(None))
        self.window = self.window_factory(self.application)
        self.addCleanup(self._close_window)
        self._pump_display_events()
        self.window._load_source((self.source_a, self.source_b))
        self._wait_until(
            lambda: (self.window.project is not None and not self.window._source_load_in_progress),
            "production source load did not complete",
        )
        self.source_hashes = {
            self.source_a: hashlib.sha256(self.source_a.read_bytes()).hexdigest(),
            self.source_b: hashlib.sha256(self.source_b.read_bytes()).hexdigest(),
        }
        self.autosave = autosave_path()
        self.assertTrue(self.autosave.is_file())
        persisted = load_autosave()
        self.assertEqual(
            {Path(source.path) for source in persisted.sources},
            {
                self.source_a,
                self.source_b,
            },
        )

    def test_migrated_project_reopens_and_displays_playback(self):
        window = self.window
        project_path = self.fixture_root / "migrated.framestudio.json"
        original_project_id = window.project.project_id
        original_segment_ids = tuple(
            segment.segment_id for segment in window.project.timeline.segment_items
        )
        window._save_to(project_path)
        self.assertTrue(project_path.is_file())
        persisted = load_project(project_path)
        self.assertEqual(persisted.schema_version, 4)
        self.assertEqual(persisted.timeline.timing_mode, "legacy-ripple")
        window._load_project_path(project_path)
        self._wait_until(
            lambda: window.project_path == project_path and window.project.schema_version == 4,
            "production GTK did not attach the migrated project",
        )
        self.assertEqual(window.project.project_id, original_project_id)
        self.assertEqual(
            tuple(segment.segment_id for segment in window.project.timeline.segment_items),
            original_segment_ids,
        )
        window.preview.set_paintable(None)
        window._on_play_clicked(None)
        self._wait_until(
            lambda: window.preview.get_paintable() is not None,
            "production FFmpeg playback did not display a frame after migration",
        )
        window.controller.pause()
        window.controller.seek(0.25)
        self.assertAlmostEqual(window.controller.snapshot().position_seconds, 0.25)
        for source_path, expected_hash in self.source_hashes.items():
            self.assertEqual(hashlib.sha256(source_path.read_bytes()).hexdigest(), expected_hash)

    def test_selected_video_details(self):
        from framestudio.app_project import (
            _finish_audio_analysis,
            _finish_source_audio_analysis,
            _invalidate_audio_analysis,
        )

        window = self.window
        segments = window.project.timeline.segment_items
        first_segment = next(
            segment
            for segment in segments
            if Path(window.project.source_by_id(segment.source_id).path).name
            == "phase010_fixture_a.mp4"
        )
        second_segment = next(
            segment
            for segment in segments
            if Path(window.project.source_by_id(segment.source_id).path).name
            == "phase010_fixture_b.mp4"
        )

        self.assertIsInstance(window, self.Gtk.ApplicationWindow)
        self._click_timeline_segment(first_segment.segment_id)
        self.assertEqual(
            window.timeline_selection_label.get_text(),
            "Selected video: phase010_fixture_a.mp4 | Dimensions: 320×180 | FPS: 12",
        )
        initial_snapshot = self.artifact_root / "changed-initial-selected-video-details.png"
        _snapshot_widget(window.timeline_selection_label, initial_snapshot, self.Gtk)

        self._click_timeline_segment(second_segment.segment_id)
        self.assertEqual(window.selected_segment_id, second_segment.segment_id)
        self.assertEqual(
            window.timeline_selection_label.get_text(),
            "Selected video: phase010_fixture_b.mp4 | Dimensions: 640×360 | FPS: 24",
        )

        self._click_timeline_segment(first_segment.segment_id, control=True)
        self.assertEqual(
            window.selected_segment_ids,
            (second_segment.segment_id, first_segment.segment_id),
        )
        self.assertEqual(window.selected_segment_id, first_segment.segment_id)
        self.assertIn("phase010_fixture_a.mp4", window.timeline_selection_label.get_text())

        self._click_timeline_segment(second_segment.segment_id, shift=True)
        self.assertEqual(
            window.selected_segment_ids,
            tuple(segment.segment_id for segment in segments),
        )
        self.assertEqual(window.selected_segment_id, second_segment.segment_id)
        self.assertIn("phase010_fixture_b.mp4", window.timeline_selection_label.get_text())

        second_source = window.project.source_by_id(second_segment.source_id)
        pending = pending_audio_decision(second_source)
        failed_decision = AudioDecision(
            status="failed",
            gain_db=0.0,
            policy_version=AUDIO_POLICY_VERSION,
            measurements=None,
            source_fingerprint=pending.source_fingerprint,
            audio_metadata=pending.audio_metadata,
            diagnostic="synthetic delayed audio callback failure",
        )
        # Complete the production callback directly so delayed worker ordering
        # is deterministic; all app/window/selection/persistence paths remain real.
        _invalidate_audio_analysis(window)
        generation = window._audio_analysis_generation
        window._audio_analysis_in_progress = True
        window._audio_analysis_source_ids = (second_segment.source_id,)
        _finish_source_audio_analysis(
            window,
            window.project,
            generation,
            second_source,
            failed_decision,
            1,
            1,
        )
        _finish_audio_analysis(window, window.project, generation)
        self._pump_display_events()
        self.assertFalse(window._audio_analysis_in_progress)
        self.assertIn(
            "synthetic delayed audio callback failure",
            window.status_label.get_text(),
        )
        self.assertIn("phase010_fixture_b.mp4", window.timeline_selection_label.get_text())

        self._click_timeline_segment(first_segment.segment_id, control=True)
        self._click_timeline_segment(second_segment.segment_id, control=True)
        self.assertEqual(window.selected_segment_ids, ())
        self.assertEqual(window.timeline_selection_label.get_text(), "No video selected")

        source_b = window.project.source_by_id(second_segment.source_id)
        original_metadata = dict(source_b.metadata)
        source_b.metadata.pop("width")
        source_b.metadata.pop("height")
        self._click_timeline_segment(second_segment.segment_id)
        self.assertEqual(
            window.timeline_selection_label.get_text(),
            "Selected video: metadata unavailable",
        )
        source_b.metadata.update(original_metadata)
        self._click_timeline_segment(second_segment.segment_id)
        self.assertEqual(
            window.timeline_selection_label.get_text(),
            "Selected video: phase010_fixture_b.mp4 | Dimensions: 640×360 | FPS: 24",
        )

        visible_text = _visible_widget_text(window)
        self.assertFalse(any(text.startswith("Audio decisions:") for text in visible_text))
        self.assertFalse(window.audio_status_label.get_visible())
        self.assertIsNone(window.project_path)
        self.assertEqual(
            {
                self.source_a: hashlib.sha256(self.source_a.read_bytes()).hexdigest(),
                self.source_b: hashlib.sha256(self.source_b.read_bytes()).hexdigest(),
            },
            self.source_hashes,
        )
        persisted = load_autosave()
        self.assertEqual(
            {Path(source.path) for source in persisted.sources},
            {
                self.source_a,
                self.source_b,
            },
        )

        final_snapshot = self.artifact_root / "changed-final-selected-video-details.png"
        _snapshot_widget(window.timeline_selection_label, final_snapshot, self.Gtk)
        self.assertTrue(final_snapshot.is_file())

    def test_complete_edit_and_delivery_journey(self):
        started = time.monotonic()
        evidence_path = self.artifact_root / "ticket125-integrated-evidence.json"
        evidence: dict[str, Any] = {
            "ticket": "TICKET-125",
            "entry": (
                "python3 -m unittest "
                "tests.test_phase010_functionality.Phase010FunctionalityTests."
                "test_complete_edit_and_delivery_journey"
            ),
            "artifact_directory": str(self.artifact_root),
            "commands": [],
            "assertions": [],
        }

        def persist_evidence() -> None:
            evidence["elapsed_seconds"] = round(time.monotonic() - started, 3)
            evidence_path.write_text(
                json.dumps(evidence, indent=2, sort_keys=True, default=str),
                encoding="utf-8",
            )

        self.addCleanup(persist_evidence)

        def assertion(name: str, detail: Any = True) -> None:
            evidence["assertions"].append({"name": name, "detail": detail})

        def run_command(
            name: str,
            command: list[str],
            *,
            timeout: float = 600.0,
            env: dict[str, str] | None = None,
        ) -> subprocess.CompletedProcess[str]:
            started_command = time.monotonic()
            command_env = os.environ.copy()
            command_env["FRAMESTUDIO_PHASE010_ARTIFACT_DIR"] = str(self.artifact_root)
            if env:
                command_env.update(env)
            result = subprocess.run(
                command,
                cwd=str(REPOSITORY_ROOT),
                env=command_env,
                capture_output=True,
                text=True,
                check=False,
                timeout=timeout,
            )
            stdout_path = self.artifact_root / f"{name}-stdout.txt"
            stderr_path = self.artifact_root / f"{name}-stderr.txt"
            stdout_path.write_text(result.stdout, encoding="utf-8")
            stderr_path.write_text(result.stderr, encoding="utf-8")
            evidence["commands"].append(
                {
                    "name": name,
                    "command": command,
                    "returncode": result.returncode,
                    "elapsed_seconds": round(time.monotonic() - started_command, 3),
                    "stdout": str(stdout_path),
                    "stderr": str(stderr_path),
                },
            )
            return result

        import gi

        from framestudio.audio_compositor import AUDIO_SAMPLE_RATE, fixed_pan_vector
        from framestudio.composition import VisualTransform
        from framestudio.export_session import discover_export_session
        from framestudio.layout_plan import plan_project_layout
        from framestudio.media import probe_media
        from framestudio.model import Project
        from framestudio.output_plan import (
            COMBINED_OUTPUT_MODE,
            FINAL_ONLY_OUTPUT_MODE,
            SOURCE_ONLY_OUTPUT_MODE,
        )
        from framestudio.persistence import save_project
        from tests.test_editor_audio_compositor import _audio_settings
        from tests.test_editor_audio_compositor_functionality import (
            _decoded_pcm,
            _tone_amplitude,
        )
        from tests.test_editor_composed_preview_functionality import _texture_rgba
        from tests.test_editor_flexible_output_recovery_functionality import (
            _make_audio_marker_source,
        )
        from tests.test_editor_layout_plan_functionality import make_block
        from tests.test_editor_removal_controls_functionality import (
            NativeRemovalControlsFunctionalityTests as RemovalControlsFunctionalityTests,
        )
        from tests.test_editor_track_drag_functionality import (
            TrackDragFunctionalityTests,
        )
        from tests.test_editor_video_compositor_functionality import (
            _decode_frame,
            _make_marker_source,
            _marker_center,
            _mean_luma,
            _scaled_region,
            _sha256,
            _white_centroid,
        )

        gi.require_version("GdkPixbuf", "2.0")
        from gi.repository import GdkPixbuf

        ffmpeg = shutil.which("ffmpeg")
        ffprobe = shutil.which("ffprobe")
        self.assertIsNotNone(ffmpeg)
        self.assertIsNotNone(ffprobe)
        assert ffmpeg is not None
        assert ffprobe is not None

        def mux_audio(
            video: Path,
            destination: Path,
            *,
            frequency: int,
            channels: int,
        ) -> None:
            result = subprocess.run(
                [
                    ffmpeg,
                    "-hide_banner",
                    "-loglevel",
                    "error",
                    "-nostdin",
                    "-y",
                    "-i",
                    str(video),
                    "-f",
                    "lavfi",
                    "-i",
                    (f"sine=frequency={frequency}:sample_rate={AUDIO_SAMPLE_RATE}:duration=4"),
                    "-map",
                    "0:v:0",
                    "-map",
                    "1:a:0",
                    "-c:v",
                    "copy",
                    "-c:a",
                    "aac",
                    "-b:a",
                    "96k",
                    "-ar",
                    str(AUDIO_SAMPLE_RATE),
                    "-ac",
                    str(channels),
                    "-channel_layout",
                    "stereo" if channels == 2 else "mono",
                    "-shortest",
                    "-movflags",
                    "+faststart",
                    str(destination),
                ],
                cwd=str(REPOSITORY_ROOT),
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode != 0:
                raise AssertionError(
                    f"Could not create {destination.name}: {result.stderr}",
                )

        journey_root = self.fixture_root / "ticket125-journey"
        journey_root.mkdir()
        source_a = _make_audio_marker_source(
            journey_root,
            "A",
            color="red",
            frequency=440,
            duration=4.0,
            stereo=True,
        )
        source_b_video = _make_marker_source(
            journey_root,
            ".B-video.mp4",
            640,
            360,
            "24/1",
            "blue",
        )
        source_b = journey_root / "B.mp4"
        mux_audio(source_b_video, source_b, frequency=660, channels=1)
        source_c = _make_marker_source(
            journey_root,
            "C.mp4",
            320,
            180,
            "30/1",
            "green",
        )
        source_d_pcm = _make_audio_marker_source(
            journey_root,
            ".D-input",
            color="yellow",
            frequency=880,
            duration=4.0,
            stereo=False,
        )
        source_d = journey_root / "D.mp4"
        mux_audio(source_d_pcm, source_d, frequency=880, channels=1)
        source_p_video = _make_marker_source(
            journey_root,
            ".P-video.mp4",
            480,
            270,
            "30/1",
            "purple",
        )
        source_p = journey_root / "P.mp4"
        mux_audio(source_p_video, source_p, frequency=1230, channels=1)
        source_paths = (source_a, source_b, source_c, source_d, source_p)
        source_hashes = {path: _sha256(path) for path in source_paths}
        assertion(
            "mixed_fixture_inputs",
            {
                "sources": [path.name for path in source_paths],
                "source_hashes": {str(path): digest for path, digest in source_hashes.items()},
            },
        )

        source_metadata = tuple((path, probe_media(path).metadata()) for path in source_paths)
        expected_source_metadata = {
            "A.mp4": ((320, 180), "10/1", True, 2),
            "B.mp4": ((640, 360), "24/1", True, 1),
            "C.mp4": ((320, 180), "30/1", False, None),
            "D.mp4": ((320, 180), "10/1", True, 1),
            "P.mp4": ((480, 270), "30/1", True, 1),
        }
        for path, metadata in source_metadata:
            dimensions, frame_rate, has_audio, channels = expected_source_metadata[path.name]
            self.assertTrue(path.is_file())
            self.assertEqual((metadata["width"], metadata["height"]), dimensions)
            self.assertEqual(metadata["frame_rate"], frame_rate)
            self.assertEqual(metadata.get("audio_stream_present", False), has_audio)
            if has_audio:
                self.assertEqual(metadata["audio_sample_rate"], AUDIO_SAMPLE_RATE)
                self.assertEqual(metadata["audio_channels"], channels)
            else:
                self.assertIsNone(metadata.get("audio_codec"))
                self.assertIsNone(metadata.get("audio_sample_rate"))
                self.assertIsNone(metadata.get("audio_channels"))
        assertion("input_filename_dimensions_fps_and_noaudio")

        project = Project.create_synchronized_multi(
            source_metadata,
            project_id="ticket-125-integrated-journey",
        )
        for track_id in ("track-2", "track-3", "track-4"):
            project.timeline.add_track(track_id)
        source_ids = {
            path.name: source.source_id
            for path, source in zip(source_paths, project.sources or (), strict=True)
        }
        project.timeline.replace_track_blocks(
            "track-1",
            (
                make_block(
                    segment_id="track1-a",
                    source_id=source_ids["A.mp4"],
                    track_id="track-1",
                    source_start=0.0,
                    source_end=1.0,
                    timeline_start=1.0,
                    timeline_end=2.0,
                    visual_transform=VisualTransform(
                        zoom=1.15,
                        offset_x=40.0,
                        offset_y=-20.0,
                    ),
                ),
                make_block(
                    segment_id="track1-b",
                    source_id=source_ids["B.mp4"],
                    track_id="track-1",
                    source_start=0.0,
                    source_end=1.0,
                    timeline_start=2.0,
                    timeline_end=3.0,
                ),
            ),
        )
        project.timeline.replace_track_blocks(
            "track-2",
            (
                make_block(
                    segment_id="track2-a",
                    source_id=source_ids["A.mp4"],
                    track_id="track-2",
                    source_start=1.0,
                    source_end=2.0,
                    timeline_start=1.0,
                    timeline_end=2.0,
                    visual_transform=VisualTransform(
                        zoom=1.3,
                        offset_x=-50.0,
                        offset_y=25.0,
                    ),
                ),
                make_block(
                    segment_id="track2-c",
                    source_id=source_ids["C.mp4"],
                    track_id="track-2",
                    source_start=0.0,
                    source_end=1.5,
                    timeline_start=2.0,
                    timeline_end=3.5,
                ),
            ),
        )
        project.timeline.replace_track_blocks(
            "track-3",
            (
                make_block(
                    segment_id="track3-d",
                    source_id=source_ids["D.mp4"],
                    track_id="track-3",
                    source_start=0.0,
                    source_end=0.5,
                    timeline_start=1.0,
                    timeline_end=1.5,
                ),
            ),
        )
        project.timeline.replace_track_blocks(
            "track-4",
            (
                make_block(
                    segment_id="track4-p",
                    source_id=source_ids["P.mp4"],
                    track_id="track-4",
                    source_start=0.0,
                    source_end=0.5,
                    timeline_start=1.25,
                    timeline_end=1.75,
                ),
            ),
        )
        for source in project.sources or ():
            if source.metadata.get("audio_stream_present", False):
                project.set_source_audio_settings(
                    source.source_id,
                    _audio_settings(
                        source,
                        peak_db=-20.0,
                        sample_count=round(
                            float(source.metadata["duration_seconds"]) * AUDIO_SAMPLE_RATE,
                        ),
                    ),
                )
        project.duration_seconds = project.timeline.timeline_duration_seconds
        project.validate()

        seed_path = journey_root / "ticket125-seed.framestudio.json"
        save_project(project, seed_path)
        window = self.window
        window.set_title("FrameStudio T125 Integrated Journey")
        window.present()
        window._load_project_path(seed_path)
        self._wait_until(
            lambda: (
                window.project_path == seed_path
                and window.project is not None
                and not window._source_load_in_progress
            ),
            "integrated project did not reopen in GTK",
            rounds=3000,
        )
        self.assertEqual(
            tuple(source.source_id for source in window.project.sources or ()),
            tuple(source_ids[path.name] for path in source_paths),
        )
        for source in window.project.sources or ():
            if source.metadata.get("audio_stream_present", False):
                window.project.set_source_audio_settings(
                    source.source_id,
                    _audio_settings(
                        source,
                        peak_db=-20.0,
                        sample_count=round(
                            float(source.metadata["duration_seconds"]) * AUDIO_SAMPLE_RATE,
                        ),
                    ),
                )
        window.project.validate()
        window._refresh_timeline(window.selected_segment_id)
        before_snapshot = self.artifact_root / "changed-before-editing.png"
        _snapshot_widget(window, before_snapshot, self.Gtk)
        self.assertTrue(before_snapshot.is_file())
        assertion("gtk_project_reopen_and_before_snapshot", before_snapshot)

        removal = RemovalControlsFunctionalityTests()
        removal.window = window
        removal.GLib = self.GLib
        removal.Gtk = self.Gtk
        removal.window_title = window.get_title()
        dragger = TrackDragFunctionalityTests()
        dragger.window = window
        dragger.GLib = self.GLib
        dragger.window_title = window.get_title()

        def segment_items() -> tuple[Any, ...]:
            return tuple(window.project.timeline.segment_items)

        def find_block(segment_id: str) -> Any:
            return next(item for item in segment_items() if item.segment_id == segment_id)

        def find_blocks(*, source_id: str | None = None, track_id: str | None = None):
            return tuple(
                item
                for item in segment_items()
                if (source_id is None or item.source_id == source_id)
                and (track_id is None or item.track_id == track_id)
            )

        def click_segment(segment_id: str) -> None:
            removal._click_segment(segment_id)
            self.assertIn(segment_id, window.selected_segment_ids)

        def seek_preview(position: float) -> tuple[bytes, int, int]:
            window.preview.set_paintable(None)
            window._request_timeline_preview(position)
            self._wait_until(
                lambda: (
                    window.controller is not None
                    and abs(window.controller.snapshot().position_seconds - position) < 0.04
                ),
                f"GTK preview did not seek to {position:.2f}s",
                rounds=3000,
            )
            self._wait_until(
                lambda: window.preview.get_paintable() is not None,
                f"GTK preview did not display a frame at {position:.2f}s",
                rounds=3000,
            )
            return _texture_rgba(
                window.preview.get_paintable(),
                fallback_path=self.artifact_root / f"preview-{position:.2f}.png",
                gdk_pixbuf=GdkPixbuf,
            )

        def rgba_to_rgb(pixels: bytes) -> bytes:
            return bytes(
                channel
                for offset in range(0, len(pixels), 4)
                for channel in pixels[offset : offset + 3]
            )

        self.assertTrue(window.preview.get_paintable() is None or window.backend is not None)
        self.assertFalse(getattr(window.backend, "audio_preview_enabled", False))
        zero_pixels, preview_width, preview_height = seek_preview(0.73)
        zero_rgb = rgba_to_rgb(zero_pixels)
        self.assertLess(_mean_luma(zero_rgb), 25.0)
        preview_process_commands: list[tuple[str, ...]] = []
        real_popen = subprocess.Popen

        def trace_preview_process(*args: Any, **kwargs: Any) -> Any:
            command = args[0] if args else kwargs.get("args")
            if isinstance(command, (list, tuple)) and command:
                command_tuple = tuple(str(item) for item in command)
                if Path(command_tuple[0]).name in {"ffmpeg", "ffplay"}:
                    preview_process_commands.append(command_tuple)
            return real_popen(*args, **kwargs)

        with patch(
            "framestudio.ffmpeg_playback.subprocess.Popen",
            side_effect=trace_preview_process,
        ):
            silent_pixels, _, _ = seek_preview(3.2)
        stats_getter = getattr(window.backend, "precise_preview_stats", None)
        native_preview = stats_getter() if callable(stats_getter) else {}
        native_engine = native_preview.get("selected_engine")
        preview_video_commands = [
            command for command in preview_process_commands if Path(command[0]).name == "ffmpeg"
        ]
        preview_trace_path = self.artifact_root / "silent-preview-process-trace.json"
        preview_trace_path.write_text(
            json.dumps([list(command) for command in preview_process_commands], indent=2) + "\n",
            encoding="utf-8",
        )
        if native_engine in {"cpu", "cuda", "mixed"}:
            self.assertIsInstance(native_preview.get("helper_pid"), int)
            self.assertTrue(native_preview.get("physical_frames"))
        else:
            self.assertTrue(preview_video_commands)
        self.assertFalse(
            any(Path(command[0]).name == "ffplay" for command in preview_process_commands),
        )
        self.assertTrue(all("-an" in command for command in preview_video_commands))
        self.assertTrue(
            all(
                "-vn" not in command and "0:a:0" not in command
                for command in preview_video_commands
            ),
        )
        silent_rgb = rgba_to_rgb(silent_pixels)
        self.assertGreater(_mean_luma(silent_rgb), 25.0)
        _white_centroid(
            silent_rgb,
            (0, 0, preview_width, preview_height),
            width=preview_width,
        )
        active_pixels, _, _ = seek_preview(1.87)
        active_rgb = rgba_to_rgb(active_pixels)
        self.assertGreater(_mean_luma(active_rgb), 25.0)
        _white_centroid(
            active_rgb,
            (0, 0, preview_width, preview_height),
            width=preview_width,
        )
        triplicate_pixels, _, _ = seek_preview(2.25)
        self.assertGreater(_mean_luma(rgba_to_rgb(triplicate_pixels)), 25.0)
        assertion(
            "silent_zero_active_preview_and_decoded_active_frames",
            {
                "preview_size": (preview_width, preview_height),
                "sampled_positions": (0.73, 3.2, 1.87, 2.25),
                "preview_video_only_commands": len(preview_video_commands),
                "native_preview_engine": native_engine,
                "preview_audio_process_launched": any(
                    Path(command[0]).name == "ffplay" for command in preview_process_commands
                ),
                "preview_process_trace": preview_trace_path,
            },
        )

        click_segment("track1-b")
        self.assertEqual(
            window.timeline_selection_label.get_text().split("|")[0].strip(),
            "Selected video: B.mp4",
        )
        window._request_timeline_preview(2.5)
        self._wait_until(
            lambda: (
                window.controller is not None
                and abs(window.controller.snapshot().position_seconds - 2.5) < 0.04
            ),
            "playhead did not reach physical split position",
        )
        removal._physical_key("b")
        self._wait_until(
            lambda: len(
                find_blocks(source_id=source_ids["B.mp4"], track_id="track-1"),
            )
            == 2,
            "physical B split did not create two source cuts",
        )
        b_parts = find_blocks(source_id=source_ids["B.mp4"], track_id="track-1")
        self.assertAlmostEqual(sum(item.duration_seconds for item in b_parts), 1.0)
        assertion(
            "physical_split_and_original_details",
            {
                "b_parts": [item.segment_id for item in b_parts],
                "durations": [item.duration_seconds for item in b_parts],
            },
        )

        right_b = max(b_parts, key=lambda item: item.timeline_start_ticks)
        click_segment(right_b.segment_id)
        removal._physical_key("BackSpace")
        self._wait_until(
            lambda: right_b.segment_id not in {item.segment_id for item in segment_items()},
            "physical Backspace did not remove the selected block",
        )
        self.assertTrue(window.undo_removal_button.get_sensitive())
        removal._click_widget_center(window.undo_removal_button)
        self._wait_until(
            lambda: right_b.segment_id in {item.segment_id for item in segment_items()},
            "physical Undo did not restore the removed block",
        )
        self.assertEqual(
            len(find_blocks(source_id=source_ids["B.mp4"], track_id="track-1")),
            2,
        )
        assertion("physical_backspace_ripple_and_undo")

        first_a = next(
            item
            for item in find_blocks(source_id=source_ids["A.mp4"], track_id="track-1")
            if item.timeline_start_seconds < 2.0
        )
        click_segment(first_a.segment_id)
        removal._xdotool("key", "--clearmodifiers", "ctrl+c")
        _pump_events(self.GLib, 10)
        removal._xdotool("key", "--clearmodifiers", "ctrl+v")
        self._wait_until(
            lambda: len(find_blocks(source_id=source_ids["A.mp4"], track_id="track-1")) == 2,
            "physical copy/paste did not create the collision-safe A copy",
        )
        track1_a_blocks = find_blocks(source_id=source_ids["A.mp4"], track_id="track-1")
        copied_a = max(track1_a_blocks, key=lambda item: item.timeline_start_ticks)
        self.assertNotEqual(copied_a.segment_id, first_a.segment_id)
        self.assertGreaterEqual(
            copied_a.timeline_start_seconds,
            max(
                item.timeline_end_seconds
                for item in find_blocks(track_id="track-1")
                if item.segment_id != copied_a.segment_id
            ),
        )
        assertion(
            "physical_copy_paste_collision_safe",
            {"source_a_blocks": [item.segment_id for item in track1_a_blocks]},
        )

        click_segment(first_a.segment_id)
        window.focus_zoom_spin.set_value(1.25)
        window.focus_offset_x_spin.set_value(70.0)
        window.focus_offset_y_spin.set_value(-30.0)
        _pump_events(self.GLib, 20)
        second_a = next(
            item for item in find_blocks(source_id=source_ids["A.mp4"], track_id="track-2")
        )
        click_segment(second_a.segment_id)
        window.focus_zoom_spin.set_value(1.5)
        window.focus_offset_x_spin.set_value(-90.0)
        window.focus_offset_y_spin.set_value(50.0)
        _pump_events(self.GLib, 20)
        c_block = next(item for item in find_blocks(source_id=source_ids["C.mp4"]))
        click_segment(c_block.segment_id)
        removal._click_widget_center(window.triplicate_button)
        self._wait_until(
            lambda: (
                find_block(c_block.segment_id).triplicate is not None
                and find_block(c_block.segment_id).triplicate.enabled
            ),
            "physical triplicate control did not persist three linked crops",
        )
        self.assertNotEqual(
            find_block(first_a.segment_id).visual_transform,
            find_block(second_a.segment_id).visual_transform,
        )
        assertion(
            "distinct_transforms_and_physical_triplicate",
            {
                "track1_transform": find_block(first_a.segment_id).visual_transform,
                "track2_transform": find_block(second_a.segment_id).visual_transform,
                "triplicate": find_block(c_block.segment_id).triplicate,
            },
        )

        d_block = find_block("track3-d")
        p_block = find_block("track4-p")
        canvas = window.timeline_canvas
        d_geometry = next(
            item
            for item in layout_timeline_segments(
                window.segment_timeline,
                canvas._viewport_width,
                canvas.get_zoom(),
            )
            if item.segment_id == d_block.segment_id
        )
        track_rows = {row.track_id: row for row in layout_timeline_tracks(window.segment_timeline)}
        start_drag = (
            d_geometry.x + d_geometry.width / 2.0,
            d_geometry.y + d_geometry.height / 2.0,
        )
        target_drag = (
            timeline_x_from_ticks(
                2_750_000,
                window.segment_timeline.timeline_duration_seconds,
                canvas._viewport_width,
                canvas.get_zoom(),
            ),
            track_rows["track-4"].y + track_rows["track-4"].height / 2.0,
        )
        dragger._xdotool(
            "windowfocus",
            "--sync",
            dragger._pointer_window_id(),
        )
        start_screen = dragger._pointer_screen_point(canvas, *start_drag)
        target_screen = dragger._pointer_screen_point(canvas, *target_drag)
        dragger._xdotool(
            "mousemove",
            "--sync",
            str(start_screen[0]),
            str(start_screen[1]),
        )
        dragger._xdotool("mousedown", "1")
        _pump_events(self.GLib, 10)
        self.assertEqual(canvas._drag_mode, "segment")
        dragger._xdotool(
            "mousemove",
            "--sync",
            str(target_screen[0]),
            str(target_screen[1]),
        )
        _pump_events(self.GLib, 30)
        dragger._xdotool("mouseup", "1")
        _pump_events(self.GLib, 30)
        self._wait_until(
            lambda: find_block("track3-d").track_id == "track-4",
            "physical drag did not route D to the fourth track",
        )
        moved_d = find_block("track3-d")
        self.assertGreaterEqual(moved_d.timeline_start_seconds, p_block.timeline_end_seconds)
        assertion(
            "physical_collision_safe_drag_across_tracks",
            {
                "track_id": moved_d.track_id,
                "start": moved_d.timeline_start_seconds,
                "existing_track4_end": p_block.timeline_end_seconds,
            },
        )

        moved_geometry = next(
            item
            for item in layout_timeline_segments(
                window.segment_timeline,
                canvas._viewport_width,
                canvas.get_zoom(),
            )
            if item.segment_id == moved_d.segment_id
        )
        track_rows = {row.track_id: row for row in layout_timeline_tracks(window.segment_timeline)}
        return_start = (
            moved_geometry.x + moved_geometry.width / 2.0,
            moved_geometry.y + moved_geometry.height / 2.0,
        )
        return_target = (
            timeline_x_from_ticks(
                d_block.timeline_start_ticks
                + (d_block.timeline_end_ticks - d_block.timeline_start_ticks) // 2,
                window.segment_timeline.timeline_duration_seconds,
                canvas._viewport_width,
                canvas.get_zoom(),
            ),
            track_rows["track-3"].y + track_rows["track-3"].height / 2.0,
        )
        dragger._xdotool("windowfocus", "--sync", dragger._pointer_window_id())
        return_screen_start = dragger._pointer_screen_point(canvas, *return_start)
        return_screen_target = dragger._pointer_screen_point(canvas, *return_target)
        dragger._xdotool(
            "mousemove",
            "--sync",
            str(return_screen_start[0]),
            str(return_screen_start[1]),
        )
        dragger._xdotool("mousedown", "1")
        _pump_events(self.GLib, 10)
        self.assertEqual(canvas._drag_mode, "segment")
        dragger._xdotool(
            "mousemove",
            "--sync",
            str(return_screen_target[0]),
            str(return_screen_target[1]),
        )
        _pump_events(self.GLib, 20)
        dragger._xdotool("mouseup", "1")
        _pump_events(self.GLib, 30)
        self._wait_until(
            lambda: find_block("track3-d").track_id == "track-3",
            "physical drag did not restore D to the third track",
        )
        self.assertAlmostEqual(find_block("track3-d").timeline_start_seconds, 1.0)

        active_project_path = journey_root / "ticket125-active.framestudio.json"
        window._save_to(active_project_path)
        self.assertTrue(active_project_path.is_file())
        active_project = load_project(active_project_path)
        active_plan = plan_project_layout(active_project)
        active_counts = tuple(len(interval.active_blocks) for interval in active_plan.intervals)
        if set(active_counts) != {0, 1, 2, 3, 4}:
            self.fail(
                "unexpected active counts "
                f"{active_counts}; blocks="
                f"{[(item.segment_id, item.track_id, item.timeline_start_seconds, item.timeline_end_seconds, item.deleted) for item in active_project.timeline.segment_items]}",
            )
        self.assertTrue(any(interval.is_black for interval in active_plan.intervals))
        self.assertTrue(
            any(
                len(interval.active_blocks) == 4 and len(interval.slots) == 4
                for interval in active_plan.intervals
            ),
        )
        assertion(
            "zero_to_four_layout_intervals",
            {"active_counts": active_counts},
        )

        def cli_command(
            mode: str,
            project_path: Path,
            destination: Path,
            *,
            ffmpeg_path: str | None = None,
            recovery_mode: str | None = None,
        ) -> list[str]:
            command = [
                sys.executable,
                str(REPOSITORY_ROOT / "framestudio.py"),
                "export",
                str(project_path),
                "--output",
                str(destination),
                "--output-mode",
                mode,
                "--fps-choice",
                "custom",
                "--custom-fps",
                "10",
                "--no-enhance-fps",
                "--no-upscale-enhancement",
                "--ffmpeg",
                ffmpeg_path or ffmpeg,
                "--ffprobe",
                ffprobe,
                "--full-paths",
            ]
            if recovery_mode is not None:
                command.append(f"--{recovery_mode}")
            return command

        def json_lines(value: str) -> list[dict[str, Any]]:
            parsed: list[dict[str, Any]] = []
            for line in value.splitlines():
                if not line.lstrip().startswith("{"):
                    continue
                item = json.loads(line)
                if isinstance(item, dict):
                    parsed.append(item)
            return parsed

        def export_payload(result: subprocess.CompletedProcess[str]) -> dict[str, Any]:
            payloads = json_lines(result.stdout) + json_lines(result.stderr)
            exports = [item for item in payloads if item.get("command") == "export"]
            self.assertTrue(
                exports,
                f"public CLI produced no export payload:\n{result.stdout}\n{result.stderr}",
            )
            return exports[-1]

        final_destination = journey_root / "ticket125-active-final.mp4"
        active_result = run_command(
            "active-final-only",
            cli_command(
                FINAL_ONLY_OUTPUT_MODE,
                active_project_path,
                final_destination,
            ),
            timeout=600.0,
        )
        self.assertEqual(active_result.returncode, 0, active_result.stderr)
        active_payload = export_payload(active_result)
        active_export = active_payload["export"]
        self.assertTrue(active_export["verified"])
        self.assertEqual(len(active_export["results"]), 1)
        self.assertEqual(active_export["results"][0]["state"], "verified")
        self.assertTrue(final_destination.is_file())
        final_metadata = probe_media(final_destination).metadata()
        self.assertEqual(
            (final_metadata["width"], final_metadata["height"]),
            (1920, 1080),
        )
        self.assertEqual(float(Fraction(str(final_metadata["frame_rate"]))), 10.0)
        self.assertAlmostEqual(float(final_metadata["duration_seconds"]), 4.0, delta=0.25)
        self.assertEqual(final_metadata["audio_sample_rate"], AUDIO_SAMPLE_RATE)
        self.assertEqual(final_metadata["audio_channels"], 2)

        def probe_frame_count(path: Path) -> int:
            return int(
                subprocess.run(
                    [
                        ffprobe,
                        "-v",
                        "error",
                        "-select_streams",
                        "v:0",
                        "-count_frames",
                        "-show_entries",
                        "stream=nb_read_frames",
                        "-of",
                        "default=nw=1:nk=1",
                        str(path),
                    ],
                    capture_output=True,
                    text=True,
                    check=True,
                ).stdout.strip(),
            )

        def assert_rendered_slot_positions(
            destination: Path,
            layout_plan: Any,
            frame_count: int,
            active_counts: tuple[int, ...],
        ) -> list[dict[str, Any]]:
            positions: list[dict[str, Any]] = []
            for active_count in active_counts:
                candidates = tuple(
                    interval
                    for interval in layout_plan.intervals
                    if len(interval.active_blocks) == active_count
                    and not any(slot.is_triplicate for slot in interval.slots)
                )
                self.assertTrue(
                    candidates,
                    f"no non-triplicate interval found for {active_count} active blocks",
                )
                interval = candidates[0]
                midpoint_tick = (interval.start_tick + interval.end_tick) // 2
                frame_index = min(
                    frame_count - 1,
                    max(0, round(midpoint_tick / 1_000_000 * 10.0)),
                )
                decoded = _decode_frame(destination, frame_index)
                for slot in interval.slots:
                    crop = slot.crop
                    self.assertIsNotNone(crop)
                    assert crop is not None
                    region = _scaled_region(
                        crop.target.x,
                        crop.target.y,
                        crop.target.width,
                        crop.target.height,
                    )
                    expected_full = _marker_center(crop)
                    expected = (
                        expected_full[0] * 384 / 1920,
                        expected_full[1] * 216 / 1080,
                    )
                    actual = _white_centroid(decoded, region)
                    self.assertAlmostEqual(
                        actual[0],
                        expected[0],
                        delta=12.0,
                        msg=(
                            f"active={active_count} frame={frame_index} "
                            f"block={slot.block.block_id} x={actual[0]} expected={expected[0]}"
                        ),
                    )
                    self.assertAlmostEqual(
                        actual[1],
                        expected[1],
                        delta=12.0,
                        msg=(
                            f"active={active_count} frame={frame_index} "
                            f"block={slot.block.block_id} y={actual[1]} expected={expected[1]}"
                        ),
                    )
                    positions.append(
                        {
                            "active_count": active_count,
                            "block_id": slot.block.block_id,
                            "frame_index": frame_index,
                            "actual": actual,
                            "expected": expected,
                        },
                    )
            return positions

        active_frame_count = probe_frame_count(final_destination)
        self.assertEqual(active_frame_count, 40)
        self.assertLess(_mean_luma(_decode_frame(final_destination, 5)), 20.0)
        for frame_index in (15, 25, min(37, active_frame_count - 1)):
            decoded = _decode_frame(final_destination, frame_index)
            self.assertGreater(_mean_luma(decoded), 25.0)
            _white_centroid(decoded, (0, 0, 384, 216))
        active_slot_positions = assert_rendered_slot_positions(
            final_destination,
            active_plan,
            active_frame_count,
            (1, 2, 3, 4),
        )
        final_samples, final_sample_rate, final_channels = _decoded_pcm(final_destination)
        self.assertEqual(final_sample_rate, AUDIO_SAMPLE_RATE)
        self.assertEqual(final_channels, 2)
        available_frames = len(final_samples) // 2
        tone_windows = {
            440: (1.05, 1.45),
            880: (1.05, 1.45),
            660: (2.05, 2.45),
            1230: (1.30, 1.70),
        }
        for frequency, (start_seconds, end_seconds) in tone_windows.items():
            audio_start = min(
                available_frames,
                max(0, round(start_seconds * AUDIO_SAMPLE_RATE)),
            )
            audio_end = min(
                available_frames,
                max(audio_start + 1, round(end_seconds * AUDIO_SAMPLE_RATE)),
            )
            self.assertGreater(
                max(
                    _tone_amplitude(
                        final_samples,
                        start_frame=audio_start,
                        end_frame=audio_end,
                        frequency=frequency,
                        channel=channel,
                    )
                    for channel in (0, 1)
                ),
                0.001,
            )
        left_440 = _tone_amplitude(
            final_samples,
            start_frame=round(1.10 * AUDIO_SAMPLE_RATE),
            end_frame=round(1.45 * AUDIO_SAMPLE_RATE),
            frequency=440,
            channel=0,
        )
        right_440 = _tone_amplitude(
            final_samples,
            start_frame=round(1.10 * AUDIO_SAMPLE_RATE),
            end_frame=round(1.45 * AUDIO_SAMPLE_RATE),
            frequency=440,
            channel=1,
        )
        left_880 = _tone_amplitude(
            final_samples,
            start_frame=round(1.10 * AUDIO_SAMPLE_RATE),
            end_frame=round(1.45 * AUDIO_SAMPLE_RATE),
            frequency=880,
            channel=0,
        )
        right_880 = _tone_amplitude(
            final_samples,
            start_frame=round(1.10 * AUDIO_SAMPLE_RATE),
            end_frame=round(1.45 * AUDIO_SAMPLE_RATE),
            frequency=880,
            channel=1,
        )
        self.assertGreater(left_440, right_440 * 1.5)
        self.assertGreater(right_880, left_880 * 1.5)
        self.assertEqual(fixed_pan_vector(1), (0.0,))
        self.assertEqual(fixed_pan_vector(2), (-25.0, 25.0))
        self.assertEqual(fixed_pan_vector(3), (-25.0, 0.0, 25.0))
        self.assertEqual(fixed_pan_vector(4), (-25.0, 25.0, -50.0, 50.0))
        assertion(
            "active_final_metadata_frames_decoded_pixels_and_audio",
            {
                "metadata": final_metadata,
                "frame_count": active_frame_count,
                "destination": final_destination,
                "rendered_slot_positions": active_slot_positions,
                "relative_pan": {
                    "440_left": left_440,
                    "440_right": right_440,
                    "880_left": left_880,
                    "880_right": right_880,
                },
            },
        )

        click_segment("track3-d")
        removal._physical_key("Delete")
        self._wait_until(
            lambda: find_block("track3-d").deleted,
            "physical Delete did not exclude D",
        )
        click_segment("track4-p")
        removal._physical_key("Delete")
        self._wait_until(
            lambda: find_block("track4-p").deleted,
            "physical Delete did not exclude P",
        )
        self.assertEqual(
            len(
                [
                    item
                    for item in segment_items()
                    if item.track_id in {"track-3", "track-4"} and not item.deleted
                ],
            ),
            0,
        )
        final_project_path = journey_root / "ticket125-final.framestudio.json"
        window._save_to(final_project_path)
        final_project_bytes = final_project_path.read_bytes()
        self.assertTrue(final_project_path.is_file())
        window._load_project_path(final_project_path)
        self._wait_until(
            lambda: (
                window.project_path == final_project_path
                and window.project is not None
                and not window._source_load_in_progress
            ),
            "saved excluded project did not reopen",
            rounds=3000,
        )
        reopened = load_project(final_project_path)
        self.assertEqual(
            {
                (item.segment_id, item.source_id, item.track_id, item.deleted)
                for item in reopened.timeline.segment_items
            },
            {
                (item.segment_id, item.source_id, item.track_id, item.deleted)
                for item in window.project.timeline.segment_items
            },
        )
        reopened_a = next(
            item
            for item in reopened.timeline.segment_items
            if item.segment_id == first_a.segment_id
        )
        reopened_second_a = next(
            item
            for item in reopened.timeline.segment_items
            if item.segment_id == second_a.segment_id
        )
        reopened_c = next(
            item
            for item in reopened.timeline.segment_items
            if item.segment_id == c_block.segment_id
        )
        self.assertNotEqual(
            reopened_a.visual_transform,
            reopened_second_a.visual_transform,
        )
        self.assertIsNotNone(reopened_c.triplicate)
        self.assertTrue(reopened_c.triplicate.enabled)
        self.assertEqual(
            tuple(item.segment_id for item in reopened.timeline.segment_items),
            tuple(item.segment_id for item in window.project.timeline.segment_items),
        )
        after_snapshot = self.artifact_root / "changed-after-editing-reopen.png"
        _snapshot_widget(window, after_snapshot, self.Gtk)
        self.assertTrue(after_snapshot.is_file())
        assertion(
            "physical_delete_save_reopen_ids_cuts_copies_transforms",
            {
                "project": final_project_path,
                "segment_ids": [item.segment_id for item in reopened.timeline.segment_items],
            },
        )

        open_result = run_command(
            "public-cli-open",
            [
                sys.executable,
                str(REPOSITORY_ROOT / "framestudio.py"),
                "open",
                str(final_project_path),
                "--full-paths",
            ],
        )
        self.assertEqual(open_result.returncode, 0, open_result.stderr)
        reopen_result = run_command(
            "public-cli-reopen",
            [
                sys.executable,
                str(REPOSITORY_ROOT / "framestudio.py"),
                "reopen",
                str(final_project_path),
                "--full-paths",
            ],
        )
        self.assertEqual(reopen_result.returncode, 0, reopen_result.stderr)
        assertion("public_cli_open_and_reopen")

        from framestudio.cli import cli_main

        guard_destination = journey_root / "ticket125-guarded-source-only.mp4"
        guard_stdout = StringIO()
        guard_stderr = StringIO()
        guard_argv = cli_command(
            SOURCE_ONLY_OUTPUT_MODE,
            final_project_path,
            guard_destination,
        )[2:]
        with patch(
            "framestudio.cli_export.render_project_av",
            side_effect=AssertionError("source-only invoked final compositor"),
        ):
            guard_code = cli_main(
                guard_argv,
                stdout=guard_stdout,
                stderr=guard_stderr,
            )
        (self.artifact_root / "guarded-source-only-stdout.txt").write_text(
            guard_stdout.getvalue(),
            encoding="utf-8",
        )
        (self.artifact_root / "guarded-source-only-stderr.txt").write_text(
            guard_stderr.getvalue(),
            encoding="utf-8",
        )
        self.assertEqual(
            guard_code,
            0,
            f"guarded public CLI source-only failed: {guard_stderr.getvalue()}",
        )
        guarded_payloads = json_lines(guard_stdout.getvalue()) + json_lines(
            guard_stderr.getvalue(),
        )
        guarded_exports = [item for item in guarded_payloads if item.get("command") == "export"]
        self.assertTrue(guarded_exports)
        self.assertTrue(guarded_exports[-1]["export"]["verified"])
        assertion(
            "source_only_public_cli_guard_did_not_schedule_final_compositor",
            {"guard_destination": guard_destination},
        )

        source_destination = journey_root / "ticket125-source-only.mp4"
        source_trace_path = self.artifact_root / "source-only-ffmpeg-trace.jsonl"
        source_trace_wrapper = self.artifact_root / "source-only-ffmpeg-trace.py"
        source_trace_wrapper.write_text(
            "\n".join(
                (
                    "#!/usr/bin/env python3",
                    "import json",
                    "import subprocess",
                    "import sys",
                    "from pathlib import Path",
                    f"actual = {str(ffmpeg)!r}",
                    f"trace = Path({str(source_trace_path)!r})",
                    "arguments = sys.argv[1:]",
                    "with trace.open('a', encoding='utf-8') as output:",
                    "    output.write(json.dumps(arguments) + '\\n')",
                    "raise SystemExit(subprocess.call([actual, *arguments]))",
                    "",
                ),
            ),
            encoding="utf-8",
        )
        source_trace_wrapper.chmod(0o755)
        source_result = run_command(
            "source-only",
            cli_command(
                SOURCE_ONLY_OUTPUT_MODE,
                final_project_path,
                source_destination,
                ffmpeg_path=str(source_trace_wrapper),
            ),
            timeout=600.0,
        )
        self.assertEqual(source_result.returncode, 0, source_result.stderr)
        source_payload = export_payload(source_result)
        source_export = source_payload["export"]
        self.assertTrue(source_export["verified"])
        self.assertEqual(source_export["output_plan"]["mode"], SOURCE_ONLY_OUTPUT_MODE)
        self.assertEqual(len(source_export["results"]), 4)
        source_trace_commands = [
            json.loads(line)
            for line in source_trace_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        source_render_commands = [
            command
            for command in source_trace_commands
            if "-filter_complex" in command
            and any("source-output-stage" in argument for argument in command)
        ]
        self.assertEqual(len(source_render_commands), 4)
        self.assertTrue(all(command.count("-i") == 1 for command in source_render_commands))
        self.assertFalse(any(command.count("-i") > 1 for command in source_trace_commands))
        source_render_inputs = [
            Path(command[command.index("-i") + 1]).name for command in source_render_commands
        ]
        self.assertEqual(source_render_inputs, ["A.mp4", "B.mp4", "A.mp4", "C.mp4"])
        expected_source_result_order = [
            ("track-1", source_ids["A.mp4"]),
            ("track-1", source_ids["B.mp4"]),
            ("track-2", source_ids["A.mp4"]),
            ("track-2", source_ids["C.mp4"]),
        ]
        self.assertEqual(
            [
                (item["identity"]["track_id"], item["identity"]["source_id"])
                for item in source_export["results"]
            ],
            expected_source_result_order,
        )

        def result_destination(item: dict[str, Any]) -> Path:
            request = item.get("request")
            if isinstance(request, dict) and isinstance(request.get("destination"), str):
                return Path(request["destination"])
            destination = item.get("destination")
            self.assertIsInstance(destination, str)
            assert isinstance(destination, str)
            return Path(destination)

        expected_source_outputs = {
            ("track-1", source_ids["A.mp4"]): 2.0,
            ("track-1", source_ids["B.mp4"]): 1.0,
            ("track-2", source_ids["A.mp4"]): 1.0,
            ("track-2", source_ids["C.mp4"]): 1.5,
        }
        actual_source_outputs = {
            (
                item["identity"]["track_id"],
                item["identity"]["source_id"],
            ): item
            for item in source_export["results"]
        }
        self.assertEqual(set(actual_source_outputs), set(expected_source_outputs))
        source_output_paths: dict[tuple[str, str], Path] = {}
        for identity, expected_duration in expected_source_outputs.items():
            item = actual_source_outputs[identity]
            self.assertEqual(item["state"], "verified")
            output_path = result_destination(item)
            source_output_paths[identity] = output_path
            self.assertTrue(output_path.is_file(), output_path)
            self.assertNotIn(output_path.resolve(), {path.resolve() for path in source_paths})
            metadata = probe_media(output_path).metadata()
            self.assertEqual(
                (metadata["width"], metadata["height"]),
                (1920, 1080),
            )
            self.assertEqual(float(Fraction(str(metadata["frame_rate"]))), 10.0)
            self.assertAlmostEqual(
                float(metadata["duration_seconds"]),
                expected_duration,
                delta=0.25,
            )
            frame_count_value = probe_frame_count(output_path)
            self.assertAlmostEqual(
                frame_count_value,
                round(expected_duration * 10.0),
                delta=2,
            )
            decoded = _decode_frame(output_path, min(frame_count_value - 1, 2))
            centroid = _white_centroid(decoded, (0, 0, 384, 216))
            self.assertAlmostEqual(centroid[0], 192.0, delta=35.0)
            self.assertAlmostEqual(centroid[1], 108.0, delta=35.0)
            if identity[1] == source_ids["C.mp4"]:
                self.assertFalse(metadata.get("audio_stream_present", False))
                self.assertIsNone(metadata.get("audio_sample_rate"))
                continue
            self.assertTrue(metadata.get("audio_stream_present", False))
            self.assertEqual(metadata["audio_sample_rate"], AUDIO_SAMPLE_RATE)
            self.assertEqual(metadata["audio_channels"], 2)
            samples, sample_rate, channels = _decoded_pcm(output_path)
            self.assertEqual(sample_rate, AUDIO_SAMPLE_RATE)
            self.assertEqual(channels, 2)
            expected_frequencies = (440, 880) if identity[1] == source_ids["A.mp4"] else (660,)
            available = len(samples) // channels
            audio_end = min(available, max(24_000, available // 2))
            for frequency in expected_frequencies:
                self.assertGreater(
                    max(
                        _tone_amplitude(
                            samples,
                            start_frame=min(4_800, max(0, audio_end // 4)),
                            end_frame=audio_end,
                            frequency=frequency,
                            channel=channel,
                        )
                        for channel in (0, 1)
                    ),
                    0.001,
                )

        def expected_full_canvas_marker(transform: VisualTransform) -> tuple[float, float]:
            scaled_width = round(1920 * transform.zoom)
            scaled_height = round(1080 * transform.zoom)
            crop_x = min(
                max(round((scaled_width - 1920) / 2 + transform.offset_x), 0),
                scaled_width - 1920,
            )
            crop_y = min(
                max(round((scaled_height - 1080) / 2 + transform.offset_y), 0),
                scaled_height - 1080,
            )
            return (
                (scaled_width / 2 - crop_x) * 384 / 1920,
                (scaled_height / 2 - crop_y) * 216 / 1080,
            )

        track1_a_decoded = _decode_frame(
            source_output_paths[("track-1", source_ids["A.mp4"])],
            5,
        )
        track2_a_decoded = _decode_frame(
            source_output_paths[("track-2", source_ids["A.mp4"])],
            5,
        )
        track1_a_marker = _white_centroid(track1_a_decoded, (0, 0, 384, 216))
        track2_a_marker = _white_centroid(track2_a_decoded, (0, 0, 384, 216))
        expected_track1_a_marker = expected_full_canvas_marker(reopened_a.visual_transform)
        expected_track2_a_marker = expected_full_canvas_marker(
            reopened_second_a.visual_transform,
        )
        self.assertAlmostEqual(track1_a_marker[0], expected_track1_a_marker[0], delta=8.0)
        self.assertAlmostEqual(track1_a_marker[1], expected_track1_a_marker[1], delta=8.0)
        self.assertAlmostEqual(track2_a_marker[0], expected_track2_a_marker[0], delta=8.0)
        self.assertAlmostEqual(track2_a_marker[1], expected_track2_a_marker[1], delta=8.0)
        self.assertGreater(abs(track1_a_marker[0] - track2_a_marker[0]), 15.0)
        self.assertGreater(abs(track1_a_marker[1] - track2_a_marker[1]), 5.0)
        self.assertNotIn(("track-3", source_ids["D.mp4"]), actual_source_outputs)
        self.assertNotIn(("track-4", source_ids["P.mp4"]), actual_source_outputs)
        assertion(
            "source_only_four_full_canvas_reels_and_no_excluded_outputs",
            {
                "identities": sorted(
                    [list(identity) for identity in actual_source_outputs],
                ),
                "outputs": {str(identity): path for identity, path in source_output_paths.items()},
                "result_order": expected_source_result_order,
                "ffmpeg_render_inputs": source_render_inputs,
                "command_trace": source_trace_path,
                "track1_a_marker": track1_a_marker,
                "track1_a_expected": expected_track1_a_marker,
                "track2_a_marker": track2_a_marker,
                "track2_a_expected": expected_track2_a_marker,
            },
        )

        combined_destination = journey_root / "ticket125-combined.mp4"
        combined_result = run_command(
            "combined",
            cli_command(
                COMBINED_OUTPUT_MODE,
                final_project_path,
                combined_destination,
            ),
            timeout=600.0,
        )
        self.assertEqual(combined_result.returncode, 0, combined_result.stderr)
        combined_payload = export_payload(combined_result)
        combined_export = combined_payload["export"]
        self.assertTrue(combined_export["verified"])
        self.assertEqual(combined_export["output_plan"]["mode"], COMBINED_OUTPUT_MODE)
        self.assertEqual(len(combined_export["results"]), 5)
        combined_identities = {
            (
                item["identity"]["output_kind"],
                item["identity"].get("track_id"),
                item["identity"].get("source_id"),
            )
            for item in combined_export["results"]
        }
        self.assertIn(("final", None, None), combined_identities)
        self.assertEqual(
            {
                (kind, track_id, source_id)
                for kind, track_id, source_id in combined_identities
                if kind == "source"
            },
            {("source", track_id, source_id) for track_id, source_id in expected_source_outputs},
        )
        self.assertTrue(combined_destination.is_file())
        combined_final_metadata = probe_media(combined_destination).metadata()
        self.assertEqual(
            (combined_final_metadata["width"], combined_final_metadata["height"]),
            (1920, 1080),
        )
        expected_combined_order = [
            ("final", None, None),
            *[
                ("source", track_id, source_id)
                for track_id, source_id in expected_source_result_order
            ],
        ]
        self.assertEqual(
            [
                (
                    item["identity"]["output_kind"],
                    item["identity"].get("track_id"),
                    item["identity"].get("source_id"),
                )
                for item in combined_export["results"]
            ],
            expected_combined_order,
        )
        self.assertEqual(combined_final_metadata["audio_sample_rate"], AUDIO_SAMPLE_RATE)
        self.assertEqual(combined_final_metadata["audio_channels"], 2)
        combined_frame_count = probe_frame_count(combined_destination)
        self.assertEqual(combined_frame_count, 40)
        self.assertLess(_mean_luma(_decode_frame(combined_destination, 5)), 20.0)
        for frame_index in (15, 25, 36):
            self.assertGreater(_mean_luma(_decode_frame(combined_destination, frame_index)), 25.0)
        final_layout = plan_project_layout(reopened)
        combined_slot_positions = assert_rendered_slot_positions(
            combined_destination,
            final_layout,
            combined_frame_count,
            (1, 2),
        )
        c_interval = next(
            interval
            for interval in final_layout.intervals
            if interval.start_tick <= round(3.15 * 1_000_000)
            and interval.end_tick >= round(3.40 * 1_000_000)
        )
        c_interval_sources = {block.source_id for block in c_interval.active_blocks}
        self.assertIn(source_ids["C.mp4"], c_interval_sources)
        self.assertNotIn(source_ids["B.mp4"], c_interval_sources)
        self.assertNotIn(source_ids["P.mp4"], c_interval_sources)
        combined_samples, combined_sample_rate, combined_channels = _decoded_pcm(
            combined_destination,
        )
        self.assertEqual(combined_sample_rate, AUDIO_SAMPLE_RATE)
        self.assertEqual(combined_channels, 2)
        combined_available_frames = len(combined_samples) // combined_channels

        def combined_tone(frequency: int, start: float, end: float) -> tuple[float, float]:
            start_frame = min(
                combined_available_frames,
                max(0, round(start * AUDIO_SAMPLE_RATE)),
            )
            end_frame = min(
                combined_available_frames,
                max(start_frame + 1, round(end * AUDIO_SAMPLE_RATE)),
            )
            return tuple(
                _tone_amplitude(
                    combined_samples,
                    start_frame=start_frame,
                    end_frame=end_frame,
                    frequency=frequency,
                    channel=channel,
                )
                for channel in (0, 1)
            )

        combined_440 = combined_tone(440, 1.15, 1.80)
        combined_880 = combined_tone(880, 1.15, 1.80)
        combined_660 = combined_tone(660, 2.15, 2.85)
        combined_silence_tones = {
            frequency: combined_tone(frequency, 3.15, 3.40) for frequency in (440, 660, 880, 1230)
        }
        combined_c_interval_b_tone = max(combined_silence_tones[660])
        combined_c_interval_p_tone = max(combined_silence_tones[1230])
        self.assertGreater(combined_440[0], 0.001)
        self.assertGreater(combined_880[1], 0.001)
        self.assertGreater(max(combined_660), 0.001)
        self.assertGreater(combined_silence_tones[440][0], 0.001)
        self.assertGreater(combined_silence_tones[880][1], 0.001)
        self.assertLess(combined_c_interval_b_tone, 0.01, combined_silence_tones)
        self.assertLess(combined_c_interval_p_tone, 0.01, combined_silence_tones)
        assertion(
            "combined_optional_final_and_four_source_outputs",
            {
                "destination": combined_destination,
                "metadata": combined_final_metadata,
                "frame_count": combined_frame_count,
                "rendered_slot_positions": combined_slot_positions,
                "c_interval_sources": sorted(c_interval_sources),
                "audio_tones": {
                    "440": combined_440,
                    "880": combined_880,
                    "660": combined_660,
                    "c_interval_tones": combined_silence_tones,
                    "c_interval_b_tone_max": combined_c_interval_b_tone,
                    "excluded_track_p_tone_max": combined_c_interval_p_tone,
                },
                "result_order": expected_combined_order,
            },
        )

        planner = RemovalControlsFunctionalityTests()
        planner.window = window
        planner.GLib = self.GLib
        planner.Gtk = self.Gtk
        planner.window_title = window.get_title()

        def walk_widgets(widget: Any):
            if widget is None:
                return
            yield widget
            child = widget.get_first_child()
            while child is not None:
                yield from walk_widgets(child)
                child = child.get_next_sibling()

        def planner_button(root: Any, label: str) -> Any:
            for widget in walk_widgets(root):
                if isinstance(widget, self.Gtk.Button) and widget.get_label() == label:
                    return widget
            raise AssertionError(f"missing planner button {label!r}")

        planner._click_widget_center(window.export_button)
        self._wait_until(
            lambda: (
                getattr(window, "export_planning_window", None) is not None
                and window.export_planning_window.get_visible()
            ),
            "GTK export planner did not open for integrated cancellation",
            rounds=3000,
        )
        panel = window.export_planning_window
        panel_title = "FrameStudio T125 Integrated Planner"
        panel.set_title(panel_title)
        panel.present()
        _pump_events(self.GLib, 20)
        planner._xdotool(
            "windowmove",
            "--sync",
            planner._window_id(panel_title),
            "0",
            "0",
        )
        _pump_events(self.GLib, 20)
        gui_destination = journey_root / "ticket125-gui-cancel.mp4"

        def owned_ffmpeg_commands() -> tuple[str, ...]:
            commands: list[str] = []
            for process_dir in Path("/proc").glob("[0-9]*"):
                try:
                    command_line = (process_dir / "cmdline").read_bytes().replace(b"\0", b" ")
                except (FileNotFoundError, PermissionError):
                    continue
                command = command_line.decode("utf-8", errors="replace").strip()
                if (
                    command
                    and "ffmpeg" in Path(command.split(" ", 1)[0]).name
                    and str(journey_root) in command
                ):
                    commands.append(command)
            return tuple(commands)

        def panel_click(widget: Any) -> None:
            planner._physical_click(
                widget,
                widget.get_width() / 2.0,
                widget.get_height() / 2.0,
                target_window=panel,
                window_title=panel_title,
            )

        def configure_planner_panel(panel: Any, title: str) -> None:
            panel.set_title(title)
            panel.present()
            for widget in walk_widgets(panel):
                if isinstance(widget, self.Gtk.Entry) and widget.get_text().endswith(".mp4"):
                    widget.set_text("ticket125-gui-cancel.mp4")
                    _pump_events(self.GLib, 20)
                    break
            else:
                raise AssertionError("GTK planner did not expose a filename entry")
            for widget in walk_widgets(panel):
                if not isinstance(widget, self.Gtk.CheckButton):
                    continue
                label = (widget.get_label() or "").lower()
                if "enhance sources below the target rate" in label or "upscale eligible" in label:
                    widget.set_active(False)
                    _pump_events(self.GLib, 20)

        panel_title = "FrameStudio T125 Integrated Planner"
        configure_planner_panel(panel, panel_title)
        final_toggle = getattr(panel, "final_output_toggle", None)
        source_toggle = getattr(panel, "source_output_toggle", None)
        self.assertIsNotNone(final_toggle)
        self.assertIsNotNone(source_toggle)
        final_toggle.set_active(False)
        source_toggle.set_active(True)
        self._wait_until(
            lambda: (
                "estimated processing time" in " ".join(_visible_widget_text(panel)).lower()
                and planner_button(panel, "Start export").get_sensitive()
            ),
            "GTK source-only cancellation planner did not become actionable",
            rounds=6000,
        )
        start_button = planner_button(panel, "Start export")
        playback_block = max(
            window.segment_timeline.active_blocks(),
            key=lambda item: item.timeline_end_seconds - item.timeline_start_seconds,
        )
        seek_preview(playback_block.timeline_start_seconds + 0.01)
        self.assertTrue(window.controller.play())
        self._wait_until(
            lambda: getattr(window.backend, "_realtime_decode_process", None) is not None,
            "GUI export resource test did not start a continuous preview decoder",
            rounds=3000,
        )
        stream_before_export = window.backend._realtime_decode_process
        self.assertIsNone(stream_before_export.poll())
        export_backend = window.backend
        export_stats_getter = getattr(export_backend, "precise_preview_stats", None)
        preview_before_export = export_stats_getter() if callable(export_stats_getter) else {}
        panel_click(start_button)
        self._wait_until(
            lambda: bool(
                window._export_in_progress
                and window.cancel_export_button.get_visible()
                and discover_export_session(gui_destination).exists
                and bool(owned_ffmpeg_commands())
            ),
            "GTK source-only export did not expose a live owned media child and session",
            rounds=12000,
        )
        self.assertIs(window.backend, export_backend)
        self.assertIsNotNone(stream_before_export.poll())
        self.assertFalse(Path(f"/proc/{stream_before_export.pid}").exists())
        self.assertIsNone(getattr(window.backend, "_realtime_decode_process", None))
        if callable(export_stats_getter):
            preview_during_export = export_stats_getter()
            self.assertIsNone(preview_during_export.get("helper_pid"))
            self.assertEqual(preview_during_export.get("contexts"), 0)
            previous_helper = preview_before_export.get("helper_pid")
            if previous_helper is not None:
                self.assertFalse(Path(f"/proc/{previous_helper}").exists())
        gui_processes_before_cancel = owned_ffmpeg_commands()
        gui_running_snapshot = self.artifact_root / "changed-gui-export-running.png"
        _snapshot_widget(window, gui_running_snapshot, self.Gtk)
        planner._click_widget_center(window.cancel_export_button)
        self._wait_until(
            lambda: not window._export_in_progress,
            "GTK cancellation did not return to an idle state",
            rounds=30_000,
        )
        gui_status = window.status_label.get_text().lower()
        self.assertTrue("cancel" in gui_status or "partial" in gui_status, gui_status)
        gui_session = discover_export_session(gui_destination)
        self.assertTrue(gui_session.exists, gui_session.to_dict())
        self.assertTrue(gui_session.valid, gui_session.to_dict())
        self.assertTrue(gui_session.resumable, gui_session.to_dict())
        self.assertGreater(gui_session.stage_count, 0, gui_session.to_dict())
        panel.close()
        _pump_events(self.GLib, 30)
        self._wait_until(
            lambda: getattr(window, "export_planning_window", None) is None,
            "GTK export planner did not close before recovery reopen",
            rounds=3000,
        )
        planner._click_widget_center(window.export_button)
        self._wait_until(
            lambda: (
                getattr(window, "export_planning_window", None) is not None
                and window.export_planning_window.get_visible()
            ),
            "GTK export planner did not reopen for cancellation recovery",
            rounds=3000,
        )
        panel = window.export_planning_window
        panel_title = "FrameStudio T125 Integrated Recovery Planner"
        configure_planner_panel(panel, panel_title)
        self._wait_until(
            lambda: "resume export" in " ".join(_visible_widget_text(panel)).lower(),
            "GTK recovery planner did not expose the retained session",
            rounds=6000,
        )
        planner_text = " ".join(_visible_widget_text(panel)).lower()
        self.assertIn("resume export", planner_text)
        self.assertIn("discard", planner_text)
        gui_session_roots = [gui_session.root]
        resume_button = planner_button(panel, "Resume export")
        self.assertTrue(resume_button.get_visible())
        self.assertTrue(resume_button.get_sensitive())
        self._wait_until(
            lambda: planner_button(panel, "Start export").get_sensitive(),
            "GTK recovery planner did not finish preparing the resumable request",
            rounds=6000,
        )
        resume_button.emit("clicked")
        self._wait_until(
            lambda: window._export_in_progress,
            "GTK export resume did not start",
            rounds=3000,
        )
        self._wait_until(
            lambda: not window._export_in_progress,
            "GTK export resume did not complete",
            rounds=30_000,
        )
        gui_batch = getattr(window, "_last_export_batch_result", None)
        self.assertIsNotNone(gui_batch)
        self.assertTrue(
            gui_batch.complete,
            {
                "mode": gui_batch.mode,
                "complete": gui_batch.complete,
                "partial_success": gui_batch.partial_success,
                "stale": gui_batch.stale,
                "error": gui_batch.error,
                "results": [result.to_dict() for result in gui_batch.results],
            },
        )
        self.assertTrue(gui_batch.results)
        self.assertTrue(all(result.state.value == "verified" for result in gui_batch.results))
        self.assertTrue(
            all(result.destination.is_file() for result in gui_batch.results),
        )
        assertion(
            "real_gui_cancel_resume_and_published_siblings",
            {
                "running_snapshot": gui_running_snapshot,
                "session_roots": gui_session_roots,
                "owned_media_processes": gui_processes_before_cancel,
                "result_count": len(gui_batch.results),
            },
        )
        panel.close()
        _pump_events(self.GLib, 30)

        wrapper_marker = self.artifact_root / "cli-cancel-wrapper-started"
        child_pid_marker = self.artifact_root / "cli-cancel-child.pid"
        wrapper_pid_marker = self.artifact_root / "cli-cancel-wrapper.pid"
        wrapper_resume_marker = self.artifact_root / "cli-cancel-wrapper-resume"
        wrapper = self.artifact_root / "slow-ffmpeg-wrapper.py"
        wrapper.write_text(
            "\n".join(
                (
                    "#!/usr/bin/env python3",
                    "import os",
                    "import signal",
                    "import subprocess",
                    "import sys",
                    "from pathlib import Path",
                    f"actual = {str(ffmpeg)!r}",
                    f"marker = Path({str(wrapper_marker)!r})",
                    f"child_pid_marker = Path({str(child_pid_marker)!r})",
                    f"wrapper_pid_marker = Path({str(wrapper_pid_marker)!r})",
                    f"resume_marker = Path({str(wrapper_resume_marker)!r})",
                    "if '--version' in sys.argv[1:]:",
                    "    raise SystemExit(subprocess.call([actual, *sys.argv[1:]]))",
                    "if resume_marker.is_file():",
                    "    raise SystemExit(subprocess.call([actual, *sys.argv[1:]]))",
                    "marker.write_text('started', encoding='utf-8')",
                    "wrapper_pid_marker.write_text(str(os.getpid()), encoding='utf-8')",
                    "os.setpgrp()",
                    "arguments = list(sys.argv[1:])",
                    "try:",
                    "    input_index = arguments.index('-i')",
                    "except ValueError:",
                    "    input_index = None",
                    "if input_index is not None:",
                    "    arguments[input_index:input_index] = ['-re']",
                    "child = subprocess.Popen([actual, *arguments])",
                    "def stop(_signum, _frame):",
                    "    if child.poll() is None:",
                    "        child.terminate()",
                    "signal.signal(signal.SIGINT, stop)",
                    "signal.signal(signal.SIGTERM, stop)",
                    "child_pid_marker.write_text(str(child.pid), encoding='utf-8')",
                    "return_code = child.wait()",
                    "raise SystemExit(return_code)",
                    "",
                ),
            ),
            encoding="utf-8",
        )
        wrapper.chmod(0o755)
        cli_cancel_destination = journey_root / "ticket125-cli-cancel.mp4"
        sessions_before_cancel = set(journey_root.rglob("*.framestudio-session"))
        cli_cancel_process = subprocess.Popen(
            cli_command(
                SOURCE_ONLY_OUTPUT_MODE,
                final_project_path,
                cli_cancel_destination,
                ffmpeg_path=str(wrapper),
            ),
            cwd=str(REPOSITORY_ROOT),
            env={
                **os.environ,
                "FRAMESTUDIO_PHASE010_ARTIFACT_DIR": str(self.artifact_root),
            },
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        wait_deadline = time.monotonic() + 120.0
        while not wrapper_marker.is_file() and cli_cancel_process.poll() is None:
            if time.monotonic() >= wait_deadline:
                cli_cancel_process.terminate()
                raise AssertionError("CLI cancellation wrapper did not start")
            time.sleep(0.05)
        self.assertTrue(wrapper_marker.is_file())
        while not child_pid_marker.is_file() and cli_cancel_process.poll() is None:
            if time.monotonic() >= wait_deadline:
                cli_cancel_process.terminate()
                raise AssertionError("CLI cancellation wrapper did not expose its media child")
            time.sleep(0.05)
        self.assertTrue(child_pid_marker.is_file())
        child_pid = int(child_pid_marker.read_text(encoding="utf-8"))
        self.assertTrue(wrapper_pid_marker.is_file())
        wrapper_pid = int(wrapper_pid_marker.read_text(encoding="utf-8"))
        os.kill(wrapper_pid, signal.SIGTERM)
        child_dead_deadline = time.monotonic() + 30.0
        while time.monotonic() < child_dead_deadline:
            try:
                os.kill(child_pid, 0)
            except ProcessLookupError:
                break
            time.sleep(0.05)
        else:
            raise AssertionError("CLI cancellation left the owned FFmpeg child running")
        try:
            cli_cancel_stdout, cli_cancel_stderr = cli_cancel_process.communicate(timeout=600.0)
        except subprocess.TimeoutExpired as error:
            cli_cancel_process.terminate()
            cli_cancel_process.communicate(timeout=30.0)
            raise AssertionError("CLI cancellation process did not terminate") from error
        cli_cancel_stdout_path = self.artifact_root / "cli-cancel-stdout.txt"
        cli_cancel_stderr_path = self.artifact_root / "cli-cancel-stderr.txt"
        cli_cancel_stdout_path.write_text(cli_cancel_stdout, encoding="utf-8")
        cli_cancel_stderr_path.write_text(cli_cancel_stderr, encoding="utf-8")
        evidence["commands"].append(
            {
                "name": "cli-cancel",
                "command": cli_command(
                    SOURCE_ONLY_OUTPUT_MODE,
                    final_project_path,
                    cli_cancel_destination,
                    ffmpeg_path=str(wrapper),
                ),
                "returncode": cli_cancel_process.returncode,
                "stdout": str(cli_cancel_stdout_path),
                "stderr": str(cli_cancel_stderr_path),
            },
        )
        self.assertNotEqual(cli_cancel_process.returncode, 0)
        cli_cancel_stdout_payloads = json_lines(cli_cancel_stdout)
        cli_cancel_stderr_payloads = json_lines(cli_cancel_stderr)
        self.assertFalse(
            any(
                item.get("ok") is True and item.get("command") == "export"
                for item in cli_cancel_stdout_payloads
            ),
        )
        cli_cancel_errors = [
            item
            for item in cli_cancel_stderr_payloads
            if item.get("ok") is False and isinstance(item.get("error"), dict)
        ]
        self.assertTrue(cli_cancel_errors, cli_cancel_stderr)
        cli_cancel_error = cli_cancel_errors[-1]
        self.assertEqual(cli_cancel_error["error"]["code"], "export_failed")
        cli_cancel_details = cli_cancel_error["error"]["details"]
        self.assertFalse(cli_cancel_details["verified"])
        self.assertTrue(
            any(
                result["state"] in {"failed", "cancelled"}
                for result in cli_cancel_details["results"]
            ),
        )
        assertion(
            "real_cli_cancel_owned_child_and_structured_error",
            {
                "stdout": cli_cancel_stdout_path,
                "stderr": cli_cancel_stderr_path,
                "error_code": cli_cancel_error["error"]["code"],
            },
        )
        sessions_after_cancel = set(journey_root.rglob("*.framestudio-session"))
        self.assertTrue(sessions_after_cancel - sessions_before_cancel)
        self.assertFalse(cli_cancel_destination.is_file())
        wrapper_resume_marker.write_text("resume", encoding="utf-8")

        cli_resume_result = run_command(
            "cli-resume",
            cli_command(
                SOURCE_ONLY_OUTPUT_MODE,
                final_project_path,
                cli_cancel_destination,
                ffmpeg_path=str(wrapper),
                recovery_mode="resume",
            ),
            timeout=600.0,
        )
        self.assertEqual(cli_resume_result.returncode, 0, cli_resume_result.stderr)
        cli_resume_payload = export_payload(cli_resume_result)
        self.assertTrue(cli_resume_payload["export"]["verified"])
        self.assertTrue(
            all(
                result["state"] == "verified" for result in cli_resume_payload["export"]["results"]
            ),
        )
        cli_restart_result = run_command(
            "cli-restart",
            cli_command(
                SOURCE_ONLY_OUTPUT_MODE,
                final_project_path,
                cli_cancel_destination,
                ffmpeg_path=str(wrapper),
                recovery_mode="restart",
            ),
            timeout=600.0,
        )
        self.assertEqual(cli_restart_result.returncode, 0, cli_restart_result.stderr)
        cli_restart_payload = export_payload(cli_restart_result)
        self.assertTrue(cli_restart_payload["export"]["verified"])

        cli_resume_results = cli_resume_payload["export"]["results"]
        cli_resume_by_identity = {
            (
                item["identity"]["track_id"],
                item["identity"]["source_id"],
            ): result_destination(item)
            for item in cli_resume_results
        }
        tamper_identity = ("track-1", source_ids["A.mp4"])
        donor_identity = ("track-1", source_ids["B.mp4"])
        tamper_path = cli_resume_by_identity[tamper_identity]
        donor_path = cli_resume_by_identity[donor_identity]
        original_tamper_bytes = tamper_path.read_bytes()
        donor_bytes = donor_path.read_bytes()
        self.assertEqual(len(original_tamper_bytes), len(original_tamper_bytes))
        tamper_path.write_bytes(donor_bytes)
        self.assertEqual(tamper_path.stat().st_size, donor_path.stat().st_size)
        tamper_result = run_command(
            "cli-resume-after-same-shaped-tamper",
            cli_command(
                SOURCE_ONLY_OUTPUT_MODE,
                final_project_path,
                cli_cancel_destination,
                ffmpeg_path=str(wrapper),
                recovery_mode="resume",
            ),
            timeout=600.0,
        )
        self.assertEqual(tamper_result.returncode, 0, tamper_result.stderr)
        tamper_payload = export_payload(tamper_result)
        self.assertTrue(tamper_payload["export"]["verified"])
        self.assertEqual(tamper_path.read_bytes(), original_tamper_bytes)
        self.assertNotEqual(tamper_path.read_bytes(), donor_bytes)
        assertion(
            "cli_cancel_resume_restart_and_same_shaped_tamper_recovery",
            {
                "cancel_stderr": cli_cancel_stderr_path,
                "resume": cli_resume_payload,
                "restart": cli_restart_payload,
                "tampered_identity": tamper_identity,
            },
        )

        failure_destination = journey_root / "ticket125-failed.mp4"
        missing_ffmpeg = self.artifact_root / "missing-ffmpeg-binary"
        failure_result = run_command(
            "cli-structured-failure",
            cli_command(
                FINAL_ONLY_OUTPUT_MODE,
                final_project_path,
                failure_destination,
                ffmpeg_path=str(missing_ffmpeg),
            ),
            timeout=120.0,
        )
        self.assertNotEqual(failure_result.returncode, 0)
        failure_payloads = json_lines(failure_result.stdout) + json_lines(
            failure_result.stderr,
        )
        self.assertTrue(failure_payloads)
        self.assertFalse('"verified": true' in failure_result.stdout.lower())
        self.assertFalse(failure_destination.is_file())
        self.assertTrue(
            any(
                payload.get("command") == "export" or "error" in payload or "code" in payload
                for payload in failure_payloads
            ),
        )
        assertion(
            "structured_cli_failure_no_success_stdout_or_destination",
            {"failure_destination": failure_destination},
        )

        self.assertEqual(
            {path: _sha256(path) for path in source_paths},
            source_hashes,
        )
        self.assertEqual(
            {
                path: hashlib.sha256(path.read_bytes()).hexdigest()
                for path in (self.source_a, self.source_b)
            },
            self.source_hashes,
        )
        self.assertEqual(final_project_path.read_bytes(), final_project_bytes)
        self.assertFalse(window._export_in_progress)
        self.assertIsNone(window._export_cancel_event)
        backend = getattr(window, "backend", None)
        if backend is not None:
            self.assertIsNone(getattr(backend, "_process", None))
            self.assertIsNone(getattr(backend, "_preview_process", None))
            window._stop_backend()
        self.assertIsNone(window.backend)
        self.assertIsNone(window.controller)
        assertion(
            "source_project_output_safety_and_runtime_cleanup",
            {
                "source_hashes": {str(path): digest for path, digest in source_hashes.items()},
                "project": final_project_path,
                "elapsed_seconds": round(time.monotonic() - started, 3),
            },
        )
