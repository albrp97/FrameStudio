from __future__ import annotations

import math
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from fractions import Fraction
from typing import Any, Protocol

FPS_POLICY_VERSION = 1
DEFAULT_FPS_CHOICE = "60"
DEFAULT_ENHANCEMENT_ENABLED = True
DEFAULT_ENHANCEMENT_SCOPE = "source"
DEFAULT_FPS_BACKEND = "rve-4.26"
DEFAULT_FPS_FALLBACK_BACKEND = "ffmpeg-minterpolate"
FPS_CHOICES = ("lowest", "highest", "custom", "60")


class FrameRatePolicyError(ValueError):
    """Raised when a target frame-rate policy is invalid or unsupported."""


class FrameRateSource(Protocol):
    @property
    def source_id(self) -> str: ...

    @property
    def metadata(self) -> Mapping[str, Any]: ...


def policy_source_metadata(
    sources: Iterable[FrameRateSource],
) -> tuple[dict[str, Any], ...]:
    return tuple(
        {
            **source.metadata,
            "source_id": source.source_id,
        }
        for source in sources
    )


def canonical_rate(value: Fraction | int | float | str) -> Fraction:
    if isinstance(value, bool):
        raise FrameRatePolicyError("Frame rate must be a positive rational value")
    if isinstance(value, Fraction):
        result = value
    elif isinstance(value, int):
        result = Fraction(value, 1)
    elif isinstance(value, float):
        if not math.isfinite(value):
            raise FrameRatePolicyError("Frame rate must be a finite value")
        result = Fraction(str(value))
    elif isinstance(value, str):
        try:
            result = Fraction(value.strip())
        except (ValueError, ZeroDivisionError) as error:
            raise FrameRatePolicyError(
                f"Invalid frame rate: {value!r}",
            ) from error
    else:
        raise FrameRatePolicyError("Frame rate must be a positive rational value")
    if result <= 0:
        raise FrameRatePolicyError("Frame rate must be greater than zero")
    return result


def rate_label(rate: Fraction | int | float | str) -> str:
    value = float(canonical_rate(rate))
    return f"{value:.3f}".rstrip("0").rstrip(".")


def rate_choice_labels(source_metadata: Sequence[Mapping[str, Any]]) -> tuple[str, ...]:
    """Return user-facing choices with the project rates resolved."""
    if not source_metadata:
        raise FrameRatePolicyError("At least one source frame rate is required")
    rates = tuple(_source_rate(metadata, index) for index, metadata in enumerate(source_metadata))
    return (
        f"Lowest input FPS ({rate_label(min(rates))} FPS)",
        f"Highest input FPS ({rate_label(max(rates))} FPS)",
        "Custom FPS",
        "60 FPS",
    )


def rate_expression(rate: Fraction | int | float | str) -> str:
    """Return an exact rational expression for media-filter arguments."""
    return str(canonical_rate(rate))


