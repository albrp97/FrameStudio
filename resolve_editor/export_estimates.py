from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from fractions import Fraction
from typing import Any

from .fps_policy import (
    FrameRatePolicy,
    ResolvedFrameRatePolicy,
    SourceRateDecision,
    canonical_rate,
    target_frame_count,
)

_OUTPUT_WIDTH = 1920
_OUTPUT_HEIGHT = 1080
_VIDEO_BITS_PER_PIXEL_FRAME = 0.08
_AUDIO_BITRATE = 192_000
_SIZE_LOWER_FACTOR = 0.65
_SIZE_UPPER_FACTOR = 1.5


@dataclass(frozen=True)
class CalibrationProfile:
    name: str
    interpolation_fps: float
    delivery_fps: float
    fixed_startup_seconds: float = 0.5
    per_input_seconds: float = 0.5
    fixed_verify_seconds: float = 0.5
    verification_probe_fps: float = 60.0
    sequential: bool = False

    def __post_init__(self) -> None:
        for label in (
            "interpolation_fps",
            "delivery_fps",
            "fixed_startup_seconds",
            "per_input_seconds",
            "fixed_verify_seconds",
            "verification_probe_fps",
        ):
            value = getattr(self, label)
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                raise ValueError(f"{label} must be numeric")
            if not math.isfinite(float(value)) or float(value) <= 0:
                raise ValueError(f"{label} must be greater than zero")


RVE_CALIBRATION = CalibrationProfile(
    name="rve-4.26-local",
    interpolation_fps=130.0,
    delivery_fps=180.0,
)
VS_RIFE_CALIBRATION = CalibrationProfile(
    name="vs-rife-local",
    interpolation_fps=55.0,
    delivery_fps=180.0,
)


def calibration_for_backend(backend: str) -> CalibrationProfile | None:
    normalized = backend.casefold().strip()
    if normalized in {"vs-rife", "rife", "vapoursynth-rife"}:
        return VS_RIFE_CALIBRATION
    if normalized.startswith("rve"):
        return RVE_CALIBRATION
    return None


def calibration_for_policy(
    policy: FrameRatePolicy | ResolvedFrameRatePolicy,
) -> CalibrationProfile | None:
    selected = policy.policy if isinstance(policy, ResolvedFrameRatePolicy) else policy
    if not selected.enhancement_enabled:
        return RVE_CALIBRATION
    return calibration_for_backend(selected.backend)


