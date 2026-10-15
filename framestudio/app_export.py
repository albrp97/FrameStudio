from __future__ import annotations

import threading
import time
from collections.abc import Collection
from copy import deepcopy
from dataclasses import replace
from functools import partial
from pathlib import Path
from typing import Any, Callable

from .app_helpers import format_export_progress_label
from .audio import audio_decision_is_stale
from .av_compositor import (
    AVCompositorExecutionError,
    AVCompositorPlanningError,
    AVRenderPlan,
    plan_project_av,
    render_project_av,
)
from .export import (
    ExportExecutionError,
    ExportPlan,
    ExportPlanningError,
    ExportProgress,
    ExportProgressCallback,
    execute_export,
)
from .export_console import ConsoleProgressReporter
from .export_coordinator import (
    ExportBatchResult,
    ExportCancelled,
    ExportCoordinator,
    ExportResultState,
    build_output_fingerprint,
    build_output_request_maps,
    build_project_output_fingerprint_payload,
    build_tool_identities,
    child_resume_mode,
    discard_batch_receipt,
    output_identity_key,
    protected_receipt_paths,
    protected_source_paths,
    resolve_output_plan,
    verify_planned_output,
)
from .export_naming import smart_export_name
from .export_panel import (
    ExportPanelState,
    fps_panel_rows,
    output_panel_rows,
    prepare_export_panel,
    upscale_panel_rows,
)
from .export_process import check_export_cancelled, report_preparation_progress
from .export_session import (
    ExportSessionError,
    discard_export_session,
    discover_export_session,
    session_root,
)
from .fps_policy import FrameRatePolicy, policy_source_metadata, rate_choice_labels
from .interpolation import RuntimeValidationCache
from .media import MediaProbeError
from .model import Project, ProjectValidationError
from .model_timeline import ABSOLUTE_TIMING_MODE
from .operations import (
    ensure_project_audio_analysis,
    export_destination_conflicts_with_project,
    plan_project_export,
)
from .output_plan import (
    OutputPlan,
    OutputPlanError,
    OutputRequest,
    OutputSelection,
    active_export_sources,
    plan_project_outputs,
    resolve_output_selection,
    set_output_selection,
)
from .performance import PerformanceMode, PerformanceModeError
from .playback import PlaybackBackendError, PlaybackState
from .post_export import (
    POST_EXPORT_ACTIONS,
    PostExportActionError,
    execute_post_export_action,
    normalize_post_export_action,
    write_export_failure_log,
)
from .render_preparations import RenderPreparations
from .source_outputs import plan_source_outputs, render_source_output
from .upscale_policy import UpscalePolicy
from .video_compositor import SourceHashCache


class ExportBatchExecutionError(ExportExecutionError):
    """Carry the structured batch result through the GTK worker boundary."""

    def __init__(self, result: ExportBatchResult) -> None:
        self.result = result
        message = (
            result.error.get("message")
            if result.error is not None
            else "One or more export outputs did not complete"
        )
        super().__init__(message)


def on_export_clicked(window: Any, Gtk: Any, GLib: Any) -> None:
    if window.project is None or window.segment_timeline is None:
        window._show_error("Open a source before exporting")
        return
    if window._export_in_progress:
        return
    open_export_planning_panel(window, Gtk, GLib)


def _choice_from_index(index: int) -> str:
    return ("lowest", "highest", "custom", "60")[index]


def _post_export_action_from_index(index: int) -> str:
    return POST_EXPORT_ACTIONS[index]


def _set_summary_grid(grid: Any, Gtk: Any, rows: tuple[tuple[str, str], ...]) -> None:
    child = grid.get_first_child()
    while child is not None:
        next_child = child.get_next_sibling()
        grid.remove(child)
        child = next_child
    for row, (label_text, value_text) in enumerate(rows):
        label = Gtk.Label(label=label_text, xalign=0.0)
        label.add_css_class("dim-label")
        value = Gtk.Label(label=value_text, xalign=0.0)
        value.set_hexpand(True)
        grid.attach(label, 0, row, 1, 1)
        grid.attach(value, 1, row, 1, 1)


def _export_panel_error_state(filename: str, error: Exception) -> ExportPanelState:
    return ExportPanelState(
        policy=None,
        destination=None,
        filename=filename,
        estimate=None,
        backend_validation=(),
        valid=False,
        reason=str(error),
    )


def _export_panel_result_is_current(
    panel_state: dict[str, Any],
    generation: int,
) -> bool:
    return not panel_state["closed"] and generation == panel_state["generation"]


class ExportPanelPreparation:
    """Keep one active request and only the latest pending panel refresh."""

    def __init__(self, glib: Any) -> None:
        self._glib = glib
        self._lock = threading.Lock()
        self._worker: threading.Thread | None = None
        self._pending: (
            tuple[Project, Path, Callable[[ExportPanelState], Any], dict[str, Any]] | None
        ) = None
        self._closed = False
        self._runtime_cache: RuntimeValidationCache = {}

    def submit(
        self,
        project: Project,
        folder: Path,
        callback: Callable[[ExportPanelState], Any],
        **options: Any,
    ) -> threading.Thread:
        with self._lock:
            if self._closed:
                raise RuntimeError("Export planner is closed")
            self._pending = (project, folder, callback, options)
            if self._worker is None:
                self._worker = threading.Thread(
                    target=self._prepare,
                    name="framestudio-editor-export-planning",
                    daemon=True,
                )
                self._worker.start()
            return self._worker

    def close(self) -> None:
        with self._lock:
            self._closed = True
            self._pending = None

    def _prepare(self) -> None:
        while True:
            with self._lock:
                if self._closed or self._pending is None:
                    self._worker = None
                    return
                project, folder, callback, options = self._pending
                self._pending = None
            try:
                state = prepare_export_panel(
                    deepcopy(project),
                    folder,
                    runtime_cache=self._runtime_cache,
                    **options,
                )
            except (ImportError, OSError, RuntimeError, ValueError) as error:
                state = _export_panel_error_state(
                    str(options.get("filename") or ""),
                    error,
                )
            with self._lock:
                deliver = not self._closed and self._pending is None
            if deliver:
                self._glib.idle_add(callback, state)


