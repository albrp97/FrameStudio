"""Native objects owned exclusively by the disposable preview helper."""

from __future__ import annotations

import gc
import importlib
import os
import time
from collections import OrderedDict, deque
from fractions import Fraction
from pathlib import Path
from typing import Any

import av

from .preview_acceleration import supported_color


class DecodeCancelled(Exception):
    pass


class UnsupportedSource(Exception):
    pass


def identity(path: Path) -> tuple[Any, ...]:
    stat = path.stat()
    return str(path.resolve()), stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns


def nearest(value: Fraction) -> int:
    if value < 0:
        return -nearest(-value)
    return (value.numerator * 2 + value.denominator) // (value.denominator * 2)


class Decoder:
    FORWARD_MAX_FRAMES = 32
    FORWARD_MAX_SECONDS = Fraction(2)
    MAX_PENDING_FRAMES = 2

    def __init__(self, path: Path, container: Any, engine: str, reason: str) -> None:
        self.path = path
        self.container = container
        self.stream = container.streams.video[0]
        self.engine = engine
        self.reason = reason
        self.origin_tick = int(container.start_time or 0)
        if not self.stream.time_base or self.stream.time_base <= 0:
            raise ValueError("Source has no usable video time base")
        if engine == "cpu":
            self.stream.codec_context.thread_count = max(1, min(16, os.cpu_count() or 1))
            self.stream.codec_context.thread_type = "FRAME"
        else:
            self.stream.codec_context.thread_count = 1
        self._packets: Any = None
        self._pending: deque[Any] = deque()
        self._last_position: Fraction | None = None
        self.seeks = 0
        self.forward_reuses = 0
        self.decoded_frames = 0

    def _reset_forward(self) -> None:
        self._pending.clear()
        packets, self._packets = self._packets, None
        self._last_position = None
        if packets is not None:
            packets.close()

    def close(self) -> None:
        self._reset_forward()
        self.container.close()
        self.stream = None
        self.container = None

    def frame(self, source_tick: int, cancelled: Any) -> tuple[Any, dict[str, Any]]:
        try:
            return self._frame(source_tick, cancelled)
        except BaseException:
            self._reset_forward()
            raise

    def _frame(self, source_tick: int, cancelled: Any) -> tuple[Any, dict[str, Any]]:
        if cancelled():
            raise DecodeCancelled
        time_base = self.stream.time_base
        target_pts = nearest(Fraction(source_tick + self.origin_tick, 1_000_000) / time_base)
        target = target_pts * time_base
        rate = self.stream.average_rate
        gap = target - self._last_position if self._last_position is not None else None
        forward = bool(
            self._packets is not None
            and gap is not None
            and rate
            and rate > 0
            and 0 < gap <= min(self.FORWARD_MAX_SECONDS, Fraction(self.FORWARD_MAX_FRAMES) / rate)
        )
        if forward:
            self.forward_reuses += 1
        else:
            self._reset_forward()
            self.container.seek(target_pts, stream=self.stream, backward=True, any_frame=False)
            self.seeks += 1
            self._packets = self.container.demux(self.stream)
        while True:
            if cancelled():
                raise DecodeCancelled
            can_continue = True
            if not self._pending:
                packet = next(self._packets, None)
                if packet is None:
                    raise ValueError("Source ended before the requested exact preview frame")
                # Evaluate against THIS request, not the target that created
                # the retained demux iterator. Future pictures must survive.
                if self.stream.codec_context.name == "h264":
                    self.stream.codec_context.skip_frame = (
                        "NONREF"
                        if packet.pts is not None
                        and packet.time_base is not None
                        and packet.pts * packet.time_base < target
                        else "DEFAULT"
                    )
                decoded = packet.decode()
                self.decoded_frames += len(decoded)
                # A flush can release a whole thread-delayed GOP. Do not pin
                # it between requests (in particular hardware-owned surfaces).
                can_continue = len(decoded) <= self.MAX_PENDING_FRAMES
                self._pending.extend(decoded)
                del decoded
            while self._pending:
                frame = self._pending.popleft()
                if cancelled():
                    raise DecodeCancelled
                if frame.pts is None or frame.time_base is None:
                    raise ValueError("Decoded source frame has no physical timestamp")
                position = frame.pts * frame.time_base
                if position < target:
                    continue
                sar = (
                    self.stream.sample_aspect_ratio
                    or self.stream.codec_context.sample_aspect_ratio
                    or Fraction(1)
                )
                if sar <= 0:
                    raise ValueError("Source has an invalid sample aspect ratio")
                if not can_continue:
                    self._reset_forward()
                else:
                    # compose() mutates frame.pts; never retain the selected
                    # frame itself as our continuity marker.
                    self._last_position = position
                return frame, {
                    "pts": frame.pts,
                    "time_base_num": frame.time_base.numerator,
                    "time_base_den": frame.time_base.denominator,
                    "source_tick": source_tick,
                    "origin_tick": self.origin_tick,
                    "effective_target_pts": target_pts,
                    "engine": self.engine,
                    "reason": self.reason,
                    "nonref_enabled": self.stream.codec_context.name == "h264",
                    "decoder_threads": self.stream.codec_context.thread_count,
                    "sar_num": sar.numerator,
                    "sar_den": sar.denominator,
                    "forward_reused": forward,
                    "forward_reuses": self.forward_reuses,
                    "seeks": self.seeks,
                    "decoded_frames": self.decoded_frames,
                    "pending_frames": len(self._pending),
                }


