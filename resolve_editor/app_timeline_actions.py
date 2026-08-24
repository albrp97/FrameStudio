from __future__ import annotations

from pathlib import Path
from typing import Any

from .app_helpers import (
    format_output_duration_label,
)
from .composition import VisualTransform
from .model import ProjectValidationError
from .operations import (
    apply_visual_transform,
    clean_visual_modifications,
    copy_segments,
    copy_visual_transform,
    disable_triplicate,
    enable_triplicate,
    move_segments,
    paste_segments_after_selection,
    split_segment,
)
from .timeline import timeline_zoom_label
from .ui import format_duration


def on_timeline_segment_selected(window: Any, segment_id: str) -> None:
    window.selected_segment_id = segment_id
    if segment_id not in window.selected_segment_ids:
        window.selected_segment_ids = (*window.selected_segment_ids, segment_id)
    window._update_selected_clip_label()
    window._update_segment_controls()


def on_timeline_selection_changed(
    window: Any,
    segment_ids: tuple[str, ...],
) -> None:
    window.selected_segment_ids = segment_ids
    window.selected_segment_id = segment_ids[-1] if segment_ids else None
    window._update_selected_clip_label()
    window._update_segment_controls()


def update_selected_clip_label(window: Any) -> None:
    project = window.project
    if project is None or window.segment_timeline is None or window.selected_segment_id is None:
        window.timeline_selection_label.set_text("No clip selected")
        return
    for index, segment in enumerate(window.segment_timeline.segment_items):
        if segment.segment_id == window.selected_segment_id:
            state = "Deleted" if segment.deleted else "Included"
            source_label = ""
            if segment.source_id is not None:
                try:
                    source = project.source_by_id(segment.source_id)
                except ProjectValidationError:
                    source_label = segment.source_id
                else:
                    source_label = Path(source.path).name
                source_label = f" | source {source_label}"
            selection_label = (
                f" | {len(window.selected_segment_ids)} selected"
                if len(window.selected_segment_ids) > 1
                else ""
            )
            composition_label = ""
            if segment.triplicate is not None and segment.triplicate.enabled:
                composition_label = " | Triplicate: center + left + right"
            elif not segment.visual_transform.is_default:
                composition_label = (
                    f" | Focus: {segment.visual_transform.zoom:.2f}x, "
                    f"X {segment.visual_transform.offset_x:.0f}, "
                    f"Y {segment.visual_transform.offset_y:.0f}"
                )
            window.timeline_selection_label.set_text(
                f"Clip {index + 1} | "
                f"{format_duration(segment.start_seconds)} - "
                f"{format_duration(segment.end_seconds)} | {state}"
                f"{source_label}{selection_label}{composition_label}"
            )
            return
    window.timeline_selection_label.set_text("No clip selected")


def on_timeline_viewport_changed(window: Any, adjustment: Any, _param: Any) -> None:
    page_size = adjustment.get_page_size()
    if page_size > 1.0:
        window.timeline_canvas.set_viewport_width(page_size)


def zoom_timeline(window: Any, direction: int) -> None:
    if direction > 0:
        window.timeline_canvas.zoom_in()
    else:
        window.timeline_canvas.zoom_out()
    window.timeline_zoom_label.set_text(
        timeline_zoom_label(window.timeline_canvas.get_zoom()),
    )
    window._center_timeline_on_playhead()


def fit_timeline_zoom(window: Any) -> None:
    window.timeline_canvas.fit_to_view()
    window.timeline_zoom_label.set_text(
        timeline_zoom_label(window.timeline_canvas.get_zoom()),
    )
    window._center_timeline_on_playhead()


def center_timeline_on_playhead(window: Any) -> None:
    if window.controller is None:
        return
    adjustment = window.timeline_viewport.get_hadjustment()
    page_size = adjustment.get_page_size()
    if page_size <= 1.0:
        return
    position = window.controller.snapshot().position_seconds
    if window.segment_timeline is not None:
        position = window.segment_timeline.edited_to_timeline_position(position)
    clips = window.timeline_canvas.get_content_width()
    if clips <= page_size:
        adjustment.set_value(adjustment.get_lower())
        return
    duration = window.controller.snapshot().duration_seconds
    content_width = window.timeline_canvas.get_content_width()
    position_ratio = position / duration if duration else 0.0
    target = position_ratio * content_width - page_size / 2.0
    lower = adjustment.get_lower()
    upper = max(lower, adjustment.get_upper() - page_size)
    adjustment.set_value(max(lower, min(upper, target)))