def start_export_panel_preparation(
    project: Project,
    folder: Path,
    glib: Any,
    callback: Callable[[ExportPanelState], Any],
    *,
    preparation: ExportPanelPreparation | None = None,
    **options: Any,
) -> threading.Thread:
    return (preparation or ExportPanelPreparation(glib)).submit(
        project,
        folder,
        callback,
        **options,
    )


def open_export_planning_panel(window: Any, Gtk: Any, GLib: Any) -> None:
    if window.project is None or window.segment_timeline is None:
        window._show_error("Open a source before exporting")
        return
    existing = getattr(window, "export_planning_window", None)
    if existing is not None:
        existing.present()
        return
    project = window.project
    folder = (
        window.project_path.parent
        if window.project_path is not None
        else Path(project.source.path).parent
    )
    panel = Gtk.Window()
    panel.set_title("Plan export")
    panel.set_transient_for(window)
    panel.set_modal(True)
    panel.set_destroy_with_parent(True)
    panel.set_default_size(620, 520)
    window.export_planning_window = panel

    root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
    root.set_margin_top(16)
    root.set_margin_bottom(16)
    root.set_margin_start(16)
    root.set_margin_end(16)
    panel.set_child(root)

    heading = Gtk.Label(label="Review export plan")
    heading.set_xalign(0.0)
    heading.add_css_class("heading")
    root.append(heading)

    destination_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
    destination_row.append(Gtk.Label(label="Folder", xalign=0.0))
    folder_label = Gtk.Label(label=str(folder))
    folder_label.set_xalign(0.0)
    folder_label.set_hexpand(True)
    destination_row.append(folder_label)
    choose_folder = Gtk.Button(label="Choose folder")
    destination_row.append(choose_folder)
    root.append(destination_row)

    filename_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
    filename_row.append(Gtk.Label(label="Filename", xalign=0.0))
    filename_entry = Gtk.Entry()
    filename_entry.set_hexpand(True)
    filename_row.append(filename_entry)
    root.append(filename_row)

    rate_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
    rate_row.append(Gtk.Label(label="Output FPS", xalign=0.0))
    rate_metadata = policy_source_metadata(active_export_sources(project))
    rate_model = Gtk.StringList.new(
        list(rate_choice_labels(rate_metadata))
        if rate_metadata
        else [
            "Lowest input FPS (no active sources)",
            "Highest input FPS (no active sources)",
            "Custom FPS",
            "60 FPS",
        ]
    )
    rate_dropdown = Gtk.DropDown.new(rate_model, None)
    rate_row.append(rate_dropdown)
    custom_entry = Gtk.Entry()
    custom_entry.set_placeholder_text("e.g. 59.94 or 60000/1001")
    custom_entry.set_width_chars(18)
    custom_entry.set_sensitive(False)
    rate_row.append(custom_entry)
    root.append(rate_row)

    enhancement = Gtk.CheckButton.new_with_label("Enhance sources below the target rate")
    root.append(enhancement)
    upscale_enhancement = Gtk.CheckButton.new_with_label(
        "Upscale eligible videos (SuperUltraCompact)",
    )
    root.append(upscale_enhancement)

    output_frame = Gtk.Frame.new("Outputs")
    output_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
    output_box.set_margin_top(8)
    output_box.set_margin_bottom(8)
    output_box.set_margin_start(12)
    output_box.set_margin_end(12)
    final_output_toggle = Gtk.CheckButton.new_with_label("Final edited video")
    source_output_toggle = Gtk.CheckButton.new_with_label(
        "Source reels (one output per track/source pair)",
    )
    output_box.append(final_output_toggle)
    output_box.append(source_output_toggle)
    output_frame.set_child(output_box)
    root.append(output_frame)
    panel.final_output_toggle = final_output_toggle
    panel.source_output_toggle = source_output_toggle

    post_export_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
    post_export_row.append(Gtk.Label(label="After export", xalign=0.0))
    post_export_model = Gtk.StringList.new(["Nothing", "Sleep", "Shutdown"])
    post_export_dropdown = Gtk.DropDown.new(post_export_model, None)
    post_export_dropdown.set_selected(0)
    post_export_dropdown.set_tooltip_text(
        "Run the selected Linux power action only after export completion",
    )
    post_export_row.append(post_export_dropdown)
    root.append(post_export_row)

    summary_frame = Gtk.Frame.new("Export summary")
    summary_grid = Gtk.Grid()
    summary_grid.set_column_spacing(20)
    summary_grid.set_row_spacing(6)
    summary_grid.set_margin_top(8)
    summary_grid.set_margin_bottom(8)
    summary_grid.set_margin_start(12)
    summary_grid.set_margin_end(12)
    summary_frame.set_child(summary_grid)
    root.append(summary_frame)
    notice_label = Gtk.Label()
    notice_label.set_xalign(0.0)
    notice_label.set_wrap(True)
    notice_label.add_css_class("dim-label")
    root.append(notice_label)
    session_frame = Gtk.Frame.new("Resumable export")
    session_root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
    session_root.set_margin_top(8)
    session_root.set_margin_bottom(8)
    session_root.set_margin_start(12)
    session_root.set_margin_end(12)
    session_label = Gtk.Label(xalign=0.0)
    session_label.set_wrap(True)
    session_root.append(session_label)
    session_actions = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
    resume_session = Gtk.Button(label="Resume export")
    restart_session = Gtk.Button(label="Start over")
    discard_session = Gtk.Button(label="Discard")
    session_actions.append(resume_session)
    session_actions.append(restart_session)
    session_actions.append(discard_session)
    session_root.append(session_actions)
    session_frame.set_child(session_root)
    session_frame.set_visible(False)
    root.append(session_frame)
    error_label = Gtk.Label()
    error_label.set_xalign(0.0)
    error_label.set_wrap(True)
    error_label.add_css_class("error")
    root.append(error_label)

    actions = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
    spacer = Gtk.Box()
    spacer.set_hexpand(True)
    actions.append(spacer)
    cancel = Gtk.Button(label="Cancel")
    confirm = Gtk.Button(label="Start export")
    confirm.set_sensitive(False)
    actions.append(cancel)
    actions.append(confirm)
    root.append(actions)

    current_policy = project.get_frame_rate_policy()
    current_upscale_policy = project.get_upscale_policy()
    suggested_filename = smart_export_name(
        [source.path for source in project.sources or (project.source,)],
        policy=current_policy,
        project_path=window.project_path,
    )
    filename_entry.set_text(suggested_filename)
    rate_dropdown.set_selected(
        {"lowest": 0, "highest": 1, "custom": 2, "60": 3}[current_policy.choice]
    )
    if current_policy.custom_rate is not None:
        custom_entry.set_text(str(current_policy.custom_rate))
    custom_entry.set_sensitive(current_policy.choice == "custom")
    enhancement.set_active(current_policy.enhancement_enabled)
    upscale_enhancement.set_active(current_upscale_policy.enhancement_enabled)
    try:
        current_output_selection = resolve_output_selection(project)
        initial_output_error = None
    except OutputPlanError as error:
        current_output_selection = OutputSelection()
        initial_output_error = str(error)
    final_output_toggle.set_active(current_output_selection.include_final)
    source_output_toggle.set_active(current_output_selection.include_source_outputs)
    panel_state: dict[str, Any] = {
        "folder": folder,
        "state": None,
        "generation": 0,
        "closed": False,
        "automatic_filename": True,
        "suggested_filename": suggested_filename,
        "updating_filename": False,
        "output_mode": current_output_selection.mode,
        "output_plan": None,
        "output_rows": (),
        "output_error": initial_output_error,
        "render_guard": None,
        "preparation": ExportPanelPreparation(GLib),
    }

    def _combined_final_supported() -> bool:
        timeline = project.timeline
        if timeline.tracks is None:
            return True
        return len(timeline.tracks) == 1 and timeline.timing_mode == "legacy-ripple"

    def _output_destination() -> Path:
        state = panel_state.get("state")
        if state is not None and state.destination is not None:
            return Path(state.destination)
        filename = filename_entry.get_text().strip() or suggested_filename
        return Path(panel_state["folder"]) / filename

    def _set_output_error(message: str | None) -> None:
        panel_state["output_error"] = message
        if message is not None:
            panel_state["render_guard"] = None

    def _refresh_output_plan(destination: Path, *, persist: bool) -> None:
        final_selected = final_output_toggle.get_active()
        source_selected = source_output_toggle.get_active()
        if not final_selected and not source_selected:
            panel_state["output_plan"] = None
            panel_state["output_rows"] = ()
            panel_state["output_mode"] = None
            _set_output_error("Select at least one output: final video or source reels.")
            return
        mode = (
            "combined"
            if final_selected and source_selected
            else "final-only"
            if final_selected
            else "source-only"
        )
        try:
            output_plan = plan_project_outputs(project, destination, mode=mode)
            if persist:
                try:
                    set_output_selection(project, mode=mode)
                except OutputPlanError:
                    previous_settings = deepcopy(project.output_settings)
                    project.output_settings["output_selection"] = OutputSelection.from_mode(
                        mode
                    ).to_dict()
                    try:
                        project.validate()
                    except (ProjectValidationError, ValueError) as error:
                        project.output_settings = previous_settings
                        raise OutputPlanError(str(error)) from error
        except OutputPlanError as error:
            panel_state["output_plan"] = None
            panel_state["output_rows"] = ()
            panel_state["output_mode"] = mode
            _set_output_error(str(error))
            return
        panel_state["output_plan"] = output_plan
        panel_state["output_rows"] = output_panel_rows(output_plan)
        panel_state["output_mode"] = mode
        _set_output_error(initial_output_error if not persist else None)
        panel_state["render_guard"] = None

    def _summary_rows(state: ExportPanelState | None) -> tuple[tuple[str, str], ...]:
        if state is None:
            selected_choice = _choice_from_index(rate_dropdown.get_selected())
            rows = (
                *fps_panel_rows(
                    project,
                    choice=selected_choice,
                    custom_rate=custom_entry.get_text().strip() or None,
                    enhancement_enabled=enhancement.get_active(),
                    backend=current_policy.backend,
                ),
                *upscale_panel_rows(
                    project,
                    enabled=upscale_enhancement.get_active(),
                ),
            )
        else:
            rows = state.display_rows
        return (*rows, *panel_state["output_rows"])

    def _update_render_button(state: ExportPanelState | None) -> None:
        if state is None:
            confirm.set_sensitive(False)
            return
        if not state.valid:
            confirm.set_sensitive(False)
            return
        confirm.set_sensitive(
            panel_state["output_plan"] is not None
            and panel_state["output_error"] is None
            and panel_state["render_guard"] is None,
        )

    def refresh_session_controls(destination: Path | None) -> None:
        if destination is None:
            session_frame.set_visible(False)
            return
        info = discover_export_session(destination)
        if not info.exists:
            session_frame.set_visible(False)
            return
        session_frame.set_visible(True)
        if info.valid:
            stage = info.last_completed_stage or "no completed stage"
            session_label.set_text(
                f"Pending session: {stage}; {info.completed_stage_count} completed stage(s)"
            )
        else:
            session_label.set_text(f"Pending session is invalid: {info.reason}")
        resume_session.set_visible(info.resumable)
        restart_session.set_visible(True)
        discard_session.set_visible(True)

    def refresh(*_args: Any) -> None:
        selected_choice = _choice_from_index(rate_dropdown.get_selected())
        custom_entry.set_sensitive(selected_choice == "custom")
        custom_value = custom_entry.get_text().strip() or None
        filename = (
            None if panel_state["automatic_filename"] else filename_entry.get_text().strip() or None
        )
        panel_state["generation"] += 1
        generation = panel_state["generation"]
        panel_state["state"] = None
        panel_state["output_plan"] = None
        panel_state["output_rows"] = ()
        panel_state["render_guard"] = None
        _set_summary_grid(
            summary_grid,
            Gtk,
            (
                *fps_panel_rows(
                    project,
                    choice=selected_choice,
                    custom_rate=custom_value,
                    enhancement_enabled=enhancement.get_active(),
                    backend=current_policy.backend,
                ),
                *upscale_panel_rows(
                    project,
                    enabled=upscale_enhancement.get_active(),
                ),
            ),
        )
        notice_label.set_text("Preparing export plan...")
        error_label.set_text(panel_state["output_error"] or "")
        confirm.set_sensitive(False)

        def apply_state(state: ExportPanelState) -> bool:
            if not _export_panel_result_is_current(panel_state, generation):
                return False
            panel_state["state"] = state
            if panel_state["automatic_filename"] and state.filename:
                if filename_entry.get_text() != state.filename:
                    panel_state["updating_filename"] = True
                    filename_entry.set_text(state.filename)
                    panel_state["updating_filename"] = False
                panel_state["suggested_filename"] = state.filename
            if state.destination is not None:
                folder_label.set_text(str(state.destination.parent))
                _refresh_output_plan(state.destination, persist=False)
            _set_summary_grid(summary_grid, Gtk, _summary_rows(state))
            notice_label.set_text(state.notice or "")
            error_label.set_text(
                panel_state["output_error"] or panel_state["render_guard"] or state.reason or "",
            )
            _update_render_button(state)
            refresh_session_controls(state.destination)
            return False

        try:
            start_export_panel_preparation(
                project,
                panel_state["folder"],
                GLib,
                apply_state,
                choice=selected_choice,
                custom_rate=custom_value,
                enhancement_enabled=enhancement.get_active(),
                upscale_enabled=upscale_enhancement.get_active(),
                filename=filename,
                project_path=window.project_path,
                preparation=panel_state["preparation"],
            )
        except (OSError, RuntimeError, ValueError) as error:
            apply_state(_export_panel_error_state(filename or "", error))
        _refresh_output_plan(_output_destination(), persist=False)
        _set_summary_grid(summary_grid, Gtk, _summary_rows(panel_state["state"]))
        error_label.set_text(
            panel_state["output_error"] or panel_state["render_guard"] or "",
        )
        _update_render_button(panel_state["state"])

    def filename_changed(_entry: Any) -> None:
        if panel_state["updating_filename"]:
            return
        current_filename = filename_entry.get_text().strip()
        if current_filename != panel_state["suggested_filename"]:
            panel_state["automatic_filename"] = False
        refresh()

    def choose_folder_done(dialog: Any, result: Any, _data: Any) -> None:
        try:
            selected = dialog.select_folder_finish(result)
        except GLib.Error as error:
            if "dismiss" not in str(error).lower():
                error_label.set_text(str(error))
            return
        if selected is None or selected.get_path() is None:
            return
        panel_state["folder"] = Path(selected.get_path())
        folder_label.set_text(str(panel_state["folder"]))
        refresh()

    def choose_folder_clicked(_button: Any) -> None:
        dialog = Gtk.FileDialog.new()
        dialog.set_title("Choose export folder")
        dialog.select_folder(panel, None, choose_folder_done, None)

    def output_choice_toggled(_button: Any) -> None:
        state = panel_state.get("state")
        _refresh_output_plan(
            state.destination
            if state is not None and state.destination is not None
            else _output_destination(),
            persist=True,
        )
        _set_summary_grid(summary_grid, Gtk, _summary_rows(state))
        error_label.set_text(
            panel_state["output_error"]
            or panel_state["render_guard"]
            or (state.reason if state is not None else "")
            or "",
        )
        _update_render_button(state)

    def cancel_clicked(_button: Any) -> None:
        panel.close()
        window.export_planning_window = None

    def begin_export(mode: str) -> None:
        state: ExportPanelState | None = panel_state.get("state")
        output_plan: OutputPlan | None = panel_state["output_plan"]
        if (
            state is None
            or not state.valid
            or state.destination is None
            or state.policy is None
            or output_plan is None
            or panel_state["output_error"] is not None
            or panel_state["render_guard"] is not None
        ):
            return
        panel.close()
        window.export_planning_window = None
        start_export(
            window,
            state.destination,
            GLib,
            state.policy.policy,
            state.upscale_policy.policy if state.upscale_policy is not None else None,
            _post_export_action_from_index(post_export_dropdown.get_selected()),
            resume_mode=mode,
            output_mode=output_plan.mode,
        )

    def confirm_clicked(_button: Any) -> None:
        begin_export("fresh")

    def resume_clicked(_button: Any) -> None:
        begin_export("resume")

    def restart_clicked(_button: Any) -> None:
        begin_export("restart")

    def discard_clicked(_button: Any) -> None:
        state: ExportPanelState = panel_state["state"]
        if state is None or state.destination is None:
            return
        try:
            output_plan: OutputPlan | None = panel_state.get("output_plan")
            planned_outputs = (
                ()
                if output_plan is None
                else tuple(request.destination for request in output_plan.output_requests)
            )
            discard_batch_receipt(
                state.destination,
                protected_source_paths=protected_receipt_paths(
                    project,
                    project_path=window.project_path,
                    planned_outputs=planned_outputs,
                ),
            )
            discard_export_session(state.destination)
        except ExportSessionError as error:
            error_label.set_text(str(error))
            return
        refresh_session_controls(state.destination)
        notice_label.set_text("Pending export session discarded.")

    choose_folder.connect("clicked", choose_folder_clicked)
    cancel.connect("clicked", cancel_clicked)
    confirm.connect("clicked", confirm_clicked)
    rate_dropdown.connect("notify::selected", refresh)
    custom_entry.connect("changed", refresh)
    enhancement.connect("toggled", refresh)
    upscale_enhancement.connect("toggled", refresh)
    final_output_toggle.connect("toggled", output_choice_toggled)
    source_output_toggle.connect("toggled", output_choice_toggled)
    filename_entry.connect("changed", filename_changed)
    resume_session.connect("clicked", resume_clicked)
    restart_session.connect("clicked", restart_clicked)
    discard_session.connect("clicked", discard_clicked)
    panel.connect("close-request", lambda _window: _clear_export_panel(window, panel_state))
    panel.present()
    refresh()


