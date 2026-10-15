"""Optional, conservative H264 CUDA primitives for the isolated preview worker.

The caller owns returned containers and must close its bounded decoder pool
before closing the device session. Neither importing this module nor testing
eligibility loads PyAV, initializes CUDA, or decodes media.
"""

from __future__ import annotations

from importlib import import_module
from math import isfinite
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import av


class CudaUnavailable(RuntimeError):
    """A known CUDA capability is unavailable; an explicit fallback is needed."""


def _load_runtime() -> tuple[Any, Any, Any]:
    try:
        runtime = import_module("av")
    except ModuleNotFoundError as error:
        if error.name != "av":
            raise
        raise CudaUnavailable("Optional PyAV preview runtime is not installed") from error
    hardware = import_module("av.codec.hwaccel")
    accel = getattr(hardware, "HWAccel", None)
    device = getattr(hardware, "HWDevice", None)
    if not callable(accel) or not callable(device):
        raise CudaUnavailable("PyAV does not expose the required CUDA device API")
    return runtime, accel, device


def _positive(value: Any) -> bool:
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        return False
    return isfinite(number) and number > 0


def supported_color(value: object) -> bool:
    """Share the verified CPU/CUDA color policy without importing optional PyAV.

    Read matrix/primaries/TRC/range from a frame or codec context. Only untagged
    (2,2,2,0), BT709 limited (1,1,1,1), and BT709 full (1,1,1,2) are supported.
    Missing attributes, unknown range on BT709, and mixed tags are rejected.
    """
    metadata = tuple(
        getattr(value, name, None)
        for name in ("colorspace", "color_primaries", "color_trc", "color_range")
    )
    return metadata in ((2, 2, 2, 0), (1, 1, 1, 1), (1, 1, 1, 2))


def _supported_stream_metadata(stream: Any) -> bool:
    codec = stream.codec_context
    rates = (stream.average_rate, stream.base_rate, stream.guessed_rate)
    rotation = stream.metadata.get("rotate", "0")
    try:
        zero_rotation = isfinite(float(rotation)) and float(rotation) == 0
    except (TypeError, ValueError, OverflowError):
        return False
    return (
        codec.name == "h264"
        and supported_color(codec)
        and stream.start_time == 0
        and _positive(stream.time_base)
        and _positive(stream.duration)
        and all(_positive(rate) for rate in rates)
        and rates[0] == rates[1] == rates[2]
        and stream.sample_aspect_ratio in (None, 1)
        and codec.sample_aspect_ratio in (None, 1)
        and zero_rotation
    )


def is_eligible(stream: av.video.stream.VideoStream) -> bool:
    """Accept only preflight software H264/yuv420p with tested metadata.

    Color support is exactly untagged (2,2,2,0) or BT709 matrix/primaries/TRC
    (1,1,1) with limited/full range (1/2). The compositor must initialize buffer
    links with these actual colorspace/range values before graph configuration.
    Other tags, uncertain/nonzero timestamps, unknown/mismatched rates,
    non-square pixels and declared rotation use the reference fallback.
    Matching rates are not a full-media CFR scan; decoded frame-only display
    matrices and interlace are rejected by normalize_frame.
    """
    codec = stream.codec_context
    return (
        codec.format is not None
        and (
            codec.format.name == "yuv420p"
            or (codec.format.name == "yuvj420p" and codec.color_range == 2)
        )
        and _supported_stream_metadata(stream)
    )


def _frame_metadata(frame: av.VideoFrame) -> tuple[Any, ...]:
    return (
        *(
            getattr(frame, name)
            for name in (
                "pts",
                "dts",
                "duration",
                "time_base",
                "width",
                "height",
                "colorspace",
                "color_range",
                "color_primaries",
                "color_trc",
                "rotation",
                "interlaced_frame",
            )
        ),
        tuple((item.type.name, bytes(item)) for item in frame.side_data.values()),
    )


def normalize_frame(frame: av.VideoFrame) -> av.VideoFrame:
    """Download only the selected CUDA surface, preserving actual frame metadata.

    No hardware frames are cached here. The caller must release discarded
    decode batches and replace its selected surface with this host result.
    """
    if (
        frame.format.name not in ("cuda", "nv12", "yuv420p")
        or not supported_color(frame)
        or frame.pts is None
        or not _positive(frame.time_base)
        or frame.rotation != 0
        or frame.interlaced_frame
        or any(item.type.name == "DISPLAYMATRIX" for item in frame.side_data.values())
    ):
        raise CudaUnavailable("Decoded CUDA frame has unsupported preview metadata")
    metadata = _frame_metadata(frame)
    if frame.format.name == "cuda":
        runtime = import_module("av")
        try:
            # PyAV 19 transfers the hardware surface before its no-op NV12
            # reformat. Keep planar normalization identical to auto-download.
            frame = frame.reformat(format="nv12")
        except (runtime.FFmpegError, NotImplementedError, ValueError) as error:
            raise CudaUnavailable("Selected CUDA frame download failed") from error
        if frame.format.name != "nv12" or _frame_metadata(frame) != metadata:
            raise CudaUnavailable("CUDA download did not preserve source metadata")
    if frame.format.name == "yuv420p":
        return frame
    result = frame.reformat(format="yuv420p")
    if result.format.name != "yuv420p" or _frame_metadata(result) != metadata:
        raise CudaUnavailable("CUDA host normalization did not preserve source metadata")
    return result


class CudaDeviceSession:
    """Retain the primary CUDA device independently of per-source decoder LRU.

    A first device initialization still has a cost. Subsequent source opens
    retain that primary context rather than creating private CUDA contexts.
    Returned containers are caller-owned; this session does not accumulate
    closed container handles as sources are evicted.
    """

    def __init__(self) -> None:
        self._runtime, accel, device = _load_runtime()
        self._device: Any = None
        self._accel: Any = None
        self._closed = True
        try:
            self._device = device("cuda", options={"primary_ctx": "1"})
            self._accel = accel(
                "cuda",
                options={"primary_ctx": "1"},
                allow_software_fallback=False,
                is_hw_owned=True,
            )
        except (self._runtime.FFmpegError, NotImplementedError, ValueError) as error:
            self.close()
            raise CudaUnavailable("CUDA primary device initialization failed") from error
        self._closed = False

    def open(self, path: Path) -> av.container.InputContainer:
        """Open a preflight-eligible source; never silently decode on the CPU."""
        if self._closed:
            raise RuntimeError("CUDA device session is closed")
        try:
            container: av.container.InputContainer = self._runtime.open(
                str(path), hwaccel=self._accel
            )
        except NotImplementedError as error:
            raise CudaUnavailable("No supported CUDA hardware decoder for source") from error
        videos = container.streams.video
        if not videos or videos[0].codec_context.is_hwaccel is not True:
            container.close()
            raise CudaUnavailable("CUDA hardware decoding is not active")
        if not _supported_stream_metadata(videos[0]):
            container.close()
            raise CudaUnavailable("Source metadata is outside the CUDA preview policy")
        return container

    def close(self) -> None:
        """Release this device reference after the caller closes its containers."""
        self._closed = True
        self._accel = None
        self._device = None
