from __future__ import annotations

import math

from .timeline_geometry import (
    SELECTED_CLIP_BORDER_COLOR,
    TIMELINE_CLIP_BADGE_RADIUS,
    TIMELINE_HORIZONTAL_PADDING,
    TIMELINE_RULER_HEIGHT,
    TIMELINE_TRACK_HEIGHT,
    TIMELINE_TRACK_Y,
    TimelineClipGeometry,
    TimelineTrackGeometry,
    timeline_tick_interval,
)
from .ui import format_duration


def draw_ruler(
    context,
    duration_seconds: float,
    pixels_per_second: float,
    width: int,
) -> None:
    draw_text(
        context,
        "ORIGINAL SOURCE",
        TIMELINE_HORIZONTAL_PADDING,
        15.0,
        0.55,
        0.62,
        0.78,
        10.0,
    )
    if duration_seconds == 0.0:
        return
    interval = timeline_tick_interval(
        duration_seconds,
        pixels_per_second,
    )
    left, _top, right, _bottom = context.clip_extents()
    first_tick = max(
        0, math.floor((left - TIMELINE_HORIZONTAL_PADDING - 90.0) / pixels_per_second / interval)
    )
    current = first_tick * interval
    while current <= duration_seconds + 1e-9:
        x = TIMELINE_HORIZONTAL_PADDING + current * pixels_per_second
        if x > min(width, right) + 1.0:
            break
        context.set_source_rgba(0.55, 0.60, 0.72, 0.55)
        context.set_line_width(1.0)
        context.move_to(x, 24.0)
        context.line_to(x, TIMELINE_TRACK_Y - 4.0)
        context.stroke()
        draw_text(
            context,
            format_duration(current),
            x + 3.0,
            31.0,
            0.56,
            0.61,
            0.72,
            10.0,
        )
        current += interval


def draw_track(
    context,
    width: int,
    rows: tuple[TimelineTrackGeometry, ...] | list[TimelineTrackGeometry] = (),
) -> None:
    if not rows:
        rows = (
            TimelineTrackGeometry(
                track_id="track-1",
                index=0,
                y=TIMELINE_TRACK_Y,
            ),
        )
    for row in rows:
        context.set_source_rgba(
            0.12 if row.active else 0.09,
            0.14 if row.active else 0.105,
            0.22 if row.active else 0.16,
            0.96,
        )
        context.rectangle(
            TIMELINE_HORIZONTAL_PADDING,
            row.y,
            max(1.0, width - TIMELINE_HORIZONTAL_PADDING * 2),
            row.height,
        )
        context.fill()
        context.set_source_rgba(
            0.58 if row.active else 0.35,
            0.66 if row.active else 0.39,
            0.86 if row.active else 0.52,
            0.82 if row.active else 0.65,
        )
        context.set_line_width(1.5 if row.active else 1.0)
        context.rectangle(
            TIMELINE_HORIZONTAL_PADDING,
            row.y,
            max(1.0, width - TIMELINE_HORIZONTAL_PADDING * 2),
            row.height,
        )
        context.stroke()
        draw_text(
            context,
            row.track_id,
            TIMELINE_HORIZONTAL_PADDING + 6.0,
            row.y + 13.0,
            0.85 if row.active else 0.56,
            0.9 if row.active else 0.61,
            1.0 if row.active else 0.72,
            9.0,
        )