def _clear_export_panel(window: Any, panel_state: dict[str, Any] | None = None) -> bool:
    if panel_state is not None:
        panel_state["closed"] = True
        panel_state["generation"] += 1
        preparation = panel_state.get("preparation")
        if preparation is not None:
            preparation.close()
    window.export_planning_window = None
    return False


def on_export_dialog_done(window: Any, dialog: Any, result: Any, GLib: Any) -> None:
    try:
        selected = dialog.save_finish(result)
    except GLib.Error as error:
        if "dismiss" not in str(error).lower():
            window._show_error(str(error))
        return
    if selected is not None and selected.get_path() is not None:
        window._start_export(Path(selected.get_path()))


def reset_export_progress(window: Any) -> None:
    window.export_progress_panel.set_visible(True)
    window.export_progress_bar.set_fraction(0.0)
    window.export_progress_bar.set_text("0.0%")
    window.export_progress_label.set_text("Preparing export...")
    window.cancel_export_button.set_visible(True)
    window.cancel_export_button.set_sensitive(True)


def update_export_progress(window: Any, progress: ExportProgress) -> bool:
    window.export_progress_bar.set_fraction(
        max(0.0, min(1.0, progress.percent / 100.0)),
    )
    window.export_progress_bar.set_text(f"{progress.percent:.1f}%")
    window.export_progress_label.set_text(format_export_progress_label(progress))
    return False


