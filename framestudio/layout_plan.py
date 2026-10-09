from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from fractions import Fraction
from itertools import pairwise
from typing import TYPE_CHECKING, Any, Mapping

from .composition import CANVAS_HEIGHT, CANVAS_WIDTH, VisualTransform
from .model_timeline import MAX_TRACK_COUNT, SegmentTimeline
from .model_types import PROJECT_TIMEBASE, Segment

if TYPE_CHECKING:
    from .model_project import Project


MAX_ACTIVE_BLOCKS = MAX_TRACK_COUNT
TRIPLICATE_ROLES = ("left", "center", "right")


class LayoutPlanError(ValueError):
    """Raised when a project cannot be represented by the shared layout plan."""


class FramingDomain(str, Enum):
    NATIVE_SOURCE = "native-source"
    FULL_CANVAS_REEL = "full-canvas-reel"
    FINAL_SLOT = "final-slot"


@dataclass(frozen=True)
class PixelRect:
    x: int
    y: int
    width: int
    height: int

    def __post_init__(self) -> None:
        values = (self.x, self.y, self.width, self.height)
        if any(isinstance(value, bool) or not isinstance(value, int) for value in values):
            raise LayoutPlanError("Pixel rectangle values must be integers")
        if self.x < 0 or self.y < 0 or self.width <= 0 or self.height <= 0:
            raise LayoutPlanError(
                "Pixel rectangle must have a non-negative origin and positive size"
            )


DEFAULT_CANVAS = PixelRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT)
DEFAULT_TRANSFORM = VisualTransform()


@dataclass(frozen=True)
class SourceGeometry:
    source_id: str
    width: int
    height: int
    sar_num: int = 1
    sar_den: int = 1
    input_domain: FramingDomain = FramingDomain.NATIVE_SOURCE

    def __post_init__(self) -> None:
        if not isinstance(self.source_id, str) or not self.source_id:
            raise LayoutPlanError("Source geometry source_id must be non-empty")
        if (
            isinstance(self.width, bool)
            or not isinstance(self.width, int)
            or self.width <= 0
            or isinstance(self.height, bool)
            or not isinstance(self.height, int)
            or self.height <= 0
        ):
            raise LayoutPlanError("Source geometry dimensions must be positive integers")
        if (
            isinstance(self.sar_num, bool)
            or not isinstance(self.sar_num, int)
            or self.sar_num <= 0
            or isinstance(self.sar_den, bool)
            or not isinstance(self.sar_den, int)
            or self.sar_den <= 0
        ):
            raise LayoutPlanError("Source sample aspect ratio must be positive integers")
        try:
            domain = (
                self.input_domain
                if isinstance(self.input_domain, FramingDomain)
                else FramingDomain(self.input_domain)
            )
        except ValueError as error:
            raise LayoutPlanError("Unsupported source framing domain") from error
        object.__setattr__(self, "input_domain", domain)

    @classmethod
    def from_metadata(
        cls,
        source_id: str,
        metadata: Mapping[str, Any],
        *,
        input_domain: FramingDomain = FramingDomain.NATIVE_SOURCE,
    ) -> SourceGeometry:
        if not isinstance(metadata, Mapping):
            raise LayoutPlanError(f"Source metadata is not an object: {source_id}")
        try:
            width = _strict_metadata_integer(metadata["width"], "Source width")
            height = _strict_metadata_integer(metadata["height"], "Source height")
        except KeyError as error:
            raise LayoutPlanError(f"Source metadata needs width and height: {source_id}") from error
        except LayoutPlanError as error:
            raise LayoutPlanError(f"Source metadata needs width and height: {source_id}") from error
        sar_num, sar_den = _sample_aspect_ratio(metadata)
        return cls(
            source_id=source_id,
            width=width,
            height=height,
            sar_num=sar_num,
            sar_den=sar_den,
            input_domain=input_domain,
        )

    @property
    def sample_aspect_ratio(self) -> Fraction:
        return Fraction(self.sar_num, self.sar_den)

    @property
    def display_width(self) -> Fraction:
        return Fraction(self.width * self.sar_num, self.sar_den)

    @property
    def source_sar(self) -> tuple[int, int]:
        return self.sar_num, self.sar_den


