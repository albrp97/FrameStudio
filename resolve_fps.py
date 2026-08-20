#!/usr/bin/env python3
"""Enhance selected video(s) to a target frame rate with the validated RIFE path."""

from __future__ import annotations

import argparse
import json
import os
import queue
import re
import shutil
import subprocess
import tempfile
import threading
import time
from argparse import Namespace
from contextlib import contextmanager
from fractions import Fraction
from pathlib import Path
from typing import BinaryIO

from resolve_concat import (
    DEFAULT_TUI_ROOT,
    PerformanceMode,
    concatenate,
    find_inputs,
    find_selected_inputs,
    interactive_selection,
    rate_label,
)


PROGRESS_PATTERN = re.compile(
    r"frame=(?P<frame>\d+)/(?P<total>\d+)\s+elapsed=(?P<elapsed>[0-9.]+)s"
)
DEFAULT_MODEL = "4.26"
DEFAULT_TARGET_FPS = Fraction(60, 1)
DEFAULT_NVENC_QP = 18
DEFAULT_FPS_PYTHON = (
    Path.home() / ".cache" / "resolve-fps" / "trt" / "bin" / "python"
)
DEFAULT_FPS_SITE = (
    Path.home()
    / ".cache"
    / "resolve-fps"
    / "trt"
    / "lib"
    / "python3.13"
    / "site-packages"
)
DEFAULT_GRAPH = Path(__file__).resolve().parent / "benchmarks" / "fps.vpy"
DEFAULT_TRT_CACHE = (
    Path.home() / ".cache" / "resolve-fps" / "engines-pixel-fallback"
)
DEFAULT_BESTSOURCE = (
    Path.home()
    / ".cache"
    / "resolve-fps"
    / "plugins"
    / "usr"
    / "lib"
    / "python3.14"
    / "site-packages"
    / "vapoursynth"
    / "plugins"
    / "libbestsource.so"
)


def require_tool(name: str) -> str:
    path = shutil.which(name)
    if not path:
        raise RuntimeError(f"Required command not found: {name}")
    return path


def parse_fraction(value: str) -> Fraction:
    try:
        result = Fraction(value)
    except (ValueError, ZeroDivisionError) as error:
        raise argparse.ArgumentTypeError(f"invalid rational value: {value}") from error
    if result <= 0:
        raise argparse.ArgumentTypeError("the frame rate must be greater than zero")
    return result


def probe_video(path: Path) -> tuple[Fraction, int]:
    command = [
        require_tool("ffprobe"),
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=r_frame_rate,avg_frame_rate,nb_read_frames,nb_frames",
        "-of",
        "json",
        str(path),
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"ffprobe failed for {path.name}: {result.stderr.strip()}")
    try:
        stream = json.loads(result.stdout)["streams"][0]
        frame_rate = next(
            Fraction(value)
            for key in ("r_frame_rate", "avg_frame_rate")
            if (value := stream.get(key)) and value not in {"N/A", "0/0"}
        )
        frame_value = stream.get("nb_frames")
    except (
        KeyError,
        IndexError,
        StopIteration,
        TypeError,
        ValueError,
        ZeroDivisionError,
        json.JSONDecodeError,
    ) as error:
        raise RuntimeError(f"Could not read frame metadata from {path}") from error
    if not frame_value or frame_value == "N/A":
        counted = subprocess.run(
            [command[0], "-count_frames", *command[1:]],
            capture_output=True,
            text=True,
            check=False,
        )
        if counted.returncode != 0:
            raise RuntimeError(
                f"ffprobe frame count failed for {path.name}: "
                f"{counted.stderr.strip()}"
            )
        try:
            frame_value = json.loads(counted.stdout)["streams"][0]["nb_read_frames"]
        except (KeyError, IndexError, TypeError, json.JSONDecodeError) as error:
            raise RuntimeError(f"Could not count frames in {path}") from error
    try:
        frame_count = int(frame_value)
    except (TypeError, ValueError) as error:
        raise RuntimeError(f"Invalid frame count in {path}") from error
    if frame_rate <= 0 or frame_count <= 0:
        raise RuntimeError(f"Invalid frame metadata from {path}")
    return frame_rate, frame_count


