from __future__ import annotations

import threading
from copy import deepcopy
from pathlib import Path
from typing import Any

from .app_helpers import format_export_progress_label
from .export import (
    ExportExecutionError,
    ExportPlan,
    ExportPlanningError,
    ExportProgress,
    ExportProgressCallback,
    execute_export,
)
from .export_panel import ExportPanelState, prepare_export_panel
from .fps_policy import FrameRatePolicy, policy_source_metadata, rate_choice_labels
from .media import MediaProbeError
from .model import Project
from .operations import export_destination_conflicts_with_project, plan_project_export
from .performance import PerformanceMode, PerformanceModeError
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
        "Upscale eligible sources (SuperUltraCompact)",
    )
    root.append(upscale_enhancement)

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

    initial = prepare_export_panel(
        project,
        folder,
        project_path=window.project_path,
    )
    filename_entry.set_text(initial.filename)
    current_policy = project.get_frame_rate_policy()
    rate_dropdown.set_selected(
        {"lowest": 0, "highest": 1, "custom": 2, "60": 3}[current_policy.choice]
    )
    if current_policy.custom_rate is not None:
        custom_entry.set_text(str(current_policy.custom_rate))
    custom_entry.set_sensitive(current_policy.choice == "custom")
    enhancement.set_active(current_policy.enhancement_enabled)
    upscale_enhancement.set_active(project.get_upscale_policy().enhancement_enabled)
    panel_state: dict[str, Any] = {
        "folder": folder,
        "state": initial,
        "automatic_filename": True,
        "suggested_filename": initial.filename,
        "updating_filename": False,
    }

    def refresh(*_args: Any) -> None:
        selected_choice = _choice_from_index(rate_dropdown.get_selected())
        custom_entry.set_sensitive(selected_choice == "custom")
        custom_value = custom_entry.get_text().strip() or None
        current_filename = filename_entry.get_text().strip() or None
        if panel_state["automatic_filename"]:
            suggestion = prepare_export_panel(
                project,
                panel_state["folder"],
                choice=selected_choice,
                custom_rate=custom_value,
                enhancement_enabled=enhancement.get_active(),
                upscale_enabled=upscale_enhancement.get_active(),
                project_path=window.project_path,
            )
            if suggestion.filename and suggestion.filename != current_filename:
                panel_state["updating_filename"] = True
                filename_entry.set_text(suggestion.filename)
                panel_state["updating_filename"] = False
            panel_state["suggested_filename"] = suggestion.filename
            current_filename = suggestion.filename or current_filename
        state = prepare_export_panel(
            project,
            panel_state["folder"],
            choice=selected_choice,
            custom_rate=custom_value,
            enhancement_enabled=enhancement.get_active(),
            upscale_enabled=upscale_enhancement.get_active(),
            filename=filename_entry.get_text().strip() or None,
            project_path=window.project_path,
        )
        panel_state["state"] = state
        if state.destination is not None:
            folder_label.set_text(str(state.destination.parent))
        _set_summary_grid(summary_grid, Gtk, state.display_rows)
        notice_label.set_text(state.notice or "")
        reason = state.reason or ""
        error_label.set_text(reason)
        confirm.set_sensitive(state.valid)

    def filename_changed(_entry: Any) -> None:
        if not panel_state["updating_filename"]:
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

    def confirm_clicked(_button: Any) -> None:
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
        )

    choose_folder.connect("clicked", choose_folder_clicked)
    cancel.connect("clicked", cancel_clicked)
    confirm.connect("clicked", confirm_clicked)
    rate_dropdown.connect("notify::selected", refresh)
    custom_entry.connect("changed", refresh)
    enhancement.connect("toggled", refresh)
    upscale_enhancement.connect("toggled", refresh)
    filename_entry.connect("changed", filename_changed)
    panel.connect("close-request", lambda _window: _clear_export_panel(window))
    refresh()
    panel.present()


def _clear_export_panel(window: Any) -> bool:
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


def run_export_job(
    project: Project,
    destination: Path,
    *,
    frame_rate_policy: FrameRatePolicy | None,
    progress_callback: ExportProgressCallback | None,
    cancel_event: threading.Event | None,
    cancellation_lock: threading.Lock | None = None,
    upscale_policy: UpscalePolicy | None = None,
) -> tuple[Path, ExportPlan]:
    with PerformanceMode("on"):
        plan = plan_project_export(
            project,
            destination,
            frame_rate_policy=frame_rate_policy,
            upscale_policy=upscale_policy,
        )
        output = execute_export(
            plan,
            progress_callback=progress_callback,
            cancel_event=cancel_event,
            cancellation_lock=cancellation_lock,
        )
    return output, plan


def start_export(
    window: Any,
    destination: Path,
    GLib: Any,
    frame_rate_policy: Any | None = None,
    upscale_policy: UpscalePolicy | None = None,
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
    project = window.project
    export_project = deepcopy(project)
    window._export_project_snapshot = export_project
    cancel_event = threading.Event()
    cancellation_lock = threading.Lock()
    window._export_cancel_event = cancel_event
    window._export_cancellation_lock = cancellation_lock
    window._export_in_progress = True
    window._update_segment_controls()
    reset_export_progress(window)
    window._set_status("Planning and exporting edited video...")

    def export_worker() -> None:
        def report_progress(progress: ExportProgress) -> None:
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
        name="resolve-editor-export",
        daemon=True,
    ).start()


def finish_export(
    window: Any,
    output: Path | None,
    message: str,
    frame_rate_policy: FrameRatePolicy | None = None,
    upscale_policy: UpscalePolicy | None = None,
) -> bool:
    window._export_in_progress = False
    window._export_cancel_event = None
    window._export_cancellation_lock = None
    window._export_project_snapshot = None
    window.cancel_export_button.set_visible(False)
    window.cancel_export_button.set_sensitive(False)
    window._update_segment_controls()
    if output is None:
        window.export_progress_label.set_text(f"Export failed: {message}")
        if message == "Export cancelled":
            window._set_status(message)
        else:
            window._show_error(message)
    else:
        if window.project is not None and frame_rate_policy is not None:
            window.project.set_frame_rate_policy(frame_rate_policy)
        if window.project is not None and upscale_policy is not None:
            window.project.set_upscale_policy(upscale_policy)
        window._set_status(message)
    return False
