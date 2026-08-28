from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from fractions import Fraction
from typing import Any, Protocol

UPSCALE_POLICY_VERSION = 1
DEFAULT_UPSCALE_ENABLED = True
DEFAULT_UPSCALE_MODEL = "SuperUltraCompact"
DEFAULT_UPSCALE_BACKEND = "rve-restoration"
DEFAULT_UPSCALE_TARGET_SHORT_SIDE = 1080
DEFAULT_LANDSCAPE_MAX_SHORT_SIDE = 1000
DEFAULT_PORTRAIT_MAX_SHORT_SIDE = 720


class UpscalePolicyError(ValueError):
    """Raised when an upscale policy or source decision is invalid."""


class UpscaleSource(Protocol):
    @property
    def source_id(self) -> str: ...

    @property
    def metadata(self) -> Mapping[str, Any]: ...


def policy_source_metadata(
    sources: Sequence[UpscaleSource],
) -> tuple[dict[str, Any], ...]:
    return tuple(
        {
            **source.metadata,
            "source_id": source.source_id,
        }
        for source in sources
    )


def _positive_int(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise UpscalePolicyError(f"{label} must be a positive integer")
    return int(value)


@dataclass(frozen=True, init=False)
class UpscalePolicy:
    enhancement_enabled: bool
    model: str
    backend: str
    target_short_side: int
    landscape_max_short_side: int
    portrait_max_short_side: int

    def __init__(
        self,
        enhancement_enabled: bool = DEFAULT_UPSCALE_ENABLED,
        model: str = DEFAULT_UPSCALE_MODEL,
        backend: str = DEFAULT_UPSCALE_BACKEND,
        target_short_side: int = DEFAULT_UPSCALE_TARGET_SHORT_SIDE,
        landscape_max_short_side: int = DEFAULT_LANDSCAPE_MAX_SHORT_SIDE,
        portrait_max_short_side: int = DEFAULT_PORTRAIT_MAX_SHORT_SIDE,
        *,
        enabled: bool | None = None,
    ) -> None:
        if enabled is not None:
            if enhancement_enabled != DEFAULT_UPSCALE_ENABLED and enhancement_enabled != enabled:
                raise UpscalePolicyError(
                    "enabled and enhancement_enabled cannot disagree",
                )
            enhancement_enabled = enabled
        if not isinstance(enhancement_enabled, bool):
            raise UpscalePolicyError("Upscale enhancement enabled must be boolean")
        if not isinstance(model, str) or not model.strip():
            raise UpscalePolicyError("Upscale model must be a non-empty string")
        if not isinstance(backend, str) or not backend.strip():
            raise UpscalePolicyError("Upscale backend must be a non-empty string")
        target = _positive_int(target_short_side, "Upscale target short side")
        landscape = _positive_int(
            landscape_max_short_side,
            "Landscape maximum source short side",
        )
        portrait = _positive_int(
            portrait_max_short_side,
            "Portrait maximum source short side",
        )
        if target <= landscape or target <= portrait:
            raise UpscalePolicyError(
                "Upscale target short side must exceed both eligibility thresholds",
            )
        object.__setattr__(self, "enhancement_enabled", enhancement_enabled)
        object.__setattr__(self, "model", model.strip())
        object.__setattr__(self, "backend", backend.strip())
        object.__setattr__(self, "target_short_side", target)
        object.__setattr__(self, "landscape_max_short_side", landscape)
        object.__setattr__(self, "portrait_max_short_side", portrait)

    @property
    def enabled(self) -> bool:
        return self.enhancement_enabled

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": UPSCALE_POLICY_VERSION,
            "enhancement_enabled": self.enhancement_enabled,
            "model": self.model,
            "backend": self.backend,
            "target_short_side": self.target_short_side,
            "landscape_max_short_side": self.landscape_max_short_side,
            "portrait_max_short_side": self.portrait_max_short_side,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> UpscalePolicy:
        if not isinstance(value, Mapping):
            raise UpscalePolicyError("Upscale policy must be an object")
        version = value.get("version", UPSCALE_POLICY_VERSION)
        if version != UPSCALE_POLICY_VERSION:
            raise UpscalePolicyError(
                f"Unsupported upscale policy version: {version!r}",
            )
        enabled = value.get(
            "enhancement_enabled",
            value.get("enabled", DEFAULT_UPSCALE_ENABLED),
        )
        return cls(
            enhancement_enabled=enabled,
            model=value.get("model", DEFAULT_UPSCALE_MODEL),
            backend=value.get("backend", DEFAULT_UPSCALE_BACKEND),
            target_short_side=value.get(
                "target_short_side",
                DEFAULT_UPSCALE_TARGET_SHORT_SIDE,
            ),
            landscape_max_short_side=value.get(
                "landscape_max_short_side",
                DEFAULT_LANDSCAPE_MAX_SHORT_SIDE,
            ),
            portrait_max_short_side=value.get(
                "portrait_max_short_side",
                DEFAULT_PORTRAIT_MAX_SHORT_SIDE,
            ),
        )


@dataclass(frozen=True)
class UpscaleDecision:
    source_id: str
    source_width: int
    source_height: int
    orientation: str
    source_short_side: int
    target_width: int
    target_height: int
    action: str
    eligible: bool
    reason: str
    model: str | None = None

    @property
    def selected_model(self) -> str | None:
        return self.model

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "source_width": self.source_width,
            "source_height": self.source_height,
            "orientation": self.orientation,
            "source_short_side": self.source_short_side,
            "target_width": self.target_width,
            "target_height": self.target_height,
            "action": self.action,
            "eligible": self.eligible,
            "reason": self.reason,
            "model": self.model,
        }


