from __future__ import annotations

import math
from fractions import Fraction
from typing import Mapping, Protocol, Sequence

from .model_types import (
    _TIME_EPSILON,
    ProjectValidationError,
    Segment,
)


class TimelineTrackTarget(Protocol):
    @property
    def track_id(self) -> str: ...

    @property
    def blocks(self) -> tuple[Segment, ...]: ...


class TimelineValidationTarget(Protocol):
    source_duration_seconds: float
    segments: tuple[Segment, ...] | None
    mixed_source: bool
    timebase: str
    frame_rate: str | None
    ripple: bool
    timing_mode: str
    active_track_id: str | None

    @property
    def tracks(self) -> Sequence[TimelineTrackTarget] | None: ...

    @property
    def source_durations(self) -> Mapping[str, float] | None: ...

    @property
    def source_durations_ticks(self) -> Mapping[str, int] | None: ...

    @property
    def has_explicit_timeline(self) -> bool: ...

    @property
    def timeline_duration_seconds(self) -> float: ...

    @property
    def edited_duration_seconds(self) -> float: ...

    @property
    def editing_duration_seconds(self) -> float: ...

    @property
    def included_duration_seconds(self) -> float: ...

    @property
    def final_duration_seconds(self) -> float: ...


def validate_timeline(timeline: TimelineValidationTarget) -> None:
    if timeline.tracks is not None:
        validate_synchronized_timeline(timeline)
        return
    if timeline.mixed_source:
        validate_mixed_timeline(timeline)
        return
    segments = timeline.segments
    if segments is None or not segments:
        raise ProjectValidationError("Segment timeline must contain at least one segment")
    seen_ids: set[str] = set()
    seen_group_ids: set[str] = set()
    for index, segment in enumerate(segments):
        if not isinstance(segment, Segment):
            raise ProjectValidationError(f"Segment at index {index} must be a Segment")
        if segment.segment_id in seen_ids:
            raise ProjectValidationError(f"Duplicate segment_id: {segment.segment_id}")
        seen_ids.add(segment.segment_id)
        if segment.triplicate is not None:
            group_id = segment.triplicate.group_id
            if group_id in seen_group_ids:
                raise ProjectValidationError(f"Duplicate triplicate group_id: {group_id}")
            seen_group_ids.add(group_id)
        if segment.start_seconds < 0 or segment.end_seconds > timeline.source_duration_seconds:
            raise ProjectValidationError(
                f"Segment {segment.segment_id} is outside the source duration"
            )
    source_order = tuple(
        sorted(
            segments,
            key=lambda segment: (segment.start_seconds, segment.end_seconds),
        )
    )
    source_end = 0.0
    for index, segment in enumerate(source_order):
        if index == 0 and not math.isclose(
            segment.start_seconds,
            0.0,
            rel_tol=0.0,
            abs_tol=_TIME_EPSILON,
        ):
            raise ProjectValidationError("First source segment must start at zero")
        if segment.start_seconds > source_end + _TIME_EPSILON:
            if index == 0:
                raise ProjectValidationError("First source segment must start at zero")
            raise ProjectValidationError(
                f"Segment {segment.segment_id} is not contiguous in source coverage"
            )
        source_end = max(source_end, segment.end_seconds)
    if not math.isclose(
        source_end,
        timeline.source_duration_seconds,
        rel_tol=0.0,
        abs_tol=_TIME_EPSILON,
    ):
        raise ProjectValidationError("Source coverage must end at the source duration")
    explicit_timeline = timeline.has_explicit_timeline
    if explicit_timeline:
        if any(segment.timeline_start_seconds is None for segment in segments):
            raise ProjectValidationError(
                "Timeline placement must be provided for every one-source segment"
            )
        timeline_end = 0.0
        for index, segment in enumerate(segments):
            if not math.isclose(
                segment.timeline_start,
                timeline_end,
                rel_tol=0.0,
                abs_tol=_TIME_EPSILON,
            ):
                if index == 0:
                    raise ProjectValidationError("First timeline segment must start at zero")
                raise ProjectValidationError(
                    f"Segment {segment.segment_id} is not contiguous in timeline order"
                )
            if not math.isclose(
                segment.timeline_end - segment.timeline_start,
                segment.duration_seconds,
                rel_tol=0.0,
                abs_tol=_TIME_EPSILON,
            ):
                raise ProjectValidationError(
                    f"Segment {segment.segment_id} timeline duration does not match its source duration"
                )
            timeline_end = segment.timeline_end
        if not math.isclose(
            timeline_end,
            timeline.timeline_duration_seconds,
            rel_tol=0.0,
            abs_tol=_TIME_EPSILON,
        ):
            raise ProjectValidationError("Timeline placement must end at the source duration")
    else:
        timeline_end = 0.0
        for index, segment in enumerate(segments):
            if not math.isclose(
                segment.start_seconds,
                timeline_end,
                rel_tol=0.0,
                abs_tol=_TIME_EPSILON,
            ):
                if index == 0:
                    raise ProjectValidationError("First segment must start at zero")
                raise ProjectValidationError(
                    f"Segment {segment.segment_id} is not contiguous with the previous segment"
                )
            timeline_end = segment.end_seconds
    edited_duration = timeline.edited_duration_seconds
    if not math.isfinite(edited_duration) or edited_duration < 0:
        raise ProjectValidationError("Edited duration must not be negative")


