"""Standalone source-output planning and delivery.

Source outputs intentionally reuse the verified one-source export route.  A
source request from a synchronized timeline is projected into a compact,
legacy one-source project so the existing FFmpeg planner and delivery
verification can be used without passing final-composition placement or
audio state into the reel.
"""

from __future__ import annotations

import math
import threading
import time
from collections.abc import Callable, Mapping, Sequence
from copy import deepcopy
from dataclasses import dataclass, replace
from pathlib import Path
from typing import TYPE_CHECKING, Any, TypedDict

if TYPE_CHECKING:
    from typing_extensions import Unpack

from .export import (
    ExportExecutionError,
    ExportPlan,
    ExportPlanningError,
    ExportProgress,
    execute_export,
)
from .export_coordinator import child_resume_mode
from .export_process import check_export_cancelled, report_preparation_progress
from .fps_policy import (
    FrameRatePolicy,
    FrameRatePolicyError,
    ResolvedFrameRatePolicy,
    policy_source_metadata,
    resolved_from_policy,
)
from .interpolation import RuntimeValidationCache
from .media import MediaProbe, MediaProbeError, probe_media
from .model_project import Project
from .model_timeline import SegmentTimeline
from .model_types import (
    ONE_SOURCE_SCHEMA_VERSION,
    ProjectValidationError,
    Segment,
    SourceReference,
)
from .operations import plan_project_export
from .output_plan import OutputIdentity, OutputRequest
from .upscale_policy import (
    ResolvedUpscalePolicy,
    UpscaleDecision,
    UpscalePolicy,
    UpscalePolicyError,
    resolve_upscale_policy,
)
from .upscale_policy import (
    policy_source_metadata as upscale_policy_source_metadata,
)

_TIME_EPSILON = 1e-9
_FrameRatePolicyInput = FrameRatePolicy | ResolvedFrameRatePolicy | Mapping[str, Any] | None
_UpscalePolicyInput = UpscalePolicy | ResolvedUpscalePolicy | Mapping[str, Any] | None


class _SourcePlanningOptions(TypedDict, total=False):
    ffprobe_path: str
    ffmpeg_path: str
    frame_rate_policy: _FrameRatePolicyInput
    upscale_policy: _UpscalePolicyInput
    plan_project_export_fn: Callable[..., ExportPlan]
    cancel_event: threading.Event | None
    runtime_cache: RuntimeValidationCache | None


class SourceOutputPlanningError(ExportPlanningError):
    """Raised when one standalone source request cannot be planned safely."""


class SourceOutputExecutionError(ExportExecutionError):
    """Raised when source preservation or output verification fails."""


@dataclass(frozen=True)
class SourceOutputPlan:
    """A typed plan for one stable ``(track_id, source_id)`` output."""

    request: OutputRequest
    derived_project: Project
    export_plan: ExportPlan
    frame_rate_policy: FrameRatePolicy
    upscale_policy: UpscalePolicy
    protected_source_paths: tuple[Path, ...]

    @property
    def project(self) -> Project:
        """Compatibility alias for consumers that call the derived project ``project``."""
        return self.derived_project

    @property
    def identity(self) -> OutputIdentity:
        return self.request.identity

    def to_dict(self) -> dict[str, Any]:
        return {
            "identity": self.identity.to_dict(),
            "request": self.request.to_dict(),
            "export_plan": self.export_plan.to_dict(),
            "frame_rate_policy": self.frame_rate_policy.to_dict(),
            "upscale_policy": self.upscale_policy.to_dict(),
            "protected_source_paths": [str(path) for path in self.protected_source_paths],
        }


