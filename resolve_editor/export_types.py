from __future__ import annotations

import math
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any

from .audio import AudioDecision
from .fps_policy import FrameRatePolicy, SourceRateDecision, canonical_rate
from .model import Segment
from .upscale_policy import UpscaleDecision, UpscalePolicy

_BOUNDARY_TOLERANCE = 1e-3
_DURATION_TOLERANCE = 0.05
_FAST_CONTAINERS = {"matroska", "mkv", "mov", "mp4"}
_FAST_VIDEO_CODECS = {"h264"}
_FAST_AUDIO_CODECS = {"aac"}
_DEFAULT_OUTPUT_WIDTH = 1920
_DEFAULT_OUTPUT_HEIGHT = 1080
_DEFAULT_OUTPUT_CONTAINER = "mp4"
_DEFAULT_OUTPUT_VIDEO_CODEC = "libx264"
_DEFAULT_OUTPUT_AUDIO_CODEC = "aac"
_DEFAULT_OUTPUT_PIXEL_FORMAT = "yuv420p"


class ExportPlanningError(RuntimeError):
    """Raised when an export plan cannot be safely determined."""


class ExportExecutionError(RuntimeError):
    """Raised when an export cannot be completed and verified safely."""


@dataclass(frozen=True)
class FfmpegProgress:
    frame: int
    fps: float | None
    out_time_seconds: float
    speed: str | None
    done: bool


@dataclass(frozen=True)
class ExportProgress:
    stage: str
    percent: float
    frame: int
    total_frames: int
    fps: float | None
    elapsed_seconds: float
    eta_seconds: float | None


ExportProgressCallback = Callable[[ExportProgress], None]


@dataclass(frozen=True)
class OutputPolicy:
    """Deterministic output profile for a set of source streams."""

    width: int
    height: int
    scaling_mode: str
    frame_rate: str
    timebase: str
    container: str
    video_codec: str
    audio_codec: str | None
    pixel_format: str
    audio_stream_present: bool
    requires_normalization: bool
    reason: str
    audio_sample_rate: int = 48000
    audio_channels: int = 2

    def to_dict(self) -> dict[str, Any]:
        return {
            "width": self.width,
            "height": self.height,
            "scaling_mode": self.scaling_mode,
            "frame_rate": self.frame_rate,
            "timebase": self.timebase,
            "container": self.container,
            "video_codec": self.video_codec,
            "audio_codec": self.audio_codec,
            "pixel_format": self.pixel_format,
            "audio_stream_present": self.audio_stream_present,
            "requires_normalization": self.requires_normalization,
            "reason": self.reason,
            "audio_sample_rate": self.audio_sample_rate,
            "audio_channels": self.audio_channels,
        }


def _metadata_int(value: Any, label: str) -> int:
    if isinstance(value, bool):
        raise ExportPlanningError(f"{label} must be a positive integer")
    try:
        parsed = int(value)
    except (TypeError, ValueError) as error:
        raise ExportPlanningError(f"{label} must be a positive integer") from error
    if parsed <= 0:
        raise ExportPlanningError(f"{label} must be a positive integer")
    return parsed


def _metadata_rate(value: Any, label: str) -> tuple[str, Fraction]:
    if not isinstance(value, str) or not value:
        raise ExportPlanningError(f"{label} must be a positive rational rate")
    try:
        parsed = Fraction(value)
    except (ValueError, ZeroDivisionError) as error:
        raise ExportPlanningError(f"{label} must be a positive rational rate") from error
    if parsed <= 0:
        raise ExportPlanningError(f"{label} must be a positive rational rate")
    return value, parsed


def resolve_output_policy(
    metadata: Sequence[Mapping[str, Any]],
    *,
    target_rate: Fraction | int | float | str | None = None,
) -> OutputPolicy:
    """Resolve a predictable canvas and timing profile for source metadata."""
    if not metadata:
        raise ExportPlanningError("At least one source is required for output policy")
    normalized: list[dict[str, Any]] = []
    for index, item in enumerate(metadata):
        if not isinstance(item, Mapping):
            raise ExportPlanningError(f"Source metadata at index {index} must be an object")
        width = _metadata_int(item.get("width"), f"Source {index + 1} width")
        height = _metadata_int(item.get("height"), f"Source {index + 1} height")
        frame_rate, rate_value = _metadata_rate(
            item.get("frame_rate"),
            f"Source {index + 1} frame rate",
        )
        audio_present = item.get("audio_stream_present")
        if audio_present is None:
            audio_present = item.get("audio_codec") is not None
        if not isinstance(audio_present, bool):
            raise ExportPlanningError(f"Source {index + 1} audio presence must be boolean")
        audio_codec = item.get("audio_codec")
        if audio_codec is not None and not isinstance(audio_codec, str):
            raise ExportPlanningError(f"Source {index + 1} audio codec is invalid")
        normalized.append(
            {
                "width": width,
                "height": height,
                "frame_rate": frame_rate,
                "rate_value": rate_value,
                "audio_present": audio_present,
            }
        )
    output_rate = (
        max(item["rate_value"] for item in normalized)
        if target_rate is None
        else canonical_rate(target_rate)
    )
    output_rate_text = (
        next(item["frame_rate"] for item in normalized if item["rate_value"] == output_rate)
        if target_rate is None
        else str(output_rate)
    )
    dimensions_differ = any(
        (item["width"], item["height"]) != (_DEFAULT_OUTPUT_WIDTH, _DEFAULT_OUTPUT_HEIGHT)
        for item in normalized
    )
    rates_differ = len({item["rate_value"] for item in normalized}) > 1
    audio_present = any(bool(item["audio_present"]) for item in normalized)
    scaling_mode = (
        "contain-letterbox" if dimensions_differ or len(normalized) > 1 else "source-native"
    )
    reasons = [
        "project output uses the fixed 1920x1080 render canvas",
        "render profile supplies container, codecs, and pixel format",
    ]
    if dimensions_differ:
        reasons.append("sources are contain-scaled to the project canvas")
    if rates_differ:
        reasons.append("source frame rates differ; current timing selection is provisional")
    if target_rate is not None:
        reasons.append("export target frame rate is selected by the project FPS policy")
    return OutputPolicy(
        width=_DEFAULT_OUTPUT_WIDTH,
        height=_DEFAULT_OUTPUT_HEIGHT,
        scaling_mode=scaling_mode,
        frame_rate=output_rate_text,
        timebase="1/1000000",
        container=_DEFAULT_OUTPUT_CONTAINER,
        video_codec=_DEFAULT_OUTPUT_VIDEO_CODEC,
        audio_codec=_DEFAULT_OUTPUT_AUDIO_CODEC if audio_present else None,
        pixel_format=_DEFAULT_OUTPUT_PIXEL_FORMAT,
        audio_stream_present=audio_present,
        requires_normalization=(len(normalized) > 1 or dimensions_differ or rates_differ),
        reason="; ".join(reasons),
    )


