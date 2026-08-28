from __future__ import annotations

import argparse
import math
import shutil
import subprocess
import tempfile
import threading
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any

from .export_process import emit_export_progress
from .export_types import ExportExecutionError, ExportProgressCallback
from .fps_policy import (
    DEFAULT_FPS_BACKEND,
    DEFAULT_FPS_FALLBACK_BACKEND,
    ResolvedFrameRatePolicy,
    canonical_rate,
    rate_expression,
    resolve_frame_rate_policy,
    supports_interpolation,
)


@dataclass(frozen=True)
class BackendValidation:
    backend: str
    available: bool
    artifact_status: str
    reason: str
    model: str = "4.26"
    precision: str = "float16"
    runtime: str = "TensorRT"
    input_format: str = "RGBH"
    target_rate: Fraction = Fraction(60, 1)

    def to_dict(self) -> dict[str, Any]:
        return {
            "backend": self.backend,
            "available": self.available,
            "artifact_status": self.artifact_status,
            "reason": self.reason,
            "model": self.model,
            "precision": self.precision,
            "runtime": self.runtime,
            "input_format": self.input_format,
            "target_rate": str(self.target_rate),
        }


def _rve_defaults() -> dict[str, Path]:
    from resolve_fps import (
        DEFAULT_FPS_PYTHON,
        DEFAULT_FPS_SITE,
        DEFAULT_RVE_MODEL,
        DEFAULT_RVE_ROOT,
        DEFAULT_RVE_SHIMS,
    )

    return {
        "fps_python": DEFAULT_FPS_PYTHON,
        "site_packages": DEFAULT_FPS_SITE,
        "rve_model": DEFAULT_RVE_MODEL,
        "rve_root": DEFAULT_RVE_ROOT,
        "rve_shims": DEFAULT_RVE_SHIMS,
    }


