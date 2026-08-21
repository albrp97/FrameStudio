from __future__ import annotations

import os
import signal
import subprocess
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .playback import PlaybackBackendError


@dataclass(frozen=True)
class VideoFrame:
    data: bytes
    width: int
    height: int
    position_seconds: float


FrameCallback = Callable[[VideoFrame], None]
MessageCallback = Callable[[str], None]
VoidCallback = Callable[[], None]


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
        self._lock = threading.RLock()
        self._process: subprocess.Popen[bytes] | None = None
        self._stop_event: threading.Event | None = None
        self._position_seconds = 0.0
        self._paused = False
        self._preview_condition = threading.Condition(self._lock)
        self._preview_request: tuple[int, float] | None = None
        self._preview_generation = 0
        self._preview_process: subprocess.Popen[bytes] | None = None
        self._preview_thread: threading.Thread | None = None
        self._preview_shutdown = False

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
                "format=rgba",
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
        self._process = process
        self._stop_event = event
        self._paused = False
        stderr_output: list[bytes] = []
        stderr_thread = threading.Thread(
            target=self._drain_stderr,
            args=(process, stderr_output),
            daemon=True,
        )
        stderr_thread.start()
        reader = threading.Thread(
            target=self._read_frames,
            args=(process, event, start_position, stderr_output, stderr_thread),
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

    def _read_frames(
        self,
        process: subprocess.Popen[bytes],
        event: threading.Event,
        start_position: float,
        stderr_output: list[bytes],
        stderr_thread: threading.Thread,
    ) -> None:
        frame_index = 0
        incomplete = False
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
                position = min(
                    self.duration_seconds,
                    start_position + frame_index / self.frame_rate,
                )
                with self._lock:
                    if self._process is not process or event.is_set():
                        break
                    self._position_seconds = position
                self.on_frame(VideoFrame(data, self.width, self.height, position))
                frame_index += 1
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
                    is_current = self._process is process
                    if is_current:
                        self._process = None
                        self._stop_event = None
                        self._paused = False
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

    def play(self) -> None:
        self._cancel_preview_requests()
        with self._lock:
            if self._process is not None and self._paused:
                try:
                    os.kill(self._process.pid, signal.SIGCONT)
                except ProcessLookupError as error:
                    raise PlaybackBackendError("Playback process is no longer running") from error
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
            self._paused = True

    def _terminate_process(self) -> None:
        with self._lock:
            process = self._process
            event = self._stop_event
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
            self._preview_generation += 1
            self._preview_request = None
            process = self._preview_process
            self._preview_condition.notify_all()
        if process is not None:
            self._terminate_preview_process(process)

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

    def _decode_preview_frame(self, position_seconds: float) -> VideoFrame:
        try:
            process = subprocess.Popen(
                self._command(position_seconds, realtime=False, frame_count=1),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True,
            )
        except FileNotFoundError as error:
            raise PlaybackBackendError(
                f"ffmpeg is not installed or not on PATH: {self.ffmpeg_path}"
            ) from error
        except OSError as error:
            raise PlaybackBackendError(f"Could not start preview seek: {error}") from error

        with self._preview_condition:
            self._preview_process = process
        try:
            try:
                output, error_output = process.communicate(timeout=15)
            except subprocess.TimeoutExpired as error:
                self._terminate_preview_process(process)
                process.wait(timeout=2)
                raise PlaybackBackendError("Timed out while rendering the preview frame") from error
            except (OSError, ValueError) as error:
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
                generation, position_seconds = request

            try:
                frame = self._decode_preview_frame(position_seconds)
            except PlaybackBackendError as error:
                with self._preview_condition:
                    is_current = (
                        generation == self._preview_generation and not self._preview_shutdown
                    )
                if is_current:
                    self._notify_error(str(error))
                continue

            with self._preview_condition:
                is_current = generation == self._preview_generation and not self._preview_shutdown
                if is_current:
                    self._position_seconds = position_seconds
            if is_current:
                self.on_frame(frame)

    def request_preview(self, position_seconds: float) -> None:
        target = max(0.0, min(self.duration_seconds, float(position_seconds)))
        self._terminate_process()
        self._cancel_preview_requests()
        with self._preview_condition:
            if self._preview_shutdown:
                raise PlaybackBackendError("Playback backend is closed")
            self._preview_generation += 1
            self._preview_request = (
                self._preview_generation,
                target,
            )
            self._position_seconds = target
            worker = self._preview_thread
            if worker is None or not worker.is_alive():
                worker = threading.Thread(
                    target=self._run_preview_worker,
                    name="resolve-editor-preview",
                    daemon=True,
                )
                self._preview_thread = worker
                worker.start()
            self._preview_condition.notify_all()

    def current_position(self) -> float:
        with self._lock:
            return self._position_seconds

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
