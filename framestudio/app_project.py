from __future__ import annotations

import threading
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

from .app_helpers import _metadata_float, editing_is_locked, format_audio_decisions
from .export import OutputPolicy, resolve_output_policy
from .ffmpeg_playback import FfmpegComposedPlaybackBackend, FfmpegPlaybackBackend
from .media import MediaProbeError
from .model import Project, ProjectValidationError, Segment, SourceReference
from .operations import (
    analyze_project_audio,
    create_project_from_source,
    create_project_from_sources,
    ensure_project_audio_analysis,
)
from .persistence import ProjectPersistenceError, load_project, save_project
from .playback import PlaybackController, PlaybackState


def _schedule_on_main(glib: Any | None, callback: Callable[..., bool], *args: Any) -> None:
    if glib is None:
        callback(*args)
        return
    glib.idle_add(callback, *args)


def _source_load_progress(
    window: Any,
    generation: int,
    index: int,
    total: int,
    phase: str,
) -> bool:
    if generation != getattr(window, "_source_load_generation", generation):
        return False
    if phase == "probe":
        percentage = round(index * 50 / total)
    else:
        percentage = 50 + round(index * 50 / total)
    window._set_status(f"Loading clip {index}/{total} ({percentage}%)")
    return False


def _build_source_project(
    selected_paths: tuple[Path, ...],
    progress_callback: Callable[[int, int, str], None] | None = None,
) -> Project:
    if len(selected_paths) == 1:
        return create_project_from_source(
            selected_paths[0],
            progress_callback=progress_callback,
        )
    return create_project_from_sources(
        selected_paths,
        progress_callback=progress_callback,
    )


def _load_source_blocking(window: Any, selected_paths: tuple[Path, ...]) -> bool:
    try:
        project = _build_source_project(selected_paths)
        analyze_project_audio(project)
    except (MediaProbeError, ProjectValidationError) as error:
        window._show_error(str(error))
        return False
    attach_project(window, project, None)
    names = ", ".join(path.name for path in selected_paths)
    window._set_status(f"Loaded source video(s): {names} (project not saved)")
    return False


def _load_source_worker(
    window: Any,
    selected_paths: tuple[Path, ...],
    generation: int,
    glib: Any,
) -> None:
    total = len(selected_paths)

    def report_progress(index: int, _phase_total: int, phase: str) -> None:
        _schedule_on_main(
            glib,
            _source_load_progress,
            window,
            generation,
            index,
            total,
            phase,
        )

    try:
        project = _build_source_project(
            selected_paths,
            progress_callback=report_progress,
        )
        analyze_project_audio(
            project,
            progress_callback=report_progress,
        )
    except (MediaProbeError, ProjectValidationError, ValueError) as error:
        _schedule_on_main(
            glib,
            _finish_source_load,
            window,
            generation,
            selected_paths,
            None,
            str(error),
        )
        return
    _schedule_on_main(
        glib,
        _finish_source_load,
        window,
        generation,
        selected_paths,
        project,
        None,
    )


def _finish_source_load(
    window: Any,
    generation: int,
    selected_paths: tuple[Path, ...],
    project: Project | None,
    error_message: str | None,
) -> bool:
    if generation != getattr(window, "_source_load_generation", generation):
        return False
    try:
        if project is None:
            window._show_error(error_message or "Source loading failed")
            return False
        try:
            attach_project(window, project, None)
        except (MediaProbeError, ProjectValidationError, ValueError) as error:
            window._show_error(str(error))
            return False
        names = ", ".join(path.name for path in selected_paths)
        window._set_status(f"Loaded source video(s): {names} (project not saved)")
        return False
    finally:
        window._source_load_in_progress = False
        window._update_segment_controls()


