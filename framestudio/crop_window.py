"""Crop a W×H window from a scaled frame, padding black where the window leaves the frame."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .layout_plan import CropPlan

CropStep = tuple[str, str]


def crop_window_filters(
    scaled_width: int,
    scaled_height: int,
    crop_x: int,
    crop_y: int,
    width: int,
    height: int,
) -> tuple[CropStep, ...]:
    """Return filter steps that map a scaled frame into a width×height window.

    The window origin (crop_x, crop_y) may be negative or extend past the
    scaled frame. Regions outside the frame are filled with black. The output
    is always exactly width×height.
    """
    left = max(0, crop_x)
    top = max(0, crop_y)
    right = min(scaled_width, crop_x + width)
    bottom = min(scaled_height, crop_y + height)
    if right <= left or bottom <= top:
        return (
            ("crop", "1:1:0:0"),
            ("drawbox", "x=0:y=0:w=1:h=1:color=black:t=fill"),
            ("pad", f"{width}:{height}:0:0:color=black"),
        )
    visible_width = right - left
    visible_height = bottom - top
    if (left, top, visible_width, visible_height) == (crop_x, crop_y, width, height):
        return (("crop", f"{width}:{height}:{crop_x}:{crop_y}"),)
    steps: list[CropStep] = []
    if (left, top, visible_width, visible_height) != (0, 0, scaled_width, scaled_height):
        steps.append(("crop", f"{visible_width}:{visible_height}:{left}:{top}"))
    if visible_width != width or visible_height != height:
        steps.append(
            ("pad", f"{width}:{height}:{left - crop_x}:{top - crop_y}:color=black")
        )
    return tuple(steps)


def crop_window_filter_string(steps: tuple[CropStep, ...]) -> str:
    return ",".join(f"{name}={args}" for name, args in steps)


def crop_window_filter(crop: CropPlan) -> str:
    return crop_window_filter_string(
        crop_window_filters(
            crop.scaled_width,
            crop.scaled_height,
            crop.crop_x,
            crop.crop_y,
            crop.target.width,
            crop.target.height,
        )
    )
