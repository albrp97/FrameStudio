#!/usr/bin/env python3
"""Benchmark real sequential imports, not synthetic multi-hour timeline metadata.

Example (run serialized; this program acquires playback-benchmark.lock itself):
  PYTHONPATH=. python3 benchmarks/large_project_preview.py --artifact-dir benchmark-run \
    --counts 2 20 200 --modes legacy-tail active-ffmpeg production

Each case runs in an isolated process with an owned-process RSS watchdog. Fixtures
are copied, not linked: same encoded content, distinct paths/inodes, NOT distinct
codec workloads. Only the artifact directory is written. Production uses the
actual mapped editor and _attach_project route. Other modes replace only the
backend factory inside that same editor. No autosave is written.

For a bounded first/middle comparison use --trace-set bounded --repetitions 1
--playback-seconds 0. Defaults are a 60s case ceiling, 15s progress timeout,
2048MiB owned-process-tree RSS stop threshold, input decoder threads=1 and
filter threads=2: guarded NOT unmodified FFmpeg. Sampled RSS can overshoot the
stop threshold between observations. The experimental active-sequential-cuda
mode adds only CUDA input decoding (plus debug diagnostics); any reference hash
mismatch rejects its quality eligibility, even when latency improves.

--no-guard records production's actual thread options without injecting limits.
--functionality additionally exercises split/delete/restore and save/reopen on
the owned copies, checks exact legacy frames and absence of audio scans, and
verifies backend-close child cleanup. Both window and module-level autosave
callbacks are disabled during that charter; no user autosave is overwritten.
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import math
import os
import re
import shutil
import signal
import subprocess
import sys
import threading
import time
import uuid
from pathlib import Path
from typing import Any
from unittest.mock import patch

SESSION = Path("/home/ghiki/.copilot/session-state/6318e80e-9055-4f34-8aff-82ab264934b4")
LOCK = SESSION / "files/playback-benchmark.lock"
FIXTURES = SESSION / "files/decoder-performance-fixtures"
MODES = (
    "legacy-tail",
    "window-five",
    "active-ffmpeg",
    "active-sync",
    "active-sequential",
    "active-sequential-cuda",
    "active-cpu",
    "active-cuda",
    "production",
)


def require_tool(name: str) -> str:
    executable = shutil.which(name)
    if executable is None:
        raise RuntimeError(f"{name} is required for this benchmark operation")
    return executable


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    buffer = bytearray(1024 * 1024)
    view = memoryview(buffer)
    with path.open("rb", buffering=0) as stream:
        while length := stream.readinto(buffer):
            digest.update(view[:length])
    return digest.hexdigest()


def copy_sources(fixture: Path, directory: Path, count: int) -> tuple[Path, ...]:
    if count < 1:
        raise ValueError("Source count must be positive")
    directory.mkdir(parents=True, exist_ok=False)
    paths = tuple(directory / f"source-{index:04d}{fixture.suffix}" for index in range(count))
    for path in paths:
        shutil.copyfile(fixture, path)
    identities = {(path.stat().st_dev, path.stat().st_ino) for path in (*paths, fixture)}
    if len(identities) != count + 1 or any(path.is_symlink() for path in paths):
        raise RuntimeError("Fixture copies must be distinct regular files")
    return paths


def source_at(position: float, durations: tuple[float, ...], fps: float) -> tuple[int, float]:
    if not durations or any(duration <= 0 for duration in durations) or fps <= 0:
        raise ValueError("Positive durations and frame rate are required")
    target = max(0.0, min(float(position), sum(durations) - 1 / fps))
    elapsed = 0.0
    for index, duration in enumerate(durations):
        if target < elapsed + duration or index == len(durations) - 1:
            return index, max(0.0, target - elapsed)
        elapsed += duration
    raise AssertionError("Unreachable source mapping")


def window_at(position: float, durations: tuple[float, ...], fps: float) -> tuple[int, int, float]:
    index, _offset = source_at(position, durations, fps)
    return index, min(len(durations), index + 5), sum(durations[:index])


def cuda_input_command(command: list[str]) -> list[str]:
    if command.count("-i") != 1:
        raise ValueError("CUDA sequential experiment requires a single input")
    index = command.index("-i")
    return command[:index] + ["-hwaccel", "cuda"] + command[index:]


def bounded_traces(count: int, duration: float) -> list[tuple[str, float]]:
    if count < 2 or duration <= 0.5:
        raise ValueError("Bounded traces require two sources longer than 0.5 seconds")
    return [("first", 0.5), ("middle", (count // 2) * duration + 0.5)]


def window_command(backend: Any, position: float, *, realtime: bool, frame_count=None):
    """Build the experimental five-block graph with locally remapped input indexes."""
    from framestudio.ffmpeg_playback import FfmpegComposedPlaybackBackend

    durations = tuple(block.duration_seconds for block in backend._blocks)
    first, end, _origin = window_at(position, durations, backend.frame_rate)
    blocks = backend._blocks[first:end]
    ids = {block.source_id for block in blocks}
    local = object.__new__(FfmpegComposedPlaybackBackend)
    local.__dict__.update(backend.__dict__)
    local._blocks = blocks
    local._source_items = tuple(item for item in backend._source_items if item[0] in ids)
    local._source_indexes = {
        source_id: index for index, (source_id, _) in enumerate(local._source_items)
    }
    index, offset = source_at(position, durations, backend.frame_rate)
    target = sum(durations[first:index]) + offset
    return FfmpegComposedPlaybackBackend._command(
        local,
        target,
        realtime=realtime,
        frame_count=frame_count,
    )


def make_traces(count: int, duration: float) -> list[tuple[str, float]]:
    if count < 1 or duration <= 2.5:
        raise ValueError("Traces require at least one source longer than 2.5 seconds")
    traces = [
        (f"clip-{index}", index * duration + offset)
        for index in dict.fromkeys((0, count // 2, count - 1))
        for offset in (0.5, 1.5, 2.5)
    ]
    traces.extend(("adjacent", index * duration + 0.5) for index in range(min(5, count)))
    traces.append(("adjacent", 0.5))
    traces.extend(
        (
            "random-distant",
            (int.from_bytes(hashlib.sha256(f"7331:{index}".encode()).digest(), "big") % count)
            * duration
            + 1.5,
        )
        for index in range(6)
    )
    traces.extend(
        ("rapid", index * duration + 2.5)
        for index in (0, count - 1, count // 2, 0, count - 1, count // 2)
    )
    return traces


def guard_command(command: list[str]) -> list[str]:
    guarded = [command[0], "-filter_threads", "2", "-filter_complex_threads", "2"]
    for argument in command[1:]:
        if argument == "-i":
            guarded.extend(("-threads", "1"))
        guarded.append(argument)
    return guarded


def thread_options(command: list[str]) -> dict[str, list[str]]:
    first_input = command.index("-i") if "-i" in command else len(command)
    return {
        "decoder_threads": [
            command[index + 1]
            for index, value in enumerate(command[:-1])
            if value == "-threads" and index < first_input
        ],
        "filter_complex_threads": [
            command[index + 1]
            for index, value in enumerate(command[:-1])
            if value == "-filter_complex_threads"
        ],
        "filter_threads": [
            command[index + 1]
            for index, value in enumerate(command[:-1])
            if value == "-filter_threads"
        ],
        "output_video_threads": [
            command[index + 1]
            for index, value in enumerate(command[:-1])
            if value == "-threads:v" and index > first_input
        ],
    }


def owned_processes(root: int) -> dict[int, tuple[int, int]]:
    """Return only the root and its currently observable descendants (RSS bytes)."""
    processes: dict[int, tuple[int, int]] = {}
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        try:
            fields = (entry / "stat").read_text().rsplit(")", 1)[1].split()
            processes[int(entry.name)] = (
                int(fields[1]),
                int(fields[21]) * os.sysconf("SC_PAGE_SIZE"),
            )
        except (OSError, ValueError, IndexError):
            continue
    included = {root}
    while True:
        expanded = included | {pid for pid, (parent, _) in processes.items() if parent in included}
        if expanded == included:
            return {pid: processes[pid] for pid in included if pid in processes}
        included = expanded


def kill_owned(process: subprocess.Popen, processes: dict[int, tuple[int, int]]) -> None:
    # FFmpeg starts its own session; session IDs alone do not identify ownership.
    def depth(pid):
        parents = set()
        while pid in processes and pid != process.pid and pid not in parents:
            parents.add(pid)
            pid = processes[pid][0]
        return len(parents)

    for pid in sorted(processes, key=depth, reverse=True):
        try:
            if pid in owned_processes(process.pid):
                os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    process.wait(timeout=5)


def gpu_usage(pids: set[int]) -> tuple[int | None, str | None]:
    executable = shutil.which("nvidia-smi")
    if executable is None:
        return None, "nvidia-smi unavailable"
    try:
        output = subprocess.check_output(
            [
                executable,
                "--query-compute-apps=pid,used_gpu_memory",
                "--format=csv,noheader,nounits",
            ],
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=1,
        )
        memory = 0
        for line in output.splitlines():
            pid, amount = line.split(",", 1)
            if int(pid.strip()) in pids:
                memory += int(amount.strip()) * 1024 * 1024
        return memory, None
    except (subprocess.SubprocessError, ValueError, OSError) as error:
        return None, f"GPU accounting unavailable: {error}"


def write_json(path: Path, value: Any) -> None:
    partial = path.with_suffix(path.suffix + ".partial")
    partial.write_text(json.dumps(value, indent=2) + "\n")
    partial.replace(path)


def latency_summary(samples: list[dict], key: str) -> dict:
    values = sorted(float(sample[key]) for sample in samples if sample.get(key) is not None)
    return {
        "count": len(values),
        "p50_ms": values[len(values) // 2] if values else None,
        "p95_ms": values[min(len(values) - 1, int(len(values) * 0.95))] if values else None,
        "max_ms": values[-1] if values else None,
    }


def _load_worker_result(directory: Path) -> dict:
    result_path = directory / "result.json"
    result = json.loads(result_path.read_text()) if result_path.exists() else {}
    invocation_path = directory / "ffmpeg-invocations.jsonl"
    if invocation_path.exists():
        invocations = []
        for line in invocation_path.read_text().splitlines():
            try:
                invocations.append(json.loads(line))
            except json.JSONDecodeError:
                result["truncated_invocation_record"] = True
        result["ffmpeg_invocations"] = invocations
    return dict(result)


def run_case(job: dict[str, Any], directory: Path, timeout: float, max_rss: int) -> dict:
    job_path = directory / "job.json"
    write_json(job_path, job)
    started = time.monotonic()
    with (directory / "worker.log").open("w") as log:
        process = subprocess.Popen(
            [sys.executable, str(Path(__file__).resolve()), "--worker", str(job_path)],
            stdout=log,
            stderr=log,
            start_new_session=True,
        )
        peak_rss = 0
        peak_rss_including_reference = 0
        peak_gpu: int | None = None
        gpu_error = None
        failure = None
        stop_gpu = threading.Event()

        def sample_gpu():
            nonlocal peak_gpu, gpu_error
            while not stop_gpu.is_set():
                phase_path = directory / "phase"
                reference_phase = phase_path.exists() and phase_path.read_text() == "reference"
                memory, gpu_error = gpu_usage(set(owned_processes(process.pid)))
                if memory is not None and not reference_phase:
                    peak_gpu = max(peak_gpu or 0, memory)
                if stop_gpu.wait(0.5):
                    break

        gpu_thread = threading.Thread(target=sample_gpu, daemon=True)
        gpu_thread.start()
        try:
            while process.poll() is None:
                tree = owned_processes(process.pid)
                rss = sum(rss for _, rss in tree.values())
                peak_rss_including_reference = max(peak_rss_including_reference, rss)
                phase_path = directory / "phase"
                reference_phase = phase_path.exists() and phase_path.read_text() == "reference"
                if not reference_phase:
                    peak_rss = max(peak_rss, rss)
                progress = directory / "heartbeat"
                last_progress = (
                    progress.stat().st_mtime if progress.exists() else job_path.stat().st_mtime
                )
                if rss > max_rss:
                    failure = "owned process-tree RSS limit exceeded"
                elif time.monotonic() - started > job.get("max_case_seconds", 60):
                    failure = "maximum case wall time exceeded"
                elif time.time() - last_progress > timeout:
                    failure = "request/attach timeout"
                if failure:
                    kill_owned(process, tree)
                    break
                time.sleep(0.025)
        finally:
            if process.poll() is None:
                kill_owned(process, owned_processes(process.pid))
            stop_gpu.set()
            gpu_thread.join(timeout=2)
    result_path = directory / "result.json"
    result = _load_worker_result(directory)
    expected_hash = job.get("fixture_sha256")
    if expected_hash is not None:
        after = {Path(path).name: sha256(Path(path)) for path in job["sources"]}
        result["source_sha256_after_watchdog"] = after
        result["sources_preserved_after_watchdog"] = all(
            digest == expected_hash for digest in after.values()
        )
        result["fixture_preserved_after_watchdog"] = sha256(Path(job["fixture"])) == expected_hash
    result.update(
        watchdog_failure=failure,
        returncode=process.returncode,
        peak_owned_process_tree_rss_bytes=peak_rss,
        peak_owned_rss_including_reference_bytes=peak_rss_including_reference,
        peak_owned_compute_gpu_memory_bytes=peak_gpu,
        gpu_memory_gap=gpu_error,
        resource_sample_interval_ms=25,
        gpu_sample_interval_ms=500,
        wall_seconds=time.monotonic() - started,
    )
    if failure or (process.returncode and result.get("status") != "rejected-quality"):
        result["status"] = "error"
    write_json(result_path, result)
    return result


def _experimental_backend_factory(job, source_items, layout, timeline, duration):
    from framestudio.composed_playback import FfmpegSynchronizedPlaybackBackend
    from framestudio.ffmpeg_playback import FfmpegComposedPlaybackBackend

    class WindowFiveBackend(FfmpegComposedPlaybackBackend):
        def _command(self, position_seconds, *, realtime, frame_count=None):
            return window_command(
                self,
                position_seconds,
                realtime=realtime,
                frame_count=frame_count,
            )

    def experimental_factory(sources, blocks_or_layout, policy, rate, *rest, **_kwargs):
        # The two production factory signatures differ only in callback position.
        callbacks = rest[0] if hasattr(blocks_or_layout, "intervals") else rest[1]
        on_frame, on_error, on_end, on_warning = callbacks
        common = dict(
            width=policy.width,
            height=policy.height,
            frame_rate=rate,
            on_frame=on_frame,
            on_error=on_error,
            on_end=on_end,
            on_warning=on_warning,
        )
        if job["mode"] in {"active-sync", "active-ffmpeg"}:
            return FfmpegSynchronizedPlaybackBackend(
                source_items,
                layout,
                preview_backend="ffmpeg",
                **common,
            )
        if job["mode"] in {
            "active-sequential",
            "active-sequential-cuda",
            "active-cpu",
            "active-cuda",
        }:
            from framestudio.sequential_playback import FfmpegSequentialPlaybackBackend

            class CudaSequentialExperiment(FfmpegSequentialPlaybackBackend):
                def _video_command(self, position_seconds, interval, *, continuous=False):
                    command = super()._video_command(
                        position_seconds,
                        interval,
                        continuous=continuous,
                    )
                    command[command.index("-loglevel") + 1] = "debug"
                    return cuda_input_command(command)

                def _run_decode_command(self, command, *, cancel_check, process_attribute):
                    output, diagnostic = super()._run_decode_command(
                        command,
                        cancel_check=cancel_check,
                        process_attribute=process_attribute,
                    )
                    lines = [
                        line
                        for line in diagnostic.decode(errors="replace").splitlines()
                        if "Format cuda chosen by get_format" in line
                        or "CUDA device" in line
                        or "cuvid" in line.casefold()
                    ]
                    self.precise_preview_diagnostics.update(
                        {
                            "selected_engine": "ffmpeg-cuda"
                            if any("Format cuda chosen by get_format" in line for line in lines)
                            else "ffmpeg-cuda-unconfirmed",
                            "hardware_decoder_evidence": lines,
                            "reason": "Experimental single-input -hwaccel cuda; unchanged legacy filters",
                        }
                    )
                    return output, diagnostic

            engine = {
                "active-sequential": "ffmpeg",
                "active-sequential-cuda": "ffmpeg",
                "active-cpu": "cpu",
                "active-cuda": "cuda",
            }[job["mode"]]
            sequential_type = (
                CudaSequentialExperiment
                if job["mode"] == "active-sequential-cuda"
                else FfmpegSequentialPlaybackBackend
            )
            return sequential_type(
                source_items,
                timeline.segment_items,
                layout,
                preview_backend=engine,
                **common,
            )
        backend_type = (
            WindowFiveBackend if job["mode"] == "window-five" else FfmpegComposedPlaybackBackend
        )
        return backend_type(
            source_items,
            timeline.active_blocks(),
            duration_seconds=duration * len(source_items),
            **common,
        )

    return experimental_factory


def _reference_factory(job, directory, source_items, layout, timeline, duration, fps, durations):
    from framestudio.composed_playback import FfmpegSynchronizedPlaybackBackend
    from framestudio.ffmpeg_playback import FfmpegComposedPlaybackBackend

    reference_cache: dict[tuple[int, float], dict] = {}

    def reference(target):
        index, offset = source_at(target, durations, fps)
        key = (index, offset)
        if key not in reference_cache:
            errors: list[str] = []
            frames: list[Any] = []
            # One-block legacy reference deliberately preserves old RGBA color policy.
            block = timeline.active_blocks()[index]
            legacy = FfmpegComposedPlaybackBackend(
                (source_items[index],),
                (block,),
                1920,
                1080,
                fps,
                duration,
                frames.append,
                errors.append,
                lambda: None,
            )
            active = FfmpegSynchronizedPlaybackBackend(
                source_items,
                layout,
                1920,
                1080,
                fps,
                frames.append,
                errors.append,
                lambda: None,
                preview_backend="ffmpeg",
            )
            try:
                (directory / "phase").write_text("reference")
                old = legacy._decode_preview_frame(offset)
                current = (
                    active._decode_preview_frame(target)
                    if job.get("trace_set", "full") == "full"
                    else None
                )
                reference_cache[key] = {
                    "legacy_single_block_sha256": hashlib.sha256(old.data).hexdigest(),
                    "active_ffmpeg_sha256": (
                        hashlib.sha256(current.data).hexdigest() if current is not None else None
                    ),
                    "reference_errors": errors,
                }
            finally:
                legacy.close()
                active.close()
                (directory / "phase").write_text("measurement")
        return reference_cache[key]

    return reference


def _dispatch_factory(
    job,
    directory,
    result,
    window,
    callbacks_seen,
    paints,
    pump,
    heartbeat,
    reference,
    stats,
    durations,
    fps,
):
    def dispatch(kind, target, wait=True):
        heartbeat()
        before_callback, before_paint = len(callbacks_seen), len(paints)
        record = {
            "kind": kind,
            "target_seconds": target,
            "source_index": source_at(target, durations, fps)[0],
            "source_offset_seconds": source_at(target, durations, fps)[1],
            "request_handler_ms": None,
            "decode_callback_ms": None,
            "gtk_delivery_ms": None,
            "after_paint_ms": None,
        }
        result["phase"] = "seek"
        result["samples"].append(record)
        write_json(directory / "result.json", result)
        started = time.monotonic()
        window._on_timeline_view_seek(target)
        returned = time.monotonic()
        record["request_handler_ms"] = (returned - started) * 1000
        if not wait:
            return
        deadline = started + job["timeout"]
        painted = None
        while time.monotonic() < deadline:
            pump()
            painted = next(
                (
                    paint
                    for paint in paints[before_paint:]
                    if math.isclose(paint["position"], target, abs_tol=1e-5)
                ),
                None,
            )
            if painted is not None:
                break
        callback = next(
            (
                item
                for item in callbacks_seen[before_callback:]
                if math.isclose(item["position"], target, abs_tol=1e-5)
            ),
            None,
        )
        if callback is not None:
            record.update(
                decode_callback_ms=(callback["at"] - started) * 1000,
                sha256=callback["sha256"],
                decoded_position_seconds=callback["decoded_position"],
                frame_width=callback["width"],
                frame_height=callback["height"],
                delivered_position_seconds=callback["position"],
            )
        if painted is not None:
            record.update(
                gtk_delivery_ms=(painted["delivery_at"] - started) * 1000,
                gtk_delivery_handler_ms=(painted["delivery_return"] - painted["delivery_at"])
                * 1000,
                after_paint_ms=(painted["at"] - started) * 1000,
                painted_position_seconds=painted["position"],
            )
        else:
            record["error"] = "GTK after-paint timeout"
        if callback is not None:
            heartbeat()
            refs = reference(target)
            record.update(refs)
            record["matches_legacy_single_block"] = (
                callback["sha256"] == refs["legacy_single_block_sha256"]
            )
            record["matches_active_ffmpeg"] = (
                callback["sha256"] == refs["active_ffmpeg_sha256"]
                if refs["active_ffmpeg_sha256"] is not None
                else None
            )
            if not record["matches_legacy_single_block"]:
                result["quality_rejected"] = True
        record["backend_stats"] = stats()
        write_json(directory / "result.json", result)
        heartbeat()

    return dispatch


def _run_traces(job, result, count, duration, dispatch):
    for repetition in range(job.get("repetitions", 1)):
        result["repetition"] = repetition + 1
        traces = (
            bounded_traces(count, duration)
            if job.get("trace_set", "full") == "bounded"
            else make_traces(count, duration)
        )
        for kind, target in traces:
            if kind != "rapid":
                dispatch(kind, target)
                if result["samples"][-1].get("error"):
                    raise RuntimeError("Stopping case after first timed-out request")
        rapid = [target for kind, target in traces if kind == "rapid"]
        if rapid:
            preview_before = result["samples"][-1].get("backend_stats", {}).get("preview", {})
            rapid_started = time.monotonic()
            for target in rapid[:-1]:
                dispatch("rapid-submitted", target, wait=False)
            dispatch("rapid-latest", rapid[-1])
            result["rapid_six_targets_wall_ms"] = (time.monotonic() - rapid_started) * 1000
            _record_rapid(result, rapid, preview_before)


def _record_rapid(result, targets, preview_before):
    sample = result["samples"][-1]
    preview_after = sample.get("backend_stats", {}).get("preview", {})
    painted = sample.get("painted_position_seconds")
    result.setdefault("rapid_batches", []).append(
        {
            "repetition": result["repetition"],
            "targets_seconds": targets,
            "latest_target_seconds": targets[-1],
            "last_painted_position_seconds": painted,
            "latest_target_painted": painted is not None
            and math.isclose(
                painted,
                targets[-1],
                abs_tol=1e-5,
            ),
            "stale_frames_delta": preview_after.get("stale_frames", 0)
            - preview_before.get("stale_frames", 0),
            "cancelled_requests_delta": preview_after.get("cancelled_requests", 0)
            - preview_before.get("cancelled_requests", 0),
            "coalesced_requests_delta": preview_after.get("coalesced_requests", 0)
            - preview_before.get("coalesced_requests", 0),
        }
    )


def _measure_playback(job, result, window, duration, dispatch, paints, pump, heartbeat):
    if job["playback_seconds"] > 0:
        dispatch("boundary-preroll", duration - 1)
        result["phase"] = "playback"
        before = len(paints)
        started = time.monotonic()
        window._on_play_clicked(None)
        while time.monotonic() - started < job["playback_seconds"]:
            pump()
            heartbeat()
        window._on_play_clicked(None)
        playback_paints = paints[before:]
        gaps = sorted(
            (right["at"] - left["at"]) * 1000
            for left, right in zip(playback_paints, playback_paints[1:], strict=False)
        )
        result["playback"] = {
            "observed_seconds": time.monotonic() - started,
            "painted_updates": len(playback_paints),
            "painted_updates_per_second": len(playback_paints) / (time.monotonic() - started),
            "p95_paint_gap_ms": gaps[min(len(gaps) - 1, int(len(gaps) * 0.95))] if gaps else None,
            "crossed_source_boundary": any(
                item["position"] >= duration for item in playback_paints
            ),
            "positions_seconds": [item["position"] for item in playback_paints],
        }
        result["playback"]["boundary_failure"] = (
            None
            if result["playback"]["crossed_source_boundary"]
            else "No painted update crossed the first source boundary"
        )
        if result["playback"]["boundary_failure"] is not None:
            result["errors"].append(result["playback"]["boundary_failure"])


def _pump_factory(context):
    def pump(seconds=0.005):
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            # Bound dispatch too: a busy GLib queue must not starve the deadline.
            for _ in range(100):
                if not context.pending():
                    break
                context.iteration(False)
            time.sleep(0.001)

    return pump


def _observe_window(window):
    callbacks_seen: list[dict] = []
    paints: list[dict] = []
    pending: list[Any] = [None]
    receive_original = window._on_frame
    deliver_original = window._deliver_latest_frame

    def receive(frame, generation=None):
        callbacks_seen.append(
            {
                "at": time.monotonic(),
                "position": frame.position_seconds,
                "decoded_position": frame.decoded_position_seconds,
                "sha256": hashlib.sha256(frame.data).hexdigest(),
                "identity": id(frame),
                "width": frame.width,
                "height": frame.height,
            }
        )
        receive_original(frame, generation)

    def deliver():
        frame = window._latest_frame
        old = window.preview.get_paintable()
        started = time.monotonic()
        value = deliver_original()
        if frame is not None and window.preview.get_paintable() != old:
            pending[0] = {
                "delivery_at": started,
                "delivery_return": time.monotonic(),
                "position": frame.position_seconds,
                "identity": id(frame),
                "paintable": window.preview.get_paintable(),
            }
        return value

    window._on_frame = receive
    window._deliver_latest_frame = deliver
    return callbacks_seen, paints, pending


def _logged_popen(directory, result, job):
    popen_original = subprocess.Popen
    result["ffmpeg_invocations"] = []

    def guarded_popen(command, *args, **kwargs):
        if isinstance(command, (tuple, list)) and Path(str(command[0])).name == "ffmpeg":
            graph = (
                command[command.index("-filter_complex") + 1]
                if "-filter_complex" in command
                else ""
            )
            invocation = {
                "inputs": command.count("-i"),
                "concat_blocks": [int(value) for value in re.findall(r"concat=n=(\d+)", graph)],
                "phase": "reference"
                if (
                    (directory / "phase").exists()
                    and (directory / "phase").read_text() == "reference"
                )
                else result.get("phase"),
                "threads": thread_options(
                    guard_command(list(command)) if job["guard"] else list(command)
                ),
            }
            result["ffmpeg_invocations"].append(invocation)
            with (directory / "ffmpeg-invocations.jsonl").open("a") as events:
                events.write(json.dumps(invocation) + "\n")
            if job["guard"]:
                command = guard_command(list(command))
        return popen_original(command, *args, **kwargs)

    return guarded_popen


def _connect_paints(window, result, pending, paints):
    if not window.get_mapped() or not window.preview.get_mapped():
        raise RuntimeError("Production editor/preview did not map")
    backend = window.backend
    result["selected_backend"] = type(backend).__name__
    result["output_frame_rate"] = window.source_frame_rate
    clock = window.get_frame_clock()
    if clock is None:
        raise RuntimeError("Mapped window has no frame clock")

    def after_paint(frame_clock):
        record = pending[0]
        if record is not None and window.preview.get_paintable() == record["paintable"]:
            paints.append(
                {key: value for key, value in record.items() if key != "paintable"}
                | {"at": time.monotonic(), "frame_counter": frame_clock.get_frame_counter()}
            )
            pending[0] = None

    clock.connect("after-paint", after_paint)
    return backend


def _backend_stats(backend):
    precise = getattr(backend, "precise_preview_stats", None)
    return {
        "preview": backend.preview_stats(),
        "native": precise() if precise else {"capability": "not available on this backend"},
        "decoder_starts": getattr(backend, "_decoder_starts", None),
    }


def _finish_backend(job, result, backend, stats):
    result["final_backend_stats"] = stats()
    native_stats = result["final_backend_stats"]["native"]
    selected = native_stats.get("selected_engine", "ffmpeg")
    result["requested_native_engine_observed"] = (
        selected == result["requested_preview_engine"]
        if job["mode"] in {"active-cpu", "active-cuda", "active-sequential-cuda"}
        else None
    )
    if result["requested_native_engine_observed"] is False:
        result["capability_gaps"].append(
            "Requested native engine was not selected; this is a fallback measurement, "
            "not evidence for native sequential decoding"
        )
    backend.close()


def _audit_route_frame(window, position, source_offset, pump):
    from framestudio.ffmpeg_playback import FfmpegComposedPlaybackBackend

    interval = window.backend._interval_at(position)
    if interval is None or len(interval.active_blocks) != 1:
        raise AssertionError("Edited production route does not have one active block")
    planned = interval.active_blocks[0]
    actual_offset = planned.source_range.source_tick_at(round(position * 1_000_000)) / 1_000_000
    if planned.source_id != window.project.source.source_id or not math.isclose(
        actual_offset,
        source_offset,
        abs_tol=1e-6,
    ):
        raise AssertionError("Edited production route selected the wrong source or source offset")
    block = window.segment_timeline.find(planned.segment_id)
    frames = []
    original = window._on_frame

    def receive(frame, generation=None):
        frames.append(frame)
        original(frame, generation)

    window._on_frame = receive
    try:
        window._seek_timeline(position)
        pump(0.05)
    finally:
        window._on_frame = original
    if not frames:
        raise AssertionError("Supported seek callback did not deliver an edited preview")
    errors: list[str] = []
    reference = FfmpegComposedPlaybackBackend(
        ((planned.source_id, Path(window.project.source.path)),),
        (block,),
        1920,
        1080,
        window.source_frame_rate,
        block.duration_seconds,
        lambda _frame: None,
        errors.append,
        lambda: None,
    )
    try:
        expected = reference._decode_preview_frame(position - interval.start_tick / 1_000_000)
    finally:
        reference.close()
    actual_hash = hashlib.sha256(frames[-1].data).hexdigest()
    expected_hash = hashlib.sha256(expected.data).hexdigest()
    if errors or actual_hash != expected_hash:
        raise AssertionError("Edited preview differs from its exact legacy block reference")
    return {
        "backend": type(window.backend).__name__,
        "source_offset_seconds": actual_offset,
        "position_seconds": position,
        "sha256": actual_hash,
        "legacy_sha256": expected_hash,
        "exact_legacy": True,
    }


def _audit_edits(window, pump):
    count = len(window.segment_timeline.segment_items)
    duration = window.segment_timeline.edited_duration_seconds
    first_id = window.segment_timeline.segment_items[0].segment_id
    window._on_timeline_selection_changed((first_id,))
    window._seek_timeline(2.0)
    window._on_split_clicked(None)
    if len(window.segment_timeline.segment_items) != count + 1:
        raise AssertionError("Split callback did not create one extra block")
    first_id = window.segment_timeline.segment_items[0].segment_id
    window._on_timeline_selection_changed((first_id,))
    window._on_delete_segment_clicked(None)
    if not math.isclose(window.segment_timeline.edited_duration_seconds, duration - 2):
        raise AssertionError("Delete callback did not compact the edited duration")
    deleted = _audit_route_frame(window, 0.5, 2.5, pump)
    window._on_delete_segment_clicked(None)
    if not math.isclose(window.segment_timeline.edited_duration_seconds, duration):
        raise AssertionError("Restore callback did not restore the edited duration")
    restored = _audit_route_frame(window, 0.5, 0.5, pump)
    return {
        "split_blocks_before": count,
        "split_blocks_after": count + 1,
        "deleted_route": deleted,
        "restored_route": restored,
    }


def _optional_functionality(job, result, window, directory, pump, heartbeat):
    if not job.get("functionality"):
        return
    from framestudio import app_project

    report: dict[str, Any] = {"status": "running", "checks": {}, "errors": []}
    result["phase"] = "functionality"
    write_json(directory / "functionality.json", report)
    try:
        with (
            patch.object(
                app_project,
                "analyze_source_audio",
                side_effect=AssertionError("Import/edit/save/reopen must not scan audio"),
            ) as audio_scan,
            patch.object(
                app_project,
                "autosave_current_project",
                return_value=False,
            ),
        ):
            window._attach_project(window.project, None)
            heartbeat()
            report["checks"]["edits"] = _audit_edits(window, pump)
            project_path = directory / "functionality.framestudio.json"
            window._save_to(project_path)
            if not project_path.is_file():
                raise AssertionError("Save callback did not persist the owned project")
            before = window.project
            expected_count = len(window.segment_timeline.segment_items)
            window._on_reopen_clicked(None)
            deadline = time.monotonic() + job["timeout"]
            while window.project is before and time.monotonic() < deadline:
                pump()
                heartbeat()
            if (
                window.project is before
                or len(window.segment_timeline.segment_items) != expected_count
            ):
                raise AssertionError(
                    "Reopen callback did not reload the saved split/restored model"
                )
            report["checks"]["reopened_route"] = _audit_route_frame(window, 0.5, 0.5, pump)
            report["checks"]["saved_project_reopened"] = True
            report["checks"]["audio_scan_calls"] = audio_scan.call_count
            if audio_scan.call_count:
                raise AssertionError("Functionality charter unexpectedly started audio analysis")
            window._stop_backend()
            pump(0.1)
            children = sorted(set(owned_processes(os.getpid())) - {os.getpid()})
            report["checks"]["owned_child_pids_after_backend_close"] = children
            if children:
                raise AssertionError("Backend close left owned child processes alive")
        report["status"] = "complete"
    except Exception as error:
        report["status"] = "error"
        report["errors"].append(f"{type(error).__name__}: {error}")
        result["errors"].append(f"Functionality charter: {error}")
    finally:
        write_json(directory / "functionality.json", report)
        heartbeat()
    result["functionality"] = report


def worker(job_path: Path) -> int:
    job = json.loads(job_path.read_text())
    directory = job_path.parent
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    if job["baseline_overlay"]:
        import framestudio

        framestudio.__path__.insert(0, str(Path(job["baseline_overlay"]) / "framestudio"))

    result: dict[str, Any] = {
        "status": "running",
        "mode": job["mode"],
        "requested_preview_engine": {
            "active-cpu": "cpu",
            "active-cuda": "cuda",
            "active-sequential": "ffmpeg",
            "active-sequential-cuda": "ffmpeg-cuda",
            "active-sync": "ffmpeg",
            "active-ffmpeg": "ffmpeg",
        }.get(job["mode"], "production-policy" if job["mode"] == "production" else "ffmpeg"),
        "samples": [],
        "errors": [],
        "capability_gaps": [
            "after-paint is GTK frame-clock acknowledgement, not physical display latency",
            "GPU accounting is compute-process memory; graphics allocations may be omitted",
            "focus/triplicate/non-square SAR compatibility is not exercised by these unmodified fixtures",
        ],
        "cache_policy": "fresh editor per case; copied files reused across modes; OS caches not dropped",
        "production_preview_setting": os.environ.get("FRAMESTUDIO_PREVIEW_BACKEND", "auto"),
        "resource_policy": (
            "25ms target RSS sampling, 500ms target GPU sampling; reference decode phases excluded "
            "from reported application peaks but included in the safety limit"
        ),
        "ffmpeg_policy": (
            "guarded NOT unmodified: input decoder threads=1, filter threads=2"
            if job["guard"]
            else "unmodified"
        ),
    }
    window = None
    try:
        require_tool("ffmpeg")
        require_tool("ffprobe")
        import gi

        gi.require_version("Gtk", "4.0")
        gi.require_version("Gdk", "4.0")
        from gi.repository import Gio, GLib, Gtk

        from framestudio import app_project
        from framestudio.app import create_editor_application
        from framestudio.layout_plan import plan_project_layout
        from framestudio.media import probe_media
        from framestudio.model import Project

        if not Gtk.init_check():
            raise RuntimeError(
                "A working mapped GTK display is required; no headless timing fallback"
            )
        metadata = probe_media(Path(job["fixture"])).metadata()
        duration = float(metadata["duration_seconds"])
        paths = tuple(Path(path) for path in job["sources"])
        hashes_before = {path.name: sha256(path) for path in paths}
        project = Project.create_multi([(path, metadata) for path in paths])
        timeline = project.segment_timeline
        if timeline is None:
            raise RuntimeError("Project.create_multi did not create a timeline")
        layout = plan_project_layout(project)
        result.update(
            count=len(paths),
            source_duration_seconds=duration,
            true_encoded_duration_seconds=duration * len(paths),
            timeline_timing_mode=timeline.timing_mode,
            same_encoded_content_distinct_paths=True,
            unique_inodes=len({(path.stat().st_dev, path.stat().st_ino) for path in paths}),
            baseline_overlay=job["baseline_overlay"],
            fixture_sha256=sha256(Path(job["fixture"])),
            source_sha256_before=hashes_before,
            canvas={"width": layout.canvas.width, "height": layout.canvas.height},
        )
        if (layout.canvas.width, layout.canvas.height) != (1920, 1080):
            raise RuntimeError("Benchmark requires full 1920x1080 production output canvas")
        fps_text = str(metadata["frame_rate"])
        numerator, _, denominator = fps_text.partition("/")
        fps = float(numerator) / float(denominator or "1")
        durations = (duration,) * len(paths)
        source_items = tuple(
            (source.source_id, Path(source.path)) for source in project.sources or (project.source,)
        )

        experimental_factory = _experimental_backend_factory(
            job,
            source_items,
            layout,
            timeline,
            duration,
        )

        application, factory = create_editor_application(
            application_id=f"io.github.framestudio.largepreview.a{uuid.uuid4().hex}",
        )
        application.set_flags(application.get_flags() | Gio.ApplicationFlags.NON_UNIQUE)
        if not application.register(None):
            raise RuntimeError("Editor application registration failed")
        window = factory(application)
        window._autosave_current_project = lambda: False
        window._show_error = lambda message: result["errors"].append(str(message))
        context = GLib.MainContext.default()

        def heartbeat():
            (directory / "heartbeat").touch()

        pump = _pump_factory(context)
        callbacks_seen, paints, pending = _observe_window(window)
        guarded_popen = _logged_popen(directory, result, job)

        with (
            patch.object(app_project, "_create_composed_preview_backend", experimental_factory)
            if job["mode"] != "production"
            else _NoPatch(),
            patch.object(app_project, "_create_synchronized_preview_backend", experimental_factory)
            if job["mode"] != "production"
            else _NoPatch(),
            patch.object(subprocess, "Popen", guarded_popen),
        ):
            heartbeat()
            result["phase"] = "attach"
            write_json(directory / "result.json", result)
            started = time.monotonic()
            window._attach_project(project, None)
            result["attach_ms"] = (time.monotonic() - started) * 1000
            heartbeat()
            pump(0.2)
            backend = _connect_paints(window, result, pending, paints)
            fps = float(window.source_frame_rate)
            reference = _reference_factory(
                job,
                directory,
                source_items,
                layout,
                timeline,
                duration,
                fps,
                durations,
            )

            def stats():
                return _backend_stats(backend)

            dispatch = _dispatch_factory(
                job,
                directory,
                result,
                window,
                callbacks_seen,
                paints,
                pump,
                heartbeat,
                reference,
                stats,
                durations,
                fps,
            )
            _run_traces(job, result, len(paths), duration, dispatch)
            _measure_playback(job, result, window, duration, dispatch, paints, pump, heartbeat)
            _finish_backend(job, result, backend, stats)
            _optional_functionality(job, result, window, directory, pump, heartbeat)
        result["source_sha256_after"] = {path.name: sha256(path) for path in paths}
        result["sources_preserved"] = hashes_before == result["source_sha256_after"]
        result["fixture_preserved"] = sha256(Path(job["fixture"])) == result["fixture_sha256"]
        result["status"] = (
            "error"
            if result["errors"]
            or any("error" in sample for sample in result["samples"])
            or not result["sources_preserved"]
            or not result["fixture_preserved"]
            else "complete"
        )
        result["quality_mismatches_legacy"] = sum(
            sample.get("matches_legacy_single_block") is False for sample in result["samples"]
        )
        result["quality_mismatches_active_ffmpeg"] = sum(
            sample.get("matches_active_ffmpeg") is False for sample in result["samples"]
        )
        if result.get("quality_rejected") and result["status"] == "complete":
            result["status"] = "rejected-quality"
        result["legacy_exact_frame_comparisons"] = sum(
            "matches_legacy_single_block" in sample for sample in result["samples"]
        )
        result["latency_summary"] = {
            key: latency_summary(result["samples"], key)
            for key in (
                "request_handler_ms",
                "decode_callback_ms",
                "gtk_delivery_ms",
                "after_paint_ms",
            )
        }
    except Exception as error:
        result["status"] = "error"
        result["errors"].append(f"{type(error).__name__}: {error}")
    finally:
        write_json(directory / "result.json", result)
        if window is not None:
            if window.backend is not None:
                window.backend.close()
            window.destroy()
    return 0 if result["status"] == "complete" else 1


class _NoPatch:
    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


def acquire_lock(lock, wait_seconds: float) -> None:
    deadline = time.monotonic() + wait_seconds
    while True:
        try:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            return
        except BlockingIOError as error:
            if time.monotonic() >= deadline:
                raise SystemExit("Exclusive playback benchmark lock is busy") from error
            time.sleep(0.25)


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-dir", type=Path)
    parser.add_argument("--fixture", type=Path, action="append", help="Repeat for each resolution")
    parser.add_argument("--counts", type=int, nargs="+", default=[2, 20, 200])
    parser.add_argument("--trace-set", choices=("full", "bounded"), default="full")
    parser.add_argument("--repetitions", type=int, default=1)
    parser.add_argument("--max-case-seconds", type=float, default=60)
    parser.add_argument("--lock-wait-seconds", type=float, default=0)
    parser.add_argument("--functionality", action="store_true")
    parser.add_argument(
        "--modes",
        choices=MODES,
        nargs="+",
        default=list(MODES),
        help="active-sync/active-ffmpeg are naive rejected color controls; cpu/cuda use the "
        "sequential adapter and explicitly report fallback rather than claiming native decoding",
    )
    parser.add_argument(
        "--baseline-overlay", type=Path, help="Trusted package overlay root containing framestudio/"
    )
    parser.add_argument(
        "--timeout", type=float, default=15, help="Seconds without completed request/progress"
    )
    parser.add_argument("--max-rss-mib", type=int, default=2048)
    parser.add_argument("--playback-seconds", type=float, default=3)
    parser.add_argument(
        "--unmodified-ffmpeg",
        "--no-guard",
        action="store_true",
        help="Disable guarded input/filter thread limits",
    )
    parser.add_argument("--worker", type=Path, help=argparse.SUPPRESS)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.worker:
        return worker(args.worker)
    if (
        args.artifact_dir is None
        or min(args.counts) < 2
        or args.timeout <= 0
        or args.max_rss_mib <= 0
        or args.playback_seconds < 0
        or args.repetitions < 1
        or args.max_case_seconds <= 0
        or args.lock_wait_seconds < 0
    ):
        raise SystemExit("Require --artifact-dir, counts >=2, positive timeout/RSS, playback >=0")
    directory = args.artifact_dir.resolve()
    if directory.parts[1:2] == ("tmp",) or directory.parts[1:3] == ("var", "tmp"):
        raise SystemExit("Artifact directories under /tmp or /var/tmp are forbidden")
    fixtures = args.fixture or [
        FIXTURES / f"high-detail-{resolution}.mp4" for resolution in ("1920x1080", "3840x2160")
    ]
    for fixture in fixtures:
        if not fixture.is_file():
            raise SystemExit(f"Fixture unavailable: {fixture.name}; pass --fixture")
    require_tool("ffmpeg")
    require_tool("ffprobe")
    with LOCK.open("a") as lock:
        acquire_lock(lock, args.lock_wait_seconds)
        directory.mkdir(parents=True, exist_ok=False)
        results = []
        for fixture_index, fixture in enumerate(fixtures):
            fixture = fixture.resolve()
            sources = copy_sources(
                fixture, directory / f"fixture-{fixture_index}", max(args.counts)
            )
            for count in args.counts:
                for mode in args.modes:
                    case_dir = directory / f"fixture-{fixture_index}-{count}-{mode}"
                    case_dir.mkdir()
                    job = {
                        "mode": mode,
                        "fixture": str(fixture),
                        "sources": [str(path) for path in sources[:count]],
                        "baseline_overlay": str(args.baseline_overlay.resolve())
                        if args.baseline_overlay
                        else None,
                        "timeout": args.timeout,
                        "max_case_seconds": args.max_case_seconds,
                        "trace_set": args.trace_set,
                        "repetitions": args.repetitions,
                        "functionality": args.functionality,
                        "playback_seconds": args.playback_seconds,
                        "guard": not args.unmodified_ffmpeg,
                        "fixture_sha256": sha256(fixture),
                    }
                    result = run_case(job, case_dir, args.timeout, args.max_rss_mib * 1024 * 1024)
                    results.append({"case": case_dir.name, **result})
                    write_json(directory / "results.json", results)
        return 1 if any(result.get("status") != "complete" for result in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
