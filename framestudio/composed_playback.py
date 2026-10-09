from __future__ import annotations

import subprocess
import threading
import time
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

from .ffmpeg_playback import (
    FfmpegPlaybackBackend,
    FrameCallback,
    MessageCallback,
    VideoFrame,
    VoidCallback,
    _PreviewRequestCancelled,
)
from .layout_plan import CropPlan, LayoutInterval, LayoutPlan, SlotPlan
from .playback import PlaybackBackendError

PROJECT_TIMEBASE = 1_000_000


def _number(value: float) -> str:
    return f"{value:.6f}".rstrip("0").rstrip(".") or "0"


class FfmpegSynchronizedPlaybackBackend(FfmpegPlaybackBackend):
    """Decode synchronized source frames and assemble the shared layout clock."""

    def __init__(
        self,
        sources: Sequence[tuple[str, Path]],
        layout: LayoutPlan,
        width: int,
        height: int,
        frame_rate: float,
        on_frame: FrameCallback,
        on_error: MessageCallback,
        on_end: VoidCallback,
        ffmpeg_path: str = "ffmpeg",
        on_warning: MessageCallback | None = None,
        preview_cache_size: int = 8,
    ) -> None:
        source_items = tuple((source_id, Path(path)) for source_id, path in sources)
        if not source_items:
            raise ValueError("At least one source is required for synchronized playback")
        if layout.canvas.width != width or layout.canvas.height != height:
            raise ValueError("Synchronized layout canvas must match playback dimensions")
        known_source_ids = {source_id for source_id, _path in source_items}
        missing_source_ids = {
            block.source_id
            for block in layout.included_blocks
            if block.source_id not in known_source_ids
        }
        if missing_source_ids:
            missing = ", ".join(sorted(missing_source_ids))
            raise ValueError(f"Synchronized layout references unknown sources: {missing}")
        super().__init__(
            source_items[0][1],
            width,
            height,
            frame_rate,
            layout.final_duration_seconds,
            on_frame,
            on_error,
            on_end,
            ffmpeg_path=ffmpeg_path,
            audio_preview_enabled=False,
            on_warning=on_warning,
            preview_cache_size=preview_cache_size,
        )
        self._source_items = source_items
        self._layout = layout
        self._playback_thread: threading.Thread | None = None
        self._realtime_run: object | None = None
        self._realtime_decode_process: subprocess.Popen[bytes] | None = None
        self._clock_origin_position = 0.0
        self._clock_origin_time: float | None = None
        self._black_frame = bytes((0, 0, 0, 255)) * (width * height)

    def _has_audio_preview(self) -> bool:
        return False

    def _preview_cache_namespace(self, position_seconds: float) -> tuple[Any, ...]:
        interval = self._interval_at(position_seconds)
        if interval is None:
            return ("black",)
        return (
            interval.start_tick,
            interval.end_tick,
            interval.active_block_ids,
        )

    def _interval_at(self, position_seconds: float) -> LayoutInterval | None:
        tick = max(0, round(float(position_seconds) * PROJECT_TIMEBASE))
        return self._layout.interval_at(tick)

    def _frame_for_interval(
        self,
        position_seconds: float,
        interval: LayoutInterval | None,
        *,
        cancel_check: Callable[[], bool] | None = None,
        process_attribute: str = "_preview_process",
    ) -> VideoFrame:
        if cancel_check is not None and cancel_check():
            raise _PreviewRequestCancelled
        if interval is None or interval.is_black:
            return VideoFrame(
                self._black_frame,
                self.width,
                self.height,
                position_seconds,
                position_seconds,
            )
        command = self._frame_command(position_seconds, interval)
        output, error_output = self._run_decode_command(
            command,
            cancel_check=cancel_check,
            process_attribute=process_attribute,
        )
        if cancel_check is not None and cancel_check():
            raise _PreviewRequestCancelled
        if len(output) != self.frame_size:
            detail = error_output.decode(errors="replace").strip()
            raise PlaybackBackendError(
                detail or "FFmpeg returned an incomplete synchronized preview frame"
            )
        return VideoFrame(
            output,
            self.width,
            self.height,
            position_seconds,
            position_seconds,
        )

    def _frame_command(
        self,
        position_seconds: float,
        interval: LayoutInterval,
    ) -> list[str]:
        position_tick = max(0, round(position_seconds * PROJECT_TIMEBASE))
        slot_ranges: list[tuple[SlotPlan, str, float]] = []
        source_offsets: dict[str, float] = {}
        for slot in interval.slots:
            source_id = slot.block.source_id
            source_tick = slot.block.source_range.source_tick_at(position_tick)
            source_position = source_tick / PROJECT_TIMEBASE
            slot_ranges.append((slot, source_id, source_position))
            source_offsets[source_id] = min(
                source_position,
                source_offsets.get(source_id, source_position),
            )

        command = [
            self.ffmpeg_path,
            "-hide_banner",
            "-loglevel",
            "error",
            "-nostdin",
        ]
        active_source_items = tuple(
            (source_id, source_path)
            for source_id, source_path in self._source_items
            if source_id in source_offsets
        )
        active_source_indexes = {
            source_id: index for index, (source_id, _path) in enumerate(active_source_items)
        }
        for source_id, source_path in active_source_items:
            if source_id not in source_offsets:
                continue
            command.extend(
                [
                    "-ss",
                    _number(source_offsets[source_id]),
                    "-noautorotate",
                    "-i",
                    str(source_path),
                ]
            )

        filters = [f"color=c=black:s={self.width}x{self.height}:r=1:d=1,format=rgba[canvas]"]
        overlay_label = "canvas"
        frame_duration = max(1.0 / self.frame_rate, 0.05)
        for slot_index, (slot, source_id, source_position) in enumerate(slot_ranges):
            source_index = active_source_indexes[source_id]
            source_offset = source_offsets[source_id]
            relative_position = max(0.0, source_position - source_offset)
            trim_label = f"[source_{slot_index}]"
            input_label = f"[{source_index}:v:0]"
            filters.append(
                f"{input_label}trim=start={_number(relative_position)}:"
                f"duration={_number(frame_duration)},setpts=PTS-STARTPTS{trim_label}"
            )
            slot_label = f"[slot_{slot_index}]"
            crops = slot.triplicate_crops if slot.triplicate_crops else (slot.crop,)
            crop_values = tuple(crop for crop in crops if crop is not None)
            if len(crop_values) != len(crops):
                raise PlaybackBackendError(f"Preview slot {slot.block.block_id} has no crop plan")
            if slot.triplicate_crops:
                source_labels = tuple(
                    f"[source_{slot_index}_{role}]" for role in ("left", "center", "right")
                )
                filters.append(f"{trim_label}split=3{''.join(source_labels)}")
                role_labels: list[str] = []
                for role, crop, source_label in zip(
                    ("left", "center", "right"),
                    crop_values,
                    source_labels,
                    strict=True,
                ):
                    role_label = f"[slot_{slot_index}_{role}]"
                    filters.append(self._crop_filter(source_label, crop, role_label))
                    role_labels.append(role_label)
                filters.append(f"{''.join(role_labels)}hstack=inputs=3:shortest=1{slot_label}")
            else:
                filters.append(self._crop_filter(trim_label, crop_values[0], slot_label))
            next_overlay_label = f"composed_{slot_index}"
            filters.append(
                f"[{overlay_label}]{slot_label}overlay="
                f"x={slot.slot.x}:y={slot.slot.y}:eof_action=pass:shortest=1"
                f"[{next_overlay_label}]"
            )
            overlay_label = next_overlay_label
        filters.append(f"[{overlay_label}]format=rgba[output]")
        command.extend(
            [
                "-filter_complex",
                ";".join(filters),
                "-map",
                "[output]",
                "-frames:v",
                "1",
                "-an",
                "-sn",
                "-dn",
                "-f",
                "rawvideo",
                "-pix_fmt",
                "rgba",
                "pipe:1",
            ]
        )
        return command

    @staticmethod
    def _crop_filter(
        input_label: str,
        crop: CropPlan,
        output_label: str,
    ) -> str:
        return (
            f"{input_label}scale={crop.scaled_width}:{crop.scaled_height}:flags=lanczos,"
            f"crop={crop.target.width}:{crop.target.height}:{crop.crop_x}:{crop.crop_y},"
            f"setsar=1,format=rgba{output_label}"
        )

    def _run_decode_command(
        self,
        command: list[str],
        *,
        cancel_check: Callable[[], bool] | None,
        process_attribute: str,
    ) -> tuple[bytes, bytes]:
        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=0,
                start_new_session=True,
            )
        except FileNotFoundError as error:
            raise PlaybackBackendError(
                f"ffmpeg is not installed or not on PATH: {self.ffmpeg_path}"
            ) from error
        except OSError as error:
            raise PlaybackBackendError(
                f"Could not start synchronized preview decode: {error}"
            ) from error
        with self._lock:
            setattr(self, process_attribute, process)
            cancelled = cancel_check is not None and cancel_check()
        if cancelled:
            self._terminate_process_instance(process)
            self._close_process_streams(process)
            with self._lock:
                if getattr(self, process_attribute, None) is process:
                    setattr(self, process_attribute, None)
            raise _PreviewRequestCancelled
        try:
            try:
                output, error_output = process.communicate(timeout=15)
            except subprocess.TimeoutExpired as error:
                self._terminate_process_instance(process)
                raise PlaybackBackendError(
                    "Timed out while rendering the synchronized preview frame"
                ) from error
            except (OSError, ValueError) as error:
                self._terminate_process_instance(process)
                raise PlaybackBackendError(
                    f"Could not render the synchronized preview frame: {error}"
                ) from error
        finally:
            with self._lock:
                if getattr(self, process_attribute, None) is process:
                    setattr(self, process_attribute, None)
        if cancel_check is not None and cancel_check():
            raise _PreviewRequestCancelled
        if process.returncode != 0:
            detail = error_output.decode(errors="replace").strip()
            raise PlaybackBackendError(
                detail or f"FFmpeg synchronized preview exited with status {process.returncode}"
            )
        return output, error_output

    def _clock_position_locked(self, now: float | None = None) -> float:
        if self._clock_origin_time is None:
            return self._position_seconds
        current_time = time.monotonic() if now is None else now
        elapsed = max(0.0, current_time - self._clock_origin_time)
        return min(
            self.duration_seconds,
            max(0.0, self._clock_origin_position + elapsed),
        )

    def current_position(self) -> float:
        with self._lock:
            self._position_seconds = self._clock_position_locked()
            return self._position_seconds

    def _decode_preview_frame(
        self,
        position_seconds: float,
        generation: int | None = None,
    ) -> VideoFrame:
        def is_cancelled() -> bool:
            with self._preview_condition:
                return generation is not None and (
                    generation != self._preview_generation or self._preview_shutdown
                )

        return self._frame_for_interval(
            position_seconds,
            self._interval_at(position_seconds),
            cancel_check=is_cancelled,
            process_attribute="_preview_process",
        )

    def _start_process_locked(self) -> None:
        if self._realtime_run is not None:
            return
        event = threading.Event()
        self._playback_generation += 1
        generation = self._playback_generation
        run = object()
        self._realtime_run = run
        self._stop_event = event
        self._paused = False
        self._clock_origin_position = self._position_seconds
        self._clock_origin_time = time.monotonic()
        worker = threading.Thread(
            target=self._run_realtime,
            args=(run, event, generation, self._position_seconds),
            name="framestudio-editor-synchronized-playback",
            daemon=True,
        )
        self._playback_thread = worker
        try:
            worker.start()
        except RuntimeError:
            self._realtime_run = None
            self._stop_event = None
            self._playback_thread = None
            self._clock_origin_time = None
            raise

    def _run_realtime(
        self,
        run: object,
        event: threading.Event,
        generation: int,
        start_position: float,
    ) -> None:
        frame_interval = 1.0 / self.frame_rate
        ended = False
        try:
            while not event.is_set():
                with self._lock:
                    if self._realtime_run is not run or generation != self._playback_generation:
                        return
                    paused = self._paused
                    position = self._clock_position_locked()
                    self._position_seconds = position
                if paused:
                    event.wait(0.05)
                    continue
                if position >= self.duration_seconds:
                    ended = True
                    return
                started_at = time.monotonic()
                frame = self._frame_for_interval(
                    position,
                    self._interval_at(position),
                    cancel_check=lambda: (
                        event.is_set() or not self._is_current_run(run, generation)
                    ),
                    process_attribute="_realtime_decode_process",
                )
                with self._lock:
                    if (
                        self._realtime_run is not run
                        or event.is_set()
                        or generation != self._playback_generation
                    ):
                        return
                    if self._paused:
                        continue
                    self._position_seconds = self._clock_position_locked()
                    self.on_frame(frame)
                elapsed = time.monotonic() - started_at
                event.wait(max(0.0, frame_interval - elapsed))
        except _PreviewRequestCancelled:
            return
        except PlaybackBackendError as error:
            if not event.is_set() and self._is_current_run(run, generation):
                self._notify_error(str(error))
        finally:
            with self._lock:
                is_current = self._realtime_run is run and generation == self._playback_generation
                if is_current:
                    self._position_seconds = (
                        self.duration_seconds if ended else self._clock_position_locked()
                    )
                    self._clock_origin_position = self._position_seconds
                    self._clock_origin_time = None
                    self._realtime_run = None
                    self._stop_event = None
                    self._paused = False
                    self._playback_thread = None
            if is_current and ended:
                self.on_end()

    def _is_current_run(self, run: object, generation: int) -> bool:
        with self._lock:
            return self._realtime_run is run and generation == self._playback_generation

    def _is_active_playback_locked(self) -> bool:
        return self._realtime_run is not None and not self._paused

    def play(self) -> None:
        self._cancel_preview_requests()
        with self._lock:
            if self._realtime_run is not None and self._paused:
                self._clock_origin_position = self._position_seconds
                self._clock_origin_time = time.monotonic()
                self._paused = False
                return
            if self._realtime_run is None:
                self._start_process_locked()

    def pause(self) -> None:
        with self._lock:
            if self._realtime_run is None or self._paused:
                return
            self._position_seconds = self._clock_position_locked()
            self._clock_origin_position = self._position_seconds
            self._clock_origin_time = None
            self._paused = True

    def _terminate_process(self) -> None:
        with self._lock:
            self._position_seconds = self._clock_position_locked()
            self._clock_origin_position = self._position_seconds
            self._clock_origin_time = None
            event = self._stop_event
            worker = self._playback_thread
            decode_process = self._realtime_decode_process
            self._playback_generation += 1
            self._realtime_run = None
            self._stop_event = None
            self._playback_thread = None
            self._realtime_decode_process = None
            self._paused = False
            if event is not None:
                event.set()
        if decode_process is not None:
            self._terminate_process_instance(decode_process)
        if worker is not None and worker is not threading.current_thread():
            worker.join(timeout=2)

    def seek(self, position_seconds: float) -> None:
        target, was_playing = self._prepare_seek(position_seconds)
        if was_playing:
            self.play()
            return
        frame = self._frame_for_interval(
            target,
            self._interval_at(target),
        )
        with self._lock:
            self._position_seconds = target
            self.on_frame(frame)


__all__ = ["FfmpegSynchronizedPlaybackBackend"]
