from __future__ import annotations

import json
import signal
import sys
import threading
from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager, redirect_stdout
from dataclasses import asdict, replace
from pathlib import Path
from typing import Any, TextIO

from .av_compositor import (
    AVCompositorExecutionError,
    AVCompositorPlanningError,
    AVRenderPlan,
    plan_project_av,
    render_project_av,
)
from .cli_payload import display_path, project_payload
from .cli_types import (
    CLI_CONTRACT_VERSION,
    CLI_EXIT_DEPENDENCY,
    CLI_EXIT_INVALID,
    CLI_EXIT_OPERATION,
    CliError,
    success_payload,
)
from .export import (
    ExportExecutionError,
    ExportPlan,
    ExportPlanningError,
    ExportProgress,
)
from .export_console import ConsoleProgressReporter
from .export_coordinator import (
    ExportCancelled,
    ExportCoordinator,
    ExportOutputResult,
    build_output_fingerprint,
    build_output_request_maps,
    build_project_output_fingerprint_payload,
    build_tool_identities,
    child_resume_mode,
    discard_batch_receipt,
    output_identity_key,
    protected_receipt_paths,
    protected_source_paths,
    resolve_output_plan,
    verify_planned_output,
)
from .export_estimates import calibration_for_policy, estimate_project_export
from .export_session import (
    ExportSessionError,
    ExportSessionInfo,
    discard_export_session,
    discover_export_session,
    session_root,
)
from .fps_policy import FrameRatePolicy, ResolvedFrameRatePolicy
from .interpolation import RuntimeValidationCache
from .media import MediaProbe, MediaProbeError
from .model import Project
from .model_timeline import ABSOLUTE_TIMING_MODE
from .operations import ensure_project_audio_analysis, export_destination_conflicts_with_project
from .output_plan import (
    OutputPlan,
    OutputRequest,
    plan_project_outputs,
)
from .render_preparations import RenderPreparations
from .source_outputs import (
    SourceOutputPlan,
    SourceOutputRenderResult,
    SourceOutputRenderSummary,
    _source_output_execution_destination,
    plan_source_outputs,
    render_source_output,
)
from .upscale_policy import ResolvedUpscalePolicy, UpscalePolicy
from .video_compositor import SourceHashCache


def progress_payload(progress: ExportProgress) -> dict[str, Any]:
    return {
        "contract_version": CLI_CONTRACT_VERSION,
        "command": "export.progress",
        "event": "progress",
        "progress": asdict(progress),
    }


def _plan_payload(plan: ExportPlan, *, include_paths: bool) -> dict[str, Any]:
    payload = plan.to_dict()
    payload["source"] = display_path(plan.source, include_paths)
    payload["destination"] = display_path(plan.destination, include_paths)
    payload["source_paths"] = [display_path(path, include_paths) for path in plan.source_paths]
    return payload


def _output_request_payload(
    request: OutputRequest,
    *,
    include_paths: bool,
    source_output_root: Path | None,
) -> dict[str, Any]:
    payload = request.to_dict()
    if include_paths:
        payload["destination"] = display_path(request.destination, True)
    elif source_output_root is not None:
        try:
            payload["destination"] = str(
                request.destination.resolve().relative_to(source_output_root.resolve()),
            )
        except ValueError:
            payload["destination"] = request.destination.name
    else:
        payload["destination"] = request.destination.name
    payload["source_paths"] = [display_path(path, include_paths) for path in request.source_paths]
    return payload


def _output_plan_payload(plan: OutputPlan, *, include_paths: bool) -> dict[str, Any]:
    source_root = plan.source_output_root
    return {
        "mode": plan.mode,
        "selection": plan.selection.to_dict(),
        "final": (
            None
            if plan.final_request is None
            else _output_request_payload(
                plan.final_request,
                include_paths=include_paths,
                source_output_root=source_root,
            )
        ),
        "source_outputs": [
            _output_request_payload(
                request,
                include_paths=include_paths,
                source_output_root=source_root,
            )
            for request in plan.source_outputs
        ],
        "source_output_root": (
            None if source_root is None else display_path(source_root, include_paths)
        ),
    }


def _source_output_plan_payload(
    plan: SourceOutputPlan,
    *,
    include_paths: bool,
    source_output_root: Path | None,
) -> dict[str, Any]:
    return {
        "identity": plan.identity.to_dict(),
        "request": _output_request_payload(
            plan.request,
            include_paths=include_paths,
            source_output_root=source_output_root,
        ),
        "plan": _plan_payload(plan.export_plan, include_paths=include_paths),
        "frame_rate_policy": plan.frame_rate_policy.to_dict(),
        "upscale_policy": plan.upscale_policy.to_dict(),
    }


