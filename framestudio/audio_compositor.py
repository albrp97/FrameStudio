from __future__ import annotations

import json
import math
import threading
import uuid
from array import array
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, Mapping

from .audio import AUDIO_POLICY_VERSION, audio_decision_is_stale
from .export_process import (
    run_command_with_cancellation,
)
from .export_process import (
    run_ffmpeg as run_managed_ffmpeg,
)
from .export_types import ExportExecutionError
from .layout_plan import LayoutPlan
from .model_project import Project
from .model_types import SourceReference

AUDIO_SAMPLE_RATE = 48_000
AUDIO_CHANNELS = 2
PREENCODE_HEADROOM = 0.90

AudioLayout = Literal["mono", "stereo", "5.1", "5.1(side)"]

_PAN_VECTORS: dict[int, tuple[float, ...]] = {
    0: (),
    1: (0.0,),
    2: (-25.0, 25.0),
    3: (-25.0, 0.0, 25.0),
    4: (-25.0, 25.0, -50.0, 50.0),
}


class AudioCompositionError(RuntimeError):
    """Raised when an audio composition cannot be planned or published."""


class AudioLayoutError(AudioCompositionError):
    """Raised when source channel metadata is unsupported or contradictory."""


class AudioRenderError(AudioCompositionError):
    """Raised when FFmpeg rendering or output verification fails."""


def sample_boundary(tick_us: int, sample_rate: int = AUDIO_SAMPLE_RATE) -> int:
    if (
        isinstance(tick_us, bool)
        or not isinstance(tick_us, int)
        or tick_us < 0
        or isinstance(sample_rate, bool)
        or not isinstance(sample_rate, int)
        or sample_rate <= 0
    ):
        raise AudioCompositionError("Audio boundaries require non-negative integer ticks")
    return (tick_us * sample_rate + 500_000) // 1_000_000


def fixed_pan_vector(active_count: int) -> tuple[float, ...]:
    try:
        return _PAN_VECTORS[active_count]
    except KeyError as error:
        raise AudioCompositionError(
            "Fixed audio layout supports one through four active visual slots",
        ) from error


def classify_audio_layout(
    channels: int,
    channel_layout: str | None,
) -> AudioLayout:
    if isinstance(channels, bool) or not isinstance(channels, int) or channels <= 0:
        raise AudioLayoutError("Audio channel count must be a positive integer")
    if channel_layout is not None and not isinstance(channel_layout, str):
        raise AudioLayoutError("Audio channel layout metadata must be a string or absent")
    normalized = channel_layout.strip().lower() if channel_layout is not None else None
    if normalized == "":
        normalized = None

    if normalized in {"stereo", "2.0"}:
        if channels != 2:
            raise AudioLayoutError(
                f"Conflicting stereo channel layout for {channels} audio channels",
            )
        return "stereo"
    if normalized == "mono":
        if channels != 1:
            raise AudioLayoutError(
                f"Conflicting mono channel layout for {channels} audio channels",
            )
        return "mono"
    if normalized == "5.1":
        if channels != 6:
            raise AudioLayoutError(
                f"Conflicting 5.1 channel layout for {channels} audio channels",
            )
        return "5.1"
    if normalized == "5.1(side)":
        if channels != 6:
            raise AudioLayoutError(
                f"Conflicting 5.1(side) channel layout for {channels} audio channels",
            )
        return "5.1(side)"
    if normalized is not None:
        raise AudioLayoutError(f"Unsupported audio channel layout: {channel_layout}")
    if channels == 2:
        return "stereo"
    raise AudioLayoutError(
        f"Audio channel layout is absent or unknown for {channels} channels",
    )


@dataclass(frozen=True)
class AudioSourcePlan:
    source_id: str
    status: str
    channels: int | None
    channel_layout: AudioLayout | None
    gain_db: float
    gain_linear: float
    peak_linear: float | None
    audio_enabled: bool