@dataclass(frozen=True)
class SourceOutputRenderResult:
    """One verified or failed source-output attempt."""

    plan: SourceOutputPlan
    destination: Path
    verified: bool
    output_media: MediaProbe | None = None
    error: str | None = None
    session_mode: str = "fresh"

    @property
    def request(self) -> OutputRequest:
        return self.plan.request

    @property
    def identity(self) -> OutputIdentity:
        return self.plan.identity

    @property
    def status(self) -> str:
        return "verified" if self.verified else "failed"

    def to_dict(self) -> dict[str, Any]:
        output: dict[str, Any] = {
            "identity": self.identity.to_dict(),
            "destination": str(self.destination),
            "status": self.status,
            "verified": self.verified,
            "session": {"mode": self.session_mode},
        }
        if self.error is not None:
            output["error"] = self.error
        if self.output_media is not None:
            output["output"] = {
                "duration_seconds": self.output_media.duration_seconds,
                "width": self.output_media.width,
                "height": self.output_media.height,
                "frame_rate": self.output_media.frame_rate,
                "video_codec": self.output_media.video_codec,
                "audio_codec": self.output_media.audio_codec,
                "format_name": self.output_media.format_name,
                "audio_stream_present": self.output_media.has_audio_stream,
            }
        return output


@dataclass(frozen=True)
class SourceOutputRenderSummary:
    """All plans and per-request results for one source-output batch."""

    plans: tuple[SourceOutputPlan, ...]
    results: tuple[SourceOutputRenderResult, ...]

    @property
    def verified_count(self) -> int:
        return sum(1 for result in self.results if result.verified)

    @property
    def failed_count(self) -> int:
        return len(self.results) - self.verified_count

    @property
    def verified(self) -> bool:
        return bool(self.results) and self.failed_count == 0

    @property
    def partial_success(self) -> bool:
        return 0 < self.verified_count < len(self.results)

    def to_dict(self) -> dict[str, Any]:
        return {
            "planned_count": len(self.plans),
            "verified_count": self.verified_count,
            "failed_count": self.failed_count,
            "verified": self.verified,
            "partial_success": self.partial_success,
            "outputs": [result.to_dict() for result in self.results],
        }


def derive_standalone_source_project(
    project: Project,
    request: OutputRequest,
    *,
    frame_rate_policy: _FrameRatePolicyInput = None,
    upscale_policy: _UpscalePolicyInput = None,
) -> Project:
    """Project one source request into compact one-source legacy timing."""
    source = _source_for_request(project, request)
    selected_frame_rate = _source_frame_rate_policy(project, source, frame_rate_policy)
    selected_upscale = _source_upscale_policy(project, source, upscale_policy)
    source_duration = _source_duration(source)
    segments = _standalone_segments(request, source_duration)
    timeline = SegmentTimeline.from_segments(source_duration, segments)
    settings = deepcopy(project.output_settings)
    settings["frame_rate_policy"] = selected_frame_rate.to_dict()
    settings["upscale_policy"] = selected_upscale.to_dict()
    source_copy = deepcopy(source)
    source_settings = {
        source.source_id: deepcopy(project.source_settings.get(source.source_id, {})),
    }
    return Project(
        project_id=_derived_project_id(project, request),
        source=source_copy,
        duration_seconds=timeline.timeline_duration_seconds,
        playhead_seconds=0.0,
        schema_version=ONE_SOURCE_SCHEMA_VERSION,
        segment_timeline=timeline,
        sources=(source_copy,),
        source_settings=source_settings,
        output_settings=settings,
        composition_version=project.composition_version,
    )


