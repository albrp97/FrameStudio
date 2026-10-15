from __future__ import annotations

import errno
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from array import array
from dataclasses import asdict, dataclass, replace
from fractions import Fraction
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import unquote, urlparse

from .audio_compositor import (
    AUDIO_CHANNELS,
    AUDIO_SAMPLE_RATE,
    AudioCompositionError,
    AudioPlan,
    build_audio_plan,
    render_audio,
)
from .export_process import (
    check_export_cancelled,
    make_progress_heartbeat,
    probe_frame_count,
    report_preparation_progress,
    run_command_with_cancellation,
    run_ffmpeg,
    validate_decoded_output,
)
from .export_types import ExportExecutionError, ExportProgressCallback
from .fps_policy import FrameRatePolicy, ResolvedFrameRatePolicy
from .interpolation import RuntimeValidationCache
from .layout_plan import LayoutPlan
from .media import MediaProbe, MediaProbeError, probe_media
from .model import Project, ProjectValidationError
from .model_types import SourceReference
from .render_preparations import PreparationCacheError, RenderPreparations
from .upscale_policy import ResolvedUpscalePolicy, UpscalePolicy
from .video_compositor import (
    SourceHashCache,
    VideoCompositorExecutionError,
    VideoCompositorPlanningError,
    VideoRenderPlan,
    _default_restoration_model,
    _restoration_model_path,
    plan_project_video,
    render_project_video,
)
from .video_compositor import (
    _sha256 as _video_file_sha256,
)

AAC_FRAME_SAMPLES = 1024
AAC_ENCODER_PRIMING_SAMPLES = 1024
AAC_SAMPLE_COUNT_TOLERANCE = AAC_ENCODER_PRIMING_SAMPLES + AAC_FRAME_SAMPLES - 1
_FrameRatePolicyInput = FrameRatePolicy | ResolvedFrameRatePolicy | Mapping[str, object] | None
_UpscalePolicyInput = UpscalePolicy | ResolvedUpscalePolicy | Mapping[str, object] | None


class AVCompositorError(RuntimeError):
    """Base error for bounded audio/video composition."""


class AVCompositorPlanningError(AVCompositorError):
    """Raised when an audio/video composition cannot be planned."""


class AVCompositorExecutionError(AVCompositorError):
    """Raised when an audio/video composition cannot be verified and published."""


@dataclass(frozen=True)
class AVSourceIdentity:
    source_id: str
    path: Path
    resolved_path: Path
    source_hash: str
    size_bytes: int
    modified_time_ns: int


@dataclass(frozen=True)
class AVRenderPlan:
    project: Project
    destination: Path
    video_plan: VideoRenderPlan
    audio_plan: AudioPlan
    protected_sources: tuple[AVSourceIdentity, ...]

    @property
    def layout_plan(self) -> LayoutPlan:
        return self.video_plan.layout_plan

    @property
    def source_paths(self) -> tuple[Path, ...]:
        return tuple(source.resolved_path for source in self.protected_sources)

    @property
    def source_hashes(self) -> tuple[str, ...]:
        return tuple(source.source_hash for source in self.protected_sources)


@dataclass(frozen=True)
class AVRenderResult:
    destination: Path
    output_probe: MediaProbe
    actual_frames: int
    expected_frames: int
    audio_sample_rate: int
    audio_channels: int
    audio_sample_count: int
    audio_peak: float
    source_hashes_unchanged: bool
    processing_fallbacks: tuple[str, ...] = ()

    @property
    def sample_rate(self) -> int:
        return self.audio_sample_rate

    @property
    def channels(self) -> int:
        return self.audio_channels

    @property
    def sample_count(self) -> int:
        return self.audio_sample_count

    @property
    def peak(self) -> float:
        return self.audio_peak


@dataclass(frozen=True)
class _VerifiedMux:
    output_probe: MediaProbe
    actual_frames: int
    sample_rate: int
    channels: int
    sample_count: int
    peak: float
    processing_fallbacks: tuple[str, ...] = ()


