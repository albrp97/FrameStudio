from __future__ import annotations

import os
from collections.abc import Iterable, Sequence
from pathlib import Path

from .fps_policy import FrameRatePolicy, rate_label

VIDEO_SUFFIXES = frozenset({".mkv", ".mov", ".mp4", ".webm"})


class ExportDestinationError(ValueError):
    """Raised when an export destination cannot be used safely."""


def _strip_project_suffix(stem: str) -> str:
    for suffix in (".resolve", ".project", ".editor"):
        if stem.casefold().endswith(suffix):
            return stem[: -len(suffix)]
    return stem


def _base_name(
    source_names: Sequence[str | Path],
    *,
    project_path: str | Path | None = None,
) -> str:
    if project_path is not None:
        project_stem = _strip_project_suffix(Path(project_path).stem)
        if project_stem:
            return project_stem
    for source_name in source_names:
        stem = Path(source_name).stem
        if stem:
            return stem
    return "export"


def smart_export_name(
    source_names: Sequence[str | Path],
    *,
    policy: FrameRatePolicy | None = None,
    backend: str | None = None,
    project_path: str | Path | None = None,
    extension: str = ".mp4",
) -> str:
    suffix = extension if extension.startswith(".") else f".{extension}"
    suffix = suffix.casefold()
    if suffix not in VIDEO_SUFFIXES:
        raise ExportDestinationError(f"Unsupported export extension: {suffix}")
    name = f"{_base_name(source_names, project_path=project_path)}-edited"
    if policy is not None and policy.enhancement_enabled:
        selected_backend = backend or policy.backend
        backend_label = selected_backend.casefold()
        if backend_label.startswith("rve-"):
            backend_label = f"rife{selected_backend[4:]}"
        elif backend_label == "rve":
            backend_label = "rife"
        else:
            backend_label = backend_label.replace(" ", "-")
        name += f"-{backend_label}-{rate_label(policy.target_rate)}fps"
    return f"{name}{suffix}"


def collision_safe_destination(folder: str | Path, filename: str) -> Path:
    destination_folder = Path(folder).expanduser()
    if not destination_folder.is_dir():
        raise ExportDestinationError(
            f"Export destination folder does not exist: {destination_folder}",
        )
    candidate = destination_folder / filename
    if not candidate.exists():
        return candidate
    stem = candidate.stem
    suffix = candidate.suffix
    counter = 1
    while True:
        alternative = destination_folder / f"{stem}-{counter}{suffix}"
        if not alternative.exists():
            return alternative
        counter += 1


def validate_export_destination(
    destination: str | Path,
    *,
    project_path: str | Path | None = None,
    source_paths: Iterable[str | Path] = (),
    require_writable: bool = True,
) -> Path:
    target = Path(destination).expanduser()
    if target.exists() and target.is_dir():
        raise ExportDestinationError("Export destination must be a file, not a directory")
    if target.suffix.casefold() not in VIDEO_SUFFIXES:
        raise ExportDestinationError(
            f"Export destination must use one of: {', '.join(sorted(VIDEO_SUFFIXES))}",
        )
    resolved = target.resolve()
    if project_path is not None and resolved == Path(project_path).expanduser().resolve():
        raise ExportDestinationError("Export destination must differ from the project file")
    source_resolved = {Path(path).expanduser().resolve() for path in source_paths}
    if resolved in source_resolved:
        raise ExportDestinationError("Export destination must differ from source media")
    parent = target.parent
    if not parent.is_dir():
        raise ExportDestinationError(f"Export folder does not exist: {parent}")
    if require_writable and not os.access(parent, os.W_OK):
        raise ExportDestinationError(f"Export folder is not writable: {parent}")
    if target.exists():
        raise ExportDestinationError(
            "Export destination already exists; choose the collision-safe suggested name",
        )
    return target