def plan_source_output(
    project: Project,
    request: OutputRequest,
    *,
    ffprobe_path: str = "ffprobe",
    ffmpeg_path: str = "ffmpeg",
    frame_rate_policy: _FrameRatePolicyInput = None,
    upscale_policy: _UpscalePolicyInput = None,
    plan_project_export_fn: Callable[..., ExportPlan] = plan_project_export,
    cancel_event: threading.Event | None = None,
    runtime_cache: RuntimeValidationCache | None = None,
) -> SourceOutputPlan:
    """Create one source-output plan without rendering output media."""
    check_export_cancelled(cancel_event)
    if request.output_kind != "source":
        raise SourceOutputPlanningError("Standalone source rendering requires a source request")
    source = _source_for_request(project, request)
    selected_frame_rate = _source_frame_rate_policy(project, source, frame_rate_policy)
    selected_upscale = _source_upscale_policy(project, source, upscale_policy)
    selected_upscale = _fallback_unavailable_source_upscale(
        selected_upscale, source, runtime_cache=runtime_cache
    )
    protected = _protected_source_paths(project)
    _ensure_destination_not_protected(request.destination, protected)
    derived = derive_standalone_source_project(
        project,
        request,
        frame_rate_policy=selected_frame_rate,
        upscale_policy=selected_upscale,
    )
    planning_arguments: dict[str, object] = {
        "ffprobe_path": ffprobe_path,
        "ffmpeg_path": ffmpeg_path,
        "frame_rate_policy": selected_frame_rate,
        "upscale_policy": selected_upscale,
    }
    if cancel_event is not None:
        planning_arguments["cancel_event"] = cancel_event
    try:
        export_plan = plan_project_export_fn(
            derived,
            request.destination,
            **planning_arguments,
        )
        _ensure_destination_not_protected(request.destination, protected)
        _ensure_destination_not_protected(export_plan.destination, protected)
        _ensure_planned_destination_matches_request(export_plan, request)
    except (ExportPlanningError, ProjectValidationError, ValueError) as error:
        raise SourceOutputPlanningError(
            f"Could not plan source output {request.identity.track_id}/{request.identity.source_id}: "
            f"{error}",
        ) from error
    return SourceOutputPlan(
        request=request,
        derived_project=derived,
        export_plan=export_plan,
        frame_rate_policy=selected_frame_rate,
        upscale_policy=selected_upscale,
        protected_source_paths=protected,
    )


def plan_source_outputs(
    project: Project,
    requests: Sequence[OutputRequest],
    *,
    progress_callback: Callable[[ExportProgress], None] | None = None,
    **options: Unpack[_SourcePlanningOptions],
) -> tuple[SourceOutputPlan, ...]:
    """Plan all source outputs before any output is rendered."""
    started = time.monotonic()
    plans = []
    for index, request in enumerate(requests):
        check_export_cancelled(options.get("cancel_event"))
        report_preparation_progress(
            progress_callback, "Planning source outputs", index, len(requests), started
        )
        plans.append(plan_source_output(project, request, **options))
    return tuple(plans)


def render_source_output(
    plan: SourceOutputPlan,
    *,
    ffmpeg_path: str = "ffmpeg",
    ffprobe_path: str = "ffprobe",
    resume_mode: str = "fresh",
    progress_callback: Callable[[ExportProgress], None] | None = None,
    execute_export_fn: Callable[..., Path] = execute_export,
    probe_media_fn: Callable[..., MediaProbe] = probe_media,
    destination_override: Path | None = None,
    cancel_event: threading.Event | None = None,
    cancellation_lock: threading.Lock | None = None,
) -> SourceOutputRenderResult:
    """Execute and verify one source output through the existing delivery route."""
    _ensure_destination_not_protected(plan.request.destination, plan.protected_source_paths)
    _ensure_destination_not_protected(plan.export_plan.destination, plan.protected_source_paths)
    _ensure_planned_destination_matches_request(plan.export_plan, plan.request)
    publication_destination = (
        plan.request.destination
        if destination_override is None
        else Path(destination_override).expanduser()
    )
    _ensure_destination_not_protected(publication_destination, plan.protected_source_paths)
    stage_destination = _source_output_execution_destination(publication_destination)
    _ensure_destination_not_protected(stage_destination, plan.protected_source_paths)
    snapshots = _source_snapshots(plan.protected_source_paths)
    execution_plan = replace(plan.export_plan, destination=stage_destination)
    execute_kwargs: dict[str, Any] = {
        "ffmpeg_path": ffmpeg_path,
        "ffprobe_path": ffprobe_path,
        "progress_callback": progress_callback,
    }
    if cancel_event is not None:
        execute_kwargs["cancel_event"] = cancel_event
    if cancellation_lock is not None:
        execute_kwargs["cancellation_lock"] = cancellation_lock
    if resume_mode != "fresh":
        execute_kwargs["resume_mode"] = child_resume_mode(stage_destination, resume_mode)
    try:
        destination = execute_export_fn(execution_plan, **execute_kwargs)
        if not _same_path(destination, stage_destination):
            raise SourceOutputExecutionError(
                "Source output executor returned an unexpected destination",
            )
        _verify_source_snapshots(snapshots)
        output_media = probe_media_fn(stage_destination, ffprobe_path)
        stage_destination.replace(publication_destination)
    except (ExportExecutionError, SourceOutputExecutionError, MediaProbeError) as error:
        error_message = _source_output_error_message(error, stage_destination)
        return SourceOutputRenderResult(
            plan=plan,
            destination=publication_destination,
            verified=False,
            error=error_message,
            session_mode=resume_mode,
        )
    except OSError as error:
        error_message = _source_output_error_message(error, stage_destination)
        return SourceOutputRenderResult(
            plan=plan,
            destination=publication_destination,
            verified=False,
            error=error_message,
            session_mode=resume_mode,
        )
    return SourceOutputRenderResult(
        plan=plan,
        destination=publication_destination,
        verified=True,
        output_media=output_media,
        session_mode=resume_mode,
    )