def _source_output_result_payload(
    result: SourceOutputRenderResult,
    *,
    include_paths: bool,
    source_output_root: Path | None,
) -> dict[str, Any]:
    payload = result.to_dict()
    payload["request"] = _output_request_payload(
        result.request,
        include_paths=include_paths,
        source_output_root=source_output_root,
    )
    payload["destination"] = payload["request"]["destination"]
    payload["plan"] = _plan_payload(result.plan.export_plan, include_paths=include_paths)
    payload["frame_rate_policy"] = result.plan.frame_rate_policy.to_dict()
    payload["upscale_policy"] = result.plan.upscale_policy.to_dict()
    return payload


def _combined_final_supported(project: Project) -> bool:
    timeline = project.timeline
    if timeline.tracks is None:
        return True
    return len(timeline.tracks) == 1 and timeline.timing_mode == "legacy-ripple"


def _independent_session_event(
    output: TextIO,
    *,
    identity: dict[str, Any],
    destination: Path,
    mode: str,
) -> None:
    if mode == "fresh":
        return
    session_info = discover_export_session(_source_output_execution_destination(destination))
    _write_json(
        output,
        {
            "contract_version": CLI_CONTRACT_VERSION,
            "command": "export.session",
            "event": "session",
            "identity": identity,
            "session": {
                "mode": mode,
                "status": session_info.to_dict(),
            },
        },
    )


def _discard_independent_sessions(
    *,
    args: Any,
    project: Project,
    output_plan: OutputPlan,
) -> dict[str, Any]:
    statuses: list[dict[str, Any]] = []
    requests: list[OutputRequest] = list(output_plan.output_requests)
    for request in requests:
        session_destination = (
            _source_output_execution_destination(request.destination)
            if request.output_kind == "source"
            else request.destination
        )
        try:
            discarded = discard_export_session(session_destination)
        except ExportSessionError as error:
            raise CliError(
                "export_session",
                str(error),
                exit_code=CLI_EXIT_OPERATION,
            ) from error
        statuses.append(
            {
                "identity": request.identity.to_dict(),
                "destination": _output_request_payload(
                    request,
                    include_paths=args.full_paths,
                    source_output_root=output_plan.source_output_root,
                )["destination"],
                "discarded": not discarded.exists,
                "status": discarded.to_dict(),
            },
        )
    return success_payload(
        "export",
        {
            "project": project_payload(
                project,
                args.project,
                include_paths=args.full_paths,
            ),
            "export": {
                "planned": True,
                "verified": False,
                "partial_success": False,
                "output_plan": _output_plan_payload(
                    output_plan,
                    include_paths=args.full_paths,
                ),
                "session": {
                    "mode": "discard",
                    "outputs": statuses,
                },
            },
        },
    )


def _source_render_payload(
    *,
    args: Any,
    project: Project,
    output_plan: OutputPlan,
    source_plans: tuple[SourceOutputPlan, ...],
    source_summary: SourceOutputRenderSummary,
    final_result: dict[str, Any] | None,
) -> dict[str, Any]:
    source_root = output_plan.source_output_root
    source_results = [
        _source_output_result_payload(
            result,
            include_paths=args.full_paths,
            source_output_root=source_root,
        )
        for result in source_summary.results
    ]
    final_verified = None if final_result is None else bool(final_result.get("verified", False))
    output_verified = [result.verified for result in source_summary.results]
    if final_verified is not None:
        output_verified.append(final_verified)
    verified_count = sum(output_verified)
    requested_count = len(output_verified)
    payload: dict[str, Any] = {
        "planned": True,
        "verified": requested_count > 0 and verified_count == requested_count,
        "partial_success": 0 < verified_count < requested_count,
        "output_plan": _output_plan_payload(
            output_plan,
            include_paths=args.full_paths,
        ),
        "source_plans": [
            _source_output_plan_payload(
                plan,
                include_paths=args.full_paths,
                source_output_root=source_root,
            )
            for plan in source_plans
        ],
        "source_outputs": source_results,
    }
    if final_result is not None:
        payload["final"] = final_result
    return {
        "project": project_payload(
            project,
            args.project,
            include_paths=args.full_paths,
        ),
        "export": payload,
    }