@dataclass(frozen=True)
class FramingIdentity:
    source_id: str
    input_domain: FramingDomain
    output_domain: FramingDomain
    source_width: int
    source_height: int
    sar_num: int
    sar_den: int
    target: PixelRect


@dataclass(frozen=True)
class CropPlan:
    source: SourceGeometry
    target: PixelRect
    scaled_width: int
    scaled_height: int
    crop_x: int
    crop_y: int
    zoom: float
    offset_x: float
    offset_y: float
    output_domain: FramingDomain
    role: str | None = None

    @property
    def crop_width(self) -> int:
        return self.target.width

    @property
    def crop_height(self) -> int:
        return self.target.height

    @property
    def source_sar(self) -> tuple[int, int]:
        return self.source.source_sar

    @property
    def framing_identity(self) -> FramingIdentity:
        return FramingIdentity(
            source_id=self.source.source_id,
            input_domain=self.source.input_domain,
            output_domain=self.output_domain,
            source_width=self.source.width,
            source_height=self.source.height,
            sar_num=self.source.sar_num,
            sar_den=self.source.sar_den,
            target=self.target,
        )

    @property
    def geometry_identity(self) -> tuple[object, ...]:
        return (
            "layout-geometry-v1",
            self.framing_identity,
            self.scaled_width,
            self.scaled_height,
            self.crop_x,
            self.crop_y,
            self.zoom,
            self.offset_x,
            self.offset_y,
            self.role,
        )


@dataclass(frozen=True)
class SourceRangePlan:
    source_start_tick: int
    source_end_tick: int
    timeline_start_tick: int
    timeline_end_tick: int

    def __post_init__(self) -> None:
        values = (
            self.source_start_tick,
            self.source_end_tick,
            self.timeline_start_tick,
            self.timeline_end_tick,
        )
        if any(
            isinstance(value, bool) or not isinstance(value, int) or value < 0 for value in values
        ):
            raise LayoutPlanError("Source ranges must use non-negative integer ticks")
        if self.source_end_tick <= self.source_start_tick:
            raise LayoutPlanError("Source range must be non-empty")
        if self.timeline_end_tick <= self.timeline_start_tick:
            raise LayoutPlanError("Timeline range must be non-empty")
        if self.source_duration_ticks != self.timeline_duration_ticks:
            raise LayoutPlanError("Layout plan does not support source speed changes")

    @property
    def source_duration_ticks(self) -> int:
        return self.source_end_tick - self.source_start_tick

    @property
    def timeline_duration_ticks(self) -> int:
        return self.timeline_end_tick - self.timeline_start_tick

    def source_tick_at(self, timeline_tick: int) -> int:
        if (
            isinstance(timeline_tick, bool)
            or not isinstance(timeline_tick, int)
            or not self.timeline_start_tick <= timeline_tick < self.timeline_end_tick
        ):
            raise LayoutPlanError("Timeline sample is outside the half-open block range")
        return self.source_start_tick + (timeline_tick - self.timeline_start_tick)


@dataclass(frozen=True)
class PlannedBlock:
    segment_id: str
    block_id: str
    track_id: str
    track_order: int
    source_id: str
    source_geometry: SourceGeometry
    source_range: SourceRangePlan
    visual_transform: VisualTransform
    triplicate_enabled: bool

    @property
    def timeline_start_tick(self) -> int:
        return self.source_range.timeline_start_tick

    @property
    def timeline_end_tick(self) -> int:
        return self.source_range.timeline_end_tick


