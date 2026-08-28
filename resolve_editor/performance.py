from __future__ import annotations

import shutil
import subprocess
from typing import Any


class PerformanceModeError(RuntimeError):
    """Raised when the requested system performance profile cannot be set."""


class PerformanceMode:
    def __init__(self, mode: str) -> None:
        self.mode = mode
        self.tool = shutil.which("powerprofilesctl")
        self.previous: str | None = None
        self.changed = False

    def __enter__(self) -> "PerformanceMode":
        if self.mode == "off" or not self.tool:
            return self
        result = subprocess.run(
            [self.tool, "get"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            if self.mode == "on":
                raise PerformanceModeError("Could not read the current power profile")
            return self
        self.previous = result.stdout.strip()
        if self.previous == "performance":
            return self
        result = subprocess.run(
            [self.tool, "set", "performance"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            if self.mode == "on":
                raise PerformanceModeError(
                    f"Could not enable performance mode: {result.stderr.strip()}"
                )
            return self
        self.changed = True
        return self

    def __exit__(self, _type: Any, _value: Any, _traceback: Any) -> None:
        if not self.changed or not self.previous or not self.tool:
            return
        current = subprocess.run(
            [self.tool, "get"],
            capture_output=True,
            text=True,
            check=False,
        )
        if current.returncode == 0 and current.stdout.strip() == "performance":
            subprocess.run(
                [self.tool, "set", self.previous],
                capture_output=True,
                text=True,
                check=False,
            )


__all__ = ["PerformanceMode", "PerformanceModeError"]
