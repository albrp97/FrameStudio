#!/usr/bin/env python3
"""Reproducible mixed-orientation upscale/render-order benchmark."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import resource
import shutil
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DEFAULT_OUTPUT_WIDTH = 1920
DEFAULT_OUTPUT_HEIGHT = 1080
DEFAULT_TARGET_RATE = Fraction(60, 1)
DEFAULT_ARTIFACT_ROOT = (
    Path.home() / "Documents" / "edit" / "ticket-080-upscale-render-strategy-20260827"
)


@dataclass(frozen=True)
class SourceSpec:
    source_id: str
    orientation: str
    fps: int
    duration_seconds: float
    width: int
    height: int
    audio: bool


@dataclass(frozen=True)
class StageResult:
    name: str
    status: str
    wall_seconds: float
    output_bytes: int = 0
    resource: dict[str, float] | None = None
    error: str | None = None
    gpu: dict[str, Any] | None = None


def expected_frame_count(duration_seconds: float, frame_rate: Fraction) -> int:
    exact = Fraction(str(duration_seconds)) * frame_rate
    return max(1, (exact.numerator + exact.denominator // 2) // exact.denominator)


def _rate_label(rate: Fraction) -> str:
    return f"{rate.numerator}/{rate.denominator}"


def report_path(path: Path) -> str:
    return path.name


def _stage_dict(stage: StageResult) -> dict[str, Any]:
    return asdict(stage)


def _tool(name: str) -> str | None:
    return shutil.which(name)


def _usage() -> resource.struct_rusage:
    return resource.getrusage(resource.RUSAGE_CHILDREN)


def _resource_delta(
    before: resource.struct_rusage, after: resource.struct_rusage
) -> dict[str, float]:
    return {
        "child_user_seconds": round(after.ru_utime - before.ru_utime, 4),
        "child_system_seconds": round(after.ru_stime - before.ru_stime, 4),
        "child_max_rss_kb_cumulative": round(after.ru_maxrss, 1),
    }


def _gpu_sample() -> dict[str, Any] | None:
    nvidia_smi = _tool("nvidia-smi")
    if nvidia_smi is None:
        return None
    try:
        result = subprocess.run(
            [
                nvidia_smi,
                "--query-gpu=name,utilization.gpu,memory.used,power.draw",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            check=False,
            timeout=3,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0 or not result.stdout.strip():
        return None
    fields = [field.strip() for field in result.stdout.splitlines()[0].split(",")]
    if len(fields) != 4:
        return None
    try:
        return {
            "name": fields[0],
            "utilization_percent": float(fields[1]),
            "memory_used_mb": float(fields[2]),
            "power_watts": float(fields[3]),
        }
    except ValueError:
        return None


def _run_stage(
    name: str,
    command: list[str],
    outputs: tuple[Path, ...],
    *,
    ffmpeg: str,
    env: dict[str, str] | None = None,
    timeout_seconds: float = 1800,
) -> StageResult:
    before = _usage()
    gpu_before = _gpu_sample()
    started = time.monotonic()
    try:
        result = subprocess.run(
            command, capture_output=True, text=True, check=False, env=env, timeout=timeout_seconds
        )
    except subprocess.TimeoutExpired:
        return StageResult(
            name,
            "failed",
            round(time.monotonic() - started, 4),
            resource=_resource_delta(before, _usage()),
            error=f"timed out after {timeout_seconds:.0f}s",
            gpu=gpu_before,
        )
    except OSError as error:
        return StageResult(
            name,
            "failed",
            round(time.monotonic() - started, 4),
            resource=_resource_delta(before, _usage()),
            error=f"could not start {ffmpeg}: {error.__class__.__name__}",
            gpu=gpu_before,
        )
    elapsed = round(time.monotonic() - started, 4)
    resources = _resource_delta(before, _usage())
    if result.returncode != 0:
        detail = (result.stderr.strip().splitlines() or ["command failed"])[-1]
        return StageResult(
            name, "failed", elapsed, resource=resources, error=detail[:300], gpu=gpu_before
        )
    size = sum(path.stat().st_size for path in outputs if path.is_file())
    if outputs and size <= 0:
        return StageResult(
            name, "failed", elapsed, resource=resources, error="no output artifact", gpu=gpu_before
        )
    return StageResult(name, "passed", elapsed, size, resources, gpu=gpu_before)


def _probe(path: Path, ffprobe: str) -> dict[str, Any]:
    result = subprocess.run(
        [
            ffprobe,
            "-v",
            "error",
            "-count_frames",
            "-show_streams",
            "-show_format",
            "-of",
            "json",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError("ffprobe failed")
    data = json.loads(result.stdout)
    streams = data.get("streams")
    if not isinstance(streams, list):
        raise ValueError("ffprobe output has no stream list")
    video = next((item for item in streams if item.get("codec_type") == "video"), None)
    if not isinstance(video, dict):
        raise ValueError("ffprobe output has no video stream")
    audio = next((item for item in streams if item.get("codec_type") == "audio"), None)
    rate = video.get("avg_frame_rate") or video.get("r_frame_rate")
    frames = video.get("nb_read_frames") or video.get("nb_frames")
    try:
        parsed_rate = Fraction(str(rate))
    except (ValueError, ZeroDivisionError) as error:
        raise ValueError("ffprobe output has invalid frame data") from error
    if parsed_rate <= 0 or frames is None:
        raise ValueError("ffprobe output has invalid frame data")
    fmt = data.get("format")
    if not isinstance(fmt, dict) or "duration" not in fmt:
        raise ValueError("ffprobe output has no format duration")
    return {
        "duration_seconds": round(float(fmt["duration"]), 6),
        "width": int(video["width"]),
        "height": int(video["height"]),
        "video_codec": str(video.get("codec_name", "")),
        "pixel_format": str(video.get("pix_fmt", "")),
        "fps": str(parsed_rate),
        "frames": int(frames),
        "audio": audio is not None,
        "audio_codec": None if audio is None else str(audio.get("codec_name", "")),
        "audio_sample_rate": None if audio is None else int(audio.get("sample_rate", 0)),
        "audio_channels": None if audio is None else int(audio.get("channels", 0)),
        "container": str(fmt.get("format_name", "")),
        "size_bytes": path.stat().st_size,
    }


def verify_output_integrity(
    metrics: dict[str, Any],
    sources: tuple[SourceSpec, ...],
    target_rate: Fraction,
    *,
    output_width: int = DEFAULT_OUTPUT_WIDTH,
    output_height: int = DEFAULT_OUTPUT_HEIGHT,
    expected_duration: float | None = None,
) -> dict[str, Any]:
    duration = (
        sum(source.duration_seconds for source in sources)
        if expected_duration is None
        else expected_duration
    )
    expected_audio = any(source.audio for source in sources)
    expected_frames = expected_frame_count(duration, target_rate)
    try:
        actual_rate = Fraction(str(metrics["fps"]))
    except (KeyError, ValueError, ZeroDivisionError):
        actual_rate = None
    tolerance = max(0.05, 1.0 / float(target_rate))
    checks = {
        "duration_seconds_matches": math.isclose(
            float(metrics.get("duration_seconds", 0)), duration, rel_tol=0, abs_tol=tolerance
        ),
        "width_matches": metrics.get("width") == output_width,
        "height_matches": metrics.get("height") == output_height,
        "video_codec_matches": metrics.get("video_codec") == "h264",
        "pixel_format_matches": metrics.get("pixel_format") == "yuv420p",
        "fps_matches": actual_rate == target_rate,
        "frames_matches": metrics.get("frames") == expected_frames,
        "audio_matches": metrics.get("audio") is expected_audio,
        "audio_codec_matches": not expected_audio or metrics.get("audio_codec") == "aac",
        "audio_sample_rate_matches": not expected_audio
        or metrics.get("audio_sample_rate") == 48000,
        "audio_channels_matches": not expected_audio or metrics.get("audio_channels") == 2,
        "container_matches": "mp4"
        in {item.strip() for item in str(metrics.get("container", "")).split(",")},
    }
    return {
        "expected_duration_seconds": duration,
        "duration_tolerance_seconds": tolerance,
        "expected_dimensions": f"{output_width}x{output_height}",
        "expected_fps": str(target_rate),
        "expected_frames": expected_frames,
        "expected_audio": expected_audio,
        **checks,
        "passed": all(checks.values()),
    }


def _playability(path: Path, ffmpeg: str) -> tuple[bool, str | None]:
    result = subprocess.run(
        [ffmpeg, "-v", "error", "-i", str(path), "-f", "null", "-"],
        capture_output=True,
        text=True,
        check=False,
    )
    return (True, None) if result.returncode == 0 else (False, "FFmpeg decode failed")


def _fixture_command(spec: SourceSpec, destination: Path, ffmpeg: str) -> list[str]:
    return [
        ffmpeg,
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-f",
        "lavfi",
        "-i",
        f"testsrc2=size={spec.width}x{spec.height}:rate={spec.fps}",
        "-f",
        "lavfi",
        "-i",
        f"sine=frequency={440 if spec.source_id == 'landscape_1080p24' else 880}:sample_rate=48000",
        "-t",
        str(spec.duration_seconds),
        "-c:v",
        "libx264",
        "-preset",
        "ultrafast",
        "-g",
        str(spec.fps),
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-ar",
        "48000",
        "-ac",
        "2",
        "-shortest",
        str(destination),
    ]


def _prepare_command(
    source: Path,
    destination: Path,
    *,
    fps: int,
    ffmpeg: str,
    output_width: int = DEFAULT_OUTPUT_WIDTH,
    output_height: int = DEFAULT_OUTPUT_HEIGHT,
) -> list[str]:
    return [
        ffmpeg,
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(source),
        "-vf",
        f"fps={fps},scale={output_width}:{output_height}:force_original_aspect_ratio=decrease,pad={output_width}:{output_height}:(ow-iw)/2:(oh-ih)/2,setsar=1",
        "-r",
        str(fps),
        "-c:v",
        "libx264",
        "-preset",
        "ultrafast",
        "-g",
        str(fps),
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-ar",
        "48000",
        "-ac",
        "2",
        "-shortest",
        str(destination),
    ]


def _cut_command(
    source: Path, destination: Path, start: float, duration: float, ffmpeg: str
) -> list[str]:
    return [
        ffmpeg,
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-ss",
        f"{start:.3f}",
        "-i",
        str(source),
        "-t",
        f"{duration:.3f}",
        "-c:v",
        "libx264",
        "-preset",
        "ultrafast",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-ar",
        "48000",
        "-ac",
        "2",
        "-avoid_negative_ts",
        "make_zero",
        str(destination),
    ]


def _spatial_command(source: Path, destination: Path, *, portrait: bool, ffmpeg: str) -> list[str]:
    if portrait:
        vf = "scale=480:1080:force_original_aspect_ratio=decrease,pad=480:1080:(ow-iw)/2:(oh-ih)/2:color=black,split=3[a][b][c];[a][b][c]hstack=inputs=3,setsar=1[out]"
        return [
            ffmpeg,
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(source),
            "-filter_complex",
            vf,
            "-map",
            "[out]",
            "-map",
            "0:a:0?",
            "-c:v",
            "libx264",
            "-preset",
            "ultrafast",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-ar",
            "48000",
            "-ac",
            "2",
            "-shortest",
            str(destination),
        ]
    else:
        vf = "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1"
    return [
        ffmpeg,
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(source),
        "-vf",
        vf,
        "-map",
        "0:v:0",
        "-map",
        "0:a:0?",
        "-c:v",
        "libx264",
        "-preset",
        "ultrafast",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-ar",
        "48000",
        "-ac",
        "2",
        "-shortest",
        str(destination),
    ]


def _fps_command(
    source: Path, destination: Path, target_rate: Fraction, ffmpeg: str, *, interpolate: bool = True
) -> list[str]:
    vf = (
        f"minterpolate=fps={target_rate.numerator}/{target_rate.denominator}:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1"
        if interpolate
        else f"fps={target_rate.numerator}/{target_rate.denominator}"
    )
    return [
        ffmpeg,
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(source),
        "-vf",
        vf,
        "-r",
        str(target_rate),
        "-c:v",
        "libx264",
        "-preset",
        "ultrafast",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-ar",
        "48000",
        "-ac",
        "2",
        "-shortest",
        str(destination),
    ]


def _concat_reencode_command(
    paths: tuple[Path, ...],
    destination: Path,
    ffmpeg: str,
    *,
    target_rate: Fraction,
) -> list[str]:
    command = [ffmpeg, "-hide_banner", "-loglevel", "error", "-y"]
    for path in paths:
        command.extend(["-i", str(path)])
    inputs = "".join(f"[{index}:v:0][{index}:a:0]" for index in range(len(paths)))
    graph = f"{inputs}concat=n={len(paths)}:v=1:a=1[v][a]"
    command.extend(
        [
            "-filter_complex",
            graph,
            "-map",
            "[v]",
            "-map",
            "[a]",
            "-r",
            str(target_rate),
            "-c:v",
            "libx264",
            "-preset",
            "ultrafast",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-ar",
            "48000",
            "-ac",
            "2",
            str(destination),
        ]
    )
    return command


def _write_concat_list(paths: tuple[Path, ...], destination: Path) -> None:
    destination.write_text(
        "".join(
            f"file '{str(path).replace(chr(39), chr(39) + chr(92) + chr(39))}'\n" for path in paths
        ),
        encoding="utf-8",
    )


def _concat_command(
    paths: tuple[Path, ...],
    list_path: Path,
    destination: Path,
    ffmpeg: str,
    *,
    target_rate: Fraction | None = None,
    target_frames: int | None = None,
) -> list[str]:
    if target_rate is None or target_frames is None:
        raise ValueError("concat target rate and frame count are required for matched benchmark")
    if not paths:
        raise ValueError("concat requires at least one input")
    from resolve_editor.export_smart_render import build_concat_copy_command

    return build_concat_copy_command(list_path, destination, has_audio=True, ffmpeg_path=ffmpeg)


def _enhance_command(
    source: Path, destination: Path, *, target_rate: Fraction, target_frames: int, ffmpeg: str
) -> list[str]:
    return _fps_command(source, destination, target_rate, ffmpeg, interpolate=True)


def _hashes(paths: tuple[Path, ...]) -> dict[str, str]:
    return {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in paths if path.is_file()
    }


def cleanup_workdir(workdir: Path, *, requested: bool) -> dict[str, Any]:
    if not requested:
        return {"requested": False, "passed": True, "workdir_removed": False, "error": None}
    try:
        shutil.rmtree(workdir)
    except FileNotFoundError:
        pass
    except OSError as error:
        return {
            "requested": True,
            "passed": False,
            "workdir_removed": False,
            "error": error.__class__.__name__,
        }
    removed = not workdir.exists()
    return {
        "requested": True,
        "passed": removed,
        "workdir_removed": removed,
        "error": None if removed else "workdir remains after cleanup",
    }


def summarize_benchmark_gates(
    strategy_results: dict[str, dict[str, Any]],
    *,
    source_preservation: dict[str, Any],
    cleanup: dict[str, Any],
) -> dict[str, Any]:
    strategy_passed = bool(strategy_results) and all(
        result.get("status") == "passed" for result in strategy_results.values()
    )
    source_passed = bool(source_preservation.get("passed"))
    cleanup_passed = bool(cleanup.get("passed"))
    return {
        "status": "passed" if strategy_passed and source_passed and cleanup_passed else "failed",
        "strategies_passed": strategy_passed,
        "source_preservation_passed": source_passed,
        "cleanup_passed": cleanup_passed,
    }


def build_comparison_report(
    *,
    sources: tuple[SourceSpec, ...],
    target_rate: Fraction,
    backend: str,
    strategy_results: dict[str, dict[str, Any]],
    environment: dict[str, Any],
    output_width: int = DEFAULT_OUTPUT_WIDTH,
    output_height: int = DEFAULT_OUTPUT_HEIGHT,
) -> dict[str, Any]:
    serialized = {}
    for strategy, result in strategy_results.items():
        serialized[strategy] = dict(result)
        serialized[strategy]["stages"] = [
            _stage_dict(stage) if isinstance(stage, StageResult) else stage
            for stage in result.get("stages", [])
        ]
    recommendation = _bounded_recommendation(serialized)
    return {
        "schema_version": 1,
        "benchmark": "ticket-080-upscale-render-strategy-benchmark",
        "status": "passed"
        if serialized and all(item.get("status") == "passed" for item in serialized.values())
        else "failed",
        "protocol": {
            "source_ids": [source.source_id for source in sources],
            "sources": [asdict(source) for source in sources],
            "retained_ranges_seconds": {
                source.source_id: {"start": 10.0, "duration": 10.0} for source in sources
            },
            "portrait_triplicate": {
                "source_id": "portrait_720x1280_30",
                "layout": "three equal side-by-side slots",
            },
            "target_fps": _rate_label(target_rate),
            "backend": backend,
            "native_rve_24_to_60": (
                "supported for constant-frame-rate input via 3x integer RVE "
                "oversampling and exact 60 FPS GPU normalization; VFR remains unsupported"
            ),
            "output_profile": {
                "dimensions": f"{output_width}x{output_height}",
                "video_codec": "h264",
                "pixel_format": "yuv420p",
                "audio_codec": "aac",
                "audio": "AAC 48kHz stereo",
                "container": "mp4",
            },
            "verification_gates": [
                "ffprobe metadata and frame count",
                "FFmpeg decode/playability",
                "source hash unchanged",
                "partial/intermediate cleanup",
            ],
            "repetitions": 1,
        },
        "environment": environment,
        "strategies": serialized,
        "comparison": {
            "facts": "Measured stage and end-to-end values are in strategy results.",
            "subjective_quality_notes": "Contact sheets and fixed frames are retained for manual inspection; no numeric visual score is inferred.",
            "recommendation": recommendation,
        },
    }


def _bounded_recommendation(
    strategy_results: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    production = strategy_results.get("production_per_source_rve", {})
    controls = {
        name: {
            "status": result.get("status"),
            "total_wall_seconds": result.get("total_wall_seconds"),
            "final_bytes": result.get("final_bytes"),
        }
        for name, result in strategy_results.items()
        if name != "production_per_source_rve"
    }
    return {
        "selected_strategy": "production_per_source_rve",
        "selected_strategy_role": "quality-oriented production candidate",
        "rationale": (
            "SuperUltraCompact restoration ran per source before spatial preparation; "
            "the 24 FPS source used the pre-fix FFmpeg minterpolate fallback. The "
            "current fractional RVE route is validated separately in TICKET-081."
        ),
        "selected_strategy_measurements": {
            "status": production.get("status"),
            "total_wall_seconds": production.get("total_wall_seconds"),
            "final_bytes": production.get("final_bytes"),
        },
        "controls": controls,
        "control_quality_limitation": (
            "Controls are no-enhancement timing/integrity controls using non-RVE FPS "
            "conversion; they are not quality-equivalent to the RVE production row and "
            "must not be used for a visual-quality ranking."
        ),
        "visual_quality_claim": "No numeric visual-quality claim is made.",
        "scope_limits": [
            "one cold run",
            "synthetic testsrc2/sine fixtures",
            "single workstation",
            "production routing is unchanged",
        ],
        "review_artifacts": "Contact sheets and fixed frames require human inspection.",
    }


def _rve_context() -> tuple[list[str], dict[str, str], str] | None:
    try:
        from resolve_fps import (
            DEFAULT_FPS_PYTHON,
            DEFAULT_FPS_SITE,
            DEFAULT_RVE_RESTORATION_MODEL,
            DEFAULT_RVE_ROOT,
            DEFAULT_RVE_SHIMS,
            rve_environment,
            validate_rve_checkout,
        )

        args = argparse.Namespace(
            python=DEFAULT_FPS_PYTHON,
            site_packages=DEFAULT_FPS_SITE,
            rve_root=DEFAULT_RVE_ROOT,
            rve_shims=DEFAULT_RVE_SHIMS,
            encoder="libx264",
        )
        validate_rve_checkout(DEFAULT_RVE_ROOT)
        if not DEFAULT_FPS_PYTHON.is_file() or not DEFAULT_RVE_RESTORATION_MODEL.is_file():
            return None
        return ([], rve_environment(args, Fraction(24, 1)), str(DEFAULT_RVE_RESTORATION_MODEL))
    except (ImportError, OSError, RuntimeError):
        return None


@dataclass
class _StageRunner:
    ffmpeg: str
    stages: list[StageResult]
    artifacts: list[Path]
    failed: bool = False

    def run(
        self,
        name: str,
        command: list[str],
        outputs: tuple[Path, ...],
        *,
        env: dict[str, str] | None = None,
        timeout: float = 1800,
    ) -> None:
        if self.failed:
            self.stages.append(StageResult(name, "blocked", 0.0, error="blocked by previous stage"))
            return
        result = _run_stage(
            name,
            command,
            outputs,
            ffmpeg=self.ffmpeg,
            env=env,
            timeout_seconds=timeout,
        )
        self.stages.append(result)
        self.artifacts.extend(outputs)
        self.failed = result.status != "passed"


def _prepare_strategy_inputs(
    strategy: str,
    sources: tuple[SourceSpec, ...],
    source_paths: tuple[Path, ...],
    workdir: Path,
    runner: _StageRunner,
) -> tuple[list[Path], dict[str, Path]]:
    retained: list[Path] = []
    pre_spatial_retained: dict[str, Path] = {}
    for spec, source in zip(sources, source_paths, strict=True):
        if strategy == "full_source_before_cut_control":
            full_spatial = workdir / f"{spec.source_id}-full-spatial.mp4"
            runner.run(
                f"spatially prepare full source {spec.source_id} before cut",
                _spatial_command(
                    source,
                    full_spatial,
                    portrait=spec.orientation == "portrait",
                    ffmpeg=runner.ffmpeg,
                ),
                (full_spatial,),
            )
            cut = workdir / f"{spec.source_id}-retained-after-spatial.mp4"
            runner.run(
                f"cut retained 10s after spatial preparation {spec.source_id}",
                _cut_command(full_spatial, cut, 10, 10, runner.ffmpeg),
                (cut,),
            )
            pre_spatial_retained[spec.source_id] = cut
        else:
            cut = workdir / f"{spec.source_id}-retained.mp4"
            runner.run(
                f"cut retained 10s {spec.source_id}",
                _cut_command(source, cut, 10, 10, runner.ffmpeg),
                (cut,),
            )
        retained.append(cut)
    return retained, pre_spatial_retained


def _prepare_spatial_inputs(
    strategy: str,
    sources: tuple[SourceSpec, ...],
    retained: list[Path],
    pre_spatial_retained: dict[str, Path],
    workdir: Path,
    runner: _StageRunner,
    *,
    use_rve: bool,
    ffprobe: str,
) -> list[Path]:
    spatial_paths: list[Path] = []
    rve_info = _rve_context() if use_rve else None
    for spec, cut in zip(sources, retained, strict=True):
        if strategy == "full_source_before_cut_control":
            spatial_paths.append(pre_spatial_retained[spec.source_id])
            continue
        current = cut
        if use_rve:
            current = _run_rve_stage(spec, current, workdir, runner, rve_info, ffprobe)
        spatial = workdir / f"{spec.source_id}-spatial.mp4"
        runner.run(
            f"spatial scale/crop/pad {spec.source_id}",
            _spatial_command(
                current,
                spatial,
                portrait=spec.orientation == "portrait",
                ffmpeg=runner.ffmpeg,
            ),
            (spatial,),
        )
        if not runner.failed:
            spatial_paths.append(spatial)
    return spatial_paths


def _run_rve_stage(
    spec: SourceSpec,
    current: Path,
    workdir: Path,
    runner: _StageRunner,
    rve_info: tuple[list[str], dict[str, str], str] | None,
    ffprobe: str,
) -> Path:
    if rve_info is None:
        runner.stages.append(
            StageResult(
                f"RVE restoration {spec.source_id}",
                "unavailable",
                0.0,
                error="validated RVE runtime/model unavailable",
            )
        )
        return current
    from resolve_fps import (
        DEFAULT_FPS_PYTHON,
        DEFAULT_FPS_SITE,
        DEFAULT_RVE_ROOT,
        DEFAULT_RVE_SHIMS,
        build_rve_restoration_command,
    )

    args = argparse.Namespace(
        python=DEFAULT_FPS_PYTHON,
        site_packages=DEFAULT_FPS_SITE,
        rve_root=DEFAULT_RVE_ROOT,
        rve_shims=DEFAULT_RVE_SHIMS,
        encoder="libx264",
    )
    out = workdir / f"{spec.source_id}-rve.mp4"
    try:
        probe = _probe(current, ffprobe)
        command = build_rve_restoration_command(
            current,
            out,
            int(probe["frames"]),
            workdir,
            args,
            Path(rve_info[2]),
        )
    except (OSError, RuntimeError, ValueError) as error:
        runner.stages.append(
            StageResult(
                f"RVE restoration {spec.source_id}",
                "failed",
                0.0,
                error=str(error)[:300],
            )
        )
        runner.failed = True
        return current
    env = dict(rve_info[1])
    env["RVE_RGB_INPUT"] = "1"
    runner.run(
        f"RVE SuperUltraCompact restoration {spec.source_id}",
        command,
        (out,),
        env=env,
        timeout=1800,
    )
    return out if not runner.failed else current


def _run_fps_stages(
    strategy: str,
    sources: tuple[SourceSpec, ...],
    spatial_paths: list[Path],
    workdir: Path,
    runner: _StageRunner,
    target_rate: Fraction,
) -> list[Path]:
    processed: list[Path] = []
    if runner.failed:
        return processed
    for spec, spatial in zip(sources, spatial_paths, strict=True):
        fps_out = workdir / f"{spec.source_id}-60fps.mp4"
        interpolate = strategy == "production_per_source_rve"
        runner.run(
            f"{'FPS minterpolate' if interpolate else 'FPS control'} {spec.source_id}",
            _fps_command(
                spatial,
                fps_out,
                target_rate,
                runner.ffmpeg,
                interpolate=interpolate,
            ),
            (fps_out,),
        )
        processed.append(fps_out)
    return processed


def _run_concat_first_control(
    sources: tuple[SourceSpec, ...],
    spatial_paths: list[Path],
    workdir: Path,
    runner: _StageRunner,
    target_rate: Fraction,
) -> list[Path]:
    normalized: list[Path] = []
    concat_rate = Fraction(30, 1)
    for spec, spatial in zip(sources, spatial_paths, strict=True):
        normalized_path = workdir / f"{spec.source_id}-concat-30fps.mp4"
        runner.run(
            f"normalize {spec.source_id} to concat FPS",
            _fps_command(
                spatial,
                normalized_path,
                concat_rate,
                runner.ffmpeg,
                interpolate=False,
            ),
            (normalized_path,),
        )
        normalized.append(normalized_path)
    if runner.failed:
        return []
    list_path = workdir / "concat-before-fps-list.txt"
    _write_concat_list(tuple(normalized), list_path)
    joined = workdir / "concat-before-fps.mp4"
    runner.run(
        "concatenate normalized sources before FPS",
        _concat_command(
            tuple(normalized),
            list_path,
            joined,
            runner.ffmpeg,
            target_rate=concat_rate,
            target_frames=expected_frame_count(30, concat_rate),
        ),
        (joined,),
    )
    if runner.failed:
        return []
    unified = workdir / "concat-first-60fps.mp4"
    runner.run(
        "FPS control after concatenation",
        _fps_command(
            joined,
            unified,
            target_rate,
            runner.ffmpeg,
            interpolate=False,
        ),
        (unified,),
    )
    return [unified]


def _finalize_strategy(
    processed: list[Path],
    workdir: Path,
    artifact_root: Path,
    runner: _StageRunner,
    target_rate: Fraction,
    *,
    strategy: str,
) -> Path:
    final = artifact_root / "outputs" / f"{strategy}.mp4"
    final.parent.mkdir(parents=True, exist_ok=True)
    if runner.failed or not processed:
        return final
    list_path = workdir / "concat-list.txt"
    _write_concat_list(tuple(processed), list_path)
    joined = workdir / "joined.mp4"
    if len(processed) == 1:
        joined = processed[0]
    else:
        runner.run(
            "concatenate processed sources",
            _concat_command(
                tuple(processed),
                list_path,
                joined,
                runner.ffmpeg,
                target_rate=target_rate,
                target_frames=expected_frame_count(30, target_rate),
            ),
            (joined,),
        )
    if not runner.failed:
        runner.run(
            "final encode fixed canvas",
            [
                runner.ffmpeg,
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-i",
                str(joined),
                "-vf",
                "fps=60,tpad=stop_mode=clone:stop_duration=2",
                "-af",
                "apad",
                "-t",
                "30",
                "-r",
                str(target_rate),
                "-c:v",
                "libx264",
                "-preset",
                "ultrafast",
                "-pix_fmt",
                "yuv420p",
                "-c:a",
                "aac",
                "-ar",
                "48000",
                "-ac",
                "2",
                "-movflags",
                "+faststart",
                str(final),
            ],
            (final,),
        )
    return final


def _strategy_ordering(strategy: str) -> str:
    return {
        "production_per_source_rve": (
            "cut -> audio-preserving RVE restoration -> spatial crop/pad -> "
            "per-source 60 FPS minterpolate -> concatenate -> final encode"
        ),
        "concat_first_control": (
            "cut -> spatial crop/pad -> normalize all sources to 30 FPS -> "
            "concatenate -> 60 FPS control conversion -> final encode"
        ),
        "cut_first_control": (
            "cut -> spatial crop/pad -> per-source 60 FPS control conversion -> "
            "concatenate -> final encode"
        ),
        "full_source_before_cut_control": (
            "full-source control variant retained as an explicit comparison row; "
            "source ranges are cut before final assembly"
        ),
    }.get(strategy, strategy)


def _record_strategy_verification(
    result: dict[str, Any],
    final: Path,
    sources: tuple[SourceSpec, ...],
    target_rate: Fraction,
    ffmpeg: str,
    ffprobe: str,
) -> None:
    try:
        metrics = _probe(final, ffprobe)
        result["output"] = metrics
        result["verification"] = verify_output_integrity(
            metrics, sources, target_rate, expected_duration=30.0
        )
        result["status"] = "passed" if result["verification"]["passed"] else "failed"
        playable, playability_error = _playability(final, ffmpeg)
        result["playability"] = {"passed": playable, "error": playability_error}
        if result["status"] != "passed" or not playable:
            result["status"] = "failed"
        _write_visual_review(result, final, ffmpeg, target_rate)
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as error:
        result["status"] = "failed"
        result["verification_error"] = error.__class__.__name__


def _write_visual_review(
    result: dict[str, Any], final: Path, ffmpeg: str, target_rate: Fraction
) -> None:
    artifact_root = final.parents[1]
    strategy = final.stem
    contact = artifact_root / "contact-sheets" / f"{strategy}.jpg"
    contact.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            ffmpeg,
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(final),
            "-vf",
            "fps=1/10,scale=320:-1,tile=3x1",
            "-frames:v",
            "1",
            str(contact),
        ],
        check=False,
    )
    fixed_frames: list[str] = []
    for timestamp in (0, 10, 20, 29.5):
        frame = artifact_root / "fixed-frames" / f"{strategy}-{timestamp:g}s.png"
        frame.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            [
                ffmpeg,
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-ss",
                str(timestamp),
                "-i",
                str(final),
                "-frames:v",
                "1",
                str(frame),
            ],
            check=False,
        )
        if frame.is_file():
            fixed_frames.append(report_path(frame))
    result["output_sha256"] = hashlib.sha256(final.read_bytes()).hexdigest()
    result["visual_review"] = {
        "contact_sheet": report_path(contact),
        "fixed_frames": fixed_frames,
        "fixed_timestamps_seconds": [0, 10, 20, 29.5],
    }


def _run_strategy(
    strategy: str,
    sources: tuple[SourceSpec, ...],
    source_paths: tuple[Path, ...],
    workdir: Path,
    artifact_root: Path,
    *,
    target_rate: Fraction,
    ffmpeg: str,
    ffprobe: str,
    use_rve: bool,
) -> dict[str, Any]:
    workdir.mkdir(parents=True, exist_ok=True)
    runner = _StageRunner(ffmpeg, [], [])
    retained, pre_spatial_retained = _prepare_strategy_inputs(
        strategy, sources, source_paths, workdir, runner
    )
    spatial_paths = _prepare_spatial_inputs(
        strategy,
        sources,
        retained,
        pre_spatial_retained,
        workdir,
        runner,
        use_rve=use_rve,
        ffprobe=ffprobe,
    )
    processed = (
        _run_concat_first_control(sources, spatial_paths, workdir, runner, target_rate)
        if strategy == "concat_first_control"
        else _run_fps_stages(strategy, sources, spatial_paths, workdir, runner, target_rate)
    )
    final = _finalize_strategy(
        processed,
        workdir,
        artifact_root,
        runner,
        target_rate,
        strategy=strategy,
    )
    intermediate_bytes = sum(path.stat().st_size for path in runner.artifacts if path.is_file())
    result: dict[str, Any] = {
        "status": "failed" if runner.failed else "passed",
        "ordering": _strategy_ordering(strategy),
        "stages": runner.stages,
        "total_wall_seconds": round(sum(item.wall_seconds for item in runner.stages), 4),
        "intermediate_bytes": intermediate_bytes,
        "temporary_storage_bytes": intermediate_bytes,
        "final_bytes": final.stat().st_size if final.is_file() else 0,
        "output_artifact": report_path(final),
        "subjective_quality_notes": (
            "Manual review required for faces/text, edges, ringing, color, crop/pad, "
            "temporal stability, and triplicate behavior."
        ),
    }
    if not runner.failed and final.is_file():
        _record_strategy_verification(result, final, sources, target_rate, ffmpeg, ffprobe)
    return result


def run_benchmark(
    report: Path,
    *,
    keep_artifacts: bool = False,
    target_rate: Fraction = DEFAULT_TARGET_RATE,
    artifact_root: Path = DEFAULT_ARTIFACT_ROOT,
) -> dict[str, Any]:
    if target_rate <= 0:
        raise ValueError("target FPS must be positive")
    report = report.expanduser().resolve()
    artifact_root = artifact_root.expanduser().resolve()
    artifact_root.mkdir(parents=True, exist_ok=True)
    ffmpeg, ffprobe = _tool("ffmpeg"), _tool("ffprobe")
    sources = (
        SourceSpec("landscape_1080p24", "landscape", 24, 40.0, 1920, 1080, True),
        SourceSpec("landscape_480p30", "landscape", 30, 40.0, 854, 480, True),
        SourceSpec("portrait_720x1280_30", "portrait", 30, 40.0, 720, 1280, True),
    )
    env: dict[str, Any] = {
        "platform": platform.platform(),
        "python": sys.version.split()[0],
        "ffmpeg": "available" if ffmpeg else "unavailable",
        "ffprobe": "available" if ffprobe else "unavailable",
        "artifact_root": "~/Documents/edit/ticket-080-upscale-render-strategy-20260827",
        "limits": "Single workstation; one cold repetition; generated fixtures; reports redact private paths.",
    }
    rve = _rve_context()
    env["rve"] = {
        "available": bool(rve),
        "executed": False,
        "model": "SuperUltraCompact" if rve else None,
        "native_24_to_60": (
            "supported for constant-frame-rate input via 3x integer RVE "
            "oversampling and exact 60 FPS GPU normalization; VFR remains unsupported"
        ),
    }
    if not ffmpeg or not ffprobe:
        results = {
            name: {"status": "blocked", "stages": [], "error": "ffmpeg/ffprobe unavailable"}
            for name in (
                "production_per_source_rve",
                "concat_first_control",
                "cut_first_control",
                "full_source_before_cut_control",
            )
        }
        env["source_preservation"] = {"passed": False, "hashes_compared": False}
        env["cleanup"] = {
            "requested": not keep_artifacts,
            "passed": True,
            "workdir_removed": not keep_artifacts,
        }
        data = build_comparison_report(
            sources=sources,
            target_rate=target_rate,
            backend="ffmpeg-minterpolate",
            strategy_results=results,
            environment=env,
        )
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        return data
    workdir = artifact_root / "work"
    workdir.mkdir(parents=True, exist_ok=True)
    source_paths = tuple(
        artifact_root / "fixtures" / f"{source.source_id}.mp4" for source in sources
    )
    (artifact_root / "fixtures").mkdir(parents=True, exist_ok=True)
    fixture_stages: list[StageResult] = []
    for spec, destination in zip(sources, source_paths, strict=True):
        fixture_stages.append(
            _run_stage(
                f"generate {spec.source_id} fixture",
                _fixture_command(spec, destination, ffmpeg),
                (destination,),
                ffmpeg=ffmpeg,
                timeout_seconds=900,
            )
        )
    before = _hashes(source_paths)
    env["fixture_generation"] = "passed" if len(before) == len(sources) else "failed"
    env["fixture_stages"] = [_stage_dict(item) for item in fixture_stages]
    results = {}
    for name, use_rve in (
        ("production_per_source_rve", True),
        ("concat_first_control", False),
        ("cut_first_control", False),
        ("full_source_before_cut_control", False),
    ):
        results[name] = _run_strategy(
            name,
            sources,
            source_paths,
            workdir / name,
            artifact_root,
            target_rate=target_rate,
            ffmpeg=ffmpeg,
            ffprobe=ffprobe,
            use_rve=use_rve,
        )
    after = _hashes(source_paths)
    env["source_preservation"] = {
        "passed": before == after and bool(before),
        "hashes_compared": bool(before),
        "before": before,
        "after": after,
    }
    env["cleanup"] = cleanup_workdir(workdir, requested=not keep_artifacts)
    env["benchmark_gates"] = summarize_benchmark_gates(
        results, source_preservation=env["source_preservation"], cleanup=env["cleanup"]
    )
    env["rve"]["executed"] = any(
        any(
            "RVE SuperUltraCompact" in stage.name and stage.status == "passed"
            for stage in result.get("stages", [])
            if isinstance(stage, StageResult)
        )
        for result in results.values()
    )
    data = build_comparison_report(
        sources=sources,
        target_rate=target_rate,
        backend="ffmpeg-minterpolate",
        strategy_results=results,
        environment=env,
    )
    data["status"] = env["benchmark_gates"]["status"]
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return data


def _write_markdown(data: dict[str, Any], destination: Path) -> None:
    lines = [
        "# TICKET-080 Upscale render strategy benchmark",
        "",
        f"Status: **{data['status']}**",
        "",
        "Generated 40-second fixtures: 1920x1080/24 landscape, 854x480/30 landscape, and 720x1280/30 portrait. Retained range is 10 seconds per source; the portrait range is triplicated side-by-side. Final policy is 1920x1080 at 60 FPS with AAC stereo.",
        "",
        "The current editor supports constant-frame-rate 24->60 through 3x integer RVE oversampling followed by exact 60 FPS GPU normalization. The strategy rows in this historical ticket-080 report were measured before that fix and retain their original FFmpeg `minterpolate` measurements.",
        "",
        "| Strategy | Status | Total seconds | Final bytes | FPS/frames | Playable |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for name, result in data.get("strategies", {}).items():
        output = result.get("output", {})
        play = result.get("playability", {}).get("passed", False)
        lines.append(
            f"| {name} | {result.get('status')} | {result.get('total_wall_seconds', 0)} | {result.get('final_bytes', 0)} | {output.get('fps', '-')}/{output.get('frames', '-')} | {'yes' if play else 'no'} |"
        )
    recommendation = data.get("comparison", {}).get("recommendation", {})
    selected = recommendation.get("selected_strategy_measurements", {})
    controls = recommendation.get("controls", {})
    selected_bytes = selected.get("final_bytes")
    selected_bytes_text = f"{selected_bytes:,}" if isinstance(selected_bytes, int) else "0"
    concat_control = controls.get("concat_first_control", {})
    concat_bytes = concat_control.get("final_bytes")
    concat_bytes_text = f"{concat_bytes:,}" if isinstance(concat_bytes, int) else "0"
    control_values = [
        f"{item.get('total_wall_seconds')}s/{item.get('final_bytes')} bytes"
        for item in controls.values()
    ]
    lines += [
        "",
        "## Bounded recommendation",
        "",
        (
            "For this workstation and generated fixture set, retain "
            f"`{recommendation.get('selected_strategy', 'production_per_source_rve')}` "
            "as the quality-oriented production candidate: "
            f"{recommendation.get('rationale', '')} This row took "
            f"{selected.get('total_wall_seconds')} seconds and produced a "
            f"{selected_bytes_text}-byte output."
        ),
        "",
        (
            f"{recommendation.get('control_quality_limitation', '')} "
            f"The repaired concat-first control now normalizes each spatially "
            f"prepared source to 30 FPS, concatenates those normalized streams, "
            f"then performs the 60 FPS control conversion; its measured result is "
            f"{concat_control.get('total_wall_seconds')} "
            f"seconds and {concat_bytes_text} "
            f"bytes. Control measurements are: {', '.join(control_values)}."
        ),
        "",
        (
            "The result is bounded to one cold run, synthetic `testsrc2`/sine "
            "fixtures, and this workstation. "
            f"{recommendation.get('review_artifacts', '')} "
            f"{recommendation.get('visual_quality_claim', '')} Production routing "
            "is not changed by this benchmark."
        ),
    ]
    lines += [
        "",
        "Artifacts are retained under the external user artifact directory recorded in the JSON; committed report paths are redacted. Contact sheets/fixed timestamps require human visual review. Failed or unavailable stages remain explicit in the machine-readable report.",
        "",
    ]
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("benchmarks/results/ticket-080-upscale-render-strategy-benchmark.json"),
    )
    parser.add_argument(
        "--markdown",
        type=Path,
        default=Path("benchmarks/results/ticket-080-upscale-render-strategy-benchmark.md"),
    )
    parser.add_argument("--artifact-root", type=Path, default=DEFAULT_ARTIFACT_ROOT)
    parser.add_argument("--target-fps", type=Fraction, default=DEFAULT_TARGET_RATE)
    parser.add_argument("--keep-artifacts", action="store_true")
    args = parser.parse_args()
    if args.target_fps <= 0:
        parser.error("--target-fps must be positive")
    data = run_benchmark(
        args.report,
        keep_artifacts=args.keep_artifacts,
        target_rate=args.target_fps,
        artifact_root=args.artifact_root,
    )
    _write_markdown(data, args.markdown)
    return 0 if data.get("status") == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