def cancel_export(window: Any) -> None:
    cancel_event = getattr(window, "_export_cancel_event", None)
    if cancel_event is None or cancel_event.is_set():
        return
    cancellation_lock = getattr(window, "_export_cancellation_lock", None)
    if cancellation_lock is None:
        cancel_event.set()
    else:
        with cancellation_lock:
            if cancel_event.is_set():
                return
            cancel_event.set()
    window.cancel_export_button.set_sensitive(False)
    window._set_status("Cancelling export...")


def request_close_after_export(window: Any) -> bool:
    if not getattr(window, "_export_in_progress", False):
        return False
    window._close_after_export = True
    cancel_export(window)
    return True


def run_export_job(
    project: Project,
    destination: Path,
    *,
    frame_rate_policy: FrameRatePolicy | None,
    progress_callback: ExportProgressCallback | None,
    cancel_event: threading.Event | None,
    cancellation_lock: threading.Lock | None = None,
    analysis_lock: threading.Lock | None = None,
    upscale_policy: UpscalePolicy | None = None,
    resume_mode: str = "fresh",
    batch_result_holder: dict[str, ExportBatchResult] | None = None,
) -> tuple[Path, ExportPlan]:
    def plan_export_job() -> ExportPlan:
        return _plan_export_with_analysis_lock(
            project,
            destination,
            frame_rate_policy=frame_rate_policy,
            upscale_policy=upscale_policy,
            cancel_event=cancel_event,
            analysis_lock=analysis_lock,
        )

    with PerformanceMode("on"):
        _ensure_audio_analysis_with_lock(
            project,
            ffmpeg_path="ffmpeg",
            cancel_event=cancel_event,
            analysis_lock=analysis_lock,
            progress_callback=progress_callback,
        )
        plan = plan_export_job()
        output = execute_export(
            plan,
            progress_callback=progress_callback,
            cancel_event=cancel_event,
            cancellation_lock=cancellation_lock,
            resume_mode=resume_mode,
        )
    return output, plan


