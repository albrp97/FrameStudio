#!/usr/bin/env python3
"""Select videos and run the concat-first FPS workflow."""

from __future__ import annotations

import argparse
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import time
from array import array
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import nullcontext
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any, Iterable

try:
    import curses
except ImportError:  # pragma: no cover - platform fallback
    curses = None


VIDEO_EXTENSIONS = {".avi", ".m4v", ".mkv", ".mov", ".mp4", ".mxf", ".webm"}
DEFAULT_TUI_ROOT = Path.home() / "Documents" / "edit"
DEFAULT_FPS_MODEL = "4.26"
DEFAULT_FPS_ENGINE = "rve"
DEFAULT_RVE_ROOT = Path(
    os.environ.get("RESOLVE_RVE_ROOT", "/tmp/REAL-Video-Enhancer")
)
DEFAULT_RVE_MODEL = Path(
    os.environ.get(
        "RESOLVE_RVE_MODEL",
        "/tmp/rve-models-pixel-fallback/rife4.26.pkl",
    )
)
DEFAULT_RVE_SHIMS = Path(
    os.environ.get("RESOLVE_RVE_SHIMS", "/tmp/rve-shims")
)
TARGET_MEAN_RMS_DB = -35.0
TARGET_MEDIAN_DB = -50.0
TARGET_PEAK_DB = -1.0
AUDIO_MEDIAN_MIN_DB = -200.0
AUDIO_MEDIAN_MAX_DB = 20.0
AUDIO_MEDIAN_STEP_DB = 0.01


@dataclass(frozen=True)
class Clip:
    path: Path
    duration: float
    video: dict[str, Any]
    audio: dict[str, Any] | None


@dataclass(frozen=True)
class AudioStats:
    peak_db: float
    mean_rms_db: float
    median_db: float


def require_tool(name: str) -> str:
    path = shutil.which(name)
    if not path:
        raise RuntimeError(f"Required command not found: {name}")
    return path


def parse_rate(value: str | None) -> Fraction | None:
    if not value or value in {"0/0", "N/A"}:
        return None
    try:
        rate = Fraction(value)
    except (ValueError, ZeroDivisionError):
        return None
    return rate if rate > 0 else None