@dataclass(frozen=True)
class AudioBlockPlan:
    segment_id: str
    source_id: str
    pan_percent: float
    source_start_sample: int
    source_end_sample: int
    start_sample: int
    end_sample: int
    audio_status: str
    channels: int | None
    channel_layout: AudioLayout | None
    gain_db: float
    gain_linear: float
    peak_linear: float | None
    audio_enabled: bool
    effective_row_abs_sums: tuple[float, float]

    @property
    def duration_samples(self) -> int:
        return self.end_sample - self.start_sample

    @property
    def source_duration_samples(self) -> int:
        return self.source_end_sample - self.source_start_sample


@dataclass(frozen=True)
class AudioIntervalPlan:
    start_tick: int
    end_tick: int
    start_sample: int
    end_sample: int
    blocks: tuple[AudioBlockPlan, ...]

    @property
    def duration_samples(self) -> int:
        return self.end_sample - self.start_sample

    @property
    def audible_blocks(self) -> tuple[AudioBlockPlan, ...]:
        return tuple(block for block in self.blocks if block.audio_enabled)


@dataclass(frozen=True)
class AudioPlan:
    sample_rate: int
    channels: int
    final_duration_ticks: int
    final_sample_count: int
    source_plans: tuple[AudioSourcePlan, ...]
    intervals: tuple[AudioIntervalPlan, ...]


@dataclass(frozen=True)
class AudioRenderResult:
    output_path: Path
    sample_rate: int
    channels: int
    sample_count: int
    peak: float
    plan: AudioPlan


def build_audio_plan(
    project: Project,
    layout_plan: LayoutPlan,
    *,
    sample_rate: int = AUDIO_SAMPLE_RATE,
) -> AudioPlan:
    if sample_rate != AUDIO_SAMPLE_RATE:
        raise AudioCompositionError("The fixed audio contract requires a 48 kHz sample rate")
    if layout_plan.final_duration_ticks <= 0:
        raise AudioCompositionError("The audio plan needs a positive final video duration")

    source_ids = {block.source_id for block in layout_plan.included_blocks}
    source_plans = {source_id: _source_plan(project, source_id) for source_id in sorted(source_ids)}
    intervals: list[AudioIntervalPlan] = []
    for interval in layout_plan.intervals:
        start_sample = sample_boundary(interval.start_tick, sample_rate)
        end_sample = sample_boundary(interval.end_tick, sample_rate)
        if end_sample <= start_sample:
            continue
        pans = fixed_pan_vector(len(interval.active_blocks))
        blocks: list[AudioBlockPlan] = []
        for block, pan_percent in zip(interval.active_blocks, pans, strict=True):
            if not (
                block.timeline_start_tick <= interval.start_tick
                and interval.end_tick <= block.timeline_end_tick
            ):
                raise AudioCompositionError(
                    f"Layout interval is outside source block {block.segment_id}",
                )
            spec = source_plans[block.source_id]
            source_start_tick = block.source_range.source_start_tick + (
                interval.start_tick - block.timeline_start_tick
            )
            source_end_tick = block.source_range.source_start_tick + (
                interval.end_tick - block.timeline_start_tick
            )
            source_start_sample = sample_boundary(source_start_tick, sample_rate)
            source_end_sample = sample_boundary(source_end_tick, sample_rate)
            row_abs_sums = _row_abs_sums(spec.channel_layout, pan_percent)
            blocks.append(
                AudioBlockPlan(
                    segment_id=block.segment_id,
                    source_id=block.source_id,
                    pan_percent=pan_percent,
                    source_start_sample=source_start_sample,
                    source_end_sample=source_end_sample,
                    start_sample=start_sample,
                    end_sample=end_sample,
                    audio_status=spec.status,
                    channels=spec.channels,
                    channel_layout=spec.channel_layout,
                    gain_db=spec.gain_db,
                    gain_linear=spec.gain_linear,
                    peak_linear=spec.peak_linear,
                    audio_enabled=spec.audio_enabled,
                    effective_row_abs_sums=(
                        spec.gain_linear * row_abs_sums[0],
                        spec.gain_linear * row_abs_sums[1],
                    ),
                )
            )
        intervals.append(
            AudioIntervalPlan(
                start_tick=interval.start_tick,
                end_tick=interval.end_tick,
                start_sample=start_sample,
                end_sample=end_sample,
                blocks=tuple(blocks),
            )
        )
    return AudioPlan(
        sample_rate=sample_rate,
        channels=AUDIO_CHANNELS,
        final_duration_ticks=layout_plan.final_duration_ticks,
        final_sample_count=sample_boundary(layout_plan.final_duration_ticks, sample_rate),
        source_plans=tuple(source_plans.values()),
        intervals=tuple(intervals),
    )