def _resolved_frame_rate_policy(
    plan: ExportPlan,
    project: Project,
) -> FrameRatePolicy | ResolvedFrameRatePolicy:
    if isinstance(plan.frame_rate_policy, ResolvedFrameRatePolicy):
        return plan.frame_rate_policy
    if isinstance(plan.frame_rate_policy, FrameRatePolicy):
        return plan.frame_rate_policy
    if isinstance(plan.frame_rate_policy, dict):
        return FrameRatePolicy.from_dict(plan.frame_rate_policy)
    return project.get_frame_rate_policy()


def _plan_arguments(args: Any) -> dict[str, Any]:
    arguments: dict[str, Any] = {
        "ffprobe_path": getattr(args, "ffprobe", "ffprobe"),
        "ffmpeg_path": getattr(args, "ffmpeg", "ffmpeg"),
    }
    if getattr(args, "frame_rate_policy", None) is not None:
        arguments["frame_rate_policy"] = args.frame_rate_policy
    if getattr(args, "upscale_policy", None) is not None:
        arguments["upscale_policy"] = args.upscale_policy
    return arguments


def _build_output_plans(
    args: Any,
    project: Project,
    output_plan: OutputPlan,
    plan_project_export_fn: Callable[..., ExportPlan],
    *,
    cancel_event: threading.Event | None = None,
    progress_callback: Callable[[ExportProgress], None] | None = None,
    source_hash_cache: SourceHashCache | None = None,
) -> tuple[
    dict[str, Any],
    ExportPlan | AVRenderPlan | None,
    tuple[SourceOutputPlan, ...],
]:
    plan_arguments = _plan_arguments(args)
    runtime_cache: RuntimeValidationCache = {}
    ensure_project_audio_analysis(
        project,
        ffmpeg_path=plan_arguments["ffmpeg_path"],
        cancel_event=cancel_event,
        source_ids={
            source_id for request in output_plan.output_requests for source_id in request.source_ids
        },
        progress_callback=progress_callback,
    )
    final_plan: ExportPlan | AVRenderPlan | None = None
    if output_plan.final_request is not None:
        if _needs_synchronized_final(project):
            final_plan = plan_project_av(
                project,
                output_plan.final_request.destination,
                frame_rate_policy=plan_arguments.get("frame_rate_policy"),
                upscale_policy=plan_arguments.get("upscale_policy"),
                ffprobe_path=plan_arguments["ffprobe_path"],
                cancel_event=cancel_event,
                progress_callback=progress_callback,
                source_hash_cache=source_hash_cache,
                runtime_cache=runtime_cache,
            )
        else:
            final_plan = plan_project_export_fn(
                project,
                output_plan.final_request.destination,
                cancel_event=cancel_event,
                **plan_arguments,
            )
    source_plans = tuple(
        plan_source_outputs(
            project,
            output_plan.source_outputs,
            **plan_arguments,
            plan_project_export_fn=plan_project_export_fn,
            cancel_event=cancel_event,
            progress_callback=progress_callback,
            runtime_cache=runtime_cache,
        )
    )
    return plan_arguments, final_plan, source_plans


def _child_completed_stage_count(destination: Path, parent: ExportSessionInfo) -> int:
    count = parent.completed_stage_count
    candidates_root = parent.root / "candidates"
    try:
        children = tuple(candidates_root.iterdir())
    except OSError:
        return count
    suffix = ".framestudio-session"
    for child in children:
        if not child.is_dir() or not child.name.endswith(suffix):
            continue
        candidate_name = child.name[1 : -len(suffix)] if child.name.startswith(".") else ""
        if not candidate_name:
            continue
        child_info = discover_export_session(candidates_root / candidate_name)
        count += child_info.completed_stage_count
    return count


def _media_payload(output_media: MediaProbe) -> dict[str, Any]:
    return {
        "duration_seconds": output_media.duration_seconds,
        "width": output_media.width,
        "height": output_media.height,
        "frame_rate": output_media.frame_rate,
        "video_codec": output_media.video_codec,
        "audio_codec": output_media.audio_codec,
        "format_name": output_media.format_name,
        "audio_stream_present": output_media.has_audio_stream,
    }


def _plan_only_response(
    args: Any,
    project: Project,
    export_payload: dict[str, Any],
) -> dict[str, Any]:
    return success_payload(
        "export-plan" if args.command == "export-plan" else "export",
        {
            "project": project_payload(
                project,
                args.project,
                include_paths=args.full_paths,
            ),
            "export": export_payload,
        },
    )


