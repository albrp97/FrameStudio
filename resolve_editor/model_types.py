from __future__ import annotations

import math
import uuid
from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence

from .composition import (
    TriplicateGroup,
    VisualTransform,
    coerce_legacy_transform,
)

LEGACY_SCHEMA_VERSION = 1
ONE_SOURCE_SCHEMA_VERSION = 2
SCHEMA_VERSION = 3
PROJECT_TIMEBASE = 1_000_000
_TIME_EPSILON = 1e-9
_SEGMENT_COLOR_SLOT_COUNT = 4


class ProjectValidationError(ValueError):
    """Raised when a project or source record is invalid."""


def _finite_float(value: Any, label: str) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ProjectValidationError(f"{label} must be a finite number")
    parsed = float(value)
    if not math.isfinite(parsed):
        raise ProjectValidationError(f"{label} must be a finite number")
    return parsed


def _default_segment_color_index(segment_id: str) -> int:
    return (
        sum((position + 1) * ord(character) for position, character in enumerate(segment_id))
        % _SEGMENT_COLOR_SLOT_COUNT
    )


def seconds_to_ticks(seconds: float) -> int:
    """Convert seconds to the canonical microsecond timeline timebase."""
    value = _finite_float(seconds, "Timeline seconds")
    if value < 0:
        raise ProjectValidationError("Timeline seconds must not be negative")
    return int(math.floor(value * PROJECT_TIMEBASE + 0.5))


def ticks_to_seconds(ticks: int) -> float:
    if not isinstance(ticks, int) or isinstance(ticks, bool) or ticks < 0:
        raise ProjectValidationError("Timeline ticks must be a non-negative integer")
    return ticks / PROJECT_TIMEBASE