def plan_project_av(
    project: Project,
    destination: Path,
    *,
    target_rate: Fraction | int | float | str | None = None,
    frame_rate_policy: _FrameRatePolicyInput = None,
    upscale_policy: _UpscalePolicyInput = None,
    ffprobe_path: str = "ffprobe",
    cancel_event: threading.Event | None = None,
    progress_callback: ExportProgressCallback | None = None,
    source_hash_cache: SourceHashCache | None = None,
    runtime_cache: RuntimeValidationCache | None = None,
) -> AVRenderPlan:
    """Plan one shared-layout video/audio composition without publishing output."""
    if not isinstance(project, Project):
        raise AVCompositorPlanningError("project must be a Project")
    check_export_cancelled(cancel_event)
    hashes: SourceHashCache = {} if source_hash_cache is None else source_hash_cache
    resolved_destination = Path(destination).expanduser().resolve()
    if not resolved_destination.name:
        raise AVCompositorPlanningError("A file destination is required")
    try:
        project.validate()
        _reject_destination_conflict(project, resolved_destination)
        protected_sources = _capture_source_identities(
            project,
            cancel_event=cancel_event,
            progress_callback=progress_callback,
            source_hash_cache=hashes,
        )
        video_plan = plan_project_video(
            project,
            resolved_destination,
            target_rate=target_rate,
            frame_rate_policy=frame_rate_policy,
            upscale_policy=upscale_policy,
            ffprobe_path=ffprobe_path,
            cancel_event=cancel_event,
            progress_callback=progress_callback,
            source_hash_cache=hashes,
            runtime_cache=runtime_cache,
        )
        audio_plan = build_audio_plan(project, video_plan.layout_plan)
        return AVRenderPlan(
            project=project,
            destination=resolved_destination,
            video_plan=video_plan,
            audio_plan=audio_plan,
            protected_sources=protected_sources,
        )
    except (OSError, ProjectValidationError, AVCompositorError) as error:
        if isinstance(error, AVCompositorError):
            raise
        raise AVCompositorPlanningError(str(error)) from error
    except (
        AudioCompositionError,
        MediaProbeError,
        VideoCompositorPlanningError,
    ) as error:
        raise AVCompositorPlanningError(str(error)) from error


def render_project_av(
    plan: AVRenderPlan,
    *,
    preparations: RenderPreparations | None = None,
    ffmpeg_path: str = "ffmpeg",
    ffprobe_path: str = "ffprobe",
    cancel_event: threading.Event | None = None,
    cancellation_lock: threading.Lock | None = None,
    progress_callback: ExportProgressCallback | None = None,
) -> AVRenderResult:
    """Render child video/audio stages, verify the mux, then atomically publish it."""
    if not isinstance(plan, AVRenderPlan):
        raise AVCompositorExecutionError("plan must be an AVRenderPlan")
    _reject_destination_conflict(
        plan.project,
        plan.destination,
        planned_source_paths=_protected_source_paths(plan.protected_sources),
    )
    _assert_sources_unchanged(
        plan.protected_sources, cancel_event=cancel_event, progress_callback=progress_callback
    )
    publication_stage: Path | None = None
    staging_directory: Path | None = None
    cleanup_attempted = False
    published = False
    try:
        if cancel_event is not None and cancel_event.is_set():
            raise AVCompositorExecutionError("Export cancelled")
        _require_executable(ffmpeg_path, "FFmpeg")
        _require_executable(ffprobe_path, "ffprobe")
        plan.destination.parent.mkdir(parents=True, exist_ok=True)
        staging_directory = Path(
            tempfile.mkdtemp(
                prefix=f".{plan.destination.name}.av-",
                dir=str(plan.destination.parent),
            ),
        )
        execution_video_plan = replace(
            plan.video_plan,
            destination=staging_directory / "video.mp4",
        )
        muxed_stage, verified = _render_verified_stages(
            plan,
            execution_video_plan,
            staging_directory,
            ffmpeg_path=ffmpeg_path,
            ffprobe_path=ffprobe_path,
            cancel_event=cancel_event,
            progress_callback=progress_callback,
            preparations=preparations,
        )
        if cancel_event is not None and cancel_event.is_set():
            raise AVCompositorExecutionError("Export cancelled")
        publication_stage = _move_verified_mux(muxed_stage, plan, staging_directory)
        cleanup_attempted = True
        _clean_staging_before_publish(staging_directory)
        _assert_sources_unchanged(
            plan.protected_sources, cancel_event=cancel_event, progress_callback=progress_callback
        )

        result = AVRenderResult(
            destination=plan.destination,
            output_probe=replace(verified.output_probe, path=plan.destination),
            actual_frames=verified.actual_frames,
            expected_frames=plan.video_plan.expected_frames,
            audio_sample_rate=verified.sample_rate,
            audio_channels=verified.channels,
            audio_sample_count=verified.sample_count,
            audio_peak=verified.peak,
            source_hashes_unchanged=True,
            processing_fallbacks=verified.processing_fallbacks,
        )

        def publish() -> None:
            if cancel_event is not None and cancel_event.is_set():
                raise AVCompositorExecutionError("Export cancelled")
            try:
                os.replace(publication_stage, plan.destination)
            except OSError as error:
                raise AVCompositorExecutionError(
                    f"Could not publish verified audio/video output: {error}",
                ) from error

        if cancellation_lock is None:
            publish()
        else:
            with cancellation_lock:
                publish()
        published = True
        return result
    except AVCompositorError:
        raise
    except (
        AudioCompositionError,
        ExportExecutionError,
        MediaProbeError,
        OSError,
        VideoCompositorExecutionError,
    ) as error:
        raise AVCompositorExecutionError(str(error)) from error
    finally:
        cleanup_errors: list[OSError] = []
        if not cleanup_attempted:
            cleanup_error = _remove_directory(staging_directory)
            if cleanup_error is not None:
                cleanup_errors.append(cleanup_error)
        if not published and publication_stage is not None:
            publication_cleanup_error = _remove_file(publication_stage)
            if publication_cleanup_error is not None:
                cleanup_errors.append(publication_cleanup_error)
        if cleanup_errors:
            cleanup_detail = "; ".join(str(error) for error in cleanup_errors)
            active_error = sys.exc_info()[1]
            if active_error is not None:
                raise AVCompositorExecutionError(
                    f"Audio/video render failed: {active_error}; "
                    f"staging cleanup failed: {cleanup_detail}",
                ) from active_error
            raise AVCompositorExecutionError(
                f"Audio/video staging cleanup failed: {cleanup_detail}",
            ) from cleanup_errors[0]