def render_audio(
    project: Project,
    layout_plan: LayoutPlan,
    destination: Path,
    *,
    ffmpeg_path: str = "ffmpeg",
    ffprobe_path: str = "ffprobe",
    cancel_event: threading.Event | None = None,
) -> AudioRenderResult:
    plan = build_audio_plan(project, layout_plan)
    output = Path(destination).expanduser()
    if not output.parent.is_dir():
        raise AudioRenderError(f"Audio destination directory does not exist: {output.parent}")
    resolved_output = output.resolve()
    project_sources = project.sources or (project.source,)
    source_paths = {Path(source.path).expanduser().resolve() for source in project_sources}
    if resolved_output in source_paths:
        raise AudioRenderError("Audio output must not overwrite a source media file")

    partial = output.with_name(f".{output.name}.{uuid.uuid4().hex}.partial")
    published = False
    try:
        command, filter_graph = _render_command(project, plan, partial, ffmpeg_path)
        _run_ffmpeg(command, filter_graph, cancel_event=cancel_event)
        sample_count, peak = _verify_pcm_output(
            partial,
            ffprobe_path=ffprobe_path,
            ffmpeg_path=ffmpeg_path,
            expected_samples=plan.final_sample_count,
            cancel_event=cancel_event,
        )
        partial.replace(output)
        published = True
        return AudioRenderResult(
            output_path=output,
            sample_rate=plan.sample_rate,
            channels=plan.channels,
            sample_count=sample_count,
            peak=peak,
            plan=plan,
        )
    finally:
        if not published:
            try:
                partial.unlink(missing_ok=True)
            except OSError:
                pass


def _source_plan(project: Project, source_id: str) -> AudioSourcePlan:
    source = project.source_by_id(source_id)
    metadata = source.metadata
    settings = project.source_audio_settings(source_id)
    status_value = settings.get("status")
    status = status_value if isinstance(status_value, str) else "pending"
    stream_present = metadata.get("audio_stream_present")
    if stream_present is False or status == "not-applicable":
        return AudioSourcePlan(
            source_id=source_id,
            status="not-applicable",
            channels=None,
            channel_layout=None,
            gain_db=0.0,
            gain_linear=1.0,
            peak_linear=None,
            audio_enabled=False,
        )
    if status in {"pending", "failed", "unsupported"}:
        diagnostic = settings.get("diagnostic")
        suffix = f": {diagnostic}" if isinstance(diagnostic, str) and diagnostic else ""
        raise AudioCompositionError(
            f"Source audio analysis is {status} for {source_id}{suffix}",
        )
    if status not in {"ready", "silent"}:
        raise AudioCompositionError(f"Unsupported source audio status for {source_id}: {status}")
    _validate_persisted_audio_decision(source, settings, status)

    raw_channels = metadata.get("audio_channels")
    if isinstance(raw_channels, bool) or not isinstance(raw_channels, int):
        raise AudioLayoutError(f"Audio channel count is missing for {source_id}")
    layout = classify_audio_layout(raw_channels, metadata.get("audio_channel_layout"))
    raw_gain = settings["gain_db"]
    if not isinstance(raw_gain, (int, float)) or isinstance(raw_gain, bool):
        raise AudioCompositionError(f"Audio gain is invalid for {source_id}")
    gain_db = float(raw_gain)
    if not math.isfinite(gain_db):
        raise AudioCompositionError(f"Audio gain is invalid for {source_id}")
    gain_linear = 10.0 ** (gain_db / 20.0)
    peak_linear = _peak_linear(settings)
    return AudioSourcePlan(
        source_id=source_id,
        status=status,
        channels=raw_channels,
        channel_layout=layout,
        gain_db=gain_db,
        gain_linear=gain_linear,
        peak_linear=peak_linear,
        audio_enabled=status == "ready",
    )