def _source_metadata(metadata: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(metadata, Mapping):
        raise ProjectValidationError("Source metadata must be an object")
    normalized = dict(metadata)
    duration = normalized.get("duration_seconds")
    if duration is not None:
        duration = _finite_float(duration, "Source duration")
        if duration <= 0:
            raise ProjectValidationError("Source duration must be greater than zero")
        normalized["duration_seconds"] = duration
    width = normalized.get("width")
    height = normalized.get("height")
    if isinstance(width, (int, float)) and not isinstance(width, bool):
        if isinstance(height, (int, float)) and not isinstance(height, bool):
            if width <= 0 or height <= 0:
                raise ProjectValidationError("Source dimensions must be positive")
            normalized.setdefault(
                "orientation",
                "portrait" if height > width else "landscape" if width > height else "square",
            )
    if "audio_stream_present" not in normalized and "audio_codec" in normalized:
        normalized["audio_stream_present"] = normalized["audio_codec"] is not None
    return normalized


@dataclass(frozen=True)
class SourceStatus:
    available: bool
    changed: bool
    reason: str | None = None


@dataclass(frozen=True)
class SourceReference:
    source_id: str
    path: str
    uri: str
    size_bytes: int
    modified_time_ns: int
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_path(
        cls,
        path: Path,
        metadata: Mapping[str, Any],
        source_id: str | None = None,
    ) -> SourceReference:
        resolved = Path(path).expanduser().resolve()
        try:
            stat = resolved.stat()
        except OSError as error:
            raise ProjectValidationError(
                f"Cannot inspect source file {resolved.name}: {error}"
            ) from error
        if not resolved.is_file():
            raise ProjectValidationError(f"Source is not a file: {resolved.name}")
        return cls(
            source_id=source_id or uuid.uuid4().hex,
            path=str(resolved),
            uri=resolved.as_uri(),
            size_bytes=stat.st_size,
            modified_time_ns=stat.st_mtime_ns,
            metadata=_source_metadata(metadata),
        )

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> SourceReference:
        if not isinstance(value, Mapping):
            raise ProjectValidationError("Project source must be an object")
        source_id = value.get("source_id")
        path_value = value.get("path")
        uri = value.get("uri")
        size_bytes = value.get("size_bytes")
        modified_time_ns = value.get("modified_time_ns")
        metadata = value.get("metadata")
        if not isinstance(source_id, str) or not source_id:
            raise ProjectValidationError("Project source_id must be a non-empty string")
        if not isinstance(path_value, str) or not path_value:
            raise ProjectValidationError("Project source path must be a non-empty string")
        path = Path(path_value)
        if not path.is_absolute():
            raise ProjectValidationError("Project source path must be absolute")
        if not isinstance(uri, str) or not uri:
            raise ProjectValidationError("Project source URI must be a non-empty string")
        if not isinstance(size_bytes, int) or isinstance(size_bytes, bool) or size_bytes < 0:
            raise ProjectValidationError("Project source size must be a non-negative integer")
        if (
            not isinstance(modified_time_ns, int)
            or isinstance(modified_time_ns, bool)
            or modified_time_ns < 0
        ):
            raise ProjectValidationError(
                "Project source modification time must be a non-negative integer"
            )
        if not isinstance(metadata, Mapping):
            raise ProjectValidationError("Project source metadata must be an object")
        return cls(
            source_id=source_id,
            path=str(path),
            uri=uri,
            size_bytes=size_bytes,
            modified_time_ns=modified_time_ns,
            metadata=_source_metadata(metadata),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "path": self.path,
            "uri": self.uri,
            "size_bytes": self.size_bytes,
            "modified_time_ns": self.modified_time_ns,
            "metadata": deepcopy(self.metadata),
        }

    def relink(
        self,
        candidate_path: Path,
        metadata: Mapping[str, Any] | None = None,
    ) -> SourceReference:
        """Return this identity at an explicitly validated replacement path."""
        resolved = Path(candidate_path).expanduser().resolve()
        try:
            stat = resolved.stat()
        except OSError as error:
            raise ProjectValidationError(
                f"Cannot inspect relink candidate {resolved.name}: {error}"
            ) from error
        if not resolved.is_file():
            raise ProjectValidationError(f"Relink candidate is not a file: {resolved.name}")
        if stat.st_size != self.size_bytes:
            raise ProjectValidationError(
                f"Relink candidate size does not match source {self.source_id}"
            )
        candidate_metadata = _source_metadata(
            self.metadata if metadata is None else metadata,
        )
        comparable_keys = (
            "duration_seconds",
            "width",
            "height",
            "frame_rate",
            "video_codec",
            "format_name",
            "audio_stream_present",
        )
        for key in comparable_keys:
            expected = self.metadata.get(key)
            actual = candidate_metadata.get(key)
            if expected is not None and actual != expected:
                raise ProjectValidationError(
                    f"Relink candidate metadata does not match source {self.source_id}: {key}"
                )
        return SourceReference(
            source_id=self.source_id,
            path=str(resolved),
            uri=resolved.as_uri(),
            size_bytes=stat.st_size,
            modified_time_ns=stat.st_mtime_ns,
            metadata=candidate_metadata,
        )

    def status(self) -> SourceStatus:
        path = Path(self.path)
        try:
            stat = path.stat()
        except FileNotFoundError:
            return SourceStatus(False, False, f"Source is missing: {path.name}")
        except OSError as error:
            return SourceStatus(False, False, f"Source cannot be inspected: {error}")
        if not path.is_file():
            return SourceStatus(False, False, f"Source is not a file: {path.name}")
        changed = stat.st_size != self.size_bytes or stat.st_mtime_ns != self.modified_time_ns
        if changed:
            return SourceStatus(
                True,
                True,
                f"Source changed since the project was saved: {path.name}",
            )
        return SourceStatus(True, False, None)


@dataclass(frozen=True)
class Segment:
    segment_id: str
    start_seconds: float
    end_seconds: float
    deleted: bool = False
    source_id: str | None = None
    timeline_start_seconds: float | None = None
    timeline_end_seconds: float | None = None
    state: dict[str, Any] = field(default_factory=dict)
    block_id: str | None = None
    color_index: int | None = None
    visual_transform: VisualTransform = field(default_factory=VisualTransform)
    triplicate: TriplicateGroup | None = None
    _color_index_explicit: bool = field(default=False, init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        if not isinstance(self.segment_id, str) or not self.segment_id:
            raise ProjectValidationError("Segment segment_id must be a non-empty string")
        start = _finite_float(self.start_seconds, "Segment start")
        end = _finite_float(self.end_seconds, "Segment end")
        if start < 0:
            raise ProjectValidationError("Segment start must not be negative")
        if end <= start:
            raise ProjectValidationError("Segment end must be greater than segment start")
        if not isinstance(self.deleted, bool):
            raise ProjectValidationError("Segment deleted must be a boolean")
        if self.source_id is not None and (
            not isinstance(self.source_id, str) or not self.source_id
        ):
            raise ProjectValidationError("Segment source_id must be a non-empty string")
        timeline_start = self.timeline_start_seconds
        timeline_end = self.timeline_end_seconds
        if (timeline_start is None) != (timeline_end is None):
            raise ProjectValidationError("Segment timeline start and end must be provided together")
        if timeline_start is not None and timeline_end is not None:
            timeline_start = _finite_float(timeline_start, "Segment timeline start")
            timeline_end = _finite_float(timeline_end, "Segment timeline end")
            if timeline_start < 0 or timeline_end <= timeline_start:
                raise ProjectValidationError("Segment timeline bounds are invalid")
        if not isinstance(self.state, Mapping):
            raise ProjectValidationError("Segment state must be an object")
        if not isinstance(self.visual_transform, VisualTransform):
            raise ProjectValidationError("Segment visual transform is invalid")
        if self.triplicate is not None and not isinstance(self.triplicate, TriplicateGroup):
            raise ProjectValidationError("Segment triplicate group is invalid")
        state = deepcopy(dict(self.state))
        visual_transform = self.visual_transform
        try:
            if visual_transform.is_default:
                visual_transform = coerce_legacy_transform(state)
        except ValueError as error:
            raise ProjectValidationError(str(error)) from error
        triplicate = self.triplicate
        if triplicate is not None and triplicate.shared_transform != visual_transform:
            raise ProjectValidationError(
                "Segment triplicate transform must match its visual transform"
            )
        if self.block_id is not None and (not isinstance(self.block_id, str) or not self.block_id):
            raise ProjectValidationError("Segment block_id must be a non-empty string")
        color_index = self.color_index
        if color_index is not None and (
            not isinstance(color_index, int) or isinstance(color_index, bool) or color_index < 0
        ):
            raise ProjectValidationError("Segment color_index must be a non-negative integer")
        color_index_explicit = color_index is not None
        if color_index is None:
            color_index = _default_segment_color_index(self.segment_id)
        object.__setattr__(self, "start_seconds", start)
        object.__setattr__(self, "end_seconds", end)
        object.__setattr__(self, "timeline_start_seconds", timeline_start)
        object.__setattr__(self, "timeline_end_seconds", timeline_end)
        object.__setattr__(self, "state", state)
        object.__setattr__(self, "color_index", color_index)
        object.__setattr__(self, "visual_transform", visual_transform)
        object.__setattr__(self, "triplicate", triplicate)
        object.__setattr__(self, "_color_index_explicit", color_index_explicit)

    @classmethod
    def create(
        cls,
        start_seconds: float,
        end_seconds: float,
        *,
        deleted: bool = False,
        segment_id: str | None = None,
        source_id: str | None = None,
        timeline_start_seconds: float | None = None,
        timeline_end_seconds: float | None = None,
        state: Mapping[str, Any] | None = None,
        block_id: str | None = None,
        color_index: int | None = None,
        visual_transform: VisualTransform | None = None,
        triplicate: TriplicateGroup | None = None,
    ) -> Segment:
        return cls(
            segment_id=segment_id or uuid.uuid4().hex,
            start_seconds=start_seconds,
            end_seconds=end_seconds,
            deleted=deleted,
            source_id=source_id,
            timeline_start_seconds=timeline_start_seconds,
            timeline_end_seconds=timeline_end_seconds,
            state={} if state is None else dict(state),
            block_id=block_id,
            color_index=color_index,
            visual_transform=(VisualTransform() if visual_transform is None else visual_transform),
            triplicate=triplicate,
        )

    @property
    def duration_seconds(self) -> float:
        return self.end_seconds - self.start_seconds

    @property
    def timeline_start(self) -> float:
        return (
            self.start_seconds
            if self.timeline_start_seconds is None
            else self.timeline_start_seconds
        )

    @property
    def timeline_end(self) -> float:
        return self.end_seconds if self.timeline_end_seconds is None else self.timeline_end_seconds

    def to_dict(self) -> dict[str, Any]:
        value: dict[str, Any] = {
            "segment_id": self.segment_id,
            "start_seconds": self.start_seconds,
            "end_seconds": self.end_seconds,
            "deleted": self.deleted,
        }
        if self.source_id is not None:
            value["source_id"] = self.source_id
        if self.timeline_start_seconds is not None:
            value["timeline_start_seconds"] = self.timeline_start_seconds
            value["timeline_end_seconds"] = self.timeline_end_seconds
        if self.state:
            value["state"] = deepcopy(self.state)
        if self.block_id is not None:
            value["block_id"] = self.block_id
        if self.color_index is not None:
            value["color_index"] = self.color_index
        value["visual_transform"] = self.visual_transform.to_dict()
        if self.triplicate is not None:
            value["triplicate"] = self.triplicate.to_dict()
        return value

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> Segment:
        if not isinstance(value, Mapping):
            raise ProjectValidationError("Project segment must be an object")
        segment_id = value.get("segment_id")
        start_seconds = value.get("start_seconds")
        end_seconds = value.get("end_seconds")
        deleted = value.get("deleted")
        source_id = value.get("source_id")
        timeline_start_seconds = value.get("timeline_start_seconds")
        timeline_end_seconds = value.get("timeline_end_seconds")
        state = value.get("state", {})
        block_id = value.get("block_id")
        color_index = value.get("color_index")
        visual_transform_value = value.get("visual_transform")
        triplicate_value = value.get("triplicate")
        if not isinstance(segment_id, str) or not segment_id:
            raise ProjectValidationError("Project segment_id must be a non-empty string")
        if not isinstance(start_seconds, (int, float)) or isinstance(start_seconds, bool):
            raise ProjectValidationError("Project segment start must be a number")
        if not isinstance(end_seconds, (int, float)) or isinstance(end_seconds, bool):
            raise ProjectValidationError("Project segment end must be a number")
        if not isinstance(deleted, bool):
            raise ProjectValidationError("Project segment deleted must be a boolean")
        if source_id is not None and not isinstance(source_id, str):
            raise ProjectValidationError("Project segment source_id must be a string")
        if timeline_start_seconds is not None and not isinstance(
            timeline_start_seconds,
            (int, float),
        ):
            raise ProjectValidationError("Project segment timeline start must be a number")
        if timeline_end_seconds is not None and not isinstance(
            timeline_end_seconds,
            (int, float),
        ):
            raise ProjectValidationError("Project segment timeline end must be a number")
        if not isinstance(state, Mapping):
            raise ProjectValidationError("Project segment state must be an object")
        if block_id is not None and not isinstance(block_id, str):
            raise ProjectValidationError("Project segment block_id must be a string")
        if color_index is not None and (
            not isinstance(color_index, int) or isinstance(color_index, bool) or color_index < 0
        ):
            raise ProjectValidationError(
                "Project segment color_index must be a non-negative integer"
            )
        try:
            visual_transform = VisualTransform.from_dict(visual_transform_value)
            triplicate = (
                None if triplicate_value is None else TriplicateGroup.from_dict(triplicate_value)
            )
        except (TypeError, ValueError) as error:
            raise ProjectValidationError(str(error)) from error
        return cls(
            segment_id=segment_id,
            start_seconds=float(start_seconds),
            end_seconds=float(end_seconds),
            deleted=deleted,
            source_id=source_id,
            timeline_start_seconds=(
                None if timeline_start_seconds is None else float(timeline_start_seconds)
            ),
            timeline_end_seconds=(
                None if timeline_end_seconds is None else float(timeline_end_seconds)
            ),
            state=dict(state),
            block_id=block_id,
            color_index=color_index,
            visual_transform=visual_transform,
            triplicate=triplicate,
        )

    def clone(
        self,
        *,
        new_id: bool = True,
        timeline_start_seconds: float | None = None,
        timeline_end_seconds: float | None = None,
    ) -> Segment:
        segment_id = uuid.uuid4().hex if new_id else self.segment_id
        return Segment(
            segment_id=segment_id,
            start_seconds=self.start_seconds,
            end_seconds=self.end_seconds,
            deleted=self.deleted,
            source_id=self.source_id,
            timeline_start_seconds=(
                self.timeline_start_seconds
                if timeline_start_seconds is None
                else timeline_start_seconds
            ),
            timeline_end_seconds=(
                self.timeline_end_seconds if timeline_end_seconds is None else timeline_end_seconds
            ),
            state=deepcopy(self.state),
            block_id=(segment_id if new_id else self.block_id),
            color_index=self.color_index,
            visual_transform=self.visual_transform,
            triplicate=(None if self.triplicate is None else self.triplicate.clone(new_id=new_id)),
        )

    def with_color_index(self, color_index: int) -> Segment:
        return Segment(
            segment_id=self.segment_id,
            start_seconds=self.start_seconds,
            end_seconds=self.end_seconds,
            deleted=self.deleted,
            source_id=self.source_id,
            timeline_start_seconds=self.timeline_start_seconds,
            timeline_end_seconds=self.timeline_end_seconds,
            state=self.state,
            block_id=self.block_id,
            color_index=color_index,
            visual_transform=self.visual_transform,
            triplicate=self.triplicate,
        )

    def with_visual_transform(self, visual_transform: VisualTransform) -> Segment:
        triplicate = (
            None if self.triplicate is None else self.triplicate.with_transform(visual_transform)
        )
        return Segment(
            segment_id=self.segment_id,
            start_seconds=self.start_seconds,
            end_seconds=self.end_seconds,
            deleted=self.deleted,
            source_id=self.source_id,
            timeline_start_seconds=self.timeline_start_seconds,
            timeline_end_seconds=self.timeline_end_seconds,
            state=self.state,
            block_id=self.block_id,
            color_index=self.color_index,
            visual_transform=visual_transform,
            triplicate=triplicate,
        )

    def with_triplicate(self, triplicate: TriplicateGroup | None) -> Segment:
        visual_transform = (
            self.visual_transform if triplicate is None else triplicate.shared_transform
        )
        return Segment(
            segment_id=self.segment_id,
            start_seconds=self.start_seconds,
            end_seconds=self.end_seconds,
            deleted=self.deleted,
            source_id=self.source_id,
            timeline_start_seconds=self.timeline_start_seconds,
            timeline_end_seconds=self.timeline_end_seconds,
            state=self.state,
            block_id=self.block_id,
            color_index=self.color_index,
            visual_transform=visual_transform,
            triplicate=triplicate,
        )

    @property
    def has_visual_modifications(self) -> bool:
        return not self.visual_transform.is_default or (
            self.triplicate is not None and self.triplicate.enabled
        )

    @property
    def color_slot(self) -> int:
        if self.color_index is None:
            raise ProjectValidationError("Segment color_index is not assigned")
        return self.color_index


def _split_segment_color_indices(segment: Segment) -> tuple[int, int]:
    return segment.color_slot + 1, segment.color_slot + 2


def _assign_missing_segment_colors(segments: Sequence[Segment]) -> tuple[Segment, ...]:
    for index, segment in enumerate(segments):
        if not isinstance(segment, Segment):
            raise ProjectValidationError(f"Timeline segment at index {index} must be a Segment")
    used_colors = {
        segment.color_index
        for segment in segments
        if segment._color_index_explicit and segment.color_index is not None
    }
    next_color = 0
    normalized: list[Segment] = []
    for segment in segments:
        if not segment._color_index_explicit:
            while next_color in used_colors:
                next_color += 1
            segment = segment.with_color_index(next_color)
            used_colors.add(next_color)
            next_color += 1
        normalized.append(segment)
    return tuple(normalized)
