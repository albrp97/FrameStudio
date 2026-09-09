from __future__ import annotations

import math
import threading
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

from .app_helpers import (
    MAX_SOURCES_PER_PROJECT,
    _metadata_float,
    editing_is_locked,
    format_audio_decisions,
    validate_source_selection,
)
from .audio import (
    AUDIO_POLICY_VERSION,
    AudioAnalysisCancelled,
    AudioDecision,
    analyze_source_audio,
    audio_decision_is_stale,
    pending_audio_decision,
)
from .export import OutputPolicy, resolve_output_policy
from .export_session import find_export_sessions_for_sources
from .ffmpeg_playback import FfmpegComposedPlaybackBackend, FfmpegPlaybackBackend
from .media import MediaProbeError
from .model import Project, ProjectValidationError, Segment, SourceReference
from .operations import (
    analyze_project_audio,
    create_project_from_source,
    create_project_from_sources,
    ensure_project_audio_analysis,
)
from .persistence import (
    ProjectPersistenceError,
    autosave_exists,
    load_project,
    save_autosave,
    save_project,
)
from .persistence import (
    load_autosave as load_autosave_project,
)
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
    _phase: str,
) -> bool:
    if generation != getattr(window, "_source_load_generation", generation):
        return False
    percentage = round(index * 100 / total)
    action = "Adding" if getattr(window, "project", None) is not None else "Loading"
    window._set_status(f"{action} clip {index}/{total} ({percentage}%)")
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
        current_project = getattr(window, "project", None)
        if current_project is None:
            analyze_project_audio(project)
            status_prefix = "Loaded"
            project_path = None
        else:
            current_project.append_sources(project.sources or (project.source,))
            ensure_project_audio_analysis(current_project)
            project = current_project
            status_prefix = "Added"
            project_path = getattr(window, "project_path", None)
    except (MediaProbeError, ProjectValidationError) as error:
        window._show_error(str(error))
        return False
    attach_project(window, project, project_path)
    names = ", ".join(path.name for path in selected_paths)
    window._set_status(f"{status_prefix} source video(s): {names} (project not saved)")
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
        glib,
    )


def _finish_source_load(
    window: Any,
    generation: int,
    selected_paths: tuple[Path, ...],
    project: Project | None,
    error_message: str | None,
    glib: Any | None = None,
) -> bool:
    if generation != getattr(window, "_source_load_generation", generation):
        return False
    should_analyze = False
    try:
        if project is None:
            window._show_error(error_message or "Source loading failed")
            return False
        try:
            current_project = getattr(window, "project", None)
            if current_project is None:
                attach_project(window, project, None)
                status_prefix = "Loaded"
            else:
                current_project.append_sources(project.sources or (project.source,))
                project = current_project
                attach_project(
                    window,
                    project,
                    getattr(window, "project_path", None),
                )
                status_prefix = "Added"
        except (MediaProbeError, ProjectValidationError, ValueError) as error:
            window._show_error(str(error))
            return False
        names = ", ".join(path.name for path in selected_paths)
        window._set_status(f"{status_prefix} source video(s): {names} (project not saved)")
        should_analyze = glib is not None
        return False
    finally:
        window._source_load_in_progress = False
        window._update_segment_controls()
        if should_analyze and project is not None:
            _start_audio_analysis(window, project, glib)


def _preview_audio_decisions(project: Project) -> dict[str, dict[str, Any]]:
    decisions: dict[str, dict[str, Any]] = {}
    for source in project.sources or (project.source,):
        settings = project.source_audio_settings(source.source_id)
        if _audio_decision_requires_analysis(source, settings):
            settings = pending_audio_decision(source).to_dict()
        decisions[source.source_id] = settings
    return decisions


def _audio_decision_requires_analysis(
    source: SourceReference,
    settings: Mapping[str, Any],
) -> bool:
    return (
        settings.get("status") not in {"ready", "silent", "unsupported", "failed", "not-applicable"}
        or settings.get("policy_version") != AUDIO_POLICY_VERSION
        or audio_decision_is_stale(source, settings)
    )