def render_source_outputs(
    project: Project,
    requests: Sequence[OutputRequest],
    *,
    ffmpeg_path: str = "ffmpeg",
    ffprobe_path: str = "ffprobe",
    frame_rate_policy: (
        FrameRatePolicy | ResolvedFrameRatePolicy | Mapping[str, Any] | None
    ) = None,
    upscale_policy: UpscalePolicy | ResolvedUpscalePolicy | Mapping[str, Any] | None = None,
    resume_mode: str = "fresh",
    progress_callback: Callable[[ExportProgress], None] | None = None,
    plan_project_export_fn: Callable[..., ExportPlan] = plan_project_export,
    execute_export_fn: Callable[..., Path] = execute_export,
    probe_media_fn: Callable[..., MediaProbe] = probe_media,
) -> SourceOutputRenderSummary:
    """Plan a source batch, then execute each output independently."""
    plans = plan_source_outputs(
        project,
        requests,
        ffprobe_path=ffprobe_path,
        ffmpeg_path=ffmpeg_path,
        frame_rate_policy=frame_rate_policy,
        upscale_policy=upscale_policy,
        plan_project_export_fn=plan_project_export_fn,
    )
    results = tuple(
        render_source_output(
            plan,
            ffmpeg_path=ffmpeg_path,
            ffprobe_path=ffprobe_path,
            resume_mode=resume_mode,
            progress_callback=progress_callback,
            execute_export_fn=execute_export_fn,
            probe_media_fn=probe_media_fn,
        )
        for plan in plans
    )
    return SourceOutputRenderSummary(plans=plans, results=results)


def _source_for_request(project: Project, request: OutputRequest) -> SourceReference:
    source_id = request.source_id
    if source_id is None:
        raise SourceOutputPlanningError("Source request must identify a source")
    for source in project.sources or (project.source,):
        if source.source_id == source_id:
            if request.source_path is not None:
                requested_path = request.source_path.expanduser().resolve()
                if requested_path != Path(source.path).expanduser().resolve():
                    raise SourceOutputPlanningError(
                        f"Source request path does not match source {source_id}",
                    )
            return source
    raise SourceOutputPlanningError(f"Source request references unknown source {source_id}")


def _source_output_execution_destination(destination: Path) -> Path:
    """Return the isolated delivery path used before source verification."""
    suffix = destination.suffix
    stem = destination.name[: -len(suffix)] if suffix else destination.name
    return destination.with_name(f".{stem}.source-output-stage{suffix}")


def _protected_source_paths(project: Project) -> tuple[Path, ...]:
    return tuple(
        Path(item.path).expanduser().resolve() for item in (project.sources or (project.source,))
    )


def _same_path(left: Path, right: Path) -> bool:
    left_path = left.expanduser()
    right_path = right.expanduser()
    try:
        if left_path.samefile(right_path):
            return True
    except OSError:
        pass
    return left_path.resolve(strict=False) == right_path.resolve(strict=False)


def _ensure_destination_not_protected(
    destination: Path,
    protected_paths: Sequence[Path],
) -> None:
    if any(_same_path(destination, source_path) for source_path in protected_paths):
        raise SourceOutputPlanningError(
            f"Source output destination aliases protected source {destination.name}",
        )


def _ensure_planned_destination_matches_request(
    export_plan: ExportPlan,
    request: OutputRequest,
) -> None:
    if not _same_path(export_plan.destination, request.destination):
        raise SourceOutputPlanningError(
            "Source output planner changed the requested destination",
        )


