#!/usr/bin/env python3
"""Benchmark the protected per-segment route against adaptive preparation."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import statistics
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from fractions import Fraction
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from benchmarks.render_strategy_benchmark import _gpu_sample, _probe, _usage  # noqa: E402
from framestudio import export_interpolation, export_process, export_smart_render  # noqa: E402
from framestudio.export_delivery import verify_mixed_export_output  # noqa: E402
from framestudio.export_planning import plan_mixed_export  # noqa: E402
from framestudio.fps_policy import FrameRatePolicy  # noqa: E402
from framestudio.media import probe_media  # noqa: E402
from framestudio.model import Segment, SegmentTimeline  # noqa: E402
from framestudio.upscale_policy import UpscalePolicy  # noqa: E402

DEFAULT_REPORT = ROOT / "evidence" / "efficient-export-pipeline-benchmark.json"
DEFAULT_MARKDOWN = ROOT / "evidence" / "efficient-export-pipeline-benchmark.md"


@dataclass
class CandidateMetrics:
    strategy: str
    status: str
    wall_seconds: float
    child_user_seconds: float
    child_system_seconds: float
    child_max_rss_kb_cumulative: float
    gpu_before: dict[str, Any] | None
    gpu_after: dict[str, Any] | None
    ffmpeg_process_count: int
    normalization_process_count: int
    interpolation_process_count: int
    interpolation_calls: int
    restoration_calls: int
    stage_seconds: dict[str, float]
    intermediate_peak_bytes: int
    output_bytes: int
    output: dict[str, Any] | None
    source_hashes_before: dict[str, str]
    source_hashes_after: dict[str, str]
    source_preserved: bool
    boundary_safe: bool | None
    boundary_samples: dict[str, str]
    error: str | None = None


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _run(command: list[str]) -> None:
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        detail = (result.stderr.strip().splitlines() or ["command failed"])[-1]
        raise RuntimeError(detail)


def _create_sources(root: Path, ffmpeg: str) -> tuple[Path, Path]:
    first = root / "source-a.mp4"
    _run(
        [
            ffmpeg,
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "color=c=red:s=640x360:r=30:d=1",
            "-f",
            "lavfi",
            "-i",
            "color=c=green:s=640x360:r=30:d=1",
            "-f",
            "lavfi",
            "-i",
            "color=c=blue:s=640x360:r=30:d=1",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=440:sample_rate=48000:duration=3",
            "-filter_complex",
            "[0:v][1:v][2:v]concat=n=3:v=1:a=0[outv]",
            "-map",
            "[outv]",
            "-map",
            "3:a:0",
            "-c:v",
            "libx264",
            "-g",
            "30",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-ar",
            "48000",
            "-ac",
            "2",
            "-shortest",
            str(first),
        ]
    )
    second = root / "source-b.mp4"
    _run(
        [
            ffmpeg,
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "testsrc2=size=480x640:rate=60",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=880:sample_rate=48000:duration=2",
            "-t",
            "2",
            "-c:v",
            "libx265",
            "-preset",
            "medium",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-ar",
            "48000",
            "-ac",
            "2",
            "-shortest",
            str(second),
        ]
    )
    return first, second


def _build_plan(first: Path, second: Path, destination: Path):
    first_probe = probe_media(first)
    second_probe = probe_media(second)
    timeline = SegmentTimeline.from_blocks(
        (
            Segment.create(0.0, 1.0, source_id="source-a"),
            Segment.create(1.0, 2.0, source_id="source-a", deleted=True),
            Segment.create(2.0, 3.0, source_id="source-a"),
            Segment.create(0.0, 2.0, source_id="source-b"),
        ),
        source_durations={
            "source-a": first_probe.duration_seconds,
            "source-b": second_probe.duration_seconds,
        },
    )
    return plan_mixed_export(
        (first_probe, second_probe),
        timeline,
        destination,
        source_ids=("source-a", "source-b"),
        frame_rate_policy=FrameRatePolicy(
            choice="custom",
            custom_rate=Fraction(60, 1),
            target_rate=Fraction(60, 1),
            enhancement_enabled=True,
            backend="ffmpeg-minterpolate",
        ),
        upscale_policy=UpscalePolicy(enhancement_enabled=False),
    )


def _intermediate_bytes(destination: Path) -> int:
    directory = destination.parent / f".{destination.name}.framestudio-intermediates"
    if not directory.is_dir():
        return 0
    return sum(path.stat().st_size for path in directory.rglob("*") if path.is_file())


def _sample_boundary(output: Path, timestamp: float, ffmpeg: str) -> str:
    result = subprocess.run(
        [
            ffmpeg,
            "-hide_banner",
            "-loglevel",
            "error",
            "-ss",
            f"{timestamp:.3f}",
            "-i",
            str(output),
            "-vf",
            "scale=32:18",
            "-frames:v",
            "1",
            "-f",
            "rawvideo",
            "-pix_fmt",
            "rgb24",
            "pipe:1",
        ],
        capture_output=True,
        check=False,
    )
    if result.returncode != 0 or len(result.stdout) < 32 * 18 * 3:
        return "unavailable"
    channels = [sum(result.stdout[index::3]) for index in range(3)]
    names = ("red", "green", "blue")
    return names[max(range(3), key=channels.__getitem__)]


def _source_hashes(paths: tuple[Path, ...]) -> dict[str, str]:
    return {path.name: _sha256(path) for path in paths}


def _run_candidate(
    strategy: str,
    *,
    first: Path,
    second: Path,
    root: Path,
    ffmpeg: str,
    ffprobe: str,
) -> CandidateMetrics:
    destination = root / f"{strategy}.mp4"
    plan = _build_plan(first, second, destination)
    source_paths = (first, second)
    source_before = _source_hashes(source_paths)
    stage_seconds: dict[str, float] = {}
    process_count = 0
    normalization_count = 0
    interpolation_process_count = 0
    interpolation_calls = 0
    restoration_calls = 0
    intermediate_peak = 0
    original_run_ffmpeg = export_process.run_ffmpeg
    original_interpolate = export_interpolation._interpolate_probe
    original_restoration = export_smart_render._run_source_restoration

    def counted_run_ffmpeg(command, *args, **kwargs):
        nonlocal process_count, normalization_count, interpolation_process_count
        nonlocal intermediate_peak
        stage = str(kwargs.get("stage", "unknown"))
        started = time.monotonic()
        try:
            return original_run_ffmpeg(command, *args, **kwargs)
        finally:
            elapsed = time.monotonic() - started
            stage_seconds[stage] = stage_seconds.get(stage, 0.0) + elapsed
            process_count += 1
            if "normaliz" in stage:
                normalization_count += 1
            if "interpolation" in stage:
                interpolation_process_count += 1
            intermediate_peak = max(intermediate_peak, _intermediate_bytes(destination))

    def counted_interpolate(*args, **kwargs):
        nonlocal interpolation_calls
        interpolation_calls += 1
        return original_interpolate(*args, **kwargs)

    def counted_restoration(*args, **kwargs):
        nonlocal restoration_calls
        restoration_calls += 1
        return original_restoration(*args, **kwargs)

    before_usage = _usage()
    gpu_before = _gpu_sample()
    started = time.monotonic()
    error: str | None = None
    output: dict[str, Any] | None = None
    try:
        with (
            patch.object(export_process, "run_ffmpeg", side_effect=counted_run_ffmpeg),
            patch.object(export_smart_render, "run_ffmpeg", side_effect=counted_run_ffmpeg),
            patch.object(export_interpolation, "run_ffmpeg", side_effect=counted_run_ffmpeg),
            patch.object(
                export_interpolation, "_interpolate_probe", side_effect=counted_interpolate
            ),
            patch.object(
                export_smart_render,
                "_run_source_restoration",
                side_effect=counted_restoration,
            ),
        ):
            export_interpolation.execute_enhanced_export(
                plan,
                ffmpeg_path=ffmpeg,
                ffprobe_path=ffprobe,
                progress_callback=None,
                verify_single_output=lambda *_args, **_kwargs: probe_media(destination),
                verify_mixed_output=lambda _plan, candidate, **kwargs: verify_mixed_export_output(
                    _plan,
                    candidate,
                    **kwargs,
                ),
                backend_kwargs={
                    "backend": "ffmpeg-minterpolate",
                    "pipeline_strategy": strategy,
                },
            )
        output = _probe(destination, ffprobe)
    except Exception as caught:  # benchmark row must report failed candidates
        error = str(caught)
    elapsed = time.monotonic() - started
    after_usage = _usage()
    source_after = _source_hashes(source_paths)
    boundary_samples: dict[str, str] = {}
    boundary_safe: bool | None = None
    if output is not None:
        boundary_samples = {
            "before_deleted_gap": _sample_boundary(destination, 0.98, ffmpeg),
            "after_deleted_gap": _sample_boundary(destination, 1.02, ffmpeg),
        }
        boundary_safe = boundary_samples == {
            "before_deleted_gap": "red",
            "after_deleted_gap": "blue",
        }
    return CandidateMetrics(
        strategy=strategy,
        status="passed" if error is None else "failed",
        wall_seconds=round(elapsed, 4),
        child_user_seconds=round(after_usage.ru_utime - before_usage.ru_utime, 4),
        child_system_seconds=round(after_usage.ru_stime - before_usage.ru_stime, 4),
        child_max_rss_kb_cumulative=round(after_usage.ru_maxrss, 1),
        gpu_before=gpu_before,
        gpu_after=_gpu_sample(),
        ffmpeg_process_count=process_count,
        normalization_process_count=normalization_count,
        interpolation_process_count=interpolation_process_count,
        interpolation_calls=interpolation_calls,
        restoration_calls=restoration_calls,
        stage_seconds={key: round(value, 4) for key, value in stage_seconds.items()},
        intermediate_peak_bytes=intermediate_peak,
        output_bytes=destination.stat().st_size if destination.is_file() else 0,
        output=output,
        source_hashes_before=source_before,
        source_hashes_after=source_after,
        source_preserved=source_before == source_after,
        boundary_safe=boundary_safe,
        boundary_samples=boundary_samples,
        error=error,
    )


def run_benchmark(
    *,
    ffmpeg: str = "ffmpeg",
    ffprobe: str = "ffprobe",
    repetitions: int = 1,
) -> dict[str, Any]:
    if shutil.which(ffmpeg) is None or shutil.which(ffprobe) is None:
        raise RuntimeError("FFmpeg and ffprobe are required")
    if isinstance(repetitions, bool) or not isinstance(repetitions, int) or repetitions <= 0:
        raise ValueError("Benchmark repetitions must be a positive integer")
    with TemporaryDirectory(prefix="framestudio-efficient-export-") as directory:
        root = Path(directory)
        first, second = _create_sources(root, ffmpeg)
        run_records: dict[str, list[dict[str, Any]]] = {
            "per-segment": [],
            "adaptive": [],
        }
        for repetition in range(repetitions):
            strategy_order = (
                ("per-segment", "adaptive") if repetition % 2 == 0 else ("adaptive", "per-segment")
            )
            for strategy in strategy_order:
                candidate_root = root / f"run-{repetition + 1}-{strategy}"
                candidate_root.mkdir()
                run_records[strategy].append(
                    asdict(
                        _run_candidate(
                            strategy,
                            first=first,
                            second=second,
                            root=candidate_root,
                            ffmpeg=ffmpeg,
                            ffprobe=ffprobe,
                        )
                    )
                )
        results = {
            strategy: _summarize_candidate_runs(runs) for strategy, runs in run_records.items()
        }
        recommendation = _recommend(results)
        report = {
            "benchmark": "efficient-export-pipeline",
            "protocol": {
                "sources": [
                    "640x360 H.264 30 FPS with red/green/blue ranges",
                    "480x640 HEVC 60 FPS",
                ],
                "retained_ranges": ["source-a 0-1s", "source-a 2-3s", "source-b 0-2s"],
                "deleted_range": "source-a 1-2s",
                "target_rate": "60/1",
                "upscale": "disabled for comparable routing benchmark",
                "backend": "ffmpeg-minterpolate",
                "repetitions": repetitions,
                "strategy_order": [
                    (
                        ("per-segment", "adaptive")
                        if repetition % 2 == 0
                        else ("adaptive", "per-segment")
                    )
                    for repetition in range(repetitions)
                ],
                "cache_note": (
                    "Each repetition uses a fresh destination-scoped export cache. "
                    "The operating-system file cache is not flushed between runs."
                ),
            },
            "strategies": results,
            "recommendation": recommendation,
        }
        return report


def _summarize_candidate_runs(runs: list[dict[str, Any]]) -> dict[str, Any]:
    if not runs:
        raise ValueError("Benchmark candidate runs cannot be empty")
    first = dict(runs[0])
    wall_seconds = [float(run["wall_seconds"]) for run in runs]
    first["run_count"] = len(runs)
    first["wall_seconds"] = round(statistics.median(wall_seconds), 4)
    first["wall_seconds_min"] = round(min(wall_seconds), 4)
    first["wall_seconds_max"] = round(max(wall_seconds), 4)
    for key in (
        "child_user_seconds",
        "child_system_seconds",
        "child_max_rss_kb_cumulative",
        "ffmpeg_process_count",
        "normalization_process_count",
        "interpolation_process_count",
        "interpolation_calls",
        "restoration_calls",
        "intermediate_peak_bytes",
        "output_bytes",
    ):
        values = [float(run[key]) for run in runs]
        median = statistics.median(values)
        if key.endswith("_count") or key.endswith("_calls") or key.endswith("_bytes"):
            first[key] = int(median)
        else:
            first[key] = round(median, 4)
    first["stage_seconds"] = {
        stage: round(
            statistics.median(float(run.get("stage_seconds", {}).get(stage, 0.0)) for run in runs),
            4,
        )
        for stage in {stage for run in runs for stage in run.get("stage_seconds", {})}
    }
    first["status"] = "passed" if all(run["status"] == "passed" for run in runs) else "failed"
    first["source_preserved"] = all(run["source_preserved"] for run in runs)
    first["boundary_safe"] = True if all(run["boundary_safe"] is True for run in runs) else False
    errors = [run["error"] for run in runs if run.get("error")]
    first["error"] = " | ".join(errors) if errors else None
    first["runs"] = runs
    return first


def _recommend(results: dict[str, dict[str, Any]]) -> dict[str, Any]:
    acceptable = [
        result
        for result in results.values()
        if result.get("status") == "passed"
        and result.get("source_preserved")
        and result.get("boundary_safe") is True
    ]
    if not acceptable:
        return {
            "selected_strategy": None,
            "reason": "No candidate passed all output, source-preservation, and boundary gates.",
        }
    selected = min(acceptable, key=lambda result: float(result["wall_seconds"]))
    return {
        "selected_strategy": selected["strategy"],
        "reason": "Selected the fastest candidate that passed the technical integrity gates.",
        "wall_seconds": selected["wall_seconds"],
        "normalization_process_count": selected["normalization_process_count"],
        "interpolation_calls": selected["interpolation_calls"],
    }


def _write_markdown(report: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [
        "| Strategy | Status | Median wall (s) | Min (s) | Max (s) | Child CPU (s) | "
        "FFmpeg processes | Normalize processes | Interpolation calls | Boundary-safe | "
        "Source preserved |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for result in report["strategies"].values():
        rows.append(
            "| {strategy} | {status} | {wall_seconds} | {wall_seconds_min} | "
            "{wall_seconds_max} | {child_user_seconds} | {ffmpeg_process_count} | "
            "{normalization_process_count} | {interpolation_calls} | {boundary_safe} | "
            "{source_preserved} |".format(**result)
        )
    selected = report["recommendation"].get("selected_strategy") or "none"
    baseline = report["strategies"].get("per-segment")
    adaptive = report["strategies"].get("adaptive")
    comparison: list[str] = []
    if isinstance(baseline, dict) and isinstance(adaptive, dict):
        wall_delta = float(baseline["wall_seconds"]) - float(adaptive["wall_seconds"])
        wall_percent = (
            wall_delta / float(baseline["wall_seconds"]) * 100.0
            if float(baseline["wall_seconds"]) > 0.0
            else 0.0
        )
        comparison = [
            "## Comparison",
            "",
            "| Metric | Adaptive vs per-segment |",
            "|---|---:|",
            f"| Wall-time change | {wall_delta:.4f} seconds ({wall_percent:.2f}%) |",
            f"| FFmpeg process change | {int(adaptive['ffmpeg_process_count']) - int(baseline['ffmpeg_process_count'])} |",
            f"| Normalization process change | {int(adaptive['normalization_process_count']) - int(baseline['normalization_process_count'])} |",
            f"| Interpolation-call change | {int(adaptive['interpolation_calls']) - int(baseline['interpolation_calls'])} |",
            "",
        ]
    stage_rows = [
        "| Strategy | Stage | Median seconds |",
        "|---|---|---:|",
    ]
    for result in report["strategies"].values():
        for stage, seconds in sorted(result.get("stage_seconds", {}).items()):
            stage_rows.append(f"| {result['strategy']} | {stage} | {seconds} |")
    path.write_text(
        "\n".join(
            [
                "# Efficient export pipeline benchmark",
                "",
                "This report compares the protected per-segment route with adaptive "
                "grouped source preparation on the same generated mixed-source fixture. "
                f"Each strategy has {report['protocol']['repetitions']} repetition(s).",
                "",
                *rows,
                "",
                f"Selected strategy: `{selected}`.",
                "",
                report["recommendation"]["reason"],
                "",
                *comparison,
                "## Stage timing",
                "",
                *stage_rows,
                "",
                "The benchmark is hardware- and fixture-specific. It does not replace "
                "the target-workstation visual review or the resumability functionality tests. "
                "The operating-system file cache was not flushed between repetitions, and "
                "GPU values are point-in-time observations rather than averages. The "
                "interpolation-process count includes FFmpeg artifact-preflight work, "
                "while interpolation-call count tracks production interpolation calls.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--markdown", type=Path, default=DEFAULT_MARKDOWN)
    parser.add_argument("--ffmpeg", default="ffmpeg")
    parser.add_argument("--ffprobe", default="ffprobe")
    parser.add_argument("--repetitions", type=int, default=1)
    args = parser.parse_args(argv)
    try:
        report = run_benchmark(
            ffmpeg=args.ffmpeg,
            ffprobe=args.ffprobe,
            repetitions=args.repetitions,
        )
    except (RuntimeError, ValueError) as error:
        print(f"benchmark blocked: {error}", file=sys.stderr)
        return 2
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    _write_markdown(report, args.markdown)
    print(json.dumps(report["recommendation"], indent=2))
    return 0 if report["recommendation"].get("selected_strategy") else 1


if __name__ == "__main__":
    raise SystemExit(main())