def _project_sources(project: Project) -> tuple[SourceReference, ...]:
    seen: set[str] = set()
    sources = project.sources if project.sources is not None else (project.source,)
    result: list[SourceReference] = []
    for source in (project.source, *sources):
        if source.source_id in seen:
            continue
        seen.add(source.source_id)
        result.append(source)
    return tuple(result)


def _source_candidates(source: SourceReference) -> tuple[Path, ...]:
    candidates = [Path(source.path).expanduser()]
    parsed = urlparse(source.uri)
    if parsed.scheme == "file":
        uri_path = unquote(parsed.path)
        if parsed.netloc and parsed.netloc != "localhost":
            uri_path = f"//{parsed.netloc}{uri_path}"
        uri_candidate = Path(uri_path).expanduser()
        if uri_candidate not in candidates:
            candidates.append(uri_candidate)
    return tuple(candidates)


def _reject_destination_conflict(
    project: Project,
    destination: Path,
    *,
    planned_source_paths: tuple[Path, ...] = (),
) -> None:
    resolved_destination = destination.expanduser().resolve()
    protected_paths = {path.expanduser().resolve() for path in planned_source_paths}
    for source in _project_sources(project):
        for candidate in _source_candidates(source):
            if candidate.resolve() == resolved_destination:
                raise AVCompositorPlanningError(
                    f"Export destination must differ from project source media: "
                    f"{resolved_destination.name}",
                )
    if resolved_destination in protected_paths:
        raise AVCompositorPlanningError(
            f"Export destination must differ from planned source media: "
            f"{resolved_destination.name}",
        )


def _protected_source_paths(
    identities: tuple[AVSourceIdentity, ...],
) -> tuple[Path, ...]:
    paths: list[Path] = []
    for identity in identities:
        paths.extend((identity.path, identity.resolved_path))
    return tuple(paths)