def _progress_callback(
    *,
    args: Any,
    output: TextIO,
    progress_output: TextIO | None,
) -> Callable[[ExportProgress], None]:
    console_progress = ConsoleProgressReporter(
        stream=sys.stderr if progress_output is None else progress_output,
        force=bool(getattr(args, "human_progress", False)),
    )

    def report_progress(progress: ExportProgress) -> None:
        console_progress(progress)
        _write_json(output, progress_payload(progress))

    return report_progress


def _final_result_payload(
    *,
    args: Any,
    plan: ExportPlan,
    project: Project,
    session_mode: str,
    session_info: ExportSessionInfo,
    destination: Path | None,
    output_media: MediaProbe | None,
    error: str | None,
) -> dict[str, Any]:
    resolved_policy = _resolved_frame_rate_policy(plan, project)
    payload: dict[str, Any] = {
        "identity": {
            "mode": "combined",
            "output_kind": "final",
            "track_id": None,
            "source_id": None,
            "framing": "final-composition",
            "audio_intent": "mixed-layout-pan",
            "render_profile": "final-composition",
        },
        "verified": error is None and output_media is not None,
        "route": plan.route,
        "reason": plan.reason,
        "plan": _plan_payload(plan, include_paths=args.full_paths),
        "frame_rate_policy": resolved_policy.to_dict(),
        "upscale_policy": _upscale_policy_payload(plan, project),
        "session": {
            "mode": session_mode,
            "resumed": session_mode == "resume",
            "previous_completed_stage_count": session_info.completed_stage_count,
        },
    }
    if destination is not None:
        payload["destination"] = display_path(destination, args.full_paths)
    if error is not None:
        payload["error"] = error
    if output_media is not None:
        payload["output"] = _media_payload(output_media)
    return payload


def _needs_synchronized_final(project: Project) -> bool:
    timeline = project.timeline
    return (
        timeline.timing_mode == ABSOLUTE_TIMING_MODE
        or timeline.tracks is not None
        and len(timeline.tracks) > 1
    )


def _coordinated_result_payload(
    *,
    args: Any,
    project: Project,
    request: OutputRequest,
    result: ExportOutputResult,
    output_plan: OutputPlan,
    final_plan: ExportPlan | AVRenderPlan | None,
    source_plan: SourceOutputPlan | None,
) -> dict[str, Any]:
    payload = result.to_dict()
    payload["request"] = _output_request_payload(
        request,
        include_paths=args.full_paths,
        source_output_root=output_plan.source_output_root,
    )
    payload["destination"] = payload["request"]["destination"]
    if final_plan is not None:
        if isinstance(final_plan, AVRenderPlan):
            payload["route"] = "synchronized-av"
            payload["reason"] = "shared synchronized audio/video compositor"
            payload["plan"] = {
                "route": payload["route"],
                "reason": payload["reason"],
                "destination": display_path(final_plan.destination, args.full_paths),
            }
        else:
            payload["route"] = final_plan.route
            payload["reason"] = final_plan.reason
            payload["plan"] = _plan_payload(final_plan, include_paths=args.full_paths)
            payload["frame_rate_policy"] = _resolved_frame_rate_policy(
                final_plan,
                project,
            ).to_dict()
            payload["upscale_policy"] = _upscale_policy_payload(
                final_plan,
                project,
            )
        verification = payload.get("verification")
        if isinstance(verification, dict) and isinstance(verification.get("media"), dict):
            payload["output"] = verification["media"]
    if source_plan is not None:
        payload["plan"] = _plan_payload(source_plan.export_plan, include_paths=args.full_paths)
        payload["frame_rate_policy"] = source_plan.frame_rate_policy.to_dict()
        payload["upscale_policy"] = source_plan.upscale_policy.to_dict()
    return payload