def _progress_float(value: str | None) -> float | None:
    if value is None:
        return None
    try:
        parsed = float(value)
    except ValueError:
        return None
    return parsed if math.isfinite(parsed) else None


def _progress_int(value: str | None) -> int:
    if value is None:
        return 0
    try:
        parsed = int(value)
    except ValueError:
        return 0
    return max(0, parsed)


def _progress_clock(value: str | None) -> float:
    if value is None:
        return 0.0
    parts = value.split(":")
    if len(parts) != 3:
        return 0.0
    try:
        hours, minutes, seconds = (float(part) for part in parts)
    except ValueError:
        return 0.0
    result = hours * 3600.0 + minutes * 60.0 + seconds
    return result if math.isfinite(result) and result >= 0 else 0.0


def parse_ffmpeg_progress_values(
    values: Mapping[str, str],
) -> FfmpegProgress:
    out_time_us = _progress_float(values.get("out_time_us"))
    if out_time_us is not None and out_time_us >= 0:
        out_time_seconds = out_time_us / 1_000_000.0
    else:
        out_time_ms = _progress_float(values.get("out_time_ms"))
        if out_time_ms is not None and out_time_ms >= 0:
            out_time_seconds = out_time_ms / 1_000_000.0
        else:
            out_time_seconds = _progress_clock(values.get("out_time"))
    fps = _progress_float(values.get("fps"))
    return FfmpegProgress(
        frame=_progress_int(values.get("frame")),
        fps=fps if fps is None or fps >= 0 else None,
        out_time_seconds=out_time_seconds,
        speed=values.get("speed") or None,
        done=values.get("progress") == "end",
    )


@dataclass(frozen=True)
class ExportPlan:
    route: str
    source: Path
    destination: Path
    segments: tuple[Segment, ...]
    expected_duration_seconds: float
    reason: str
    fallback_video_codec: str | None = None
    fallback_audio_codec: str | None = None
    fallback_container: str | None = None
    fallback_pixel_format: str | None = None
    source_paths: tuple[Path, ...] = ()
    source_ids: tuple[str, ...] = ()
    output_policy: OutputPolicy | None = None
    audio_decisions: tuple[tuple[str, AudioDecision | dict[str, Any]], ...] = ()
    frame_rate_policy: FrameRatePolicy | dict[str, Any] | None = None
    rate_decisions: tuple[SourceRateDecision | dict[str, Any], ...] = ()
    upscale_policy: UpscalePolicy | dict[str, Any] | None = None
    upscale_decisions: tuple[UpscaleDecision | dict[str, Any], ...] = ()
    estimate: dict[str, Any] | None = None

    @property
    def is_fast_path(self) -> bool:
        return self.route == "stream-copy"

    def to_dict(self) -> dict[str, Any]:
        return {
            "route": self.route,
            "source": str(self.source),
            "destination": str(self.destination),
            "segments": [segment.to_dict() for segment in self.segments],
            "expected_duration_seconds": self.expected_duration_seconds,
            "reason": self.reason,
            "fallback_video_codec": self.fallback_video_codec,
            "fallback_audio_codec": self.fallback_audio_codec,
            "fallback_container": self.fallback_container,
            "fallback_pixel_format": self.fallback_pixel_format,
            "source_paths": [str(path) for path in self.source_paths],
            "source_ids": list(self.source_ids),
            "output_policy": (None if self.output_policy is None else self.output_policy.to_dict()),
            "audio_decisions": {
                source_id: (
                    decision.to_dict() if isinstance(decision, AudioDecision) else dict(decision)
                )
                for source_id, decision in self.audio_decisions
            },
            "frame_rate_policy": (
                None
                if self.frame_rate_policy is None
                else (
                    self.frame_rate_policy.to_dict()
                    if isinstance(self.frame_rate_policy, FrameRatePolicy)
                    else dict(self.frame_rate_policy)
                )
            ),
            "rate_decisions": [
                decision.to_dict() if isinstance(decision, SourceRateDecision) else dict(decision)
                for decision in self.rate_decisions
            ],
            "upscale_policy": (
                None
                if self.upscale_policy is None
                else (
                    self.upscale_policy.to_dict()
                    if isinstance(self.upscale_policy, UpscalePolicy)
                    else dict(self.upscale_policy)
                )
            ),
            "upscale_decisions": [
                decision.to_dict() if isinstance(decision, UpscaleDecision) else dict(decision)
                for decision in self.upscale_decisions
            ],
            "estimate": None if self.estimate is None else dict(self.estimate),
        }
