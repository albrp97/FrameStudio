"""FrameStudio GUI and CLI entrypoint."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .cli_types import CLI_COMMANDS

WORKFLOW_COMMANDS = frozenset({"media", "concat", "fps"})


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="framestudio",
        description="Open FrameStudio or run one of its media workflows.",
        epilog=(
            "Use `framestudio media`, `framestudio concat`, or `framestudio fps` "
            "for the repository's media workflows. Editor operations such as "
            "`inspect` and `export` remain top-level commands."
        ),
    )
    source_group = parser.add_mutually_exclusive_group()
    source_group.add_argument(
        "--source",
        type=Path,
        help="open one source video",
    )
    source_group.add_argument(
        "--project",
        type=Path,
        help="reopen one editor project",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="framestudio 0.1.0",
    )
    parser.add_argument(
        "--smoke-test",
        action="store_true",
        help="exercise open, playback, seek, and optional save before exiting",
    )
    parser.add_argument(
        "--smoke-project",
        type=Path,
        help="project path to save during --smoke-test",
    )
    return parser


def _run_workflow(arguments: list[str]) -> int:
    command = arguments[0]
    workflow_arguments = arguments[1:]
    if command == "media":
        from framestudio_media import main as workflow_main
    elif command == "concat":
        from framestudio_concat import main as workflow_main
    else:
        from framestudio_fps import main as workflow_main
    return workflow_main(workflow_arguments, prog=f"framestudio {command}")


def main(argv: list[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    if arguments and arguments[0] in WORKFLOW_COMMANDS:
        return _run_workflow(arguments)
    if arguments and arguments[0] in CLI_COMMANDS:
        from .cli import cli_main

        return cli_main(arguments)
    args = build_parser().parse_args(arguments)
    if args.smoke_project is not None and not args.smoke_test:
        print(
            "framestudio: --smoke-project requires --smoke-test",
            file=sys.stderr,
        )
        return 2
    try:
        from .app import run_gui

        return run_gui(
            args.source,
            args.project,
            args.smoke_test,
            args.smoke_project,
        )
    except RuntimeError as error:
        print(f"framestudio: {error}", file=sys.stderr)
        return 2
