from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .export_estimates import (
    calibration_for_policy,
    estimate_project_export,
)
from .export_naming import (
    ExportDestinationError,
    collision_safe_destination,
    smart_export_name,
    validate_export_destination,
)
from .fps_policy import (
    FrameRatePolicyError,
    ResolvedFrameRatePolicy,
    policy_source_metadata,
    rate_label,
    resolve_frame_rate_policy,
)
from .interpolation import (
    BackendValidation,
    resolve_frame_rate_policy_with_fallback,
    validate_interpolation_backend,
)
from .upscale_policy import (
    DEFAULT_UPSCALE_BACKEND,
    DEFAULT_UPSCALE_MODEL,
    ResolvedUpscalePolicy,
    UpscalePolicy,
    resolve_upscale_policy,
)


@dataclass(frozen=True)
class ExportPanelState:
    policy: ResolvedFrameRatePolicy | None
    destination: Path | None
    filename: str
    estimate: dict[str, Any] | None
    backend_validation: tuple[BackendValidation, ...]
    valid: bool
    reason: str | None
    upscale_policy: ResolvedUpscalePolicy | None = None
    notice: str | None = None

    @property
    def summary(self) -> dict[str, Any]:
        if self.policy is None:
            return {
                "valid": False,
                "reason": self.reason,
                "notice": self.notice,
                "filename": self.filename,
            }
        upscale = self.upscale_policy
        return {
            "valid": self.valid,
            "reason": self.reason,
            "notice": self.notice,
            "filename": self.filename,
            "destination": None if self.destination is None else str(self.destination),
            "input_count": len(self.policy.decisions),
            "target_rate": str(self.policy.target_rate),
            "enhancement_enabled": self.policy.policy.enhancement_enabled,
            "eligible_source_ids": list(self.policy.eligible_source_ids),
            "fps": {
                "enabled": self.policy.policy.enhancement_enabled,
                "eligible_source_ids": list(self.policy.eligible_source_ids),
                "eligible_source_count": len(self.policy.eligible_source_ids),
                "source_count": len(self.policy.decisions),
                "decisions": [item.to_dict() for item in self.policy.decisions],
            },
            "estimate": self.estimate,
            "backend": [item.to_dict() for item in self.backend_validation],
            "upscale": (
                None
                if upscale is None
                else {
                    "enabled": upscale.policy.enhancement_enabled,
                    "model": upscale.policy.model,
                    "backend": upscale.policy.backend,
                    "eligible_source_ids": list(upscale.eligible_source_ids),
                    "eligible_source_count": len(upscale.eligible_source_ids),
                    "source_count": len(upscale.decisions),
                    "decisions": [item.to_dict() for item in upscale.decisions],
                }
            ),
        }

    @property
    def display_rows(self) -> tuple[tuple[str, str], ...]:
        if self.policy is None:
            return ()
        upscale = self.upscale_policy
        estimate = self.estimate or {}
        rows = [
            ("Inputs", str(estimate.get("input_count", len(self.policy.decisions)))),
            (
                "Final duration",
                _format_duration(estimate.get("edited_duration_seconds")),
            ),
            (
                "Output FPS",
                f"{rate_label(self.policy.target_rate)} FPS",
            ),
            (
                "FPS enhancement",
                "On" if self.policy.policy.enhancement_enabled else "Off",
            ),
            (
                "Videos to FPS enhance",
                str(len(self.policy.eligible_source_ids)),
            ),
            (
                "Estimated processing time",
                _format_time_estimate(estimate),
            ),
            (
                "Estimated output size",
                _format_size_estimate(estimate),
            ),
        ]
        if self.policy.policy.enhancement_enabled:
            rows.append(("Backend", self.policy.policy.backend))
        rows.extend(_upscale_display_rows(upscale))
        return tuple(rows)


def _metadata(project: Any) -> tuple[dict[str, Any], ...]:
    return policy_source_metadata(project.sources or (project.source,))


def _upscale_display_rows(
    upscale: ResolvedUpscalePolicy | None,
) -> tuple[tuple[str, str], ...]:
    if upscale is None:
        return ()
    rows = [
        (
            "Upscale enhancement",
            "On" if upscale.policy.enhancement_enabled else "Off",
        ),
    ]
    if upscale.policy.enhancement_enabled:
        rows.append(("Upscale model", upscale.policy.model))
    rows.append(("Videos to upscale", str(len(upscale.eligible_source_ids))))
    return tuple(rows)


