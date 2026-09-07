from __future__ import annotations

import fcntl
import hashlib
import json
import os
import shutil
import stat
import tempfile
import time
import uuid
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TypeVar

from .export_cache import (
    CACHE_DIRECTORY_SUFFIX,
    ExportCacheError,
    build_export_cache_request,
)

SESSION_SCHEMA_VERSION = 1
SESSION_DIRECTORY_SUFFIX = ".framestudio-session"
_T = TypeVar("_T")


class ExportSessionError(RuntimeError):
    """Raised when a resumable export session cannot be used safely."""


class ExportSessionBusy(ExportSessionError):
    """Raised when another worker owns the same export session."""


class ExportSessionNotFound(ExportSessionError):
    """Raised when an explicit resume is requested without a session."""


class ExportSessionMismatch(ExportSessionError):
    """Raised when an explicit resume does not match the current request."""


class ExportSessionInvalid(ExportSessionError):
    """Raised when a session manifest is corrupt or unsupported."""


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


def _request_key(request: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        _json_value(request),
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _timestamp() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _validate_root(root: Path) -> None:
    try:
        metadata = root.lstat()
    except FileNotFoundError:
        return
    except OSError as error:
        raise ExportSessionError(f"Could not inspect export session: {error}") from error
    if stat.S_ISLNK(metadata.st_mode):
        raise ExportSessionError("Export session path must not be a symbolic link")
    if not stat.S_ISDIR(metadata.st_mode):
        raise ExportSessionError("Export session path is not a directory")


def _safe_relative(root: Path, path: Path) -> Path:
    resolved_root = root.resolve()
    resolved_path = path.expanduser().resolve()
    try:
        return resolved_path.relative_to(resolved_root)
    except ValueError as error:
        raise ExportSessionError("Export session artifact escapes its session directory") from error


def _artifact_name(stage_id: str, suffix: str = ".artifact") -> str:
    safe = "".join(
        character if character.isalnum() or character in {"-", "_", "."} else "-"
        for character in stage_id
    ).strip(".")
    if not safe:
        raise ExportSessionError("Export session stage identifier is empty")
    normalized_suffix = suffix if suffix.startswith(".") else f".{suffix}"
    return f"{safe}{normalized_suffix}"


@dataclass(frozen=True)
class ExportSessionInfo:
    destination: Path
    root: Path
    exists: bool
    valid: bool
    request_key: str | None
    state: str | None
    last_completed_stage: str | None
    completed_stage_count: int
    stage_count: int
    last_error: str | None
    updated_at: str | None
    reason: str | None = None

    @property
    def resumable(self) -> bool:
        return self.exists and self.valid and self.state not in {"complete", "discarded"}

    def to_dict(self) -> dict[str, Any]:
        return {
            "destination": str(self.destination),
            "root": str(self.root),
            "exists": self.exists,
            "valid": self.valid,
            "request_key": self.request_key,
            "state": self.state,
            "last_completed_stage": self.last_completed_stage,
            "completed_stage_count": self.completed_stage_count,
            "stage_count": self.stage_count,
            "last_error": self.last_error,
            "updated_at": self.updated_at,
            "reason": self.reason,
            "resumable": self.resumable,
        }


def session_root(destination: Path) -> Path:
    resolved = destination.expanduser()
    return resolved.parent / f".{resolved.name}{SESSION_DIRECTORY_SUFFIX}"


def build_export_session_request(
    *,
    plan: Any,
    source_paths: Sequence[Path],
    source_stats: Sequence[os.stat_result],
    options: Mapping[str, Any] | None = None,
    runtime_paths: Mapping[str, Any] | None = None,
    ffmpeg_path: str = "ffmpeg",
    ffprobe_path: str = "ffprobe",
) -> dict[str, Any]:
    try:
        cache_request = build_export_cache_request(
            plan=plan,
            source_paths=tuple(source_paths),
            source_stats=tuple(source_stats),
            options=options or {},
            runtime_paths=runtime_paths or {},
            ffmpeg_path=ffmpeg_path,
            ffprobe_path=ffprobe_path,
        )
    except ExportCacheError as error:
        raise ExportSessionError(str(error)) from error
    return {
        "session_schema_version": SESSION_SCHEMA_VERSION,
        "plan": cache_request["plan"],
        "sources": cache_request["sources"],
        "options": cache_request["options"],
        "runtime_paths": cache_request["runtime_paths"],
        "ffmpeg_path": cache_request["ffmpeg_path"],
        "ffprobe_path": cache_request["ffprobe_path"],
        "destination": str(Path(plan.destination).expanduser().resolve()),
    }


def _read_manifest(root: Path) -> dict[str, Any] | None:
    manifest_path = root / "manifest.json"
    try:
        if stat.S_ISLNK(manifest_path.lstat().st_mode):
            raise ExportSessionInvalid("Export session manifest must not be a symbolic link")
    except FileNotFoundError:
        return None
    except OSError as error:
        raise ExportSessionInvalid(f"Could not inspect export session manifest: {error}") from error
    try:
        parsed = json.loads(manifest_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ExportSessionInvalid(f"Export session manifest is unreadable: {error}") from error
    if not isinstance(parsed, dict):
        raise ExportSessionInvalid("Export session manifest must contain an object")
    if parsed.get("schema_version") != SESSION_SCHEMA_VERSION:
        raise ExportSessionInvalid("Unsupported export session manifest version")
    if not isinstance(parsed.get("request"), dict):
        raise ExportSessionInvalid("Export session manifest request is invalid")
    if not isinstance(parsed.get("stages"), dict):
        raise ExportSessionInvalid("Export session manifest stages are invalid")
    return parsed


def _clear_session_root(root: Path) -> None:
    _validate_root(root)
    if not root.exists():
        return
    for child in tuple(root.iterdir()):
        if child.name == ".lock":
            continue
        try:
            if child.is_dir() and not child.is_symlink():
                shutil.rmtree(child)
            else:
                child.unlink()
        except OSError as error:
            raise ExportSessionError(
                f"Could not clear export session item {child.name}: {error}"
            ) from error


def _summary_from_manifest(
    destination: Path,
    root: Path,
    manifest: Mapping[str, Any],
) -> ExportSessionInfo:
    stages = manifest.get("stages", {})
    stage_values = tuple(stages.values()) if isinstance(stages, dict) else ()
    completed = [
        stage
        for stage in stage_values
        if isinstance(stage, dict) and stage.get("status") == "complete"
    ]
    ordered_completed = [
        (stage.get("order", 0), stage.get("id"))
        for stage in completed
        if isinstance(stage.get("id"), str)
    ]
    ordered_completed.sort()
    last_completed = ordered_completed[-1][1] if ordered_completed else None
    return ExportSessionInfo(
        destination=destination,
        root=root,
        exists=True,
        valid=True,
        request_key=manifest.get("request_key")
        if isinstance(manifest.get("request_key"), str)
        else None,
        state=manifest.get("state") if isinstance(manifest.get("state"), str) else None,
        last_completed_stage=last_completed,
        completed_stage_count=len(completed),
        stage_count=len(stage_values),
        last_error=manifest.get("last_error")
        if isinstance(manifest.get("last_error"), str)
        else None,
        updated_at=manifest.get("updated_at")
        if isinstance(manifest.get("updated_at"), str)
        else None,
    )


def discover_export_session(destination: Path) -> ExportSessionInfo:
    resolved = destination.expanduser()
    root = session_root(resolved)
    try:
        _validate_root(root)
    except ExportSessionError as error:
        return ExportSessionInfo(
            destination=resolved,
            root=root,
            exists=True,
            valid=False,
            request_key=None,
            state=None,
            last_completed_stage=None,
            completed_stage_count=0,
            stage_count=0,
            last_error=None,
            updated_at=None,
            reason=str(error),
        )
    if not root.exists():
        return ExportSessionInfo(
            destination=resolved,
            root=root,
            exists=False,
            valid=True,
            request_key=None,
            state=None,
            last_completed_stage=None,
            completed_stage_count=0,
            stage_count=0,
            last_error=None,
            updated_at=None,
        )
    try:
        manifest = _read_manifest(root)
    except ExportSessionInvalid as error:
        return ExportSessionInfo(
            destination=resolved,
            root=root,
            exists=True,
            valid=False,
            request_key=None,
            state=None,
            last_completed_stage=None,
            completed_stage_count=0,
            stage_count=0,
            last_error=None,
            updated_at=None,
            reason=str(error),
        )
    if manifest is None:
        return ExportSessionInfo(
            destination=resolved,
            root=root,
            exists=True,
            valid=False,
            request_key=None,
            state=None,
            last_completed_stage=None,
            completed_stage_count=0,
            stage_count=0,
            last_error=None,
            updated_at=None,
            reason="Export session manifest is missing",
        )
    return _summary_from_manifest(resolved, root, manifest)


@dataclass
class ExportSession:
    destination: Path
    root: Path
    request: dict[str, Any]
    request_key: str
    manifest: dict[str, Any]
    _lock_handle: Any = None

    @classmethod
    def open(
        cls,
        destination: Path,
        request: Mapping[str, Any],
        stage_ids: Sequence[str],
        *,
        mode: str = "fresh",
    ) -> ExportSession:
        if mode not in {"fresh", "resume", "restart"}:
            raise ExportSessionError(f"Unsupported export session mode: {mode}")
        resolved_destination = destination.expanduser()
        root = session_root(resolved_destination)
        request_value = _json_value(request)
        if not isinstance(request_value, dict):
            raise ExportSessionError("Export session request must be an object")
        request_key = _request_key(request_value)
        try:
            _validate_root(root)
            root.mkdir(parents=True, exist_ok=True)
            lock_path = root / ".lock"
            if lock_path.is_symlink():
                raise ExportSessionError("Export session lock must not be a symbolic link")
            lock_handle = lock_path.open("a+b")
            try:
                fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as error:
                lock_handle.close()
                raise ExportSessionBusy(
                    f"Export session is already active for {resolved_destination.name}"
                ) from error
        except ExportSessionError:
            raise
        except OSError as error:
            raise ExportSessionError(f"Could not open export session: {error}") from error

        try:
            existing = _read_manifest(root)
        except ExportSessionInvalid:
            if mode == "resume":
                lock_handle.close()
                raise
            existing = None
            _clear_session_root(root)

        if mode == "resume":
            if existing is None:
                lock_handle.close()
                raise ExportSessionNotFound(
                    f"No resumable export session exists for {resolved_destination.name}"
                )
            existing_key = existing.get("request_key")
            if existing_key != request_key:
                lock_handle.close()
                raise ExportSessionMismatch(
                    "Export session does not match the current project, sources, destination, "
                    "or export policy"
                )
            manifest = existing
        else:
            if mode == "fresh" and existing is not None:
                _clear_session_root(root)
            elif mode == "restart":
                _clear_session_root(root)
            manifest = {
                "schema_version": SESSION_SCHEMA_VERSION,
                "session_id": uuid.uuid4().hex,
                "request_key": request_key,
                "request": request_value,
                "state": "running",
                "stages": {},
                "last_error": None,
                "cancelled": False,
                "created_at": _timestamp(),
                "updated_at": _timestamp(),
            }
        stages = manifest.setdefault("stages", {})
        if not isinstance(stages, dict):
            lock_handle.close()
            raise ExportSessionInvalid("Export session stages are invalid")
        for index, stage_id in enumerate(stage_ids):
            if not isinstance(stage_id, str) or not stage_id:
                lock_handle.close()
                raise ExportSessionError(
                    "Export session stage identifiers must be non-empty strings"
                )
            stage = stages.get(stage_id)
            if not isinstance(stage, dict):
                stages[stage_id] = {
                    "id": stage_id,
                    "order": index,
                    "status": "pending",
                    "artifact": None,
                    "metadata": {},
                }
            else:
                stage.setdefault("id", stage_id)
                stage.setdefault("order", index)
                stage.setdefault("status", "pending")
                stage.setdefault("artifact", None)
                stage.setdefault("metadata", {})
        session = cls(
            destination=resolved_destination,
            root=root,
            request=dict(request_value),
            request_key=request_key,
            manifest=manifest,
            _lock_handle=lock_handle,
        )
        session._save_manifest()
        return session

    @property
    def artifacts_root(self) -> Path:
        path = self.root / "artifacts"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def last_completed_stage(self) -> str | None:
        info = _summary_from_manifest(self.destination, self.root, self.manifest)
        return info.last_completed_stage

    @property
    def reused_stage_count(self) -> int:
        stages = self.manifest.get("stages", {})
        if not isinstance(stages, dict):
            return 0
        return sum(
            1
            for stage in stages.values()
            if isinstance(stage, dict) and stage.get("reused") is True
        )

    def artifact_path(self, stage_id: str, *, suffix: str = ".artifact") -> Path:
        stage = self._stage(stage_id)
        artifact = stage.get("artifact")
        if isinstance(artifact, dict) and isinstance(artifact.get("path"), str):
            return self._path_for(artifact["path"])
        return self.artifacts_root / _artifact_name(stage_id, suffix)

    def _stage(self, stage_id: str) -> dict[str, Any]:
        stages = self.manifest.get("stages")
        if not isinstance(stages, dict):
            raise ExportSessionInvalid("Export session stages are invalid")
        stage = stages.get(stage_id)
        if not isinstance(stage, dict):
            stage = {
                "id": stage_id,
                "order": len(stages),
                "status": "pending",
                "artifact": None,
                "metadata": {},
            }
            stages[stage_id] = stage
        return stage

    def _path_for(self, relative: str) -> Path:
        return self.root / _safe_relative(self.root, self.root / relative)

    def _save_manifest(self) -> None:
        manifest_path = self.root / "manifest.json"
        self.manifest["updated_at"] = _timestamp()
        temporary_path: Path | None = None
        try:
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
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)
            raise ExportSessionError(f"Could not save export session manifest: {error}") from error

    def mark_running(self, stage_id: str) -> None:
        stage = self._stage(stage_id)
        stage["status"] = "running"
        stage["started_at"] = _timestamp()
        stage["reused"] = False
        self.manifest["state"] = "running"
        self.manifest["cancelled"] = False
        self.manifest["last_error"] = None
        self._save_manifest()

    def mark_complete(
        self,
        stage_id: str,
        *,
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        stage = self._stage(stage_id)
        stage["status"] = "complete"
        stage["completed_at"] = _timestamp()
        stage["metadata"] = _json_value(metadata or {})
        stage["reused"] = False
        self.manifest["state"] = "running"
        self.manifest["last_error"] = None
        self._save_manifest()

    def record(
        self,
        stage_id: str,
        path: Path,
        *,
        metadata: Mapping[str, Any] | None = None,
        validator: Callable[[Path], _T] | None = None,
    ) -> Path:
        source = path.expanduser()
        try:
            source_stat = source.stat()
        except OSError as error:
            raise ExportSessionError(
                f"Could not record export session artifact {stage_id}: {error}"
            ) from error
        if source_stat.st_size <= 0:
            raise ExportSessionError(f"Could not record empty export session artifact {stage_id}")
        destination = self.artifact_path(
            stage_id,
            suffix=source.suffix or ".artifact",
        )
        if source.resolve() != destination.resolve():
            temporary = destination.with_name(f".{destination.name}.tmp")
            try:
                shutil.copyfile(source, temporary)
                with temporary.open("rb") as stream:
                    os.fsync(stream.fileno())
                os.replace(temporary, destination)
            except OSError as error:
                temporary.unlink(missing_ok=True)
                raise ExportSessionError(
                    f"Could not persist export session artifact {stage_id}: {error}"
                ) from error
        if validator is not None:
            validator(destination)
        artifact_stat = destination.stat()
        relative = _safe_relative(self.root, destination)
        stage = self._stage(stage_id)
        stage["status"] = "complete"
        stage["completed_at"] = _timestamp()
        stage["reused"] = False
        stage["artifact"] = {
            "path": relative.as_posix(),
            "size": artifact_stat.st_size,
            "mtime_ns": artifact_stat.st_mtime_ns,
        }
        stage["metadata"] = _json_value(metadata or {})
        self.manifest["state"] = "running"
        self.manifest["last_error"] = None
        self._save_manifest()
        return destination

    def reuse(
        self,
        stage_id: str,
        validator: Callable[[Path], _T] | None = None,
    ) -> Path | None:
        stage = self._stage(stage_id)
        if stage.get("status") != "complete":
            return None
        artifact = stage.get("artifact")
        if not isinstance(artifact, dict) or not isinstance(artifact.get("path"), str):
            return None
        try:
            path = self._path_for(artifact["path"])
            stat_result = path.stat()
        except (OSError, ExportSessionError):
            self.invalidate(stage_id)
            return None
        if (
            stat_result.st_size <= 0
            or artifact.get("size") != stat_result.st_size
            or artifact.get("mtime_ns") != stat_result.st_mtime_ns
        ):
            self.invalidate(stage_id)
            return None
        try:
            if validator is not None:
                validator(path)
        except (OSError, TypeError, ValueError, RuntimeError):
            self.invalidate(stage_id)
            return None
        stage["reused"] = True
        self.manifest["last_reused_stage"] = stage_id
        self._save_manifest()
        return path

    def invalidate(self, stage_id: str) -> None:
        stages = self.manifest.get("stages")
        if not isinstance(stages, dict):
            return
        target = self._stage(stage_id)
        target_order = target.get("order", 0)
        for candidate_id, candidate in stages.items():
            if not isinstance(candidate, dict):
                continue
            if candidate_id == stage_id or candidate.get("order", 0) >= target_order:
                artifact = candidate.get("artifact")
                if isinstance(artifact, dict) and isinstance(artifact.get("path"), str):
                    self._path_for(artifact["path"]).unlink(missing_ok=True)
                candidate["status"] = "pending"
                candidate["artifact"] = None
                candidate["reused"] = False
                candidate.pop("completed_at", None)
        self.manifest["state"] = "running"
        self._save_manifest()

    def mark_failure(self, message: str, *, cancelled: bool = False) -> None:
        self.manifest["state"] = "cancelled" if cancelled else "failed"
        self.manifest["cancelled"] = cancelled
        self.manifest["last_error"] = str(message)
        self._save_manifest()

    def cleanup_after_success(self) -> None:
        self.manifest["state"] = "complete"
        self._save_manifest()
        self.close()
        try:
            shutil.rmtree(self.root)
        except FileNotFoundError:
            return
        except OSError as error:
            raise ExportSessionError(
                f"Export completed but its session could not be removed: {error}"
            ) from error

    def discard(self) -> None:
        self.close()
        try:
            shutil.rmtree(self.root)
        except FileNotFoundError:
            return
        except OSError as error:
            raise ExportSessionError(f"Could not discard export session: {error}") from error

    def close(self) -> None:
        if self._lock_handle is None:
            return
        try:
            fcntl.flock(self._lock_handle.fileno(), fcntl.LOCK_UN)
        finally:
            self._lock_handle.close()
            self._lock_handle = None

    def __enter__(self) -> ExportSession:
        return self

    def __exit__(self, _type: Any, _value: Any, _traceback: Any) -> None:
        self.close()


def discard_export_session(destination: Path) -> ExportSessionInfo:
    info = discover_export_session(destination)
    if not info.exists:
        return info
    root = info.root
    try:
        _validate_root(root)
        lock_path = root / ".lock"
        if lock_path.is_symlink():
            raise ExportSessionError("Export session lock must not be a symbolic link")
        with lock_path.open("a+b") as lock_handle:
            try:
                fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as error:
                raise ExportSessionBusy(
                    f"Export session is already active for {Path(destination).name}"
                ) from error
            shutil.rmtree(root)
        cache_root = destination.expanduser().parent / (
            f".{destination.expanduser().name}{CACHE_DIRECTORY_SUFFIX}"
        )
        if cache_root.exists():
            _validate_root(cache_root)
            shutil.rmtree(cache_root)
    except ExportSessionBusy:
        raise
    except OSError as error:
        raise ExportSessionError(f"Could not discard export session: {error}") from error
    return discover_export_session(destination)


def find_export_sessions_for_sources(
    directory: Path,
    source_paths: Sequence[Path],
) -> tuple[ExportSessionInfo, ...]:
    normalized_sources = {str(path.expanduser().resolve()) for path in source_paths}
    try:
        candidates = tuple(directory.expanduser().iterdir())
    except OSError:
        return ()
    matches: list[ExportSessionInfo] = []
    for candidate in candidates:
        if not candidate.name.endswith(SESSION_DIRECTORY_SUFFIX):
            continue
        destination_name = candidate.name[1 : -len(SESSION_DIRECTORY_SUFFIX)]
        if not destination_name:
            continue
        destination = candidate.parent / destination_name
        info = discover_export_session(destination)
        if not info.exists or not info.valid:
            continue
        try:
            manifest = _read_manifest(info.root)
        except ExportSessionInvalid:
            continue
        if manifest is None:
            continue
        request = manifest.get("request")
        request_sources = request.get("sources") if isinstance(request, dict) else None
        if not isinstance(request_sources, list):
            continue
        manifest_sources = {
            item.get("path")
            for item in request_sources
            if isinstance(item, dict) and isinstance(item.get("path"), str)
        }
        if manifest_sources and manifest_sources <= normalized_sources:
            matches.append(info)
    matches.sort(key=lambda item: item.updated_at or "", reverse=True)
    return tuple(matches)


__all__ = [
    "ExportSession",
    "ExportSessionBusy",
    "ExportSessionError",
    "ExportSessionInfo",
    "ExportSessionInvalid",
    "ExportSessionMismatch",
    "ExportSessionNotFound",
    "CACHE_DIRECTORY_SUFFIX",
    "SESSION_DIRECTORY_SUFFIX",
    "SESSION_SCHEMA_VERSION",
    "build_export_session_request",
    "discover_export_session",
    "discard_export_session",
    "find_export_sessions_for_sources",
    "session_root",
]