def _validate_persisted_audio_decision(
    source: SourceReference,
    settings: Mapping[str, Any],
    status: str,
) -> None:
    if settings.get("policy_version") != AUDIO_POLICY_VERSION:
        raise AudioCompositionError(
            f"Source audio analysis policy is missing or unsupported for {source.source_id}",
        )
    if audio_decision_is_stale(source, settings):
        raise AudioCompositionError(
            f"Source audio analysis is missing or stale for {source.source_id}",
        )
    if "gain_db" not in settings:
        raise AudioCompositionError(
            f"Source audio gain is missing for {source.source_id}",
        )
    measurements = settings.get("measurements")
    if not isinstance(measurements, Mapping):
        raise AudioCompositionError(
            f"Source audio measurements are missing for {source.source_id}",
        )
    if status == "ready":
        peak_db = measurements.get("peak_db")
        if (
            isinstance(peak_db, bool)
            or not isinstance(peak_db, (int, float))
            or not math.isfinite(peak_db)
        ):
            raise AudioCompositionError(
                f"Source audio peak measurement is invalid for {source.source_id}",
            )
        try:
            linear_peak = math.pow(10.0, peak_db / 20.0)
        except OverflowError as error:
            raise AudioCompositionError(
                f"Source audio peak measurement is out of range for {source.source_id}",
            ) from error
        if not math.isfinite(linear_peak):
            raise AudioCompositionError(
                f"Source audio peak measurement is out of range for {source.source_id}",
            )


def _peak_linear(settings: Mapping[str, Any]) -> float | None:
    measurements = settings.get("measurements")
    if not isinstance(measurements, Mapping):
        return None
    peak_db = measurements.get("peak_db")
    if not isinstance(peak_db, (int, float)) or isinstance(peak_db, bool):
        return None
    numeric_peak_db = float(peak_db)
    if not math.isfinite(numeric_peak_db):
        return None
    return math.pow(10.0, numeric_peak_db / 20.0)


def _row_abs_sums(layout: AudioLayout | None, pan_percent: float) -> tuple[float, float]:
    if layout is None:
        return 0.0, 0.0
    left_balance, right_balance = _balance_factors(pan_percent)
    if layout == "mono":
        left, right = _mono_coefficients(pan_percent)
        return abs(left), abs(right)
    if layout == "stereo":
        return abs(left_balance), abs(right_balance)
    shared = 0.7071067811865475
    base = 1.0 + shared + 0.5 + shared
    return base * abs(left_balance), base * abs(right_balance)


def _mono_coefficients(pan_percent: float) -> tuple[float, float]:
    p = max(-1.0, min(1.0, pan_percent / 100.0))
    theta = (p + 1.0) * math.pi / 4.0
    return math.cos(theta), math.sin(theta)


def _balance_factors(pan_percent: float) -> tuple[float, float]:
    p = max(-1.0, min(1.0, pan_percent / 100.0))
    if p < 0:
        return 1.0, 1.0 + p
    if p > 0:
        return 1.0 - p, 1.0
    return 1.0, 1.0