def validate_synchronized_timeline(timeline: TimelineValidationTarget) -> None:
    tracks = timeline.tracks
    if tracks is None:
        raise ProjectValidationError("Synchronized timeline tracks are required")
    if not 1 <= len(tracks) <= 4:
        raise ProjectValidationError(
            "Synchronized timelines must contain between one and four tracks"
        )
    if timeline.timing_mode not in {"legacy-ripple", "absolute"}:
        raise ProjectValidationError("Synchronized timelines have an unsupported timing mode")
    if timeline.timing_mode == "legacy-ripple" and len(tracks) != 1:
        raise ProjectValidationError(
            "Legacy-ripple synchronized timelines must contain exactly one track"
        )
    if timeline.timing_mode == "legacy-ripple" and timeline.ripple is not True:
        raise ProjectValidationError("Legacy-ripple timelines must enable ripple timing")
    if timeline.timebase != "1/1000000":
        raise ProjectValidationError("Synchronized timeline timebase must be 1/1000000")
    if not isinstance(timeline.ripple, bool):
        raise ProjectValidationError("Synchronized timeline ripple must be a boolean")
    if timeline.frame_rate is not None:
        if not isinstance(timeline.frame_rate, str) or not timeline.frame_rate:
            raise ProjectValidationError("Synchronized timeline frame rate must be a string")
        try:
            if Fraction(timeline.frame_rate) <= 0:
                raise ValueError
        except (TypeError, ValueError, ZeroDivisionError):
            raise ProjectValidationError(
                "Synchronized timeline frame rate must be a positive rate"
            ) from None
    if timeline.active_track_id not in {track.track_id for track in tracks}:
        raise ProjectValidationError("Synchronized timeline active_track_id must reference a track")
    source_durations = timeline.source_durations
    if not isinstance(source_durations, Mapping) or not source_durations:
        raise ProjectValidationError("Synchronized timeline source durations are required")
    source_duration_ticks = timeline.source_durations_ticks
    if not isinstance(source_duration_ticks, Mapping) or not source_duration_ticks:
        raise ProjectValidationError("Synchronized timeline source duration ticks are required")
    if any(not isinstance(source_id, str) or not source_id for source_id in source_durations):
        raise ProjectValidationError(
            "Synchronized timeline source identifiers must be non-empty strings"
        )
    if set(source_duration_ticks) != set(source_durations):
        raise ProjectValidationError(
            "Synchronized timeline source duration representations must match"
        )
    if any(
        not isinstance(ticks, int) or isinstance(ticks, bool) or ticks <= 0
        for ticks in source_duration_ticks.values()
    ):
        raise ProjectValidationError(
            "Synchronized timeline source duration ticks must be positive integers"
        )
    seen_track_ids: set[str] = set()
    seen_segment_ids: set[str] = set()
    seen_block_ids: set[str] = set()
    seen_group_ids: set[str] = set()
    flattened: list[Segment] = []
    for track_index, track in enumerate(tracks):
        track_id = getattr(track, "track_id", None)
        blocks = track.blocks
        if not isinstance(track_id, str) or not track_id:
            raise ProjectValidationError(
                f"Synchronized track at index {track_index} needs a track_id"
            )
        if track_id in seen_track_ids:
            raise ProjectValidationError(f"Duplicate track_id: {track_id}")
        seen_track_ids.add(track_id)
        if not isinstance(blocks, tuple):
            raise ProjectValidationError(f"Track {track_id} blocks must be a tuple")
        ordered = tuple(
            sorted(blocks, key=lambda block: (block.timeline_start_ticks, block.timeline_end_ticks))
        )
        previous_end_ticks = 0
        for block_index, segment in enumerate(ordered):
            if not isinstance(segment, Segment):
                raise ProjectValidationError(
                    f"Track {track_id} block at index {block_index} must be a Segment"
                )
            if segment.track_id != track_id:
                raise ProjectValidationError(
                    f"Track block {segment.segment_id} references an unexpected track"
                )
            if segment.segment_id in seen_segment_ids:
                raise ProjectValidationError(f"Duplicate segment_id: {segment.segment_id}")
            seen_segment_ids.add(segment.segment_id)
            if segment.block_id is not None:
                if segment.block_id in seen_block_ids:
                    raise ProjectValidationError(f"Duplicate block_id: {segment.block_id}")
                seen_block_ids.add(segment.block_id)
            if segment.triplicate is not None:
                group_id = segment.triplicate.group_id
                if group_id in seen_group_ids:
                    raise ProjectValidationError(f"Duplicate triplicate group_id: {group_id}")
                seen_group_ids.add(group_id)
            if not isinstance(segment.source_id, str):
                raise ProjectValidationError(
                    f"Timeline block {segment.segment_id} needs a source_id"
                )
            source_duration = source_durations.get(segment.source_id)
            source_duration_tick = source_duration_ticks.get(segment.source_id)
            if source_duration is None or source_duration_tick is None:
                raise ProjectValidationError(
                    f"Timeline block {segment.segment_id} references unknown source: "
                    f"{segment.source_id}"
                )
            if segment.source_start_ticks < 0 or segment.source_end_ticks > source_duration_tick:
                raise ProjectValidationError(
                    f"Timeline block {segment.segment_id} exceeds its source range"
                )
            if (
                segment.timeline_end_ticks - segment.timeline_start_ticks
                != segment.source_end_ticks - segment.source_start_ticks
            ):
                raise ProjectValidationError(
                    f"Timeline block {segment.segment_id} occupied duration does not "
                    "match its source duration"
                )
            if block_index and segment.timeline_start_ticks < previous_end_ticks:
                raise ProjectValidationError(
                    f"Timeline block {segment.segment_id} overlaps another block on track "
                    f"{track_id}"
                )
            previous_end_ticks = max(previous_end_ticks, segment.timeline_end_ticks)
            flattened.append(segment)
    if tuple(flattened) != tuple(block for track in tracks for block in track.blocks):
        raise ProjectValidationError("Synchronized timeline blocks are not in track order")
    editing_duration = timeline.editing_duration_seconds
    included_duration = timeline.included_duration_seconds
    final_duration = timeline.final_duration_seconds
    if not all(
        math.isfinite(value) and value >= 0
        for value in (editing_duration, included_duration, final_duration)
    ):
        raise ProjectValidationError("Synchronized timeline durations must be non-negative")


