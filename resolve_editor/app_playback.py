from __future__ import annotations

from typing import Any

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
from .ffmpeg_playback import PlaybackBackendError, VideoFrame
from .playback import PlaybackState
from .ui import format_duration


def stop_backend(window: Any) -> None:
    if window.backend is not None:
        window.backend.close()
    window.backend = None
    window.controller = None


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
        window.project.set_playhead(window.controller.snapshot().position_seconds)
    window.timeline_canvas.set_playhead(window.controller.snapshot().position_seconds)
    window._update_playback_controls()
    return True


def request_timeline_preview(window: Any, position_seconds: float) -> None:
    if window.controller is None or window.backend is None:
        return
    if window.controller.snapshot().state == PlaybackState.PLAYING:
        if not window.controller.pause():
            window._show_error(
                window.controller.snapshot().error or "Could not pause source for preview",
            )
            return
    window.controller.update_position(position_seconds)
    if window.project is not None:
        window.project.set_playhead(position_seconds)
    window.timeline_canvas.set_playhead(position_seconds)
    window._update_playback_controls()
    try:
        window.backend.request_preview(position_seconds)
    except PlaybackBackendError as error:
        window.controller.report_error(str(error))
        window._show_error(str(error))


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
            window.project.set_playhead(window.controller.snapshot().position_seconds)
        window._update_playback_controls()
    return True


def update_playback_controls(window: Any) -> None:
    if window.controller is None:
        window.play_button.set_label("Play")
        return
    snapshot = window.controller.snapshot()
    window.play_button.set_label(playback_action_label(snapshot.state))
    window.position_label.set_text(format_duration(snapshot.position_seconds))
    window.timeline_canvas.set_playhead(snapshot.position_seconds)


def on_frame(window: Any, frame: VideoFrame, GLib: Any) -> None:
    with window._frame_lock:
        window._latest_frame = frame
        if window._frame_delivery_scheduled:
            return
        window._frame_delivery_scheduled = True
    GLib.idle_add(window._deliver_latest_frame)


def deliver_latest_frame(window: Any, Gdk: Any, GLib: Any) -> bool:
    with window._frame_lock:
        frame = window._latest_frame
        window._latest_frame = None
    if frame is None:
        with window._frame_lock:
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


def on_backend_error(window: Any, message: str, GLib: Any) -> None:
    GLib.idle_add(window._handle_backend_error, message)


def handle_backend_error(window: Any, message: str) -> bool:
    if window.controller is not None:
        window.controller.report_error(message)
    window._show_error(message)
    window._update_playback_controls()
    return False


def on_backend_end(window: Any, GLib: Any) -> None:
    GLib.idle_add(window._handle_backend_end)


def handle_backend_end(window: Any) -> bool:
    if window.controller is not None:
        window.controller.finish()
        window._update_playback_controls()
    return False


def on_close_request(window: Any, _window: Any) -> bool:
    window._stop_backend()
    return False


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
