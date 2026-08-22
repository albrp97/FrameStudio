from __future__ import annotations

import json
import math
import subprocess
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any


class MediaProbeError(RuntimeError):
    """Raised when a source cannot be probed into editor metadata."""


@dataclass(frozen=True)
class MediaProbe:
    path: Path
    duration_seconds: float
    width: int
    height: int
    frame_rate: str
    video_codec: str
    audio_codec: str | None
    format_name: str
    audio_stream_present: bool | None = None

    def metadata(self) -> dict[str, Any]:
        orientation = (
            "portrait"
            if self.height > self.width
            else "landscape"
            if self.width > self.height
            else "square"
        )
        return {
            "duration_seconds": self.duration_seconds,
            "width": self.width,
            "height": self.height,
            "orientation": orientation,
            "frame_rate": self.frame_rate,
            "video_codec": self.video_codec,
            "audio_codec": self.audio_codec,
            "audio_stream_present": self.has_audio_stream,
            "format_name": self.format_name,
        }

    @property
    def has_audio_stream(self) -> bool:
        if self.audio_stream_present is not None:
            return self.audio_stream_present
        return self.audio_codec is not None

    @property
    def frame_rate_value(self) -> float:
        try:
            rate = Fraction(self.frame_rate)
        except (ValueError, ZeroDivisionError) as error:
            raise MediaProbeError(
                f"Invalid frame rate for {self.path.name}: {self.frame_rate}"
            ) from error
        if rate <= 0:
            raise MediaProbeError(f"Invalid frame rate for {self.path.name}")
        return float(rate)


def _stream_rate(stream: dict[str, Any]) -> str | None:
    for key in ("avg_frame_rate", "r_frame_rate"):
        value = stream.get(key)
        if isinstance(value, str) and value not in {"", "0/0", "N/A"}:
            try:
                if Fraction(value) > 0:
                    return value
            except (ValueError, ZeroDivisionError):
                continue
    return None


def probe_media(path: Path, ffprobe_path: str = "ffprobe") -> MediaProbe:
    source = Path(path).expanduser().resolve()
    if not source.is_file():
        raise MediaProbeError(f"Source file does not exist: {source.name}")
    try:
        result = subprocess.run(
            [
                ffprobe_path,
                "-v",
                "error",
                "-print_format",
                "json",
                "-show_streams",
                "-show_format",
                str(source),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError as error:
        raise MediaProbeError(f"ffprobe is not installed or not on PATH: {ffprobe_path}") from error
    if result.returncode != 0:
        detail = result.stderr.strip() or "ffprobe could not read the source"
        raise MediaProbeError(f"Could not probe {source.name}: {detail}")
    try:
        data = json.loads(result.stdout)
        streams = data["streams"]
        video = next(stream for stream in streams if stream.get("codec_type") == "video")
    except (KeyError, StopIteration, TypeError, json.JSONDecodeError) as error:
        raise MediaProbeError(f"Could not read a video stream from {source.name}") from error
    duration_value = data.get("format", {}).get("duration")
    try:
        duration = float(duration_value)
    except (TypeError, ValueError) as error:
        raise MediaProbeError(f"Could not read duration from {source.name}") from error
    if not math.isfinite(duration) or duration <= 0:
        raise MediaProbeError(f"Source duration is invalid: {source.name}")
    try:
        width = int(video["width"])
        height = int(video["height"])
    except (KeyError, TypeError, ValueError) as error:
        raise MediaProbeError(f"Could not read video dimensions from {source.name}") from error
    if width <= 0 or height <= 0:
        raise MediaProbeError(f"Source dimensions are invalid: {source.name}")
    frame_rate = _stream_rate(video)
    if frame_rate is None:
        raise MediaProbeError(f"Could not read frame rate from {source.name}")
    video_codec = video.get("codec_name")
    if not isinstance(video_codec, str) or not video_codec:
        raise MediaProbeError(f"Could not read video codec from {source.name}")
    audio = next(
        (stream for stream in streams if stream.get("codec_type") == "audio"),
        None,
    )
    audio_codec = None if audio is None else audio.get("codec_name")
    if audio_codec is not None and not isinstance(audio_codec, str):
        audio_codec = None
    format_name = data.get("format", {}).get("format_name")
    if not isinstance(format_name, str):
        format_name = ""
    return MediaProbe(
        path=source,
        duration_seconds=duration,
        width=width,
        height=height,
        frame_rate=frame_rate,
        video_codec=video_codec,
        audio_codec=audio_codec,
        format_name=format_name,
        audio_stream_present=audio is not None,
    )