@dataclass(frozen=True)
class ResolvedUpscalePolicy:
    policy: UpscalePolicy
    decisions: tuple[UpscaleDecision, ...]

    @property
    def eligible_source_ids(self) -> tuple[str, ...]:
        return tuple(item.source_id for item in self.decisions if item.eligible)

    @property
    def has_eligible_sources(self) -> bool:
        return bool(self.eligible_source_ids)

    def to_dict(self) -> dict[str, Any]:
        payload = self.policy.to_dict()
        payload["decisions"] = [item.to_dict() for item in self.decisions]
        return payload


def _source_id(metadata: Mapping[str, Any], index: int) -> str:
    value = metadata.get("source_id", metadata.get("id", f"source-{index + 1}"))
    if not isinstance(value, str) or not value.strip():
        raise UpscalePolicyError(f"Source {index + 1} has an invalid source identifier")
    return value


def _dimensions(metadata: Mapping[str, Any], index: int) -> tuple[int, int]:
    width = metadata.get("width")
    height = metadata.get("height")
    return (
        _positive_int(width, f"Source {index + 1} width"),
        _positive_int(height, f"Source {index + 1} height"),
    )


def _orientation(width: int, height: int) -> str:
    if width == height:
        return "square"
    return "landscape" if width > height else "portrait"


def _even_dimension(value: Fraction) -> int:
    rounded = max(1, (value.numerator * 2 + value.denominator) // (2 * value.denominator))
    return rounded if rounded % 2 == 0 else rounded + 1


def _target_dimensions(
    width: int,
    height: int,
    target_short_side: int,
) -> tuple[int, int]:
    if width > height:
        return _even_dimension(Fraction(width * target_short_side, height)), target_short_side
    return target_short_side, _even_dimension(Fraction(height * target_short_side, width))


def _eligible(policy: UpscalePolicy, width: int, height: int) -> tuple[bool, str]:
    orientation = _orientation(width, height)
    short_side = min(width, height)
    if not policy.enhancement_enabled:
        return False, "upscale enhancement is disabled"
    if orientation == "square":
        return False, "square sources are not part of the orientation-aware upscale policy"
    threshold = (
        policy.landscape_max_short_side
        if orientation == "landscape"
        else policy.portrait_max_short_side
    )
    if short_side > threshold:
        return (
            False,
            f"{orientation} source short side {short_side} exceeds the "
            f"{threshold}-pixel eligibility threshold",
        )
    return True, f"{orientation} source short side {short_side} is eligible for enhancement"


def resolve_upscale_policy(
    source_metadata: Sequence[Mapping[str, Any]],
    *,
    policy: UpscalePolicy | Mapping[str, Any] | None = None,
    enabled: bool | None = None,
    model: str | None = None,
    backend: str | None = None,
) -> ResolvedUpscalePolicy:
    if not isinstance(source_metadata, Sequence) or isinstance(source_metadata, (str, bytes)):
        raise UpscalePolicyError("Source metadata must be a sequence")
    if policy is None:
        selected = UpscalePolicy(
            enhancement_enabled=(DEFAULT_UPSCALE_ENABLED if enabled is None else enabled),
            model=DEFAULT_UPSCALE_MODEL if model is None else model,
            backend=DEFAULT_UPSCALE_BACKEND if backend is None else backend,
        )
    else:
        selected = policy if isinstance(policy, UpscalePolicy) else UpscalePolicy.from_dict(policy)
        if enabled is not None or model is not None or backend is not None:
            selected = UpscalePolicy(
                enhancement_enabled=selected.enhancement_enabled if enabled is None else enabled,
                model=selected.model if model is None else model,
                backend=selected.backend if backend is None else backend,
                target_short_side=selected.target_short_side,
                landscape_max_short_side=selected.landscape_max_short_side,
                portrait_max_short_side=selected.portrait_max_short_side,
            )
    decisions: list[UpscaleDecision] = []
    for index, metadata in enumerate(source_metadata):
        if not isinstance(metadata, Mapping):
            raise UpscalePolicyError(f"Source metadata at index {index} must be an object")
        width, height = _dimensions(metadata, index)
        source_id = _source_id(metadata, index)
        orientation = _orientation(width, height)
        short_side = min(width, height)
        eligible, reason = _eligible(selected, width, height)
        if eligible:
            target_width, target_height = _target_dimensions(
                width,
                height,
                selected.target_short_side,
            )
            action = "enhance"
            model_name: str | None = selected.model
        else:
            target_width, target_height = width, height
            action = "passthrough"
            model_name = None
        decisions.append(
            UpscaleDecision(
                source_id=source_id,
                source_width=width,
                source_height=height,
                orientation=orientation,
                source_short_side=short_side,
                target_width=target_width,
                target_height=target_height,
                action=action,
                eligible=eligible,
                reason=reason,
                model=model_name,
            )
        )
    return ResolvedUpscalePolicy(policy=selected, decisions=tuple(decisions))


def resolved_from_policy(
    source_metadata: Sequence[Mapping[str, Any]],
    policy: UpscalePolicy,
) -> ResolvedUpscalePolicy:
    return resolve_upscale_policy(source_metadata, policy=policy)


__all__ = [
    "DEFAULT_LANDSCAPE_MAX_SHORT_SIDE",
    "DEFAULT_PORTRAIT_MAX_SHORT_SIDE",
    "DEFAULT_UPSCALE_BACKEND",
    "DEFAULT_UPSCALE_ENABLED",
    "DEFAULT_UPSCALE_MODEL",
    "DEFAULT_UPSCALE_TARGET_SHORT_SIDE",
    "UPSCALE_POLICY_VERSION",
    "ResolvedUpscalePolicy",
    "UpscaleDecision",
    "UpscalePolicy",
    "UpscalePolicyError",
    "policy_source_metadata",
    "resolve_upscale_policy",
    "resolved_from_policy",
]
