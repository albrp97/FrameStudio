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
from .crop_window import crop_window_filter_string, crop_window_filters
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


def _crop_origin(scaled: int, window: int, offset: float, scale: float = 1.0) -> int:
    return round((scaled - window) / 2 + offset * scale)


def _window_filter(
    scaled_width: int,
    scaled_height: int,
    crop_x: int,
    crop_y: int,
    width: int,
    height: int,
) -> str:
    return crop_window_filter_string(
        crop_window_filters(scaled_width, scaled_height, crop_x, crop_y, width, height)
    )


def _normal_branch(
    input_label: str,
    transform: VisualTransform,
    width: int,
    height: int,
    *,
    preserve_resolution: bool = False,
    content_width: int | None = None,
    content_height: int | None = None,
) -> str:
    if preserve_resolution:
        if content_width is None or content_height is None:
            raise ValueError("Preserve-resolution rendering requires content dimensions")
        scaled_width = math.ceil(content_width * transform.zoom)
        scaled_height = math.ceil(content_height * transform.zoom)
        crop_x = _crop_origin(scaled_width, width, transform.offset_x)
        crop_y = _crop_origin(scaled_height, height, transform.offset_y)
        window = _window_filter(scaled_width, scaled_height, crop_x, crop_y, width, height)
        return (
            f"{input_label}scale={content_width}:{content_height},"
            f"scale={scaled_width}:{scaled_height},"
            f"{window},setsar=1"
        )
    scaled_width = math.ceil(width * transform.zoom)
    scaled_height = math.ceil(height * transform.zoom)
    crop_x = _crop_origin(scaled_width, width, transform.offset_x)
    crop_y = _crop_origin(scaled_height, height, transform.offset_y)
    window = _window_filter(scaled_width, scaled_height, crop_x, crop_y, width, height)
    return (
        f"{input_label}scale={width}:{height}:force_original_aspect_ratio=decrease,"
        f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color=black,"
        f"scale={scaled_width}:{scaled_height},"
        f"{window},setsar=1"
    )


def _triplicate_branch(
    input_label: str,
    transform: VisualTransform,
    width: int,
    height: int,
    *,
    preserve_resolution: bool = False,
    content_width: int | None = None,
    content_height: int | None = None,
) -> str:
    zoom = transform.zoom
    slot_width = width // 3
    if preserve_resolution:
        if content_width is None or content_height is None:
            raise ValueError("Preserve-resolution rendering requires content dimensions")
        scaled_width = math.ceil(content_width * zoom)
        scaled_height = math.ceil(content_height * zoom)
        crop_x = _crop_origin(scaled_width, slot_width, transform.offset_x)
        crop_y = _crop_origin(scaled_height, height, transform.offset_y)
        window = _window_filter(scaled_width, scaled_height, crop_x, crop_y, slot_width, height)
        return (
            f"{input_label}scale={content_width}:{content_height},"
            f"scale={scaled_width}:{scaled_height},"
            f"{window},setsar=1"
        )
    scaled_width = math.ceil(width * zoom)
    scaled_height = math.ceil(height * zoom)
    if zoom <= 1.0:
        triplicate_x_scale = 1.0
    else:
        triplicate_x_scale = (width * zoom - slot_width) / (width * (zoom - 1.0))
    crop_x = _crop_origin(
        scaled_width,
        slot_width,
        transform.offset_x,
        (width / CANVAS_WIDTH) * triplicate_x_scale,
    )
    crop_y = _crop_origin(scaled_height, height, transform.offset_y, height / CANVAS_HEIGHT)
    window = _window_filter(scaled_width, scaled_height, crop_x, crop_y, slot_width, height)
    return (
        f"{input_label}scale={width}:{height}:"
        "force_original_aspect_ratio=decrease,"
        f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color=black,"
        f"scale={scaled_width}:{scaled_height},"
        f"{window},setsar=1"
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
    preserve_resolution: bool = False,
    content_width: int | None = None,
    content_height: int | None = None,
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
    if preserve_resolution and (
        content_width is None or content_height is None or content_width <= 0 or content_height <= 0
    ):
        raise ValueError("Preserve-resolution rendering requires positive content dimensions")
    preserve_source_resolution = preserve_resolution and not (
        content_width is not None
        and content_height is not None
        and content_width > width
        and content_height > height
    )
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
            branch = _triplicate_branch(
                source_label,
                transform,
                width,
                height,
                preserve_resolution=preserve_source_resolution,
                content_width=content_width,
                content_height=content_height,
            )
            if rate is not None:
                branch += f",fps={rate}"
            filters.append(branch + role_label)
        composed = (
            f"{role_labels['left']}{role_labels['center']}{role_labels['right']}hstack=inputs=3"
        )
        filters.append(f"{composed}{output_label}")
        return filters
    normal = _normal_branch(
        f"{trim},",
        segment.visual_transform,
        width,
        height,
        preserve_resolution=preserve_source_resolution,
        content_width=content_width,
        content_height=content_height,
    )
    if rate is not None:
        normal += f",fps={rate}"
    return [f"{normal}{output_label}"]


__all__ = ["segment_video_filters"]
