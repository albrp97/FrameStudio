from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, TextIO

from .cli_export import handle_export, progress_payload
from .cli_parser import JsonArgumentParser, build_cli_parser
from .cli_payload import (
    display_path as _display_path,
)
from .cli_payload import (
    project_payload,
)
from .cli_payload import (
    segment_payload as _segment_payload,
)
from .cli_payload import (
    source_payload as _source_payload,
)
from .cli_types import (
    CLI_COMMANDS,
    CLI_CONTRACT_VERSION,
    CLI_EXIT_DEPENDENCY,
    CLI_EXIT_INVALID,
    CLI_EXIT_OPERATION,
    CLI_EXIT_SUCCESS,
    CLI_EXIT_USAGE,
    CliError,
    error_payload,
    success_payload,
)
from .export import ExportProgress, execute_export
from .media import MediaProbeError, probe_media
from .model import Project, ProjectValidationError, Segment
from .operations import (
    analyze_project_audio,
    copy_segments,
    create_project_from_source,
    create_project_from_sources,
    move_segment,
    move_segments,
    paste_segments,
    plan_project_export,
    relink_project_source,
    set_segment_deleted,
    split_segment,
)
from .persistence import (
    ProjectPersistenceError,
    load_project,
    save_project,
)

__all__ = [
    "CLI_COMMANDS",
    "CLI_CONTRACT_VERSION",
    "CLI_EXIT_DEPENDENCY",
    "CLI_EXIT_INVALID",
    "CLI_EXIT_OPERATION",
    "CLI_EXIT_SUCCESS",
    "CLI_EXIT_USAGE",
    "CliError",
    "_display_path",
    "_segment_payload",
    "_source_payload",
    "build_cli_parser",
    "cli_main",
    "error_payload",
    "project_payload",
    "success_payload",
]

_JsonArgumentParser = JsonArgumentParser


def _load_project_for_cli(
    path: Path,
    *,
    allow_unavailable_sources: bool = False,
) -> Project:
    try:
        project = load_project(path)
    except ProjectPersistenceError as error:
        raise CliError(
            "project_io",
            str(error),
            exit_code=CLI_EXIT_INVALID,
        ) from error
    if not allow_unavailable_sources:
        for source in project.sources or (project.source,):
            status = source.status()
            if not status.available:
                raise CliError(
                    "source_unavailable",
                    status.reason or "Project source is unavailable",
                    exit_code=CLI_EXIT_INVALID,
                    details={"source_id": source.source_id},
                )
            if status.changed:
                raise CliError(
                    "source_changed",
                    status.reason or "Project source has changed",
                    exit_code=CLI_EXIT_INVALID,
                    details={"source_id": source.source_id},
                )
    return project


def _save_project_for_cli(
    project: Project,
    input_path: Path,
    output_path: Path | None,
) -> Path:
    destination = input_path.expanduser() if output_path is None else output_path.expanduser()
    source_paths = {Path(source.path).resolve() for source in project.sources or (project.source,)}
    if destination.resolve() in source_paths:
        raise CliError(
            "invalid_arguments",
            "Project destination must differ from every source video",
            exit_code=CLI_EXIT_INVALID,
        )
    try:
        return save_project(project, destination)
    except ProjectPersistenceError as error:
        raise CliError(
            "project_io",
            str(error),
            exit_code=CLI_EXIT_OPERATION,
        ) from error


def _project_result(
    command: str,
    project: Project,
    project_path: Path,
    *,
    include_paths: bool,
    operation: dict[str, Any] | None = None,
) -> dict[str, Any]:
    data: dict[str, Any] = {
        "project": project_payload(
            project,
            project_path,
            include_paths=include_paths,
        ),
    }
    if operation is not None:
        data["operation"] = operation
    return success_payload(command, data)


def _handle_import(args: argparse.Namespace) -> dict[str, Any]:
    sources = tuple(path.expanduser() for path in args.source)
    destination = args.output.expanduser()
    if destination.resolve() in {source.resolve() for source in sources}:
        raise CliError(
            "invalid_arguments",
            "Project destination must differ from every source video",
            exit_code=CLI_EXIT_INVALID,
        )
    try:
        if len(sources) == 1:
            project = create_project_from_source(sources[0], ffprobe_path=args.ffprobe)
        else:
            project = create_project_from_sources(sources, ffprobe_path=args.ffprobe)
        analyze_project_audio(project)
    except MediaProbeError as error:
        raise CliError(
            "media_probe",
            str(error),
            exit_code=(
                CLI_EXIT_DEPENDENCY if "not installed" in str(error).lower() else CLI_EXIT_INVALID
            ),
        ) from error
    except ProjectValidationError as error:
        raise CliError(
            "invalid_media",
            str(error),
            exit_code=CLI_EXIT_INVALID,
        ) from error
    saved = _save_project_for_cli(project, destination, destination)
    return _project_result(
        "import",
        project,
        saved,
        include_paths=args.full_paths,
        operation={"saved": True},
    )


