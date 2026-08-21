from __future__ import annotations

import math
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

LEGACY_SCHEMA_VERSION = 1
SCHEMA_VERSION = 2
_TIME_EPSILON = 1e-9


class ProjectValidationError(ValueError):
    """Raised when a project or source record is invalid."""


def _finite_float(value: Any, label: str) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ProjectValidationError(f"{label} must be a finite number")
    parsed = float(value)
    if not math.isfinite(parsed):
        raise ProjectValidationError(f"{label} must be a finite number")
    return parsed


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
        if not isinstance(metadata, Mapping):
            raise ProjectValidationError("Source metadata must be an object")
        return cls(
            source_id=source_id or uuid.uuid4().hex,
            path=str(resolved),
            uri=resolved.as_uri(),
            size_bytes=stat.st_size,
            modified_time_ns=stat.st_mtime_ns,
            metadata=dict(metadata),
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
            metadata=dict(metadata),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "path": self.path,
            "uri": self.uri,
            "size_bytes": self.size_bytes,
            "modified_time_ns": self.modified_time_ns,
            "metadata": dict(self.metadata),
        }

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
        object.__setattr__(self, "start_seconds", start)
        object.__setattr__(self, "end_seconds", end)

    @classmethod
    def create(
        cls,
        start_seconds: float,
        end_seconds: float,
        *,
        deleted: bool = False,
        segment_id: str | None = None,
    ) -> Segment:
        return cls(
            segment_id=segment_id or uuid.uuid4().hex,
            start_seconds=start_seconds,
            end_seconds=end_seconds,
            deleted=deleted,
        )

    @property
    def duration_seconds(self) -> float:
        return self.end_seconds - self.start_seconds

    def to_dict(self) -> dict[str, Any]:
        return {
            "segment_id": self.segment_id,
            "start_seconds": self.start_seconds,
            "end_seconds": self.end_seconds,
            "deleted": self.deleted,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> Segment:
        if not isinstance(value, Mapping):
            raise ProjectValidationError("Project segment must be an object")
        segment_id = value.get("segment_id")
        start_seconds = value.get("start_seconds")
        end_seconds = value.get("end_seconds")
        deleted = value.get("deleted")
        if not isinstance(segment_id, str) or not segment_id:
            raise ProjectValidationError("Project segment_id must be a non-empty string")
        if not isinstance(start_seconds, (int, float)) or isinstance(start_seconds, bool):
            raise ProjectValidationError("Project segment start must be a number")
        if not isinstance(end_seconds, (int, float)) or isinstance(end_seconds, bool):
            raise ProjectValidationError("Project segment end must be a number")
        if not isinstance(deleted, bool):
            raise ProjectValidationError("Project segment deleted must be a boolean")
        return cls(
            segment_id=segment_id,
            start_seconds=float(start_seconds),
            end_seconds=float(end_seconds),
            deleted=deleted,
        )


@dataclass
class SegmentTimeline:
    source_duration_seconds: float
    segments: tuple[Segment, ...] | None = None

    def __post_init__(self) -> None:
        self.source_duration_seconds = _finite_float(
            self.source_duration_seconds,
            "Source duration",
        )
        if self.source_duration_seconds <= 0:
            raise ProjectValidationError("Source duration must be greater than zero")
        if self.segments is None:
            self.segments = (Segment.create(0.0, self.source_duration_seconds),)
        else:
            self.segments = tuple(self.segments)
        self.validate()

    @classmethod
    def from_segments(
        cls,
        source_duration_seconds: float,
        segments: tuple[Segment, ...] | list[Segment],
    ) -> SegmentTimeline:
        return cls(source_duration_seconds, tuple(segments))

    @property
    def segment_items(self) -> tuple[Segment, ...]:
        if self.segments is None:
            raise ProjectValidationError("Segment timeline must contain segments")
        return self.segments

    @property
    def edited_duration_seconds(self) -> float:
        return sum(
            segment.duration_seconds for segment in self.segment_items if not segment.deleted
        )

    def validate(self) -> None:
        segments = self.segments
        if segments is None or not segments:
            raise ProjectValidationError("Segment timeline must contain at least one segment")
        seen_ids: set[str] = set()
        previous_end = 0.0
        for index, segment in enumerate(segments):
            if not isinstance(segment, Segment):
                raise ProjectValidationError(f"Segment at index {index} must be a Segment")
            if segment.segment_id in seen_ids:
                raise ProjectValidationError(f"Duplicate segment_id: {segment.segment_id}")
            seen_ids.add(segment.segment_id)
            if segment.start_seconds < 0 or segment.end_seconds > self.source_duration_seconds:
                raise ProjectValidationError(
                    f"Segment {segment.segment_id} is outside the source duration"
                )
            if not math.isclose(
                segment.start_seconds,
                previous_end,
                rel_tol=0.0,
                abs_tol=_TIME_EPSILON,
            ):
                if index == 0:
                    raise ProjectValidationError("First segment must start at zero")
                raise ProjectValidationError(
                    f"Segment {segment.segment_id} is not contiguous with the previous segment"
                )
            previous_end = segment.end_seconds
        if not math.isclose(
            previous_end,
            self.source_duration_seconds,
            rel_tol=0.0,
            abs_tol=_TIME_EPSILON,
        ):
            raise ProjectValidationError("Last segment must end at the source duration")
        edited_duration = self.edited_duration_seconds
        if not math.isfinite(edited_duration) or edited_duration < 0:
            raise ProjectValidationError("Edited duration must not be negative")

    def split(self, position_seconds: float) -> tuple[Segment, Segment]:
        position = _finite_float(position_seconds, "Split position")
        self.validate()
        segments = self.segment_items
        for index, segment in enumerate(segments):
            if segment.start_seconds < position < segment.end_seconds:
                first = Segment.create(
                    segment.start_seconds,
                    position,
                    deleted=segment.deleted,
                )
                second = Segment.create(
                    position,
                    segment.end_seconds,
                    deleted=segment.deleted,
                )
                candidate = segments[:index] + (first, second) + segments[index + 1 :]
                self._replace_segments(candidate)
                return first, second
        raise ProjectValidationError("Split position must be strictly inside one segment")

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

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "source_duration_seconds": self.source_duration_seconds,
            "segments": [segment.to_dict() for segment in self.segment_items],
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> SegmentTimeline:
        if not isinstance(value, Mapping):
            raise ProjectValidationError("Segment timeline must be an object")
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

    def _replace_segments(self, segments: tuple[Segment, ...]) -> None:
        previous_segments = self.segments
        self.segments = segments
        try:
            self.validate()
        except ProjectValidationError:
            self.segments = previous_segments
            raise


@dataclass
class Project:
    project_id: str
    source: SourceReference
    duration_seconds: float
    playhead_seconds: float = 0.0
    schema_version: int = SCHEMA_VERSION
    segment_timeline: SegmentTimeline | None = None

    @classmethod
    def create(
        cls,
        source_path: Path,
        metadata: Mapping[str, Any],
        project_id: str | None = None,
    ) -> Project:
        duration_value = metadata.get("duration_seconds")
        if not isinstance(duration_value, (int, float)) or isinstance(duration_value, bool):
            raise ProjectValidationError("Source metadata needs duration_seconds")
        duration = float(duration_value)
        if not math.isfinite(duration) or duration <= 0:
            raise ProjectValidationError("Source duration must be greater than zero")
        return cls(
            project_id=project_id or uuid.uuid4().hex,
            source=SourceReference.from_path(source_path, metadata),
            duration_seconds=duration,
        )

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> Project:
        if not isinstance(value, Mapping):
            raise ProjectValidationError("Project must be an object")
        schema_version = value.get("schema_version")
        if (
            not isinstance(schema_version, int)
            or isinstance(schema_version, bool)
            or schema_version not in (LEGACY_SCHEMA_VERSION, SCHEMA_VERSION)
        ):
            raise ProjectValidationError(
                f"Unsupported project schema version: {schema_version!r}; "
                f"supported versions are {LEGACY_SCHEMA_VERSION} and "
                f"{SCHEMA_VERSION}"
            )
        project_id = value.get("project_id")
        if not isinstance(project_id, str) or not project_id:
            raise ProjectValidationError("Project project_id must be a non-empty string")
        raw_source = value.get("source")
        if not isinstance(raw_source, Mapping):
            raise ProjectValidationError("Project source must be an object")
        source = SourceReference.from_dict(raw_source)
        timeline = value.get("timeline")
        if not isinstance(timeline, Mapping):
            raise ProjectValidationError("Project timeline must be an object")
        duration = timeline.get("duration_seconds")
        playhead = timeline.get("playhead_seconds")
        if not isinstance(duration, (int, float)) or isinstance(duration, bool):
            raise ProjectValidationError("Timeline duration must be a number")
        if not isinstance(playhead, (int, float)) or isinstance(playhead, bool):
            raise ProjectValidationError("Timeline playhead must be a number")
        if schema_version == LEGACY_SCHEMA_VERSION:
            segment_timeline = SegmentTimeline(float(duration))
        else:
            raw_segments = timeline.get("segments")
            if not isinstance(raw_segments, list):
                raise ProjectValidationError("Timeline segments must be an array")
            segments: list[Segment] = []
            for item in raw_segments:
                if not isinstance(item, Mapping):
                    raise ProjectValidationError("Project segment must be an object")
                segments.append(Segment.from_dict(item))
            segment_timeline = SegmentTimeline.from_segments(
                float(duration),
                tuple(segments),
            )
            persisted_edited_duration = timeline.get("edited_duration_seconds")
            if persisted_edited_duration is None:
                raise ProjectValidationError("Timeline edited duration is required")
            persisted_edited_duration = _finite_float(
                persisted_edited_duration,
                "Timeline edited duration",
            )
            if not math.isclose(
                persisted_edited_duration,
                segment_timeline.edited_duration_seconds,
                rel_tol=0.0,
                abs_tol=_TIME_EPSILON,
            ):
                raise ProjectValidationError("Timeline edited duration does not match its segments")
        project = cls(
            project_id=project_id,
            source=source,
            duration_seconds=float(duration),
            playhead_seconds=float(playhead),
            schema_version=SCHEMA_VERSION,
            segment_timeline=segment_timeline,
        )
        project.validate()
        return project

    def __post_init__(self) -> None:
        if self.segment_timeline is None:
            self.segment_timeline = SegmentTimeline(self.duration_seconds)
        self.validate()

    def validate(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise ProjectValidationError(
                f"Unsupported project schema version: {self.schema_version!r}"
            )
        if not isinstance(self.project_id, str) or not self.project_id:
            raise ProjectValidationError("Project project_id must be a non-empty string")
        if not math.isfinite(self.duration_seconds) or self.duration_seconds <= 0:
            raise ProjectValidationError("Project duration must be greater than zero")
        if not math.isfinite(self.playhead_seconds):
            raise ProjectValidationError("Project playhead must be finite")
        if not 0 <= self.playhead_seconds <= self.duration_seconds:
            raise ProjectValidationError("Project playhead must be within the duration")
        if self.segment_timeline is None:
            raise ProjectValidationError("Project segment timeline is required")
        self.segment_timeline.validate()
        if not math.isclose(
            self.segment_timeline.source_duration_seconds,
            self.duration_seconds,
            rel_tol=0.0,
            abs_tol=_TIME_EPSILON,
        ):
            raise ProjectValidationError(
                "Project segment timeline duration must match project duration"
            )

    def set_playhead(self, position_seconds: float) -> None:
        if (
            not isinstance(position_seconds, (int, float))
            or isinstance(position_seconds, bool)
            or not math.isfinite(float(position_seconds))
        ):
            raise ProjectValidationError("Playhead position must be finite")
        self.playhead_seconds = max(
            0.0,
            min(self.duration_seconds, float(position_seconds)),
        )

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        if self.segment_timeline is None:
            raise ProjectValidationError("Project segment timeline is required")
        segments = self.segment_timeline.segment_items
        return {
            "schema_version": self.schema_version,
            "project_id": self.project_id,
            "source": self.source.to_dict(),
            "timeline": {
                "duration_seconds": self.duration_seconds,
                "playhead_seconds": self.playhead_seconds,
                "edited_duration_seconds": (self.segment_timeline.edited_duration_seconds),
                "segments": [segment.to_dict() for segment in segments],
            },
        }