def _create_backend_callbacks(window: Any) -> tuple[Any, Any, Any, Any]:
    generation = int(getattr(window, "_playback_generation", 0)) + 1
    window._playback_generation = generation

    def is_current() -> bool:
        return generation == getattr(window, "_playback_generation", generation)

    def on_frame(frame) -> None:
        if is_current():
            window._on_frame(frame, generation)

    def on_error(message: str) -> None:
        if is_current():
            window._on_backend_error(message, generation)

    def on_end() -> None:
        if is_current():
            window._on_backend_end(generation)

    def on_warning(message: str) -> None:
        if is_current():
            window._on_backend_warning(message, generation)

    return on_frame, on_error, on_end, on_warning


def _create_composed_preview_backend(
    sources: Sequence[SourceReference],
    active_segments: Sequence[Segment],
    policy: OutputPolicy,
    frame_rate: float,
    duration_seconds: float,
    callbacks: tuple[Any, Any, Any, Any],
    audio_decisions: Mapping[str, Any],
) -> FfmpegComposedPlaybackBackend:
    on_frame, on_error, on_end, on_warning = callbacks
    return FfmpegComposedPlaybackBackend(
        tuple((source.source_id, Path(source.path)) for source in sources),
        active_segments,
        policy.width,
        policy.height,
        frame_rate,
        duration_seconds,
        on_frame,
        on_error,
        on_end,
        audio_decisions=audio_decisions,
        on_warning=on_warning,
    )


def save_to(window: Any, path: Path) -> None:
    if editing_is_locked(window):
        return
    if window.project is None:
        return
    if window.controller is not None:
        if window.segment_timeline is not None:
            window.project.set_playhead(
                window.segment_timeline.edited_to_timeline_position(
                    window.controller.snapshot().position_seconds,
                )
            )
        else:
            window.project.set_playhead(window.controller.snapshot().position_seconds)
    try:
        destination = save_project(window.project, path)
    except ProjectPersistenceError as error:
        window._show_error(str(error))
        return
    window.project_path = destination
    window._set_status(f"Saved editor project: {destination.name}")


def load_source(
    window: Any,
    paths: Path | Sequence[Path],
    glib: Any | None = None,
) -> bool:
    if editing_is_locked(window):
        return False
    selected_paths = (
        (Path(paths),) if isinstance(paths, Path) else tuple(Path(path) for path in paths)
    )
    if not selected_paths:
        window._show_error("At least one source is required")
        return False
    if getattr(window, "_source_load_in_progress", False):
        window._set_status("Source loading is already in progress")
        return False
    if glib is None:
        return _load_source_blocking(window, selected_paths)
    generation = int(getattr(window, "_source_load_generation", 0)) + 1
    window._source_load_generation = generation
    window._source_load_in_progress = True
    window._set_status(f"Loading clip 1/{len(selected_paths)} (0%)")
    window._update_segment_controls()
    worker = threading.Thread(
        target=_load_source_worker,
        args=(window, selected_paths, generation, glib),
        name="framestudio-editor-source-loader",
        daemon=True,
    )
    try:
        worker.start()
    except RuntimeError as error:
        window._source_load_in_progress = False
        window._update_segment_controls()
        window._show_error(f"Could not start source loading: {error}")
    return False