def _handle_coordinated_output_plan(
    args: Any,
    project: Project,
    *,
    output: TextIO,
    output_plan: OutputPlan,
    plan_project_export_fn: Callable[..., ExportPlan],
    execute_export_fn: Callable[..., Path],
    probe_media_fn: Callable[..., MediaProbe],
    progress_output: TextIO | None,
    cancel_event: threading.Event,
) -> dict[str, Any]:
    resume_mode = getattr(args, "resume_mode", "fresh")
    session_info = discover_export_session(args.output)
    previous_completed_stage_count = _child_completed_stage_count(
        args.output,
        session_info,
    )
    if resume_mode == "discard":
        try:
            discard_batch_receipt(
                args.output,
                protected_source_paths=protected_receipt_paths(
                    project,
                    project_path=args.project,
                    planned_outputs=tuple(
                        request.destination for request in output_plan.output_requests
                    ),
                ),
            )
            discarded = discard_export_session(args.output)
        except ExportSessionError as error:
            raise CliError(
                "export_session",
                str(error),
                exit_code=CLI_EXIT_OPERATION,
            ) from error
        return success_payload(
            "export",
            {
                "project": project_payload(
                    project,
                    args.project,
                    include_paths=args.full_paths,
                ),
                "export": {
                    "planned": True,
                    "verified": False,
                    "complete": False,
                    "partial_success": False,
                    "output_plan": _output_plan_payload(
                        output_plan,
                        include_paths=args.full_paths,
                    ),
                    "results": [],
                    "session": {
                        "mode": "discard",
                        "discarded": not discarded.exists,
                        "status": discarded.to_dict(),
                    },
                },
            },
        )
    if resume_mode != "fresh":
        _write_json(
            output,
            {
                "contract_version": CLI_CONTRACT_VERSION,
                "command": "export.session",
                "event": "session",
                "session": {
                    "mode": resume_mode,
                    "status": session_info.to_dict(),
                },
            },
        )

    report_preparation = ConsoleProgressReporter(
        stream=sys.stderr if progress_output is None else progress_output,
        force=bool(getattr(args, "human_progress", False)),
    )
    source_hash_cache: SourceHashCache = {}
    plan_arguments, final_plan, source_plans = _build_output_plans(
        args,
        project,
        output_plan,
        plan_project_export_fn,
        cancel_event=cancel_event,
        progress_callback=report_preparation,
        source_hash_cache=source_hash_cache,
    )
    tool_identities = build_tool_identities(
        ffmpeg_path=plan_arguments["ffmpeg_path"],
        ffprobe_path=plan_arguments["ffprobe_path"],
    )
    source_by_key = {output_identity_key(plan.request.identity): plan for plan in source_plans}
    final_by_key: dict[str, ExportPlan | AVRenderPlan]
    request_by_key: dict[str, OutputRequest]
    final_by_key, request_by_key = build_output_request_maps(
        output_plan,
        final_plan,
    )
    fingerprints = {
        key: build_output_fingerprint(
            build_project_output_fingerprint_payload(
                project,
                request_by_key[key],
                frame_rate_policy=getattr(args, "frame_rate_policy", None),
                upscale_policy=getattr(args, "upscale_policy", None),
                ffmpeg_path=plan_arguments["ffmpeg_path"],
                ffprobe_path=plan_arguments["ffprobe_path"],
                tool_identities=tool_identities,
                source_hash_cache=source_hash_cache,
                cancel_event=cancel_event,
                progress_callback=report_preparation,
            )
        )
        for key in request_by_key
    }
    report_progress = _progress_callback(
        args=args,
        output=output,
        progress_output=progress_output,
    )
    publication_lock = threading.Lock()

    def render_output(request: OutputRequest, candidate: Path, event: threading.Event) -> Path:
        key = output_identity_key(request.identity)
        with redirect_stdout(sys.stderr if progress_output is None else progress_output):
            if request.output_kind == "source":
                source_plan = source_by_key[key]
                rendered = render_source_output(
                    source_plan,
                    ffmpeg_path=plan_arguments["ffmpeg_path"],
                    ffprobe_path=plan_arguments["ffprobe_path"],
                    resume_mode=resume_mode,
                    progress_callback=report_progress,
                    execute_export_fn=execute_export_fn,
                    probe_media_fn=probe_media_fn,
                    destination_override=candidate,
                    cancel_event=event,
                    cancellation_lock=publication_lock,
                )
                if not rendered.verified:
                    if event.is_set():
                        raise ExportCancelled(rendered.error or "Export cancelled")
                    raise RuntimeError(rendered.error or "Source output failed verification")
                return candidate
            planned = final_by_key[key]
            if isinstance(planned, AVRenderPlan):
                av_plan = replace(planned, destination=candidate)
                render_project_av(
                    av_plan,
                    ffmpeg_path=plan_arguments["ffmpeg_path"],
                    ffprobe_path=plan_arguments["ffprobe_path"],
                    cancel_event=event,
                    cancellation_lock=publication_lock,
                    progress_callback=report_progress,
                    preparations=RenderPreparations(
                        session_root(args.output) / "render-preparations",
                        cancel_event=event,
                        progress_callback=report_progress,
                    ),
                )
                return candidate
            execution_plan = replace(planned, destination=candidate)
            execute_kwargs: dict[str, Any] = {
                "ffmpeg_path": plan_arguments["ffmpeg_path"],
                "ffprobe_path": plan_arguments["ffprobe_path"],
                "progress_callback": report_progress,
                "cancel_event": event,
                "cancellation_lock": publication_lock,
                "resume_mode": child_resume_mode(candidate, resume_mode),
            }
            rendered_path = execute_export_fn(execution_plan, **execute_kwargs)
            if rendered_path.expanduser().resolve() != candidate.expanduser().resolve():
                raise RuntimeError("Final renderer returned an unexpected candidate path")
            return candidate

    def verify_output(
        request: OutputRequest,
        candidate: Path,
        event: threading.Event,
    ) -> Mapping[str, Any]:
        key = output_identity_key(request.identity)
        planned = resolve_output_plan(key, source_by_key, final_by_key)
        if planned is None:
            raise ExportExecutionError("No concrete output plan is available for verification")
        return verify_planned_output(
            planned,
            candidate,
            ffmpeg_path=plan_arguments["ffmpeg_path"],
            ffprobe_path=plan_arguments["ffprobe_path"],
            cancel_event=event,
        )

    try:
        coordinator = ExportCoordinator(
            output_requests=output_plan.output_requests,
            session_destination=args.output,
            output_fingerprints=fingerprints,
            render_output=render_output,
            verify_output=verify_output,
            publication_lock=publication_lock,
            tool_versions=tool_identities,
            protected_source_paths=protected_source_paths(project),
            protected_receipt_paths=protected_receipt_paths(
                project,
                project_path=args.project,
                planned_outputs=tuple(
                    request.destination for request in output_plan.output_requests
                ),
            ),
        )
    except ExportSessionError as error:
        raise CliError(
            "export_session",
            str(error),
            exit_code=CLI_EXIT_OPERATION,
        ) from error
    result = coordinator.run(mode=resume_mode, cancel_event=cancel_event)
    result_payloads = [
        _coordinated_result_payload(
            args=args,
            project=project,
            request=request,
            result=item,
            output_plan=output_plan,
            final_plan=final_by_key.get(output_identity_key(request.identity)),
            source_plan=source_by_key.get(output_identity_key(request.identity)),
        )
        for request, item in zip(output_plan.output_requests, result.results, strict=True)
    ]
    final_payload = None
    source_payloads: list[dict[str, Any]] = []
    for item in result_payloads:
        if item["identity"]["output_kind"] == "final":
            final_payload = item
        else:
            source_payloads.append(item)
    export_payload: dict[str, Any] = {
        "planned": True,
        "verified": result.complete,
        "complete": result.complete,
        "partial_success": result.partial_success,
        "output_plan": _output_plan_payload(output_plan, include_paths=args.full_paths),
        "source_plans": [
            _source_output_plan_payload(
                plan,
                include_paths=args.full_paths,
                source_output_root=output_plan.source_output_root,
            )
            for plan in source_plans
        ],
        "results": result_payloads,
        "source_outputs": source_payloads,
        "session": {
            "mode": resume_mode,
            "resumed": resume_mode == "resume",
            "previous_completed_stage_count": previous_completed_stage_count,
            "receipt": None
            if result.receipt is None
            else display_path(
                result.receipt,
                args.full_paths,
            ),
        },
    }
    if final_payload is not None:
        export_payload["final"] = final_payload
        if output_plan.mode == "final-only":
            for field in (
                "route",
                "reason",
                "plan",
                "frame_rate_policy",
                "upscale_policy",
                "session",
                "destination",
                "output",
            ):
                if field in final_payload:
                    export_payload[field] = final_payload[field]
    response = {
        "project": project_payload(
            project,
            args.project,
            include_paths=args.full_paths,
        ),
        "export": export_payload,
    }
    if not result.complete:
        message = (
            result.error.get("message", "Export did not complete")
            if result.error is not None
            else next(
                (item.error["message"] for item in result.results if item.error is not None),
                "One or more export outputs failed",
            )
        )
        raise CliError(
            "export_cancelled"
            if any(item["state"] == "cancelled" for item in result_payloads)
            else "export_failed",
            message,
            exit_code=CLI_EXIT_OPERATION,
            details=export_payload,
        )
    return success_payload("export", response)


