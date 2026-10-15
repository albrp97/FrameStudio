import hashlib
import os
import subprocess
import sys
import threading
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import cairo

from framestudio.app_playback import (
    deliver_latest_frame,
    on_frame,
    poll_playback,
    start_smoke_test,
    update_playback_controls,
)
from framestudio.model import Segment, SegmentTimeline, VisualTransform
from framestudio.model_timeline import TimelineTrack
from framestudio.timeline import create_timeline_canvas
from framestudio.timeline_geometry import layout_timeline_segments


def gtk_modules():
    import gi

    gi.require_foreign("cairo")
    gi.require_version("Gtk", "4.0")
    from gi.repository import GLib, Gtk

    if not Gtk.init_check():
        raise unittest.SkipTest("A working GTK display is required")
    return Gtk, GLib


def pump(GLib, duration=0.08):
    deadline = time.monotonic() + duration
    context = GLib.MainContext.default()
    while time.monotonic() < deadline:
        while context.pending():
            context.iteration(False)
        time.sleep(0.001)


def large_timeline():
    blocks = tuple(
        Segment(
            segment_id=f"segment-{index}",
            start_seconds=0,
            end_seconds=720,
            source_id=f"source-{index}",
            timeline_start_seconds=index * 720,
            timeline_end_seconds=(index + 1) * 720,
            track_id="track-1",
        )
        for index in range(200)
    )
    return SegmentTimeline.from_tracks(
        (TimelineTrack("track-1", blocks),),
        source_durations={f"source-{index}": 720 for index in range(200)},
    )


