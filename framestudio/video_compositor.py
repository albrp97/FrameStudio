from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
import threading
import time
import uuid
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, replace
from fractions import Fraction
from functools import partial
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

from .export_journal import record_export_error
from .export_process import (
    check_export_cancelled,
    make_progress_heartbeat,
    partial_path,
    probe_frame_count,
    publish_verified_export,
    remove_partial,
    report_preparation_progress,
    run_ffmpeg,
    validate_decoded_output,
)
from .export_progress import progress_scope
from .export_types import ExportExecutionError, ExportProgressCallback
from .fps_policy import (
    DEFAULT_FPS_BACKEND,
    DEFAULT_FPS_FALLBACK_BACKEND,
    FrameRatePolicy,
    FrameRatePolicyError,
    ResolvedFrameRatePolicy,
    canonical_rate,
    resolve_frame_rate_policy,
)
from .interpolation import (
    RuntimeValidationCache,
    run_source_interpolation,
    validate_interpolation_backend,
    validate_rve_runtime,
)
from .layout_plan import (
    DEFAULT_CANVAS,
    CropPlan,
    LayoutInterval,
    LayoutPlan,
    LayoutPlanError,
    PlannedBlock,
    SlotPlan,
    SourceGeometry,
    plan_project_layout,
)
from .media import MediaProbe, MediaProbeError, probe_media
from .model import Project, ProjectValidationError
from .output_plan import active_export_sources
from .render_preparations import PreparationCacheError, RenderPreparations
from .source_hash_cache import SourceHashCache
from .source_hash_cache import file_sha256 as _sha256
from .upscale_policy import (
    ResolvedUpscalePolicy,
    UpscaleDecision,
    UpscalePolicy,
    UpscalePolicyError,
    resolve_upscale_policy,
)

PROJECT_TIMEBASE = 1_000_000


class VideoCompositorError(RuntimeError):
    """Base error for bounded video-only composition."""


class VideoCompositorPlanningError(VideoCompositorError):
    """Raised when a project cannot be planned for video-only rendering."""


class VideoCompositorExecutionError(VideoCompositorError):
    """Raised when a planned video render cannot be verified and published."""


@dataclass(frozen=True)
class VideoSourceProbe:
    source_id: str
    path: Path
    media: MediaProbe
    geometry: SourceGeometry
    sample_aspect_ratio: tuple[int, int]
    frame_count: int | None
    source_hash: str
    source_stat: os.stat_result

    @property
    def metadata(self) -> dict[str, Any]:
        return {
            **self.media.metadata(),
            "source_id": self.source_id,
            "sample_aspect_ratio": f"{self.sample_aspect_ratio[0]}/{self.sample_aspect_ratio[1]}",
        }


@dataclass(frozen=True)
class VideoProcessingRoute:
    source_id: str
    source_rate: Fraction
    target_rate: Fraction
    fps_action: str
    fps_backend: str
    fps_status: str
    fps_reason: str
    upscale_requested: bool
    upscale_backend: str
    upscale_status: str
    upscale_reason: str
    upscale_model: str | None = None


@dataclass(frozen=True)
class VideoPreparationIdentity:
    block_id: str
    source_id: str
    source_hash: str
    source_range_ticks: tuple[int, int]
    target_rate: Fraction
    input_domain: str = "native-source"
    output_domain: str = "native-preparation"
    modification_identity: tuple[object, ...] = ()
    policy_identity: tuple[object, ...] = ()

    @property
    def cache_key(self) -> str:
        payload = {
            "cache_version": 3,
            "source_hash": self.source_hash,
            "source_range_ticks": self.source_range_ticks,
            "target_rate": str(self.target_rate),
            "input_domain": self.input_domain,
            "output_domain": self.output_domain,
            "policy_identity": self.policy_identity,
        }
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, default=str).encode("utf-8"),
        ).hexdigest()


@dataclass(frozen=True)
class VideoRenderPlan:
    project: Project
    destination: Path
    layout_plan: LayoutPlan
    probed_metadata: tuple[VideoSourceProbe, ...]
    target_rate: Fraction
    frame_boundaries: tuple[int, ...]
    interval_frame_counts: tuple[int, ...]
    expected_frames: int
    include_audio: bool
    frame_rate_policy: ResolvedFrameRatePolicy
    upscale_policy: ResolvedUpscalePolicy
    processing_routes: tuple[VideoProcessingRoute, ...]
    preparation_identities: tuple[VideoPreparationIdentity, ...]

    @property
    def expected_duration_seconds(self) -> float:
        return self.expected_frames / float(self.target_rate)

    @property
    def source_paths(self) -> tuple[Path, ...]:
        return tuple(item.path for item in self.probed_metadata)


@dataclass(frozen=True)
class VideoRenderResult:
    destination: Path
    output_probe: MediaProbe
    actual_frames: int
    expected_frames: int
    source_hashes_unchanged: bool
    processing_fallbacks: tuple[str, ...] = ()


@dataclass(frozen=True)
class _PreparedAsset:
    path: Path
    fps_converted: bool


def cumulative_frame_boundaries(
    timeline_boundaries: Sequence[int],
    target_rate: Fraction | int | float | str,
) -> tuple[int, ...]:
    """Round cumulative timeline positions half-up, then derive interval counts."""
    rate = canonical_rate(target_rate)
    if not timeline_boundaries:
        raise VideoCompositorPlanningError("At least one timeline boundary is required")
    previous = -1
    result: list[int] = []
    for value in timeline_boundaries:
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise VideoCompositorPlanningError("Timeline boundaries must be non-negative ticks")
        if value <= previous:
            raise VideoCompositorPlanningError("Timeline boundaries must be strictly increasing")
        exact = Fraction(value, PROJECT_TIMEBASE) * rate
        rounded = (exact.numerator * 2 + exact.denominator) // (2 * exact.denominator)
        result.append(rounded)
        previous = value
    return tuple(result)


def _source_destination_conflict(
    project: Project,
    destination: Path,
    planned_source_paths: Sequence[Path] = (),
) -> Path | None:
    resolved_destination = destination.expanduser().resolve()
    aliases = {path.expanduser().resolve() for path in planned_source_paths}
    project_sources = project.sources if project.sources is not None else ()
    sources = (project.source, *project_sources)
    for source in sources:
        aliases.add(Path(source.path).expanduser().resolve())
        parsed_uri = urlparse(source.uri)
        if parsed_uri.scheme == "file":
            uri_path = unquote(parsed_uri.path)
            if parsed_uri.netloc and parsed_uri.netloc != "localhost":
                uri_path = f"//{parsed_uri.netloc}{uri_path}"
            aliases.add(Path(uri_path).expanduser().resolve())
    for source_path in aliases:
        if resolved_destination == source_path:
            return source_path
    return None


