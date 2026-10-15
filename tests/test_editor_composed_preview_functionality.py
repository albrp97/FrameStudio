from __future__ import annotations

import shutil
import subprocess
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from framestudio.app import create_editor_application
from framestudio.layout_plan import CropPlan
from framestudio.media import probe_media
from framestudio.model import Project
from framestudio.operations import remove_blocks, undo_removed_blocks
from framestudio.persistence import save_project
from framestudio.playback import PlaybackState
from tests.test_editor_composed_preview import (
    CANVAS_HEIGHT,
    CANVAS_WIDTH,
    PreviewFixture,
    _assert_empty_preview_state,
    _assert_video_only_commands,
    _mean_luma,
    _ready_audio_settings,
    _sha256,
    _visible_marker_center,
    _white_centroid,
    build_four_track_fixture,
    isolated_directory,
)

TIGHT_RASTER_PIXELS_AT_640 = 3.0
BACKGROUND_CHANNEL_TOLERANCE = 32


def _pump_events(glib, rounds: int = 10) -> None:
    context = glib.MainContext.default()
    for _ in range(rounds):
        while context.pending():
            context.iteration(False)
        time.sleep(0.01)


def _one_track_fixture(fixture: PreviewFixture) -> tuple[Project, Path, str]:
    source = fixture.sources[0]
    metadata = probe_media(source).metadata()
    project = Project.create_synchronized(
        source,
        metadata,
        project_id="ticket-120-one-track-fixture",
    )
    source_reference = project.source
    project.set_source_audio_settings(
        source_reference.source_id,
        _ready_audio_settings(source_reference),
    )
    project.validate()
    project_path = fixture.root / "one-track.framestudio.json"
    save_project(project, project_path)
    return project, project_path, _sha256(source)


def _legacy_one_track_fixture(fixture: PreviewFixture) -> tuple[Project, Path, str]:
    source = fixture.sources[0]
    metadata = probe_media(source).metadata()
    project = Project.create(
        source,
        metadata,
        project_id="ticket-120-legacy-one-track-fixture",
    )
    source_reference = project.source
    project.set_source_audio_settings(
        source_reference.source_id,
        _ready_audio_settings(source_reference),
    )
    project.validate()
    project_path = fixture.root / "legacy-one-track.framestudio.json"
    save_project(project, project_path)
    return project, project_path, _sha256(source)