def _capture_source_identities(
    project: Project,
    *,
    cancel_event: threading.Event | None = None,
    progress_callback: ExportProgressCallback | None = None,
    source_hash_cache: SourceHashCache | None = None,
) -> tuple[AVSourceIdentity, ...]:
    identities: list[AVSourceIdentity] = []
    seen: set[tuple[Path, Path]] = set()
    sources = tuple(_project_sources(project))
    started = time.monotonic()
    for index, source in enumerate(sources):
        check_export_cancelled(cancel_event)
        report_preparation_progress(
            progress_callback, "Protecting export sources", index, len(sources), started
        )
        for candidate in _source_candidates(source):
            resolved = candidate.resolve()
            key = (candidate, resolved)
            if key in seen:
                continue
            seen.add(key)
            try:
                stat = resolved.stat()
                source_hash = _video_file_sha256(
                    resolved,
                    cancel_event=cancel_event,
                    source_hash_cache=source_hash_cache,
                    heartbeat_callback=make_progress_heartbeat(
                        progress_callback,
                        stage="Protecting export sources",
                        total_frames=len(sources),
                        frame=index,
                        started=started,
                        percent=index * 100 / len(sources),
                    ),
                )
            except OSError as error:
                raise AVCompositorPlanningError(
                    f"Could not inspect source {resolved.name}: {error}",
                ) from error
            identities.append(
                AVSourceIdentity(
                    source_id=source.source_id,
                    path=candidate,
                    resolved_path=resolved,
                    source_hash=source_hash,
                    size_bytes=stat.st_size,
                    modified_time_ns=stat.st_mtime_ns,
                ),
            )
    if not identities:
        raise AVCompositorPlanningError("The project has no source media")
    return tuple(identities)


def _assert_sources_unchanged(
    identities: tuple[AVSourceIdentity, ...],
    *,
    cancel_event: threading.Event | None = None,
    progress_callback: ExportProgressCallback | None = None,
) -> None:
    started = time.monotonic()
    for index, identity in enumerate(identities):
        check_export_cancelled(cancel_event)
        report_preparation_progress(
            progress_callback, "Verifying export sources", index, len(identities), started
        )
        current_path = identity.path.expanduser()
        try:
            if current_path.resolve() != identity.resolved_path:
                raise AVCompositorExecutionError(
                    f"Source path changed during render: {current_path.name}",
                )
            stat = identity.resolved_path.stat()
            current_hash = _video_file_sha256(
                identity.resolved_path,
                cancel_event=cancel_event,
                heartbeat_callback=make_progress_heartbeat(
                    progress_callback,
                    stage="Verifying export sources",
                    total_frames=len(identities),
                    frame=index,
                    started=started,
                    percent=index * 100 / len(identities),
                ),
            )
        except OSError as error:
            raise AVCompositorExecutionError(
                f"Could not verify source preservation for {current_path.name}: {error}",
            ) from error
        if (
            stat.st_size != identity.size_bytes
            or stat.st_mtime_ns != identity.modified_time_ns
            or current_hash != identity.source_hash
        ):
            raise AVCompositorExecutionError(
                f"Source changed during render; output was not published: {current_path.name}",
            )


def _require_executable(path: str, label: str) -> None:
    if shutil.which(path) is None:
        raise AVCompositorExecutionError(f"{label} executable was not found: {path}")


def _is_within(path: Path, directory: Path) -> bool:
    try:
        path.expanduser().resolve().relative_to(directory.expanduser().resolve())
    except ValueError:
        return False
    return True


def _publication_stage_path(plan: AVRenderPlan, staging_directory: Path) -> Path:
    return plan.destination.parent / (f".{plan.destination.name}.av-final-{staging_directory.name}")


