#!/usr/bin/env python3
"""EXPERIMENTAL video-only architecture comparison; never a production backend.

Use --help for the protocol. Tiles are the actual compositor's cropped slot
outputs (including triplicate), NOT independently rendered full-canvas reels.
Temporal shards trim exact frames from the current graph, so later shards still
decode/render the preceding prefix. This deliberately conservative first
comparator does not claim efficient source seeking or dynamic-layout support.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import platform
import re
import shutil
import statistics
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from framestudio.export_types import ExportExecutionError  # noqa: E402
from framestudio.media import probe_media  # noqa: E402
from framestudio.model import Project, Segment, TriplicateGroup, VisualTransform  # noqa: E402
from framestudio.render_preparations import RenderPreparations  # noqa: E402
from framestudio.upscale_policy import UpscalePolicy  # noqa: E402
from framestudio.video_compositor import _build_render_command, plan_project_video  # noqa: E402
from framestudio.video_compositor import _sha256 as sha256  # noqa: E402

LABEL = re.compile(r"\[([^\]]+)\]")
RATE = 30


def frame_chunks(frames: int, count: int) -> tuple[tuple[int, int], ...]:
    if count < 1 or frames < count:
        raise ValueError("Chunk count must be between one and the output frame count")
    lengths = [frames // count + (index < frames % count) for index in range(count)]
    boundaries = [0]
    for length in lengths:
        boundaries.append(boundaries[-1] + length)
    return tuple(zip(boundaries[:-1], boundaries[1:], strict=True))


def counterbalanced(candidates: tuple[str, ...], trial: int) -> tuple[str, ...]:
    shift = trial % len(candidates)
    return candidates[shift:] + candidates[:shift]


def graph_dependencies(graph: str, label: str) -> str:
    """Retain complete multi-output filters, then the requested ancestry only."""
    filters = graph.split(";")
    producers: dict[str, int] = {}
    dependencies: dict[int, list[str]] = {}
    for index, item in enumerate(filters):
        prefix = re.match(r"^(?:\[[^\]]+\])*", item)
        if prefix is None:
            raise ValueError("Compositor filter has no input label prefix")
        suffix = re.search(r"(?:\[[^\]]+\])+$", item)
        dependencies[index] = LABEL.findall(prefix.group())
        for output in LABEL.findall(suffix.group() if suffix else ""):
            producers[output] = index
    selected: set[int] = set()

    def visit(output: str) -> None:
        if re.fullmatch(r"\d+:v(?::\d+)?", output):
            return
        if output not in producers:
            raise ValueError(f"Compositor graph has no producer for {output}")
        index = producers[output]
        if index not in selected:
            selected.add(index)
            for dependency in dependencies[index]:
                visit(dependency)

    visit(label)
    return ";".join(item for index, item in enumerate(filters) if index in selected)


def run(command: list[str]) -> bytes:
    result = subprocess.run(command, capture_output=True, check=False)
    if result.returncode:
        raise RuntimeError(result.stderr.decode(errors="replace")[-4000:])
    return result.stdout


def bounded(command: list[str], threads: int) -> list[str]:
    result = command[:1] + ["-filter_threads", "1", "-filter_complex_threads", "1"]
    for item in command[1:]:
        if item == "-i":
            result.extend(["-threads", "1"])
        result.append(item)
    return result[:-1] + ["-threads", str(threads), result[-1]]


def lossless_command(command: list[str], graph: str, output: Path, frames: int) -> list[str]:
    prefix = command[: command.index("-filter_complex")]
    return prefix + [
        "-filter_complex",
        graph,
        "-map",
        "[vout]",
        "-an",
        "-r",
        str(RATE),
        "-frames:v",
        str(frames),
        "-c:v",
        "ffv1",
        "-level",
        "3",
        "-pix_fmt",
        "yuv444p",
        str(output),
    ]


def probe(path: Path) -> dict[str, Any]:
    payload = json.loads(
        run(
            [
                "ffprobe",
                "-v",
                "error",
                "-count_frames",
                "-show_streams",
                "-show_format",
                "-of",
                "json",
                str(path),
            ]
        )
    )
    video = payload["streams"][0]
    return {
        "width": int(video["width"]),
        "height": int(video["height"]),
        "rate": video["r_frame_rate"],
        "frames": int(video["nb_read_frames"]),
        "pixel_format": video["pix_fmt"],
        "codec": video["codec_name"],
        "duration": float(payload["format"]["duration"]),
        "audio_streams": sum(stream["codec_type"] == "audio" for stream in payload["streams"]),
    }


def frame_hashes(path: Path) -> list[str]:
    payload = run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-threads",
            "1",
            "-i",
            str(path),
            "-map",
            "0:v:0",
            "-an",
            "-threads",
            "1",
            "-f",
            "framehash",
            "-hash",
            "sha256",
            "-",
        ]
    ).decode()
    return [
        line.split(",")[-1].strip()
        for line in payload.splitlines()
        if line.strip() and not line.startswith("#")
    ]


def _contained(path: Path) -> Path:
    resolved = path.expanduser().resolve()
    if not resolved.is_relative_to(ROOT) or resolved == ROOT:
        raise ValueError("Report and artifact paths must be inside this experiment worktree")
    return resolved


def create_workload(root: Path, frames: int, tracks: int, triplicate_track: int):
    sources: list[Path] = []
    for index in range(tracks):
        source = root / f"source-{index}.mkv"
        run(
            bounded(
                [
                    "ffmpeg",
                    "-v",
                    "error",
                    "-nostdin",
                    "-y",
                    "-f",
                    "lavfi",
                    "-i",
                    f"testsrc2=size=320x180:rate={RATE}",
                    "-vf",
                    f"hue=h={index * 53}",
                    "-frames:v",
                    str(frames),
                    "-an",
                    "-c:v",
                    "ffv1",
                    "-pix_fmt",
                    "yuv420p",
                    str(source),
                ],
                1,
            )
        )
        sources.append(source)
    project = Project.create_synchronized_multi(
        tuple((path, probe_media(path).metadata()) for path in sources),
        project_id="experimental-static-all-active",
    )
    duration = frames / RATE
    for index, source_reference in enumerate(project.sources or (project.source,)):
        track_id = f"track-{index + 1}"
        if index:
            project.timeline.add_track(track_id)
        transform = VisualTransform(zoom=1.15, offset_x=index * 9, offset_y=-index * 5)
        project.timeline.replace_track_blocks(
            track_id,
            (
                Segment.create(
                    0.0,
                    duration,
                    segment_id=f"block-{index}",
                    block_id=f"block-{index}",
                    source_id=source_reference.source_id,
                    track_id=track_id,
                    timeline_start_seconds=0.0,
                    timeline_end_seconds=duration,
                    visual_transform=transform,
                    triplicate=(
                        TriplicateGroup.create(transform, group_id="experimental-triplicate")
                        if index + 1 == triplicate_track
                        else None
                    ),
                ),
            ),
        )
    project.duration_seconds = project.timeline.timeline_duration_seconds
    project.validate()
    plan = plan_project_video(
        project,
        root / "unused-planning-destination.mp4",
        target_rate=RATE,
        upscale_policy=UpscalePolicy(enhancement_enabled=False),
    )
    if len(plan.layout_plan.intervals) != 1 or len(plan.layout_plan.intervals[0].slots) != tracks:
        raise ValueError("Only one static all-active layout is supported")
    return plan, sources


def final_filters(plan, pixel_format="yuv420p", label="vout") -> str:
    return (
        f"format={pixel_format},"
        f"settb=expr={plan.target_rate.denominator}/{plan.target_rate.numerator},"
        f"setpts=N[{label}]"
    )


def command_parts(plan, output: Path, threads: int):
    command = _build_render_command(plan, {}, output=output, ffmpeg_path="ffmpeg")
    graph = command[command.index("-filter_complex") + 1]
    if not graph.endswith("," + final_filters(plan)):
        raise ValueError(
            "Current compositor graph no longer has the expected final format boundary"
        )
    return bounded(command, threads), graph


def _input_command(inputs: list[Path]) -> list[str]:
    return [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-nostdin",
        "-y",
        *[item for path in inputs for item in ("-i", str(path))],
    ]


def _final_command(inputs: list[Path], graph: str, baseline: list[str], threads: int):
    # Preserve the baseline's exact final encoder options, including its default CRF.
    suffix = baseline[baseline.index("-map") :]
    return bounded(_input_command(inputs) + ["-filter_complex", graph] + suffix, threads)


def _slot_label(index: int, slot) -> str:
    return f"i0s{index}trip" if slot.is_triplicate else f"i0s{index}c0"


def make_jobs(plan, kind: str, chunks: int, threads: int, output: Path):
    baseline, graph = command_parts(plan, output, threads)
    interval = plan.layout_plan.intervals[0]
    windows = (
        frame_chunks(plan.expected_frames, chunks)
        if kind != "tracks"
        else ((0, plan.expected_frames),)
    )
    jobs: list[dict[str, Any]] = []
    if kind in ("tracks", "track-chunks"):
        for chunk_index, (start, end) in enumerate(windows):
            for index, slot in enumerate(interval.slots):
                label = _slot_label(index, slot)
                branch = graph_dependencies(graph, label)
                branch += (
                    f";[{label}]trim=end_frame={plan.expected_frames},"
                    f"tpad=stop_mode=clone:stop={plan.expected_frames},"
                    f"trim=start_frame={start}:end_frame={end},setpts=PTS-STARTPTS[vout]"
                )
                jobs.append(
                    {
                        "label": f"chunk-{chunk_index}-track-{index}",
                        "graph": branch,
                        "frames": end - start,
                        "width": slot.slot.width,
                        "height": slot.slot.height,
                    }
                )
    elif kind == "chunks":
        full_graph = graph.removesuffix(final_filters(plan)) + final_filters(
            plan, pixel_format="yuv444p", label="full"
        )
        for index, (start, end) in enumerate(windows):
            jobs.append(
                {
                    "label": f"chunk-{index}",
                    "graph": full_graph
                    + (
                        f";[full]trim=start_frame={start}:end_frame={end},setpts=PTS-STARTPTS[vout]"
                    ),
                    "frames": end - start,
                    "width": 1920,
                    "height": 1080,
                }
            )
    else:
        raise ValueError(f"Unsupported architecture: {kind}")
    return baseline, graph, jobs, windows


def assembly_graph(plan, kind: str, windows, graph: str) -> str:
    if kind == "chunks":
        labels = "".join(f"[{index}:v]" for index in range(len(windows)))
        return f"{labels}concat=n={len(windows)}:v=1:a=0," + final_filters(plan)
    slots = plan.layout_plan.intervals[0].slots
    # Reuse the original placement, frame padding, concatenation and format boundary.
    suffix = graph[
        graph.index(";" + "".join(f"[{_slot_label(i, slot)}]" for i, slot in enumerate(slots))) :
    ].lstrip(";")
    if kind == "tracks":
        for index, slot in enumerate(slots):
            suffix = suffix.replace(f"[{_slot_label(index, slot)}]", f"[{index}:v]")
        return suffix
    filters: list[str] = []
    for chunk_index, (start, end) in enumerate(windows):
        labels = "".join(f"[{chunk_index * len(slots) + index}:v]" for index in range(len(slots)))
        if len(slots) > 1:
            layout = "|".join(f"{slot.slot.x}_{slot.slot.y}" for slot in slots)
            filters.append(
                f"{labels}xstack=inputs={len(slots)}:layout={layout}:fill=black"
                f",format=yuv444p,trim=end_frame={end - start},"
                f"setpts=PTS-STARTPTS[chunk{chunk_index}]"
            )
        else:
            filters.append(f"{labels}format=yuv444p,setpts=PTS-STARTPTS[chunk{chunk_index}]")
    labels = "".join(f"[chunk{index}]" for index in range(len(windows)))
    filters.append(f"{labels}concat=n={len(windows)}:v=1:a=0,format=yuv420p[vout]")
    return ";".join(filters)


def materialize_job(cache_root: Path, job, baseline, threads: int, identity, cancel_event=None):
    cache = RenderPreparations(cache_root, cancel_event=cancel_event)
    request = {
        **identity,
        "graph": job["graph"],
        "frames": job["frames"],
        "codec": "ffv1-level3-yuv444p",
        "threads": threads,
    }

    def produce(path: Path):
        run(bounded(lossless_command(baseline, job["graph"], path, job["frames"]), threads))

    def validate(path: Path):
        metadata = probe(path)
        for key in ("frames", "width", "height"):
            if metadata[key] != job[key]:
                raise ValueError(f"Invalid {job['label']} checkpoint: {key}")
        if metadata["pixel_format"] != "yuv444p" or metadata["codec"] != "ffv1":
            raise ValueError("Checkpoint must be lossless yuv444p FFV1")
        return {**metadata, "frame_hashes": frame_hashes(path)}

    started = time.perf_counter()
    path = cache.materialize("experimental-video-shard", request, produce, validate, suffix=".mkv")
    return {
        "path": path,
        "seconds": time.perf_counter() - started,
        "hits": cache.hits,
        "misses": cache.misses,
        "sha256": sha256(path),
    }


def render_row(plan, candidate: str, trial: int, root: Path, args, identity):
    kind, _, worker_text = candidate.partition(":")
    workers = int(worker_text) if worker_text else 1
    directory = root / f"trial-{trial}-{kind}-{workers}"
    directory.mkdir()
    output = directory / "final.mp4"
    baseline, graph = command_parts(plan, output, args.threads)
    row: dict[str, Any] = {
        "candidate": candidate,
        "trial": trial,
        "status": "failed",
        "output": str(output),
        "input_identity": identity,
        "intermediate_bytes": 0,
        "timing": {},
        "budget": {
            "max_concurrent_ffmpeg_processes": workers,
            "decoder_threads_per_input": 1,
            "filter_threads": 1,
            "filter_complex_threads": 1,
            "encoder_threads_per_process": args.threads,
            "note": "Explicit FFmpeg codec/filter budgets; not a bound on auxiliary OS threads.",
        },
    }
    started = time.perf_counter()
    try:
        if kind == "monolithic":
            run(baseline)
            row["timing"]["prepare_seconds"] = 0.0
            row["timing"]["encode_assembly_seconds"] = time.perf_counter() - started
            row["ffmpeg_render_processes"] = 1
        else:
            baseline, graph, jobs, windows = make_jobs(
                plan, kind, args.segments, args.threads, output
            )
            prep_start = time.perf_counter()
            with ThreadPoolExecutor(max_workers=workers) as pool:
                prepared = list(
                    pool.map(
                        lambda job: materialize_job(
                            directory / "checkpoints", job, baseline, args.threads, identity
                        ),
                        jobs,
                    )
                )
            row["timing"]["prepare_seconds"] = time.perf_counter() - prep_start
            row["timing"]["shard_seconds"] = [item["seconds"] for item in prepared]
            paths = [item["path"] for item in prepared]
            row["intermediate_bytes"] = sum(path.stat().st_size for path in paths)
            row["checkpoint_bytes_including_manifests"] = sum(
                path.stat().st_size
                for path in (directory / "checkpoints").rglob("*")
                if path.is_file()
            )
            row["checkpoints"] = [{**item, "path": str(item["path"])} for item in prepared]
            final_graph = assembly_graph(plan, kind, windows, graph)
            encode_start = time.perf_counter()
            run(_final_command(paths, final_graph, baseline, args.threads))
            row["timing"]["encode_assembly_seconds"] = time.perf_counter() - encode_start
            row["ffmpeg_render_processes"] = len(jobs) + 1
        row["timing"]["render_wall_seconds"] = time.perf_counter() - started
        verify_start = time.perf_counter()
        row["metadata"] = probe(output)
        row["frame_hashes"] = frame_hashes(output)
        row["timing"]["final_verification_seconds"] = time.perf_counter() - verify_start
        row["output_bytes"] = output.stat().st_size
        row["status"] = "pending-oracle"
    except (OSError, RuntimeError, ValueError) as error:
        row["error"] = str(error)
        row["timing"]["failed_wall_seconds"] = time.perf_counter() - started
    return row


def recovery_demo(plan, root: Path, args, identity, oracle_hashes) -> dict[str, Any]:
    """Controlled coordinator interruption after one committed shard, not SIGKILL."""
    output = root / "recovery-final.mp4"
    baseline, graph, jobs, windows = make_jobs(
        plan,
        "chunks",
        args.segments,
        args.threads,
        output,
    )
    cache_root = root / "recovery-checkpoints"
    event = threading.Event()
    first = materialize_job(cache_root, jobs[0], baseline, args.threads, identity, event)
    event.set()
    cancellation_observed = False
    try:
        materialize_job(cache_root, jobs[-1], baseline, args.threads, identity, event)
    except ExportExecutionError as error:
        if str(error) != "Export cancelled":
            raise
        cancellation_observed = True
    original = (first["path"].stat().st_mtime_ns, first["sha256"])
    second = materialize_job(cache_root, jobs[0], baseline, args.threads, identity)
    remaining = [
        materialize_job(cache_root, job, baseline, args.threads, identity) for job in jobs[1:]
    ]
    paths = [second["path"], *(item["path"] for item in remaining)]
    run(
        _final_command(
            paths, assembly_graph(plan, "chunks", windows, graph), baseline, args.threads
        )
    )
    output_matches = frame_hashes(output) == oracle_hashes
    return {
        "mode": "controlled stop after finished shard; fresh coordinator; no mid-process kill",
        "cancellation_observed": cancellation_observed,
        "reused_finished_artifact": second["hits"] == 1 and second["misses"] == 0,
        "same_artifact_hash": original == (second["path"].stat().st_mtime_ns, second["sha256"]),
        "remaining_shards_completed": len(remaining),
        "resumed_output_matches_oracle": output_matches,
        "first_seconds": first["seconds"],
        "resume_lookup_seconds": second["seconds"],
    }


def run_benchmark(args) -> dict[str, Any]:
    if args.tracks not in (1, 2, 3, 4) or not math.isfinite(args.duration) or args.duration <= 0:
        raise ValueError("Use 1–4 tracks and a positive finite duration")
    if args.trials < 1 or args.threads < 1:
        raise ValueError("Trials and encoder threads must be positive")
    workers = tuple(dict.fromkeys(int(item) for item in args.workers.split(",")))
    if not workers or any(item not in (1, 2, 3) for item in workers):
        raise ValueError("Workers must be a comma-separated subset of 1,2,3")
    if args.triplicate_track < 0 or args.triplicate_track > args.tracks:
        raise ValueError("Triplicate track must be zero (disabled) or an existing 1-based track")
    frames = max(1, round(args.duration * RATE))
    frame_chunks(frames, args.segments)
    artifact_root, report_path = _contained(args.artifact_root), _contained(args.report)
    if report_path.suffix != ".json":
        raise ValueError(
            "The experiment report must be a JSON file, not a source/configuration path"
        )
    artifact_root.mkdir(parents=True, exist_ok=True)
    # Never overwrite an earlier experiment or silently reuse a warm application cache.
    root = artifact_root / f"run-{time.time_ns()}"
    root.mkdir()
    generation_start = time.perf_counter()
    plan, sources = create_workload(root, frames, args.tracks, args.triplicate_track)
    generation_seconds = time.perf_counter() - generation_start
    identity = {
        "source_files": {path.name: sha256(path) for path in sources},
        "decoded_source_frames": {path.name: frame_hashes(path) for path in sources},
        "preparation": "none; identical lossless native sources for all rows",
        "compositor_sha256": sha256(ROOT / "framestudio/video_compositor.py"),
        "harness_sha256": sha256(Path(__file__)),
    }
    kinds = ("tracks", "chunks", "track-chunks") if args.combined else ("tracks", "chunks")
    candidates = ("monolithic",) + tuple(f"{kind}:{worker}" for kind in kinds for worker in workers)
    rows: list[dict[str, Any]] = []
    for trial in range(args.trials):
        for candidate in counterbalanced(candidates, trial):
            row = render_row(plan, candidate, trial, root, args, identity)
            row["sources_after"] = {path.name: sha256(path) for path in sources}
            rows.append(row)
    for row in rows:
        oracle = next(
            item
            for item in rows
            if item["trial"] == row["trial"] and item["candidate"] == "monolithic"
        )
        if row["status"] != "pending-oracle":
            continue
        meta = row["metadata"]
        verification = {
            "frames": meta["frames"],
            "exact_frame_hashes": (
                len(row["frame_hashes"]) == frames
                and row["frame_hashes"] == oracle.get("frame_hashes")
            ),
            "metadata_matches_oracle": all(
                meta[key] == oracle.get("metadata", {}).get(key)
                for key in (
                    "width",
                    "height",
                    "rate",
                    "frames",
                    "duration",
                    "pixel_format",
                    "codec",
                )
            ),
            "expected_output": (
                meta["width"] == 1920
                and meta["height"] == 1080
                and meta["frames"] == frames
                and meta["rate"] == "30/1"
                and meta["pixel_format"] == "yuv420p"
                and meta["codec"] == "h264"
                and meta["audio_streams"] == 0
            ),
            "source_hashes_unchanged": row["sources_after"] == identity["source_files"],
        }
        row["verification"] = verification
        row["status"] = (
            "eligible"
            if all(value for key, value in verification.items() if key != "frames")
            else "ineligible"
        )
    medians: dict[str, Any] = {}
    baseline_times = [
        row["timing"]["render_wall_seconds"]
        for row in rows
        if row["candidate"] == "monolithic" and row["status"] == "eligible"
    ]
    for candidate in candidates:
        accepted = [
            row for row in rows if row["candidate"] == candidate and row["status"] == "eligible"
        ]
        times = [row["timing"]["render_wall_seconds"] for row in accepted]
        median = statistics.median(times) if times else None
        medians[candidate] = {
            "eligible_trials": len(times),
            "required_trials": args.trials,
            "median_render_wall_seconds": median,
            "median_prepare_seconds": statistics.median(
                row["timing"]["prepare_seconds"] for row in accepted
            )
            if times
            else None,
            "median_encode_assembly_seconds": statistics.median(
                row["timing"]["encode_assembly_seconds"] for row in accepted
            )
            if times
            else None,
            "speedup_vs_monolithic": (
                statistics.median(baseline_times) / median
                if median and len(times) == args.trials and len(baseline_times) == args.trials
                else None
            ),
        }
    recovery: dict[str, Any] = {"status": "not-requested"}
    if args.recovery_demo:
        try:
            oracle = next(row for row in rows if row["candidate"] == "monolithic")
            recovery = recovery_demo(plan, root, args, identity, oracle.get("frame_hashes"))
            recovery["status"] = (
                "verified"
                if all(
                    recovery[key]
                    for key in (
                        "cancellation_observed",
                        "reused_finished_artifact",
                        "same_artifact_hash",
                        "resumed_output_matches_oracle",
                    )
                )
                else "failed"
            )
        except (OSError, RuntimeError, ValueError) as error:
            recovery = {"status": "failed", "error": str(error)}
    report = {
        "experimental": True,
        "production_backend": False,
        "workload": "synthetic static all-active synchronized tracks; VIDEO ONLY",
        "representativeness": {
            "reference_shape": "3 tracks / 114 blocks / 54 unique ranges / 116 intervals / 493 seconds",
            "not_reproduced": "Dynamic layouts, gaps, late source seeking, mixed FPS, audio, enhancements.",
        },
        "protocol": {
            "frames": frames,
            "tracks": args.tracks,
            "segments": args.segments,
            "trials": args.trials,
            "requested_duration_seconds": args.duration,
            "effective_duration_seconds": frames / RATE,
            "triplicate_track": args.triplicate_track,
            "final_encoder": "current compositor libx264 ultrafast default CRF / yuv420p, single final encode",
            "oracle_scope": (
                "controlled video-only oracle with identical explicit encoder threads in every row; "
                "not the production auto-thread baseline"
            ),
            "intermediates": "FFV1 level 3 yuv444p; never delivery-encoded chunks",
            "cache": "fresh application checkpoint namespace per row; OS page cache uncontrolled",
            "recovery_limit": "persisted shard checkpoints and controlled cancel/reopen demo; no general resume CLI",
            "counterbalance": "cyclic rotation; 3 trials default, not a full Latin square for >3 candidates",
            "temporal_limit": "exact frame slicing after full graph; each shard renders preceding prefix",
            "timing": "render wall includes preparation validation/checkpoint I/O and final encoding, excludes final verification",
            "assembly": "lossless decoded tiles/chunks joined as raw pixels before ONE delivery encode",
            "unmeasured": ["GPU", "peak RSS", "disk cold", "audio", "mid-process crash recovery"],
        },
        "baseline": {
            "revision": run(["git", "-C", str(ROOT), "rev-parse", "HEAD"]).decode().strip(),
            "tracked_diff_sha256": hashlib.sha256(
                run(["git", "-C", str(ROOT), "diff", "--binary", "HEAD"])
            ).hexdigest(),
            "status": run(["git", "-C", str(ROOT), "status", "--short"]).decode().splitlines(),
            "ffmpeg_version": run(["ffmpeg", "-version"]).decode().splitlines()[0],
            "effective_python_source_hashes": {
                str(path.relative_to(ROOT)): sha256(path)
                for path in sorted((ROOT / "framestudio").glob("*.py"))
            },
            "python_version": platform.python_version(),
            "platform": platform.system() + "/" + platform.machine(),
            "logical_cpus": os.cpu_count(),
        },
        "generation_seconds": generation_seconds,
        "input_identity": identity,
        "artifact_root": str(root),
        "rows": rows,
        "medians": medians,
        "recovery": recovery,
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    pending = report_path.with_name(report_path.name + ".pending")
    pending.write_text(json.dumps(report, indent=2) + "\n")
    pending.replace(report_path)
    return report


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    result.add_argument("--duration", type=float, default=1.0, help="seconds, rounded to 30 FPS")
    result.add_argument("--tracks", type=int, default=3, help="1–4 simultaneous static tracks")
    result.add_argument(
        "--segments",
        "--segment-count",
        type=int,
        default=3,
        help="exact-frame temporal shard count",
    )
    result.add_argument("--workers", default="1,2,3", help="comma-separated shard process limits")
    result.add_argument(
        "--threads", type=int, default=1, help="encoder threads per process, same final encoder"
    )
    result.add_argument(
        "--trials", type=int, default=3, help="counterbalanced fresh-cache repetitions"
    )
    result.add_argument(
        "--combined", action="store_true", help="also shard tracks AND time before final encode"
    )
    result.add_argument(
        "--triplicate-track",
        type=int,
        default=0,
        help="optional 1-based track with odd subslot widths",
    )
    result.add_argument(
        "--recovery-demo",
        action="store_true",
        help="reopen cache after a finished shard and complete remaining shards",
    )
    result.add_argument(
        "--artifact-root", type=Path, default=ROOT / "benchmarks/results/multitrack-architecture"
    )
    result.add_argument(
        "--report", type=Path, default=ROOT / "benchmarks/results/multitrack-architecture.json"
    )
    return result


def main() -> int:
    args = parser().parse_args()
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        print("ffmpeg and ffprobe are required", file=sys.stderr)
        return 2
    try:
        report = run_benchmark(args)
    except (OSError, RuntimeError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 2
    print(json.dumps({"report": str(args.report), "medians": report["medians"]}, indent=2))
    return (
        0
        if (
            all(row["status"] == "eligible" for row in report["rows"])
            and report["recovery"]["status"] != "failed"
        )
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())
