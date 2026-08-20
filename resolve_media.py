#!/usr/bin/env python3
"""Resolve Media TUI: fast, Resolve-compatible media preparation."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
try:
    import curses
except ImportError:  # pragma: no cover - platform fallback
    curses = None  # type: ignore[assignment]
import json
import os
import queue
import shutil
import subprocess
import sys
import threading
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

VERSION = "1.3.0"
DEFAULT_ROOT = Path.home() / "Documents" / "edit"
DEFAULT_PROFILE = "fast"
DEFAULT_JOBS = 0
DEFAULT_PERFORMANCE_MODE = "auto"
FAST_VIDEO_SUFFIX = ".resolve-ready.mxf"
FAST_AUDIO_SUFFIX = ".resolve-ready.mkv"
LOSSLESS_SUFFIX = ".resolve-lossless.mkv"
GENERATED_SUFFIX = FAST_VIDEO_SUFFIX
GENERATED_SUFFIXES = (FAST_VIDEO_SUFFIX, FAST_AUDIO_SUFFIX, LOSSLESS_SUFFIX)
VIDEO_SAFE = {
    "ffv1",
    "dnxhd",
    "dnxhr",
    "prores",
    "prores_ks",
    "prores_aw",
    "huffyuv",
    "utvideo",
    "v210",
    "v410",
    "rawvideo",
}
AUDIO_SAFE_PREFIXES = ("pcm_",)
AUDIO_SAFE = {"flac"}
GPU_DECODERS = {
    "av1": "av1_cuvid",
    "h264": "h264_cuvid",
    "hevc": "hevc_cuvid",
    "mjpeg": "mjpeg_cuvid",
    "mpeg1video": "mpeg1_cuvid",
    "mpeg2video": "mpeg2_cuvid",
    "mpeg4": "mpeg4_cuvid",
    "vc1": "vc1_cuvid",
    "vp8": "vp8_cuvid",
    "vp9": "vp9_cuvid",
}
_gpu_available: bool | None = None


@dataclass
class MediaInfo:
    path: Path
    streams: list[dict[str, Any]]
    format: dict[str, Any]
    error: str | None = None

    @property
    def video_streams(self) -> list[dict[str, Any]]:
        return [s for s in self.streams if s.get("codec_type") == "video"]

    @property
    def audio_streams(self) -> list[dict[str, Any]]:
        return [s for s in self.streams if s.get("codec_type") == "audio"]

    @property
    def duration(self) -> float:
        value = self.format.get("duration")
        try:
            return max(0.0, float(value))
        except (TypeError, ValueError):
            return 0.0


@dataclass
class Classification:
    ready: bool
    needs_video: bool
    needs_audio: bool
    label: str
    reason: str


def run_probe(path: Path) -> MediaInfo:
    """Probe one file. Errors are represented in MediaInfo, not raised."""
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-print_format",
                "json",
                "-show_streams",
                "-show_format",
                str(path),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        return MediaInfo(path, [], {}, "ffprobe is not installed or not on PATH")
    if result.returncode != 0:
        return MediaInfo(path, [], {}, result.stderr.strip() or "ffprobe could not read the file")
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        return MediaInfo(path, [], {}, f"invalid ffprobe JSON: {exc}")
    return MediaInfo(path, data.get("streams", []), data.get("format", {}))


def classify(info: MediaInfo) -> Classification:
    """Apply the documented conservative Resolve Linux Free policy."""
    if info.error:
        return Classification(False, True, True, "ERROR", info.error)
    videos = info.video_streams
    audios = info.audio_streams
    video_codecs = [str(s.get("codec_name", "")).lower() for s in videos]
    audio_codecs = [str(s.get("codec_name", "")).lower() for s in audios]
    video_ok = not videos or video_codecs[0] in VIDEO_SAFE
    audio_ok = all(c in AUDIO_SAFE or c.startswith(AUDIO_SAFE_PREFIXES) for c in audio_codecs)
    needs_video = bool(videos) and not video_ok
    needs_audio = bool(audios) and not audio_ok
    if not videos and not audios:
        return Classification(False, True, True, "NOT MEDIA", "No video or audio streams")
    if not needs_video and not needs_audio:
        return Classification(True, False, False, "READY", "Resolve-readable video/audio codecs")
    reasons = []
    if needs_video:
        reasons.append("video codec " + (video_codecs[0] if video_codecs else "missing"))
    if needs_audio:
        reasons.append("unsupported audio: " + ", ".join(audio_codecs))
    return Classification(False, needs_video, needs_audio, "PREPARE", "; ".join(reasons))


def gpu_available() -> bool:
    global _gpu_available
    if _gpu_available is None:
        if shutil.which("nvidia-smi") is None:
            _gpu_available = False
        else:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
                capture_output=True,
                text=True,
                check=False,
            )
            _gpu_available = result.returncode == 0 and bool(result.stdout.strip())
    return _gpu_available


def gpu_decoder(info: MediaInfo) -> str | None:
    if not info.video_streams:
        return None
    codec = str(info.video_streams[0].get("codec_name", "")).lower()
    return GPU_DECODERS.get(codec)


def normalize_profile(profile: str) -> str:
    """Map the legacy DNxHR name to the current fast profile."""
    normalized = profile.lower()
    if normalized == "dnxhr":
        return DEFAULT_PROFILE
    if normalized in {"fast", "lossless"}:
        return normalized
    raise ValueError(f"unsupported profile: {profile}")


def effective_jobs(profile: str, requested: int, cpu_count: int | None = None) -> int:
    """Choose bounded concurrency; lossless GPU work remains single-file."""
    if normalize_profile(profile) == "lossless":
        return 1
    if requested > 0:
        return requested
    available = cpu_count if cpu_count is not None else (os.cpu_count() or 1)
    return min(3, max(1, available // 4))


def output_format(info: MediaInfo | None, profile: str) -> str:
    normalized = normalize_profile(profile)
    if normalized == "lossless":
        return "matroska"
    if info is not None and info.video_streams and classify(info).needs_video:
        return "mxf"
    return "matroska"


def output_suffix(info: MediaInfo | None, profile: str) -> str:
    normalized = normalize_profile(profile)
    if normalized == "lossless":
        return LOSSLESS_SUFFIX
    return FAST_VIDEO_SUFFIX if output_format(info, normalized) == "mxf" else FAST_AUDIO_SUFFIX


def output_path(source: Path, profile: str = DEFAULT_PROFILE, info: MediaInfo | None = None) -> Path:
    return source.with_name(source.stem + output_suffix(info, profile))


def generated_candidates(source: Path, info: MediaInfo, profile: str) -> list[Path]:
    """Return current and compatible generated names for the requested profile."""
    candidates = [output_path(source, profile, info)]
    if normalize_profile(profile) == DEFAULT_PROFILE:
        candidates.extend(
            source.with_name(source.stem + suffix)
            for suffix in (FAST_VIDEO_SUFFIX, FAST_AUDIO_SUFFIX, LOSSLESS_SUFFIX)
        )
    unique: list[Path] = []
    for candidate in candidates:
        if candidate not in unique:
            unique.append(candidate)
    return unique


def existing_generated_output(source: MediaInfo, profile: str) -> Path | None:
    for candidate in generated_candidates(source.path, source, profile):
        if valid_generated_output(source, candidate):
            return candidate
    return None


def valid_generated_output(source: MediaInfo, generated: Path) -> bool:
    if not generated.is_file():
        return False
    out = run_probe(generated)
    if out.error:
        return False
    if bool(source.video_streams) != bool(out.video_streams):
        return False
    if len(out.audio_streams) < len(source.audio_streams):
        return False
    if source.duration and out.duration and abs(source.duration - out.duration) > max(1.0, source.duration * 0.01):
        return False
    result = classify(out)
    return result.ready


def media_files(root: Path) -> Iterable[Path]:
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.name.startswith("."):
            continue
        if any(path.name.endswith(suffix) for suffix in GENERATED_SUFFIXES) or ".partial-" in path.name:
            continue
        yield path


def format_seconds(seconds: float) -> str:
    if seconds <= 0:
        return "--:--"
    total = int(seconds)
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours}h {minutes:02d}m"
    return f"{minutes:02d}:{secs:02d}"


def progress_bar(percent: int, width: int = 24) -> str:
    percent = max(0, min(100, percent))
    filled = int(width * percent / 100)
    return "[" + "#" * filled + "." * (width - filled) + "]"


def scan(root: Path, profile: str = DEFAULT_PROFILE) -> list[tuple[Path, MediaInfo, Classification, str]]:
    records = []
    for path in media_files(root):
        info = run_probe(path)
        if existing_generated_output(info, profile):
            records.append((path, info, Classification(True, False, False, "PREPARED", "Valid generated output exists"), "prepared"))
        else:
            records.append((path, info, classify(info), ""))
    return records


def _codec_for_audio(stream: dict[str, Any]) -> str:
    # 32-bit PCM avoids adding quantization loss for common source formats.
    sample_fmt = str(stream.get("sample_fmt", ""))
    return "pcm_f32le" if "flt" in sample_fmt else "pcm_s32le"


def _mxf_audio_codec(stream: dict[str, Any]) -> str:
    """Select PCM supported by MXF without needlessly reducing 24-bit audio."""
    try:
        bits = int(stream.get("bits_per_sample", 0) or 0)
    except (TypeError, ValueError):
        bits = 0
    return "pcm_s24le" if bits >= 24 else "pcm_s16le"


def _fast_video_codec(info: MediaInfo) -> tuple[list[str], str]:
    pixel_format = str(info.video_streams[0].get("pix_fmt", "")).lower() if info.video_streams else ""
    high_bit_depth = any(depth in pixel_format for depth in ("10", "12", "14", "16"))
    if high_bit_depth:
        return ["-c:v", "dnxhd", "-profile:v", "dnxhr_hqx", "-pix_fmt", "yuv422p10le"], "DNxHR HQX"
    return ["-c:v", "dnxhd", "-profile:v", "dnxhr_sq", "-pix_fmt", "yuv422p"], "DNxHR SQ"


def ffmpeg_command(
    info: MediaInfo,
    source: Path,
    partial: Path,
    profile: str,
    use_gpu: bool = False,
) -> list[str]:
    profile = normalize_profile(profile)
    classification = classify(info)
    decoder = gpu_decoder(info) if profile == "lossless" and use_gpu and classification.needs_video else None
    input_options: list[str] = []
    if decoder:
        input_options = [
            "-init_hw_device",
            "vulkan=gpu:0",
            "-filter_hw_device",
            "gpu",
            "-hwaccel",
            "cuda",
            "-hwaccel_device",
            "0",
            "-c:v",
            decoder,
        ]
    if profile == "fast":
        video_codec, _ = _fast_video_codec(info)
    else:
        video_codec = ["-c:v", "ffv1", "-level", "3", "-coder", "1", "-context", "1", "-g", "1", "-pix_fmt", "+"]
    args = [
        "ffmpeg",
        "-hide_banner",
        "-nostdin",
        "-y",
        *input_options,
        "-i",
        str(source),
        "-map",
        "0:v:0?",
        "-map",
        "0:a?",
        "-map_metadata",
        "0",
        "-map_chapters",
        "0",
    ]
    if info.video_streams:
        if classification.needs_video:
            if decoder and profile == "lossless":
                pixel_format = str(info.video_streams[0].get("pix_fmt", "")).lower()
                if not pixel_format:
                    raise ValueError("GPU lossless mode needs a known source pixel format")
                args += [
                    "-vf",
                    f"format={pixel_format},hwupload",
                    "-c:v",
                    "ffv1_vulkan",
                    "-strict",
                    "experimental",
                    "-level",
                    "4",
                    "-coder",
                    "1",
                    "-context",
                    "1",
                    "-g",
                    "1",
                ]
            else:
                args += video_codec
        else:
            args += ["-c:v", "copy"]
    if info.audio_streams:
        if classification.needs_audio:
            audio_codec = _codec_for_audio(info.audio_streams[0])
            if profile == "fast" and output_format(info, profile) == "mxf":
                audio_codec = _mxf_audio_codec(info.audio_streams[0])
            args += ["-c:a", audio_codec]
        else:
            args += ["-c:a", "copy"]
    args += ["-f", output_format(info, profile), "-progress", "pipe:1", "-nostats", str(partial)]
    return args


def verify_output(source: MediaInfo, generated: Path) -> tuple[bool, str]:
    out = run_probe(generated)
    if out.error:
        return False, out.error
    if bool(source.video_streams) != bool(out.video_streams):
        return False, "video stream presence does not match source"
    if len(out.audio_streams) < len(source.audio_streams):
        return False, "not all source audio streams are present"
    if source.duration and out.duration and abs(source.duration - out.duration) > max(1.0, source.duration * 0.01):
        return False, f"duration differs ({source.duration:.2f}s vs {out.duration:.2f}s)"
    if classify(out).needs_video or classify(out).needs_audio:
        return False, "output is not Resolve-readable under the conservative policy"
    return True, "verified"


def trash_original(source: Path, emit) -> None:
    gio = shutil.which("gio")
    if not gio:
        emit("warning", source, 100, 0, "gio not available; original was retained")
        return
    trash = subprocess.run([gio, "trash", str(source)], capture_output=True, text=True, check=False)
    if trash.returncode:
        emit("warning", source, 100, 0, "gio trash failed; original was retained")
    else:
        emit("deleted", source, 100, 0, "original moved to Trash after verification")


def begin_performance_mode(mode: str, notify) -> tuple[str, str] | None:
    """Temporarily select the performance profile and return its restore state."""
    if mode == "off":
        return None
    tool = shutil.which("powerprofilesctl")
    if not tool:
        notify("Performance mode unavailable: powerprofilesctl is not installed.")
        return None
    try:
        current = subprocess.run([tool, "get"], capture_output=True, text=True, check=False)
        available = subprocess.run([tool, "list"], capture_output=True, text=True, check=False)
    except OSError as exc:
        notify(f"Performance mode unavailable: {exc}")
        return None
    previous = current.stdout.strip()
    if current.returncode or not previous:
        notify("Performance mode unavailable: could not read the current profile.")
        return None
    if available.returncode or "performance" not in available.stdout:
        notify("Performance mode unavailable: the performance profile is not exposed.")
        return None
    if previous == "performance":
        notify("Performance mode already active; it will be left unchanged.")
        return None
    try:
        changed = subprocess.run([tool, "set", "performance"], capture_output=True, text=True, check=False)
    except OSError as exc:
        notify(f"Performance mode unavailable: {exc}")
        return None
    if changed.returncode:
        detail = changed.stderr.strip() or "powerprofilesctl rejected the change"
        notify(f"Performance mode could not be enabled: {detail}")
        return None
    notify(f"Performance mode enabled temporarily (was {previous}).")
    return tool, previous


def restore_performance_mode(state: tuple[str, str] | None, notify) -> None:
    if state is None:
        return
    tool, previous = state
    try:
        current = subprocess.run([tool, "get"], capture_output=True, text=True, check=False)
    except OSError as exc:
        notify(f"Warning: could not restore performance mode ({exc}).")
        return
    if current.returncode == 0 and current.stdout.strip() != "performance":
        notify("Performance profile changed externally; leaving it unchanged.")
        return
    try:
        restored = subprocess.run([tool, "set", previous], capture_output=True, text=True, check=False)
    except OSError as exc:
        notify(f"Warning: could not restore performance mode ({exc}).")
        return
    if restored.returncode:
        detail = restored.stderr.strip() or "powerprofilesctl rejected the restore"
        notify(f"Warning: could not restore performance mode: {detail}")
    else:
        notify(f"Performance mode restored to {previous}.")


def convert_one(source: Path, profile: str, delete_original: bool, gpu_mode: str, emit) -> str:
    profile = normalize_profile(profile)
    info = run_probe(source)
    classification = classify(info)
    if info.error:
        emit("failed", source, 0, 0, info.error)
        return "failed"
    if classification.ready:
        emit("skipped", source, 100, info.duration, "already Resolve-readable")
        return "skipped"
    destination = output_path(source, profile, info)
    generated = existing_generated_output(info, profile)
    if generated is not None:
        if delete_original:
            trash_original(source, emit)
        emit("skipped", source, 100, info.duration, f"valid generated output already exists: {generated.name}")
        return "skipped"
    started = time.monotonic()
    can_use_gpu = (
        profile == "lossless"
        and gpu_mode != "off"
        and gpu_available()
        and bool(gpu_decoder(info))
        and classification.needs_video
    )
    attempts = [True, False] if can_use_gpu else [False]
    if profile == "lossless" and gpu_mode == "on" and not can_use_gpu:
        emit("warning", source, 0, 0, "GPU path unavailable; using CPU")

    for attempt, use_gpu in enumerate(attempts):
        partial = destination.with_name(destination.name + f".partial-{os.getpid()}-{uuid.uuid4().hex[:8]}")
        last = 0
        try:
            command = ffmpeg_command(info, source, partial, profile, use_gpu=use_gpu)
            proc = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
        except (FileNotFoundError, ValueError) as exc:
            if use_gpu:
                emit("warning", source, 0, 0, f"GPU path unavailable ({exc}); retrying on CPU")
                partial.unlink(missing_ok=True)
                continue
            emit("failed", source, 0, 0, str(exc) or "ffmpeg is not installed or not on PATH")
            return "failed"

        assert proc.stdout is not None
        for line in proc.stdout:
            line = line.strip()
            if line.startswith("out_time_ms="):
                try:
                    elapsed_media = int(line.split("=", 1)[1]) / 1_000_000
                    last = int(min(99, (elapsed_media / info.duration * 100) if info.duration else 0))
                    label = "GPU encode" if use_gpu else ("CPU DNxHR" if profile == "fast" else "CPU encode")
                    emit("progress", source, last, elapsed_media, label)
                except ValueError:
                    pass
            elif line == "progress=end":
                emit("progress", source, 99, info.duration, "verifying")
        return_code = proc.wait()
        if return_code == 0 and partial.exists():
            ok, message = verify_output(info, partial)
            if ok:
                os.replace(partial, destination)
                if profile == "fast":
                    mode_label = _fast_video_codec(info)[1] if info.video_streams and classification.needs_video else "CPU PCM"
                else:
                    mode_label = "GPU" if use_gpu else ("CPU fallback" if attempt else "CPU")
                if delete_original:
                    trash_original(source, emit)
                emit("completed", source, 100, time.monotonic() - started, f"created {destination.name} ({mode_label})")
                return "completed"
            failure = "verification failed: " + message
        else:
            failure = "ffmpeg failed; source was left untouched"
        partial.unlink(missing_ok=True)
        if use_gpu:
            emit("warning", source, last, 0, f"GPU path failed ({failure}); retrying on CPU")
            continue
        emit("failed", source, last, time.monotonic() - started, failure)
        return "failed"
    emit("failed", source, 0, time.monotonic() - started, "GPU and CPU conversion paths failed")
    return "failed"


@dataclass
class Entry:
    path: Path
    is_dir: bool
    selected: bool = False
    status: str = ""
    classification: str = ""
    detail: str = ""
    duration: float = 0.0


class Processor(threading.Thread):
    def __init__(
        self,
        paths: list[Path],
        profile: str,
        delete_original: bool,
        gpu_mode: str,
        jobs: int,
        performance_mode: str,
        events: queue.Queue,
    ):
        super().__init__(daemon=True)
        self.paths = paths
        self.profile = profile
        self.delete_original = delete_original
        self.gpu_mode = gpu_mode
        self.jobs = jobs
        self.performance_mode = performance_mode
        self.events = events

    def run(self) -> None:
        files: list[Path] = []
        for path in self.paths:
            if path.is_dir():
                files.extend(media_files(path))
            elif path.is_file():
                files.append(path)
        files = list(dict.fromkeys(files))
        durations = {path: run_probe(path).duration for path in files}
        total_duration = sum(durations.values())
        performance_state = None

        def notify(message: str) -> None:
            self.events.put(("notice", message))

        try:
            if files:
                performance_state = begin_performance_mode(self.performance_mode, notify)
            self.events.put(("batch", len(files), total_duration, durations))
            worker_count = min(effective_jobs(self.profile, self.jobs), len(files)) if files else 1
            if len(files) > 1 and worker_count > 1:
                notify(f"Running {worker_count} conversions in parallel.")

            def process(item: tuple[int, Path]) -> str:
                index, path = item

                def emit(kind, source, percent, value, message):
                    self.events.put(
                        (
                            "event",
                            kind,
                            source,
                            percent,
                            value,
                            message,
                            index,
                            len(files),
                            total_duration,
                            durations[path],
                        )
                    )

                try:
                    return convert_one(path, self.profile, self.delete_original, self.gpu_mode, emit)
                except (OSError, ValueError, subprocess.SubprocessError) as exc:
                    emit("failed", path, 0, 0, f"worker error: {exc}")
                    return "failed"

            with ThreadPoolExecutor(max_workers=worker_count) as executor:
                list(executor.map(process, enumerate(files, 1)))
        finally:
            restore_performance_mode(performance_state, notify)
            self.events.put(("done",))


class ResolveTUI:
    def __init__(
        self,
        stdscr,
        root: Path,
        profile: str,
        delete_requested: bool,
        gpu_mode: str,
        jobs: int,
        performance_mode: str,
    ):
        self.stdscr = stdscr
        self.root = root.expanduser().resolve()
        self.profile = profile
        self.delete_original = delete_requested
        self.gpu_mode = gpu_mode
        self.jobs = jobs
        self.performance_mode = performance_mode
        self.events: queue.Queue = queue.Queue()
        self.entries: list[Entry] = []
        self.cursor = 0
        self.offset = 0
        self.message = "Space selects; ? shows help."
        self.running = True
        self.processing = False
        self.processor: Processor | None = None
        self.completed = self.skipped = self.failed = 0
        self.current_percent = 0
        self.global_percent = 0
        self.current_name = ""
        self.current_action = "idle"
        self.batch_total = self.batch_done = 0
        self.batch_duration = 0.0
        self.batch_started = 0.0
        self.batch_durations: dict[Path, float] = {}
        self.file_progress: dict[Path, int] = {}
        self.finished_paths: set[Path] = set()
        self.selection: set[Path] = set()

    def load(self) -> None:
        self.entries = []
        try:
            children = sorted(self.root.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        except OSError as exc:
            self.message = f"Cannot read {self.root}: {exc}"
            return
        for path in children:
            if path.name.startswith("."):
                continue
            if path.is_dir():
                self.entries.append(Entry(path, True, path in self.selection))
                continue
            if any(path.name.endswith(suffix) for suffix in GENERATED_SUFFIXES) or ".partial-" in path.name:
                continue
            info = run_probe(path)
            classification = classify(info)
            if existing_generated_output(info, self.profile):
                classification = Classification(True, False, False, "PREPARED", "valid generated output exists")
            self.entries.append(Entry(path, False, path in self.selection, classification.label, classification.reason, info.duration))
        self.cursor = min(self.cursor, max(0, len(self.entries) - 1))

    def selected_paths(self) -> list[Path]:
        return [p for p in self.selection if p.exists()]

    def draw(self) -> None:
        self.stdscr.erase()
        height, width = self.stdscr.getmaxyx()
        if height < 16 or width < 70:
            self.stdscr.addnstr(0, 0, "Terminal too small. Resize to at least 70x16.", width - 1, curses.color_pair(2))
            self.stdscr.addnstr(2, 0, "q quit", width - 1)
            self.stdscr.refresh()
            return
        self.stdscr.attron(curses.color_pair(1) | curses.A_BOLD)
        self.stdscr.addnstr(0, 0, "+-" + "-" * max(0, width - 4) + "-+", width - 1)
        self.stdscr.attroff(curses.color_pair(1) | curses.A_BOLD)
        self.stdscr.addnstr(
            1,
            0,
            f"| RESOLVE MEDIA // EVA-01 INGEST // {self.profile.upper()}",
            width - 1,
            curses.color_pair(1) | curses.A_BOLD,
        )
        self.stdscr.addnstr(
            2,
            0,
            f"| ROOT {self.root} | PATH {self.path_label()} | JOBS {self.jobs_label()} | PERF {self.performance_mode.upper()} | DELETE {'ON' if self.delete_original else 'OFF'}",
            width - 1,
            curses.color_pair(3),
        )
        self.stdscr.addnstr(
            3,
            0,
            "| Right/l enter folder  Left/h/backspace up  Enter convert  Space select  a all  n clear  g GPU  p PERF  D delete  r rescan  ? help  q quit",
            width - 1,
            curses.color_pair(2),
        )
        list_top = 5
        list_bottom = max(list_top + 1, height - 10)
        visible = list_bottom - list_top
        if self.cursor < self.offset:
            self.offset = self.cursor
        if self.cursor >= self.offset + visible:
            self.offset = self.cursor - visible + 1
        for row, entry in enumerate(self.entries[self.offset:self.offset + visible], list_top):
            idx = row - list_top + self.offset
            marker = "[x]" if entry.path in self.selection else "[ ]"
            icon = "[DIR]" if entry.is_dir else "[MED]"
            label = entry.path.name + ("/" if entry.is_dir else "")
            if not entry.is_dir:
                label += f" [{entry.classification}]"
            text = f"{marker} {icon:5} {label}"
            attr = curses.A_REVERSE if idx == self.cursor else curses.color_pair(2)
            self.stdscr.addnstr(row, 0, text, width - 1, attr)
            if entry.status:
                self.stdscr.addnstr(row, max(0, width - 26), entry.status[:25], 25, curses.color_pair(4) | curses.A_BOLD)
        elapsed = time.monotonic() - self.batch_started if self.batch_started else 0
        eta = self._eta(elapsed, self.global_percent)
        current = f"FILE  {progress_bar(self.current_percent)} {self.current_percent:3d}%  {self.current_name or 'idle'}"
        total = f"TOTAL {progress_bar(self.global_percent)} {self.global_percent:3d}%  ETA {eta}"
        self.stdscr.addnstr(height - 7, 0, current, width - 1, curses.color_pair(3))
        self.stdscr.addnstr(height - 6, 0, total, width - 1, curses.color_pair(1))
        footer = (
            f"Selected {len(self.selection)} | {self.current_action} | "
            f"Elapsed {format_seconds(elapsed)} | Media {format_seconds(self.batch_duration)}"
        )
        self.stdscr.addnstr(height - 5, 0, footer, width - 1, curses.color_pair(3))
        counts = f"Completed {self.completed}  Skipped {self.skipped}  Failed {self.failed}"
        self.stdscr.addnstr(height - 4, 0, counts, width - 1)
        self.stdscr.addnstr(height - 3, 0, self.message, width - 1, curses.color_pair(4) | curses.A_BOLD)
        self.stdscr.addnstr(height - 2, 0, "+" + "-" * max(0, width - 2) + "+", width - 1, curses.color_pair(1))
        self.stdscr.refresh()

    def path_label(self) -> str:
        if normalize_profile(self.profile) == DEFAULT_PROFILE:
            return "CPU DNxHR"
        return f"GPU {self.gpu_mode.upper()}"

    def jobs_label(self) -> str:
        return "AUTO" if self.jobs == DEFAULT_JOBS else str(self.jobs)

    def _eta(self, elapsed: float, percent: int) -> str:
        if percent <= 0 or elapsed <= 0:
            return "--:--"
        return format_seconds(elapsed * (100 - percent) / percent)

    def help(self) -> None:
        self.stdscr.erase()
        height, width = self.stdscr.getmaxyx()
        lines = [
            "Resolve Media help",
            "",
            "Select files or folders; folders are processed recursively.",
            "Only files needing preparation are converted.",
            "Fast profile (default): DNxHR SQ + PCM audio in MXF (.mxf).",
            "10-bit sources use DNxHR HQX to avoid an unnecessary bit-depth drop.",
            "The CPU DNxHR path is faster than GPU ProRes on this machine.",
            "Lossless profile: FFV1 video + PCM audio in Matroska (.mkv).",
            "GPU mode applies to the lossless profile: NVIDIA decode and Vulkan FFV1 are attempted.",
            "If the lossless GPU path fails, conversion retries safely on the CPU.",
            "Performance mode defaults to AUTO: it switches to performance for the batch and restores the prior profile.",
            "Fast mode uses bounded parallel conversion; lossless GPU mode stays single-file.",
            "Safe codecs: FFV1, DNxHD/DNxHR, ProRes and documented intra codecs;",
            "audio: PCM or FLAC. AAC is already lossy; PCM adds no further loss.",
            "Generated files are verified before the original is moved to Trash.",
            "",
            "Keys: arrows/j/k move | Right/l enter | Left/h/backspace up | Enter convert",
            "Space select | a all | n clear | g GPU | p performance | D delete | r rescan | q quit",
            "",
            "Press any key to return.",
        ]
        for i, line in enumerate(lines[:height - 1]):
            self.stdscr.addnstr(i, 0, line, width - 1)
        self.stdscr.refresh()
        self.stdscr.timeout(-1)
        try:
            self.stdscr.getch()
        finally:
            self.stdscr.timeout(100)

    def confirm_delete(self) -> bool:
        height, width = self.stdscr.getmaxyx()
        self.stdscr.addnstr(height - 2, 0, "DELETE ORIGINALS after verification? Press y to confirm, any other key cancels.", width - 1, curses.color_pair(4) | curses.A_BOLD)
        self.stdscr.refresh()
        self.stdscr.timeout(-1)
        try:
            key = self.stdscr.getch()
        finally:
            self.stdscr.timeout(100)
        return key in (ord("y"), ord("Y"))

    def start(self) -> None:
        paths = self.selected_paths()
        if not paths:
            paths = [self.root]
            self.message = f"No explicit selection; processing {self.root.name}/ recursively."
        if self.delete_original and not self.confirm_delete():
            self.message = "Conversion cancelled: deletion confirmation was not given."
            return
        self.completed = self.skipped = self.failed = 0
        self.current_percent = self.global_percent = 0
        self.current_name = ""
        self.batch_durations = {}
        self.file_progress = {}
        self.finished_paths = set()
        self.processing = True
        self.batch_started = time.monotonic()
        self.current_action = "starting"
        self.message = "Preparing worker..."
        self.processor = Processor(
            paths,
            self.profile,
            self.delete_original,
            self.gpu_mode,
            self.jobs,
            self.performance_mode,
            self.events,
        )
        self.processor.start()

    def handle_event(self, event) -> None:
        kind = event[0]
        if kind == "notice":
            self.message = event[1]
            return
        if kind == "batch":
            _, self.batch_total, self.batch_duration, self.batch_durations = event
            return
        if kind == "done":
            self.processing = False
            self.current_action = "finished"
            self.message = "Processing complete. Press r to rescan."
            return
        _, action, source, percent, value, message, index, total, total_duration, file_duration = event
        self.current_name = source.name
        self.current_percent = percent
        self.file_progress[source] = percent
        if action in {"completed", "skipped", "failed"}:
            self.finished_paths.add(source)
        if total_duration:
            weighted_done = sum(
                self.batch_durations.get(path, 0.0) * progress / 100
                for path, progress in self.file_progress.items()
            )
            self.global_percent = int(min(100, weighted_done / total_duration * 100))
        else:
            self.global_percent = int(len(self.finished_paths) / total * 100) if total else 0
        self.current_action = message
        for entry in self.entries:
            if entry.path == source:
                entry.status = f"{percent:3d}% {action}"
                if action == "completed":
                    entry.classification = "PREPARED"
                break
        if action in {"completed", "skipped", "failed"}:
            self.batch_done = len(self.finished_paths)
            if action == "completed":
                self.completed += 1
            elif action == "skipped":
                self.skipped += 1
            else:
                self.failed += 1
        self.message = f"{source.name}: {message}"

    def run(self) -> None:
        if curses is None:
            self.message = "Python curses is unavailable."
            return
        try:
            curses.curs_set(0)
        except curses.error:
            pass
        self.stdscr.nodelay(True)
        self.stdscr.timeout(100)
        try:
            curses.start_color()
            curses.use_default_colors()
            curses.init_pair(1, -1, -1)
            curses.init_pair(2, curses.COLOR_CYAN, -1)
            curses.init_pair(3, curses.COLOR_YELLOW, -1)
            curses.init_pair(4, curses.COLOR_MAGENTA, -1)
            curses.init_pair(5, curses.COLOR_RED, -1)
        except curses.error:
            pass
        self.load()
        while self.running:
            while True:
                try:
                    self.handle_event(self.events.get_nowait())
                except queue.Empty:
                    break
            self.draw()
            key = self.stdscr.getch()
            if key == -1:
                continue
            if key in (ord("q"), ord("Q")):
                if self.processing:
                    self.message = "Worker is active; quit will leave source files untouched."
                else:
                    self.running = False
            elif key in (curses.KEY_DOWN, ord("j")) and self.entries:
                self.cursor = min(len(self.entries) - 1, self.cursor + 1)
            elif key in (curses.KEY_UP, ord("k")) and self.entries:
                self.cursor = max(0, self.cursor - 1)
            elif key in (curses.KEY_RIGHT, ord("l")) and self.entries and not self.processing:
                entry = self.entries[self.cursor]
                if entry.is_dir:
                    self.root = entry.path
                    self.cursor = self.offset = 0
                    self.load()
                else:
                    self.message = "Right/l enters folders. Press Space to select this file."
            elif key in (curses.KEY_LEFT, ord("h"), curses.KEY_BACKSPACE, 127, 8) and not self.processing:
                if self.root.parent != self.root:
                    self.root = self.root.parent
                    self.cursor = self.offset = 0
                    self.load()
            elif key in (curses.KEY_ENTER, 10, 13) and not self.processing:
                self.start()
            elif key == ord(" ") and self.entries and not self.processing:
                path = self.entries[self.cursor].path
                if path in self.selection:
                    self.selection.remove(path)
                else:
                    self.selection.add(path)
                self.entries[self.cursor].selected = path in self.selection
            elif key in (ord("a"), ord("A")) and not self.processing:
                self.selection.update(e.path for e in self.entries)
                for e in self.entries:
                    e.selected = True
            elif key in (ord("n"), ord("N")) and not self.processing:
                self.selection.clear()
                for e in self.entries:
                    e.selected = False
            elif key in (ord("d"), ord("D")) and not self.processing:
                self.delete_original = not self.delete_original
                self.message = "Original deletion toggled; Enter/c will require confirmation when ON."
            elif key in (ord("g"), ord("G")) and not self.processing:
                self.gpu_mode = {"auto": "off", "off": "on", "on": "auto"}[self.gpu_mode]
                if normalize_profile(self.profile) == DEFAULT_PROFILE:
                    self.message = f"GPU mode: {self.gpu_mode.upper()} (fast DNxHR remains CPU-encoded)."
                else:
                    self.message = f"GPU mode: {self.gpu_mode.upper()}."
            elif key in (ord("p"), ord("P")) and not self.processing:
                self.performance_mode = {"auto": "off", "off": "on", "on": "auto"}[self.performance_mode]
                self.message = f"Performance mode: {self.performance_mode.upper()}."
            elif key in (ord("r"), ord("R")) and not self.processing:
                self.load()
                self.message = "Rescanned current folder."
            elif key in (ord("c"), ord("C")) and not self.processing:
                self.start()
            elif key == ord("?"):
                self.help()


def dry_run(root: Path, profile: str = DEFAULT_PROFILE) -> int:
    if not root.exists():
        print(f"error: root does not exist: {root}", file=sys.stderr)
        return 2
    if not root.is_dir():
        print(f"error: root is not a directory: {root}", file=sys.stderr)
        return 2
    profile = normalize_profile(profile)
    records = scan(root, profile)
    print(f"Root: {root}")
    print(f"Profile: {profile}")
    print(f"Policy: video {', '.join(sorted(VIDEO_SAFE))}; audio PCM*/FLAC")
    print(f"Files inspected: {len(records)}")
    for path, info, classification, _ in records:
        duration = f"{info.duration:.1f}s" if info.duration else "?"
        print(f"{classification.label:8} {duration:>9}  {path}")
        if classification.reason:
            print(f"         {classification.reason}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Prepare media for DaVinci Resolve Linux Free (fast DNxHR/PCM by default).")
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT, help=f"root folder (default: {DEFAULT_ROOT})")
    parser.add_argument("--dry-run", action="store_true", help="scan and report; never convert or delete")
    deletion = parser.add_mutually_exclusive_group()
    deletion.add_argument("--delete-originals", dest="delete_originals", action="store_true", help="delete originals after verification (default)")
    deletion.add_argument("--keep-originals", dest="delete_originals", action="store_false", help="keep originals after conversion")
    parser.add_argument(
        "--profile",
        choices=("fast", "lossless", "dnxhr"),
        default=DEFAULT_PROFILE,
        help="conversion profile: fast DNxHR SQ/PCM, lossless FFV1/PCM, or legacy dnxhr alias (default: fast)",
    )
    parser.add_argument("--gpu", choices=("auto", "on", "off"), default="on", help="GPU mode for lossless encoding: on, auto, or off (default: on)")
    parser.add_argument(
        "--jobs",
        type=int,
        default=DEFAULT_JOBS,
        help="parallel conversions; 0 selects a bounded automatic value (default: auto)",
    )
    parser.add_argument(
        "--performance-mode",
        choices=("auto", "on", "off"),
        default=DEFAULT_PERFORMANCE_MODE,
        help="temporarily use the system performance profile and restore it afterward (default: auto)",
    )
    parser.set_defaults(delete_originals=True)
    parser.add_argument("--version", action="version", version=f"resolve-media {VERSION}")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.jobs < 0:
        build_parser().error("--jobs must be zero or greater")
    root = args.root.expanduser()
    profile = normalize_profile(args.profile)
    if args.dry_run:
        if shutil.which("ffprobe") is None:
            print("error: ffprobe is required for --dry-run; install FFmpeg.", file=sys.stderr)
            return 2
        return dry_run(root, profile)
    if curses is None:
        print("error: Python curses is unavailable; use --dry-run or install a curses-enabled Python.", file=sys.stderr)
        return 2
    if shutil.which("ffprobe") is None or shutil.which("ffmpeg") is None:
        print("error: ffprobe and ffmpeg are required. Install FFmpeg and retry.", file=sys.stderr)
        return 2
    if not root.exists() or not root.is_dir():
        print(f"error: root directory does not exist: {root}", file=sys.stderr)
        return 2
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        print("error: interactive TUI needs a terminal; use --dry-run for a non-interactive scan.", file=sys.stderr)
        return 2
    try:
        curses.wrapper(
            lambda stdscr: ResolveTUI(
                stdscr,
                root,
                profile,
                args.delete_originals,
                args.gpu,
                args.jobs,
                args.performance_mode,
            ).run()
        )
    except (curses.error, KeyboardInterrupt) as exc:
        print(f"\nTUI ended: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
