from __future__ import annotations

import subprocess
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from .export_types import ExportExecutionError

_SAMPLE_WIDTH = 64
_SAMPLE_HEIGHT = 36
_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
_GRID_SCORE_THRESHOLD = 16.0


@dataclass(frozen=True)
class ArtifactGateResult:
    status: str
    raw_sample_count: int
    encoded_sample_count: int
    grid_detected: bool
    reason: str

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "raw_sample_count": self.raw_sample_count,
            "encoded_sample_count": self.encoded_sample_count,
            "grid_detected": self.grid_detected,
            "reason": self.reason,
        }


def _frame_size(width: int, height: int) -> int:
    return width * height * 3


def _luma(frame: bytes) -> list[int]:
    return [
        (frame[index] * 3 + frame[index + 1] * 6 + frame[index + 2]) // 10
        for index in range(0, len(frame), 3)
    ]


def _mean_difference(values: Sequence[int], stride: int) -> float:
    if len(values) <= stride:
        return 0.0
    return sum(
        abs(values[index] - values[index + stride]) for index in range(len(values) - stride)
    ) / (len(values) - stride)


def _grid_score(frame: bytes, width: int, height: int) -> float:
    values = _luma(frame)
    horizontal_adjacent = sum(
        abs(values[row * width + column] - values[row * width + column + 1])
        for row in range(height)
        for column in range(width - 1)
    ) / (height * (width - 1))
    vertical_adjacent = sum(
        abs(values[row * width + column] - values[(row + 1) * width + column])
        for row in range(height - 1)
        for column in range(width)
    ) / ((height - 1) * width)
    if horizontal_adjacent < 16.0 or vertical_adjacent < 16.0:
        return 0.0

    best_score = 0.0
    for period in range(2, min(width, height, 9)):
        horizontal_periodic = _mean_difference(values, period)
        vertical_periodic = sum(
            abs(values[row * width + column] - values[(row + period) * width + column])
            for row in range(height - period)
            for column in range(width)
        ) / ((height - period) * width)
        score = min(
            horizontal_adjacent / max(horizontal_periodic, 1.0),
            vertical_adjacent / max(vertical_periodic, 1.0),
        )
        best_score = max(best_score, score)
    return best_score


def _has_periodic_grid(
    raw_frames: Sequence[bytes],
    *,
    width: int,
    height: int,
) -> bool:
    scores = [
        _grid_score(frame, width, height)
        for frame in raw_frames
        if len(frame) == _frame_size(width, height)
    ]
    if not scores:
        return False
    detected = sum(score >= _GRID_SCORE_THRESHOLD for score in scores)
    return detected >= max(1, (len(scores) + 1) // 2)


def check_artifact_samples(
    raw_frames: Sequence[bytes],
    encoded_frames: Sequence[bytes],
    *,
    width: int = _SAMPLE_WIDTH,
    height: int = _SAMPLE_HEIGHT,
) -> ArtifactGateResult:
    expected_size = _frame_size(width, height)
    if not raw_frames or not encoded_frames:
        return ArtifactGateResult(
            status="rejected",
            raw_sample_count=len(raw_frames),
            encoded_sample_count=len(encoded_frames),
            grid_detected=False,
            reason="raw-frame and encoded-output samples are required",
        )
    if len(raw_frames) != len(encoded_frames):
        return ArtifactGateResult(
            status="rejected",
            raw_sample_count=len(raw_frames),
            encoded_sample_count=len(encoded_frames),
            grid_detected=False,
            reason="raw-frame and encoded-output sample counts differ",
        )
    if any(len(frame) != expected_size for frame in raw_frames):
        return ArtifactGateResult(
            status="rejected",
            raw_sample_count=len(raw_frames),
            encoded_sample_count=len(encoded_frames),
            grid_detected=False,
            reason="raw-frame sample has an unexpected size",
        )
    if any(not frame for frame in encoded_frames):
        return ArtifactGateResult(
            status="rejected",
            raw_sample_count=len(raw_frames),
            encoded_sample_count=len(encoded_frames),
            grid_detected=False,
            reason="encoded-output sample contains an empty frame",
        )
    grid_detected = _has_periodic_grid(raw_frames, width=width, height=height)
    if grid_detected:
        return ArtifactGateResult(
            status="rejected",
            raw_sample_count=len(raw_frames),
            encoded_sample_count=len(encoded_frames),
            grid_detected=True,
            reason="periodic grid artifact detected in raw-frame samples",
        )
    return ArtifactGateResult(
        status="passed",
        raw_sample_count=len(raw_frames),
        encoded_sample_count=len(encoded_frames),
        grid_detected=False,
        reason="raw-frame and encoded-output samples passed artifact checks",
    )


def _sample_indices(expected_frames: int, sample_count: int) -> tuple[int, ...]:
    if sample_count <= 1:
        return (0,)
    return tuple(
        round(index * (expected_frames - 1) / (sample_count - 1)) for index in range(sample_count)
    )


def _select_filter(indices: Sequence[int]) -> str:
    expression = "+".join(f"eq(n\\,{index})" for index in indices)
    return f"select='{expression}',scale={_SAMPLE_WIDTH}:{_SAMPLE_HEIGHT}:flags=area"


def _run_sample_command(
    command: list[str],
    *,
    label: str,
) -> bytes:
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            check=False,
        )
    except OSError as error:
        raise ExportExecutionError(
            f"Could not start FFmpeg for {label} artifact sampling"
        ) from error
    if result.returncode != 0:
        detail = result.stderr.decode(errors="replace").strip()
        raise ExportExecutionError(
            f"FFmpeg failed during {label} artifact sampling" + (f": {detail}" if detail else "")
        )
    return result.stdout