class DecoderPool:
    MAX_CONTEXTS = 2
    MAX_CUDA_CONTEXTS = 5

    def __init__(self, engine: str, *, max_cuda_contexts: int = MAX_CUDA_CONTEXTS) -> None:
        if type(max_cuda_contexts) is not int or not 1 <= max_cuda_contexts <= 5:
            raise ValueError("CUDA preview residency must be between one and five contexts")
        self.engine = engine
        self.max_cuda_contexts = max_cuda_contexts
        self.contexts: OrderedDict[tuple[Any, ...], Decoder] = OrderedDict()
        self.device: Any = None
        self.acceleration: Any = None
        self.cuda_reason = "CPU explicitly selected"
        self.cuda_attempted = False
        self.opens = 0
        self.evictions = 0
        self.composition = CompositionCache()

    def _trim_contexts(self, maximum: int) -> None:
        while len(self.contexts) > maximum:
            _, old = self.contexts.popitem(last=False)
            old.close()
            self.evictions += 1

    def _device(self, stream: Any) -> None:
        if self.engine == "cpu":
            return
        if self.acceleration is None:
            try:
                self.acceleration = importlib.import_module("framestudio.preview_acceleration")
            except ModuleNotFoundError as error:
                if error.name != "framestudio.preview_acceleration":
                    raise
                self.cuda_reason = "CUDA integration is unavailable; selected CPU"
                return
        if not self.acceleration.is_eligible(stream):
            self.cuda_reason = "Source is not eligible for exact CUDA preview; selected CPU"
            return
        if self.cuda_attempted:
            return
        self.cuda_attempted = True
        try:
            self.device = self.acceleration.CudaDeviceSession()
        except self.acceleration.CudaUnavailable as error:
            self.cuda_reason = f"CUDA unavailable; selected CPU: {error}"

    def get(self, path: Path, width: int, height: int) -> tuple[Decoder, tuple[Any, ...], float]:
        key = (*identity(path), 0, width, height, self.engine)
        if key in self.contexts:
            self.contexts.move_to_end(key)
            return self.contexts[key], key, 0.0
        # A changed stat identity must retire the old physical path too.
        for old_key in list(self.contexts):
            if old_key[0] == key[0]:
                self.contexts.pop(old_key).close()
                self.evictions += 1
        started = time.perf_counter()
        container = av.open(str(path), timeout=(5.0, 5.0))
        try:
            stream: Any = container.streams.video[0]
            codec = stream.codec_context
            if not supported_color(codec):
                raise UnsupportedSource(
                    "Source color metadata is outside the proven native composition policy; "
                    "selected reference FFmpeg"
                )
            self._device(stream)
            engine = "cpu"
            reason = self.cuda_reason
            if self.device is not None:
                if self.acceleration.is_eligible(stream):
                    container.close()
                    stream = None
                    try:
                        container = self.device.open(path)
                    except self.acceleration.CudaUnavailable as error:
                        container = av.open(str(path), timeout=(5.0, 5.0))
                        reason = f"CUDA source unavailable; selected CPU: {error}"
                    else:
                        engine = "cuda"
                        reason = "Eligible H264 source; CUDA hardware decoder selected"
                else:
                    reason = "Source is not eligible for exact CUDA preview; selected CPU"
            maximum = (
                self.max_cuda_contexts
                if engine == "cuda"
                and all(value.engine == "cuda" for value in self.contexts.values())
                else self.MAX_CONTEXTS
            )
            self._trim_contexts(maximum - 1)
            decoder = Decoder(path, container, engine, reason)
        except BaseException:
            container.close()
            raise
        self.contexts[key] = decoder
        self.opens += 1
        return decoder, key, (time.perf_counter() - started) * 1000

    def close(self) -> None:
        self.composition.clear()
        for decoder in self.contexts.values():
            decoder.close()
        self.contexts.clear()
        if self.device is not None:
            self.device.close()
            self.device = None
        gc.collect()

    def render(self, request: dict[str, Any], cancelled: Any) -> tuple[bytes, dict[str, Any]]:
        try:
            return self._render(request, cancelled)
        except BaseException:
            self.composition.clear()
            gc.collect()
            raise

    def _render(self, request: dict[str, Any], cancelled: Any) -> tuple[bytes, dict[str, Any]]:
        frames = []
        physical = []
        source_keys = []
        for slot in request["slots"]:
            if cancelled():
                raise DecodeCancelled
            path = Path(slot["path"])
            decoder, key, open_ms = self.get(path, request["width"], request["height"])
            frame, timestamp = decoder.frame(slot["source_tick"], cancelled)
            timestamp["open_ms"] = open_ms
            if not supported_color(frame):
                raise UnsupportedSource(
                    "Decoded source color metadata is outside the proven native composition "
                    "policy; selected reference FFmpeg"
                )
            if decoder.engine == "cuda":
                try:
                    frame = self.acceleration.normalize_frame(frame)
                except self.acceleration.CudaUnavailable as error:
                    decoder.close()
                    decoder = Decoder(
                        path,
                        av.open(str(path), timeout=(5.0, 5.0)),
                        "cpu",
                        f"CUDA frame unsupported; selected CPU: {error}",
                    )
                    self.contexts[key] = decoder
                    self.contexts.move_to_end(key)
                    self._trim_contexts(self.MAX_CONTEXTS)
                    frame, timestamp = decoder.frame(slot["source_tick"], cancelled)
                    timestamp["open_ms"] = open_ms
                    if not supported_color(frame):
                        raise UnsupportedSource(
                            "Decoded source color metadata is outside the proven native composition "
                            "policy; selected reference FFmpeg"
                        ) from error
            timestamp["source_color"] = {
                "colorspace": frame.colorspace,
                "range": frame.color_range,
                "primaries": frame.color_primaries,
                "transfer": frame.color_trc,
            }
            slot["source_sar"] = f"{timestamp['sar_num']}/{timestamp['sar_den']}"
            frames.append(frame)
            physical.append(timestamp)
            source_keys.append((path, key[:5]))
        if cancelled():
            raise DecodeCancelled
        self.composition.set_capacity(
            self.max_cuda_contexts
            if all(frame["engine"] == "cuda" for frame in physical)
            else self.MAX_CONTEXTS
        )
        try:
            pixels = compose(
                request,
                frames,
                cache=self.composition,
                source_identity=source_keys[0][1] if len(source_keys) == 1 else None,
            )
        finally:
            # PyAV graph/filter nodes form cycles holding native queues and
            # threads. Collect retired graphs after EACH render.
            gc.collect()
        if cancelled():
            raise DecodeCancelled
        if any(identity(path) != key for path, key in source_keys):
            raise ValueError("Source changed while decoding its preview")
        return pixels, {
            "physical_frames": physical,
            "contexts": len(self.contexts),
            "context_opens": self.opens,
            "context_evictions": self.evictions,
            "composition_contexts": len(self.composition.contexts),
            "composition_opens": self.composition.opens,
            "composition_reuses": self.composition.reuses,
        }


