from __future__ import annotations

import argparse
from collections.abc import Callable
from pathlib import Path
from typing import TypeVar

from .app_removal import remove_selected_blocks
from .cli_types import CLI_EXIT_INVALID, CliError
from .model import Project, ProjectValidationError
from .removal_history import RemovalReceipt

__all__ = [
    "add_removal_parser",
]

_Parser = TypeVar("_Parser", bound=argparse.ArgumentParser)


def add_removal_parser(
    commands: argparse._SubParsersAction[_Parser],
) -> _Parser:
    """Register the parent-owned public ``remove`` parser and return it."""
    parser = commands.add_parser(
        "remove",
        help="remove one or more timeline blocks with track-local ripple",
    )
    parser.add_argument("project", type=Path)
    parser.add_argument(
        "--segment",
        dest="segments",
        action="append",
        required=True,
    )
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--full-paths",
        action="store_true",
        help="include absolute local paths in output",
    )
    return parser


def handle_remove(
    args: argparse.Namespace,
    *,
    load_project_fn: Callable[[Path], Project],
    save_project_fn: Callable[[Project, Path, Path | None], Path],
    project_result_fn: Callable[..., dict[str, object]],
) -> dict[str, object]:
    """Execute public CLI removal without exposing the runtime receipt."""
    project = load_project_fn(args.project)
    if project.segment_timeline is None:
        raise CliError(
            "invalid_project",
            "Project segment timeline is required",
            exit_code=CLI_EXIT_INVALID,
        )
    segment_ids = tuple(getattr(args, "segments", ()) or ())
    try:
        receipt: RemovalReceipt = remove_selected_blocks(
            project,
            segment_ids,
        )
    except ProjectValidationError as error:
        raise CliError(
            "invalid_operation",
            str(error),
            exit_code=CLI_EXIT_INVALID,
        ) from error

    destination = save_project_fn(
        project,
        args.project,
        getattr(args, "output", None),
    )
    return project_result_fn(
        "remove",
        project,
        destination,
        include_paths=bool(getattr(args, "full_paths", False)),
        operation={
            "removed_segment_ids": list(receipt.removed_segment_ids),
        },
    )
