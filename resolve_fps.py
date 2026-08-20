#!/usr/bin/env python3
"""Enhance selected video(s) to a target frame rate with the validated RIFE path."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import tempfile
from argparse import Namespace
from fractions import Fraction
from pathlib import Path

from resolve_concat import (
    DEFAULT_TUI_ROOT,
    concatenate,
    find_inputs,
    find_selected_inputs,
    interactive_selection,
    rate_label,
)


DEFAULT_MODEL = "4.26"
DEFAULT_TARGET_FPS = Fraction(60, 1)
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
        command.extend(["-preset", "p1", "-rc", "constqp", "-qp", "1"])
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
    try:
        writer = subprocess.Popen(
            [str(arguments.python), str(helper), str(arguments.graph)],
            env=environment,
            stdout=subprocess.PIPE,
        )
        assert writer.stdout is not None
        encoder = subprocess.Popen(
            build_encode_command(source, partial, arguments.encoder),
            stdin=writer.stdout,
        )
        writer.stdout.close()
        encoder_return_code = encoder.wait()
        writer_return_code = writer.wait()
        if encoder_return_code != 0:
            raise RuntimeError("FFmpeg failed while encoding the FPS output")
        if writer_return_code != 0:
            raise RuntimeError("RIFE/VapourSynth failed while generating frames")
        os.replace(partial, output)
    finally:
        if encoder is not None and encoder.poll() is None:
            encoder.terminate()
            encoder.wait()
        if writer is not None and writer.poll() is None:
            writer.terminate()
            writer.wait()
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

    if len(paths) == 1:
        source = paths[0]
        print("Single input: skipping concatenation and audio transformation.")
        if arguments.dry_run:
            source_rate, source_frames = probe_video(source)
            target_frames = target_frame_count(
                source_rate, source_frames, arguments.target_fps
            )
            print(f"Input: {source}")
            print(f"Target FPS: {arguments.target_fps} ({target_frames} frames)")
            return 0
        source_rate, source_frames = probe_video(source)
        target_frames = target_frame_count(
            source_rate, source_frames, arguments.target_fps
        )
        run_interpolation(source, output, arguments.target_fps, target_frames, arguments)
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
        run_interpolation(master, output, arguments.target_fps, target_frames, arguments)
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
        "--encoder",
        choices=("h264_nvenc", "libx264"),
        default="h264_nvenc",
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true")
    return parser.parse_args(argv)


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