def target_frame_count(
    source_rate: Fraction,
    source_frames: int,
    target_rate: Fraction,
) -> int:
    factor = target_rate / source_rate
    exact_count = source_frames * factor
    return max(
        1,
        (exact_count.numerator + exact_count.denominator // 2)
        // exact_count.denominator,
    )


def default_output(
    paths: list[Path],
    current_dir: Path,
    model: str,
    target_rate: Fraction,
) -> Path:
    label = rate_label(target_rate)
    if len(paths) == 1:
        source = paths[0]
        return source.with_name(
            f"{source.stem}-rife{model}-{label}fps.mp4"
        )
    return current_dir / f"{current_dir.name}-rife{model}-{label}fps.mp4"


def build_encode_command(
    source: Path,
    partial: Path,
    encoder: str,
) -> list[str]:
    command = [
        require_tool("ffmpeg"),
        "-hide_banner",
        "-y",
        "-nostdin",
        "-loglevel",
        "error",
        "-f",
        "yuv4mpegpipe",
        "-i",
        "pipe:0",
        "-i",
        str(source),
        "-map",
        "0:v:0",
        "-map",
        "1:a:0?",
        "-c:v",
        encoder,
    ]
    if encoder == "h264_nvenc":
        command.extend(
            ["-preset", "p1", "-rc", "constqp", "-qp", str(DEFAULT_NVENC_QP)]
        )
    else:
        command.extend(["-preset", "slow", "-crf", "20"])
    command.extend(
        [
            "-profile:v",
            "high",
            "-pix_fmt",
            "yuv420p",
            "-color_range",
            "tv",
            "-colorspace",
            "bt709",
            "-color_primaries",
            "bt709",
            "-color_trc",
            "bt709",
            "-c:a",
            "copy",
            "-movflags",
            "+faststart",
            "-f",
            "mp4",
            str(partial),
        ]
    )
    return command


def format_clock(seconds: float | None) -> str:
    if seconds is None or seconds < 0:
        return "--:--:--"
    whole = int(seconds)
    hours, remainder = divmod(whole, 3600)
    minutes, seconds_value = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds_value:02d}"


def progress_line(
    completed: int,
    total: int,
    started: float,
    now: float | None = None,
) -> str:
    now = time.monotonic() if now is None else now
    elapsed = max(0.0, now - started)
    fraction = min(1.0, completed / total) if total else 0.0
    width = 30
    position = min(width - 1, int(fraction * width)) if width else 0
    bar = "=" * position + "C" + "-" * max(0, width - position - 1)
    speed = completed / elapsed if elapsed > 0 else 0.0
    eta = (total - completed) / speed if speed > 0 else None
    return (
        f"[{bar}] {fraction * 100:6.2f}% "
        f"frame {completed}/{total} pipeline {speed:7.2f} fps "
        f"elapsed {format_clock(elapsed)} ETA {format_clock(eta)}"
    )


def drain_stderr(
    stream: BinaryIO,
    label: str,
    messages: queue.Queue[tuple[str, str | None]],
) -> None:
    for raw_line in iter(stream.readline, b""):
        messages.put((label, raw_line.decode(errors="replace").rstrip()))
    stream.close()
    messages.put((label, None))


@contextmanager
def performance_scope(mode: str, dry_run: bool):
    if dry_run:
        print("Performance mode: unchanged (dry run).")
        yield
        return
    performance = PerformanceMode(mode)
    try:
        with performance:
            if performance.changed:
                print(
                    "Performance mode: performance (temporary); "
                    f"previous profile: {performance.previous}"
                )
            else:
                print(
                    "Performance mode: unchanged "
                    f"({performance.previous or 'unavailable'})."
                )
            yield
    finally:
        if performance.changed:
            print(f"Performance mode restored: {performance.previous}")