def _render_command(
    project: Project,
    plan: AudioPlan,
    partial: Path,
    ffmpeg_path: str,
    *,
    reuse_inputs: bool = True,
) -> tuple[list[str], str]:
    input_paths: list[Path] = []
    input_indexes: dict[Path, int] = {}
    input_uses: list[int] = []
    block_inputs: list[list[int]] = []
    for interval in plan.intervals:
        interval_inputs: list[int] = []
        for block in interval.audible_blocks:
            path = Path(project.source_by_id(block.source_id).path)
            if reuse_inputs and path in input_indexes:
                input_index = input_indexes[path]
            else:
                input_index = len(input_paths)
                input_paths.append(path)
                input_uses.append(0)
                if reuse_inputs:
                    input_indexes[path] = input_index
            input_uses[input_index] += 1
            interval_inputs.append(input_index)
        block_inputs.append(interval_inputs)

    filters: list[str] = []
    split_refs: dict[int, deque[str]] = {}
    for input_index, uses in enumerate(input_uses):
        if uses < 2:
            continue
        split_labels = [f"in_{input_index}_{use}" for use in range(uses)]
        filters.append(
            f"[{input_index}:a:0]asplit={uses}" + "".join(f"[{label}]" for label in split_labels),
        )
        split_refs[input_index] = deque(f"[{label}]" for label in split_labels)

    interval_labels: list[str] = []
    for interval_index, interval in enumerate(plan.intervals):
        audio_blocks = interval.audible_blocks
        mapped_labels: list[str] = []
        for block_index, block in enumerate(audio_blocks):
            input_index = block_inputs[interval_index][block_index]
            if input_index in split_refs:
                input_ref = split_refs[input_index].popleft()
            else:
                input_ref = f"[{input_index}:a:0]"
            label = f"src_{interval_index}_{block_index}"
            legacy_center = (
                len(audio_blocks) == 1
                and block.pan_percent == 0.0
                and block.channel_layout in {"mono", "stereo"}
            )
            if legacy_center:
                source_filter = _legacy_center_source_filter(block)
                filters.append(
                    f"{input_ref}{source_filter},"
                    f"atrim=start_sample={block.source_start_sample}:"
                    f"end_sample={block.source_end_sample},"
                    f"apad=pad_len={interval.duration_samples},"
                    f"atrim=end_sample={interval.duration_samples},"
                    f"asetpts=PTS-STARTPTS[{label}]",
                )
            else:
                filters.append(
                    _composed_source_filter(
                        input_ref,
                        block,
                        label,
                        interval.duration_samples,
                    ),
                )
            mapped_labels.append(f"[{label}]")

        interval_label = f"interval_{interval_index}"
        if not mapped_labels:
            filters.append(
                f"anullsrc=r={plan.sample_rate}:cl=stereo,"
                f"atrim=end_sample={interval.duration_samples},"
                f"asetpts=PTS-STARTPTS[{interval_label}]",
            )
        elif len(mapped_labels) == 1:
            label = mapped_labels[0]
            block = audio_blocks[0]
            safety_bound = _safety_bound(block)
            if safety_bound is not None and safety_bound > 1.0:
                attenuation = min(1.0, PREENCODE_HEADROOM / safety_bound)
                filters.append(
                    f"{label}volume={_number(attenuation)},"
                    "alimiter=limit=0.90:level=false:latency=true,"
                    f"atrim=end_sample={interval.duration_samples},"
                    f"asetpts=PTS-STARTPTS[{interval_label}]",
                )
            else:
                filters.append(
                    f"{label}atrim=end_sample={interval.duration_samples},"
                    f"asetpts=PTS-STARTPTS[{interval_label}]",
                )
        else:
            p_bound = max(
                sum(block.effective_row_abs_sums[0] for block in audio_blocks),
                sum(block.effective_row_abs_sums[1] for block in audio_blocks),
            )
            mix_gain = 1.0 if p_bound <= 1.0 else min(1.0, PREENCODE_HEADROOM / p_bound)
            mix_label = f"mixed_{interval_index}"
            filters.append(
                f"{''.join(mapped_labels)}amix=inputs={len(mapped_labels)}:"
                f"duration=longest:dropout_transition=0:normalize=0[{mix_label}]",
            )
            filters.append(
                f"[{mix_label}]volume={_number(mix_gain)},"
                "alimiter=limit=0.90:level=false:latency=true,"
                f"atrim=end_sample={interval.duration_samples},"
                f"asetpts=PTS-STARTPTS[{interval_label}]",
            )
        interval_labels.append(f"[{interval_label}]")

    if not interval_labels:
        raise AudioRenderError("The audio plan contains no renderable samples")
    if len(interval_labels) == 1:
        joined = interval_labels[0]
    else:
        joined = f"{''.join(interval_labels)}concat=n={len(interval_labels)}:v=0:a=1[concatenated]"
        filters.append(joined)
        joined = "[concatenated]"
    filters.append(
        f"{joined}apad=pad_len={plan.final_sample_count},"
        f"atrim=end_sample={plan.final_sample_count},"
        f"aresample={plan.sample_rate}:async=0:first_pts=0,"
        f"asetpts=PTS-STARTPTS[final_audio]",
    )

    command = [
        ffmpeg_path,
        "-hide_banner",
        "-loglevel",
        "error",
        "-nostdin",
        "-y",
    ]
    for path in input_paths:
        command.extend(["-i", str(path)])
    command.extend(
        [
            "-filter_complex",
            ";".join(filters),
            "-map",
            "[final_audio]",
            "-c:a",
            "pcm_f32le",
            "-ar",
            str(plan.sample_rate),
            "-ac",
            str(plan.channels),
            "-f",
            "wav",
            str(partial),
        ],
    )
    return command, ";".join(filters)