def _render_verified_stages(
    plan: AVRenderPlan,
    video_plan: VideoRenderPlan,
    staging_directory: Path,
    *,
    ffmpeg_path: str,
    ffprobe_path: str,
    cancel_event: threading.Event | None = None,
    progress_callback: ExportProgressCallback | None = None,
    preparations: RenderPreparations | None = None,
) -> tuple[Path, _VerifiedMux]:
    if not staging_directory.is_dir():
        raise AVCompositorExecutionError("AV staging directory is unavailable")
    if not _is_within(video_plan.destination, staging_directory):
        raise AVCompositorExecutionError(
            "Video child render must target the private AV staging directory",
        )
    if preparations is not None:
        muxed, verified = _render_checkpointed_stages(
            plan,
            video_plan,
            preparations,
            ffmpeg_path=ffmpeg_path,
            ffprobe_path=ffprobe_path,
            cancel_event=cancel_event,
            progress_callback=progress_callback,
        )
        staged_mux = staging_directory / "muxed.mp4"
        _stage_cached_mux(muxed, staged_mux, cancel_event)
        return staged_mux, verified
    video_result = render_project_video(
        video_plan,
        ffmpeg_path=ffmpeg_path,
        ffprobe_path=ffprobe_path,
        cancel_event=cancel_event,
        progress_callback=progress_callback,
    )
    _assert_sources_unchanged(
        plan.protected_sources, cancel_event=cancel_event, progress_callback=progress_callback
    )
    audio_stage = staging_directory / "audio.wav"
    audio_result = render_audio(
        plan.project,
        video_plan.layout_plan,
        audio_stage,
        ffmpeg_path=ffmpeg_path,
        ffprobe_path=ffprobe_path,
        cancel_event=cancel_event,
    )
    _assert_sources_unchanged(
        plan.protected_sources, cancel_event=cancel_event, progress_callback=progress_callback
    )
    muxed_stage = staging_directory / "muxed.mp4"
    _mux_stages(
        video_result.destination,
        audio_result.output_path,
        muxed_stage,
        ffmpeg_path=ffmpeg_path,
        cancel_event=cancel_event,
    )
    verified = _verify_muxed_output(
        muxed_stage,
        plan,
        ffmpeg_path=ffmpeg_path,
        ffprobe_path=ffprobe_path,
        cancel_event=cancel_event,
    )
    _assert_sources_unchanged(
        plan.protected_sources, cancel_event=cancel_event, progress_callback=progress_callback
    )
    return muxed_stage, replace(verified, processing_fallbacks=video_result.processing_fallbacks)


def _stage_cached_mux(cached: Path, staged: Path, cancel_event: threading.Event | None) -> None:
    check_export_cancelled(cancel_event)
    try:
        os.link(cached, staged)
        return
    except OSError as error:
        if error.errno not in {errno.EXDEV, errno.EPERM, errno.EOPNOTSUPP}:
            raise
    with cached.open("rb") as source, staged.open("xb") as destination:
        while chunk := source.read(1024 * 1024):
            check_export_cancelled(cancel_event)
            destination.write(chunk)
    check_export_cancelled(cancel_event)


