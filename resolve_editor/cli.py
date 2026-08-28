from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Callable, TextIO

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
from .export_estimates import (
    SourceWorkload,
    calibration_for_policy,
    estimate_export,
)
from .export_naming import (
    ExportDestinationError,
    collision_safe_destination,
    smart_export_name,
)
from .fps_policy import (
    FrameRatePolicyError,
    ResolvedFrameRatePolicy,
    policy_source_metadata,
    resolve_frame_rate_policy,
)
from .interpolation import resolve_frame_rate_policy_with_fallback
from .media import MediaProbeError, probe_media
from .model import Project, ProjectValidationError, Segment
from .operations import (
    analyze_project_audio,
    apply_visual_transform,
    clean_visual_modifications,
    copy_segments,
    copy_visual_transform,
    create_project_from_source,
    create_project_from_sources,
    disable_triplicate,
    enable_triplicate,
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
from .upscale_policy import (
    ResolvedUpscalePolicy,
    UpscalePolicy,
    UpscalePolicyError,
    resolve_upscale_policy,
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


def _handle_focus(args: argparse.Namespace) -> dict[str, Any]:
    project = _load_project_for_cli(args.project)
    try:
        transform = apply_visual_transform(
            project,
            args.segments,
            zoom=args.zoom,
            offset_x=args.offset_x,
            offset_y=args.offset_y,
        )
    except ProjectValidationError as error:
        raise CliError(
            "invalid_operation",
            str(error),
            exit_code=CLI_EXIT_INVALID,
        ) from error
    destination = _save_project_for_cli(project, args.project, args.output)
    return _project_result(
        "focus",
        project,
        destination,
        include_paths=args.full_paths,
        operation={
            "segment_ids": list(args.segments),
            "visual_transform": transform.to_dict(),
        },
    )


def _handle_clean_focus(args: argparse.Namespace) -> dict[str, Any]:
    project = _load_project_for_cli(args.project)
    try:
        clean_visual_modifications(project, args.segments)
    except ProjectValidationError as error:
        raise CliError(
            "invalid_operation",
            str(error),
            exit_code=CLI_EXIT_INVALID,
        ) from error
    destination = _save_project_for_cli(project, args.project, args.output)
    return _project_result(
        "clean-focus",
        project,
        destination,
        include_paths=args.full_paths,
        operation={
            "segment_ids": list(args.segments),
            "cleaned": True,
        },
    )


def _handle_copy_focus(args: argparse.Namespace) -> dict[str, Any]:
    project = _load_project_for_cli(args.project)
    try:
        transform = copy_visual_transform(
            project,
            args.source_segment,
            args.segments,
        )
    except ProjectValidationError as error:
        raise CliError(
            "invalid_operation",
            str(error),
            exit_code=CLI_EXIT_INVALID,
        ) from error
    destination = _save_project_for_cli(project, args.project, args.output)
    return _project_result(
        "copy-focus",
        project,
        destination,
        include_paths=args.full_paths,
        operation={
            "source_segment_id": args.source_segment,
            "destination_segment_ids": list(args.segments),
            "visual_transform": transform.to_dict(),
        },
    )


def _handle_triplicate(args: argparse.Namespace) -> dict[str, Any]:
    project = _load_project_for_cli(args.project)
    enabled = args.command in {"triplicate-enable", "enable-triplicate"}
    try:
        if enabled:
            enable_triplicate(project, args.segments)
        else:
            disable_triplicate(project, args.segments)
    except ProjectValidationError as error:
        raise CliError(
            "invalid_operation",
            str(error),
            exit_code=CLI_EXIT_INVALID,
        ) from error
    destination = _save_project_for_cli(project, args.project, args.output)
    return _project_result(
        "triplicate-enable" if enabled else "triplicate-disable",
        project,
        destination,
        include_paths=args.full_paths,
        operation={
            "segment_ids": list(args.segments),
            "enabled": enabled,
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


def _policy_metadata(project: Project) -> tuple[dict[str, Any], ...]:
    return policy_source_metadata(project.sources or (project.source,))


def _frame_rate_policy_override(
    project: Project,
    args: argparse.Namespace,
) -> ResolvedFrameRatePolicy:
    choice = getattr(args, "fps_choice", None)
    custom_rate = getattr(args, "custom_fps", None)
    enhancement = getattr(args, "enhance_fps", None)
    backend = getattr(args, "fps_backend", None)
    current = project.get_frame_rate_policy()
    selected_choice = current.choice if choice is None else choice
    selected_custom_rate = current.custom_rate if custom_rate is None else custom_rate
    if selected_choice != "custom":
        selected_custom_rate = None
    selected_enhancement = current.enhancement_enabled if enhancement is None else enhancement
    selected_backend = current.backend if backend is None else backend
    try:
        resolved, _validations, _notice = resolve_frame_rate_policy_with_fallback(
            _policy_metadata(project),
            choice=selected_choice,
            custom_rate=selected_custom_rate,
            enhancement_enabled=selected_enhancement,
            backend=selected_backend,
            ffmpeg_path=getattr(args, "ffmpeg", "ffmpeg"),
        )
        if resolved.has_unsupported_sources:
            reasons = "; ".join(
                decision.reason
                for decision in resolved.decisions
                if decision.action == "unsupported"
            )
            raise CliError(
                "invalid_arguments",
                "Frame-rate enhancement is not supported for the selected sources"
                + (f": {reasons}" if reasons else ""),
                exit_code=CLI_EXIT_INVALID,
            )
        invalid_backend = next(
            (validation for validation in _validations if not validation.available),
            None,
        )
        if invalid_backend is not None:
            raise CliError(
                "dependency",
                invalid_backend.reason,
                exit_code=CLI_EXIT_DEPENDENCY,
            )
        return resolved
    except FrameRatePolicyError as error:
        raise CliError(
            "invalid_arguments",
            str(error),
            exit_code=CLI_EXIT_INVALID,
        ) from error


def _upscale_policy_override(
    project: Project,
    args: argparse.Namespace,
) -> ResolvedUpscalePolicy:
    current = project.get_upscale_policy()
    enabled = getattr(args, "enhance_upscale", None)
    model = getattr(args, "upscale_model", None)
    backend = getattr(args, "upscale_backend", None)
    try:
        return resolve_upscale_policy(
            _policy_metadata(project),
            policy=UpscalePolicy(
                enhancement_enabled=current.enhancement_enabled if enabled is None else enabled,
                model=current.model if model is None else model,
                backend=current.backend if backend is None else backend,
                target_short_side=current.target_short_side,
                landscape_max_short_side=current.landscape_max_short_side,
                portrait_max_short_side=current.portrait_max_short_side,
            ),
        )
    except UpscalePolicyError as error:
        raise CliError(
            "invalid_arguments",
            str(error),
            exit_code=CLI_EXIT_INVALID,
        ) from error


def _source_workloads(project: Project) -> tuple[SourceWorkload, ...]:
    timeline = project.timeline
    active_segments = tuple(segment for segment in timeline.segment_items if not segment.deleted)
    workloads: list[SourceWorkload] = []
    sources = {source.source_id: source for source in project.sources or (project.source,)}
    for source_id, source in sources.items():
        duration = sum(
            segment.duration_seconds
            for segment in active_segments
            if segment.source_id in {None, source_id}
        )
        if duration <= 0:
            continue
        rate = source.metadata.get("frame_rate")
        if rate is None:
            continue
        workloads.append(
            SourceWorkload(
                source_id=source_id,
                duration_seconds=duration,
                source_rate=rate,
            )
        )
    return tuple(workloads)


def _estimate_for_plan(
    project: Project,
    policy: ResolvedFrameRatePolicy,
) -> dict[str, Any]:
    calibration = calibration_for_policy(policy)
    return estimate_export(
        _source_workloads(project),
        policy,
        calibration=calibration,
    ).to_dict()


def _progress_payload(progress: ExportProgress) -> dict[str, Any]:
    return progress_payload(progress)


def _handle_export(
    args: argparse.Namespace,
    output: TextIO,
) -> dict[str, Any]:
    project = _load_project_for_cli(args.project)
    args.frame_rate_policy = _frame_rate_policy_override(project, args)
    args.upscale_policy = _upscale_policy_override(project, args)
    return handle_export(
        args,
        output,
        load_project_fn=_load_project_for_cli,
        probe_media_fn=probe_media,
        plan_project_export_fn=plan_project_export,
        execute_export_fn=execute_export,
    )


def _handle_export_plan(
    args: argparse.Namespace,
    output: TextIO,
) -> dict[str, Any]:
    project = _load_project_for_cli(args.project)
    policy = _frame_rate_policy_override(project, args)
    upscale_policy = _upscale_policy_override(project, args)
    if args.output is None:
        source_names = [source.path for source in project.sources or (project.source,)]
        filename = smart_export_name(
            source_names,
            policy=policy.policy,
            project_path=args.project,
        )
        try:
            destination = collision_safe_destination(args.project.parent, filename)
        except ExportDestinationError as error:
            raise CliError(
                "invalid_arguments",
                str(error),
                exit_code=CLI_EXIT_INVALID,
            ) from error
        args.output = destination
    args.plan_only = True
    args.frame_rate_policy = policy
    args.upscale_policy = upscale_policy
    return handle_export(
        args,
        output,
        load_project_fn=_load_project_for_cli,
        probe_media_fn=probe_media,
        plan_project_export_fn=plan_project_export,
        execute_export_fn=execute_export,
    )


def _handle_set_fps_policy(args: argparse.Namespace) -> dict[str, Any]:
    project = _load_project_for_cli(args.project)
    current = project.get_frame_rate_policy()
    selected_backend = current.backend if args.fps_backend is None else args.fps_backend
    selected_enhancement = (
        current.enhancement_enabled if args.enhance_fps is None else args.enhance_fps
    )
    try:
        resolved = resolve_frame_rate_policy(
            _policy_metadata(project),
            choice=args.fps_choice,
            custom_rate=args.custom_fps,
            enhancement_enabled=selected_enhancement,
            backend=selected_backend,
        )
        project.set_frame_rate_policy(resolved.policy)
    except FrameRatePolicyError as error:
        raise CliError(
            "invalid_arguments",
            str(error),
            exit_code=CLI_EXIT_INVALID,
        ) from error
    except ProjectValidationError as error:
        raise CliError(
            "invalid_operation",
            str(error),
            exit_code=CLI_EXIT_INVALID,
        ) from error
    destination = _save_project_for_cli(project, args.project, args.output)
    return _project_result(
        "set-fps-policy",
        project,
        destination,
        include_paths=args.full_paths,
        operation={
            "frame_rate_policy": resolved.to_dict(),
        },
    )


def _handle_set_upscale_policy(args: argparse.Namespace) -> dict[str, Any]:
    project = _load_project_for_cli(args.project)
    current = project.get_upscale_policy()
    try:
        resolved = resolve_upscale_policy(
            _policy_metadata(project),
            policy=UpscalePolicy(
                enhancement_enabled=args.enhance_upscale,
                model=current.model if args.upscale_model is None else args.upscale_model,
                backend=current.backend if args.upscale_backend is None else args.upscale_backend,
                target_short_side=current.target_short_side,
                landscape_max_short_side=current.landscape_max_short_side,
                portrait_max_short_side=current.portrait_max_short_side,
            ),
        )
        project.set_upscale_policy(resolved.policy)
    except (ProjectValidationError, UpscalePolicyError) as error:
        raise CliError(
            "invalid_arguments",
            str(error),
            exit_code=CLI_EXIT_INVALID,
        ) from error
    destination = _save_project_for_cli(project, args.project, args.output)
    return _project_result(
        "set-upscale-policy",
        project,
        destination,
        include_paths=args.full_paths,
        operation={
            "upscale_policy": resolved.to_dict(),
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
    handlers: dict[str, Callable[[argparse.Namespace], dict[str, Any]]] = {
        "inspect": _handle_inspect,
        "import": _handle_import,
        "analyze-audio": _handle_analyze_audio,
        "move": _handle_move,
        "copy": _handle_copy,
        "paste": _handle_paste,
        "focus": _handle_focus,
        "set-focus": _handle_focus,
        "clean-focus": _handle_clean_focus,
        "clean-modifications": _handle_clean_focus,
        "copy-focus": _handle_copy_focus,
        "triplicate-enable": _handle_triplicate,
        "enable-triplicate": _handle_triplicate,
        "triplicate-disable": _handle_triplicate,
        "disable-triplicate": _handle_triplicate,
        "relink": _handle_relink,
        "open": _handle_open,
        "reopen": _handle_open,
        "split": _handle_split,
        "delete": _handle_deletion,
        "restore": _handle_deletion,
        "toggle-delete": _handle_deletion,
        "duration": _handle_duration,
        "save": _handle_save,
        "set-fps-policy": _handle_set_fps_policy,
        "set-fps": _handle_set_fps_policy,
        "set-upscale-policy": _handle_set_upscale_policy,
        "set-upscale": _handle_set_upscale_policy,
    }
    if args.command == "export":
        raise CliError(
            "internal_error",
            "Export output stream was not provided",
            exit_code=CLI_EXIT_OPERATION,
        )
    handler = handlers.get(args.command)
    if handler is None:
        raise CliError(
            "unsupported_command",
            f"Command is not implemented: {args.command}",
        )
    return handler(args)


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
        elif args.command == "export-plan":
            payload = _handle_export_plan(args, output)
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
