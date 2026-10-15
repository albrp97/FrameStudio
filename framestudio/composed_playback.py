from __future__ import annotations

import math
import shutil
import subprocess
import threading
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
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
from .precise_preview import (
    PrecisePreviewClient,
    PreviewDependencyUnavailable,
    PreviewUnsupportedSource,
)

PROJECT_TIMEBASE = 1_000_000


def _number(value: float) -> str:
    return f"{value:.6f}".rstrip("0").rstrip(".") or "0"


@dataclass
class _RealtimeDecoder:
    process: subprocess.Popen[bytes]
    interval: LayoutInterval
    origin: float
    generation: int
    stderr: list[bytes]
    stderr_thread: threading.Thread
    next_frame_index: int = 0


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
        preview_backend: str = "ffmpeg",
    ) -> None:
        if preview_backend not in {"ffmpeg", "auto", "cpu", "cuda"}:
            raise PlaybackBackendError("Invalid synchronized preview backend")
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
        self._source_paths = dict(source_items)
        self._layout = layout
        self._playback_thread: threading.Thread | None = None
        self._realtime_run: object | None = None
        self._realtime_decode_process: subprocess.Popen[bytes] | None = None
        self._realtime_decoder: _RealtimeDecoder | None = None
        self._decoder_starts = 0
        self._decoded_frames = 0
        self._dropped_frames = 0
        self._clock_origin_position = 0.0
        self._clock_origin_time: float | None = None
        self._black_frame = bytes((0, 0, 0, 255)) * (width * height)
        self._precise_preview = (
            None if preview_backend == "ffmpeg" else PrecisePreviewClient(preview_backend)
        )
        self._precise_dependency_missing = False
        self._precise_diagnostic_key: object = None
        self.precise_preview_diagnostics: dict[str, Any] = {}

    def stop(self) -> None:
        client = getattr(self, "_precise_preview", None)
        if client is not None:
            self.release_preview_resources()
        super().stop()

    def release_preview_resources(self) -> None:
        """Reap preview decoders without changing the playhead, pause state or cache."""
        client = self._precise_preview
        self._cancel_preview_requests()
        try:
            self._terminate_process(preserve_pause=True)
        finally:
            # Generation fences precede I/O interruption. No backend/UI lock
            # is held while terminating and reaping either decoder.
            if client is not None:
                client.interrupt()

    def close(self) -> None:
        client = getattr(self, "_precise_preview", None)
        if client is not None:
            with self._preview_condition:
                self._preview_shutdown = True
                self._preview_generation += 1
                self._preview_request = None
                self._preview_condition.notify_all()
            client.close()
        super().close()

    def precise_preview_stats(self) -> dict[str, Any]:
        diagnostics = dict(self.precise_preview_diagnostics)
        physical = diagnostics.get("physical_frames", [])
        engines = tuple(dict.fromkeys(frame["engine"] for frame in physical))
        process = (
            self._precise_preview.snapshot()
            if self._precise_preview is not None
            else {"helper_pid": None, "requests": 0, "closed": self._preview_shutdown}
        )
        return {
            **diagnostics,
            "selected_engine": diagnostics.get(
                "selected_engine",
                engines[0] if len(engines) == 1 else ("mixed" if engines else "ffmpeg"),
            ),
            "fallback_reason": diagnostics.get(
                "reason", "; ".join(dict.fromkeys(frame["reason"] for frame in physical))
            ),
            "last_request_contexts": diagnostics.get("contexts", 0),
            "contexts": diagnostics.get("contexts", 0) if process["helper_pid"] is not None else 0,
            "last_request_composition_contexts": diagnostics.get("composition_contexts", 0),
            "composition_contexts": (
                diagnostics.get("composition_contexts", 0)
                if process["helper_pid"] is not None
                else 0
            ),
            **process,
        }

    def _has_audio_preview(self) -> bool:
        return False

    def _preview_cache_namespace(self, position_seconds: float) -> tuple[Any, ...]:
        interval = self._interval_at(position_seconds)
        if interval is None:
            return ("black",)
        namespace: tuple[Any, ...] = (
            interval.start_tick,
            interval.end_tick,
            interval.active_block_ids,
        )
        if self._precise_preview is not None:
            paths = self._source_paths
            identities: list[tuple[Any, ...]] = []
            for source_id in dict.fromkeys(slot.block.source_id for slot in interval.slots):
                path = paths[source_id]
                try:
                    stat = path.stat()
                    identities.append(
                        (
                            str(path.resolve()),
                            stat.st_dev,
                            stat.st_ino,
                            stat.st_size,
                            stat.st_mtime_ns,
                        )
                    )
                except OSError:
                    identities.append((str(path.resolve()), "unavailable"))
            namespace += (tuple(identities),)
        return namespace

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
        if process_attribute == "_realtime_decode_process":
            if interval is not None and not interval.is_black:
                return self._read_realtime_frame(position_seconds, interval, cancel_check)
            self._release_realtime_decoder()
        if interval is None or interval.is_black:
            self.precise_preview_diagnostics = {
                **{
                    key: self.precise_preview_diagnostics[key]
                    for key in (
                        "contexts",
                        "context_opens",
                        "context_evictions",
                        "composition_contexts",
                        "composition_opens",
                        "composition_reuses",
                    )
                    if key in self.precise_preview_diagnostics
                },
                "selected_engine": "black",
                "reason": "Black gap; no native decode required",
            }
            return VideoFrame(
                self._black_frame,
                self.width,
                self.height,
                position_seconds,
                position_seconds,
            )
        if (
            process_attribute == "_preview_process"
            and self._precise_preview is not None
            and not self._precise_dependency_missing
        ):
            if shutil.which(self.ffmpeg_path) is None:
                raise PlaybackBackendError(
                    f"ffmpeg is not installed or not on PATH: {self.ffmpeg_path}"
                )
            try:
                return self._precise_frame(position_seconds, interval, cancel_check)
            except PreviewDependencyUnavailable as error:
                self._precise_dependency_missing = True
                self.precise_preview_diagnostics = {
                    "selected_engine": "ffmpeg",
                    "reason": str(error),
                }
                self._precise_warning(("missing-av",), str(error))
            except PreviewUnsupportedSource as error:
                self.precise_preview_diagnostics = {
                    **self._precise_preview.last_diagnostics,
                    "selected_engine": "ffmpeg",
                    "reason": str(error),
                }
                self._precise_warning(("unsupported", str(error)), str(error))
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

    def _precise_warning(self, key: object, message: str) -> None:
        if key != self._precise_diagnostic_key:
            self._precise_diagnostic_key = key
            self.on_warning(message)

    def _precise_frame(
        self,
        position_seconds: float,
        interval: LayoutInterval,
        cancel_check: Callable[[], bool] | None,
    ) -> VideoFrame:
        if self._precise_preview is None:
            raise PlaybackBackendError("The precise preview runtime is not selected")
        project_tick = max(0, round(position_seconds * PROJECT_TIMEBASE))
        paths = self._source_paths
        slots = []
        for slot in interval.slots:
            crops = slot.triplicate_crops or (slot.crop,)
            slots.append(
                {
                    "path": str(paths[slot.block.source_id].resolve()),
                    "source_tick": slot.block.source_range.source_tick_at(project_tick),
                    "x": slot.slot.x,
                    "y": slot.slot.y,
                    "crops": [
                        {
                            "scaled_width": crop.scaled_width,
                            "scaled_height": crop.scaled_height,
                            "width": crop.target.width,
                            "height": crop.target.height,
                            "crop_x": crop.crop_x,
                            "crop_y": crop.crop_y,
                        }
                        for crop in crops
                        if crop is not None
                    ],
                }
            )
        pixels, diagnostics = self._precise_preview.render(
            {
                "project_tick": project_tick,
                "width": self.width,
                "height": self.height,
                "slots": slots,
            },
            cancelled=cancel_check,
        )
        self.precise_preview_diagnostics = diagnostics
        physical = diagnostics["physical_frames"]
        key = tuple((frame["engine"], frame["reason"]) for frame in physical)
        self._precise_warning(
            key,
            "Exact preview: "
            + "; ".join(
                dict.fromkeys(f"{frame['engine']}: {frame['reason']}" for frame in physical)
            ),
        )
        first = physical[0]
        actual_source_seconds = (
            first["pts"] * first["time_base_num"] / first["time_base_den"]
            - first["origin_tick"] / PROJECT_TIMEBASE
        )
        actual_project_seconds = (
            position_seconds + actual_source_seconds - first["source_tick"] / PROJECT_TIMEBASE
        )
        return VideoFrame(pixels, self.width, self.height, position_seconds, actual_project_seconds)

    def _frame_command(
        self,
        position_seconds: float,
        interval: LayoutInterval,
    ) -> list[str]:
        return self._video_command(position_seconds, interval)

    def _video_command(
        self,
        position_seconds: float,
        interval: LayoutInterval,
        *,
        continuous: bool = False,
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
            (source_id, self._source_paths[source_id]) for source_id in source_offsets
        )
        active_source_indexes = {
            source_id: index for index, (source_id, _path) in enumerate(active_source_items)
        }
        if continuous:
            command.extend(["-filter_complex_threads", "2"])
        for source_id, source_path in active_source_items:
            if source_id not in source_offsets:
                continue
            if continuous:
                # Bound the aggregate decoder budget, rather than multiplying
                # FFmpeg's auto-sized frame queues by the number of slots.
                command.extend(["-threads", str(max(1, 4 // len(active_source_items)))])
            command.extend(
                [
                    "-ss",
                    _number(source_offsets[source_id]),
                    "-noautorotate",
                    "-i",
                    str(source_path),
                ]
            )

        remaining = max(
            1.0 / self.frame_rate,
            interval.end_tick / PROJECT_TIMEBASE - position_seconds,
        )
        canvas_rate = _number(self.frame_rate) if continuous else "1"
        canvas_duration = _number(remaining) if continuous else "1"
        filters = [
            f"color=c=black:s={self.width}x{self.height}:"
            f"r={canvas_rate}:d={canvas_duration},format=rgba[canvas]"
        ]
        overlay_label = "canvas"
        frame_duration = remaining if continuous else max(1.0 / self.frame_rate, 0.05)
        for slot_index, (slot, source_id, source_position) in enumerate(slot_ranges):
            source_index = active_source_indexes[source_id]
            source_offset = source_offsets[source_id]
            relative_position = max(0.0, source_position - source_offset)
            trim_label = f"[source_{slot_index}]"
            input_label = f"[{source_index}:v:0]"
            trim_end = "" if continuous else f":duration={_number(frame_duration)}"
            filters.append(
                f"{input_label}trim=start={_number(relative_position)}"
                f"{trim_end},setpts=PTS-STARTPTS{trim_label}"
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
            if continuous:
                # The finite canvas/frame count bounds the interval; do not cut
                # away the next native frame needed by a fractional seek.
                # At true media EOF cover at most one fractional source frame,
                # without repeating a truncated source indefinitely.
                padded_label = f"[padded_{slot_index}]"
                filters.append(f"{slot_label}tpad=stop_mode=clone:stop=1{padded_label}")
                slot_label = padded_label
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
                str(max(1, math.ceil(remaining * self.frame_rate))) if continuous else "1",
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
        if continuous:
            command[-1:-1] = ["-threads:v", "1"]
        return command

    def _release_realtime_decoder(self, expected: _RealtimeDecoder | None = None) -> None:
        with self._lock:
            decoder = self._realtime_decoder
            if decoder is None or (expected is not None and decoder is not expected):
                return
            self._realtime_decoder = None
            if self._realtime_decode_process is decoder.process:
                self._realtime_decode_process = None
        self._stop_realtime_process(decoder.process)
        self._close_process_streams(decoder.process)
        decoder.stderr_thread.join(timeout=1)

    def _stop_realtime_process(self, process: subprocess.Popen[bytes]) -> None:
        # A decoder owns no output file to finalize. SIGTERM can instead block
        # flushing unread raw frames into a full pipe at a clip boundary.
        self._terminate_preview_process(process)
        process.wait(timeout=2)

    def _read_realtime_frame(
        self,
        position_seconds: float,
        interval: LayoutInterval,
        cancel_check: Callable[[], bool] | None,
    ) -> VideoFrame:
        with self._lock:
            decoder = self._realtime_decoder
            generation = self._playback_generation
        if decoder is not None and (
            decoder.interval is not interval
            or decoder.generation != generation
            or position_seconds < decoder.origin
        ):
            self._release_realtime_decoder(decoder)
            decoder = None
        if decoder is None:
            decoder = self._start_realtime_decoder(
                position_seconds, interval, generation, cancel_check
            )
        process = decoder.process
        target_index = max(
            decoder.next_frame_index,
            int((position_seconds - decoder.origin) * self.frame_rate + 1e-6),
        )
        try:
            while True:
                if cancel_check is not None and cancel_check():
                    raise _PreviewRequestCancelled
                if process.stdout is None:
                    raise PlaybackBackendError("Synchronized playback did not provide a video pipe")
                data = self._read_exact(process.stdout, self.frame_size)
                if cancel_check is not None and cancel_check():
                    raise _PreviewRequestCancelled
                if len(data) != self.frame_size:
                    decoder.stderr_thread.join(timeout=1)
                    detail = b"".join(decoder.stderr).decode(errors="replace").strip()
                    raise PlaybackBackendError(
                        detail or "FFmpeg returned an incomplete synchronized playback frame"
                    )
                frame_index = decoder.next_frame_index
                decoder.next_frame_index += 1
                with self._lock:
                    self._decoded_frames += 1
                    if frame_index < target_index:
                        self._dropped_frames += 1
                if frame_index >= target_index:
                    break
        except (OSError, ValueError) as error:
            if cancel_check is not None and cancel_check():
                raise _PreviewRequestCancelled from error
            raise PlaybackBackendError(f"Could not read synchronized playback: {error}") from error
        decoded_position = decoder.origin + frame_index / self.frame_rate
        return VideoFrame(data, self.width, self.height, decoded_position, decoded_position)

    def _start_realtime_decoder(
        self,
        position_seconds: float,
        interval: LayoutInterval,
        generation: int,
        cancel_check: Callable[[], bool] | None,
    ) -> _RealtimeDecoder:
        if cancel_check is not None and cancel_check():
            raise _PreviewRequestCancelled
        try:
            process = subprocess.Popen(
                self._video_command(position_seconds, interval, continuous=True),
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
            raise PlaybackBackendError(f"Could not start synchronized playback: {error}") from error
        stderr: list[bytes] = []
        stderr_thread = threading.Thread(
            target=self._drain_stderr,
            args=(process, stderr),
            daemon=True,
        )
        decoder = _RealtimeDecoder(
            process, interval, position_seconds, generation, stderr, stderr_thread
        )
        try:
            stderr_thread.start()
        except RuntimeError as error:
            self._stop_realtime_process(process)
            self._close_process_streams(process)
            raise PlaybackBackendError(
                f"Could not start synchronized playback error reader: {error}"
            ) from error
        with self._lock:
            cancelled = generation != self._playback_generation or (
                cancel_check is not None and cancel_check()
            )
            if not cancelled:
                self._realtime_decoder = decoder
                self._realtime_decode_process = process
                self._decoder_starts += 1
        if cancelled:
            self._stop_realtime_process(process)
            self._close_process_streams(process)
            stderr_thread.join(timeout=1)
            raise _PreviewRequestCancelled
        return decoder

    def playback_stats(self) -> dict[str, int]:
        with self._lock:
            return {
                "decoder_starts": self._decoder_starts,
                "decoded_frames": self._decoded_frames,
                "dropped_frames": self._dropped_frames,
            }

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
                decoder = self._realtime_decoder
            if decoder is not None and decoder.generation == generation:
                self._release_realtime_decoder(decoder)
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

    def _terminate_process(self, *, preserve_pause: bool = False) -> None:
        with self._lock:
            self._position_seconds = self._clock_position_locked()
            self._clock_origin_position = self._position_seconds
            self._clock_origin_time = None
            event = self._stop_event
            worker = self._playback_thread
            decode_process = self._realtime_decode_process
            decoder = self._realtime_decoder
            self._playback_generation += 1
            self._realtime_run = None
            self._stop_event = None
            self._playback_thread = None
            self._realtime_decode_process = None
            if not preserve_pause:
                self._paused = False
            if event is not None:
                event.set()
        if decode_process is not None:
            if decoder is not None and decoder.process is decode_process:
                self._stop_realtime_process(decode_process)
            else:
                self._terminate_process_instance(decode_process)
        if worker is not None and worker is not threading.current_thread():
            worker.join(timeout=2)
        if decoder is not None:
            self._release_realtime_decoder(decoder)
        if preserve_pause and worker is not None and worker.is_alive():
            raise PlaybackBackendError(
                "Synchronized playback worker did not stop before preview resource release"
            )

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
