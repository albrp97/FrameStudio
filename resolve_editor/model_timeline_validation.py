from __future__ import annotations

import math
from fractions import Fraction
from typing import Mapping, Protocol

from .model_types import (
    _TIME_EPSILON,
    ProjectValidationError,
    Segment,
)


class TimelineValidationTarget(Protocol):
    source_duration_seconds: float
    segments: tuple[Segment, ...] | None
    mixed_source: bool
    timebase: str
    frame_rate: str | None

    @property
    def source_durations(self) -> Mapping[str, float] | None: ...

    @property
    def has_explicit_timeline(self) -> bool: ...

    @property
    def timeline_duration_seconds(self) -> float: ...

    @property
    def edited_duration_seconds(self) -> float: ...


def validate_timeline(timeline: TimelineValidationTarget) -> None:
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
