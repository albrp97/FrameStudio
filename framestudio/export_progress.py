from __future__ import annotations

import math
import threading
import time
from collections.abc import Sequence
from dataclasses import replace

from .export_types import ExportProgress, ExportProgressCallback

# Discrete milestones are never replayed by heartbeat; replaying one would
# duplicate a completed event (for example a checkpoint) in the progress stream.
_MILESTONE_STAGE_PREFIXES = (
    "Checkpointed ",
    "Starting output",
    "Verified output",
    "Reusing verified",
    "complete",
)


def progress_scope(
    callback: ExportProgressCallback | None, start: float, end: float
) -> ExportProgressCallback | None:
    if callback is None:
        return None

    def report(progress: ExportProgress) -> None:
        callback(
            replace(
                progress,
                percent=start + (end - start) * max(0.0, min(100.0, progress.percent)) / 100,
                current_percent=(
                    progress.percent
                    if progress.current_percent is None
                    else progress.current_percent
                ),
            )
        )

    return report


class ExportProgressTracker:
    """Duration-weighted planned work, not an estimate of remaining wall time."""

    def __init__(self, callback: ExportProgressCallback | None) -> None:
        self.callback = callback
        self.started = time.monotonic()
        self.weights: tuple[float, ...] = ()
        self.completed: list[float] = []
        self.index: int | None = None
        self.overall = 0.0
        self.reused_percent = 0.0
        self._lock = threading.RLock()
        self._last: ExportProgress | None = None

    def configure(self, weights: Sequence[float]) -> None:
        if not weights or any(not math.isfinite(w) or w <= 0 for w in weights):
            raise ValueError("Export progress weights must be finite and positive")
        with self._lock:
            self.weights = tuple(weights)
            self.completed = [0.0] * len(weights)

    def begin_output(self, index: int) -> None:
        with self._lock:
            self.index = index
            self._emit("Starting output", 0.0)

    def finish_output(self, index: int, *, reused: bool = False) -> None:
        with self._lock:
            self.completed[index] = 1.0
            self.index = index
            self._emit("Reusing verified output" if reused else "Verified output", 100.0)

    def verifying(self) -> None:
        with self._lock:
            if self.index is not None:
                self.completed[self.index] = max(self.completed[self.index], 0.95)
            self._emit("Verifying output", 0.0)

    def finish(self) -> None:
        with self._lock:
            self.overall = 100.0
            self._emit("complete", 100.0)

    def _emit(self, stage: str, percent: float) -> None:
        self(ExportProgress(stage, percent, 0, 0, None, 0.0, None))

    def __call__(self, progress: ExportProgress) -> None:
        with self._lock:
            self._report(progress)

    def heartbeat(self) -> None:
        with self._lock:
            if self._last is not None and self.overall < 100:
                self._report(self._last)

    def _report(self, progress: ExportProgress) -> None:
        if not progress.stage.startswith(_MILESTONE_STAGE_PREFIXES):
            self._last = progress
        if self.index is None:
            overall = min(5.0, progress.percent * 0.05)
        else:
            self.completed[self.index] = max(
                self.completed[self.index], min(1.0, max(0.0, progress.percent / 100)) * 0.95
            )
            overall = 5.0 + 95.0 * sum(
                weight * done for weight, done in zip(self.weights, self.completed, strict=True)
            ) / sum(self.weights)
        previous = self.overall
        self.overall = max(self.overall, min(99.9, overall))
        if progress.stage.startswith("Reusing verified"):
            self.reused_percent += self.overall - previous
        elapsed = max(0.0, time.monotonic() - self.started)
        measured = self.overall - self.reused_percent
        eta = (
            0.0
            if self.overall >= 100.0
            else elapsed * (100.0 - self.overall) / measured
            if measured > 0 and elapsed > 0
            else None
        )
        if self.callback is not None:
            self.callback(
                replace(
                    progress,
                    current_percent=(
                        progress.percent
                        if progress.current_percent is None
                        else progress.current_percent
                    ),
                    overall_percent=self.overall,
                    output_index=0 if self.index is None else self.index + 1,
                    output_count=len(self.weights),
                    overall_elapsed_seconds=elapsed,
                    overall_eta_seconds=eta,
                )
            )