def _render_combined_final(
    *,
    args: Any,
    output: TextIO,
    project: Project,
    plan: ExportPlan,
    execute_export_fn: Callable[..., Path],
    probe_media_fn: Callable[..., MediaProbe],
    progress_callback: Callable[[ExportProgress], None],
    diagnostic_output: TextIO,
) -> dict[str, Any]:
    session_mode, session_info, discard_response = _prepare_export_session(
        args,
        output,
        project,
        plan,
    )
    if discard_response is not None:
        return _final_result_payload(
            args=args,
            plan=plan,
            project=project,
            session_mode=session_mode,
            session_info=session_info,
            destination=None,
            output_media=None,
            error="Final output session was discarded",
        )
    try:
        with redirect_stdout(diagnostic_output):
            execute_kwargs: dict[str, Any] = {
                "ffmpeg_path": args.ffmpeg,
                "ffprobe_path": args.ffprobe,
                "progress_callback": progress_callback,
            }
            if session_mode != "fresh":
                execute_kwargs["resume_mode"] = session_mode
            destination = execute_export_fn(plan, **execute_kwargs)
        output_media = probe_media_fn(destination, args.ffprobe)
    except (ExportExecutionError, MediaProbeError) as error:
        return _final_result_payload(
            args=args,
            plan=plan,
            project=project,
            session_mode=session_mode,
            session_info=session_info,
            destination=plan.destination,
            output_media=None,
            error=str(error),
        )
    return _final_result_payload(
        args=args,
        plan=plan,
        project=project,
        session_mode=session_mode,
        session_info=session_info,
        destination=destination,
        output_media=output_media,
        error=None,
    )


