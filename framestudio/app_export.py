from __future__ import annotations

import threading
from copy import deepcopy
from pathlib import Path
from typing import Any, Callable

from .app_helpers import format_export_progress_label
from .export import (
    ExportExecutionError,
    ExportPlan,
    ExportPlanningError,
    ExportProgress,
    ExportProgressCallback,
    execute_export,
)
from .export_console import ConsoleProgressReporter
from .export_naming import smart_export_name
from .export_panel import (
    ExportPanelState,
    fps_panel_rows,
    prepare_export_panel,
    upscale_panel_rows,
)
from .export_session import (
    ExportSessionError,
    discard_export_session,
    discover_export_session,
)
from .fps_policy import FrameRatePolicy, policy_source_metadata, rate_choice_labels
from .media import MediaProbeError
from .model import Project
from .operations import export_destination_conflicts_with_project, plan_project_export
from .performance import PerformanceMode, PerformanceModeError
from .post_export import (
    POST_EXPORT_ACTIONS,
    PostExportActionError,
    execute_post_export_action,
    normalize_post_export_action,
    write_export_failure_log,
)
from .upscale_policy import UpscalePolicy


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


def start_export_panel_preparation(
    project: Project,
    folder: Path,
    glib: Any,
    callback: Callable[[ExportPanelState], Any],
    **options: Any,
) -> threading.Thread:
    def prepare() -> None:
        try:
            state = prepare_export_panel(
                deepcopy(project),
                folder,
                **options,
            )
        except (ImportError, OSError, RuntimeError, ValueError) as error:
            state = _export_panel_error_state(
                str(options.get("filename") or ""),
                error,
            )
        glib.idle_add(callback, state)

    worker = threading.Thread(
        target=prepare,
        name="framestudio-editor-export-planning",
        daemon=True,
    )
    worker.start()
    return worker


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
    rate_model = Gtk.StringList.new(
        list(rate_choice_labels(policy_source_metadata(project.sources or (project.source,))))
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
    panel_state: dict[str, Any] = {
        "folder": folder,
        "state": None,
        "generation": 0,
        "closed": False,
        "automatic_filename": True,
        "suggested_filename": suggested_filename,
        "updating_filename": False,
    }

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
        error_label.set_text("")
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
            _set_summary_grid(summary_grid, Gtk, state.display_rows)
            notice_label.set_text(state.notice or "")
            error_label.set_text(state.reason or "")
            confirm.set_sensitive(state.valid)
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
            )
        except (OSError, RuntimeError, ValueError) as error:
            apply_state(_export_panel_error_state(filename or "", error))

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

    def cancel_clicked(_button: Any) -> None:
        panel.close()
        window.export_planning_window = None

    def begin_export(mode: str) -> None:
        state: ExportPanelState = panel_state["state"]
        if not state.valid or state.destination is None or state.policy is None:
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
) -> tuple[Path, ExportPlan]:
    def plan_export_job() -> ExportPlan:
        if analysis_lock is None:
            return plan_project_export(
                project,
                destination,
                frame_rate_policy=frame_rate_policy,
                upscale_policy=upscale_policy,
                cancel_event=cancel_event,
            )
        while not analysis_lock.acquire(timeout=0.05):
            if cancel_event is not None and cancel_event.is_set():
                raise ExportPlanningError("Export cancelled")
        try:
            return plan_project_export(
                project,
                destination,
                frame_rate_policy=frame_rate_policy,
                upscale_policy=upscale_policy,
                cancel_event=cancel_event,
            )
        finally:
            analysis_lock.release()

    with PerformanceMode("on"):
        plan = plan_export_job()
        output = execute_export(
            plan,
            progress_callback=progress_callback,
            cancel_event=cancel_event,
            cancellation_lock=cancellation_lock,
            resume_mode=resume_mode,
        )
    return output, plan


def start_export(
    window: Any,
    destination: Path,
    GLib: Any,
    frame_rate_policy: Any | None = None,
    upscale_policy: UpscalePolicy | None = None,
    post_export_action: str | None = None,
    resume_mode: str = "fresh",
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
    project = window.project
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
            output, plan = run_export_job(
                export_project,
                destination,
                frame_rate_policy=frame_rate_policy,
                upscale_policy=upscale_policy,
                progress_callback=report_progress,
                cancel_event=cancel_event,
                cancellation_lock=cancellation_lock,
                analysis_lock=getattr(window, "_audio_analysis_worker_lock", None),
                resume_mode=resume_mode,
            )
        except (
            ExportExecutionError,
            ExportPlanningError,
            MediaProbeError,
            PerformanceModeError,
        ) as error:
            message = str(error)
            if "export cancelled" in message.casefold():
                message = "Export cancelled"
            GLib.idle_add(finish_export, window, None, message)
            return
        GLib.idle_add(
            finish_export,
            window,
            output,
            f"Exported {output.name} using {plan.route}: {plan.reason}",
            frame_rate_policy,
            upscale_policy,
        )

    threading.Thread(
        target=export_worker,
        name="framestudio-editor-export",
        daemon=True,
    ).start()


def finish_export(
    window: Any,
    output: Path | None,
    message: str,
    frame_rate_policy: FrameRatePolicy | None = None,
    upscale_policy: UpscalePolicy | None = None,
) -> bool:
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
    close_after_export = bool(getattr(window, "_close_after_export", False))
    window._close_after_export = False
    window.cancel_export_button.set_visible(False)
    window.cancel_export_button.set_sensitive(False)
    window._update_segment_controls()
    if output is None:
        window.export_progress_label.set_text(f"Export failed: {message}")
        if message == "Export cancelled":
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
    if output is not None or message != "Export cancelled":
        try:
            execute_post_export_action(post_export_action)
        except PostExportActionError as error:
            window._show_error(str(error))
    if close_after_export:
        application = window.get_application()
        if application is not None:
            application.quit()
    return False
