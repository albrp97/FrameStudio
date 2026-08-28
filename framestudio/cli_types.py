from __future__ import annotations

from typing import Any

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
        "analyze-audio",
        "move",
        "copy",
        "paste",
        "focus",
        "set-focus",
        "clean-focus",
        "clean-modifications",
        "copy-focus",
        "triplicate-enable",
        "enable-triplicate",
        "triplicate-disable",
        "disable-triplicate",
        "relink",
        "open",
        "reopen",
        "split",
        "delete",
        "restore",
        "toggle-delete",
        "duration",
        "save",
        "export",
        "export-plan",
        "set-fps-policy",
        "set-fps",
        "set-upscale-policy",
        "set-upscale",
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