def plan_project_video(
    project: Project,
    destination: Path,
    *,
    target_rate: Fraction | int | float | str | None = None,
    frame_rate_policy: (
        FrameRatePolicy | ResolvedFrameRatePolicy | Mapping[str, object] | None
    ) = None,
    upscale_policy: (UpscalePolicy | ResolvedUpscalePolicy | Mapping[str, object] | None) = None,
    ffprobe_path: str = "ffprobe",
    cancel_event: threading.Event | None = None,
    progress_callback: ExportProgressCallback | None = None,
    source_hash_cache: SourceHashCache | None = None,
    runtime_cache: RuntimeValidationCache | None = None,
) -> VideoRenderPlan:
    """Plan the final-slot, video-only render without mutating the project."""
    if not isinstance(project, Project):
        raise VideoCompositorPlanningError("project must be a Project")
    check_export_cancelled(cancel_event)
    if not isinstance(destination, Path):
        destination = Path(destination)
    destination = destination.expanduser().resolve()
    if destination.name in {"", ".", ".."}:
        raise VideoCompositorPlanningError("A file destination is required")
    conflict = _source_destination_conflict(project, destination)
    if conflict is not None:
        raise VideoCompositorPlanningError(
            f"Export destination must differ from project source media: {conflict.name}",
        )

    try:
        project.validate()
    except ProjectValidationError as error:
        raise VideoCompositorPlanningError(f"Project validation failed: {error}") from error

    sources = active_export_sources(project)
    started = time.monotonic()
    probe_items = []
    for index, source in enumerate(sources):
        check_export_cancelled(cancel_event)
        report_preparation_progress(
            progress_callback, "Inspecting export sources", index, len(sources), started
        )
        probe_items.append(
            _probe_source(
                source.source_id,
                Path(source.path),
                ffprobe_path=ffprobe_path,
                cancel_event=cancel_event,
                source_hash_cache=source_hash_cache,
                heartbeat_callback=make_progress_heartbeat(
                    progress_callback,
                    stage="Inspecting export sources",
                    total_frames=len(sources),
                    frame=index,
                    started=started,
                    percent=index * 100 / len(sources),
                ),
            )
        )
    probes = tuple(probe_items)
    check_export_cancelled(cancel_event)
    runtime_cache = {} if runtime_cache is None else runtime_cache
    source_geometries = {item.source_id: item.geometry for item in probes}
    try:
        layout = plan_project_layout(
            project,
            source_geometries,
            canvas=DEFAULT_CANVAS,
        )
    except LayoutPlanError as error:
        raise VideoCompositorPlanningError(
            f"Could not plan synchronized layout: {error}",
        ) from error

    metadata = tuple(item.metadata for item in probes)
    resolved_fps = _resolve_frame_rate_policy(
        metadata,
        project,
        target_rate=target_rate,
        frame_rate_policy=frame_rate_policy,
        runtime_cache=runtime_cache,
    )
    resolved_upscale = _resolve_upscale_policy(
        metadata,
        project,
        policy=upscale_policy,
    )
    routes = tuple(
        _processing_route(
            item,
            resolved_fps,
            resolved_upscale,
            runtime_cache=runtime_cache,
        )
        for item in probes
    )
    route_by_source = {item.source_id: item for item in routes}
    probe_by_source = {item.source_id: item for item in probes}
    preparation_identities = tuple(
        _preparation_identity(
            block,
            probe_by_source[block.source_id],
            route_by_source[block.source_id],
        )
        for block in layout.included_blocks
    )
    boundaries = cumulative_frame_boundaries(layout.boundaries, resolved_fps.policy.target_rate)
    counts = tuple(
        right - left for left, right in zip(boundaries[:-1], boundaries[1:], strict=True)
    )
    expected_frames = boundaries[-1]
    if expected_frames <= 0 or any(count < 0 for count in counts):
        raise VideoCompositorPlanningError("The planned timeline has no positive output frames")
    return VideoRenderPlan(
        project=project,
        destination=destination,
        layout_plan=layout,
        probed_metadata=probes,
        target_rate=resolved_fps.policy.target_rate,
        frame_boundaries=boundaries,
        interval_frame_counts=counts,
        expected_frames=expected_frames,
        include_audio=False,
        frame_rate_policy=resolved_fps,
        upscale_policy=resolved_upscale,
        processing_routes=routes,
        preparation_identities=preparation_identities,
    )


def render_project_video(
    plan: VideoRenderPlan,
    *,
    ffmpeg_path: str = "ffmpeg",
    ffprobe_path: str = "ffprobe",
    cancel_event: threading.Event | None = None,
    cancellation_lock: threading.Lock | None = None,
    progress_callback: ExportProgressCallback | None = None,
    preparations: RenderPreparations | None = None,
) -> VideoRenderResult:
    """Render, verify, and atomically publish a planned video-only composition."""
    if not isinstance(plan, VideoRenderPlan):
        raise VideoCompositorExecutionError("plan must be a VideoRenderPlan")
    if plan.include_audio:
        raise VideoCompositorExecutionError("Video compositor cannot render audio")
    conflict = _source_destination_conflict(
        plan.project,
        plan.destination,
        plan.source_paths,
    )
    if conflict is not None:
        raise VideoCompositorExecutionError(
            f"Export destination must differ from project source media: {conflict.name}",
        )
    if shutil.which(ffmpeg_path) is None:
        raise VideoCompositorExecutionError(f"FFmpeg executable was not found: {ffmpeg_path}")
    if shutil.which(ffprobe_path) is None:
        raise VideoCompositorExecutionError(f"ffprobe executable was not found: {ffprobe_path}")

    destination = plan.destination
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = partial_path(destination)
    workspace = destination.parent / f".{destination.name}.video-compositor-{uuid.uuid4().hex}"
    workspace.mkdir(parents=True, exist_ok=False)
    source_hashes = tuple(item.source_hash for item in plan.probed_metadata)
    fallbacks: list[str] = []
    started = time.monotonic()
    preparation_end = (
        80.0
        if any(
            route.upscale_requested or route.fps_action == "interpolate"
            for route in plan.processing_routes
        )
        else 0.0
    )
    try:
        source_stats = tuple(item.path.stat() for item in plan.probed_metadata)
        assets = _prepare_assets(
            plan,
            workspace,
            ffmpeg_path=ffmpeg_path,
            ffprobe_path=ffprobe_path,
            fallbacks=fallbacks,
            cancel_event=cancel_event,
            progress_callback=progress_scope(progress_callback, 0, preparation_end),
            preparations=preparations,
        )
        composition_progress = progress_scope(progress_callback, preparation_end, 98)
        if _needs_bounded_composition(plan, assets):
            _render_bounded_composition(
                plan,
                assets,
                output=partial,
                workspace=workspace,
                ffmpeg_path=ffmpeg_path,
                ffprobe_path=ffprobe_path,
                cancel_event=cancel_event,
                progress_callback=composition_progress,
                preparations=preparations,
            )
        else:
            command = _build_render_command(
                plan,
                assets,
                output=partial,
                ffmpeg_path=ffmpeg_path,
            )
            run_ffmpeg(
                command,
                cancel_event=cancel_event,
                stage="video composition",
                command_duration_seconds=plan.expected_duration_seconds,
                command_total_frames=plan.expected_frames,
                progress_total_duration_seconds=plan.expected_duration_seconds,
                progress_total_frames=plan.expected_frames,
                progress_callback=composition_progress,
            )
        report_preparation_progress(
            progress_scope(progress_callback, 98, 100),
            "Verifying video composition",
            0,
            1,
            started,
        )
        _verify_rendered_output(
            partial,
            plan,
            ffprobe_path=ffprobe_path,
            ffmpeg_path=ffmpeg_path,
            cancel_event=cancel_event,
        )
        output_probe = probe_media(partial, ffprobe_path)
        actual_frames = probe_frame_count(partial, ffprobe_path, cancel_event=cancel_event)
        current_hashes = tuple(
            _sha256(path, cancel_event=cancel_event, persistent=True) for path in plan.source_paths
        )
        if current_hashes != source_hashes:
            raise VideoCompositorExecutionError(
                "A source changed during rendering; output was not published",
            )
        if tuple(path.stat() for path in plan.source_paths) != source_stats:
            raise VideoCompositorExecutionError(
                "Source metadata changed during rendering; output was not published",
            )
        publish_verified_export(
            partial,
            destination,
            plan.source_paths,
            source_stats,
            cancel_event=cancel_event,
            progress_callback=None,
            expected_duration_seconds=plan.expected_duration_seconds,
            total_frames=plan.expected_frames,
            started=started,
            cancellation_lock=cancellation_lock,
        )
        output_probe = replace(output_probe, path=destination)
        report_preparation_progress(
            progress_scope(progress_callback, 98, 100),
            "Verified video composition",
            1,
            1,
            started,
        )
        return VideoRenderResult(
            destination=destination,
            output_probe=output_probe,
            actual_frames=actual_frames,
            expected_frames=plan.expected_frames,
            source_hashes_unchanged=True,
            processing_fallbacks=tuple(fallbacks),
        )
    except ExportExecutionError as error:
        raise VideoCompositorExecutionError(str(error)) from error
    except (OSError, MediaProbeError, VideoCompositorError) as error:
        if isinstance(error, VideoCompositorError):
            raise
        raise VideoCompositorExecutionError(str(error)) from error
    finally:
        cleanup_error = _cleanup_render_artifacts(partial, workspace)
        if cleanup_error is not None:
            active_error = sys.exc_info()[1]
            if active_error is not None:
                raise VideoCompositorExecutionError(
                    f"Render failed: {active_error}; cleanup failed: {cleanup_error}",
                ) from active_error
            else:
                raise VideoCompositorExecutionError(str(cleanup_error)) from cleanup_error