def _handle_analyze_audio(args: argparse.Namespace) -> dict[str, Any]:
    project = _load_project_for_cli(args.project)
    decisions = analyze_project_audio(
        project,
        ffmpeg_path=args.ffmpeg,
    )
    destination = _save_project_for_cli(project, args.project, args.output)
    return _project_result(
        "analyze-audio",
        project,
        destination,
        include_paths=args.full_paths,
        operation={
            "source_ids": list(decisions),
            "statuses": {source_id: decision.status for source_id, decision in decisions.items()},
        },
    )


def _handle_open(args: argparse.Namespace) -> dict[str, Any]:
    project = _load_project_for_cli(args.project)
    return _project_result(
        args.command,
        project,
        args.project,
        include_paths=args.full_paths,
    )


def _handle_split(args: argparse.Namespace) -> dict[str, Any]:
    project = _load_project_for_cli(args.project)
    if project.segment_timeline is None:
        raise CliError(
            "invalid_project",
            "Project segment timeline is required",
            exit_code=CLI_EXIT_INVALID,
        )
    if project.segment_timeline.mixed_source and args.segment is None:
        raise CliError(
            "invalid_arguments",
            "Mixed-source split requires --segment",
            exit_code=CLI_EXIT_INVALID,
        )
    try:
        first, second = split_segment(
            project.segment_timeline,
            args.position,
            segment_id=args.segment,
            coordinate=args.coordinate,
        )
    except ProjectValidationError as error:
        raise CliError(
            "invalid_operation",
            str(error),
            exit_code=CLI_EXIT_INVALID,
        ) from error
    destination = _save_project_for_cli(project, args.project, args.output)
    return _project_result(
        "split",
        project,
        destination,
        include_paths=args.full_paths,
        operation={
            "position_seconds": args.position,
            "segment_ids": [first.segment_id, second.segment_id],
        },
    )


def _handle_move(args: argparse.Namespace) -> dict[str, Any]:
    project = _load_project_for_cli(args.project)
    try:
        if len(args.segments) == 1:
            changed = move_segment(project, args.segments[0], args.direction)
        else:
            changed = move_segments(project, args.segments, args.direction)
    except ProjectValidationError as error:
        raise CliError(
            "invalid_operation",
            str(error),
            exit_code=CLI_EXIT_INVALID,
        ) from error
    destination = _save_project_for_cli(project, args.project, args.output)
    return _project_result(
        "move",
        project,
        destination,
        include_paths=args.full_paths,
        operation={
            "segment_ids": list(args.segments),
            "direction": args.direction,
            "changed": changed,
        },
    )


def _handle_copy(args: argparse.Namespace) -> dict[str, Any]:
    project = _load_project_for_cli(args.project)
    try:
        copied = copy_segments(project, args.segments)
    except ProjectValidationError as error:
        raise CliError(
            "invalid_operation",
            str(error),
            exit_code=CLI_EXIT_INVALID,
        ) from error
    return success_payload(
        "copy",
        {
            "project": project_payload(
                project,
                args.project,
                include_paths=args.full_paths,
            ),
            "operation": {
                "segment_ids": list(args.segments),
                "blocks": [_segment_payload(segment) for segment in copied],
            },
        },
    )


def _handle_paste(args: argparse.Namespace) -> dict[str, Any]:
    project = _load_project_for_cli(args.project)
    try:
        copied = copy_segments(project, args.segments)
        pasted = paste_segments(project, copied, at_seconds=args.at)
    except ProjectValidationError as error:
        raise CliError(
            "invalid_operation",
            str(error),
            exit_code=CLI_EXIT_INVALID,
        ) from error
    destination = _save_project_for_cli(project, args.project, args.output)
    return _project_result(
        "paste",
        project,
        destination,
        include_paths=args.full_paths,
        operation={
            "source_segment_ids": list(args.segments),
            "pasted_segment_ids": [segment.segment_id for segment in pasted],
            "at_seconds": args.at,
        },
    )


def _handle_relink(args: argparse.Namespace) -> dict[str, Any]:
    project = _load_project_for_cli(
        args.project,
        allow_unavailable_sources=True,
    )
    source = project.source_by_id(args.source)
    try:
        replacement = relink_project_source(
            project,
            source.source_id,
            args.path,
            source.metadata,
        )
    except ProjectValidationError as error:
        raise CliError(
            "invalid_operation",
            str(error),
            exit_code=CLI_EXIT_INVALID,
        ) from error
    destination = _save_project_for_cli(project, args.project, args.output)
    return _project_result(
        "relink",
        project,
        destination,
        include_paths=args.full_paths,
        operation={
            "source_id": replacement.source_id,
            "path": _display_path(replacement.path, args.full_paths),
            "path_redacted": not args.full_paths,
        },
    )


