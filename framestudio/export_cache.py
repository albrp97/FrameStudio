from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
import tempfile
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TypeVar

CACHE_SCHEMA_VERSION = 2
CACHE_DIRECTORY_SUFFIX = ".framestudio-intermediates"
_T = TypeVar("_T")


class CachedArtifactInvalid(ValueError):
    """Raised by a validator when a cached artifact is not reusable."""


class ExportCacheError(RuntimeError):
    """Raised when an export intermediate cache cannot be maintained."""


def _json_value(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value.expanduser().resolve())
    if isinstance(value, Mapping):
        return {
            str(key): _json_value(item)
            for key, item in sorted(value.items(), key=lambda item: str(item[0]))
        }
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _fingerprint(path: Path, stat_result: os.stat_result) -> dict[str, Any]:
    return {
        "path": str(path.expanduser().resolve()),
        "size": stat_result.st_size,
        "mtime_ns": stat_result.st_mtime_ns,
        "device": stat_result.st_dev,
        "inode": stat_result.st_ino,
    }


def _directory_fingerprint(directory: Path) -> dict[str, Any]:
    digest = hashlib.sha256()
    entries = 0

    def raise_walk_error(error: OSError) -> None:
        raise ExportCacheError(
            f"Could not inspect export runtime directory {directory}: {error}"
        ) from error

    for current, directories, files in os.walk(
        directory,
        topdown=True,
        followlinks=False,
        onerror=raise_walk_error,
    ):
        directories.sort()
        files.sort()
        for kind, names in (("directory", directories), ("file", files)):
            for name in names:
                path = Path(current) / name
                try:
                    stat_result = path.stat()
                except OSError as error:
                    raise ExportCacheError(
                        f"Could not inspect export runtime path {path}: {error}"
                    ) from error
                relative = path.relative_to(directory).as_posix()
                digest.update(
                    (
                        f"{kind}\0{relative}\0{stat_result.st_size}\0"
                        f"{stat_result.st_mtime_ns}\0{stat_result.st_dev}\0"
                        f"{stat_result.st_ino}\n"
                    ).encode("utf-8")
                )
                entries += 1
    return {"entries": entries, "sha256": digest.hexdigest()}


def _path_identity(path: Path) -> dict[str, Any]:
    resolved = path.expanduser().resolve()
    try:
        stat_result = resolved.stat()
    except FileNotFoundError:
        return {"path": str(resolved), "exists": False}
    except OSError as error:
        raise ExportCacheError(
            f"Could not inspect export runtime path {resolved}: {error}"
        ) from error
    identity = {
        "path": str(resolved),
        "exists": True,
        "kind": "directory" if resolved.is_dir() else "file",
        "size": stat_result.st_size,
        "mtime_ns": stat_result.st_mtime_ns,
        "device": stat_result.st_dev,
        "inode": stat_result.st_ino,
    }
    if stat.S_ISDIR(stat_result.st_mode):
        identity["tree"] = _directory_fingerprint(resolved)
    return identity


def _command_identity(command: str) -> dict[str, Any]:
    candidate = Path(command).expanduser()
    if candidate.is_absolute() or os.sep in command or (os.altsep and os.altsep in command):
        return _path_identity(candidate)
    resolved = shutil.which(command)
    if resolved is None:
        return {"command": command, "resolved": None}
    return _path_identity(Path(resolved))


def _runtime_value(value: Any) -> Any:
    if isinstance(value, Path):
        return _path_identity(value)
    if isinstance(value, Mapping):
        return {
            str(key): _runtime_value(item)
            for key, item in sorted(value.items(), key=lambda item: str(item[0]))
        }
    if isinstance(value, (list, tuple)):
        return [_runtime_value(item) for item in value]
    return _json_value(value)


def build_export_cache_request(
    *,
    plan: Any,
    source_paths: tuple[Path, ...],
    source_stats: tuple[os.stat_result, ...],
    options: Mapping[str, Any],
    runtime_paths: Mapping[str, Any] | None = None,
    ffmpeg_path: str,
    ffprobe_path: str,
) -> dict[str, Any]:
    if len(source_paths) != len(source_stats):
        raise ExportCacheError("Export cache source fingerprints do not match source paths")
    return {
        "schema_version": CACHE_SCHEMA_VERSION,
        "plan": _json_value(plan.to_dict()),
        "sources": [
            _fingerprint(path, stat_result)
            for path, stat_result in zip(source_paths, source_stats, strict=True)
        ],
        "options": _json_value(options),
        "runtime_paths": _runtime_value(runtime_paths or {}),
        "ffmpeg_path": _command_identity(ffmpeg_path),
        "ffprobe_path": _command_identity(ffprobe_path),
    }