def validate_mixed_timeline(timeline: TimelineValidationTarget) -> None:
    segments = timeline.segments
    if segments is None or not segments:
        raise ProjectValidationError("Timeline must contain at least one block")
    if timeline.timebase != "1/1000000":
        raise ProjectValidationError("Timeline timebase must be 1/1000000")
    if timeline.frame_rate is not None:
        if not isinstance(timeline.frame_rate, str) or not timeline.frame_rate:
            raise ProjectValidationError("Timeline frame rate must be a non-empty string")
        try:
            if Fraction(timeline.frame_rate) <= 0:
                raise ValueError
        except (TypeError, ValueError, ZeroDivisionError):
            raise ProjectValidationError("Timeline frame rate must be a positive rate") from None
    seen_ids: set[str] = set()
    seen_group_ids: set[str] = set()
    previous_end = 0.0
    maximum_end = 0.0
    for index, segment in enumerate(segments):
        if not isinstance(segment, Segment):
            raise ProjectValidationError(f"Timeline block at index {index} must be a Segment")
        if segment.segment_id in seen_ids:
            raise ProjectValidationError(f"Duplicate segment_id: {segment.segment_id}")
        seen_ids.add(segment.segment_id)
        if segment.triplicate is not None:
            group_id = segment.triplicate.group_id
            if group_id in seen_group_ids:
                raise ProjectValidationError(f"Duplicate triplicate group_id: {group_id}")
            seen_group_ids.add(group_id)
        if segment.source_id is None:
            raise ProjectValidationError(f"Timeline block {segment.segment_id} needs a source_id")
        timeline_start = segment.timeline_start
        timeline_end = segment.timeline_end
        if timeline_start < 0 or timeline_end <= timeline_start:
            raise ProjectValidationError(
                f"Timeline block {segment.segment_id} has invalid placement"
            )
        if index and timeline_start < previous_end - _TIME_EPSILON:
            raise ProjectValidationError(
                f"Timeline block {segment.segment_id} overlaps the previous block"
            )
        if timeline.source_durations is not None:
            source_duration = timeline.source_durations.get(segment.source_id)
            if source_duration is None:
                raise ProjectValidationError(
                    f"Timeline block references unknown source: {segment.source_id}"
                )
            if segment.end_seconds > source_duration + _TIME_EPSILON:
                raise ProjectValidationError(
                    f"Timeline block {segment.segment_id} exceeds its source duration"
                )
        previous_end = timeline_end
        maximum_end = max(maximum_end, timeline_end)
    if not math.isclose(
        maximum_end,
        timeline.source_duration_seconds,
        rel_tol=0.0,
        abs_tol=_TIME_EPSILON,
    ):
        raise ProjectValidationError("Timeline duration does not match its block placements")
    edited_duration = timeline.edited_duration_seconds
    if not math.isfinite(edited_duration) or edited_duration < 0:
        raise ProjectValidationError("Edited duration must not be negative")