def _plan_export_with_analysis_lock(
    project: Project,
    destination: Path,
    *,
    cancel_event: threading.Event | None,
    analysis_lock: threading.Lock | None,
    frame_rate_policy: FrameRatePolicy | None = None,
    upscale_policy: UpscalePolicy | None = None,
    ffprobe_path: str = "ffprobe",
    ffmpeg_path: str = "ffmpeg",
) -> ExportPlan:
    planner = partial(
        plan_project_export,
        project,
        destination,
        frame_rate_policy=frame_rate_policy,
        upscale_policy=upscale_policy,
        ffprobe_path=ffprobe_path,
        ffmpeg_path=ffmpeg_path,
        cancel_event=cancel_event,
    )
    if analysis_lock is None:
        return planner()
    while not analysis_lock.acquire(timeout=0.05):
        if cancel_event is not None and cancel_event.is_set():
            raise ExportPlanningError("Export cancelled")
    try:
        return planner()
    finally:
        analysis_lock.release()


def _ensure_audio_analysis_with_lock(
    project: Project,
    *,
    ffmpeg_path: str,
    cancel_event: threading.Event | None,
    analysis_lock: threading.Lock | None,
    source_ids: Collection[str] | None = None,
    progress_callback: ExportProgressCallback | None = None,
) -> None:
    analyze = partial(
        ensure_project_audio_analysis,
        project,
        ffmpeg_path=ffmpeg_path,
        cancel_event=cancel_event,
        source_ids=source_ids,
        progress_callback=progress_callback,
    )
    if analysis_lock is None:
        analyze()
        return
    while not analysis_lock.acquire(timeout=0.05):
        if cancel_event is not None and cancel_event.is_set():
            raise ExportPlanningError("Export cancelled")
    try:
        analyze()
    finally:
        analysis_lock.release()