def _audio_sources_needing_analysis(project: Project) -> tuple[SourceReference, ...]:
    sources: list[SourceReference] = []
    for source in project.sources or (project.source,):
        settings = project.source_audio_settings(source.source_id)
        if _audio_decision_requires_analysis(source, settings):
            sources.append(source)
    return tuple(sources)


def _failed_audio_decision(source: SourceReference, error: Exception) -> AudioDecision:
    pending = pending_audio_decision(source)
    return AudioDecision(
        status="failed",
        gain_db=0.0,
        policy_version=pending.policy_version,
        measurements=None,
        source_fingerprint=pending.source_fingerprint,
        audio_metadata=pending.audio_metadata,
        diagnostic=f"Audio analysis failed: {error}",
    )


def _record_rejected_audio_source(window: Any, source_id: str) -> None:
    rejected = getattr(window, "_audio_analysis_rejected_source_ids", None)
    if rejected is None:
        rejected = set()
        window._audio_analysis_rejected_source_ids = rejected
    rejected.add(source_id)


def _audio_analysis_worker(
    window: Any,
    project: Project,
    generation: int,
    sources: Sequence[SourceReference],
    glib: Any,
    cancel_event: threading.Event | None = None,
) -> None:
    total = len(sources)
    for index, source in enumerate(sources, start=1):
        if cancel_event is not None and cancel_event.is_set():
            return
        analysis_lock = getattr(window, "_audio_analysis_worker_lock", None)
        if analysis_lock is None:
            analysis_lock = threading.Lock()
            window._audio_analysis_worker_lock = analysis_lock
        with analysis_lock:
            if cancel_event is not None and cancel_event.is_set():
                return
            try:
                decision = analyze_source_audio(source, cancel_event=cancel_event)
            except AudioAnalysisCancelled:
                return
            except (OSError, ValueError) as error:
                decision = _failed_audio_decision(source, error)
        if cancel_event is not None and cancel_event.is_set():
            return
        _schedule_on_main(
            glib,
            _finish_source_audio_analysis,
            window,
            project,
            generation,
            source,
            decision,
            index,
            total,
        )
    if cancel_event is not None and cancel_event.is_set():
        return
    _schedule_on_main(
        glib,
        _finish_audio_analysis,
        window,
        project,
        generation,
    )


def _finish_source_audio_analysis(
    window: Any,
    project: Project,
    generation: int,
    source: SourceReference,
    decision: AudioDecision,
    index: int,
    total: int,
) -> bool:
    if (
        generation != getattr(window, "_audio_analysis_generation", generation)
        or window.project is not project
    ):
        return False
    try:
        current_source = project.source_by_id(source.source_id)
    except ProjectValidationError:
        _record_rejected_audio_source(window, source.source_id)
        return False
    if current_source != source:
        _record_rejected_audio_source(window, source.source_id)
        return False
    source_status = current_source.status()
    settings = decision.to_dict()
    if (
        not source_status.available
        or source_status.changed
        or audio_decision_is_stale(current_source, settings)
    ):
        _record_rejected_audio_source(window, source.source_id)
        return False
    rejected = getattr(window, "_audio_analysis_rejected_source_ids", None)
    if rejected is not None:
        rejected.discard(source.source_id)
    project.set_source_audio_settings(source.source_id, settings)
    window.audio_status_label.set_text(
        format_audio_decisions(
            project,
            getattr(window, "_audio_analysis_source_ids", ()),
        )
    )
    window._set_status(f"Analyzing audio {index}/{total} ({round(index * 100 / total)}%)")
    return False


