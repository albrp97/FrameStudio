#!/usr/bin/env python3
"""Run a reproducible, dependency-free cross-model restoration benchmark."""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import platform
import resource
import shutil
import statistics
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from datetime import date
from fractions import Fraction
from pathlib import Path
from typing import Any, Iterable, Mapping

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = Path(__file__).with_name("restoration_candidates.json")
DEFAULT_REUSE_ROOT = Path.home() / "Documents/edit/restore-benchmark-20260826"
TARGET_WIDTH = 1920
TARGET_HEIGHT = 1080
WINDOW_SECONDS = 15.0
WINDOW_COUNT = 3
WINDOW_SEED = 770
WARM_RUNS = 2
EXPECTED_CANDIDATE_NAMES = {
    "Topaz Video AI Gaia",
    "Nomos2",
    "4xNomos2_otf_esrgan",
    "EDVR",
    "BasicVSR",
    "BasicVSR++",
    "TecoGAN",
    "RealESRGAN x4plus",
    "Video2X wrapper (RealESRGAN)",
}
TERMINAL_CANDIDATE_STATUSES = {
    "passed",
    "failed",
    "unavailable",
    "excluded-license",
    "not-comparable",
}


@dataclass(frozen=True)
class GpuSample:
    name: str
    utilization_percent: float
    memory_used_mb: float
    power_watts: float

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "utilization_percent": self.utilization_percent,
            "memory_used_mb": self.memory_used_mb,
            "power_watts": self.power_watts,
        }


@dataclass(frozen=True)
class CommandRun:
    status: str
    wall_seconds: float
    returncode: int | None
    command: tuple[str, ...]
    log: str
    stderr_tail: str | None
    output_bytes: int
    resources: dict[str, float]
    gpu: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "wall_seconds": self.wall_seconds,
            "returncode": self.returncode,
            "command": list(self.command),
            "log": self.log,
            "stderr_tail": self.stderr_tail,
            "output_bytes": self.output_bytes,
            "resources": self.resources,
            "gpu": self.gpu,
        }


def load_manifest(path: Path = DEFAULT_MANIFEST) -> dict[str, Any]:
    """Load and validate the versioned candidate manifest."""

    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"could not load candidate manifest: {path.name}") from error
    if not isinstance(manifest, dict):
        raise ValueError("candidate manifest must be a JSON object")
    candidates = manifest.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        raise ValueError("candidate manifest must contain candidates")
    identifiers: set[str] = set()
    names: set[str] = set()
    for candidate in candidates:
        if not isinstance(candidate, dict):
            raise ValueError("candidate manifest contains a non-object candidate")
        identifier = candidate.get("id")
        name = candidate.get("name")
        if not isinstance(identifier, str) or not identifier:
            raise ValueError("every candidate needs a non-empty id")
        if not isinstance(name, str) or not name:
            raise ValueError(f"candidate {identifier} needs a non-empty name")
        if identifier in identifiers:
            raise ValueError(f"duplicate candidate id: {identifier}")
        identifiers.add(identifier)
        names.add(name)
        runner = candidate.get("runner")
        if not isinstance(runner, str) or not runner:
            raise ValueError(f"candidate {identifier} needs a runner")
    missing_names = EXPECTED_CANDIDATE_NAMES - names
    if missing_names:
        missing = ", ".join(sorted(missing_names))
        raise ValueError(f"manifest is missing requested candidates: {missing}")
    return manifest


def report_path(path: Path, root: Path | None = None) -> str:
    """Return a local-data path without exposing an absolute private path."""

    resolved = path.expanduser().resolve()
    if root is not None:
        resolved_root = root.expanduser().resolve()
        try:
            return resolved.relative_to(resolved_root).as_posix()
        except ValueError:
            pass
    try:
        return f"~/{resolved.relative_to(Path.home()).as_posix()}"
    except ValueError:
        return resolved.name


def redact_text(text: str, replacements: Mapping[str, str]) -> str:
    """Redact known local paths before storing commands or logs."""

    redacted = text
    for original, replacement in sorted(
        replacements.items(),
        key=lambda item: len(item[0]),
        reverse=True,
    ):
        if original:
            redacted = redacted.replace(original, replacement)
    return redacted


def redact_command(command: Iterable[str], replacements: Mapping[str, str]) -> tuple[str, ...]:
    return tuple(redact_text(str(argument), replacements) for argument in command)


def _parse_rate(value: Any) -> Fraction | None:
    if not isinstance(value, str) or value in {"", "0/0", "N/A"}:
        return None
    try:
        rate = Fraction(value)
    except (ValueError, ZeroDivisionError):
        return None
    return rate if rate > 0 else None


def _parse_frame_count(stream: Mapping[str, Any]) -> int | None:
    for key in ("nb_read_frames", "nb_frames"):
        value = stream.get(key)
        if value in {None, "", "N/A"} or not isinstance(value, (str, int, float)):
            continue
        try:
            return int(value)
        except (TypeError, ValueError):
            continue
    return None


def _parse_optional_int(value: Any) -> int | None:
    if value in {None, "", "N/A"}:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def probe_media(
    path: Path,
    ffprobe: str = "ffprobe",
    *,
    timeout_seconds: float = 30,
) -> dict[str, Any]:
    """Read the fields needed for the common output contract."""

    command = [
        ffprobe,
        "-v",
        "error",
        "-count_frames",
        "-show_streams",
        "-show_format",
        "-of",
        "json",
        str(path),
    ]
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout_seconds,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise RuntimeError("ffprobe could not inspect the media") from error
    if result.returncode != 0:
        raise RuntimeError("ffprobe could not inspect the media")
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise RuntimeError("ffprobe returned malformed JSON") from error
    streams = payload.get("streams")
    format_data = payload.get("format")
    if not isinstance(streams, list) or not isinstance(format_data, dict):
        raise ValueError("ffprobe output is missing streams or format")
    video = next(
        (stream for stream in streams if stream.get("codec_type") == "video"),
        None,
    )
    if not isinstance(video, dict):
        raise ValueError("media has no video stream")
    audio = next(
        (stream for stream in streams if stream.get("codec_type") == "audio"),
        None,
    )
    duration = format_data.get("duration")
    frame_rate = _parse_rate(video.get("avg_frame_rate")) or _parse_rate(video.get("r_frame_rate"))
    frame_count = _parse_frame_count(video)
    if (
        duration in {None, "N/A"}
        or not isinstance(duration, (str, int, float))
        or frame_rate is None
        or frame_count is None
    ):
        raise ValueError("ffprobe output lacks duration, frame rate, or frame count")
    try:
        parsed_duration = float(duration)
        width = int(video["width"])
        height = int(video["height"])
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError("ffprobe output has invalid media metadata") from error
    return {
        "duration_seconds": round(parsed_duration, 6),
        "width": width,
        "height": height,
        "fps": f"{frame_rate.numerator}/{frame_rate.denominator}",
        "frame_count": frame_count,
        "video_codec": str(video.get("codec_name", "")),
        "pixel_format": str(video.get("pix_fmt", "")),
        "video_bitrate": _parse_optional_int(video.get("bit_rate")),
        "audio": audio is not None,
        "audio_codec": None if audio is None else str(audio.get("codec_name", "")),
        "audio_bitrate": (None if audio is None else _parse_optional_int(audio.get("bit_rate"))),
        "audio_sample_rate": (None if audio is None else int(audio.get("sample_rate", 0))),
        "audio_channels": None if audio is None else int(audio.get("channels", 0)),
        "container": str(format_data.get("format_name", "")),
        "bitrate": _parse_optional_int(format_data.get("bit_rate")),
        "size_bytes": path.stat().st_size,
    }


