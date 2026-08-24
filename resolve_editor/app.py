from __future__ import annotations

import threading
from collections.abc import Sequence
from pathlib import Path

from .app_export import (
    finish_export,
    on_export_clicked,
    on_export_dialog_done,
    reset_export_progress,
    start_export,
    update_export_progress,
)
from .app_helpers import (
    KEY_BINDINGS,
    KEYCODE_SPACE,
    KEYVAL_DELETE,
    KEYVAL_KP_DELETE,
    KEYVAL_KP_SPACE,
    KEYVAL_LEFT,
    KEYVAL_RIGHT,
    MAX_SOURCES_PER_PROJECT,
    TIMELINE_SCROLL_PIXELS,
    TIMELINE_SCROLL_STEP_SECONDS,
    _metadata_float,
    create_play_pause_key_controller,
    format_export_progress_label,
    format_key_bindings,
    format_output_duration_label,
    format_segment_label,
    frame_step_direction,
    frame_step_position,
    is_delete_key,
    is_fit_zoom_key,
    is_frame_step_key,
    is_play_pause_key,
    is_split_key,
    playback_action_label,
    segment_action_state,
    timeline_scroll_mode,
    timeline_scroll_position,
    toggle_segment_deleted_state,
    validate_source_selection,
)
from .app_playback import (
    deliver_latest_frame,
    end_smoke_test,
    finish_smoke_test,
    handle_backend_end,
    handle_backend_error,
    handle_backend_warning,
    on_backend_end,
    on_backend_error,
    on_backend_warning,
    on_close_request,
    on_frame,
    on_key_pressed,
    on_play_clicked,
    on_timeline_scroll,
    on_timeline_view_seek,
    poll_playback,
    request_timeline_preview,
    seek_timeline,
    start_smoke_test,
    step_playhead,
    stop_backend,
    update_playback_controls,
)
from .app_project import (
    attach_project,
    load_project_path,
    load_source,
    refresh_playback_backend,
    refresh_timeline,
    save_to,
)
from .app_timeline_actions import (
    center_timeline_on_playhead,
    copy_selected_segments,
    fit_timeline_zoom,
    move_selected_segments,
    on_apply_focus_clicked,
    on_clean_visual_clicked,
    on_copy_focus_clicked,
    on_delete_segment_clicked,
    on_focus_control_changed,
    on_split_clicked,
    on_timeline_segment_selected,
    on_timeline_selection_changed,
    on_timeline_viewport_changed,
    on_triplicate_clicked,
    paste_selected_segments,
    update_segment_controls,
    update_selected_clip_label,
    zoom_timeline,
)
from .app_ui import build_editor_ui, build_key_bindings_window
from .export import ExportProgress
from .ffmpeg_playback import (
    FfmpegPlaybackBackend,
    VideoFrame,
)
from .model import (
    Project,
    Segment,
    SegmentTimeline,
)
from .playback import PlaybackController

__all__ = [
    "KEY_BINDINGS",
    "KEYCODE_SPACE",
    "KEYVAL_DELETE",
    "KEYVAL_KP_DELETE",
    "KEYVAL_KP_SPACE",
    "KEYVAL_LEFT",
    "KEYVAL_RIGHT",
    "MAX_SOURCES_PER_PROJECT",
    "TIMELINE_SCROLL_PIXELS",
    "TIMELINE_SCROLL_STEP_SECONDS",
    "_metadata_float",
    "create_play_pause_key_controller",
    "format_export_progress_label",
    "format_key_bindings",
    "format_output_duration_label",
    "format_segment_label",
    "frame_step_direction",
    "frame_step_position",
    "is_delete_key",
    "is_fit_zoom_key",
    "is_frame_step_key",
    "is_play_pause_key",
    "is_split_key",
    "playback_action_label",
    "run_gui",
    "segment_action_state",
    "timeline_scroll_mode",
    "timeline_scroll_position",
    "toggle_segment_deleted_state",
    "validate_source_selection",
]