def _cleanup_render_artifacts(partial: Path, workspace: Path) -> OSError | None:
    errors: list[str] = []
    partial_error = remove_partial(partial)
    if partial_error is not None:
        errors.append(f"Could not remove partial output {partial.name}: {partial_error}")
    try:
        shutil.rmtree(workspace)
    except FileNotFoundError:
        pass
    except OSError as error:
        errors.append(f"Could not remove render workspace {workspace.name}: {error}")
    if not errors:
        return None
    return OSError("; ".join(errors))


def _probe_source(
    source_id: str,
    path: Path,
    *,
    ffprobe_path: str = "ffprobe",
    cancel_event: threading.Event | None = None,
    source_hash_cache: SourceHashCache | None = None,
    heartbeat_callback: Callable[[], None] | None = None,
) -> VideoSourceProbe:
    resolved_path = Path(path).expanduser().resolve()
    try:
        media = probe_media(resolved_path, ffprobe_path)
        sample_aspect_ratio = _probe_sample_aspect_ratio(resolved_path, ffprobe_path)
        source_stat = resolved_path.stat()
    except (OSError, MediaProbeError, VideoCompositorPlanningError) as error:
        raise VideoCompositorPlanningError(
            f"Could not probe source {source_id}: {error}",
        ) from error
    try:
        source_hash = _sha256(
            resolved_path,
            persistent=True,
            cancel_event=cancel_event,
            source_hash_cache=source_hash_cache,
            heartbeat_callback=heartbeat_callback,
        )
        geometry = SourceGeometry(
            source_id,
            media.width,
            media.height,
            sar_num=sample_aspect_ratio[0],
            sar_den=sample_aspect_ratio[1],
        )
    except (ExportExecutionError, OSError, VideoCompositorError) as error:
        raise VideoCompositorPlanningError(
            f"Could not prepare source {source_id}: {error}",
        ) from error
    return VideoSourceProbe(
        source_id=source_id,
        path=resolved_path,
        media=media,
        geometry=geometry,
        sample_aspect_ratio=sample_aspect_ratio,
        frame_count=None,
        source_hash=source_hash,
        source_stat=source_stat,
    )


