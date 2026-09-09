from __future__ import annotations

import threading
from typing import Any

from .app_export import request_close_after_export
from .app_helpers import (
    TIMELINE_SCROLL_PIXELS,
    frame_step_direction,
    frame_step_position,
    is_delete_key,
    is_fit_zoom_key,
    is_frame_step_key,
    is_play_pause_key,
    is_split_key,
    playback_action_label,
    timeline_scroll_mode,
    timeline_scroll_position,
)
from .app_project import _invalidate_audio_analysis
from .ffmpeg_playback import PlaybackBackendError, VideoFrame
from .playback import PlaybackState
from .ui import format_duration


def stop_backend(window: Any, *, asynchronous: bool = False) -> None:
    backend = window.backend
    window._playback_generation = int(getattr(window, "_playback_generation", 0)) + 1
    window.backend = None
    window.controller = None
    if backend is None:
        return
    if not asynchronous:
        backend.close()
        return

    cleanup = threading.Thread(
        target=backend.close,
        name="framestudio-editor-playback-cleanup",
        daemon=True,
    )
    try:
        cleanup.start()
    except RuntimeError:
        backend.close()


def stop_backend_nonblocking(window: Any) -> None:
    stop_backend(window, asynchronous=True)


def on_play_clicked(window: Any, _button: Any) -> None:
    if window.controller is None:
        return
    snapshot = window.controller.snapshot()
    if snapshot.state == PlaybackState.PLAYING:
        window.controller.pause()
    else:
        window.controller.play()
    window._update_playback_controls()
    if window.controller.snapshot().error:
        window._show_error(window.controller.snapshot().error or "Playback failed")


def on_key_pressed(
    window: Any,
    _controller: Any,
    keyval: int,
    keycode: int,
    _state: Any,
    Gdk: Any,
) -> bool:
    state = int(_state)
    shift_pressed = bool(state & int(Gdk.ModifierType.SHIFT_MASK))
    control_pressed = bool(state & int(Gdk.ModifierType.CONTROL_MASK))
    if is_fit_zoom_key(
        keyval,
        _state,
        int(Gdk.ModifierType.CONTROL_MASK),
    ):
        window._fit_timeline_zoom()
        return True
    if is_play_pause_key(keyval, keycode):
        window._on_play_clicked(None)
        return True
    if is_split_key(keyval):
        window._on_split_clicked(None)
        return True
    if is_delete_key(keyval):
        window._on_delete_segment_clicked(None)
        return True
    if is_frame_step_key(keyval):
        direction = frame_step_direction(keyval)
        if direction is None:
            return False

        if shift_pressed and not control_pressed:
            window._move_selected_segments("left" if direction < 0 else "right")
            return True
        window._step_playhead(direction)
        return True
    if control_pressed and keyval in (ord("c"), ord("C")):
        window._copy_selected_segments()
        return True
    if control_pressed and keyval in (ord("v"), ord("V")):
        window._paste_selected_segments()
        return True
    return False


def step_playhead(window: Any, direction: int) -> None:
    if window.controller is None:
        return
    snapshot = window.controller.snapshot()
    if snapshot.state == PlaybackState.PLAYING:
        window.controller.pause()
    position = frame_step_position(
        snapshot.position_seconds,
        direction,
        window.source_frame_rate,
        snapshot.duration_seconds,
    )
    window._seek_timeline(position)


def seek_timeline(window: Any, position_seconds: float) -> bool:
    if window.controller is None:
        return False
    if not window.controller.seek(position_seconds):
        window._show_error(
            window.controller.snapshot().error or "Could not seek source",
        )
        return False
    if window.project is not None:
        window.project.set_playhead(_timeline_position(window))
    window.timeline_canvas.set_playhead(_timeline_position(window))
    window._update_playback_controls()
    return True


def request_timeline_preview(window: Any, position_seconds: float) -> None:
    if window.controller is None or window.backend is None:
        return
    was_playing = window.controller.snapshot().state == PlaybackState.PLAYING
    if was_playing:
        if not window.controller.pause():
            window._show_error(
                window.controller.snapshot().error or "Could not pause source for preview",
            )
            return
    edited_position = (
        window.segment_timeline.timeline_to_edited_position(
            position_seconds,
        )
        if window.segment_timeline is not None
        else position_seconds
    )
    window.controller.update_position(edited_position)
    actual_position = window.controller.snapshot().position_seconds
    if window.project is not None:
        window.project.set_playhead(
            _timeline_position(window, actual_position),
        )
    window.timeline_canvas.set_playhead(_timeline_position(window, actual_position))
    window._update_playback_controls()
    try:
        window.backend.request_preview(edited_position)
    except PlaybackBackendError as error:
        window.controller.report_error(str(error))
        window._show_error(str(error))
        return
    if was_playing and not window.controller.play():
        window._show_error(
            window.controller.snapshot().error or "Could not resume source after preview seek",
        )


def on_timeline_scroll(
    window: Any,
    _controller: Any,
    _delta_x: float,
    delta_y: float,
    Gdk: Any,
) -> bool:
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
        window._zoom_timeline(1 if delta < 0 else -1)
        return True
    adjustment = window.timeline_viewport.get_hadjustment()
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
    if window.controller is None:
        return False
    snapshot = window.controller.snapshot()
    target = timeline_scroll_position(
        snapshot.position_seconds,
        delta_y,
        snapshot.duration_seconds,
    )
    window._seek_timeline(target)
    return True


