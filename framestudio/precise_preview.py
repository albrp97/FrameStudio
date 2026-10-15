"""Standard-library transport for the isolated, optional exact-preview runtime."""

from __future__ import annotations

import json
import os
import select
import struct
import subprocess
import sys
import threading
import time
import uuid
from collections.abc import Callable
from pathlib import Path
from typing import Any

from .ffmpeg_playback import _PreviewRequestCancelled
from .playback import PlaybackBackendError

PROTOCOL_VERSION = 1
AV_VERSION = "19.0.1"
MAX_HEADER_BYTES = 262144
MAX_FRAME_BYTES = 64 * 1024 * 1024


class PreviewDependencyUnavailable(PlaybackBackendError):
    """Only an absent optional PyAV installation permits reference fallback."""


class PreviewUnsupportedSource(PlaybackBackendError):
    """A known exactness limitation selects the explicit reference path."""


def preview_backend_setting() -> str:
    value = os.environ.get("FRAMESTUDIO_PREVIEW_BACKEND", "auto")
    if value not in {"auto", "cpu", "cuda", "ffmpeg"}:
        raise PlaybackBackendError("FRAMESTUDIO_PREVIEW_BACKEND must be auto, cpu, cuda, or ffmpeg")
    return value


def preview_python() -> str:
    explicit = os.environ.get("FRAMESTUDIO_PREVIEW_PYTHON")
    if explicit:
        return explicit
    local = Path(__file__).resolve().parent.parent / ".venv" / "bin" / "python"
    return str(local) if local.is_file() else sys.executable


def encode_message(header: dict[str, Any], payload: bytes = b"") -> bytes:
    header = dict(header, payload_bytes=len(payload))
    raw = json.dumps(header, separators=(",", ":"), allow_nan=False).encode()
    if len(raw) > MAX_HEADER_BYTES or len(payload) > MAX_FRAME_BYTES:
        raise PlaybackBackendError("Precise preview message exceeds the protocol limit")
    return struct.pack("!I", len(raw)) + raw + payload


def decode_header(raw: bytes) -> dict[str, Any]:
    if not raw or len(raw) > MAX_HEADER_BYTES:
        raise PlaybackBackendError("Invalid precise preview header size")
    try:
        result = json.loads(raw)
    except (ValueError, UnicodeError) as error:
        raise PlaybackBackendError("Corrupt precise preview JSON") from error
    if not isinstance(result, dict):
        raise PlaybackBackendError("Precise preview header must be an object")
    size = result.get("payload_bytes", 0)
    if type(size) is not int or not 0 <= size <= MAX_FRAME_BYTES:
        raise PlaybackBackendError("Invalid precise preview payload size")
    return result