def _source_duration(source: SourceReference) -> float:
    value = source.metadata.get("duration_seconds")
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise SourceOutputPlanningError(
            f"Source {source.source_id} has invalid duration metadata",
        )
    duration = float(value)
    if not math.isfinite(duration) or duration <= 0:
        raise SourceOutputPlanningError(
            f"Source {source.source_id} has invalid duration metadata",
        )
    return duration


def _standalone_segments(
    request: OutputRequest,
    source_duration: float,
) -> tuple[Segment, ...]:
    if not request.segments:
        raise SourceOutputPlanningError("Source request must contain at least one segment")
    active: list[Segment] = []
    cursor = 0.0
    intervals: list[tuple[float, float]] = []
    source_id = request.source_id
    if source_id is None:
        raise SourceOutputPlanningError("Source request must identify a source")
    for segment in request.segments:
        if segment.source_id not in {None, source_id}:
            raise SourceOutputPlanningError(
                f"Source request segment {segment.segment_id} references another source",
            )
        if segment.start_seconds < 0 or segment.end_seconds > source_duration:
            raise SourceOutputPlanningError(
                f"Source request segment {segment.segment_id} exceeds source duration",
            )
        duration = segment.duration_seconds
        timeline_end = cursor + duration
        active.append(
            replace(
                segment,
                deleted=False,
                source_id=source_id,
                timeline_start_seconds=cursor,
                timeline_end_seconds=timeline_end,
            ),
        )
        intervals.append((segment.start_seconds, segment.end_seconds))
        cursor = timeline_end
    gaps = _coverage_gaps(intervals, source_duration)
    for index, (start, end) in enumerate(gaps):
        gap_duration = end - start
        active.append(
            Segment.create(
                start,
                end,
                deleted=True,
                segment_id=f"source-output-gap-{index + 1}",
                block_id=f"source-output-gap-{index + 1}",
                source_id=source_id,
                timeline_start_seconds=cursor,
                timeline_end_seconds=cursor + gap_duration,
                state={"source_output_gap": True},
            ),
        )
        cursor += gap_duration
    return tuple(active)


def _coverage_gaps(
    intervals: Sequence[tuple[float, float]],
    source_duration: float,
) -> tuple[tuple[float, float], ...]:
    ordered = sorted(intervals)
    gaps: list[tuple[float, float]] = []
    covered_until = 0.0
    for start, end in ordered:
        if start > covered_until + _TIME_EPSILON:
            gaps.append((covered_until, start))
        covered_until = max(covered_until, end)
    if covered_until < source_duration - _TIME_EPSILON:
        gaps.append((covered_until, source_duration))
    return tuple(gaps)


def _derived_project_id(project: Project, request: OutputRequest) -> str:
    track_id = request.identity.track_id or "track"
    source_id = request.identity.source_id or "source"
    return f"{project.project_id}:standalone:{track_id}:{source_id}"


def _source_frame_rate_policy(
    project: Project,
    source: SourceReference,
    policy: FrameRatePolicy | ResolvedFrameRatePolicy | Mapping[str, Any] | None,
) -> FrameRatePolicy:
    try:
        selected = _coerce_frame_rate_policy(project, policy)
        metadata = policy_source_metadata((source,))
        try:
            resolved_from_policy(metadata, selected)
            return selected
        except FrameRatePolicyError:
            return FrameRatePolicy(
                choice="custom",
                target_rate=selected.target_rate,
                custom_rate=selected.target_rate,
                enhancement_enabled=selected.enhancement_enabled,
                enhancement_scope=selected.enhancement_scope,
                backend=selected.backend,
            )
    except (FrameRatePolicyError, ProjectValidationError, ValueError) as error:
        raise SourceOutputPlanningError(
            f"Could not resolve frame-rate policy for source {source.source_id}: {error}",
        ) from error


