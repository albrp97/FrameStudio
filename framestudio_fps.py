#!/usr/bin/env python3
"""Enhance selected video(s) with the preferred RVE path or FFmpeg fallback."""

from __future__ import annotations

import argparse
import json
import os
import queue
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
from argparse import Namespace
from contextlib import contextmanager
from fractions import Fraction
from pathlib import Path
from typing import BinaryIO, Callable, Protocol

from framestudio_concat import (
    DEFAULT_TUI_ROOT,
    PerformanceMode,
    concatenate,
    find_inputs,
    find_selected_inputs,
    interactive_selection,
    rate_label,
)


class _ManagedProcess(Protocol):
    pid: int
    returncode: int | None

    def poll(self) -> int | None: ...

    def terminate(self) -> None: ...

    def kill(self) -> None: ...

    def wait(self, timeout: float | None = None) -> int: ...


PROGRESS_PATTERN = re.compile(
    r"frame=(?P<frame>\d+)/(?P<total>\d+)\s+elapsed=(?P<elapsed>[0-9.]+)s"
)
RVE_PROGRESS_PATTERN = re.compile(r"Current Frame:\s*(?P<frame>\d+)")
RveProgressCallback = Callable[[int, int, float | None], None]
DEFAULT_MODEL = "4.26"
DEFAULT_TARGET_FPS = Fraction(60, 1)
DEFAULT_NVENC_QP = 18
DEFAULT_ENGINE = "rve"
DEFAULT_FALLBACK_ENGINE = "ffmpeg-minterpolate"
PROCESS_TERMINATION_TIMEOUT_SECONDS = 5.0
FRAMESTUDIO_CACHE_ROOT = Path.home() / ".cache" / "framestudio-fps"
LEGACY_CACHE_ROOT = Path.home() / ".cache" / "resolve-fps"


def _preferred_cache_path(*parts: str) -> Path:
    canonical = FRAMESTUDIO_CACHE_ROOT.joinpath(*parts)
    legacy = LEGACY_CACHE_ROOT.joinpath(*parts)
    if not canonical.exists() and legacy.exists():
        return legacy
    return canonical


def _environment_path(name: str, legacy_name: str, *parts: str) -> Path:
    value = os.environ.get(name) or os.environ.get(legacy_name)
    return Path(value) if value else _preferred_cache_path(*parts)