@dataclass(frozen=True)
class SlotPlan:
    block: PlannedBlock
    slot: PixelRect
    crop: CropPlan | None = None
    triplicate_crops: tuple[CropPlan, ...] = ()

    def __post_init__(self) -> None:
        if (self.crop is None) == (not self.triplicate_crops):
            raise LayoutPlanError("A slot must have one normal crop or triplicate crops")
        if self.triplicate_crops and len(self.triplicate_crops) != 3:
            raise LayoutPlanError("Triplicate slots must have three crop plans")

    @property
    def is_triplicate(self) -> bool:
        return bool(self.triplicate_crops)

    @property
    def requires_yuv444_intermediate(self) -> bool:
        return bool(self.triplicate_crops) and any(
            crop.target.width % 2 or crop.target.height % 2 for crop in self.triplicate_crops
        )


@dataclass(frozen=True)
class LayoutInterval:
    start_tick: int
    end_tick: int
    active_blocks: tuple[PlannedBlock, ...]
    slots: tuple[SlotPlan, ...]

    def __post_init__(self) -> None:
        if (
            isinstance(self.start_tick, bool)
            or isinstance(self.end_tick, bool)
            or not isinstance(self.start_tick, int)
            or not isinstance(self.end_tick, int)
            or self.start_tick < 0
            or self.end_tick <= self.start_tick
        ):
            raise LayoutPlanError("Layout interval must be a positive half-open tick range")
        if len(self.active_blocks) != len(self.slots):
            raise LayoutPlanError("Each active block must have one layout slot")

    @property
    def active_block_ids(self) -> tuple[str, ...]:
        return tuple(block.segment_id for block in self.active_blocks)

    @property
    def is_black(self) -> bool:
        return not self.active_blocks


@dataclass(frozen=True)
class LayoutPlan:
    canvas: PixelRect
    timing_mode: str
    output_domain: FramingDomain
    final_duration_ticks: int
    boundaries: tuple[int, ...]
    included_blocks: tuple[PlannedBlock, ...]
    intervals: tuple[LayoutInterval, ...]

    @property
    def final_duration_seconds(self) -> float:
        return self.final_duration_ticks / PROJECT_TIMEBASE

    @property
    def active_intervals(self) -> tuple[LayoutInterval, ...]:
        return tuple(interval for interval in self.intervals if not interval.is_black)

    def interval_at(self, timeline_tick: int) -> LayoutInterval | None:
        if (
            isinstance(timeline_tick, bool)
            or not isinstance(timeline_tick, int)
            or timeline_tick < 0
            or timeline_tick >= self.final_duration_ticks
        ):
            return None
        for interval in self.intervals:
            if interval.start_tick <= timeline_tick < interval.end_tick:
                return interval
        return None


def partition_pixels(total: int, count: int) -> tuple[int, ...]:
    if (
        isinstance(total, bool)
        or not isinstance(total, int)
        or total <= 0
        or isinstance(count, bool)
        or not isinstance(count, int)
        or count <= 0
    ):
        raise LayoutPlanError("Pixel partition dimensions must be positive integers")
    boundaries = tuple(_round_half_up(Fraction(index * total, count)) for index in range(count + 1))
    return tuple(boundaries[index + 1] - boundaries[index] for index in range(count))


def slot_rects(
    active_count: int,
    *,
    canvas: PixelRect = DEFAULT_CANVAS,
) -> tuple[PixelRect, ...]:
    if isinstance(active_count, bool) or not isinstance(active_count, int):
        raise LayoutPlanError("Active slot count must be an integer")
    if active_count < 0 or active_count > MAX_ACTIVE_BLOCKS:
        raise LayoutPlanError("The shared layout supports zero through four active blocks")
    if active_count == 0:
        return ()
    if active_count == 1:
        return (canvas,)
    widths = partition_pixels(canvas.width, 2 if active_count == 4 else active_count)
    if active_count in (2, 3):
        return tuple(
            PixelRect(canvas.x + sum(widths[:index]), canvas.y, width, canvas.height)
            for index, width in enumerate(widths)
        )
    heights = partition_pixels(canvas.height, 2)
    return (
        PixelRect(canvas.x, canvas.y, widths[0], heights[0]),
        PixelRect(canvas.x + widths[0], canvas.y, widths[1], heights[0]),
        PixelRect(canvas.x, canvas.y + heights[0], widths[0], heights[1]),
        PixelRect(canvas.x + widths[0], canvas.y + heights[0], widths[1], heights[1]),
    )