def validate_interpolation_backend(
    backend: str = DEFAULT_FPS_BACKEND,
    *,
    source_rate: Fraction | int | float | str,
    target_rate: Fraction | int | float | str,
    ffmpeg_path: str = "ffmpeg",
    rve_root: Path | None = None,
    rve_model: Path | None = None,
    fps_python: Path | None = None,
    site_packages: Path | None = None,
    graph: Path | None = None,
    trt_cache: Path | None = None,
    bestsource: Path | None = None,
) -> BackendValidation:
    source = canonical_rate(source_rate)
    target = canonical_rate(target_rate)
    if target <= source:
        return BackendValidation(
            backend=backend,
            available=False,
            artifact_status="blocked",
            reason="Interpolation requires a target rate above the source rate",
            target_rate=target,
        )
    if not supports_interpolation(source, target, backend=backend):
        return BackendValidation(
            backend=backend,
            available=False,
            artifact_status="blocked",
            reason=f"Backend {backend!r} does not support this interpolation factor",
            target_rate=target,
        )
    normalized_backend = backend.casefold().strip()
    if normalized_backend in {"ffmpeg", "ffmpeg-minterpolate"}:
        if shutil.which(ffmpeg_path) is None:
            return BackendValidation(
                backend=backend,
                available=False,
                artifact_status="blocked",
                reason=f"FFmpeg executable was not found: {ffmpeg_path}",
                runtime="FFmpeg",
                input_format="native decoded frames",
                target_rate=target,
            )
        return BackendValidation(
            backend=backend,
            available=True,
            artifact_status="validated-fallback",
            reason="Explicit FFmpeg minterpolate fallback; not the validated RVE profile",
            runtime="FFmpeg",
            input_format="native decoded frames",
            target_rate=target,
        )
    defaults = _rve_defaults()
    fps_python = (fps_python or defaults["fps_python"]).expanduser()
    site_packages = (site_packages or defaults["site_packages"]).expanduser()
    rve_model = (rve_model or defaults["rve_model"]).expanduser()
    rve_root = (rve_root or defaults["rve_root"]).expanduser()
    if normalized_backend in {"vs-rife", "rife", "vapoursynth-rife"}:
        required = (
            ("FPS Python", fps_python),
            ("site-packages", site_packages),
            ("VapourSynth graph", graph or Path("/missing/fps.vpy")),
            ("TensorRT cache", trt_cache or Path("/missing/trt-cache")),
            ("BestSource plugin", bestsource or Path("/missing/libbestsource.so")),
        )
        missing = next(((label, path) for label, path in required if not path.exists()), None)
        if missing is not None:
            return BackendValidation(
                backend=backend,
                available=False,
                artifact_status="blocked",
                reason=f"{missing[0]} was not found: {missing[1]}",
                target_rate=target,
            )
        return BackendValidation(
            backend=backend,
            available=True,
            artifact_status="validated",
            reason="VapourSynth RIFE prerequisites are present",
            runtime="VapourSynth",
            input_format="RGBH",
            target_rate=target,
        )
    if normalized_backend.startswith("rve"):
        if not fps_python.is_file():
            reason = f"RVE Python environment was not found: {fps_python}"
        elif not site_packages.is_dir():
            reason = f"FPS site-packages directory was not found: {site_packages}"
        elif not rve_model.is_file():
            reason = f"RIFE model was not found: {rve_model}"
        else:
            try:
                from resolve_fps import rve_unavailable_reason

                runtime_reason = rve_unavailable_reason(
                    argparse.Namespace(
                        python=fps_python,
                        site_packages=site_packages,
                        rve_model=rve_model,
                        rve_root=rve_root,
                        rve_shims=defaults["rve_shims"],
                    ),
                    announce=False,
                )
                if runtime_reason is not None:
                    reason = runtime_reason
                else:
                    return BackendValidation(
                        backend=backend,
                        available=True,
                        artifact_status="validated",
                        reason=(
                            "RVE checkout and CUDA/TensorRT runtime preflight "
                            "passed the interpolation prerequisite gate"
                        ),
                        target_rate=target,
                    )
            except (OSError, RuntimeError) as error:
                reason = str(error)
        return BackendValidation(
            backend=backend,
            available=False,
            artifact_status="blocked",
            reason=reason,
            target_rate=target,
        )
    return BackendValidation(
        backend=backend,
        available=False,
        artifact_status="blocked",
        reason=f"Unknown interpolation backend: {backend}",
        target_rate=target,
    )


def resolve_frame_rate_policy_with_fallback(
    source_metadata: Sequence[Mapping[str, Any]],
    *,
    choice: str,
    custom_rate: Any,
    enhancement_enabled: bool,
    backend: str,
    ffmpeg_path: str = "ffmpeg",
    backend_validator: Callable[..., BackendValidation] = validate_interpolation_backend,
) -> tuple[ResolvedFrameRatePolicy, tuple[BackendValidation, ...], str | None]:
    policy = resolve_frame_rate_policy(
        source_metadata,
        choice=choice,
        custom_rate=custom_rate,
        enhancement_enabled=enhancement_enabled,
        backend=backend,
    )
    if not enhancement_enabled:
        return policy, (), None
    validations = tuple(
        backend_validator(
            policy.policy.backend,
            source_rate=decision.source_rate,
            target_rate=decision.target_rate,
            ffmpeg_path=ffmpeg_path,
        )
        for decision in policy.decisions
        if decision.action in {"interpolate", "unsupported"}
    )
    if (
        not validations
        or not backend.casefold().strip().startswith("rve")
        or all(item.available for item in validations)
        or any(
            item.action == "unsupported" and "variable-frame-rate" in item.reason.casefold()
            for item in policy.decisions
        )
    ):
        return policy, validations, None
    fallback = resolve_frame_rate_policy(
        source_metadata,
        choice=choice,
        custom_rate=custom_rate,
        enhancement_enabled=enhancement_enabled,
        backend=DEFAULT_FPS_FALLBACK_BACKEND,
    )
    if fallback.has_unsupported_sources:
        return policy, validations, None
    fallback_validations = tuple(
        backend_validator(
            fallback.policy.backend,
            source_rate=decision.source_rate,
            target_rate=decision.target_rate,
            ffmpeg_path=ffmpeg_path,
        )
        for decision in fallback.decisions
        if decision.action in {"interpolate", "unsupported"}
    )
    if not fallback_validations or not all(item.available for item in fallback_validations):
        return policy, validations, None
    return (
        fallback,
        fallback_validations,
        f"{backend} is unavailable; using validated {DEFAULT_FPS_FALLBACK_BACKEND} fallback.",
    )