def _needs_synchronized_final(project: Project) -> bool:
    timeline = getattr(project, "timeline", None)
    if timeline is None:
        return False
    return (
        timeline.timing_mode == ABSOLUTE_TIMING_MODE
        or timeline.tracks is not None
        and len(timeline.tracks) > 1
    )


def run_output_choice_job(
    project: Project,
    destination: Path,
    *,
    output_mode: str,
    frame_rate_policy: FrameRatePolicy | None,
    upscale_policy: UpscalePolicy | None = None,
    progress_callback: ExportProgressCallback | None,
    cancel_event: threading.Event | None,
    cancellation_lock: threading.Lock | None = None,
    analysis_lock: threading.Lock | None = None,
    resume_mode: str = "fresh",
    batch_result_holder: dict[str, ExportBatchResult] | None = None,
    project_path: Path | None = None,
) -> tuple[Path, OutputPlan, ExportPlan | AVRenderPlan | None, int]:
    """Render a selected output set through one recoverable coordinator."""

    plan_export_job = partial(
        _plan_export_with_analysis_lock,
        cancel_event=cancel_event,
        analysis_lock=analysis_lock,
    )

    with PerformanceMode("on"):
        started = time.monotonic()
        source_hash_cache: SourceHashCache = {}
        runtime_cache: RuntimeValidationCache = {}
        check_export_cancelled(cancel_event)
        output_plan = plan_project_outputs(project, destination, mode=output_mode)
        _ensure_audio_analysis_with_lock(
            project,
            ffmpeg_path="ffmpeg",
            cancel_event=cancel_event,
            analysis_lock=analysis_lock,
            source_ids={
                source_id
                for request in output_plan.output_requests
                for source_id in request.source_ids
            },
            progress_callback=progress_callback,
        )
        final_plan: ExportPlan | AVRenderPlan | None = None
        check_export_cancelled(cancel_event)
        report_preparation_progress(
            progress_callback,
            "Planning export outputs",
            0,
            len(output_plan.output_requests),
            started,
        )
        if output_plan.final_request is not None:
            if _needs_synchronized_final(project):
                final_plan = plan_project_av(
                    project,
                    output_plan.final_request.destination,
                    frame_rate_policy=frame_rate_policy,
                    upscale_policy=upscale_policy,
                    cancel_event=cancel_event,
                    progress_callback=progress_callback,
                    source_hash_cache=source_hash_cache,
                    runtime_cache=runtime_cache,
                )
            else:
                final_plan = plan_export_job(
                    project,
                    output_plan.final_request.destination,
                    frame_rate_policy=frame_rate_policy,
                    upscale_policy=upscale_policy,
                )
        source_plans = plan_source_outputs(
            project,
            output_plan.source_outputs,
            ffprobe_path="ffprobe",
            ffmpeg_path="ffmpeg",
            frame_rate_policy=frame_rate_policy,
            upscale_policy=upscale_policy,
            plan_project_export_fn=plan_export_job,
            cancel_event=cancel_event,
            progress_callback=progress_callback,
            runtime_cache=runtime_cache,
        )
        check_export_cancelled(cancel_event)
        source_by_key = {output_identity_key(plan.request.identity): plan for plan in source_plans}
        final_by_key: dict[str, ExportPlan | AVRenderPlan]
        request_by_key: dict[str, OutputRequest]
        final_by_key, request_by_key = build_output_request_maps(
            output_plan,
            final_plan,
        )
        tool_identities = build_tool_identities()
        fingerprints = {
            key: build_output_fingerprint(
                build_project_output_fingerprint_payload(
                    project,
                    request,
                    frame_rate_policy=frame_rate_policy,
                    upscale_policy=upscale_policy,
                    tool_identities=tool_identities,
                    source_hash_cache=source_hash_cache,
                    cancel_event=cancel_event,
                    progress_callback=progress_callback,
                )
            )
            for key, request in request_by_key.items()
        }
        lock = cancellation_lock or threading.Lock()

        def render_output(request: Any, candidate: Path, event: threading.Event) -> Path:
            key = output_identity_key(request.identity)
            if request.output_kind == "source":
                rendered = render_source_output(
                    source_by_key[key],
                    resume_mode=resume_mode,
                    progress_callback=progress_callback,
                    destination_override=candidate,
                    cancel_event=event,
                    cancellation_lock=lock,
                )
                if not rendered.verified:
                    if event.is_set():
                        raise ExportCancelled(rendered.error or "Export cancelled")
                    raise ExportExecutionError(
                        rendered.error or "Source output failed verification"
                    )
                return candidate
            planned = final_by_key[key]
            if isinstance(planned, AVRenderPlan):
                render_project_av(
                    replace(planned, destination=candidate),
                    cancel_event=event,
                    cancellation_lock=lock,
                    progress_callback=progress_callback,
                    preparations=RenderPreparations(
                        session_root(destination) / "render-preparations",
                        cancel_event=event,
                        progress_callback=progress_callback,
                    ),
                )
                return candidate
            rendered_path = execute_export(
                replace(planned, destination=candidate),
                progress_callback=progress_callback,
                cancel_event=event,
                cancellation_lock=lock,
                resume_mode=child_resume_mode(candidate, resume_mode),
            )
            if rendered_path.expanduser().resolve() != candidate.expanduser().resolve():
                raise ExportExecutionError("Final renderer returned an unexpected candidate path")
            return candidate

        def verify_output(
            request: Any,
            candidate: Path,
            event: threading.Event,
        ) -> dict[str, Any]:
            key = output_identity_key(request.identity)
            planned = resolve_output_plan(key, source_by_key, final_by_key)
            if planned is None:
                raise ExportExecutionError(
                    "No concrete output plan is available for verification",
                )
            return verify_planned_output(
                planned,
                candidate,
                ffmpeg_path="ffmpeg",
                ffprobe_path="ffprobe",
                cancel_event=event,
            )

        try:
            coordinator = ExportCoordinator(
                output_requests=output_plan.output_requests,
                session_destination=destination,
                output_fingerprints=fingerprints,
                render_output=render_output,
                verify_output=verify_output,
                publication_lock=lock,
                tool_versions=tool_identities,
                protected_source_paths=protected_source_paths(project),
                protected_receipt_paths=protected_receipt_paths(
                    project,
                    project_path=project_path,
                    planned_outputs=tuple(
                        request.destination for request in output_plan.output_requests
                    ),
                ),
            )
        except (ExportSessionError, ValueError) as error:
            raise ExportExecutionError(str(error)) from error
        coordinated = coordinator.run(mode=resume_mode, cancel_event=cancel_event)
        if batch_result_holder is not None:
            batch_result_holder["result"] = coordinated
        if not coordinated.complete:
            raise ExportBatchExecutionError(coordinated)
        output = (
            output_plan.final_request.destination
            if output_plan.final_request is not None
            else output_plan.source_output_root
        )
        if output is None:
            raise ExportExecutionError("Selected output set produced no destination")
    return output, output_plan, final_plan, len(source_plans)


