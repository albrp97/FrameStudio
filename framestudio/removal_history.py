from __future__ import annotations

import uuid
from collections import OrderedDict
from copy import deepcopy
from dataclasses import dataclass, field, replace
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .model_types import Segment, TimelineTrack

MAX_REMOVAL_RECEIPTS = 20


class _RuntimeContext:
    _runtime_identity: str
    _runtime_epoch: int

    def _initialize_runtime_context(self) -> None:
        self._runtime_identity = uuid.uuid4().hex
        self._runtime_epoch = 0


@dataclass(frozen=True)
class TimelineStateSnapshot:
    """Runtime-only state used to prove an exact removal-history boundary."""

    tracks: tuple[TimelineTrack, ...] | None
    segments: tuple[Segment, ...] | None
    active_track_id: str | None
    source_duration_seconds: float
    mixed_source: bool
    source_durations: dict[str, float] | None
    source_durations_ticks: dict[str, int] | None
    timebase: str
    frame_rate: str | None
    ripple: bool
    timing_mode: str
    timeline_model_version: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "tracks", deepcopy(self.tracks))
        object.__setattr__(self, "segments", deepcopy(self.segments))
        object.__setattr__(
            self,
            "source_durations",
            None if self.source_durations is None else deepcopy(self.source_durations),
        )
        object.__setattr__(
            self,
            "source_durations_ticks",
            None if self.source_durations_ticks is None else deepcopy(self.source_durations_ticks),
        )


@dataclass(frozen=True)
class RemovalReceipt:
    """Opaque, in-memory receipt for one atomic track-local removal."""

    receipt_id: str
    timeline_runtime_identity: str
    timeline_runtime_epoch: int
    project_runtime_identity: str | None
    project_runtime_epoch: int | None
    before_revision: int
    after_revision: int
    removed_segment_ids: tuple[str, ...]
    selection_ids: tuple[str, ...]
    focused_segment_id: str | None
    before_state: TimelineStateSnapshot
    after_state: TimelineStateSnapshot
    receipt_token: str = field(
        default_factory=lambda: uuid.uuid4().hex,
        repr=False,
        compare=False,
    )
    known_after_revisions: tuple[int, ...] = ()


@dataclass(frozen=True)
class RemovalUndoResult:
    receipt_id: str
    restored_selection_ids: tuple[str, ...]
    focused_segment_id: str | None


class RemovalHistory:
    """Bounded runtime-only receipt storage with deterministic oldest eviction."""

    def __init__(self) -> None:
        self._receipts: OrderedDict[str, RemovalReceipt] = OrderedDict()

    def append(self, receipt: RemovalReceipt) -> None:
        self._receipts[receipt.receipt_id] = deepcopy(receipt)
        while len(self._receipts) > MAX_REMOVAL_RECEIPTS:
            self._receipts.popitem(last=False)

    def find(self, receipt: RemovalReceipt) -> RemovalReceipt | None:
        stored = self._receipts.get(receipt.receipt_id)
        if stored is None or stored.receipt_token != receipt.receipt_token:
            return None
        return stored

    def replace(self, receipt: RemovalReceipt) -> None:
        if receipt.receipt_id not in self._receipts:
            return
        self._receipts[receipt.receipt_id] = deepcopy(receipt)

    def remove(self, receipt_id: str) -> None:
        self._receipts.pop(receipt_id, None)

    def values(self) -> tuple[RemovalReceipt, ...]:
        return tuple(self._receipts.values())

    def clear(self) -> None:
        self._receipts.clear()

    @staticmethod
    def with_known_revision(receipt: RemovalReceipt, revision: int) -> RemovalReceipt:
        if revision in receipt.known_after_revisions:
            return receipt
        return replace(
            receipt,
            known_after_revisions=(*receipt.known_after_revisions, revision),
        )
