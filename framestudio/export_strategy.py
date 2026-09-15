from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from fractions import Fraction
from typing import Any

from .export_types import ExportExecutionError, ExportPlan
from .fps_policy import SourceRateDecision, canonical_rate
from .model import Segment
from .upscale_policy import UpscaleDecision


@dataclass(frozen=True)
class ExportRun:
    """A contiguous output run whose source and processing policy are compatible."""

    run_index: int
    source_id: str
    segment_indices: tuple[int, ...]
    segments: tuple[Segment, ...]
    source_rate: Fraction
    target_rate: Fraction
    action: str
    upscale_eligible: bool
    upscale_model: str | None
    upscale_target_width: int | None
    upscale_target_height: int | None
    has_deleted_gap: bool

    @property
    def duration_seconds(self) -> float:
        return sum(segment.duration_seconds for segment in self.segments)

    @property
    def boundary_safe_for_ffmpeg_ranges(self) -> bool:
        """Each segment can remain an independent filter branch before concat."""
        return len(self.segments) > 1 or self.has_deleted_gap

    @property
    def can_batch_source_preparation(self) -> bool:
        """Restoration remains per segment until a safe grouped route exists."""
        return not self.upscale_eligible


def _value(decision: SourceRateDecision | Mapping[str, Any], key: str) -> Any:
    if isinstance(decision, SourceRateDecision):
        return getattr(decision, key)
    return decision.get(key)


def _upscale_values(
    decision: UpscaleDecision | Mapping[str, Any] | None,
) -> tuple[bool, str | None, int | None, int | None]:
    if decision is None:
        return False, None, None, None
    if isinstance(decision, UpscaleDecision):
        return (
            decision.eligible,
            decision.model,
            decision.target_width,
            decision.target_height,
        )
    return (
        bool(decision.get("eligible")),
        decision.get("model"),
        decision.get("target_width"),
        decision.get("target_height"),
    )


def _upscale_by_source(
    decisions: Mapping[str, UpscaleDecision | Mapping[str, Any]]
    | Sequence[UpscaleDecision | Mapping[str, Any]],
) -> dict[str, UpscaleDecision | Mapping[str, Any]]:
    if isinstance(decisions, Mapping):
        return dict(decisions)
    result: dict[str, UpscaleDecision | Mapping[str, Any]] = {}
    for decision in decisions:
        source_id = (
            decision.source_id
            if isinstance(decision, UpscaleDecision)
            else decision.get("source_id")
        )
        if not isinstance(source_id, str) or not source_id:
            raise ExportExecutionError("Upscale decisions must include source identities")
        result[source_id] = decision
    return result


def segment_source_id(
    plan: ExportPlan,
    segment: Segment,
    decision_ids: tuple[str, ...],
) -> str:
    if segment.source_id:
        return segment.source_id
    if len(decision_ids) == 1:
        return decision_ids[0]
    if len(plan.source_ids) == 1:
        return plan.source_ids[0]
    raise ExportExecutionError("Enhanced export segment has no source identity")


def build_export_runs(
    plan: ExportPlan,
    decisions: Mapping[str, SourceRateDecision | Mapping[str, Any]],
    *,
    upscale_decisions: Mapping[str, UpscaleDecision | Mapping[str, Any]]
    | Sequence[UpscaleDecision | Mapping[str, Any]]
    | None = None,
) -> tuple[ExportRun, ...]:
    """Group active timeline segments without crossing incompatible policies."""
    if not decisions:
        raise ExportExecutionError("Enhanced export has no rate decisions")
    upscale_by_source = _upscale_by_source(upscale_decisions or {})
    decision_ids = tuple(decisions)
    runs: list[ExportRun] = []

    current_source: str | None = None
    current_key: tuple[Any, ...] | None = None
    current_indices: list[int] = []
    current_segments: list[Segment] = []
    current_source_rate: Fraction | None = None
    current_target_rate: Fraction | None = None
    current_action: str | None = None
    current_upscale: tuple[bool, str | None, int | None, int | None] = (
        False,
        None,
        None,
        None,
    )
    has_deleted_gap = False
    previous_index: int | None = None

    def flush() -> None:
        nonlocal current_source, current_key, current_indices, current_segments
        nonlocal current_source_rate, current_target_rate, current_action
        nonlocal current_upscale, has_deleted_gap, previous_index
        if current_source is None or current_source_rate is None or current_target_rate is None:
            return
        runs.append(
            ExportRun(
                run_index=len(runs),
                source_id=current_source,
                segment_indices=tuple(current_indices),
                segments=tuple(current_segments),
                source_rate=current_source_rate,
                target_rate=current_target_rate,
                action=current_action or "unsupported",
                upscale_eligible=current_upscale[0],
                upscale_model=current_upscale[1],
                upscale_target_width=current_upscale[2],
                upscale_target_height=current_upscale[3],
                has_deleted_gap=has_deleted_gap,
            )
        )
        current_source = None
        current_key = None
        current_indices = []
        current_segments = []
        current_source_rate = None
        current_target_rate = None
        current_action = None
        current_upscale = (False, None, None, None)
        has_deleted_gap = False
        previous_index = None

    for segment_index, segment in enumerate(plan.segments):
        if segment.deleted:
            continue
        source_id = segment_source_id(plan, segment, decision_ids)
        decision = decisions.get(source_id)
        if decision is None:
            raise ExportExecutionError(
                f"Enhanced export has no rate decision for source {source_id}"
            )
        try:
            source_rate = canonical_rate(_value(decision, "source_rate"))
            target_rate = canonical_rate(_value(decision, "target_rate"))
        except (TypeError, ValueError) as error:
            raise ExportExecutionError(
                f"Enhanced export rate decision is invalid for source {source_id}"
            ) from error
        action = _value(decision, "action")
        if not isinstance(action, str) or not action:
            raise ExportExecutionError(
                f"Enhanced export rate decision is invalid for source {source_id}"
            )
        upscale = _upscale_values(upscale_by_source.get(source_id))
        key = (source_id, source_rate, target_rate, action, upscale)
        if current_key != key:
            flush()
            current_source = source_id
            current_key = key
            current_source_rate = source_rate
            current_target_rate = target_rate
            current_action = action
            current_upscale = upscale
        elif previous_index is not None and segment_index != previous_index + 1:
            has_deleted_gap = True
        current_indices.append(segment_index)
        current_segments.append(segment)
        previous_index = segment_index

    flush()
    return tuple(runs)


__all__ = ["ExportRun", "build_export_runs", "segment_source_id"]