def start_export(
    window: Any,
    destination: Path,
    GLib: Any,
    frame_rate_policy: Any | None = None,
    upscale_policy: UpscalePolicy | None = None,
    post_export_action: str | None = None,
    resume_mode: str = "fresh",
    output_mode: str = "final-only",
) -> None:
    if window.project is None or window.segment_timeline is None:
        window._show_error("Open a source before exporting")
        return
    if export_destination_conflicts_with_project(
        window.project_path,
        destination,
    ):
        window._show_error("Export destination must differ from the project file")
        return
    try:
        normalized_post_export_action = normalize_post_export_action(post_export_action)
    except PostExportActionError as error:
        window._show_error(str(error))
        return
    controller = getattr(window, "controller", None)
    if controller is not None and controller.snapshot().state == PlaybackState.PLAYING:
        if not controller.pause():
            window._show_error(controller.snapshot().error or "Could not pause playback for export")
            return
        window._update_playback_controls()
    project = window.project
    preview_backend = getattr(window, "backend", None)
    export_project = deepcopy(project)
    window._export_project_snapshot = export_project
    window._export_project_path = window.project_path
    window._export_destination = destination
    window._export_post_export_action = normalized_post_export_action
    window._export_resume_mode = resume_mode
    cancel_event = threading.Event()
    cancellation_lock = threading.Lock()
    window._export_cancel_event = cancel_event
    window._export_cancellation_lock = cancellation_lock
    batch_result_holder: dict[str, ExportBatchResult] = {}
    window._close_after_export = False
    window._export_in_progress = True
    window._update_segment_controls()
    reset_export_progress(window)
    window._set_status("Planning and exporting edited video...")

    def export_worker() -> None:
        console_progress = ConsoleProgressReporter()

        def report_progress(progress: ExportProgress) -> None:
            console_progress(progress)
            GLib.idle_add(update_export_progress, window, progress)

        try:
            release_preview = getattr(preview_backend, "release_preview_resources", None)
            if callable(release_preview):
                release_preview()
            analysis_lock = getattr(window, "_audio_analysis_worker_lock", None)
            output, output_plan, final_plan, source_count = run_output_choice_job(
                export_project,
                destination,
                output_mode=output_mode,
                frame_rate_policy=frame_rate_policy,
                upscale_policy=upscale_policy,
                progress_callback=report_progress,
                cancel_event=cancel_event,
                cancellation_lock=cancellation_lock,
                analysis_lock=analysis_lock,
                resume_mode=resume_mode,
                batch_result_holder=batch_result_holder,
                project_path=window.project_path,
            )
            if final_plan is None:
                message = f"Exported {source_count} source output(s) in {output_plan.mode} mode"
            elif isinstance(final_plan, AVRenderPlan):
                message = (
                    f"Exported synchronized final output and {source_count} "
                    f"source output(s) in {output_plan.mode} mode"
                )
            else:
                message = (
                    f"Exported final output and {source_count} source output(s) "
                    f"in {output_plan.mode} mode using {final_plan.route}: "
                    f"{final_plan.reason}"
                )
        except (
            ExportBatchExecutionError,
            AVCompositorExecutionError,
            AVCompositorPlanningError,
            ExportExecutionError,
            ExportPlanningError,
            MediaProbeError,
            PerformanceModeError,
            PlaybackBackendError,
        ) as error:
            if isinstance(error, ExportBatchExecutionError):
                GLib.idle_add(
                    finish_export,
                    window,
                    None,
                    str(error),
                    frame_rate_policy,
                    upscale_policy,
                    error.result,
                )
                return
            message = str(error)
            if "export cancelled" in message.casefold():
                message = "Export cancelled"
            GLib.idle_add(finish_export, window, None, message)
            return
        GLib.idle_add(
            finish_export,
            window,
            output,
            message,
            frame_rate_policy,
            upscale_policy,
            batch_result_holder.get("result"),
        )

    threading.Thread(
        target=export_worker,
        name="framestudio-editor-export",
        daemon=True,
    ).start()