def target_frame_count(
    source_rate: Fraction | int | float | str,
    source_frames: int,
    target_rate: Fraction | int | float | str,
) -> int:
    source = canonical_rate(source_rate)
    target = canonical_rate(target_rate)
    if isinstance(source_frames, bool) or not isinstance(source_frames, int):
        raise FrameRatePolicyError("Source frame count must be a positive integer")
    if source_frames <= 0:
        raise FrameRatePolicyError("Source frame count must be a positive integer")
    exact_count = source_frames * target / source
    return max(
        1,
        (exact_count.numerator + exact_count.denominator // 2) // exact_count.denominator,
    )


def _source_rate(metadata: Mapping[str, Any], index: int) -> Fraction:
    for key in ("frame_rate", "r_frame_rate", "avg_frame_rate"):
        value = metadata.get(key)
        if value not in (None, "", "0/0", "N/A"):
            if not isinstance(value, (Fraction, int, float, str)) or isinstance(
                value,
                bool,
            ):
                raise FrameRatePolicyError(
                    f"Source {index + 1} has an invalid frame rate",
                )
            try:
                return canonical_rate(value)
            except FrameRatePolicyError as error:
                raise FrameRatePolicyError(
                    f"Source {index + 1} has an invalid frame rate",
                ) from error
    raise FrameRatePolicyError(f"Source {index + 1} is missing a frame rate")


def _source_id(metadata: Mapping[str, Any], index: int) -> str:
    value = metadata.get("source_id", metadata.get("id", f"source-{index + 1}"))
    if not isinstance(value, str) or not value:
        raise FrameRatePolicyError(f"Source {index + 1} has an invalid source identifier")
    return value


def _is_variable_frame_rate(metadata: Mapping[str, Any]) -> bool:
    if metadata.get("variable_frame_rate") is True:
        return True
    mode = metadata.get("frame_rate_mode")
    return isinstance(mode, str) and mode.casefold() in {"vfr", "variable"}


def normalize_choice(value: str) -> str:
    if not isinstance(value, str):
        raise FrameRatePolicyError("Frame-rate choice must be a string")
    normalized = value.strip().casefold().replace("_", "-")
    aliases = {
        "lowest": "lowest",
        "lowest-input": "lowest",
        "lowest-input-fps": "lowest",
        "min": "lowest",
        "highest": "highest",
        "highest-input": "highest",
        "highest-input-fps": "highest",
        "max": "highest",
        "custom": "custom",
        "60": "60",
        "60fps": "60",
        "60-fps": "60",
    }
    try:
        return aliases[normalized]
    except KeyError as error:
        raise FrameRatePolicyError(
            f"Unsupported frame-rate choice: {value!r}; choose one of {', '.join(FPS_CHOICES)}",
        ) from error


def supports_interpolation(
    source_rate: Fraction | int | float | str,
    target_rate: Fraction | int | float | str,
    *,
    backend: str = DEFAULT_FPS_BACKEND,
) -> bool:
    source = canonical_rate(source_rate)
    target = canonical_rate(target_rate)
    if target <= source:
        return False
    backend_name = backend.casefold().strip()
    if backend_name.startswith("rve"):
        factor = float(target / source)
        return factor > 1.0
    if backend_name in {
        "vs-rife",
        "rife",
        "vapoursynth-rife",
        "ffmpeg",
        "ffmpeg-minterpolate",
    }:
        return True
    return False


@dataclass(frozen=True)
class SourceRateDecision:
    source_id: str
    source_rate: Fraction
    target_rate: Fraction
    action: str
    eligible: bool
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "source_rate": str(self.source_rate),
            "target_rate": str(self.target_rate),
            "action": self.action,
            "eligible": self.eligible,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class FrameRatePolicy:
    choice: str
    target_rate: Fraction
    enhancement_enabled: bool = DEFAULT_ENHANCEMENT_ENABLED
    enhancement_scope: str = DEFAULT_ENHANCEMENT_SCOPE
    backend: str = DEFAULT_FPS_BACKEND
    custom_rate: Fraction | None = None

    def __post_init__(self) -> None:
        normalized_choice = normalize_choice(self.choice)
        object.__setattr__(self, "choice", normalized_choice)
        object.__setattr__(self, "target_rate", canonical_rate(self.target_rate))
        if self.custom_rate is not None:
            object.__setattr__(self, "custom_rate", canonical_rate(self.custom_rate))
        if not isinstance(self.enhancement_enabled, bool):
            raise FrameRatePolicyError("Enhancement enabled must be boolean")
        if self.enhancement_scope != DEFAULT_ENHANCEMENT_SCOPE:
            raise FrameRatePolicyError(
                f"Unsupported enhancement scope: {self.enhancement_scope!r}",
            )
        if not isinstance(self.backend, str) or not self.backend.strip():
            raise FrameRatePolicyError("FPS backend must be a non-empty string")
        if self.choice == "custom" and self.custom_rate is None:
            raise FrameRatePolicyError("Custom frame-rate choice requires custom_rate")
        if self.choice != "custom" and self.custom_rate is not None:
            raise FrameRatePolicyError(
                "custom_rate is only valid with the custom frame-rate choice",
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": FPS_POLICY_VERSION,
            "choice": self.choice,
            "target_rate": str(self.target_rate),
            "enhancement_enabled": self.enhancement_enabled,
            "enhancement_scope": self.enhancement_scope,
            "backend": self.backend,
            "custom_rate": (None if self.custom_rate is None else str(self.custom_rate)),
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> FrameRatePolicy:
        if not isinstance(value, Mapping):
            raise FrameRatePolicyError("Frame-rate policy must be an object")
        version = value.get("version", FPS_POLICY_VERSION)
        if version != FPS_POLICY_VERSION:
            raise FrameRatePolicyError(
                f"Unsupported frame-rate policy version: {version!r}",
            )
        raw_choice = value.get("choice")
        if not isinstance(raw_choice, str):
            raise FrameRatePolicyError("Frame-rate policy choice is required")
        choice = normalize_choice(raw_choice)
        target_value = value.get("target_rate")
        if target_value is None:
            raise FrameRatePolicyError("Frame-rate policy target_rate is required")
        custom_value = value.get("custom_rate")
        return cls(
            choice=choice,
            target_rate=canonical_rate(target_value),
            enhancement_enabled=value.get(
                "enhancement_enabled",
                DEFAULT_ENHANCEMENT_ENABLED,
            ),
            enhancement_scope=value.get(
                "enhancement_scope",
                DEFAULT_ENHANCEMENT_SCOPE,
            ),
            backend=value.get("backend", DEFAULT_FPS_BACKEND),
            custom_rate=(None if custom_value is None else canonical_rate(custom_value)),
        )


@dataclass(frozen=True)
class ResolvedFrameRatePolicy:
    policy: FrameRatePolicy
    decisions: tuple[SourceRateDecision, ...]

    @property
    def target_rate(self) -> Fraction:
        return self.policy.target_rate

    @property
    def has_unsupported_sources(self) -> bool:
        return any(not item.eligible and item.action == "unsupported" for item in self.decisions)

    @property
    def eligible_source_ids(self) -> tuple[str, ...]:
        return tuple(item.source_id for item in self.decisions if item.eligible)

    def to_dict(self) -> dict[str, Any]:
        payload = self.policy.to_dict()
        payload["decisions"] = [item.to_dict() for item in self.decisions]
        return payload


def _resolve_target_rate(
    rates: Sequence[Fraction],
    choice: str,
    custom_rate: Fraction | int | float | str | None,
) -> tuple[Fraction, Fraction | None]:
    if not rates:
        raise FrameRatePolicyError("At least one source frame rate is required")
    if choice != "custom" and custom_rate is not None:
        raise FrameRatePolicyError(
            "custom_rate is only valid with the custom frame-rate choice",
        )
    if choice == "lowest":
        return min(rates), None
    if choice == "highest":
        return max(rates), None
    if choice == "60":
        return Fraction(60, 1), None
    if custom_rate is None:
        raise FrameRatePolicyError("Custom frame-rate choice requires a custom rate")
    custom = canonical_rate(custom_rate)
    return custom, custom


def resolve_frame_rate_policy(
    source_metadata: Sequence[Mapping[str, Any]],
    *,
    choice: str = DEFAULT_FPS_CHOICE,
    custom_rate: Fraction | int | float | str | None = None,
    enhancement_enabled: bool = DEFAULT_ENHANCEMENT_ENABLED,
    enhancement_scope: str = DEFAULT_ENHANCEMENT_SCOPE,
    backend: str = DEFAULT_FPS_BACKEND,
) -> ResolvedFrameRatePolicy:
    if not isinstance(source_metadata, Sequence) or isinstance(source_metadata, (str, bytes)):
        raise FrameRatePolicyError("Source metadata must be a sequence")
    normalized_metadata: list[Mapping[str, Any]] = []
    rates: list[Fraction] = []
    for index, metadata in enumerate(source_metadata):
        if not isinstance(metadata, Mapping):
            raise FrameRatePolicyError(f"Source metadata at index {index} must be an object")
        normalized_metadata.append(metadata)
        rates.append(_source_rate(metadata, index))
    normalized_choice = normalize_choice(choice)
    target_rate, persisted_custom_rate = _resolve_target_rate(
        rates,
        normalized_choice,
        custom_rate,
    )
    policy = FrameRatePolicy(
        choice=normalized_choice,
        target_rate=target_rate,
        enhancement_enabled=enhancement_enabled,
        enhancement_scope=enhancement_scope,
        backend=backend,
        custom_rate=persisted_custom_rate,
    )
    decisions: list[SourceRateDecision] = []
    for index, metadata in enumerate(normalized_metadata):
        source_id = _source_id(metadata, index)
        source_rate = rates[index]
        if source_rate == target_rate:
            decisions.append(
                SourceRateDecision(
                    source_id,
                    source_rate,
                    target_rate,
                    "passthrough",
                    False,
                    "source already matches the target rate",
                )
            )
            continue
        if source_rate > target_rate:
            decisions.append(
                SourceRateDecision(
                    source_id,
                    source_rate,
                    target_rate,
                    "convert-down",
                    False,
                    "source is above the target rate and is not interpolated",
                )
            )
            continue
        if not enhancement_enabled:
            decisions.append(
                SourceRateDecision(
                    source_id,
                    source_rate,
                    target_rate,
                    "convert",
                    False,
                    "enhancement is disabled; use the ordinary conversion route",
                )
            )
            continue
        if _is_variable_frame_rate(metadata):
            decisions.append(
                SourceRateDecision(
                    source_id,
                    source_rate,
                    target_rate,
                    "unsupported",
                    False,
                    "variable-frame-rate input requires explicit normalization before enhancement",
                )
            )
            continue
        if not supports_interpolation(source_rate, target_rate, backend=backend):
            decisions.append(
                SourceRateDecision(
                    source_id,
                    source_rate,
                    target_rate,
                    "unsupported",
                    False,
                    f"backend {backend!r} does not support this interpolation factor",
                )
            )
            continue
        decisions.append(
            SourceRateDecision(
                source_id,
                source_rate,
                target_rate,
                "interpolate",
                True,
                "source is below the target and matches the validated backend policy",
            )
        )
    return ResolvedFrameRatePolicy(policy=policy, decisions=tuple(decisions))


def resolved_from_policy(
    source_metadata: Sequence[Mapping[str, Any]],
    policy: FrameRatePolicy,
) -> ResolvedFrameRatePolicy:
    custom_rate = policy.custom_rate if policy.choice == "custom" else None
    resolved = resolve_frame_rate_policy(
        source_metadata,
        choice=policy.choice,
        custom_rate=custom_rate,
        enhancement_enabled=policy.enhancement_enabled,
        enhancement_scope=policy.enhancement_scope,
        backend=policy.backend,
    )
    if resolved.policy.target_rate != policy.target_rate:
        raise FrameRatePolicyError(
            "Persisted frame-rate policy target does not match source metadata",
        )
    return resolved