def draw_clip(
    context,
    clip: TimelineClipGeometry,
    selected_segment_ids: tuple[str, ...] = (),
) -> None:
    y = clip.y
    height = clip.height
    if clip.deleted:
        fill = (0.22, 0.12, 0.18, 0.96)
        border = (0.82, 0.28, 0.38, 0.95)
    else:
        palette = (
            (0.45, 0.29, 0.22),
            (0.28, 0.46, 0.25),
            (0.21, 0.38, 0.54),
            (0.42, 0.30, 0.52),
        )
        red, green, blue = palette[clip.color_index % len(palette)]
        fill = (red, green, blue, 0.96)
        border = (0.72, 0.79, 0.92, 0.82)
    selected = clip.segment_id in selected_segment_ids
    if selected:
        border = SELECTED_CLIP_BORDER_COLOR

    rounded_rectangle(
        context,
        clip.x,
        y,
        clip.width,
        height,
        5.0,
    )
    context.set_source_rgba(*fill)
    context.fill_preserve()
    context.save()
    context.clip()
    context.rectangle(clip.x, y, clip.snap_width, height)
    context.set_source_rgba(1.0, 1.0, 1.0, 0.16)
    context.fill()
    context.restore()
    rounded_rectangle(context, clip.x, y, clip.width, height, 5.0)
    context.set_source_rgba(*border)
    context.set_line_width(3.0 if selected else 1.0)
    context.stroke()

    if clip.deleted:
        context.save()
        context.rectangle(clip.x, y, clip.width, height)
        context.clip()
        context.set_source_rgba(0.90, 0.34, 0.42, 0.48)
        context.set_line_width(1.0)
        left, _top, right, _bottom = context.clip_extents()
        offset = -height + max(0, math.floor((left - clip.x) / 10.0)) * 10.0
        while offset < min(clip.width, right - clip.x) + height:
            context.move_to(clip.x + offset, y + height)
            context.line_to(clip.x + offset + height, y)
            context.stroke()
            offset += 10.0
        context.restore()

    badge = clip.badge_center
    if badge is not None:
        bubble_x, bubble_y = badge
        context.set_source_rgba(0.08, 0.09, 0.14, 0.92)
        context.arc(bubble_x, bubble_y, TIMELINE_CLIP_BADGE_RADIUS, 0.0, math.tau)
        context.fill()
        draw_text(
            context,
            str(clip.index + 1),
            bubble_x - 3.0,
            y + 3.5,
            0.92,
            0.94,
            1.0,
            10.0,
        )

    if clip.width >= 74.0:
        label = "DELETED" if clip.deleted else "INCLUDED"
        draw_text(
            context,
            label,
            clip.x + 8.0,
            y + min(height - 7.0, 24.0),
            0.94,
            0.95,
            1.0,
            9.0,
        )
    if clip.width >= 126.0:
        draw_text(
            context,
            f"{format_duration(clip.start_seconds)} - {format_duration(clip.end_seconds)}",
            clip.x + 8.0,
            y + height - 7.0,
            0.78,
            0.82,
            0.92,
            9.0,
        )

    if clip.index > 0:
        context.set_source_rgba(0.84, 0.88, 0.98, 0.62)
        context.set_line_width(1.0)
        context.move_to(clip.x, clip.y - 5.0)
        context.line_to(clip.x, clip.y - 2.0)
        context.stroke()


def draw_playhead(
    context,
    playhead_seconds: float,
    pixels_per_second: float,
    rows: tuple[TimelineTrackGeometry, ...] | list[TimelineTrackGeometry] = (),
) -> None:
    x = TIMELINE_HORIZONTAL_PADDING + playhead_seconds * pixels_per_second
    last_row_end = max(
        (row.end_y for row in rows), default=TIMELINE_TRACK_Y + TIMELINE_TRACK_HEIGHT
    )
    context.set_source_rgba(0.96, 0.97, 1.0, 0.95)
    context.set_line_width(1.5)
    context.move_to(x, TIMELINE_RULER_HEIGHT - 4.0)
    context.line_to(x, last_row_end + 7.0)
    context.stroke()
    context.set_source_rgba(0.95, 0.28, 0.34, 1.0)
    context.move_to(x - 6.0, 23.0)
    context.line_to(x + 6.0, 23.0)
    context.line_to(x, 31.0)
    context.close_path()
    context.fill()


def rounded_rectangle(context, x, y, width, height, radius) -> None:
    radius = min(radius, width / 2.0, height / 2.0)
    context.new_sub_path()
    context.arc(
        x + width - radius,
        y + radius,
        radius,
        -math.pi / 2,
        0,
    )
    context.arc(
        x + width - radius,
        y + height - radius,
        radius,
        0,
        math.pi / 2,
    )
    context.arc(
        x + radius,
        y + height - radius,
        radius,
        math.pi / 2,
        math.pi,
    )
    context.arc(
        x + radius,
        y + radius,
        radius,
        math.pi,
        math.pi * 1.5,
    )
    context.close_path()


def draw_text(
    context,
    text: str,
    x: float,
    y: float,
    red: float,
    green: float,
    blue: float,
    size: float,
) -> None:
    context.set_source_rgb(red, green, blue)
    context.select_font_face("Sans")
    context.set_font_size(size)
    context.move_to(x, y)
    context.show_text(text)
