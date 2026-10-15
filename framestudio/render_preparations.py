from __future__ import annotations

import hashlib
import json
import os
import tempfile
import threading
import time
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from .export_cache import _command_identity, _path_identity
from .export_process import check_export_cancelled, report_preparation_progress
from .export_session import ExportSession, ExportSessionError, discover_export_session
from .export_types import ExportExecutionError, ExportProgressCallback


class PreparationCacheError(ExportExecutionError):
    """A checkpoint failure, not an unavailable enhancement backend."""


def file_digest(path: Path, cancel_event: threading.Event | None = None) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            while chunk := handle.read(1024 * 1024):
                check_export_cancelled(cancel_event)
                digest.update(chunk)
    except OSError as error:
        raise PreparationCacheError("Could not read checkpoint content identity") from error
    check_export_cancelled(cancel_event)
    return digest.hexdigest()


class RenderPreparations:
    """Content-addressed, verified stages inside an export's owned checkpoint root."""

    def __init__(
        self,
        root: Path,
        *,
        cancel_event: threading.Event | None = None,
        progress_callback: ExportProgressCallback | None = None,
    ) -> None:
        self.root = root
        self.cancel_event = cancel_event
        self.progress_callback = progress_callback
        self.hits = 0
        self.misses = 0
        self._ready: dict[str, Path] = {}
        self._runtime: dict[str, Any] = {}
        self._models: dict[Path, dict[str, Any]] = {}
        self.validation_data: dict[Path, Any] = {}

    def model_identity(self, path: Path) -> dict[str, Any]:
        path = path.expanduser().resolve()
        if path not in self._models:
            try:
                self._models[path] = {
                    "file": _path_identity(path),
                    "sha256": file_digest(path, self.cancel_event),
                }
            except OSError as error:
                raise PreparationCacheError("Could not fingerprint enhancement model") from error
        return self._models[path]

    def runtime(self, ffmpeg_path: str, ffprobe_path: str, *, neural: bool = False) -> Any:
        key = f"{ffmpeg_path}|{ffprobe_path}|{neural}"
        if key not in self._runtime:
            identity: dict[str, Any] = {
                "ffmpeg": _command_identity(ffmpeg_path),
                "ffprobe": _command_identity(ffprobe_path),
            }
            if neural:
                from framestudio_fps import (
                    DEFAULT_FPS_PYTHON,
                    DEFAULT_FPS_SITE,
                    DEFAULT_RVE_MODEL,
                    DEFAULT_RVE_RESTORATION_MODEL,
                    DEFAULT_RVE_ROOT,
                    DEFAULT_RVE_SHIMS,
                )

                identity["neural"] = [
                    _path_identity(path)
                    for path in (
                        DEFAULT_FPS_PYTHON,
                        DEFAULT_RVE_MODEL,
                        DEFAULT_RVE_RESTORATION_MODEL,
                    )
                ]
                code = sorted((DEFAULT_RVE_ROOT / "backend").rglob("*.py"))
                code.extend(sorted(DEFAULT_RVE_SHIMS.rglob("*.py")))
                code.extend(sorted(DEFAULT_FPS_SITE.glob("*dist-info/METADATA")))
                identity["runtime_code"] = [
                    (str(path), file_digest(path, self.cancel_event)) for path in code
                ]
            self._runtime[key] = identity
        return self._runtime[key]

    def materialize(
        self,
        stage: str,
        request: Mapping[str, Any],
        produce: Callable[[Path], object],
        validate: Callable[[Path], object],
        *,
        suffix: str = ".mp4",
    ) -> Path:
        check_export_cancelled(self.cancel_event)
        payload = {"preparation_version": 1, "stage": stage, "request": dict(request)}
        key = hashlib.sha256(
            json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
        ).hexdigest()
        if key in self._ready:
            self.hits += 1
            return self._ready[key]
        destination = self.root / f"{key}{suffix}"
        started = time.monotonic()
        session = None
        candidate = None
        producing = False
        try:
            info = discover_export_session(destination)
            session = ExportSession.open(
                destination, payload, (stage,), mode="resume" if info.exists else "fresh"
            )
            cached = session.reuse(stage)
            if cached is not None:
                record = session.manifest["stages"][stage]["metadata"]
                if isinstance(record, dict) and file_digest(
                    cached, self.cancel_event
                ) == record.get("sha256"):
                    self.hits += 1
                    self._ready[key] = cached
                    self.validation_data[cached] = record.get("validation")
                    report_preparation_progress(
                        self.progress_callback, f"Reusing verified {stage}", 1, 1, started
                    )
                    return cached
                session.invalidate(stage)
            self.misses += 1
            session.mark_running(stage)
            final_path = session.artifact_path(stage, suffix=suffix)
            with tempfile.NamedTemporaryFile(
                dir=final_path.parent,
                prefix=f"{final_path.stem}.partial-",
                suffix=suffix,
                delete=False,
            ) as temporary:
                candidate = Path(temporary.name)
            candidate.unlink()
            producing = True
            produce(candidate)
            producing = False
            check_export_cancelled(self.cancel_event)
            validation = validate(candidate)
            proof = file_digest(candidate, self.cancel_event)
            with candidate.open("rb") as handle:
                os.fsync(handle.fileno())
            os.replace(candidate, final_path)
            session.record(stage, final_path, metadata={"sha256": proof, "validation": validation})
            self._ready[key] = final_path
            self.validation_data[final_path] = validation
            report_preparation_progress(
                self.progress_callback, f"Checkpointed {stage}", 1, 1, started
            )
            return final_path
        except ExportSessionError as error:
            raise PreparationCacheError(str(error)) from error
        except OSError as error:
            if producing:
                raise
            raise PreparationCacheError(f"Could not persist or read {stage} checkpoint") from error
        finally:
            try:
                if candidate is not None:
                    candidate.unlink(missing_ok=True)
            except OSError as error:
                raise PreparationCacheError("Could not clean incomplete checkpoint") from error
            finally:
                if session is not None:
                    session.close()
