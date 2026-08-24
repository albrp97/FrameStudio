from __future__ import annotations

import argparse
from pathlib import Path
from typing import NoReturn

from .cli_types import CLI_EXIT_USAGE, CliError


class JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        raise CliError(
            "invalid_arguments",
            message,
            exit_code=CLI_EXIT_USAGE,
        )


def build_cli_parser() -> argparse.ArgumentParser:
    parser = JsonArgumentParser(
        prog="resolve-editor",
        description="Deterministic machine-readable editor operations.",
    )
    commands = parser.add_subparsers(
        dest="command",
        required=True,
        parser_class=JsonArgumentParser,
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
        help="create a project from one or more source videos",
    )
    import_parser.add_argument("source", type=Path, nargs="+")
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

    analyze_audio_parser = commands.add_parser(
        "analyze-audio",
        help="analyze and persist one source-level audio decision per source",
    )
    analyze_audio_parser.add_argument("project", type=Path)
    analyze_audio_parser.add_argument("--ffmpeg", default="ffmpeg")
    analyze_audio_parser.add_argument("--output", type=Path)
    analyze_audio_parser.add_argument("--full-paths", action="store_true")

    move_parser = commands.add_parser(
        "move",
        help="move one or more timeline blocks left or right",
    )
    move_parser.add_argument("project", type=Path)
    move_parser.add_argument(
        "--segment",
        dest="segments",
        action="append",
        required=True,
    )
    move_parser.add_argument("--direction", choices=("left", "right"), required=True)
    move_parser.add_argument("--output", type=Path)
    move_parser.add_argument("--full-paths", action="store_true")

    copy_parser = commands.add_parser(
        "copy",
        help="return fresh copies of one or more timeline blocks",
    )
    copy_parser.add_argument("project", type=Path)
    copy_parser.add_argument(
        "--segment",
        dest="segments",
        action="append",
        required=True,
    )
    copy_parser.add_argument("--full-paths", action="store_true")

    paste_parser = commands.add_parser(
        "paste",
        help="copy one or more blocks and insert them at a timeline position",
    )
    paste_parser.add_argument("project", type=Path)
    paste_parser.add_argument(
        "--segment",
        dest="segments",
        action="append",
        required=True,
    )
    paste_parser.add_argument("--at", type=float, required=True)
    paste_parser.add_argument("--output", type=Path)
    paste_parser.add_argument("--full-paths", action="store_true")

    focus_parser = commands.add_parser(
        "focus",
        aliases=("set-focus",),
        help="apply a shared visual focus transform to one or more segments",
    )
    focus_parser.add_argument("project", type=Path)
    focus_parser.add_argument(
        "--segment",
        dest="segments",
        action="append",
        required=True,
    )
    focus_parser.add_argument("--zoom", type=float, default=1.0)
    focus_parser.add_argument("--offset-x", "--x", dest="offset_x", type=float, default=0.0)
    focus_parser.add_argument("--offset-y", "--y", dest="offset_y", type=float, default=0.0)
    focus_parser.add_argument("--output", type=Path)
    focus_parser.add_argument("--full-paths", action="store_true")

    clean_focus_parser = commands.add_parser(
        "clean-focus",
        aliases=("clean-modifications",),
        help="reset visual focus and triplicate state for selected segments",
    )
    clean_focus_parser.add_argument("project", type=Path)
    clean_focus_parser.add_argument(
        "--segment",
        dest="segments",
        action="append",
        required=True,
    )
    clean_focus_parser.add_argument("--output", type=Path)
    clean_focus_parser.add_argument("--full-paths", action="store_true")

    copy_focus_parser = commands.add_parser(
        "copy-focus",
        help="copy one segment's visual focus values to other segments",
    )
    copy_focus_parser.add_argument("project", type=Path)
    copy_focus_parser.add_argument("--source-segment", required=True)
    copy_focus_parser.add_argument(
        "--segment",
        dest="segments",
        action="append",
        required=True,
    )
    copy_focus_parser.add_argument("--output", type=Path)
    copy_focus_parser.add_argument("--full-paths", action="store_true")

    for command, aliases, help_text in (
        (
            "triplicate-enable",
            ("enable-triplicate",),
            "enable linked center, left, and right composition instances",
        ),
        (
            "triplicate-disable",
            ("disable-triplicate",),
            "disable linked triplicate composition instances",
        ),
    ):
        triplicate_parser = commands.add_parser(
            command,
            aliases=aliases,
            help=help_text,
        )
        triplicate_parser.add_argument("project", type=Path)
        triplicate_parser.add_argument(
            "--segment",
            dest="segments",
            action="append",
            required=True,
        )
        triplicate_parser.add_argument("--output", type=Path)
        triplicate_parser.add_argument("--full-paths", action="store_true")

    relink_parser = commands.add_parser(
        "relink",
        help="relink a source identity to a replacement local file",
    )
    relink_parser.add_argument("project", type=Path)
    relink_parser.add_argument("--source", required=True)
    relink_parser.add_argument("--path", type=Path, required=True)
    relink_parser.add_argument("--output", type=Path)
    relink_parser.add_argument("--full-paths", action="store_true")

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
    split_parser.add_argument(
        "project",
        type=Path,
    )
    split_parser.add_argument(
        "--at",
        "--position",
        dest="position",
        type=float,
        required=True,
    )
    split_parser.add_argument("--segment")
    split_parser.add_argument(
        "--coordinate",
        choices=("source", "timeline"),
        default="source",
    )
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
