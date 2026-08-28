from __future__ import annotations

import os
import shutil
import signal
import subprocess
import threading
import time
from collections.abc import Hashable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from .audio import AUDIO_CHANNELS, AUDIO_SAMPLE_RATE, audio_filter
from .composition_render import segment_video_filters
from .playback import PlaybackBackendError
from .preview_strategy import PreviewFrameCache


@dataclass(frozen=True)
class VideoFrame:
    data: bytes
    width: int
    height: int
    position_seconds: float
    decoded_position_seconds: float | None = None

    def at_position(self, position_seconds: float) -> VideoFrame:
        decoded_position = (
            self.position_seconds
            if self.decoded_position_seconds is None
            else self.decoded_position_seconds
        )
        return VideoFrame(
            self.data,
            self.width,
            self.height,
            position_seconds,
            decoded_position,
        )


FrameCallback = Callable[[VideoFrame], None]
MessageCallback = Callable[[str], None]
VoidCallback = Callable[[], None]


class _PreviewRequestCancelled(Exception):
    """Internal signal used when a preview request is obsolete before decode."""


class FfmpegPlaybackBackend:
    """Decode video frames in real time through a managed FFmpeg process."""

    def __init__(
        self,
        source: Path,
        width: int,
        height: int,
        frame_rate: float,
        duration_seconds: float,
        on_frame: FrameCallback,
        on_error: MessageCallback,
        on_end: VoidCallback,
        ffmpeg_path: str = "ffmpeg",
        audio_decision: Mapping[str, Any] | None = None,
        ffplay_path: str = "ffplay",
        on_warning: MessageCallback | None = None,
        preview_cache_size: int = 8,
    ) -> None:
        if width <= 0 or height <= 0:
            raise ValueError("Playback dimensions must be positive")
        if frame_rate <= 0:
            raise ValueError("Playback frame rate must be positive")
        self.source = Path(source)
        self.width = width
        self.height = height
        self.frame_rate = frame_rate
        self.duration_seconds = duration_seconds
        self.on_frame = on_frame
        self.on_error = on_error
        self.on_end = on_end
        self.ffmpeg_path = ffmpeg_path
        self.audio_decision = None if audio_decision is None else dict(audio_decision)
        self.ffplay_path = ffplay_path
        self.on_warning = on_warning or (lambda _message: None)
        self._lock = threading.RLock()
        self._process: subprocess.Popen[bytes] | None = None
        self._stop_event: threading.Event | None = None
        self._audio_process: subprocess.Popen[bytes] | None = None
        self._audio_sink: subprocess.Popen[bytes] | None = None
        self._audio_copy_thread: threading.Thread | None = None
        self._audio_monitor_thread: threading.Thread | None = None
        self._position_seconds = 0.0
        self._paused = False
        self._playback_generation = 0
        self._preview_condition = threading.Condition(self._lock)
        self._preview_request: tuple[int, float, Hashable | None] | None = None
        self._preview_generation = 0
        self._preview_process: subprocess.Popen[bytes] | None = None
        self._preview_thread: threading.Thread | None = None
        self._preview_shutdown = False
        self._preview_cache: PreviewFrameCache[VideoFrame] = PreviewFrameCache(
            preview_cache_size,
            frame_rate,
        )
        self._preview_stale_frames = 0
        self._preview_requests = 0
        self._preview_cancelled_requests = 0
        self._preview_coalesced_requests = 0
        self._preview_failures = 0

    @property
    def frame_size(self) -> int:
        return self.width * self.height * 4

    def _command(
        self,
        position_seconds: float,
        *,
        realtime: bool,
        frame_count: int | None = None,
    ) -> list[str]:
        command = [
            self.ffmpeg_path,
            "-hide_banner",
            "-loglevel",
            "error",
            "-ss",
            f"{position_seconds:.6f}",
        ]
        if realtime:
            command.append("-re")
        command.extend(
            [
                "-noautorotate",
                "-i",
                str(self.source),
                "-map",
                "0:v:0",
                "-an",
                "-sn",
                "-dn",
                "-vf",
                (
                    f"scale={self.width}:{self.height}:force_original_aspect_ratio=decrease,"
                    f"pad={self.width}:{self.height}:(ow-iw)/2:(oh-ih)/2,"
                    "setsar=1,format=rgba"
                ),
            ]
        )
        if frame_count is not None:
            command.extend(["-frames:v", str(frame_count)])
        command.extend(
            [
                "-f",
                "rawvideo",
                "-pix_fmt",
                "rgba",
                "pipe:1",
            ]
        )
        return command

    def _has_audio_preview(self) -> bool:
        if self.audio_decision is None:
            return False
        return self.audio_decision.get("status") != "not-applicable"

    def _audio_command(
        self,
        position_seconds: float,
        *,
        realtime: bool,
    ) -> list[str]:
        command = [
            self.ffmpeg_path,
            "-hide_banner",
            "-loglevel",
            "error",
            "-nostdin",
        ]
        if realtime:
            command.append("-re")
        command.extend(
            [
                "-ss",
                f"{position_seconds:.6f}",
                "-i",
                str(self.source),
                "-map",
                "0:a:0",
                "-vn",
                "-af",
                audio_filter(self.audio_decision),
                "-f",
                "s16le",
                "-ar",
                str(AUDIO_SAMPLE_RATE),
                "-ac",
                str(AUDIO_CHANNELS),
                "pipe:1",
            ]
        )
        return command

    def _start_audio_preview_locked(self, position_seconds: float) -> None:
        if not self._has_audio_preview():
            return
        if shutil.which(self.ffplay_path) is None:
            raise PlaybackBackendError(
                f"ffplay is required for audio preview but was not found: {self.ffplay_path}"
            )
        try:
            audio_process = subprocess.Popen(
                self._audio_command(position_seconds, realtime=True),
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                bufsize=0,
                start_new_session=True,
            )
            audio_sink = subprocess.Popen(
                [
                    self.ffplay_path,
                    "-hide_banner",
                    "-loglevel",
                    "error",
                    "-nodisp",
                    "-autoexit",
                    "-f",
                    "s16le",
                    "-ar",
                    str(AUDIO_SAMPLE_RATE),
                    "-ac",
                    str(AUDIO_CHANNELS),
                    "-i",
                    "pipe:0",
                ],
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
        except (FileNotFoundError, OSError) as error:
            for process in (
                audio_process if "audio_process" in locals() else None,
                audio_sink if "audio_sink" in locals() else None,
            ):
                if process is not None:
                    self._terminate_process_instance(process)
                    self._close_process_streams(process)
            raise PlaybackBackendError(f"Could not start audio preview: {error}") from error
        self._audio_process = audio_process
        self._audio_sink = audio_sink
        self._audio_copy_thread = threading.Thread(
            target=self._copy_audio,
            args=(audio_process, audio_sink),
            name="framestudio-editor-audio",
            daemon=True,
        )
        self._audio_copy_thread.start()
        self._audio_monitor_thread = threading.Thread(
            target=self._monitor_audio_preview,
            args=(audio_process, audio_sink),
            name="framestudio-editor-audio-monitor",
            daemon=True,
        )
        self._audio_monitor_thread.start()

    @staticmethod
    def _close_process_streams(process: subprocess.Popen[bytes] | None) -> None:
        if process is None:
            return
        for stream in (process.stdin, process.stdout, process.stderr):
            if stream is not None:
                stream.close()

    @staticmethod
    def _copy_audio(
        audio_process: subprocess.Popen[bytes],
        audio_sink: subprocess.Popen[bytes],
    ) -> None:
        try:
            if audio_process.stdout is None or audio_sink.stdin is None:
                return
            while True:
                chunk = audio_process.stdout.read(64 * 1024)
                if not chunk:
                    break
                audio_sink.stdin.write(chunk)
                audio_sink.stdin.flush()
        except (BrokenPipeError, OSError, ValueError):
            return
        finally:
            if audio_sink.stdin is not None:
                try:
                    audio_sink.stdin.close()
                except (OSError, ValueError):
                    pass

    def _monitor_audio_preview(
        self,
        audio_process: subprocess.Popen[bytes],
        audio_sink: subprocess.Popen[bytes],
    ) -> None:
        sink_return_code = audio_sink.wait()
        if sink_return_code != 0 and audio_process.poll() is None:
            self._terminate_process_instance(audio_process)
        audio_return_code = audio_process.wait()
        with self._lock:
            is_current = self._audio_process is audio_process or self._audio_sink is audio_sink
            if is_current:
                self._audio_process = None
                self._audio_sink = None
                self._audio_monitor_thread = None
        if is_current and (sink_return_code != 0 or audio_return_code != 0):
            self._notify_warning(
                "Audio preview failed "
                f"(ffplay status {sink_return_code}, ffmpeg status {audio_return_code})"
            )

    def _terminate_audio_preview(self, *, expected_generation: int | None = None) -> None:
        with self._lock:
            if expected_generation is not None and expected_generation != self._playback_generation:
                return
            audio_process = self._audio_process
            audio_sink = self._audio_sink
            copy_thread = self._audio_copy_thread
            monitor_thread = self._audio_monitor_thread
            self._audio_process = None
            self._audio_sink = None
            self._audio_copy_thread = None
            self._audio_monitor_thread = None
        for process in (audio_process, audio_sink):
            if process is None:
                continue
            if process.poll() is None:
                try:
                    os.kill(process.pid, signal.SIGCONT)
                except ProcessLookupError:
                    pass
                self._terminate_process_instance(process)
            else:
                process.wait()
        self._close_process_streams(audio_process)
        self._close_process_streams(audio_sink)
        if copy_thread is not None and copy_thread is not threading.current_thread():
            copy_thread.join(timeout=1)
        if monitor_thread is not None and monitor_thread is not threading.current_thread():
            monitor_thread.join(timeout=1)

    def _start_process_locked(self) -> None:
        if self._process is not None:
            return
        event = threading.Event()
        start_position = self._position_seconds
        try:
            process = subprocess.Popen(
                self._command(start_position, realtime=True),
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
            raise PlaybackBackendError(f"Could not start FFmpeg playback: {error}") from error
        self._playback_generation += 1
        generation = self._playback_generation
        self._process = process
        self._stop_event = event
        self._paused = False
        try:
            self._start_audio_preview_locked(start_position)
        except PlaybackBackendError as error:
            self._notify_warning(str(error))
        stderr_output: list[bytes] = []
        stderr_thread = threading.Thread(
            target=self._drain_stderr,
            args=(process, stderr_output),
            daemon=True,
        )
        stderr_thread.start()
        reader = threading.Thread(
            target=self._read_frames,
            args=(process, event, start_position, stderr_output, stderr_thread, generation),
            daemon=True,
        )
        reader.start()

    @staticmethod
    def _drain_stderr(
        process: subprocess.Popen[bytes],
        output: list[bytes],
    ) -> None:
        if process.stderr is not None:
            try:
                output.append(process.stderr.read())
            except (OSError, ValueError):
                output.append(b"")
            finally:
                process.stderr.close()

    @staticmethod
    def _read_exact(stream, size: int) -> bytes:
        data = bytearray()
        while len(data) < size:
            chunk = stream.read(size - len(data))
            if not chunk:
                break
            data.extend(chunk)
        return bytes(data)

    def _wait_for_frame_deadline(
        self,
        process: subprocess.Popen[bytes],
        event: threading.Event,
        deadline: float,
        frame_interval: float,
    ) -> bool:
        while not event.is_set():
            with self._lock:
                if self._process is not process:
                    return False
                paused = self._paused
            if paused:
                event.wait(min(frame_interval, 0.05))
                deadline = time.monotonic() + frame_interval
                continue
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return True
            if event.wait(min(remaining, 0.05)):
                return False
        return False

    def _deliver_playback_frame(
        self,
        process: subprocess.Popen[bytes],
        event: threading.Event,
        generation: int,
        frame: VideoFrame,
        position: float,
    ) -> bool:
        with self._lock:
            if (
                self._process is not process
                or event.is_set()
                or generation != self._playback_generation
            ):
                return False
            self._position_seconds = position
            self.on_frame(frame)
        return True

    def _read_frames(
        self,
        process: subprocess.Popen[bytes],
        event: threading.Event,
        start_position: float,
        stderr_output: list[bytes],
        stderr_thread: threading.Thread,
        generation: int,
    ) -> None:
        frame_index = 0
        incomplete = False
        frame_interval = 1.0 / self.frame_rate
        next_frame_at = time.monotonic()
        if process.stdout is None:
            self._notify_error("FFmpeg playback did not provide a video pipe")
            return
        try:
            while not event.is_set():
                data = self._read_exact(process.stdout, self.frame_size)
                if not data:
                    break
                if len(data) != self.frame_size:
                    incomplete = True
                    break
                if not self._wait_for_frame_deadline(
                    process,
                    event,
                    next_frame_at,
                    frame_interval,
                ):
                    break
                position = min(
                    self.duration_seconds,
                    start_position + frame_index / self.frame_rate,
                )
                if not self._deliver_playback_frame(
                    process,
                    event,
                    generation,
                    VideoFrame(data, self.width, self.height, position),
                    position,
                ):
                    break
                frame_index += 1
                next_frame_at = time.monotonic() + frame_interval
        except (OSError, ValueError) as error:
            if not event.is_set():
                self._notify_error(f"FFmpeg playback read failed: {error}")
        finally:
            process.stdout.close()
            if not event.is_set():
                return_code: int | None
                try:
                    return_code = process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    return_code = process.poll()
                stderr_thread.join(timeout=1)
                with self._lock:
                    is_current = (
                        self._process is process and generation == self._playback_generation
                    )
                    if is_current:
                        self._process = None
                        self._stop_event = None
                        self._paused = False
                if is_current:
                    self._terminate_audio_preview(expected_generation=generation)
                    with self._lock:
                        is_current = (
                            generation == self._playback_generation and self._process is None
                        )
                        if is_current:
                            if incomplete:
                                self._notify_error("FFmpeg playback ended with an incomplete frame")
                            elif return_code not in (0, None):
                                detail = stderr_output[0].decode(errors="replace").strip()
                                self._notify_error(
                                    detail or f"FFmpeg playback exited with status {return_code}"
                                )
                            else:
                                self.on_end()

    def _notify_error(self, message: str) -> None:
        self.on_error(message or "FFmpeg playback failed")

    def _notify_warning(self, message: str) -> None:
        self.on_warning(message or "Audio preview warning")

    @staticmethod
    def _terminate_process_instance(process: subprocess.Popen[bytes]) -> None:
        if process.poll() is None:
            try:
                process.terminate()
            except ProcessLookupError:
                pass
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            try:
                process.kill()
            except ProcessLookupError:
                pass
            process.wait(timeout=2)

    def play(self) -> None:
        self._cancel_preview_requests()
        with self._lock:
            if self._process is not None and self._paused:
                try:
                    os.kill(self._process.pid, signal.SIGCONT)
                except ProcessLookupError as error:
                    raise PlaybackBackendError("Playback process is no longer running") from error
                if self._audio_process is not None:
                    if self._audio_process.poll() is None:
                        try:
                            os.kill(self._audio_process.pid, signal.SIGCONT)
                        except ProcessLookupError as error:
                            raise PlaybackBackendError(
                                "Audio preview process is no longer running"
                            ) from error
                if self._audio_sink is not None:
                    if self._audio_sink.poll() is None:
                        try:
                            os.kill(self._audio_sink.pid, signal.SIGCONT)
                        except ProcessLookupError as error:
                            raise PlaybackBackendError(
                                "Audio preview sink is no longer running"
                            ) from error
                self._paused = False
                return
            if self._process is None:
                self._start_process_locked()

    def pause(self) -> None:
        with self._lock:
            if self._process is None or self._paused:
                return
            try:
                os.kill(self._process.pid, signal.SIGSTOP)
            except ProcessLookupError as error:
                raise PlaybackBackendError("Playback process is no longer running") from error
            for process in (self._audio_process, self._audio_sink):
                if process is not None and process.poll() is None:
                    try:
                        os.kill(process.pid, signal.SIGSTOP)
                    except ProcessLookupError as error:
                        raise PlaybackBackendError(
                            "Audio preview process is no longer running"
                        ) from error
            self._paused = True

    def _terminate_process(self) -> None:
        self._terminate_audio_preview()
        with self._lock:
            process = self._process
            event = self._stop_event
            self._playback_generation += 1
            self._process = None
            self._stop_event = None
            self._paused = False
            if event is not None:
                event.set()
        if process is None:
            return
        try:
            os.kill(process.pid, signal.SIGCONT)
        except ProcessLookupError:
            pass
        if process.stdout is not None:
            process.stdout.close()
        if process.stderr is not None:
            process.stderr.close()
        try:
            process.terminate()
        except ProcessLookupError:
            return
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=2)

    def stop(self) -> None:
        self._terminate_process()
        self._cancel_preview_requests()

    @staticmethod
    def _terminate_preview_process(
        process: subprocess.Popen[bytes],
    ) -> None:
        if process.poll() is not None:
            return
        try:
            process.kill()
        except ProcessLookupError:
            pass

    def _cancel_preview_requests(self) -> None:
        with self._preview_condition:
            if self._preview_request is not None:
                self._preview_coalesced_requests += 1
            if self._preview_request is not None or self._preview_process is not None:
                self._preview_cancelled_requests += 1
            self._preview_generation += 1
            self._preview_request = None
            process = self._preview_process
            self._preview_condition.notify_all()
        if process is not None:
            self._terminate_preview_process(process)

    def _preview_cache_namespace(self, _position_seconds: float) -> Hashable | None:
        return None

    def _decode_one_frame(self, position_seconds: float) -> None:
        try:
            result = subprocess.run(
                self._command(position_seconds, realtime=False, frame_count=1),
                capture_output=True,
                check=False,
                timeout=15,
            )
        except FileNotFoundError as error:
            raise PlaybackBackendError(
                f"ffmpeg is not installed or not on PATH: {self.ffmpeg_path}"
            ) from error
        except (OSError, subprocess.TimeoutExpired) as error:
            raise PlaybackBackendError(f"Could not seek preview: {error}") from error
        if result.returncode != 0:
            detail = result.stderr.decode(errors="replace").strip()
            raise PlaybackBackendError(detail or "FFmpeg could not seek the source")
        if len(result.stdout) != self.frame_size:
            raise PlaybackBackendError("FFmpeg returned an incomplete preview frame")
        with self._lock:
            self._position_seconds = position_seconds
        self.on_frame(
            VideoFrame(
                result.stdout,
                self.width,
                self.height,
                position_seconds,
            )
        )

    def seek(self, position_seconds: float) -> None:
        target = max(0.0, min(self.duration_seconds, float(position_seconds)))
        self._cancel_preview_requests()
        with self._lock:
            was_playing = self._process is not None and not self._paused
        self._terminate_process()
        with self._lock:
            self._position_seconds = target
        if was_playing:
            self.play()
        else:
            self._decode_one_frame(target)

    def _decode_preview_frame(
        self,
        position_seconds: float,
        generation: int | None = None,
    ) -> VideoFrame:
        try:
            with self._preview_condition:
                if generation is not None and (
                    generation != self._preview_generation or self._preview_shutdown
                ):
                    raise _PreviewRequestCancelled
                process = subprocess.Popen(
                    self._command(position_seconds, realtime=False, frame_count=1),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    start_new_session=True,
                )
                self._preview_process = process
        except FileNotFoundError as error:
            raise PlaybackBackendError(
                f"ffmpeg is not installed or not on PATH: {self.ffmpeg_path}"
            ) from error
        except OSError as error:
            raise PlaybackBackendError(f"Could not start preview seek: {error}") from error
        try:
            try:
                output, error_output = process.communicate(timeout=15)
            except subprocess.TimeoutExpired as error:
                self._abort_preview_process(process)
                raise PlaybackBackendError("Timed out while rendering the preview frame") from error
            except (OSError, ValueError) as error:
                self._abort_preview_process(process)
                raise PlaybackBackendError(
                    f"Could not render the preview frame: {error}"
                ) from error
        finally:
            with self._preview_condition:
                if self._preview_process is process:
                    self._preview_process = None

        if process.returncode != 0:
            detail = error_output.decode(errors="replace").strip()
            raise PlaybackBackendError(detail or "FFmpeg could not render the preview frame")
        if len(output) != self.frame_size:
            raise PlaybackBackendError("FFmpeg returned an incomplete preview frame")
        return VideoFrame(
            output,
            self.width,
            self.height,
            position_seconds,
        )

    def _abort_preview_process(self, process: subprocess.Popen[bytes]) -> None:
        self._terminate_preview_process(process)
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            self._terminate_preview_process(process)
            process.wait(timeout=2)
        for stream in (process.stdout, process.stderr):
            if stream is not None:
                try:
                    stream.close()
                except (OSError, ValueError):
                    pass

    def _deliver_preview_frame(
        self,
        generation: int,
        position_seconds: float,
        cache_namespace: Hashable | None,
        frame: VideoFrame,
    ) -> bool:
        with self._preview_condition:
            if generation != self._preview_generation or self._preview_shutdown:
                self._preview_stale_frames += 1
                return False
            self._position_seconds = position_seconds
            self._preview_cache.put(frame, namespace=cache_namespace)
            self.on_frame(frame)
        return True

    def _run_preview_worker(self) -> None:
        while True:
            with self._preview_condition:
                while self._preview_request is None and not self._preview_shutdown:
                    self._preview_condition.wait()
                if self._preview_shutdown:
                    self._preview_thread = None
                    return
                request = self._preview_request
                self._preview_request = None
                if request is None:
                    continue
                generation, position_seconds, cache_namespace = request

            try:
                frame = self._decode_preview_frame(position_seconds, generation)
            except _PreviewRequestCancelled:
                continue
            except PlaybackBackendError as error:
                with self._preview_condition:
                    is_current = (
                        generation == self._preview_generation and not self._preview_shutdown
                    )
                if is_current:
                    self._preview_failures += 1
                    self._notify_error(str(error))
                continue

            self._deliver_preview_frame(
                generation,
                position_seconds,
                cache_namespace,
                frame,
            )

    def request_preview(self, position_seconds: float) -> None:
        target = max(0.0, min(self.duration_seconds, float(position_seconds)))
        self._terminate_process()
        self._cancel_preview_requests()
        cached_frame: VideoFrame | None
        cache_namespace = self._preview_cache_namespace(target)
        with self._preview_condition:
            if self._preview_shutdown:
                raise PlaybackBackendError("Playback backend is closed")
            self._preview_requests += 1
            cached_frame = self._preview_cache.get(target, namespace=cache_namespace)
            if cached_frame is not None:
                self._position_seconds = target
            else:
                self._preview_generation += 1
                self._preview_request = (
                    self._preview_generation,
                    target,
                    cache_namespace,
                )
                self._position_seconds = target
                worker = self._preview_thread
                if worker is None or not worker.is_alive():
                    worker = threading.Thread(
                        target=self._run_preview_worker,
                        name="framestudio-editor-preview",
                        daemon=True,
                    )
                    self._preview_thread = worker
                    worker.start()
                self._preview_condition.notify_all()
        if cached_frame is not None:
            self.on_frame(cached_frame.at_position(target))

    def current_position(self) -> float:
        with self._lock:
            return self._position_seconds

    def preview_stats(self) -> dict[str, int]:
        with self._lock:
            return {
                "requests": self._preview_requests,
                "cache_hits": self._preview_cache.hits,
                "cache_misses": self._preview_cache.misses,
                "cache_evictions": self._preview_cache.evictions,
                "stale_frames": self._preview_stale_frames,
                "cancelled_requests": self._preview_cancelled_requests,
                "coalesced_requests": self._preview_coalesced_requests,
                "failures": self._preview_failures,
            }

    def close(self) -> None:
        self.stop()
        with self._preview_condition:
            self._preview_shutdown = True
            self._preview_generation += 1
            self._preview_request = None
            process = self._preview_process
            worker = self._preview_thread
            self._preview_condition.notify_all()
        if process is not None:
            self._terminate_preview_process(process)
        if worker is not None and worker is not threading.current_thread():
            worker.join(timeout=2)


class FfmpegComposedPlaybackBackend(FfmpegPlaybackBackend):
    """Decode a sequential mixed-source timeline into one preview stream."""

    def __init__(
        self,
        sources: Sequence[tuple[str, Path]],
        blocks,
        width: int,
        height: int,
        frame_rate: float,
        duration_seconds: float,
        on_frame: FrameCallback,
        on_error: MessageCallback,
        on_end: VoidCallback,
        ffmpeg_path: str = "ffmpeg",
        audio_decisions: Mapping[str, Mapping[str, Any]] | None = None,
        ffplay_path: str = "ffplay",
        on_warning: MessageCallback | None = None,
        preview_cache_size: int = 8,
    ) -> None:
        source_items = tuple(sources)
        if not source_items:
            raise ValueError("At least one source is required for composed playback")
        self._source_items = source_items
        self._blocks = tuple(block for block in blocks if not block.deleted)
        if not self._blocks:
            raise ValueError("At least one active timeline block is required for composed playback")
        self._source_indexes = {
            source_id: index for index, (source_id, _path) in enumerate(source_items)
        }
        self.audio_decisions = {} if audio_decisions is None else dict(audio_decisions)
        super().__init__(
            source_items[0][1],
            width,
            height,
            frame_rate,
            duration_seconds,
            on_frame,
            on_error,
            on_end,
            ffmpeg_path,
            ffplay_path=ffplay_path,
            on_warning=on_warning,
            preview_cache_size=preview_cache_size,
        )

    def _has_audio_preview(self) -> bool:
        return any(
            settings.get("status") != "not-applicable" for settings in self.audio_decisions.values()
        )

    def _preview_cache_namespace(self, position_seconds: float) -> Hashable | None:
        plan, _optimized, _input_offsets = self._render_plan(position_seconds)
        segment_id = getattr(plan[0][0], "segment_id", None)
        if not isinstance(segment_id, str):
            raise PlaybackBackendError("Preview block does not have a valid segment identity")
        return segment_id

    def _render_plan(
        self,
        position_seconds: float,
    ) -> tuple[tuple[tuple[Any, int, float, float], ...], bool, dict[int, float]]:
        total_duration = sum(block.duration_seconds for block in self._blocks)
        target = max(0.0, min(total_duration, float(position_seconds)))
        plan: list[tuple[Any, int, float, float]] = []
        elapsed = 0.0
        optimized = target < total_duration - 1e-9
        start_index = 0
        if optimized:
            for index, block in enumerate(self._blocks):
                block_end = elapsed + block.duration_seconds
                if target >= block_end - 1e-9:
                    elapsed = block_end
                    continue
                offset = max(0.0, target - elapsed)
                source_start = block.start_seconds + offset
                plan.append(
                    (
                        block,
                        self._source_index_for_block(block),
                        source_start,
                        block.end_seconds - source_start,
                    )
                )
                start_index = index + 1
                break
        if not plan:
            optimized = False
            plan = [
                (
                    block,
                    self._source_index_for_block(block),
                    block.start_seconds,
                    block.duration_seconds,
                )
                for block in self._blocks
            ]
        else:
            for block in self._blocks[start_index:]:
                plan.append(
                    (
                        block,
                        self._source_index_for_block(block),
                        block.start_seconds,
                        block.duration_seconds,
                    )
                )
        input_offsets: dict[int, float] = {}
        if optimized:
            for _block, source_index, source_start, _duration in plan:
                input_offsets[source_index] = min(
                    source_start,
                    input_offsets.get(source_index, source_start),
                )
        return tuple(plan), optimized, input_offsets

    def _source_index_for_block(self, block: Any) -> int:
        source_id = block.source_id or (
            self._source_items[0][0] if len(self._source_items) == 1 else ""
        )
        source_index = self._source_indexes.get(source_id)
        if source_index is None:
            raise PlaybackBackendError(
                f"Preview block references unknown source: {block.source_id}"
            )
        return source_index

    def _append_inputs(
        self,
        command: list[str],
        *,
        realtime: bool,
        input_offsets: Mapping[int, float],
    ) -> None:
        for index, (_source_id, path) in enumerate(self._source_items):
            if realtime:
                command.append("-re")
            offset = input_offsets.get(index, 0.0)
            if offset > 0:
                command.extend(["-ss", f"{offset:.6f}"])
            command.extend(["-noautorotate", "-i", str(path)])

    def _base_command(
        self,
        *,
        realtime: bool,
        input_offsets: Mapping[int, float],
    ) -> list[str]:
        command = [
            self.ffmpeg_path,
            "-hide_banner",
            "-loglevel",
            "error",
            "-nostdin",
        ]
        self._append_inputs(
            command,
            realtime=realtime,
            input_offsets=input_offsets,
        )
        return command

    def _audio_command(
        self,
        position_seconds: float,
        *,
        realtime: bool,
    ) -> list[str]:
        plan, optimized, input_offsets = self._render_plan(position_seconds)
        command = self._base_command(
            realtime=realtime,
            input_offsets=input_offsets,
        )
        filters: list[str] = []
        audio_inputs: list[str] = []
        for index, (block, source_index, source_start, duration_value) in enumerate(plan):
            source_id = block.source_id or (
                self._source_items[0][0] if len(self._source_items) == 1 else ""
            )
            source_offset = input_offsets.get(source_index, 0.0)
            start = f"{source_start - source_offset:.6f}"
            duration = f"{duration_value:.6f}"
            decision = self.audio_decisions.get(source_id)
            if decision is not None and decision.get("status") == "not-applicable":
                filters.append(
                    f"anullsrc=channel_layout=stereo:sample_rate={AUDIO_SAMPLE_RATE},"
                    f"atrim=duration={duration},asetpts=PTS-STARTPTS[a{index}]"
                )
            else:
                filters.append(
                    f"[{source_index}:a:0]atrim=start={start}:duration={duration},"
                    f"{audio_filter(decision)}[a{index}]"
                )
            audio_inputs.append(f"[a{index}]")
        filters.append(f"{''.join(audio_inputs)}concat=n={len(audio_inputs)}:v=0:a=1[outa]")
        output_options = ["-map", "[outa]"]
        if not optimized and position_seconds > 0:
            output_options.extend(["-ss", f"{position_seconds:.6f}"])
        output_options.extend(
            [
                "-f",
                "s16le",
                "-ar",
                str(AUDIO_SAMPLE_RATE),
                "-ac",
                str(AUDIO_CHANNELS),
                "pipe:1",
            ]
        )
        command.extend(
            [
                "-filter_complex",
                ";".join(filters),
                *output_options,
            ]
        )
        return command

    def _command(
        self,
        position_seconds: float,
        *,
        realtime: bool,
        frame_count: int | None = None,
    ) -> list[str]:
        plan, optimized, input_offsets = self._render_plan(position_seconds)
        command = self._base_command(
            realtime=realtime,
            input_offsets=input_offsets,
        )
        filters: list[str] = []
        video_inputs: list[str] = []
        for index, (block, source_index, source_start, duration_value) in enumerate(plan):
            source_offset = input_offsets.get(source_index, 0.0)
            filters.extend(
                segment_video_filters(
                    f"[{source_index}:v:0]",
                    block,
                    self.width,
                    self.height,
                    f"[v{index}]",
                    frame_rate=self.frame_rate,
                    source_start_seconds=source_start - source_offset,
                    source_duration_seconds=duration_value,
                )
            )
            video_inputs.append(f"[v{index}]")
        filters.append(f"{''.join(video_inputs)}concat=n={len(video_inputs)}:v=1:a=0[outv]")
        command.extend(
            [
                "-filter_complex",
                ";".join(filters),
                "-map",
                "[outv]",
            ]
        )
        if not optimized and position_seconds > 0:
            command.extend(["-ss", f"{position_seconds:.6f}"])
        if frame_count is not None:
            command.extend(["-frames:v", str(frame_count)])
        command.extend(
            [
                "-f",
                "rawvideo",
                "-pix_fmt",
                "rgba",
                "pipe:1",
            ]
        )
        return command