@dataclass(frozen=True)
class SourceWorkload:
    source_id: str
    duration_seconds: float
    source_rate: Fraction
    source_frames: int | None = None
    edited_duration_seconds: float | None = None
    audio_stream_present: bool = False
    width: int = _OUTPUT_WIDTH
    height: int = _OUTPUT_HEIGHT
    source_size_bytes: int | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.source_id, str) or not self.source_id:
            raise ValueError("Source workload needs a source identifier")
        if not math.isfinite(float(self.duration_seconds)) or self.duration_seconds <= 0:
            raise ValueError("Source workload duration must be greater than zero")
        object.__setattr__(self, "source_rate", canonical_rate(self.source_rate))
        if self.source_frames is not None and (
            isinstance(self.source_frames, bool)
            or not isinstance(self.source_frames, int)
            or self.source_frames <= 0
        ):
            raise ValueError("Source workload frame count must be a positive integer")
        if self.edited_duration_seconds is not None and (
            not math.isfinite(float(self.edited_duration_seconds))
            or self.edited_duration_seconds <= 0
        ):
            raise ValueError("Edited workload duration must be greater than zero")
        if not isinstance(self.audio_stream_present, bool):
            raise ValueError("Source workload audio presence must be boolean")
        for value, label in (
            (self.width, "Source workload width"),
            (self.height, "Source workload height"),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError(f"{label} must be a positive integer")
        if self.source_size_bytes is not None and (
            isinstance(self.source_size_bytes, bool)
            or not isinstance(self.source_size_bytes, int)
            or self.source_size_bytes < 0
        ):
            raise ValueError("Source workload size must be a non-negative integer")

    @property
    def resolved_source_frames(self) -> int:
        if self.source_frames is not None:
            return self.source_frames
        return _duration_frame_count(self.duration_seconds, self.source_rate)

    @property
    def resolved_edited_duration(self) -> float:
        return (
            self.duration_seconds
            if self.edited_duration_seconds is None
            else self.edited_duration_seconds
        )


@dataclass(frozen=True)
class ExportEstimate:
    input_count: int
    edited_duration_seconds: float
    target_rate: Fraction
    source_frames: int
    target_frames: int
    eligible_source_frames: int
    eligible_target_frames: int
    enhancement_duration_seconds: float
    preflight_seconds: float
    interpolation_seconds: float | None
    delivery_seconds: float | None
    verification_seconds: float | None
    total_seconds: float | None
    lower_seconds: float | None
    upper_seconds: float | None
    confidence: str
    assumptions: tuple[str, ...]
    calibration_name: str | None
    estimated_output_size_bytes: int
    estimated_output_size_lower_bytes: int
    estimated_output_size_upper_bytes: int

    def to_dict(self) -> dict[str, Any]:
        def rounded(value: float | None) -> float | None:
            return None if value is None else round(value, 3)

        return {
            "input_count": self.input_count,
            "edited_duration_seconds": round(self.edited_duration_seconds, 3),
            "target_rate": str(self.target_rate),
            "source_frames": self.source_frames,
            "target_frames": self.target_frames,
            "eligible_source_frames": self.eligible_source_frames,
            "eligible_target_frames": self.eligible_target_frames,
            "enhancement_duration_seconds": round(self.enhancement_duration_seconds, 3),
            "preflight_seconds": rounded(self.preflight_seconds),
            "interpolation_seconds": rounded(self.interpolation_seconds),
            "delivery_seconds": rounded(self.delivery_seconds),
            "verification_seconds": rounded(self.verification_seconds),
            "total_seconds": rounded(self.total_seconds),
            "lower_seconds": rounded(self.lower_seconds),
            "upper_seconds": rounded(self.upper_seconds),
            "confidence": self.confidence,
            "assumptions": list(self.assumptions),
            "calibration_name": self.calibration_name,
            "estimated_output_size_bytes": self.estimated_output_size_bytes,
            "estimated_output_size_lower_bytes": self.estimated_output_size_lower_bytes,
            "estimated_output_size_upper_bytes": self.estimated_output_size_upper_bytes,
        }


def _policy_and_decisions(
    policy: FrameRatePolicy | ResolvedFrameRatePolicy,
    decisions: Sequence[SourceRateDecision] | None,
) -> tuple[FrameRatePolicy, tuple[SourceRateDecision, ...]]:
    if isinstance(policy, ResolvedFrameRatePolicy):
        return policy.policy, tuple(policy.decisions)
    return policy, tuple(decisions or ())


def _fallback_range(
    *,
    base_seconds: float,
    eligible_target_frames: int,
    delivery_frames: int,
) -> tuple[float, float]:
    lower = base_seconds + delivery_frames / 240.0 + eligible_target_frames / 120.0
    upper = base_seconds + delivery_frames / 60.0 + eligible_target_frames / 20.0
    return lower, max(lower, upper)


def _duration_frame_count(duration_seconds: float, rate: Fraction) -> int:
    exact = Fraction(str(duration_seconds)) * rate
    return max(
        1,
        (exact.numerator + exact.denominator // 2) // exact.denominator,
    )


def _source_bits_per_pixel_frame(item: SourceWorkload) -> float:
    if item.source_size_bytes is None or item.source_size_bytes <= 0:
        return _VIDEO_BITS_PER_PIXEL_FRAME
    source_pixels = item.width * item.height
    source_bitrate = item.source_size_bytes * 8.0 / item.duration_seconds
    bits_per_pixel_frame = source_bitrate / (source_pixels * float(item.source_rate))
    if not math.isfinite(bits_per_pixel_frame) or bits_per_pixel_frame <= 0:
        return _VIDEO_BITS_PER_PIXEL_FRAME
    return max(0.035, min(0.14, bits_per_pixel_frame))


def _estimated_output_size(
    workloads: Sequence[SourceWorkload],
    target_rate: Fraction,
) -> tuple[int, int, int]:
    video_bits = sum(
        item.resolved_edited_duration
        * float(target_rate)
        * _OUTPUT_WIDTH
        * _OUTPUT_HEIGHT
        * _source_bits_per_pixel_frame(item)
        for item in workloads
    )
    edited_duration = sum(item.resolved_edited_duration for item in workloads)
    has_audio = any(item.audio_stream_present for item in workloads)
    audio_bits = edited_duration * _AUDIO_BITRATE if has_audio else 0.0
    estimate = max(1, round((video_bits + audio_bits) / 8.0))
    lower = max(1, round(estimate * _SIZE_LOWER_FACTOR))
    upper = max(lower, round(estimate * _SIZE_UPPER_FACTOR))
    return estimate, lower, upper


def estimate_export(
    workloads: Sequence[SourceWorkload],
    policy: FrameRatePolicy | ResolvedFrameRatePolicy,
    *,
    calibration: CalibrationProfile | None = RVE_CALIBRATION,
    decisions: Sequence[SourceRateDecision] | None = None,
) -> ExportEstimate:
    if not workloads:
        raise ValueError("At least one source workload is required")
    resolved_policy, resolved_decisions = _policy_and_decisions(policy, decisions)
    decision_by_id = {item.source_id: item for item in resolved_decisions}
    source_frames = sum(item.resolved_source_frames for item in workloads)
    edited_duration = sum(item.resolved_edited_duration for item in workloads)
    target_frames = sum(
        (
            target_frame_count(
                item.source_rate,
                item.resolved_source_frames,
                resolved_policy.target_rate,
            )
            if item.edited_duration_seconds is None
            else _duration_frame_count(
                item.resolved_edited_duration,
                resolved_policy.target_rate,
            )
        )
        for item in workloads
    )
    eligible_source_frames = 0
    eligible_target_frames = 0
    enhancement_duration = 0.0
    for item in workloads:
        decision = decision_by_id.get(item.source_id)
        eligible = (
            decision.eligible
            if decision is not None
            else (
                resolved_policy.enhancement_enabled
                and item.source_rate < resolved_policy.target_rate
            )
        )
        if eligible:
            eligible_source_frames += item.resolved_source_frames
            eligible_target_frames += target_frame_count(
                item.source_rate,
                item.resolved_source_frames,
                resolved_policy.target_rate,
            )
            enhancement_duration += item.duration_seconds
    estimated_size, size_lower, size_upper = _estimated_output_size(
        workloads,
        resolved_policy.target_rate,
    )
    preflight = 0.5 + 0.5 * len(workloads)
    assumptions = [
        "frame counts use rational source and target rates with half-up rounding",
        "enhancement processes each eligible input source once; delivery uses edited duration",
        "interpolation and delivery overlap unless the calibration is sequential",
        "estimate is local calibration evidence, not a hardware guarantee",
    ]
    if calibration is None:
        base = preflight + edited_duration / 60.0 + target_frames / 240.0
        lower, upper = _fallback_range(
            base_seconds=base,
            eligible_target_frames=eligible_target_frames,
            delivery_frames=target_frames,
        )
        assumptions.append("no matching calibration profile was available")
        return ExportEstimate(
            input_count=len(workloads),
            edited_duration_seconds=edited_duration,
            target_rate=resolved_policy.target_rate,
            source_frames=source_frames,
            target_frames=target_frames,
            eligible_source_frames=eligible_source_frames,
            eligible_target_frames=eligible_target_frames,
            enhancement_duration_seconds=enhancement_duration,
            preflight_seconds=preflight,
            interpolation_seconds=None,
            delivery_seconds=None,
            verification_seconds=None,
            total_seconds=None,
            lower_seconds=lower,
            upper_seconds=upper,
            confidence="low",
            assumptions=tuple(assumptions),
            calibration_name=None,
            estimated_output_size_bytes=estimated_size,
            estimated_output_size_lower_bytes=size_lower,
            estimated_output_size_upper_bytes=size_upper,
        )
    interpolation = (
        eligible_target_frames / calibration.interpolation_fps
        if resolved_policy.enhancement_enabled
        else 0.0
    )
    delivery = target_frames / calibration.delivery_fps
    verification = (
        calibration.fixed_verify_seconds + edited_duration / calibration.verification_probe_fps
    )
    work_seconds = (
        interpolation + delivery if calibration.sequential else max(interpolation, delivery)
    )
    total = preflight + work_seconds + verification
    return ExportEstimate(
        input_count=len(workloads),
        edited_duration_seconds=edited_duration,
        target_rate=resolved_policy.target_rate,
        source_frames=source_frames,
        target_frames=target_frames,
        eligible_source_frames=eligible_source_frames,
        eligible_target_frames=eligible_target_frames,
        enhancement_duration_seconds=enhancement_duration,
        preflight_seconds=preflight,
        interpolation_seconds=interpolation,
        delivery_seconds=delivery,
        verification_seconds=verification,
        total_seconds=total,
        lower_seconds=total * 0.8,
        upper_seconds=total * 1.2,
        confidence="local",
        assumptions=tuple(assumptions),
        calibration_name=calibration.name,
        estimated_output_size_bytes=estimated_size,
        estimated_output_size_lower_bytes=size_lower,
        estimated_output_size_upper_bytes=size_upper,
    )


def workloads_from_project(project: Any) -> tuple[SourceWorkload, ...]:
    """Build source-level workloads from the active timeline blocks."""
    timeline = project.timeline
    active_segments = tuple(segment for segment in timeline.segment_items if not segment.deleted)
    sources = tuple(project.sources or (project.source,))
    workloads: list[SourceWorkload] = []
    for source in sources:
        edited_duration = sum(
            segment.duration_seconds
            for segment in active_segments
            if segment.source_id in {None, source.source_id}
        )
        if edited_duration <= 0:
            continue
        source_duration = source.metadata.get("duration_seconds")
        if source_duration is None:
            raise ValueError(f"Source {source.source_id} is missing a duration")
        rate = source.metadata.get("frame_rate")
        if rate is None:
            raise ValueError(f"Source {source.source_id} is missing a frame rate")
        width = source.metadata.get("width")
        height = source.metadata.get("height")
        if (
            isinstance(width, bool)
            or not isinstance(width, int)
            or width <= 0
            or isinstance(height, bool)
            or not isinstance(height, int)
            or height <= 0
        ):
            raise ValueError(f"Source {source.source_id} has invalid dimensions")
        audio_present = source.metadata.get("audio_stream_present")
        if audio_present is None:
            audio_present = source.metadata.get("audio_codec") is not None
        if not isinstance(audio_present, bool):
            raise ValueError(f"Source {source.source_id} has invalid audio presence")
        workloads.append(
            SourceWorkload(
                source_id=source.source_id,
                duration_seconds=float(source_duration),
                source_rate=canonical_rate(rate),
                edited_duration_seconds=edited_duration,
                audio_stream_present=audio_present,
                width=width,
                height=height,
                source_size_bytes=source.size_bytes,
            )
        )
    if not workloads:
        raise ValueError("The project has no active source workload")
    return tuple(workloads)


def estimate_project_export(
    project: Any,
    policy: FrameRatePolicy | ResolvedFrameRatePolicy,
    *,
    calibration: CalibrationProfile | None = RVE_CALIBRATION,
) -> ExportEstimate:
    return estimate_export(
        workloads_from_project(project),
        policy,
        calibration=calibration,
    )