def plan_crop(
    source: SourceGeometry,
    target: PixelRect,
    transform: VisualTransform = DEFAULT_TRANSFORM,
    *,
    output_domain: FramingDomain = FramingDomain.FINAL_SLOT,
    role: str | None = None,
) -> CropPlan:
    normalized_output_domain = _coerce_domain(output_domain)
    _validate_output_domain(source, normalized_output_domain)
    scaled_width, scaled_height = _cover_dimensions(source, target, transform.zoom)
    mapped_x = _fraction(transform.offset_x) * Fraction(target.width, CANVAS_WIDTH)
    mapped_y = _fraction(transform.offset_y) * Fraction(target.height, CANVAS_HEIGHT)
    crop_x = _clamp(
        _round_half_up(Fraction(scaled_width - target.width, 2) + mapped_x),
        0,
        scaled_width - target.width,
    )
    crop_y = _clamp(
        _round_half_up(Fraction(scaled_height - target.height, 2) + mapped_y),
        0,
        scaled_height - target.height,
    )
    return _build_crop_plan(
        source=source,
        target=target,
        scaled_width=scaled_width,
        scaled_height=scaled_height,
        crop_x=crop_x,
        crop_y=crop_y,
        transform=transform,
        output_domain=normalized_output_domain,
        role=role,
    )


def plan_triplicate(
    source: SourceGeometry,
    slot: PixelRect,
    transform: VisualTransform,
    *,
    output_domain: FramingDomain = FramingDomain.FINAL_SLOT,
) -> tuple[CropPlan, ...]:
    normalized_output_domain = _coerce_domain(output_domain)
    _validate_output_domain(source, normalized_output_domain)
    scaled_width, scaled_height = _cover_dimensions(source, slot, transform.zoom)
    zoom = _fraction(transform.zoom)
    if zoom == 1:
        triplicate_scale = Fraction(1)
    else:
        triplicate_scale = (Fraction(slot.width) * zoom - Fraction(slot.width, 3)) / (
            Fraction(slot.width) * (zoom - 1)
        )
    mapped_x = _fraction(transform.offset_x) * Fraction(slot.width, CANVAS_WIDTH) * triplicate_scale
    mapped_y = _fraction(transform.offset_y) * Fraction(slot.height, CANVAS_HEIGHT)
    widths = partition_pixels(slot.width, 3)
    crops: list[CropPlan] = []
    x = slot.x
    for role, width in zip(TRIPLICATE_ROLES, widths, strict=True):
        target = PixelRect(x, slot.y, width, slot.height)
        crop_x = _clamp(
            _round_half_up(Fraction(scaled_width - width, 2) + mapped_x),
            0,
            scaled_width - width,
        )
        crop_y = _clamp(
            _round_half_up(Fraction(scaled_height - slot.height, 2) + mapped_y),
            0,
            scaled_height - slot.height,
        )
        crops.append(
            _build_crop_plan(
                source=source,
                target=target,
                scaled_width=scaled_width,
                scaled_height=scaled_height,
                crop_x=crop_x,
                crop_y=crop_y,
                transform=transform,
                output_domain=normalized_output_domain,
                role=role,
            )
        )
        x += width
    return tuple(crops)


def _build_crop_plan(
    *,
    source: SourceGeometry,
    target: PixelRect,
    scaled_width: int,
    scaled_height: int,
    crop_x: int,
    crop_y: int,
    transform: VisualTransform,
    output_domain: FramingDomain,
    role: str | None,
) -> CropPlan:
    return CropPlan(
        source=source,
        target=target,
        scaled_width=scaled_width,
        scaled_height=scaled_height,
        crop_x=crop_x,
        crop_y=crop_y,
        zoom=transform.zoom,
        offset_x=transform.offset_x,
        offset_y=transform.offset_y,
        output_domain=output_domain,
        role=role,
    )