def verify_output(
    metrics: Mapping[str, Any],
    fixture: Mapping[str, Any],
    *,
    width: int = TARGET_WIDTH,
    height: int = TARGET_HEIGHT,
) -> dict[str, Any]:
    """Verify dimensions, native frame rate/count, audio, and playability inputs."""

    expected_rate = _parse_rate(str(fixture.get("fps", "")))
    actual_rate = _parse_rate(str(metrics.get("fps", "")))
    expected_audio = bool(fixture.get("audio"))
    duration = float(fixture.get("duration_seconds", 0.0))
    tolerance = max(0.25, 2.0 / float(expected_rate or Fraction(1, 1)))
    checks = {
        "duration_matches": abs(float(metrics.get("duration_seconds", 0.0)) - duration)
        <= tolerance,
        "width_matches": metrics.get("width") == width,
        "height_matches": metrics.get("height") == height,
        "fps_matches": actual_rate == expected_rate,
        "frame_count_matches": metrics.get("frame_count") == fixture.get("frame_count"),
        "video_codec_matches": metrics.get("video_codec") == "h264",
        "pixel_format_matches": metrics.get("pixel_format") == "yuv420p",
        "audio_matches": bool(metrics.get("audio")) is expected_audio,
        "audio_codec_matches": (not expected_audio or metrics.get("audio_codec") == "aac"),
        "audio_sample_rate_matches": (
            not expected_audio or metrics.get("audio_sample_rate") == 48000
        ),
        "audio_channels_matches": (not expected_audio or metrics.get("audio_channels") == 2),
        "container_matches": "mp4"
        in {part.strip() for part in str(metrics.get("container", "")).split(",")},
    }
    return {
        "expected_duration_seconds": duration,
        "duration_tolerance_seconds": tolerance,
        "expected_dimensions": f"{width}x{height}",
        "expected_fps": None if expected_rate is None else str(expected_rate),
        "expected_frame_count": fixture.get("frame_count"),
        "checks": checks,
        "passed": all(checks.values()),
    }


