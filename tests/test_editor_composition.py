import io
import json
import shutil
import subprocess
import threading
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from resolve_editor import app_timeline_actions
from resolve_editor.app_playback import (
    deliver_latest_frame,
    handle_backend_end,
    on_frame,
    on_key_pressed,
    on_timeline_scroll,
    request_timeline_preview,
    stop_backend,
)
from resolve_editor.app_project import (
    _finish_source_load,
    _load_source_worker,
    attach_project,
    load_project_path,
    load_source,
    refresh_playback_backend,
)
from resolve_editor.cli import cli_main
from resolve_editor.composition import (
    CANVAS_HEIGHT,
    CANVAS_WIDTH,
    MAX_OFFSET_X,
    MAX_OFFSET_Y,
    MAX_ZOOM,
    TriplicateGroup,
    VisualTransform,
    focus_offset_bounds,
)
from resolve_editor.composition_render import segment_video_filters
from resolve_editor.export import execute_export
from resolve_editor.ffmpeg_playback import VideoFrame
from resolve_editor.media import probe_media
from resolve_editor.model import Project, ProjectValidationError, SegmentTimeline
from resolve_editor.operations import (
    apply_visual_transform,
    clean_visual_modifications,
    copy_visual_transform,
    disable_triplicate,
    enable_triplicate,
    paste_segments_after_selection,
    plan_project_export,
)
from resolve_editor.persistence import load_project, save_project
from resolve_editor.playback import PlaybackController, PlaybackState
from resolve_editor.upscale_policy import UpscalePolicy


def metadata(duration=10.0):
    return {
        "duration_seconds": duration,
        "width": 320,
        "height": 180,
        "frame_rate": "10/1",
        "video_codec": "h264",
        "audio_codec": None,
        "audio_stream_present": False,
        "format_name": "mp4",
    }


def make_project(root: Path) -> Project:
    source = root / "source.mp4"
    source.write_bytes(b"fixture")
    return Project.create(source, metadata())


def run_cli(*arguments: str):
    stdout = io.StringIO()
    stderr = io.StringIO()
    result = cli_main(list(arguments), stdout=stdout, stderr=stderr)
    return result, stdout, stderr