def _render_checkpointed_stages(
    plan: AVRenderPlan,
    video_plan: VideoRenderPlan,
    preparations: RenderPreparations,
    *,
    ffmpeg_path: str,
    ffprobe_path: str,
    cancel_event: threading.Event | None,
    progress_callback: ExportProgressCallback | None,
) -> tuple[Path, _VerifiedMux]:
    request = {
        "composition_version": 2,
        "layout": asdict(video_plan.layout_plan),
        "sources": plan.source_hashes,
        "target_rate": str(video_plan.target_rate),
        "frame_counts": video_plan.interval_frame_counts,
        "routes": [asdict(route) for route in video_plan.processing_routes],
        "restoration_models": [
            preparations.model_identity(
                _restoration_model_path(
                    route.upscale_model or "SuperUltraCompact",
                    _default_restoration_model(),
                )
            )
            for route in video_plan.processing_routes
            if route.upscale_requested and route.upscale_status == "available"
        ],
        "runtime": preparations.runtime(
            ffmpeg_path,
            ffprobe_path,
            neural=any(
                (route.upscale_requested and route.upscale_status == "available")
                or (route.fps_action == "interpolate" and route.fps_backend.startswith("rve"))
                for route in video_plan.processing_routes
            ),
        ),
    }
    video_validation: dict[str, Any] = {}

    def render_video(destination: Path) -> None:
        result = render_project_video(
            replace(video_plan, destination=destination),
            ffmpeg_path=ffmpeg_path,
            ffprobe_path=ffprobe_path,
            cancel_event=cancel_event,
            progress_callback=progress_callback,
            preparations=preparations,
        )
        video_validation["processing_fallbacks"] = list(result.processing_fallbacks)

    video_stage = preparations.materialize(
        "video composition",
        request,
        render_video,
        lambda _path: video_validation,  # The child verifies before returning.
    )
    video_metadata = preparations.validation_data[video_stage]
    if (
        not isinstance(video_metadata, dict)
        or not isinstance(video_metadata.get("processing_fallbacks"), list)
        or not all(isinstance(item, str) for item in video_metadata["processing_fallbacks"])
    ):
        raise PreparationCacheError("Video checkpoint has invalid enhancement metadata")
    fallbacks = tuple(video_metadata["processing_fallbacks"])
    for fallback in fallbacks:
        report_preparation_progress(
            progress_callback, f"Video enhancement fallback: {fallback}", 1, 1, time.monotonic()
        )
    _assert_sources_unchanged(
        plan.protected_sources, cancel_event=cancel_event, progress_callback=progress_callback
    )
    audio_request = {
        "audio_plan": asdict(plan.audio_plan),
        "sources": plan.source_hashes,
        "runtime": preparations.runtime(ffmpeg_path, ffprobe_path),
    }
    audio_stage = preparations.materialize(
        "audio composition",
        audio_request,
        lambda destination: render_audio(
            plan.project,
            video_plan.layout_plan,
            destination,
            ffmpeg_path=ffmpeg_path,
            ffprobe_path=ffprobe_path,
            cancel_event=cancel_event,
        ),
        lambda _path: None,  # render_audio already verifies the exact PCM contract.
        suffix=".wav",
    )

    def verify(path: Path) -> dict[str, float]:
        result = _verify_muxed_output(
            path,
            plan,
            ffmpeg_path=ffmpeg_path,
            ffprobe_path=ffprobe_path,
            cancel_event=cancel_event,
        )
        return {"peak": result.peak}

    muxed = preparations.materialize(
        "verified AV composition",
        {"video": request, "audio": audio_request},
        lambda destination: _mux_stages(
            video_stage,
            audio_stage,
            destination,
            ffmpeg_path=ffmpeg_path,
            cancel_event=cancel_event,
        ),
        verify,
    )
    summary = preparations.validation_data[muxed]
    if (
        not isinstance(summary, dict)
        or not isinstance(summary.get("peak"), (float, int))
        or not math.isfinite(summary["peak"])
        or not 0 <= summary["peak"] <= 1.0 + 1e-6
    ):
        raise PreparationCacheError("Verified composition checkpoint has invalid audio metadata")
    _assert_sources_unchanged(
        plan.protected_sources, cancel_event=cancel_event, progress_callback=progress_callback
    )
    return muxed, _VerifiedMux(
        output_probe=probe_media(muxed, ffprobe_path),
        actual_frames=video_plan.expected_frames,
        sample_rate=AUDIO_SAMPLE_RATE,
        channels=AUDIO_CHANNELS,
        sample_count=plan.audio_plan.final_sample_count,
        peak=float(summary["peak"]),
        processing_fallbacks=fallbacks,
    )


def _move_verified_mux(
    muxed_stage: Path,
    plan: AVRenderPlan,
    staging_directory: Path,
) -> Path:
    publication_stage = _publication_stage_path(plan, staging_directory)
    if publication_stage.exists() or publication_stage.is_symlink():
        raise AVCompositorExecutionError(
            f"Private publication stage already exists: {publication_stage.name}",
        )
    try:
        os.replace(muxed_stage, publication_stage)
    except OSError as error:
        raise AVCompositorExecutionError(
            f"Could not prepare verified audio/video output: {error}",
        ) from error
    return publication_stage


def _clean_staging_before_publish(staging_directory: Path) -> None:
    cleanup_error = _remove_directory(staging_directory)
    if cleanup_error is not None:
        raise AVCompositorExecutionError(
            f"Could not clean private AV staging directory: {cleanup_error}",
        ) from cleanup_error


