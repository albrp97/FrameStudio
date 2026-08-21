from __future__ import annotations

import threading
from collections.abc import Mapping, Sequence
from fractions import Fraction
from pathlib import Path

from .export import (
    ExportExecutionError,
    ExportPlanningError,
    ExportProgress,
    execute_export,
)
from .ffmpeg_playback import (
    FfmpegPlaybackBackend,
    PlaybackBackendError,
    VideoFrame,
)
from .media import MediaProbeError
from .model import (
    Project,
    ProjectValidationError,
    Segment,
    SegmentTimeline,
)
from .operations import (
    create_project_from_source,
    export_destination_conflicts_with_project,
    plan_project_export,
    split_segment,
    toggle_segment_deleted,
)
from .persistence import ProjectPersistenceError, load_project, save_project
from .playback import PlaybackController, PlaybackState
from .timeline import create_timeline_canvas, timeline_zoom_label
from .ui import format_duration

MAX_SOURCES_PER_PROJECT = 1
TIMELINE_SCROLL_STEP_SECONDS = 1.0
TIMELINE_SCROLL_PIXELS = 140.0
KEYVAL_LEFT = 0xFF51
KEYVAL_RIGHT = 0xFF53
KEYVAL_DELETE = 0xFFFF
KEYVAL_KP_DELETE = 0xFF9F


def validate_source_selection(
    paths: Sequence[Path],
    max_sources: int = MAX_SOURCES_PER_PROJECT,
) -> tuple[Path, ...]:
    if max_sources < 1:
        raise ValueError("The project source limit must be at least one")
    selected = tuple(Path(path) for path in paths)
    if len(selected) > max_sources:
        if max_sources == 1:
            raise ValueError(
                "This editor phase supports one source video per project; "
                "multi-source timelines are planned for a later phase"
            )
        raise ValueError(
            f"This editor phase supports at most {max_sources} source videos per project"
        )
    return selected


def timeline_scroll_position(
    position_seconds: float,
    scroll_delta: float,
    duration_seconds: float,
    step_seconds: float = TIMELINE_SCROLL_STEP_SECONDS,
) -> float:
    if duration_seconds <= 0:
        raise ValueError("Timeline duration must be greater than zero")
    if step_seconds <= 0:
        raise ValueError("Timeline scroll step must be greater than zero")
    target = float(position_seconds) - float(scroll_delta) * float(step_seconds)
    return max(0.0, min(float(duration_seconds), target))


def is_play_pause_key(keyval: int) -> bool:
    return keyval == ord(" ")


def is_split_key(keyval: int) -> bool:
    return keyval in (ord("b"), ord("B"))


def is_delete_key(keyval: int) -> bool:
    return keyval in (KEYVAL_DELETE, KEYVAL_KP_DELETE)


def is_frame_step_key(keyval: int) -> bool:
    return keyval in (KEYVAL_LEFT, KEYVAL_RIGHT)


def frame_step_direction(keyval: int) -> int | None:
    if keyval == KEYVAL_LEFT:
        return -1
    if keyval == KEYVAL_RIGHT:
        return 1
    return None


def frame_step_position(
    position_seconds: float,
    direction: int,
    frame_rate: float,
    duration_seconds: float,
) -> float:
    if direction not in (-1, 1):
        raise ValueError("Frame step direction must be -1 or 1")
    if frame_rate <= 0:
        raise ValueError("Frame rate must be greater than zero")
    if duration_seconds <= 0:
        raise ValueError("Timeline duration must be greater than zero")
    target = float(position_seconds) + direction / float(frame_rate)
    return max(0.0, min(float(duration_seconds), target))


def format_output_duration_label(duration_seconds: float) -> str:
    return f"Final output: {format_duration(duration_seconds)}"


