from __future__ import annotations

import json
import math
import os
import subprocess
import tempfile
import time
import uuid
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .media import MediaProbe, MediaProbeError, probe_media
from .model import Segment, SegmentTimeline

_BOUNDARY_TOLERANCE = 1e-3
_DURATION_TOLERANCE = 0.05
_FAST_CONTAINERS = {"matroska", "mkv", "mov", "mp4"}
_FAST_VIDEO_CODECS = {"h264"}
_FAST_AUDIO_CODECS = {"aac"}


class ExportPlanningError(RuntimeError):
    """Raised when an export plan cannot be safely determined."""


class ExportExecutionError(RuntimeError):
    """Raised when an export cannot be completed and verified safely."""


@dataclass(frozen=True)
class FfmpegProgress:
    frame: int
    fps: float | None
    out_time_seconds: float
    speed: str | None
    done: bool


@dataclass(frozen=True)
class ExportProgress:
    stage: str
    percent: float
    frame: int
    total_frames: int
    fps: float | None
    elapsed_seconds: float
    eta_seconds: float | None


ExportProgressCallback = Callable[[ExportProgress], None]


def _progress_float(value: str | None) -> float | None:
    if value is None:
        return None
    try:
        parsed = float(value)
    except ValueError:
        return None
    return parsed if math.isfinite(parsed) else None


def _progress_int(value: str | None) -> int:
    if value is None:
        return 0
    try:
        parsed = int(value)
    except ValueError:
        return 0
    return max(0, parsed)


def _progress_clock(value: str | None) -> float:
    if value is None:
        return 0.0
    parts = value.split(":")
    if len(parts) != 3:
        return 0.0
    try:
        hours, minutes, seconds = (float(part) for part in parts)
    except ValueError:
        return 0.0
    result = hours * 3600.0 + minutes * 60.0 + seconds
    return result if math.isfinite(result) and result >= 0 else 0.0


def parse_ffmpeg_progress_values(
    values: Mapping[str, str],
) -> FfmpegProgress:
    out_time_us = _progress_float(values.get("out_time_us"))
    if out_time_us is not None and out_time_us >= 0:
        out_time_seconds = out_time_us / 1_000_000.0
    else:
        out_time_ms = _progress_float(values.get("out_time_ms"))
        if out_time_ms is not None and out_time_ms >= 0:
            out_time_seconds = out_time_ms / 1_000_000.0
        else:
            out_time_seconds = _progress_clock(values.get("out_time"))
    fps = _progress_float(values.get("fps"))
    return FfmpegProgress(
        frame=_progress_int(values.get("frame")),
        fps=fps if fps is None or fps >= 0 else None,
        out_time_seconds=out_time_seconds,
        speed=values.get("speed") or None,
        done=values.get("progress") == "end",
    )


@dataclass(frozen=True)
class ExportPlan:
    route: str
    source: Path
    destination: Path
    segments: tuple[Segment, ...]
    expected_duration_seconds: float
    reason: str
    fallback_video_codec: str | None = None
    fallback_audio_codec: str | None = None
    fallback_container: str | None = None
    fallback_pixel_format: str | None = None

    @property
    def is_fast_path(self) -> bool:
        return self.route == "stream-copy"

    def to_dict(self) -> dict[str, Any]:
        return {
            "route": self.route,
            "source": str(self.source),
            "destination": str(self.destination),
            "segments": [segment.to_dict() for segment in self.segments],
            "expected_duration_seconds": self.expected_duration_seconds,
            "reason": self.reason,
            "fallback_video_codec": self.fallback_video_codec,
            "fallback_audio_codec": self.fallback_audio_codec,
            "fallback_container": self.fallback_container,
            "fallback_pixel_format": self.fallback_pixel_format,
        }


def _output_format(path: Path) -> str:
    return "matroska" if path.suffix.lower() in {".mkv", ".matroska"} else "mp4"