def _mux_stages(
    video_path: Path,
    audio_path: Path,
    destination: Path,
    *,
    ffmpeg_path: str,
    cancel_event: threading.Event | None = None,
) -> None:
    command = [
        ffmpeg_path,
        "-hide_banner",
        "-loglevel",
        "error",
        "-nostdin",
        "-y",
        "-i",
        str(video_path),
        "-i",
        str(audio_path),
        "-map",
        "0:v:0",
        "-map",
        "1:a:0",
        "-c:v",
        "copy",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-ar",
        str(AUDIO_SAMPLE_RATE),
        "-ac",
        str(AUDIO_CHANNELS),
        "-shortest",
        "-movflags",
        "+faststart",
        str(destination),
    ]
    try:
        run_ffmpeg(
            command,
            cancel_event=cancel_event,
            stage="audio/video mux",
        )
    except OSError as error:
        raise AVCompositorExecutionError(f"Could not start FFmpeg mux: {error}") from error
    except ExportExecutionError as error:
        raise AVCompositorExecutionError(str(error)) from error


def _verify_muxed_output(
    candidate: Path,
    plan: AVRenderPlan,
    *,
    ffmpeg_path: str,
    ffprobe_path: str,
    cancel_event: threading.Event | None = None,
) -> _VerifiedMux:
    streams, format_duration = _probe_muxed_streams(
        candidate,
        ffprobe_path,
        cancel_event=cancel_event,
    )
    video_stream = next(
        (stream for stream in streams if stream.get("codec_type") == "video"),
        None,
    )
    audio_stream = next(
        (stream for stream in streams if stream.get("codec_type") == "audio"),
        None,
    )
    if video_stream is None or audio_stream is None:
        raise AVCompositorExecutionError("Muxed output must contain video and audio streams")
    try:
        width = int(video_stream["width"])
        height = int(video_stream["height"])
        frame_rate = Fraction(video_stream["r_frame_rate"])
        audio_sample_rate = int(audio_stream["sample_rate"])
        audio_channels = int(audio_stream["channels"])
        audio_codec = audio_stream["codec_name"]
        video_duration = float(video_stream["duration"])
        audio_duration = float(audio_stream["duration"])
    except (KeyError, TypeError, ValueError, ZeroDivisionError) as error:
        raise AVCompositorExecutionError(
            "Muxed output stream metadata is incomplete",
        ) from error
    if (width, height) != (1920, 1080):
        raise AVCompositorExecutionError(
            f"Muxed video canvas is {width}x{height}, expected 1920x1080",
        )
    if frame_rate != plan.video_plan.target_rate:
        raise AVCompositorExecutionError(
            f"Muxed video rate is {frame_rate}, expected {plan.video_plan.target_rate}",
        )
    if audio_codec != "aac":
        raise AVCompositorExecutionError(
            f"Muxed audio codec is {audio_codec!r}, expected AAC",
        )
    if (audio_sample_rate, audio_channels) != (AUDIO_SAMPLE_RATE, AUDIO_CHANNELS):
        raise AVCompositorExecutionError(
            "Muxed audio does not match the 48 kHz stereo contract",
        )

    actual_frames = probe_frame_count(
        candidate,
        ffprobe_path,
        cancel_event=cancel_event,
    )
    if actual_frames != plan.video_plan.expected_frames:
        raise AVCompositorExecutionError(
            f"Muxed video has {actual_frames} frames; expected {plan.video_plan.expected_frames}",
        )
    expected_video_duration = plan.video_plan.expected_frames / float(
        plan.video_plan.target_rate,
    )
    expected_audio_duration = plan.audio_plan.final_sample_count / AUDIO_SAMPLE_RATE
    video_duration_tolerance = 1.0 / float(plan.video_plan.target_rate)
    audio_duration_tolerance = AAC_SAMPLE_COUNT_TOLERANCE / AUDIO_SAMPLE_RATE
    if abs(video_duration - expected_video_duration) > video_duration_tolerance:
        raise AVCompositorExecutionError("Muxed video stream duration is misaligned")
    if abs(audio_duration - expected_audio_duration) > audio_duration_tolerance:
        raise AVCompositorExecutionError("Muxed audio stream duration is misaligned")
    expected_format_duration = max(expected_video_duration, expected_audio_duration)
    if abs(format_duration - expected_format_duration) > max(
        video_duration_tolerance,
        audio_duration_tolerance,
    ):
        raise AVCompositorExecutionError("Muxed container duration is misaligned")

    try:
        validate_decoded_output(
            candidate,
            ffmpeg_path,
            label="final audio/video output",
            cancel_event=cancel_event,
        )
    except (ExportExecutionError, OSError) as error:
        raise AVCompositorExecutionError(str(error)) from error
    sample_count, peak = _decode_audio_stats(
        candidate,
        ffmpeg_path=ffmpeg_path,
        expected_samples=plan.audio_plan.final_sample_count,
        cancel_event=cancel_event,
    )
    output_probe = probe_media(candidate, ffprobe_path)
    return _VerifiedMux(
        output_probe=output_probe,
        actual_frames=actual_frames,
        sample_rate=audio_sample_rate,
        channels=audio_channels,
        sample_count=sample_count,
        peak=peak,
    )


