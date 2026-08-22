from __future__ import annotations

import threading
from pathlib import Path
from typing import Any

from .app_helpers import format_export_progress_label
from .export import (
    ExportExecutionError,
    ExportPlanningError,
    ExportProgress,
    execute_export,
)
from .media import MediaProbeError
from .operations import export_destination_conflicts_with_project, plan_project_export


def on_export_clicked(window: Any, Gtk: Any) -> None:
    if window.project is None or window.segment_timeline is None:
        window._show_error("Open a source before exporting")
        return
    if window._export_in_progress:
        return
    dialog = Gtk.FileDialog.new()
    dialog.set_title("Export edited video")
    dialog.set_initial_name(f"{Path(window.project.source.path).stem}-edited.mp4")
    dialog.save(window, None, window._on_export_dialog_done, None)


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


def update_export_progress(window: Any, progress: ExportProgress) -> bool:
    window.export_progress_bar.set_fraction(
        max(0.0, min(1.0, progress.percent / 100.0)),
    )
    window.export_progress_bar.set_text(f"{progress.percent:.1f}%")
    window.export_progress_label.set_text(format_export_progress_label(progress))
    return False


def start_export(window: Any, destination: Path, GLib: Any) -> None:
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
    window._export_in_progress = True
    window._update_segment_controls()
    reset_export_progress(window)
    window._set_status("Planning and exporting edited video...")

    def export_worker() -> None:
        def report_progress(progress: ExportProgress) -> None:
            GLib.idle_add(update_export_progress, window, progress)

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
                finish_export,
                window,
                None,
                str(error),
            )
            return
        GLib.idle_add(
            finish_export,
            window,
            output,
            f"Exported {output.name} using {plan.route}: {plan.reason}",
        )

    threading.Thread(
        target=export_worker,
        name="resolve-editor-export",
        daemon=True,
    ).start()


def finish_export(window: Any, output: Path | None, message: str) -> bool:
    window._export_in_progress = False
    window._update_segment_controls()
    if output is None:
        window.export_progress_label.set_text(f"Export failed: {message}")
        window._show_error(message)
    else:
        window._set_status(message)
    return False
