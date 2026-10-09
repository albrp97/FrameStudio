from __future__ import annotations

import math
import uuid
from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence, cast

from .audio import pending_audio_decision
from .composition import COMPOSITION_SCHEMA_VERSION
from .fps_policy import (
    FrameRatePolicy,
    FrameRatePolicyError,
    ResolvedFrameRatePolicy,
    resolved_from_policy,
)
from .fps_policy import (
    resolve_frame_rate_policy as resolve_fps_policy,
)
from .model_timeline import (
    ABSOLUTE_TIMING_MODE,
    LEGACY_TIMING_MODE,
    SegmentTimeline,
    TimelineTrack,
)
from .model_types import (
    _TIME_EPSILON,
    LEGACY_SCHEMA_VERSION,
    MIXED_SOURCE_SCHEMA_VERSION,
    ONE_SOURCE_SCHEMA_VERSION,
    SCHEMA_VERSION,
    ProjectValidationError,
    Segment,
    SourceReference,
    _finite_float,
    seconds_to_ticks,
    ticks_to_seconds,
)
from .removal_history import _RuntimeContext
from .upscale_policy import (
    ResolvedUpscalePolicy,
    UpscalePolicy,
    UpscalePolicyError,
)
from .upscale_policy import (
    resolve_upscale_policy as resolve_upscale,
)