class EditorCompositionTests(unittest.TestCase):
    def test_export_disables_project_lifecycle_controls(self):
        controls = [MagicMock() for _ in range(4)]
        window = SimpleNamespace(
            _export_in_progress=True,
            project=None,
            segment_timeline=None,
            selected_segment_ids=(),
            selected_segment_id=None,
            export_button=MagicMock(),
            timeline_canvas=MagicMock(),
            focus_zoom_spin=MagicMock(),
            focus_offset_x_spin=MagicMock(),
            focus_offset_y_spin=MagicMock(),
            copy_focus_button=MagicMock(),
            clean_focus_button=MagicMock(),
            triplicate_button=MagicMock(),
            timeline_output_label=MagicMock(),
            timeline_zoom_label=MagicMock(),
            _update_selected_clip_label=MagicMock(),
            open_source_button=controls[0],
            open_project_button=controls[1],
            save_button=controls[2],
            reopen_button=controls[3],
        )
        window.timeline_canvas.get_zoom.return_value = 1.0

        app_timeline_actions.update_segment_controls(window)

        for control in controls:
            control.set_sensitive.assert_called_once_with(False)

    def test_source_loading_is_blocked_during_export(self):
        window = SimpleNamespace(
            _export_in_progress=True,
            _set_status=MagicMock(),
        )
        with patch(
            "resolve_editor.app_project.create_project_from_source",
            side_effect=AssertionError("source loading must be blocked"),
        ):
            self.assertFalse(load_source(window, Path("source.mp4")))

        window._set_status.assert_called_once_with(
            "Editing is disabled while export is in progress",
        )

    def test_source_loading_starts_a_worker_and_reports_clip_progress(self):
        window = SimpleNamespace(
            _export_in_progress=False,
            _source_load_in_progress=False,
            _set_status=MagicMock(),
            _update_segment_controls=MagicMock(),
        )
        glib = SimpleNamespace(idle_add=MagicMock())
        with patch("resolve_editor.app_project.threading.Thread") as thread:
            self.assertFalse(
                load_source(
                    window,
                    (Path("first.mp4"), Path("second.mp4")),
                    glib,
                )
            )

        self.assertTrue(window._source_load_in_progress)
        thread.assert_called_once()
        window._set_status.assert_called_once_with("Loading clip 1/2 (0%)")

    def test_source_loading_worker_reports_monotonic_per_clip_progress(self):
        statuses = []
        window = SimpleNamespace(
            _source_load_generation=4,
            _set_status=statuses.append,
        )
        glib = SimpleNamespace(
            idle_add=lambda callback, *args: callback(*args),
        )

        def build_project(_paths, progress_callback):
            progress_callback(1, 2, "probe")
            progress_callback(2, 2, "probe")
            return object()

        def analyze_audio(_project, progress_callback):
            progress_callback(1, 2, "audio")
            progress_callback(2, 2, "audio")

        with (
            patch(
                "resolve_editor.app_project._build_source_project",
                side_effect=build_project,
            ),
            patch(
                "resolve_editor.app_project.analyze_project_audio",
                side_effect=analyze_audio,
            ),
            patch("resolve_editor.app_project._finish_source_load"),
        ):
            _load_source_worker(
                window,
                (Path("first.mp4"), Path("second.mp4")),
                4,
                glib,
            )

        self.assertEqual(
            statuses,
            [
                "Loading clip 1/2 (25%)",
                "Loading clip 2/2 (50%)",
                "Loading clip 1/2 (75%)",
                "Loading clip 2/2 (100%)",
            ],
        )

    def test_stale_source_load_completion_does_not_replace_current_project(self):
        current_project = object()
        window = SimpleNamespace(
            _source_load_generation=2,
            _source_load_in_progress=True,
            project=current_project,
            _show_error=MagicMock(),
            _update_segment_controls=MagicMock(),
        )

        self.assertFalse(
            _finish_source_load(
                window,
                1,
                (Path("stale.mp4"),),
                object(),
                None,
            )
        )

        self.assertIs(window.project, current_project)
        self.assertTrue(window._source_load_in_progress)
        window._show_error.assert_not_called()
        window._update_segment_controls.assert_not_called()

    def test_source_load_failure_clears_loading_state(self):
        window = SimpleNamespace(
            _source_load_generation=1,
            _source_load_in_progress=True,
            _show_error=MagicMock(),
            _update_segment_controls=MagicMock(),
        )

        self.assertFalse(
            _finish_source_load(
                window,
                1,
                (Path("broken.mp4"),),
                None,
                "Could not probe broken.mp4",
            )
        )

        self.assertFalse(window._source_load_in_progress)
        window._show_error.assert_called_once_with("Could not probe broken.mp4")
        window._update_segment_controls.assert_called_once_with()

    def test_project_loading_is_blocked_during_export(self):
        window = SimpleNamespace(
            _export_in_progress=True,
            _set_status=MagicMock(),
        )
        with patch(
            "resolve_editor.app_project.load_project",
            side_effect=AssertionError("project loading must be blocked"),
        ):
            self.assertFalse(load_project_path(window, Path("project.resolve.json")))

        window._set_status.assert_called_once_with(
            "Editing is disabled while export is in progress",
        )

    def test_queued_frame_from_replaced_playback_generation_is_not_painted(self):
        idle_callbacks = []
        glib = SimpleNamespace(
            Bytes=SimpleNamespace(new=MagicMock()),
            idle_add=lambda callback: idle_callbacks.append(callback),
        )
        gdk = SimpleNamespace(
            MemoryFormat=SimpleNamespace(R8G8B8A8="rgba"),
            MemoryTexture=SimpleNamespace(new=MagicMock()),
        )
        window = SimpleNamespace(
            _frame_lock=threading.Lock(),
            _latest_frame=None,
            _frame_delivery_scheduled=False,
            _playback_generation=1,
            _deliver_latest_frame=MagicMock(),
            preview=MagicMock(),
        )
        frame = VideoFrame(b"\x00" * 4, 1, 1, 0.0)

        on_frame(window, frame, glib, generation=1)
        window._playback_generation = 2
        self.assertEqual(len(idle_callbacks), 1)

        self.assertFalse(deliver_latest_frame(window, gdk, glib))
        gdk.MemoryTexture.new.assert_not_called()
        window.preview.set_paintable.assert_not_called()

    def test_deleted_timeline_positions_map_to_edited_playback_positions(self):
        timeline = SegmentTimeline(10.0)
        timeline.split(3.0)
        timeline.split(7.0)
        middle = timeline.segment_items[1]
        timeline.set_deleted(middle.segment_id, True)

        self.assertAlmostEqual(timeline.timeline_duration_seconds, 10.0)
        self.assertAlmostEqual(timeline.edited_duration_seconds, 6.0)
        self.assertAlmostEqual(timeline.timeline_to_edited_position(8.0), 4.0)
        self.assertAlmostEqual(timeline.edited_to_timeline_position(4.0), 8.0)

    def test_timeline_preview_seeks_visible_positions_after_deleted_blocks(self):
        with TemporaryDirectory() as temporary_directory:
            project = make_project(Path(temporary_directory))
            project.timeline.split(3.0)
            project.timeline.split(7.0)
            project.timeline.set_deleted(project.timeline.segments[1].segment_id, True)
            backend = MagicMock()
            window = SimpleNamespace(
                backend=backend,
                controller=PlaybackController(
                    backend,
                    project.timeline.edited_duration_seconds,
                ),
                project=project,
                segment_timeline=project.timeline,
                timeline_canvas=MagicMock(),
                _update_playback_controls=MagicMock(),
                _show_error=MagicMock(),
            )

            request_timeline_preview(window, 8.0)

            self.assertAlmostEqual(window.controller.snapshot().position_seconds, 4.0)
            backend.request_preview.assert_called_once_with(4.0)
            self.assertAlmostEqual(project.playhead_seconds, 8.0)
            window.timeline_canvas.set_playhead.assert_called_with(8.0)

    def test_b_key_splits_at_visible_playhead_after_deleted_block(self):
        with TemporaryDirectory() as temporary_directory:
            project = make_project(Path(temporary_directory))
            project.timeline.split(3.0)
            project.timeline.split(7.0)
            project.timeline.set_deleted(project.timeline.segments[1].segment_id, True)
            selected = project.timeline.segments[2]
            backend = MagicMock()
            window = SimpleNamespace(
                controller=PlaybackController(
                    backend,
                    project.timeline.edited_duration_seconds,
                    initial_position=4.0,
                ),
                project=project,
                segment_timeline=project.timeline,
                selected_segment_id=selected.segment_id,
                selected_segment_ids=(selected.segment_id,),
                _show_error=MagicMock(),
                _refresh_timeline=MagicMock(),
                _set_status=MagicMock(),
            )
            window._on_split_clicked = lambda button: app_timeline_actions.on_split_clicked(
                window,
                button,
            )
            gdk = SimpleNamespace(
                ModifierType=SimpleNamespace(
                    SHIFT_MASK=1,
                    CONTROL_MASK=2,
                ),
            )

            handled = on_key_pressed(window, None, ord("b"), 0, 0, gdk)

            self.assertTrue(handled)
            window._show_error.assert_not_called()
            self.assertEqual(
                [
                    (segment.start_seconds, segment.end_seconds)
                    for segment in project.timeline.segments
                ],
                [(0.0, 3.0), (3.0, 7.0), (7.0, 8.0), (8.0, 10.0)],
            )
            self.assertEqual(window.selected_segment_id, project.timeline.segments[3].segment_id)
            window._refresh_timeline.assert_called_once_with(window.selected_segment_id)
            window._set_status.assert_called_once_with("Split clip at 00:08")

    def test_b_key_cannot_mutate_timeline_during_export(self):
        with TemporaryDirectory() as temporary_directory:
            project = make_project(Path(temporary_directory))
            selected = project.timeline.segments[0]
            backend = MagicMock()
            window = SimpleNamespace(
                _export_in_progress=True,
                controller=PlaybackController(
                    backend,
                    project.timeline.edited_duration_seconds,
                    initial_position=4.0,
                ),
                project=project,
                segment_timeline=project.timeline,
                selected_segment_id=selected.segment_id,
                selected_segment_ids=(selected.segment_id,),
                _show_error=MagicMock(),
                _refresh_timeline=MagicMock(),
                _set_status=MagicMock(),
            )
            window._on_split_clicked = lambda button: app_timeline_actions.on_split_clicked(
                window,
                button,
            )
            gdk = SimpleNamespace(
                ModifierType=SimpleNamespace(
                    SHIFT_MASK=1,
                    CONTROL_MASK=2,
                ),
            )

            handled = on_key_pressed(window, None, ord("b"), 0, 0, gdk)

            self.assertTrue(handled)
            self.assertEqual(len(project.timeline.segments), 1)
            window._set_status.assert_called_once_with(
                "Editing is disabled while export is in progress",
            )

    def test_b_key_splits_mixed_block_at_visible_playhead_after_deleted_block(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            first_source = root / "first.mp4"
            second_source = root / "second.mp4"
            first_source.write_bytes(b"first")
            second_source.write_bytes(b"second")
            project = Project.create_multi(
                (
                    (first_source, metadata(duration=4.0)),
                    (second_source, metadata(duration=3.0)),
                ),
            )
            project.timeline.set_deleted(project.timeline.blocks[0].segment_id, True)
            selected = project.timeline.blocks[1]
            backend = MagicMock()
            window = SimpleNamespace(
                controller=PlaybackController(
                    backend,
                    project.timeline.edited_duration_seconds,
                    initial_position=1.0,
                ),
                project=project,
                segment_timeline=project.timeline,
                selected_segment_id=selected.segment_id,
                selected_segment_ids=(selected.segment_id,),
                _show_error=MagicMock(),
                _refresh_timeline=MagicMock(),
                _set_status=MagicMock(),
            )
            window._on_split_clicked = lambda button: app_timeline_actions.on_split_clicked(
                window,
                button,
            )
            gdk = SimpleNamespace(
                ModifierType=SimpleNamespace(
                    SHIFT_MASK=1,
                    CONTROL_MASK=2,
                ),
            )

            handled = on_key_pressed(window, None, ord("B"), 0, 0, gdk)

            self.assertTrue(handled)
            window._show_error.assert_not_called()
            self.assertEqual(
                [
                    (
                        segment.source_id,
                        segment.start_seconds,
                        segment.end_seconds,
                        segment.timeline_start,
                        segment.timeline_end,
                    )
                    for segment in project.timeline.blocks
                ],
                [
                    (project.sources[0].source_id, 0.0, 4.0, 0.0, 4.0),
                    (project.sources[1].source_id, 0.0, 1.0, 4.0, 5.0),
                    (project.sources[1].source_id, 1.0, 3.0, 5.0, 7.0),
                ],
            )
            self.assertEqual(window.selected_segment_id, project.timeline.blocks[2].segment_id)
            window._refresh_timeline.assert_called_once_with(window.selected_segment_id)
            window._set_status.assert_called_once_with("Split clip at 00:05")

    def test_focus_control_changes_apply_immediately_without_an_apply_button(self):
        with TemporaryDirectory() as temporary_directory:
            project = make_project(Path(temporary_directory))
            segment_id = project.timeline.segments[0].segment_id

            class Spin:
                def __init__(self, value):
                    self.value = value

                def get_value(self):
                    return self.value

            window = SimpleNamespace(
                project=project,
                selected_segment_ids=(segment_id,),
                selected_segment_id=segment_id,
                focus_zoom_spin=Spin(2.0),
                focus_offset_x_spin=Spin(120.0),
                focus_offset_y_spin=Spin(-80.0),
                _refresh_timeline=MagicMock(),
                _set_status=MagicMock(),
                _show_error=MagicMock(),
            )

            app_timeline_actions.on_focus_control_changed(window, None)

            self.assertEqual(
                project.timeline.find(segment_id).visual_transform,
                VisualTransform(zoom=2.0, offset_x=120.0, offset_y=-80.0),
            )
            window._refresh_timeline.assert_called_once_with(segment_id)

    def test_focus_scroll_updates_only_the_target_field_and_refreshes_preview(self):
        with TemporaryDirectory() as temporary_directory:
            project = make_project(Path(temporary_directory))
            segment_id = project.timeline.segments[0].segment_id
            apply_visual_transform(
                project,
                [segment_id],
                zoom=2.0,
                offset_x=100.0,
                offset_y=-50.0,
            )
            window = SimpleNamespace(
                project=project,
                segment_timeline=project.timeline,
                selected_segment_ids=(segment_id,),
                selected_segment_id=segment_id,
                _refresh_timeline=MagicMock(),
                _set_status=MagicMock(),
                _show_error=MagicMock(),
            )

            handled = app_timeline_actions.on_focus_control_scroll(
                window,
                "offset_x",
                None,
                0.0,
                -1.0,
            )

            self.assertTrue(handled)
            self.assertEqual(
                project.timeline.find(segment_id).visual_transform,
                VisualTransform(zoom=2.0, offset_x=110.0, offset_y=-50.0),
            )
            window._refresh_timeline.assert_called_once_with(segment_id)
            window._show_error.assert_not_called()

    def test_focus_scroll_updates_triplicate_group_atomically(self):
        with TemporaryDirectory() as temporary_directory:
            project = make_project(Path(temporary_directory))
            segment_id = project.timeline.segments[0].segment_id
            enable_triplicate(project, [segment_id])
            window = SimpleNamespace(
                project=project,
                segment_timeline=project.timeline,
                selected_segment_ids=(segment_id,),
                selected_segment_id=segment_id,
                _refresh_timeline=MagicMock(),
                _set_status=MagicMock(),
                _show_error=MagicMock(),
            )

            handled = app_timeline_actions.on_focus_control_scroll(
                window,
                "zoom",
                None,
                0.0,
                -10.0,
            )

            segment = project.timeline.find(segment_id)
            self.assertTrue(handled)
            self.assertEqual(segment.visual_transform.zoom, 2.0)
            self.assertIsNotNone(segment.triplicate)
            self.assertEqual(segment.triplicate.shared_transform, segment.visual_transform)
            window._refresh_timeline.assert_called_once_with(segment_id)

    def test_scroll_outside_focus_controls_keeps_playhead_navigation(self):
        backend = MagicMock()
        window = SimpleNamespace(
            controller=PlaybackController(backend, 60.0, initial_position=10.0),
            _seek_timeline=MagicMock(),
            timeline_viewport=MagicMock(),
        )
        event_controller = SimpleNamespace(get_current_event_state=lambda: 0)
        gdk = SimpleNamespace(
            ModifierType=SimpleNamespace(
                CONTROL_MASK=1,
                ALT_MASK=2,
                SHIFT_MASK=4,
            ),
        )

        handled = on_timeline_scroll(window, event_controller, 0.0, 1.0, gdk)

        self.assertTrue(handled)
        window._seek_timeline.assert_called_once_with(9.0)

    def test_triplicate_refresh_ignores_completion_from_replaced_backend(self):
        with TemporaryDirectory() as temporary_directory:
            project = make_project(Path(temporary_directory))
            segment_id = project.timeline.segments[0].segment_id
            direct_backend = MagicMock()
            window = SimpleNamespace(
                backend=None,
                controller=None,
                project=None,
                project_path=None,
                segment_timeline=None,
                source_frame_rate=10.0,
                timeline_canvas=MagicMock(),
                audio_status_label=MagicMock(),
                _on_frame=MagicMock(),
                _on_backend_error=MagicMock(),
                _on_backend_end=lambda _generation=None: handle_backend_end(window),
                _stop_backend=lambda: stop_backend(window),
                _update_selected_clip_label=MagicMock(),
                _update_playback_controls=MagicMock(),
                _update_segment_controls=MagicMock(),
            )

            with (
                patch("resolve_editor.app_project.ensure_project_audio_analysis") as analyze,
                patch("resolve_editor.app_project.FfmpegPlaybackBackend") as direct_type,
                patch("resolve_editor.app_project.FfmpegComposedPlaybackBackend") as composed_type,
            ):
                analyze.return_value = {
                    project.source.source_id: {"status": "not-applicable", "gain_db": 0.0},
                }
                direct_type.return_value = direct_backend
                composed_type.return_value = MagicMock()
                attach_project(window, project, None)
                old_backend_end = direct_type.call_args.args[7]
                self.assertTrue(window.controller.play())
                enable_triplicate(project, [segment_id])
                window._refresh_timeline = lambda selected=None: None

                refresh_playback_backend(window)
                self.assertEqual(window.controller.snapshot().state, PlaybackState.PLAYING)

                old_backend_end()

            self.assertEqual(window.controller.snapshot().state, PlaybackState.PLAYING)

    def test_transform_contract_clamps_interactive_values_and_rejects_invalid_state(self):
        transform = VisualTransform.clamped(
            zoom=MAX_ZOOM + 10,
            offset_x=MAX_OFFSET_X + 10,
            offset_y=-MAX_OFFSET_Y - 10,
        )

        self.assertEqual(transform.zoom, MAX_ZOOM)
        self.assertEqual(transform.offset_x, MAX_OFFSET_X)
        self.assertEqual(transform.offset_y, -MAX_OFFSET_Y)

        with self.assertRaisesRegex(ValueError, "zoom"):
            VisualTransform(zoom=0.5)
        with self.assertRaisesRegex(ValueError, "version"):
            VisualTransform.from_dict({"version": 99})

    def test_zoom_dependent_focus_bounds_reach_all_canvas_edges(self):
        self.assertEqual(focus_offset_bounds(1.0), ((-640.0, 640.0), (0.0, 0.0)))
        self.assertEqual(focus_offset_bounds(2.0), ((-960.0, 960.0), (-540.0, 540.0)))
        self.assertEqual(focus_offset_bounds(4.0), ((-2880.0, 2880.0), (-1620.0, 1620.0)))
        default_clamped = VisualTransform.clamped(zoom=1.0, offset_x=99999.0)
        self.assertEqual(default_clamped.offset_x, 640.0)
        transform = VisualTransform.clamped(
            zoom=4.0,
            offset_x=99999.0,
            offset_y=-99999.0,
        )
        self.assertEqual(transform.offset_x, 2880.0)
        self.assertEqual(transform.offset_y, -1620.0)
        with self.assertRaisesRegex(ValueError, "for zoom 1"):
            VisualTransform(zoom=1.0, offset_x=641.0)
        with self.assertRaisesRegex(ValueError, "for zoom 2"):
            VisualTransform(zoom=2.0, offset_x=961.0)

    def test_triplicate_default_zoom_accepts_horizontal_focus_offsets(self):
        timeline = SegmentTimeline(10.0)
        for offset_x in (-640.0, 640.0):
            transform = VisualTransform(zoom=1.0, offset_x=offset_x)
            segment = timeline.segments[0].with_triplicate(TriplicateGroup.create(transform))

            grouped = segment_video_filters(
                "[0:v:0]",
                segment,
                CANVAS_WIDTH,
                CANVAS_HEIGHT,
                "[outv]",
            )

            self.assertIn(f"{offset_x:g}", grouped[1])

    def test_default_zoom_triplicate_focus_control_updates_shared_transform(self):
        with TemporaryDirectory() as temporary_directory:
            project = make_project(Path(temporary_directory))
            segment_id = project.timeline.segments[0].segment_id
            enable_triplicate(project, [segment_id])

            class Spin:
                def __init__(self, value):
                    self.value = value

                def get_value(self):
                    return self.value

            window = SimpleNamespace(
                project=project,
                selected_segment_ids=(segment_id,),
                selected_segment_id=segment_id,
                focus_zoom_spin=Spin(1.0),
                focus_offset_x_spin=Spin(-640.0),
                focus_offset_y_spin=Spin(0.0),
                _refresh_timeline=MagicMock(),
                _set_status=MagicMock(),
                _show_error=MagicMock(),
            )

            app_timeline_actions.on_focus_control_changed(window, None)

            segment = project.timeline.find(segment_id)
            self.assertEqual(
                segment.visual_transform,
                VisualTransform(zoom=1.0, offset_x=-640.0),
            )
            self.assertIsNotNone(segment.triplicate)
            self.assertEqual(segment.triplicate.shared_transform, segment.visual_transform)
            window._show_error.assert_not_called()

    def test_default_zoom_triplicate_focus_controls_expose_horizontal_range(self):
        with TemporaryDirectory() as temporary_directory:
            project = make_project(Path(temporary_directory))
            segment_id = project.timeline.segments[0].segment_id
            enable_triplicate(project, [segment_id])

            class Adjustment:
                def __init__(self):
                    self.lower = None
                    self.upper = None

                def set_lower(self, value):
                    self.lower = value

                def set_upper(self, value):
                    self.upper = value

            class Spin:
                def __init__(self):
                    self.adjustment = Adjustment()
                    self.value = None

                def set_sensitive(self, _value):
                    return None

                def get_adjustment(self):
                    return self.adjustment

                def set_value(self, value):
                    self.value = value

            window = SimpleNamespace(
                _export_in_progress=False,
                _source_load_in_progress=False,
                project=project,
                segment_timeline=project.timeline,
                selected_segment_ids=(segment_id,),
                selected_segment_id=segment_id,
                export_button=MagicMock(),
                open_source_button=MagicMock(),
                open_project_button=MagicMock(),
                save_button=MagicMock(),
                reopen_button=MagicMock(),
                timeline_canvas=MagicMock(),
                focus_zoom_spin=Spin(),
                focus_offset_x_spin=Spin(),
                focus_offset_y_spin=Spin(),
                copy_focus_button=MagicMock(),
                clean_focus_button=MagicMock(),
                triplicate_button=MagicMock(),
                timeline_output_label=MagicMock(),
                timeline_zoom_label=MagicMock(),
                _update_selected_clip_label=MagicMock(),
            )
            window.timeline_canvas.get_zoom.return_value = 1.0

            app_timeline_actions.update_segment_controls(window)

            self.assertEqual(
                (
                    window.focus_offset_x_spin.adjustment.lower,
                    window.focus_offset_x_spin.adjustment.upper,
                ),
                (-640.0, 640.0),
            )
            self.assertEqual(
                (
                    window.focus_offset_y_spin.adjustment.lower,
                    window.focus_offset_y_spin.adjustment.upper,
                ),
                (0.0, 0.0),
            )

    def test_transform_values_apply_to_selected_segments_without_timing_changes(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            project = make_project(root)
            project.timeline.split(4.0)
            ids = [segment.segment_id for segment in project.timeline.segments]
            before = [
                (
                    segment.segment_id,
                    segment.start_seconds,
                    segment.end_seconds,
                    segment.timeline_start,
                    segment.timeline_end,
                    segment.color_index,
                )
                for segment in project.timeline.segments
            ]

            transform = apply_visual_transform(
                project,
                ids,
                zoom=2.0,
                offset_x=120.0,
                offset_y=-80.0,
            )

            self.assertEqual(
                [segment.visual_transform for segment in project.timeline.segments],
                [transform, transform],
            )
            self.assertEqual(
                [
                    (
                        segment.segment_id,
                        segment.start_seconds,
                        segment.end_seconds,
                        segment.timeline_start,
                        segment.timeline_end,
                        segment.color_index,
                    )
                    for segment in project.timeline.segments
                ],
                before,
            )

    def test_split_copy_move_delete_and_clean_preserve_or_clone_visual_state(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            project = make_project(root)
            segment_id = project.timeline.segments[0].segment_id
            transform = apply_visual_transform(
                project,
                [segment_id],
                zoom=1.75,
                offset_x=200,
                offset_y=-100,
            )
            enable_triplicate(project, [segment_id])
            original_group = project.timeline.find(segment_id).triplicate
            self.assertIsNotNone(original_group)

            project.timeline.split(5.0)
            first, second = project.timeline.segments
            self.assertEqual(first.visual_transform, transform)
            self.assertEqual(second.visual_transform, transform)
            self.assertIsNot(first.triplicate, second.triplicate)
            self.assertNotEqual(first.triplicate.group_id, second.triplicate.group_id)
            self.assertNotEqual(first.triplicate.group_id, original_group.group_id)

            copied = project.timeline.copy_blocks([first.segment_id])
            pasted = paste_segments_after_selection(project, copied, first.segment_id)
            inserted = pasted[0]
            self.assertEqual(inserted.visual_transform, transform)
            self.assertIsNot(inserted.triplicate, first.triplicate)
            self.assertNotEqual(inserted.triplicate.group_id, first.triplicate.group_id)

            project.timeline.move_block(inserted.segment_id, "left")
            self.assertEqual(project.timeline.find(inserted.segment_id).visual_transform, transform)
            project.timeline.set_deleted(inserted.segment_id, True)
            project.timeline.set_deleted(inserted.segment_id, False)
            self.assertEqual(project.timeline.find(inserted.segment_id).visual_transform, transform)

            clean_visual_modifications(project, [inserted.segment_id])
            cleaned = project.timeline.find(inserted.segment_id)
            self.assertTrue(cleaned.visual_transform.is_default)
            self.assertIsNone(cleaned.triplicate)
            current_first = project.timeline.find(first.segment_id)
            self.assertIsNotNone(current_first.triplicate)
            self.assertEqual(current_first.visual_transform, transform)

    def test_group_shared_transform_and_disable_are_atomic(self):
        with TemporaryDirectory() as temporary_directory:
            project = make_project(Path(temporary_directory))
            project.timeline.split(5.0)
            ids = [segment.segment_id for segment in project.timeline.segments]
            enable_triplicate(project, ids)
            transform = apply_visual_transform(
                project,
                ids,
                zoom=3.0,
                offset_x=400,
                offset_y=200,
            )

            for segment in project.timeline.segments:
                self.assertIsNotNone(segment.triplicate)
                self.assertEqual(segment.triplicate.shared_transform, transform)
                self.assertEqual(
                    {instance.role for instance in segment.triplicate.instances},
                    {"center", "left", "right"},
                )

            disable_triplicate(project, ids)
            self.assertTrue(
                all(segment.triplicate is None for segment in project.timeline.segments)
            )
            self.assertTrue(
                all(segment.visual_transform == transform for segment in project.timeline.segments)
            )

    def test_visual_state_round_trips_and_invalid_group_state_is_rejected(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            project = make_project(root)
            segment_id = project.timeline.segments[0].segment_id
            apply_visual_transform(project, [segment_id], zoom=2.0, offset_x=50, offset_y=-25)
            enable_triplicate(project, [segment_id])
            destination = root / "focused.resolve.json"

            save_project(project, destination)
            restored = load_project(destination)

            self.assertEqual(restored.to_dict(), project.to_dict())
            restored_segment = restored.timeline.segments[0]
            self.assertEqual(restored_segment.visual_transform.zoom, 2.0)
            self.assertEqual(
                {instance.role for instance in restored_segment.triplicate.instances},
                {"center", "left", "right"},
            )

            payload = project.to_dict()
            payload["timeline"]["segments"][0]["triplicate"]["instances"] = [
                {"role": "center"},
                {"role": "left"},
            ]
            with self.assertRaises(ProjectValidationError):
                Project.from_dict(payload)

    def test_copying_visual_transform_does_not_share_mutable_state(self):
        with TemporaryDirectory() as temporary_directory:
            project = make_project(Path(temporary_directory))
            project.timeline.split(5.0)
            first, second = project.timeline.segments
            apply_visual_transform(project, [first.segment_id], zoom=2.0, offset_x=10, offset_y=20)
            copied = copy_visual_transform(project, first.segment_id, [second.segment_id])

            current_second = project.timeline.find(second.segment_id)
            self.assertEqual(copied, current_second.visual_transform)
            self.assertEqual(
                project.timeline.find(first.segment_id).visual_transform,
                current_second.visual_transform,
            )

    def test_render_filters_share_contain_focus_and_triplicate_policy(self):
        timeline = SegmentTimeline(10.0)
        segment = timeline.segments[0].with_visual_transform(
            VisualTransform(zoom=2.0, offset_x=100, offset_y=-50),
        )
        normal = segment_video_filters(
            "[0:v:0]",
            segment,
            CANVAS_WIDTH,
            CANVAS_HEIGHT,
            "[outv]",
            frame_rate="30/1",
        )
        self.assertIn("force_original_aspect_ratio=decrease", normal[0])
        self.assertIn("crop=1920:1080", normal[0])
        self.assertIn("fps=30/1", normal[0])

        triplicate = segment.with_triplicate(TriplicateGroup.create(segment.visual_transform))
        grouped = segment_video_filters(
            "[0:v:0]",
            triplicate,
            CANVAS_WIDTH,
            CANVAS_HEIGHT,
            "[outv]",
        )
        self.assertIn("split=3", grouped[0])
        self.assertIn("hstack=inputs=3", grouped[-1])
        self.assertIn("crop=640:1080", grouped[1])

    def test_triplicate_focus_bounds_reach_canvas_edges_without_aspect_crop(self):
        timeline = SegmentTimeline(10.0)
        segment = timeline.segments[0].with_triplicate(
            TriplicateGroup.create(
                VisualTransform(zoom=2.0, offset_x=960.0, offset_y=540.0),
            ),
        )

        grouped = segment_video_filters(
            "[0:v:0]",
            segment,
            CANVAS_WIDTH,
            CANVAS_HEIGHT,
            "[outv]",
        )

        self.assertIn(
            "scale=1920:1080:force_original_aspect_ratio=decrease",
            grouped[1],
        )
        self.assertIn("scale=3840:2160", grouped[1])
        self.assertIn("+1600", grouped[1])
        self.assertIn("+540", grouped[1])

    def test_preserve_resolution_mode_crops_or_pads_without_downscaling(self):
        timeline = SegmentTimeline(10.0)
        segment = timeline.segments[0]

        filters = segment_video_filters(
            "[0:v:0]",
            segment,
            CANVAS_WIDTH,
            CANVAS_HEIGHT,
            "[outv]",
            preserve_resolution=True,
            content_width=1080,
            content_height=1920,
        )

        self.assertIn("scale=1080:1920", filters[0])
        self.assertIn("crop=1080:1080", filters[0])
        self.assertIn("pad=1920:1080", filters[0])
        self.assertNotIn("force_original_aspect_ratio=decrease", filters[0])

    def test_preserve_resolution_triplicate_crops_each_slot_without_downscaling(self):
        timeline = SegmentTimeline(10.0)
        segment = timeline.segments[0].with_triplicate(
            TriplicateGroup.create(VisualTransform()),
        )

        filters = segment_video_filters(
            "[0:v:0]",
            segment,
            CANVAS_WIDTH,
            CANVAS_HEIGHT,
            "[outv]",
            preserve_resolution=True,
            content_width=1080,
            content_height=1920,
        )

        self.assertIn("scale=1080:1920", filters[1])
        self.assertIn("crop=640:1080", filters[1])
        self.assertNotIn("force_original_aspect_ratio=decrease", filters[1])

    @unittest.skipUnless(
        shutil.which("ffmpeg") and shutil.which("ffprobe"),
        "FFmpeg and ffprobe are required",
    )
    def test_triplicate_export_renders_verified_canvas_and_preserves_source(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = root / "portrait.mp4"
            subprocess.run(
                [
                    "ffmpeg",
                    "-hide_banner",
                    "-loglevel",
                    "error",
                    "-y",
                    "-f",
                    "lavfi",
                    "-i",
                    "testsrc=size=180x320:rate=10",
                    "-t",
                    "0.6",
                    "-c:v",
                    "libx264",
                    "-pix_fmt",
                    "yuv420p",
                    str(source),
                ],
                check=True,
            )
            project = Project.create(source, probe_media(source).metadata())
            segment_id = project.timeline.segments[0].segment_id
            enable_triplicate(project, [segment_id])
            source_bytes = source.read_bytes()

            destination = root / "triplicate.mp4"
            plan = plan_project_export(
                project,
                destination,
                upscale_policy=UpscalePolicy(enhancement_enabled=False),
            )
            execute_export(plan)
            output = probe_media(destination)

            self.assertEqual(plan.route, "fallback")
            self.assertEqual((output.width, output.height), (CANVAS_WIDTH, CANVAS_HEIGHT))
            self.assertAlmostEqual(
                output.duration_seconds,
                project.timeline.edited_duration_seconds,
                delta=0.15,
            )
            self.assertEqual(source.read_bytes(), source_bytes)

    @unittest.skipUnless(
        shutil.which("ffmpeg") and shutil.which("ffprobe"),
        "FFmpeg and ffprobe are required",
    )
    def test_default_zoom_triplicate_offsets_change_generated_media(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = root / "asymmetric.mp4"
            subprocess.run(
                [
                    "ffmpeg",
                    "-hide_banner",
                    "-loglevel",
                    "error",
                    "-y",
                    "-f",
                    "lavfi",
                    "-i",
                    "color=c=black:s=1920x1080:r=10,"
                    "drawbox=x=0:y=0:w=640:h=1080:color=red:t=fill,"
                    "drawbox=x=1280:y=0:w=640:h=1080:color=blue:t=fill",
                    "-t",
                    "0.6",
                    "-c:v",
                    "libx264",
                    "-pix_fmt",
                    "yuv420p",
                    str(source),
                ],
                check=True,
            )
            project = Project.create(source, probe_media(source).metadata())
            segment_id = project.timeline.segments[0].segment_id
            enable_triplicate(project, [segment_id])

            digests = {}
            for offset_x in (-640.0, 0.0, 640.0):
                apply_visual_transform(
                    project,
                    [segment_id],
                    zoom=1.0,
                    offset_x=offset_x,
                    offset_y=0.0,
                )
                destination = root / f"triplicate-{offset_x:g}.mp4"
                plan = plan_project_export(
                    project,
                    destination,
                    upscale_policy=UpscalePolicy(enhancement_enabled=False),
                )
                execute_export(plan)
                output = probe_media(destination)
                self.assertEqual((output.width, output.height), (CANVAS_WIDTH, CANVAS_HEIGHT))
                digest = subprocess.run(
                    [
                        "ffmpeg",
                        "-hide_banner",
                        "-loglevel",
                        "error",
                        "-i",
                        str(destination),
                        "-frames:v",
                        "1",
                        "-f",
                        "framemd5",
                        "-",
                    ],
                    check=True,
                    capture_output=True,
                    text=True,
                ).stdout
                digests[offset_x] = next(
                    line.rsplit(",", 1)[-1]
                    for line in reversed(digest.splitlines())
                    if line and not line.startswith("#")
                )

            self.assertNotEqual(digests[-640.0], digests[0.0])
            self.assertNotEqual(digests[0.0], digests[640.0])
            self.assertNotEqual(digests[-640.0], digests[640.0])

    def test_composed_preview_uses_active_blocks_and_edited_duration(self):
        with TemporaryDirectory() as temporary_directory:
            project = make_project(Path(temporary_directory))
            project.timeline.split(5.0)
            deleted = project.timeline.segments[1]
            project.timeline.set_deleted(deleted.segment_id, True)
            active = project.timeline.active_blocks()
            window = SimpleNamespace(
                backend=None,
                controller=None,
                project=None,
                project_path=None,
                segment_timeline=None,
                timeline_canvas=MagicMock(),
                audio_status_label=MagicMock(),
                _stop_backend=MagicMock(),
                _on_frame=MagicMock(),
                _on_backend_error=MagicMock(),
                _on_backend_end=MagicMock(),
                _update_selected_clip_label=MagicMock(),
                _update_playback_controls=MagicMock(),
                _update_segment_controls=MagicMock(),
            )

            with (
                patch("resolve_editor.app_project.ensure_project_audio_analysis") as analyze,
                patch("resolve_editor.app_project.FfmpegComposedPlaybackBackend") as backend_type,
            ):
                analyze.return_value = {
                    project.source.source_id: {"status": "not-applicable", "gain_db": 0.0},
                }
                backend_type.return_value = MagicMock()
                attach_project(window, project, None)

            call_args = backend_type.call_args.args
            self.assertEqual(call_args[1], active)
            self.assertEqual(call_args[5], project.timeline.edited_duration_seconds)
            self.assertEqual(
                window.controller.snapshot().duration_seconds,
                project.timeline.edited_duration_seconds,
            )

    def test_refresh_after_deletion_maps_saved_timeline_playhead_to_output_time(self):
        with TemporaryDirectory() as temporary_directory:
            project = make_project(Path(temporary_directory))
            project.timeline.split(3.0)
            project.timeline.split(7.0)
            project.set_playhead(8.0)
            direct_backend = MagicMock()
            composed_backend = MagicMock()
            window = SimpleNamespace(
                backend=None,
                controller=None,
                project=None,
                project_path=None,
                segment_timeline=None,
                source_frame_rate=10.0,
                timeline_canvas=MagicMock(),
                audio_status_label=MagicMock(),
                _stop_backend=lambda: stop_backend(window),
                _on_frame=MagicMock(),
                _on_backend_error=MagicMock(),
                _on_backend_end=MagicMock(),
                _on_backend_warning=MagicMock(),
                _update_selected_clip_label=MagicMock(),
                _update_playback_controls=MagicMock(),
                _update_segment_controls=MagicMock(),
            )

            with (
                patch("resolve_editor.app_project.ensure_project_audio_analysis") as analyze,
                patch("resolve_editor.app_project.FfmpegPlaybackBackend") as direct_type,
                patch("resolve_editor.app_project.FfmpegComposedPlaybackBackend") as composed_type,
            ):
                analyze.return_value = {
                    project.source.source_id: {"status": "not-applicable", "gain_db": 0.0},
                }
                direct_type.return_value = direct_backend
                composed_type.return_value = composed_backend
                attach_project(window, project, None)
                project.timeline.set_deleted(project.timeline.segments[1].segment_id, True)

                refresh_playback_backend(window)

            self.assertAlmostEqual(window.controller.snapshot().position_seconds, 4.0)
            self.assertEqual(window.controller.snapshot().duration_seconds, 6.0)

    def test_cli_focus_and_triplicate_operations_are_persisted(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            project_path = root / "edit.resolve.json"
            project = make_project(root)
            segment_id = project.timeline.segments[0].segment_id
            save_project(project, project_path)

            result, stdout, stderr = run_cli(
                "focus",
                str(project_path),
                "--segment",
                segment_id,
                "--zoom",
                "2",
                "--offset-x",
                "100",
                "--offset-y",
                "-50",
            )
            self.assertEqual(result, 0)
            self.assertEqual(stderr.getvalue(), "")
            focused = json.loads(stdout.getvalue())
            self.assertEqual(
                focused["project"]["timeline"]["segments"][0]["visual_transform"]["zoom"],
                2.0,
            )

            result, stdout, stderr = run_cli(
                "triplicate-enable",
                str(project_path),
                "--segment",
                segment_id,
            )
            self.assertEqual(result, 0)
            self.assertEqual(stderr.getvalue(), "")
            enabled = json.loads(stdout.getvalue())
            self.assertEqual(
                {
                    item["role"]
                    for item in enabled["project"]["timeline"]["segments"][0]["triplicate"][
                        "instances"
                    ]
                },
                {"center", "left", "right"},
            )

            result, stdout, stderr = run_cli(
                "clean-focus",
                str(project_path),
                "--segment",
                segment_id,
            )
            self.assertEqual(result, 0)
            self.assertEqual(stderr.getvalue(), "")
            cleaned = json.loads(stdout.getvalue())
            self.assertIsNone(cleaned["project"]["timeline"]["segments"][0]["triplicate"])
            self.assertEqual(
                cleaned["project"]["timeline"]["segments"][0]["visual_transform"]["zoom"],
                1.0,
            )