class LargeTimelinePerformanceTests(unittest.TestCase):
    def setUp(self):
        Gtk, _ = gtk_modules()
        self.canvas = create_timeline_canvas(Gtk)()
        self.timeline = SegmentTimeline(40 * 3600.0)
        self.canvas.set_timeline(self.timeline)
        self.context = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 800, 124))

    def draw(self):
        self.canvas._draw(None, self.context, 800, 124)

    def test_playhead_draw_reuses_validated_geometry(self):
        with patch.object(self.timeline, "validate", wraps=self.timeline.validate) as validate:
            self.draw()
            first_count = validate.call_count
            self.canvas.set_playhead(1.0)
            self.draw()
            self.assertEqual(validate.call_count, first_count)

    def test_public_edit_invalidates_cached_geometry(self):
        self.draw()
        left, right = self.timeline.split(72000)
        self.draw()
        with patch.object(self.canvas, "_draw_clip") as draw_clip:
            self.draw()
        self.assertEqual(
            [call.args[1].segment_id for call in draw_clip.call_args_list],
            [left.segment_id, right.segment_id],
        )

    def test_unchanged_playhead_does_not_queue_idle_redraw(self):
        self.canvas.set_playhead(1.0)
        with patch.object(self.canvas, "queue_draw") as queue_draw:
            self.canvas.set_playhead(1.0)
        queue_draw.assert_not_called()

    def test_clipped_draw_does_not_paint_offscreen_clips(self):
        self.timeline.split(72000)
        self.canvas.set_zoom(12)
        self.context.rectangle(0, 0, 800, 124)
        self.context.clip()
        with patch.object(self.canvas, "_draw_clip") as draw_clip:
            self.draw()
        self.assertEqual(draw_clip.call_count, 1)

    def test_layout_helper_still_rejects_invalid_model(self):
        self.timeline.source_duration_seconds = -1
        with self.assertRaises(ValueError):
            layout_timeline_segments(self.timeline, 800, 1)

    def test_edit_revision_track_activation_and_new_project_refresh_cache(self):
        timeline = large_timeline()
        self.canvas.set_timeline(timeline)
        first = timeline.segment_items[0].segment_id
        with patch(
            "framestudio.timeline.layout_timeline_segments", wraps=layout_timeline_segments
        ) as layout:
            self.draw()
            self.assertEqual(layout.call_count, 0)
            timeline.set_visual_transform((first,), VisualTransform(zoom=2, offset_x=100))
            self.draw()
            timeline.enable_triplicate((first,))
            self.draw()
            timeline.set_deleted(first, True)
            self.draw()
            second_track = timeline.add_track()
            self.draw()
            revision = timeline.revision
            timeline.set_active_track(second_track)
            self.assertEqual(timeline.revision, revision)
            self.draw()
            self.assertTrue(self.canvas._layout_rows[1].active)
            timeline.set_deleted(first, False)
            timeline.move_block(first, timeline_start_ticks=0, target_track_id=second_track)
            self.draw()
            self.assertEqual(layout.call_count, 6)
        first_block = timeline.find(first)
        self.assertEqual(first_block.visual_transform.zoom, 2)
        self.assertTrue(first_block.triplicate.enabled)
        self.assertEqual(
            self.canvas._layout(),
            layout_timeline_segments(timeline, 800, self.canvas.get_zoom()),
        )
        self.canvas.set_timeline(SegmentTimeline(3))
        self.canvas.set_playhead(144000)
        self.assertEqual(self.canvas.get_playhead_seconds(), 3)

    def test_selection_and_resize_zoom_do_not_reuse_stale_layout(self):
        self.timeline.split(72000)
        ids = tuple(block.segment_id for block in self.timeline.segment_items)
        self.canvas.set_selected_segments(ids, ids[0])
        self.assertEqual(self.canvas.get_selected_segment_ids(), ids)
        self.canvas.set_viewport_width(1200)
        self.canvas.set_zoom(4)
        self.assertEqual(self.canvas._layout(), layout_timeline_segments(self.timeline, 1200, 4))
        self.canvas.fit_to_view()
        self.assertEqual(self.canvas.get_selected_segment_ids(), ids)

    def test_clearing_timeline_releases_derived_geometry(self):
        self.draw()
        self.canvas.set_timeline(None)
        self.assertEqual(self.canvas._layout(), ())
        self.assertIsNone(self.canvas._layout_segments)
        self.assertIsNone(self.canvas._layout_tracks)
        self.assertEqual(self.canvas._layout_clips, ())

    def test_scrolled_deleted_clip_and_ruler_pixels_match_full_canvas(self):
        self.timeline.split(72000)
        self.timeline.set_deleted(self.timeline.segment_items[1].segment_id, True)
        self.canvas.set_zoom(12)
        width = int(self.canvas.get_content_width())
        full = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, 124)
        self.canvas._draw(None, cairo.Context(full), width, 124)
        expected = cairo.ImageSurface(cairo.FORMAT_ARGB32, 800, 124)
        expected_context = cairo.Context(expected)
        expected_context.set_source_surface(full, -5500, 0)
        expected_context.paint()
        actual = cairo.ImageSurface(cairo.FORMAT_ARGB32, 800, 124)
        actual_context = cairo.Context(actual)
        actual_context.translate(-5500, 0)
        self.canvas._draw(None, actual_context, width, 124)
        differences = [
            abs(actual_channel - expected_channel)
            for actual_channel, expected_channel in zip(
                bytes(actual.get_data()), bytes(expected.get_data()), strict=True
            )
        ]
        # Cairo may round an antialiased channel by one after coordinate translation.
        self.assertLessEqual(max(differences), 1)
        self.assertLess(sum(difference > 0 for difference in differences), 800)

    def test_idle_poll_does_not_scan_audio_or_redraw_unchanged_playhead(self):
        from framestudio.playback import PlaybackState

        window = SimpleNamespace(
            backend=SimpleNamespace(current_position=lambda: 1.0),
            controller=MagicMock(),
            project=MagicMock(),
            segment_timeline=None,
            play_button=MagicMock(),
            position_label=MagicMock(),
            timeline_canvas=self.canvas,
        )
        window.controller.snapshot.return_value = SimpleNamespace(
            state=PlaybackState.PAUSED, position_seconds=1.0
        )
        window._update_playback_controls = lambda: update_playback_controls(window)
        poll_playback(window)
        with (
            patch.object(self.canvas, "queue_draw") as queue_draw,
            patch("framestudio.app_project._preview_audio_decisions") as audio_scan,
            patch("framestudio.app_project._audio_sources_needing_analysis") as audio_sources,
            patch("framestudio.app_project.format_audio_decisions") as audio_format,
        ):
            for _ in range(10):
                poll_playback(window)
        queue_draw.assert_not_called()
        audio_scan.assert_not_called()
        audio_sources.assert_not_called()
        audio_format.assert_not_called()