def _finish_audio_analysis(
    window: Any,
    project: Project,
    generation: int,
) -> bool:
    if (
        generation != getattr(window, "_audio_analysis_generation", generation)
        or window.project is not project
    ):
        return False
    window._audio_analysis_in_progress = False
    window._audio_analysis_source_ids = ()
    window._audio_analysis_cancel_event = None
    window.audio_status_label.set_text(format_audio_decisions(project))
    has_failures = any(
        project.source_audio_settings(source.source_id).get("status") == "failed"
        for source in project.sources or (project.source,)
    )
    unresolved_sources = _audio_sources_needing_analysis(project)
    rejected_source_ids: set[str] = getattr(
        window,
        "_audio_analysis_rejected_source_ids",
        set(),
    )
    if unresolved_sources or rejected_source_ids:
        has_source_change = any(
            (status := source.status()).changed or not status.available
            for source in unresolved_sources
        )
        if rejected_source_ids or has_source_change:
            status_message = "Audio analysis incomplete: source changed or unavailable"
        else:
            status_message = "Audio analysis incomplete: unresolved source audio"
    elif has_failures:
        status_message = "Audio analysis complete with failures"
    else:
        status_message = "Audio analysis complete"
    window._audio_analysis_rejected_source_ids = set()
    window._set_status(status_message)
    if getattr(window, "audio_preview_enabled", False):
        refresh_playback_backend(window, force=True)
    window._update_segment_controls()
    return False


def _start_audio_analysis(
    window: Any,
    project: Project,
    glib: Any,
) -> bool:
    if getattr(window, "_audio_analysis_in_progress", False):
        _invalidate_audio_analysis(window)
    sources = _audio_sources_needing_analysis(project)
    if not sources:
        window._audio_analysis_in_progress = False
        window._audio_analysis_source_ids = ()
        window._audio_analysis_cancel_event = None
        window._audio_analysis_rejected_source_ids = set()
        return False
    generation = int(getattr(window, "_audio_analysis_generation", 0)) + 1
    window._audio_analysis_generation = generation
    window._audio_analysis_in_progress = True
    window._audio_analysis_source_ids = tuple(source.source_id for source in sources)
    cancel_event = threading.Event()
    window._audio_analysis_cancel_event = cancel_event
    window._audio_analysis_rejected_source_ids = set()
    window.audio_status_label.set_text(
        format_audio_decisions(project, window._audio_analysis_source_ids)
    )
    window._set_status(f"Analyzing audio 0/{len(sources)} (0%)")
    worker = threading.Thread(
        target=_audio_analysis_worker,
        args=(window, project, generation, sources, glib, cancel_event),
        name="framestudio-editor-audio-analyzer",
        daemon=True,
    )
    try:
        worker.start()
    except RuntimeError as error:
        cancel_event.set()
        window._audio_analysis_in_progress = False
        window._audio_analysis_source_ids = ()
        window._audio_analysis_cancel_event = None
        window._audio_analysis_rejected_source_ids = set()
        window.audio_status_label.set_text(format_audio_decisions(project))
        window._show_error(f"Could not start audio analysis: {error}")
    return False


def _invalidate_audio_analysis(window: Any) -> None:
    cancel_event = getattr(window, "_audio_analysis_cancel_event", None)
    if cancel_event is not None:
        cancel_event.set()
    window._audio_analysis_generation = int(getattr(window, "_audio_analysis_generation", 0)) + 1
    window._audio_analysis_in_progress = False
    window._audio_analysis_source_ids = ()
    window._audio_analysis_cancel_event = None
    window._audio_analysis_rejected_source_ids = set()


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
    audio_preview_enabled: bool = False,
) -> FfmpegComposedPlaybackBackend:
    on_frame, on_error, on_end, on_warning = callbacks
    source_ids = {segment.source_id for segment in active_segments if segment.source_id is not None}
    if len(sources) > 1 and source_ids:
        sources = tuple(source for source in sources if source.source_id in source_ids)
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
        audio_preview_enabled=audio_preview_enabled,
        on_warning=on_warning,
    )


