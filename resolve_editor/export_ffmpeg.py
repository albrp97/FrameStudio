from __future__ import annotations

import tempfile
import time
from collections.abc import Sequence
from fractions import Fraction
from pathlib import Path

from .export_process import (
    emit_export_progress,
    expected_export_frames,
    output_format,
    run_ffmpeg,
    segment_is_full_source,
)
from .export_types import (
    ExportExecutionError,
    ExportPlan,
    ExportProgressCallback,
    OutputPolicy,
)
from .media import MediaProbe
from .model import Segment


def stream_maps(has_audio: bool) -> list[str]:
    maps = ["-map", "0:v:0"]
    if has_audio:
        maps.extend(["-map", "0:a:0"])
    return maps


def execute_stream_copy(
    plan: ExportPlan,
    source_probe: MediaProbe,
    partial: Path,
    ffmpeg_path: str,
    *,
    progress_callback: ExportProgressCallback | None = None,
    started: float | None = None,
) -> None:
    has_audio = source_probe.has_audio_stream
    output_format_name = output_format(plan.destination)
    segments = plan.segments
    total_frames = expected_export_frames(plan, source_probe)
    if len(segments) == 1:
        segment = segments[0]
        command = [
            ffmpeg_path,
            "-hide_banner",
            "-loglevel",
            "error",
            "-nostdin",
        ]
        if not segment_is_full_source(
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
        if not segment_is_full_source(
            segment,
            source_probe.duration_seconds,
        ):
            command.extend(["-t", f"{segment.duration_seconds:.6f}"])
        command.extend(
            stream_maps(has_audio)
            + [
                "-c",
                "copy",
                "-avoid_negative_ts",
                "make_zero",
                "-f",
                output_format_name,
                str(partial),
            ]
        )
        run_ffmpeg(
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
                *stream_maps(has_audio),
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
            run_ffmpeg(
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
            *stream_maps(has_audio),
            "-c",
            "copy",
            "-avoid_negative_ts",
            "make_zero",
            "-f",
            output_format_name,
            str(partial),
        ]
        emit_export_progress(
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
        run_ffmpeg(command)


def fallback_filter(
    segments: Sequence[Segment],
    has_audio: bool,
    *,
    output_policy: OutputPolicy | None = None,
) -> str:
    filters: list[str] = []
    for index, segment in enumerate(segments):
        start = f"{segment.start_seconds:.6f}"
        end = f"{segment.end_seconds:.6f}"
        video_filter = f"[0:v]trim=start={start}:end={end},setpts=PTS-STARTPTS"
        if output_policy is not None:
            video_filter += (
                f",scale={output_policy.width}:{output_policy.height}:"
                "force_original_aspect_ratio=decrease,"
                f"pad={output_policy.width}:{output_policy.height}:(ow-iw)/2:(oh-ih)/2,"
                "setsar=1"
            )
        filters.append(f"{video_filter}[v{index}]")
        if has_audio:
            filters.append(f"[0:a]atrim=start={start}:end={end},asetpts=PTS-STARTPTS[a{index}]")
    if has_audio:
        inputs = "".join(f"[v{index}][a{index}]" for index in range(len(segments)))
        filters.append(f"{inputs}concat=n={len(segments)}:v=1:a=1[outv][outa]")
    else:
        inputs = "".join(f"[v{index}]" for index in range(len(segments)))
        filters.append(f"{inputs}concat=n={len(segments)}:v=1:a=0[outv]")
    return ";".join(filters)


def mixed_fallback_filter(
    plan: ExportPlan,
    probes: Sequence[MediaProbe],
) -> str:
    policy = plan.output_policy
    if policy is None:
        raise ExportExecutionError("Mixed export is missing its output policy")
    source_indexes = {source_id: index for index, source_id in enumerate(plan.source_ids)}
    if len(source_indexes) != len(probes):
        raise ExportExecutionError("Mixed export source identities do not match probes")
    filters: list[str] = []
    video_inputs: list[str] = []
    audio_inputs: list[str] = []
    target_rate = policy.frame_rate
    for index, segment in enumerate(plan.segments):
        source_index = source_indexes.get(segment.source_id or "")
        if source_index is None:
            raise ExportExecutionError(
                f"Mixed export block references unknown source: {segment.source_id}"
            )
        start = f"{segment.start_seconds:.6f}"
        duration = f"{segment.duration_seconds:.6f}"
        filters.append(
            f"[{source_index}:v:0]trim=start={start}:duration={duration},"
            f"setpts=PTS-STARTPTS,scale={policy.width}:{policy.height}:"
            "force_original_aspect_ratio=decrease,"
            f"pad={policy.width}:{policy.height}:(ow-iw)/2:(oh-ih)/2,"
            f"setsar=1,fps={target_rate}[v{index}]"
        )
        video_inputs.append(f"[v{index}]")
        if policy.audio_stream_present:
            if probes[source_index].has_audio_stream:
                filters.append(
                    f"[{source_index}:a:0]atrim=start={start}:duration={duration},"
                    f"asetpts=PTS-STARTPTS,aresample=async=1:first_pts=0[a{index}]"
                )
            else:
                filters.append(
                    f"anullsrc=channel_layout=stereo:sample_rate=48000,"
                    f"atrim=duration={duration},asetpts=PTS-STARTPTS[a{index}]"
                )
            audio_inputs.append(f"[a{index}]")
    if policy.audio_stream_present:
        inputs = "".join(
            f"{video_inputs[index]}{audio_inputs[index]}" for index in range(len(video_inputs))
        )
        filters.append(f"{inputs}concat=n={len(video_inputs)}:v=1:a=1[outv][outa]")
    else:
        filters.append(f"{''.join(video_inputs)}concat=n={len(video_inputs)}:v=1:a=0[outv]")
    return ";".join(filters)


def expected_mixed_export_frames(plan: ExportPlan) -> tuple[int, float]:
    if plan.output_policy is None:
        raise ExportExecutionError("Mixed export is missing its output policy")
    try:
        rate = float(Fraction(plan.output_policy.frame_rate))
    except (ValueError, ZeroDivisionError) as error:
        raise ExportExecutionError("Mixed export output frame rate is invalid") from error
    return max(1, round(plan.expected_duration_seconds * rate)), rate


def execute_mixed_fallback(
    plan: ExportPlan,
    probes: Sequence[MediaProbe],
    partial: Path,
    ffmpeg_path: str,
    *,
    progress_callback: ExportProgressCallback | None = None,
    started: float | None = None,
) -> None:
    policy = plan.output_policy
    if policy is None:
        raise ExportExecutionError("Mixed export is missing its output policy")
    total_frames, _frame_rate = expected_mixed_export_frames(plan)
    command = [
        ffmpeg_path,
        "-hide_banner",
        "-loglevel",
        "error",
        "-nostdin",
    ]
    for probe in probes:
        command.extend(["-i", str(probe.path)])
    command.extend(
        [
            "-filter_complex",
            mixed_fallback_filter(plan, probes),
            "-map",
            "[outv]",
            "-c:v",
            policy.video_codec,
            "-preset",
            "medium",
            "-crf",
            "18",
            "-pix_fmt",
            policy.pixel_format,
        ]
    )
    if policy.audio_stream_present:
        command.extend(
            [
                "-map",
                "[outa]",
                "-c:a",
                policy.audio_codec or "aac",
                "-b:a",
                "192k",
            ]
        )
    command.extend(
        [
            "-movflags",
            "+faststart",
            "-f",
            policy.container,
            str(partial),
        ]
    )
    run_ffmpeg(
        command,
        progress_callback=progress_callback,
        stage="composing",
        command_duration_seconds=plan.expected_duration_seconds,
        progress_total_duration_seconds=plan.expected_duration_seconds,
        command_total_frames=total_frames,
        progress_total_frames=total_frames,
        started=started,
    )


def execute_fallback(
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
        fallback_filter(
            plan.segments,
            has_audio,
            output_policy=plan.output_policy,
        ),
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
    total_frames = expected_export_frames(plan, source_probe)
    run_ffmpeg(
        command,
        progress_callback=progress_callback,
        command_duration_seconds=plan.expected_duration_seconds,
        progress_total_duration_seconds=plan.expected_duration_seconds,
        command_total_frames=total_frames,
        progress_total_frames=total_frames,
        started=started,
    )