def _fps_display_rows(
    policy: ResolvedFrameRatePolicy,
) -> tuple[tuple[str, str], ...]:
    return (
        (
            "FPS enhancement",
            "On" if policy.policy.enhancement_enabled else "Off",
        ),
        (
            "Videos to FPS enhance",
            str(len(policy.eligible_source_ids)),
        ),
    )


def _resolve_upscale_panel_policy(
    metadata: tuple[dict[str, Any], ...],
    *,
    enabled: bool,
    model: str = DEFAULT_UPSCALE_MODEL,
    backend: str = DEFAULT_UPSCALE_BACKEND,
) -> ResolvedUpscalePolicy:
    return resolve_upscale_policy(
        metadata,
        policy=UpscalePolicy(
            enhancement_enabled=enabled,
            model=model,
            backend=backend,
        ),
    )


def resolve_upscale_panel_policy(
    project: Any,
    *,
    enabled: bool | None = None,
) -> ResolvedUpscalePolicy:
    current = project.get_upscale_policy()
    selected_enabled = current.enhancement_enabled if enabled is None else enabled
    return _resolve_upscale_panel_policy(
        _metadata(project),
        enabled=selected_enabled,
        model=current.model,
        backend=current.backend,
    )


def upscale_panel_rows(
    project: Any,
    *,
    enabled: bool | None = None,
) -> tuple[tuple[str, str], ...]:
    return _upscale_display_rows(
        resolve_upscale_panel_policy(project, enabled=enabled),
    )


def fps_panel_rows(
    project: Any,
    *,
    choice: str | None = None,
    custom_rate: str | None = None,
    enhancement_enabled: bool | None = None,
    backend: str | None = None,
) -> tuple[tuple[str, str], ...]:
    current = project.get_frame_rate_policy()
    selected_choice = current.choice if choice is None else choice
    selected_custom = current.custom_rate if custom_rate is None else custom_rate
    if selected_choice != "custom":
        selected_custom = None
    selected_enabled = (
        current.enhancement_enabled if enhancement_enabled is None else enhancement_enabled
    )
    selected_backend = current.backend if backend is None else backend
    try:
        policy = resolve_frame_rate_policy(
            _metadata(project),
            choice=selected_choice,
            custom_rate=selected_custom,
            enhancement_enabled=selected_enabled,
            backend=selected_backend,
        )
    except (FrameRatePolicyError, ValueError):
        return (
            ("FPS enhancement", "On" if selected_enabled else "Off"),
            ("Videos to FPS enhance", "unavailable"),
        )
    return _fps_display_rows(policy)


def _calibration(policy: ResolvedFrameRatePolicy):
    return calibration_for_policy(policy)


def _format_duration(value: Any) -> str:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return "unavailable"
    seconds = float(value)
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes, remainder = divmod(int(round(seconds)), 60)
    return f"{minutes}m {remainder:02d}s"


def _format_size(value: Any) -> str:
    if not isinstance(value, (int, float)) or isinstance(value, bool) or value < 0:
        return "unavailable"
    amount = float(value)
    for unit in ("B", "KiB", "MiB", "GiB"):
        if amount < 1024 or unit == "GiB":
            return f"{amount:.1f} {unit}"
        amount /= 1024
    return "unavailable"


def _format_time_estimate(estimate: dict[str, Any]) -> str:
    total = estimate.get("total_seconds")
    if total is not None:
        return f"~{_format_duration(total)}"
    lower = estimate.get("lower_seconds")
    upper = estimate.get("upper_seconds")
    if lower is None or upper is None:
        return "unavailable"
    return f"{_format_duration(lower)}-{_format_duration(upper)} range"


def _format_size_estimate(estimate: dict[str, Any]) -> str:
    value = estimate.get("estimated_output_size_bytes")
    lower = estimate.get("estimated_output_size_lower_bytes")
    upper = estimate.get("estimated_output_size_upper_bytes")
    if value is None:
        return "unavailable"
    if lower is None or upper is None:
        return f"~{_format_size(value)}"
    return f"~{_format_size(value)} ({_format_size(lower)}-{_format_size(upper)})"


