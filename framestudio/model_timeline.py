from __future__ import annotations

import math
import uuid
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol, Sequence

from .model_timeline_validation import validate_timeline
from .model_types import (
    _TIME_EPSILON,
    PROJECT_TIMEBASE,
    ProjectValidationError,
    Segment,
    TimelineTrack,
    TriplicateGroup,
    VisualTransform,
    _assign_missing_segment_colors,
    _finite_float,
    _split_segment_color_indices,
    seconds_to_ticks,
    ticks_to_seconds,
)
from .removal_history import (
    RemovalHistory,
    RemovalReceipt,
    RemovalUndoResult,
    TimelineStateSnapshot,
    _RuntimeContext,
)

MAX_TRACK_COUNT = 4
TIMELINE_MODEL_VERSION = 1
LEGACY_TIMING_MODE = "legacy-ripple"
ABSOLUTE_TIMING_MODE = "absolute"


class _ProjectOwner(Protocol):
    @property
    def runtime_identity(self) -> str: ...

    @property
    def runtime_epoch(self) -> int: ...

    def _sync_timeline_state(self) -> None: ...


def _required_tick(value: object, name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ProjectValidationError(f"{name} must be a non-negative integer")
    return value


def _segment_with_ticks(
    segment: Segment,
    *,
    timeline_start_ticks: int,
    timeline_end_ticks: int,
    track_id: str | None = None,
    new_id: bool = False,
    source_start_ticks: int | None = None,
    source_end_ticks: int | None = None,
    triplicate: TriplicateGroup | None = None,
    color_index: int | None = None,
) -> Segment:
    canonical = segment.to_dict(
        canonical_ticks=True,
        track_id=segment.track_id if track_id is None else track_id,
    )
    segment_id = uuid.uuid4().hex if new_id else segment.segment_id
    canonical.update(
        {
            "segment_id": segment_id,
            "block_id": (segment_id if new_id else (segment.block_id or segment_id)),
            "source_start_ticks": (
                segment.source_start_ticks if source_start_ticks is None else source_start_ticks
            ),
            "source_end_ticks": (
                segment.source_end_ticks if source_end_ticks is None else source_end_ticks
            ),
            "timeline_start_ticks": timeline_start_ticks,
            "timeline_end_ticks": timeline_end_ticks,
            "color_index": (canonical["color_index"] if color_index is None else color_index),
            "triplicate": (canonical["triplicate"] if triplicate is None else triplicate.to_dict()),
        }
    )
    return Segment.from_canonical_dict(
        canonical,
        expected_track_id=canonical["track_id"],
    )


def _sorted_blocks(blocks: Sequence[Segment]) -> tuple[Segment, ...]:
    return tuple(
        sorted(
            blocks,
            key=lambda block: (
                block.timeline_start_ticks,
                block.timeline_end_ticks,
                block.segment_id,
            ),
        )
    )


def _earliest_fit(
    requested_start_ticks: int,
    duration_ticks: int,
    occupied: Sequence[Segment],
) -> int:
    candidate_start = requested_start_ticks
    for block in sorted(
        occupied,
        key=lambda item: (item.timeline_start_ticks, item.timeline_end_ticks, item.segment_id),
    ):
        candidate_end = candidate_start + duration_ticks
        if candidate_end <= block.timeline_start_ticks:
            break
        if candidate_start >= block.timeline_end_ticks:
            continue
        candidate_start = block.timeline_end_ticks
    return candidate_start


@dataclass
class SegmentTimeline(_RuntimeContext):
    source_duration_seconds: float
    segments: tuple[Segment, ...] | None = None
    mixed_source: bool = False
    source_durations: dict[str, float] | None = None
    source_durations_ticks: dict[str, int] | None = None
    timebase: str = "1/1000000"
    frame_rate: str | None = None
    ripple: bool = True
    timing_mode: str = LEGACY_TIMING_MODE
    tracks: tuple[TimelineTrack, ...] | None = None
    active_track_id: str | None = None
    mutation_revision: int = 0
    timeline_model_version: int = TIMELINE_MODEL_VERSION
    _project_owner: _ProjectOwner | None = field(
        default=None,
        init=False,
        repr=False,
        compare=False,
    )
    _removal_history: RemovalHistory = field(
        default_factory=RemovalHistory,
        init=False,
        repr=False,
        compare=False,
    )

    def __post_init__(self) -> None:
        self._initialize_runtime_context()
        self.source_duration_seconds = _finite_float(
            self.source_duration_seconds,
            "Timeline duration" if self.mixed_source else "Source duration",
        )
        if self.source_duration_seconds <= 0:
            raise ProjectValidationError("Timeline duration must be greater than zero")
        if (
            not isinstance(self.mutation_revision, int)
            or isinstance(self.mutation_revision, bool)
            or self.mutation_revision < 0
        ):
            raise ProjectValidationError(
                "Timeline mutation_revision must be a non-negative integer"
            )
        if (
            not isinstance(self.timeline_model_version, int)
            or isinstance(self.timeline_model_version, bool)
            or self.timeline_model_version != TIMELINE_MODEL_VERSION
        ):
            raise ProjectValidationError(
                f"Unsupported timeline model version: {self.timeline_model_version!r}"
            )
        if not isinstance(self.timing_mode, str) or self.timing_mode not in {
            LEGACY_TIMING_MODE,
            ABSOLUTE_TIMING_MODE,
        }:
            raise ProjectValidationError(f"Unsupported timeline timing mode: {self.timing_mode!r}")
        if self.segments is None:
            self.segments = (
                Segment.create(
                    0.0,
                    self.source_duration_seconds,
                ),
            )
        else:
            self.segments = tuple(self.segments)
        self.segments = _assign_missing_segment_colors(self.segments)
        if self.tracks is not None:
            self.tracks = self._normalize_tracks(self.tracks)
            if not self.tracks:
                raise ProjectValidationError("A synchronized timeline needs at least one track")
            self.segments = tuple(block for track in self.tracks for block in track.blocks)
            if self.active_track_id is None:
                self.active_track_id = self.tracks[0].track_id
            if self.source_durations_ticks is None:
                if not isinstance(self.source_durations, Mapping) or not self.source_durations:
                    raise ProjectValidationError(
                        "Synchronized timeline source durations are required"
                    )
                self.source_durations_ticks = {
                    source_id: seconds_to_ticks(duration)
                    for source_id, duration in self.source_durations.items()
                }
            else:
                if not isinstance(self.source_durations_ticks, Mapping):
                    raise ProjectValidationError(
                        "Synchronized timeline source durations must be an object"
                    )
                self.source_durations_ticks = dict(self.source_durations_ticks)
            for source_id, ticks in self.source_durations_ticks.items():
                if not isinstance(source_id, str) or not source_id:
                    raise ProjectValidationError(
                        "Synchronized timeline source identifiers must be non-empty strings"
                    )
                if not isinstance(ticks, int) or isinstance(ticks, bool) or ticks <= 0:
                    raise ProjectValidationError(
                        f"Synchronized timeline source duration for {source_id} "
                        "must be a positive integer"
                    )
            self.source_durations = {
                source_id: ticks_to_seconds(ticks)
                for source_id, ticks in self.source_durations_ticks.items()
            }
        elif self.timing_mode != LEGACY_TIMING_MODE:
            raise ProjectValidationError("Absolute timelines must provide tracks")
        elif self.source_durations is not None:
            if not isinstance(self.source_durations, Mapping):
                raise ProjectValidationError("Source durations must be an object")
            self.source_durations = {
                source_id: _finite_float(duration, f"Source duration for {source_id}")
                for source_id, duration in self.source_durations.items()
            }
        self.validate()

    @classmethod
    def from_segments(
        cls,
        source_duration_seconds: float,
        segments: tuple[Segment, ...] | list[Segment],
    ) -> SegmentTimeline:
        return cls(source_duration_seconds, tuple(segments))

    @classmethod
    def from_blocks(
        cls,
        blocks: Sequence[Segment],
        *,
        duration_seconds: float | None = None,
        source_durations: Mapping[str, float] | None = None,
        timebase: str = "1/1000000",
        frame_rate: str | None = None,
        ripple: bool = True,
        mutation_revision: int = 0,
    ) -> SegmentTimeline:
        block_items = tuple(blocks)
        if not block_items:
            raise ProjectValidationError("Timeline must contain at least one block")
        next_position = 0.0
        positioned: list[Segment] = []
        for block in block_items:
            if not isinstance(block, Segment):
                raise ProjectValidationError("Timeline block must be a Segment")
            start = block.timeline_start
            end = block.timeline_end
            if block.timeline_start_seconds is None:
                start = next_position
                end = start + block.duration_seconds
            positioned.append(
                Segment(
                    segment_id=block.segment_id,
                    start_seconds=block.start_seconds,
                    end_seconds=block.end_seconds,
                    deleted=block.deleted,
                    source_id=block.source_id,
                    timeline_start_seconds=start,
                    timeline_end_seconds=end,
                    state=block.state,
                    block_id=block.block_id,
                    color_index=(block.color_index if block._color_index_explicit else None),
                    visual_transform=block.visual_transform,
                    triplicate=block.triplicate,
                )
            )
            next_position = end
        calculated_duration = max(block.timeline_end for block in positioned)
        if duration_seconds is not None:
            calculated_duration = _finite_float(duration_seconds, "Timeline duration")
        return cls(
            calculated_duration,
            tuple(positioned),
            mixed_source=True,
            source_durations=(None if source_durations is None else dict(source_durations)),
            timebase=timebase,
            frame_rate=frame_rate,
            ripple=ripple,
            mutation_revision=mutation_revision,
        )

    @classmethod
    def from_tracks(
        cls,
        tracks: Sequence[TimelineTrack],
        *,
        source_durations: Mapping[str, float],
        source_durations_ticks: Mapping[str, int] | None = None,
        active_track_id: str | None = None,
        timebase: str = "1/1000000",
        frame_rate: str | None = None,
        ripple: bool = False,
        timing_mode: str = ABSOLUTE_TIMING_MODE,
        mutation_revision: int = 0,
    ) -> SegmentTimeline:
        track_items = tuple(tracks)
        if not track_items:
            raise ProjectValidationError("A synchronized timeline needs at least one track")
        if len(track_items) > MAX_TRACK_COUNT:
            raise ProjectValidationError(
                f"A synchronized timeline supports at most {MAX_TRACK_COUNT} tracks"
            )
        if not isinstance(source_durations, Mapping) or not source_durations:
            raise ProjectValidationError(
                "Synchronized timeline source_durations must be a non-empty object"
            )
        if any(not isinstance(source_id, str) or not source_id for source_id in source_durations):
            raise ProjectValidationError(
                "Synchronized timeline source identifiers must be non-empty strings"
            )
        durations = {
            source_id: _finite_float(duration, f"Source duration for {source_id}")
            for source_id, duration in source_durations.items()
        }
        if any(duration <= 0 for duration in durations.values()):
            raise ProjectValidationError("Source durations must be greater than zero")
        if source_durations_ticks is None:
            duration_ticks = {
                source_id: seconds_to_ticks(duration) for source_id, duration in durations.items()
            }
        else:
            if set(source_durations_ticks) != set(durations):
                raise ProjectValidationError(
                    "Synchronized timeline source duration tick identifiers must match"
                )
            duration_ticks = dict(source_durations_ticks)
            if any(
                not isinstance(ticks, int) or isinstance(ticks, bool) or ticks <= 0
                for ticks in duration_ticks.values()
            ):
                raise ProjectValidationError(
                    "Synchronized timeline source duration ticks must be positive integers"
                )
            if any(
                duration_ticks[source_id] != seconds_to_ticks(duration)
                for source_id, duration in durations.items()
            ):
                raise ProjectValidationError(
                    "Synchronized timeline source duration ticks do not match seconds"
                )
        first_duration = ticks_to_seconds(max(duration_ticks.values()))
        return cls(
            source_duration_seconds=first_duration,
            segments=tuple(block for track in track_items for block in track.blocks),
            mixed_source=True,
            source_durations={
                source_id: ticks_to_seconds(ticks) for source_id, ticks in duration_ticks.items()
            },
            source_durations_ticks=duration_ticks,
            timebase=timebase,
            frame_rate=frame_rate,
            ripple=ripple,
            timing_mode=timing_mode,
            tracks=track_items,
            active_track_id=active_track_id,
            mutation_revision=mutation_revision,
        )

    def _normalize_tracks(
        self,
        tracks: Sequence[TimelineTrack],
    ) -> tuple[TimelineTrack, ...]:
        prepared: list[Segment] = []
        track_items = tuple(tracks)
        for track in track_items:
            if not isinstance(track, TimelineTrack):
                raise ProjectValidationError("Timeline tracks must be TimelineTrack values")
            prepared.extend(track.blocks)
        colored = _assign_missing_segment_colors(prepared)
        colored_by_id = {block.segment_id: block for block in colored}
        normalized: list[TimelineTrack] = []
        for track in track_items:
            blocks: list[Segment] = []
            for block in track.blocks:
                if block.track_id not in (None, track.track_id):
                    raise ProjectValidationError(
                        f"Track block {block.segment_id} references another track"
                    )
                blocks.append(
                    (
                        colored_by_id[block.segment_id]
                        if block.track_id == track.track_id
                        else colored_by_id[block.segment_id].with_track_id(track.track_id)
                    )
                )
            normalized.append(TimelineTrack(track.track_id, tuple(blocks)))
        return tuple(normalized)

    @property
    def segment_items(self) -> tuple[Segment, ...]:
        if self.segments is None:
            raise ProjectValidationError("Segment timeline must contain segments")
        return self.segments

    @property
    def blocks(self) -> tuple[Segment, ...]:
        return self.segment_items

    @property
    def track_ids(self) -> tuple[str, ...]:
        if self.tracks is None:
            return ()
        return tuple(track.track_id for track in self.tracks)

    @property
    def is_synchronized(self) -> bool:
        return self.tracks is not None

    @property
    def revision(self) -> int:
        return self.mutation_revision

    @property
    def runtime_identity(self) -> str:
        return self._runtime_identity

    @property
    def runtime_epoch(self) -> int:
        return self._runtime_epoch

    @property
    def track_count(self) -> int:
        return len(self.track_ids)

    @property
    def active_track(self) -> TimelineTrack:
        if self.tracks is None or self.active_track_id is None:
            raise ProjectValidationError(
                "An active track is only available on synchronized timelines"
            )
        return self.track_by_id(self.active_track_id)

    @property
    def populated_track_count(self) -> int:
        if self.tracks is None:
            return 0
        return sum(bool(track.blocks) for track in self.tracks)

    @property
    def included_track_count(self) -> int:
        if self.tracks is None:
            return 0
        return sum(any(not block.deleted for block in track.blocks) for track in self.tracks)

    @property
    def duration_seconds(self) -> float:
        return self.timeline_duration_seconds

    @property
    def timeline_duration_seconds(self) -> float:
        if self.tracks is not None:
            return ticks_to_seconds(self.editing_duration_ticks)
        if not self.has_explicit_timeline:
            return self.source_duration_seconds
        return max(segment.timeline_end for segment in self.segment_items)

    @property
    def has_explicit_timeline(self) -> bool:
        if self.tracks is not None:
            return True
        return any(segment.timeline_start_seconds is not None for segment in self.segment_items)

    @property
    def edited_duration_seconds(self) -> float:
        return self.included_duration_seconds

    @property
    def editing_duration_seconds(self) -> float:
        if self.tracks is None:
            return self.timeline_duration_seconds
        return ticks_to_seconds(self.editing_duration_ticks)

    @property
    def included_duration_seconds(self) -> float:
        return ticks_to_seconds(self.included_duration_ticks)

    @property
    def occupied_duration_seconds(self) -> float:
        return self.editing_duration_seconds

    @property
    def legacy_output_duration_seconds(self) -> float:
        if self.tracks is not None and self.timing_mode != LEGACY_TIMING_MODE:
            raise ProjectValidationError(
                "Synchronized timelines do not have one implicit legacy output duration"
            )
        return self.included_duration_seconds

    @property
    def absolute_final_duration_seconds(self) -> float:
        return self.final_duration_seconds

    @property
    def final_duration_seconds(self) -> float:
        if self.tracks is None:
            return self.timeline_duration_seconds
        if self.timing_mode == LEGACY_TIMING_MODE:
            return self.included_duration_seconds
        active = self.active_blocks()
        if not active:
            return 0.0
        return ticks_to_seconds(max(segment.timeline_end_ticks for segment in active))

    @property
    def editing_duration_ticks(self) -> int:
        if self.tracks is None:
            return seconds_to_ticks(self.editing_duration_seconds)
        if not self.segment_items:
            return 0
        return max(segment.timeline_end_ticks for segment in self.segment_items)

    @property
    def included_duration_ticks(self) -> int:
        return sum(
            segment.timeline_end_ticks - segment.timeline_start_ticks
            for segment in self.segment_items
            if not segment.deleted
        )

    @property
    def final_duration_ticks(self) -> int:
        if self.tracks is not None and self.timing_mode == LEGACY_TIMING_MODE:
            return self.included_duration_ticks
        if self.tracks is None:
            return seconds_to_ticks(self.final_duration_seconds)
        active = self.active_blocks()
        return 0 if not active else max(segment.timeline_end_ticks for segment in active)

    def occupied_intervals(self, track_id: str | None = None) -> tuple[Segment, ...]:
        if self.tracks is None:
            if track_id is not None:
                raise ProjectValidationError("Legacy timelines do not have track identities")
            return tuple(sorted(self.segment_items, key=lambda block: block.timeline_start))
        tracks = (self.track_by_id(track_id),) if track_id is not None else self.tracks
        return tuple(
            block
            for track in tracks
            for block in sorted(track.blocks, key=lambda item: item.timeline_start)
        )

    def active_intervals(self, track_id: str | None = None) -> tuple[Segment, ...]:
        return tuple(block for block in self.occupied_intervals(track_id) if not block.deleted)

    def absolute_active_intervals(self, track_id: str | None = None) -> tuple[Segment, ...]:
        return self.active_intervals(track_id)

    def legacy_active_intervals(
        self,
        track_id: str | None = None,
    ) -> tuple[tuple[Segment, float, float], ...]:
        if self.tracks is not None and track_id is None:
            raise ProjectValidationError(
                "Synchronized timelines require a track_id for legacy projection"
            )
        output_position = 0.0
        intervals: list[tuple[Segment, float, float]] = []
        for block in self.active_intervals(track_id):
            end = output_position + block.duration_seconds
            intervals.append((block, output_position, end))
            output_position = end
        return tuple(intervals)

    def grouped_blocks_by_track_source(
        self,
    ) -> dict[tuple[str, str], tuple[Segment, ...]]:
        """Group included blocks for independent track/source reels."""
        groups: dict[tuple[str, str], list[Segment]] = {}
        for block in self.active_intervals():
            if block.source_id is None:
                continue
            track_id = block.track_id or "track-1"
            groups.setdefault((track_id, block.source_id), []).append(block)
        return {key: tuple(value) for key, value in groups.items()}

    def absolute_to_output_seconds(self, position_seconds: float) -> float:
        position = _finite_float(position_seconds, "Absolute timeline position")
        if self.tracks is None:
            return self.timeline_to_edited_position(position)
        return max(0.0, min(self.final_duration_seconds, position))

    def output_to_absolute_seconds(self, position_seconds: float) -> float:
        position = _finite_float(position_seconds, "Output position")
        if self.tracks is None:
            return self.edited_to_timeline_position(position)
        return max(0.0, min(self.final_duration_seconds, position))

    def track_by_id(self, track_id: str) -> TimelineTrack:
        if self.tracks is None:
            raise ProjectValidationError(
                "Track identity is only available on synchronized timelines"
            )
        for track in self.tracks:
            if track.track_id == track_id:
                return track
        raise ProjectValidationError(f"Unknown track_id: {track_id}")

    def set_active_track(self, track_id: str) -> None:
        if self.tracks is None:
            raise ProjectValidationError(
                "Convert the project to synchronized timing before selecting a track"
            )
        self.track_by_id(track_id)
        if self.active_track_id == track_id:
            return
        self.active_track_id = track_id
        self._invalidate_removal_history()

    def add_track(self, track_id: str | None = None) -> str:
        if self.tracks is None or self.timing_mode != ABSOLUTE_TIMING_MODE:
            raise ProjectValidationError(
                "Explicit synchronized conversion confirmation is required before adding tracks"
            )
        if len(self.tracks) >= MAX_TRACK_COUNT:
            raise ProjectValidationError(
                f"A synchronized timeline supports at most {MAX_TRACK_COUNT} tracks"
            )
        if track_id is None:
            index = 1
            existing = set(self.track_ids)
            while f"track-{index}" in existing:
                index += 1
            track_id = f"track-{index}"
        if not isinstance(track_id, str) or not track_id:
            raise ProjectValidationError("Track track_id must be a non-empty string")
        if track_id in self.track_ids:
            raise ProjectValidationError(f"Duplicate track_id: {track_id}")
        candidate = self.tracks + (TimelineTrack(track_id),)
        self._replace_tracks(candidate, active_track_id=self.active_track_id)
        return track_id

    def remove_track(self, track_id: str) -> None:
        if self.tracks is None or self.timing_mode != ABSOLUTE_TIMING_MODE:
            raise ProjectValidationError(
                "Track removal requires an explicitly synchronized project"
            )
        if len(self.tracks) == 1:
            raise ProjectValidationError("A synchronized timeline must retain one track")
        track = self.track_by_id(track_id)
        if track.blocks:
            raise ProjectValidationError("Only empty tracks can be removed")
        candidate = tuple(item for item in self.tracks if item.track_id != track_id)
        active = self.active_track_id if self.active_track_id != track_id else candidate[0].track_id
        self._replace_tracks(candidate, active_track_id=active)

    def replace_track_blocks(
        self,
        track_id: str,
        blocks: Sequence[Segment],
    ) -> None:
        if self.tracks is None or self.timing_mode != ABSOLUTE_TIMING_MODE:
            raise ProjectValidationError("Track blocks require an explicitly synchronized project")
        self.track_by_id(track_id)
        existing_by_id = {
            block.segment_id: block for track in self.tracks for block in track.blocks
        }
        for block in blocks:
            existing = existing_by_id.get(block.segment_id)
            if existing is not None and (
                block.source_id != existing.source_id
                or block.source_start_ticks != existing.source_start_ticks
                or block.source_end_ticks != existing.source_end_ticks
            ):
                raise ProjectValidationError(
                    f"Source range is immutable for segment {block.segment_id}"
                )
        normalized = tuple(
            _segment_with_ticks(
                block,
                timeline_start_ticks=block.timeline_start_ticks,
                timeline_end_ticks=block.timeline_end_ticks,
                track_id=track_id,
            )
            for block in blocks
        )
        normalized = _sorted_blocks(normalized)
        candidate = tuple(
            TimelineTrack(
                track.track_id, normalized if track.track_id == track_id else track.blocks
            )
            for track in self.tracks
        )
        self._replace_tracks(candidate, active_track_id=self.active_track_id)

    def timeline_to_edited_position(self, position_seconds: float) -> float:
        """Map a visible timeline position to the concatenated playback time."""
        if self.tracks is not None and self.timing_mode == ABSOLUTE_TIMING_MODE:
            raise ProjectValidationError(
                "Absolute synchronized timelines do not have a single ripple mapping"
            )
        position = _finite_float(position_seconds, "Timeline position")
        timeline_duration = self.timeline_duration_seconds
        position = max(0.0, min(timeline_duration, position))
        edited_position = 0.0
        for segment in self.segment_items:
            start = segment.timeline_start
            end = segment.timeline_end
            if position <= start + _TIME_EPSILON:
                return edited_position
            if position < end - _TIME_EPSILON:
                if segment.deleted:
                    return edited_position
                return min(
                    self.edited_duration_seconds,
                    edited_position + position - start,
                )
            if position <= end + _TIME_EPSILON:
                if segment.deleted:
                    return edited_position
                return min(
                    self.edited_duration_seconds,
                    edited_position + segment.duration_seconds,
                )
            if not segment.deleted:
                edited_position += segment.duration_seconds
        return min(self.edited_duration_seconds, edited_position)

    def edited_to_timeline_position(self, position_seconds: float) -> float:
        """Map concatenated playback time to the visible timeline position."""
        if self.tracks is not None and self.timing_mode == ABSOLUTE_TIMING_MODE:
            raise ProjectValidationError(
                "Absolute synchronized timelines do not have a single ripple mapping"
            )
        position = _finite_float(position_seconds, "Edited position")
        edited_duration = self.edited_duration_seconds
        position = max(0.0, min(edited_duration, position))
        active_segments = self.active_blocks()
        if not active_segments:
            return 0.0
        edited_position = 0.0
        for index, segment in enumerate(active_segments):
            segment_end = edited_position + segment.duration_seconds
            if position < segment_end - _TIME_EPSILON:
                return segment.timeline_start + position - edited_position
            if position <= segment_end + _TIME_EPSILON:
                if index + 1 < len(active_segments):
                    return active_segments[index + 1].timeline_start
                return segment.timeline_end
            edited_position = segment_end
        return active_segments[-1].timeline_end

    def validate(self) -> None:
        if self.tracks is not None:
            validate_timeline(self)
            return
        validate_timeline(self)

    def split(self, position_seconds: float) -> tuple[Segment, Segment]:
        position = _finite_float(position_seconds, "Split position")
        self.validate()
        for segment in self.segment_items:
            if segment.start_seconds < position < segment.end_seconds:
                return self.split_block(
                    segment.segment_id,
                    position,
                    coordinate="source",
                )
        raise ProjectValidationError("Split position must be strictly inside one segment")

    def split_block(
        self,
        segment_id: str,
        position_seconds: float | None = None,
        *,
        coordinate: str = "source",
        position_ticks: int | None = None,
    ) -> tuple[Segment, Segment]:
        if coordinate not in {"source", "timeline"}:
            raise ProjectValidationError("Split coordinate must be source or timeline")
        if position_seconds is not None and position_ticks is not None:
            raise ProjectValidationError("Choose split position seconds or ticks")
        if position_ticks is not None:
            position_tick_value = _required_tick(position_ticks, "Split position ticks")
            position = ticks_to_seconds(position_tick_value)
        elif position_seconds is not None:
            position = _finite_float(position_seconds, "Split position")
            position_tick_value = seconds_to_ticks(position)
        else:
            raise ProjectValidationError("A split position is required")
        if self.tracks is not None and self.timing_mode == ABSOLUTE_TIMING_MODE:
            return self._split_absolute_block(
                segment_id,
                position_tick_value,
                coordinate=coordinate,
            )
        self.validate()
        for index, segment in enumerate(self.segment_items):
            if segment.segment_id != segment_id:
                continue
            if coordinate == "source":
                if not segment.start_seconds < position < segment.end_seconds:
                    raise ProjectValidationError(
                        "Split position must be strictly inside the selected block"
                    )
                ratio = (position - segment.start_seconds) / segment.duration_seconds
            else:
                if not segment.timeline_start < position < segment.timeline_end:
                    raise ProjectValidationError(
                        "Split position must be strictly inside the selected block"
                    )
                ratio = (position - segment.timeline_start) / (
                    segment.timeline_end - segment.timeline_start
                )
            timeline_position = segment.timeline_start + ratio * (
                segment.timeline_end - segment.timeline_start
            )
            first_color, second_color = _split_segment_color_indices(segment)
            preserve_timeline = self.mixed_source or self.has_explicit_timeline
            timeline_start = segment.timeline_start
            first = Segment.create(
                segment.start_seconds,
                (
                    position
                    if coordinate == "source"
                    else segment.start_seconds + ratio * segment.duration_seconds
                ),
                deleted=segment.deleted,
                source_id=segment.source_id,
                timeline_start_seconds=(timeline_start if preserve_timeline else None),
                timeline_end_seconds=(timeline_position if preserve_timeline else None),
                state=segment.state,
                color_index=first_color,
                visual_transform=segment.visual_transform,
                triplicate=(None if segment.triplicate is None else segment.triplicate.clone()),
                track_id=segment.track_id,
            )
            second = Segment.create(
                first.end_seconds,
                segment.end_seconds,
                deleted=segment.deleted,
                source_id=segment.source_id,
                timeline_start_seconds=(timeline_position if preserve_timeline else None),
                timeline_end_seconds=(segment.timeline_end if preserve_timeline else None),
                state=segment.state,
                color_index=second_color,
                visual_transform=segment.visual_transform,
                triplicate=(None if segment.triplicate is None else segment.triplicate.clone()),
                track_id=segment.track_id,
            )
            candidate = (
                self.segment_items[:index] + (first, second) + self.segment_items[index + 1 :]
            )
            self._replace_segments(candidate)
            return first, second
        raise ProjectValidationError(f"Unknown segment_id: {segment_id}")

    def _split_absolute_block(
        self,
        segment_id: str,
        position_ticks: int,
        *,
        coordinate: str,
    ) -> tuple[Segment, Segment]:
        if self.tracks is None:
            raise ProjectValidationError("Synchronized tracks are required for absolute splitting")
        self.validate()
        for track in self.tracks:
            for index, segment in enumerate(track.blocks):
                if segment.segment_id != segment_id:
                    continue
                if coordinate == "source":
                    if not segment.source_start_ticks < position_ticks < segment.source_end_ticks:
                        raise ProjectValidationError(
                            "Split position must be strictly inside the selected block"
                        )
                    source_split = position_ticks
                    timeline_split = segment.timeline_start_ticks + (
                        position_ticks - segment.source_start_ticks
                    )
                else:
                    if (
                        not segment.timeline_start_ticks
                        < position_ticks
                        < segment.timeline_end_ticks
                    ):
                        raise ProjectValidationError(
                            "Split position must be strictly inside the selected block"
                        )
                    timeline_split = position_ticks
                    source_split = segment.source_start_ticks + (
                        position_ticks - segment.timeline_start_ticks
                    )
                first_triplicate = (
                    None if segment.triplicate is None else segment.triplicate.clone()
                )
                second_triplicate = (
                    None if segment.triplicate is None else segment.triplicate.clone()
                )
                first = _segment_with_ticks(
                    segment,
                    timeline_start_ticks=segment.timeline_start_ticks,
                    timeline_end_ticks=timeline_split,
                    track_id=track.track_id,
                    new_id=True,
                    source_start_ticks=segment.source_start_ticks,
                    source_end_ticks=source_split,
                    triplicate=first_triplicate,
                )
                second = _segment_with_ticks(
                    segment,
                    timeline_start_ticks=timeline_split,
                    timeline_end_ticks=segment.timeline_end_ticks,
                    track_id=track.track_id,
                    new_id=True,
                    source_start_ticks=source_split,
                    source_end_ticks=segment.source_end_ticks,
                    triplicate=second_triplicate,
                )
                first = _segment_with_ticks(
                    first,
                    timeline_start_ticks=first.timeline_start_ticks,
                    timeline_end_ticks=first.timeline_end_ticks,
                    track_id=track.track_id,
                    color_index=segment.color_slot + 1,
                )
                second = _segment_with_ticks(
                    second,
                    timeline_start_ticks=second.timeline_start_ticks,
                    timeline_end_ticks=second.timeline_end_ticks,
                    track_id=track.track_id,
                    color_index=segment.color_slot + 2,
                )
                blocks = list(track.blocks)
                blocks[index : index + 1] = [first, second]
                candidate_tracks = tuple(
                    TimelineTrack(
                        candidate.track_id,
                        (
                            _sorted_blocks(blocks)
                            if candidate.track_id == track.track_id
                            else candidate.blocks
                        ),
                    )
                    for candidate in self.tracks
                )
                self._replace_tracks(
                    candidate_tracks,
                    active_track_id=self.active_track_id,
                )
                return first, second
        raise ProjectValidationError(f"Unknown segment_id: {segment_id}")

    def set_deleted(self, segment_id: str, deleted: bool) -> None:
        if not isinstance(segment_id, str) or not segment_id:
            raise ProjectValidationError("Segment segment_id must be a non-empty string")
        if not isinstance(deleted, bool):
            raise ProjectValidationError("Segment deleted must be a boolean")
        self.validate()
        segments = self.segment_items
        for index, segment in enumerate(segments):
            if segment.segment_id == segment_id:
                if segment.deleted == deleted:
                    return
                replacement = Segment(
                    segment_id=segment.segment_id,
                    start_seconds=segment.start_seconds,
                    end_seconds=segment.end_seconds,
                    deleted=deleted,
                    source_id=segment.source_id,
                    timeline_start_seconds=segment.timeline_start_seconds,
                    timeline_end_seconds=segment.timeline_end_seconds,
                    state=segment.state,
                    block_id=segment.block_id,
                    color_index=segment.color_index,
                    visual_transform=segment.visual_transform,
                    triplicate=segment.triplicate,
                    track_id=segment.track_id,
                )
                candidate = list(segments)
                candidate[index] = replacement
                self._replace_segments(tuple(candidate))
                return
        raise ProjectValidationError(f"Unknown segment_id: {segment_id}")

    def delete_segment(self, segment_id: str) -> None:
        self.set_deleted(segment_id, True)

    def restore_segment(self, segment_id: str) -> None:
        self.set_deleted(segment_id, False)

    def remove_blocks(
        self,
        segment_ids: Sequence[str],
        *,
        selection_ids: Sequence[str] | None = None,
        focused_segment_id: str | None = None,
    ) -> RemovalReceipt:
        """Remove occupied blocks and ripple only their original tracks."""
        if self.tracks is None:
            raise ProjectValidationError(
                "Track-local removal requires a canonical synchronized timeline"
            )
        self.validate()
        requested_ids = tuple(segment_ids)
        if not requested_ids:
            raise ProjectValidationError("At least one segment_id is required")
        if len(set(requested_ids)) != len(requested_ids):
            raise ProjectValidationError("Segment identifiers must be unique")
        known_ids = {block.segment_id for block in self.segment_items}
        unknown = next(
            (segment_id for segment_id in requested_ids if segment_id not in known_ids), None
        )
        if unknown is not None:
            raise ProjectValidationError(f"Unknown segment_id: {unknown}")
        restored_selection = requested_ids if selection_ids is None else tuple(selection_ids)
        if not restored_selection:
            raise ProjectValidationError("Selection identifiers must not be empty")
        if len(set(restored_selection)) != len(restored_selection):
            raise ProjectValidationError("Selection identifiers must be unique")
        unknown_selection = next(
            (segment_id for segment_id in restored_selection if segment_id not in known_ids),
            None,
        )
        if unknown_selection is not None:
            raise ProjectValidationError(f"Unknown selection segment_id: {unknown_selection}")
        if focused_segment_id is not None and focused_segment_id not in restored_selection:
            raise ProjectValidationError(
                "Focused segment must be included in the supplied selection"
            )

        selected = set(requested_ids)
        before_revision = self.revision
        before_state = self._capture_removal_state()
        candidate_tracks: list[TimelineTrack] = []
        for track in self.tracks:
            removed = tuple(block for block in track.blocks if block.segment_id in selected)
            if not removed:
                candidate_tracks.append(track)
                continue
            remaining: list[Segment] = []
            for block in track.blocks:
                if block.segment_id in selected:
                    continue
                shift = sum(
                    removed_block.timeline_end_ticks - removed_block.timeline_start_ticks
                    for removed_block in removed
                    if removed_block.timeline_end_ticks <= block.timeline_start_ticks
                )
                if shift == 0:
                    remaining.append(block)
                    continue
                remaining.append(
                    _segment_with_ticks(
                        block,
                        timeline_start_ticks=block.timeline_start_ticks - shift,
                        timeline_end_ticks=block.timeline_end_ticks - shift,
                        track_id=track.track_id,
                    )
                )
            candidate_tracks.append(TimelineTrack(track.track_id, tuple(remaining)))

        self._replace_tracks(
            tuple(candidate_tracks),
            active_track_id=self.active_track_id,
            preserve_removal_history=True,
        )
        after_revision = self.revision
        after_state = self._capture_removal_state()
        project_identity, project_epoch = self._project_runtime_context()
        receipt = RemovalReceipt(
            receipt_id=uuid.uuid4().hex,
            timeline_runtime_identity=self.runtime_identity,
            timeline_runtime_epoch=self.runtime_epoch,
            project_runtime_identity=project_identity,
            project_runtime_epoch=project_epoch,
            before_revision=before_revision,
            after_revision=after_revision,
            removed_segment_ids=requested_ids,
            selection_ids=restored_selection,
            focused_segment_id=focused_segment_id,
            before_state=before_state,
            after_state=after_state,
            known_after_revisions=(after_revision,),
        )
        self._removal_history.append(receipt)
        return receipt

    def undo_remove(self, receipt: RemovalReceipt) -> RemovalUndoResult:
        if not isinstance(receipt, RemovalReceipt):
            raise ProjectValidationError("Removal receipt is invalid")
        stored = self._validated_removal_receipt(receipt)
        before_state = stored.before_state
        if before_state.tracks is None:
            raise ProjectValidationError("Removal receipt does not contain synchronized tracks")
        self._replace_tracks(
            deepcopy(before_state.tracks),
            active_track_id=before_state.active_track_id,
            preserve_removal_history=True,
        )
        restored_revision = self.revision
        self._removal_history.remove(stored.receipt_id)
        for older in self._removal_history.values():
            if older.after_state == before_state:
                self._removal_history.replace(
                    RemovalHistory.with_known_revision(older, restored_revision)
                )
        return RemovalUndoResult(
            receipt_id=stored.receipt_id,
            restored_selection_ids=stored.selection_ids,
            focused_segment_id=stored.focused_segment_id,
        )

    def _validated_segment_ids(self, segment_ids: Sequence[str]) -> set[str]:
        requested = tuple(segment_ids)
        if not requested:
            raise ProjectValidationError("At least one segment_id is required")
        selected = set(requested)
        if len(selected) != len(requested):
            raise ProjectValidationError("Segment identifiers must be unique")
        known = {segment.segment_id for segment in self.segment_items}
        missing = next((segment_id for segment_id in selected if segment_id not in known), None)
        if missing is not None:
            raise ProjectValidationError(f"Unknown segment_id: {missing}")
        return selected

    def set_visual_transform(
        self,
        segment_ids: Sequence[str],
        visual_transform: VisualTransform,
    ) -> None:
        self.validate()
        selected = self._validated_segment_ids(segment_ids)
        if not isinstance(visual_transform, VisualTransform):
            raise ProjectValidationError("Segment visual transform is invalid")
        replacements = tuple(
            segment.with_visual_transform(visual_transform)
            if segment.segment_id in selected
            else segment
            for segment in self.segment_items
        )
        self._replace_segments(replacements)

    def clean_visual_modifications(self, segment_ids: Sequence[str]) -> None:
        self.validate()
        selected = self._validated_segment_ids(segment_ids)
        replacements = tuple(
            segment.with_visual_transform(VisualTransform()).with_triplicate(None)
            if segment.segment_id in selected
            else segment
            for segment in self.segment_items
        )
        self._replace_segments(replacements)

    def enable_triplicate(self, segment_ids: Sequence[str]) -> None:
        self.validate()
        selected = self._validated_segment_ids(segment_ids)
        replacements = tuple(
            segment.with_triplicate(
                (
                    TriplicateGroup.create(segment.visual_transform)
                    if segment.triplicate is None
                    else segment.triplicate.with_enabled(True)
                )
            )
            if segment.segment_id in selected
            else segment
            for segment in self.segment_items
        )
        self._replace_segments(replacements)

    def disable_triplicate(self, segment_ids: Sequence[str]) -> None:
        self.validate()
        selected = self._validated_segment_ids(segment_ids)
        replacements = tuple(
            segment.with_triplicate(None) if segment.segment_id in selected else segment
            for segment in self.segment_items
        )
        self._replace_segments(replacements)

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        if self.tracks is not None:
            return {
                "timebase": self.timebase,
                "frame_rate": self.frame_rate,
                "ripple": self.ripple,
                "timing_mode": self.timing_mode,
                "timeline_model_version": self.timeline_model_version,
                "active_track_id": self.active_track_id,
                "source_durations_ticks": dict(self.source_durations_ticks or {}),
                "tracks": [
                    {
                        "track_id": track.track_id,
                        "blocks": [
                            block.to_dict(canonical_ticks=True, track_id=track.track_id)
                            for block in track.blocks
                        ],
                    }
                    for track in self.tracks
                ],
            }
        if self.mixed_source:
            return {
                "duration_seconds": self.source_duration_seconds,
                "edited_duration_seconds": self.edited_duration_seconds,
                "timebase": self.timebase,
                "frame_rate": self.frame_rate,
                "ripple": self.ripple,
                "source_durations": (
                    None if self.source_durations is None else dict(self.source_durations)
                ),
                "blocks": [segment.to_dict() for segment in self.segment_items],
            }
        return {
            "source_duration_seconds": self.source_duration_seconds,
            "segments": [segment.to_dict() for segment in self.segment_items],
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> SegmentTimeline:
        if not isinstance(value, Mapping):
            raise ProjectValidationError("Segment timeline must be an object")
        if "tracks" in value:
            timeline_model_version = value.get("timeline_model_version")
            if (
                not isinstance(timeline_model_version, int)
                or isinstance(timeline_model_version, bool)
                or timeline_model_version != TIMELINE_MODEL_VERSION
            ):
                raise ProjectValidationError("Project timeline timeline_model_version must be 1")
            timing_mode = value.get("timing_mode")
            if not isinstance(timing_mode, str) or timing_mode not in {
                LEGACY_TIMING_MODE,
                ABSOLUTE_TIMING_MODE,
            }:
                raise ProjectValidationError(
                    "Project timeline timing_mode must be legacy-ripple or absolute"
                )
            if value.get("timebase") != f"1/{PROJECT_TIMEBASE}":
                raise ProjectValidationError("Project timeline timebase must be 1/1000000")
            ripple = value.get("ripple")
            if not isinstance(ripple, bool):
                raise ProjectValidationError("Project timeline ripple must be a boolean")
            active_track_id = value.get("active_track_id")
            if not isinstance(active_track_id, str) or not active_track_id:
                raise ProjectValidationError(
                    "Project timeline active_track_id must be a non-empty string"
                )
            raw_tracks = value.get("tracks")
            if not isinstance(raw_tracks, list):
                raise ProjectValidationError("Project timeline tracks must be an array")
            if not 1 <= len(raw_tracks) <= MAX_TRACK_COUNT:
                raise ProjectValidationError(
                    f"Project timeline must contain between one and {MAX_TRACK_COUNT} tracks"
                )
            raw_durations = value.get("source_durations_ticks")
            if not isinstance(raw_durations, Mapping) or not raw_durations:
                raise ProjectValidationError(
                    "Project timeline source_durations_ticks must be an object"
                )
            source_durations: dict[str, float] = {}
            for source_id, ticks in raw_durations.items():
                if not isinstance(source_id, str) or not source_id:
                    raise ProjectValidationError(
                        "Project timeline source duration identifiers must be non-empty strings"
                    )
                if not isinstance(ticks, int) or isinstance(ticks, bool) or ticks <= 0:
                    raise ProjectValidationError(
                        f"Project timeline source duration for {source_id} must be a positive integer"
                    )
                source_durations[source_id] = ticks_to_seconds(ticks)
            tracks: list[TimelineTrack] = []
            seen_track_ids: set[str] = set()
            for raw_track in raw_tracks:
                if not isinstance(raw_track, Mapping):
                    raise ProjectValidationError("Project timeline track must be an object")
                track_id = raw_track.get("track_id")
                raw_blocks = raw_track.get("blocks")
                if not isinstance(track_id, str) or not track_id:
                    raise ProjectValidationError(
                        "Project timeline track_id must be a non-empty string"
                    )
                if track_id in seen_track_ids:
                    raise ProjectValidationError(f"Duplicate track_id: {track_id}")
                seen_track_ids.add(track_id)
                if not isinstance(raw_blocks, list):
                    raise ProjectValidationError(
                        f"Project timeline blocks must be an array for {track_id}"
                    )
                track_blocks = tuple(
                    Segment.from_canonical_dict(item, expected_track_id=track_id)
                    for item in raw_blocks
                )
                tracks.append(TimelineTrack(track_id, track_blocks))
            return cls.from_tracks(
                tracks,
                source_durations=source_durations,
                source_durations_ticks=dict(raw_durations),
                active_track_id=active_track_id,
                timebase=value["timebase"],
                frame_rate=value.get("frame_rate"),
                ripple=ripple,
                timing_mode=timing_mode,
            )
        if "blocks" in value:
            raw_blocks = value.get("blocks")
            if not isinstance(raw_blocks, list):
                raise ProjectValidationError("Project timeline blocks must be an array")
            blocks: list[Segment] = []
            for item in raw_blocks:
                if not isinstance(item, Mapping):
                    raise ProjectValidationError("Project timeline block must be an object")
                blocks.append(Segment.from_dict(item))
            duration = value.get("duration_seconds")
            if not isinstance(duration, (int, float)) or isinstance(duration, bool):
                raise ProjectValidationError("Project timeline duration must be a number")
            edited = value.get("edited_duration_seconds")
            timeline = cls.from_blocks(
                blocks,
                duration_seconds=float(duration),
                source_durations=value.get("source_durations"),
                timebase=value.get("timebase", "1/1000000"),
                frame_rate=value.get("frame_rate"),
                ripple=value.get("ripple", True),
            )
            if edited is None or not math.isclose(
                _finite_float(edited, "Timeline edited duration"),
                timeline.edited_duration_seconds,
                rel_tol=0.0,
                abs_tol=_TIME_EPSILON,
            ):
                raise ProjectValidationError("Timeline edited duration does not match its blocks")
            return timeline
        raw_segments = value.get("segments")
        if not isinstance(raw_segments, list):
            raise ProjectValidationError("Segment timeline segments must be an array")
        source_duration_seconds = value.get("source_duration_seconds")
        if not isinstance(source_duration_seconds, (int, float)) or isinstance(
            source_duration_seconds, bool
        ):
            raise ProjectValidationError("Segment timeline duration must be a number")
        segments: list[Segment] = []
        for item in raw_segments:
            if not isinstance(item, Mapping):
                raise ProjectValidationError("Project segment must be an object")
            segments.append(Segment.from_dict(item))
        return cls(float(source_duration_seconds), tuple(segments))

    def find(self, segment_id: str) -> Segment:
        for segment in self.segment_items:
            if segment.segment_id == segment_id:
                return segment
        raise ProjectValidationError(f"Unknown segment_id: {segment_id}")

    def active_blocks(self) -> tuple[Segment, ...]:
        return tuple(segment for segment in self.segment_items if not segment.deleted)

    def move_block(
        self,
        segment_id: str,
        direction: str | int | None = None,
        *,
        target_track_id: str | None = None,
        timeline_start_ticks: int | None = None,
    ) -> bool:
        if direction is not None and timeline_start_ticks is not None:
            raise ProjectValidationError("Choose a move direction or an absolute timeline start")
        if timeline_start_ticks is not None:
            direction = timeline_start_ticks
        if direction is None:
            raise ProjectValidationError("A move direction or timeline start is required")
        if self.tracks is not None and self.timing_mode == ABSOLUTE_TIMING_MODE:
            return self._move_absolute_block(
                segment_id,
                direction,
                target_track_id=target_track_id,
            )
        if direction in ("left", -1):
            step = -1
        elif direction in ("right", 1):
            step = 1
        else:
            raise ProjectValidationError("Move direction must be left or right")
        index = next(
            (
                index
                for index, segment in enumerate(self.segment_items)
                if segment.segment_id == segment_id
            ),
            None,
        )
        if index is None:
            raise ProjectValidationError(f"Unknown segment_id: {segment_id}")
        target = index + step
        if target < 0 or target >= len(self.segment_items):
            return False
        candidate = list(self.segment_items)
        candidate[index], candidate[target] = candidate[target], candidate[index]
        self._replace_segments(tuple(self._reflow(candidate)))
        return True

    def move_blocks(self, segment_ids: Sequence[str], direction: str | int) -> bool:
        if self.tracks is not None and self.timing_mode == ABSOLUTE_TIMING_MODE:
            raise ProjectValidationError(
                "Synchronized block movement is not available before track editing support"
            )
        selected = set(segment_ids)
        if not selected:
            raise ProjectValidationError("At least one segment_id is required")
        if len(selected) != len(tuple(segment_ids)):
            raise ProjectValidationError("Segment identifiers must be unique")
        indices = [
            index
            for index, segment in enumerate(self.segment_items)
            if segment.segment_id in selected
        ]
        if len(indices) != len(selected):
            missing = next(
                segment_id
                for segment_id in selected
                if segment_id not in {item.segment_id for item in self.segment_items}
            )
            raise ProjectValidationError(f"Unknown segment_id: {missing}")
        if direction in ("left", -1):
            step = -1
        elif direction in ("right", 1):
            step = 1
        else:
            raise ProjectValidationError("Move direction must be left or right")
        candidate = list(self.segment_items)
        changed = False
        if step < 0:
            index = 0
            while index < len(candidate):
                if candidate[index].segment_id not in selected:
                    index += 1
                    continue
                run_start = index
                while index < len(candidate) and candidate[index].segment_id in selected:
                    index += 1
                if run_start > 0 and candidate[run_start - 1].segment_id not in selected:
                    selected_run = candidate[run_start:index]
                    candidate[run_start - 1 : index] = [
                        *selected_run,
                        candidate[run_start - 1],
                    ]
                    changed = True
                    index = run_start + len(selected_run)
        else:
            reordered: list[Segment] = []
            index = 0
            while index < len(candidate):
                if candidate[index].segment_id not in selected:
                    reordered.append(candidate[index])
                    index += 1
                    continue
                run_start = index
                while index < len(candidate) and candidate[index].segment_id in selected:
                    index += 1
                selected_run = candidate[run_start:index]
                if index < len(candidate) and candidate[index].segment_id not in selected:
                    reordered.append(candidate[index])
                    reordered.extend(selected_run)
                    index += 1
                else:
                    reordered.extend(selected_run)
            changed = [item.segment_id for item in reordered] != [
                item.segment_id for item in candidate
            ]
            candidate = reordered
        if changed:
            self._replace_segments(tuple(self._reflow(candidate)))
        return changed

    def _move_absolute_block(
        self,
        segment_id: str,
        timeline_start_ticks: object,
        *,
        target_track_id: str | None,
    ) -> bool:
        if self.tracks is None:
            raise ProjectValidationError("Absolute block movement requires synchronized tracks")
        requested_start = _required_tick(timeline_start_ticks, "Timeline start ticks")
        source_track: TimelineTrack | None = None
        selected: Segment | None = None
        for track in self.tracks:
            for block in track.blocks:
                if block.segment_id == segment_id:
                    source_track = track
                    selected = block
                    break
            if selected is not None:
                break
        if selected is None or source_track is None:
            raise ProjectValidationError(f"Unknown segment_id: {segment_id}")
        destination_id = source_track.track_id if target_track_id is None else target_track_id
        destination = self.track_by_id(destination_id)
        duration_ticks = selected.source_end_ticks - selected.source_start_ticks
        occupied = tuple(
            block for block in destination.blocks if block.segment_id != selected.segment_id
        )
        fitted_start = _earliest_fit(requested_start, duration_ticks, occupied)
        fitted_end = fitted_start + duration_ticks
        if (
            destination_id == source_track.track_id
            and fitted_start == selected.timeline_start_ticks
            and fitted_end == selected.timeline_end_ticks
        ):
            return False
        moved = _segment_with_ticks(
            selected,
            timeline_start_ticks=fitted_start,
            timeline_end_ticks=fitted_end,
            track_id=destination_id,
        )
        candidate_tracks: list[TimelineTrack] = []
        for track in self.tracks:
            blocks = [block for block in track.blocks if block.segment_id != segment_id]
            if track.track_id == destination_id:
                blocks.append(moved)
            candidate_tracks.append(TimelineTrack(track.track_id, _sorted_blocks(blocks)))
        return self._replace_tracks(
            tuple(candidate_tracks),
            active_track_id=self.active_track_id,
        )

    def plan_block_move(
        self,
        segment_ids: Sequence[str],
        *,
        anchor_segment_id: str,
        timeline_start_ticks: int,
        target_track_id: str,
    ) -> tuple[tuple[str, int, str], ...]:
        if self.tracks is None or self.timing_mode != ABSOLUTE_TIMING_MODE:
            raise ProjectValidationError("Track movement requires synchronized tracks")
        requested_start = _required_tick(timeline_start_ticks, "Timeline start ticks")
        selected_ids = set(segment_ids)
        if not selected_ids or len(selected_ids) != len(segment_ids):
            raise ProjectValidationError("Move requires unique segment identifiers")
        if anchor_segment_id not in selected_ids:
            raise ProjectValidationError("The dragged clip must belong to the selected group")
        blocks_by_id = {block.segment_id: block for block in self.segment_items}
        for segment_id in segment_ids:
            if segment_id not in blocks_by_id:
                raise ProjectValidationError(f"Unknown segment_id: {segment_id}")
        selected = tuple(blocks_by_id[segment_id] for segment_id in segment_ids)
        anchor = blocks_by_id[anchor_segment_id]
        self.track_by_id(target_track_id)
        if anchor.track_id is None:
            raise ProjectValidationError("The dragged clip must belong to a track")
        track_delta = self.track_ids.index(target_track_id) - self.track_ids.index(anchor.track_id)
        targets: list[tuple[Segment, str]] = []
        for block in selected:
            if block.track_id is None:
                raise ProjectValidationError("Selected clips must belong to tracks")
            index = self.track_ids.index(block.track_id) + track_delta
            if not 0 <= index < len(self.tracks):
                raise ProjectValidationError("Selected group would move outside available tracks")
            targets.append((block, self.track_ids[index]))
        occupied = {
            track.track_id: tuple(
                block for block in track.blocks if block.segment_id not in selected_ids
            )
            for track in self.tracks
        }
        delta = max(
            requested_start - anchor.timeline_start_ticks,
            -min(block.timeline_start_ticks for block in selected),
        )
        while True:
            previous_delta = delta
            for block, destination_id in targets:
                start = block.timeline_start_ticks + delta
                fitted = _earliest_fit(
                    start,
                    block.timeline_end_ticks - block.timeline_start_ticks,
                    occupied[destination_id],
                )
                delta += fitted - start
            if delta == previous_delta:
                break
        return tuple(
            (block.segment_id, block.timeline_start_ticks + delta, destination_id)
            for block, destination_id in targets
        )

    def move_blocks_to_track(
        self,
        segment_ids: Sequence[str],
        *,
        anchor_segment_id: str,
        timeline_start_ticks: int,
        target_track_id: str,
    ) -> bool:
        placements = self.plan_block_move(
            segment_ids,
            anchor_segment_id=anchor_segment_id,
            timeline_start_ticks=timeline_start_ticks,
            target_track_id=target_track_id,
        )
        moved: dict[str, Segment] = {}
        blocks_by_id = {block.segment_id: block for block in self.segment_items}
        for segment_id, start, track_id in placements:
            original = blocks_by_id[segment_id]
            moved[segment_id] = _segment_with_ticks(
                original,
                timeline_start_ticks=start,
                timeline_end_ticks=start
                + original.timeline_end_ticks
                - original.timeline_start_ticks,
                track_id=track_id,
            )
        if self.tracks is None:
            raise ProjectValidationError("Track movement requires synchronized tracks")
        candidate = tuple(
            TimelineTrack(
                track.track_id,
                _sorted_blocks(
                    tuple(block for block in track.blocks if block.segment_id not in moved)
                    + tuple(block for block in moved.values() if block.track_id == track.track_id)
                ),
            )
            for track in self.tracks
        )
        return self._replace_tracks(candidate, active_track_id=self.active_track_id)

    def copy_blocks(self, segment_ids: Sequence[str]) -> tuple[Segment, ...]:
        self.validate()
        requested = set(segment_ids)
        if not requested:
            raise ProjectValidationError("At least one segment_id is required")
        selected = tuple(
            segment for segment in self.segment_items if segment.segment_id in requested
        )
        if len(selected) != len(requested):
            missing = next(
                segment_id
                for segment_id in requested
                if segment_id not in {item.segment_id for item in selected}
            )
            raise ProjectValidationError(f"Unknown segment_id: {missing}")
        if self.tracks is not None and self.timing_mode == ABSOLUTE_TIMING_MODE:
            selected_track_ids = {segment.track_id for segment in selected}
            if len(selected_track_ids) != 1:
                raise ProjectValidationError(
                    "Synchronized clipboard blocks must come from one track"
                )
        return tuple(segment.clone() for segment in selected)

    def paste_blocks(
        self,
        blocks: Sequence[Segment],
        *,
        at_index: int | None = None,
        at_seconds: float | None = None,
        at_ticks: int | None = None,
        target_track_id: str | None = None,
    ) -> tuple[Segment, ...]:
        if self.tracks is not None and self.timing_mode == ABSOLUTE_TIMING_MODE:
            return self._paste_absolute_blocks(
                blocks,
                at_index=at_index,
                at_seconds=at_seconds,
                at_ticks=at_ticks,
                target_track_id=target_track_id,
            )
        self.validate()
        copies = tuple(blocks)
        if not copies:
            raise ProjectValidationError("At least one block is required to paste")
        for block in copies:
            if not isinstance(block, Segment):
                raise ProjectValidationError("Pasted blocks must be segments")
            if self.mixed_source and block.source_id is None:
                raise ProjectValidationError("Pasted blocks must reference a source")
        if at_index is not None and at_seconds is not None:
            raise ProjectValidationError("Choose an insertion index or timeline position")
        if at_seconds is not None:
            position = _finite_float(at_seconds, "Paste position")
            if position < 0 or position > self.timeline_duration_seconds:
                raise ProjectValidationError("Paste position is outside the timeline")
            insertion = len(self.segment_items)
            for index, block in enumerate(self.segment_items):
                if position <= block.timeline_start + _TIME_EPSILON:
                    insertion = index
                    break
                if block.timeline_start < position < block.timeline_end:
                    insertion = index
                    break
        elif at_index is None:
            insertion = len(self.segment_items)
        else:
            if not isinstance(at_index, int) or isinstance(at_index, bool):
                raise ProjectValidationError("Paste index must be an integer")
            if at_index < 0 or at_index > len(self.segment_items):
                raise ProjectValidationError("Paste index is outside the timeline")
            insertion = at_index
        pasted = tuple(block.clone() for block in copies)
        candidate = self.segment_items[:insertion] + pasted + self.segment_items[insertion:]
        reflowed = tuple(self._reflow(candidate))
        self._replace_segments(reflowed)
        return reflowed[insertion : insertion + len(pasted)]

    def _paste_absolute_blocks(
        self,
        blocks: Sequence[Segment],
        *,
        at_index: int | None,
        at_seconds: float | None,
        at_ticks: int | None,
        target_track_id: str | None,
    ) -> tuple[Segment, ...]:
        if self.tracks is None:
            raise ProjectValidationError("Synchronized tracks are required for absolute pasting")
        if at_index is not None:
            raise ProjectValidationError("Absolute pasting uses a timeline position, not an index")
        if sum(value is not None for value in (at_seconds, at_ticks)) > 1:
            raise ProjectValidationError("Choose paste position seconds or ticks")
        self.validate()
        copies = tuple(blocks)
        if not copies:
            raise ProjectValidationError("At least one block is required to paste")
        if any(not isinstance(block, Segment) for block in copies):
            raise ProjectValidationError("Pasted blocks must be segments")
        source_track_ids = {block.track_id for block in copies}
        if len(source_track_ids) != 1 or None in source_track_ids:
            raise ProjectValidationError("Synchronized clipboard blocks must come from one track")
        copy_ids = [block.segment_id for block in copies]
        if len(set(copy_ids)) != len(copy_ids):
            raise ProjectValidationError("Pasted block identifiers must be unique")
        destination_id = target_track_id or self.active_track_id
        if destination_id is None:
            raise ProjectValidationError("An active target track is required for pasting")
        destination = self.track_by_id(destination_id)
        if at_ticks is not None:
            requested_start = _required_tick(at_ticks, "Paste position ticks")
        elif at_seconds is not None:
            requested_start = seconds_to_ticks(
                _finite_float(at_seconds, "Paste position"),
            )
        else:
            requested_start = max(
                (block.timeline_end_ticks for block in destination.blocks),
                default=0,
            )
        minimum_start = min(block.timeline_start_ticks for block in copies)
        offsets = tuple(block.timeline_start_ticks - minimum_start for block in copies)
        durations = tuple(block.source_end_ticks - block.source_start_ticks for block in copies)
        occupied = destination.blocks
        placement_start = requested_start
        while True:
            collision_shift = 0
            for offset, duration in zip(offsets, durations, strict=True):
                candidate_start = placement_start + offset
                candidate_end = candidate_start + duration
                for occupied_block in occupied:
                    if (
                        candidate_start < occupied_block.timeline_end_ticks
                        and candidate_end > occupied_block.timeline_start_ticks
                    ):
                        collision_shift = max(
                            collision_shift,
                            occupied_block.timeline_end_ticks - candidate_start,
                        )
            if collision_shift == 0:
                break
            placement_start += collision_shift
        pasted: list[Segment] = []
        for block, offset, duration in zip(copies, offsets, durations, strict=True):
            start = placement_start + offset
            pasted.append(
                _segment_with_ticks(
                    block,
                    timeline_start_ticks=start,
                    timeline_end_ticks=start + duration,
                    track_id=destination_id,
                    new_id=True,
                    triplicate=(None if block.triplicate is None else block.triplicate.clone()),
                )
            )
        candidate_tracks = tuple(
            TimelineTrack(
                track.track_id,
                _sorted_blocks(
                    (
                        track.blocks + tuple(pasted)
                        if track.track_id == destination_id
                        else track.blocks
                    )
                ),
            )
            for track in self.tracks
        )
        self._replace_tracks(candidate_tracks, active_track_id=self.active_track_id)
        return tuple(pasted)

    def _reflow(self, segments: Sequence[Segment]) -> list[Segment]:
        position = 0.0
        position_ticks = 0
        result: list[Segment] = []
        for segment in segments:
            if self.tracks is not None:
                start = ticks_to_seconds(position_ticks)
                end_ticks = position_ticks + (segment.source_end_ticks - segment.source_start_ticks)
                end = ticks_to_seconds(end_ticks)
            else:
                start = position
                end = position + segment.duration_seconds
            result.append(
                Segment(
                    segment_id=segment.segment_id,
                    start_seconds=segment.start_seconds,
                    end_seconds=segment.end_seconds,
                    deleted=segment.deleted,
                    source_id=segment.source_id,
                    timeline_start_seconds=start,
                    timeline_end_seconds=end,
                    state=segment.state,
                    block_id=segment.block_id,
                    color_index=segment.color_index,
                    visual_transform=segment.visual_transform,
                    triplicate=segment.triplicate,
                    track_id=segment.track_id,
                )
            )
            position = end
            position_ticks = end_ticks if self.tracks is not None else seconds_to_ticks(end)
        if self.mixed_source and self.tracks is None:
            self.source_duration_seconds = position
        return result

    def _notify_project_owner(self) -> None:
        owner = self._project_owner
        if owner is not None:
            owner._sync_timeline_state()

    def _project_runtime_context(self) -> tuple[str | None, int | None]:
        owner = self._project_owner
        if owner is None:
            return None, None
        return owner.runtime_identity, owner.runtime_epoch

    def _capture_removal_state(self) -> TimelineStateSnapshot:
        return TimelineStateSnapshot(
            tracks=self.tracks,
            segments=self.segments,
            active_track_id=self.active_track_id,
            source_duration_seconds=self.source_duration_seconds,
            mixed_source=self.mixed_source,
            source_durations=(
                None if self.source_durations is None else dict(self.source_durations)
            ),
            source_durations_ticks=(
                None if self.source_durations_ticks is None else dict(self.source_durations_ticks)
            ),
            timebase=self.timebase,
            frame_rate=self.frame_rate,
            ripple=self.ripple,
            timing_mode=self.timing_mode,
            timeline_model_version=self.timeline_model_version,
        )

    def _invalidate_removal_history(self) -> None:
        self._removal_history.clear()
        self._runtime_epoch += 1

    def _validated_removal_receipt(self, receipt: RemovalReceipt) -> RemovalReceipt:
        stored = self._removal_history.find(receipt)
        if stored is None:
            raise ProjectValidationError("Removal receipt is stale or no longer available")
        project_identity, project_epoch = self._project_runtime_context()
        if (
            stored.timeline_runtime_identity != self.runtime_identity
            or stored.timeline_runtime_epoch != self.runtime_epoch
            or stored.project_runtime_identity != project_identity
            or stored.project_runtime_epoch != project_epoch
        ):
            raise ProjectValidationError("Removal receipt is stale for this project runtime")
        if self.revision not in stored.known_after_revisions:
            raise ProjectValidationError(
                "Removal receipt is stale for the current mutation revision"
            )
        if self._capture_removal_state() != stored.after_state:
            raise ProjectValidationError("Removal receipt is stale for the current timeline state")
        return stored

    def _replace_segments(
        self,
        segments: tuple[Segment, ...],
        *,
        preserve_removal_history: bool = False,
    ) -> bool:
        candidate_tracks: tuple[TimelineTrack, ...]
        if self.tracks is not None:
            if self.timing_mode == LEGACY_TIMING_MODE:
                track = self.tracks[0]
                candidate_tracks = (
                    TimelineTrack(
                        track.track_id,
                        tuple(
                            _segment_with_ticks(
                                segment,
                                timeline_start_ticks=segment.timeline_start_ticks,
                                timeline_end_ticks=segment.timeline_end_ticks,
                                track_id=track.track_id,
                            )
                            for segment in segments
                        ),
                    ),
                )
                self._replace_tracks(
                    candidate_tracks,
                    active_track_id=self.active_track_id,
                    preserve_removal_history=preserve_removal_history,
                )
                return True
            by_id = {segment.segment_id: segment for segment in segments}
            normalized_tracks: list[TimelineTrack] = []
            for track in self.tracks:
                normalized_blocks: list[Segment] = []
                for block in track.blocks:
                    candidate = by_id.get(block.segment_id, block)
                    normalized_blocks.append(
                        _segment_with_ticks(
                            candidate,
                            timeline_start_ticks=candidate.timeline_start_ticks,
                            timeline_end_ticks=candidate.timeline_end_ticks,
                            track_id=track.track_id,
                        )
                    )
                normalized_tracks.append(TimelineTrack(track.track_id, tuple(normalized_blocks)))
            candidate_tracks = tuple(normalized_tracks)
            self._replace_tracks(
                candidate_tracks,
                active_track_id=self.active_track_id,
                preserve_removal_history=preserve_removal_history,
            )
            return True
        previous_segments = self.segments
        previous_duration = self.source_duration_seconds
        self.segments = segments
        try:
            self.validate()
            self.mutation_revision += 1
            if not preserve_removal_history:
                self._invalidate_removal_history()
            self._notify_project_owner()
            return True
        except ProjectValidationError:
            self.segments = previous_segments
            self.source_duration_seconds = previous_duration
            raise

    def _replace_tracks(
        self,
        tracks: tuple[TimelineTrack, ...],
        *,
        active_track_id: str | None,
        preserve_removal_history: bool = False,
    ) -> bool:
        if self.tracks == tracks and self.active_track_id == active_track_id:
            return False
        previous_tracks = self.tracks
        previous_segments = self.segments
        previous_active = self.active_track_id
        self.tracks = tracks
        self.active_track_id = active_track_id
        self.segments = tuple(block for track in tracks for block in track.blocks)
        try:
            self.validate()
            self.mutation_revision += 1
            if not preserve_removal_history:
                self._invalidate_removal_history()
            self._notify_project_owner()
            return True
        except ProjectValidationError:
            self.tracks = previous_tracks
            self.segments = previous_segments
            self.active_track_id = previous_active
            raise