def format_export_progress_label(progress: ExportProgress) -> str:
    fps = f"{progress.fps:.1f} fps" if progress.fps is not None else "-- fps"
    eta = format_duration(progress.eta_seconds) if progress.eta_seconds is not None else "--:--"
    return (
        f"{progress.stage.title()} | {progress.percent:.1f}% | "
        f"frame {progress.frame}/{progress.total_frames} | {fps} | "
        f"elapsed {format_duration(progress.elapsed_seconds)} | ETA {eta}"
    )


def is_fit_zoom_key(
    keyval: int,
    modifier_state: int,
    control_mask: int,
) -> bool:
    return keyval == ord("0") and bool(int(modifier_state) & int(control_mask))


def timeline_scroll_mode(
    delta_x: float,
    delta_y: float,
    modifier_state: int,
    control_mask: int,
    alternate_mask: int,
    shift_mask: int,
) -> str:
    state = int(modifier_state)
    has_delta = abs(delta_x) > 0.01 or abs(delta_y) > 0.01
    if has_delta and state & int(control_mask):
        return "zoom"
    if abs(delta_x) > 0.01 or state & (int(alternate_mask) | int(shift_mask)):
        return "viewport"
    if abs(delta_y) > 0.01:
        return "playhead"
    return "none"


def toggle_segment_deleted_state(
    timeline: SegmentTimeline,
    segment_id: str,
) -> bool:
    try:
        return toggle_segment_deleted(timeline, segment_id)
    except ProjectValidationError as error:
        raise ProjectValidationError("Selected clip was not found") from error


def create_play_pause_key_controller(gtk_module, callback):
    controller = gtk_module.EventControllerKey()
    controller.set_propagation_phase(gtk_module.PropagationPhase.CAPTURE)
    controller.connect("key-pressed", callback)
    return controller


def format_segment_label(index: int, segment: Segment) -> str:
    state = "Deleted" if segment.deleted else "Active"
    return (
        f"Segment {index + 1}: "
        f"{format_duration(segment.start_seconds)} - "
        f"{format_duration(segment.end_seconds)} ({state})"
    )


def segment_action_state(
    timeline: SegmentTimeline | None,
    selected_segment_id: str | None,
) -> tuple[bool, bool]:
    if timeline is None or selected_segment_id is None:
        return False, False
    for segment in timeline.segment_items:
        if segment.segment_id == selected_segment_id:
            return not segment.deleted, segment.deleted
    return False, False


def _metadata_int(metadata: Mapping[str, object], key: str) -> int:
    value = metadata.get(key)
    if value is None or isinstance(value, bool):
        raise ValueError(f"Source metadata {key} is invalid")
    if not isinstance(value, (int, float, str)):
        raise ValueError(f"Source metadata {key} is invalid")
    try:
        parsed = int(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"Source metadata {key} is invalid") from error
    if parsed <= 0:
        raise ValueError(f"Source metadata {key} is invalid")
    return parsed


