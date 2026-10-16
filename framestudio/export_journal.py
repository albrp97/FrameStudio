from __future__ import annotations

import fcntl
import json
import os
import stat
import threading
import time
import traceback
from collections.abc import Callable, Sequence
from contextvars import ContextVar, Token
from dataclasses import asdict
from pathlib import Path
from types import TracebackType
from typing import Any, TextIO

from .export_types import ExportExecutionError, ExportProgress

_active: ContextVar[ExportJournal | None] = ContextVar("export_journal", default=None)


def journal_path(destination: Path) -> Path:
    return destination.with_name(f".{destination.name}.framestudio-export.log")


def record_export_process(event: str, pid: int, command: str, **details: Any) -> None:
    journal = _active.get()
    if journal is not None:
        journal.record(event, pid=pid, executable=Path(command).name, **details)


def record_export_error(error: BaseException) -> None:
    journal = _active.get()
    if journal is not None:
        journal.record("operation_failed", error="".join(traceback.format_exception(error)))


class ExportJournal:
    """Append-only diagnostics outside the checkpoint tree; fsynced before continuing."""

    def __init__(
        self,
        destination: Path,
        *,
        heartbeat_seconds: float = 5.0,
        protected_paths: Sequence[Path] = (),
    ) -> None:
        self.path = journal_path(destination.expanduser())
        if self.path.resolve() in {
            path.expanduser().resolve() for path in (*protected_paths, destination)
        }:
            raise ExportExecutionError("Export journal aliases a protected source or output")
        self.heartbeat_seconds = heartbeat_seconds
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._stream: TextIO | None = None
        self._thread: threading.Thread | None = None
        self._write_error: OSError | ExportExecutionError | None = None
        self.heartbeat_callback: Callable[[], None] | None = None
        self._progress: dict[str, Any] | None = None
        self._last_progress_at = 0.0
        self._last_stage: str | None = None
        self._token: Token[ExportJournal | None] | None = None

    def __enter__(self) -> ExportJournal:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(self.path, os.O_RDWR | os.O_CREAT | os.O_APPEND | os.O_NOFOLLOW, 0o600)
        self._stream = os.fdopen(fd, "a+", encoding="utf-8")
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            metadata = os.fstat(fd)
            if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
                raise ExportExecutionError("Export journal must be a private regular file")
            os.fchmod(fd, 0o600)
            self._stream.seek(0, os.SEEK_END)
            size = self._stream.tell()
            self._stream.seek(max(0, size - 65536))
            content = self._stream.read()
            previous = content.splitlines()
            last = {}
            for line in reversed(previous):
                try:
                    last = json.loads(line)
                    break
                except json.JSONDecodeError:
                    continue
            if content and not content.endswith("\n"):
                self._stream.write("\n")
            self.record(
                "started",
                previous_run_interrupted=bool(previous)
                and last.get("event") not in {"failed", "cancelled", "complete"},
                previous_pid=last.get("owner_pid"),
            )
            self._sync_parent()
        except (OSError, ValueError, ExportExecutionError):
            self._stream.close()
            self._stream = None
            raise
        self._token = _active.set(self)
        self._thread = threading.Thread(
            target=self._heartbeat, name="framestudio-export-journal", daemon=True
        )
        self._thread.start()
        return self

    def record(self, event: str, **details: Any) -> None:
        if self._write_error is not None:
            raise ExportExecutionError(
                f"Export diagnostic journal could not be persisted: {self._write_error}"
            ) from self._write_error
        with self._lock:
            if self._stream is None:
                raise ExportExecutionError("Export diagnostic journal is not open")
            payload = {
                "event": event,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "owner_pid": os.getpid(),
                "memory": self._memory(os.getpid()),
                "progress": self._progress,
                **details,
            }
            self._stream.write(json.dumps(payload, ensure_ascii=True) + "\n")
            self._stream.flush()
            os.fsync(self._stream.fileno())

    def _sync_parent(self) -> None:
        fd = os.open(self.path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)

    def _children(self) -> list[dict[str, Any]]:
        pending = [os.getpid()]
        seen = set(pending)
        processes = []
        while pending:
            parent = pending.pop()
            try:
                tasks = tuple(Path(f"/proc/{parent}/task").iterdir())
            except FileNotFoundError:
                continue
            except OSError as error:
                processes.append({"pid": parent, "inspection_error": str(error)})
                continue
            for task in tasks:
                try:
                    children = (task / "children").read_text().split()
                except FileNotFoundError:
                    continue
                except OSError as error:
                    processes.append({"pid": parent, "inspection_error": str(error)})
                    continue
                for child in children:
                    pid = int(child)
                    if pid in seen:
                        continue
                    seen.add(pid)
                    pending.append(pid)
                    try:
                        processes.append(
                            {
                                "pid": pid,
                                "parent_pid": parent,
                                "executable": Path(f"/proc/{pid}/comm").read_text().strip(),
                                "memory": self._memory(pid),
                            }
                        )
                    except FileNotFoundError:
                        continue
                    except OSError as error:
                        processes.append({"pid": pid, "inspection_error": str(error)})
        return processes

    @staticmethod
    def _memory(pid: int) -> dict[str, Any]:
        try:
            lines = Path(f"/proc/{pid}/status").read_text().splitlines()
        except OSError as error:
            return {"inspection_error": str(error)}
        fields = {"VmRSS": "rss_kib", "VmHWM": "peak_rss_kib", "VmSwap": "swap_kib"}
        return {
            fields[key]: int(value.split()[0])
            for line in lines
            if ":" in line
            for key, value in (line.split(":", 1),)
            if key in fields
        }

    def progress(self, progress: ExportProgress) -> None:
        self._progress = asdict(progress)
        now = time.monotonic()
        if progress.stage != self._last_stage or now - self._last_progress_at >= 1.0:
            self.record("progress")
            self._last_progress_at = now
            self._last_stage = progress.stage
        elif self._write_error is not None:
            raise ExportExecutionError(
                "Export diagnostic journal heartbeat failed"
            ) from self._write_error

    def _heartbeat(self) -> None:
        while not self._stop.wait(self.heartbeat_seconds):
            try:
                self.record("heartbeat", active_processes=self._children())
                if self.heartbeat_callback is not None:
                    self.heartbeat_callback()
            except (OSError, ExportExecutionError) as error:
                self._write_error = error
                return

    def __exit__(
        self,
        error_type: type[BaseException] | None,
        error: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join()
        try:
            self.record(
                "complete"
                if error is None
                else "cancelled"
                if "cancel" in str(error).lower()
                else "failed",
                error=None if error is None else "".join(traceback.format_exception(error)),
            )
            if error is None:
                self.path.unlink()
                self._sync_parent()
        except (OSError, ExportExecutionError) as journal_error:
            if error is not None:
                raise ExportExecutionError(
                    f"{error}; could not finalize export journal: {journal_error}"
                ) from error
            else:
                raise
        finally:
            if self._token is not None:
                _active.reset(self._token)
            if self._stream is not None:
                self._stream.close()