def _plan_output_only(
    args: Any,
    project: Project,
    output_plan: OutputPlan,
    *,
    plan_project_export_fn: Callable[..., ExportPlan],
    cancel_event: threading.Event,
) -> dict[str, Any]:
    _, final_plan, source_plans = _build_output_plans(
        args,
        project,
        output_plan,
        plan_project_export_fn=plan_project_export_fn,
        cancel_event=cancel_event,
    )
    export_payload: dict[str, Any] = {
        "planned": True,
        "verified": False,
        "output_plan": _output_plan_payload(output_plan, include_paths=args.full_paths),
        "source_plans": [
            _source_output_plan_payload(
                plan,
                include_paths=args.full_paths,
                source_output_root=output_plan.source_output_root,
            )
            for plan in source_plans
        ],
    }
    if isinstance(final_plan, AVRenderPlan):
        export_payload["plan"] = {
            "route": "synchronized-av",
            "reason": "shared synchronized audio/video compositor",
            "destination": display_path(final_plan.destination, args.full_paths),
        }
    elif isinstance(final_plan, ExportPlan):
        resolved_policy = _resolved_frame_rate_policy(final_plan, project)
        export_payload.update(
            {
                "plan": _plan_payload(final_plan, include_paths=args.full_paths),
                "frame_rate_policy": resolved_policy.to_dict(),
                "upscale_policy": _upscale_policy_payload(final_plan, project),
                "estimate": estimate_project_export(
                    project,
                    resolved_policy,
                    calibration=calibration_for_policy(resolved_policy),
                ).to_dict(),
            }
        )
    return _plan_only_response(
        args,
        project,
        export_payload,
    )


def _handle_independent_output_plan(
    args: Any,
    project: Project,
    *,
    output: TextIO,
    plan_project_export_fn: Callable[..., ExportPlan],
    execute_export_fn: Callable[..., Path],
    probe_media_fn: Callable[..., MediaProbe],
    progress_output: TextIO | None,
    cancel_event: threading.Event,
) -> dict[str, Any]:
    output_mode = getattr(args, "output_mode", None)
    output_plan = plan_project_outputs(project, args.output, mode=output_mode)
    if getattr(args, "plan_only", False):
        return _plan_output_only(
            args,
            project,
            output_plan,
            plan_project_export_fn=plan_project_export_fn,
            cancel_event=cancel_event,
        )
    return _handle_coordinated_output_plan(
        args,
        project,
        output=output,
        output_plan=output_plan,
        plan_project_export_fn=plan_project_export_fn,
        execute_export_fn=execute_export_fn,
        probe_media_fn=probe_media_fn,
        progress_output=progress_output,
        cancel_event=cancel_event,
    )