def run_gui(
    source_path: Path | None = None,
    project_path: Path | None = None,
    smoke_test: bool = False,
    smoke_project_path: Path | None = None,
) -> int:
    try:
        import gi

        gi.require_version("Gdk", "4.0")
        gi.require_version("Gtk", "4.0")
        from gi.repository import Gdk, GLib, Gtk
    except (ImportError, ValueError) as error:
        raise RuntimeError("GTK 4 and PyGObject are required for resolve-editor") from error

    class EditorWindow(Gtk.ApplicationWindow):
        def __init__(
            self,
            application,
            initial_source: Path | None,
            initial_project: Path | None,
        ) -> None:
            super().__init__(application=application)
            self.set_title("Resolve Editor")
            self.set_default_size(1100, 720)
            self.project: Project | None = None
            self.project_path: Path | None = None
            self.backend: FfmpegPlaybackBackend | None = None
            self.controller: PlaybackController | None = None
            self._frame_lock = threading.Lock()
            self._latest_frame: VideoFrame | None = None
            self._frame_delivery_scheduled = False
            self.segment_timeline: SegmentTimeline | None = None
            self.selected_segment_id: str | None = None
            self.selected_segment_ids: tuple[str, ...] = ()
            self._segment_clipboard: tuple[Segment, ...] = ()
            self.source_frame_rate = 30.0
            self._export_in_progress = False
            self._updating_focus_controls = False
            self._playback_generation = 0
            self._smoke_test = smoke_test
            self._smoke_project_path = smoke_project_path
            self._build_ui()
            self.set_focusable(True)
            key_controller = create_play_pause_key_controller(
                Gtk,
                self._on_key_pressed,
            )
            self.add_controller(key_controller)
            self.connect("close-request", self._on_close_request)
            GLib.timeout_add(100, self._poll_playback)
            if initial_project is not None:
                GLib.idle_add(self._load_project_path, initial_project)
            elif initial_source is not None:
                GLib.idle_add(self._load_source, initial_source)
            if self._smoke_test:
                GLib.idle_add(self._start_smoke_test)

        def _build_ui(self) -> None:
            build_editor_ui(self, Gtk, Gdk)

        def _build_key_bindings_window(self, Gtk) -> None:
            build_key_bindings_window(self, Gtk)

        def _on_key_bindings_clicked(self, _button) -> None:
            window = self.key_bindings_window
            if window is None:
                self._build_key_bindings_window(Gtk)
                window = self.key_bindings_window
            if window is None:
                raise RuntimeError("Key bindings window could not be created")
            window.present()

        def _on_key_bindings_window_close(self, _window) -> bool:
            self.key_bindings_window = None
            return False

        def _set_status(self, message: str) -> None:
            self.status_label.set_text(message)

        def _show_error(self, message: str) -> None:
            self._set_status(f"Error: {message}")

        def _on_open_source_clicked(self, _button) -> None:
            dialog = Gtk.FileDialog.new()
            dialog.set_title("Select source video(s)")
            dialog.open_multiple(self, None, self._on_source_dialog_done, None)

        def _on_source_dialog_done(self, dialog, result, _data) -> None:
            try:
                selected_files = dialog.open_multiple_finish(result)
            except GLib.Error as error:
                if "dismiss" not in str(error).lower():
                    self._show_error(str(error))
                return
            if selected_files is None:
                return
            selected_paths: list[Path] = []
            for index in range(selected_files.get_n_items()):
                selected_file = selected_files.get_item(index)
                if selected_file is None:
                    self._show_error("Selected sources must be local files")
                    return
                selected_path = selected_file.get_path()
                if selected_path is None:
                    self._show_error("Selected sources must be local files")
                    return
                selected_paths.append(Path(selected_path))
            try:
                selected = validate_source_selection(
                    selected_paths,
                    max_sources=MAX_SOURCES_PER_PROJECT,
                )
            except ValueError as error:
                self._show_error(str(error))
                return
            if selected:
                self._load_source(selected)

        def _on_open_project_clicked(self, _button) -> None:
            dialog = Gtk.FileDialog.new()
            dialog.set_title("Open editor project")
            dialog.open(self, None, self._on_project_dialog_done, None)

        def _on_project_dialog_done(self, dialog, result, _data) -> None:
            try:
                selected = dialog.open_finish(result)
            except GLib.Error as error:
                if "dismiss" not in str(error).lower():
                    self._show_error(str(error))
                return
            if selected is not None and selected.get_path() is not None:
                self._load_project_path(Path(selected.get_path()))

        def _on_save_clicked(self, _button) -> None:
            if self.project is None:
                self._show_error("Open a source or project before saving")
                return
            if self.project_path is not None:
                self._save_to(self.project_path)
                return
            dialog = Gtk.FileDialog.new()
            dialog.set_title("Save editor project")
            dialog.set_initial_name(f"{Path(self.project.source.path).stem}.resolve.json")
            dialog.save(self, None, self._on_save_dialog_done, None)

        def _on_save_dialog_done(self, dialog, result, _data) -> None:
            try:
                selected = dialog.save_finish(result)
            except GLib.Error as error:
                if "dismiss" not in str(error).lower():
                    self._show_error(str(error))
                return
            if selected is not None and selected.get_path() is not None:
                self._save_to(Path(selected.get_path()))

        def _on_export_clicked(self, _button) -> None:
            on_export_clicked(self, Gtk)

        def _on_export_dialog_done(self, dialog, result, _data) -> None:
            on_export_dialog_done(self, dialog, result, GLib)

        def _reset_export_progress(self) -> None:
            reset_export_progress(self)

        def _update_export_progress(self, progress: ExportProgress) -> bool:
            return update_export_progress(self, progress)

        def _start_export(self, destination: Path) -> None:
            start_export(self, destination, GLib)

        def _finish_export(
            self,
            output: Path | None,
            message: str,
        ) -> bool:
            return finish_export(self, output, message)

        def _save_to(self, path: Path) -> None:
            save_to(self, path)

        def _on_reopen_clicked(self, _button) -> None:
            if self.project_path is None:
                self._show_error("No project has been saved yet")
                return
            self._load_project_path(self.project_path)

        def _load_source(self, paths: Path | Sequence[Path]) -> bool:
            return load_source(self, paths)

        def _load_project_path(self, path: Path) -> bool:
            return load_project_path(self, path)

        def _attach_project(
            self,
            project: Project,
            project_path: Path | None,
        ) -> None:
            attach_project(self, project, project_path)

        def _refresh_playback_backend(self) -> None:
            refresh_playback_backend(self)

        def _refresh_timeline(self, selected_segment_id: str | None = None) -> None:
            refresh_timeline(self, selected_segment_id)

        def _on_timeline_segment_selected(self, segment_id: str) -> None:
            on_timeline_segment_selected(self, segment_id)

        def _on_timeline_selection_changed(self, segment_ids: tuple[str, ...]) -> None:
            on_timeline_selection_changed(self, segment_ids)

        def _update_selected_clip_label(self) -> None:
            update_selected_clip_label(self)

        def _on_timeline_viewport_changed(self, adjustment, _param) -> None:
            on_timeline_viewport_changed(self, adjustment, _param)

        def _zoom_timeline(self, direction: int) -> None:
            zoom_timeline(self, direction)

        def _fit_timeline_zoom(self) -> None:
            fit_timeline_zoom(self)

        def _center_timeline_on_playhead(self) -> None:
            center_timeline_on_playhead(self)

        def _update_segment_controls(self) -> None:
            update_segment_controls(self)

        def _on_split_clicked(self, _button) -> None:
            on_split_clicked(self, _button)

        def _on_apply_focus_clicked(self, _button) -> None:
            on_apply_focus_clicked(self, _button)

        def _on_focus_control_changed(self, _control) -> None:
            on_focus_control_changed(self, _control)

        def _on_clean_visual_clicked(self, _button) -> None:
            on_clean_visual_clicked(self, _button)

        def _on_copy_focus_clicked(self, _button) -> None:
            on_copy_focus_clicked(self, _button)

        def _on_triplicate_clicked(self, _button) -> None:
            on_triplicate_clicked(self, _button)

        def _on_delete_segment_clicked(self, _button) -> None:
            on_delete_segment_clicked(self, _button)

        def _move_selected_segments(self, direction: str) -> None:
            move_selected_segments(self, direction)

        def _copy_selected_segments(self) -> None:
            copy_selected_segments(self)

        def _paste_selected_segments(self) -> None:
            paste_selected_segments(self)

        def _stop_backend(self) -> None:
            stop_backend(self)

        def _on_play_clicked(self, _button) -> None:
            on_play_clicked(self, _button)

        def _on_key_pressed(
            self,
            _controller,
            keyval: int,
            keycode: int,
            _state,
        ) -> bool:
            return on_key_pressed(self, _controller, keyval, keycode, _state, Gdk)

        def _step_playhead(self, direction: int) -> None:
            step_playhead(self, direction)

        def _seek_timeline(self, position_seconds: float) -> bool:
            return seek_timeline(self, position_seconds)

        def _request_timeline_preview(self, position_seconds: float) -> None:
            request_timeline_preview(self, position_seconds)

        def _on_timeline_scroll(self, _controller, _delta_x, delta_y) -> bool:
            return on_timeline_scroll(
                self,
                _controller,
                _delta_x,
                delta_y,
                Gdk,
            )

        def _on_timeline_view_seek(self, position_seconds: float) -> None:
            on_timeline_view_seek(self, position_seconds)

        def _poll_playback(self) -> bool:
            return poll_playback(self)

        def _update_playback_controls(self) -> None:
            update_playback_controls(self)

        def _on_frame(self, frame: VideoFrame) -> None:
            on_frame(self, frame, GLib)

        def _deliver_latest_frame(self) -> bool:
            return deliver_latest_frame(self, Gdk, GLib)

        def _on_backend_error(self, message: str, generation: int | None = None) -> None:
            on_backend_error(self, message, GLib, generation)

        def _handle_backend_warning(
            self,
            message: str,
            generation: int | None = None,
        ) -> bool:
            return handle_backend_warning(self, message, generation)

        def _on_backend_warning(self, message: str, generation: int | None = None) -> None:
            on_backend_warning(self, message, GLib, generation)

        def _handle_backend_error(
            self,
            message: str,
            generation: int | None = None,
        ) -> bool:
            return handle_backend_error(self, message, generation)

        def _on_backend_end(self, generation: int | None = None) -> None:
            on_backend_end(self, GLib, generation)

        def _handle_backend_end(self, generation: int | None = None) -> bool:
            return handle_backend_end(self, generation)

        def _on_close_request(self, _window) -> bool:
            return on_close_request(self, _window)

        def _start_smoke_test(self) -> bool:
            return start_smoke_test(self, GLib)

        def _finish_smoke_test(self) -> bool:
            return finish_smoke_test(self, GLib)

        def _end_smoke_test(self) -> bool:
            return end_smoke_test(self)

    application = Gtk.Application(
        application_id="io.github.resolve_media.editor",
    )

    def on_activate(app) -> None:
        window = EditorWindow(app, source_path, project_path)
        window.present()
        window.grab_focus()

    application.connect("activate", on_activate)
    return int(application.run([]))
