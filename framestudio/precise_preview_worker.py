"""Disposable native preview process; execute by absolute path from any cwd."""

from __future__ import annotations

import gc
import os
import struct
import sys
import threading
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from framestudio.precise_preview import (
    AV_VERSION,
    MAX_FRAME_BYTES,
    MAX_HEADER_BYTES,
    PROTOCOL_VERSION,
    decode_header,
    encode_message,
)


def rss_bytes() -> int:
    for line in Path("/proc/self/status").read_text().splitlines():
        if line.startswith("VmRSS:"):
            return int(line.split()[1]) * 1024
    return 0


def rss_limit() -> int:
    available = 6144
    for line in Path("/proc/meminfo").read_text().splitlines():
        if line.startswith("MemAvailable:"):
            available = int(line.split()[1]) // 1024
    configured = os.environ.get("FRAMESTUDIO_PREVIEW_RSS_LIMIT_MB")
    limit = int(configured) if configured is not None else min(1536, max(256, available // 4))
    if limit <= 0:
        raise ValueError("FRAMESTUDIO_PREVIEW_RSS_LIMIT_MB must be positive")
    return limit * 1024 * 1024


def read_exact(stream: Any, size: int) -> bytes:
    chunks = bytearray()
    while len(chunks) < size:
        chunk = stream.read(size - len(chunks))
        if not chunk:
            raise EOFError
        chunks.extend(chunk)
    return bytes(chunks)


class Inbox:
    def __init__(self, epoch: str) -> None:
        self.epoch = epoch
        self.condition = threading.Condition()
        self.latest: dict[str, Any] | None = None
        self.latest_id = 0
        self.cancel_id = 0
        self.stopped = False
        self.error: Exception | None = None

    def read(self) -> None:
        try:
            while True:
                size = struct.unpack("!I", read_exact(sys.stdin.buffer, 4))[0]
                if not 0 < size <= MAX_HEADER_BYTES:
                    raise ValueError("Invalid request header size")
                message = decode_header(read_exact(sys.stdin.buffer, size))
                if message.get("payload_bytes") or message.get("epoch") != self.epoch:
                    raise ValueError("Invalid preview request epoch or payload")
                request_id = message.get("id")
                if type(request_id) is not int or request_id <= 0:
                    raise ValueError("Invalid preview request ID")
                with self.condition:
                    if message.get("op") == "cancel":
                        self.cancel_id = max(self.cancel_id, request_id)
                    elif message.get("op") == "render" and request_id > self.latest_id:
                        self.latest_id = request_id
                        self.latest = message
                    else:
                        raise ValueError("Invalid or nonmonotonic preview operation")
                    self.condition.notify_all()
        except EOFError:
            pass
        except Exception as error:
            self.error = error
        finally:
            with self.condition:
                self.stopped = True
                self.condition.notify_all()

    def cancelled(self, request_id: int) -> bool:
        with self.condition:
            return self.stopped or self.latest_id > request_id or self.cancel_id >= request_id


def validate_request(request: dict[str, Any]) -> None:
    for field in ("width", "height", "project_tick"):
        if type(request.get(field)) is not int or request[field] < 0:
            raise ValueError(f"Invalid preview {field}")
    if (
        not request["width"]
        or not request["height"]
        or request["width"] * request["height"] * 4 > MAX_FRAME_BYTES
    ):
        raise ValueError("Preview canvas exceeds its protocol limit")
    slots = request.get("slots")
    if not isinstance(slots, list) or not 1 <= len(slots) <= 4:
        raise ValueError("Preview requires one through four active slots")
    for slot in slots:
        if (
            not isinstance(slot.get("path"), str)
            or type(slot.get("source_tick")) is not int
            or slot["source_tick"] < 0
        ):
            raise ValueError("Invalid preview physical source")
        for field in ("x", "y"):
            if type(slot.get(field)) is not int or slot[field] < 0:
                raise ValueError("Invalid preview slot origin")
        if not isinstance(slot.get("crops"), list) or len(slot["crops"]) not in (1, 3):
            raise ValueError("Invalid preview crop count")
        for crop in slot["crops"]:
            for field in ("scaled_width", "scaled_height", "width", "height", "crop_x", "crop_y"):
                if type(crop.get(field)) is not int or crop[field] < 0:
                    raise ValueError("Invalid preview crop geometry")
            if (
                min(crop["scaled_width"], crop["scaled_height"], crop["width"], crop["height"]) <= 0
                or max(crop["scaled_width"], crop["scaled_height"]) > 32768
            ):
                raise ValueError("Preview crop exceeds its native resource limit")


def main() -> None:
    engine, epoch = sys.argv[1:]

    def send(header: dict[str, Any], payload: bytes = b"") -> None:
        sys.stdout.buffer.write(encode_message(dict(header, epoch=epoch), payload))
        sys.stdout.buffer.flush()

    try:
        import av
    except ModuleNotFoundError as error:
        if error.name != "av":
            raise
        send({"status": "missing_dependency", "dependency": "av"})
        return
    if av.__version__ != AV_VERSION:
        send({"status": "error", "error": f"Precise preview requires av=={AV_VERSION}"})
        return
    from framestudio.precise_preview_native import DecodeCancelled, DecoderPool, UnsupportedSource

    # Exclude long-lived imports from per-render collection, never live decoders or graphs.
    gc.collect()
    gc.freeze()
    limit = rss_limit()
    send({"status": "ready", "protocol": PROTOCOL_VERSION, "av_version": av.__version__})
    inbox = Inbox(epoch)
    threading.Thread(target=inbox.read, name="preview-control", daemon=True).start()
    pool = DecoderPool(engine, max_cuda_contexts=5 if limit >= 1536 * 1024 * 1024 else 2)
    try:
        while True:
            with inbox.condition:
                inbox.condition.wait_for(lambda: inbox.latest is not None or inbox.stopped)
                if inbox.stopped:
                    return
                request, inbox.latest = inbox.latest, None
            if request is None:
                continue
            request_id = request["id"]
            try:
                validate_request(request)
                pixels, diagnostics = pool.render(
                    request, lambda request_id=request_id: inbox.cancelled(request_id)
                )
                if inbox.cancelled(request_id):
                    raise DecodeCancelled
                memory = rss_bytes()
                retire = memory > limit
                send(
                    {
                        "id": request_id,
                        "status": "frame",
                        **diagnostics,
                        "rss_bytes": memory,
                        "rss_limit_bytes": limit,
                        "retire": retire,
                    },
                    pixels,
                )
                if retire:
                    return
            except DecodeCancelled:
                send({"id": request_id, "status": "cancelled"})
            except UnsupportedSource as error:
                send(
                    {
                        "id": request_id,
                        "status": "unsupported",
                        "error": str(error),
                        "contexts": len(pool.contexts),
                        "context_opens": pool.opens,
                        "context_evictions": pool.evictions,
                    }
                )
            except Exception as error:
                send(
                    {
                        "id": request_id,
                        "status": "error",
                        "error": f"Exact preview failed: {type(error).__name__}: {error}",
                    }
                )
                return
    finally:
        pool.close()


if __name__ == "__main__":
    main()