def is_playable(path: Path, ffmpeg: str = "ffmpeg") -> dict[str, Any]:
    try:
        result = subprocess.run(
            [ffmpeg, "-v", "error", "-i", str(path), "-f", "null", "-"],
            capture_output=True,
            text=True,
            check=False,
            timeout=120,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        return {"passed": False, "error": error.__class__.__name__}
    return {
        "passed": result.returncode == 0,
        "error": None if result.returncode == 0 else "FFmpeg decode failed",
    }


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def choose_windows(
    duration_seconds: float,
    *,
    count: int = WINDOW_COUNT,
    window_seconds: float = WINDOW_SECONDS,
    seed: int = WINDOW_SEED,
) -> list[dict[str, float]]:
    """Select deterministic, non-overlapping windows without source metadata."""

    if duration_seconds < count * window_seconds + (count - 1) * 0.5:
        raise ValueError("source is too short for the benchmark fixture")
    maximum_start = duration_seconds - window_seconds
    starts: list[float] = []
    for attempt in range(10000):
        digest = hashlib.sha256(f"{seed}:{attempt}".encode("ascii")).digest()
        fraction = int.from_bytes(digest[:8], "big") / float(2**64)
        candidate = round(fraction * maximum_start, 3)
        if all(abs(candidate - existing) >= window_seconds + 0.5 for existing in starts):
            starts.append(candidate)
        if len(starts) == count:
            break
    if len(starts) != count:
        spacing = (maximum_start - 0.5 * (count - 1)) / max(1, count - 1)
        starts = [round(index * spacing, 3) for index in range(count)]
    starts.sort()
    return [
        {
            "index": float(index + 1),
            "start_seconds": start,
            "end_seconds": round(start + window_seconds, 3),
        }
        for index, start in enumerate(starts)
    ]


def _partial_path(path: Path) -> Path:
    return path.with_name(f"{path.stem}.partial{path.suffix}")


def _usage() -> resource.struct_rusage:
    return resource.getrusage(resource.RUSAGE_CHILDREN)


def _resource_summary(
    before: resource.struct_rusage,
    after: resource.struct_rusage,
) -> dict[str, float]:
    return {
        "child_user_seconds": round(after.ru_utime - before.ru_utime, 4),
        "child_system_seconds": round(after.ru_stime - before.ru_stime, 4),
        "child_max_rss_kb": round(after.ru_maxrss, 1),
    }


def _query_gpu(nvidia_smi: str | None) -> GpuSample | None:
    if not nvidia_smi:
        return None
    command = [
        nvidia_smi,
        "--query-gpu=name,utilization.gpu,memory.used,power.draw",
        "--format=csv,noheader,nounits",
    ]
    try:
        result = subprocess.run(
            command,
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
        return GpuSample(
            name=fields[0],
            utilization_percent=float(fields[1]),
            memory_used_mb=float(fields[2]),
            power_watts=float(fields[3]),
        )
    except ValueError:
        return None


def _sample_gpu(
    nvidia_smi: str | None,
    stop_event: threading.Event,
    samples: list[GpuSample],
) -> None:
    while not stop_event.wait(0.25):
        sample = _query_gpu(nvidia_smi)
        if sample is not None:
            samples.append(sample)


def _gpu_summary(
    before: GpuSample | None,
    samples: list[GpuSample],
    after: GpuSample | None,
) -> dict[str, Any]:
    all_samples = [sample for sample in [before, *samples, after] if sample is not None]
    if not all_samples:
        return {
            "available": False,
            "sample_count": 0,
            "samples": [],
        }
    return {
        "available": True,
        "sample_count": len(all_samples),
        "name": all_samples[0].name,
        "utilization_average_percent": round(
            statistics.fmean(sample.utilization_percent for sample in all_samples),
            2,
        ),
        "utilization_peak_percent": round(
            max(sample.utilization_percent for sample in all_samples),
            2,
        ),
        "memory_peak_mb": round(
            max(sample.memory_used_mb for sample in all_samples),
            2,
        ),
        "power_average_watts": round(
            statistics.fmean(sample.power_watts for sample in all_samples),
            2,
        ),
        "power_peak_watts": round(
            max(sample.power_watts for sample in all_samples),
            2,
        ),
        "before": None if before is None else before.as_dict(),
        "after": None if after is None else after.as_dict(),
        "samples": [sample.as_dict() for sample in all_samples],
    }


def run_command(
    command: list[str],
    *,
    outputs: tuple[Path, ...],
    log_path: Path,
    replacements: Mapping[str, str],
    ffmpeg: str,
    nvidia_smi: str | None,
    timeout_seconds: float | None = None,
) -> CommandRun:
    """Run one bounded stage and retain redacted command/resource evidence."""

    before_usage = _usage()
    before_gpu = _query_gpu(nvidia_smi)
    samples: list[GpuSample] = []
    stop_event = threading.Event()
    monitor = threading.Thread(
        target=_sample_gpu,
        args=(nvidia_smi, stop_event, samples),
        daemon=True,
    )
    monitor.start()
    started = time.monotonic()
    returncode: int | None = None
    stderr = ""
    stdout = ""
    status = "failed"
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout_seconds,
        )
        returncode = result.returncode
        stderr = result.stderr
        stdout = result.stdout
        status = "passed" if result.returncode == 0 else "failed"
    except subprocess.TimeoutExpired:
        stderr = f"{ffmpeg} timed out"
        status = "failed"
    except OSError as error:
        stderr = f"{ffmpeg} could not start: {error.__class__.__name__}"
        status = "failed"
    finally:
        stop_event.set()
        monitor.join(timeout=2)
    elapsed = round(time.monotonic() - started, 4)
    after_gpu = _query_gpu(nvidia_smi)
    after_usage = _usage()
    redacted_command = redact_command(command, replacements)
    redacted_stderr = redact_text(stderr, replacements)
    redacted_stdout = redact_text(stdout, replacements)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(
        "command: "
        + " ".join(redacted_command)
        + "\n\nstdout:\n"
        + redacted_stdout
        + "\n\nstderr:\n"
        + redacted_stderr,
        encoding="utf-8",
    )
    output_bytes = sum(path.stat().st_size for path in outputs if path.is_file())
    if status == "passed" and outputs and output_bytes <= 0:
        status = "failed"
        redacted_stderr = "command completed without an output artifact"
    if status != "passed":
        for path in outputs:
            if path.is_file():
                path.unlink()
        output_bytes = 0
    stderr_tail = (
        None
        if status == "passed"
        else (redacted_stderr.strip().splitlines() or ["command failed"])[-1][:500]
    )
    return CommandRun(
        status=status,
        wall_seconds=elapsed,
        returncode=returncode,
        command=redacted_command,
        log=report_path(log_path),
        stderr_tail=stderr_tail,
        output_bytes=output_bytes,
        resources=_resource_summary(before_usage, after_usage),
        gpu=_gpu_summary(before_gpu, samples, after_gpu),
    )


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _scale_filter() -> str:
    return (
        f"scale={TARGET_WIDTH}:{TARGET_HEIGHT}:"
        "force_original_aspect_ratio=decrease,"
        f"pad={TARGET_WIDTH}:{TARGET_HEIGHT}:(ow-iw)/2:(oh-ih)/2:"
        "color=black,setsar=1"
    )


def detect_video_encoder(ffmpeg: str) -> str:
    try:
        result = subprocess.run(
            [ffmpeg, "-hide_banner", "-encoders"],
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired):
        return "libx264"
    return "h264_nvenc" if result.returncode == 0 and "h264_nvenc" in result.stdout else "libx264"


def build_ffmpeg_command(
    filter_spec: str,
    source: Path,
    destination: Path,
    *,
    ffmpeg: str,
    video_encoder: str,
) -> list[str]:
    video_filter = ",".join(part for part in (filter_spec, _scale_filter()) if part)
    command = [
        ffmpeg,
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-fflags",
        "+genpts",
        "-i",
        str(source),
        "-map",
        "0:v:0",
        "-map",
        "0:a?",
        "-vf",
        video_filter,
        "-fps_mode",
        "passthrough",
    ]
    if video_encoder == "h264_nvenc":
        command.extend(["-c:v", "h264_nvenc", "-preset", "p5", "-cq", "18"])
    else:
        command.extend(["-c:v", "libx264", "-preset", "medium", "-crf", "18"])
    command.extend(
        [
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-ar",
            "48000",
            "-ac",
            "2",
            "-af",
            "aresample=async=1:first_pts=0,apad",
            "-movflags",
            "+faststart",
            "-shortest",
            str(destination),
        ]
    )
    return command


def _fixture_clip_command(
    source: Path,
    destination: Path,
    start_seconds: float,
    *,
    ffmpeg: str,
) -> list[str]:
    return [
        ffmpeg,
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(source),
        "-ss",
        f"{start_seconds:.3f}",
        "-t",
        f"{WINDOW_SECONDS:.3f}",
        "-map",
        "0:v:0",
        "-map",
        "0:a?",
        "-c:v",
        "libx264",
        "-preset",
        "medium",
        "-crf",
        "18",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-ar",
        "48000",
        "-ac",
        "2",
        "-movflags",
        "+faststart",
        "-shortest",
        str(destination),
    ]


def _concat_fixture_command(
    list_path: Path,
    destination: Path,
    *,
    ffmpeg: str,
    frame_rate: str,
    frame_count: int,
) -> list[str]:
    return [
        ffmpeg,
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(list_path),
        "-map",
        "0:v:0",
        "-map",
        "0:a?",
        "-vf",
        f"fps={frame_rate},setpts=N/({frame_rate}*TB)",
        "-fps_mode",
        "cfr",
        "-frames:v",
        str(frame_count),
        "-c:v",
        "libx264",
        "-preset",
        "medium",
        "-crf",
        "18",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-ar",
        "48000",
        "-ac",
        "2",
        "-af",
        "aresample=async=1:first_pts=0",
        "-movflags",
        "+faststart",
        "-shortest",
        str(destination),
    ]


def _write_concat_list(paths: Iterable[Path], destination: Path) -> None:
    lines = []
    for path in paths:
        escaped = str(path).replace("'", "'\\''")
        lines.append(f"file '{escaped}'")
    _write_text(destination, "\n".join(lines) + "\n")


def _candidate_replacements(
    *,
    source: Path | None,
    fixture: Path,
    output_root: Path,
    repository_root: Path = REPOSITORY_ROOT,
) -> dict[str, str]:
    replacements = {
        str(fixture.resolve()): "<FIXTURE>",
        str(output_root.resolve()): "<OUTPUT_DIR>",
        str(repository_root.resolve()): "<REPOSITORY>",
        str(Path.home().resolve()): "~",
    }
    if source is not None:
        replacements[str(source.resolve())] = "<SOURCE>"
    return replacements


def build_fixture(
    source: Path,
    output_root: Path,
    *,
    ffmpeg: str,
    ffprobe: str,
    nvidia_smi: str | None,
    window_count: int = WINDOW_COUNT,
) -> tuple[Path, dict[str, Any], dict[str, Any]]:
    """Build a deterministic multi-window fixture from a local source."""

    source_metadata = probe_media(source, ffprobe, timeout_seconds=180)
    source_hash_before = file_sha256(source)
    fixture_root = output_root / "fixture"
    clips_root = fixture_root / "clips"
    clips_root.mkdir(parents=True, exist_ok=True)
    windows = choose_windows(source_metadata["duration_seconds"], count=window_count)
    fixture_name = f"fixture-{int(WINDOW_SECONDS * window_count)}s.mp4"
    replacements = _candidate_replacements(
        source=source,
        fixture=fixture_root / fixture_name,
        output_root=output_root,
    )
    clips: list[Path] = []
    for window in windows:
        clip = clips_root / f"window-{int(window['index']):02d}.mp4"
        partial = _partial_path(clip)
        run = run_command(
            _fixture_clip_command(
                source,
                partial,
                window["start_seconds"],
                ffmpeg=ffmpeg,
            ),
            outputs=(partial,),
            log_path=output_root / "logs" / f"fixture-window-{int(window['index']):02d}.log",
            replacements=replacements,
            ffmpeg=ffmpeg,
            nvidia_smi=nvidia_smi,
            timeout_seconds=300,
        )
        if run.status != "passed":
            raise RuntimeError(f"fixture window {int(window['index'])} failed")
        partial.replace(clip)
        clips.append(clip)
    list_path = fixture_root / "concat-list.txt"
    _write_concat_list(clips, list_path)
    fixture = fixture_root / fixture_name
    partial_fixture = _partial_path(fixture)
    frame_rate = Fraction(str(source_metadata["fps"]))
    frame_count = int(frame_rate * WINDOW_SECONDS) * window_count
    run = run_command(
        _concat_fixture_command(
            list_path,
            partial_fixture,
            ffmpeg=ffmpeg,
            frame_rate=str(source_metadata["fps"]),
            frame_count=frame_count,
        ),
        outputs=(partial_fixture,),
        log_path=output_root / "logs" / "fixture-concat.log",
        replacements=replacements,
        ffmpeg=ffmpeg,
        nvidia_smi=nvidia_smi,
        timeout_seconds=300,
    )
    if run.status != "passed":
        raise RuntimeError("fixture concatenation failed")
    partial_fixture.replace(fixture)
    metadata = probe_media(fixture, ffprobe)
    source_hash_after = file_sha256(source)
    selection = {
        "seed": WINDOW_SEED,
        "window_seconds": WINDOW_SECONDS,
        "window_count": window_count,
        "expected_frame_count": frame_count,
        "windows": windows,
        "source": "local source path redacted",
        "fixture": report_path(fixture, output_root),
        "source_metadata": source_metadata,
        "fixture_metadata": metadata,
    }
    _write_json(fixture_root / "selection.json", selection)
    _write_json(fixture_root / "metadata.json", metadata)
    return (
        fixture,
        metadata,
        {
            "protected_input": "source",
            "_protected_path": str(source),
            "source_hash_before": source_hash_before,
            "source_hash_after_fixture": source_hash_after,
            "source_hash_after_runs": None,
            "unchanged": source_hash_before == source_hash_after,
            "source_metadata": source_metadata,
            "selection": selection,
        },
    )


def reuse_fixture(
    fixture: Path,
    output_root: Path,
    *,
    ffprobe: str,
) -> tuple[Path, dict[str, Any], dict[str, Any]]:
    if not fixture.is_file():
        raise ValueError(f"fixture does not exist: {fixture.name}")
    metadata = probe_media(fixture, ffprobe)
    protected_hash = file_sha256(fixture)
    _write_json(output_root / "fixture" / "metadata.json", metadata)
    return (
        fixture,
        metadata,
        {
            "protected_input": "existing TICKET-077 fixture",
            "_protected_path": str(fixture),
            "source_hash_before": protected_hash,
            "source_hash_after_fixture": protected_hash,
            "source_hash_after_runs": None,
            "unchanged": True,
            "source_metadata": metadata,
            "selection": {
                "reused": True,
                "source": "existing TICKET-077 fixture",
                "fixture": report_path(fixture),
            },
        },
    )


def _candidate_base(candidate: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "id": candidate["id"],
        "name": candidate["name"],
        "category": candidate.get("category", "unknown"),
        "runner": candidate["runner"],
        "version": candidate.get("version"),
        "backend": candidate.get("backend"),
        "underlying_model": candidate.get("underlying_model"),
        "configuration": candidate.get("configuration"),
        "previous_configuration": candidate.get("previous_configuration"),
        "adapter": candidate.get("adapter"),
        "wrapper": bool(candidate.get("wrapper", False)),
        "underlying_model_required": bool(candidate.get("underlying_model_required", False)),
        "filter_mode": candidate.get("filter_mode"),
        "temporal": bool(candidate.get("temporal", False)),
        "license": candidate.get("license", {}),
        "status": "failed",
        "reason": None,
        "availability": {},
        "execution": {},
        "performance": {
            "status": "not-run",
            "setup_seconds": None,
            "inference_seconds": None,
            "normalization_seconds": None,
            "final_encode_seconds": None,
            "end_to_end_seconds": None,
            "processed_source_fps": None,
            "output_fps": None,
            "real_time_factor": None,
        },
        "resource_telemetry": {
            "status": "not-run",
            "cpu": {},
            "gpu": {},
            "temporary_storage_bytes": None,
        },
        "cleanup": {
            "status": "not-run",
            "partial_artifacts_removed": [],
        },
        "output": None,
        "visual_review": {
            "status": "pending",
            "contact_sheet": None,
        },
        "quality_metrics": {
            "status": "unavailable",
            "reason": "no clean aligned reference is available",
        },
    }


def _find_weight_matches(patterns: Iterable[str]) -> list[Path]:
    roots = [
        Path.home() / ".cache",
        Path.home() / ".local/share",
        Path.home() / "models",
        Path.home() / "Documents/edit",
    ]
    matches: list[Path] = []
    for root in roots:
        if not root.exists():
            continue
        for pattern in patterns:
            try:
                found = root.glob(pattern)
            except OSError:
                continue
            for path in found:
                if path.is_file() and path not in matches:
                    matches.append(path)
                if len(matches) >= 10:
                    return matches
    return matches


def discover_runtime(
    candidate: Mapping[str, Any],
    *,
    python_executable: str = sys.executable,
) -> dict[str, Any]:
    probe = candidate.get("runtime_probe", {})
    executables = [
        name
        for name in probe.get("executables", [])
        if isinstance(name, str) and shutil.which(name)
    ]
    executable_paths: list[str] = []
    for value in probe.get("executable_paths", []):
        if not isinstance(value, str):
            continue
        path = Path(value).expanduser()
        if path.is_file() and shutil.which(str(path)):
            executable_paths.append(report_path(path))
    modules: list[str] = []
    for module in probe.get("modules", []):
        if not isinstance(module, str):
            continue
        try:
            available = importlib.util.find_spec(module) is not None
        except (ImportError, ValueError):
            available = False
        if available:
            modules.append(module)
    weight_matches = _find_weight_matches(
        pattern for pattern in probe.get("weight_patterns", []) if isinstance(pattern, str)
    )
    return {
        "python": Path(python_executable).name,
        "executables": executables,
        "executable_paths": executable_paths,
        "modules": modules,
        "weight_count": len(weight_matches),
        "weight_names": [path.name for path in weight_matches],
    }


def _external_candidate_result(candidate: Mapping[str, Any]) -> dict[str, Any]:
    result = _candidate_base(candidate)
    discovery = discover_runtime(candidate)
    result["availability"] = discovery
    license_data = candidate.get("license", {})
    license_status = license_data.get("status")
    has_runtime = bool(
        discovery["executables"]
        or discovery.get("executable_paths")
        or discovery["modules"]
        or discovery["weight_count"]
    )
    if candidate.get("id") == "topaz-gaia" and not discovery["executables"]:
        result["status"] = "unavailable"
        result["reason"] = (
            "no licensed local Topaz Video AI installation or Gaia executable was discovered"
        )
        return result
    if not has_runtime:
        result["status"] = "unavailable"
        result["reason"] = (
            "required executable, Python module, or model weight was not "
            "found in the configured local search scope"
        )
        return result
    if license_status == "unverified":
        result["status"] = "excluded-license"
        result["reason"] = (
            "exact checkpoint and upstream license terms are unresolved; "
            "execution is not permitted by the benchmark contract"
        )
        return result
    result["status"] = "not-comparable"
    result["reason"] = (
        f"runtime capability was discovered, but the declared adapter "
        f"{candidate.get('adapter', 'unknown')} is not configured for a "
        "pinned video run"
    )
    if candidate.get("wrapper"):
        result["reason"] += (
            "; underlying model, backend, and filter-only command must be declared before execution"
        )
    return result


def _load_reuse_index(reuse_root: Path) -> dict[str, Any]:
    report = reuse_root / "rve-restoration-benchmark.json"
    if not report.is_file():
        return {}
    try:
        payload = json.loads(report.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    candidates = payload.get("candidates")
    if not isinstance(candidates, list):
        return {}
    return {
        str(item["id"]): item
        for item in candidates
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }


def _reused_candidate_result(
    candidate: Mapping[str, Any],
    reuse_root: Path,
    fixture: Mapping[str, Any],
    *,
    ffmpeg: str,
    ffprobe: str,
) -> dict[str, Any]:
    result = _candidate_base(candidate)
    reuse_id = candidate.get("reuse_id")
    if not isinstance(reuse_id, str):
        result["status"] = "unavailable"
        result["reason"] = "candidate has no valid TICKET-077 reuse identifier"
        return result
    reused = _load_reuse_index(reuse_root).get(reuse_id)
    if reused is None:
        result["status"] = "unavailable"
        result["reason"] = "TICKET-077 RVE result was not found in the reuse report"
        return result
    output_name = Path(str(reused.get("output", ""))).name
    output = reuse_root / "outputs" / output_name
    if not output.is_file():
        result["status"] = "unavailable"
        result["reason"] = "TICKET-077 output artifact is not present"
        return result
    try:
        metadata = probe_media(output, ffprobe)
    except (RuntimeError, ValueError, OSError) as error:
        result["status"] = "failed"
        result["reason"] = f"reused output probe failed: {error}"
        return result
    playability = is_playable(output, ffmpeg)
    verification = verify_output(metadata, fixture)
    result["availability"] = {
        "reuse_report": "TICKET-077",
        "artifact_present": True,
        "backend": reused.get("backend"),
        "model": reused.get("model"),
    }
    result["execution"] = {
        "provenance": "reused TICKET-077 measurement",
        "timing_granularity": "RVE inference and normalization measured separately",
        "cold_seconds": reused.get("rve_wall_seconds"),
        "normalization_seconds": reused.get("normalize_wall_seconds"),
        "warm_runs": [],
        "resources": {
            "gpu_max_memory_used_mb": reused.get("gpu_max_memory_used_mb"),
            "process_max_hwm_kb": reused.get("process_max_hwm_kb"),
            "gpu_samples": reused.get("gpu_samples", []),
        },
        "command": "redacted in source TICKET-077 evidence",
    }
    result["output"] = {
        "path": f"~/{output.relative_to(Path.home()).as_posix()}"
        if output.is_relative_to(Path.home())
        else output.name,
        "metadata": metadata,
        "playability": playability,
        "verification": verification,
        "size_bytes": output.stat().st_size,
    }
    result["performance"] = _performance_metrics(
        fixture,
        result["output"],
        setup_seconds=None,
        inference_seconds=reused.get("rve_wall_seconds"),
        normalization_seconds=reused.get("normalize_wall_seconds"),
        final_encode_seconds=reused.get("normalize_wall_seconds"),
        end_to_end_seconds=reused.get("wall_seconds"),
    )
    result["resource_telemetry"] = {
        "status": "reused",
        "cpu": {
            "child_user_seconds": reused.get("child_user_seconds"),
            "child_system_seconds": reused.get("child_system_seconds"),
            "child_max_rss_kb": reused.get("process_max_hwm_kb"),
        },
        "gpu": {
            "sample_count": reused.get("gpu_sample_count"),
            "samples": reused.get("gpu_samples", []),
            "memory_peak_mb": reused.get("gpu_max_memory_used_mb"),
        },
        "temporary_storage_bytes": None,
    }
    result["cleanup"] = {
        "status": "reused-artifact",
        "partial_artifacts_removed": [],
        "source_artifact_untouched": True,
    }
    if playability["passed"] and verification["passed"]:
        result["status"] = "passed"
        result["reason"] = "reused output satisfies the native-frame protocol"
    elif playability["passed"]:
        result["status"] = "not-comparable"
        failed_checks = [name for name, passed in verification["checks"].items() if not passed]
        result["reason"] = (
            "reused TICKET-077 output is playable but does not satisfy the "
            f"TICKET-078 native-frame contract: {', '.join(failed_checks)}"
        )
    else:
        result["status"] = "failed"
        result["reason"] = "reused output failed FFmpeg playability"
    return result


def _output_result(
    path: Path,
    fixture: Mapping[str, Any],
    *,
    ffmpeg: str,
    ffprobe: str,
    output_root: Path,
) -> dict[str, Any]:
    metadata = probe_media(path, ffprobe)
    playability = is_playable(path, ffmpeg)
    verification = verify_output(metadata, fixture)
    return {
        "path": report_path(path, output_root),
        "metadata": metadata,
        "playability": playability,
        "verification": verification,
        "size_bytes": path.stat().st_size,
    }


def _performance_metrics(
    fixture: Mapping[str, Any],
    output: Mapping[str, Any],
    *,
    setup_seconds: float | None,
    inference_seconds: float | None,
    normalization_seconds: float | None,
    final_encode_seconds: float | None,
    end_to_end_seconds: float | None,
) -> dict[str, Any]:
    source_rate = _parse_rate(str(fixture.get("fps", "")))
    output_rate = _parse_rate(str(output.get("metadata", {}).get("fps", "")))
    frame_count = output.get("metadata", {}).get("frame_count")
    timing_seconds = inference_seconds or end_to_end_seconds
    processed_source_fps = (
        round(float(frame_count) / timing_seconds, 3)
        if isinstance(frame_count, int) and timing_seconds and timing_seconds > 0
        else None
    )
    real_time_factor = (
        round(float(fixture.get("duration_seconds", 0.0)) / end_to_end_seconds, 3)
        if end_to_end_seconds and end_to_end_seconds > 0
        else None
    )
    return {
        "status": "measured",
        "setup_seconds": setup_seconds,
        "inference_seconds": inference_seconds,
        "normalization_seconds": normalization_seconds,
        "final_encode_seconds": final_encode_seconds,
        "end_to_end_seconds": end_to_end_seconds,
        "input_frames": fixture.get("frame_count"),
        "source_fps": None if source_rate is None else float(source_rate),
        "output_fps": None if output_rate is None else float(output_rate),
        "processed_source_fps": processed_source_fps,
        "real_time_factor": real_time_factor,
    }


def _directory_size(path: Path) -> int:
    if not path.exists():
        return 0
    if path.is_file():
        return path.stat().st_size
    return sum(item.stat().st_size for item in path.rglob("*") if item.is_file())


def _record_ffmpeg_telemetry(
    result: dict[str, Any],
    *,
    cold_run: CommandRun,
    warm_results: list[dict[str, Any]],
    run_root: Path,
    cold_partial: Path,
    output_root: Path,
) -> None:
    result["resource_telemetry"] = {
        "status": "measured",
        "cpu": cold_run.resources,
        "gpu": cold_run.gpu,
        "warm_runs": [
            {
                "cpu": run.get("resources", {}),
                "gpu": run.get("gpu", {}),
            }
            for run in warm_results
        ],
        "temporary_storage_bytes": _directory_size(run_root),
    }
    result["cleanup"] = {
        "status": "passed",
        "partial_artifacts_remaining": False,
        "partial_artifacts_removed": [report_path(cold_partial, output_root)],
    }


def _run_ffmpeg_candidate(
    candidate: Mapping[str, Any],
    fixture_path: Path,
    fixture: Mapping[str, Any],
    output_root: Path,
    *,
    ffmpeg: str,
    ffprobe: str,
    nvidia_smi: str | None,
    video_encoder: str,
    warm_runs: int,
) -> dict[str, Any]:
    result = _candidate_base(candidate)
    output_path = output_root / "outputs" / f"{candidate['id']}.mp4"
    run_root = output_root / "runs" / str(candidate["id"])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    run_root.mkdir(parents=True, exist_ok=True)
    replacements = _candidate_replacements(
        source=None,
        fixture=fixture_path,
        output_root=output_root,
    )
    command_runs: list[dict[str, Any]] = []
    cold_partial = _partial_path(output_path)
    cold_command = build_ffmpeg_command(
        str(candidate.get("filter", "")),
        fixture_path,
        cold_partial,
        ffmpeg=ffmpeg,
        video_encoder=video_encoder,
    )
    cold_run = run_command(
        cold_command,
        outputs=(cold_partial,),
        log_path=output_root / "logs" / f"{candidate['id']}-cold.log",
        replacements=replacements,
        ffmpeg=ffmpeg,
        nvidia_smi=nvidia_smi,
        timeout_seconds=1800,
    )
    command_runs.append(cold_run.as_dict())
    if cold_run.status != "passed":
        result["status"] = "failed"
        result["reason"] = cold_run.stderr_tail or "cold run failed"
        result["execution"] = {
            "provenance": "new local run",
            "timing_granularity": "FFmpeg decode, filter, and final encode combined",
            "video_encoder": video_encoder,
            "cold": cold_run.as_dict(),
            "warm_runs": [],
        }
        _record_ffmpeg_telemetry(
            result,
            cold_run=cold_run,
            warm_results=[],
            run_root=run_root,
            cold_partial=cold_partial,
            output_root=output_root,
        )
        return result
    cold_partial.replace(output_path)
    warm_results: list[dict[str, Any]] = []
    for index in range(warm_runs):
        warm_output = run_root / f"warm-{index + 1:02d}.mp4"
        warm_partial = _partial_path(warm_output)
        warm_command = build_ffmpeg_command(
            str(candidate.get("filter", "")),
            fixture_path,
            warm_partial,
            ffmpeg=ffmpeg,
            video_encoder=video_encoder,
        )
        warm_run = run_command(
            warm_command,
            outputs=(warm_partial,),
            log_path=output_root / "logs" / f"{candidate['id']}-warm-{index + 1:02d}.log",
            replacements=replacements,
            ffmpeg=ffmpeg,
            nvidia_smi=nvidia_smi,
            timeout_seconds=1800,
        )
        warm_data = warm_run.as_dict()
        if warm_run.status == "passed":
            warm_partial.replace(warm_output)
            try:
                warm_data["verification"] = _output_result(
                    warm_output,
                    fixture,
                    ffmpeg=ffmpeg,
                    ffprobe=ffprobe,
                    output_root=output_root,
                )["verification"]
            except (RuntimeError, ValueError, OSError) as error:
                warm_data["status"] = "failed"
                warm_data["error"] = f"warm output probe failed: {error}"
        warm_results.append(warm_data)
        command_runs.append(warm_data)
    try:
        output_data = _output_result(
            output_path,
            fixture,
            ffmpeg=ffmpeg,
            ffprobe=ffprobe,
            output_root=output_root,
        )
    except (RuntimeError, ValueError, OSError) as error:
        result["status"] = "failed"
        result["reason"] = f"output verification could not run: {error}"
        result["execution"] = {
            "provenance": "new local run",
            "timing_granularity": "FFmpeg decode, filter, and final encode combined",
            "video_encoder": video_encoder,
            "cold": cold_run.as_dict(),
            "warm_runs": warm_results,
        }
        _record_ffmpeg_telemetry(
            result,
            cold_run=cold_run,
            warm_results=warm_results,
            run_root=run_root,
            cold_partial=cold_partial,
            output_root=output_root,
        )
        output_path.unlink(missing_ok=True)
        return result
    result["availability"] = {
        "ffmpeg": True,
        "video_encoder": video_encoder,
    }
    result["execution"] = {
        "provenance": "new local run",
        "timing_granularity": "FFmpeg decode, filter, and final encode combined",
        "video_encoder": video_encoder,
        "cold": cold_run.as_dict(),
        "warm_runs": warm_results,
        "warm_median_seconds": (
            statistics.median(
                run["wall_seconds"] for run in warm_results if run.get("status") == "passed"
            )
            if any(run.get("status") == "passed" for run in warm_results)
            else None
        ),
        "warm_spread_seconds": (
            round(
                max(run["wall_seconds"] for run in warm_results if run.get("status") == "passed")
                - min(run["wall_seconds"] for run in warm_results if run.get("status") == "passed"),
                4,
            )
            if sum(run.get("status") == "passed" for run in warm_results) > 1
            else None
        ),
        "command_count": len(command_runs),
    }
    result["output"] = output_data
    result["performance"] = _performance_metrics(
        fixture,
        output_data,
        setup_seconds=0.0,
        inference_seconds=None,
        normalization_seconds=None,
        final_encode_seconds=cold_run.wall_seconds,
        end_to_end_seconds=cold_run.wall_seconds,
    )
    _record_ffmpeg_telemetry(
        result,
        cold_run=cold_run,
        warm_results=warm_results,
        run_root=run_root,
        cold_partial=cold_partial,
        output_root=output_root,
    )
    if output_data["playability"]["passed"] and output_data["verification"]["passed"]:
        result["status"] = "passed"
    else:
        failed_checks = [
            name for name, passed in output_data["verification"]["checks"].items() if not passed
        ]
        result["status"] = "failed"
        result["reason"] = "output integrity gate failed: " + ", ".join(failed_checks)
        output_path.unlink(missing_ok=True)
        result["output"] = None
    result["_commands"] = command_runs
    return result


def _contact_sheet(
    candidate: Mapping[str, Any],
    input_path: Path,
    output_root: Path,
    *,
    ffmpeg: str,
    timestamps: tuple[float, ...],
) -> dict[str, Any]:
    output = output_root / "contact-sheets" / f"{candidate['id']}.jpg"
    partial = output.with_name(f"{output.stem}.partial{output.suffix}")
    output.parent.mkdir(parents=True, exist_ok=True)
    frame_filters = [
        (
            f"[0:v]trim=start={timestamp}:end={timestamp + 0.1},"
            f"setpts=PTS-STARTPTS,select=eq(n\\,0),scale=480:-2[v{index}]"
        )
        for index, timestamp in enumerate(timestamps)
    ]
    filter_complex = ";".join(frame_filters)
    filter_complex += ";" + "".join(f"[v{index}]" for index in range(len(timestamps)))
    filter_complex += f"hstack=inputs={len(timestamps)}:shortest=1"
    command = [
        ffmpeg,
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(input_path),
        "-filter_complex",
        filter_complex,
        "-frames:v",
        "1",
        "-q:v",
        "3",
        str(partial),
    ]
    replacements = _candidate_replacements(
        source=None,
        fixture=input_path,
        output_root=output_root,
    )
    started = time.monotonic()
    try:
        run = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            timeout=180,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        return {
            "status": "failed",
            "error": error.__class__.__name__,
            "path": None,
        }
    if run.returncode != 0 or not partial.is_file():
        partial.unlink(missing_ok=True)
        return {
            "status": "failed",
            "error": redact_text(
                (run.stderr.strip().splitlines() or ["contact sheet failed"])[-1],
                replacements,
            )[:500],
            "path": None,
        }
    partial.replace(output)
    return {
        "status": "passed",
        "wall_seconds": round(time.monotonic() - started, 4),
        "path": report_path(output, output_root),
        "command": list(redact_command(command, replacements)),
    }


def _availability_csv(results: Iterable[Mapping[str, Any]], path: Path) -> None:
    fieldnames = [
        "id",
        "name",
        "status",
        "category",
        "runner",
        "license",
        "license_status",
        "reason",
        "executables",
        "executable_paths",
        "modules",
        "weight_count",
        "adapter",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            license_data = result.get("license", {})
            availability = result.get("availability", {})
            writer.writerow(
                {
                    "id": result.get("id", ""),
                    "name": result.get("name", ""),
                    "status": result.get("status", ""),
                    "category": result.get("category", ""),
                    "runner": result.get("runner", ""),
                    "license": license_data.get("name", ""),
                    "license_status": license_data.get("status", ""),
                    "reason": result.get("reason") or "",
                    "executables": ",".join(availability.get("executables", [])),
                    "executable_paths": ",".join(availability.get("executable_paths", [])),
                    "modules": ",".join(availability.get("modules", [])),
                    "weight_count": availability.get("weight_count", ""),
                    "adapter": result.get("adapter", ""),
                }
            )


def _visual_template(results: Iterable[Mapping[str, Any]]) -> str:
    return _visual_template_with_timestamps(results, (7.0, 22.0, 37.0))


def _visual_template_with_timestamps(
    results: Iterable[Mapping[str, Any]],
    timestamps: tuple[float, ...],
) -> str:
    lines = [
        "# TICKET-078 Visual Review",
        "",
        "Review the same timestamps ("
        + ", ".join(f"{timestamp:g}s" for timestamp in timestamps)
        + ") and record visual",
        "judgment separately from measured metadata.",
        "",
        "| Candidate | Status | Contact sheet | Blocking/ringing | Noise/detail | Faces/text | Flicker/motion | Color/halos | Notes |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for result in results:
        sheet = result.get("visual_review", {}).get("contact_sheet") or "-"
        lines.append(
            f"| {result.get('name', '')} | {result.get('status', '')} | {sheet} | | | | | | |"
        )
    lines.extend(
        [
            "",
            "No clean aligned reference is available for this fixture; do not",
            "turn visual notes into a universal quality claim.",
        ]
    )
    return "\n".join(lines) + "\n"


def _markdown_report(report: Mapping[str, Any]) -> str:
    protocol = report["protocol"]
    summary = report["summary"]
    timestamps = report["subjective_quality"]["timestamps_seconds"]
    lines = [
        "# TICKET-078 Cross-Model Restoration Benchmark",
        "",
        "This is research evidence for one local fixture and workstation. It",
        "does not enable a production restoration route.",
        "",
        "## Protocol",
        "",
        f"- Fixture: `{report['fixture']['path']}`",
        f"- Source frame-rate policy: {protocol['source_frame_rate_policy']}",
        f"- Target: {protocol['target_dimensions']}",
        f"- Video encoder: `{protocol['final_encoder']}`",
        f"- Audio policy: {protocol['audio_policy']}",
        "- Frame interpolation: disabled in the primary restoration comparison",
        "- Objective quality: unavailable without a clean aligned reference",
        "",
        "## Candidate results",
        "",
        "| Candidate | Category | Status | Cold seconds | Warm median | Warm spread | Output | Reason |",
        "|---|---|---|---:|---:|---:|---|---|",
    ]
    for result in report["candidates"]:
        execution = result.get("execution", {})
        cold = execution.get("cold_seconds")
        if cold is None and isinstance(execution.get("cold"), dict):
            cold = execution["cold"].get("wall_seconds")
        warm = execution.get("warm_median_seconds")
        spread = execution.get("warm_spread_seconds")
        output = result.get("output") or {}
        lines.append(
            f"| {result['name']} | {result['category']} | {result['status']} | "
            f"{'-' if cold is None else cold} | "
            f"{'-' if warm is None else warm} | "
            f"{'-' if spread is None else spread} | "
            f"{output.get('path', '-')} | {result.get('reason') or '-'} |"
        )
    lines.extend(
        [
            "",
            "## Measured performance",
            "",
            "Measured timing and resource values are kept in each candidate's",
            "`performance` and `resource_telemetry` objects. FFmpeg controls",
            "measure the combined decode/filter/encode path; reused RVE rows",
            "retain their historical inference and normalization timings.",
            "",
            "## Objective quality",
            "",
            "Objective quality metrics are unavailable because this local",
            "fixture has no clean, aligned reference. No synthetic-reference",
            "score is used for ranking.",
            "",
            "## Subjective quality",
            "",
            "Subjective observations are intentionally blank until the same",
            ", ".join(f"{timestamp:g}s" for timestamp in timestamps)
            + " frames are reviewed with the supplied rubric.",
            "",
            "## Licensing and availability",
            "",
            "License state, runtime discovery, and explicit unavailable or",
            "non-comparable reasons are retained in every candidate row and",
            "the CSV availability table. Unavailable candidates are not ranked.",
            "",
            "",
            "## Summary",
            "",
            f"- Total rows: {summary['total']}",
            f"- Passed: {summary['passed']}",
            f"- Failed: {summary['failed']}",
            f"- Unavailable: {summary['unavailable']}",
            f"- Excluded by license: {summary['excluded_license']}",
            f"- Not comparable: {summary['not_comparable']}",
            "",
            "## Suggestions for review",
            "",
            "1. Start with the FFmpeg Lanczos control and the available RVE",
            "   baseline outputs. The prior TICKET-077 evidence favored RTMoSR",
            "   for quality balance and SuperUltraCompact for conservative speed,",
            "   but those outputs are marked historical when their frame count",
            "   does not satisfy this ticket's native-frame contract.",
            "2. Do not rank an unavailable or license-excluded model. If a model",
            "   is later installed, pin its checkpoint, runtime, backend, and",
            "   license before adding it to the comparable set.",
            "3. Treat Video2X as a wrapper row. Its underlying model and backend",
            "   must be named before comparing it with direct RealESRGAN.",
            "4. Use the visual-review template for blocking, ringing, hallucinated",
            "   detail, faces/text, flicker, motion stability, and color shifts.",
            "",
            "## Artifacts",
            "",
            f"- Machine report: `{report['artifacts']['machine_report']}`",
            f"- Candidate availability: `{report['artifacts']['availability_csv']}`",
            f"- Visual review template: `{report['artifacts']['visual_template']}`",
            f"- Contact sheets: `{report['artifacts']['contact_sheets']}`",
            "",
            "## Gates",
            "",
            f"- Source preservation: `{report['gates']['source_preservation']['status']}`",
            f"- Output integrity: `{report['gates']['output_integrity']['status']}`",
            f"- Contact sheets: `{report['gates']['contact_sheets']['status']}`",
            f"- User validation: `{report['gates']['user_validation']['status']}`",
            "",
        ]
    )
    return "\n".join(lines)


def _environment(
    *,
    ffmpeg: str,
    ffprobe: str,
    nvidia_smi: str | None,
) -> dict[str, Any]:
    def version(executable: str, args: list[str]) -> str | None:
        try:
            result = subprocess.run(
                [executable, *args],
                capture_output=True,
                text=True,
                check=False,
                timeout=30,
            )
        except (OSError, subprocess.TimeoutExpired):
            return None
        line = (result.stdout or result.stderr).splitlines()
        return line[0][:200] if line else None

    gpu = _query_gpu(nvidia_smi)
    return {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "ffmpeg": version(ffmpeg, ["-version"]),
        "ffprobe": version(ffprobe, ["-version"]),
        "nvidia_smi": bool(nvidia_smi),
        "gpu": None if gpu is None else gpu.as_dict(),
        "vapoursynth_module": importlib.util.find_spec("vapoursynth") is not None,
        "vspipe": shutil.which("vspipe") is not None,
    }


def run_benchmark(
    *,
    manifest_path: Path = DEFAULT_MANIFEST,
    source: Path | None = None,
    fixture: Path | None = None,
    output_root: Path | None = None,
    reuse_root: Path = DEFAULT_REUSE_ROOT,
    ffmpeg: str = "ffmpeg",
    ffprobe: str = "ffprobe",
    nvidia_smi: str | None = None,
    warm_runs: int = WARM_RUNS,
    segment_count: int = WINDOW_COUNT,
) -> dict[str, Any]:
    if warm_runs < 1:
        raise ValueError("warm_runs must be at least one")
    if segment_count < 1:
        raise ValueError("segment_count must be at least one")
    manifest = load_manifest(manifest_path)
    output_root = (
        output_root or Path.home() / f"Documents/edit/restoration-cross-model-{date.today():%Y%m%d}"
    )
    output_root = output_root.expanduser().resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    if source is not None and fixture is not None:
        raise ValueError("source and fixture are mutually exclusive")
    if fixture is None and source is None:
        default_fixture = reuse_root / "fixture-45s.mp4"
        fixture = (
            default_fixture
            if default_fixture.is_file()
            else Path.home() / "Videos/editor-test-1m.mp4"
        )
    if fixture is not None:
        fixture_path, fixture_metadata, preservation = reuse_fixture(
            fixture.expanduser().resolve(),
            output_root,
            ffprobe=ffprobe,
        )
    else:
        if source is None:
            raise ValueError("a source or fixture is required")
        fixture_path, fixture_metadata, preservation = build_fixture(
            source.expanduser().resolve(),
            output_root,
            ffmpeg=ffmpeg,
            ffprobe=ffprobe,
            nvidia_smi=nvidia_smi,
            window_count=segment_count,
        )
    review_timestamps = tuple(
        timestamp
        for timestamp in (7.0, 22.0, 37.0, 52.0)
        if timestamp + 0.1 < float(fixture_metadata["duration_seconds"])
    )
    video_encoder = detect_video_encoder(ffmpeg)
    results: list[dict[str, Any]] = []
    for candidate in manifest["candidates"]:
        runner = candidate["runner"]
        if runner == "ffmpeg_filter":
            result = _run_ffmpeg_candidate(
                candidate,
                fixture_path,
                fixture_metadata,
                output_root,
                ffmpeg=ffmpeg,
                ffprobe=ffprobe,
                nvidia_smi=nvidia_smi,
                video_encoder=video_encoder,
                warm_runs=warm_runs,
            )
        elif runner == "reuse_json":
            result = _reused_candidate_result(
                candidate,
                reuse_root,
                fixture_metadata,
                ffmpeg=ffmpeg,
                ffprobe=ffprobe,
            )
        elif runner == "external":
            result = _external_candidate_result(candidate)
        else:
            result = _candidate_base(candidate)
            result["status"] = "not-comparable"
            result["reason"] = f"unknown runner: {runner}"
        if result.get("status") not in TERMINAL_CANDIDATE_STATUSES:
            result["status"] = "failed"
            result["reason"] = "candidate did not produce a terminal status"
        if result.get("output"):
            output_path_text = result["output"].get("path")
            if isinstance(output_path_text, str):
                output_path = Path(output_path_text).expanduser()
                if not output_path.is_absolute():
                    output_path = output_root / output_path
                if output_path.is_file():
                    sheet = _contact_sheet(
                        candidate,
                        output_path,
                        output_root,
                        ffmpeg=ffmpeg,
                        timestamps=review_timestamps,
                    )
                    result["visual_review"] = {
                        "status": sheet["status"],
                        "contact_sheet": sheet.get("path"),
                        "contact_sheet_error": sheet.get("error"),
                    }
        command_record = result.pop("_commands", None)
        command_payload = {
            "candidate": candidate["name"],
            "status": result["status"],
            "reason": result.get("reason"),
            "commands": command_record or [],
            "availability": result.get("availability", {}),
        }
        _write_json(
            output_root / "commands" / f"{candidate['id']}.json",
            command_payload,
        )
        results.append(result)
    protected_path = Path(str(preservation.pop("_protected_path"))).expanduser()
    preservation["source_hash_after_runs"] = file_sha256(protected_path)
    preservation["unchanged"] = (
        preservation["source_hash_before"] == preservation["source_hash_after_runs"]
    )
    _write_json(output_root / "source-preservation.json", preservation)
    contact_sheet_results = [
        result["visual_review"]
        for result in results
        if result.get("visual_review", {}).get("status") == "passed"
    ]
    counts = {
        "total": len(results),
        "passed": sum(result["status"] == "passed" for result in results),
        "failed": sum(result["status"] == "failed" for result in results),
        "unavailable": sum(result["status"] == "unavailable" for result in results),
        "excluded_license": sum(result["status"] == "excluded-license" for result in results),
        "not_comparable": sum(result["status"] == "not-comparable" for result in results),
    }
    benchmark_status = "failed" if counts["failed"] else "passedWithConcerns"
    report = {
        "schema_version": 1,
        "ticket": "TICKET-078",
        "status": benchmark_status,
        "readiness": "pending_user_validation",
        "protocol": {
            **manifest["protocol"],
            "source_frame_rate": fixture_metadata["fps"],
            "source_frame_count": fixture_metadata["frame_count"],
            "final_encoder": video_encoder,
            "interpolation": "disabled",
            "fixture_selection_seed": WINDOW_SEED,
            "fixture_segment_count": segment_count,
            "fixture_window_seconds": WINDOW_SECONDS,
            "visual_review_timestamps_seconds": list(review_timestamps),
        },
        "environment": _environment(
            ffmpeg=ffmpeg,
            ffprobe=ffprobe,
            nvidia_smi=nvidia_smi,
        ),
        "fixture": {
            "path": report_path(fixture_path, output_root),
            "metadata": fixture_metadata,
            "preservation": preservation,
        },
        "candidates": results,
        "summary": counts,
        "measured": {
            "fields": [
                "performance",
                "resource_telemetry",
                "output.metadata",
                "output.playability",
                "output.verification",
            ],
            "timing_note": (
                "FFmpeg controls combine decode, filter, normalization, and "
                "final encode; reused RVE rows preserve historical inference "
                "and normalization timing fields."
            ),
        },
        "objective_quality": {
            "status": "unavailable",
            "reason": "no clean aligned reference is available for the fixture",
        },
        "subjective_quality": {
            "status": "pending_user_validation",
            "rubric": [
                "blocking/ringing",
                "noise/detail",
                "faces/text",
                "flicker/motion",
                "color/halos",
            ],
            "timestamps_seconds": list(review_timestamps),
        },
        "licensing": {
            "source": "candidate manifest and local runtime probes",
            "rows": [
                {
                    "id": result["id"],
                    "status": result["status"],
                    "license": result.get("license", {}),
                }
                for result in results
            ],
        },
        "summary_note": (
            "Unavailable, excluded-license, and not-comparable rows are "
            "retained and are not quality failures."
        ),
        "gates": {
            "source_preservation": {
                "status": "passed" if preservation["unchanged"] else "failed",
                "passed": preservation["unchanged"],
            },
            "output_integrity": {
                "status": (
                    "passed"
                    if not any(result["status"] == "failed" for result in results)
                    and all(
                        result["status"] != "passed"
                        or (
                            result.get("output", {}).get("playability", {}).get("passed", False)
                            and result.get("output", {})
                            .get("verification", {})
                            .get("passed", False)
                        )
                        for result in results
                    )
                    else "failed"
                ),
                "failed_candidates": [
                    result["id"] for result in results if result["status"] == "failed"
                ],
            },
            "contact_sheets": {
                "status": ("passed" if contact_sheet_results else "failed"),
                "count": len(contact_sheet_results),
            },
            "user_validation": {
                "status": "pending",
                "required": True,
            },
        },
        "artifacts": {
            "machine_report": "restoration-cross-model.json",
            "human_report": "restoration-cross-model.md",
            "availability_csv": "candidate-availability.csv",
            "visual_template": "visual-review-template.md",
            "contact_sheets": "contact-sheets/",
            "commands": "commands/",
            "logs": "logs/",
        },
        "recommendation": {
            "status": "bounded_pending_user_review",
            "suggestion": (
                "Review the FFmpeg controls against the reused RVE evidence "
                "first; do not rank unavailable or non-comparable requested "
                "models."
            ),
            "confidence_limits": [
                "one local fixture",
                "one workstation",
                "no clean aligned reference",
                "direct requested model runtimes and weights unavailable",
                "RVE reused outputs may not satisfy native frame-count policy",
            ],
        },
    }
    _availability_csv(results, output_root / "candidate-availability.csv")
    _write_text(
        output_root / "visual-review-template.md",
        _visual_template_with_timestamps(results, review_timestamps),
    )
    _write_json(output_root / "restoration-cross-model.json", report)
    _write_text(
        output_root / "restoration-cross-model.md",
        _markdown_report(report),
    )
    return report


def parse_arguments(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the TICKET-078 cross-model restoration benchmark."
    )
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--fixture", type=Path)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path.home() / f"Documents/edit/restoration-cross-model-{date.today():%Y%m%d}",
    )
    parser.add_argument("--reuse-existing", type=Path, default=DEFAULT_REUSE_ROOT)
    parser.add_argument("--ffmpeg", default="ffmpeg")
    parser.add_argument("--ffprobe", default="ffprobe")
    parser.add_argument("--nvidia-smi", default=None)
    parser.add_argument("--warm-runs", type=int, default=WARM_RUNS)
    parser.add_argument(
        "--segment-count",
        type=int,
        default=WINDOW_COUNT,
        help="number of deterministic random segments to concatenate",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    arguments = parse_arguments(argv)
    nvidia_smi = arguments.nvidia_smi or shutil.which("nvidia-smi")
    try:
        report = run_benchmark(
            manifest_path=arguments.manifest.expanduser().resolve(),
            source=None if arguments.source is None else arguments.source.expanduser().resolve(),
            fixture=None if arguments.fixture is None else arguments.fixture.expanduser().resolve(),
            output_root=arguments.output_dir.expanduser().resolve(),
            reuse_root=arguments.reuse_existing.expanduser().resolve(),
            ffmpeg=arguments.ffmpeg,
            ffprobe=arguments.ffprobe,
            nvidia_smi=nvidia_smi,
            warm_runs=arguments.warm_runs,
            segment_count=arguments.segment_count,
        )
    except (OSError, RuntimeError, ValueError) as error:
        print(f"restoration benchmark failed: {error}", file=sys.stderr)
        return 2
    print(
        json.dumps(
            {
                "report": report["artifacts"]["machine_report"],
                "output_dir": report_path(arguments.output_dir),
                "status": report["status"],
                "candidates": report["summary"],
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
