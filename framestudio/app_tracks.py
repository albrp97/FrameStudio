from __future__ import annotations

import math
from collections.abc import Sequence
from fractions import Fraction
from pathlib import Path
from typing import Any, Callable

from .app_helpers import (
    editing_is_locked,
    route_timeline_scroll,
    timeline_scroll_position,
)
from .app_playback import request_timeline_preview, stop_backend_nonblocking
from .app_project import (
    _invalidate_audio_analysis,
    _validate_project_sources,
)
from .app_project import (
    attach_project as _attach_playback_project,
)
from .app_project import (
    refresh_playback_backend as _refresh_playback_backend,
)
from .media import MediaProbeError, probe_media
from .model import ABSOLUTE_TIMING_MODE, Project, ProjectValidationError, SourceReference
from .persistence import ProjectPersistenceError, load_project
from .ui import format_duration

PREVIEW_UNAVAILABLE_MESSAGE = (
    "Editing only: preview unavailable until synchronized playback integration (T120)"
)


def is_absolute_project(project: Project | None) -> bool:
    return (
        project is not None
        and project.segment_timeline is not None
        and project.timeline.timing_mode == ABSOLUTE_TIMING_MODE
    )


def _source_frame_rate(project: Project) -> float:
    value = project.source.metadata.get("frame_rate")
    if value is None or isinstance(value, bool) or not isinstance(value, (int, float, str)):
        raise ProjectValidationError("Source metadata frame_rate is invalid")
    try:
        parsed = float(Fraction(str(value)))
    except (TypeError, ValueError, ZeroDivisionError, OverflowError):
        raise ProjectValidationError("Source metadata frame_rate is invalid") from None
    if not math.isfinite(parsed) or parsed <= 0:
        raise ProjectValidationError("Source metadata frame_rate is invalid")
    return parsed


def _stop_preview(window: Any) -> None:
    invalidate = getattr(window, "_invalidate_audio_analysis", None)
    if callable(invalidate):
        invalidate()
    else:
        _invalidate_audio_analysis(window)
    stop = getattr(window, "_stop_backend_nonblocking", None)
    if callable(stop):
        stop()
    else:
        stop_backend_nonblocking(window)
    window.backend = None
    window.controller = None
    window._latest_frame = None
    window.preview.set_paintable(None)


def _selection_for_timeline(
    timeline: Any,
    selected_segment_id: str | None,
    selected_segment_ids: Sequence[str],
) -> tuple[str | None, tuple[str, ...]]:
    known_ids = {segment.segment_id for segment in timeline.segment_items}
    selected = tuple(segment_id for segment_id in selected_segment_ids if segment_id in known_ids)
    primary = selected_segment_id if selected_segment_id in known_ids else None
    if primary is not None and primary not in selected:
        selected = (*selected, primary)
    if primary is None and selected:
        primary = selected[-1]
    if primary is None and timeline.segment_items:
        primary = timeline.segment_items[0].segment_id
        selected = (primary,)
    return primary, selected


def _update_editing_position(window: Any) -> None:
    position = 0.0 if window.project is None else window.project.playhead_seconds
    window.position_label.set_text(format_duration(position))
    window.timeline_canvas.set_playhead(position)


def _disable_preview_controls(window: Any) -> None:
    window.play_button.set_label("Play")
    window.play_button.set_sensitive(False)
    window.preview.set_tooltip_text(PREVIEW_UNAVAILABLE_MESSAGE)


def attach_editing_only(
    window: Any,
    project: Project,
    project_path: Path | None,
    *,
    announce: bool = True,
) -> None:
    timeline = project.timeline
    if timeline.timing_mode != ABSOLUTE_TIMING_MODE:
        raise ProjectValidationError("Editing-only attachment requires an absolute timeline")
    _attach_playback_project(window, project, project_path)
    refresh_track_controls(window)
    if announce:
        window._set_status("Synchronized silent preview ready")


def refresh_editing_only(window: Any, selected_segment_id: str | None = None) -> None:
    if window.project is None or not is_absolute_project(window.project):
        return
    if selected_segment_id is not None:
        window.selected_segment_id = selected_segment_id
    attach_editing_only(
        window,
        window.project,
        getattr(window, "project_path", None),
        announce=True,
    )


def seek_editing_only(window: Any, position_seconds: float) -> bool:
    if not is_absolute_project(window.project):
        return False
    timeline = window.project.timeline
    position = max(0.0, min(timeline.timeline_duration_seconds, float(position_seconds)))
    return request_timeline_preview(window, position)


def on_timeline_scroll_editing_only(
    window: Any,
    controller: Any,
    delta_x: float,
    delta_y: float,
    Gdk: Any,
) -> bool:
    mode = route_timeline_scroll(window, controller, delta_x, delta_y, Gdk)
    if mode != "playhead":
        return mode != "none"
    timeline = window.project.timeline
    if timeline.timeline_duration_seconds <= 0:
        target = 0.0
    else:
        target = timeline_scroll_position(
            window.project.playhead_seconds,
            delta_y,
            timeline.timeline_duration_seconds,
        )
    return seek_editing_only(window, target)


def refresh_playback_backend(window: Any, *, force: bool = False) -> None:
    if is_absolute_project(window.project):
        _refresh_playback_backend(window, force=force)


