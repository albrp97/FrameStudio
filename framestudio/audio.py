from __future__ import annotations

import math
import subprocess
import threading
from array import array
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .model_types import SourceReference

AUDIO_POLICY_VERSION = "legacy-concat-v1"
TARGET_MEAN_RMS_DB = -35.0
TARGET_MEDIAN_DB = -50.0
TARGET_PEAK_DB = -1.0
AUDIO_MEDIAN_MIN_DB = -200.0
AUDIO_MEDIAN_MAX_DB = 20.0
AUDIO_MEDIAN_STEP_DB = 0.01
AUDIO_SAMPLE_RATE = 48000
AUDIO_CHANNELS = 2
_AUDIO_GAIN_THRESHOLD_DB = 0.01


class AudioAnalysisError(RuntimeError):
    """Raised when FFmpeg cannot produce source audio measurements."""


class AudioAnalysisCancelled(RuntimeError):
    """Raised when an in-progress audio analysis is superseded."""


@dataclass(frozen=True)
class AudioPolicy:
    version: str
    target_mean_rms_db: float
    target_median_db: float
    target_peak_db: float
    median_min_db: float
    median_max_db: float
    median_step_db: float
    sample_rate: int
    channels: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "target_mean_rms_db": self.target_mean_rms_db,
            "target_median_db": self.target_median_db,
            "target_peak_db": self.target_peak_db,
            "median_min_db": self.median_min_db,
            "median_max_db": self.median_max_db,
            "median_step_db": self.median_step_db,
            "sample_rate": self.sample_rate,
            "channels": self.channels,
        }


LEGACY_AUDIO_POLICY = AudioPolicy(
    version=AUDIO_POLICY_VERSION,
    target_mean_rms_db=TARGET_MEAN_RMS_DB,
    target_median_db=TARGET_MEDIAN_DB,
    target_peak_db=TARGET_PEAK_DB,
    median_min_db=AUDIO_MEDIAN_MIN_DB,
    median_max_db=AUDIO_MEDIAN_MAX_DB,
    median_step_db=AUDIO_MEDIAN_STEP_DB,
    sample_rate=AUDIO_SAMPLE_RATE,
    channels=AUDIO_CHANNELS,
)


@dataclass(frozen=True)
class AudioStats:
    peak_db: float
    mean_rms_db: float
    median_db: float
    sample_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "peak_db": _json_number(self.peak_db),
            "mean_rms_db": _json_number(self.mean_rms_db),
            "median_db": _json_number(self.median_db),
            "sample_count": self.sample_count,
        }


@dataclass(frozen=True)
class AudioDecision:
    status: str
    gain_db: float
    policy_version: str
    measurements: AudioStats | None
    source_fingerprint: dict[str, int]
    audio_metadata: dict[str, Any]
    diagnostic: str | None = None

    @property
    def requires_filter(self) -> bool:
        return self.status == "ready" and abs(self.gain_db) >= _AUDIO_GAIN_THRESHOLD_DB

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "gain_db": self.gain_db,
            "policy_version": self.policy_version,
            "measurements": (None if self.measurements is None else self.measurements.to_dict()),
            "source_fingerprint": dict(self.source_fingerprint),
            "audio": dict(self.audio_metadata),
            "diagnostic": self.diagnostic,
        }


def _json_number(value: float) -> float | None:
    return value if math.isfinite(value) else None


def _dbfs(value: float) -> float:
    if value <= 0:
        return -math.inf
    return 20.0 * math.log10(value)


def _source_fingerprint(source: SourceReference) -> dict[str, int]:
    return {
        "size_bytes": source.size_bytes,
        "modified_time_ns": source.modified_time_ns,
    }


def _audio_metadata(source: SourceReference) -> dict[str, Any]:
    metadata = source.metadata
    return {
        "codec": metadata.get("audio_codec"),
        "sample_rate": metadata.get("audio_sample_rate"),
        "channels": metadata.get("audio_channels"),
        "channel_layout": metadata.get("audio_channel_layout"),
    }


def _audio_present(source: SourceReference) -> bool:
    value = source.metadata.get("audio_stream_present")
    if value is None:
        return source.metadata.get("audio_codec") is not None
    return bool(value)


