from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any, NoReturn, TextIO

from .export import (
    ExportExecutionError,
    ExportPlanningError,
    ExportProgress,
    execute_export,
)
from .media import MediaProbeError, probe_media
from .model import Project, ProjectValidationError, Segment, SourceReference
from .operations import (
    create_project_from_source,
    export_destination_conflicts_with_project,
    plan_project_export,
    set_segment_deleted,
    split_segment,
)
from .persistence import (
    ProjectPersistenceError,
    load_project,
    save_project,
)

CLI_CONTRACT_VERSION = 1
CLI_EXIT_SUCCESS = 0
CLI_EXIT_USAGE = 2
CLI_EXIT_INVALID = 3
CLI_EXIT_DEPENDENCY = 4
CLI_EXIT_OPERATION = 5
CLI_COMMANDS = frozenset(
    {
        "inspect",
        "import",
        "open",
        "reopen",
        "split",
        "delete",
        "restore",
        "toggle-delete",
        "duration",
        "save",
        "export",
    }
)


class CliError(RuntimeError):
    """An expected CLI failure with a stable machine-readable code."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        exit_code: int = CLI_EXIT_OPERATION,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.exit_code = exit_code
        self.details = {} if details is None else details


def success_payload(command: str, data: dict[str, Any]) -> dict[str, Any]:
    return {
        "ok": True,
        "contract_version": CLI_CONTRACT_VERSION,
        "command": command,
        **data,
    }


def error_payload(
    code: str,
    message: str,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "ok": False,
        "contract_version": CLI_CONTRACT_VERSION,
        "error": {
            "code": code,
            "message": message,
            "details": {} if details is None else details,
        },
    }


def _display_path(path: str | Path, include_paths: bool) -> str:
    value = Path(path).expanduser()
    return str(value.resolve()) if include_paths else value.name


def _source_payload(
    source: SourceReference,
    *,
    include_paths: bool,
) -> dict[str, Any]:
    status = source.status()
    return {
        "source_id": source.source_id,
        "path": _display_path(source.path, include_paths),
        "uri": (source.uri if include_paths else Path(source.path).name),
        "path_redacted": not include_paths,
        "size_bytes": source.size_bytes,
        "modified_time_ns": source.modified_time_ns,
        "metadata": dict(source.metadata),
        "status": {
            "available": status.available,
            "changed": status.changed,
            "reason": status.reason,
        },
    }


def _segment_payload(segment: Segment) -> dict[str, Any]:
    return {
        "segment_id": segment.segment_id,
        "start_seconds": segment.start_seconds,
        "end_seconds": segment.end_seconds,
        "duration_seconds": segment.duration_seconds,
        "deleted": segment.deleted,
    }


def project_payload(
    project: Project,
    project_path: Path | None = None,
    *,
    include_paths: bool = False,
) -> dict[str, Any]:
    project.validate()
    timeline = project.segment_timeline
    if timeline is None:
        raise CliError(
            "invalid_project",
            "Project segment timeline is required",
            exit_code=CLI_EXIT_INVALID,
        )
    return {
        "project_id": project.project_id,
        "schema_version": project.schema_version,
        "project_path": (
            None if project_path is None else _display_path(project_path, include_paths)
        ),
        "source": _source_payload(
            project.source,
            include_paths=include_paths,
        ),
        "timeline": {
            "source_duration_seconds": timeline.source_duration_seconds,
            "edited_duration_seconds": timeline.edited_duration_seconds,
            "playhead_seconds": project.playhead_seconds,
            "segments": [_segment_payload(segment) for segment in timeline.segment_items],
        },
        "export": {
            "exportable": timeline.edited_duration_seconds > 0,
            "active_segment_count": sum(not segment.deleted for segment in timeline.segment_items),
            "deleted_segment_count": sum(segment.deleted for segment in timeline.segment_items),
        },
    }


class _JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        raise CliError(
            "invalid_arguments",
            message,
            exit_code=CLI_EXIT_USAGE,
        )


def build_cli_parser() -> argparse.ArgumentParser:
    parser = _JsonArgumentParser(
        prog="resolve-editor",
        description="Deterministic machine-readable editor operations.",
    )
    commands = parser.add_subparsers(
        dest="command",
        required=True,
        parser_class=_JsonArgumentParser,
    )
    inspect_parser = commands.add_parser(
        "inspect",
        help="inspect a project",
    )
    inspect_parser.add_argument("project", type=Path)
    inspect_parser.add_argument(
        "--full-paths",
        action="store_true",
        help="include absolute local paths in output",
    )
    import_parser = commands.add_parser(
        "import",
        help="create a project from one source video",
    )
    import_parser.add_argument("source", type=Path)
    import_destination = import_parser.add_mutually_exclusive_group(
        required=True,
    )
    import_destination.add_argument(
        "--project",
        "--output",
        dest="output",
        type=Path,
        help="destination project path",
    )
    import_parser.add_argument("--ffprobe", default="ffprobe")
    import_parser.add_argument(
        "--full-paths",
        action="store_true",
        help="include absolute local paths in output",
    )

    for command in ("open", "reopen"):
        open_parser = commands.add_parser(
            command,
            help="load and inspect a project",
        )
        open_parser.add_argument("project", type=Path)
        open_parser.add_argument(
            "--full-paths",
            action="store_true",
            help="include absolute local paths in output",
        )

    split_parser = commands.add_parser(
        "split",
        help="split one source segment at a source position",
    )
    split_parser.add_argument("project", type=Path)
    split_parser.add_argument("--at", "--position", dest="position", type=float, required=True)
    split_parser.add_argument("--output", type=Path)
    split_parser.add_argument(
        "--full-paths",
        action="store_true",
        help="include absolute local paths in output",
    )

    for command in ("delete", "restore", "toggle-delete"):
        deletion_parser = commands.add_parser(
            command,
            help="change one segment deletion state",
        )
        deletion_parser.add_argument("project", type=Path)
        deletion_parser.add_argument("--segment", required=True)
        deletion_parser.add_argument("--output", type=Path)
        deletion_parser.add_argument(
            "--full-paths",
            action="store_true",
            help="include absolute local paths in output",
        )

    duration_parser = commands.add_parser(
        "duration",
        help="report source and edited durations",
    )
    duration_parser.add_argument("project", type=Path)

    save_parser = commands.add_parser(
        "save",
        help="load and atomically save a project",
    )
    save_parser.add_argument("project", type=Path)
    save_parser.add_argument("--output", type=Path)
    save_parser.add_argument(
        "--full-paths",
        action="store_true",
        help="include absolute local paths in output",
    )

    export_parser = commands.add_parser(
        "export",
        help="export an edited project through the verified export path",
    )
    export_parser.add_argument("project", type=Path)
    export_parser.add_argument("--output", type=Path, required=True)
    export_parser.add_argument("--ffmpeg", default="ffmpeg")
    export_parser.add_argument("--ffprobe", default="ffprobe")
    export_parser.add_argument(
        "--full-paths",
        action="store_true",
        help="include absolute local paths in output",
    )
    return parser


def _load_project_for_cli(path: Path) -> Project:
    try:
        project = load_project(path)
    except ProjectPersistenceError as error:
        raise CliError(
            "project_io",
            str(error),
            exit_code=CLI_EXIT_INVALID,
        ) from error
    status = project.source.status()
    if not status.available:
        raise CliError(
            "source_unavailable",
            status.reason or "Project source is unavailable",
            exit_code=CLI_EXIT_INVALID,
        )
    if status.changed:
        raise CliError(
            "source_changed",
            status.reason or "Project source has changed",
            exit_code=CLI_EXIT_INVALID,
        )
    return project


def _save_project_for_cli(
    project: Project,
    input_path: Path,
    output_path: Path | None,
) -> Path:
    destination = input_path.expanduser() if output_path is None else output_path.expanduser()
    if destination.resolve() == Path(project.source.path).resolve():
        raise CliError(
            "invalid_arguments",
            "Project destination must differ from the source video",
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
    source = args.source.expanduser()
    destination = args.output.expanduser()
    if destination.resolve() == source.resolve():
        raise CliError(
            "invalid_arguments",
            "Project destination must differ from the source video",
            exit_code=CLI_EXIT_INVALID,
        )
    try:
        project = create_project_from_source(
            source,
            ffprobe_path=args.ffprobe,
        )
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
    try:
        first, second = split_segment(
            project.segment_timeline,
            args.position,
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
    return {
        "contract_version": CLI_CONTRACT_VERSION,
        "command": "export.progress",
        "event": "progress",
        "progress": asdict(progress),
    }


def _handle_export(
    args: argparse.Namespace,
    output: TextIO,
) -> dict[str, Any]:
    project = _load_project_for_cli(args.project)
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
        plan = plan_project_export(
            project,
            args.output,
            ffprobe_path=args.ffprobe,
        )

        def report_progress(progress: ExportProgress) -> None:
            _write_json(output, _progress_payload(progress))

        destination = execute_export(
            plan,
            ffmpeg_path=args.ffmpeg,
            ffprobe_path=args.ffprobe,
            progress_callback=report_progress,
        )
        output_media = probe_media(destination, args.ffprobe)
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
                "destination": _display_path(
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