def _probe_muxed_streams(
    candidate: Path,
    ffprobe_path: str,
    *,
    cancel_event: threading.Event | None = None,
) -> tuple[tuple[dict[str, Any], ...], float]:
    command = [
        ffprobe_path,
        "-hide_banner",
        "-v",
        "error",
        "-show_streams",
        "-show_format",
        "-of",
        "json",
        str(candidate),
    ]
    try:
        if cancel_event is None:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,
            )
        else:
            completed = run_command_with_cancellation(command, cancel_event=cancel_event)
    except ExportExecutionError as error:
        raise AVCompositorExecutionError(str(error)) from error
    except OSError as error:
        raise AVCompositorExecutionError(f"Could not start ffprobe: {error}") from error
    if completed.returncode != 0:
        raise AVCompositorExecutionError(
            completed.stderr.strip() or "ffprobe could not verify muxed output",
        )
    try:
        payload = json.loads(completed.stdout)
        streams = tuple(payload["streams"])
        format_duration = float(payload["format"]["duration"])
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        raise AVCompositorExecutionError(
            "ffprobe returned incomplete muxed output metadata",
        ) from error
    if not math.isfinite(format_duration) or format_duration <= 0.0:
        raise AVCompositorExecutionError("Muxed output duration is invalid")
    if not streams:
        raise AVCompositorExecutionError("ffprobe returned no muxed output streams")
    return streams, format_duration


def _decode_audio_stats(
    candidate: Path,
    *,
    ffmpeg_path: str,
    expected_samples: int,
    cancel_event: threading.Event | None = None,
) -> tuple[int, float]:
    try:
        completed = run_command_with_cancellation(
            [
                ffmpeg_path,
                "-hide_banner",
                "-loglevel",
                "error",
                "-nostdin",
                "-i",
                str(candidate),
                "-map",
                "0:a:0",
                "-f",
                "f32le",
                "-ar",
                str(AUDIO_SAMPLE_RATE),
                "-ac",
                str(AUDIO_CHANNELS),
                "pipe:1",
            ],
            cancel_event=cancel_event,
            text=False,
        )
    except ExportExecutionError as error:
        raise AVCompositorExecutionError(str(error)) from error
    except OSError as error:
        raise AVCompositorExecutionError(f"Could not decode muxed audio: {error}") from error
    if completed.returncode != 0:
        raise AVCompositorExecutionError(
            completed.stderr.decode(errors="replace").strip() or "Could not decode muxed audio",
        )
    if len(completed.stdout) % 4:
        raise AVCompositorExecutionError("Muxed PCM byte count is not float32 aligned")
    samples = array("f")
    samples.frombytes(completed.stdout)
    sample_count = len(samples) // AUDIO_CHANNELS
    if abs(sample_count - expected_samples) > AAC_SAMPLE_COUNT_TOLERANCE:
        raise AVCompositorExecutionError(
            f"Muxed audio has {sample_count} decoded samples; expected {expected_samples}",
        )
    if any(not math.isfinite(value) for value in samples):
        raise AVCompositorExecutionError("Muxed PCM contains a non-finite sample")
    peak = max((abs(value) for value in samples), default=0.0)
    if peak > 1.0 + 1e-6:
        raise AVCompositorExecutionError(f"Muxed PCM clips above unity: {peak:.9f}")
    return sample_count, peak


def _remove_directory(path: Path | None) -> OSError | None:
    if path is None:
        return None
    try:
        shutil.rmtree(path)
    except FileNotFoundError:
        return None
    except OSError as error:
        return error
    return None


def _remove_file(path: Path) -> OSError | None:
    try:
        path.unlink()
    except FileNotFoundError:
        return None
    except OSError as error:
        return error
    return None