def _source_buffer(graph: Any, frame: Any, slot: dict[str, Any]) -> Any:
    # add_buffer(template=...) omits link color/range during configure.
    return graph.add(
        "buffer",
        video_size=f"{frame.width}x{frame.height}",
        pix_fmt=frame.format.name,
        time_base=str(frame.time_base),
        pixel_aspect=slot["source_sar"],
        colorspace=str(int(frame.colorspace)),
        range=str(int(frame.color_range)),
    )


def _cropped(graph: Any, source: Any, crop: dict[str, int], output: int = 0) -> Any:
    scale = graph.add("scale", f"{crop['scaled_width']}:{crop['scaled_height']}:flags=lanczos")
    source.link_to(scale, output, 0)
    clip = graph.add(
        "crop",
        f"{crop['width']}:{crop['height']}:{crop['crop_x']}:{crop['crop_y']}",
    )
    sar = graph.add("setsar", "1")
    rgba = graph.add("format", "rgba")
    graph.link_nodes(scale, clip, sar, rgba)
    return rgba


def _packed_pixels(result: Any, width: int, height: int) -> bytes:
    plane = result.planes[0]
    raw = bytes(plane)
    row_bytes = width * 4
    if plane.line_size == row_bytes:
        return raw[: row_bytes * height]
    return b"".join(
        raw[row * plane.line_size : row * plane.line_size + row_bytes] for row in range(height)
    )


def _opaque_canvas(request: dict[str, Any], frames: list[Any]) -> bool:
    slots = request["slots"]
    return (
        len(slots) == 1
        and len(frames) == 1
        and len(slots[0]["crops"]) == 1
        and slots[0]["x"] == slots[0]["y"] == 0
        and slots[0]["crops"][0]["width"] == request["width"]
        and slots[0]["crops"][0]["height"] == request["height"]
        and frames[0].format.name in ("yuv420p", "nv12", "yuvj420p")
    )