def _partial_path(destination: Path) -> Path:
    suffix = destination.suffix or ".mp4"
    return destination.with_name(f".{destination.name}.partial-{uuid.uuid4().hex}{suffix}")


def _remove_partial(path: Path) -> OSError | None:
    try:
        path.unlink()
    except FileNotFoundError:
        return None
    except OSError as error:
        return error
    return None


def _emit_export_progress(
    callback: ExportProgressCallback | None,
    *,
    stage: str,
    current_seconds: float,
    total_duration_seconds: float,
    frame: int,
    total_frames: int,
    fps: float | None,
    started: float,
    percent_override: float | None = None,
) -> None:
    if callback is None:
        return
    total_duration = max(0.0, float(total_duration_seconds))
    current = max(0.0, min(total_duration, float(current_seconds)))
    fraction = current / total_duration if total_duration else 0.0
    percent = percent_override if percent_override is not None else fraction * 100.0
    percent = max(0.0, min(100.0, percent))
    elapsed = max(0.0, time.monotonic() - started)
    eta = (
        elapsed * (1.0 - fraction) / fraction
        if fraction > 0.0 and percent < 100.0
        else 0.0
        if percent >= 100.0
        else None
    )
    total = max(0, int(total_frames))
    callback(
        ExportProgress(
            stage=stage,
            percent=percent,
            frame=max(0, min(total, int(frame))),
            total_frames=total,
            fps=fps,
            elapsed_seconds=elapsed,
            eta_seconds=eta,
        )
    )


