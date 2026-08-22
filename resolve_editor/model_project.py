from __future__ import annotations

import math
import uuid
from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence

from .model_timeline import SegmentTimeline
from .model_types import (
    _TIME_EPSILON,
    LEGACY_SCHEMA_VERSION,
    ONE_SOURCE_SCHEMA_VERSION,
    SCHEMA_VERSION,
    ProjectValidationError,
    Segment,
    SourceReference,
    _finite_float,
)


@dataclass
class Project:
    project_id: str
    source: SourceReference
    duration_seconds: float
    playhead_seconds: float = 0.0
    schema_version: int = ONE_SOURCE_SCHEMA_VERSION
    segment_timeline: SegmentTimeline | None = None
    sources: tuple[SourceReference, ...] | None = None
    source_settings: dict[str, dict[str, Any]] = field(default_factory=dict)
    output_settings: dict[str, Any] = field(default_factory=dict)

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
        source = SourceReference.from_path(source_path, metadata)
        return cls(
            project_id=project_id or uuid.uuid4().hex,
            source=source,
            duration_seconds=duration,
            schema_version=ONE_SOURCE_SCHEMA_VERSION,
            sources=(source,),
        )

    @classmethod
    def create_multi(
        cls,
        entries: Sequence[SourceReference | tuple[Path, Mapping[str, Any]]],
        project_id: str | None = None,
        *,
        frame_rate: str | None = None,
    ) -> Project:
        if not entries:
            raise ProjectValidationError("At least one source is required")
        sources: list[SourceReference] = []
        for entry in entries:
            if isinstance(entry, SourceReference):
                source = entry
            else:
                if not isinstance(entry, tuple) or len(entry) != 2:
                    raise ProjectValidationError(
                        "Source entries must be SourceReference values or path/metadata pairs"
                    )
                path, metadata = entry
                if not isinstance(path, Path) or not isinstance(metadata, Mapping):
                    raise ProjectValidationError(
                        "Source entries must contain a Path and metadata object"
                    )
                source = SourceReference.from_path(path, metadata)
            if any(item.source_id == source.source_id for item in sources):
                raise ProjectValidationError(f"Duplicate source_id: {source.source_id}")
            sources.append(source)
        source_durations: dict[str, float] = {}
        blocks: list[Segment] = []
        position = 0.0
        for source in sources:
            duration_value = source.metadata.get("duration_seconds")
            if not isinstance(duration_value, (int, float)) or isinstance(duration_value, bool):
                raise ProjectValidationError(
                    f"Source metadata needs duration_seconds: {source.source_id}"
                )
            duration = _finite_float(duration_value, "Source duration")
            if duration <= 0:
                raise ProjectValidationError("Source duration must be greater than zero")
            source_durations[source.source_id] = duration
            blocks.append(
                Segment.create(
                    0.0,
                    duration,
                    source_id=source.source_id,
                    timeline_start_seconds=position,
                    timeline_end_seconds=position + duration,
                )
            )
            position += duration
        timeline = SegmentTimeline.from_blocks(
            blocks,
            duration_seconds=position,
            source_durations=source_durations,
            frame_rate=frame_rate,
        )
        return cls(
            project_id=project_id or uuid.uuid4().hex,
            source=sources[0],
            duration_seconds=position,
            schema_version=SCHEMA_VERSION,
            segment_timeline=timeline,
            sources=tuple(sources),
            source_settings={source.source_id: {} for source in sources},
        )

    @classmethod
    def create_from_sources(
        cls,
        entries: Sequence[SourceReference | tuple[Path, Mapping[str, Any]]],
        project_id: str | None = None,
        *,
        frame_rate: str | None = None,
    ) -> Project:
        return cls.create_multi(entries, project_id, frame_rate=frame_rate)

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> Project:
        if not isinstance(value, Mapping):
            raise ProjectValidationError("Project must be an object")
        schema_version = value.get("schema_version")
        if (
            not isinstance(schema_version, int)
            or isinstance(schema_version, bool)
            or schema_version
            not in (
                LEGACY_SCHEMA_VERSION,
                ONE_SOURCE_SCHEMA_VERSION,
                SCHEMA_VERSION,
            )
        ):
            raise ProjectValidationError(
                f"Unsupported project schema version: {schema_version!r}; "
                f"supported versions are {LEGACY_SCHEMA_VERSION} and "
                f"{ONE_SOURCE_SCHEMA_VERSION} and {SCHEMA_VERSION}"
            )
        project_id = value.get("project_id")
        if not isinstance(project_id, str) or not project_id:
            raise ProjectValidationError("Project project_id must be a non-empty string")
        timeline = value.get("timeline")
        if not isinstance(timeline, Mapping):
            raise ProjectValidationError("Project timeline must be an object")
        duration = timeline.get("duration_seconds")
        playhead = timeline.get("playhead_seconds")
        if not isinstance(duration, (int, float)) or isinstance(duration, bool):
            raise ProjectValidationError("Timeline duration must be a number")
        if not isinstance(playhead, (int, float)) or isinstance(playhead, bool):
            raise ProjectValidationError("Timeline playhead must be a number")
        if schema_version in (LEGACY_SCHEMA_VERSION, ONE_SOURCE_SCHEMA_VERSION):
            raw_source = value.get("source")
            if not isinstance(raw_source, Mapping):
                raise ProjectValidationError("Project source must be an object")
            source = SourceReference.from_dict(raw_source)
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
                source_duration = timeline.get("source_duration_seconds")
                if source_duration is None:
                    source_duration = source.metadata.get("duration_seconds", duration)
                segment_timeline = SegmentTimeline.from_segments(
                    _finite_float(source_duration, "Source duration"),
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
                    raise ProjectValidationError(
                        "Timeline edited duration does not match its segments"
                    )
            project = cls(
                project_id=project_id,
                source=source,
                duration_seconds=float(duration),
                playhead_seconds=float(playhead),
                schema_version=ONE_SOURCE_SCHEMA_VERSION,
                segment_timeline=segment_timeline,
                sources=(source,),
            )
            project.validate()
            return project

        raw_sources = value.get("sources")
        if not isinstance(raw_sources, list) or not raw_sources:
            raise ProjectValidationError("Project sources must be a non-empty array")
        sources: list[SourceReference] = []
        for item in raw_sources:
            if not isinstance(item, Mapping):
                raise ProjectValidationError("Project source must be an object")
            sources.append(SourceReference.from_dict(item))
        source_ids = [source.source_id for source in sources]
        if len(set(source_ids)) != len(source_ids):
            raise ProjectValidationError("Project sources must have unique source_id values")
        raw_source = value.get("source")
        source = sources[0] if raw_source is None else SourceReference.from_dict(raw_source)
        if source != sources[0]:
            raise ProjectValidationError("Project source must match the first source entry")
        if "blocks" not in timeline:
            raw_segments = timeline.get("segments")
            if raw_segments is not None:
                timeline = dict(timeline)
                timeline["blocks"] = raw_segments
        source_durations = {
            source.source_id: _finite_float(
                source.metadata.get("duration_seconds"),
                f"Source duration for {source.source_id}",
            )
            for source in sources
        }
        timeline_payload = dict(timeline)
        timeline_payload["source_durations"] = source_durations
        segment_timeline = SegmentTimeline.from_dict(timeline_payload)
        persisted_edited_duration = timeline.get("edited_duration_seconds")
        if persisted_edited_duration is None or not math.isclose(
            _finite_float(persisted_edited_duration, "Timeline edited duration"),
            segment_timeline.edited_duration_seconds,
            rel_tol=0.0,
            abs_tol=_TIME_EPSILON,
        ):
            raise ProjectValidationError("Timeline edited duration does not match its blocks")
        raw_source_settings = value.get("source_settings", {})
        raw_output_settings = value.get("output_settings", {})
        if not isinstance(raw_source_settings, Mapping):
            raise ProjectValidationError("Project source settings must be an object")
        if not isinstance(raw_output_settings, Mapping):
            raise ProjectValidationError("Project output settings must be an object")
        project = cls(
            project_id=project_id,
            source=source,
            duration_seconds=float(duration),
            playhead_seconds=float(playhead),
            schema_version=SCHEMA_VERSION,
            segment_timeline=segment_timeline,
            sources=tuple(sources),
            source_settings=dict(raw_source_settings),
            output_settings=dict(raw_output_settings),
        )
        project.validate()
        return project

    def __post_init__(self) -> None:
        if self.segment_timeline is None:
            self.segment_timeline = SegmentTimeline(self.duration_seconds)
        if self.sources is None:
            self.sources = (self.source,)
        else:
            self.sources = tuple(self.sources)
        if not self.sources:
            raise ProjectValidationError("Project must contain at least one source")
        self.source = self.sources[0]
        if not isinstance(self.source_settings, dict):
            raise ProjectValidationError("Project source settings must be an object")
        for source_id, settings in tuple(self.source_settings.items()):
            if not isinstance(source_id, str) or not source_id:
                raise ProjectValidationError("Project source settings need source identifiers")
            if not isinstance(settings, Mapping):
                raise ProjectValidationError(f"Source settings must be an object: {source_id}")
            self.source_settings[source_id] = deepcopy(dict(settings))
        for source in self.sources:
            self.source_settings.setdefault(source.source_id, {})
        if not isinstance(self.output_settings, dict):
            raise ProjectValidationError("Project output settings must be an object")
        self.validate()

    def validate(self) -> None:
        if self.schema_version not in (ONE_SOURCE_SCHEMA_VERSION, SCHEMA_VERSION):
            raise ProjectValidationError(
                f"Unsupported project schema version: {self.schema_version!r}"
            )
        if not isinstance(self.project_id, str) or not self.project_id:
            raise ProjectValidationError("Project project_id must be a non-empty string")
        if not isinstance(self.sources, tuple) or not self.sources:
            raise ProjectValidationError("Project sources must be a non-empty tuple")
        source_ids = [source.source_id for source in self.sources]
        if len(set(source_ids)) != len(source_ids):
            raise ProjectValidationError("Project source identifiers must be unique")
        if self.source.source_id != self.sources[0].source_id:
            raise ProjectValidationError("Project source must match the first source entry")
        if not math.isfinite(self.duration_seconds) or self.duration_seconds <= 0:
            raise ProjectValidationError("Project duration must be greater than zero")
        if not math.isfinite(self.playhead_seconds):
            raise ProjectValidationError("Project playhead must be finite")
        if not 0 <= self.playhead_seconds <= self.duration_seconds:
            raise ProjectValidationError("Project playhead must be within the duration")
        if self.segment_timeline is None:
            raise ProjectValidationError("Project segment timeline is required")
        self.segment_timeline.validate()
        if self.schema_version == ONE_SOURCE_SCHEMA_VERSION:
            if len(self.sources) != 1 or self.segment_timeline.mixed_source:
                raise ProjectValidationError(
                    "One-source schema cannot contain a mixed-source timeline"
                )
        else:
            if not self.segment_timeline.mixed_source:
                raise ProjectValidationError("Multi-source schema requires a mixed-source timeline")
            self.duration_seconds = self.segment_timeline.source_duration_seconds
            known_sources = set(source_ids)
            for segment in self.segment_timeline.segment_items:
                if segment.source_id not in known_sources:
                    raise ProjectValidationError(
                        f"Timeline block references unknown source: {segment.source_id}"
                    )
            expected_durations = {
                source.source_id: _finite_float(
                    source.metadata.get("duration_seconds"),
                    f"Source duration for {source.source_id}",
                )
                for source in self.sources
            }
            self.segment_timeline.source_durations = expected_durations
            self.segment_timeline.validate()
        if not math.isclose(
            self.segment_timeline.timeline_duration_seconds,
            self.duration_seconds,
            rel_tol=0.0,
            abs_tol=_TIME_EPSILON,
        ):
            raise ProjectValidationError(
                "Project segment timeline duration must match project duration"
            )

    @property
    def timeline(self) -> SegmentTimeline:
        if self.segment_timeline is None:
            raise ProjectValidationError("Project segment timeline is required")
        return self.segment_timeline

    def source_by_id(self, source_id: str) -> SourceReference:
        for source in self.sources or ():
            if source.source_id == source_id:
                return source
        raise ProjectValidationError(f"Unknown source_id: {source_id}")

    def relink_source(
        self,
        source_id: str,
        candidate_path: Path,
        metadata: Mapping[str, Any] | None = None,
    ) -> SourceReference:
        source = self.source_by_id(source_id)
        replacement = source.relink(candidate_path, metadata)
        if self.sources is None:
            raise ProjectValidationError("Project sources are required")
        self.sources = tuple(
            replacement if item.source_id == source_id else item for item in self.sources
        )
        self.source = self.sources[0]
        return replacement

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
        if self.schema_version == ONE_SOURCE_SCHEMA_VERSION:
            segments = self.segment_timeline.segment_items
            return {
                "schema_version": self.schema_version,
                "project_id": self.project_id,
                "source": self.source.to_dict(),
                "timeline": {
                    "duration_seconds": self.duration_seconds,
                    "source_duration_seconds": (self.segment_timeline.source_duration_seconds),
                    "playhead_seconds": self.playhead_seconds,
                    "edited_duration_seconds": (self.segment_timeline.edited_duration_seconds),
                    "segments": [segment.to_dict() for segment in segments],
                },
            }
        return {
            "schema_version": self.schema_version,
            "project_id": self.project_id,
            "source": self.source.to_dict(),
            "sources": [source.to_dict() for source in self.sources or ()],
            "timeline": {
                "duration_seconds": self.duration_seconds,
                "playhead_seconds": self.playhead_seconds,
                **self.segment_timeline.to_dict(),
            },
            "source_settings": deepcopy(self.source_settings),
            "output_settings": deepcopy(self.output_settings),
        }