def run_interpolation(
    source: Path,
    output: Path,
    target_rate: Fraction,
    target_frames: int,
    arguments: Namespace,
) -> None:
    if output.resolve() == source.resolve():
        raise RuntimeError("The FPS output must be different from the input")
    if output.exists() and not arguments.force:
        raise RuntimeError(f"Output already exists; use --force to replace it: {output}")
    if not arguments.python.is_file():
        raise RuntimeError(
            f"FPS Python environment was not found: {arguments.python}"
        )
    if not arguments.graph.is_file():
        raise RuntimeError(f"VapourSynth graph was not found: {arguments.graph}")
    if not arguments.site_packages.is_dir():
        raise RuntimeError(
            f"FPS site-packages directory was not found: {arguments.site_packages}"
        )
    if not arguments.trt_cache.is_dir():
        raise RuntimeError(f"TensorRT cache was not found: {arguments.trt_cache}")
    if not arguments.bestsource.is_file():
        raise RuntimeError(
            f"BestSource plugin was not found: {arguments.bestsource}"
        )

    helper = Path(__file__).resolve().parent / "benchmarks" / "vsrawpipe.py"
    partial = output.with_name(f".{output.name}.partial")
    output.parent.mkdir(parents=True, exist_ok=True)
    partial.unlink(missing_ok=True)
    environment = os.environ.copy()
    environment.update(
        {
            "SOURCE": str(source),
            "MODEL": arguments.model,
            "TRT_CACHE": str(arguments.trt_cache),
            "INPUT_FORMAT": "RGBH",
            "TRT_TORCH_PIXEL": "1",
            "BESTSOURCE_PLUGIN": str(arguments.bestsource),
            "LIMIT_SECONDS": "0",
            "TARGET_FRAMES": str(target_frames),
            "TARGET_FPS_NUM": str(target_rate.numerator),
            "TARGET_FPS_DEN": str(target_rate.denominator),
            "PYTHONPATH": os.pathsep.join(
                [str(arguments.site_packages), environment.get("PYTHONPATH", "")]
            ).rstrip(os.pathsep),
        }
    )
    writer: subprocess.Popen[bytes] | None = None
    encoder: subprocess.Popen[bytes] | None = None
    messages: queue.Queue[tuple[str, str | None]] = queue.Queue()
    threads: list[threading.Thread] = []
    writer_errors: list[str] = []
    encoder_errors: list[str] = []
    completed = 0
    started = time.monotonic()
    progress_is_tty = os.isatty(1)

    def render(force: bool = False) -> None:
        if not progress_is_tty and not force:
            return
        text = progress_line(completed, target_frames, started)
        if progress_is_tty:
            print(f"\r{text}", end="", flush=True)
        elif force:
            print(text, flush=True)

    try:
        writer = subprocess.Popen(
            [str(arguments.python), str(helper), str(arguments.graph)],
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        assert writer.stdout is not None
        assert writer.stderr is not None
        encoder = subprocess.Popen(
            build_encode_command(source, partial, arguments.encoder),
            stdin=writer.stdout,
            stderr=subprocess.PIPE,
        )
        assert encoder.stderr is not None
        writer.stdout.close()
        for stream, label in (
            (writer.stderr, "writer"),
            (encoder.stderr, "encoder"),
        ):
            thread = threading.Thread(
                target=drain_stderr,
                args=(stream, label, messages),
                daemon=True,
            )
            thread.start()
            threads.append(thread)
        render(force=True)
        streams_finished: set[str] = set()
        while len(streams_finished) < 2:
            try:
                label, line = messages.get(timeout=0.1)
            except queue.Empty:
                continue
            if line is None:
                streams_finished.add(label)
                continue
            if label == "writer":
                match = PROGRESS_PATTERN.search(line)
                if match:
                    completed = min(
                        target_frames,
                        int(match.group("frame")),
                    )
                    if progress_is_tty:
                        render()
                elif line:
                    writer_errors.append(line)
            elif line:
                encoder_errors.append(line)
        for thread in threads:
            thread.join()
        if writer.poll() is None:
            writer.wait()
        if encoder.poll() is None:
            encoder.wait()
        writer_return_code = writer.returncode
        encoder_return_code = encoder.returncode
        if encoder_return_code != 0:
            details = "\n".join(encoder_errors[-8:])
            raise RuntimeError(
                "FFmpeg failed while encoding the FPS output"
                + (f":\n{details}" if details else "")
            )
        if writer_return_code != 0:
            details = "\n".join(writer_errors[-8:])
            raise RuntimeError(
                "RIFE/VapourSynth failed while generating frames"
                + (f":\n{details}" if details else "")
            )
        if completed != target_frames:
            completed = target_frames
            render(force=True)
        if progress_is_tty:
            print()
        os.replace(partial, output)
    finally:
        if encoder is not None and encoder.poll() is None:
            encoder.terminate()
            encoder.wait()
        if writer is not None and writer.poll() is None:
            writer.terminate()
            writer.wait()
        for thread in threads:
            thread.join(timeout=1.0)
        partial.unlink(missing_ok=True)


def concat_arguments() -> Namespace:
    return Namespace(
        mode="auto",
        gpu="auto",
        strategy="parallel",
        jobs=0,
        audio_normalization="off",
        performance_mode="off",
        dry_run=False,
        force=True,
    )


def run_pipeline(
    paths: list[Path],
    current_dir: Path,
    arguments: Namespace,
) -> int:
    paths = find_selected_inputs(paths, arguments.output)
    output = arguments.output or default_output(
        paths,
        current_dir,
        arguments.model,
        arguments.target_fps,
    )
    output = output.expanduser().resolve()
    if any(output == path.resolve() for path in paths):
        raise RuntimeError("The FPS output must not overwrite a selected input")

    with performance_scope(arguments.performance_mode, arguments.dry_run):
        if len(paths) == 1:
            source = paths[0]
            print("Single input: skipping concatenation and audio transformation.")
            source_rate, source_frames = probe_video(source)
            target_frames = target_frame_count(
                source_rate, source_frames, arguments.target_fps
            )
            if arguments.dry_run:
                print(f"Input: {source}")
                print(f"Target FPS: {arguments.target_fps} ({target_frames} frames)")
                return 0
            run_interpolation(
                source,
                output,
                arguments.target_fps,
                target_frames,
                arguments,
            )
            print(f"Finished: {output}")
            return 0

        print(f"Multiple inputs: concatenating {len(paths)} files before RIFE.")
        if arguments.dry_run:
            return 0
        with tempfile.TemporaryDirectory(prefix="resolve-fps-") as temporary_directory:
            master = Path(temporary_directory) / "master.mp4"
            concatenate(paths, current_dir, master, concat_arguments())
            source_rate, source_frames = probe_video(master)
            target_frames = target_frame_count(
                source_rate, source_frames, arguments.target_fps
            )
            run_interpolation(
                master,
                output,
                arguments.target_fps,
                target_frames,
                arguments,
            )
        print(f"Finished: {output}")
        return 0


def parse_arguments(argv: list[str] | None = None) -> Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Enhance video to a target FPS; no input opens the video selector TUI."
        )
    )
    parser.add_argument(
        "input_path",
        nargs="?",
        type=Path,
        help="video file or folder; omit to open the selector TUI",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=DEFAULT_TUI_ROOT,
        help=f"TUI starting folder (default: {DEFAULT_TUI_ROOT})",
    )
    parser.add_argument("-o", "--output", type=Path)
    parser.add_argument("--target-fps", type=parse_fraction, default=DEFAULT_TARGET_FPS)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--python", type=Path, default=DEFAULT_FPS_PYTHON)
    parser.add_argument("--site-packages", type=Path, default=DEFAULT_FPS_SITE)
    parser.add_argument("--graph", type=Path, default=DEFAULT_GRAPH)
    parser.add_argument("--trt-cache", type=Path, default=DEFAULT_TRT_CACHE)
    parser.add_argument("--bestsource", type=Path, default=DEFAULT_BESTSOURCE)
    parser.add_argument(
        "--performance-mode",
        choices=("auto", "on", "off"),
        default="auto",
        help="temporarily use the performance profile and restore it afterward",
    )
    parser.add_argument(
        "--encoder",
        choices=("h264_nvenc", "libx264"),
        default="h264_nvenc",
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true")
    return parser.parse_args(argv)


def run_combined_pipeline(
    paths: list[Path],
    current_dir: Path,
    output: Path | None,
    model: str,
    encoder: str,
    performance_mode: str,
    dry_run: bool,
    force: bool,
) -> int:
    arguments = parse_arguments([])
    arguments.output = output
    arguments.model = model
    arguments.encoder = encoder
    arguments.performance_mode = performance_mode
    arguments.dry_run = dry_run
    arguments.force = force
    return run_pipeline(paths, current_dir, arguments)


def main(argv: list[str] | None = None) -> int:
    arguments = parse_arguments(argv)
    requested_output = (
        arguments.output.expanduser().resolve() if arguments.output else None
    )
    arguments.output = requested_output
    if arguments.input_path is None:
        selection = interactive_selection(
            arguments.root.expanduser().resolve(),
            "| RESOLVE FPS // SELECT INPUT VIDEOS",
        )
        if selection is None:
            return 0
        paths, current_dir = selection
    else:
        input_path = arguments.input_path.expanduser().resolve()
        if input_path.is_dir():
            paths = find_inputs(input_path, requested_output)
            current_dir = input_path
        elif input_path.is_file():
            paths = [input_path]
            current_dir = input_path.parent
        else:
            raise RuntimeError(f"Input path does not exist: {input_path}")
    return run_pipeline(paths, current_dir, arguments)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nCancelled.", file=os.sys.stderr)
        raise SystemExit(130)
    except RuntimeError as error:
        print(f"Error: {error}", file=os.sys.stderr)
        raise SystemExit(1)