def _terminate_audio_analysis_process(process: subprocess.Popen[bytes]) -> None:
    try:
        process.terminate()
        process.wait(timeout=2)
    except ProcessLookupError:
        return
    except subprocess.TimeoutExpired:
        try:
            process.kill()
        except ProcessLookupError:
            return
        process.wait()


def analyze_audio(
    path: Path,
    *,
    ffmpeg_path: str = "ffmpeg",
    policy: AudioPolicy = LEGACY_AUDIO_POLICY,
    cancel_event: threading.Event | None = None,
) -> AudioStats:
    """Measure PCM samples using the legacy mean/median histogram algorithm."""
    if cancel_event is not None and cancel_event.is_set():
        raise AudioAnalysisCancelled("Audio analysis was cancelled")
    try:
        process = subprocess.Popen(
            [
                ffmpeg_path,
                "-hide_banner",
                "-v",
                "error",
                "-nostdin",
                "-i",
                str(Path(path).expanduser()),
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
    except FileNotFoundError as error:
        raise AudioAnalysisError(
            f"ffmpeg is not installed or not on PATH: {ffmpeg_path}"
        ) from error
    except OSError as error:
        raise AudioAnalysisError(f"Could not start FFmpeg audio analysis: {error}") from error

    histogram = [0] * (
        int((policy.median_max_db - policy.median_min_db) / policy.median_step_db) + 1
    )
    sample_count = 0
    sum_squares = 0.0
    peak = 0.0
    stderr_output = ""
    cancellation_stop = threading.Event()
    cancellation_watcher: threading.Thread | None = None

    if cancel_event is not None:

        def watch_cancellation() -> None:
            while not cancellation_stop.wait(0.05):
                if not cancel_event.is_set():
                    continue
                _terminate_audio_analysis_process(process)
                return

        cancellation_watcher = threading.Thread(
            target=watch_cancellation,
            name="framestudio-editor-audio-cancel",
            daemon=True,
        )
        cancellation_watcher.start()

    try:
        if process.stdout is None:
            raise AudioAnalysisError("FFmpeg audio analysis did not provide a sample pipe")
        while True:
            if cancel_event is not None and cancel_event.is_set():
                _terminate_audio_analysis_process(process)
                raise AudioAnalysisCancelled("Audio analysis was cancelled")
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
                    level = max(
                        policy.median_min_db,
                        min(policy.median_max_db, _dbfs(magnitude)),
                    )
                    bucket = round(
                        (level - policy.median_min_db) / policy.median_step_db,
                    )
                histogram[bucket] += 1
    except (OSError, ValueError) as error:
        if cancel_event is not None and cancel_event.is_set():
            raise AudioAnalysisCancelled("Audio analysis was cancelled") from error
        raise AudioAnalysisError(f"Could not read FFmpeg audio samples: {error}") from error
    finally:
        cancellation_stop.set()
        if cancellation_watcher is not None:
            cancellation_watcher.join(timeout=3)
        if process.stdout is not None:
            process.stdout.close()
        if process.stderr is not None:
            stderr_output = process.stderr.read().decode(errors="replace").strip()
            process.stderr.close()
        return_code = process.wait()
    if cancel_event is not None and cancel_event.is_set():
        raise AudioAnalysisCancelled("Audio analysis was cancelled")
    if return_code != 0:
        raise AudioAnalysisError(
            f"Audio analysis failed for {Path(path).name}: {stderr_output or 'ffmpeg failed'}"
        )
    if sample_count == 0:
        raise AudioAnalysisError(f"Audio analysis found no samples in {Path(path).name}")

    def percentile_bucket(index: int) -> int:
        total = 0
        for bucket, amount in enumerate(histogram):
            total += amount
            if total > index:
                return bucket
        return 0

    lower = percentile_bucket((sample_count - 1) // 2)
    upper = percentile_bucket(sample_count // 2)
    median_db = policy.median_min_db + ((lower + upper) / 2.0 * policy.median_step_db)
    return AudioStats(
        peak_db=_dbfs(peak),
        mean_rms_db=_dbfs(math.sqrt(sum_squares / sample_count)),
        median_db=median_db,
        sample_count=sample_count,
    )


def audio_gain_db(
    stats: AudioStats,
    *,
    policy: AudioPolicy = LEGACY_AUDIO_POLICY,
) -> float:
    if not math.isfinite(stats.peak_db):
        return 0.0
    mean_gain = policy.target_mean_rms_db - stats.mean_rms_db
    median_gain = policy.target_median_db - stats.median_db
    balanced_gain = (mean_gain + median_gain) / 2.0
    peak_limited_gain = policy.target_peak_db - stats.peak_db
    return min(balanced_gain, peak_limited_gain)


def pending_audio_decision(source: SourceReference) -> AudioDecision:
    return AudioDecision(
        status="pending",
        gain_db=0.0,
        policy_version=AUDIO_POLICY_VERSION,
        measurements=None,
        source_fingerprint=_source_fingerprint(source),
        audio_metadata=_audio_metadata(source),
        diagnostic="Source audio has not been analyzed",
    )


def _decision(
    source: SourceReference,
    *,
    status: str,
    gain_db: float = 0.0,
    measurements: AudioStats | None = None,
    diagnostic: str | None = None,
) -> AudioDecision:
    return AudioDecision(
        status=status,
        gain_db=gain_db,
        policy_version=AUDIO_POLICY_VERSION,
        measurements=measurements,
        source_fingerprint=_source_fingerprint(source),
        audio_metadata=_audio_metadata(source),
        diagnostic=diagnostic,
    )


def analyze_source_audio(
    source: SourceReference,
    *,
    ffmpeg_path: str = "ffmpeg",
    policy: AudioPolicy = LEGACY_AUDIO_POLICY,
    cancel_event: threading.Event | None = None,
) -> AudioDecision:
    if not _audio_present(source):
        return _decision(
            source,
            status="not-applicable",
            diagnostic="Source has no audio stream",
        )
    if source.metadata.get("audio_codec") is None:
        return _decision(
            source,
            status="unsupported",
            diagnostic="Audio stream codec metadata is unavailable",
        )
    try:
        stats = analyze_audio(
            Path(source.path),
            ffmpeg_path=ffmpeg_path,
            policy=policy,
            cancel_event=cancel_event,
        )
    except AudioAnalysisError as error:
        return _decision(
            source,
            status="failed",
            diagnostic=str(error),
        )
    if not math.isfinite(stats.peak_db) or stats.peak_db <= policy.median_min_db:
        return _decision(
            source,
            status="silent",
            measurements=stats,
            diagnostic="Source audio contains no measurable signal",
        )
    return _decision(
        source,
        status="ready",
        gain_db=audio_gain_db(stats, policy=policy),
        measurements=stats,
    )


def audio_decision_is_stale(
    source: SourceReference,
    settings: Mapping[str, Any] | None,
) -> bool:
    if not isinstance(settings, Mapping):
        return True
    raw_fingerprint = settings.get("source_fingerprint")
    if not isinstance(raw_fingerprint, Mapping):
        return True
    return (
        raw_fingerprint.get("size_bytes") != source.size_bytes
        or raw_fingerprint.get("modified_time_ns") != source.modified_time_ns
    )


def audio_filter(
    decision: AudioDecision | Mapping[str, Any] | None,
    *,
    policy: AudioPolicy = LEGACY_AUDIO_POLICY,
) -> str:
    gain = 0.0
    status = "not-applicable"
    if isinstance(decision, AudioDecision):
        gain = decision.gain_db
        status = decision.status
    elif isinstance(decision, Mapping):
        raw_gain = decision.get("gain_db")
        if isinstance(raw_gain, (int, float)) and not isinstance(raw_gain, bool):
            gain = float(raw_gain)
        raw_status = decision.get("status")
        if isinstance(raw_status, str):
            status = raw_status
    filters = [
        f"aresample={policy.sample_rate}:async=1:first_pts=0",
        f"aformat=sample_rates={policy.sample_rate}:channel_layouts=stereo",
    ]
    if status == "ready" and math.isfinite(gain) and abs(gain) >= _AUDIO_GAIN_THRESHOLD_DB:
        filters.append(f"volume={gain:.2f}dB")
    filters.append("asetpts=PTS-STARTPTS")
    return ",".join(filters)


def decision_summary(decision: AudioDecision | Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(decision, AudioDecision):
        return decision.to_dict()
    return dict(decision)