def _legacy_center_source_filter(block: AudioBlockPlan) -> str:
    filters = [
        "aresample=48000:async=1:first_pts=0",
        "aformat=sample_rates=48000:channel_layouts=stereo",
    ]
    if abs(block.gain_db) > 0.0:
        filters.append(f"volume={block.gain_db:.12f}dB")
    filters.append("asetpts=PTS-STARTPTS")
    return ",".join(filters)


def _composed_source_filter(
    input_ref: str,
    block: AudioBlockPlan,
    label: str,
    interval_samples: int,
) -> str:
    filters = [
        f"{input_ref}aresample=48000:async=0:first_pts=0",
        f"atrim=start_sample={block.source_start_sample}:end_sample={block.source_end_sample}",
        "asetpts=PTS-STARTPTS",
    ]
    if abs(block.gain_db) > 0.0:
        filters.append(f"volume={block.gain_db:.12f}dB")
    filters.extend(
        [
            _pan_filter(block.channel_layout, block.pan_percent),
            f"apad=pad_len={interval_samples}",
            f"atrim=end_sample={interval_samples}",
            "asetpts=PTS-STARTPTS",
        ],
    )
    return ",".join(filters) + f"[{label}]"


def _pan_filter(layout: AudioLayout | None, pan_percent: float) -> str:
    if layout is None:
        raise AudioLayoutError("Cannot map audio without a channel layout")
    left_balance, right_balance = _balance_factors(pan_percent)
    if layout == "mono":
        left, right = _mono_coefficients(pan_percent)
        return f"pan=stereo|c0={_number(left)}*c0|c1={_number(right)}*c0"
    if layout == "stereo":
        return f"pan=stereo|c0={_number(left_balance)}*c0|c1={_number(right_balance)}*c1"
    rear_left = "c4"
    rear_right = "c5"
    left_terms = (
        f"{_number(left_balance)}*c0",
        f"{_number(left_balance * 0.7071067811865475)}*c2",
        f"{_number(left_balance * 0.5)}*c3",
        f"{_number(left_balance * 0.7071067811865475)}*{rear_left}",
    )
    right_terms = (
        f"{_number(right_balance)}*c1",
        f"{_number(right_balance * 0.7071067811865475)}*c2",
        f"{_number(right_balance * 0.5)}*c3",
        f"{_number(right_balance * 0.7071067811865475)}*{rear_right}",
    )
    return f"pan=stereo|c0={'+'.join(left_terms)}|c1={'+'.join(right_terms)}"


def _safety_bound(block: AudioBlockPlan) -> float | None:
    if block.peak_linear is None:
        return None
    return block.peak_linear * max(block.effective_row_abs_sums)


def _number(value: float) -> str:
    return f"{value:.12f}".rstrip("0").rstrip(".") or "0"


