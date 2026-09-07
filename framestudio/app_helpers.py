from __future__ import annotations

from collections.abc import Mapping, Sequence
from fractions import Fraction
from pathlib import Path
from typing import Any

from .audio import audio_decision_is_stale
from .composition import MAX_ZOOM, MIN_ZOOM
from .export import ExportProgress
from .model import ProjectValidationError, Segment, SegmentTimeline
from .operations import toggle_segment_deleted
from .playback import PlaybackState
from .ui import format_duration

MAX_SOURCES_PER_PROJECT = 32
TIMELINE_SCROLL_STEP_SECONDS = 1.0
TIMELINE_SCROLL_PIXELS = 140.0
FOCUS_ZOOM_SCROLL_STEP = 0.1
FOCUS_OFFSET_SCROLL_STEP = 10.0
FOCUS_SCROLL_FIELDS = ("zoom", "offset_x", "offset_y")
KEYVAL_LEFT = 0xFF51
KEYVAL_RIGHT = 0xFF53
KEYVAL_DELETE = 0xFFFF
KEYVAL_KP_DELETE = 0xFF9F
KEYVAL_KP_SPACE = 0xFF80
KEYCODE_SPACE = 65
KEY_BINDINGS: tuple[tuple[str, str], ...] = (
    ("Space", "Play or pause playback"),
    ("B", "Split the selected clip at the playhead"),
    ("Delete", "Toggle the selected clip between included and deleted"),
    ("Left / Right", "Move the playhead by one output frame"),
    ("Shift+Left / Shift+Right", "Move selected block(s) left or right"),
    ("Ctrl-click", "Add or remove clips from the multi-selection"),
    ("Shift-click", "Select the inclusive range from the current clip"),
    ("Ctrl+C / Ctrl+V", "Copy selected blocks and paste them after the selected block"),
    ("Ctrl+mouse wheel", "Zoom the timeline"),
    ("Ctrl+0", "Fit the timeline to the viewport"),
    ("Alt/Shift+mouse wheel", "Scroll the timeline viewport"),
    ("Horizontal wheel", "Scroll the timeline viewport"),
    ("Normal mouse wheel", "Move the playhead"),
    ("Click/drag timeline", "Seek and preview while dragging"),
    ("Focus controls: Up / Down", "Adjust the focused Zoom, X, or Y field"),
)

__all__ = [
    "KEY_BINDINGS",
    "KEYCODE_SPACE",
    "KEYVAL_DELETE",
    "KEYVAL_KP_DELETE",
    "KEYVAL_KP_SPACE",
    "KEYVAL_LEFT",
    "KEYVAL_RIGHT",
    "MAX_SOURCES_PER_PROJECT",
    "FOCUS_OFFSET_SCROLL_STEP",
    "FOCUS_SCROLL_FIELDS",
    "FOCUS_ZOOM_SCROLL_STEP",
    "TIMELINE_SCROLL_PIXELS",
    "TIMELINE_SCROLL_STEP_SECONDS",
    "_metadata_float",
    "create_play_pause_key_controller",
    "editing_is_locked",
    "focus_control_has_keyboard_focus",
    "format_audio_decisions",
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
    "segment_action_state",
    "timeline_scroll_mode",
    "timeline_scroll_position",
    "toggle_segment_deleted_state",
    "validate_source_selection",
]


def editing_is_locked(window: Any) -> bool:
    if getattr(window, "_export_in_progress", False):
        window._set_status("Editing is disabled while export is in progress")
        return True
    if getattr(window, "_source_load_in_progress", False):
        window._set_status("Editing is disabled while source is loading")
        return True
    return False


def validate_source_selection(
    paths: Sequence[Path],
    max_sources: int = 1,
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


def focus_scroll_value(field: str, value: float, scroll_delta: float) -> float:
    if field not in FOCUS_SCROLL_FIELDS:
        raise ValueError(f"Unknown focus scroll field: {field}")
    step = FOCUS_ZOOM_SCROLL_STEP if field == "zoom" else FOCUS_OFFSET_SCROLL_STEP
    target = float(value) - float(scroll_delta) * step
    if field == "zoom":
        return max(MIN_ZOOM, min(MAX_ZOOM, target))
    return target


def focus_control_has_keyboard_focus(window: object) -> bool:
    for name in ("focus_zoom_spin", "focus_offset_x_spin", "focus_offset_y_spin"):
        control = getattr(window, name, None)
        has_focus = getattr(control, "has_focus", None)
        if callable(has_focus) and has_focus():
            return True
    return False


def is_play_pause_key(keyval: int, keycode: int | None = None) -> bool:
    return keyval in (ord(" "), KEYVAL_KP_SPACE) or keycode == KEYCODE_SPACE


def playback_action_label(state: PlaybackState) -> str:
    return "Pause" if state == PlaybackState.PLAYING else "Play"


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


def format_audio_decisions(
    project,
    analyzing_source_ids: Sequence[str] = (),
) -> str:
    sources = project.sources or (project.source,)
    analyzing = set(analyzing_source_ids)
    labels: list[str] = []
    for source in sources:
        settings = project.source_audio_settings(source.source_id)
        status = settings.get("status", "pending")
        if source.source_id in analyzing and status == "pending":
            status = "analyzing"
        elif audio_decision_is_stale(source, settings):
            status = "stale"
        label = f"{Path(source.path).name}: {status}"
        gain = settings.get("gain_db")
        if status == "ready" and isinstance(gain, (int, float)) and not isinstance(gain, bool):
            label += f" ({float(gain):+.2f} dB)"
        diagnostic = settings.get("diagnostic")
        if status in {"failed", "unsupported"} and isinstance(diagnostic, str) and diagnostic:
            label += f" [{diagnostic}]"
        labels.append(label)
    return "Audio decisions: " + "; ".join(labels)


def format_key_bindings() -> str:
    return "\n".join(f"{shortcut}: {description}" for shortcut, description in KEY_BINDINGS)


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