class PrecisePreviewClient:
    def __init__(
        self,
        engine: str,
        *,
        timeout: float = 15.0,
        python: str | None = None,
        worker_path: Path | None = None,
    ) -> None:
        if engine not in {"auto", "cpu", "cuda"}:
            raise ValueError("Invalid precise preview engine")
        self.engine = engine
        self.timeout = timeout
        self.python = python or preview_python()
        self.worker_path = worker_path or Path(__file__).with_name("precise_preview_worker.py")
        self._io_lock = threading.Lock()
        self._state_lock = threading.Lock()
        self._process: subprocess.Popen[bytes] | None = None
        self._closed = False
        self._epoch = uuid.uuid4().hex
        self._next_id = 0
        self._buffer = bytearray()
        self._pending_cancel = False
        self.last_diagnostics: dict[str, Any] = {}

    def snapshot(self) -> dict[str, Any]:
        with self._state_lock:
            process = self._process
            return {
                "helper_pid": (
                    process.pid if process is not None and process.poll() is None else None
                ),
                "requests": self._next_id,
                "closed": self._closed,
            }

    @staticmethod
    def _kill(process: subprocess.Popen[bytes]) -> None:
        if process.poll() is None:
            try:
                process.kill()
            except ProcessLookupError:
                pass
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired as error:
            raise PlaybackBackendError("Could not reap the precise preview helper") from error
        for stream in (process.stdin, process.stdout):
            if stream is not None:
                stream.close()

    def _reset(self) -> None:
        with self._state_lock:
            process, self._process = self._process, None
        if process is not None:
            self._kill(process)
        self._buffer.clear()

    def close(self) -> None:
        # Never wait on the decode I/O lock: GTK stop/reload must interrupt a
        # helper blocked inside native demux, decode, or composition.
        with self._state_lock:
            self._closed = True
            process, self._process = self._process, None
        if process is not None:
            self._kill(process)

    def interrupt(self) -> None:
        """Stop an in-flight operation without permanently closing the client."""
        with self._state_lock:
            process, self._process = self._process, None
        if process is not None:
            self._kill(process)

    def _check(self, deadline: float, cancelled: Callable[[], bool] | None = None) -> None:
        if self._closed or (cancelled is not None and cancelled()):
            raise _PreviewRequestCancelled
        if time.monotonic() >= deadline:
            raise PlaybackBackendError("Timed out while rendering the precise preview frame")

    def _write(self, raw: bytes, deadline: float) -> None:
        process = self._process
        if process is None or process.stdin is None:
            raise PlaybackBackendError("Precise preview helper is not running")
        offset = 0
        while offset < len(raw):
            self._check(deadline)
            _, ready, _ = select.select([], [process.stdin], [], 0.02)
            if ready:
                try:
                    offset += os.write(process.stdin.fileno(), raw[offset:])
                except BlockingIOError:
                    continue

    def _read(
        self, deadline: float, cancelled: Callable[[], bool] | None = None
    ) -> tuple[dict[str, Any], bytes]:
        process = self._process
        if process is None or process.stdout is None:
            raise PlaybackBackendError("Precise preview helper is not running")
        while True:
            self._check(deadline, cancelled)
            if len(self._buffer) >= 4:
                size = struct.unpack("!I", self._buffer[:4])[0]
                if not 0 < size <= MAX_HEADER_BYTES:
                    raise PlaybackBackendError("Invalid precise preview frame header")
                if len(self._buffer) >= size + 4:
                    header = decode_header(bytes(self._buffer[4 : size + 4]))
                    end = size + 4 + header.get("payload_bytes", 0)
                    if len(self._buffer) >= end:
                        payload = bytes(self._buffer[size + 4 : end])
                        del self._buffer[:end]
                        return header, payload
            ready, _, _ = select.select([process.stdout], [], [], 0.02)
            if ready:
                chunk = os.read(process.stdout.fileno(), 1024 * 1024)
                if not chunk:
                    raise PlaybackBackendError("Precise preview helper exited unexpectedly")
                self._buffer.extend(chunk)
                if len(self._buffer) > MAX_FRAME_BYTES + MAX_HEADER_BYTES + 4:
                    raise PlaybackBackendError("Precise preview response exceeds its limit")

    def _start(self, deadline: float) -> None:
        if self._pending_cancel and self._process is not None and self._process.poll() is not None:
            self._reset()
        if self._process is not None:
            return
        self._buffer.clear()
        with self._state_lock:
            if self._closed:
                raise _PreviewRequestCancelled
            self._process = subprocess.Popen(
                [self.python, str(self.worker_path.resolve()), self.engine, self._epoch],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                # Inherit stderr; never create an undrained diagnostic pipe.
                stderr=None,
                bufsize=0,
                start_new_session=True,
            )
            if self._process.stdin is None or self._process.stdout is None:
                raise PlaybackBackendError("Precise preview helper pipes were not created")
            os.set_blocking(self._process.stdin.fileno(), False)
            os.set_blocking(self._process.stdout.fileno(), False)
        header, payload = self._read(deadline)
        if header.get("status") == "missing_dependency" and header.get("dependency") == "av":
            raise PreviewDependencyUnavailable(
                "Exact preview optional dependency av is missing; selected reference FFmpeg"
            )
        if (
            payload
            or header.get("status") != "ready"
            or header.get("protocol") != PROTOCOL_VERSION
            or header.get("av_version") != AV_VERSION
            or header.get("epoch") != self._epoch
        ):
            raise PlaybackBackendError(
                str(header.get("error") or "Incompatible precise preview helper handshake")
            )

    def render(
        self,
        request: dict[str, Any],
        *,
        cancelled: Callable[[], bool] | None = None,
    ) -> tuple[bytes, dict[str, Any]]:
        with self._io_lock:
            deadline = time.monotonic() + self.timeout
            self._next_id += 1
            request_id = self._next_id
            restarted = False
            wire_request = encode_message(
                dict(request, id=request_id, epoch=self._epoch, op="render")
            )
            try:
                self._check(deadline, cancelled)
                self._start(deadline)
                try:
                    self._write(wire_request, deadline)
                except BrokenPipeError:
                    if not self._pending_cancel:
                        raise
                    self._reset()
                    self._start(deadline)
                    self._write(wire_request, deadline)
                    restarted = True
                self._pending_cancel = False
                while True:
                    header, payload = self._read(deadline, cancelled)
                    if header.get("epoch") != self._epoch:
                        raise PlaybackBackendError("Precise preview helper epoch mismatch")
                    response_id = header.get("id")
                    if type(response_id) is not int or not 0 < response_id <= request_id:
                        raise PlaybackBackendError("Precise preview helper request ID mismatch")
                    if response_id < request_id:
                        if header.get("retire") or header.get("status") == "error":
                            if restarted:
                                raise PlaybackBackendError(
                                    "Precise preview helper repeatedly retired stale requests"
                                )
                            self._reset()
                            self._start(deadline)
                            self._write(wire_request, deadline)
                            restarted = True
                        continue
                    if header.get("status") == "cancelled":
                        raise _PreviewRequestCancelled
                    if header.get("status") == "unsupported":
                        self.last_diagnostics = header
                        raise PreviewUnsupportedSource(str(header["error"]))
                    if header.get("status") != "frame":
                        raise PlaybackBackendError(
                            str(
                                header.get("error") or "Precise preview could not decode the source"
                            )
                        )
                    expected = request["width"] * request["height"] * 4
                    if len(payload) != expected:
                        raise PlaybackBackendError(
                            "Precise preview returned an incomplete RGBA frame"
                        )
                    physical = header.get("physical_frames")
                    if not isinstance(physical, list) or len(physical) != len(request["slots"]):
                        raise PlaybackBackendError(
                            "Precise preview omitted physical frame provenance"
                        )
                    for index, frame in enumerate(physical):
                        if (
                            not isinstance(frame, dict)
                            or any(
                                type(frame.get(field)) is not int
                                for field in (
                                    "pts",
                                    "time_base_num",
                                    "time_base_den",
                                    "source_tick",
                                    "origin_tick",
                                )
                            )
                            or frame["time_base_num"] <= 0
                            or frame["time_base_den"] <= 0
                            or frame.get("engine") not in {"cpu", "cuda"}
                            or not isinstance(frame.get("reason"), str)
                            or frame["source_tick"] != request["slots"][index]["source_tick"]
                        ):
                            raise PlaybackBackendError(
                                "Invalid precise preview physical provenance"
                            )
                    self._check(deadline, cancelled)
                    self.last_diagnostics = header
                    if header.get("retire"):
                        self._reset()
                    return payload, header
            except _PreviewRequestCancelled:
                self._pending_cancel = True
                if not self._closed and self._process is not None:
                    try:
                        self._write(
                            encode_message(
                                {"op": "cancel", "id": request_id, "epoch": self._epoch}
                            ),
                            min(deadline, time.monotonic() + 0.05),
                        )
                    except (OSError, ValueError, PlaybackBackendError, _PreviewRequestCancelled):
                        self._reset()
                raise
            except (OSError, ValueError) as error:
                self._reset()
                if self._closed or (cancelled is not None and cancelled()):
                    raise _PreviewRequestCancelled from error
                raise PlaybackBackendError(f"Precise preview transport failed: {error}") from error
            except PreviewUnsupportedSource:
                raise
            except PlaybackBackendError as error:
                self._reset()
                if self._closed or (cancelled is not None and cancelled()):
                    raise _PreviewRequestCancelled from error
                raise