def _resolve_panel_policy(
    metadata: tuple[dict[str, Any], ...],
    *,
    choice: str,
    custom_rate: Any,
    enhancement_enabled: bool,
    backend: str,
    ffmpeg_path: str,
) -> tuple[ResolvedFrameRatePolicy, tuple[BackendValidation, ...], str | None]:
    return resolve_frame_rate_policy_with_fallback(
        metadata,
        choice=choice,
        custom_rate=custom_rate,
        enhancement_enabled=enhancement_enabled,
        backend=backend,
        ffmpeg_path=ffmpeg_path,
        backend_validator=validate_interpolation_backend,
    )


def prepare_export_panel(
    project: Any,
    folder: str | Path,
    *,
    choice: str | None = None,
    custom_rate: str | None = None,
    enhancement_enabled: bool | None = None,
    upscale_enabled: bool | None = None,
    backend: str | None = None,
    ffmpeg_path: str = "ffmpeg",
    project_path: str | Path | None = None,
    filename: str | None = None,
) -> ExportPanelState:
    try:
        current = project.get_frame_rate_policy()
        selected_choice = current.choice if choice is None else choice
        selected_custom = current.custom_rate if custom_rate is None else custom_rate
        if selected_choice != "custom":
            selected_custom = None
        selected_enhancement = (
            current.enhancement_enabled if enhancement_enabled is None else enhancement_enabled
        )
        selected_backend = current.backend if backend is None else backend
        policy, backend_validation, notice = _resolve_panel_policy(
            _metadata(project),
            choice=selected_choice,
            custom_rate=selected_custom,
            enhancement_enabled=selected_enhancement,
            backend=selected_backend,
            ffmpeg_path=ffmpeg_path,
        )
        upscale_policy = resolve_upscale_panel_policy(
            project,
            enabled=upscale_enabled,
        )
    except (FrameRatePolicyError, ValueError) as error:
        return ExportPanelState(
            policy=None,
            destination=None,
            filename=filename or "",
            estimate=None,
            backend_validation=(),
            valid=False,
            reason=str(error),
        )

    chosen_filename = filename or smart_export_name(
        [source.path for source in project.sources or (project.source,)],
        policy=policy.policy,
        project_path=project_path,
    )
    estimate = estimate_project_export(
        project,
        policy,
        calibration=_calibration(policy),
    ).to_dict()
    try:
        destination = collision_safe_destination(folder, chosen_filename)
        if filename is not None:
            if (
                not filename.strip()
                or Path(filename).is_absolute()
                or Path(filename).name != filename
            ):
                raise ExportDestinationError("Export filename must be a simple file name")
            destination = Path(folder).expanduser() / filename
        else:
            chosen_filename = destination.name
        validate_export_destination(
            destination,
            project_path=project_path,
            source_paths=[source.path for source in project.sources or (project.source,)],
        )
    except ExportDestinationError as error:
        return ExportPanelState(
            policy=policy,
            destination=None,
            filename=chosen_filename,
            estimate=estimate,
            backend_validation=tuple(backend_validation),
            valid=False,
            reason=str(error),
            upscale_policy=upscale_policy,
            notice=notice,
        )
    invalid_backend = next(
        (item for item in backend_validation if not item.available),
        None,
    )
    if policy.has_unsupported_sources:
        reason = "; ".join(item.reason for item in policy.decisions if item.action == "unsupported")
        return ExportPanelState(
            policy=policy,
            destination=destination,
            filename=chosen_filename,
            estimate=estimate,
            backend_validation=tuple(backend_validation),
            valid=False,
            reason=reason,
            upscale_policy=upscale_policy,
            notice=notice,
        )
    if invalid_backend is not None:
        return ExportPanelState(
            policy=policy,
            destination=destination,
            filename=chosen_filename,
            estimate=estimate,
            backend_validation=tuple(backend_validation),
            valid=False,
            reason=invalid_backend.reason,
            upscale_policy=upscale_policy,
            notice=notice,
        )
    return ExportPanelState(
        policy=policy,
        destination=destination,
        filename=chosen_filename,
        estimate=estimate,
        backend_validation=tuple(backend_validation),
        valid=True,
        reason=None,
        upscale_policy=upscale_policy,
        notice=notice,
    )


__all__ = [
    "ExportPanelState",
    "fps_panel_rows",
    "prepare_export_panel",
    "resolve_upscale_panel_policy",
    "upscale_panel_rows",
]