def _prepare_export_session(
    args: Any,
    output: TextIO,
    project: Project,
    plan: ExportPlan,
) -> tuple[str, Any, dict[str, Any] | None]:
    session_mode = getattr(args, "resume_mode", "fresh")
    session_info = discover_export_session(plan.destination)
    if session_mode == "resume" and not session_info.resumable:
        reason = session_info.reason or "No compatible resumable export session exists"
        raise CliError(
            "export_session",
            reason,
            exit_code=CLI_EXIT_OPERATION,
        )
    if session_mode == "discard":
        try:
            discarded = discard_export_session(plan.destination)
        except ExportSessionError as error:
            raise CliError(
                "export_session",
                str(error),
                exit_code=CLI_EXIT_OPERATION,
            ) from error
        return (
            session_mode,
            session_info,
            success_payload(
                "export",
                {
                    "project": project_payload(
                        project,
                        args.project,
                        include_paths=args.full_paths,
                    ),
                    "export": {
                        "planned": True,
                        "verified": False,
                        "session": {
                            "mode": "discard",
                            "discarded": not discarded.exists,
                            "status": discarded.to_dict(),
                        },
                    },
                },
            ),
        )
    if session_mode != "fresh":
        _write_json(
            output,
            {
                "contract_version": CLI_CONTRACT_VERSION,
                "command": "export.session",
                "event": "session",
                "session": {
                    "mode": session_mode,
                    "status": session_info.to_dict(),
                },
            },
        )
    return session_mode, session_info, None


def _upscale_policy_payload(plan: ExportPlan, project: Project) -> dict[str, Any]:
    value = plan.upscale_policy
    if isinstance(value, ResolvedUpscalePolicy):
        payload = value.to_dict()
        decisions = value.decisions
    elif isinstance(value, UpscalePolicy):
        payload = value.to_dict()
        decisions = plan.upscale_decisions
    elif isinstance(value, dict):
        payload = UpscalePolicy.from_dict(value).to_dict()
        decisions = plan.upscale_decisions or tuple(value.get("decisions", ()))
    else:
        resolved = project.resolve_upscale_policy()
        payload = resolved.policy.to_dict()
        decisions = resolved.decisions
    payload["decisions"] = [
        decision.to_dict() if hasattr(decision, "to_dict") else dict(decision)
        for decision in decisions
    ]
    return payload


@contextmanager
def _export_cancellation() -> Iterator[threading.Event]:
    cancel_event = threading.Event()
    on_main_thread = threading.current_thread() is threading.main_thread()
    previous_sigint = signal.getsignal(signal.SIGINT)
    if on_main_thread:
        signal.signal(signal.SIGINT, lambda _signum, _frame: cancel_event.set())
    try:
        yield cancel_event
    except ExportPlanningError as error:
        if cancel_event.is_set():
            raise CliError(
                "export_cancelled",
                str(error),
                exit_code=CLI_EXIT_OPERATION,
            ) from error
        raise
    finally:
        if on_main_thread:
            signal.signal(signal.SIGINT, previous_sigint)


def handle_export(
    args: Any,
    output: TextIO,
    *,
    progress_output: TextIO | None = None,
    load_project_fn: Callable[..., Project],
    probe_media_fn: Callable[..., MediaProbe],
    plan_project_export_fn: Callable[..., ExportPlan],
    execute_export_fn: Callable[..., Path],
) -> dict[str, Any]:
    project = load_project_fn(args.project)
    if project.segment_timeline is None:
        raise CliError(
            "invalid_project",
            "Project segment timeline is required",
            exit_code=CLI_EXIT_INVALID,
        )
    if export_destination_conflicts_with_project(
        args.project,
        args.output,
    ):
        raise CliError(
            "invalid_arguments",
            "Export destination must differ from the project file",
            exit_code=CLI_EXIT_INVALID,
        )
    try:
        with _export_cancellation() as cancel_event:
            return _handle_independent_output_plan(
                args,
                project,
                output=output,
                plan_project_export_fn=plan_project_export_fn,
                execute_export_fn=execute_export_fn,
                probe_media_fn=probe_media_fn,
                progress_output=progress_output,
                cancel_event=cancel_event,
            )
    except AVCompositorPlanningError as error:
        raise CliError(
            "export_planning",
            str(error),
            exit_code=CLI_EXIT_INVALID,
        ) from error
    except AVCompositorExecutionError as error:
        raise CliError(
            "export_failed",
            str(error),
            exit_code=CLI_EXIT_OPERATION,
        ) from error
    except MediaProbeError as error:
        raise CliError(
            "media_probe",
            str(error),
            exit_code=(
                CLI_EXIT_DEPENDENCY if "not installed" in str(error).lower() else CLI_EXIT_INVALID
            ),
        ) from error
    except ExportPlanningError as error:
        raise CliError(
            "export_planning",
            str(error),
            exit_code=CLI_EXIT_INVALID,
        ) from error
    except ExportExecutionError as error:
        raise CliError(
            "export_failed",
            str(error),
            exit_code=CLI_EXIT_OPERATION,
        ) from error


def _write_json(stream: TextIO, payload: dict[str, Any]) -> None:
    json.dump(payload, stream, ensure_ascii=True, sort_keys=True)
    stream.write("\n")