def _run_ffmpeg(
    command: list[str],
    filter_graph: str,
    *,
    cancel_event: threading.Event | None = None,
) -> None:
    try:
        run_managed_ffmpeg(
            command,
            cancel_event=cancel_event,
            stage="audio composition",
        )
    except FileNotFoundError as error:
        raise AudioRenderError(f"FFmpeg is unavailable: {command[0]}") from error
    except ExportExecutionError as error:
        if "cancel" in str(error).casefold():
            raise AudioRenderError("Export cancelled") from error
        raise AudioRenderError(f"FFmpeg audio render failed: {error}") from error
    if not filter_graph:
        raise AudioRenderError("Audio render graph was empty")


def _verify_pcm_output(
    output: Path,
    *,
    ffprobe_path: str,
    ffmpeg_path: str,
    expected_samples: int,
    cancel_event: threading.Event | None = None,
) -> tuple[int, float]:
    try:
        probe = run_command_with_cancellation(
            [
                ffprobe_path,
                "-hide_banner",
                "-v",
                "error",
                "-show_entries",
                "stream=codec_name,sample_rate,channels",
                "-of",
                "json",
                str(output),
            ],
            cancel_event=cancel_event,
            text=False,
        )
    except ExportExecutionError as error:
        if "cancel" in str(error).casefold():
            raise AudioRenderError("Export cancelled") from error
        raise AudioRenderError(f"ffprobe could not verify audio: {error}") from error
    except OSError as error:
        raise AudioRenderError(f"ffprobe is unavailable: {ffprobe_path}") from error
    if probe.returncode != 0:
        raise AudioRenderError(
            f"ffprobe could not verify audio: {probe.stderr.decode(errors='replace').strip()}",
        )
    try:
        streams = json.loads(probe.stdout.decode())["streams"]
        stream = streams[0]
        sample_rate = int(stream["sample_rate"])
        channels = int(stream["channels"])
    except (KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError) as error:
        raise AudioRenderError("ffprobe returned incomplete audio metadata") from error
    if sample_rate != AUDIO_SAMPLE_RATE or channels != AUDIO_CHANNELS:
        raise AudioRenderError("Rendered audio does not match the 48 kHz stereo contract")

    try:
        decoded = run_command_with_cancellation(
            [
                ffmpeg_path,
                "-hide_banner",
                "-loglevel",
                "error",
                "-nostdin",
                "-i",
                str(output),
                "-map",
                "0:a:0",
                "-f",
                "f32le",
                "-ar",
                str(AUDIO_SAMPLE_RATE),
                "-ac",
                str(AUDIO_CHANNELS),
                "pipe:1",
            ],
            cancel_event=cancel_event,
            text=False,
        )
    except ExportExecutionError as error:
        if "cancel" in str(error).casefold():
            raise AudioRenderError("Export cancelled") from error
        raise AudioRenderError(f"Rendered audio could not be decoded: {error}") from error
    except OSError as error:
        raise AudioRenderError(f"FFmpeg is unavailable: {ffmpeg_path}") from error
    if decoded.returncode != 0:
        raise AudioRenderError(
            f"Rendered audio could not be decoded: "
            f"{decoded.stderr.decode(errors='replace').strip()}",
        )
    if len(decoded.stdout) % 4:
        raise AudioRenderError("Rendered PCM byte count is not float32 aligned")
    samples = array("f")
    samples.frombytes(decoded.stdout)
    sample_count = len(samples) // AUDIO_CHANNELS
    if sample_count != expected_samples:
        raise AudioRenderError(
            f"Rendered audio has {sample_count} samples; expected {expected_samples}",
        )
    if any(not math.isfinite(value) for value in samples):
        raise AudioRenderError("Rendered PCM contains a non-finite sample")
    peak = max((abs(value) for value in samples), default=0.0)
    if peak > 1.0 + 1e-6:
        raise AudioRenderError(f"Rendered PCM clips above unity: {peak:.9f}")
    return sample_count, peak