def on_timeline_view_seek(window: Any, position_seconds: float) -> None:
    window._request_timeline_preview(position_seconds)


def poll_playback(window: Any) -> bool:
    if window.backend is not None and window.controller is not None:
        window.controller.update_position(window.backend.current_position())
        if window.project is not None:
            window.project.set_playhead(_timeline_position(window))
        window._update_playback_controls()
    return True


def update_playback_controls(window: Any) -> None:
    if window.controller is None:
        window.play_button.set_label("Play")
        return
    snapshot = window.controller.snapshot()
    window.play_button.set_label(playback_action_label(snapshot.state))
    window.position_label.set_text(format_duration(snapshot.position_seconds))
    window.timeline_canvas.set_playhead(_timeline_position(window))


def _timeline_position(window: Any, edited_position: float | None = None) -> float:
    position = edited_position
    if position is None:
        if window.controller is None:
            return 0.0
        position = float(window.controller.snapshot().position_seconds)
    if window.segment_timeline is None:
        return float(position)
    return float(window.segment_timeline.edited_to_timeline_position(position))


def on_frame(
    window: Any,
    frame: VideoFrame,
    GLib: Any,
    generation: int | None = None,
) -> None:
    with window._frame_lock:
        if generation is not None and generation != getattr(
            window, "_playback_generation", generation
        ):
            return
        window._latest_frame = frame
        window._latest_frame_generation = generation
        if window._frame_delivery_scheduled:
            return
        window._frame_delivery_scheduled = True
    GLib.idle_add(window._deliver_latest_frame)


def deliver_latest_frame(window: Any, Gdk: Any, GLib: Any) -> bool:
    with window._frame_lock:
        frame = window._latest_frame
        generation = getattr(window, "_latest_frame_generation", None)
        window._latest_frame = None
        window._latest_frame_generation = None
    if frame is None:
        with window._frame_lock:
            window._frame_delivery_scheduled = False
        return False
    if generation is not None and generation != getattr(window, "_playback_generation", generation):
        with window._frame_lock:
            if window._latest_frame is not None:
                return True
            window._frame_delivery_scheduled = False
        return False
    texture = Gdk.MemoryTexture.new(
        frame.width,
        frame.height,
        Gdk.MemoryFormat.R8G8B8A8,
        GLib.Bytes.new(frame.data),
        frame.width * 4,
    )
    window.preview.set_paintable(texture)
    with window._frame_lock:
        if window._latest_frame is not None:
            return True
        window._frame_delivery_scheduled = False
    return False


def on_backend_error(
    window: Any,
    message: str,
    GLib: Any,
    generation: int | None = None,
) -> None:
    GLib.idle_add(window._handle_backend_error, message, generation)


def handle_backend_error(
    window: Any,
    message: str,
    generation: int | None = None,
) -> bool:
    if generation is not None and generation != getattr(window, "_playback_generation", generation):
        return False
    if window.controller is not None:
        window.controller.report_error(message)
    window._show_error(message)
    window._update_playback_controls()
    return False


def on_backend_warning(
    window: Any,
    message: str,
    GLib: Any,
    generation: int | None = None,
) -> None:
    GLib.idle_add(window._handle_backend_warning, message, generation)


def handle_backend_warning(
    window: Any,
    message: str,
    generation: int | None = None,
) -> bool:
    if generation is not None and generation != getattr(window, "_playback_generation", generation):
        return False
    window._set_status(f"Warning: {message}")
    return False


def on_backend_end(
    window: Any,
    GLib: Any,
    generation: int | None = None,
) -> None:
    GLib.idle_add(window._handle_backend_end, generation)


def handle_backend_end(window: Any, generation: int | None = None) -> bool:
    if generation is not None and generation != getattr(window, "_playback_generation", generation):
        return False
    if window.controller is not None:
        window.controller.finish()
        window._update_playback_controls()
    return False


def on_close_request(window: Any, _window: Any) -> bool:
    defer_close = request_close_after_export(window)
    _invalidate_audio_analysis(window)
    window._stop_backend()
    return defer_close


def start_smoke_test(window: Any, GLib: Any) -> bool:
    if window.project is None or window.controller is None:
        window._show_error("Smoke test could not open a source project")
        window._finish_smoke_test()
        return False
    window._on_play_clicked(None)
    GLib.timeout_add(300, window._finish_smoke_test)
    return False


def finish_smoke_test(window: Any, GLib: Any) -> bool:
    if window.controller is not None:
        window.controller.pause()
        duration = window.controller.snapshot().duration_seconds
        position = duration * 0.25
        window.controller.seek(position)
        if window.segment_timeline is not None and 0.0 < position < duration:
            window._on_split_clicked(None)
            window._on_delete_segment_clicked(None)
    if window._smoke_project_path is not None:
        window._save_to(window._smoke_project_path)
    GLib.timeout_add(300, window._end_smoke_test)
    return False


def end_smoke_test(window: Any) -> bool:
    window._stop_backend()
    window.get_application().quit()
    return False