def update_segment_controls(window: Any) -> None:
    enabled = not window._export_in_progress
    window.export_button.set_sensitive(window.project is not None and enabled)
    has_selection = (
        window.project is not None
        and window.segment_timeline is not None
        and bool(window.selected_segment_ids)
    )
    for control in (
        window.focus_zoom_spin,
        window.focus_offset_x_spin,
        window.focus_offset_y_spin,
        window.copy_focus_button,
        window.clean_focus_button,
        window.triplicate_button,
    ):
        control.set_sensitive(enabled and has_selection)
    if has_selection:
        try:
            selected = window.segment_timeline.find(window.selected_segment_id)
        except ProjectValidationError:
            selected = None
        if selected is not None:
            transform = selected.visual_transform
            was_updating = getattr(window, "_updating_focus_controls", False)
            window._updating_focus_controls = True
            try:
                window.focus_zoom_spin.set_value(transform.zoom)
                window.focus_offset_x_spin.set_value(transform.offset_x)
                window.focus_offset_y_spin.set_value(transform.offset_y)
            finally:
                window._updating_focus_controls = was_updating
            window.copy_focus_button.set_sensitive(enabled and len(window.selected_segment_ids) > 1)
            all_triplicate = all(
                (
                    window.segment_timeline.find(segment_id).triplicate is not None
                    and window.segment_timeline.find(segment_id).triplicate.enabled
                )
                for segment_id in window.selected_segment_ids
            )
            window.triplicate_button.set_label(
                "Disable triplicate" if all_triplicate else "Enable triplicate",
            )
        else:
            window.copy_focus_button.set_sensitive(False)
    else:
        window.triplicate_button.set_label("Enable triplicate")
        window.copy_focus_button.set_sensitive(False)
    if window.segment_timeline is not None:
        window.timeline_output_label.set_text(
            format_output_duration_label(
                window.segment_timeline.edited_duration_seconds,
            ),
        )
    window.timeline_zoom_label.set_text(
        timeline_zoom_label(window.timeline_canvas.get_zoom()),
    )
    window._update_selected_clip_label()


def _apply_focus_from_controls(window: Any) -> VisualTransform | None:
    if window.project is None or not window.selected_segment_ids:
        window._show_error("Select a clip before changing focus")
        return None
    try:
        transform = apply_visual_transform(
            window.project,
            window.selected_segment_ids,
            zoom=window.focus_zoom_spin.get_value(),
            offset_x=window.focus_offset_x_spin.get_value(),
            offset_y=window.focus_offset_y_spin.get_value(),
        )
    except ProjectValidationError as error:
        window._show_error(str(error))
        return None
    window._refresh_timeline(window.selected_segment_id)
    return transform


def on_focus_control_changed(window: Any, _control: Any) -> None:
    if getattr(window, "_updating_focus_controls", False):
        return
    transform = _apply_focus_from_controls(window)
    if transform is None:
        return
    window._set_status(
        f"Updated focus for {len(window.selected_segment_ids)} selected clip(s): "
        f"{transform.zoom:.2f}x, X {transform.offset_x:.0f}, Y {transform.offset_y:.0f}",
    )


def on_apply_focus_clicked(window: Any, _button: Any) -> None:
    transform = _apply_focus_from_controls(window)
    if transform is None:
        return
    window._set_status(
        f"Applied focus to {len(window.selected_segment_ids)} selected clip(s): "
        f"{transform.zoom:.2f}x, X {transform.offset_x:.0f}, Y {transform.offset_y:.0f}",
    )


def on_clean_visual_clicked(window: Any, _button: Any) -> None:
    if window.project is None or not window.selected_segment_ids:
        window._show_error("Select a clip before cleaning visual modifications")
        return
    try:
        clean_visual_modifications(window.project, window.selected_segment_ids)
    except ProjectValidationError as error:
        window._show_error(str(error))
        return
    window._refresh_timeline(window.selected_segment_id)
    window._set_status(
        f"Cleaned visual modifications from {len(window.selected_segment_ids)} selected clip(s)",
    )


def on_copy_focus_clicked(window: Any, _button: Any) -> None:
    if window.project is None or len(window.selected_segment_ids) < 2:
        window._show_error("Select a source clip and at least one destination clip")
        return
    if window.selected_segment_id is None:
        window._show_error("Select a source clip before copying focus")
        return
    destination_ids = tuple(
        segment_id
        for segment_id in window.selected_segment_ids
        if segment_id != window.selected_segment_id
    )
    try:
        copy_visual_transform(
            window.project,
            window.selected_segment_id,
            destination_ids,
        )
    except ProjectValidationError as error:
        window._show_error(str(error))
        return
    window._refresh_timeline(window.selected_segment_id)
    window._set_status(
        f"Copied focus from the primary clip to {len(destination_ids)} selected clip(s)",
    )