def source_geometries_from_project(project: Project) -> dict[str, SourceGeometry]:
    sources = getattr(project, "sources", None) or (project.source,)
    return {
        source.source_id: SourceGeometry.from_metadata(source.source_id, source.metadata)
        for source in sources
    }


def plan_project_layout(
    project: Project,
    source_geometries: Mapping[str, SourceGeometry] | None = None,
    *,
    canvas: PixelRect = DEFAULT_CANVAS,
    output_domain: FramingDomain = FramingDomain.FINAL_SLOT,
) -> LayoutPlan:
    normalized_output_domain = _coerce_domain(output_domain)
    if source_geometries is None:
        source_geometries = source_geometries_from_project(project)
    geometries = _normalize_geometries(source_geometries)
    timeline = project.timeline
    track_order, ordered_blocks = _ordered_timeline_blocks(timeline)
    legacy = not timeline.is_synchronized or timeline.timing_mode == "legacy-ripple"
    if legacy and len(track_order) > 1:
        raise LayoutPlanError("Legacy compact projection supports one track only")

    candidates: list[tuple[Segment, int, str]] = []
    for candidate in ordered_blocks:
        if not _is_included(candidate):
            continue
        source_id = candidate.source_id or project.source.source_id
        geometry = geometries.get(source_id)
        if geometry is None:
            raise LayoutPlanError(f"Missing source geometry for {source_id}")
        source_start = candidate.source_start_ticks
        source_end = candidate.source_end_ticks
        timeline_start = candidate.timeline_start_ticks
        timeline_end = candidate.timeline_end_ticks
        if source_end - source_start != timeline_end - timeline_start:
            raise LayoutPlanError("Layout planning does not support speed changes")
        candidates.append(
            (candidate, track_order.get(candidate.track_id or "track-1", 0), source_id)
        )

    planned: list[PlannedBlock] = []
    compact_position = 0
    for candidate, stable_track_order, source_id in candidates:
        timeline_start = compact_position if legacy else candidate.timeline_start_ticks
        timeline_end = (
            timeline_start + candidate.timeline_end_ticks - candidate.timeline_start_ticks
            if legacy
            else candidate.timeline_end_ticks
        )
        geometry = geometries[source_id]
        planned.append(
            PlannedBlock(
                segment_id=candidate.segment_id,
                block_id=candidate.block_id or candidate.segment_id,
                track_id=candidate.track_id or "track-1",
                track_order=stable_track_order,
                source_id=source_id,
                source_geometry=geometry,
                source_range=SourceRangePlan(
                    source_start_tick=candidate.source_start_ticks,
                    source_end_tick=candidate.source_end_ticks,
                    timeline_start_tick=timeline_start,
                    timeline_end_tick=timeline_end,
                ),
                visual_transform=candidate.visual_transform,
                triplicate_enabled=bool(
                    candidate.triplicate is not None and candidate.triplicate.enabled
                ),
            )
        )
        compact_position = timeline_end if legacy else compact_position

    final_duration = max((block.timeline_end_tick for block in planned), default=0)
    boundaries = {0}
    if final_duration:
        boundaries.add(final_duration)
    for planned_block in planned:
        boundaries.add(planned_block.timeline_start_tick)
        boundaries.add(planned_block.timeline_end_tick)
    ordered_boundaries = tuple(sorted(boundaries))
    intervals: list[LayoutInterval] = []
    for start_tick, end_tick in pairwise(ordered_boundaries):
        if end_tick <= start_tick:
            continue
        active = tuple(
            sorted(
                (
                    planned_block
                    for planned_block in planned
                    if planned_block.timeline_start_tick
                    <= start_tick
                    < planned_block.timeline_end_tick
                ),
                key=lambda planned_block: (
                    planned_block.track_order,
                    planned_block.timeline_start_tick,
                    planned_block.segment_id,
                ),
            )
        )
        if len(active) > MAX_ACTIVE_BLOCKS:
            raise LayoutPlanError("An interval has more than four active blocks")
        slots = slot_rects(len(active), canvas=canvas)
        slot_plans = tuple(
            _slot_plan(
                block,
                slot,
                output_domain=normalized_output_domain,
            )
            for block, slot in zip(active, slots, strict=True)
        )
        intervals.append(
            LayoutInterval(
                start_tick=start_tick,
                end_tick=end_tick,
                active_blocks=active,
                slots=slot_plans,
            )
        )

    if normalized_output_domain == FramingDomain.FULL_CANVAS_REEL and any(
        len(interval.active_blocks) > 1 for interval in intervals
    ):
        raise LayoutPlanError(
            "Standalone full-canvas planning cannot combine multiple active blocks"
        )
    return LayoutPlan(
        canvas=canvas,
        timing_mode=("legacy-ripple" if legacy else timeline.timing_mode),
        output_domain=normalized_output_domain,
        final_duration_ticks=final_duration,
        boundaries=ordered_boundaries,
        included_blocks=tuple(planned),
        intervals=tuple(intervals),
    )