DEFAULT_FPS_PYTHON = _preferred_cache_path("trt", "bin", "python")
DEFAULT_FPS_SITE = _preferred_cache_path("trt", "lib", "python3.13", "site-packages")
DEFAULT_GRAPH = Path(__file__).resolve().parent / "benchmarks" / "fps.vpy"
DEFAULT_TRT_CACHE = _preferred_cache_path("engines-pixel-fallback")
DEFAULT_BESTSOURCE = _preferred_cache_path(
    "plugins",
    "usr",
    "lib",
    "python3.14",
    "site-packages",
    "vapoursynth",
    "plugins",
    "libbestsource.so",
)
DEFAULT_RVE_ROOT = _environment_path(
    "FRAMESTUDIO_RVE_ROOT",
    "RESOLVE_RVE_ROOT",
    "REAL-Video-Enhancer",
)
DEFAULT_RVE_MODEL = _environment_path(
    "FRAMESTUDIO_RVE_MODEL",
    "RESOLVE_RVE_MODEL",
    "rve-models-pixel-fallback",
    "rife4.26.pkl",
)
DEFAULT_RVE_RESTORATION_MODEL = _environment_path(
    "FRAMESTUDIO_RVE_RESTORATION_MODEL",
    "RESOLVE_RVE_RESTORATION_MODEL",
    "rve-benchmark-models",
    "deH264_SuperUltraCompact.safetensors",
)
DEFAULT_RVE_SHIMS = _environment_path(
    "FRAMESTUDIO_RVE_SHIMS",
    "RESOLVE_RVE_SHIMS",
    "rve-shims",
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
                f"ffprobe frame count failed for {path.name}: {counted.stderr.strip()}"
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
        (exact_count.numerator + exact_count.denominator // 2) // exact_count.denominator,
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
        return source.with_name(f"{source.stem}-rife{model}-{label}fps.mp4")
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
        command.extend(["-preset", "p1", "-rc", "constqp", "-qp", str(DEFAULT_NVENC_QP)])
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


def rve_interpolation_factor(
    source_rate: Fraction,
    target_rate: Fraction,
) -> int:
    factor = target_rate / source_rate
    if factor < 1:
        raise RuntimeError("The RVE engine requires a target FPS at least as high as the input FPS")
    rounded = max(1, round(float(factor)))
    if factor == 1:
        return 1
    if rounded >= 2 and abs(float(factor) - rounded) <= 0.01:
        return rounded
    return max(2, (factor.numerator + factor.denominator - 1) // factor.denominator)


def rve_render_rate(
    source_rate: Fraction,
    target_rate: Fraction,
) -> Fraction:
    """Return the integer-rate RVE pass rate used before target-rate normalization."""
    factor = target_rate / source_rate
    integer_factor = rve_interpolation_factor(source_rate, target_rate)
    rounded = round(float(factor))
    if factor == 1 or (
        rounded >= 2 and integer_factor == rounded and abs(float(factor) - rounded) <= 0.01
    ):
        return target_rate
    return source_rate * integer_factor


def rve_base_frame_count(
    source_rate: Fraction,
    source_frames: int,
    target_rate: Fraction,
) -> int:
    return source_frames * rve_interpolation_factor(source_rate, target_rate)


def rve_render_frame_count(
    source_rate: Fraction,
    source_frames: int,
    target_rate: Fraction,
    target_frames: int,
) -> int:
    """Return enough frames for RVE before any target-rate normalization."""
    base_frames = rve_base_frame_count(source_rate, source_frames, target_rate)
    if rve_render_rate(source_rate, target_rate) == target_rate:
        return max(target_frames, base_frames)
    return base_frames


def build_rve_normalization_command(
    source: Path,
    destination: Path,
    target_rate: Fraction,
    target_frames: int,
    encoder: str = "h264_nvenc",
) -> list[str]:
    target_expression = str(target_rate)
    command = [
        require_tool("ffmpeg"),
        "-hide_banner",
        "-y",
        "-nostdin",
        "-loglevel",
        "error",
        "-i",
        str(source),
        "-vf",
        (
            f"fps={target_expression},"
            f"tpad=stop_mode=clone:stop={target_frames},"
            f"setpts=N/({target_expression})/TB"
        ),
        "-frames:v",
        str(target_frames),
    ]
    if encoder == "h264_nvenc":
        command.extend(
            [
                "-c:v",
                encoder,
                "-preset",
                "p1",
                "-rc",
                "constqp",
                "-qp",
                str(DEFAULT_NVENC_QP),
            ]
        )
    else:
        command.extend(["-c:v", encoder, "-preset", "slow", "-crf", "20"])
    command.extend(
        [
            "-profile:v",
            "high",
            "-pix_fmt",
            "yuv420p",
            "-an",
            "-movflags",
            "+faststart",
            "-fps_mode",
            "cfr",
            "-f",
            "mp4",
            str(destination),
        ]
    )
    return command


def build_rve_custom_encoder(
    target_frames: int,
    base_frames: int,
    encoder: str = "h264_nvenc",
) -> str:
    options = ["-c:v", encoder]
    if encoder == "h264_nvenc":
        options.extend(
            [
                "-preset",
                "p1",
                "-rc",
                "constqp",
                "-qp",
                str(DEFAULT_NVENC_QP),
            ]
        )
    else:
        options.extend(["-preset", "slow", "-crf", "20"])
    options.extend(["-profile:v", "high"])
    if target_frames > base_frames:
        options.extend(
            [
                "-vf",
                f"tpad=stop_mode=clone:stop={target_frames - base_frames}",
            ]
        )
    options.extend(
        [
            "-frames:v",
            str(target_frames),
            "-c:a",
            "copy",
            "-c:s",
            "copy",
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
            "-movflags",
            "+faststart",
            "-f",
            "mp4",
        ]
    )
    return " ".join(options)


def validate_rve_checkout(root: Path) -> Path:
    root = root.expanduser().resolve()
    backend = root / "backend" / "rve-backend.py"
    tensor_rt_handler = root / "backend" / "src" / "pytorch" / "TensorRTHandler.py"
    ffmpeg_buffers = root / "backend" / "src" / "FFmpegBuffers.py"
    for path in (backend, tensor_rt_handler, ffmpeg_buffers):
        if not path.is_file():
            raise RuntimeError(f"RVE checkout is missing required file: {path}")
    try:
        tensor_rt_text = tensor_rt_handler.read_text(encoding="utf-8")
        ffmpeg_text = ffmpeg_buffers.read_text(encoding="utf-8")
    except OSError as error:
        raise RuntimeError(f"Could not inspect the RVE checkout: {root}") from error
    if "RVE_TRT_TORCH_PIXEL" not in tensor_rt_text:
        raise RuntimeError(
            "RVE checkout lacks the validated PixelShuffle TensorRT fallback; "
            "use the corrected checkout"
        )
    if "RVE_OUTPUT_FPS" not in ffmpeg_text:
        raise RuntimeError(
            "RVE checkout lacks exact output-FPS support; use the corrected checkout"
        )
    render_video = root / "backend" / "src" / "RenderVideo.py"
    try:
        render_text = render_video.read_text(encoding="utf-8")
    except OSError as error:
        raise RuntimeError(f"Could not inspect the RVE checkout: {root}") from error
    if "RVE_RGB_INPUT" not in ffmpeg_text:
        raise RuntimeError(
            "RVE checkout lacks the validated RGB input path; use the corrected checkout"
        )
    if "RVE_EXACT_FRAME_COUNT" not in render_text:
        raise RuntimeError(
            "RVE checkout lacks exact frame-count padding; use the corrected checkout"
        )
    return backend


def rve_runtime_unavailable_reason(
    arguments: Namespace,
    *,
    announce: bool = True,
) -> str | None:
    environment = rve_environment(arguments, Fraction(1, 1))
    check_script = (
        "import sys\n"
        "import torch\n"
        "import torch_tensorrt\n"
        "import tensorrt\n"
        "if not torch.cuda.is_available():\n"
        "    raise RuntimeError('torch.cuda.is_available() returned false')\n"
        "device = torch.cuda.get_device_name(0)\n"
        "capability = torch.cuda.get_device_capability(0)\n"
        "probe = torch.ones((1,), device='cuda')\n"
        "torch.cuda.synchronize()\n"
        "if probe.item() != 1.0:\n"
        "    raise RuntimeError('CUDA probe returned an invalid value')\n"
        "torch.load(sys.argv[1], map_location='cpu', weights_only=True, mmap=True)\n"
        "print(f'CUDA device={device}; capability={capability[0]}.{capability[1]}; '\n"
        "      f'torch={torch.__version__}; '\n"
        "      f'torch_tensorrt={torch_tensorrt.__version__}; '\n"
        "      f'tensorrt={tensorrt.__version__}; model=loaded')\n"
    )
    result = subprocess.run(
        [
            str(arguments.python),
            "-c",
            check_script,
            str(arguments.rve_model.expanduser().resolve()),
        ],
        capture_output=True,
        text=True,
        env=environment,
        check=False,
    )
    if result.returncode != 0:
        details = result.stderr.strip() or result.stdout.strip()
        return "RVE CUDA/TensorRT preflight failed" + (f": {details}" if details else "")
    if announce:
        print(f"RVE CUDA/TensorRT preflight: {result.stdout.strip()}")
    return None


def rve_library_paths(arguments: Namespace) -> list[str]:
    candidates = (
        arguments.site_packages / "nvidia" / "cu13" / "lib",
        arguments.site_packages / "tensorrt_libs",
        arguments.site_packages / "nvidia" / "cuda_runtime" / "lib",
    )
    return [str(path) for path in candidates if path.is_dir()]


def rve_unavailable_reason(
    arguments: Namespace,
    *,
    announce: bool = True,
) -> str | None:
    if not arguments.python.is_file():
        return f"RVE Python environment was not found: {arguments.python}"
    if not arguments.site_packages.is_dir():
        return f"FPS site-packages directory was not found: {arguments.site_packages}"
    if not arguments.rve_model.is_file():
        return f"RIFE 4.26 model was not found: {arguments.rve_model}"
    try:
        validate_rve_checkout(arguments.rve_root)
    except (OSError, RuntimeError) as error:
        return str(error)
    return rve_runtime_unavailable_reason(arguments, announce=announce)


def rve_environment(arguments: Namespace, target_rate: Fraction) -> dict[str, str]:
    environment = os.environ.copy()
    python_paths = [
        str(arguments.rve_root / "backend"),
        str(arguments.rve_root),
        str(arguments.site_packages),
    ]
    if arguments.rve_shims.is_dir():
        python_paths.insert(0, str(arguments.rve_shims))
    existing_python_path = environment.get("PYTHONPATH")
    if existing_python_path:
        python_paths.append(existing_python_path)
    existing_library_path = environment.get("LD_LIBRARY_PATH")
    library_paths = rve_library_paths(arguments)
    if existing_library_path:
        library_paths.extend(
            path
            for path in existing_library_path.split(os.pathsep)
            if path and path not in library_paths
        )
    environment.update(
        {
            "RVE_TRT_TORCH_PIXEL": "1",
            "RVE_RGB_INPUT": "1",
            "RVE_EXACT_FRAME_COUNT": "1",
            "RVE_OUTPUT_FPS": str(float(target_rate)),
            "PYTHONPATH": os.pathsep.join(python_paths),
        }
    )
    if library_paths:
        environment["LD_LIBRARY_PATH"] = os.pathsep.join(library_paths)
    return environment


def build_rve_command(
    source: Path,
    partial: Path,
    source_rate: Fraction,
    source_frames: int,
    target_rate: Fraction,
    target_frames: int,
    cwd: Path,
    arguments: Namespace,
) -> list[str]:
    backend = validate_rve_checkout(arguments.rve_root)
    factor = rve_interpolation_factor(source_rate, target_rate)
    base_frames = source_frames * factor
    render_frames = rve_render_frame_count(
        source_rate,
        source_frames,
        target_rate,
        target_frames,
    )
    custom_encoder = build_rve_custom_encoder(
        render_frames,
        base_frames,
        arguments.encoder,
    )
    return [
        str(arguments.python),
        str(backend),
        "-i",
        str(source),
        "-o",
        str(partial),
        "--ffmpeg_path",
        require_tool("ffmpeg"),
        "--interpolate_model",
        str(arguments.rve_model.expanduser().resolve()),
        "--interpolate_factor",
        str(factor),
        "--backend",
        "tensorrt",
        "--device",
        "cuda",
        "--pytorch_gpu_id",
        "0",
        "--precision",
        "float16",
        "--tensorrt_opt_profile",
        "3",
        "--scene_detect_method",
        "pyscenedetect",
        "--scene_detect_threshold",
        "4.0",
        "--custom_encoder",
        custom_encoder,
        "--audio_encoder_preset",
        "copy_audio",
        "--subtitle_encoder_preset",
        "copy_subtitle",
        "--video_pixel_format",
        "yuv420p",
        "--overwrite",
        "--cwd",
        str(cwd),
    ]


def build_rve_restoration_command(
    source: Path,
    partial: Path,
    source_frames: int,
    cwd: Path,
    arguments: Namespace,
    restoration_model: Path,
) -> list[str]:
    backend = validate_rve_checkout(arguments.rve_root)
    if isinstance(source_frames, bool) or not isinstance(source_frames, int) or source_frames <= 0:
        raise RuntimeError("RVE restoration source frame count must be positive")
    model = restoration_model.expanduser().resolve()
    if not model.is_file():
        raise RuntimeError(f"RVE restoration model was not found: {model}")
    custom_encoder = build_rve_custom_encoder(
        source_frames,
        source_frames,
        arguments.encoder,
    )
    return [
        str(arguments.python),
        str(backend),
        "-i",
        str(source),
        "-o",
        str(partial),
        "--ffmpeg_path",
        require_tool("ffmpeg"),
        "--extra_restoration_models",
        str(model),
        "--backend",
        "tensorrt",
        "--device",
        "cuda",
        "--pytorch_gpu_id",
        "0",
        "--precision",
        "float16",
        "--tensorrt_opt_profile",
        "3",
        "--scene_detect_method",
        "none",
        "--custom_encoder",
        custom_encoder,
        "--audio_encoder_preset",
        "copy_audio",
        "--subtitle_encoder_preset",
        "copy_subtitle",
        "--video_pixel_format",
        "yuv420p",
        "--overwrite",
        "--cwd",
        str(cwd),
    ]


def remux_rve_audio(
    source: Path,
    video: Path,
    output: Path,
    *,
    cancel_event: threading.Event | None = None,
) -> None:
    if cancel_event is not None and cancel_event.is_set():
        raise RuntimeError("Export cancelled")
    command = [
        require_tool("ffmpeg"),
        "-hide_banner",
        "-y",
        "-nostdin",
        "-loglevel",
        "error",
        "-i",
        str(video),
        "-i",
        str(source),
        "-map",
        "0:v:0",
        "-map",
        "1:a:0?",
        "-c:v",
        "copy",
        "-c:a",
        "copy",
        "-movflags",
        "+faststart",
        "-f",
        "mp4",
        str(output),
    ]
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )
    try:
        if cancel_event is None:
            _, stderr = process.communicate()
        else:
            while True:
                if cancel_event.is_set():
                    _terminate_process_group(process, "FFmpeg audio remux")
                    raise RuntimeError("Export cancelled")
                try:
                    process.wait(timeout=0.1)
                    break
                except subprocess.TimeoutExpired:
                    continue
            stderr = process.stderr.read() if process.stderr is not None else ""
    except KeyboardInterrupt:
        _terminate_process_group(process, "FFmpeg audio remux")
        raise
    result = subprocess.CompletedProcess(command, process.returncode, None, stderr)
    if result.returncode != 0:
        raise RuntimeError(
            "FFmpeg failed while restoring the source audio stream"
            + (f":\n{result.stderr.strip()}" if result.stderr.strip() else "")
        )


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


def drain_rve_output(
    stream: BinaryIO,
    messages: queue.Queue[tuple[str, str | None]],
) -> None:
    pending = ""
    while True:
        chunk = os.read(stream.fileno(), 4096)
        if not chunk:
            break
        pending += chunk.decode(errors="replace")
        lines = re.split(r"[\r\n]", pending)
        pending = lines.pop()
        for line in lines:
            if line:
                messages.put(("rve", line))
    if pending:
        messages.put(("rve", pending))
    stream.close()
    messages.put(("rve", None))


def _terminate_process(process: _ManagedProcess, label: str) -> None:
    if process.poll() is not None:
        return
    try:
        process.terminate()
    except ProcessLookupError:
        return
    try:
        process.wait(timeout=PROCESS_TERMINATION_TIMEOUT_SECONDS)
        return
    except subprocess.TimeoutExpired:
        pass
    try:
        process.kill()
    except ProcessLookupError:
        return
    try:
        process.wait(timeout=PROCESS_TERMINATION_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired as error:
        raise RuntimeError(f"{label} did not terminate after cancellation") from error


def _terminate_process_group(
    process: _ManagedProcess,
    label: str,
) -> None:
    if process.poll() is not None:
        return
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        process.wait(timeout=PROCESS_TERMINATION_TIMEOUT_SECONDS)
        return
    except subprocess.TimeoutExpired:
        pass
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        return
    try:
        process.wait(timeout=PROCESS_TERMINATION_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired as error:
        raise RuntimeError(f"{label} did not terminate after cancellation") from error


def _wait_for_process(
    process: _ManagedProcess,
    label: str,
    *,
    cancel_event: threading.Event | None = None,
) -> int:
    while process.poll() is None:
        try:
            process.wait(timeout=0.1)
        except subprocess.TimeoutExpired:
            if cancel_event is not None and cancel_event.is_set():
                _terminate_process(process, label)
                raise RuntimeError("Export cancelled") from None
    return_code = process.returncode
    if return_code is None:
        raise RuntimeError(f"{label} did not report an exit code")
    return return_code


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
                print(f"Performance mode: unchanged ({performance.previous or 'unavailable'}).")
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
    *,
    cancel_event: threading.Event | None = None,
) -> None:
    if cancel_event is not None and cancel_event.is_set():
        raise RuntimeError("Export cancelled")
    if output.resolve() == source.resolve():
        raise RuntimeError("The FPS output must be different from the input")
    if output.exists() and not arguments.force:
        raise RuntimeError(f"Output already exists; use --force to replace it: {output}")
    if not arguments.python.is_file():
        raise RuntimeError(f"FPS Python environment was not found: {arguments.python}")
    if not arguments.graph.is_file():
        raise RuntimeError(f"VapourSynth graph was not found: {arguments.graph}")
    if not arguments.site_packages.is_dir():
        raise RuntimeError(f"FPS site-packages directory was not found: {arguments.site_packages}")
    if not arguments.trt_cache.is_dir():
        raise RuntimeError(f"TensorRT cache was not found: {arguments.trt_cache}")
    if not arguments.bestsource.is_file():
        raise RuntimeError(f"BestSource plugin was not found: {arguments.bestsource}")

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
            start_new_session=True,
        )
        assert writer.stdout is not None
        assert writer.stderr is not None
        encoder = subprocess.Popen(
            build_encode_command(source, partial, arguments.encoder),
            stdin=writer.stdout,
            stderr=subprocess.PIPE,
            start_new_session=True,
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
            if cancel_event is not None and cancel_event.is_set():
                for running_process in (encoder, writer):
                    if running_process is not None and running_process.poll() is None:
                        _terminate_process(running_process, "FPS interpolation")
                raise RuntimeError("Export cancelled")
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
        writer_return_code = _wait_for_process(
            writer,
            "VapourSynth writer",
            cancel_event=cancel_event,
        )
        encoder_return_code = _wait_for_process(
            encoder,
            "FPS encoder",
            cancel_event=cancel_event,
        )
        if encoder_return_code != 0:
            details = "\n".join(encoder_errors[-8:])
            raise RuntimeError(
                "FFmpeg failed while encoding the FPS output" + (f":\n{details}" if details else "")
            )
        if writer_return_code != 0:
            details = "\n".join(writer_errors[-8:])
            raise RuntimeError(
                "RIFE/VapourSynth failed while generating frames"
                + (f":\n{details}" if details else "")
            )
        if cancel_event is not None and cancel_event.is_set():
            raise RuntimeError("Export cancelled")
        if completed != target_frames:
            completed = target_frames
            render(force=True)
        if progress_is_tty:
            print()
        os.replace(partial, output)
    finally:
        if encoder is not None and encoder.poll() is None:
            _terminate_process(encoder, "FPS encoder")
        if writer is not None and writer.poll() is None:
            _terminate_process(writer, "VapourSynth writer")
        for thread in threads:
            thread.join(timeout=1.0)
        partial.unlink(missing_ok=True)


def run_ffmpeg_interpolation(
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
    from framestudio.export_process import run_ffmpeg
    from framestudio.export_types import ExportProgress
    from framestudio.interpolation import build_ffmpeg_interpolation_command

    partial = output.with_name(f".{output.name}.partial")
    output.parent.mkdir(parents=True, exist_ok=True)
    partial.unlink(missing_ok=True)
    command = build_ffmpeg_interpolation_command(
        source,
        partial,
        target_rate,
        target_frames,
        ffmpeg_path=require_tool("ffmpeg"),
    )
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

    def report(progress: ExportProgress) -> None:
        nonlocal completed
        completed = min(target_frames, progress.frame)
        if progress_is_tty:
            render()

    try:
        render(force=True)
        duration_seconds = target_frames / float(target_rate)
        run_ffmpeg(
            command,
            progress_callback=report,
            stage="interpolation",
            command_duration_seconds=duration_seconds,
            progress_total_duration_seconds=duration_seconds,
            command_total_frames=target_frames,
            progress_total_frames=target_frames,
            started=started,
        )
        if not partial.is_file():
            raise RuntimeError("FFmpeg minterpolate fallback did not produce an output file")
        if completed != target_frames:
            completed = target_frames
            render(force=True)
        if progress_is_tty:
            print()
        os.replace(partial, output)
    finally:
        partial.unlink(missing_ok=True)


def run_interpolation_rve(
    source: Path,
    output: Path,
    source_rate: Fraction,
    source_frames: int,
    target_rate: Fraction,
    target_frames: int,
    arguments: Namespace,
    *,
    cancel_event: threading.Event | None = None,
    progress_callback: RveProgressCallback | None = None,
) -> None:
    if cancel_event is not None and cancel_event.is_set():
        raise RuntimeError("Export cancelled")
    if output.resolve() == source.resolve():
        raise RuntimeError("The FPS output must be different from the input")
    if output.exists() and not arguments.force:
        raise RuntimeError(f"Output already exists; use --force to replace it: {output}")
    if not arguments.python.is_file():
        raise RuntimeError(f"RVE Python environment was not found: {arguments.python}")
    if not arguments.site_packages.is_dir():
        raise RuntimeError(f"FPS site-packages directory was not found: {arguments.site_packages}")
    if not arguments.rve_model.is_file():
        raise RuntimeError(f"RIFE 4.26 model was not found: {arguments.rve_model}")
    validate_rve_checkout(arguments.rve_root)
    render_rate = rve_render_rate(source_rate, target_rate)
    render_frames = rve_render_frame_count(
        source_rate,
        source_frames,
        target_rate,
        target_frames,
    )

    partial = output.with_name(f".{output.name}.partial")
    output.parent.mkdir(parents=True, exist_ok=True)
    partial.unlink(missing_ok=True)
    messages: queue.Queue[tuple[str, str | None]] = queue.Queue()
    thread: threading.Thread | None = None
    process: subprocess.Popen[bytes] | None = None
    output_lines: list[str] = []
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

    def stop_process() -> None:
        if process is not None:
            _terminate_process_group(process, "REAL-Video-Enhancer")

    def report_progress() -> None:
        if progress_callback is None:
            return
        elapsed = max(0.0, time.monotonic() - started)
        fps = completed / elapsed if elapsed > 0.0 else None
        progress_callback(completed, target_frames, fps)

    try:
        with tempfile.TemporaryDirectory(
            prefix="framestudio-rve-",
            dir=output.parent,
        ) as temporary_directory:
            cwd = Path(temporary_directory)
            rve_video = cwd / "rve-video.mp4"
            command = build_rve_command(
                source,
                rve_video,
                source_rate,
                source_frames,
                target_rate,
                target_frames,
                cwd,
                arguments,
            )
            environment = rve_environment(arguments, render_rate)
            process = subprocess.Popen(
                command,
                env=environment,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
            assert process.stdout is not None
            thread = threading.Thread(
                target=drain_rve_output,
                args=(process.stdout, messages),
                daemon=True,
            )
            thread.start()
            render(force=True)
            stream_finished = False
            while not stream_finished:
                if cancel_event is not None and cancel_event.is_set():
                    stop_process()
                    raise RuntimeError("Export cancelled")
                try:
                    label, line = messages.get(timeout=0.1)
                except queue.Empty:
                    continue
                if line is None:
                    stream_finished = True
                    continue
                output_lines.append(line)
                match = RVE_PROGRESS_PATTERN.search(line)
                if match:
                    render_completed = min(render_frames, int(match.group("frame")))
                    completed = min(
                        target_frames,
                        round(render_completed * target_frames / render_frames),
                    )
                    report_progress()
                    if progress_is_tty:
                        render()
            thread.join()
            return_code = _wait_for_process(
                process,
                "REAL-Video-Enhancer",
                cancel_event=cancel_event,
            )
            if cancel_event is not None and cancel_event.is_set():
                raise RuntimeError("Export cancelled")
            if return_code != 0:
                details = "\n".join(output_lines[-12:])
                raise RuntimeError(
                    "REAL-Video-Enhancer failed" + (f":\n{details}" if details else "")
                )
            if not rve_video.is_file():
                raise RuntimeError("REAL-Video-Enhancer did not produce an output file")
            actual_rate, actual_frames = probe_video(rve_video)
            if actual_rate != render_rate or actual_frames != render_frames:
                raise RuntimeError(
                    "REAL-Video-Enhancer produced invalid output timing: "
                    f"{actual_rate} FPS, {actual_frames} frames; expected "
                    f"{render_rate} FPS, {render_frames} frames"
                )
            video_for_remux = rve_video
            if render_rate != target_rate or render_frames != target_frames:
                from framestudio.export_process import run_ffmpeg
                from framestudio.export_types import ExportExecutionError, ExportProgress

                normalized_video = cwd / "normalized-video.mp4"

                def report_normalization_progress(progress: ExportProgress) -> None:
                    if progress_callback is not None:
                        progress_callback(
                            progress.frame,
                            progress.total_frames,
                            progress.fps,
                        )

                try:
                    run_ffmpeg(
                        build_rve_normalization_command(
                            rve_video,
                            normalized_video,
                            target_rate,
                            target_frames,
                            arguments.encoder,
                        ),
                        progress_callback=(
                            report_normalization_progress if progress_callback is not None else None
                        ),
                        command_duration_seconds=target_frames / float(target_rate),
                        progress_total_duration_seconds=target_frames / float(target_rate),
                        command_total_frames=target_frames,
                        progress_total_frames=target_frames,
                        started=started,
                        cancel_event=cancel_event,
                    )
                except ExportExecutionError as error:
                    raise RuntimeError(
                        f"FFmpeg failed to normalize fractional RVE output: {error}"
                    ) from error
                video_for_remux = normalized_video
            remux_rve_audio(
                source,
                video_for_remux,
                partial,
                cancel_event=cancel_event,
            )
            final_rate, final_frames = probe_video(partial)
            if final_rate != target_rate or final_frames != target_frames:
                raise RuntimeError(
                    "The final RVE remux changed output timing: "
                    f"{final_rate} FPS, {final_frames} frames; expected "
                    f"{target_rate} FPS, {target_frames} frames"
                )
            if cancel_event is not None and cancel_event.is_set():
                raise RuntimeError("Export cancelled")
            if completed != target_frames:
                completed = target_frames
                report_progress()
                render(force=True)
            if progress_is_tty:
                print()
            os.replace(partial, output)
    finally:
        stop_process()
        if thread is not None:
            thread.join(timeout=1.0)
        partial.unlink(missing_ok=True)


def run_restoration_rve(
    source: Path,
    output: Path,
    source_rate: Fraction,
    source_frames: int,
    arguments: Namespace,
    *,
    restoration_model: Path | None = None,
    cancel_event: threading.Event | None = None,
) -> None:
    if cancel_event is not None and cancel_event.is_set():
        raise RuntimeError("Export cancelled")
    if output.resolve() == source.resolve():
        raise RuntimeError("The restoration output must be different from the input")
    if output.exists() and not arguments.force:
        raise RuntimeError(f"Output already exists; use --force to replace it: {output}")
    if not arguments.python.is_file():
        raise RuntimeError(f"RVE Python environment was not found: {arguments.python}")
    if not arguments.site_packages.is_dir():
        raise RuntimeError(f"FPS site-packages directory was not found: {arguments.site_packages}")
    model_value: object = restoration_model
    if model_value is None:
        model_value = getattr(
            arguments,
            "restoration_model",
            DEFAULT_RVE_RESTORATION_MODEL,
        )
    if not isinstance(model_value, (str, Path)):
        raise RuntimeError("RVE restoration model path is invalid")
    model = Path(model_value).expanduser().resolve()
    if not model.is_file():
        raise RuntimeError(f"RVE restoration model was not found: {model}")
    validate_rve_checkout(arguments.rve_root)

    partial = output.with_name(f".{output.name}.partial")
    output.parent.mkdir(parents=True, exist_ok=True)
    partial.unlink(missing_ok=True)
    messages: queue.Queue[tuple[str, str | None]] = queue.Queue()
    thread: threading.Thread | None = None
    process: subprocess.Popen[bytes] | None = None
    output_lines: list[str] = []
    completed = 0
    started = time.monotonic()
    progress_is_tty = os.isatty(1)

    def render(force: bool = False) -> None:
        if not progress_is_tty and not force:
            return
        text = progress_line(completed, source_frames, started)
        if progress_is_tty:
            print(f"\r{text}", end="", flush=True)
        elif force:
            print(text, flush=True)

    def stop_process() -> None:
        if process is not None:
            _terminate_process_group(process, "REAL-Video-Enhancer restoration")

    try:
        with tempfile.TemporaryDirectory(
            prefix="framestudio-rve-restoration-",
            dir=output.parent,
        ) as temporary_directory:
            cwd = Path(temporary_directory)
            rve_video = cwd / "rve-video.mp4"
            command = build_rve_restoration_command(
                source,
                rve_video,
                source_frames,
                cwd,
                arguments,
                model,
            )
            environment = rve_environment(arguments, source_rate)
            process = subprocess.Popen(
                command,
                env=environment,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
            assert process.stdout is not None
            thread = threading.Thread(
                target=drain_rve_output,
                args=(process.stdout, messages),
                daemon=True,
            )
            thread.start()
            render(force=True)
            stream_finished = False
            while not stream_finished:
                if cancel_event is not None and cancel_event.is_set():
                    stop_process()
                    raise RuntimeError("Export cancelled")
                try:
                    label, line = messages.get(timeout=0.1)
                except queue.Empty:
                    continue
                if line is None:
                    stream_finished = True
                    continue
                output_lines.append(line)
                match = RVE_PROGRESS_PATTERN.search(line)
                if match:
                    completed = min(source_frames, int(match.group("frame")))
                    if progress_is_tty:
                        render()
            thread.join()
            return_code = _wait_for_process(
                process,
                "REAL-Video-Enhancer restoration",
                cancel_event=cancel_event,
            )
            if cancel_event is not None and cancel_event.is_set():
                raise RuntimeError("Export cancelled")
            if return_code != 0:
                details = "\n".join(output_lines[-12:])
                raise RuntimeError(
                    "REAL-Video-Enhancer restoration failed" + (f":\n{details}" if details else "")
                )
            if not rve_video.is_file():
                raise RuntimeError("REAL-Video-Enhancer restoration did not produce an output file")
            actual_rate, actual_frames = probe_video(rve_video)
            if actual_rate != source_rate or actual_frames != source_frames:
                raise RuntimeError(
                    "REAL-Video-Enhancer restoration produced invalid output timing: "
                    f"{actual_rate} FPS, {actual_frames} frames; expected "
                    f"{source_rate} FPS, {source_frames} frames"
                )
            remux_rve_audio(
                source,
                rve_video,
                partial,
                cancel_event=cancel_event,
            )
            final_rate, final_frames = probe_video(partial)
            if final_rate != source_rate or final_frames != source_frames:
                raise RuntimeError(
                    "The final RVE restoration remux changed output timing: "
                    f"{final_rate} FPS, {final_frames} frames; expected "
                    f"{source_rate} FPS, {source_frames} frames"
                )
            if cancel_event is not None and cancel_event.is_set():
                raise RuntimeError("Export cancelled")
            if completed != source_frames:
                completed = source_frames
                render(force=True)
            if progress_is_tty:
                print()
            os.replace(partial, output)
    finally:
        stop_process()
        if thread is not None:
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


def select_engine(arguments: Namespace) -> str:
    engine: object = arguments.engine
    if not isinstance(engine, str):
        raise RuntimeError("FPS engine must be a string")
    if engine != DEFAULT_ENGINE:
        return engine
    reason = rve_unavailable_reason(arguments)
    if reason is None:
        return DEFAULT_ENGINE
    try:
        require_tool("ffmpeg")
    except RuntimeError as error:
        raise RuntimeError(
            f"{reason}; {DEFAULT_FALLBACK_ENGINE} is unavailable: {error}"
        ) from error
    print(f"RVE backend unavailable: {reason}")
    print("Using FFmpeg minterpolate fallback.")
    return DEFAULT_FALLBACK_ENGINE


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
            target_frames = target_frame_count(source_rate, source_frames, arguments.target_fps)
            if arguments.dry_run:
                print(f"Input: {source}")
                print(f"Target FPS: {arguments.target_fps} ({target_frames} frames)")
                return 0
            engine = select_engine(arguments)
            if engine == "rve":
                run_interpolation_rve(
                    source,
                    output,
                    source_rate,
                    source_frames,
                    arguments.target_fps,
                    target_frames,
                    arguments,
                )
            elif engine == DEFAULT_FALLBACK_ENGINE:
                run_ffmpeg_interpolation(
                    source,
                    output,
                    arguments.target_fps,
                    target_frames,
                    arguments,
                )
            else:
                run_interpolation(
                    source,
                    output,
                    arguments.target_fps,
                    target_frames,
                    arguments,
                )
            print(f"Finished: {output}")
            return 0

        print(f"Multiple inputs: concatenating {len(paths)} files before FPS enhancement.")
        if arguments.dry_run:
            return 0
        with tempfile.TemporaryDirectory(prefix="framestudio-fps-") as temporary_directory:
            master = Path(temporary_directory) / "master.mp4"
            concatenate(paths, current_dir, master, concat_arguments())
            source_rate, source_frames = probe_video(master)
            target_frames = target_frame_count(source_rate, source_frames, arguments.target_fps)
            engine = select_engine(arguments)
            if engine == "rve":
                run_interpolation_rve(
                    master,
                    output,
                    source_rate,
                    source_frames,
                    arguments.target_fps,
                    target_frames,
                    arguments,
                )
            elif engine == DEFAULT_FALLBACK_ENGINE:
                run_ffmpeg_interpolation(
                    master,
                    output,
                    arguments.target_fps,
                    target_frames,
                    arguments,
                )
            else:
                run_interpolation(
                    master,
                    output,
                    arguments.target_fps,
                    target_frames,
                    arguments,
                )
        print(f"Finished: {output}")
        return 0


def parse_arguments(
    argv: list[str] | None = None,
    *,
    prog: str | None = None,
) -> Namespace:
    parser = argparse.ArgumentParser(
        prog=prog,
        description=("Enhance video to a target FPS; no input opens the video selector TUI.")
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
    parser.add_argument(
        "--engine",
        choices=("rve", "vs-rife", DEFAULT_FALLBACK_ENGINE),
        default=DEFAULT_ENGINE,
        help=(
            "FPS backend (default: rve; missing RVE uses the FFmpeg fallback; "
            "vs-rife remains available)"
        ),
    )
    parser.add_argument("--python", type=Path, default=DEFAULT_FPS_PYTHON)
    parser.add_argument("--site-packages", type=Path, default=DEFAULT_FPS_SITE)
    parser.add_argument("--graph", type=Path, default=DEFAULT_GRAPH)
    parser.add_argument("--trt-cache", type=Path, default=DEFAULT_TRT_CACHE)
    parser.add_argument("--bestsource", type=Path, default=DEFAULT_BESTSOURCE)
    parser.add_argument("--rve-root", type=Path, default=DEFAULT_RVE_ROOT)
    parser.add_argument("--rve-model", type=Path, default=DEFAULT_RVE_MODEL)
    parser.add_argument("--rve-shims", type=Path, default=DEFAULT_RVE_SHIMS)
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
    engine: str = DEFAULT_ENGINE,
    rve_root: Path = DEFAULT_RVE_ROOT,
    rve_model: Path = DEFAULT_RVE_MODEL,
    rve_shims: Path = DEFAULT_RVE_SHIMS,
) -> int:
    arguments = parse_arguments([])
    arguments.output = output
    arguments.model = model
    arguments.encoder = encoder
    arguments.performance_mode = performance_mode
    arguments.dry_run = dry_run
    arguments.force = force
    arguments.engine = engine
    arguments.rve_root = rve_root
    arguments.rve_model = rve_model
    arguments.rve_shims = rve_shims
    return run_pipeline(paths, current_dir, arguments)


def main(argv: list[str] | None = None, *, prog: str | None = None) -> int:
    arguments = parse_arguments(argv, prog=prog)
    requested_output = arguments.output.expanduser().resolve() if arguments.output else None
    arguments.output = requested_output
    if arguments.input_path is None:
        selection = interactive_selection(
            arguments.root.expanduser().resolve(),
            "| FRAMESTUDIO FPS // SELECT INPUT VIDEOS",
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
        print("\nCancelled.", file=sys.stderr)
        raise SystemExit(130)
    except RuntimeError as error:
        print(f"Error: {error}", file=sys.stderr)
        raise SystemExit(1)
