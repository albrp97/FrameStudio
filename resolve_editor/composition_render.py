from __future__ import annotations

import math
from fractions import Fraction

from .composition import (
    CANVAS_HEIGHT,
    CANVAS_WIDTH,
    TRIPLICATE_ROLES,
    TriplicateGroup,
    VisualTransform,
)
from .model_types import Segment


def _filter_number(value: float) -> str:
    return f"{float(value):.6f}".rstrip("0").rstrip(".") or "0"


def _frame_rate_text(frame_rate: float | str | None) -> str | None:
    if frame_rate is None:
        return None
    if isinstance(frame_rate, str):
        try:
            if Fraction(frame_rate) <= 0:
                raise ValueError
        except (ValueError, ZeroDivisionError):
            raise ValueError("Render frame rate must be a positive rate") from None
        return frame_rate
    if not math.isfinite(float(frame_rate)) or float(frame_rate) <= 0:
        raise ValueError("Render frame rate must be a positive rate")
    return _filter_number(float(frame_rate))


def _crop_expression(
    transform: VisualTransform,
    *,
    x_scale: float = 1.0,
    y_scale: float = 1.0,
) -> tuple[str, str]:
    offset_x = _filter_number(transform.offset_x * x_scale)
    offset_y = _filter_number(transform.offset_y * y_scale)
    x = f"'clip((in_w-out_w)/2+{offset_x},0,in_w-out_w)'"
    y = f"'clip((in_h-out_h)/2+{offset_y},0,in_h-out_h)'"
    return x, y


def _normal_branch(
    input_label: str,
    transform: VisualTransform,
    width: int,
    height: int,
) -> str:
    scaled_width = max(width, int(math.ceil(width * transform.zoom)))
    scaled_height = max(height, int(math.ceil(height * transform.zoom)))
    x, y = _crop_expression(transform)
    return (
        f"{input_label}scale={width}:{height}:force_original_aspect_ratio=decrease,"
        f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color=black,"
        f"scale={scaled_width}:{scaled_height},"
        f"crop={width}:{height}:x={x}:y={y},setsar=1"
    )


def _triplicate_branch(
    input_label: str,
    transform: VisualTransform,
    width: int,
    height: int,
) -> str:
    slot_width = width // 3
    scaled_width = max(slot_width, int(math.ceil(slot_width * transform.zoom)))
    scaled_height = max(height, int(math.ceil(height * transform.zoom)))
    x, y = _crop_expression(
        transform,
        x_scale=slot_width / CANVAS_WIDTH,
        y_scale=height / CANVAS_HEIGHT,
    )
    return (
        f"{input_label}scale={scaled_width}:{scaled_height}:"
        "force_original_aspect_ratio=increase,"
        f"crop={slot_width}:{height}:x={x}:y={y},setsar=1"
    )


def segment_video_filters(
    input_label: str,
    segment: Segment,
    width: int,
    height: int,
    output_label: str,
    *,
    frame_rate: float | str | None = None,
    source_start_seconds: float | None = None,
    source_duration_seconds: float | None = None,
) -> list[str]:
    """Build the shared video graph used by preview and export."""
    if width <= 0 or height <= 0:
        raise ValueError("Render dimensions must be positive")
    rate = _frame_rate_text(frame_rate)
    root = output_label.strip("[]")
    start_value = (
        segment.start_seconds if source_start_seconds is None else float(source_start_seconds)
    )
    duration_value = (
        segment.duration_seconds
        if source_duration_seconds is None
        else float(source_duration_seconds)
    )
    if not math.isfinite(start_value) or start_value < 0:
        raise ValueError("Render source start must be finite and non-negative")
    if not math.isfinite(duration_value) or duration_value <= 0:
        raise ValueError("Render source duration must be finite and greater than zero")
    if start_value + duration_value > segment.end_seconds + 1e-6:
        raise ValueError("Render source range must be within the segment")
    start = f"{start_value:.6f}"
    duration = f"{duration_value:.6f}"
    trim = f"{input_label}trim=start={start}:duration={duration},setpts=PTS-STARTPTS"
    group: TriplicateGroup | None = segment.triplicate
    if group is not None and group.enabled:
        if width % 3 != 0:
            raise ValueError("Triplicate render width must be divisible by three")
        source_labels = tuple(f"[{root}_{role}_source]" for role in TRIPLICATE_ROLES)
        filters = [f"{trim},split=3{''.join(source_labels)}"]
        role_labels: dict[str, str] = {}
        transform = group.shared_transform
        for role, source_label in zip(TRIPLICATE_ROLES, source_labels, strict=True):
            role_label = f"[{root}_{role}]"
            role_labels[role] = role_label
            filters.append(
                _triplicate_branch(
                    source_label,
                    transform,
                    width,
                    height,
                )
                + role_label
            )
        composed = (
            f"{role_labels['left']}{role_labels['center']}{role_labels['right']}hstack=inputs=3"
        )
        if rate is not None:
            composed += f",fps={rate}"
        filters.append(f"{composed}{output_label}")
        return filters
    normal = _normal_branch(
        f"{trim},",
        segment.visual_transform,
        width,
        height,
    )
    if rate is not None:
        normal += f",fps={rate}"
    return [f"{normal}{output_label}"]


__all__ = ["segment_video_filters"]
