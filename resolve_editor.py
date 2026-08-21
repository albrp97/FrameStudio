#!/usr/bin/env python3
"""Launch the focused local video editor."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from resolve_editor.app import run_gui
from resolve_editor.cli import CLI_COMMANDS, cli_main


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Open the focused local video editor.",
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
        version="resolve-editor 0.1.0",
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


def main(argv: list[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    if arguments and arguments[0] in CLI_COMMANDS:
        return cli_main(arguments)
    args = build_parser().parse_args(arguments)
    if args.smoke_project is not None and not args.smoke_test:
        print(
            "resolve-editor: --smoke-project requires --smoke-test",
            file=sys.stderr,
        )
        return 2
    try:
        return run_gui(
            args.source,
            args.project,
            args.smoke_test,
            args.smoke_project,
        )
    except RuntimeError as error:
        print(f"resolve-editor: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
