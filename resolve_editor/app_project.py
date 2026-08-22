from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any

from .app_helpers import _metadata_float
from .export import resolve_output_policy
from .ffmpeg_playback import FfmpegComposedPlaybackBackend, FfmpegPlaybackBackend
from .media import MediaProbeError
from .model import Project, ProjectValidationError
from .operations import (
    create_project_from_source,
    create_project_from_sources,
)
from .persistence import ProjectPersistenceError, load_project, save_project
from .playback import PlaybackController, PlaybackState
from .ui import format_duration


def save_to(window: Any, path: Path) -> None:
    if window.project is None:
        return
    if window.controller is not None:
        window.project.set_playhead(window.controller.snapshot().position_seconds)
    try:
        destination = save_project(window.project, path)
    except ProjectPersistenceError as error:
        window._show_error(str(error))
        return
    window.project_path = destination
    window._set_status(f"Saved editor project: {destination.name}")


def load_source(window: Any, paths: Path | Sequence[Path]) -> bool:
    selected_paths = (
        (Path(paths),) if isinstance(paths, Path) else tuple(Path(path) for path in paths)
    )
    try:
        if len(selected_paths) == 1:
            project = create_project_from_source(selected_paths[0])
        else:
            project = create_project_from_sources(selected_paths)
    except (MediaProbeError, ProjectValidationError) as error:
        window._show_error(str(error))
        return False
    attach_project(window, project, None)
    names = ", ".join(path.name for path in selected_paths)
    window._set_status(f"Loaded source video(s): {names} (project not saved)")
    return False


def load_project_path(window: Any, path: Path) -> bool:
    try:
        project = load_project(path)
    except ProjectPersistenceError as error:
        window._show_error(str(error))
        return False
    for source in project.sources or (project.source,):
        source_status = source.status()
        if not source_status.available:
            window._show_error(
                f"{source.source_id}: {source_status.reason or 'Source is unavailable'}"
            )
            return False
        if source_status.changed:
            window._show_error(
                f"{source.source_id}: {source_status.reason or 'Source has changed'}"
            )
            return False
    try:
        attach_project(window, project, path)
    except (MediaProbeError, ProjectValidationError, ValueError) as error:
        window._show_error(str(error))
        return False
    window._set_status(f"Reopened editor project: {path.name}")
    return False


def attach_project(
    window: Any,
    project: Project,
    project_path: Path | None,
) -> None:
    window._stop_backend()
    sources = project.sources or (project.source,)
    policy = resolve_output_policy([source.metadata for source in sources])
    window.project = project
    window.project_path = project_path
    window.source_frame_rate = _metadata_float(
        {"frame_rate": policy.frame_rate},
        "frame_rate",
    )
    window.segment_timeline = project.segment_timeline
    if window.segment_timeline is None:
        raise ProjectValidationError("Project segment timeline is required")
    segments = window.segment_timeline.segment_items
    window.selected_segment_id = segments[0].segment_id
    window.selected_segment_ids = (window.selected_segment_id,)
    window.timeline_canvas.set_timeline(
        window.segment_timeline,
        window.selected_segment_id,
        window.selected_segment_ids,
    )
    window.timeline_canvas.set_sensitive(True)
    if window.segment_timeline.mixed_source:
        window.backend = FfmpegComposedPlaybackBackend(
            tuple((source.source_id, Path(source.path)) for source in sources),
            segments,
            policy.width,
            policy.height,
            window.source_frame_rate,
            project.duration_seconds,
            window._on_frame,
            window._on_backend_error,
            window._on_backend_end,
        )
    elif window.segment_timeline.has_explicit_timeline:
        window.backend = FfmpegComposedPlaybackBackend(
            ((project.source.source_id, Path(project.source.path)),),
            segments,
            policy.width,
            policy.height,
            window.source_frame_rate,
            project.duration_seconds,
            window._on_frame,
            window._on_backend_error,
            window._on_backend_end,
        )
    else:
        window.backend = FfmpegPlaybackBackend(
            Path(project.source.path),
            policy.width,
            policy.height,
            window.source_frame_rate,
            project.duration_seconds,
            window._on_frame,
            window._on_backend_error,
            window._on_backend_end,
        )
    window.controller = PlaybackController(
        window.backend,
        project.duration_seconds,
        project.playhead_seconds,
    )
    window.position_label.set_text(format_duration(project.playhead_seconds))
    window.timeline_canvas.set_playhead(project.playhead_seconds)
    window._update_selected_clip_label()
    if not window.controller.seek(project.playhead_seconds):
        raise MediaProbeError(window.controller.snapshot().error or "Could not show source preview")
    window._update_playback_controls()
    window._update_segment_controls()


def refresh_playback_backend(window: Any) -> None:
    if window.project is None or window.segment_timeline is None:
        return
    if (
        not window.segment_timeline.mixed_source
        and not window.segment_timeline.has_explicit_timeline
    ):
        return
    previous_snapshot = None if window.controller is None else window.controller.snapshot()
    position = 0.0 if previous_snapshot is None else previous_snapshot.position_seconds
    was_playing = previous_snapshot is not None and previous_snapshot.state == PlaybackState.PLAYING
    sources = window.project.sources or (window.project.source,)
    policy = resolve_output_policy([source.metadata for source in sources])
    window._stop_backend()
    if window.segment_timeline.mixed_source:
        window.backend = FfmpegComposedPlaybackBackend(
            tuple((source.source_id, Path(source.path)) for source in sources),
            window.segment_timeline.segment_items,
            policy.width,
            policy.height,
            window.source_frame_rate,
            window.project.duration_seconds,
            window._on_frame,
            window._on_backend_error,
            window._on_backend_end,
        )
    else:
        window.backend = FfmpegComposedPlaybackBackend(
            ((window.project.source.source_id, Path(window.project.source.path)),),
            window.segment_timeline.segment_items,
            policy.width,
            policy.height,
            window.source_frame_rate,
            window.project.duration_seconds,
            window._on_frame,
            window._on_backend_error,
            window._on_backend_end,
        )
    window.controller = PlaybackController(
        window.backend,
        window.project.duration_seconds,
        position,
    )
    if not window.controller.seek(position):
        window._show_error(window.controller.snapshot().error or "Could not refresh source preview")
        return
    if was_playing and not window.controller.play():
        window._show_error(window.controller.snapshot().error or "Could not resume source preview")


def refresh_timeline(window: Any, selected_segment_id: str | None = None) -> None:
    if window.segment_timeline is None:
        return
    if selected_segment_id is None:
        selected_segment_id = window.selected_segment_id
    segments = window.segment_timeline.segment_items
    if selected_segment_id is None and segments:
        selected_segment_id = segments[0].segment_id
    window.selected_segment_id = selected_segment_id
    if selected_segment_id is None:
        window.selected_segment_ids = ()
    else:
        window.selected_segment_ids = tuple(
            segment_id
            for segment_id in window.selected_segment_ids
            if any(segment.segment_id == segment_id for segment in segments)
        )
        if not window.selected_segment_ids:
            window.selected_segment_ids = (selected_segment_id,)
    window.timeline_canvas.set_timeline(
        window.segment_timeline,
        window.selected_segment_id,
        window.selected_segment_ids,
    )
    refresh_playback_backend(window)
    window._update_selected_clip_label()
    window._update_segment_controls()