def probe(path: Path) -> Clip:
    result = subprocess.run(
        [
            require_tool("ffprobe"),
            "-v",
            "error",
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
        raise RuntimeError(f"ffprobe failed for {path.name}: {result.stderr.strip()}")

    try:
        data = json.loads(result.stdout)
        streams = data["streams"]
        video = next(stream for stream in streams if stream.get("codec_type") == "video")
    except (KeyError, StopIteration, TypeError, json.JSONDecodeError) as error:
        raise RuntimeError(f"Could not read a video stream from {path}") from error

    audio = next(
        (stream for stream in streams if stream.get("codec_type") == "audio"),
        None,
    )
    try:
        duration = float(data["format"]["duration"])
    except (KeyError, TypeError, ValueError) as error:
        raise RuntimeError(f"Could not read the duration from {path}") from error
    return Clip(path=path, duration=duration, video=video, audio=audio)


def _video_paths(paths: Iterable[Path], output: Path | None) -> list[Path]:
    output_resolved = output.resolve() if output else None
    selected = [
        path
        for path in paths
        if path.is_file()
        and path.suffix.casefold() in VIDEO_EXTENSIONS
        and (output_resolved is None or path.resolve() != output_resolved)
        and not path.name.startswith(".")
    ]
    selected.sort(key=lambda item: (item.name.casefold(), str(item)))
    return selected


def find_inputs(input_dir: Path, output: Path | None) -> list[Path]:
    if not input_dir.is_dir():
        raise RuntimeError(f"Input directory does not exist: {input_dir}")
    paths = _video_paths(input_dir.iterdir(), output)
    if not paths:
        raise RuntimeError(f"No supported video files found in {input_dir}")
    return paths


def find_selected_inputs(paths: list[Path], output: Path | None) -> list[Path]:
    selected = _video_paths(paths, output)
    if not selected:
        raise RuntimeError("No supported video files were selected")
    return selected


def nominal_rate(clip: Clip) -> Fraction:
    rate = parse_rate(clip.video.get("r_frame_rate"))
    if rate is None:
        rate = parse_rate(clip.video.get("avg_frame_rate"))
    if rate is None:
        raise RuntimeError(f"Could not determine the frame rate of {clip.path.name}")
    return rate


def rate_label(rate: Fraction) -> str:
    value = float(rate)
    return f"{value:.3f}".rstrip("0").rstrip(".")


def common_resolution(clips: list[Clip]) -> tuple[int, int]:
    resolutions = [
        (int(clip.video["width"]), int(clip.video["height"]))
        for clip in clips
    ]
    counts = Counter(resolutions)
    order = {resolution: index for index, resolution in enumerate(resolutions)}
    return max(
        counts,
        key=lambda resolution: (
            counts[resolution],
            resolution[0] * resolution[1],
            -order[resolution],
        ),
    )


def copy_signature(clip: Clip) -> tuple[Any, ...]:
    video = clip.video
    audio = clip.audio
    return (
        video.get("codec_name"),
        video.get("profile"),
        video.get("pix_fmt"),
        video.get("width"),
        video.get("height"),
        video.get("r_frame_rate"),
        video.get("time_base"),
        video.get("codec_tag_string"),
        None if audio is None else audio.get("codec_name"),
        None if audio is None else audio.get("sample_rate"),
        None if audio is None else audio.get("channels"),
        None if audio is None else audio.get("channel_layout"),
        None if audio is None else audio.get("time_base"),
        None if audio is None else audio.get("codec_tag_string"),
    )


def can_stream_copy(
    clips: list[Clip],
    target_rate: Fraction,
    target_resolution: tuple[int, int],
) -> bool:
    first = clips[0]
    if first.video.get("codec_name") != "h264":
        return False
    if first.video.get("pix_fmt") != "yuv420p":
        return False
    if first.audio and (
        first.audio.get("codec_name") != "aac"
        or first.audio.get("sample_rate") != "48000"
        or first.audio.get("channels") != 2
    ):
        return False
    if nominal_rate(first) != target_rate:
        return False
    if (int(first.video["width"]), int(first.video["height"])) != target_resolution:
        return False
    signature = copy_signature(first)
    return all(
        nominal_rate(clip) == target_rate
        and (int(clip.video["width"]), int(clip.video["height"])) == target_resolution
        and copy_signature(clip) == signature
        for clip in clips[1:]
    )


def dbfs(value: float) -> float:
    if value <= 0:
        return -math.inf
    return 20 * math.log10(value)


def analyze_audio(path: Path) -> AudioStats:
    process = subprocess.Popen(
        [
            require_tool("ffmpeg"),
            "-v",
            "error",
            "-i",
            str(path),
            "-map",
            "0:a:0",
            "-f",
            "f32le",
            "-acodec",
            "pcm_f32le",
            "pipe:1",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    histogram = [0] * (
        int((AUDIO_MEDIAN_MAX_DB - AUDIO_MEDIAN_MIN_DB) / AUDIO_MEDIAN_STEP_DB)
        + 1
    )
    sample_count = 0
    sum_squares = 0.0
    peak = 0.0
    try:
        assert process.stdout is not None
        while True:
            chunk = process.stdout.read(1024 * 1024)
            if not chunk:
                break
            chunk = chunk[: len(chunk) - (len(chunk) % 4)]
            samples = array("f")
            samples.frombytes(chunk)
            for sample in samples:
                if not math.isfinite(sample):
                    continue
                magnitude = abs(sample)
                sample_count += 1
                sum_squares += sample * sample
                peak = max(peak, magnitude)
                if magnitude == 0:
                    bucket = 0
                else:
                    level = max(AUDIO_MEDIAN_MIN_DB, min(AUDIO_MEDIAN_MAX_DB, dbfs(magnitude)))
                    bucket = round(
                        (level - AUDIO_MEDIAN_MIN_DB) / AUDIO_MEDIAN_STEP_DB
                    )
                histogram[bucket] += 1
    finally:
        stderr = process.stderr.read().decode(errors="replace").strip()
        return_code = process.wait()
    if return_code != 0:
        raise RuntimeError(
            f"Audio analysis failed for {path.name}: {stderr or 'ffmpeg failed'}"
        )
    if sample_count == 0:
        raise RuntimeError(f"Audio analysis found no samples in {path.name}")

    def percentile_bucket(index: int) -> int:
        total = 0
        for bucket, amount in enumerate(histogram):
            total += amount
            if total > index:
                return bucket
        return 0

    lower = percentile_bucket((sample_count - 1) // 2)
    upper = percentile_bucket(sample_count // 2)
    median_db = AUDIO_MEDIAN_MIN_DB + (
        (lower + upper) / 2 * AUDIO_MEDIAN_STEP_DB
    )
    return AudioStats(
        peak_db=dbfs(peak),
        mean_rms_db=dbfs(math.sqrt(sum_squares / sample_count)),
        median_db=median_db,
    )


def audio_gain_db(stats: AudioStats) -> float:
    mean_gain = TARGET_MEAN_RMS_DB - stats.mean_rms_db
    median_gain = TARGET_MEDIAN_DB - stats.median_db
    balanced_gain = (mean_gain + median_gain) / 2
    peak_limited_gain = TARGET_PEAK_DB - stats.peak_db
    return min(balanced_gain, peak_limited_gain)


def h264_level(
    target_resolution: tuple[int, int],
    target_rate: Fraction,
) -> str:
    width, height = target_resolution
    pixels_per_frame = width * height
    frames_per_second = float(target_rate)
    if pixels_per_frame <= 1920 * 1080 and frames_per_second <= 60:
        return "4.2"
    if pixels_per_frame <= 3840 * 2160 and frames_per_second <= 30:
        return "5.1"
    return "5.2"


def shell_quote(path: Path) -> str:
    return "'" + str(path).replace("'", "'\\''") + "'"


def write_concat_list(paths: list[Path]) -> Path:
    temporary = tempfile.NamedTemporaryFile(
        mode="w",
        prefix="resolve-concat-",
        suffix=".txt",
        delete=False,
        encoding="utf-8",
    )
    try:
        for path in paths:
            temporary.write(f"file {shell_quote(path)}\n")
        return Path(temporary.name)
    finally:
        temporary.close()


def format_seconds(seconds: float | None) -> str:
    if seconds is None or seconds < 0:
        return "--:--:--"
    whole = int(seconds)
    hours, remainder = divmod(whole, 3600)
    minutes, seconds_value = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds_value:02d}"


def terminate_process(process: subprocess.Popen) -> None:
    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()


def effective_jobs(requested: int, item_count: int) -> int:
    if requested < 0:
        raise RuntimeError("--jobs must be zero or greater")
    if item_count <= 0:
        return 1
    if requested:
        return min(requested, item_count)
    return min(3, item_count, max(1, (os.cpu_count() or 1) // 2))


def run_command(command: list[str], label: str) -> None:
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        output, _ = process.communicate()
    except KeyboardInterrupt:
        terminate_process(process)
        raise
    result = subprocess.CompletedProcess(command, process.returncode, output)
    if result.returncode != 0:
        details = "\n".join(result.stdout.splitlines()[-8:])
        raise RuntimeError(f"FFmpeg failed during {label}:\n{details}")


def run_parallel_commands(commands: list[list[str]], jobs: int) -> None:
    completed = 0
    with ThreadPoolExecutor(max_workers=jobs) as executor:
        futures = [
            executor.submit(run_command, command, f"part {index + 1}")
            for index, command in enumerate(commands)
        ]
        for future in as_completed(futures):
            future.result()
            completed += 1
            print(f"Parallel normalization: {completed}/{len(commands)} parts complete")


def calculate_audio_gains(
    clips: list[Clip],
    jobs: int,
) -> dict[Path, tuple[AudioStats, float]]:
    audio_clips = [clip for clip in clips if clip.audio]
    if not audio_clips:
        return {}
    worker_count = min(jobs, len(audio_clips))
    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        stats = list(executor.map(analyze_audio, (clip.path for clip in audio_clips)))
    return {
        clip.path: (clip_stats, audio_gain_db(clip_stats))
        for clip, clip_stats in zip(audio_clips, stats)
    }


def run_ffmpeg(command: list[str], total_duration: float, label: str) -> None:
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    started = time.monotonic()
    current = 0.0
    speed = ""
    last_report = 0.0
    tail: list[str] = []
    try:
        assert process.stdout is not None
        for line in process.stdout:
            line = line.strip()
            if not line:
                continue
            if line.startswith("out_time_us="):
                try:
                    current = max(0.0, float(line.split("=", 1)[1]) / 1_000_000)
                except ValueError:
                    pass
            elif line.startswith("speed="):
                speed = line.split("=", 1)[1]
            elif not line.startswith(("frame=", "fps=", "stream_")):
                tail.append(line)
                tail = tail[-8:]

            now = time.monotonic()
            if now - last_report >= 0.5:
                fraction = min(1.0, current / total_duration) if total_duration else 0.0
                elapsed = now - started
                eta = elapsed * (1 - fraction) / fraction if fraction > 0 else None
                message = (
                    f"\r{label}: {fraction * 100:6.2f}%  "
                    f"elapsed {format_seconds(elapsed)}  "
                    f"ETA {format_seconds(eta)}  speed {speed or '--'}"
                )
                if sys.stdout.isatty():
                    print(message, end="", flush=True)
                else:
                    print(message.lstrip(), flush=True)
                last_report = now
    finally:
        if process.poll() is None:
            terminate_process(process)
        return_code = process.wait()
        if sys.stdout.isatty():
            print()
    if return_code != 0:
        details = "\n".join(tail)
        raise RuntimeError(f"FFmpeg failed during {label}:\n{details}")


class PerformanceMode:
    def __init__(self, mode: str) -> None:
        self.mode = mode
        self.tool = shutil.which("powerprofilesctl")
        self.previous: str | None = None
        self.changed = False

    def __enter__(self) -> "PerformanceMode":
        if self.mode == "off" or not self.tool:
            return self
        result = subprocess.run(
            [self.tool, "get"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            if self.mode == "on":
                raise RuntimeError("Could not read the current power profile")
            return self
        self.previous = result.stdout.strip()
        if self.previous == "performance":
            return self
        result = subprocess.run(
            [self.tool, "set", "performance"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            if self.mode == "on":
                raise RuntimeError(
                    f"Could not enable performance mode: {result.stderr.strip()}"
                )
            return self
        self.changed = True
        return self

    def __exit__(self, _type: Any, _value: Any, _traceback: Any) -> None:
        if not self.changed or not self.previous or not self.tool:
            return
        current = subprocess.run(
            [self.tool, "get"],
            capture_output=True,
            text=True,
            check=False,
        )
        if current.returncode == 0 and current.stdout.strip() == "performance":
            subprocess.run(
                [self.tool, "set", self.previous],
                capture_output=True,
                text=True,
                check=False,
            )


def video_encoder_options(
    video_encoder: str,
    target_resolution: tuple[int, int],
    target_rate: Fraction,
) -> list[str]:
    options = ["-c:v", video_encoder]
    if video_encoder == "h264_nvenc":
        options.extend(
            ["-preset", "p6", "-tune", "hq", "-rc", "vbr", "-cq", "19", "-b:v", "0"]
        )
    else:
        options.extend(["-preset", "slow", "-crf", "20"])
    options.extend(
        [
            "-profile:v",
            "high",
            "-level:v",
            h264_level(target_resolution, target_rate),
            "-pix_fmt",
            "yuv420p",
            "-tag:v",
            "avc1",
            "-color_primaries",
            "bt709",
            "-color_trc",
            "bt709",
            "-colorspace",
            "bt709",
        ]
    )
    return options


def audio_encoder_options() -> list[str]:
    return [
        "-c:a",
        "aac",
        "-profile:a",
        "aac_low",
        "-b:a",
        "192k",
        "-ar",
        "48000",
        "-ac",
        "2",
    ]


def video_filter(
    target_rate: Fraction,
    target_resolution: tuple[int, int],
) -> str:
    width, height = target_resolution
    return (
        f"fps={target_rate.numerator}/{target_rate.denominator},"
        f"scale={width}:{height}:force_original_aspect_ratio=decrease:flags=fast_bilinear,"
        f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color=black,"
        "setsar=1"
    )


def build_normalized_part_command(
    clip: Clip,
    output: Path,
    target_rate: Fraction,
    target_resolution: tuple[int, int],
    video_encoder: str,
    audio_gain: float,
) -> list[str]:
    command = [
        require_tool("ffmpeg"),
        "-hide_banner",
        "-y",
        "-nostdin",
        "-loglevel",
        "error",
        "-i",
        str(clip.path),
    ]
    if clip.audio is None:
        command.extend(
            [
                "-f",
                "lavfi",
                "-t",
                f"{clip.duration:.6f}",
                "-i",
                "anullsrc=r=48000:cl=stereo",
            ]
        )
    command.extend(
        [
            "-map",
            "0:v:0",
            "-map",
            "0:a:0" if clip.audio else "1:a:0",
            "-vf",
            f"{video_filter(target_rate, target_resolution)},setpts=PTS-STARTPTS",
        ]
    )
    if clip.audio:
        audio_filter = "aresample=48000:async=1:first_pts=0"
        if abs(audio_gain) >= 0.01:
            audio_filter += f",volume={audio_gain:.2f}dB"
        audio_filter += ",asetpts=PTS-STARTPTS"
        command.extend(["-af", audio_filter])
    command.extend(video_encoder_options(video_encoder, target_resolution, target_rate))
    command.extend(
        [
            *audio_encoder_options(),
            "-shortest",
            "-avoid_negative_ts",
            "make_zero",
            "-video_track_timescale",
            "90000",
            "-f",
            "mp4",
            str(output),
        ]
    )
    return command


def build_normalized_command(
    clips: list[Clip],
    output: Path,
    target_rate: Fraction,
    target_resolution: tuple[int, int],
    video_encoder: str,
    audio_gains: dict[Path, float],
) -> list[str]:
    command = [require_tool("ffmpeg"), "-hide_banner", "-y", "-nostdin", "-loglevel", "error"]
    for clip in clips:
        command.extend(["-i", str(clip.path)])

    filters: list[str] = []
    concat_inputs: list[str] = []
    for index, clip in enumerate(clips):
        filters.append(
            f"[{index}:v:0]{video_filter(target_rate, target_resolution)},"
            f"setpts=PTS-STARTPTS[v{index}]"
        )
        if clip.audio:
            audio_chain = "aresample=48000:async=1:first_pts=0"
            gain = audio_gains.get(clip.path, 0.0)
            if abs(gain) >= 0.01:
                audio_chain += f",volume={gain:.2f}dB"
            filters.append(
                f"[{index}:a:0]{audio_chain},asetpts=PTS-STARTPTS[a{index}]"
            )
        else:
            filters.append(
                f"anullsrc=r=48000:cl=stereo,atrim=duration={clip.duration:.6f},"
                f"asetpts=PTS-STARTPTS[a{index}]"
            )
        concat_inputs.extend([f"[v{index}]", f"[a{index}]"])

    filters.append(
        "".join(concat_inputs)
        + f"concat=n={len(clips)}:v=1:a=1[outv][outa]"
    )
    command.extend(
        [
            "-filter_complex",
            ";".join(filters),
            "-map",
            "[outv]",
            "-map",
            "[outa]",
        ]
    )
    command.extend(
        [
            *video_encoder_options(video_encoder, target_resolution, target_rate),
            *audio_encoder_options(),
            "-movflags",
            "+faststart",
            "-f",
            "mp4",
            "-progress",
            "pipe:1",
            "-nostats",
            str(output),
        ]
    )
    return command


def build_copy_command(list_path: Path, output: Path) -> list[str]:
    return [
        require_tool("ffmpeg"),
        "-hide_banner",
        "-y",
        "-nostdin",
        "-loglevel",
        "error",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(list_path),
        "-map",
        "0:v:0",
        "-map",
        "0:a:0?",
        "-c",
        "copy",
        "-movflags",
        "+faststart",
        "-f",
        "mp4",
        "-progress",
        "pipe:1",
        "-nostats",
        str(output),
    ]


def run_normalization(
    clips: list[Clip],
    output: Path,
    partial: Path,
    target_rate: Fraction,
    target_resolution: tuple[int, int],
    video_encoder: str,
    audio_gains: dict[Path, float],
    strategy: str,
    jobs: int,
    total_duration: float,
    dry_run: bool,
) -> None:
    if strategy == "single":
        command = build_normalized_command(
            clips,
            partial,
            target_rate,
            target_resolution,
            video_encoder,
            audio_gains,
        )
        if dry_run:
            print(" ".join(command))
        else:
            run_ffmpeg(command, total_duration, "Normalizing and concatenating")
        return

    created_parts_dir = not dry_run
    parts_dir = (
        output.parent / f".{output.stem}.parts"
        if dry_run
        else Path(
            tempfile.mkdtemp(
                prefix=f".{output.stem}.parts-",
                dir=output.parent,
            )
        )
    )
    list_path: Path | None = None
    try:
        part_paths = [
            parts_dir / f"part-{index:04d}.mp4"
            for index in range(len(clips))
        ]
        commands = [
            build_normalized_part_command(
                clip,
                part_path,
                target_rate,
                target_resolution,
                video_encoder,
                audio_gains.get(clip.path, 0.0),
            )
            for clip, part_path in zip(clips, part_paths)
        ]
        print(f"Parallel normalization: {len(clips)} parts, {jobs} workers")
        if dry_run:
            for index, command in enumerate(commands, start=1):
                print(f"Part {index}: {' '.join(command)}")
            list_path = parts_dir / "concat-list.txt"
            print(
                "Final join: "
                + " ".join(build_copy_command(list_path, partial))
            )
            return

        run_parallel_commands(commands, jobs)
        list_path = write_concat_list(part_paths)
        run_ffmpeg(
            build_copy_command(list_path, partial),
            total_duration,
            "Joining normalized parts",
        )
    finally:
        if list_path:
            list_path.unlink(missing_ok=True)
        if created_parts_dir and parts_dir.exists():
            shutil.rmtree(parts_dir)


@dataclass(frozen=True)
class ConcatEntry:
    path: Path
    is_dir: bool


class ConcatTUI:
    def __init__(
        self,
        stdscr: Any,
        root: Path,
        title: str = "| RESOLVE CONCAT + FPS // SELECT INPUT VIDEOS",
    ):
        self.stdscr = stdscr
        self.root = root.expanduser().resolve()
        self.title = title
        self.entries: list[ConcatEntry] = []
        self.cursor = 0
        self.offset = 0
        self.selection: set[Path] = set()
        self.message = "Space selects; a selects all videos; Enter runs."

    def load(self) -> None:
        try:
            children = sorted(
                self.root.iterdir(),
                key=lambda path: (not path.is_dir(), path.name.casefold()),
            )
        except OSError as error:
            self.entries = []
            self.message = f"Cannot read {self.root}: {error}"
            return
        self.entries = [
            ConcatEntry(path, path.is_dir())
            for path in children
            if not path.name.startswith(".")
            and (path.is_dir() or path.suffix.casefold() in VIDEO_EXTENSIONS)
        ]
        self.cursor = min(self.cursor, max(0, len(self.entries) - 1))

    def selected_paths(self) -> list[Path]:
        return sorted(
            (path for path in self.selection if path.is_file()),
            key=lambda path: (path.name.casefold(), str(path)),
        )

    def draw(self) -> None:
        self.stdscr.erase()
        height, width = self.stdscr.getmaxyx()
        if height < 12 or width < 70:
            self.stdscr.addnstr(
                0,
                0,
                "Terminal too small. Resize to at least 70x12.",
                max(0, width - 1),
            )
            self.stdscr.addnstr(2, 0, "q quit", max(0, width - 1))
            self.stdscr.refresh()
            return

        self.stdscr.addnstr(
            0,
            0,
            self.title,
            width - 1,
            curses.color_pair(1) | curses.A_BOLD,
        )
        self.stdscr.addnstr(
            1,
            0,
            f"| PATH {self.root}",
            width - 1,
            curses.color_pair(3),
        )
        self.stdscr.addnstr(
            2,
            0,
            "| Up/down or j/k move  Right/l open  Left/h/backspace up  Space select  a all  n clear  Enter run  ? help  q quit",
            width - 1,
            curses.color_pair(2),
        )
        list_top = 4
        list_bottom = max(list_top + 1, height - 5)
        visible = list_bottom - list_top
        if self.cursor < self.offset:
            self.offset = self.cursor
        if self.cursor >= self.offset + visible:
            self.offset = self.cursor - visible + 1
        for row, entry in enumerate(
            self.entries[self.offset : self.offset + visible],
            list_top,
        ):
            index = row - list_top + self.offset
            marker = "[x]" if entry.path in self.selection else "[ ]"
            icon = "[DIR]" if entry.is_dir else "[VID]"
            label = entry.path.name + ("/" if entry.is_dir else "")
            text = f"{marker} {icon} {label}"
            attribute = (
                curses.A_REVERSE
                if index == self.cursor
                else curses.color_pair(2)
            )
            self.stdscr.addnstr(row, 0, text, width - 1, attribute)
        self.stdscr.addnstr(
            height - 3,
            0,
            f"Selected {len(self.selection)} video(s)",
            width - 1,
            curses.color_pair(1),
        )
        self.stdscr.addnstr(
            height - 2,
            0,
            self.message,
            width - 1,
            curses.color_pair(4) | curses.A_BOLD,
        )
        self.stdscr.refresh()

    def help(self) -> None:
        self.stdscr.erase()
        height, width = self.stdscr.getmaxyx()
        if "CONCAT + FPS" in self.title:
            operation = "concat + FPS"
        elif "FPS" in self.title:
            operation = "FPS enhancement"
        else:
            operation = "concat"
        lines = [
            f"Resolve {operation} help",
            "",
            "Navigate to the folder containing the clips.",
            "Space selects or clears the highlighted video.",
            "a selects every video in the current folder; n clears all selections.",
            "Selections remain active while you navigate between folders.",
            f"Enter runs {operation} on the selected videos in filename order.",
            "The output is written beside the current folder unless --output is used.",
            "",
            "Keys: arrows/j/k move | Right/l open | Left/h/backspace up",
            "Space select | a all | n clear | Enter run | r rescan | q quit",
            "",
            "Press any key to return.",
        ]
        for index, line in enumerate(lines[: max(0, height - 1)]):
            self.stdscr.addnstr(index, 0, line, max(0, width - 1))
        self.stdscr.refresh()
        self.stdscr.timeout(-1)
        try:
            self.stdscr.getch()
        finally:
            self.stdscr.timeout(100)

    def run(self) -> tuple[list[Path], Path] | None:
        if curses is None:
            return None
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
        except curses.error:
            pass
        self.load()
        while True:
            self.draw()
            key = self.stdscr.getch()
            if key == -1:
                continue
            if key in (ord("q"), ord("Q")):
                return None
            if key in (curses.KEY_DOWN, ord("j")) and self.entries:
                self.cursor = min(len(self.entries) - 1, self.cursor + 1)
            elif key in (curses.KEY_UP, ord("k")) and self.entries:
                self.cursor = max(0, self.cursor - 1)
            elif key in (curses.KEY_RIGHT, ord("l")) and self.entries:
                entry = self.entries[self.cursor]
                if entry.is_dir:
                    self.root = entry.path
                    self.cursor = self.offset = 0
                    self.load()
                else:
                    self.message = "Select videos with Space."
            elif key in (curses.KEY_LEFT, ord("h"), curses.KEY_BACKSPACE, 127, 8):
                if self.root.parent != self.root:
                    self.root = self.root.parent
                    self.cursor = self.offset = 0
                    self.load()
            elif key in (curses.KEY_ENTER, 10, 13):
                paths = self.selected_paths()
                if paths:
                    return paths, self.root
                self.message = "No videos selected. Use Space or a first."
            elif key == ord(" ") and self.entries:
                entry = self.entries[self.cursor]
                if entry.is_dir:
                    self.message = "Folders are for navigation; select video files."
                elif entry.path in self.selection:
                    self.selection.remove(entry.path)
                else:
                    self.selection.add(entry.path)
            elif key in (ord("a"), ord("A")):
                self.selection.update(
                    entry.path for entry in self.entries if not entry.is_dir
                )
                self.message = "Selected all videos in the current folder."
            elif key in (ord("n"), ord("N")):
                self.selection.clear()
                self.message = "Selection cleared."
            elif key in (ord("r"), ord("R")):
                self.load()
                self.message = "Rescanned current folder."
            elif key == ord("?"):
                self.help()


def interactive_selection(
    root: Path,
    title: str = "| RESOLVE CONCAT + FPS // SELECT INPUT VIDEOS",
) -> tuple[list[Path], Path] | None:
    if curses is None:
        raise RuntimeError(
            "Python curses is unavailable; pass an input directory explicitly."
        )
    if not root.is_dir():
        raise RuntimeError(f"TUI root directory does not exist: {root}")
    return curses.wrapper(lambda stdscr: ConcatTUI(stdscr, root, title).run())


def parse_arguments(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run concat-first FPS enhancement; no input opens the selector TUI."
        )
    )
    parser.add_argument(
        "input_dir",
        nargs="?",
        type=Path,
        help="Video file or folder; omit to open the selector TUI",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=DEFAULT_TUI_ROOT,
        help=f"TUI starting folder (default: {DEFAULT_TUI_ROOT})",
    )
    parser.add_argument(
        "--concat-only",
        action="store_true",
        help="Only concatenate; skip FPS enhancement",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_FPS_MODEL,
        help="RIFE model for the integrated FPS pass (default: 4.26)",
    )
    parser.add_argument(
        "--engine",
        choices=("rve", "vs-rife"),
        default=DEFAULT_FPS_ENGINE,
        help="FPS backend (default: rve; vs-rife is the VapourSynth fallback)",
    )
    parser.add_argument(
        "--rve-root",
        type=Path,
        default=DEFAULT_RVE_ROOT,
        help="Corrected REAL-Video-Enhancer checkout",
    )
    parser.add_argument(
        "--rve-model",
        type=Path,
        default=DEFAULT_RVE_MODEL,
        help="RIFE 4.26 model used by the RVE backend",
    )
    parser.add_argument(
        "--rve-shims",
        type=Path,
        default=DEFAULT_RVE_SHIMS,
        help="Optional compatibility modules for the RVE Python environment",
    )
    parser.add_argument(
        "--encoder",
        choices=("h264_nvenc", "libx264"),
        default="h264_nvenc",
        help="delivery encoder for the integrated FPS pass",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Output MP4 path; defaults beside the input folder",
    )
    parser.add_argument(
        "--mode",
        choices=("auto", "copy", "gpu", "cpu"),
        default="auto",
        help="auto selects copy when safe, otherwise GPU normalization",
    )
    parser.add_argument(
        "--gpu",
        choices=("auto", "on", "off"),
        default="auto",
        help="GPU fallback policy for normalization (default: auto)",
    )
    parser.add_argument(
        "--strategy",
        choices=("parallel", "single"),
        default="parallel",
        help="parallelize per-file normalization before the final copy join",
    )
    parser.add_argument(
        "--jobs",
        type=int,
        default=0,
        help="parallel normalization workers (default: auto, capped at three)",
    )
    parser.add_argument(
        "--audio-normalization",
        choices=("on", "off"),
        default="on",
        help=(
            "audio gain policy for --concat-only; the integrated FPS workflow "
            "preserves audio gain"
        ),
    )
    parser.add_argument(
        "--performance-mode",
        choices=("auto", "on", "off"),
        default="auto",
        help="Temporarily use the system performance profile",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print the plan only")
    parser.add_argument("--force", action="store_true", help="Replace an existing output")
    return parser.parse_args(argv)


def concatenate(
    paths: list[Path],
    input_dir: Path,
    requested_output: Path | None,
    arguments: argparse.Namespace,
) -> int:
    clips = [probe(path) for path in paths]
    jobs = effective_jobs(arguments.jobs, len(clips))
    target_rate = min((nominal_rate(clip) for clip in clips), key=float)
    target_resolution = common_resolution(clips)
    output = requested_output or (
        input_dir.parent
        / f"{input_dir.name}-concatenated-{rate_label(target_rate)}fps.mp4"
    )
    audio_normalization = arguments.audio_normalization == "on"
    copy_safe = can_stream_copy(clips, target_rate, target_resolution)
    if audio_normalization and any(clip.audio for clip in clips):
        copy_safe = False

    if arguments.mode == "copy" and not copy_safe:
        raise RuntimeError(
            "Stream copy is unsafe because the inputs do not share identical "
            "universal H.264/AAC parameters, resolution, and frame rate, or "
            "audio normalization is enabled."
        )
    use_copy = arguments.mode == "copy" or (
        arguments.mode == "auto" and copy_safe
    )
    if arguments.mode == "gpu":
        use_copy = False
    if arguments.mode == "cpu":
        use_copy = False

    if output.exists() and not arguments.force and not arguments.dry_run:
        raise RuntimeError(f"Output already exists; use --force to replace it: {output}")
    partial = output.with_name(f".{output.name}.partial")
    if not arguments.dry_run:
        output.parent.mkdir(parents=True, exist_ok=True)
        if partial.exists():
            partial.unlink()

    total_duration = sum(clip.duration for clip in clips)
    print(f"Inputs: {len(clips)} files, {format_seconds(total_duration)} total")
    print(f"Resolution: {target_resolution[0]}x{target_resolution[1]}")
    print(f"Frame rate: {target_rate.numerator}/{target_rate.denominator} ({rate_label(target_rate)} fps)")
    print(f"Output: {output}")

    list_path: Path | None = None
    audio_gains: dict[Path, float] = {}
    try:
        performance_context = (
            nullcontext()
            if arguments.dry_run
            else PerformanceMode(arguments.performance_mode)
        )
        with performance_context:
            if use_copy:
                list_path = write_concat_list(paths)
                command = build_copy_command(list_path, partial)
                print("Mode: stream copy (no re-encode)")
                if arguments.dry_run:
                    print(" ".join(command))
                    return 0
                run_ffmpeg(command, total_duration, "Concatenating")
            else:
                if audio_normalization:
                    print(
                        "Audio targets: mean RMS "
                        f"{TARGET_MEAN_RMS_DB:.0f} dBFS, median "
                        f"{TARGET_MEDIAN_DB:.0f} dBFS, peak cap "
                        f"{TARGET_PEAK_DB:.0f} dBFS"
                    )
                    gain_info = calculate_audio_gains(
                        clips,
                        jobs if arguments.strategy == "parallel" else 1,
                    )
                    for clip in clips:
                        if clip.path not in gain_info:
                            continue
                        stats, _ = gain_info[clip.path]
                        gain = audio_gain_db(stats)
                        audio_gains[clip.path] = gain
                        print(
                            f"Audio {clip.path.name}: gain {gain:+.2f} dB; "
                            f"estimated mean {stats.mean_rms_db + gain:+.2f} dBFS; "
                            f"median {stats.median_db + gain:+.2f} dBFS"
                        )
                encoder = "libx264"
                if (
                    arguments.mode == "gpu"
                    or (
                        arguments.mode == "auto"
                        and arguments.gpu != "off"
                        and shutil.which("nvidia-smi")
                    )
                ):
                    encoder = "h264_nvenc"
                print(
                    "Mode: "
                    + (
                        "GPU H.264 normalization"
                        if encoder == "h264_nvenc"
                        else "CPU H.264 normalization"
                    )
                )
                if arguments.strategy == "parallel":
                    print(f"Strategy: parallel per-file normalization ({jobs} workers)")
                else:
                    print("Strategy: single filter graph")
                try:
                    run_normalization(
                        clips,
                        output,
                        partial,
                        target_rate,
                        target_resolution,
                        encoder,
                        audio_gains,
                        arguments.strategy,
                        jobs,
                        total_duration,
                        arguments.dry_run,
                    )
                except RuntimeError:
                    if encoder != "h264_nvenc" or arguments.gpu == "on":
                        raise
                    print("GPU encoding failed; retrying with CPU H.264.")
                    if partial.exists():
                        partial.unlink()
                    run_normalization(
                        clips,
                        output,
                        partial,
                        target_rate,
                        target_resolution,
                        "libx264",
                        audio_gains,
                        arguments.strategy,
                        jobs,
                        total_duration,
                        arguments.dry_run,
                    )
                if arguments.dry_run:
                    return 0
        os.replace(partial, output)
    finally:
        if list_path:
            list_path.unlink(missing_ok=True)
        if partial.exists():
            partial.unlink()

    print(f"Finished: {output}")
    return 0


def main(argv: list[str] | None = None) -> int:
    arguments = parse_arguments(argv)
    requested_output = (
        arguments.output.expanduser().resolve() if arguments.output else None
    )
    if arguments.input_dir is None:
        selection = interactive_selection(arguments.root.expanduser().resolve())
        if selection is None:
            return 0
        selected_paths, input_dir = selection
        paths = find_selected_inputs(selected_paths, requested_output)
    else:
        input_dir = arguments.input_dir.expanduser().resolve()
        if input_dir.is_dir():
            paths = find_inputs(input_dir, requested_output)
        elif input_dir.is_file():
            paths = find_selected_inputs([input_dir], requested_output)
            input_dir = input_dir.parent
        else:
            raise RuntimeError(f"Input path does not exist: {input_dir}")
    if arguments.concat_only:
        return concatenate(paths, input_dir, requested_output, arguments)
    from resolve_fps import run_combined_pipeline

    return run_combined_pipeline(
        paths,
        input_dir,
        requested_output,
        arguments.model,
        arguments.encoder,
        arguments.performance_mode,
        arguments.dry_run,
        arguments.force,
        arguments.engine,
        arguments.rve_root.expanduser().resolve(),
        arguments.rve_model.expanduser().resolve(),
        arguments.rve_shims.expanduser().resolve(),
    )


if __name__ == "__main__":
    sys.modules.setdefault("resolve_concat", sys.modules[__name__])
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nCancelled.", file=sys.stderr)
        raise SystemExit(130)
    except RuntimeError as error:
        print(f"Error: {error}", file=sys.stderr)
        raise SystemExit(1)
