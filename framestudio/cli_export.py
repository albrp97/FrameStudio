from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import asdict
from pathlib import Path
from typing import Any, TextIO

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
from .export_estimates import (
    calibration_for_policy,
    estimate_project_export,
)
from .fps_policy import FrameRatePolicy, ResolvedFrameRatePolicy
from .media import MediaProbe, MediaProbeError
from .model import Project
from .operations import export_destination_conflicts_with_project
from .upscale_policy import ResolvedUpscalePolicy, UpscalePolicy


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


def handle_export(
    args: Any,
    output: TextIO,
    *,
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
        plan_arguments: dict[str, Any] = {
            "ffprobe_path": args.ffprobe,
            "ffmpeg_path": args.ffmpeg,
        }
        frame_rate_policy = getattr(args, "frame_rate_policy", None)
        if frame_rate_policy is not None:
            plan_arguments["frame_rate_policy"] = frame_rate_policy
        upscale_policy = getattr(args, "upscale_policy", None)
        if upscale_policy is not None:
            plan_arguments["upscale_policy"] = upscale_policy
        plan = plan_project_export_fn(
            project,
            args.output,
            **plan_arguments,
        )
        resolved_policy = (
            plan.frame_rate_policy
            if isinstance(plan.frame_rate_policy, ResolvedFrameRatePolicy)
            else (
                plan.frame_rate_policy
                if isinstance(plan.frame_rate_policy, FrameRatePolicy)
                else (
                    FrameRatePolicy.from_dict(plan.frame_rate_policy)
                    if isinstance(plan.frame_rate_policy, dict)
                    else project.get_frame_rate_policy()
                )
            )
        )
        calibration = calibration_for_policy(resolved_policy)
        estimate = estimate_project_export(
            project,
            resolved_policy,
            calibration=calibration,
        ).to_dict()
        upscale_policy_payload = _upscale_policy_payload(plan, project)

        if getattr(args, "plan_only", False):
            return success_payload(
                "export-plan" if args.command == "export-plan" else "export",
                {
                    "project": project_payload(
                        project,
                        args.project,
                        include_paths=args.full_paths,
                    ),
                    "export": {
                        "planned": True,
                        "verified": False,
                        "plan": _plan_payload(plan, include_paths=args.full_paths),
                        "frame_rate_policy": resolved_policy.to_dict(),
                        "upscale_policy": upscale_policy_payload,
                        "estimate": estimate,
                    },
                },
            )

        def report_progress(progress: ExportProgress) -> None:
            _write_json(output, progress_payload(progress))

        destination = execute_export_fn(
            plan,
            ffmpeg_path=args.ffmpeg,
            ffprobe_path=args.ffprobe,
            progress_callback=report_progress,
        )
        output_media = probe_media_fn(destination, args.ffprobe)
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
    return success_payload(
        "export",
        {
            "project": project_payload(
                project,
                args.project,
                include_paths=args.full_paths,
            ),
            "export": {
                "route": plan.route,
                "reason": plan.reason,
                "verified": True,
                "frame_rate_policy": resolved_policy.to_dict(),
                "upscale_policy": upscale_policy_payload,
                "estimate": estimate,
                "destination": display_path(
                    destination,
                    args.full_paths,
                ),
                "output": {
                    "duration_seconds": output_media.duration_seconds,
                    "width": output_media.width,
                    "height": output_media.height,
                    "frame_rate": output_media.frame_rate,
                    "video_codec": output_media.video_codec,
                    "audio_codec": output_media.audio_codec,
                    "format_name": output_media.format_name,
                    "audio_stream_present": output_media.has_audio_stream,
                },
            },
        },
    )


def _write_json(stream: TextIO, payload: dict[str, Any]) -> None:
    json.dump(payload, stream, ensure_ascii=True, sort_keys=True)
    stream.write("\n")
