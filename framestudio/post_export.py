from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

POST_EXPORT_ACTIONS = ("nothing", "sleep", "shutdown")


class PostExportActionError(RuntimeError):
    """Raised when a requested post-export system action cannot be completed."""


def normalize_post_export_action(action: str | None) -> str:
    if action is None:
        return "nothing"
    normalized = action.strip().casefold().replace("_", "-")
    aliases = {
        "nothing": "nothing",
        "none": "nothing",
        "sleep": "sleep",
        "suspend": "sleep",
        "shutdown": "shutdown",
        "shut-down": "shutdown",
        "poweroff": "shutdown",
        "power-off": "shutdown",
    }
    try:
        return aliases[normalized]
    except KeyError as error:
        choices = ", ".join(POST_EXPORT_ACTIONS)
        raise PostExportActionError(
            f"Unsupported post-export action: {action!r}; choose one of {choices}",
        ) from error


def failure_log_path(
    project_path: Path | None,
    destination: Path | None,
) -> Path:
    anchor = project_path if project_path is not None else destination
    if anchor is None:
        anchor = Path.cwd() / "framestudio-export"
    anchor = Path(anchor).expanduser()
    return anchor.with_name(f"{anchor.stem}.export-failure.log")


def write_export_failure_log(
    *,
    project_path: Path | None,
    destination: Path | None,
    message: str,
    action: str,
    timestamp: datetime | None = None,
) -> Path:
    target = failure_log_path(project_path, destination)
    target.parent.mkdir(parents=True, exist_ok=True)
    when = timestamp or datetime.now(timezone.utc)
    safe_message = " ".join(str(message).splitlines()).strip() or "Unknown export failure"
    payload = (
        "FrameStudio export failure\n"
        f"Timestamp (UTC): {when.isoformat()}\n"
        f"Action: {normalize_post_export_action(action)}\n"
        f"Destination: {Path(destination).name if destination is not None else 'unknown'}\n"
        f"Error: {safe_message}\n"
    )
    partial: Path | None = None
    file_descriptor: int | None = None
    try:
        file_descriptor, partial_name = tempfile.mkstemp(
            prefix=f".{target.name}.partial-",
            dir=str(target.parent),
            text=True,
        )
        partial = Path(partial_name)
        with os.fdopen(file_descriptor, "w", encoding="utf-8") as handle:
            file_descriptor = None
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(partial, target)
        partial = None
    except (OSError, ValueError) as error:
        if file_descriptor is not None:
            os.close(file_descriptor)
        if partial is not None:
            try:
                partial.unlink()
            except FileNotFoundError:
                pass
            except OSError:
                pass
        raise PostExportActionError(
            f"Could not write export failure log {target.name}: {error}",
        ) from error
    return target


def execute_post_export_action(
    action: str | None,
    *,
    which: Callable[[str], str | None] | None = None,
    run: Callable[..., subprocess.CompletedProcess[str]] | None = None,
) -> None:
    which = shutil.which if which is None else which
    run = subprocess.run if run is None else run
    normalized = normalize_post_export_action(action)
    if normalized == "nothing":
        return
    command_name, operation = (
        ("systemctl", "suspend") if normalized == "sleep" else ("systemctl", "poweroff")
    )
    executable = which(command_name)
    if executable is None:
        loginctl = which("loginctl")
        if loginctl is not None:
            executable = loginctl
        else:
            raise PostExportActionError(
                f"Post-export action {normalized} is not available: "
                "systemctl or loginctl was not found",
            )
    try:
        run(
            [executable, operation],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            timeout=15,
        )
    except subprocess.CalledProcessError as error:
        detail = (error.stderr or "").strip()
        suffix = f": {detail}" if detail else ""
        raise PostExportActionError(
            f"Post-export action {normalized} failed{suffix}",
        ) from error
    except (OSError, subprocess.TimeoutExpired) as error:
        raise PostExportActionError(
            f"Post-export action {normalized} failed: {error}",
        ) from error


__all__ = [
    "POST_EXPORT_ACTIONS",
    "PostExportActionError",
    "execute_post_export_action",
    "failure_log_path",
    "normalize_post_export_action",
    "write_export_failure_log",
]
