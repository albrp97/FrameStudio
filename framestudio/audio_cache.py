from __future__ import annotations

import hashlib
import json
import math
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any, Mapping

from .audio import (
    AUDIO_POLICY_VERSION,
    LEGACY_AUDIO_POLICY,
    AudioAnalysisError,
    audio_decision_is_stale,
)
from .model_types import SourceReference

_CACHE_STATUSES = {"ready", "silent", "unsupported", "not-applicable"}


def _cache_path(source: SourceReference, ffmpeg_path: str) -> Path:
    path = Path(source.path).expanduser().resolve()
    source_stat = path.stat()
    if (
        source_stat.st_size != source.size_bytes
        or source_stat.st_mtime_ns != source.modified_time_ns
    ):
        raise AudioAnalysisError(
            f"Source changed since import; reload it before audio analysis: {path.name}"
        )
    executable = shutil.which(ffmpeg_path)
    tool = None if executable is None else Path(executable).resolve()
    tool_stat = None if tool is None else tool.stat()
    identity = {
        "version": 1,
        "source": str(path),
        "stat": (
            source_stat.st_dev,
            source_stat.st_ino,
            source_stat.st_size,
            source_stat.st_mtime_ns,
            source_stat.st_ctime_ns,
        ),
        "metadata": source.metadata,
        "policy": LEGACY_AUDIO_POLICY.to_dict(),
        "ffmpeg": (
            str(tool or ffmpeg_path),
            None if tool_stat is None else (tool_stat.st_size, tool_stat.st_mtime_ns),
        ),
    }
    key = hashlib.sha256(json.dumps(identity, sort_keys=True).encode("utf-8")).hexdigest()
    cache_home = os.environ.get("XDG_CACHE_HOME")
    base = Path(cache_home).expanduser() if cache_home else Path.home() / ".cache"
    return base / "framestudio" / "audio-analysis" / f"{key}.json"


def load_audio_analysis(source: SourceReference, *, ffmpeg_path: str) -> dict[str, Any] | None:
    try:
        path = _cache_path(source, ffmpeg_path)
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return None
        if not isinstance(payload, dict) or payload.get("version") != 1:
            raise ValueError("Unsupported cache record")
        settings = payload.get("settings")
        if (
            not isinstance(settings, dict)
            or settings.get("status") not in _CACHE_STATUSES
            or settings.get("policy_version") != AUDIO_POLICY_VERSION
            or audio_decision_is_stale(source, settings)
        ):
            raise ValueError("Invalid cached audio decision")
        gain = settings.get("gain_db")
        if isinstance(gain, bool) or not isinstance(gain, (int, float)) or not math.isfinite(gain):
            raise ValueError("Invalid cached audio gain")
        return settings
    except (OSError, TypeError, ValueError) as error:
        raise AudioAnalysisError(
            f"Could not read audio-analysis cache for {Path(source.path).name}: {error}"
        ) from error


def save_audio_analysis(
    source: SourceReference,
    settings: Mapping[str, Any],
    *,
    ffmpeg_path: str,
) -> None:
    if settings.get("status") not in _CACHE_STATUSES:
        return
    partial: Path | None = None
    try:
        target = _cache_path(source, ffmpeg_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=target.parent, prefix=".audio-", delete=False
        ) as handle:
            partial = Path(handle.name)
            json.dump({"version": 1, "settings": dict(settings)}, handle, sort_keys=True)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(partial, target)
        partial = None
    except (OSError, TypeError, ValueError) as error:
        if partial is not None:
            try:
                partial.unlink(missing_ok=True)
            except OSError as cleanup_error:
                raise AudioAnalysisError(
                    f"Could not save audio-analysis cache: {error}; "
                    f"partial cleanup failed: {cleanup_error}"
                ) from error
        raise AudioAnalysisError(
            f"Could not save audio-analysis cache for {Path(source.path).name}: {error}"
        ) from error
