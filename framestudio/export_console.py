from __future__ import annotations

import sys
import time
from dataclasses import dataclass, field
from typing import Callable, TextIO

from .export_types import ExportProgress

CONSOLE_EXPORT_STEP_COUNT = 5
_MIN_PROGRESS_INTERVAL_SECONDS = 0.5
_MIN_PROGRESS_DELTA_PERCENT = 1.0


def console_progress_enabled(stream: TextIO, *, force: bool = False) -> bool:
    if force:
        return True
    isatty = getattr(stream, "isatty", None)
    return bool(callable(isatty) and isatty())


def _step_for_stage(stage: str) -> tuple[int, str]:
    normalized = stage.casefold()
    if "publishing interpolated" in normalized:
        return 2, "Rendering and enhancing"
    if normalized == "complete" or "publish" in normalized:
        return 5, "Publishing output"
    if "verif" in normalized:
        return 4, "Verifying output"
    if "concat" in normalized or "assembling" in normalized or "composing" in normalized:
        return 3, "Concatenating and composing"
    if "interpolat" in normalized or "restor" in normalized or "encoding" in normalized:
        return 2, "Rendering and enhancing"
    return 1, "Preparing sources"


def _format_seconds(seconds: float | None) -> str:
    if seconds is None:
        return "--:--"
    total = max(0, int(round(seconds)))
    minutes, remaining = divmod(total, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours:02d}:{minutes:02d}:{remaining:02d}"
    return f"{minutes:02d}:{remaining:02d}"


@dataclass
class ConsoleProgressReporter:
    stream: TextIO = field(default_factory=lambda: sys.stderr)
    force: bool = False
    clock: Callable[[], float] = time.monotonic
    enabled: bool = field(default=False, init=False)
    _last_step: int | None = field(default=None, init=False)
    _last_stage: str | None = field(default=None, init=False)
    _last_percent: float | None = field(default=None, init=False)
    _last_report_time: float | None = field(default=None, init=False)

    def __post_init__(self) -> None:
        self.enabled = console_progress_enabled(self.stream, force=self.force)

    def __call__(self, progress: ExportProgress) -> None:
        if not self.enabled:
            return
        step, label = _step_for_stage(progress.stage)
        now = self.clock()
        stage_changed = step != self._last_step or progress.stage != self._last_stage
        percent_changed = (
            self._last_percent is None
            or abs(progress.percent - self._last_percent) >= _MIN_PROGRESS_DELTA_PERCENT
        )
        interval_elapsed = (
            self._last_report_time is None
            or now - self._last_report_time >= _MIN_PROGRESS_INTERVAL_SECONDS
        )
        if not stage_changed and not (percent_changed and interval_elapsed):
            return

        detail = f"Step {step}/{CONSOLE_EXPORT_STEP_COUNT} - {label}: {progress.percent:.1f}%"
        if progress.stage.casefold() not in {label.casefold(), "complete"}:
            detail += f" [{progress.stage}]"
        if progress.total_frames:
            detail += f" | frame {progress.frame}/{progress.total_frames}"
        if progress.fps is not None:
            detail += f" | {progress.fps:.1f} fps"
        detail += f" | elapsed {_format_seconds(progress.elapsed_seconds)}"
        if progress.eta_seconds is not None:
            detail += f" | ETA {_format_seconds(progress.eta_seconds)}"
        print(detail, file=self.stream, flush=True)
        if progress.stage.casefold() == "complete":
            print("Export complete.", file=self.stream, flush=True)
        self._last_step = step
        self._last_stage = progress.stage
        self._last_percent = progress.percent
        self._last_report_time = now


__all__ = [
    "CONSOLE_EXPORT_STEP_COUNT",
    "ConsoleProgressReporter",
    "console_progress_enabled",
]
