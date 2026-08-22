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
from .media import MediaProbe, MediaProbeError
from .model import Project
from .operations import export_destination_conflicts_with_project


def progress_payload(progress: ExportProgress) -> dict[str, Any]:
    return {
        "contract_version": CLI_CONTRACT_VERSION,
        "command": "export.progress",
        "event": "progress",
        "progress": asdict(progress),
    }


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
        plan = plan_project_export_fn(
            project,
            args.output,
            ffprobe_path=args.ffprobe,
            ffmpeg_path=args.ffmpeg,
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
