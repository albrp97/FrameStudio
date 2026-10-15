"""Planning for final and independent synchronized-track outputs.

This module describes output requests without invoking a renderer.  The
request identity is intentionally explicit so rendering and checkpoint
consumers can distinguish a final composition from a standalone
track/source reel.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .export_types import ExportPlanningError
from .model_project import Project
from .model_timeline import ABSOLUTE_TIMING_MODE
from .model_types import ProjectValidationError, Segment, SourceReference

FINAL_ONLY_OUTPUT_MODE = "final-only"
COMBINED_OUTPUT_MODE = "combined"
SOURCE_ONLY_OUTPUT_MODE = "source-only"

FINAL_FRAMING = "final-composition"
SOURCE_FRAMING = "standalone-full-canvas"
FINAL_AUDIO_INTENT = "mixed-layout-pan"
SOURCE_AUDIO_INTENT = "normal-source-audio"

FINAL_ONLY = FINAL_ONLY_OUTPUT_MODE
COMBINED = COMBINED_OUTPUT_MODE
SOURCE_ONLY = SOURCE_ONLY_OUTPUT_MODE

_OUTPUT_SELECTION_KEY = "output_selection"
_VALID_MODES = {
    FINAL_ONLY_OUTPUT_MODE,
    COMBINED_OUTPUT_MODE,
    SOURCE_ONLY_OUTPUT_MODE,
}
_SAFE_COMPONENT = re.compile(r"[^A-Za-z0-9._-]+")


class OutputPlanError(ExportPlanningError):
    """Raised when a requested output plan cannot be made safely."""


@dataclass(frozen=True)
class OutputSelection:
    """Persisted choice of final and independent source outputs."""

    include_final: bool = True
    include_source_outputs: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.include_final, bool):
            raise OutputPlanError("include_final must be a boolean")
        if not isinstance(self.include_source_outputs, bool):
            raise OutputPlanError("include_source_outputs must be a boolean")
        if not self.include_final and not self.include_source_outputs:
            raise OutputPlanError("At least one output must be selected")

    @property
    def mode(self) -> str:
        if self.include_final and self.include_source_outputs:
            return COMBINED_OUTPUT_MODE
        if self.include_source_outputs:
            return SOURCE_ONLY_OUTPUT_MODE
        return FINAL_ONLY_OUTPUT_MODE

    @classmethod
    def from_mode(cls, mode: str) -> OutputSelection:
        if mode not in _VALID_MODES:
            raise OutputPlanError(f"Unsupported output mode: {mode!r}")
        return cls(
            include_final=mode in {FINAL_ONLY_OUTPUT_MODE, COMBINED_OUTPUT_MODE},
            include_source_outputs=mode in {SOURCE_ONLY_OUTPUT_MODE, COMBINED_OUTPUT_MODE},
        )

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> OutputSelection:
        if not isinstance(value, Mapping):
            raise OutputPlanError("Persisted output selection must be an object")
        mode = value.get("mode")
        raw_final = value.get("include_final")
        raw_sources = value.get("include_source_outputs")
        if raw_final is not None and not isinstance(raw_final, bool):
            raise OutputPlanError("Persisted include_final must be a boolean")
        if raw_sources is not None and not isinstance(raw_sources, bool):
            raise OutputPlanError("Persisted include_source_outputs must be a boolean")
        if mode is not None:
            if not isinstance(mode, str):
                raise OutputPlanError("Persisted output mode must be a string")
            derived = cls.from_mode(mode)
            if raw_final is not None and raw_final != derived.include_final:
                raise OutputPlanError("Persisted output mode conflicts with include_final")
            if raw_sources is not None and raw_sources != derived.include_source_outputs:
                raise OutputPlanError("Persisted output mode conflicts with include_source_outputs")
            return derived
        return cls(
            include_final=True if raw_final is None else raw_final,
            include_source_outputs=False if raw_sources is None else raw_sources,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "include_final": self.include_final,
            "include_source_outputs": self.include_source_outputs,
            "mode": self.mode,
        }


@dataclass(frozen=True)
class OutputIdentity:
    """Stable identity shared by an output request and its eventual result."""

    mode: str
    output_kind: str
    track_id: str | None
    source_id: str | None
    framing: str
    audio_intent: str
    render_profile: str

    def __post_init__(self) -> None:
        if self.mode not in _VALID_MODES:
            raise OutputPlanError(f"Unsupported output mode: {self.mode!r}")
        if self.output_kind not in {"final", "source"}:
            raise OutputPlanError(f"Unsupported output kind: {self.output_kind!r}")
        if self.output_kind == "final" and (
            self.track_id is not None or self.source_id is not None
        ):
            raise OutputPlanError("Final output identity cannot contain a track/source pair")
        if self.output_kind == "source" and (
            not isinstance(self.track_id, str)
            or not self.track_id
            or not isinstance(self.source_id, str)
            or not self.source_id
        ):
            raise OutputPlanError("Source output identity needs a track/source pair")

    @property
    def pair(self) -> tuple[str, str] | None:
        if self.track_id is None or self.source_id is None:
            return None
        return self.track_id, self.source_id

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "output_kind": self.output_kind,
            "track_id": self.track_id,
            "source_id": self.source_id,
            "framing": self.framing,
            "audio_intent": self.audio_intent,
            "render_profile": self.render_profile,
        }


@dataclass(frozen=True)
class OutputRequest:
    """A render-independent request for one final or source output."""

    identity: OutputIdentity
    destination: Path
    segments: tuple[Segment, ...]
    expected_duration_seconds: float
    source_paths: tuple[Path, ...] = ()
    source_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.destination, Path):
            raise OutputPlanError("Output destination must be a path")
        if self.expected_duration_seconds <= 0:
            raise OutputPlanError("Output request duration must be greater than zero")
        if not isinstance(self.segments, tuple):
            object.__setattr__(self, "segments", tuple(self.segments))
        if not isinstance(self.source_paths, tuple):
            object.__setattr__(self, "source_paths", tuple(self.source_paths))
        if not isinstance(self.source_ids, tuple):
            object.__setattr__(self, "source_ids", tuple(self.source_ids))
        if self.identity.output_kind == "source":
            if len(self.source_paths) != 1 or len(self.source_ids) != 1:
                raise OutputPlanError("Source output request needs exactly one source")

    @property
    def output_kind(self) -> str:
        return self.identity.output_kind

    @property
    def track_id(self) -> str | None:
        return self.identity.track_id

    @property
    def source_id(self) -> str | None:
        return self.identity.source_id

    @property
    def source_path(self) -> Path | None:
        return self.source_paths[0] if len(self.source_paths) == 1 else None

    @property
    def segment_ids(self) -> tuple[str, ...]:
        return tuple(segment.segment_id for segment in self.segments)

    @property
    def framing(self) -> str:
        return self.identity.framing

    @property
    def audio_intent(self) -> str:
        return self.identity.audio_intent

    @property
    def result_identity(self) -> OutputIdentity:
        return self.identity

    def to_dict(self) -> dict[str, Any]:
        return {
            "identity": self.identity.to_dict(),
            "destination": str(self.destination),
            "segments": [segment.to_dict() for segment in self.segments],
            "segment_ids": list(self.segment_ids),
            "expected_duration_seconds": self.expected_duration_seconds,
            "source_paths": [str(path) for path in self.source_paths],
            "source_ids": list(self.source_ids),
        }


@dataclass(frozen=True)
class OutputResult:
    """Minimal result identity for a later verified publication step."""

    identity: OutputIdentity
    destination: Path
    verified: bool

    @classmethod
    def from_request(
        cls,
        request: OutputRequest,
        *,
        verified: bool,
    ) -> OutputResult:
        return cls(request.identity, request.destination, verified)

    def to_dict(self) -> dict[str, Any]:
        return {
            "identity": self.identity.to_dict(),
            "destination": str(self.destination),
            "verified": self.verified,
        }


@dataclass(frozen=True)
class OutputPlan:
    """All output requests for one project and one persisted mode."""

    selection: OutputSelection
    final_request: OutputRequest | None
    source_outputs: tuple[OutputRequest, ...]
    source_output_root: Path | None

    @property
    def mode(self) -> str:
        return self.selection.mode

    @property
    def final_output(self) -> OutputRequest | None:
        return self.final_request

    @property
    def output_requests(self) -> tuple[OutputRequest, ...]:
        requests: list[OutputRequest] = []
        if self.final_request is not None:
            requests.append(self.final_request)
        requests.extend(self.source_outputs)
        return tuple(requests)

    @property
    def requests(self) -> tuple[OutputRequest, ...]:
        return self.output_requests

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "selection": self.selection.to_dict(),
            "final": None if self.final_request is None else self.final_request.to_dict(),
            "source_outputs": [request.to_dict() for request in self.source_outputs],
            "source_output_root": (
                None if self.source_output_root is None else str(self.source_output_root)
            ),
        }


def resolve_output_selection(project: Project) -> OutputSelection:
    """Read and validate persisted output choices, defaulting to final-only."""
    raw = project.output_settings.get(_OUTPUT_SELECTION_KEY)
    if raw is None:
        return OutputSelection()
    try:
        return OutputSelection.from_mapping(raw)
    except OutputPlanError:
        raise
    except (TypeError, ValueError) as error:
        raise OutputPlanError(f"Invalid persisted output selection: {error}") from error


def set_output_selection(
    project: Project,
    *,
    mode: str | None = None,
    include_final: bool | None = None,
    include_source_outputs: bool | None = None,
) -> OutputSelection:
    """Persist validated output choices through ``Project.output_settings``."""
    current = resolve_output_selection(project)
    if mode is not None:
        selection = OutputSelection.from_mode(mode)
        if include_final is not None and include_final != selection.include_final:
            raise OutputPlanError("Output mode conflicts with include_final")
        if (
            include_source_outputs is not None
            and include_source_outputs != selection.include_source_outputs
        ):
            raise OutputPlanError("Output mode conflicts with include_source_outputs")
    else:
        selection = OutputSelection(
            include_final=current.include_final if include_final is None else include_final,
            include_source_outputs=(
                current.include_source_outputs
                if include_source_outputs is None
                else include_source_outputs
            ),
        )
    previous = deepcopy(project.output_settings)
    project.output_settings[_OUTPUT_SELECTION_KEY] = selection.to_dict()
    try:
        project.validate()
    except (ProjectValidationError, ValueError) as error:
        project.output_settings = previous
        raise OutputPlanError(f"Invalid output selection: {error}") from error
    return selection


def plan_project_outputs(
    project: Project,
    final_destination: Path,
    *,
    mode: str | None = None,
    source_output_root: Path | None = None,
) -> OutputPlan:
    """Plan final and/or independent source outputs without rendering."""
    selection = (
        resolve_output_selection(project) if mode is None else OutputSelection.from_mode(mode)
    )
    final_path: Path | None = None
    if selection.include_final:
        final_path = _destination_path(final_destination, "final output")
    sources = _sources_by_id(project)
    active_blocks = _ordered_active_blocks(project)
    if not active_blocks:
        raise OutputPlanError("Cannot plan outputs for an empty edit")
    source_ids = tuple(_block_source_id(block, sources) for block in active_blocks)
    all_source_paths = tuple(Path(source.path).resolve() for source in sources.values())
    source_paths = tuple(
        Path(sources[source_id].path).resolve() for source_id in _unique(source_ids)
    )

    final_request = None
    if final_path is not None:
        _reject_source_collision(final_path, all_source_paths, "Final output")
        final_request = _final_request(
            selection.mode,
            final_path,
            active_blocks,
            source_ids,
            source_paths,
            project,
        )

    source_requests: tuple[OutputRequest, ...] = ()
    output_root: Path | None = None
    if selection.include_source_outputs:
        if source_output_root is not None and final_path is not None:
            _reject_output_root_collision(final_path, source_output_root)
        source_destination = final_path if final_path is not None else final_destination
        output_root = _source_output_root(
            source_destination if source_output_root is None else source_output_root,
            infer=source_output_root is None,
            final_requested=selection.include_final,
        )
        source_requests = _source_requests(
            project,
            selection.mode,
            output_root,
            sources,
        )
        if final_path is not None and any(
            final_path == request.destination
            or final_path in request.destination.parents
            or request.destination in final_path.parents
            for request in source_requests
        ):
            raise OutputPlanError("Final and source output destinations must not overlap")
    return OutputPlan(selection, final_request, source_requests, output_root)


def active_export_sources(project: Project) -> tuple[SourceReference, ...]:
    """Return only sources referenced by included blocks, in import order."""
    sources = _sources_by_id(project)
    source_ids = {
        _block_source_id(block, sources)
        for block in project.timeline.segment_items
        if not block.deleted
    }
    return tuple(source for source_id, source in sources.items() if source_id in source_ids)


def _sources_by_id(project: Project) -> dict[str, SourceReference]:
    records = tuple(project.sources or (project.source,))
    result: dict[str, SourceReference] = {}
    for source in records:
        if source.source_id in result:
            raise OutputPlanError(f"Duplicate source_id: {source.source_id}")
        result[source.source_id] = source
    return result


def _ordered_active_blocks(project: Project) -> tuple[Segment, ...]:
    timeline = project.timeline
    if timeline.tracks is None:
        blocks = sorted(
            timeline.segment_items,
            key=lambda block: (block.timeline_start_ticks, block.segment_id),
        )
        return tuple(block for block in blocks if not block.deleted)
    ordered: list[Segment] = []
    for track in timeline.tracks:
        ordered.extend(
            sorted(
                (block for block in track.blocks if not block.deleted),
                key=lambda block: (block.timeline_start_ticks, block.segment_id),
            ),
        )
    return tuple(ordered)


def _block_source_id(block: Segment, sources: Mapping[str, SourceReference]) -> str:
    if block.source_id is None:
        if len(sources) == 1:
            return next(iter(sources))
        raise OutputPlanError(f"Active block {block.segment_id} has no source_id")
    if block.source_id not in sources:
        raise OutputPlanError(
            f"Active block {block.segment_id} references unknown source {block.source_id}"
        )
    return block.source_id


def _final_request(
    mode: str,
    destination: Path,
    active_blocks: tuple[Segment, ...],
    source_ids: tuple[str, ...],
    source_paths: tuple[Path, ...],
    project: Project,
) -> OutputRequest:
    timeline = project.timeline
    if timeline.tracks is not None and timeline.timing_mode == ABSOLUTE_TIMING_MODE:
        expected_duration = timeline.final_duration_seconds
    else:
        expected_duration = sum(block.duration_seconds for block in active_blocks)
    identity = OutputIdentity(
        mode=mode,
        output_kind="final",
        track_id=None,
        source_id=None,
        framing=FINAL_FRAMING,
        audio_intent=FINAL_AUDIO_INTENT,
        render_profile="final-composition",
    )
    return OutputRequest(
        identity=identity,
        destination=destination,
        segments=active_blocks,
        expected_duration_seconds=expected_duration,
        source_paths=source_paths,
        source_ids=_unique(source_ids),
    )


def _source_requests(
    project: Project,
    mode: str,
    output_root: Path,
    sources: Mapping[str, SourceReference],
) -> tuple[OutputRequest, ...]:
    groups = _ordered_source_groups(project, sources)
    if not groups:
        raise OutputPlanError("Cannot plan outputs for an empty edit")
    source_paths = tuple(Path(source.path).resolve() for source in sources.values())
    track_names = _NameAllocator(source_paths)
    track_name_by_id: dict[str, str] = {}
    source_names_by_track: dict[str, _NameAllocator] = {}
    requests: list[OutputRequest] = []
    for track_id, source_id, segments in groups:
        track_name = track_name_by_id.get(track_id)
        if track_name is None:
            track_name = track_names.allocate(
                output_root,
                _safe_component(track_id, "track"),
                track_id,
            )
            track_name_by_id[track_id] = track_name
        source_names = source_names_by_track.setdefault(
            track_id,
            _NameAllocator(source_paths),
        )
        source_name = _source_filename(sources[source_id])
        filename = source_names.allocate(
            output_root / track_name,
            source_name,
            source_id,
        )
        destination = (output_root / track_name / filename).resolve()
        _reject_source_collision(destination, source_paths, "Source output")
        identity = OutputIdentity(
            mode=mode,
            output_kind="source",
            track_id=track_id,
            source_id=source_id,
            framing=SOURCE_FRAMING,
            audio_intent=SOURCE_AUDIO_INTENT,
            render_profile="standalone-source",
        )
        requests.append(
            OutputRequest(
                identity=identity,
                destination=destination,
                segments=segments,
                expected_duration_seconds=sum(segment.duration_seconds for segment in segments),
                source_paths=(Path(sources[source_id].path).resolve(),),
                source_ids=(source_id,),
            ),
        )
    return tuple(requests)


def _ordered_source_groups(
    project: Project,
    sources: Mapping[str, SourceReference],
) -> tuple[tuple[str, str, tuple[Segment, ...]], ...]:
    timeline = project.timeline
    track_items: tuple[tuple[str, tuple[Segment, ...]], ...]
    if timeline.tracks is None:
        track_items = (("track-1", tuple(timeline.segment_items)),)
    else:
        track_items = tuple((track.track_id, track.blocks) for track in timeline.tracks)
    groups: list[tuple[str, str, tuple[Segment, ...]]] = []
    for track_id, blocks in track_items:
        by_source: dict[str, list[Segment]] = {}
        first_position: dict[str, tuple[int, str]] = {}
        for block in sorted(
            (item for item in blocks if not item.deleted),
            key=lambda item: (item.timeline_start_ticks, item.segment_id),
        ):
            source_id = _block_source_id(block, sources)
            by_source.setdefault(source_id, []).append(block)
            first_position.setdefault(
                source_id,
                (block.timeline_start_ticks, block.segment_id),
            )
        for source_id in sorted(
            by_source,
            key=lambda item: (first_position[item], item),
        ):
            groups.append((track_id, source_id, tuple(by_source[source_id])))
    return tuple(groups)


def _source_output_root(
    destination: Path,
    *,
    infer: bool,
    final_requested: bool,
) -> Path:
    if not isinstance(destination, Path):
        raise OutputPlanError("source output root must be a path")
    path = destination.expanduser().resolve()
    if not infer:
        if path.exists() and not path.is_dir():
            raise OutputPlanError("source output root must be a directory path")
        return path
    if path.exists() and path.is_dir():
        return path
    if path.suffix or final_requested:
        stem = path.stem if path.suffix else path.name
        inferred = path.parent / f"{stem}-sources"
    elif path.exists():
        inferred = path.parent / f"{path.name}-sources"
    else:
        return path
    if inferred.exists() and not inferred.is_dir():
        raise OutputPlanError("source output root must be a directory path")
    return inferred


def _destination_path(value: Path, label: str) -> Path:
    if not isinstance(value, Path):
        raise OutputPlanError(f"{label} must be a path")
    path = value.expanduser().resolve()
    if path.exists() and path.is_dir():
        raise OutputPlanError(f"{label} must be a file path")
    return path


def _reject_output_root_collision(final_destination: Path, source_output_root: Path) -> None:
    final_path = final_destination.expanduser().resolve()
    output_root = source_output_root.expanduser().resolve()
    try:
        output_root.relative_to(final_path)
    except ValueError:
        return
    raise OutputPlanError(
        "Source output root must not be equal to or nested under final output",
    )


def _reject_source_collision(destination: Path, source_paths: tuple[Path, ...], label: str) -> None:
    for source_path in source_paths:
        if _paths_alias(destination, source_path):
            raise OutputPlanError(f"{label} would overwrite source {destination.name}")


def _paths_alias(destination: Path, source_path: Path) -> bool:
    try:
        if destination.resolve() == source_path.resolve():
            return True
        return destination.samefile(source_path)
    except FileNotFoundError:
        return False
    except OSError as error:
        detail = error.strerror or type(error).__name__
        raise OutputPlanError(
            f"Could not verify source preservation for {source_path.name}: {detail}",
        ) from error


def _source_filename(source: SourceReference) -> str:
    original = Path(source.path).name
    stem = Path(original).stem
    return f"{_safe_component(stem, 'source')}.mp4"


def _safe_component(value: str, fallback: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).strip()
    sanitized = _SAFE_COMPONENT.sub("_", normalized).strip(" .")
    if not sanitized or sanitized in {".", ".."}:
        return fallback
    return sanitized[:120]


def _stable_suffix(value: str) -> str:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
    return f"{_safe_component(value, 'item')}-{digest[:8]}"


def _unique(values: tuple[str, ...]) -> tuple[str, ...]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return tuple(result)


class _NameAllocator:
    def __init__(self, source_paths: tuple[Path, ...]) -> None:
        self._source_paths = tuple(dict.fromkeys(path.resolve() for path in source_paths))
        self._allocated: dict[Path, set[str]] = {}

    def allocate(self, parent: Path, base_name: str, stable_id: str) -> str:
        names = self._allocated.setdefault(parent.resolve(), set())
        candidate = base_name
        if candidate in names or self._aliases_source(parent, candidate):
            candidate = self._with_stable_suffix(base_name, stable_id)
        if (parent / candidate).resolve() in self._source_paths:
            candidate = self._with_stable_suffix(base_name, stable_id)
        index = 2
        while candidate in names or self._aliases_source(parent, candidate):
            candidate = self._with_stable_suffix(base_name, stable_id, index)
            index += 1
        names.add(candidate)
        return candidate

    def _aliases_source(self, parent: Path, candidate: str) -> bool:
        destination = parent / candidate
        return any(_paths_alias(destination, source_path) for source_path in self._source_paths)

    @staticmethod
    def _with_stable_suffix(base_name: str, stable_id: str, index: int | None = None) -> str:
        path = Path(base_name)
        suffix = path.suffix
        stem = path.name[: -len(suffix)] if suffix else path.name
        stable = _stable_suffix(stable_id)
        if index is not None:
            stable = f"{stable}-{index}"
        return f"{stem}-{stable}{suffix}"


__all__ = [
    "active_export_sources",
    "COMBINED",
    "COMBINED_OUTPUT_MODE",
    "FINAL_AUDIO_INTENT",
    "FINAL_FRAMING",
    "FINAL_ONLY",
    "FINAL_ONLY_OUTPUT_MODE",
    "OutputIdentity",
    "OutputPlan",
    "OutputPlanError",
    "OutputRequest",
    "OutputResult",
    "OutputSelection",
    "SOURCE_AUDIO_INTENT",
    "SOURCE_FRAMING",
    "SOURCE_ONLY",
    "SOURCE_ONLY_OUTPUT_MODE",
    "plan_project_outputs",
    "resolve_output_selection",
    "set_output_selection",
]