def _sync_project_playhead(window: Any) -> None:
    if window.controller is None:
        return
    if window.segment_timeline is not None:
        window.project.set_playhead(
            window.segment_timeline.edited_to_timeline_position(
                window.controller.snapshot().position_seconds,
            )
        )
    else:
        window.project.set_playhead(window.controller.snapshot().position_seconds)


def save_to(window: Any, path: Path) -> None:
    if editing_is_locked(window):
        return
    if window.project is None:
        return
    _sync_project_playhead(window)
    try:
        destination = save_project(window.project, path)
    except ProjectPersistenceError as error:
        window._show_error(str(error))
        return
    window.project_path = destination
    window._set_status(f"Saved editor project: {destination.name}")
    autosave_current_project(window)


def autosave_current_project(window: Any) -> bool:
    if window.project is None:
        return False
    _sync_project_playhead(window)
    try:
        save_autosave(window.project)
    except ProjectPersistenceError as error:
        window._show_error(f"Autosave failed: {error}")
        return False
    return True


def _validate_project_sources(window: Any, project: Project) -> bool:
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
    return True


def _attach_loaded_project(
    window: Any,
    project: Project,
    project_path: Path | None,
    glib: Any | None,
    *,
    preserve_project_path: bool = False,
) -> bool:
    if glib is None:
        try:
            ensure_project_audio_analysis(project)
        except ProjectValidationError as error:
            window._show_error(str(error))
            return False
    previous_project_path = getattr(window, "project_path", None)
    try:
        attach_project(window, project, project_path)
    except (MediaProbeError, ProjectValidationError, ValueError) as error:
        window._show_error(str(error))
        return False
    finally:
        if preserve_project_path:
            window.project_path = previous_project_path
    return True


def recover_autosave(window: Any, glib: Any | None = None) -> bool:
    if editing_is_locked(window):
        return False
    if not autosave_exists():
        window._show_error("No autosaved project is available")
        return False
    try:
        project = load_autosave_project()
    except ProjectPersistenceError as error:
        window._show_error(str(error))
        return False
    if not _validate_project_sources(window, project):
        return False
    if not _attach_loaded_project(
        window,
        project,
        None,
        glib,
        preserve_project_path=True,
    ):
        return False
    window._set_status("Recovered autosaved editor project")
    if glib is not None:
        _start_audio_analysis(window, project, glib)
    return False


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
    current_project = getattr(window, "project", None)
    existing_source_count = 0 if current_project is None else len(current_project.sources)
    try:
        selected_paths = validate_source_selection(
            selected_paths,
            max_sources=MAX_SOURCES_PER_PROJECT,
            existing_source_count=existing_source_count,
        )
    except ValueError as error:
        window._show_error(str(error))
        return False
    if getattr(window, "_source_load_in_progress", False):
        window._set_status("Source loading is already in progress")
        return False
    if glib is None:
        return _load_source_blocking(window, selected_paths)
    generation = int(getattr(window, "_source_load_generation", 0)) + 1
    window._source_load_generation = generation
    window._source_load_in_progress = True
    action = "Adding" if getattr(window, "project", None) is not None else "Loading"
    window._set_status(f"{action} clip 1/{len(selected_paths)} (0%)")
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


def load_project_path(
    window: Any,
    path: Path,
    glib: Any | None = None,
) -> bool:
    if editing_is_locked(window):
        return False
    try:
        project = load_project(path)
    except ProjectPersistenceError as error:
        window._show_error(str(error))
        return False
    if not _validate_project_sources(window, project):
        return False
    if not _attach_loaded_project(window, project, path, glib):
        return False
    pending_sessions = find_export_sessions_for_sources(
        path.parent,
        tuple(Path(source.path) for source in project.sources or (project.source,)),
    )
    if pending_sessions:
        pending = pending_sessions[0]
        stage = pending.last_completed_stage or "no completed stage"
        window._set_status(
            f"Reopened editor project: {path.name}; resumable export available ({stage})",
        )
    else:
        window._set_status(f"Reopened editor project: {path.name}")
    if glib is not None:
        _start_audio_analysis(window, project, glib)
    return False


