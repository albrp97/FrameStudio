#!/usr/bin/env python3
"""Sequential, exact-AV multitrack export comparisons (TICKET-102 experiment).

No production code is changed. Supply the current baseline checkout and optional
isolated candidate module paths. The baseline PACKAGE is snapshotted, including
uncommitted Python files, before importing anything; baseline dedup/input sharing
remain enabled. Each row runs in a new interpreter with the correct package
context. Artifacts, commands, failures and decoded hashes are retained.

Example (start only after other workers/exports have stopped):
  python3 benchmarks/multitrack_render_benchmark.py \
    --baseline-root /path/to/current/FrameStudio \
    --video-candidate /path/to/video-worktree/framestudio/video_compositor.py \
    --audio-candidate /path/to/audio-worktree/framestudio/audio_compositor.py \
    --tracks 3 --repeats 2 --duration .5 --trials 3 \
    --thread-budgets 1,2,4,6,auto --decoder-threads 1,2,auto --report bench-report.json \
    --artifact-root bench-artifacts

--duration is seconds PER source range; --range-count distinct adjacent ranges
are reused --repeats times on each track. --intervals overrides this segment
count per track; --source-count cycles source identities across segments/tracks.
Use --source-count 35 --intervals 38 --tracks 3 --stagger-frames 1 for a
114-block/116-interval zero-triplicate stress graph (not a faithful
reconstruction of an actual project).
--source-start 113 --source-duration 120 adds a long-GOP/B-frame decoded-prefix
fixture. seek/combined-seek are EXPERIMENTAL, restricted to this generated
zero-origin, integer-CFR fixture, not production media eligibility.
Default --seek-mode copyts preserves video timestamps/original trim using
-noaccurate_seek/-copyts/-start_at_zero; audio remains baseline (sample-index
trims cannot be rebased merely by preserving PTS). --seek-mode rebase instead
accurately seeks both streams and subtracts the synthetic fixture offset from
video trim seconds/audio trim samples. Both modes require exact AV hashes.
Lossless temporal/per-track architecture comparisons live in the separate
multitrack_architecture_benchmark.py harness.
Exact final decoded video AND PCM equality is mandatory even for experiments.
nvdec/combined-nvdec (and seek-nvdec/combined-seek-nvdec) only add input
``-hwaccel cuda``. Software-returning decode, CPU filters and libx264 remain;
GPU decode failure stays a failed row, never a silent CPU or quality fallback.

Fresh means empty application cache, OS page cache uncontrolled/warm; no privileged
cache dropping. checkpoint-warm and resume are separate rows and never determine
the fresh winner. Existing AV checkpoint/cancellation mechanisms provide
warm/resume observations. No automatic
production policy is changed, and no perceptual-quality claim replaces equality.
The command exits nonzero if no exact fresh baseline/winner exists; failures
remain in the report. Include fresh alongside warm modes for selection runs.
Staggered tracks exposed a legacy baseline concat timestamp defect at one-frame
layout intervals: inferred zero durations overlap PTS and CFR output drops frames.
Such valid fixtures remain failed comparisons; no padding or relaxed frame gate
is substituted for the final-clock correctness repair.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import importlib.util
import inspect
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
import traceback
from contextlib import ExitStack
from fractions import Fraction
from pathlib import Path
from typing import Any
from unittest.mock import patch

STRATEGIES = (
    "baseline",
    "video",
    "audio",
    "combined",
    "seek",
    "combined-seek",
    "nvdec",
    "combined-nvdec",
    "seek-nvdec",
    "combined-seek-nvdec",
)
EXPERIMENTAL = set(STRATEGIES) - {"baseline", "video", "audio", "combined"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    buffer = bytearray(1024 * 1024)
    with path.open("rb") as stream:
        while count := stream.readinto(buffer):
            digest.update(memoryview(buffer)[:count])
    return digest.hexdigest()


def trial_order(rows: list, trial: int) -> list:
    """Cyclic Latin-square positions; invert each complete square."""
    size = len(rows)
    if not size:
        return []
    base = list(reversed(rows)) if (trial // size) % 2 else list(rows)
    offset = trial % size
    return base[offset:] + base[:offset]


def thread_command(command: list[str], budget: int, decoder_budget: int = 0) -> list[str]:
    if Path(command[0]).name != "ffmpeg":
        return list(command)
    if not budget and not decoder_budget:
        return list(command)
    # Decoder options are input-scoped; NEVER alter final encoder threading.
    result = [command[0]]
    if budget:
        result += ["-filter_threads", str(budget), "-filter_complex_threads", str(budget)]
    for argument in command[1:]:
        if argument == "-i" and decoder_budget:
            result.extend(["-threads", str(decoder_budget)])
        result.append(argument)
    return result


def nvdec_command(command: list[str]) -> list[str]:
    """Decode only: no GPU output format, scaling or NVENC substitution."""
    result = []
    for argument in command:
        if argument == "-i":
            result.extend(["-hwaccel", "cuda"])
        result.append(argument)
    if "-i" not in command:
        raise ValueError("NVDEC probe requires video inputs")
    return result


def frame_signature(payload: bytes) -> tuple[str, int]:
    # Hash decoded frame bytes/checksums in order, not mux timestamps or headers.
    hashes = [
        line.rsplit(b",", 1)[-1].strip()
        for line in payload.splitlines()
        if line.strip() and not line.startswith(b"#")
    ]
    return hashlib.sha256(b"\n".join(hashes)).hexdigest(), len(hashes)


def seek_fixture_command(
    command: list[str], source: Path, offset: float, mode: str = "copyts"
) -> list[str]:
    """Only called for the known generated fixture; never a CFR production guard."""
    result = list(command)
    inputs = [result[index + 1] for index, value in enumerate(result) if value == "-i"]
    if not inputs or any(Path(value).resolve() != source.resolve() for value in inputs):
        raise ValueError("experimental seek requires only the generated fixture inputs")
    if mode == "copyts":
        result[1:1] = ["-copyts", "-start_at_zero"]
        for index in reversed([i for i, value in enumerate(result) if value == "-i"]):
            result[index:index] = ["-ss", f"{offset:.9f}", "-noaccurate_seek"]
        return result
    if mode != "rebase":
        raise ValueError("unknown synthetic fixture seek mode")
    index = result.index("-filter_complex") + 1
    graph = result[index]
    samples = round(offset * 48000)

    def video_trim(match):
        start, end = map(float, match.groups())
        if start < offset - 1e-8:
            raise ValueError("trim precedes fixture seek boundary")
        return f"trim=start={start - offset:.9f}:end={end - offset:.9f}"

    def audio_trim(match):
        start, end = map(int, match.groups())
        if start < samples:
            raise ValueError("audio trim precedes fixture seek boundary")
        return f"atrim=start_sample={start - samples}:end_sample={end - samples}"

    graph, videos = re.subn(r"(?<!a)trim=start=([\d.]+):end=([\d.]+)", video_trim, graph)
    graph, audios = re.subn(r"atrim=start_sample=(\d+):end_sample=(\d+)", audio_trim, graph)
    if not videos + audios:
        raise ValueError("unsupported fixture trim syntax")
    result[index] = graph
    for index in reversed([i for i, value in enumerate(result) if value == "-i"]):
        result[index:index] = ["-ss", f"{offset:.9f}"]
    return result


class ProcessSampler:
    """Linux sampled process-tree telemetry; explicitly NOT cumulative accounting."""

    def __init__(self):
        self.stop = threading.Event()
        self.peak_rss = 0
        self.cpu = {}
        self.available = Path("/proc/self/stat").exists()
        self.thread = threading.Thread(target=self._sample, daemon=True)

    def _sample(self):
        while not self.stop.is_set():
            table = {}
            if not self.available:
                return
            for path in Path("/proc").glob("[0-9]*/stat"):
                try:
                    data = path.read_text().rsplit(")", 1)[1].split()
                    table[int(path.parent.name)] = (
                        int(data[1]),
                        int(data[11]) + int(data[12]),
                        max(0, int(data[21])) * os.sysconf("SC_PAGE_SIZE"),
                    )
                except (OSError, ValueError, IndexError):
                    continue
            tree = {os.getpid()}
            while True:
                expanded = tree | {pid for pid, (parent, _, _) in table.items() if parent in tree}
                if expanded == tree:
                    break
                tree = expanded
            self.peak_rss = max(self.peak_rss, sum(table[pid][2] for pid in tree if pid in table))
            for pid in tree:
                if pid in table:
                    self.cpu[pid] = max(self.cpu.get(pid, 0), table[pid][1])
            self.stop.wait(0.05)

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *_):
        self.stop.set()
        self.thread.join()

    def report(self):
        return {
            "available": self.available,
            "scope": "worker plus descendants, sampled /proc every 50ms; RSS is summed "
            "resident memory (shared pages double-counted), not peak allocation; "
            "CPU is observed lifetime ticks, short-lived children may be missed",
            "sampled_peak_tree_rss_bytes": self.peak_rss if self.available else None,
            "observed_process_cpu_seconds": (
                sum(self.cpu.values()) / os.sysconf("SC_CLK_TCK") if self.available else None
            ),
            "observed_processes": len(self.cpu),
        }


def gpu_snapshot() -> dict:
    executable = shutil.which("nvidia-smi")
    if executable is None:
        return {"available": False, "reason": "nvidia-smi unavailable", "scope": "snapshot only"}
    try:
        result = subprocess.run(
            [
                executable,
                "--query-gpu=name,driver_version,memory.used,utilization.gpu",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return {
            "available": result.returncode == 0,
            "scope": "snapshot only; NOT an average",
            "csv": result.stdout.strip(),
            "error": result.stderr.strip(),
        }
    except (OSError, subprocess.TimeoutExpired) as error:
        return {"available": False, "scope": "snapshot only", "reason": str(error)}


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(f"framestudio.{name}", path)
    if spec is None or spec.loader is None:
        raise ValueError(f"cannot load module {name}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    setattr(sys.modules["framestudio"], name, module)
    return module


def make_project(sources: list[Path], config: dict):
    from framestudio.media import probe_media
    from framestudio.model import Project, Segment, TriplicateGroup, VisualTransform
    from framestudio.operations import ensure_project_audio_analysis

    project = Project.create_synchronized_multi(
        tuple((source, probe_media(source).metadata()) for source in sources)
    )
    project.project_id = "multitrack-benchmark"
    project_sources = project.sources or (project.source,)
    for index in range(2, config["tracks"] + 1):
        project.timeline.add_track(f"track-{index}")
    duration = config["duration"]
    count = config["intervals"] or config["repeats"] * config["range_count"]
    for track_index, track in enumerate(tuple(project.timeline.tracks or ())):
        segments = []
        stagger = track_index * config.get("stagger_frames", 0) / 30
        for index in range(count):
            start = config["late_start"] + (index % config["range_count"]) * duration
            transform = VisualTransform()
            triplicate = (
                TriplicateGroup.create(transform, group_id=f"group-{track.track_id}-{index}")
                if config["triplicate"]
                else None
            )
            segments.append(
                Segment.create(
                    segment_id=f"{track.track_id}-{index}",
                    track_id=track.track_id,
                    source_id=project_sources[
                        (track_index * count + index) % len(sources)
                    ].source_id,
                    start_seconds=start,
                    end_seconds=start + duration,
                    timeline_start_seconds=index * duration + stagger,
                    timeline_end_seconds=(index + 1) * duration + stagger,
                    visual_transform=transform,
                    triplicate=triplicate,
                )
            )
        project.timeline.replace_track_blocks(track.track_id, tuple(segments))
    ensure_project_audio_analysis(project)
    return project


def decoded_signature(output: Path, directory: Path) -> dict:
    ffprobe_path = shutil.which("ffprobe")
    ffmpeg_path = shutil.which("ffmpeg")
    if ffprobe_path is None or ffmpeg_path is None:
        raise ValueError("FFprobe and FFmpeg are required for decoded integrity checks")
    metadata = json.loads(
        subprocess.run(
            [ffprobe_path, "-v", "error", "-show_streams", "-of", "json", str(output)],
            check=True,
            capture_output=True,
            text=True,
        ).stdout
    )
    videos = [stream for stream in metadata["streams"] if stream["codec_type"] == "video"]
    audios = [stream for stream in metadata["streams"] if stream["codec_type"] == "audio"]
    if len(videos) != 1 or len(audios) != 1:
        raise ValueError("expected exactly one video and one audio stream")
    audio = audios[0]
    if int(audio["channels"]) != 2 or int(audio["sample_rate"]) != 48000:
        raise ValueError("output is not native stereo 48kHz; refusing resampled parity")
    video_hashes = directory / "decoded-video.framemd5"
    subprocess.run(
        [
            ffmpeg_path,
            "-v",
            "error",
            "-threads",
            "1",
            "-i",
            str(output),
            "-map",
            "0:v:0",
            "-an",
            "-pix_fmt",
            "yuv420p",
            "-threads",
            "1",
            "-fps_mode",
            "passthrough",
            "-f",
            "framemd5",
            "-y",
            str(video_hashes),
        ],
        check=True,
        capture_output=True,
    )
    video_hash, frames = frame_signature(video_hashes.read_bytes())
    pcm = directory / "decoded-audio.s32le"
    subprocess.run(
        [
            ffmpeg_path,
            "-v",
            "error",
            "-threads",
            "1",
            "-i",
            str(output),
            "-map",
            "0:a:0",
            "-vn",
            "-c:a",
            "pcm_s32le",
            "-f",
            "s32le",
            "-y",
            str(pcm),
        ],
        check=True,
        capture_output=True,
    )
    return {
        "video_sha256": video_hash,
        "video_frames": frames,
        "audio_sha256": sha256_file(pcm),
        "audio_samples": pcm.stat().st_size // 8,
        "audio_pcm_frames": pcm.stat().st_size // 8,
        "audio_channels": 2,
        "audio_rate": 48000,
        "width": videos[0]["width"],
        "height": videos[0]["height"],
        "video_rate": videos[0]["r_frame_rate"],
        "video_pixel_format": videos[0]["pix_fmt"],
        "video_codec": videos[0]["codec_name"],
        "audio_codec": audio["codec_name"],
        "audio_channel_layout": audio.get("channel_layout"),
        "video_sar": videos[0].get("sample_aspect_ratio"),
        "video_time_base": videos[0]["time_base"],
        "audio_time_base": audio["time_base"],
        "video_hash_scope": "ordered decoded yuv420p frame checksums",
        "audio_hash_scope": "decoded interleaved signed 32-bit LE stereo PCM at 48kHz",
    }


def validate_decoded_counts(signature: dict, expected_frames: int, expected_samples: int) -> None:
    for field, expected in (
        ("video_frames", expected_frames),
        ("audio_pcm_frames", expected_samples),
    ):
        if signature[field] != expected:
            raise ValueError(f"Decoded {field} is {signature[field]}, expected {expected}")


def _worker_modules(config: dict):
    strategy = config["strategy"]
    use_video = strategy == "video" or strategy.startswith("combined")
    use_audio = strategy == "audio" or strategy.startswith("combined")
    if use_video and not config["video_candidate"]:
        return None, None, None, "video candidate module not supplied"
    if use_audio and not config["audio_candidate"]:
        return None, None, None, "audio candidate module not supplied"
    video = load_module(
        "video_compositor",
        Path(config["video_candidate"])
        if use_video
        else Path(config["runtime"]) / "framestudio/video_compositor.py",
    )
    audio = load_module(
        "audio_compositor",
        Path(config["audio_candidate"])
        if use_audio
        else Path(config["runtime"]) / "framestudio/audio_compositor.py",
    )
    av = importlib.import_module("framestudio.av_compositor")
    if (
        use_video
        and "factor_triplicate" not in inspect.signature(video._build_render_command).parameters
    ):
        return None, None, None, "video candidate lacks factor_triplicate API"
    if use_audio and "reuse_inputs" not in inspect.signature(audio._render_command).parameters:
        return None, None, None, "audio candidate lacks reuse_inputs API"
    if "seek" in strategy and (
        config["enhance"] or config["late_start"] <= 0 or len(config["sources"]) != 1
    ):
        return (
            None,
            None,
            None,
            "experimental seek requires one fixture, --source-start > 0, no --enhance; "
            "prepared inputs are intentionally not seek-rewritten",
        )
    return video, audio, av, None


def _process_class(config: dict, calls: list[dict[str, Any]], active_stage: list[str]):
    class TracedProcess(subprocess.Popen):
        def __init__(self, command, *args, **kwargs):
            rewritten = thread_command(list(command), config["budget"], config["decoder_budget"])
            self.record: dict[str, Any] = {
                "argv": rewritten,
                "stage": active_stage[0],
                "inputs": rewritten.count("-i"),
                "output_bytes_at_exit": None,
            }
            self.started = time.perf_counter()
            self.recorded = False
            calls.append(self.record)
            super().__init__(rewritten, *args, **kwargs)

        def _record(self):
            if self.returncode is not None and not self.recorded:
                self.recorded = True
                self.record.update(
                    returncode=self.returncode, wall_seconds=time.perf_counter() - self.started
                )
                path = Path(self.record["argv"][-1])
                if path.is_file():
                    self.record["output_bytes_at_exit"] = path.stat().st_size

        def poll(self):
            result = super().poll()
            self._record()
            return result

        def wait(self, *args, **kwargs):
            result = super().wait(*args, **kwargs)
            self._record()
            return result

        def communicate(self, *args, **kwargs):
            result = super().communicate(*args, **kwargs)
            self._record()
            return result

    return TracedProcess


def _command_wrappers(video, audio, config: dict):
    strategy = config["strategy"]
    use_video = strategy == "video" or strategy.startswith("combined")
    use_audio = strategy == "audio" or strategy.startswith("combined")
    source = Path(config["sources"][0])
    build_video = video._build_render_command
    build_audio = audio._render_command

    def video_command(*args, **kwargs):
        if use_video:
            kwargs["factor_triplicate"] = True
        command = build_video(*args, **kwargs)
        if "seek" in strategy:
            command = seek_fixture_command(
                command, source, config["late_start"], config["seek_mode"]
            )
        if "nvdec" in strategy:
            command = nvdec_command(command)
        return command

    def audio_command(*args, **kwargs):
        if use_audio:
            kwargs["reuse_inputs"] = True
        command, label = build_audio(*args, **kwargs)
        if "seek" in strategy and config["seek_mode"] == "rebase":
            command = seek_fixture_command(command, source, config["late_start"], "rebase")
        return command, label

    return video_command, audio_command


def _timer(active_stage, stage_calls, stage_seconds):
    def timed(function, name):
        def invoke(*args, **kwargs):
            previous = active_stage[0]
            active_stage[0] = name
            started = time.perf_counter()
            stage_calls[name] = stage_calls.get(name, 0) + 1
            try:
                return function(*args, **kwargs)
            finally:
                stage_seconds[name] = stage_seconds.get(name, 0) + time.perf_counter() - started
                active_stage[0] = previous

        return invoke

    return timed


def _warm_cache(av, plan, config, directory, result, calls, stage_seconds, stage_calls):
    from framestudio.render_preparations import RenderPreparations

    mode = config["cache_mode"]
    if mode == "fresh":
        return
    event = threading.Event()

    def cancel_at_checkpoint(progress):
        if progress.stage == "Checkpointed " + config["resume_after"]:
            event.set()

    preflight_start = time.perf_counter()
    preparations = RenderPreparations(
        directory / "application-cache",
        cancel_event=event,
        progress_callback=cancel_at_checkpoint if mode == "resume" else None,
    )
    if mode == "resume":
        try:
            av.render_project_av(plan, cancel_event=event, preparations=preparations)
        except av.AVCompositorExecutionError:
            if not event.is_set():
                raise
        else:
            raise RuntimeError("requested resume checkpoint was not reached")
    else:
        av.render_project_av(plan, preparations=preparations)
        (directory / "output.mp4").unlink()
    result["preflight"] = {
        "wall_seconds": time.perf_counter() - preflight_start,
        "commands": list(calls),
        "stage_seconds": dict(stage_seconds),
    }
    calls.clear()
    stage_seconds.clear()
    stage_calls.clear()


def worker(config: dict) -> dict:
    # Fix all stdlib temp locations BEFORE importing production renderers.
    import tempfile

    directory = Path(config["directory"])
    scratch = directory / "scratch"
    scratch.mkdir()
    os.environ["TMPDIR"] = str(scratch)
    tempfile.tempdir = str(scratch)
    sys.path.insert(0, config["runtime"])
    importlib.import_module("framestudio")
    video, audio, av, reason = _worker_modules(config)
    if reason:
        return {"status": "unsupported", "reason": reason}
    from framestudio.fps_policy import FrameRatePolicy
    from framestudio.render_preparations import RenderPreparations
    from framestudio.upscale_policy import UpscalePolicy

    sources = [Path(path) for path in config["sources"]]
    before = {str(source): sha256_file(source) for source in sources}
    calls: list[dict[str, Any]] = []
    stage_seconds: dict[str, float] = {}
    stage_calls: dict[str, int] = {}
    active_stage = ["planning"]
    timed = _timer(active_stage, stage_calls, stage_seconds)
    video_command, audio_command = _command_wrappers(video, audio, config)
    destination = directory / "output.mp4"
    result: dict[str, Any] = {"status": "failed", "gpu_before": gpu_snapshot()}
    started = time.perf_counter()
    with ExitStack() as stack, ProcessSampler() as sampler:
        stack.enter_context(
            patch.object(subprocess, "Popen", _process_class(config, calls, active_stage))
        )
        stack.enter_context(patch.object(video, "_build_render_command", video_command))
        stack.enter_context(patch.object(audio, "_render_command", audio_command))
        for module, name, stage in (
            (video, "_prepare_assets", "native_preparations"),
            (video, "_extract_block", "extraction"),
            (video, "run_source_interpolation", "interpolation"),
            (av, "render_project_video", "video_total"),
            (av, "render_audio", "audio_total"),
            (av, "_mux_stages", "mux"),
            (av, "_verify_muxed_output", "av_verification"),
        ):
            stack.enter_context(patch.object(module, name, timed(getattr(module, name), stage)))
        try:
            project = timed(make_project, "fixture_analysis")(sources, config)
            policy = FrameRatePolicy(
                choice="custom",
                custom_rate=Fraction(60 if config["enhance"] else 30),
                target_rate=Fraction(60 if config["enhance"] else 30),
                backend="ffmpeg-minterpolate",
                enhancement_enabled=config["enhance"],
            )
            plan = timed(av.plan_project_av, "planning")(
                project,
                destination,
                frame_rate_policy=policy,
                upscale_policy=UpscalePolicy(enhancement_enabled=False),
            )
            result["expected_frames"] = plan.video_plan.expected_frames
            result["expected_audio_samples"] = plan.audio_plan.final_sample_count
            result["layout_intervals"] = len(plan.video_plan.layout_plan.intervals)
            result["included_blocks"] = sum(len(track.blocks) for track in project.timeline.tracks)
            cache_root = directory / "application-cache"
            if config["cache_mode"] != "fresh":
                _warm_cache(av, plan, config, directory, result, calls, stage_seconds, stage_calls)
                started = time.perf_counter()
            rendered = av.render_project_av(plan, preparations=RenderPreparations(cache_root))
            result.update(
                status="completed",
                frames=rendered.actual_frames,
                processing_fallbacks=list(rendered.processing_fallbacks),
                output_bytes=destination.stat().st_size,
            )
        except Exception as error:
            result.update(
                reason=f"{type(error).__name__}: {error}", traceback=traceback.format_exc()
            )
        result["wall_seconds"] = time.perf_counter() - started
    result.update(
        commands=calls,
        stage_seconds=stage_seconds,
        stage_calls=stage_calls,
        stage_timing_scope="nested/inclusive, not additive; fresh wall includes analysis/planning",
        resources={
            **sampler.report(),
            "includes_warm_resume_preflight": config["cache_mode"] != "fresh",
        },
        source_preserved=(
            before == config["source_hashes"]
            and all(sha256_file(Path(path)) == digest for path, digest in before.items())
        ),
        invocation_count=len(calls),
        ffmpeg_invocations=sum(Path(call["argv"][0]).name == "ffmpeg" for call in calls),
        ffmpeg_input_count=sum(
            call["inputs"] for call in calls if Path(call["argv"][0]).name == "ffmpeg"
        ),
        composition_input_counts=[
            {"stage": call["stage"], "inputs": call["inputs"]}
            for call in calls
            if "-filter_complex" in call["argv"]
        ],
        observed_command_output_bytes=sum(call.get("output_bytes_at_exit") or 0 for call in calls),
        retained_bytes=sum(path.stat().st_size for path in directory.rglob("*") if path.is_file()),
        byte_scope="logical bytes at command completion, may include overwritten paths; "
        "not physical I/O. Retained bytes before decoded-integrity artifacts.",
        gpu_after=gpu_snapshot(),
    )
    if result["status"] == "completed":
        try:
            result["signature"] = decoded_signature(destination, directory)
            validate_decoded_counts(
                result["signature"], result["expected_frames"], result["expected_audio_samples"]
            )
        except Exception as error:
            result.update(status="failed", reason=f"decoded integrity: {error}")
    return result


def summarize(rows: list[dict], trials: int) -> list[dict]:
    baselines = {
        (
            row["trial"],
            row["budget"],
            row.get("decoder_budget", 0),
            row.get("cache_mode", "fresh"),
        ): row
        for row in rows
        if row["strategy"] == "baseline"
    }
    groups: dict[tuple[str, int, int, str], list[dict[str, Any]]] = {}
    for row in rows:
        key = (
            row["strategy"],
            row["budget"],
            row.get("decoder_budget", 0),
            row.get("cache_mode", "fresh"),
        )
        baseline = baselines.get((row["trial"], key[1], key[2], key[3]), {})
        stock = baselines.get((row["trial"], 0, 0, key[3]), {})
        row["exact_parity"] = bool(
            row.get("status") == baseline.get("status") == stock.get("status") == "completed"
            and row.get("signature")
            and row["signature"] == baseline.get("signature") == stock.get("signature")
            and row.get("source_preserved")
            and baseline.get("source_preserved")
            and stock.get("source_preserved")
        )
        row["parity_differences_vs_current_baseline"] = [
            field
            for field in sorted(set(row.get("signature", {})) | set(stock.get("signature", {})))
            if row.get("signature", {}).get(field) != stock.get("signature", {}).get(field)
        ]
        groups.setdefault(key, []).append(row)
    summary = []
    for (strategy, budget, decoder_budget, mode), samples in groups.items():
        times = [row["wall_seconds"] for row in samples if row.get("status") == "completed"]
        baseline_times = [
            row["wall_seconds"]
            for row in rows
            if row["strategy"] == "baseline"
            and row["budget"] == budget
            and row.get("decoder_budget", 0) == decoder_budget
            and row.get("cache_mode", "fresh") == mode
            and row.get("status") == "completed"
        ]
        median = statistics.median(times) if times else None
        base = statistics.median(baseline_times) if baseline_times else None
        stock_times = [
            row["wall_seconds"]
            for row in rows
            if row["strategy"] == "baseline"
            and row["budget"] == 0
            and row.get("decoder_budget", 0) == 0
            and row.get("cache_mode", "fresh") == mode
            and row.get("status") == "completed"
        ]
        stock_median = statistics.median(stock_times) if stock_times else None
        stock_rows = [
            row
            for row in rows
            if row["strategy"] == "baseline"
            and row["budget"] == 0
            and row.get("decoder_budget", 0) == 0
            and row.get("cache_mode", "fresh") == mode
        ]
        baseline_stable = (
            len(stock_rows) == trials
            and all(
                row.get("status") == "completed"
                and row.get("source_preserved")
                and row.get("signature")
                for row in stock_rows
            )
            and len({json.dumps(row.get("signature"), sort_keys=True) for row in stock_rows}) == 1
        )
        exact = (
            len(samples) == trials
            and len({row["trial"] for row in samples}) == trials
            and baseline_stable
            and all(row["exact_parity"] for row in samples)
        )
        summary.append(
            {
                "strategy": strategy,
                "budget": budget,
                "decoder_budget": decoder_budget,
                "cache_mode": mode,
                "experimental_only": strategy in EXPERIMENTAL,
                "eligible_exact": exact,
                "current_baseline_exact_and_stable_across_trials": baseline_stable,
                "samples_seconds": times,
                "median_seconds": median,
                "baseline_same_budget_median_seconds": base,
                "speedup_vs_baseline": base / median if base and median else None,
                "relative_gain_percent": 100 * (base - median) / base if base and median else None,
                "current_baseline_auto_median_seconds": stock_median,
                "speedup_vs_current_baseline_auto": stock_median / median
                if stock_median and median
                else None,
                "gain_vs_current_baseline_auto_percent": (
                    100 * (stock_median - median) / stock_median
                    if stock_median and median
                    else None
                ),
                "selection_scope": "same fixture, encoder, pixels, rate and cache mode only",
            }
        )
    return summary


def argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--baseline-root", type=Path)
    parser.add_argument("--video-candidate", type=Path)
    parser.add_argument("--audio-candidate", type=Path)
    parser.add_argument("--tracks", type=int, choices=range(1, 5), default=3)
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--range-count", type=int, default=2)
    parser.add_argument("--duration", type=float, default=0.2)
    parser.add_argument("--source-count", type=int, default=1)
    parser.add_argument(
        "--intervals",
        type=int,
        default=0,
        help="segments per track, overriding repeats x range-count",
    )
    parser.add_argument(
        "--stagger-frames",
        type=int,
        default=0,
        help="track start offset in 30fps frames per track; 1 exercises changing layouts",
    )
    parser.add_argument("--late-start", "--source-start", dest="late_start", type=float, default=0)
    parser.add_argument(
        "--source-duration",
        type=float,
        help="fixture duration, default range end; use 120 with source-start 113",
    )
    parser.add_argument(
        "--seek-mode",
        choices=("copyts", "rebase"),
        default="copyts",
        help="EXPERIMENTAL: video-only timestamp-preserving seek or AV rebased seek",
    )
    parser.add_argument("--triplicate", action="store_true")
    parser.add_argument("--enhance", action="store_true")
    parser.add_argument("--trials", type=int, default=3)
    parser.add_argument(
        "--thread-budgets",
        default="1,2,4,6,auto",
        help="filter/filter_complex threads; encoder settings are NEVER modified",
    )
    parser.add_argument(
        "--decoder-threads",
        default="1",
        help="comma-separated input decoder budgets, e.g. 1,2,auto; encoder unchanged",
    )
    parser.add_argument("--strategies", default="baseline,video,audio,combined")
    parser.add_argument("--cache-modes", default="fresh")
    parser.add_argument("--resume-after", default="video composition")
    parser.add_argument("--report", type=Path)
    parser.add_argument("--artifact-root", type=Path)
    parser.add_argument("--worker", type=Path, help=argparse.SUPPRESS)
    return parser


def validate_args(args):
    if not args.baseline_root or not args.report or not args.artifact_root:
        raise ValueError("--baseline-root, --report and --artifact-root are required")
    if (
        min(args.repeats, args.range_count, args.trials, args.source_count) < 1
        or args.intervals < 0
        or args.stagger_frames < 0
    ):
        raise ValueError("repeat/range/trial/source counts must be positive; intervals nonnegative")
    if not math.isfinite(args.duration) or args.duration <= 0:
        raise ValueError("--duration must be finite and positive")
    if not math.isfinite(args.late_start) or args.late_start < 0:
        raise ValueError("--late-start must be finite and nonnegative")
    if args.source_duration is not None and (
        not math.isfinite(args.source_duration)
        or args.source_duration < args.late_start + args.duration * args.range_count
    ):
        raise ValueError("--source-duration must cover every requested source range")
    # Integer frame/sample boundaries are part of this controlled fixture contract.
    for label, value in (("duration", args.duration), ("late-start", args.late_start)):
        if abs(value * 30 - round(value * 30)) > 1e-7:
            raise ValueError(f"--{label} must be a multiple of 1/30 second")
    args.budgets = [0 if item == "auto" else int(item) for item in args.thread_budgets.split(",")]
    if (
        not args.budgets
        or any(item < 0 for item in args.budgets)
        or len(set(args.budgets)) != len(args.budgets)
    ):
        raise ValueError("thread budgets must be distinct nonnegative integers or auto")
    args.decoder_budgets = [
        0 if item == "auto" else int(item) for item in args.decoder_threads.split(",")
    ]
    if (
        not args.decoder_budgets
        or any(item < 0 for item in args.decoder_budgets)
        or len(set(args.decoder_budgets)) != len(args.decoder_budgets)
    ):
        raise ValueError("--decoder-threads must contain distinct nonnegative integers or auto")
    args.strategy_list = args.strategies.split(",")
    if (
        "baseline" not in args.strategy_list
        or len(set(args.strategy_list)) != len(args.strategy_list)
        or any(item not in STRATEGIES for item in args.strategy_list)
    ):
        raise ValueError(f"strategies require baseline plus distinct choices from {STRATEGIES}")
    args.modes = args.cache_modes.split(",")
    if len(set(args.modes)) != len(args.modes) or any(
        mode not in {"fresh", "checkpoint-warm", "resume"} for mode in args.modes
    ):
        raise ValueError("cache modes: fresh,checkpoint-warm,resume")
    # Reject shared temp roots rather than creating artifacts there.
    forbidden = (Path("/tmp"), Path("/var/tmp"))  # nosec B108
    for path in (args.artifact_root, args.report):
        if any(path.resolve().is_relative_to(root) for root in forbidden):
            raise ValueError(
                "use a project-relative artifact/report path, never a temporary directory"
            )


def run(args) -> dict:
    validate_args(args)
    tools = {}
    for tool in ("ffmpeg", "ffprobe"):
        executable = shutil.which(tool)
        if executable is None:
            raise ValueError(f"{tool} is required")
        version = subprocess.run(
            [executable, "-version"], check=True, capture_output=True, text=True
        )
        tools[tool] = {"path": executable, "version": version.stdout.splitlines()[0]}
    if args.report.exists():
        raise ValueError("report exists; choose a fresh report path")
    baseline = args.baseline_root.resolve()
    root = args.artifact_root.resolve()
    # Exclusive creation avoids accidentally consuming or deleting earlier caches.
    root.mkdir(parents=True, exist_ok=False)
    runtime = root / "runtime"
    runtime.mkdir()
    shutil.copytree(
        baseline / "framestudio",
        runtime / "framestudio",
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )
    for helper in baseline.glob("framestudio_*.py"):
        shutil.copy2(helper, runtime / helper.name)
    manifest = {str(path.relative_to(runtime)): sha256_file(path) for path in runtime.rglob("*.py")}
    candidates = {}
    for kind in ("video", "audio"):
        original = getattr(args, f"{kind}_candidate")
        if original:
            target = root / f"candidate-{kind}.py"
            shutil.copy2(original.resolve(), target)
            candidates[kind] = {
                "path": str(target),
                "sha256": sha256_file(target),
                "original": str(original.resolve()),
            }
    fixture_duration = args.source_duration or (args.late_start + args.duration * args.range_count)
    sources = []
    fixture_records = []
    for index in range(args.source_count):
        source = root / f"source-{index:03d}.mkv"
        fixture_command = [
            "ffmpeg",
            "-v",
            "error",
            "-nostdin",
            "-f",
            "lavfi",
            "-i",
            f"testsrc2=size=320x180:rate=30:duration={fixture_duration:.9f}",
            "-f",
            "lavfi",
            "-i",
            f"sine=frequency={440 + index * 13}:sample_rate=48000:duration={fixture_duration:.9f}",
            "-vf",
            f"hue=h={index * 17}",
            "-c:v",
            "libx264",
            "-preset",
            "ultrafast",
            "-g",
            "300",
            "-keyint_min",
            "300",
            "-sc_threshold",
            "0",
            "-bf",
            "3",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "pcm_s16le",
            "-ac",
            "2",
            "-threads",
            "1",
            str(source),
        ]
        subprocess.run(fixture_command, check=True, capture_output=True)
        sources.append(source)
        fixture_records.append(
            {
                "command": fixture_command,
                "sha256": sha256_file(source),
                "bytes": source.stat().st_size,
                "path": str(source),
            }
        )
    report: dict[str, Any] = {
        "schema_version": 1,
        "ticket": "TICKET-102",
        "phase": "PHASE-009",
        "features": ["FEAT-030", "FEAT-031"],
        "baseline_root": str(baseline),
        "baseline_snapshot_manifest": manifest,
        "candidates": candidates,
        "protocol": {
            key: value
            for key, value in vars(args).items()
            if isinstance(value, (str, bool, int, float, list))
        },
        "fixture": {
            "sources": fixture_records,
            "source_duration_seconds": fixture_duration,
            "codec": "H264 long GOP=300, Bframes=3, stereo PCM, 320x180 30fps",
            "timeline_duration_seconds": args.duration
            * (args.intervals or args.range_count * args.repeats)
            + (args.tracks - 1) * args.stagger_frames / 30,
        },
        "environment": {
            "platform": platform.platform(),
            "python": sys.version,
            "logical_cpu_count": os.cpu_count(),
            "tools": tools,
            "gpu": gpu_snapshot(),
        },
        "limitations": [
            "Sequential rows; counterbalanced cyclic order, not concurrent trials.",
            "Filter and input decoder budgets are independent; final encoder options unchanged. "
            "A baseline auto-filter/auto-decoder control is always included.",
            "Fresh application caches; OS cache uncontrolled, likely warm. No cold-OS claim.",
            "Synthetic same-source integer-CFR motion+tone fixture, not arbitrary user media.",
            "Process telemetry sampled; bytes sum observed command output files, not physical disk I/O.",
            "Stages inclusive/nested; subprocess sums are not end-to-end wall time.",
            "Decoded hashes run after timing; GPU data are snapshots, not averages.",
            "Exact parity is fixture-specific evidence, not proof for all timelines/codecs.",
            "One-frame staggered layout intervals can expose the legacy concat PTS defect; "
            "those frame-count failures are retained and cannot select a winner.",
            "Experimental seek has no production eligibility guard; one generated source only.",
            "Track boundaries may be staggered; source count/range reuse are configurable, "
            "but synthetic layouts are not an actual-project performance claim.",
            "Selection is observational only; production adoption requires TICKET-103/104 validation.",
        ],
        "rows": [],
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)

    def persist():
        args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    persist()
    for trial in range(args.trials):
        # Rotate candidate order WITHIN each thread block, not only the whole
        # matrix (the latter would leave most candidate pair order unchanged).
        combinations = [
            (strategy, budget, decoder_budget, mode)
            for mode in trial_order(args.modes, trial)
            for decoder_budget in trial_order(args.decoder_budgets, trial)
            for budget in trial_order(args.budgets, trial)
            for strategy in trial_order(args.strategy_list, trial)
        ]
        for mode in args.modes:
            stock = ("baseline", 0, 0, mode)
            if stock not in combinations:
                combinations.insert(trial % (len(combinations) + 1), stock)
        for sequence, (strategy, budget, decoder_budget, mode) in enumerate(combinations):
            directory = (
                root
                / f"trial-{trial:03d}-{sequence:03d}-{strategy}-f{budget}-d{decoder_budget}-{mode}"
            )
            directory.mkdir()
            config = {
                "trial": trial,
                "strategy": strategy,
                "budget": budget,
                "cache_mode": mode,
                "decoder_budget": decoder_budget,
                "directory": str(directory),
                "runtime": str(runtime),
                "sources": [str(source) for source in sources],
                "source_hashes": {record["path"]: record["sha256"] for record in fixture_records},
                "video_candidate": candidates.get("video", {}).get("path"),
                "audio_candidate": candidates.get("audio", {}).get("path"),
                **{
                    key: getattr(args, key)
                    for key in (
                        "tracks",
                        "repeats",
                        "range_count",
                        "duration",
                        "late_start",
                        "triplicate",
                        "enhance",
                        "intervals",
                        "stagger_frames",
                        "resume_after",
                        "seek_mode",
                    )
                },
            }
            config_path = directory / "request.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")
            started = time.perf_counter()
            child = subprocess.run(
                [sys.executable, str(Path(__file__).resolve()), "--worker", str(config_path)],
                capture_output=True,
                text=True,
            )
            (directory / "worker.stdout").write_text(child.stdout, encoding="utf-8")
            (directory / "worker.stderr").write_text(child.stderr, encoding="utf-8")
            response = directory / "result.json"
            row = (
                json.loads(response.read_text())
                if response.exists()
                else {"status": "failed", "reason": f"worker exited {child.returncode}; see stderr"}
            )
            row.update(
                trial=trial,
                sequence=sequence,
                strategy=strategy,
                budget=budget,
                decoder_budget=decoder_budget,
                cache_mode=mode,
                application_cache="fresh" if mode == "fresh" else mode,
                seek_mode=args.seek_mode if "seek" in strategy else None,
                os_cache="uncontrolled/OS-warm",
                worker_wall_seconds=time.perf_counter() - started,
                artifact_directory=str(directory),
                experimental_only=strategy in EXPERIMENTAL,
            )
            report["rows"].append(row)
            persist()
    report["summary"] = summarize(report["rows"], args.trials)
    report["source_preserved"] = all(
        sha256_file(Path(record["path"])) == record["sha256"] for record in fixture_records
    )
    eligible = [
        item
        for item in report["summary"]
        if item["eligible_exact"] and item["cache_mode"] == "fresh" and report["source_preserved"]
    ]
    report["fastest_measured_exact_fresh"] = (
        min(eligible, key=lambda item: item["median_seconds"]) if eligible else None
    )
    production = [item for item in eligible if not item["experimental_only"]]
    report["fastest_nonexperimental_exact_fresh"] = (
        min(production, key=lambda item: item["median_seconds"]) if production else None
    )
    report["status"] = "completed" if comparison_succeeded(report) else "failed"
    if report["status"] == "failed":
        report["failure_reason"] = "No eligible exact fresh baseline/winner; inspect retained rows"
    persist()
    return report


def comparison_succeeded(report: dict) -> bool:
    return bool(
        report.get("source_preserved")
        and report.get("fastest_measured_exact_fresh")
        and any(
            row["strategy"] == "baseline" and row["cache_mode"] == "fresh" and row["eligible_exact"]
            for row in report.get("summary", ())
        )
    )


def main():
    parser = argument_parser()
    args = parser.parse_args()
    if args.worker:
        config = json.loads(args.worker.read_text())
        try:
            result = worker(config)
        except Exception as error:
            result = {
                "status": "failed",
                "reason": f"{type(error).__name__}: {error}",
                "traceback": traceback.format_exc(),
            }
        Path(config["directory"], "result.json").write_text(
            json.dumps(result, indent=2) + "\n",
            encoding="utf-8",
        )
        return
    try:
        report = run(args)
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        parser.exit(2, f"benchmark setup failed: {error}\n")
    print(
        json.dumps(
            {
                "report": str(args.report),
                "status": report.get("status", "failed"),
                "rows": len(report["rows"]),
                "fastest_measured_exact_fresh": report["fastest_measured_exact_fresh"],
            },
            indent=2,
        )
    )
    if not comparison_succeeded(report):
        parser.exit(
            1, "No eligible exact fresh baseline/winner; failure data retained in report.\n"
        )


if __name__ == "__main__":
    main()