def _probe_sample_aspect_ratio(path: Path, ffprobe_path: str) -> tuple[int, int]:
    result = subprocess.run(
        [
            ffprobe_path,
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=sample_aspect_ratio",
            "-of",
            "json",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise VideoCompositorPlanningError(
            result.stderr.strip() or f"Could not probe SAR for {path.name}",
        )
    try:
        streams = json.loads(result.stdout)["streams"]
        value = streams[0].get("sample_aspect_ratio")
    except (IndexError, KeyError, TypeError, json.JSONDecodeError) as error:
        raise VideoCompositorPlanningError(f"Could not read SAR for {path.name}") from error
    if value in (None, "", "N/A", "0:1", "0/1"):
        return (1, 1)
    if not isinstance(value, str):
        raise VideoCompositorPlanningError(f"Invalid SAR for {path.name}: {value!r}")
    return _parse_ratio(value, f"sample aspect ratio for {path.name}")


def _parse_ratio(value: str, label: str) -> tuple[int, int]:
    separator = "/" if "/" in value else ":"
    pieces = value.split(separator)
    if len(pieces) != 2:
        raise VideoCompositorPlanningError(f"Invalid {label}: {value!r}")
    try:
        numerator = int(pieces[0])
        denominator = int(pieces[1])
    except ValueError as error:
        raise VideoCompositorPlanningError(f"Invalid {label}: {value!r}") from error
    if numerator <= 0 or denominator <= 0:
        raise VideoCompositorPlanningError(f"Invalid {label}: {value!r}")
    divisor = math.gcd(numerator, denominator)
    return numerator // divisor, denominator // divisor


def _resolve_frame_rate_policy(
    metadata: Sequence[Mapping[str, Any]],
    project: Project,
    *,
    target_rate: Fraction | int | float | str | None,
    frame_rate_policy: (FrameRatePolicy | ResolvedFrameRatePolicy | Mapping[str, object] | None),
    runtime_cache: RuntimeValidationCache | None = None,
) -> ResolvedFrameRatePolicy:
    if target_rate is not None and frame_rate_policy is not None:
        raise VideoCompositorPlanningError(
            "target_rate and frame_rate_policy are mutually exclusive",
        )
    try:
        if target_rate is not None:
            rate = canonical_rate(target_rate)
            policy = FrameRatePolicy(
                choice="custom",
                target_rate=rate,
                custom_rate=rate,
                enhancement_enabled=True,
                backend=DEFAULT_FPS_BACKEND,
            )
            resolved = resolve_frame_rate_policy(
                metadata,
                choice=policy.choice,
                custom_rate=policy.custom_rate,
                enhancement_enabled=policy.enhancement_enabled,
                backend=policy.backend,
            )
        elif isinstance(frame_rate_policy, ResolvedFrameRatePolicy):
            resolved = frame_rate_policy
        elif frame_rate_policy is None:
            persisted = project.output_settings.get("frame_rate_policy")
            if persisted is None:
                resolved = resolve_frame_rate_policy(metadata)
            else:
                normalized = FrameRatePolicy.from_dict(persisted)
                resolved = resolve_frame_rate_policy(
                    metadata,
                    choice=normalized.choice,
                    custom_rate=normalized.custom_rate,
                    enhancement_enabled=normalized.enhancement_enabled,
                    backend=normalized.backend,
                )
        else:
            normalized = (
                frame_rate_policy
                if isinstance(frame_rate_policy, FrameRatePolicy)
                else FrameRatePolicy.from_dict(frame_rate_policy)
            )
            resolved = resolve_frame_rate_policy(
                metadata,
                choice=normalized.choice,
                custom_rate=normalized.custom_rate,
                enhancement_enabled=normalized.enhancement_enabled,
                backend=normalized.backend,
            )
    except FrameRatePolicyError as error:
        raise VideoCompositorPlanningError(f"Invalid frame-rate policy: {error}") from error

    if not resolved.policy.enhancement_enabled:
        return resolved
    if not any(item.action in {"interpolate", "unsupported"} for item in resolved.decisions):
        return resolved
    validate_backend = partial(
        validate_interpolation_backend,
        runtime_cache={} if runtime_cache is None else runtime_cache,
    )
    validations = tuple(
        validate_backend(
            resolved.policy.backend,
            source_rate=item.source_rate,
            target_rate=item.target_rate,
        )
        for item in resolved.decisions
        if item.action in {"interpolate", "unsupported"}
    )
    if all(item.available for item in validations):
        return resolved
    if not resolved.policy.backend.casefold().strip().startswith("rve"):
        return resolved
    fallback = resolve_frame_rate_policy(
        metadata,
        choice=resolved.policy.choice,
        custom_rate=resolved.policy.custom_rate,
        enhancement_enabled=resolved.policy.enhancement_enabled,
        backend=DEFAULT_FPS_FALLBACK_BACKEND,
    )
    fallback_validations = tuple(
        validate_backend(
            fallback.policy.backend,
            source_rate=item.source_rate,
            target_rate=item.target_rate,
        )
        for item in fallback.decisions
        if item.action in {"interpolate", "unsupported"}
    )
    if (
        all(item.available for item in fallback_validations)
        and not fallback.has_unsupported_sources
    ):
        return fallback
    if resolved.has_unsupported_sources or fallback.has_unsupported_sources:
        reasons = "; ".join(
            item.reason
            for item in (*resolved.decisions, *fallback.decisions)
            if item.action == "unsupported"
        )
        raise VideoCompositorPlanningError(
            f"Video frame-rate preparation is unsupported: {reasons}",
        )
    return resolved


def _resolve_upscale_policy(
    metadata: Sequence[Mapping[str, Any]],
    project: Project,
    policy: UpscalePolicy | ResolvedUpscalePolicy | Mapping[str, object] | None,
) -> ResolvedUpscalePolicy:
    try:
        if isinstance(policy, ResolvedUpscalePolicy):
            return policy
        if policy is None:
            persisted = project.output_settings.get("upscale_policy")
            if persisted is None:
                return resolve_upscale_policy(metadata)
            return resolve_upscale_policy(
                metadata,
                policy=UpscalePolicy.from_dict(persisted),
            )
        normalized = (
            policy if isinstance(policy, UpscalePolicy) else UpscalePolicy.from_dict(policy)
        )
        return resolve_upscale_policy(metadata, policy=normalized)
    except UpscalePolicyError as error:
        raise VideoCompositorPlanningError(f"Invalid upscale policy: {error}") from error


def _processing_route(
    source: VideoSourceProbe,
    frame_rate_policy: ResolvedFrameRatePolicy,
    upscale_policy: ResolvedUpscalePolicy,
    *,
    runtime_cache: RuntimeValidationCache | None = None,
) -> VideoProcessingRoute:
    fps_decision = next(
        item for item in frame_rate_policy.decisions if item.source_id == source.source_id
    )
    upscale_decision = next(
        item for item in upscale_policy.decisions if item.source_id == source.source_id
    )
    fps_status = "passthrough" if fps_decision.action == "passthrough" else "planned"
    fps_reason = fps_decision.reason
    if fps_decision.action == "unsupported":
        fps_status = "unsupported"
    upscale_requested = upscale_decision.eligible
    upscale_status = "not-requested"
    upscale_reason = upscale_decision.reason
    if upscale_requested:
        upscale_status, upscale_reason = _upscale_runtime_status(
            upscale_policy.policy,
            upscale_decision,
            runtime_cache=runtime_cache,
        )
    return VideoProcessingRoute(
        source_id=source.source_id,
        source_rate=canonical_rate(source.media.frame_rate),
        target_rate=frame_rate_policy.policy.target_rate,
        fps_action=fps_decision.action,
        fps_backend=frame_rate_policy.policy.backend,
        fps_status=fps_status,
        fps_reason=fps_reason,
        upscale_requested=upscale_requested,
        upscale_backend=upscale_policy.policy.backend,
        upscale_status=upscale_status,
        upscale_reason=upscale_reason,
        upscale_model=upscale_decision.model,
    )


def _preparation_identity(
    block: PlannedBlock,
    source: VideoSourceProbe,
    route: VideoProcessingRoute,
) -> VideoPreparationIdentity:
    transform = block.visual_transform
    modification_identity = (
        "native-preparation-v2",
        transform.version,
        transform.zoom,
        transform.offset_x,
        transform.offset_y,
        "triplicate" if block.triplicate_enabled else "single",
    )
    policy_identity = (
        "video-preparation-v1",
        route.fps_action,
        route.fps_backend,
        route.target_rate,
        route.upscale_requested,
        route.upscale_backend,
        route.upscale_model,
    )
    return VideoPreparationIdentity(
        block_id=block.block_id,
        source_id=block.source_id,
        source_hash=source.source_hash,
        source_range_ticks=(
            block.source_range.source_start_tick,
            block.source_range.source_end_tick,
        ),
        target_rate=route.target_rate,
        modification_identity=modification_identity,
        policy_identity=policy_identity,
    )


def _upscale_runtime_status(
    policy: UpscalePolicy,
    decision: UpscaleDecision,
    *,
    runtime_cache: RuntimeValidationCache | None = None,
) -> tuple[str, str]:
    if not policy.backend.casefold().strip().startswith("rve"):
        return "unavailable", f"Unsupported dynamic upscale backend: {policy.backend}"
    try:
        from framestudio_fps import (
            DEFAULT_FPS_PYTHON,
            DEFAULT_FPS_SITE,
            DEFAULT_RVE_MODEL,
            DEFAULT_RVE_RESTORATION_MODEL,
            DEFAULT_RVE_ROOT,
            DEFAULT_RVE_SHIMS,
        )

        reason = validate_rve_runtime(
            argparse.Namespace(
                python=DEFAULT_FPS_PYTHON,
                site_packages=DEFAULT_FPS_SITE,
                rve_model=DEFAULT_RVE_MODEL,
                rve_root=DEFAULT_RVE_ROOT,
                rve_shims=DEFAULT_RVE_SHIMS,
            ),
            runtime_cache,
        )
    except (ImportError, OSError, RuntimeError) as error:
        return "unavailable", str(error)
    if reason is not None:
        return "unavailable", reason
    model = decision.model or policy.model
    model_path = _restoration_model_path(model, DEFAULT_RVE_RESTORATION_MODEL)
    if not model_path.is_file():
        return "unavailable", f"RVE restoration model was not found: {model_path}"
    return "available", f"Validated RVE restoration runtime is available for {model}"


def _restoration_model_path(model: str, default_path: Path) -> Path:
    candidate = Path(model).expanduser()
    if model == "SuperUltraCompact" or not candidate.is_absolute():
        return default_path.expanduser().resolve()
    return candidate.resolve()


def _renderable_block_ids(plan: VideoRenderPlan) -> set[str]:
    block_ids: set[str] = set()
    for interval, frame_count in zip(
        plan.layout_plan.intervals,
        plan.interval_frame_counts,
        strict=True,
    ):
        if frame_count <= 0:
            continue
        block_ids.update(slot.block.block_id for slot in interval.slots)
    return block_ids


def _prepare_assets(
    plan: VideoRenderPlan,
    workspace: Path,
    *,
    ffmpeg_path: str,
    ffprobe_path: str,
    fallbacks: list[str],
    cancel_event: threading.Event | None = None,
    progress_callback: ExportProgressCallback | None = None,
    preparations: RenderPreparations | None = None,
) -> dict[str, _PreparedAsset]:
    routes = {item.source_id: item for item in plan.processing_routes}
    probes = {item.source_id: item for item in plan.probed_metadata}
    renderable_block_ids = _renderable_block_ids(plan)
    assets: dict[str, _PreparedAsset] = {}
    prepared_by_content: dict[str, _PreparedAsset] = {}
    started = time.monotonic()
    blocks = plan.layout_plan.included_blocks
    report_preparation_progress(
        progress_scope(progress_callback, 0, 0),
        "Preparing video segments",
        0,
        len(blocks),
        started,
    )
    check_export_cancelled(cancel_event)
    work = {
        _preparation_identity(
            block, probes[block.source_id], routes[block.source_id]
        ).cache_key: max(1, block.source_range.source_duration_ticks)
        for block in blocks
        if block.block_id in renderable_block_ids
        and (
            routes[block.source_id].upscale_requested
            or routes[block.source_id].fps_action == "interpolate"
        )
    }
    total_work = sum(work.values()) or 1
    completed_work = 0
    for block in blocks:
        check_export_cancelled(cancel_event)
        if block.block_id not in renderable_block_ids:
            continue
        route = routes[block.source_id]
        if not route.upscale_requested and route.fps_action != "interpolate":
            continue
        probe = probes[block.source_id]
        identity = _preparation_identity(block, probe, route).cache_key
        if identity in prepared_by_content:
            assets[block.block_id] = prepared_by_content[identity]
            continue
        item_progress = progress_scope(
            progress_callback,
            100 * completed_work / total_work,
            100 * (completed_work + work[identity]) / total_work,
        )
        report_preparation_progress(
            item_progress,
            f"Preparing video segment {len(prepared_by_content) + 1}/{len(work)}",
            0,
            1,
            started,
        )
        source_frames = _round_half_up(
            Fraction(block.source_range.source_duration_ticks, PROJECT_TIMEBASE)
            * canonical_rate(probe.media.frame_rate),
        )
        source_frames = max(1, source_frames)
        asset_stem = _asset_stem(block.block_id)
        raw = workspace / f"{asset_stem}-native.mp4"
        request: dict[str, Any] = {
            "source_hash": probe.source_hash,
            "source_range": (
                block.source_range.source_start_tick,
                block.source_range.source_end_tick,
            ),
            "source_frames": source_frames,
            "source_rate": str(canonical_rate(probe.media.frame_rate)),
            "runtime": (
                preparations.runtime(ffmpeg_path, ffprobe_path)
                if preparations is not None
                else None
            ),
        }
        raw = _materialize_video_stage(
            preparations,
            "native segment",
            request,
            raw,
            partial(
                _extract_block,
                probe.path,
                start_seconds=block.source_range.source_start_tick / PROJECT_TIMEBASE,
                end_seconds=block.source_range.source_end_tick / PROJECT_TIMEBASE,
                expected_frames=source_frames,
                ffmpeg_path=ffmpeg_path,
                cancel_event=cancel_event,
            ),
            ffmpeg_path=ffmpeg_path,
            ffprobe_path=ffprobe_path,
            cancel_event=cancel_event,
            progress_callback=progress_scope(item_progress, 0, 5),
        )
        current = raw
        if route.upscale_requested:
            if route.upscale_status == "available":
                restored = workspace / f"{asset_stem}-restored.mp4"
                try:
                    model_path = _restoration_model_path(
                        route.upscale_model or "SuperUltraCompact",
                        _default_restoration_model(),
                    )
                    restored_request = {
                        "input": request,
                        "model": (
                            preparations.model_identity(model_path)
                            if preparations is not None
                            else str(model_path)
                        ),
                        "runtime": (
                            preparations.runtime(ffmpeg_path, ffprobe_path, neural=True)
                            if preparations is not None
                            else None
                        ),
                    }
                    restored = _materialize_video_stage(
                        preparations,
                        "upscaled segment",
                        restored_request,
                        restored,
                        partial(
                            _run_rve_restoration,
                            current,
                            probe=probe,
                            source_frames=source_frames,
                            model_path=model_path,
                            cancel_event=cancel_event,
                        ),
                        ffmpeg_path=ffmpeg_path,
                        ffprobe_path=ffprobe_path,
                        cancel_event=cancel_event,
                        progress_callback=progress_scope(item_progress, 5, 30),
                    )
                    current = restored
                    request = restored_request
                except PreparationCacheError:
                    raise
                except (ExportExecutionError, OSError, RuntimeError, VideoCompositorError) as error:
                    record_export_error(error)
                    check_export_cancelled(cancel_event)
                    fallbacks.append(
                        f"{block.block_id}: RVE upscale unavailable at render time; "
                        f"native scaling fallback used ({error})",
                    )
            else:
                fallbacks.append(
                    f"{block.block_id}: upscale unavailable; native scaling fallback used "
                    f"({route.upscale_reason})",
                )
        if route.fps_action == "interpolate":
            target_frames = _round_half_up(
                Fraction(block.source_range.source_duration_ticks, PROJECT_TIMEBASE)
                * plan.target_rate,
            )
            target_frames = max(1, target_frames)
            interpolated = workspace / f"{asset_stem}-fps.mp4"
            interpolation_source_rate = canonical_rate(probe.media.frame_rate)
            interpolation_progress = progress_scope(
                item_progress, 30 if route.upscale_requested else 5, 100
            )
            interpolation_requests = {
                backend: {
                    "input": request,
                    "backend": backend,
                    "target_rate": str(plan.target_rate),
                    "target_frames": target_frames,
                    "runtime": (
                        preparations.runtime(
                            ffmpeg_path, ffprobe_path, neural=backend.startswith("rve")
                        )
                        if preparations is not None
                        else None
                    ),
                }
                for backend in dict.fromkeys((route.fps_backend, DEFAULT_FPS_FALLBACK_BACKEND))
            }

            def interpolate(
                backend: str,
                *,
                input_path: Path = current,
                destination: Path = interpolated,
                source_rate: Fraction = interpolation_source_rate,
                input_frames: int = source_frames,
                output_frames: int = target_frames,
                requests: Mapping[str, Any] = interpolation_requests,
                callback: ExportProgressCallback | None = interpolation_progress,
            ) -> Path:
                return _materialize_video_stage(
                    preparations,
                    "interpolated segment",
                    requests[backend],
                    destination,
                    partial(
                        run_source_interpolation,
                        input_path,
                        source_rate=source_rate,
                        source_frames=input_frames,
                        target_rate=plan.target_rate,
                        target_frames=output_frames,
                        backend=backend,
                        ffmpeg_path=ffmpeg_path,
                        artifact_gate=False,
                        cancel_event=cancel_event,
                        progress_callback=callback,
                    ),
                    ffmpeg_path=ffmpeg_path,
                    ffprobe_path=ffprobe_path,
                    cancel_event=cancel_event,
                    progress_callback=callback,
                )

            try:
                cached = None
                if preparations is not None:
                    for backend, interpolation_request in interpolation_requests.items():
                        cached = preparations.reuse(
                            "interpolated segment",
                            interpolation_request,
                            progress_callback=interpolation_progress,
                        )
                        if cached is not None:
                            if backend != route.fps_backend:
                                fallbacks.append(
                                    f"{block.block_id}: reusing verified {backend} fallback"
                                )
                            break
                current = cached if cached is not None else interpolate(route.fps_backend)
                fps_converted = True
            except PreparationCacheError:
                raise
            except (ExportExecutionError, OSError, RuntimeError, VideoCompositorError) as error:
                record_export_error(error)
                check_export_cancelled(cancel_event)
                if route.fps_backend != DEFAULT_FPS_FALLBACK_BACKEND:
                    try:
                        current = interpolate(DEFAULT_FPS_FALLBACK_BACKEND)
                        fps_converted = True
                        fallbacks.append(
                            f"{block.block_id}: {route.fps_backend} failed; "
                            "verified FFmpeg minterpolate fallback used",
                        )
                    except (
                        ExportExecutionError,
                        OSError,
                        RuntimeError,
                        VideoCompositorError,
                    ) as fallback_error:
                        raise VideoCompositorExecutionError(
                            f"{block.block_id}: interpolation failed with "
                            f"{route.fps_backend} ({error}); verified fallback "
                            f"{DEFAULT_FPS_FALLBACK_BACKEND} also failed "
                            f"({fallback_error})",
                        ) from fallback_error
                else:
                    raise VideoCompositorExecutionError(
                        f"{block.block_id}: interpolation failed with {route.fps_backend}: {error}",
                    ) from error
        else:
            fps_converted = False
        assets[block.block_id] = _PreparedAsset(
            path=current,
            fps_converted=fps_converted,
        )
        prepared_by_content[identity] = assets[block.block_id]
        completed_work += work[identity]
        report_preparation_progress(
            item_progress,
            f"Prepared video segment {len(prepared_by_content)}/{len(work)}",
            1,
            1,
            started,
        )
        if preparations is None:
            _verify_preparation(current, ffprobe_path, ffmpeg_path, cancel_event=cancel_event)
    return assets


def _materialize_video_stage(
    preparations: RenderPreparations | None,
    stage: str,
    request: Mapping[str, Any],
    destination: Path,
    produce: Callable[[Path], object],
    *,
    ffmpeg_path: str,
    ffprobe_path: str,
    cancel_event: threading.Event | None,
    progress_callback: ExportProgressCallback | None = None,
) -> Path:
    if preparations is None:
        produce(destination)
        return destination

    def validate(path: Path) -> None:
        try:
            _verify_preparation(path, ffprobe_path, ffmpeg_path, cancel_event=cancel_event)
        except VideoCompositorExecutionError as error:
            raise ExportExecutionError(str(error)) from error

    return preparations.materialize(
        stage,
        request,
        produce,
        validate,
        progress_callback=progress_callback,
    )


def _extract_block(
    source: Path,
    destination: Path,
    start_seconds: float,
    end_seconds: float,
    expected_frames: int,
    ffmpeg_path: str,
    *,
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
        str(source),
        "-vf",
        f"trim=start={start_seconds:.9f}:end={end_seconds:.9f},setpts=PTS-STARTPTS",
        "-frames:v",
        str(expected_frames),
        "-an",
        "-c:v",
        "libx264",
        "-preset",
        "ultrafast",
        "-pix_fmt",
        "yuv420p",
        str(destination),
    ]
    from .export_process import run_command_with_cancellation

    result = run_command_with_cancellation(command, cancel_event=cancel_event)
    if result.returncode != 0:
        raise VideoCompositorExecutionError(
            result.stderr.strip() or f"Could not extract {source.name}",
        )


def _run_rve_restoration(
    source: Path,
    destination: Path,
    probe: VideoSourceProbe,
    source_frames: int,
    model_path: Path,
    *,
    cancel_event: threading.Event | None = None,
) -> None:
    from framestudio_fps import (
        DEFAULT_FPS_PYTHON,
        DEFAULT_FPS_SITE,
        DEFAULT_RVE_ROOT,
        DEFAULT_RVE_SHIMS,
        run_restoration_rve,
    )

    arguments = argparse.Namespace(
        force=True,
        python=DEFAULT_FPS_PYTHON,
        site_packages=DEFAULT_FPS_SITE,
        rve_root=DEFAULT_RVE_ROOT,
        rve_shims=DEFAULT_RVE_SHIMS,
        restoration_model=model_path,
        encoder="h264_nvenc",
    )
    run_restoration_rve(
        source,
        destination,
        canonical_rate(probe.media.frame_rate),
        source_frames,
        arguments,
        restoration_model=model_path,
        cancel_event=cancel_event,
    )


def _default_restoration_model() -> Path:
    from framestudio_fps import DEFAULT_RVE_RESTORATION_MODEL

    return DEFAULT_RVE_RESTORATION_MODEL


def _verify_preparation(
    path: Path,
    ffprobe_path: str,
    ffmpeg_path: str,
    *,
    cancel_event: threading.Event | None = None,
) -> None:
    try:
        probe_media(path, ffprobe_path)
        probe_frame_count(path, ffprobe_path, cancel_event=cancel_event)
        validate_decoded_output(
            path, ffmpeg_path, label=f"prepared clip {path.name}", cancel_event=cancel_event
        )
    except (ExportExecutionError, OSError, MediaProbeError, VideoCompositorError) as error:
        raise VideoCompositorExecutionError(
            f"Prepared clip verification failed for {path.name}: {error}",
        ) from error


def _crop_plans_for_slot(slot: SlotPlan) -> tuple[CropPlan, ...]:
    if slot.triplicate_crops:
        if len(slot.triplicate_crops) != 3:
            raise VideoCompositorExecutionError(
                f"Triplicate slot {slot.block.block_id} has an invalid crop count",
            )
        return slot.triplicate_crops
    if slot.crop is None:
        raise VideoCompositorExecutionError(
            f"Slot {slot.block.block_id} has no crop plan",
        )
    return (slot.crop,)


def _build_render_command(
    plan: VideoRenderPlan,
    assets: Mapping[str, _PreparedAsset],
    *,
    output: Path,
    ffmpeg_path: str,
    reuse_inputs: bool = True,
    factor_triplicate: bool = True,
    lossless: bool = False,
) -> list[str]:
    inputs: list[Path] = []
    input_indices: dict[Path, int] = {}
    filters: list[str] = []
    interval_labels: list[str] = []
    target_rate = str(plan.target_rate)
    for interval_index, (interval, frame_count) in enumerate(
        zip(plan.layout_plan.intervals, plan.interval_frame_counts, strict=True),
    ):
        if frame_count == 0:
            continue
        if frame_count < 0:
            raise VideoCompositorExecutionError(
                f"Layout interval {interval_index} has a negative frame count",
            )
        if interval.is_black:
            label = f"interval{interval_index}"
            filters.append(
                f"color=c=black:s={DEFAULT_CANVAS.width}x{DEFAULT_CANVAS.height}:"
                f"r={target_rate}:d={frame_count / float(plan.target_rate):.9f},"
                f"format=yuv444p,trim=end_frame={frame_count},setpts=PTS-STARTPTS[{label}]",
            )
            interval_labels.append(label)
            continue
        slot_labels: list[str] = []
        for slot_index, slot in enumerate(interval.slots):
            asset = assets.get(slot.block.block_id)
            input_path = (
                asset.path if asset is not None else _source_path(plan, slot.block.source_id)
            )
            if not reuse_inputs:
                input_index = len(inputs)
                inputs.append(input_path)
            elif input_path not in input_indices:
                input_indices[input_path] = len(inputs)
                inputs.append(input_path)
                input_index = input_indices[input_path]
            else:
                input_index = input_indices[input_path]
            prepared = asset is not None
            fps_ready = asset.fps_converted if asset is not None else False
            source_start = slot.block.source_range.source_start_tick / PROJECT_TIMEBASE
            source_end = slot.block.source_range.source_end_tick / PROJECT_TIMEBASE
            if prepared:
                sample_start = (
                    _interval_source_tick(interval, slot.block)
                    - slot.block.source_range.source_start_tick
                ) / PROJECT_TIMEBASE
                sample_end = (
                    sample_start + (interval.end_tick - interval.start_tick) / PROJECT_TIMEBASE
                )
            else:
                sample_start = source_start + (
                    _interval_source_tick(interval, slot.block) / PROJECT_TIMEBASE - source_start
                )
                sample_end = min(
                    source_end,
                    sample_start + (interval.end_tick - interval.start_tick) / PROJECT_TIMEBASE,
                )
            crop_plans = _crop_plans_for_slot(slot)
            first_crop = crop_plans[0]
            crop_labels: list[str] = []
            trim = f"trim=start={sample_start:.9f}:end={sample_end:.9f}"
            if fps_ready and frame_count == 1:
                start_position = Fraction(f"{sample_start:.9f}") * plan.target_rate
                end_position = Fraction(f"{sample_end:.9f}") * plan.target_rate
                prepared_frames = max(
                    1,
                    _round_half_up(
                        Fraction(slot.block.source_range.source_duration_ticks, PROJECT_TIMEBASE)
                        * plan.target_rate
                    ),
                )
                if (
                    math.ceil(start_position) >= math.ceil(end_position)
                    or math.ceil(start_position) >= prepared_frames
                ):
                    # Quantization can leave a one-frame interval between timestamps or at EOF.
                    covering_frame = min(math.floor(start_position), prepared_frames - 1)
                    trim = f"trim=start_frame={covering_frame}:end_frame={covering_frame + 1}"
            trim_prefix = (
                f"[{input_index}:v]{trim},"
                f"setpts=PTS-STARTPTS,"
                f"{'' if fps_ready else f'fps={target_rate},'}"
                "setsar=1,"
            )
            if len(crop_plans) == 1:
                crop = first_crop
                crop_label = f"i{interval_index}s{slot_index}c0"
                filters.append(
                    f"{trim_prefix}scale={crop.scaled_width}:{crop.scaled_height}:"
                    f"flags=lanczos,format=yuv444p,"
                    f"crop={crop.target.width}:{crop.target.height}:"
                    f"{crop.crop_x}:{crop.crop_y},setsar=1[{crop_label}]",
                )
                crop_labels.append(crop_label)
            else:
                shared_scale = factor_triplicate and all(
                    (crop.scaled_width, crop.scaled_height)
                    == (first_crop.scaled_width, first_crop.scaled_height)
                    for crop in crop_plans
                )
                # Convert before splitting so odd-width crops retain full chroma resolution.
                scale_prefix = (
                    f"scale={first_crop.scaled_width}:{first_crop.scaled_height}:"
                    "flags=lanczos,format=yuv444p,"
                    if shared_scale
                    else ""
                )
                split_labels = [
                    f"i{interval_index}s{slot_index}split{crop_index}"
                    for crop_index in range(len(crop_plans))
                ]
                filters.append(
                    f"{trim_prefix}{scale_prefix}split={len(split_labels)}"
                    + "".join(f"[{label}]" for label in split_labels),
                )
                for crop_index, crop in enumerate(crop_plans):
                    crop_label = f"i{interval_index}s{slot_index}c{crop_index}"
                    branch_scale = (
                        ""
                        if shared_scale
                        else (
                            f"scale={crop.scaled_width}:{crop.scaled_height}:flags=lanczos,"
                            "format=yuv444p,"
                        )
                    )
                    filters.append(
                        f"[{split_labels[crop_index]}]{branch_scale}"
                        f"crop={crop.target.width}:{crop.target.height}:"
                        f"{crop.crop_x}:{crop.crop_y},setsar=1[{crop_label}]",
                    )
                    crop_labels.append(crop_label)
            if len(crop_labels) == 1:
                slot_label = crop_labels[0]
            else:
                slot_label = f"i{interval_index}s{slot_index}trip"
                filters.append(
                    f"{''.join(f'[{label}]' for label in crop_labels)}"
                    f"hstack=inputs={len(crop_labels)}:shortest=1[{slot_label}]",
                )
            slot_labels.append(slot_label)
        interval_label = f"interval{interval_index}"
        if len(slot_labels) == 1:
            filters.append(
                f"[{slot_labels[0]}]format=yuv444p,trim=end_frame={frame_count},"
                f"tpad=stop_mode=clone:stop={frame_count},trim=end_frame={frame_count},"
                f"setpts=PTS-STARTPTS[{interval_label}]",
            )
        else:
            layout = "|".join(f"{slot.slot.x}_{slot.slot.y}" for slot in interval.slots)
            filters.append(
                f"{''.join(f'[{label}]' for label in slot_labels)}"
                f"xstack=inputs={len(slot_labels)}:layout={layout}:fill=black,"
                f"format=yuv444p,trim=end_frame={frame_count},"
                f"tpad=stop_mode=clone:stop={frame_count},trim=end_frame={frame_count},"
                f"setpts=PTS-STARTPTS[{interval_label}]",
            )
        interval_labels.append(interval_label)
    concat_inputs = "".join(f"[{label}]" for label in interval_labels)
    # Concat cannot infer a one-frame interval's duration; keep every planned frame.
    filters.append(
        f"{concat_inputs}concat=n={len(interval_labels)}:v=1:a=0,format=yuv420p,"
        f"settb=expr={plan.target_rate.denominator}/{plan.target_rate.numerator},"
        "setpts=N[vout]",
    )
    budgeted_composition = lossless or len(set(inputs)) >= 3
    decoder_options = ["-threads", "1"] if budgeted_composition else []
    return [
        ffmpeg_path,
        "-hide_banner",
        "-loglevel",
        "error",
        "-nostdin",
        "-y",
        *(["-filter_complex_threads", "2"] if budgeted_composition else []),
        *sum(([*decoder_options, "-i", str(path)] for path in inputs), []),
        "-filter_complex",
        ";".join(filters),
        "-map",
        "[vout]",
        "-an",
        "-r",
        target_rate,
        "-frames:v",
        str(plan.expected_frames),
        *(
            ["-c:v", "ffv1", "-level", "3", "-threads", "2"]
            if lossless
            else ["-c:v", "libx264", "-preset", "ultrafast"]
        ),
        "-pix_fmt",
        "yuv420p",
        *([] if lossless else ["-movflags", "+faststart"]),
        str(output),
    ]


def _needs_bounded_composition(plan: VideoRenderPlan, assets: Mapping[str, _PreparedAsset]) -> bool:
    inputs: set[Path] = set()
    for interval, count in zip(plan.layout_plan.intervals, plan.interval_frame_counts, strict=True):
        if count == 0:
            continue
        for slot in interval.slots:
            asset = assets.get(slot.block.block_id)
            path = asset.path if asset is not None else _source_path(plan, slot.block.source_id)
            # Shared decoders can buffer entire future ranges behind concat/xstack.
            if path in inputs:
                return True
            inputs.add(path)
    return len(inputs) > 4


def _render_bounded_composition(
    plan: VideoRenderPlan,
    assets: Mapping[str, _PreparedAsset],
    *,
    output: Path,
    workspace: Path,
    ffmpeg_path: str,
    ffprobe_path: str,
    cancel_event: threading.Event | None,
    progress_callback: ExportProgressCallback | None,
    preparations: RenderPreparations | None,
) -> None:
    parts: list[Path] = []
    completed_frames = 0
    runtime = preparations.runtime(ffmpeg_path, ffprobe_path) if preparations else None
    for index, (interval, count) in enumerate(
        zip(plan.layout_plan.intervals, plan.interval_frame_counts, strict=True)
    ):
        check_export_cancelled(cancel_event)
        if count == 0:
            continue
        interval_plan = replace(
            plan,
            layout_plan=replace(
                plan.layout_plan,
                intervals=(interval,),
                boundaries=(interval.start_tick, interval.end_tick),
                included_blocks=interval.active_blocks,
            ),
            frame_boundaries=(0, count),
            interval_frame_counts=(count,),
            expected_frames=count,
        )
        callback = progress_scope(
            progress_callback,
            85 * completed_frames / plan.expected_frames,
            85 * (completed_frames + count) / plan.expected_frames,
        )
        command = _build_render_command(
            interval_plan,
            assets,
            output=Path("interval.avi"),
            ffmpeg_path=ffmpeg_path,
            reuse_inputs=False,
            lossless=True,
        )

        def produce(
            path: Path,
            command: list[str] = command,
            interval_plan: VideoRenderPlan = interval_plan,
            index: int = index,
            callback: ExportProgressCallback | None = callback,
        ) -> None:
            run_ffmpeg(
                [*command[:-1], str(path)],
                cancel_event=cancel_event,
                stage=f"video composition interval {index + 1}/{len(plan.interval_frame_counts)}",
                command_duration_seconds=interval_plan.expected_duration_seconds,
                command_total_frames=interval_plan.expected_frames,
                progress_total_duration_seconds=interval_plan.expected_duration_seconds,
                progress_total_frames=interval_plan.expected_frames,
                progress_callback=callback,
            )

        def validate(path: Path, interval_plan: VideoRenderPlan = interval_plan) -> None:
            _verify_rendered_output(
                path,
                interval_plan,
                ffprobe_path=ffprobe_path,
                ffmpeg_path=ffmpeg_path,
                cancel_event=cancel_event,
            )

        if preparations is None:
            path = workspace / f"interval-{index}.avi"
            produce(path)
            validate(path)
        else:
            request = {
                "interval_version": 1,
                "command": command,
                "sources": tuple(probe.source_hash for probe in plan.probed_metadata),
                "runtime": runtime,
                "assets": {
                    str(asset.path): (asset.path.stat().st_size, asset.path.stat().st_mtime_ns)
                    for slot in interval.slots
                    if (asset := assets.get(slot.block.block_id)) is not None
                },
            }
            path = preparations.materialize(
                "video composition interval",
                request,
                produce,
                validate,
                suffix=".avi",
                progress_callback=callback,
            )
        parts.append(path)
        completed_frames += count
    listing = workspace / "composition-intervals.txt"
    listing.write_text(
        "".join("file '" + str(path.resolve()).replace("'", "'\\''") + "'\n" for path in parts),
        encoding="utf-8",
    )
    run_ffmpeg(
        [
            ffmpeg_path,
            "-hide_banner",
            "-loglevel",
            "error",
            "-nostdin",
            "-y",
            "-threads",
            "1",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(listing),
            "-map",
            "0:v:0",
            "-an",
            "-vf",
            f"settb=expr={plan.target_rate.denominator}/{plan.target_rate.numerator},setpts=N",
            "-r",
            str(plan.target_rate),
            "-frames:v",
            str(plan.expected_frames),
            "-c:v",
            "libx264",
            "-preset",
            "ultrafast",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(output),
        ],
        cancel_event=cancel_event,
        stage="video composition assembly",
        command_duration_seconds=plan.expected_duration_seconds,
        command_total_frames=plan.expected_frames,
        progress_total_duration_seconds=plan.expected_duration_seconds,
        progress_total_frames=plan.expected_frames,
        progress_callback=progress_scope(progress_callback, 85, 100),
    )


def _verify_rendered_output(
    partial: Path,
    plan: VideoRenderPlan,
    *,
    ffprobe_path: str,
    ffmpeg_path: str,
    cancel_event: threading.Event | None = None,
) -> None:
    if not partial.is_file() or partial.stat().st_size <= 0:
        raise VideoCompositorExecutionError("FFmpeg did not create a non-empty partial output")
    try:
        output = probe_media(partial, ffprobe_path)
        actual_frames = probe_frame_count(
            partial,
            ffprobe_path,
            cancel_event=cancel_event,
        )
        validate_decoded_output(
            partial,
            ffmpeg_path,
            label="composed video",
            cancel_event=cancel_event,
        )
    except (ExportExecutionError, OSError, MediaProbeError, VideoCompositorError) as error:
        raise VideoCompositorExecutionError(
            f"Rendered output verification failed: {error}",
        ) from error
    if output.width != DEFAULT_CANVAS.width or output.height != DEFAULT_CANVAS.height:
        raise VideoCompositorExecutionError(
            f"Rendered dimensions are {output.width}x{output.height}, expected 1920x1080",
        )
    if canonical_rate(output.frame_rate) != plan.target_rate:
        raise VideoCompositorExecutionError(
            f"Rendered FPS is {output.frame_rate}, expected {plan.target_rate}",
        )
    if output.has_audio_stream:
        raise VideoCompositorExecutionError("Video-only render unexpectedly contains audio")
    if actual_frames != plan.expected_frames:
        raise VideoCompositorExecutionError(
            f"Rendered frame count is {actual_frames}, expected {plan.expected_frames}",
        )
    expected_duration = plan.expected_duration_seconds
    duration_tolerance = max(0.05, 2.0 / float(plan.target_rate))
    if abs(output.duration_seconds - expected_duration) > duration_tolerance:
        raise VideoCompositorExecutionError(
            f"Rendered duration is {output.duration_seconds:.6f}s, expected "
            f"{expected_duration:.6f}s",
        )


def _source_probe(plan: VideoRenderPlan, source_id: str) -> VideoSourceProbe:
    try:
        return next(item for item in plan.probed_metadata if item.source_id == source_id)
    except StopIteration as error:
        raise VideoCompositorExecutionError(f"Unknown source in layout: {source_id}") from error


def _source_path(plan: VideoRenderPlan, source_id: str) -> Path:
    return _source_probe(plan, source_id).path


def _interval_source_tick(interval: LayoutInterval, block: PlannedBlock) -> int:
    if not block.timeline_start_tick <= interval.start_tick < block.timeline_end_tick:
        raise VideoCompositorExecutionError(
            f"Interval {interval.start_tick} is outside block {block.block_id}",
        )
    return block.source_range.source_tick_at(interval.start_tick)


def _round_half_up(value: Fraction) -> int:
    if value < 0:
        raise VideoCompositorPlanningError("Frame positions cannot be negative")
    return (value.numerator * 2 + value.denominator) // (2 * value.denominator)


def _safe_name(value: str) -> str:
    return "".join(
        character if character.isalnum() or character in "-_" else "_" for character in value
    )


def _asset_stem(block_id: str) -> str:
    readable = _safe_name(block_id) or "block"
    identity = hashlib.sha256(block_id.encode("utf-8")).hexdigest()[:12]
    return f"{readable}-{identity}"


__all__ = [
    "VideoCompositorError",
    "VideoCompositorExecutionError",
    "VideoCompositorPlanningError",
    "VideoProcessingRoute",
    "VideoPreparationIdentity",
    "VideoRenderPlan",
    "VideoRenderResult",
    "VideoSourceProbe",
    "cumulative_frame_boundaries",
    "plan_project_video",
    "render_project_video",
]