def _retain_export_audio_settings(window: Any) -> None:
    snapshot = getattr(window, "_export_project_snapshot", None)
    project = getattr(window, "project", None)
    if not isinstance(snapshot, Project) or not isinstance(project, Project):
        return
    if snapshot.project_id != project.project_id:
        return
    changed = False
    for source in project.sources or (project.source,):
        settings = snapshot.source_audio_settings(source.source_id)
        if settings.get("status") not in {
            "ready",
            "silent",
            "unsupported",
            "failed",
            "not-applicable",
        }:
            continue
        if audio_decision_is_stale(source, settings):
            continue
        if settings != project.source_audio_settings(source.source_id):
            project.set_source_audio_settings(source.source_id, deepcopy(settings))
            changed = True
    autosave = getattr(window, "_autosave_current_project", None)
    if changed and callable(autosave):
        autosave()


def finish_export(
    window: Any,
    output: Path | None,
    message: str,
    frame_rate_policy: FrameRatePolicy | None = None,
    upscale_policy: UpscalePolicy | None = None,
    batch_result: ExportBatchResult | None = None,
) -> bool:
    _retain_export_audio_settings(window)
    post_export_action = normalize_post_export_action(
        getattr(window, "_export_post_export_action", None),
    )
    project_path = getattr(window, "_export_project_path", None)
    destination = getattr(window, "_export_destination", None)
    if destination is None:
        destination = output
    window._export_in_progress = False
    window._export_cancel_event = None
    window._export_cancellation_lock = None
    window._export_project_snapshot = None
    window._export_project_path = None
    window._export_destination = None
    window._export_post_export_action = None
    window._export_resume_mode = None
    window._last_export_batch_result = batch_result
    window._export_output_results = (
        tuple(result.to_dict() for result in batch_result.results)
        if batch_result is not None
        else ()
    )
    close_after_export = bool(getattr(window, "_close_after_export", False))
    window._close_after_export = False
    window.cancel_export_button.set_visible(False)
    window.cancel_export_button.set_sensitive(False)
    window._update_segment_controls()
    if output is None:
        if batch_result is not None:
            window._export_output_results = tuple(
                result.to_dict() for result in batch_result.results
            )
            completed = sum(result.verified for result in batch_result.results)
            total = len(batch_result.results)
            state_summary = ", ".join(
                f"{result.identity.output_kind}:{result.state}" for result in batch_result.results
            )
            window.export_progress_label.set_text(
                f"Export {completed}/{total} outputs complete: {state_summary}",
            )
            if batch_result.partial_success:
                window._set_status(
                    f"Export partially completed ({completed}/{total} outputs); "
                    "resume to finish pending outputs",
                )
            elif any(
                result.state is ExportResultState.CANCELLED for result in batch_result.results
            ):
                window._set_status("Export cancelled")
            else:
                window._show_error(message)
        else:
            window._export_output_results = ()
            window.export_progress_label.set_text(f"Export failed: {message}")
        if batch_result is not None:
            if not batch_result.partial_success and not any(
                result.state is ExportResultState.CANCELLED for result in batch_result.results
            ):
                try:
                    failure_log = write_export_failure_log(
                        project_path=project_path,
                        destination=destination,
                        message=message,
                        action=post_export_action,
                    )
                except PostExportActionError as error:
                    window._show_error(str(error))
                else:
                    window._set_status(
                        f"{message}; saved failure log {failure_log.name}",
                    )
        elif message == "Export cancelled":
            window._set_status(message)
        else:
            window._show_error(message)
            try:
                failure_log = write_export_failure_log(
                    project_path=project_path,
                    destination=destination,
                    message=message,
                    action=post_export_action,
                )
            except PostExportActionError as error:
                window._show_error(str(error))
            else:
                window._set_status(
                    f"{message}; saved failure log {failure_log.name}",
                )
    else:
        if window.project is not None and frame_rate_policy is not None:
            window.project.set_frame_rate_policy(frame_rate_policy)
        if window.project is not None and upscale_policy is not None:
            window.project.set_upscale_policy(upscale_policy)
        window._set_status(message)
    if (output is not None and (batch_result is None or batch_result.complete)) or (
        batch_result is None and message != "Export cancelled"
    ):
        try:
            execute_post_export_action(post_export_action)
        except PostExportActionError as error:
            window._show_error(str(error))
    if close_after_export:
        application = window.get_application()
        if application is not None:
            application.quit()
    return False
