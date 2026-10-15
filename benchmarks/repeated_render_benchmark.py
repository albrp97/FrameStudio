#!/usr/bin/env python3
"""Measure repeated native-range preparation and whole-render checkpoint reuse."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import shutil
import sys
import threading
import time
from contextlib import ExitStack
from fractions import Fraction
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from framestudio import av_compositor as av  # noqa: E402
from framestudio import video_compositor as video  # noqa: E402
from framestudio.fps_policy import FrameRatePolicy  # noqa: E402
from framestudio.media import probe_media  # noqa: E402
from framestudio.model import Project, Segment  # noqa: E402
from framestudio.operations import ensure_project_audio_analysis  # noqa: E402
from framestudio.render_preparations import RenderPreparations  # noqa: E402
from framestudio.upscale_policy import UpscalePolicy  # noqa: E402


def _load_baseline(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(f"framestudio.{name}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load preserved baseline renderer")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _cancelled_attempt(
    args: argparse.Namespace,
    plan: av.AVRenderPlan,
    cache_root: Path,
    counts: dict[str, int],
    timings: dict[str, float],
    input_counts: list[int],
    completed_backends: list[str],
) -> dict[str, object]:
    event = threading.Event()

    def cancel_after_stage(progress):
        if progress.stage == "Checkpointed " + args.resume_after:
            event.set()

    started = time.perf_counter()
    try:
        av.render_project_av(
            plan,
            cancel_event=event,
            preparations=RenderPreparations(
                cache_root,
                cancel_event=event,
                progress_callback=cancel_after_stage,
            ),
        )
    except av.AVCompositorExecutionError:
        if not event.is_set():
            raise
    else:
        raise RuntimeError("Checkpoint cancellation was not reached")
    attempt = {
        "wall_seconds": time.perf_counter() - started,
        "calls": dict(counts),
        "completed_backends": list(completed_backends),
    }
    for name in counts:
        counts[name] = 0
        timings[name] = 0.0
    input_counts.clear()
    completed_backends.clear()
    return attempt


def _repeated_project(source: Path, repeats_per_track: int) -> Project:
    project = Project.create_synchronized_multi(((source, probe_media(source).metadata()),))
    for track_id in ("track-2", "track-3"):
        project.timeline.add_track(track_id)
    for track in tuple(project.timeline.tracks or ()):
        project.timeline.replace_track_blocks(
            track.track_id,
            tuple(
                Segment.create(
                    segment_id=f"{track.track_id}-{index}",
                    track_id=track.track_id,
                    source_id=project.source.source_id,
                    start_seconds=(index % 2) * 0.5,
                    end_seconds=(index % 2 + 1) * 0.5,
                    timeline_start_seconds=index * 0.5,
                    timeline_end_seconds=(index + 1) * 0.5,
                )
                for index in range(2 * repeats_per_track)
            ),
        )
    ensure_project_audio_analysis(project)
    return project


def run(args: argparse.Namespace) -> dict:
    import subprocess

    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path is None:
        raise RuntimeError("FFmpeg is required for the repeated-render benchmark")
    baseline = (
        _load_baseline(args.baseline_video, "_benchmark_baseline_video")
        if args.baseline_video
        else video
    )
    baseline_av = (
        _load_baseline(args.baseline_av, "_benchmark_baseline_av") if args.baseline_av else av
    )
    results = []
    with TemporaryDirectory(prefix="framestudio-repeat-benchmark-") as temporary:
        root = Path(temporary)
        source = root / "source.mp4"
        subprocess.run(
            [
                ffmpeg_path,
                "-hide_banner",
                "-loglevel",
                "error",
                "-f",
                "lavfi",
                "-i",
                "testsrc2=size=320x180:rate=30:duration=1",
                "-f",
                "lavfi",
                "-i",
                "sine=frequency=440:sample_rate=48000:duration=1",
                "-c:v",
                "libx264",
                "-preset",
                "ultrafast",
                "-pix_fmt",
                "yuv420p",
                "-c:a",
                "aac",
                "-ac",
                "2",
                "-shortest",
                str(source),
            ],
            check=True,
            capture_output=True,
        )
        project = _repeated_project(source, args.repeats_per_track)
        original = hashlib.sha256(source.read_bytes()).hexdigest()
        fps = FrameRatePolicy(
            choice="custom",
            custom_rate=Fraction(60),
            target_rate=Fraction(60),
            backend=args.backend,
            enhancement_enabled=True,
        )
        for trial in range(args.trials):
            counts = {"extraction": 0, "interpolation": 0, "restoration": 0}
            timings = dict.fromkeys(counts, 0.0)
            input_counts: list[int] = []
            completed_backends: list[str] = []
            with ExitStack() as stack:
                for module in {video, baseline}:
                    for name, kind in (
                        ("_extract_block", "extraction"),
                        ("run_source_interpolation", "interpolation"),
                        ("_run_rve_restoration", "restoration"),
                    ):
                        original_function = getattr(module, name)

                        def traced(
                            *a,
                            _fn=original_function,
                            _kind=kind,
                            _counts=counts,
                            _timings=timings,
                            _backends=completed_backends,
                            **kw,
                        ):
                            started = time.perf_counter()
                            _counts[_kind] += 1
                            try:
                                result = _fn(*a, **kw)
                                if _kind == "interpolation":
                                    _backends.append(kw["backend"])
                                return result
                            finally:
                                _timings[_kind] += time.perf_counter() - started

                        stack.enter_context(patch.object(module, name, traced))
                build = (
                    baseline._build_render_command
                    if args.strategy == "baseline"
                    else video._build_render_command
                )

                def build_traced(*a, _build=build, _inputs=input_counts, **kw):
                    if args.strategy == "deduplicated":
                        kw["reuse_inputs"] = False
                    command = _build(*a, **kw)
                    _inputs.append(command.count("-i"))
                    return command

                if args.strategy == "baseline":
                    if baseline is video:
                        stack.enter_context(
                            patch.object(
                                video.VideoPreparationIdentity,
                                "cache_key",
                                property(lambda item: item.block_id),
                            )
                        )
                    else:

                        def prepare_baseline(*a, **kw):
                            kw.pop("preparations", None)
                            return baseline._prepare_assets(*a, **kw)

                        def stages_baseline(*a, **kw):
                            kw.pop("preparations", None)
                            path, verified = baseline_av._render_verified_stages(*a, **kw)
                            return path, av._VerifiedMux(**vars(verified))

                        stack.enter_context(
                            patch.object(video, "_prepare_assets", prepare_baseline)
                        )
                        stack.enter_context(
                            patch.object(av, "_render_verified_stages", stages_baseline)
                        )
                stack.enter_context(patch.object(video, "_build_render_command", build_traced))
                destination = root / f"{args.strategy}-{trial}.mp4"
                plan = av.plan_project_av(
                    project,
                    destination,
                    frame_rate_policy=fps,
                    upscale_policy=UpscalePolicy(enhancement_enabled=args.upscale),
                )
                started = time.perf_counter()
                preparations = (
                    RenderPreparations(root / f"cache-{trial}")
                    if args.strategy in {"optimized", "resume"}
                    else None
                )
                cancelled_attempt = None
                if args.strategy == "resume":
                    cancelled_attempt = _cancelled_attempt(
                        args,
                        plan,
                        root / f"cache-{trial}",
                        counts,
                        timings,
                        input_counts,
                        completed_backends,
                    )
                    started = time.perf_counter()
                result = av.render_project_av(plan, preparations=preparations)
                wall = time.perf_counter() - started
                decoded = subprocess.run(
                    [
                        ffmpeg_path,
                        "-v",
                        "error",
                        "-i",
                        str(destination),
                        "-map",
                        "0:v",
                        "-f",
                        "framemd5",
                        "-",
                    ],
                    check=True,
                    capture_output=True,
                ).stdout
                frames = b"\n".join(
                    line for line in decoded.splitlines() if not line.startswith(b"#")
                )
                results.append(
                    {
                        "trial": trial,
                        "wall_seconds": wall,
                        "stage_seconds": timings,
                        "calls": counts,
                        "composition_inputs": input_counts,
                        "completed_backends": completed_backends,
                        "frames": result.actual_frames,
                        "decoded_frame_hash": hashlib.sha256(frames).hexdigest(),
                        "source_preserved": hashlib.sha256(source.read_bytes()).hexdigest()
                        == original,
                        "processing_fallbacks": result.processing_fallbacks,
                        "cancelled_attempt": cancelled_attempt,
                    }
                )
    return {
        "strategy": args.strategy,
        "backend": args.backend,
        "repeats_per_track": args.repeats_per_track,
        "upscale_enabled": args.upscale,
        "results": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-video", type=Path)
    parser.add_argument("--baseline-av", type=Path)
    parser.add_argument(
        "--strategy",
        choices=("baseline", "deduplicated", "shared-inputs", "optimized", "resume"),
        required=True,
    )
    parser.add_argument("--resume-after", default="video composition")
    parser.add_argument("--backend", default="ffmpeg-minterpolate")
    parser.add_argument("--trials", type=int, default=3)
    parser.add_argument("--repeats-per-track", type=int, default=1)
    parser.add_argument("--upscale", action="store_true")
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    if bool(args.baseline_video) != bool(args.baseline_av):
        parser.error("Supply both preserved baseline modules or neither")
    if args.trials < 1:
        parser.error("--trials must be positive")
    if args.repeats_per_track < 1:
        parser.error("--repeats-per-track must be positive")
    result = run(args)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
