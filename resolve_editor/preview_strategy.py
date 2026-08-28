from __future__ import annotations

from collections import OrderedDict
from collections.abc import Hashable
from typing import Generic, TypeVar

FrameT = TypeVar("FrameT")


class PreviewFrameCache(Generic[FrameT]):
    """Small LRU cache keyed by the nearest decoded frame."""

    def __init__(self, max_entries: int, frame_rate: float) -> None:
        if max_entries < 0:
            raise ValueError("Preview cache size cannot be negative")
        if frame_rate <= 0:
            raise ValueError("Preview frame rate must be positive")
        self.max_entries = int(max_entries)
        self.frame_rate = float(frame_rate)
        self._frames: OrderedDict[tuple[Hashable | None, int], FrameT] = OrderedDict()
        self.hits = 0
        self.misses = 0
        self.evictions = 0

    def _frame_index(self, position_seconds: float) -> int:
        return max(0, int(float(position_seconds) * self.frame_rate + 0.5))

    def get(
        self,
        position_seconds: float,
        *,
        namespace: Hashable | None = None,
    ) -> FrameT | None:
        if self.max_entries == 0:
            self.misses += 1
            return None
        key = (namespace, self._frame_index(position_seconds))
        frame = self._frames.get(key)
        if frame is None:
            self.misses += 1
            return None
        self._frames.move_to_end(key)
        self.hits += 1
        return frame

    def put(
        self,
        frame: FrameT,
        *,
        namespace: Hashable | None = None,
    ) -> None:
        if self.max_entries == 0:
            return
        position = getattr(frame, "position_seconds", None)
        if position is None:
            raise ValueError("Preview frames must expose position_seconds")
        key = (namespace, self._frame_index(position))
        self._frames[key] = frame
        self._frames.move_to_end(key)
        while len(self._frames) > self.max_entries:
            self._frames.popitem(last=False)
            self.evictions += 1

    def clear(self) -> None:
        self._frames.clear()