def _normalize_downloaded_pixels(raw: bytes, format_name: str) -> bytes:
    format_name = format_name.lower()
    if format_name in {"r8g8b8a8", "r8g8b8a8-premultiplied"}:
        return raw
    layouts = {
        "b8g8r8a8": (2, 1, 0, 3, None),
        "a8r8g8b8": (1, 2, 3, 0, None),
        "a8b8g8r8": (3, 2, 1, 0, None),
        "x8r8g8b8": (1, 2, 3, None, 255),
        "x8b8g8r8": (3, 2, 1, None, 255),
    }
    base_name = format_name.removesuffix("-premultiplied")
    layout = layouts.get(base_name)
    if layout is not None:
        red, green, blue, alpha, fill = layout
        planes = tuple(raw[index::4] for index in (red, green, blue))
        if alpha is None:
            alpha_plane = bytes((fill,)) * (len(raw) // 4)
        else:
            alpha_plane = raw[alpha::4]
        return bytes(
            channel for pixel in zip(*planes, alpha_plane, strict=False) for channel in pixel
        )
    raise AssertionError(f"Unsupported Gdk texture download format: {format_name}")


def _texture_rgba(
    paintable,
    *,
    fallback_path: Path,
    gdk_pixbuf,
) -> tuple[bytes, int, int]:
    if paintable is None:
        raise AssertionError("The GTK preview did not expose a displayed paintable")
    width = int(paintable.get_width())
    height = int(paintable.get_height())
    if (width, height) != (CANVAS_WIDTH, CANVAS_HEIGHT):
        raise AssertionError(f"Unexpected displayed texture size: {width}×{height}")
    download = getattr(paintable, "download", None)
    if not callable(download):
        raise AssertionError("The GTK preview paintable is not a downloadable Gdk.Texture")
    pixels = bytearray(width * height * 4)
    download(pixels, width * 4)
    format_value = paintable.get_format()
    format_name = getattr(format_value, "value_nick", str(format_value))
    normalized = _normalize_downloaded_pixels(bytes(pixels), format_name)
    if any(normalized):
        return normalized, width, height
    save_to_png = getattr(paintable, "save_to_png", None)
    if not callable(save_to_png) or not save_to_png(str(fallback_path)):
        raise AssertionError("GTK could not persist the displayed texture for pixel inspection")
    try:
        pixbuf = gdk_pixbuf.Pixbuf.new_from_file(str(fallback_path))
        channels = int(pixbuf.get_n_channels())
        rowstride = int(pixbuf.get_rowstride())
        source_pixels = bytes(pixbuf.get_pixels())
        rows = [
            source_pixels[row * rowstride : row * rowstride + width * channels]
            for row in range(height)
        ]
        if channels == 4:
            return b"".join(rows), width, height
        if channels == 3:
            return (
                b"".join(
                    bytes(
                        channel
                        for index in range(0, len(row), 3)
                        for channel in (row[index], row[index + 1], row[index + 2], 255)
                    )
                    for row in rows
                ),
                width,
                height,
            )
        raise AssertionError(f"Unexpected GdkPixbuf channel count: {channels}")
    finally:
        fallback_path.unlink(missing_ok=True)


def _sample_background_rgb(
    pixels: bytes,
    width: int,
    height: int,
    crop: CropPlan,
) -> tuple[int, int, int]:
    target = crop.target
    radius = max(2, min(target.width, target.height) // 80)
    samples: list[tuple[int, int, int]] = []
    for x_fraction in (0.15, 0.85):
        for y_fraction in (0.15, 0.85):
            center_x = target.x + round(target.width * x_fraction)
            center_y = target.y + round(target.height * y_fraction)
            for y in range(center_y - radius, center_y + radius + 1):
                for x in range(center_x - radius, center_x + radius + 1):
                    if not (0 <= x < width and 0 <= y < height):
                        continue
                    offset = (y * width + x) * 4
                    red, green, blue = pixels[offset : offset + 3]
                    if (
                        min(red, green, blue) >= 180
                        and max(
                            red,
                            green,
                            blue,
                        )
                        - min(red, green, blue)
                        <= 35
                    ):
                        continue
                    if max(red, green, blue) < 12:
                        continue
                    samples.append((red, green, blue))
    if not samples:
        raise AssertionError(f"No colored background samples found in crop {target}")
    return tuple(
        sorted(channel_values)[len(channel_values) // 2]
        for channel_values in zip(*samples, strict=False)
    )


def _centroid_tolerance(
    crop: CropPlan,
    slot,
    fixture: PreviewFixture,
    width: int,
    height: int,
) -> float:
    marker_width, marker_height = fixture.marker_dimensions[slot.block.source_id]
    geometry = slot.block.source_geometry
    scaled_marker_width = marker_width * crop.scaled_width / geometry.width
    scaled_marker_height = marker_height * crop.scaled_height / geometry.height
    preview_scale = min(width / 640.0, height / 360.0)
    raster_bound = TIGHT_RASTER_PIXELS_AT_640 * preview_scale
    marker_bound = max(1.0, min(scaled_marker_width, scaled_marker_height) / 2.0)
    return min(raster_bound, marker_bound)


def _assert_texture_matches_interval(
    test_case: unittest.TestCase,
    pixels: bytes,
    width: int,
    height: int,
    interval,
    fixture: PreviewFixture,
) -> None:
    test_case.assertEqual((width, height), (CANVAS_WIDTH, CANVAS_HEIGHT))
    if interval.is_black:
        test_case.assertLess(_mean_luma(pixels, width, height), 8.0)
        return
    for slot in interval.slots:
        crops: tuple[CropPlan | None, ...] = (
            slot.triplicate_crops if slot.triplicate_crops else (slot.crop,)
        )
        for crop in crops:
            test_case.assertIsNotNone(crop)
            assert crop is not None
            expected_background = fixture.source_backgrounds[slot.block.source_id]
            actual_background = _sample_background_rgb(pixels, width, height, crop)
            for actual_channel, expected_channel in zip(
                actual_background,
                expected_background,
                strict=True,
            ):
                test_case.assertLessEqual(
                    abs(actual_channel - expected_channel),
                    BACKGROUND_CHANNEL_TOLERANCE,
                    msg=(
                        f"wrong source background for {slot.block.block_id}: "
                        f"actual={actual_background} expected={expected_background}"
                    ),
                )
            expected = _visible_marker_center(
                crop,
                fixture.marker_dimensions[slot.block.source_id],
            )
            actual = _white_centroid(
                pixels,
                width,
                (
                    crop.target.x,
                    crop.target.y,
                    crop.target.x + crop.target.width,
                    crop.target.y + crop.target.height,
                ),
            )
            tolerance = _centroid_tolerance(crop, slot, fixture, width, height)
            test_case.assertAlmostEqual(actual[0], expected[0], delta=tolerance)
            test_case.assertAlmostEqual(actual[1], expected[1], delta=tolerance)


class ComposedPreviewFunctionalityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            import gi

            gi.require_version("Gdk", "4.0")
            gi.require_version("GdkPixbuf", "2.0")
            gi.require_version("Gio", "2.0")
            gi.require_version("GLib", "2.0")
            gi.require_version("Gtk", "4.0")
            from gi.repository import GdkPixbuf, Gio, GLib, Gtk
        except (ImportError, ValueError) as error:
            raise AssertionError("GTK 4 and PyGObject are required for TICKET-120") from error
        if not Gtk.init_check():
            raise AssertionError("GTK 4 could not initialize on the test display")
        for tool in ("ffmpeg", "ffprobe"):
            if shutil.which(tool) is None:
                raise AssertionError(f"{tool} is required for TICKET-120 media preflight")
        cls.Gio = Gio
        cls.GLib = GLib
        cls.GdkPixbuf = GdkPixbuf
        cls.Gtk = Gtk

    def setUp(self):
        self.fixture_context = isolated_directory("ticket120-gtk")
        self.fixture_root = self.fixture_context.__enter__()
        self.addCleanup(self.fixture_context.__exit__, None, None, None)
        self.fixture = build_four_track_fixture(self.fixture_root)
        self.application, self.window_factory = create_editor_application()
        app_suffix = self.fixture_root.name.replace(".", "").replace("-", "")
        self.application.set_application_id(f"io.github.framestudio.t120.{app_suffix}")
        self.application.set_flags(
            self.application.get_flags() | self.Gio.ApplicationFlags.NON_UNIQUE,
        )
        self.assertTrue(self.application.register(None))
        self.addCleanup(self._quit_application)
        self.window = self.window_factory(self.application)
        self.window.set_title(f"FrameStudio T120 preview {app_suffix}")
        self.window.audio_preview_enabled = True
        self.frame_positions: list[tuple[float, int | None]] = []
        original_on_frame = self.window._on_frame

        def capture_frame(frame, generation=None):
            self.frame_positions.append((frame.position_seconds, generation))
            original_on_frame(frame, generation)

        self.window._on_frame = capture_frame
        self.addCleanup(self._close_window)
        self._pump_display()

    def _pump_display(self, rounds: int = 10) -> None:
        _pump_events(self.GLib, rounds)

    def _wait_until(self, predicate, message: str, rounds: int = 600) -> None:
        for _ in range(rounds):
            self._pump_display(1)
            if predicate():
                return
        status = getattr(self.window, "status_label", None)
        status_text = "" if status is None else status.get_text()
        raise AssertionError(f"{message}; last status={status_text!r}")

    def _open_project(self, project_path: Path) -> None:
        self.window._load_project_path(project_path)
        self._wait_until(
            lambda: self.window.project_path == project_path and self.window.project is not None,
            "GTK did not attach the composed project",
        )

    def _require_preview_backend(self) -> None:
        self.assertIsNotNone(
            self.window.backend,
            "TICKET-120 preview backend is still unavailable for an absolute project",
        )
        self.assertIsNotNone(
            self.window.controller,
            "TICKET-120 playback controller is still unavailable for an absolute project",
        )
        self.assertTrue(
            self.window.play_button.get_sensitive(),
            "TICKET-120 preview controls remain disabled for an absolute project",
        )

    def _seek_and_capture(self, position_seconds: float) -> tuple[bytes, int, int]:
        self._require_preview_backend()
        initial_frame_count = len(self.frame_positions)
        self.window._request_timeline_preview(position_seconds)
        self._wait_until(
            lambda: (
                self.window.controller is not None
                and abs(
                    self.window.controller.snapshot().position_seconds - position_seconds,
                )
                < 0.04
            ),
            f"GTK seek did not reach {position_seconds:.2f}s",
        )
        self._wait_until(
            lambda: any(
                abs(frame_position - position_seconds) < 0.04
                for frame_position, _generation in self.frame_positions[initial_frame_count:]
            ),
            f"GTK did not deliver a decoded frame at {position_seconds:.2f}s",
        )
        self._wait_until(
            lambda: self.window.preview.get_paintable() is not None,
            "GTK preview did not display a decoded texture",
        )
        self._pump_display(20)
        return _texture_rgba(
            self.window.preview.get_paintable(),
            fallback_path=self.fixture_root / "displayed-texture.png",
            gdk_pixbuf=self.GdkPixbuf,
        )

    def _close_window(self) -> None:
        window = getattr(self, "window", None)
        if window is not None:
            window.close()
            self._pump_display(10)

    def _quit_application(self) -> None:
        application = getattr(self, "application", None)
        if application is not None:
            application.quit()
            self._pump_display(5)

    def _play_pause_once(self, label: str) -> None:
        self.window.play_button.activate()
        self._wait_until(
            lambda: (
                self.window.controller is not None
                and self.window.controller.snapshot().state == PlaybackState.PLAYING
            ),
            f"{label} native GTK Play activation did not start preview",
        )
        self._wait_until(
            lambda: self.window.preview.get_paintable() is not None,
            f"{label} preview did not display a decoded texture",
        )
        self.window.play_button.activate()
        self._wait_until(
            lambda: (
                self.window.controller is not None
                and self.window.controller.snapshot().state == PlaybackState.PAUSED
            ),
            f"{label} native GTK Play activation did not pause preview",
        )

    def test_preflight_probes_audible_sources_and_layout_before_gtk_guard(self):
        self.assertEqual(len(self.fixture.sources), 4)
        for source in self.fixture.sources:
            probe = probe_media(source)
            self.assertTrue(probe.audio_stream_present, source.name)
            self.assertGreater(probe.duration_seconds, 0.0)
            self.assertGreater(probe.width, 0)
            self.assertGreater(probe.height, 0)
            self.assertEqual(_sha256(source), self.fixture.source_hashes[source])
        expected_counts = {
            1_250_000: 2,
            2_250_000: 4,
            3_000_000: 3,
            3_750_000: 0,
            4_500_000: 1,
        }
        for position_ticks, expected_count in expected_counts.items():
            interval = self.fixture.layout.interval_at(position_ticks)
            self.assertIsNotNone(interval)
            assert interval is not None
            self.assertEqual(len(interval.active_block_ids), expected_count)

    def test_real_gtk_preview_shows_synchronized_slots_boundaries_and_gap(self):
        self._open_project(self.fixture.project_path)
        self._require_preview_backend()
        samples = (
            (1.25, 2),
            (2.25, 4),
            (3.0, 3),
            (3.49, 3),
            (3.5, 0),
            (3.75, 0),
            (4.49, 2),
            (4.5, 1),
        )
        for position_seconds, expected_active_count in samples:
            interval = self.fixture.layout.interval_at(round(position_seconds * 1_000_000))
            self.assertIsNotNone(interval)
            assert interval is not None
            self.assertEqual(len(interval.active_block_ids), expected_active_count)
            pixels, width, height = self._seek_and_capture(position_seconds)
            _assert_texture_matches_interval(
                self,
                pixels,
                width,
                height,
                interval,
                self.fixture,
            )
            self.assertAlmostEqual(
                self.window.project.playhead_seconds,
                position_seconds,
                delta=0.04,
            )
            if interval.active_block_ids:
                self.assertIn(self.window.selected_segment_id, interval.active_block_ids)
                self.assertEqual(
                    set(self.window.selected_segment_ids),
                    {self.window.selected_segment_id},
                )
        for source, expected_hash in self.fixture.source_hashes.items():
            self.assertEqual(_sha256(source), expected_hash)

    def test_native_play_pause_button_controls_real_silent_preview(self):
        self._open_project(self.fixture.project_path)
        self._require_preview_backend()
        selected_segment_id = self.window.selected_segment_id
        self.window._request_timeline_preview(2.25)
        self._pump_display(20)

        self.window.play_button.activate()
        self._wait_until(
            lambda: (
                self.window.controller is not None
                and self.window.controller.snapshot().state == PlaybackState.PLAYING
            ),
            "native GTK Play activation did not start the synchronized preview",
        )
        self._wait_until(
            lambda: self.window.preview.get_paintable() is not None,
            "playing preview did not deliver a displayed texture",
        )
        self.window.play_button.activate()
        self._wait_until(
            lambda: (
                self.window.controller is not None
                and self.window.controller.snapshot().state == PlaybackState.PAUSED
            ),
            "native GTK Play activation did not pause the synchronized preview",
        )
        paused_pixels, width, height = _texture_rgba(
            self.window.preview.get_paintable(),
            fallback_path=self.fixture_root / "paused-texture.png",
            gdk_pixbuf=self.GdkPixbuf,
        )
        self._pump_display(20)
        stable_pixels, stable_width, stable_height = _texture_rgba(
            self.window.preview.get_paintable(),
            fallback_path=self.fixture_root / "stable-texture.png",
            gdk_pixbuf=self.GdkPixbuf,
        )
        self.assertEqual((stable_width, stable_height), (width, height))
        self.assertEqual(stable_pixels, paused_pixels)
        self.assertEqual(self.window.selected_segment_id, selected_segment_id)

    def _prepare_timed_preview(self) -> tuple[list[tuple[float, float]], object]:
        timed_frames: list[tuple[float, float]] = []
        original_on_frame = self.window._on_frame

        def capture_timed_frame(frame, generation=None):
            timed_frames.append((time.monotonic(), frame.position_seconds))
            original_on_frame(frame, generation)

        self.window._on_frame = capture_timed_frame
        self._open_project(self.fixture.project_path)
        self._require_preview_backend()
        self.window._request_timeline_preview(1.25)
        self._pump_display(20)
        timed_frames.clear()
        assert self.window.backend is not None
        assert self.window.controller is not None
        return timed_frames, self.window.backend._frame_for_interval

    def test_native_playback_position_tracks_observed_wall_time_under_decode_delay(self):
        timed_frames, original_decode = self._prepare_timed_preview()
        assert self.window.backend is not None
        decode_latencies: list[float] = []

        def delayed_decode(position_seconds, interval, **kwargs):
            started_at = time.monotonic()
            time.sleep(0.22)
            try:
                return original_decode(position_seconds, interval, **kwargs)
            finally:
                decode_latencies.append(time.monotonic() - started_at)

        with patch.object(
            self.window.backend,
            "_frame_for_interval",
            side_effect=delayed_decode,
        ):
            started_at = time.monotonic()
            self.window.play_button.activate()
            self._wait_until(
                lambda: (
                    self.window.controller is not None
                    and self.window.controller.snapshot().state == PlaybackState.PLAYING
                ),
                "native GTK delayed preview did not start",
            )
            self._wait_until(
                lambda: len(timed_frames) >= 4,
                "native GTK delayed preview did not deliver four frames",
            )
            observed_decode_latency = max(decode_latencies[-4:])
            observed_position = self.window.controller.snapshot().position_seconds
            expected_position = max(
                1.25,
                1.25 + time.monotonic() - started_at - observed_decode_latency,
            )
            self.assertGreaterEqual(
                observed_position,
                expected_position - observed_decode_latency,
            )
            self.window.play_button.activate()
            self._wait_until(
                lambda: (
                    self.window.controller is not None
                    and self.window.controller.snapshot().state == PlaybackState.PAUSED
                ),
                "native GTK delayed preview did not pause",
            )

    def test_native_pause_drops_inflight_decode_frame_after_control_settles(self):
        timed_frames, original_decode = self._prepare_timed_preview()
        assert self.window.backend is not None
        decode_started = threading.Event()
        release_decode = threading.Event()
        decode_returned = threading.Event()

        def gated_decode(position_seconds, interval, **kwargs):
            decode_started.set()
            release_decode.wait(timeout=2.0)
            try:
                return original_decode(position_seconds, interval, **kwargs)
            finally:
                decode_returned.set()

        self.addCleanup(release_decode.set)
        with patch.object(
            self.window.backend,
            "_frame_for_interval",
            side_effect=gated_decode,
        ):
            self.window.play_button.activate()
            self._wait_until(decode_started.is_set, "delayed GTK decode did not start")
            self._wait_until(
                lambda: (
                    self.window.controller is not None
                    and self.window.controller.snapshot().state == PlaybackState.PLAYING
                ),
                "native GTK gated preview did not start",
            )
            self.window.play_button.activate()
            pause_returned_at = time.monotonic()
            self._wait_until(
                lambda: (
                    self.window.controller is not None
                    and self.window.controller.snapshot().state == PlaybackState.PAUSED
                ),
                "native GTK gated preview did not pause",
            )
            release_decode.set()
            self._wait_until(
                decode_returned.is_set,
                "gated GTK decode did not settle after pause",
            )
            self._pump_display(30)
            self.assertFalse(
                any(timestamp >= pause_returned_at for timestamp, _position in timed_frames),
                "an in-flight frame was published after native GTK pause returned",
            )

    def test_one_track_audible_source_never_launches_audio_preview_process(self):
        project, project_path, source_hash = _one_track_fixture(self.fixture)
        legacy_project, legacy_path, legacy_source_hash = _legacy_one_track_fixture(self.fixture)
        self.assertEqual(project.timeline.timing_mode, "absolute")
        self.assertEqual(legacy_project.timeline.timing_mode, "legacy-ripple")
        real_popen = subprocess.Popen
        with patch.object(subprocess, "Popen", wraps=real_popen) as popen:
            self._open_project(project_path)
            self._require_preview_backend()
            self._play_pause_once("synchronized one-track")
            self._open_project(legacy_path)
            self._require_preview_backend()
            self._play_pause_once("legacy one-track")

        commands = _assert_video_only_commands(self, popen.call_args_list)
        self.assertTrue(commands, "the real FFmpeg video decoder was never launched")
        self.assertFalse(
            any(
                "-map" in command
                and any(stream.startswith("0:a") for stream in command[command.index("-map") + 1 :])
                for command in commands
            ),
            "preview launched an FFmpeg audio output mapping",
        )
        self.assertEqual(_sha256(self.fixture.sources[0]), source_hash)
        self.assertEqual(_sha256(self.fixture.sources[0]), legacy_source_hash)

    def test_rapid_seek_reload_suppresses_old_generation_frames(self):
        seen_generations: list[int | None] = []
        original_on_frame = self.window._on_frame

        def capture_frame(frame, generation=None):
            seen_generations.append(generation)
            original_on_frame(frame, generation)

        self.window._on_frame = capture_frame
        self._open_project(self.fixture.project_path)
        self._require_preview_backend()
        self.window._request_timeline_preview(0.75)
        self.window._request_timeline_preview(4.5)
        old_generation = self.window._playback_generation
        seen_generations.clear()
        self.window._load_project_path(self.fixture.project_path)
        self._wait_until(
            lambda: (
                self.window.project_path == self.fixture.project_path
                and self.window.controller is not None
                and self.window._playback_generation > old_generation
            ),
            "rapid project reload did not install a new playback generation",
        )
        new_generation = self.window._playback_generation
        self._pump_display(40)
        self.assertTrue(seen_generations)
        self.assertTrue(
            all(generation == new_generation for generation in seen_generations),
            "a stale decoder generation published a GTK frame after reload",
        )

    def test_empty_saved_and_removed_timelines_clear_preview_and_restore_playback(self):
        fixture = self.fixture
        empty_project = Project.from_dict(fixture.project.to_dict())
        segment_ids = tuple(segment.segment_id for segment in empty_project.timeline.segment_items)
        remove_blocks(
            empty_project,
            segment_ids,
            selection_ids=segment_ids,
            focused_segment_id=segment_ids[0],
        )
        empty_project_path = self.fixture_root / "empty-four-track.framestudio.json"
        save_project(empty_project, empty_project_path)
        source_paths = tuple(Path(source.path) for source in fixture.project.sources)
        source_hashes = {path: _sha256(path) for path in source_paths}

        self._open_project(fixture.project_path)
        self._seek_and_capture(2.25)
        self._open_project(empty_project_path)

        self.assertEqual(
            tuple(Path(source.path) for source in self.window.project.sources),
            source_paths,
        )
        _assert_empty_preview_state(self, self.window)
        self.assertIsNone(self.window.preview.get_paintable())
        self.assertFalse(self.window.play_button.get_sensitive())

        self._open_project(fixture.project_path)
        self._wait_until(
            lambda: self.window.preview.get_paintable() is not None,
            "GTK preview did not restore before empty removal",
        )
        restored_project = self.window.project
        assert restored_project is not None
        receipt = remove_blocks(
            restored_project,
            segment_ids,
            selection_ids=segment_ids,
            focused_segment_id=segment_ids[0],
        )
        self.window._refresh_timeline()
        self._wait_until(
            lambda: self.window.backend is None and self.window.controller is None,
            "GTK empty refresh retained a playback backend",
        )
        _assert_empty_preview_state(self, self.window)
        self.assertIsNone(self.window.preview.get_paintable())
        self.assertFalse(self.window.play_button.get_sensitive())
        self.assertEqual(
            tuple(Path(source.path) for source in restored_project.sources),
            source_paths,
        )

        undo_removed_blocks(restored_project, receipt)
        self.window._refresh_timeline()
        self._require_preview_backend()
        self._wait_until(
            lambda: self.window.preview.get_paintable() is not None,
            "GTK preview did not restore after undoing all removals",
        )
        for path, expected_hash in source_hashes.items():
            self.assertEqual(_sha256(path), expected_hash)

    def test_decoder_failure_surfaces_in_gtk_and_releases_resources(self):
        self._open_project(self.fixture.project_path)
        self._require_preview_backend()
        self.window.preview.set_paintable(None)
        self.window.backend.ffmpeg_path = "framestudio-t120-missing-ffmpeg"
        self.window._request_timeline_preview(1.25)
        self._wait_until(
            lambda: self.window.status_label.get_text().startswith("Error:"),
            "decoder failure did not reach the visible GTK error path",
        )
        self.assertIsNone(self.window.preview.get_paintable())
        self.assertIsNone(getattr(self.window.backend, "_preview_process", None))
        self.assertIsNone(getattr(self.window.backend, "_process", None))
        self.assertNotEqual(
            self.window.controller.snapshot().state,
            PlaybackState.PLAYING,
        )


if __name__ == "__main__":
    unittest.main()