def require_validated_backend(
    backend: str,
    *,
    source_rate: Fraction | int | float | str,
    target_rate: Fraction | int | float | str,
    ffmpeg_path: str = "ffmpeg",
    **kwargs: Any,
) -> BackendValidation:
    validation = validate_interpolation_backend(
        backend,
        source_rate=source_rate,
        target_rate=target_rate,
        ffmpeg_path=ffmpeg_path,
        **kwargs,
    )
    if not validation.available or validation.artifact_status in {"rejected", "blocked"}:
        raise ExportExecutionError(
            f"Interpolation backend {backend!r} is unavailable or unvalidated: {validation.reason}"
        )
    return validation


def _rounded_frame_position(seconds: Fraction | float, rate: Fraction) -> int:
    exact = (seconds if isinstance(seconds, Fraction) else Fraction(str(seconds))) * rate
    return (exact.numerator + exact.denominator // 2) // exact.denominator


def _target_range_frame_counts(
    ranges: Sequence[tuple[float, float]],
    *,
    source_rate: Fraction,
    source_frames: int,
    target_rate: Fraction,
    target_frames: int,
) -> tuple[int, ...]:
    if source_frames <= 0 or target_frames <= 0:
        raise ExportExecutionError("Interpolation frame counts must be positive")
    counts: list[int] = []
    previous_end: float | None = None
    for index, (start, duration) in enumerate(ranges):
        end = start + duration
        if not math.isfinite(start) or not math.isfinite(duration) or start < 0 or duration <= 0:
            raise ExportExecutionError("Interpolation ranges must be finite and positive")
        if previous_end is not None and not math.isclose(
            start,
            previous_end,
            rel_tol=0.0,
            abs_tol=1e-6,
        ):
            raise ExportExecutionError("Interpolation ranges must be contiguous")
        source_start = 0 if index == 0 else _rounded_frame_position(start, source_rate)
        source_end = (
            source_frames if index == len(ranges) - 1 else _rounded_frame_position(end, source_rate)
        )
        target_start = (
            0
            if index == 0
            else _rounded_frame_position(
                Fraction(source_start, 1) / source_rate,
                target_rate,
            )
        )
        target_end = (
            target_frames
            if index == len(ranges) - 1
            else _rounded_frame_position(
                Fraction(source_end, 1) / source_rate,
                target_rate,
            )
        )
        source_start = max(0, min(source_frames, source_start))
        source_end = max(0, min(source_frames, source_end))
        target_start = max(0, min(target_frames, target_start))
        target_end = max(0, min(target_frames, target_end))
        if source_end <= source_start or target_end <= target_start:
            raise ExportExecutionError("Interpolation ranges must contain video frames")
        counts.append(target_end - target_start)
        previous_end = end
    if not ranges or sum(counts) != target_frames:
        raise ExportExecutionError("Interpolation ranges do not cover the target frame count")
    return tuple(counts)


def build_ffmpeg_interpolation_command(
    source: Path,
    destination: Path,
    target_rate: Fraction | int | float | str,
    target_frames: int,
    *,
    ffmpeg_path: str = "ffmpeg",
    ranges: Sequence[tuple[float, float]] | None = None,
    range_frame_counts: Sequence[int] | None = None,
) -> list[str]:
    target = canonical_rate(target_rate)
    if isinstance(target_frames, bool) or not isinstance(target_frames, int) or target_frames <= 0:
        raise ExportExecutionError("Interpolation target frame count must be positive")
    target_expression = rate_expression(target)
    interpolation = (
        f"minterpolate=fps={target_expression}:"
        "mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1,"
        f"setpts=N/({target_expression})/TB,tpad=stop_mode=clone:stop_duration=1"
    )
    if ranges is None:
        filter_value = f"{interpolation},trim=end_frame={target_frames}"
        return [
            ffmpeg_path,
            "-hide_banner",
            "-loglevel",
            "error",
            "-nostdin",
            "-i",
            str(source),
            "-vf",
            filter_value,
            "-frames:v",
            str(target_frames),
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "copy",
            "-movflags",
            "+faststart",
            "-f",
            "mp4",
            str(destination),
        ]
    if not ranges:
        raise ExportExecutionError("Interpolation ranges must not be empty")
    counts = tuple(range_frame_counts or ())
    if len(counts) != len(ranges):
        raise ExportExecutionError("Interpolation range frame counts are invalid")
    if sum(counts) != target_frames or any(
        isinstance(count, bool) or not isinstance(count, int) or count <= 0 for count in counts
    ):
        raise ExportExecutionError("Interpolation range frame counts must match the target")
    branches: list[str] = []
    labels: list[str] = []
    for index, ((start, duration), frame_count) in enumerate(zip(ranges, counts, strict=True)):
        if not math.isfinite(start) or not math.isfinite(duration) or start < 0 or duration <= 0:
            raise ExportExecutionError("Interpolation ranges must be finite and positive")
        label = f"[range_{index}]"
        labels.append(label)
        branches.append(
            f"[0:v:0]trim=start={start:.6f}:duration={duration:.6f},"
            f"setpts=PTS-STARTPTS,{interpolation},trim=end_frame={frame_count},"
            f"setpts=N/({target_expression})/TB{label}"
        )
    branches.append(f"{''.join(labels)}concat=n={len(labels)}:v=1:a=0[outv]")
    filter_complex = ";".join(branches)
    return [
        ffmpeg_path,
        "-hide_banner",
        "-loglevel",
        "error",
        "-nostdin",
        "-i",
        str(source),
        "-filter_complex",
        filter_complex,
        "-map",
        "[outv]",
        "-map",
        "0:a:0?",
        "-frames:v",
        str(target_frames),
        "-c:v",
        "libx264",
        "-preset",
        "medium",
        "-crf",
        "18",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "copy",
        "-movflags",
        "+faststart",
        "-f",
        "mp4",
        str(destination),
    ]


def _sample_frame_count(
    source_rate: Fraction,
    source_frames: int,
    target_rate: Fraction,
) -> tuple[int, int]:
    source_sample_frames = max(
        1,
        min(source_frames, round(float(source_rate) * 0.5)),
    )
    exact_target_frames = Fraction(source_sample_frames, 1) * target_rate / source_rate
    target_sample_frames = max(
        1,
        (exact_target_frames.numerator + exact_target_frames.denominator // 2)
        // exact_target_frames.denominator,
    )
    return source_sample_frames, target_sample_frames


def _create_artifact_sample_source(
    source: Path,
    destination: Path,
    *,
    ffmpeg_path: str,
    source_frames: int,
    source_rate: Fraction,
) -> int:
    source_sample_frames, _ = _sample_frame_count(
        source_rate,
        source_frames,
        source_rate,
    )
    command = [
        ffmpeg_path,
        "-hide_banner",
        "-loglevel",
        "error",
        "-nostdin",
        "-y",
        "-i",
        str(source),
        "-map",
        "0:v:0",
        "-an",
        "-frames:v",
        str(source_sample_frames),
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        str(destination),
    ]
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as error:
        raise ExportExecutionError(
            f"Could not start FFmpeg for interpolation artifact preflight: {ffmpeg_path}"
        ) from error
    if result.returncode != 0:
        detail = result.stderr.strip() or "FFmpeg could not prepare the artifact sample"
        raise ExportExecutionError(detail)
    return source_sample_frames


def _run_interpolation_backend(
    source: Path,
    destination: Path,
    *,
    source_rate: Fraction,
    source_frames: int,
    target_rate: Fraction,
    target_frames: int,
    backend: str,
    ffmpeg_path: str,
    cancel_event: threading.Event | None,
    ranges: Sequence[tuple[float, float]] | None,
    progress_callback: ExportProgressCallback | None = None,
    progress_stage: str = "interpolation",
    progress_started: float | None = None,
    backend_kwargs: dict[str, Any],
) -> None:
    normalized_backend = backend.casefold().strip()
    if normalized_backend in {"ffmpeg", "ffmpeg-minterpolate"}:
        from .export_process import run_ffmpeg

        range_frame_counts: tuple[int, ...] | None = None
        if ranges is not None:
            range_frame_counts = _target_range_frame_counts(
                ranges,
                source_rate=source_rate,
                source_frames=source_frames,
                target_rate=target_rate,
                target_frames=target_frames,
            )
        run_ffmpeg(
            build_ffmpeg_interpolation_command(
                source,
                destination,
                target_rate,
                target_frames,
                ffmpeg_path=ffmpeg_path,
                ranges=ranges,
                range_frame_counts=range_frame_counts,
            ),
            command_duration_seconds=target_frames / float(target_rate),
            progress_total_duration_seconds=target_frames / float(target_rate),
            command_total_frames=target_frames,
            progress_total_frames=target_frames,
            progress_callback=progress_callback,
            stage=progress_stage,
            started=progress_started,
            cancel_event=cancel_event,
        )
        return
    if ranges is not None and len(ranges) > 1:
        raise ExportExecutionError(
            f"Backend {backend!r} cannot provide boundary-safe interpolation for multiple ranges"
        )
    from resolve_fps import (
        DEFAULT_BESTSOURCE,
        DEFAULT_FPS_PYTHON,
        DEFAULT_FPS_SITE,
        DEFAULT_GRAPH,
        DEFAULT_RVE_MODEL,
        DEFAULT_RVE_ROOT,
        DEFAULT_RVE_SHIMS,
        DEFAULT_TRT_CACHE,
        run_interpolation,
        run_interpolation_rve,
    )

    arguments = argparse.Namespace(
        force=True,
        python=backend_kwargs.get("fps_python", DEFAULT_FPS_PYTHON),
        site_packages=backend_kwargs.get("site_packages", DEFAULT_FPS_SITE),
        graph=backend_kwargs.get("graph", DEFAULT_GRAPH),
        trt_cache=backend_kwargs.get("trt_cache", DEFAULT_TRT_CACHE),
        bestsource=backend_kwargs.get("bestsource", DEFAULT_BESTSOURCE),
        rve_root=backend_kwargs.get("rve_root", DEFAULT_RVE_ROOT),
        rve_model=backend_kwargs.get("rve_model", DEFAULT_RVE_MODEL),
        rve_shims=backend_kwargs.get("rve_shims", DEFAULT_RVE_SHIMS),
        model=backend_kwargs.get("model", "4.26"),
        encoder=backend_kwargs.get(
            "encoder",
            "h264_nvenc" if normalized_backend.startswith("rve") else "libx264",
        ),
    )
    rve_progress_callback = None
    if progress_callback is not None and normalized_backend.startswith("rve"):
        started = progress_started if progress_started is not None else time.monotonic()
        total_duration_seconds = target_frames / float(target_rate)

        def report_rve_progress(
            frame: int,
            _reported_total_frames: int,
            fps: float | None,
        ) -> None:
            emit_export_progress(
                progress_callback,
                stage=progress_stage,
                current_seconds=frame / float(target_rate),
                total_duration_seconds=total_duration_seconds,
                frame=frame,
                total_frames=target_frames,
                fps=fps,
                started=started,
            )

        rve_progress_callback = report_rve_progress
    try:
        if normalized_backend.startswith("rve"):
            run_interpolation_rve(
                source,
                destination,
                source_rate,
                source_frames,
                target_rate,
                target_frames,
                arguments,
                cancel_event=cancel_event,
                progress_callback=rve_progress_callback,
            )
        else:
            run_interpolation(
                source,
                destination,
                target_rate,
                target_frames,
                arguments,
                cancel_event=cancel_event,
            )
    except (OSError, RuntimeError) as error:
        raise ExportExecutionError(
            f"Interpolation backend {backend!r} failed: {error}",
        ) from error


def _run_artifact_preflight(
    source: Path,
    destination: Path,
    *,
    source_rate: Fraction,
    source_frames: int,
    target_rate: Fraction,
    backend: str,
    ffmpeg_path: str,
    cancel_event: threading.Event | None,
    backend_kwargs: dict[str, Any],
) -> None:
    if cancel_event is not None and cancel_event.is_set():
        raise ExportExecutionError("Export cancelled")
    from .interpolation_artifacts import run_artifact_gate

    with tempfile.TemporaryDirectory(prefix="resolve-interpolation-artifact-") as directory:
        temporary = Path(directory)
        sample_source = temporary / "source.mp4"
        sample_output = temporary / "output.mp4"
        sample_source_frames = _create_artifact_sample_source(
            source,
            sample_source,
            ffmpeg_path=ffmpeg_path,
            source_frames=source_frames,
            source_rate=source_rate,
        )
        _, sample_target_frames = _sample_frame_count(
            source_rate,
            sample_source_frames,
            target_rate,
        )
        _run_interpolation_backend(
            sample_source,
            sample_output,
            source_rate=source_rate,
            source_frames=sample_source_frames,
            target_rate=target_rate,
            target_frames=sample_target_frames,
            backend=backend,
            ffmpeg_path=ffmpeg_path,
            cancel_event=cancel_event,
            ranges=None,
            backend_kwargs=backend_kwargs,
        )
        run_artifact_gate(
            sample_output,
            sample_target_frames,
            ffmpeg_path=ffmpeg_path,
            label=f"{backend} artifact preflight",
        )
    if cancel_event is not None and cancel_event.is_set():
        raise ExportExecutionError("Export cancelled")


def run_source_interpolation(
    source: Path,
    destination: Path,
    *,
    source_rate: Fraction,
    source_frames: int,
    target_rate: Fraction,
    target_frames: int,
    backend: str = DEFAULT_FPS_BACKEND,
    ffmpeg_path: str = "ffmpeg",
    cancel_event: threading.Event | None = None,
    ranges: Sequence[tuple[float, float]] | None = None,
    progress_callback: ExportProgressCallback | None = None,
    progress_stage: str = "interpolation",
    progress_started: float | None = None,
    **backend_kwargs: Any,
) -> None:
    artifact_gate = backend_kwargs.pop("artifact_gate", True)
    if not isinstance(artifact_gate, bool):
        raise ExportExecutionError("Interpolation artifact_gate must be boolean")
    require_validated_backend(
        backend,
        source_rate=source_rate,
        target_rate=target_rate,
        ffmpeg_path=ffmpeg_path,
        **backend_kwargs,
    )
    if artifact_gate:
        _run_artifact_preflight(
            source,
            destination,
            source_rate=source_rate,
            source_frames=source_frames,
            target_rate=target_rate,
            backend=backend,
            ffmpeg_path=ffmpeg_path,
            cancel_event=cancel_event,
            backend_kwargs=backend_kwargs,
        )
    _run_interpolation_backend(
        source,
        destination,
        source_rate=source_rate,
        source_frames=source_frames,
        target_rate=target_rate,
        target_frames=target_frames,
        backend=backend,
        ffmpeg_path=ffmpeg_path,
        cancel_event=cancel_event,
        ranges=ranges,
        progress_callback=progress_callback,
        progress_stage=progress_stage,
        progress_started=progress_started,
        backend_kwargs=backend_kwargs,
    )
    if cancel_event is not None and cancel_event.is_set():
        raise ExportExecutionError("Export cancelled")


__all__ = [
    "BackendValidation",
    "build_ffmpeg_interpolation_command",
    "require_validated_backend",
    "run_source_interpolation",
    "validate_interpolation_backend",
]
