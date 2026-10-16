from __future__ import annotations

import hashlib
import json
import os
import tempfile
import threading
import time
from collections.abc import Callable
from pathlib import Path

from .export_process import check_export_cancelled
from .export_types import ExportExecutionError

SourceHashKey = tuple[Path, int, int, int, int, int]
SourceHashCache = dict[SourceHashKey, str]


def _source_key(path: Path) -> SourceHashKey:
    stat = path.stat()
    return path, stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns


def _cache_record(key: SourceHashKey) -> tuple[Path, list[str | int]]:
    identity: list[str | int] = [str(key[0]), *key[1:]]
    name = hashlib.sha256(json.dumps(identity).encode("utf-8")).hexdigest()
    cache_home = os.environ.get("XDG_CACHE_HOME")
    root = Path(cache_home).expanduser() if cache_home else Path.home() / ".cache"
    return root / "framestudio" / "source-hashes" / f"{name}.json", identity


def _load_cached_hash(key: SourceHashKey) -> str | None:
    path, identity = _cache_record(key)
    try:
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return None
        if (
            not isinstance(record, dict)
            or record.get("version") != 1
            or record.get("identity") != identity
        ):
            raise ValueError("Invalid cache identity")
        digest = record.get("sha256")
        if (
            not isinstance(digest, str)
            or len(digest) != 64
            or any(character not in "0123456789abcdef" for character in digest)
        ):
            raise ValueError("Invalid cached SHA-256")
        return digest
    except (OSError, ValueError) as error:
        raise ExportExecutionError(f"Could not read source-hash cache: {error}") from error


def _save_cached_hash(key: SourceHashKey, digest: str) -> None:
    path, identity = _cache_record(key)
    partial: Path | None = None
    try:
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent, prefix=".hash-", delete=False
        ) as handle:
            partial = Path(handle.name)
            json.dump({"version": 1, "identity": identity, "sha256": digest}, handle)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(partial, path)
    except OSError as error:
        if partial is not None:
            try:
                partial.unlink(missing_ok=True)
            except OSError as cleanup_error:
                raise ExportExecutionError(
                    f"Could not save source-hash cache: {error}; cleanup failed: {cleanup_error}"
                ) from error
        raise ExportExecutionError(f"Could not save source-hash cache: {error}") from error


def file_sha256(
    path: Path,
    *,
    cancel_event: threading.Event | None = None,
    source_hash_cache: SourceHashCache | None = None,
    heartbeat_callback: Callable[[], None] | None = None,
    persistent: bool = False,
) -> str:
    check_export_cancelled(cancel_event)
    path = path.expanduser().resolve()
    key = _source_key(path)
    value = source_hash_cache.get(key) if source_hash_cache is not None else None
    if value is None and persistent:
        value = _load_cached_hash(key)
    if value is None:
        digest = hashlib.sha256()
        buffer = bytearray(1024 * 1024)
        reported = time.monotonic()
        with path.open("rb") as handle:
            while count := handle.readinto(buffer):
                check_export_cancelled(cancel_event)
                digest.update(memoryview(buffer)[:count])
                if heartbeat_callback is not None and time.monotonic() - reported >= 0.25:
                    heartbeat_callback()
                    reported = time.monotonic()
        value = digest.hexdigest()
        check_export_cancelled(cancel_event)
        if _source_key(path) != key:
            raise ExportExecutionError("Source changed while computing its export identity")
        if persistent:
            _save_cached_hash(key, value)
    check_export_cancelled(cancel_event)
    if _source_key(path) != key:
        raise ExportExecutionError("Source changed while computing its export identity")
    if source_hash_cache is not None:
        source_hash_cache[key] = value
    return value