def refresh_track_controls(window: Any) -> None:
    selector = getattr(window, "track_selector", None)
    if selector is None:
        return
    timeline = getattr(window, "segment_timeline", None)
    track_ids = (
        ("track-1",)
        if timeline is None
        else tuple(timeline.track_ids if timeline.tracks is not None else ("track-1",))
    )
    string_list = window._Gtk.StringList.new(list(track_ids))
    window._updating_track_selector = True
    try:
        current_model = selector.get_model()
        same_model = (
            current_model is not None
            and current_model.get_n_items() == len(track_ids)
            and all(
                current_model.get_string(index) == track_id
                for index, track_id in enumerate(track_ids)
            )
        )
        if not same_model:
            selector.set_model(string_list)
        active_id = (
            timeline.active_track_id
            if timeline is not None and timeline.tracks is not None
            else track_ids[0]
        )
        selected_index = max(0, track_ids.index(active_id))
        if selector.get_selected() != selected_index:
            selector.set_selected(selected_index)
    finally:
        window._updating_track_selector = False
    absolute = is_absolute_project(getattr(window, "project", None))
    selector.set_sensitive(absolute)
    window.add_track_button.set_sensitive(
        getattr(window, "project", None) is not None and not editing_is_locked(window)
    )
    window.remove_track_button.set_sensitive(absolute and not editing_is_locked(window))


def set_active_track(window: Any, track_id: str) -> None:
    if not is_absolute_project(window.project):
        return
    try:
        window.project.timeline.set_active_track(track_id)
    except ProjectValidationError as error:
        window._show_error(str(error))
        return
    refresh_track_controls(window)
    window.timeline_canvas.queue_draw()


def _on_conversion_response(window: Any, dialog: Any, response_id: int) -> None:
    if getattr(window, "_track_confirmation_dialog", None) is dialog:
        window._track_confirmation_dialog = None
    dialog.close()
    if int(response_id) != 1:
        return
    try:
        _source_frame_rate(window.project)
        window.project.convert_to_synchronized(confirm=True)
        window.project.timeline.add_track()
    except ProjectValidationError as error:
        window._show_error(str(error))
        return
    refresh_editing_only(window)
    window._set_status("Synchronized silent preview ready")


def request_add_track(window: Any, Gtk: Any) -> None:
    if editing_is_locked(window) or window.project is None:
        return
    timeline = window.project.timeline
    if timeline.timing_mode != ABSOLUTE_TIMING_MODE:
        dialog = Gtk.MessageDialog(
            transient_for=window,
            modal=True,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.NONE,
            text=(
                "Convert this project to synchronized tracks?\n\n"
                "Track editing uses absolute timeline positions. "
                "The existing ordered clips will be preserved."
            ),
        )
        dialog.add_button("Cancel", 0)
        dialog.add_button("Convert and add track", 1)
        dialog.connect(
            "response",
            lambda response_dialog, response_id: _on_conversion_response(
                window,
                response_dialog,
                response_id,
            ),
        )
        window._track_confirmation_dialog = dialog
        dialog.present()
        return
    try:
        timeline.add_track()
    except ProjectValidationError as error:
        window._show_error(str(error))
        return
    refresh_editing_only(window)
    window._set_status("Synchronized silent preview ready")


def request_remove_active_track(window: Any) -> None:
    if editing_is_locked(window) or not is_absolute_project(window.project):
        return
    try:
        window.project.timeline.remove_track(window.project.timeline.active_track_id or "")
    except ProjectValidationError as error:
        window._show_error(str(error))
        return
    refresh_editing_only(window)
    window._set_status("Synchronized silent preview ready")


def load_absolute_project_path(
    window: Any,
    path: Path,
) -> bool:
    try:
        project = load_project(path)
    except ProjectPersistenceError as error:
        window._show_error(str(error))
        return False
    if not _validate_project_sources(window, project):
        return False
    if not is_absolute_project(project):
        return False
    try:
        attach_editing_only(window, project, path)
    except ProjectValidationError as error:
        window._show_error(str(error))
        return False
    window._set_status(f"Reopened editor project: {path.name}")
    return False


def load_project_path(
    window: Any,
    path: Path,
    legacy_loader: Callable[[Path], bool],
) -> bool:
    try:
        project = load_project(path)
    except ProjectPersistenceError as error:
        window._show_error(str(error))
        return False
    if is_absolute_project(project):
        if not _validate_project_sources(window, project):
            return False
        try:
            attach_editing_only(window, project, path)
        except ProjectValidationError as error:
            window._show_error(str(error))
            return False
        window._set_status(f"Reopened editor project: {path.name}")
        return False
    return legacy_loader(path)


def load_sources(
    window: Any,
    paths: Path | Sequence[Path],
) -> bool:
    if editing_is_locked(window) or not is_absolute_project(window.project):
        return False
    selected_paths = (
        (Path(paths),) if isinstance(paths, Path) else tuple(Path(path) for path in paths)
    )
    if not selected_paths:
        window._show_error("At least one source is required")
        return False
    window._source_load_in_progress = True
    window._update_segment_controls()
    try:
        sources: list[SourceReference] = []
        for path in selected_paths:
            probe = probe_media(path)
            sources.append(SourceReference.from_path(path, probe.metadata()))
        window.project.append_sources(tuple(sources))
        refresh_editing_only(window)
        names = ", ".join(path.name for path in selected_paths)
        window._set_status(f"Added source video(s): {names}")
    except (MediaProbeError, ProjectValidationError, ValueError) as error:
        window._show_error(str(error))
    finally:
        window._source_load_in_progress = False
        window._update_segment_controls()
    return False
