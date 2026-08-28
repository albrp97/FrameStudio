from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from .model import Project, ProjectValidationError


class ProjectPersistenceError(RuntimeError):
    """Raised when a project cannot be safely saved or loaded."""


def _cleanup_partial(path: Path | None) -> OSError | None:
    if path is None:
        return None
    try:
        path.unlink()
    except FileNotFoundError:
        return None
    except OSError as error:
        return error
    return None


def save_project(project: Project, destination: Path) -> Path:
    target = Path(destination).expanduser()
    partial: Path | None = None
    file_descriptor: int | None = None
    try:
        project.validate()
        payload = (
            json.dumps(
                project.to_dict(),
                indent=2,
                sort_keys=True,
                ensure_ascii=True,
            )
            + "\n"
        )
        target.parent.mkdir(parents=True, exist_ok=True)
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
    except (OSError, TypeError, ValueError, ProjectValidationError) as error:
        if file_descriptor is not None:
            os.close(file_descriptor)
        cleanup_error = _cleanup_partial(partial)
        message = f"Could not save project {target.name}: {error}"
        if cleanup_error is not None:
            message += f"; could not remove partial file: {cleanup_error}"
        raise ProjectPersistenceError(message) from error
    return target


def load_project(path: Path) -> Project:
    source = Path(path).expanduser()
    try:
        payload = source.read_text(encoding="utf-8")
    except FileNotFoundError as error:
        raise ProjectPersistenceError(f"Project file does not exist: {source.name}") from error
    except OSError as error:
        raise ProjectPersistenceError(f"Could not read project {source.name}: {error}") from error
    try:
        value = json.loads(payload)
    except json.JSONDecodeError as error:
        raise ProjectPersistenceError(f"Project file is not valid JSON: {source.name}") from error
    try:
        return Project.from_dict(value)
    except ProjectValidationError as error:
        raise ProjectPersistenceError(f"Project file is invalid: {source.name}: {error}") from error
