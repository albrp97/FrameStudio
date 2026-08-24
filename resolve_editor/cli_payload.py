from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from .audio import audio_decision_is_stale
from .cli_types import CLI_EXIT_INVALID, CliError
from .model import Project, Segment, SourceReference


def display_path(path: str | Path, include_paths: bool) -> str:
    value = Path(path).expanduser()
    return str(value.resolve()) if include_paths else value.name


def source_payload(
    source: SourceReference,
    *,
    include_paths: bool,
    audio: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    status = source.status()
    payload = {
        "source_id": source.source_id,
        "path": display_path(source.path, include_paths),
        "uri": (source.uri if include_paths else Path(source.path).name),
        "path_redacted": not include_paths,
        "size_bytes": source.size_bytes,
        "modified_time_ns": source.modified_time_ns,
        "metadata": dict(source.metadata),
        "status": {
            "available": status.available,
            "changed": status.changed,
            "reason": status.reason,
        },
    }
    if audio is not None:
        payload["audio"] = dict(audio)
    return payload


def segment_payload(segment: Segment) -> dict[str, Any]:
    return {
        "segment_id": segment.segment_id,
        "start_seconds": segment.start_seconds,
        "end_seconds": segment.end_seconds,
        "duration_seconds": segment.duration_seconds,
        "deleted": segment.deleted,
        "source_id": segment.source_id,
        "timeline_start_seconds": segment.timeline_start_seconds,
        "timeline_end_seconds": segment.timeline_end_seconds,
        "state": dict(segment.state),
        "block_id": segment.block_id,
        "color_index": segment.color_index,
        "visual_transform": segment.visual_transform.to_dict(),
        "triplicate": (None if segment.triplicate is None else segment.triplicate.to_dict()),
    }


def project_payload(
    project: Project,
    project_path: Path | None = None,
    *,
    include_paths: bool = False,
) -> dict[str, Any]:
    project.validate()
    timeline = project.segment_timeline
    if timeline is None:
        raise CliError(
            "invalid_project",
            "Project segment timeline is required",
            exit_code=CLI_EXIT_INVALID,
        )
    timeline_payload: dict[str, Any] = {
        "source_duration_seconds": timeline.source_duration_seconds,
        "edited_duration_seconds": timeline.edited_duration_seconds,
        "playhead_seconds": project.playhead_seconds,
    }
    if timeline.mixed_source:
        timeline_payload.update(
            {
                "duration_seconds": timeline.timeline_duration_seconds,
                "timebase": timeline.timebase,
                "frame_rate": timeline.frame_rate,
                "ripple": timeline.ripple,
                "blocks": [segment_payload(segment) for segment in timeline.segment_items],
            }
        )
    else:
        timeline_payload["duration_seconds"] = timeline.timeline_duration_seconds
        timeline_payload["segments"] = [
            segment_payload(segment) for segment in timeline.segment_items
        ]
    sources = project.sources or (project.source,)
    audio_decisions: dict[str, dict[str, Any]] = {}
    for source in sources:
        settings = project.source_audio_settings(source.source_id)
        if audio_decision_is_stale(source, settings):
            settings["status"] = "stale"
            settings["diagnostic"] = "Source changed since audio analysis"
        audio_decisions[source.source_id] = settings
    return {
        "project_id": project.project_id,
        "schema_version": project.schema_version,
        "project_path": (
            None if project_path is None else display_path(project_path, include_paths)
        ),
        "source": source_payload(
            project.source,
            include_paths=include_paths,
            audio=audio_decisions.get(project.source.source_id),
        ),
        "sources": [
            source_payload(
                source,
                include_paths=include_paths,
                audio=audio_decisions.get(source.source_id),
            )
            for source in sources
        ],
        "timeline": timeline_payload,
        "source_settings": dict(project.source_settings),
        "audio_decisions": audio_decisions,
        "output_settings": dict(project.output_settings),
        "export": {
            "exportable": timeline.edited_duration_seconds > 0,
            "active_segment_count": sum(not segment.deleted for segment in timeline.segment_items),
            "deleted_segment_count": sum(segment.deleted for segment in timeline.segment_items),
        },
    }