def _coerce_frame_rate_policy(
    project: Project,
    policy: FrameRatePolicy | ResolvedFrameRatePolicy | Mapping[str, Any] | None,
) -> FrameRatePolicy:
    if isinstance(policy, ResolvedFrameRatePolicy):
        return policy.policy
    if isinstance(policy, FrameRatePolicy):
        return policy
    if isinstance(policy, Mapping):
        return FrameRatePolicy.from_dict(policy)
    return project.get_frame_rate_policy()


def _source_upscale_policy(
    project: Project,
    source: SourceReference,
    policy: UpscalePolicy | ResolvedUpscalePolicy | Mapping[str, Any] | None,
) -> UpscalePolicy:
    try:
        if isinstance(policy, ResolvedUpscalePolicy):
            selected = policy.policy
        elif isinstance(policy, UpscalePolicy):
            selected = policy
        elif isinstance(policy, Mapping):
            selected = UpscalePolicy.from_dict(policy)
        else:
            selected = project.get_upscale_policy()
        resolve_upscale_policy(
            upscale_policy_source_metadata((source,)),
            policy=selected,
        )
        return selected
    except (UpscalePolicyError, ProjectValidationError, ValueError) as error:
        raise SourceOutputPlanningError(
            f"Could not resolve upscale policy for source {source.source_id}: {error}",
        ) from error


def _fallback_unavailable_source_upscale(
    policy: UpscalePolicy,
    source: SourceReference,
    *,
    runtime_cache: RuntimeValidationCache | None = None,
) -> UpscalePolicy:
    if not policy.enhancement_enabled or not policy.backend.casefold().startswith("rve"):
        return policy
    resolved = resolve_upscale_policy(
        upscale_policy_source_metadata((source,)),
        policy=policy,
    )
    decision = resolved.decisions[0]
    if (
        not decision.eligible
        or _source_upscale_runtime_reason(policy, decision, runtime_cache=runtime_cache) is None
    ):
        return policy
    return UpscalePolicy(
        enhancement_enabled=False,
        model=policy.model,
        backend=policy.backend,
        target_short_side=policy.target_short_side,
        landscape_max_short_side=policy.landscape_max_short_side,
        portrait_max_short_side=policy.portrait_max_short_side,
    )


def _source_upscale_runtime_reason(
    policy: UpscalePolicy,
    decision: UpscaleDecision,
    *,
    runtime_cache: RuntimeValidationCache | None = None,
) -> str | None:
    from .video_compositor import _upscale_runtime_status

    status, reason = _upscale_runtime_status(policy, decision, runtime_cache=runtime_cache)
    return None if status == "available" else reason


def _source_snapshots(paths: Sequence[Path]) -> tuple[tuple[Path, int, int], ...]:
    snapshots: list[tuple[Path, int, int]] = []
    for path in paths:
        try:
            stat = path.stat()
        except OSError as error:
            raise SourceOutputExecutionError(
                f"Could not protect source {path.name}: {error.strerror or type(error).__name__}",
            ) from error
        snapshots.append((path, stat.st_size, stat.st_mtime_ns))
    return tuple(snapshots)


def _verify_source_snapshots(snapshots: Sequence[tuple[Path, int, int]]) -> None:
    for path, size, modified_time_ns in snapshots:
        try:
            stat = path.stat()
        except OSError as error:
            raise SourceOutputExecutionError(
                f"Source {path.name} disappeared during export",
            ) from error
        if stat.st_size != size or stat.st_mtime_ns != modified_time_ns:
            raise SourceOutputExecutionError(
                f"Source {path.name} changed during export; output was not published",
            )


def _source_output_error_message(error: BaseException, stage_destination: Path) -> str:
    message = str(error)
    cleanup_error = _remove_unverified_destination(stage_destination)
    if cleanup_error is not None:
        message += f"; could not remove unverified output: {cleanup_error}"
    return message


def _remove_unverified_destination(path: Path) -> OSError | None:
    try:
        path.unlink(missing_ok=True)
    except OSError as error:
        return error
    return None


__all__ = [
    "SourceOutputExecutionError",
    "SourceOutputPlan",
    "SourceOutputPlanningError",
    "SourceOutputRenderResult",
    "SourceOutputRenderSummary",
    "derive_standalone_source_project",
    "plan_source_output",
    "plan_source_outputs",
    "render_source_output",
    "render_source_outputs",
]