def attach_project(
    window: Any,
    project: Project,
    project_path: Path | None,
) -> None:
    _invalidate_audio_analysis(window)
    window._stop_backend()
    on_frame, on_error, on_end, on_warning = _create_backend_callbacks(window)
    sources = project.sources or (project.source,)
    policy = resolve_output_policy([source.metadata for source in sources])
    audio_decisions = _preview_audio_decisions(project)
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
    segments = window.segment_timeline.segment_items
    if not segments:
        raise ProjectValidationError("Project segment timeline must contain a segment")
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
    if not active_segments:
        window.backend = None
        window.controller = None
        window._update_selected_clip_label()
        window._update_playback_controls()
        window._update_segment_controls()
        autosave_callback = getattr(window, "_autosave_current_project", None)
        if callable(autosave_callback):
            autosave_callback()
        return
    if use_composed_preview:
        window.backend = _create_composed_preview_backend(
            sources,
            active_segments,
            policy,
            window.source_frame_rate,
            window.segment_timeline.edited_duration_seconds,
            (on_frame, on_error, on_end, on_warning),
            audio_decisions,
            getattr(window, "audio_preview_enabled", False),
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
            audio_preview_enabled=getattr(window, "audio_preview_enabled", False),
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
    autosave_callback = getattr(window, "_autosave_current_project", None)
    if callable(autosave_callback):
        autosave_callback()


def refresh_playback_backend(window: Any, *, force: bool = False) -> None:
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
    active_segments = window.segment_timeline.active_blocks()
    if not active_segments:
        stop_backend = getattr(window, "_stop_backend_nonblocking", None)
        if callable(stop_backend):
            stop_backend()
        else:
            window._stop_backend()
        window.audio_status_label.set_text(
            format_audio_decisions(
                window.project,
                getattr(window, "_audio_analysis_source_ids", ()),
            )
        )
        window._update_playback_controls()
        window._set_status("No included clips in the timeline")
        return
    if (
        not force
        and not requires_composed_preview
        and not isinstance(
            window.backend,
            FfmpegComposedPlaybackBackend,
        )
    ):
        return
    previous_snapshot = None if window.controller is None else window.controller.snapshot()
    position = None
    if force and window.backend is not None:
        try:
            backend_position = float(window.backend.current_position())
        except (AttributeError, TypeError, ValueError):
            backend_position = None
        if backend_position is not None and math.isfinite(backend_position):
            position = max(0.0, backend_position)
    if position is None and force and previous_snapshot is not None:
        position = previous_snapshot.position_seconds
    if position is None:
        timeline_position = 0.0 if window.project is None else window.project.playhead_seconds
        position = window.segment_timeline.timeline_to_edited_position(timeline_position)
    if force and window.project is not None and previous_snapshot is not None:
        window.project.set_playhead(
            window.segment_timeline.edited_to_timeline_position(position),
        )
    was_playing = previous_snapshot is not None and previous_snapshot.state == PlaybackState.PLAYING
    sources = window.project.sources or (window.project.source,)
    policy = resolve_output_policy([source.metadata for source in sources])
    audio_decisions = _preview_audio_decisions(window.project)
    window.audio_status_label.set_text(
        format_audio_decisions(
            window.project,
            getattr(window, "_audio_analysis_source_ids", ()),
        )
    )
    window._stop_backend()
    on_frame, on_error, on_end, on_warning = _create_backend_callbacks(window)
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
            getattr(window, "audio_preview_enabled", False),
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
            audio_preview_enabled=getattr(window, "audio_preview_enabled", False),
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
    autosave_callback = getattr(window, "_autosave_current_project", None)
    if callable(autosave_callback):
        autosave_callback()