def _run_ffmpeg(
    command: list[str],
    *,
    progress_callback: ExportProgressCallback | None = None,
    stage: str = "encoding",
    command_duration_seconds: float = 0.0,
    progress_offset_seconds: float = 0.0,
    progress_total_duration_seconds: float = 0.0,
    command_total_frames: int = 0,
    progress_total_frames: int = 0,
    frame_offset: int = 0,
    started: float | None = None,
) -> None:
    if progress_callback is None:
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,
            )
        except OSError as error:
            raise ExportExecutionError(f"Could not start FFmpeg: {command[0]}") from error
        if result.returncode != 0:
            detail = result.stderr.strip() or "FFmpeg failed without a diagnostic"
            raise ExportExecutionError(detail)
        return

    if not command:
        raise ExportExecutionError("FFmpeg command is empty")
    progress_command = [
        *command[:-1],
        "-progress",
        "pipe:1",
        "-stats_period",
        "0.25",
        "-nostats",
        command[-1],
    ]
    try:
        process = subprocess.Popen(
            progress_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
    except OSError as error:
        raise ExportExecutionError(f"Could not start FFmpeg: {command[0]}") from error

    progress_values: dict[str, str] = {}
    tail: list[str] = []
    progress_started = time.monotonic() if started is None else started
    try:
        if process.stdout is None:
            raise ExportExecutionError("FFmpeg progress pipe is unavailable")
        for raw_line in process.stdout:
            line = raw_line.strip()
            if not line:
                continue
            if "=" not in line:
                tail.append(line)
                tail = tail[-8:]
                continue
            key, value = line.split("=", 1)
            if key not in {
                "frame",
                "fps",
                "out_time_us",
                "out_time_ms",
                "out_time",
                "speed",
                "progress",
            }:
                continue
            progress_values[key] = value
            if key != "progress":
                continue
            sample = parse_ffmpeg_progress_values(progress_values)
            local_time = sample.out_time_seconds
            if sample.done and command_duration_seconds > 0:
                local_time = command_duration_seconds
            command_duration = max(0.0, command_duration_seconds)
            if command_duration:
                local_time = min(command_duration, local_time)
            total_duration = progress_total_duration_seconds or command_duration
            local_fraction = local_time / command_duration if command_duration > 0 else 0.0
            local_frame = sample.frame
            if sample.done and command_total_frames > 0:
                local_frame = command_total_frames
            elif local_frame <= 0 and command_total_frames > 0:
                local_frame = round(local_fraction * command_total_frames)
            _emit_export_progress(
                progress_callback,
                stage=stage,
                current_seconds=progress_offset_seconds + local_time,
                total_duration_seconds=total_duration,
                frame=frame_offset + local_frame,
                total_frames=progress_total_frames or command_total_frames,
                fps=sample.fps,
                started=progress_started,
                percent_override=(
                    100.0
                    if sample.done and progress_offset_seconds + local_time >= total_duration
                    else None
                ),
            )
    except KeyboardInterrupt:
        process.terminate()
        process.wait()
        raise
    finally:
        if process.stdout is not None:
            process.stdout.close()
    return_code = process.wait()
    if return_code != 0:
        detail = "\n".join(tail) or "FFmpeg failed without a diagnostic"
        raise ExportExecutionError(detail)


def _expected_export_frames(
    plan: ExportPlan,
    source_probe: MediaProbe,
) -> int:
    return max(
        1,
        round(plan.expected_duration_seconds * source_probe.frame_rate_value),
    )


def _stream_maps(has_audio: bool) -> list[str]:
    maps = ["-map", "0:v:0"]
    if has_audio:
        maps.extend(["-map", "0:a:0"])
    return maps


def _segment_is_full_source(
    segment: Segment,
    source_duration_seconds: float,
) -> bool:
    return math.isclose(segment.start_seconds, 0.0, abs_tol=_BOUNDARY_TOLERANCE) and math.isclose(
        segment.end_seconds,
        source_duration_seconds,
        abs_tol=_BOUNDARY_TOLERANCE,
    )


def _execute_stream_copy(
    plan: ExportPlan,
    source_probe: MediaProbe,
    partial: Path,
    ffmpeg_path: str,
    *,
    progress_callback: ExportProgressCallback | None = None,
    started: float | None = None,
) -> None:
    has_audio = source_probe.has_audio_stream
    output_format = _output_format(plan.destination)
    segments = plan.segments
    total_frames = _expected_export_frames(plan, source_probe)
    if len(segments) == 1:
        segment = segments[0]
        command = [
            ffmpeg_path,
            "-hide_banner",
            "-loglevel",
            "error",
            "-nostdin",
        ]
        if not _segment_is_full_source(
            segment,
            source_probe.duration_seconds,
        ):
            command.extend(
                [
                    "-ss",
                    f"{segment.start_seconds:.6f}",
                ]
            )
        command.extend(
            [
                "-i",
                str(plan.source),
            ]
        )
        if not _segment_is_full_source(
            segment,
            source_probe.duration_seconds,
        ):
            command.extend(["-t", f"{segment.duration_seconds:.6f}"])
        command.extend(
            _stream_maps(has_audio)
            + [
                "-c",
                "copy",
                "-avoid_negative_ts",
                "make_zero",
                "-f",
                output_format,
                str(partial),
            ]
        )
        _run_ffmpeg(
            command,
            progress_callback=progress_callback,
            command_duration_seconds=segment.duration_seconds,
            progress_total_duration_seconds=plan.expected_duration_seconds,
            command_total_frames=total_frames,
            progress_total_frames=total_frames,
            started=started,
        )
        return

    with tempfile.TemporaryDirectory(
        prefix=f".{plan.destination.name}.parts-",
        dir=str(plan.destination.parent),
    ) as temporary_directory:
        parts_directory = Path(temporary_directory)
        part_paths: list[Path] = []
        part_suffix = plan.source.suffix or ".mp4"
        frame_rate = source_probe.frame_rate_value
        progress_offset = 0.0
        frame_offset = 0
        for index, segment in enumerate(segments):
            part = parts_directory / f"part-{index}{part_suffix}"
            command = [
                ffmpeg_path,
                "-hide_banner",
                "-loglevel",
                "error",
                "-nostdin",
                "-ss",
                f"{segment.start_seconds:.6f}",
                "-i",
                str(plan.source),
                "-t",
                f"{segment.duration_seconds:.6f}",
                *_stream_maps(has_audio),
                "-c",
                "copy",
                "-avoid_negative_ts",
                "make_zero",
                str(part),
            ]
            command_frames = max(
                1,
                round(segment.duration_seconds * frame_rate),
            )
            _run_ffmpeg(
                command,
                progress_callback=progress_callback,
                stage=f"cut {index + 1}/{len(segments)}",
                command_duration_seconds=segment.duration_seconds,
                progress_offset_seconds=progress_offset,
                progress_total_duration_seconds=plan.expected_duration_seconds,
                command_total_frames=command_frames,
                progress_total_frames=total_frames,
                frame_offset=frame_offset,
                started=started,
            )
            part_paths.append(part)
            progress_offset += segment.duration_seconds
            frame_offset += command_frames
        list_path = parts_directory / "concat-list.txt"
        list_path.write_text(
            "\n".join("'" + str(path).replace("'", "'\\''") + "'" for path in part_paths) + "\n",
            encoding="utf-8",
        )
        command = [
            ffmpeg_path,
            "-hide_banner",
            "-loglevel",
            "error",
            "-nostdin",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(list_path),
            *_stream_maps(has_audio),
            "-c",
            "copy",
            "-avoid_negative_ts",
            "make_zero",
            "-f",
            output_format,
            str(partial),
        ]
        _emit_export_progress(
            progress_callback,
            stage="assembling",
            current_seconds=plan.expected_duration_seconds,
            total_duration_seconds=plan.expected_duration_seconds,
            frame=total_frames,
            total_frames=total_frames,
            fps=None,
            started=time.monotonic() if started is None else started,
            percent_override=99.0,
        )
        _run_ffmpeg(command)


def _fallback_filter(
    segments: Sequence[Segment],
    has_audio: bool,
) -> str:
    filters: list[str] = []
    for index, segment in enumerate(segments):
        start = f"{segment.start_seconds:.6f}"
        end = f"{segment.end_seconds:.6f}"
        filters.append(f"[0:v]trim=start={start}:end={end},setpts=PTS-STARTPTS[v{index}]")
        if has_audio:
            filters.append(f"[0:a]atrim=start={start}:end={end},asetpts=PTS-STARTPTS[a{index}]")
    if has_audio:
        inputs = "".join(f"[v{index}][a{index}]" for index in range(len(segments)))
        filters.append(f"{inputs}concat=n={len(segments)}:v=1:a=1[outv][outa]")
    else:
        inputs = "".join(f"[v{index}]" for index in range(len(segments)))
        filters.append(f"{inputs}concat=n={len(segments)}:v=1:a=0[outv]")
    return ";".join(filters)


def _execute_fallback(
    plan: ExportPlan,
    source_probe: MediaProbe,
    partial: Path,
    ffmpeg_path: str,
    *,
    progress_callback: ExportProgressCallback | None = None,
    started: float | None = None,
) -> None:
    has_audio = source_probe.has_audio_stream
    command = [
        ffmpeg_path,
        "-hide_banner",
        "-loglevel",
        "error",
        "-nostdin",
        "-i",
        str(plan.source),
        "-filter_complex",
        _fallback_filter(plan.segments, has_audio),
        "-map",
        "[outv]",
        "-c:v",
        plan.fallback_video_codec or "libx264",
        "-preset",
        "medium",
        "-crf",
        "18",
        "-pix_fmt",
        plan.fallback_pixel_format or "yuv420p",
    ]
    if has_audio:
        command.extend(
            [
                "-map",
                "[outa]",
                "-c:a",
                plan.fallback_audio_codec or "aac",
                "-b:a",
                "192k",
            ]
        )
    command.extend(
        [
            "-movflags",
            "+faststart",
            "-f",
            plan.fallback_container or "mp4",
            str(partial),
        ]
    )
    total_frames = _expected_export_frames(plan, source_probe)
    _run_ffmpeg(
        command,
        progress_callback=progress_callback,
        command_duration_seconds=plan.expected_duration_seconds,
        progress_total_duration_seconds=plan.expected_duration_seconds,
        command_total_frames=total_frames,
        progress_total_frames=total_frames,
        started=started,
    )


def verify_export_output(
    plan: ExportPlan,
    source_probe: MediaProbe,
    candidate: Path,
    *,
    ffmpeg_path: str = "ffmpeg",
    ffprobe_path: str = "ffprobe",
) -> MediaProbe:
    if not candidate.is_file() or candidate.stat().st_size <= 0:
        raise ExportExecutionError("FFmpeg did not create a non-empty output")
    try:
        output_probe = probe_media(candidate, ffprobe_path)
    except MediaProbeError as error:
        raise ExportExecutionError(f"Export output could not be probed: {error}") from error
    try:
        frame_rate = source_probe.frame_rate_value
    except MediaProbeError as error:
        raise ExportExecutionError(
            f"Source frame rate is invalid during output validation: {error}"
        ) from error
    duration_tolerance = max(_DURATION_TOLERANCE, 2.0 / frame_rate)
    if abs(output_probe.duration_seconds - plan.expected_duration_seconds) > duration_tolerance:
        raise ExportExecutionError("Export duration does not match the edited duration")
    if output_probe.width != source_probe.width or output_probe.height != source_probe.height:
        raise ExportExecutionError("Export dimensions do not match the source dimensions")
    if output_probe.has_audio_stream != source_probe.has_audio_stream:
        raise ExportExecutionError("Export audio stream presence does not match the source")
    try:
        result = subprocess.run(
            [
                ffmpeg_path,
                "-hide_banner",
                "-loglevel",
                "error",
                "-xerror",
                "-nostdin",
                "-i",
                str(candidate),
                "-map",
                "0",
                "-f",
                "null",
                "-",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as error:
        raise ExportExecutionError(
            f"Could not start FFmpeg for output validation: {ffmpeg_path}"
        ) from error
    if result.returncode != 0:
        detail = result.stderr.strip() or "Output decode validation failed"
        raise ExportExecutionError(detail)
    return output_probe


def execute_export(
    plan: ExportPlan,
    *,
    ffmpeg_path: str = "ffmpeg",
    ffprobe_path: str = "ffprobe",
    progress_callback: ExportProgressCallback | None = None,
) -> Path:
    if plan.route not in {"stream-copy", "fallback"}:
        raise ExportExecutionError(f"Unsupported export route: {plan.route}")
    source = plan.source.expanduser().resolve()
    destination = plan.destination.expanduser()
    if destination.resolve() == source:
        raise ExportExecutionError("Export destination must differ from the source")
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        source_stat = source.stat()
    except OSError as error:
        raise ExportExecutionError(f"Could not prepare export paths: {error}") from error
    try:
        source_probe = probe_media(source, ffprobe_path)
    except MediaProbeError as error:
        raise ExportExecutionError(f"Could not inspect export source: {error}") from error
    started = time.monotonic()
    total_frames = _expected_export_frames(plan, source_probe)
    _emit_export_progress(
        progress_callback,
        stage="starting",
        current_seconds=0.0,
        total_duration_seconds=plan.expected_duration_seconds,
        frame=0,
        total_frames=total_frames,
        fps=None,
        started=started,
    )
    partial = _partial_path(destination)
    try:
        if plan.route == "stream-copy":
            _execute_stream_copy(
                plan,
                source_probe,
                partial,
                ffmpeg_path,
                progress_callback=progress_callback,
                started=started,
            )
        else:
            _execute_fallback(
                plan,
                source_probe,
                partial,
                ffmpeg_path,
                progress_callback=progress_callback,
                started=started,
            )
        _emit_export_progress(
            progress_callback,
            stage="verifying",
            current_seconds=plan.expected_duration_seconds,
            total_duration_seconds=plan.expected_duration_seconds,
            frame=total_frames,
            total_frames=total_frames,
            fps=None,
            started=started,
            percent_override=99.0,
        )
        verify_export_output(
            plan,
            source_probe,
            partial,
            ffmpeg_path=ffmpeg_path,
            ffprobe_path=ffprobe_path,
        )
        current_source_stat = source.stat()
        if (
            current_source_stat.st_size != source_stat.st_size
            or current_source_stat.st_mtime_ns != source_stat.st_mtime_ns
        ):
            raise ExportExecutionError("Source changed during export; output was not published")
        os.replace(partial, destination)
        _emit_export_progress(
            progress_callback,
            stage="complete",
            current_seconds=plan.expected_duration_seconds,
            total_duration_seconds=plan.expected_duration_seconds,
            frame=total_frames,
            total_frames=total_frames,
            fps=None,
            started=started,
            percent_override=100.0,
        )
    except (ExportExecutionError, MediaProbeError, OSError) as error:
        cleanup_error = _remove_partial(partial)
        message = f"Could not export {destination.name}: {error}"
        if cleanup_error is not None:
            message += f"; could not remove partial output: {cleanup_error}"
        raise ExportExecutionError(message) from error
    return destination


def _format_name_tokens(format_name: str) -> set[str]:
    return {token.strip().lower() for token in format_name.split(",") if token.strip()}


def _probe_keyframe_timestamps(
    source: Path,
    ffprobe_path: str,
) -> tuple[float, ...]:
    try:
        result = subprocess.run(
            [
                ffprobe_path,
                "-v",
                "error",
                "-select_streams",
                "v:0",
                "-skip_frame",
                "nokey",
                "-show_frames",
                "-show_entries",
                "frame=best_effort_timestamp_time",
                "-of",
                "json",
                str(source),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError as error:
        raise ExportPlanningError(
            f"ffprobe is not installed or not on PATH: {ffprobe_path}"
        ) from error
    if result.returncode != 0:
        detail = result.stderr.strip() or "ffprobe could not read keyframes"
        raise ExportPlanningError(f"Could not inspect keyframes for {source.name}: {detail}")
    try:
        data = json.loads(result.stdout)
        frames = data["frames"]
    except (KeyError, TypeError, json.JSONDecodeError) as error:
        raise ExportPlanningError(
            f"ffprobe returned invalid keyframe data for {source.name}"
        ) from error
    if not isinstance(frames, list):
        raise ExportPlanningError(f"ffprobe returned invalid keyframe data for {source.name}")
    timestamps: list[float] = []
    for frame in frames:
        if not isinstance(frame, dict):
            raise ExportPlanningError(f"ffprobe returned invalid keyframe data for {source.name}")
        value = frame.get("best_effort_timestamp_time")
        if value is None:
            continue
        try:
            timestamp = float(value)
        except ValueError as error:
            raise ExportPlanningError(
                f"ffprobe returned an invalid keyframe timestamp for {source.name}"
            ) from error
        if not math.isfinite(timestamp) or timestamp < 0:
            raise ExportPlanningError(
                f"ffprobe returned an invalid keyframe timestamp for {source.name}"
            )
        timestamps.append(timestamp)
    return tuple(timestamps)


def _validated_keyframes(
    keyframe_timestamps: Sequence[float],
) -> tuple[float, ...]:
    validated: list[float] = []
    for timestamp in keyframe_timestamps:
        if (
            not isinstance(timestamp, (int, float))
            or isinstance(timestamp, bool)
            or not math.isfinite(float(timestamp))
            or float(timestamp) < 0
        ):
            raise ExportPlanningError("Keyframe timestamps must be finite non-negative numbers")
        validated.append(float(timestamp))
    return tuple(validated)


def _boundary_is_keyframe(
    boundary: float,
    keyframes: Sequence[float],
) -> bool:
    return any(
        math.isclose(
            boundary,
            keyframe,
            rel_tol=0.0,
            abs_tol=_BOUNDARY_TOLERANCE,
        )
        for keyframe in keyframes
    )


def _internal_boundaries(
    segments: Sequence[Segment],
    source_duration_seconds: float,
) -> tuple[float, ...]:
    boundaries: set[float] = set()
    for segment in segments:
        if segment.start_seconds > _BOUNDARY_TOLERANCE:
            boundaries.add(segment.start_seconds)
        if segment.end_seconds < source_duration_seconds - _BOUNDARY_TOLERANCE:
            boundaries.add(segment.end_seconds)
    return tuple(sorted(boundaries))


def plan_export(
    media: MediaProbe,
    timeline: SegmentTimeline,
    destination: Path,
    *,
    keyframe_timestamps: Sequence[float] | None = None,
    ffprobe_path: str = "ffprobe",
) -> ExportPlan:
    timeline.validate()
    if not math.isclose(
        media.duration_seconds,
        timeline.source_duration_seconds,
        rel_tol=0.0,
        abs_tol=_DURATION_TOLERANCE,
    ):
        raise ExportPlanningError("Source duration does not match the project timeline")
    source = media.path.expanduser().resolve()
    output = Path(destination).expanduser()
    if output.resolve() == source:
        raise ExportPlanningError("Export destination must differ from the source")
    active_segments = tuple(segment for segment in timeline.segment_items if not segment.deleted)
    if not active_segments or timeline.edited_duration_seconds <= 0:
        raise ExportPlanningError("Cannot export an empty edit")

    fallback_reasons: list[str] = []
    formats = _format_name_tokens(media.format_name)
    if not formats.intersection(_FAST_CONTAINERS):
        fallback_reasons.append("source container is not in the conservative stream-copy policy")
    if media.video_codec.lower() not in _FAST_VIDEO_CODECS:
        fallback_reasons.append(f"video codec {media.video_codec} is not in the stream-copy policy")
    audio_is_eligible = (
        media.audio_codec in _FAST_AUDIO_CODECS
        if media.has_audio_stream
        else media.audio_codec is None
    )
    if not audio_is_eligible:
        fallback_reasons.append(f"audio codec {media.audio_codec} is not in the stream-copy policy")

    boundaries = _internal_boundaries(
        active_segments,
        timeline.source_duration_seconds,
    )
    keyframes: tuple[float, ...] = ()
    if boundaries:
        if keyframe_timestamps is None:
            keyframes = _probe_keyframe_timestamps(source, ffprobe_path)
        else:
            keyframes = _validated_keyframes(keyframe_timestamps)
        if not keyframes or any(
            not _boundary_is_keyframe(boundary, keyframes) for boundary in boundaries
        ):
            fallback_reasons.append("one or more cut boundaries are not keyframe-aligned")

    if not fallback_reasons:
        if boundaries:
            reason = "All retained cut boundaries are keyframe-aligned for stream copy"
        else:
            reason = "No internal cut boundaries require re-encoding"
        return ExportPlan(
            route="stream-copy",
            source=source,
            destination=output,
            segments=active_segments,
            expected_duration_seconds=timeline.edited_duration_seconds,
            reason=reason,
        )

    return ExportPlan(
        route="fallback",
        source=source,
        destination=output,
        segments=active_segments,
        expected_duration_seconds=timeline.edited_duration_seconds,
        reason="; ".join(fallback_reasons),
        fallback_video_codec="libx264",
        fallback_audio_codec="aac" if media.has_audio_stream else None,
        fallback_container="mp4",
        fallback_pixel_format="yuv420p",
    )