class AsyncSmokeTests(unittest.TestCase):
    def make_window(self):
        return SimpleNamespace(
            project=None,
            controller=None,
            _source_load_in_progress=True,
            _start_smoke_test=MagicMock(),
            _finish_smoke_test=MagicMock(),
            _show_error=MagicMock(),
            _stop_backend=MagicMock(),
            get_application=MagicMock(),
        )

    def test_smoke_waits_for_async_source_load_without_finishing(self):
        window = self.make_window()
        glib = MagicMock()
        self.assertFalse(start_smoke_test(window, glib))
        window._finish_smoke_test.assert_not_called()
        window._show_error.assert_not_called()
        glib.timeout_add.assert_called_once_with(50, window._start_smoke_test)

    def test_smoke_source_load_failure_exits_nonzero(self):
        window = self.make_window()
        window._source_load_in_progress = False
        with self.assertRaises(SystemExit) as raised:
            start_smoke_test(window, MagicMock())
        self.assertNotEqual(raised.exception.code, 0)
        window._finish_smoke_test.assert_not_called()

    def test_smoke_source_load_timeout_exits_nonzero(self):
        window = self.make_window()
        window._smoke_load_started = 1.0
        with patch("framestudio.app_playback.time.monotonic", return_value=62):
            with self.assertRaises(SystemExit):
                start_smoke_test(window, MagicMock())
        window._finish_smoke_test.assert_not_called()