def load_project_path(window: Any, path: Path) -> bool:
    if editing_is_locked(window):
        return False
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
        ensure_project_audio_analysis(project)
    except ProjectValidationError as error:
        window._show_error(str(error))
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
    on_frame, on_error, on_end, on_warning = _create_backend_callbacks(window)
    sources = project.sources or (project.source,)
    policy = resolve_output_policy([source.metadata for source in sources])
    audio_decisions = ensure_project_audio_analysis(project)
    window.project = project
    window.project_path = project_path
    window.source_frame_rate = _metadata_float(
        {"frame_rate": policy.frame_rate},
        "frame_rate",
    )
    window.segment_timeline = project.segment_timeline
    if window.segment_timeline is None:
        raise ProjectValidationError("Project segment timeline is required")
    active_segments = window.segment_timeline.active_blocks()
    if not active_segments:
        raise ProjectValidationError("Cannot preview an empty edit")
    segments = window.segment_timeline.segment_items
    use_composed_preview = (
        window.segment_timeline.mixed_source
        or window.segment_timeline.has_explicit_timeline
        or any(segment.deleted for segment in segments)
        or any(segment.has_visual_modifications for segment in active_segments)
    )
    window.selected_segment_id = segments[0].segment_id
    window.selected_segment_ids = (window.selected_segment_id,)
    window.timeline_canvas.set_timeline(
        window.segment_timeline,
        window.selected_segment_id,
        window.selected_segment_ids,
    )
    window.timeline_canvas.set_sensitive(True)
    window.audio_status_label.set_text(format_audio_decisions(project))
    if use_composed_preview:
        window.backend = _create_composed_preview_backend(
            sources,
            active_segments,
            policy,
            window.source_frame_rate,
            window.segment_timeline.edited_duration_seconds,
            (on_frame, on_error, on_end, on_warning),
            audio_decisions,
        )
    else:
        window.backend = FfmpegPlaybackBackend(
            Path(project.source.path),
            policy.width,
            policy.height,
            window.source_frame_rate,
            window.segment_timeline.edited_duration_seconds,
            on_frame,
            on_error,
            on_end,
            audio_decision=audio_decisions[project.source.source_id],
            on_warning=on_warning,
        )
    initial_position = window.segment_timeline.timeline_to_edited_position(
        project.playhead_seconds,
    )
    window.controller = PlaybackController(
        window.backend,
        window.segment_timeline.edited_duration_seconds,
        initial_position,
    )
    window._update_selected_clip_label()
    if not window.controller.seek(initial_position):
        raise MediaProbeError(window.controller.snapshot().error or "Could not show source preview")
    window._update_playback_controls()
    window._update_segment_controls()


def refresh_playback_backend(window: Any) -> None:
    if window.project is None or window.segment_timeline is None:
        return
    requires_composed_preview = (
        window.segment_timeline.mixed_source
        or window.segment_timeline.has_explicit_timeline
        or any(segment.deleted for segment in window.segment_timeline.segment_items)
        or any(
            segment.has_visual_modifications for segment in window.segment_timeline.active_blocks()
        )
    )
    if not requires_composed_preview and not isinstance(
        window.backend, FfmpegComposedPlaybackBackend
    ):
        return
    previous_snapshot = None if window.controller is None else window.controller.snapshot()
    timeline_position = 0.0 if window.project is None else window.project.playhead_seconds
    position = window.segment_timeline.timeline_to_edited_position(timeline_position)
    was_playing = previous_snapshot is not None and previous_snapshot.state == PlaybackState.PLAYING
    sources = window.project.sources or (window.project.source,)
    policy = resolve_output_policy([source.metadata for source in sources])
    audio_decisions = ensure_project_audio_analysis(window.project)
    window.audio_status_label.set_text(format_audio_decisions(window.project))
    window._stop_backend()
    on_frame, on_error, on_end, on_warning = _create_backend_callbacks(window)
    active_segments = window.segment_timeline.active_blocks()
    if not active_segments:
        window._show_error("Cannot preview an empty edit")
        window._update_playback_controls()
        return
    if requires_composed_preview:
        composed_sources = (
            sources if window.segment_timeline.mixed_source else (window.project.source,)
        )
        window.backend = _create_composed_preview_backend(
            composed_sources,
            active_segments,
            policy,
            window.source_frame_rate,
            window.segment_timeline.edited_duration_seconds,
            (on_frame, on_error, on_end, on_warning),
            audio_decisions,
        )
    else:
        window.backend = FfmpegPlaybackBackend(
            Path(window.project.source.path),
            policy.width,
            policy.height,
            window.source_frame_rate,
            window.segment_timeline.edited_duration_seconds,
            on_frame,
            on_error,
            on_end,
            audio_decision=audio_decisions[window.project.source.source_id],
            on_warning=on_warning,
        )
    window.controller = PlaybackController(
        window.backend,
        window.segment_timeline.edited_duration_seconds,
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