def _slot_plan(
    block: PlannedBlock,
    slot: PixelRect,
    *,
    output_domain: FramingDomain,
) -> SlotPlan:
    transform = block.visual_transform
    segment_triplicate = block.triplicate_enabled
    if segment_triplicate:
        # The canonical v4 model stores the shared triplicate transform on both
        # the segment and its group. The model validation guarantees equality.
        crops = plan_triplicate(
            block.source_geometry,
            slot,
            transform,
            output_domain=output_domain,
        )
        return SlotPlan(block=block, slot=slot, triplicate_crops=crops)
    return SlotPlan(
        block=block,
        slot=slot,
        crop=plan_crop(
            block.source_geometry,
            slot,
            transform,
            output_domain=output_domain,
        ),
    )


def _ordered_timeline_blocks(
    timeline: SegmentTimeline,
) -> tuple[dict[str, int], tuple[Segment, ...]]:
    if timeline.tracks is None:
        return {"track-1": 0}, tuple(
            sorted(
                timeline.segment_items,
                key=lambda block: (block.timeline_start_ticks, block.segment_id),
            )
        )
    track_order = {track.track_id: index for index, track in enumerate(timeline.tracks)}
    blocks = tuple(
        block
        for track in timeline.tracks
        for block in sorted(
            track.blocks,
            key=lambda item: (item.timeline_start_ticks, item.segment_id),
        )
    )
    return track_order, blocks


def _is_included(block: Segment) -> bool:
    return not block.deleted


def _normalize_geometries(
    source_geometries: Mapping[str, SourceGeometry],
) -> dict[str, SourceGeometry]:
    if not isinstance(source_geometries, Mapping):
        raise LayoutPlanError("Source geometries must be a mapping")
    normalized: dict[str, SourceGeometry] = {}
    for source_id, geometry in source_geometries.items():
        if not isinstance(source_id, str) or not source_id:
            raise LayoutPlanError("Source geometry identifiers must be non-empty")
        if not isinstance(geometry, SourceGeometry):
            raise LayoutPlanError(f"Source geometry is invalid: {source_id}")
        if geometry.source_id != source_id:
            raise LayoutPlanError(f"Source geometry key does not match source_id: {source_id}")
        normalized[source_id] = geometry
    return normalized