@unittest.skipUnless(
    os.environ.get("FRAMESTUDIO_TIMELINE_FUNCTIONALITY_MEDIA"),
    "Set FRAMESTUDIO_TIMELINE_FUNCTIONALITY_MEDIA to a generated short video",
)
class LargeTimelineGtkFunctionalityTests(unittest.TestCase):
    """Public GTK and CLI boundaries; run with the shared benchmark flock."""

    def test_scrolling_selection_playhead_and_real_media_frame_delivery(self):
        import gi

        gi.require_version("Gdk", "4.0")
        from gi.repository import Gdk

        from framestudio.ffmpeg_playback import FfmpegPlaybackBackend

        Gtk, GLib = gtk_modules()
        media = Path(os.environ["FRAMESTUDIO_TIMELINE_FUNCTIONALITY_MEDIA"]).resolve()
        before_hash = hashlib.sha256(media.read_bytes()).hexdigest()
        canvas = create_timeline_canvas(Gtk)()
        timeline = large_timeline()
        canvas.set_timeline(timeline)
        canvas.set_viewport_width(900)
        canvas.set_zoom(12)
        canvas.set_playhead(72000.125)
        selected = (timeline.segment_items[0].segment_id, timeline.segment_items[1].segment_id)
        canvas.set_selected_segments(selected)
        scroll = Gtk.ScrolledWindow()
        scroll.set_min_content_height(150)
        scroll.set_vexpand(True)
        scroll.set_child(canvas)
        preview = Gtk.Picture()
        preview.set_size_request(320, 180)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box.append(preview)
        box.append(scroll)
        window = Gtk.Window()
        window.set_default_size(900, 360)
        window.set_resizable(False)
        window.set_child(box)
        clips_drawn = []
        original_clip = canvas._draw_clip

        def record_clip(context, clip):
            clips_drawn.append(clip.segment_id)
            original_clip(context, clip)

        canvas._draw_clip = record_clip
        delivery = SimpleNamespace(
            _frame_lock=threading.Lock(),
            _latest_frame=None,
            _frame_delivery_scheduled=False,
            _playback_generation=1,
            preview=preview,
        )
        delivery._deliver_latest_frame = lambda: deliver_latest_frame(delivery, Gdk, GLib)
        frames = []
        errors = []

        def receive_frame(frame):
            frames.append(frame)
            on_frame(delivery, frame, GLib, 1)

        backend = FfmpegPlaybackBackend(
            media, 320, 180, 30, 1, receive_frame, errors.append, lambda: None
        )
        try:
            window.present()
            pump(GLib)
            initial_visible = set(clips_drawn)
            self.assertTrue(initial_visible)
            self.assertLess(len(initial_visible), len(timeline.segment_items))
            clips_drawn.clear()
            scroll.get_hadjustment().set_value(4000)
            pump(GLib)
            self.assertTrue(clips_drawn, "Scrolling must invalidate the cached GTK drawing")
            self.assertTrue(set(clips_drawn).isdisjoint(initial_visible))
            self.assertEqual(canvas.get_selected_segment_ids(), selected)
            self.assertEqual(canvas.get_playhead_seconds(), 72000.125)
            canvas.set_viewport_width(1000)
            canvas.set_zoom(6)
            pump(GLib)
            self.assertEqual(canvas.get_selected_segment_ids(), selected)
            backend.request_preview(0.25)
            deadline = time.monotonic() + 10
            while preview.get_paintable() is None and not errors and time.monotonic() < deadline:
                pump(GLib, 0.02)
            self.assertFalse(errors)
            self.assertTrue(frames)
            self.assertIsNotNone(preview.get_paintable())
            self.assertEqual(preview.get_paintable().get_intrinsic_width(), 320)
            self.assertAlmostEqual(frames[-1].position_seconds, 0.25)
        finally:
            backend.close()
            window.destroy()
            pump(GLib)
        self.assertEqual(hashlib.sha256(media.read_bytes()).hexdigest(), before_hash)

    def test_public_cli_async_smoke_saves_reopens_and_rejects_missing_source(self):
        from framestudio.persistence import load_project

        media = Path(os.environ["FRAMESTUDIO_TIMELINE_FUNCTIONALITY_MEDIA"]).resolve()
        project_path = media.parent / "timeline-performance-functionality.framestudio.json"
        root = Path(__file__).resolve().parents[1]
        executable = [sys.executable, str(root / "framestudio.py")]
        before_hash = hashlib.sha256(media.read_bytes()).hexdigest()
        result = subprocess.run(
            executable
            + ["--source", str(media), "--smoke-test", "--smoke-project", str(project_path)],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=70,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(project_path.is_file())
        project = load_project(project_path)
        self.assertEqual(len(project.timeline.blocks), 2)
        self.assertEqual(sum(block.deleted for block in project.timeline.blocks), 1)
        self.assertEqual(project.playhead_seconds, 0)
        reopened = subprocess.run(
            executable + ["--project", str(project_path), "--smoke-test"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=70,
        )
        self.assertEqual(reopened.returncode, 0, reopened.stderr)
        missing = subprocess.run(
            executable
            + ["--source", str(media.with_name("missing-timeline-media.mp4")), "--smoke-test"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=15,
        )
        self.assertNotEqual(missing.returncode, 0)
        self.assertIn("Smoke test could not open", missing.stderr)
        unwritable = subprocess.run(
            executable
            + [
                "--source",
                str(media),
                "--smoke-test",
                "--smoke-project",
                str(media / "project.json"),
            ],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=70,
        )
        self.assertNotEqual(unwritable.returncode, 0)
        self.assertIn("Smoke test could not save", unwritable.stderr)
        self.assertEqual(hashlib.sha256(media.read_bytes()).hexdigest(), before_hash)