def _metadata_float(metadata: Mapping[str, object], key: str) -> float:
    value = metadata.get(key)
    if value is None or isinstance(value, bool):
        raise ValueError(f"Source metadata {key} is invalid")
    if not isinstance(value, (int, float, str)):
        raise ValueError(f"Source metadata {key} is invalid")
    try:
        parsed = float(Fraction(value)) if isinstance(value, str) else float(value)
    except (TypeError, ValueError, ZeroDivisionError) as error:
        raise ValueError(f"Source metadata {key} is invalid") from error
    if parsed <= 0:
        raise ValueError(f"Source metadata {key} is invalid")
    return parsed


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
            self.source_frame_rate = 30.0
            self._export_in_progress = False
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
            header = Gtk.HeaderBar()
            self.set_titlebar(header)

            open_source = Gtk.Button(label="Select video(s)")
            open_source.connect("clicked", self._on_open_source_clicked)
            header.pack_start(open_source)

            open_project = Gtk.Button(label="Open project")
            open_project.connect("clicked", self._on_open_project_clicked)
            header.pack_start(open_project)

            export = Gtk.Button(label="Export video")
            export.connect("clicked", self._on_export_clicked)
            export.set_sensitive(False)
            header.pack_end(export)
            self.export_button = export

            save = Gtk.Button(label="Save project")
            save.connect("clicked", self._on_save_clicked)
            header.pack_end(save)

            reopen = Gtk.Button(label="Reopen project")
            reopen.connect("clicked", self._on_reopen_clicked)
            header.pack_end(reopen)

            root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
            root.set_margin_top(12)
            root.set_margin_bottom(12)
            root.set_margin_start(12)
            root.set_margin_end(12)
            self.set_child(root)

            self.preview = Gtk.Picture()
            self.preview.set_hexpand(True)
            self.preview.set_vexpand(True)
            self.preview.set_content_fit(Gtk.ContentFit.CONTAIN)
            preview_frame = Gtk.Frame()
            preview_frame.set_child(self.preview)
            root.append(preview_frame)

            controls = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            root.append(controls)

            self.position_label = Gtk.Label(label="00:00")
            self.position_label.set_tooltip_text("Current source position")
            controls.append(self.position_label)

            timeline_frame = Gtk.Frame()
            timeline_frame.set_label("Timeline / clips")
            timeline_layout = Gtk.Box(
                orientation=Gtk.Orientation.VERTICAL,
                spacing=6,
            )
            timeline_toolbar = Gtk.Box(
                orientation=Gtk.Orientation.HORIZONTAL,
                spacing=6,
            )
            timeline_toolbar.append(Gtk.Label(label="Zoom", xalign=0.0))

            self.timeline_zoom_label = Gtk.Label(label="100%")
            self.timeline_zoom_label.set_width_chars(6)
            timeline_toolbar.append(self.timeline_zoom_label)

            self.timeline_output_label = Gtk.Label(label="Final output: 00:00")
            self.timeline_output_label.set_tooltip_text(
                "Duration of included clips in the final export"
            )
            timeline_toolbar.append(self.timeline_output_label)

            self.timeline_shortcuts_label = Gtk.Label(
                label=(
                    "Space: play/pause | B: split | Del: toggle delete | "
                    "Left/Right: frame | Ctrl+wheel: zoom | "
                    "Alt/Shift/horizontal wheel: scroll"
                )
            )
            self.timeline_shortcuts_label.set_xalign(1.0)
            self.timeline_shortcuts_label.set_hexpand(True)
            timeline_toolbar.append(self.timeline_shortcuts_label)
            timeline_layout.append(timeline_toolbar)

            TimelineCanvas = create_timeline_canvas(Gtk)
            self.timeline_canvas = TimelineCanvas(
                on_seek=self._on_timeline_view_seek,
                on_segment_selected=self._on_timeline_segment_selected,
            )
            self.timeline_canvas.set_tooltip_text(
                "Click/drag to seek; normal wheel seeks; Ctrl+wheel zooms; "
                "Alt/Shift/horizontal wheel scrolls"
            )
            timeline_scroll = Gtk.EventControllerScroll.new(
                Gtk.EventControllerScrollFlags.BOTH_AXES
            )
            timeline_scroll.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
            timeline_scroll.connect("scroll", self._on_timeline_scroll)
            self.timeline_canvas.add_controller(timeline_scroll)

            timeline_viewport = Gtk.ScrolledWindow()
            timeline_viewport.set_policy(
                Gtk.PolicyType.AUTOMATIC,
                Gtk.PolicyType.NEVER,
            )
            timeline_viewport.set_min_content_height(132)
            timeline_viewport.set_child(self.timeline_canvas)
            timeline_layout.append(timeline_viewport)
            self.timeline_viewport = timeline_viewport
            adjustment = timeline_viewport.get_hadjustment()
            adjustment.connect(
                "notify::page-size",
                self._on_timeline_viewport_changed,
            )
            adjustment.connect(
                "notify::upper",
                self._on_timeline_viewport_changed,
            )
            self._on_timeline_viewport_changed(adjustment, None)

            timeline_selection = Gtk.Label(label="No clip selected")
            timeline_selection.set_xalign(0.0)
            timeline_selection.set_wrap(True)
            timeline_layout.append(timeline_selection)
            self.timeline_selection_label = timeline_selection

            timeline_frame.set_child(timeline_layout)
            root.append(timeline_frame)

            export_progress_panel = Gtk.Box(
                orientation=Gtk.Orientation.VERTICAL,
                spacing=4,
            )
            export_progress_bar = Gtk.ProgressBar()
            export_progress_bar.set_show_text(True)
            export_progress_bar.set_text("0.0%")
            export_progress_panel.append(export_progress_bar)
            export_progress_label = Gtk.Label(label="")
            export_progress_label.set_xalign(0.0)
            export_progress_label.set_wrap(True)
            export_progress_panel.append(export_progress_label)
            export_progress_panel.set_visible(False)
            root.append(export_progress_panel)
            self.export_progress_panel = export_progress_panel
            self.export_progress_bar = export_progress_bar
            self.export_progress_label = export_progress_label

            self.status_label = Gtk.Label(label="Select source video(s) or open a project file")
            self.status_label.set_xalign(0.0)
            self.status_label.set_wrap(True)
            root.append(self.status_label)

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
                selected = validate_source_selection(selected_paths)
            except ValueError as error:
                self._show_error(str(error))
                return
            if selected:
                self._load_source(selected[0])

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
            if self.project is None or self.segment_timeline is None:
                self._show_error("Open a source before exporting")
                return
            if self._export_in_progress:
                return
            dialog = Gtk.FileDialog.new()
            dialog.set_title("Export edited video")
            dialog.set_initial_name(f"{Path(self.project.source.path).stem}-edited.mp4")
            dialog.save(self, None, self._on_export_dialog_done, None)

        def _on_export_dialog_done(self, dialog, result, _data) -> None:
            try:
                selected = dialog.save_finish(result)
            except GLib.Error as error:
                if "dismiss" not in str(error).lower():
                    self._show_error(str(error))
                return
            if selected is not None and selected.get_path() is not None:
                self._start_export(Path(selected.get_path()))

        def _reset_export_progress(self) -> None:
            self.export_progress_panel.set_visible(True)
            self.export_progress_bar.set_fraction(0.0)
            self.export_progress_bar.set_text("0.0%")
            self.export_progress_label.set_text("Preparing export...")

        def _update_export_progress(self, progress: ExportProgress) -> bool:
            self.export_progress_bar.set_fraction(max(0.0, min(1.0, progress.percent / 100.0)))
            self.export_progress_bar.set_text(f"{progress.percent:.1f}%")
            self.export_progress_label.set_text(format_export_progress_label(progress))
            return False

        def _start_export(self, destination: Path) -> None:
            if self.project is None or self.segment_timeline is None:
                self._show_error("Open a source before exporting")
                return
            if export_destination_conflicts_with_project(
                self.project_path,
                destination,
            ):
                self._show_error("Export destination must differ from the project file")
                return
            project = self.project
            self._export_in_progress = True
            self._update_segment_controls()
            self._reset_export_progress()
            self._set_status("Planning and exporting edited video...")

            def export_worker() -> None:
                def report_progress(progress: ExportProgress) -> None:
                    GLib.idle_add(self._update_export_progress, progress)

                try:
                    plan = plan_project_export(project, destination)
                    output = execute_export(
                        plan,
                        progress_callback=report_progress,
                    )
                except (
                    ExportExecutionError,
                    ExportPlanningError,
                    MediaProbeError,
                ) as error:
                    GLib.idle_add(
                        self._finish_export,
                        None,
                        str(error),
                    )
                    return
                GLib.idle_add(
                    self._finish_export,
                    output,
                    f"Exported {output.name} using {plan.route}: {plan.reason}",
                )

            threading.Thread(
                target=export_worker,
                name="resolve-editor-export",
                daemon=True,
            ).start()

        def _finish_export(
            self,
            output: Path | None,
            message: str,
        ) -> bool:
            self._export_in_progress = False
            self._update_segment_controls()
            if output is None:
                self.export_progress_label.set_text(f"Export failed: {message}")
                self._show_error(message)
            else:
                self._set_status(message)
            return False

        def _save_to(self, path: Path) -> None:
            if self.project is None:
                return
            if self.controller is not None:
                self.project.set_playhead(self.controller.snapshot().position_seconds)
            try:
                destination = save_project(self.project, path)
            except ProjectPersistenceError as error:
                self._show_error(str(error))
                return
            self.project_path = destination
            self._set_status(f"Saved editor project: {destination.name}")

        def _on_reopen_clicked(self, _button) -> None:
            if self.project_path is None:
                self._show_error("No project has been saved yet")
                return
            self._load_project_path(self.project_path)

        def _load_source(self, path: Path) -> bool:
            try:
                project = create_project_from_source(path)
            except (MediaProbeError, ProjectValidationError) as error:
                self._show_error(str(error))
                return False
            self._attach_project(project, None)
            self._set_status(f"Loaded source video: {path.name} (project not saved)")
            return False

        def _load_project_path(self, path: Path) -> bool:
            try:
                project = load_project(path)
            except ProjectPersistenceError as error:
                self._show_error(str(error))
                return False
            source_status = project.source.status()
            if not source_status.available:
                self._show_error(source_status.reason or "Source is unavailable")
                return False
            if source_status.changed:
                self._show_error(source_status.reason or "Source has changed")
                return False
            try:
                self._attach_project(project, path)
            except (MediaProbeError, ProjectValidationError, ValueError) as error:
                self._show_error(str(error))
                return False
            self._set_status(f"Reopened editor project: {path.name}")
            return False

        def _attach_project(
            self,
            project: Project,
            project_path: Path | None,
        ) -> None:
            self._stop_backend()
            metadata = project.source.metadata
            width = _metadata_int(metadata, "width")
            height = _metadata_int(metadata, "height")
            frame_rate = _metadata_float(metadata, "frame_rate")
            self.project = project
            self.project_path = project_path
            self.source_frame_rate = frame_rate
            self.segment_timeline = project.segment_timeline
            if self.segment_timeline is None:
                raise ProjectValidationError("Project segment timeline is required")
            segments = self.segment_timeline.segment_items
            self.selected_segment_id = segments[0].segment_id
            self.timeline_canvas.set_timeline(
                self.segment_timeline,
                self.selected_segment_id,
            )
            self.timeline_canvas.set_sensitive(True)
            self.backend = FfmpegPlaybackBackend(
                Path(project.source.path),
                width,
                height,
                frame_rate,
                project.duration_seconds,
                self._on_frame,
                self._on_backend_error,
                self._on_backend_end,
            )
            self.controller = PlaybackController(
                self.backend,
                project.duration_seconds,
                project.playhead_seconds,
            )
            self.position_label.set_text(format_duration(project.playhead_seconds))
            self.timeline_canvas.set_playhead(project.playhead_seconds)
            self._update_selected_clip_label()
            if not self.controller.seek(project.playhead_seconds):
                raise MediaProbeError(
                    self.controller.snapshot().error or "Could not show source preview"
                )
            self._update_playback_controls()
            self._update_segment_controls()

        def _refresh_timeline(self, selected_segment_id: str | None = None) -> None:
            if self.segment_timeline is None:
                return
            if selected_segment_id is None:
                selected_segment_id = self.selected_segment_id
            segments = self.segment_timeline.segment_items
            if selected_segment_id is None and segments:
                selected_segment_id = segments[0].segment_id
            self.selected_segment_id = selected_segment_id
            self.timeline_canvas.set_timeline(
                self.segment_timeline,
                self.selected_segment_id,
            )
            self._update_selected_clip_label()
            self._update_segment_controls()

        def _on_timeline_segment_selected(self, segment_id: str) -> None:
            self.selected_segment_id = segment_id
            self._update_selected_clip_label()
            self._update_segment_controls()

        def _update_selected_clip_label(self) -> None:
            if self.segment_timeline is None or self.selected_segment_id is None:
                self.timeline_selection_label.set_text("No clip selected")
                return
            for index, segment in enumerate(self.segment_timeline.segment_items):
                if segment.segment_id == self.selected_segment_id:
                    state = "Deleted" if segment.deleted else "Included"
                    self.timeline_selection_label.set_text(
                        f"Clip {index + 1} | "
                        f"{format_duration(segment.start_seconds)} - "
                        f"{format_duration(segment.end_seconds)} | {state}"
                    )
                    return
            self.timeline_selection_label.set_text("No clip selected")

        def _on_timeline_viewport_changed(self, adjustment, _param) -> None:
            page_size = adjustment.get_page_size()
            if page_size > 1.0:
                self.timeline_canvas.set_viewport_width(page_size)

        def _zoom_timeline(self, direction: int) -> None:
            if direction > 0:
                self.timeline_canvas.zoom_in()
            else:
                self.timeline_canvas.zoom_out()
            self.timeline_zoom_label.set_text(timeline_zoom_label(self.timeline_canvas.get_zoom()))
            self._center_timeline_on_playhead()

        def _fit_timeline_zoom(self) -> None:
            self.timeline_canvas.fit_to_view()
            self.timeline_zoom_label.set_text(timeline_zoom_label(self.timeline_canvas.get_zoom()))
            self._center_timeline_on_playhead()

        def _center_timeline_on_playhead(self) -> None:
            if self.controller is None:
                return
            adjustment = self.timeline_viewport.get_hadjustment()
            page_size = adjustment.get_page_size()
            if page_size <= 1.0:
                return
            position = self.controller.snapshot().position_seconds
            clips = self.timeline_canvas.get_content_width()
            if clips <= page_size:
                adjustment.set_value(adjustment.get_lower())
                return
            duration = self.controller.snapshot().duration_seconds
            content_width = self.timeline_canvas.get_content_width()
            position_ratio = position / duration if duration else 0.0
            target = position_ratio * content_width - page_size / 2.0
            lower = adjustment.get_lower()
            upper = max(lower, adjustment.get_upper() - page_size)
            adjustment.set_value(max(lower, min(upper, target)))

        def _update_segment_controls(self) -> None:
            enabled = not self._export_in_progress
            self.export_button.set_sensitive(self.project is not None and enabled)
            if self.segment_timeline is not None:
                self.timeline_output_label.set_text(
                    format_output_duration_label(self.segment_timeline.edited_duration_seconds)
                )
            self.timeline_zoom_label.set_text(timeline_zoom_label(self.timeline_canvas.get_zoom()))
            self._update_selected_clip_label()

        def _on_split_clicked(self, _button) -> None:
            if self.segment_timeline is None or self.controller is None:
                self._show_error("Open a source before splitting segments")
                return
            position = self.controller.snapshot().position_seconds
            try:
                _first, second = split_segment(
                    self.segment_timeline,
                    position,
                )
            except ProjectValidationError as error:
                self._show_error(str(error))
                return
            self.selected_segment_id = second.segment_id
            self._refresh_timeline(second.segment_id)
            self._set_status(f"Split clip at {format_duration(position)}")

        def _on_delete_segment_clicked(self, _button) -> None:
            if self.segment_timeline is None or self.selected_segment_id is None:
                self._show_error("Select a clip before toggling its deleted state")
                return
            try:
                deleted = toggle_segment_deleted_state(
                    self.segment_timeline,
                    self.selected_segment_id,
                )
            except ProjectValidationError as error:
                self._show_error(str(error))
                return
            self._refresh_timeline(self.selected_segment_id)
            self._set_status("Deleted selected clip" if deleted else "Restored selected clip")

        def _stop_backend(self) -> None:
            if self.backend is not None:
                self.backend.close()
            self.backend = None
            self.controller = None

        def _on_play_clicked(self, _button) -> None:
            if self.controller is None:
                return
            snapshot = self.controller.snapshot()
            if snapshot.state == PlaybackState.PLAYING:
                self.controller.pause()
            else:
                self.controller.play()
            self._update_playback_controls()
            if self.controller.snapshot().error:
                self._show_error(self.controller.snapshot().error or "Playback failed")

        def _on_key_pressed(
            self,
            _controller,
            keyval: int,
            _keycode: int,
            _state,
        ) -> bool:
            if is_fit_zoom_key(
                keyval,
                _state,
                int(Gdk.ModifierType.CONTROL_MASK),
            ):
                self._fit_timeline_zoom()
                return True
            if is_play_pause_key(keyval):
                self._on_play_clicked(None)
                return True
            if is_split_key(keyval):
                self._on_split_clicked(None)
                return True
            if is_delete_key(keyval):
                self._on_delete_segment_clicked(None)
                return True
            if is_frame_step_key(keyval):
                direction = frame_step_direction(keyval)
                if direction is None:
                    return False
                self._step_playhead(direction)
                return True
            return False

        def _step_playhead(self, direction: int) -> None:
            if self.controller is None:
                return
            snapshot = self.controller.snapshot()
            if snapshot.state == PlaybackState.PLAYING:
                self.controller.pause()
            position = frame_step_position(
                snapshot.position_seconds,
                direction,
                self.source_frame_rate,
                snapshot.duration_seconds,
            )
            self._seek_timeline(position)

        def _seek_timeline(self, position_seconds: float) -> bool:
            if self.controller is None:
                return False
            if not self.controller.seek(position_seconds):
                self._show_error(self.controller.snapshot().error or "Could not seek source")
                return False
            if self.project is not None:
                self.project.set_playhead(self.controller.snapshot().position_seconds)
            self.timeline_canvas.set_playhead(self.controller.snapshot().position_seconds)
            self._update_playback_controls()
            return True

        def _request_timeline_preview(self, position_seconds: float) -> None:
            if self.controller is None or self.backend is None:
                return
            if self.controller.snapshot().state == PlaybackState.PLAYING:
                if not self.controller.pause():
                    self._show_error(
                        self.controller.snapshot().error or "Could not pause source for preview"
                    )
                    return
            self.controller.update_position(position_seconds)
            if self.project is not None:
                self.project.set_playhead(position_seconds)
            self.timeline_canvas.set_playhead(position_seconds)
            self._update_playback_controls()
            try:
                self.backend.request_preview(position_seconds)
            except PlaybackBackendError as error:
                self.controller.report_error(str(error))
                self._show_error(str(error))

        def _on_timeline_scroll(self, _controller, _delta_x, delta_y) -> bool:
            state = _controller.get_current_event_state()
            mode = timeline_scroll_mode(
                _delta_x,
                delta_y,
                int(state),
                int(Gdk.ModifierType.CONTROL_MASK),
                int(Gdk.ModifierType.ALT_MASK),
                int(Gdk.ModifierType.SHIFT_MASK),
            )
            if mode == "none":
                return False
            if mode == "zoom":
                delta = delta_y if abs(delta_y) > 0.01 else _delta_x
                self._zoom_timeline(1 if delta < 0 else -1)
                return True
            adjustment = self.timeline_viewport.get_hadjustment()
            if mode == "viewport":
                delta = _delta_x if abs(_delta_x) > 0.01 else delta_y
                lower = adjustment.get_lower()
                upper = max(
                    lower,
                    adjustment.get_upper() - adjustment.get_page_size(),
                )
                target = adjustment.get_value() + delta * TIMELINE_SCROLL_PIXELS
                adjustment.set_value(max(lower, min(upper, target)))
                return True
            if self.controller is None:
                return False
            snapshot = self.controller.snapshot()
            target = timeline_scroll_position(
                snapshot.position_seconds,
                delta_y,
                snapshot.duration_seconds,
            )
            self._seek_timeline(target)
            return True

        def _on_timeline_view_seek(self, position_seconds: float) -> None:
            self._request_timeline_preview(position_seconds)

        def _poll_playback(self) -> bool:
            if self.backend is not None and self.controller is not None:
                self.controller.update_position(self.backend.current_position())
                if self.project is not None:
                    self.project.set_playhead(self.controller.snapshot().position_seconds)
                self._update_playback_controls()
            return True

        def _update_playback_controls(self) -> None:
            if self.controller is None:
                return
            snapshot = self.controller.snapshot()
            self.position_label.set_text(format_duration(snapshot.position_seconds))
            self.timeline_canvas.set_playhead(snapshot.position_seconds)

        def _on_frame(self, frame: VideoFrame) -> None:
            with self._frame_lock:
                self._latest_frame = frame
                if self._frame_delivery_scheduled:
                    return
                self._frame_delivery_scheduled = True
            GLib.idle_add(self._deliver_latest_frame)

        def _deliver_latest_frame(self) -> bool:
            with self._frame_lock:
                frame = self._latest_frame
                self._latest_frame = None
            if frame is None:
                with self._frame_lock:
                    self._frame_delivery_scheduled = False
                return False
            texture = Gdk.MemoryTexture.new(
                frame.width,
                frame.height,
                Gdk.MemoryFormat.R8G8B8A8,
                GLib.Bytes.new(frame.data),
                frame.width * 4,
            )
            self.preview.set_paintable(texture)
            with self._frame_lock:
                if self._latest_frame is not None:
                    return True
                self._frame_delivery_scheduled = False
            return False

        def _on_backend_error(self, message: str) -> None:
            GLib.idle_add(self._handle_backend_error, message)

        def _handle_backend_error(self, message: str) -> bool:
            if self.controller is not None:
                self.controller.report_error(message)
            self._show_error(message)
            self._update_playback_controls()
            return False

        def _on_backend_end(self) -> None:
            GLib.idle_add(self._handle_backend_end)

        def _handle_backend_end(self) -> bool:
            if self.controller is not None:
                self.controller.finish()
                self._update_playback_controls()
            return False

        def _on_close_request(self, _window) -> bool:
            self._stop_backend()
            return False

        def _start_smoke_test(self) -> bool:
            if self.project is None or self.controller is None:
                self._show_error("Smoke test could not open a source project")
                self._finish_smoke_test()
                return False
            self._on_play_clicked(None)
            GLib.timeout_add(300, self._finish_smoke_test)
            return False

        def _finish_smoke_test(self) -> bool:
            if self.controller is not None:
                self.controller.pause()
                duration = self.controller.snapshot().duration_seconds
                position = duration * 0.25
                self.controller.seek(position)
                if self.segment_timeline is not None and 0.0 < position < duration:
                    self._on_split_clicked(None)
                    self._on_delete_segment_clicked(None)
            if self._smoke_project_path is not None:
                self._save_to(self._smoke_project_path)
            GLib.timeout_add(300, self._end_smoke_test)
            return False

        def _end_smoke_test(self) -> bool:
            self._stop_backend()
            self.get_application().quit()
            return False

    application = Gtk.Application(
        application_id="io.github.resolve_media.editor",
    )

    def on_activate(app) -> None:
        window = EditorWindow(app, source_path, project_path)
        window.present()

    application.connect("activate", on_activate)
    return int(application.run([]))