def _opaque_graph(request: dict[str, Any], frame: Any, threads: int) -> tuple[Any, Any]:
    graph = av.filter.Graph()
    graph.threads = threads
    buffer = _source_buffer(graph, frame, request["slots"][0])
    rendered = _cropped(graph, buffer, request["slots"][0]["crops"][0])
    # Preserve the general overlay's color roundtrip, even without its black input.
    alpha = graph.add("format", "yuva420p")
    planar = graph.add("format", "yuv420p")
    output = graph.add("format", "rgba")
    sink = graph.add("buffersink")
    graph.link_nodes(rendered, alpha, planar, output, sink)
    graph.configure()
    return graph, buffer


class CompositionCache:
    MAX_CONTEXTS = 2

    def __init__(self) -> None:
        self.threads = max(1, min(4, os.cpu_count() or 1))
        self.capacity = self.MAX_CONTEXTS
        self.contexts: OrderedDict[tuple[Any, ...], tuple[Any, Any]] = OrderedDict()
        self.opens = 0
        self.reuses = 0

    def clear(self) -> None:
        self.contexts.clear()

    def set_capacity(self, capacity: int) -> None:
        if type(capacity) is not int or not 1 <= capacity <= 5:
            raise ValueError("Composition residency must be between one and five contexts")
        self.capacity = capacity
        while len(self.contexts) > capacity:
            self.contexts.popitem(last=False)

    def render(
        self, request: dict[str, Any], frame: Any, source_identity: tuple[Any, ...]
    ) -> bytes:
        slot = request["slots"][0]
        key = (
            source_identity,
            frame.width,
            frame.height,
            frame.format.name,
            frame.time_base,
            frame.colorspace,
            frame.color_primaries,
            frame.color_trc,
            frame.color_range,
            frame.chroma_location,
            frame.rotation,
            frame.interlaced_frame,
            slot["source_sar"],
            tuple(sorted(slot["crops"][0].items())),
            request["width"],
            request["height"],
            self.threads,
        )
        if key in self.contexts:
            self.contexts.move_to_end(key)
            self.reuses += 1
        else:
            for previous in list(self.contexts):
                if previous[0][0] == source_identity[0]:
                    del self.contexts[previous]
            while len(self.contexts) >= self.capacity:
                self.contexts.popitem(last=False)
            self.contexts[key] = _opaque_graph(request, frame, self.threads)
            self.opens += 1
        graph, buffer = self.contexts[key]
        # Only stateless scale/crop/color filters: physical PTS may go backward.
        # Do not send EOF or retain an unconsumed picture between requests.
        buffer.push(frame)
        return _packed_pixels(graph.vpull(), request["width"], request["height"])


def compose(
    request: dict[str, Any],
    frames: list[Any],
    *,
    cache: CompositionCache | None = None,
    source_identity: tuple[Any, ...] | None = None,
) -> bytes:
    if not _opaque_canvas(request, frames):
        if cache is not None:
            cache.clear()
        return _compose_general(request, frames)
    if cache is not None:
        if source_identity is None:
            raise ValueError("Retained composition requires physical source identity")
        return cache.render(request, frames[0], source_identity)
    graph, buffer = _opaque_graph(request, frames[0], 2)
    frames[0].pts = 0
    buffer.push(frames[0])
    buffer.push(None)
    return _packed_pixels(graph.vpull(), request["width"], request["height"])


def _compose_general(request: dict[str, Any], frames: list[Any]) -> bytes:
    graph = av.filter.Graph()
    graph.threads = 2
    color = graph.add("color", f"c=black:s={request['width']}x{request['height']}:r=1:d=1")
    composed = graph.add("format", "rgba")
    color.link_to(composed)
    buffers = []

    for slot, frame in zip(request["slots"], frames, strict=True):
        buffer = _source_buffer(graph, frame, slot)
        buffers.append(buffer)
        crops = slot["crops"]
        if len(crops) == 3:
            split = graph.add("split", "3")
            buffer.link_to(split)
            stack = graph.add("hstack", "inputs=3:shortest=1")
            for index, crop in enumerate(crops):
                _cropped(graph, split, crop, index).link_to(stack, 0, index)
            rendered = stack
        else:
            rendered = _cropped(graph, buffer, crops[0])
        overlay = graph.add("overlay", f"x={slot['x']}:y={slot['y']}:eof_action=pass:shortest=1")
        composed.link_to(overlay, 0, 0)
        rendered.link_to(overlay, 0, 1)
        composed = overlay
    output = graph.add("format", "rgba")
    sink = graph.add("buffersink")
    graph.link_nodes(composed, output, sink)
    graph.configure()
    for buffer, frame in zip(buffers, frames, strict=True):
        frame.pts = 0
        buffer.push(frame)
        buffer.push(None)
    return _packed_pixels(graph.vpull(), request["width"], request["height"])