def _sample_aspect_ratio(metadata: Mapping[str, Any]) -> tuple[int, int]:
    raw_num = metadata.get("sar_num")
    raw_den = metadata.get("sar_den")
    if raw_num is not None or raw_den is not None:
        try:
            num = _strict_metadata_integer(raw_num, "SAR numerator")
            den = _strict_metadata_integer(raw_den, "SAR denominator")
        except LayoutPlanError as error:
            raise LayoutPlanError("Source sample aspect ratio is invalid") from error
        return _reduce_ratio(num, den)
    raw = metadata.get("sample_aspect_ratio", metadata.get("sar", "1:1"))
    if raw in (None, "", "N/A", "0:1", "0/1"):
        return 1, 1
    if isinstance(raw, str):
        separator = ":" if ":" in raw else "/" if "/" in raw else None
        if separator is not None:
            pieces = raw.split(separator)
            if len(pieces) == 2:
                try:
                    return _reduce_ratio(
                        _strict_metadata_integer(pieces[0], "SAR numerator"),
                        _strict_metadata_integer(pieces[1], "SAR denominator"),
                    )
                except LayoutPlanError as error:
                    raise LayoutPlanError("Source sample aspect ratio is invalid") from error
    raise LayoutPlanError("Source sample aspect ratio is invalid")


def _strict_metadata_integer(value: object, label: str) -> int:
    if isinstance(value, bool):
        raise LayoutPlanError(f"{label} must be an integer")
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    raise LayoutPlanError(f"{label} must be an integer")


def _reduce_ratio(num: int, den: int) -> tuple[int, int]:
    if num <= 0 or den <= 0:
        raise LayoutPlanError("Source sample aspect ratio must be positive")
    divisor = math.gcd(num, den)
    return num // divisor, den // divisor


def _cover_dimensions(
    source: SourceGeometry,
    target: PixelRect,
    zoom: float,
) -> tuple[int, int]:
    zoom_fraction = _fraction(zoom)
    if zoom_fraction <= 0:
        raise LayoutPlanError("Visual transform zoom must be positive")
    cover = max(
        Fraction(target.width, 1) / source.display_width,
        Fraction(target.height, source.height),
    )
    scaled_width = max(
        target.width,
        _ceil_fraction(source.display_width * cover * zoom_fraction),
    )
    scaled_height = max(
        target.height,
        _ceil_fraction(Fraction(source.height, 1) * cover * zoom_fraction),
    )
    return scaled_width, scaled_height


def _validate_output_domain(
    source: SourceGeometry,
    output_domain: FramingDomain,
) -> None:
    normalized = _coerce_domain(output_domain)
    if normalized == FramingDomain.NATIVE_SOURCE:
        raise LayoutPlanError("A crop plan must produce a framed output domain")
    if source.input_domain != FramingDomain.NATIVE_SOURCE:
        raise LayoutPlanError(
            "Final-slot geometry must consume native-source media; "
            "preframed artifacts are not accepted"
        )


def _coerce_domain(value: FramingDomain | str) -> FramingDomain:
    try:
        return value if isinstance(value, FramingDomain) else FramingDomain(value)
    except ValueError as error:
        raise LayoutPlanError("Unsupported framing domain") from error


def _fraction(value: float | int) -> Fraction:
    try:
        return Fraction(str(value))
    except (ValueError, ZeroDivisionError) as error:
        raise LayoutPlanError("Geometry values must be finite numbers") from error


def _ceil_fraction(value: Fraction) -> int:
    return (value.numerator + value.denominator - 1) // value.denominator


def _round_half_up(value: Fraction) -> int:
    return math.floor(value + Fraction(1, 2))


def _clamp(value: int, lower: int, upper: int) -> int:
    return max(lower, min(upper, value))


__all__ = [
    "CANVAS_HEIGHT",
    "CANVAS_WIDTH",
    "CropPlan",
    "FramingDomain",
    "FramingIdentity",
    "LayoutInterval",
    "LayoutPlan",
    "LayoutPlanError",
    "PixelRect",
    "PlannedBlock",
    "SlotPlan",
    "SourceGeometry",
    "SourceRangePlan",
    "partition_pixels",
    "plan_crop",
    "plan_project_layout",
    "plan_triplicate",
    "slot_rects",
    "source_geometries_from_project",
]