def _find_segment(project: Project, segment_id: str) -> Segment:
    if project.segment_timeline is not None:
        for segment in project.segment_timeline.segment_items:
            if segment.segment_id == segment_id:
                return segment
    raise CliError(
        "invalid_operation",
        f"Unknown segment_id: {segment_id}",
        exit_code=CLI_EXIT_INVALID,
    )


def _handle_deletion(args: argparse.Namespace) -> dict[str, Any]:
    project = _load_project_for_cli(args.project)
    if project.segment_timeline is None:
        raise CliError(
            "invalid_project",
            "Project segment timeline is required",
            exit_code=CLI_EXIT_INVALID,
        )
    segment = _find_segment(project, args.segment)
    if args.command == "delete":
        deleted = True
    elif args.command == "restore":
        deleted = False
    else:
        deleted = not segment.deleted
    try:
        set_segment_deleted(
            project.segment_timeline,
            args.segment,
            deleted,
        )
    except ProjectValidationError as error:
        raise CliError(
            "invalid_operation",
            str(error),
            exit_code=CLI_EXIT_INVALID,
        ) from error
    destination = _save_project_for_cli(project, args.project, args.output)
    return _project_result(
        args.command,
        project,
        destination,
        include_paths=args.full_paths,
        operation={
            "segment_id": args.segment,
            "deleted": deleted,
        },
    )


def _handle_duration(args: argparse.Namespace) -> dict[str, Any]:
    project = _load_project_for_cli(args.project)
    if project.segment_timeline is None:
        raise CliError(
            "invalid_project",
            "Project segment timeline is required",
            exit_code=CLI_EXIT_INVALID,
        )
    timeline = project.segment_timeline
    return success_payload(
        "duration",
        {
            "project_id": project.project_id,
            "source_duration_seconds": timeline.source_duration_seconds,
            "duration_seconds": timeline.edited_duration_seconds,
            "active_segment_count": sum(not segment.deleted for segment in timeline.segment_items),
            "deleted_segment_count": sum(segment.deleted for segment in timeline.segment_items),
        },
    )


def _handle_save(args: argparse.Namespace) -> dict[str, Any]:
    project = _load_project_for_cli(args.project)
    destination = _save_project_for_cli(project, args.project, args.output)
    return _project_result(
        "save",
        project,
        destination,
        include_paths=args.full_paths,
        operation={"saved": True},
    )


def _progress_payload(progress: ExportProgress) -> dict[str, Any]:
    return progress_payload(progress)


def _handle_export(
    args: argparse.Namespace,
    output: TextIO,
) -> dict[str, Any]:
    return handle_export(
        args,
        output,
        load_project_fn=_load_project_for_cli,
        probe_media_fn=probe_media,
        plan_project_export_fn=plan_project_export,
        execute_export_fn=execute_export,
    )


def _handle_inspect(args: argparse.Namespace) -> dict[str, Any]:
    project = _load_project_for_cli(args.project)
    return success_payload(
        "inspect",
        {
            "project": project_payload(
                project,
                args.project,
                include_paths=args.full_paths,
            ),
        },
    )


def _dispatch(args: argparse.Namespace) -> dict[str, Any]:
    if args.command == "inspect":
        return _handle_inspect(args)
    if args.command == "import":
        return _handle_import(args)
    if args.command == "analyze-audio":
        return _handle_analyze_audio(args)
    if args.command == "move":
        return _handle_move(args)
    if args.command == "copy":
        return _handle_copy(args)
    if args.command == "paste":
        return _handle_paste(args)
    if args.command == "relink":
        return _handle_relink(args)
    if args.command in {"open", "reopen"}:
        return _handle_open(args)
    if args.command == "split":
        return _handle_split(args)
    if args.command in {"delete", "restore", "toggle-delete"}:
        return _handle_deletion(args)
    if args.command == "duration":
        return _handle_duration(args)
    if args.command == "save":
        return _handle_save(args)
    if args.command == "export":
        raise CliError(
            "internal_error",
            "Export output stream was not provided",
            exit_code=CLI_EXIT_OPERATION,
        )
    raise CliError(
        "unsupported_command",
        f"Command is not implemented: {args.command}",
    )


def _write_json(stream: TextIO, payload: dict[str, Any]) -> None:
    json.dump(payload, stream, ensure_ascii=True, sort_keys=True)
    stream.write("\n")


def cli_main(
    argv: list[str] | None = None,
    *,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
) -> int:
    output = sys.stdout if stdout is None else stdout
    error_output = sys.stderr if stderr is None else stderr
    parser = build_cli_parser()
    try:
        args = parser.parse_args(argv)
        if args.command == "export":
            payload = _handle_export(args, output)
        else:
            payload = _dispatch(args)
        _write_json(output, payload)
        return CLI_EXIT_SUCCESS
    except CliError as error:
        _write_json(
            error_output,
            error_payload(error.code, error.message, error.details),
        )
        return error.exit_code