def on_triplicate_clicked(window: Any, _button: Any) -> None:
    if window.project is None or not window.selected_segment_ids:
        window._show_error("Select a clip before changing triplicate mode")
        return
    try:
        selected = tuple(
            window.segment_timeline.find(segment_id) for segment_id in window.selected_segment_ids
        )
        should_disable = all(
            segment.triplicate is not None and segment.triplicate.enabled for segment in selected
        )
        if should_disable:
            disable_triplicate(window.project, window.selected_segment_ids)
        else:
            enable_triplicate(window.project, window.selected_segment_ids)
    except ProjectValidationError as error:
        window._show_error(str(error))
        return
    window._refresh_timeline(window.selected_segment_id)
    window._set_status(
        f"{'Disabled' if should_disable else 'Enabled'} triplicate for "
        f"{len(window.selected_segment_ids)} selected clip(s)",
    )


def on_split_clicked(window: Any, _button: Any) -> None:
    if window.segment_timeline is None or window.controller is None:
        window._show_error("Open a source before splitting segments")
        return
    position = window.controller.snapshot().position_seconds
    try:
        segment_id = window.selected_segment_id
        coordinate = "source"
        if window.segment_timeline.mixed_source or window.segment_timeline.has_explicit_timeline:
            coordinate = "timeline"
            if segment_id is None:
                raise ProjectValidationError("Select a clip before splitting segments")
        _first, second = split_segment(
            window.segment_timeline,
            position,
            segment_id=segment_id,
            coordinate=coordinate,
        )
    except ProjectValidationError as error:
        window._show_error(str(error))
        return
    selected_ids = tuple(
        segment_id
        for segment_id in window.selected_segment_ids
        if segment_id != window.selected_segment_id
    )
    window.selected_segment_ids = (*selected_ids, second.segment_id)
    window.selected_segment_id = second.segment_id
    window._refresh_timeline(second.segment_id)
    window._set_status(f"Split clip at {format_duration(position)}")


def on_delete_segment_clicked(window: Any, _button: Any) -> None:
    if window.segment_timeline is None or not window.selected_segment_ids:
        window._show_error("Select a clip before toggling its deleted state")
        return
    try:
        selected = tuple(
            window.segment_timeline.find(segment_id) for segment_id in window.selected_segment_ids
        )
        deleted = not all(segment.deleted for segment in selected)
        for segment in selected:
            window.segment_timeline.set_deleted(segment.segment_id, deleted)
    except ProjectValidationError as error:
        window._show_error(str(error))
        return
    window._refresh_timeline(window.selected_segment_id)
    noun = "clips" if len(selected) > 1 else "clip"
    window._set_status(f"{'Deleted' if deleted else 'Restored'} selected {noun}")


def move_selected_segments(window: Any, direction: str) -> None:
    if window.project is None or window.segment_timeline is None:
        return
    if not window.selected_segment_ids:
        window._show_error("Select a clip before moving blocks")
        return
    try:
        changed = move_segments(
            window.project,
            window.selected_segment_ids,
            direction,
        )
    except ProjectValidationError as error:
        window._show_error(str(error))
        return
    window._refresh_timeline(window.selected_segment_id)
    window._set_status(
        f"Moved {len(window.selected_segment_ids)} selected block(s) {direction}"
        if changed
        else f"Selected block(s) cannot move {direction}"
    )


def copy_selected_segments(window: Any) -> None:
    if window.project is None or not window.selected_segment_ids:
        window._show_error("Select a clip before copying blocks")
        return
    try:
        window._segment_clipboard = copy_segments(
            window.project,
            window.selected_segment_ids,
        )
    except ProjectValidationError as error:
        window._show_error(str(error))
        return
    window._set_status(f"Copied {len(window._segment_clipboard)} block(s) to the editor clipboard")


def paste_selected_segments(window: Any) -> None:
    if window.project is None or not window._segment_clipboard:
        window._show_error("Copy a clip before pasting")
        return
    try:
        pasted = paste_segments_after_selection(
            window.project,
            window._segment_clipboard,
            window.selected_segment_id,
        )
    except ProjectValidationError as error:
        window._show_error(str(error))
        return
    window.selected_segment_ids = tuple(segment.segment_id for segment in pasted)
    window.selected_segment_id = (
        window.selected_segment_ids[-1] if window.selected_segment_ids else None
    )
    window._refresh_timeline(window.selected_segment_id)
    window._set_status(f"Pasted {len(pasted)} block(s) after the selected block")
