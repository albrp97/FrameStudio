from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from .model_timeline_validation import validate_timeline
from .model_types import (
    _TIME_EPSILON,
    ProjectValidationError,
    Segment,
    TriplicateGroup,
    VisualTransform,
    _assign_missing_segment_colors,
    _finite_float,
    _split_segment_color_indices,
)


@dataclass
class SegmentTimeline:
    source_duration_seconds: float
    segments: tuple[Segment, ...] | None = None
    mixed_source: bool = False
    source_durations: dict[str, float] | None = None
    timebase: str = "1/1000000"
    frame_rate: str | None = None
    ripple: bool = True

    def __post_init__(self) -> None:
        self.source_duration_seconds = _finite_float(
            self.source_duration_seconds,
            "Timeline duration" if self.mixed_source else "Source duration",
        )
        if self.source_duration_seconds <= 0:
            raise ProjectValidationError("Timeline duration must be greater than zero")
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
        if self.source_durations is not None:
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
        )

    @property
    def segment_items(self) -> tuple[Segment, ...]:
        if self.segments is None:
            raise ProjectValidationError("Segment timeline must contain segments")
        return self.segments

    @property
    def blocks(self) -> tuple[Segment, ...]:
        return self.segment_items

    @property
    def duration_seconds(self) -> float:
        return self.timeline_duration_seconds

    @property
    def timeline_duration_seconds(self) -> float:
        if not self.has_explicit_timeline:
            return self.source_duration_seconds
        return max(segment.timeline_end for segment in self.segment_items)

    @property
    def has_explicit_timeline(self) -> bool:
        return any(segment.timeline_start_seconds is not None for segment in self.segment_items)

    @property
    def edited_duration_seconds(self) -> float:
        return sum(
            segment.duration_seconds for segment in self.segment_items if not segment.deleted
        )

    def timeline_to_edited_position(self, position_seconds: float) -> float:
        """Map a visible timeline position to the concatenated playback time."""
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
        position_seconds: float,
        *,
        coordinate: str = "source",
    ) -> tuple[Segment, Segment]:
        position = _finite_float(position_seconds, "Split position")
        if coordinate not in {"source", "timeline"}:
            raise ProjectValidationError("Split coordinate must be source or timeline")
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
            )
            candidate = (
                self.segment_items[:index] + (first, second) + self.segment_items[index + 1 :]
            )
            self._replace_segments(candidate)
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

    def move_block(self, segment_id: str, direction: str | int) -> bool:
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
        return tuple(segment.clone() for segment in selected)

    def paste_blocks(
        self,
        blocks: Sequence[Segment],
        *,
        at_index: int | None = None,
        at_seconds: float | None = None,
    ) -> tuple[Segment, ...]:
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

    def _reflow(self, segments: Sequence[Segment]) -> list[Segment]:
        position = 0.0
        result: list[Segment] = []
        for segment in segments:
            end = position + segment.duration_seconds
            result.append(
                Segment(
                    segment_id=segment.segment_id,
                    start_seconds=segment.start_seconds,
                    end_seconds=segment.end_seconds,
                    deleted=segment.deleted,
                    source_id=segment.source_id,
                    timeline_start_seconds=position,
                    timeline_end_seconds=end,
                    state=segment.state,
                    block_id=segment.block_id,
                    color_index=segment.color_index,
                    visual_transform=segment.visual_transform,
                    triplicate=segment.triplicate,
                )
            )
            position = end
        if self.mixed_source:
            self.source_duration_seconds = position
        return result

    def _replace_segments(self, segments: tuple[Segment, ...]) -> None:
        previous_segments = self.segments
        previous_duration = self.source_duration_seconds
        self.segments = segments
        try:
            self.validate()
        except ProjectValidationError:
            self.segments = previous_segments
            self.source_duration_seconds = previous_duration
            raise