def _request_key(request: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        _json_value(request),
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _clear_directory(directory: Path) -> None:
    _validate_cache_root(directory)
    try:
        children = tuple(directory.iterdir())
    except FileNotFoundError:
        return
    except OSError as error:
        raise ExportCacheError(f"Could not inspect export cache: {error}") from error
    for child in children:
        try:
            if child.is_dir() and not child.is_symlink():
                shutil.rmtree(child)
            else:
                child.unlink()
        except OSError as error:
            raise ExportCacheError(
                f"Could not clear export cache item {child.name}: {error}"
            ) from error


def _validate_cache_root(directory: Path) -> None:
    try:
        metadata = directory.lstat()
    except FileNotFoundError:
        return
    except OSError as error:
        raise ExportCacheError(f"Could not inspect export cache: {error}") from error
    if stat.S_ISLNK(metadata.st_mode):
        raise ExportCacheError("Export cache path must not be a symbolic link")
    if not stat.S_ISDIR(metadata.st_mode):
        raise ExportCacheError("Export cache path is not a directory")


@dataclass
class ExportCache:
    root: Path
    key: str
    request: dict[str, Any]
    manifest: dict[str, Any]

    @classmethod
    def open(
        cls,
        destination: Path,
        request: Mapping[str, Any],
    ) -> ExportCache:
        root = destination.parent / f".{destination.name}{CACHE_DIRECTORY_SUFFIX}"
        key = _request_key(request)
        manifest_path = root / "manifest.json"
        try:
            _validate_cache_root(root)
            root.mkdir(parents=True, exist_ok=True)
        except OSError as error:
            raise ExportCacheError(f"Could not create export cache: {error}") from error

        existing: dict[str, Any] | None = None
        try:
            if manifest_path.is_file():
                parsed = json.loads(manifest_path.read_text(encoding="utf-8"))
                if isinstance(parsed, dict):
                    existing = parsed
        except (OSError, TypeError, json.JSONDecodeError):
            existing = None

        if (
            existing is None
            or existing.get("schema_version") != CACHE_SCHEMA_VERSION
            or existing.get("cache_key") != key
        ):
            _clear_directory(root)
            manifest = {
                "schema_version": CACHE_SCHEMA_VERSION,
                "cache_key": key,
                "request": _json_value(request),
                "artifacts": {},
            }
            cache = cls(root=root, key=key, request=dict(request), manifest=manifest)
            cache._save_manifest()
            return cache

        artifacts = existing.get("artifacts")
        if not isinstance(artifacts, dict):
            artifacts = {}
        existing["artifacts"] = artifacts
        return cls(root=root, key=key, request=dict(request), manifest=existing)

    @property
    def reused_artifact_count(self) -> int:
        artifacts = self.manifest.get("artifacts", {})
        return len(artifacts) if isinstance(artifacts, dict) else 0

    def _save_manifest(self) -> None:
        manifest_path = self.root / "manifest.json"
        try:
            self.root.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self.root,
                prefix=".manifest-",
                suffix=".tmp",
                delete=False,
            ) as temporary:
                temporary_path = Path(temporary.name)
                json.dump(self.manifest, temporary, ensure_ascii=True, indent=2, sort_keys=True)
                temporary.write("\n")
                temporary.flush()
                os.fsync(temporary.fileno())
            os.replace(temporary_path, manifest_path)
        except OSError as error:
            if "temporary_path" in locals():
                temporary_path.unlink(missing_ok=True)
            raise ExportCacheError(f"Could not save export cache manifest: {error}") from error

    def _path_for(self, artifact_path: str) -> Path:
        candidate = (self.root / artifact_path).resolve()
        try:
            candidate.relative_to(self.root.resolve())
        except ValueError as error:
            raise ExportCacheError(
                "Export cache artifact path escapes the cache directory"
            ) from error
        return candidate

    def reuse(
        self,
        artifact_id: str,
        validator: Callable[[Path], _T],
    ) -> _T | None:
        artifacts = self.manifest.get("artifacts")
        if not isinstance(artifacts, dict):
            return None
        record = artifacts.get(artifact_id)
        if not isinstance(record, dict):
            return None
        artifact_name = record.get("path")
        if not isinstance(artifact_name, str) or not artifact_name:
            self.invalidate(artifact_id)
            return None
        path = self._path_for(artifact_name)
        try:
            stat_result = path.stat()
        except OSError:
            self.invalidate(artifact_id)
            return None
        if (
            stat_result.st_size <= 0
            or record.get("size") != stat_result.st_size
            or record.get("mtime_ns") != stat_result.st_mtime_ns
        ):
            self.invalidate(artifact_id)
            return None
        try:
            return validator(path)
        except CachedArtifactInvalid:
            self.invalidate(artifact_id)
            return None

    def record(
        self,
        artifact_id: str,
        path: Path,
        *,
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        resolved = path.expanduser().resolve()
        try:
            relative = resolved.relative_to(self.root.resolve())
            stat_result = resolved.stat()
        except (OSError, ValueError) as error:
            raise ExportCacheError(
                f"Could not record export cache artifact {artifact_id}: {error}"
            ) from error
        if stat_result.st_size <= 0:
            raise ExportCacheError(f"Could not record empty export cache artifact {artifact_id}")
        artifacts = self.manifest.setdefault("artifacts", {})
        if not isinstance(artifacts, dict):
            raise ExportCacheError("Export cache manifest artifacts are invalid")
        artifacts[artifact_id] = {
            "path": relative.as_posix(),
            "size": stat_result.st_size,
            "mtime_ns": stat_result.st_mtime_ns,
            "metadata": _json_value(metadata or {}),
        }
        self._save_manifest()

    def invalidate(self, artifact_id: str) -> None:
        artifacts = self.manifest.get("artifacts")
        if not isinstance(artifacts, dict):
            return
        record = artifacts.pop(artifact_id, None)
        if isinstance(record, dict):
            artifact_name = record.get("path")
            if isinstance(artifact_name, str):
                path = self._path_for(artifact_name)
                path.unlink(missing_ok=True)
        self._save_manifest()

    def discard_after_success(self) -> None:
        try:
            shutil.rmtree(self.root)
        except FileNotFoundError:
            return
        except OSError as error:
            raise ExportCacheError(
                f"Export completed but its intermediate cache could not be removed: {error}"
            ) from error


__all__ = [
    "CACHE_DIRECTORY_SUFFIX",
    "CACHE_SCHEMA_VERSION",
    "CachedArtifactInvalid",
    "ExportCache",
    "ExportCacheError",
    "build_export_cache_request",
]
