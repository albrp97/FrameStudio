from __future__ import annotations

import math
import os
from bisect import bisect_right
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from .composed_playback import PROJECT_TIMEBASE, FfmpegSynchronizedPlaybackBackend
from .composition_render import segment_video_filters
from .ffmpeg_playback import FrameCallback, MessageCallback, VoidCallback
from .layout_plan import LayoutInterval, LayoutPlan
from .model_types import Segment
from .playback import PlaybackBackendError


class FfmpegSequentialPlaybackBackend(FfmpegSynchronizedPlaybackBackend):
    """Use the sequential render graph with the bounded interval playback runtime."""

    _NATIVE_FALLBACK_REASON = (
        "Native sequential composition is not validated against the legacy "
        "scale/pad/fps path; using the exact sequential FFmpeg graph"
    )

    def __init__(
        self,
        sources: Sequence[tuple[str, Path]],
        blocks: Sequence[Segment],
        layout: LayoutPlan,
        width: int,
        height: int,
        frame_rate: float,
        on_frame: FrameCallback,
        on_error: MessageCallback,
        on_end: VoidCallback,
        *,
        ffmpeg_path: str = "ffmpeg",
        on_warning: MessageCallback | None = None,
        preview_cache_size: int = 8,
        preview_backend: str = "auto",
    ) -> None:
        if preview_backend not in {"ffmpeg", "auto", "cpu", "cuda"}:
            raise PlaybackBackendError("Invalid sequential preview backend")
        if layout.timing_mode != "legacy-ripple":
            raise ValueError("Sequential playback requires a compact legacy-ripple layout")
        source_items = tuple(sources)
        block_items = tuple(block for block in blocks if not block.deleted)
        self._blocks_by_id = {block.segment_id: block for block in block_items}
        if not block_items or len(self._blocks_by_id) != len(block_items):
            raise ValueError("Sequential playback requires unique active timeline blocks")
        self._source_paths = dict(source_items)
        if len(self._source_paths) != len(source_items):
            raise ValueError("Sequential playback requires unique source identities")
        previous_end = 0
        for interval in layout.intervals:
            if interval.start_tick != previous_end or len(interval.active_blocks) != 1:
                raise ValueError("Sequential playback requires one active block per interval")
            planned = interval.active_blocks[0]
            block = self._blocks_by_id.get(planned.segment_id)
            if block is None or (
                block.source_start_ticks != planned.source_range.source_start_tick
                or block.source_end_ticks != planned.source_range.source_end_tick
                or block.visual_transform != planned.visual_transform
                or bool(block.triplicate is not None and block.triplicate.enabled)
                != planned.triplicate_enabled
                or (block.source_id is not None and block.source_id != planned.source_id)
            ):
                raise ValueError("Sequential layout does not match the original timeline blocks")
            previous_end = interval.end_tick
        if previous_end != layout.final_duration_ticks or (
            {block.segment_id for block in layout.included_blocks} != set(self._blocks_by_id)
        ):
            raise ValueError("Sequential layout must include every active timeline block")
        self._interval_starts = tuple(interval.start_tick for interval in layout.intervals)
        super().__init__(
            source_items,
            layout,
            width,
            height,
            frame_rate,
            on_frame,
            on_error,
            on_end,
            ffmpeg_path=ffmpeg_path,
            on_warning=on_warning,
            preview_cache_size=preview_cache_size,
            preview_backend="ffmpeg",
        )
        self.precise_preview_diagnostics = {
            "requested_engine": preview_backend,
            "composition_policy": "sequential-reference",
            "selected_engine": "ffmpeg",
            "reason": self._NATIVE_FALLBACK_REASON,
        }
        if preview_backend != "ffmpeg":
            self.on_warning(self._NATIVE_FALLBACK_REASON)

    def _interval_at(self, position_seconds: float) -> LayoutInterval | None:
        tick = max(0, round(float(position_seconds) * PROJECT_TIMEBASE))
        if tick >= self._layout.final_duration_ticks:
            return None
        index = bisect_right(self._interval_starts, tick) - 1
        return self._layout.intervals[index] if index >= 0 else None

    def _preview_cache_namespace(self, position_seconds: float) -> tuple[Any, ...]:
        interval = self._interval_at(position_seconds)
        if interval is None:
            return ("sequential-black",)
        planned = interval.active_blocks[0]
        block = self._blocks_by_id[planned.segment_id]
        path = self._source_paths[planned.source_id]
        try:
            stat = path.stat()
            identity: tuple[Any, ...] = (
                str(path.resolve()),
                stat.st_dev,
                stat.st_ino,
                stat.st_size,
                stat.st_mtime_ns,
            )
        except OSError:
            identity = (str(path.resolve()), "unavailable")
        return (
            "sequential-reference-v1",
            interval.start_tick,
            interval.end_tick,
            block.segment_id,
            block.source_start_ticks,
            block.source_end_ticks,
            block.visual_transform,
            block.triplicate,
            planned.source_geometry,
            self._layout.output_domain,
            self.width,
            self.height,
            self.frame_rate,
            identity,
        )

    def _video_command(
        self,
        position_seconds: float,
        interval: LayoutInterval,
        *,
        continuous: bool = False,
    ) -> list[str]:
        planned = interval.active_blocks[0]
        block = self._blocks_by_id[planned.segment_id]
        tick = max(0, round(position_seconds * PROJECT_TIMEBASE))
        source_start = planned.source_range.source_tick_at(tick) / PROJECT_TIMEBASE
        remaining = (interval.end_tick - tick) / PROJECT_TIMEBASE
        command = [
            self.ffmpeg_path,
            "-hide_banner",
            "-loglevel",
            "error",
            "-nostdin",
        ]
        decoder_threads = 4 if continuous else max(1, min(8, os.cpu_count() or 1))
        command.extend(["-filter_complex_threads", "2", "-threads", str(decoder_threads)])
        command.extend(
            [
                "-ss",
                f"{source_start:.6f}",
                "-noautorotate",
                "-i",
                str(self._source_paths[planned.source_id]),
            ]
        )
        filters = segment_video_filters(
            "[0:v:0]",
            block,
            self.width,
            self.height,
            "[v0]",
            frame_rate=self.frame_rate,
            source_start_seconds=0,
            source_duration_seconds=remaining,
        )
        output = "[v0]"
        if continuous:
            # fps rounds a fractional tail down in some intervals. Cover only
            # that final partial frame, bounded by the interval's frame count.
            filters.append("[v0]tpad=stop_mode=clone:stop=1[tail]")
            output = "[tail]"
        # Keep the one-segment concat negotiation used by legacy preview/export;
        # removing it can change automatic pixel-format/color conversions.
        filters.append(f"{output}concat=n=1:v=1:a=0[outv]")
        command.extend(
            [
                "-filter_complex",
                ";".join(filters),
                "-map",
                "[outv]",
                "-frames:v",
                str(max(1, math.ceil(remaining * self.frame_rate))) if continuous else "1",
                "-an",
                "-sn",
                "-dn",
                "-f",
                "rawvideo",
                "-pix_fmt",
                "rgba",
            ]
        )
        command.extend(["-threads:v", "1"])
        command.append("pipe:1")
        return command


__all__ = ["FfmpegSequentialPlaybackBackend"]
