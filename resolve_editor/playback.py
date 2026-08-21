from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Protocol


class PlaybackBackendError(RuntimeError):
    """Raised when a playback backend cannot perform an operation."""


class PlaybackState(str, Enum):
    STOPPED = "stopped"
    PLAYING = "playing"
    PAUSED = "paused"
    SEEKING = "seeking"
    ERROR = "error"


class PlaybackBackend(Protocol):
    def play(self) -> None: ...

    def pause(self) -> None: ...

    def seek(self, position_seconds: float) -> None: ...

    def stop(self) -> None: ...


@dataclass(frozen=True)
class PlaybackSnapshot:
    state: PlaybackState
    position_seconds: float
    duration_seconds: float
    error: str | None


class PlaybackController:
    def __init__(
        self,
        backend: PlaybackBackend,
        duration_seconds: float,
        initial_position: float = 0.0,
    ) -> None:
        if not math.isfinite(duration_seconds) or duration_seconds <= 0:
            raise ValueError("Playback duration must be greater than zero")
        self._backend = backend
        self._duration_seconds = float(duration_seconds)
        self._position_seconds = self._clamp(initial_position)
        self._state = PlaybackState.PAUSED
        self._error: str | None = None

    def _clamp(self, position_seconds: float) -> float:
        if not math.isfinite(float(position_seconds)):
            raise ValueError("Playback position must be finite")
        return max(0.0, min(self._duration_seconds, float(position_seconds)))

    def _backend_call(self, action) -> bool:
        try:
            action()
        except PlaybackBackendError as error:
            self.report_error(str(error))
            return False
        return True

    def play(self) -> bool:
        if not self._backend_call(self._backend.play):
            return False
        self._error = None
        self._state = PlaybackState.PLAYING
        return True

    def pause(self) -> bool:
        if not self._backend_call(self._backend.pause):
            return False
        self._error = None
        self._state = PlaybackState.PAUSED
        return True

    def stop(self) -> bool:
        if not self._backend_call(self._backend.stop):
            return False
        self._error = None
        self._state = PlaybackState.STOPPED
        return True

    def seek(self, position_seconds: float) -> bool:
        try:
            target = self._clamp(position_seconds)
        except (TypeError, ValueError) as error:
            self.report_error(str(error))
            return False
        was_playing = self._state == PlaybackState.PLAYING
        self._state = PlaybackState.SEEKING
        if not self._backend_call(lambda: self._backend.seek(target)):
            return False
        self._position_seconds = target
        self._error = None
        self._state = PlaybackState.PLAYING if was_playing else PlaybackState.PAUSED
        return True

    def update_position(self, position_seconds: float) -> None:
        self._position_seconds = self._clamp(position_seconds)
        if (
            self._state == PlaybackState.PLAYING
            and self._position_seconds >= self._duration_seconds
        ):
            self._state = PlaybackState.PAUSED

    def finish(self) -> None:
        self._position_seconds = self._duration_seconds
        self._state = PlaybackState.PAUSED
        self._error = None

    def report_error(self, message: str) -> None:
        self._state = PlaybackState.ERROR
        self._error = message or "Playback failed"

    def clear_error(self) -> None:
        self._error = None
        self._state = PlaybackState.PAUSED

    def snapshot(self) -> PlaybackSnapshot:
        return PlaybackSnapshot(
            state=self._state,
            position_seconds=self._position_seconds,
            duration_seconds=self._duration_seconds,
            error=self._error,
        )