@dataclass
class Project(_RuntimeContext):
    project_id: str
    source: SourceReference
    duration_seconds: float
    playhead_seconds: float = 0.0
    schema_version: int = ONE_SOURCE_SCHEMA_VERSION
    segment_timeline: SegmentTimeline | None = None
    sources: tuple[SourceReference, ...] | None = None
    source_settings: dict[str, dict[str, Any]] = field(default_factory=dict)
    output_settings: dict[str, Any] = field(default_factory=dict)
    composition_version: int = COMPOSITION_SCHEMA_VERSION

    @staticmethod
    def _settings_with_pending_audio(
        source_settings: Mapping[str, Mapping[str, Any]],
        sources: Sequence[SourceReference],
    ) -> dict[str, dict[str, Any]]:
        settings = cast(
            dict[str, dict[str, Any]],
            deepcopy(dict(source_settings)),
        )
        for source in sources:
            settings[source.source_id] = {
                "audio": pending_audio_decision(source).to_dict(),
            }
        return settings

    @staticmethod
    def _track_block(
        block: Segment,
        source_id: str,
        *,
        track_id: str = "track-1",
    ) -> Segment:
        return Segment(
            segment_id=block.segment_id,
            start_seconds=block.start_seconds,
            end_seconds=block.end_seconds,
            deleted=block.deleted,
            source_id=source_id,
            timeline_start_seconds=block.timeline_start,
            timeline_end_seconds=block.timeline_end,
            state=block.state,
            block_id=block.block_id or block.segment_id,
            color_index=block.color_index,
            visual_transform=block.visual_transform,
            triplicate=block.triplicate,
            track_id=track_id,
        )

    @staticmethod
    def _sources_from_value(
        raw_sources: object,
        *,
        missing_message: str,
    ) -> tuple[SourceReference, ...]:
        if not isinstance(raw_sources, list) or not raw_sources:
            raise ProjectValidationError(missing_message)
        sources: list[SourceReference] = []
        for item in raw_sources:
            if not isinstance(item, Mapping):
                raise ProjectValidationError("Project source must be an object")
            sources.append(SourceReference.from_dict(item))
        source_ids = [source.source_id for source in sources]
        if len(set(source_ids)) != len(source_ids):
            raise ProjectValidationError("Project sources must have unique source_id values")
        return tuple(sources)

    @staticmethod
    def _settings_from_value(
        value: Mapping[str, Any],
    ) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
        raw_source_settings = value.get("source_settings", {})
        raw_output_settings = value.get("output_settings", {})
        if not isinstance(raw_source_settings, Mapping):
            raise ProjectValidationError("Project source settings must be an object")
        if not isinstance(raw_output_settings, Mapping):
            raise ProjectValidationError("Project output settings must be an object")
        return (
            cast(dict[str, dict[str, Any]], dict(raw_source_settings)),
            dict(raw_output_settings),
        )

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
            source_settings={
                source.source_id: {
                    "audio": pending_audio_decision(source).to_dict(),
                },
            },
        )

    @classmethod
    def create_synchronized(
        cls,
        source_path: Path,
        metadata: Mapping[str, Any],
        project_id: str | None = None,
    ) -> Project:
        base = cls.create(source_path, metadata, project_id)
        duration = _finite_float(
            base.source.metadata.get("duration_seconds"),
            "Source duration",
        )
        block = Segment.create(
            0.0,
            duration,
            segment_id="segment-1",
            block_id="block-1",
            source_id=base.source.source_id,
            timeline_start_seconds=0.0,
            timeline_end_seconds=duration,
            track_id="track-1",
        )
        timeline = SegmentTimeline.from_tracks(
            (TimelineTrack("track-1", (block,)),),
            source_durations={base.source.source_id: duration},
            active_track_id="track-1",
        )
        return cls(
            project_id=base.project_id,
            source=base.source,
            duration_seconds=timeline.timeline_duration_seconds,
            playhead_seconds=0.0,
            schema_version=SCHEMA_VERSION,
            segment_timeline=timeline,
            sources=(base.source,),
            source_settings=deepcopy(base.source_settings),
            output_settings=deepcopy(base.output_settings),
            composition_version=base.composition_version,
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
            schema_version=MIXED_SOURCE_SCHEMA_VERSION,
            segment_timeline=timeline,
            sources=tuple(sources),
            source_settings={
                source.source_id: {
                    "audio": pending_audio_decision(source).to_dict(),
                }
                for source in sources
            },
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
    def create_synchronized_multi(
        cls,
        entries: Sequence[SourceReference | tuple[Path, Mapping[str, Any]]],
        project_id: str | None = None,
        *,
        frame_rate: str | None = None,
    ) -> Project:
        project = cls.create_multi(entries, project_id, frame_rate=frame_rate)
        project.convert_to_synchronized(confirm=True)
        return project

    def append_sources(self, sources: Sequence[SourceReference]) -> tuple[SourceReference, ...]:
        timeline = self.timeline
        incoming = tuple(sources)
        if not incoming:
            raise ProjectValidationError("At least one source is required")
        if any(not isinstance(source, SourceReference) for source in incoming):
            raise ProjectValidationError("Appended sources must be SourceReference values")
        existing_sources = tuple(self.sources or (self.source,))
        existing_ids = {source.source_id for source in existing_sources}
        existing_paths = {Path(source.path).expanduser().resolve() for source in existing_sources}
        incoming_ids: set[str] = set()
        incoming_paths: set[Path] = set()
        for source in incoming:
            path = Path(source.path).expanduser().resolve()
            if path in existing_paths:
                raise ProjectValidationError(
                    f"Source path already belongs to this project: {path.name}"
                )
            if path in incoming_paths:
                raise ProjectValidationError(
                    f"Duplicate source path cannot be appended: {path.name}"
                )
            if source.source_id in existing_ids or source.source_id in incoming_ids:
                raise ProjectValidationError(
                    f"Duplicate source_id cannot be appended: {source.source_id}"
                )
            duration = source.metadata.get("duration_seconds")
            if not isinstance(duration, (int, float)) or isinstance(duration, bool):
                raise ProjectValidationError(
                    f"Source metadata needs duration_seconds: {source.source_id}"
                )
            if _finite_float(duration, "Source duration") <= 0:
                raise ProjectValidationError("Source duration must be greater than zero")
            incoming_ids.add(source.source_id)
            incoming_paths.add(path)
        source_durations = {
            source.source_id: _finite_float(
                source.metadata.get("duration_seconds"),
                f"Source duration for {source.source_id}",
            )
            for source in existing_sources
        }
        source_durations.update(
            {
                source.source_id: _finite_float(
                    source.metadata.get("duration_seconds"),
                    f"Source duration for {source.source_id}",
                )
                for source in incoming
            }
        )
        source_duration_ticks = {
            source_id: seconds_to_ticks(duration)
            for source_id, duration in source_durations.items()
        }
        if self.schema_version == SCHEMA_VERSION and timeline.timing_mode == ABSOLUTE_TIMING_MODE:
            if timeline.tracks is None or timeline.active_track_id is None:
                raise ProjectValidationError(
                    "Synchronized import requires an active timeline track"
                )
            existing_sources = tuple(self.sources or (self.source,))
            active_track = timeline.track_by_id(timeline.active_track_id)
            position_ticks = max(
                (block.timeline_end_ticks for block in active_track.blocks),
                default=0,
            )
            imported_blocks: list[Segment] = []
            for source in incoming:
                duration_ticks = source_duration_ticks[source.source_id]
                imported_blocks.append(
                    Segment.create(
                        0.0,
                        ticks_to_seconds(duration_ticks),
                        source_id=source.source_id,
                        timeline_start_seconds=ticks_to_seconds(position_ticks),
                        timeline_end_seconds=ticks_to_seconds(
                            position_ticks + duration_ticks,
                        ),
                        track_id=timeline.active_track_id,
                    )
                )
                position_ticks += duration_ticks
            candidate_tracks = tuple(
                TimelineTrack(
                    track.track_id,
                    (
                        track.blocks + tuple(imported_blocks)
                        if track.track_id == timeline.active_track_id
                        else track.blocks
                    ),
                )
                for track in timeline.tracks
            )
            combined_timeline = SegmentTimeline.from_tracks(
                candidate_tracks,
                source_durations=source_durations,
                source_durations_ticks=source_duration_ticks,
                active_track_id=timeline.active_track_id,
                timebase=timeline.timebase,
                frame_rate=timeline.frame_rate,
                ripple=False,
                timing_mode=ABSOLUTE_TIMING_MODE,
                mutation_revision=timeline.revision + 1,
            )
            combined_sources = existing_sources + incoming
            combined_settings = self._settings_with_pending_audio(
                self.source_settings,
                incoming,
            )
            candidate = type(self)(
                project_id=self.project_id,
                source=combined_sources[0],
                duration_seconds=combined_timeline.editing_duration_seconds,
                playhead_seconds=min(
                    self.playhead_seconds,
                    combined_timeline.editing_duration_seconds,
                ),
                schema_version=SCHEMA_VERSION,
                segment_timeline=combined_timeline,
                sources=combined_sources,
                source_settings=combined_settings,
                output_settings=deepcopy(self.output_settings),
                composition_version=self.composition_version,
            )
            self._replace_with(candidate)
            return incoming
        if self.schema_version == SCHEMA_VERSION and (timeline.timing_mode != LEGACY_TIMING_MODE):
            raise ProjectValidationError(
                "Appending sources to synchronized projects requires a later track-aware operation"
            )
        if self.schema_version == SCHEMA_VERSION and timeline.timing_mode == "legacy-ripple":
            position_ticks = timeline.editing_duration_ticks
            legacy_appended_blocks: list[Segment] = []
            for source in incoming:
                duration_ticks = seconds_to_ticks(source_durations[source.source_id])
                legacy_appended_blocks.append(
                    Segment.create(
                        0.0,
                        ticks_to_seconds(duration_ticks),
                        source_id=source.source_id,
                        timeline_start_seconds=ticks_to_seconds(position_ticks),
                        timeline_end_seconds=ticks_to_seconds(position_ticks + duration_ticks),
                        track_id=timeline.track_ids[0],
                    )
                )
                position_ticks += duration_ticks
            combined_timeline = SegmentTimeline.from_tracks(
                (
                    TimelineTrack(
                        timeline.track_ids[0],
                        timeline.blocks + tuple(legacy_appended_blocks),
                    ),
                ),
                source_durations=source_durations,
                source_durations_ticks=source_duration_ticks,
                active_track_id=timeline.active_track_id,
                timebase=timeline.timebase,
                frame_rate=timeline.frame_rate,
                ripple=True,
                timing_mode=LEGACY_TIMING_MODE,
                mutation_revision=timeline.revision + 1,
            )
            combined_sources = existing_sources + incoming
            combined_settings = self._settings_with_pending_audio(self.source_settings, incoming)
            candidate = type(self)(
                project_id=self.project_id,
                source=combined_sources[0],
                duration_seconds=combined_timeline.timeline_duration_seconds,
                playhead_seconds=min(
                    self.playhead_seconds,
                    combined_timeline.timeline_duration_seconds,
                ),
                schema_version=SCHEMA_VERSION,
                segment_timeline=combined_timeline,
                sources=combined_sources,
                source_settings=combined_settings,
                output_settings=deepcopy(self.output_settings),
                composition_version=self.composition_version,
            )
            self._replace_with(candidate)
            return incoming
        existing_blocks: tuple[Segment, ...]
        position = timeline.timeline_duration_seconds
        if self.schema_version == ONE_SOURCE_SCHEMA_VERSION:
            original_source_id = existing_sources[0].source_id
            migrated_blocks: list[Segment] = []
            position = 0.0
            for block in timeline.segment_items:
                migrated_blocks.append(
                    Segment(
                        segment_id=block.segment_id,
                        start_seconds=block.start_seconds,
                        end_seconds=block.end_seconds,
                        deleted=block.deleted,
                        source_id=original_source_id,
                        timeline_start_seconds=position,
                        timeline_end_seconds=position + block.duration_seconds,
                        state=block.state,
                        block_id=block.block_id,
                        color_index=block.color_index,
                        visual_transform=block.visual_transform,
                        triplicate=block.triplicate,
                    )
                )
                position += block.duration_seconds
            existing_blocks = tuple(migrated_blocks)
        else:
            existing_blocks = timeline.blocks

        appended_blocks: list[Segment] = []
        for source in incoming:
            duration = source_durations.setdefault(
                source.source_id,
                _finite_float(
                    source.metadata.get("duration_seconds"),
                    f"Source duration for {source.source_id}",
                ),
            )
            appended_blocks.append(
                Segment.create(
                    0.0,
                    duration,
                    source_id=source.source_id,
                    timeline_start_seconds=position,
                    timeline_end_seconds=position + duration,
                )
            )
            position += duration

        combined_sources = existing_sources + incoming
        combined_timeline = SegmentTimeline.from_blocks(
            existing_blocks + tuple(appended_blocks),
            duration_seconds=position,
            source_durations=source_durations,
            timebase=timeline.timebase,
            frame_rate=timeline.frame_rate,
            ripple=timeline.ripple,
            mutation_revision=timeline.revision + 1,
        )
        combined_settings = self._settings_with_pending_audio(self.source_settings, incoming)

        candidate = type(self)(
            project_id=self.project_id,
            source=combined_sources[0],
            duration_seconds=position,
            playhead_seconds=self.playhead_seconds,
            schema_version=MIXED_SOURCE_SCHEMA_VERSION,
            segment_timeline=combined_timeline,
            sources=combined_sources,
            source_settings=combined_settings,
            output_settings=deepcopy(self.output_settings),
            composition_version=self.composition_version,
        )
        self._replace_with(candidate)
        return incoming

    def _legacy_v4_candidate(self) -> Project:
        """Build the canonical one-track legacy-ripple representation."""
        if self.schema_version == SCHEMA_VERSION:
            self.validate()
            return self
        existing_sources = tuple(self.sources or (self.source,))
        source_durations = {
            source.source_id: _finite_float(
                source.metadata.get("duration_seconds"),
                f"Source duration for {source.source_id}",
            )
            for source in existing_sources
        }
        primary_source_id = existing_sources[0].source_id
        blocks: list[Segment] = []
        for block in self.timeline.segment_items:
            source_id = block.source_id or primary_source_id
            if source_id not in source_durations:
                raise ProjectValidationError(
                    f"Legacy block {block.segment_id} references unknown source {source_id}"
                )
            blocks.append(self._track_block(block, source_id))
        timeline = SegmentTimeline.from_tracks(
            (TimelineTrack("track-1", tuple(blocks)),),
            source_durations=source_durations,
            source_durations_ticks={
                source_id: seconds_to_ticks(duration)
                for source_id, duration in source_durations.items()
            },
            active_track_id="track-1",
            timebase=self.timeline.timebase,
            frame_rate=self.timeline.frame_rate,
            ripple=True,
            timing_mode=LEGACY_TIMING_MODE,
        )
        timeline.mixed_source = len(existing_sources) > 1
        return type(self)(
            project_id=self.project_id,
            source=existing_sources[0],
            duration_seconds=timeline.timeline_duration_seconds,
            playhead_seconds=min(
                self.playhead_seconds,
                timeline.timeline_duration_seconds,
            ),
            schema_version=SCHEMA_VERSION,
            segment_timeline=timeline,
            sources=existing_sources,
            source_settings=deepcopy(self.source_settings),
            output_settings=deepcopy(self.output_settings),
            composition_version=self.composition_version,
        )

    def _replace_with(self, candidate: Project) -> Project:
        if self.segment_timeline is not None:
            self.segment_timeline._project_owner = None
        self._runtime_epoch += 1
        self.project_id = candidate.project_id
        self.source = candidate.source
        self.duration_seconds = candidate.duration_seconds
        self.playhead_seconds = candidate.playhead_seconds
        self.schema_version = candidate.schema_version
        self.segment_timeline = candidate.segment_timeline
        self.sources = candidate.sources
        self.source_settings = candidate.source_settings
        self.output_settings = candidate.output_settings
        self.composition_version = candidate.composition_version
        if self.segment_timeline is not None:
            self.segment_timeline._project_owner = self
        return self

    def _migrate_legacy_to_v4(self) -> Project:
        return self._replace_with(self._legacy_v4_candidate())

    @classmethod
    def _from_synchronized_dict(
        cls,
        value: Mapping[str, Any],
        *,
        project_id: str,
        composition_version: int,
        timeline: Mapping[str, Any],
    ) -> Project:
        sources = cls._sources_from_value(
            value.get("sources"),
            missing_message="Synchronized projects need a non-empty sources array",
        )
        raw_source = value.get("source")
        if not isinstance(raw_source, Mapping):
            raise ProjectValidationError("Synchronized projects need a source object")
        source = SourceReference.from_dict(raw_source)
        if source != sources[0]:
            raise ProjectValidationError("Project source must match the first source entry")
        duration_ticks = timeline.get("duration_ticks")
        playhead_ticks = timeline.get("playhead_ticks")
        if (
            not isinstance(duration_ticks, int)
            or isinstance(duration_ticks, bool)
            or duration_ticks < 0
        ):
            raise ProjectValidationError(
                "Synchronized timeline duration_ticks must be a non-negative integer"
            )
        if (
            not isinstance(playhead_ticks, int)
            or isinstance(playhead_ticks, bool)
            or playhead_ticks < 0
        ):
            raise ProjectValidationError(
                "Synchronized timeline playhead_ticks must be a non-negative integer"
            )
        segment_timeline = SegmentTimeline.from_dict(timeline)
        if segment_timeline.timing_mode == LEGACY_TIMING_MODE:
            segment_timeline.mixed_source = len(sources) > 1
        if duration_ticks != segment_timeline.editing_duration_ticks:
            raise ProjectValidationError(
                "Synchronized timeline duration_ticks does not match its blocks"
            )
        if playhead_ticks > duration_ticks:
            raise ProjectValidationError(
                "Synchronized timeline playhead_ticks must be within its duration"
            )
        source_settings, output_settings = cls._settings_from_value(value)
        project = cls(
            project_id=project_id,
            source=source,
            duration_seconds=segment_timeline.timeline_duration_seconds,
            playhead_seconds=ticks_to_seconds(playhead_ticks),
            schema_version=SCHEMA_VERSION,
            segment_timeline=segment_timeline,
            sources=tuple(sources),
            source_settings=source_settings,
            output_settings=output_settings,
            composition_version=composition_version,
        )
        project.validate()
        return project

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
                MIXED_SOURCE_SCHEMA_VERSION,
                SCHEMA_VERSION,
            )
        ):
            raise ProjectValidationError(
                f"Unsupported project schema version: {schema_version!r}; "
                f"supported versions are {LEGACY_SCHEMA_VERSION} and "
                f"{ONE_SOURCE_SCHEMA_VERSION}, {MIXED_SOURCE_SCHEMA_VERSION}, and "
                f"{SCHEMA_VERSION}"
            )
        project_id = value.get("project_id")
        if not isinstance(project_id, str) or not project_id:
            raise ProjectValidationError("Project project_id must be a non-empty string")
        composition_version = value.get(
            "composition_version",
            COMPOSITION_SCHEMA_VERSION,
        )
        if (
            isinstance(composition_version, bool)
            or not isinstance(composition_version, int)
            or composition_version != COMPOSITION_SCHEMA_VERSION
        ):
            raise ProjectValidationError(
                f"Unsupported composition version: {composition_version!r}"
            )
        timeline = value.get("timeline")
        if not isinstance(timeline, Mapping):
            raise ProjectValidationError("Project timeline must be an object")
        if schema_version == SCHEMA_VERSION:
            return cls._from_synchronized_dict(
                value,
                project_id=project_id,
                composition_version=composition_version,
                timeline=timeline,
            )
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
                legacy_segment = Segment.create(
                    0.0,
                    float(duration),
                    segment_id="segment-1",
                    block_id="segment-1",
                )
                segment_timeline = SegmentTimeline.from_segments(
                    float(duration),
                    (legacy_segment,),
                )
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
            source_settings, output_settings = cls._settings_from_value(value)
            project = cls(
                project_id=project_id,
                source=source,
                duration_seconds=float(duration),
                playhead_seconds=float(playhead),
                schema_version=ONE_SOURCE_SCHEMA_VERSION,
                segment_timeline=segment_timeline,
                sources=(source,),
                source_settings=source_settings,
                output_settings=output_settings,
                composition_version=composition_version,
            )
            project.validate()
            return project._migrate_legacy_to_v4()

        sources = cls._sources_from_value(
            value.get("sources"),
            missing_message="Project sources must be a non-empty array",
        )
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
        source_settings, output_settings = cls._settings_from_value(value)
        project = cls(
            project_id=project_id,
            source=source,
            duration_seconds=float(duration),
            playhead_seconds=float(playhead),
            schema_version=MIXED_SOURCE_SCHEMA_VERSION,
            segment_timeline=segment_timeline,
            sources=tuple(sources),
            source_settings=source_settings,
            output_settings=output_settings,
            composition_version=composition_version,
        )
        project.validate()
        return project._migrate_legacy_to_v4()

    def __post_init__(self) -> None:
        self._initialize_runtime_context()
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
            self.source_settings.setdefault(
                source.source_id,
                {
                    "audio": pending_audio_decision(source).to_dict(),
                },
            )
        if not isinstance(self.output_settings, dict):
            raise ProjectValidationError("Project output settings must be an object")
        self.segment_timeline._project_owner = self
        self.validate()

    def validate(self) -> None:
        if self.composition_version != COMPOSITION_SCHEMA_VERSION:
            raise ProjectValidationError(
                f"Unsupported composition version: {self.composition_version!r}"
            )
        if self.schema_version not in (
            ONE_SOURCE_SCHEMA_VERSION,
            MIXED_SOURCE_SCHEMA_VERSION,
            SCHEMA_VERSION,
        ):
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
        unknown_settings = set(self.source_settings).difference(source_ids)
        if unknown_settings:
            raise ProjectValidationError(
                "Project source settings reference unknown sources: "
                + ", ".join(sorted(unknown_settings))
            )
        for source_id, settings in self.source_settings.items():
            if not isinstance(settings, Mapping):
                raise ProjectValidationError(f"Source settings must be an object: {source_id}")
        if not math.isfinite(self.duration_seconds) or (
            self.duration_seconds < 0
            if self.schema_version == SCHEMA_VERSION
            else self.duration_seconds <= 0
        ):
            raise ProjectValidationError(
                "Project duration must not be negative"
                if self.schema_version == SCHEMA_VERSION
                else "Project duration must be greater than zero"
            )
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
        elif self.schema_version == MIXED_SOURCE_SCHEMA_VERSION:
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
        else:
            if not self.segment_timeline.is_synchronized:
                raise ProjectValidationError("Track schema requires a synchronized timeline")
            if not self.segment_timeline.tracks:
                raise ProjectValidationError("Track schema requires at least one track")
            expected_durations = {
                source.source_id: _finite_float(
                    source.metadata.get("duration_seconds"),
                    f"Source duration for {source.source_id}",
                )
                for source in self.sources
            }
            actual_duration_ticks = self.segment_timeline.source_durations_ticks or {}
            expected_duration_ticks = {
                source_id: seconds_to_ticks(duration)
                for source_id, duration in expected_durations.items()
            }
            if set(actual_duration_ticks) != set(expected_duration_ticks):
                raise ProjectValidationError(
                    "Synchronized timeline source durations must match project sources"
                )
            for source_id in expected_durations:
                actual = actual_duration_ticks[source_id]
                if actual != expected_duration_ticks[source_id]:
                    raise ProjectValidationError(
                        f"Synchronized timeline source duration does not match source {source_id}"
                    )
            self.segment_timeline.validate()
        if self.schema_version == SCHEMA_VERSION:
            duration_matches = (
                seconds_to_ticks(self.duration_seconds)
                == self.segment_timeline.editing_duration_ticks
            )
        else:
            duration_matches = math.isclose(
                self.segment_timeline.timeline_duration_seconds,
                self.duration_seconds,
                rel_tol=0.0,
                abs_tol=_TIME_EPSILON,
            )
        if not duration_matches:
            raise ProjectValidationError(
                "Project segment timeline duration must match project duration"
            )
        self._validate_output_settings()

    def _frame_rate_metadata(self) -> tuple[dict[str, Any], ...]:
        return tuple(
            {
                **source.metadata,
                "source_id": source.source_id,
            }
            for source in (self.sources or (self.source,))
        )

    def _validate_output_settings(self) -> None:
        persisted_fps = self.output_settings.get("frame_rate_policy")
        if persisted_fps is not None:
            try:
                policy = FrameRatePolicy.from_dict(persisted_fps)
                resolved_from_policy(self._frame_rate_metadata(), policy)
            except FrameRatePolicyError as error:
                raise ProjectValidationError(
                    f"Invalid output frame-rate policy: {error}",
                ) from error
        persisted_upscale = self.output_settings.get("upscale_policy")
        if persisted_upscale is not None:
            try:
                upscale_policy = UpscalePolicy.from_dict(persisted_upscale)
                resolve_upscale(
                    self._frame_rate_metadata(),
                    policy=upscale_policy,
                )
            except UpscalePolicyError as error:
                raise ProjectValidationError(
                    f"Invalid output upscale policy: {error}",
                ) from error

    def resolve_frame_rate_policy(self) -> ResolvedFrameRatePolicy:
        persisted = self.output_settings.get("frame_rate_policy")
        try:
            if persisted is None:
                return resolve_fps_policy(self._frame_rate_metadata())
            return resolved_from_policy(
                self._frame_rate_metadata(),
                FrameRatePolicy.from_dict(persisted),
            )
        except FrameRatePolicyError as error:
            raise ProjectValidationError(
                f"Invalid output frame-rate policy: {error}",
            ) from error

    def get_frame_rate_policy(self) -> FrameRatePolicy:
        return self.resolve_frame_rate_policy().policy

    def set_frame_rate_policy(self, policy: FrameRatePolicy | Mapping[str, Any]) -> None:
        try:
            normalized = (
                policy if isinstance(policy, FrameRatePolicy) else FrameRatePolicy.from_dict(policy)
            )
            resolved_from_policy(self._frame_rate_metadata(), normalized)
        except FrameRatePolicyError as error:
            raise ProjectValidationError(
                f"Invalid output frame-rate policy: {error}",
            ) from error
        previous = deepcopy(self.output_settings)
        self.output_settings["frame_rate_policy"] = normalized.to_dict()
        try:
            self.validate()
        except ProjectValidationError:
            self.output_settings = previous
            raise

    def resolve_upscale_policy(self) -> ResolvedUpscalePolicy:
        persisted = self.output_settings.get("upscale_policy")
        try:
            if persisted is None:
                return resolve_upscale(self._frame_rate_metadata())
            return resolve_upscale(
                self._frame_rate_metadata(),
                policy=UpscalePolicy.from_dict(persisted),
            )
        except UpscalePolicyError as error:
            raise ProjectValidationError(
                f"Invalid output upscale policy: {error}",
            ) from error

    def get_upscale_policy(self) -> UpscalePolicy:
        return self.resolve_upscale_policy().policy

    def set_upscale_policy(self, policy: UpscalePolicy | Mapping[str, Any]) -> None:
        try:
            normalized = (
                policy if isinstance(policy, UpscalePolicy) else UpscalePolicy.from_dict(policy)
            )
            resolve_upscale(self._frame_rate_metadata(), policy=normalized)
        except UpscalePolicyError as error:
            raise ProjectValidationError(
                f"Invalid output upscale policy: {error}",
            ) from error
        previous = deepcopy(self.output_settings)
        self.output_settings["upscale_policy"] = normalized.to_dict()
        try:
            self.validate()
        except ProjectValidationError:
            self.output_settings = previous
            raise

    @property
    def timeline(self) -> SegmentTimeline:
        if self.segment_timeline is None:
            raise ProjectValidationError("Project segment timeline is required")
        return self.segment_timeline

    @property
    def runtime_identity(self) -> str:
        return self._runtime_identity

    @property
    def runtime_epoch(self) -> int:
        return self._runtime_epoch

    def _sync_timeline_state(self) -> None:
        timeline = self.segment_timeline
        if timeline is None:
            return
        self.duration_seconds = (
            timeline.editing_duration_seconds
            if self.schema_version == SCHEMA_VERSION
            else timeline.timeline_duration_seconds
        )
        self.playhead_seconds = max(
            0.0,
            min(self.duration_seconds, self.playhead_seconds),
        )

    def convert_to_synchronized(self, *, confirm: bool = False) -> Project:
        """Explicitly convert a legacy project to absolute synchronized timing."""
        if (
            self.schema_version == SCHEMA_VERSION
            and self.timeline.timing_mode == ABSOLUTE_TIMING_MODE
        ):
            self.validate()
            return self
        if confirm is not True:
            raise ProjectValidationError(
                "Explicit confirmation is required to convert legacy timing to synchronized tracks"
            )
        base = self._legacy_v4_candidate()
        existing_sources = tuple(base.sources or (base.source,))
        source_durations = {
            source.source_id: _finite_float(
                source.metadata.get("duration_seconds"),
                f"Source duration for {source.source_id}",
            )
            for source in existing_sources
        }
        source_id = existing_sources[0].source_id
        converted: list[Segment] = []
        for block in base.timeline.segment_items:
            block_source_id = block.source_id or source_id
            if block_source_id not in source_durations:
                raise ProjectValidationError(
                    f"Legacy block {block.segment_id} references unknown source {block_source_id}"
                )
            converted.append(self._track_block(block, block_source_id))
        timeline = SegmentTimeline.from_tracks(
            (TimelineTrack("track-1", tuple(converted)),),
            source_durations=source_durations,
            active_track_id="track-1",
            frame_rate=base.timeline.frame_rate,
            ripple=False,
            timing_mode=ABSOLUTE_TIMING_MODE,
        )
        candidate = type(self)(
            project_id=self.project_id,
            source=existing_sources[0],
            duration_seconds=timeline.timeline_duration_seconds,
            playhead_seconds=min(
                base.playhead_seconds,
                timeline.timeline_duration_seconds,
            ),
            schema_version=SCHEMA_VERSION,
            segment_timeline=timeline,
            sources=existing_sources,
            source_settings=deepcopy(self.source_settings),
            output_settings=deepcopy(self.output_settings),
            composition_version=self.composition_version,
        )
        return self._replace_with(candidate)

    def migrate_to_v4(self, *, confirm: bool = False) -> Project:
        if self.schema_version == SCHEMA_VERSION:
            self.validate()
            return self
        return self._migrate_legacy_to_v4()

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

    def source_audio_settings(self, source_id: str) -> dict[str, Any]:
        source = self.source_by_id(source_id)
        settings = self.source_settings.setdefault(
            source.source_id,
            {
                "audio": pending_audio_decision(source).to_dict(),
            },
        )
        audio = settings.get("audio")
        if not isinstance(audio, Mapping):
            audio = pending_audio_decision(source).to_dict()
            settings["audio"] = audio
        return deepcopy(dict(audio))

    def set_source_audio_settings(
        self,
        source_id: str,
        settings: Mapping[str, Any],
    ) -> None:
        self.source_by_id(source_id)
        if not isinstance(settings, Mapping):
            raise ProjectValidationError("Source audio settings must be an object")
        source_settings = self.source_settings.setdefault(source_id, {})
        source_settings["audio"] = deepcopy(dict(settings))

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
        if self.schema_version == SCHEMA_VERSION:
            timeline = self.segment_timeline.to_dict()
            timeline.update(
                {
                    "duration_ticks": seconds_to_ticks(self.duration_seconds),
                    "playhead_ticks": seconds_to_ticks(self.playhead_seconds),
                }
            )
            return {
                "schema_version": self.schema_version,
                "composition_version": self.composition_version,
                "project_id": self.project_id,
                "source": self.source.to_dict(),
                "sources": [source.to_dict() for source in self.sources or ()],
                "timeline": timeline,
                "source_settings": deepcopy(self.source_settings),
                "output_settings": deepcopy(self.output_settings),
            }
        if self.schema_version == ONE_SOURCE_SCHEMA_VERSION:
            segments = self.segment_timeline.segment_items
            return {
                "schema_version": self.schema_version,
                "composition_version": self.composition_version,
                "project_id": self.project_id,
                "source": self.source.to_dict(),
                "timeline": {
                    "duration_seconds": self.duration_seconds,
                    "source_duration_seconds": (self.segment_timeline.source_duration_seconds),
                    "playhead_seconds": self.playhead_seconds,
                    "edited_duration_seconds": (self.segment_timeline.edited_duration_seconds),
                    "segments": [segment.to_dict() for segment in segments],
                },
                "source_settings": deepcopy(self.source_settings),
                "output_settings": deepcopy(self.output_settings),
            }
        return {
            "schema_version": self.schema_version,
            "composition_version": self.composition_version,
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