def _split_raw_frames(data: bytes, sample_count: int) -> tuple[bytes, ...]:
    size = _frame_size(_SAMPLE_WIDTH, _SAMPLE_HEIGHT)
    expected_size = size * sample_count
    if len(data) != expected_size:
        raise ExportExecutionError(
            "Raw-frame artifact sampling returned an unexpected number of bytes"
        )
    return tuple(data[index : index + size] for index in range(0, len(data), size))


def _split_png_frames(data: bytes) -> tuple[bytes, ...]:
    frames: list[bytes] = []
    start = 0
    while True:
        marker = data.find(_PNG_SIGNATURE, start)
        if marker < 0:
            break
        end = data.find(b"IEND", marker + len(_PNG_SIGNATURE))
        if end < 0:
            break
        frames.append(data[marker : end + 8])
        start = end + 8
    return tuple(frames)


def run_artifact_gate(
    candidate: Path,
    expected_frames: int,
    *,
    ffmpeg_path: str = "ffmpeg",
    label: str = "interpolation output",
    sample_count: int = 4,
) -> ArtifactGateResult:
    if expected_frames <= 0:
        raise ExportExecutionError("Artifact sampling requires a positive frame count")
    count = max(1, min(sample_count, expected_frames))
    indices = _sample_indices(expected_frames, count)
    select_filter = _select_filter(indices)
    common = [
        ffmpeg_path,
        "-hide_banner",
        "-loglevel",
        "error",
        "-nostdin",
        "-i",
        str(candidate),
        "-map",
        "0:v:0",
        "-vf",
        select_filter,
        "-frames:v",
        str(count),
    ]
    raw_data = _run_sample_command(
        common
        + [
            "-an",
            "-f",
            "rawvideo",
            "-pix_fmt",
            "rgb24",
            "pipe:1",
        ],
        label=label,
    )
    encoded_data = _run_sample_command(
        common
        + [
            "-an",
            "-c:v",
            "png",
            "-f",
            "image2pipe",
            "pipe:1",
        ],
        label=label,
    )
    raw_frames = _split_raw_frames(raw_data, count)
    encoded_frames = _split_png_frames(encoded_data)
    result = check_artifact_samples(raw_frames, encoded_frames)
    if result.status != "passed":
        raise ExportExecutionError(f"{label} artifact gate failed: {result.reason}")
    return result


__all__ = [
    "ArtifactGateResult",
    "check_artifact_samples",
    "run_artifact_gate",
]
