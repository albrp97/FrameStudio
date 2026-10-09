from __future__ import annotations

import array
import hashlib
import json
import math
import shlex
import shutil
import subprocess
import sys
import unittest
from collections.abc import Sequence
from fractions import Fraction
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, cast

from framestudio.composition import TriplicateGroup, VisualTransform
from framestudio.export_coordinator import _safe_name
from framestudio.export_types import ExportProgress
from framestudio.fps_policy import FrameRatePolicy, SourceRateDecision
from framestudio.interpolation import validate_interpolation_backend
from framestudio.media import probe_media
from framestudio.model import Project, Segment, SourceReference
from framestudio.model_timeline import SegmentTimeline, TimelineTrack
from framestudio.model_types import SCHEMA_VERSION
from framestudio.output_plan import (
    SOURCE_ONLY_OUTPUT_MODE,
    plan_project_outputs,
    set_output_selection,
)
from framestudio.persistence import save_project
from framestudio.source_outputs import (
    _source_output_execution_destination,
    plan_source_outputs,
    render_source_output,
)
from framestudio.upscale_policy import UpscalePolicy
from tests.test_editor_source_output_plan_functionality import _source_reference

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
FFMPEG = shutil.which("ffmpeg")
FFPROBE = shutil.which("ffprobe")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _run(command: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )


def _make_constant_source(
    path: Path,
    *,
    color: str,
    frame_rate: int | str,
    width: int,
    height: int,
    frequencies: tuple[int, int],
    duration: float = 1.2,
) -> None:
    assert FFMPEG is not None
    result = _run(
        [
            FFMPEG,
            "-hide_banner",
            "-loglevel",
            "error",
            "-nostdin",
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"color=c={color}:s={width}x{height}:r={frame_rate}:d={duration}",
            "-f",
            "lavfi",
            "-i",
            f"sine=frequency={frequencies[0]}:sample_rate=48000:duration={duration}",
            "-f",
            "lavfi",
            "-i",
            f"sine=frequency={frequencies[1]}:sample_rate=48000:duration={duration}",
            "-filter_complex",
            "[1:a][2:a]amerge=inputs=2[a]",
            "-map",
            "0:v:0",
            "-map",
            "[a]",
            "-t",
            str(duration),
            "-c:v",
            "libx264",
            "-preset",
            "ultrafast",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-ar",
            "48000",
            "-ac",
            "2",
            str(path),
        ],
        cwd=REPOSITORY_ROOT,
    )
    if result.returncode != 0:
        raise AssertionError(f"Could not create {path.name}: {result.stderr}")


def _make_multicolor_source(path: Path) -> None:
    assert FFMPEG is not None
    colors = ("red", "blue", "yellow", "magenta")
    command = [
        FFMPEG,
        "-hide_banner",
        "-loglevel",
        "error",
        "-nostdin",
        "-y",
    ]
    for color in colors:
        command.extend(
            (
                "-f",
                "lavfi",
                "-i",
                f"color=c={color}:s=320x180:r=24:d=0.3",
            ),
        )
    command.extend(
        (
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=440:sample_rate=48000:duration=1.2",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=880:sample_rate=48000:duration=1.2",
            "-filter_complex",
            "[0:v][1:v][2:v][3:v]concat=n=4:v=1:a=0[v];[4:a][5:a]amerge=inputs=2[a]",
            "-map",
            "[v]",
            "-map",
            "[a]",
            "-t",
            "1.2",
            "-c:v",
            "libx264",
            "-preset",
            "ultrafast",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-ar",
            "48000",
            "-ac",
            "2",
            str(path),
        ),
    )
    result = _run(command, cwd=REPOSITORY_ROOT)
    if result.returncode != 0:
        raise AssertionError(f"Could not create {path.name}: {result.stderr}")


def _segment(
    source_id: str,
    segment_id: str,
    start: float,
    end: float,
    track_id: str,
    timeline_start: float,
    *,
    deleted: bool = False,
    zoom: float = 1.0,
    offset_x: float = 0.0,
    offset_y: float = 0.0,
    triplicate: bool = False,
) -> Segment:
    visual_transform = VisualTransform(
        zoom=zoom,
        offset_x=offset_x,
        offset_y=offset_y,
    )
    return Segment.create(
        start,
        end,
        segment_id=segment_id,
        block_id=f"block-{segment_id}",
        source_id=source_id,
        timeline_start_seconds=timeline_start,
        timeline_end_seconds=timeline_start + end - start,
        track_id=track_id,
        deleted=deleted,
        visual_transform=visual_transform,
        triplicate=TriplicateGroup.create(
            visual_transform,
            group_id=f"triplicate-{segment_id}",
        )
        if triplicate
        else None,
    )


def _build_source_output_project(
    project_id: str,
    sources: Sequence[SourceReference],
    paths: Sequence[Path],
    tracks: tuple[TimelineTrack, ...],
    active_track_id: str,
) -> tuple[Project, tuple[Path, ...]]:
    durations = {source.source_id: float(source.metadata["duration_seconds"]) for source in sources}
    timeline = SegmentTimeline.from_tracks(
        tracks,
        source_durations=durations,
        active_track_id=active_track_id,
    )
    project = Project(
        project_id=project_id,
        source=sources[0],
        duration_seconds=timeline.timeline_duration_seconds,
        schema_version=SCHEMA_VERSION,
        segment_timeline=timeline,
        sources=tuple(sources),
        source_settings={},
    )
    project.validate()
    set_output_selection(project, mode=SOURCE_ONLY_OUTPUT_MODE)
    return project, tuple(paths)


def _make_project(root: Path) -> tuple[Project, tuple[Path, ...]]:
    root.mkdir(parents=True, exist_ok=True)
    source_specs = (
        ("source-a", "a.mp4", "red", 24, 320, 180, (440, 880), True),
        ("source-b", "b.mp4", "blue", 30, 640, 360, (550, 1100), False),
        ("source-c", "c.mp4", "green", 12, 180, 320, (660, 1320), False),
        ("source-unused", "unused.mp4", "yellow", 24, 320, 180, (770, 1540), False),
    )
    sources: list[SourceReference] = []
    paths: list[Path] = []
    for source_id, name, color, rate, width, height, frequencies, multicolor in source_specs:
        path = root / name
        if multicolor:
            _make_multicolor_source(path)
        else:
            _make_constant_source(
                path,
                color=color,
                frame_rate=rate,
                width=width,
                height=height,
                frequencies=frequencies,
            )
        paths.append(path)
        sources.append(_source_reference(path, source_id))
    tracks = (
        TimelineTrack(
            "Track/One",
            (
                _segment(
                    "source-a", "a-first", 0.0, 0.2, "Track/One", 0.0, zoom=1.2, offset_x=20.0
                ),
                _segment("source-b", "b-first", 0.1, 0.3, "Track/One", 0.25),
                _segment(
                    "source-a",
                    "a-copy",
                    0.6,
                    0.8,
                    "Track/One",
                    0.5,
                    zoom=1.25,
                    offset_x=90.0,
                    offset_y=-30.0,
                    triplicate=True,
                ),
                _segment(
                    "source-b",
                    "b-excluded",
                    0.8,
                    1.0,
                    "Track/One",
                    0.75,
                    deleted=True,
                ),
            ),
        ),
        TimelineTrack(
            "Track:Two",
            (
                _segment("source-a", "a-second-track", 0.3, 0.5, "Track:Two", 0.0),
                _segment("source-c", "c-second-track", 0.1, 0.7, "Track:Two", 0.25),
            ),
        ),
        TimelineTrack(
            "Track Three",
            (_segment("source-b", "b-third-track", 0.5, 0.7, "Track Three", 0.0),),
        ),
        TimelineTrack(
            "Track-Four",
            (
                _segment("source-c", "c-fourth-track", 0.5, 1.1, "Track-Four", 0.0),
                _segment(
                    "source-unused",
                    "unused-excluded",
                    0.0,
                    0.2,
                    "Track-Four",
                    0.75,
                    deleted=True,
                ),
            ),
        ),
    )
    return _build_source_output_project(
        "ticket-113-functionality",
        sources,
        paths,
        tracks,
        active_track_id="Track/One",
    )


def _make_fractional_rve_project(root: Path) -> tuple[Project, tuple[Path, ...]]:
    root.mkdir(parents=True, exist_ok=True)
    source_specs = (
        ("fractional-low", "fractional-low.mp4", "red", "30000/1001", (330, 660)),
        ("fractional-high", "fractional-high.mp4", "blue", "60000/1001", (550, 1100)),
    )
    sources: list[SourceReference] = []
    paths: list[Path] = []
    for source_id, name, color, frame_rate, frequencies in source_specs:
        path = root / name
        _make_constant_source(
            path,
            color=color,
            frame_rate=frame_rate,
            width=320,
            height=180,
            frequencies=frequencies,
            duration=0.6,
        )
        paths.append(path)
        sources.append(_source_reference(path, source_id))
    durations = {source.source_id: float(source.metadata["duration_seconds"]) for source in sources}
    track_id = "Fractional/RVE"
    tracks = (
        TimelineTrack(
            track_id,
            (
                _segment(
                    "fractional-low",
                    "fractional-low-full",
                    0.0,
                    durations["fractional-low"],
                    track_id,
                    0.0,
                ),
                _segment(
                    "fractional-high",
                    "fractional-high-full",
                    0.0,
                    durations["fractional-high"],
                    track_id,
                    durations["fractional-low"],
                ),
            ),
        ),
    )
    return _build_source_output_project(
        "ticket-113-fractional-rve",
        sources,
        paths,
        tracks,
        active_track_id=track_id,
    )


def _saved_project(root: Path) -> tuple[Project, tuple[Path, ...], Path, Path]:
    project, source_paths = _make_project(root / "fixtures")
    project_path = root / "project.framestudio.json"
    published = root / "published"
    published.mkdir()
    save_project(project, project_path)
    return project, source_paths, project_path, published


def _run_export(
    project_path: Path,
    destination: Path,
    *,
    ffmpeg: str = "ffmpeg",
) -> subprocess.CompletedProcess[str]:
    assert FFPROBE is not None
    return _run(
        [
            sys.executable,
            str(REPOSITORY_ROOT / "framestudio.py"),
            "export",
            str(project_path),
            "--output",
            str(destination),
            "--fps-choice",
            "custom",
            "--custom-fps",
            "24",
            "--enhance-fps",
            "--fps-backend",
            "ffmpeg-minterpolate",
            "--no-upscale-enhancement",
            "--ffmpeg",
            ffmpeg,
            "--ffprobe",
            FFPROBE,
            "--full-paths",
        ],
        cwd=REPOSITORY_ROOT,
    )


def _result_payload(stdout: str) -> dict[str, object]:
    payloads = [
        cast(dict[str, Any], json.loads(line)) for line in stdout.splitlines() if line.strip()
    ]
    for payload in reversed(payloads):
        if payload.get("command") == "export" and payload.get("ok") is True:
            return payload
    raise AssertionError(f"No successful export payload in stdout: {stdout}")


def _frame_count(path: Path) -> int:
    assert FFPROBE is not None
    result = _run(
        [
            FFPROBE,
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-count_frames",
            "-show_entries",
            "stream=nb_read_frames",
            "-of",
            "default=nw=1:nk=1",
            str(path),
        ],
        cwd=REPOSITORY_ROOT,
    )
    if result.returncode != 0:
        raise AssertionError(result.stderr)
    return int(result.stdout.strip())


def _sample_rgb(path: Path, seconds: float, x: int, y: int) -> tuple[int, int, int]:
    assert FFMPEG is not None
    result = subprocess.run(
        [
            FFMPEG,
            "-hide_banner",
            "-loglevel",
            "error",
            "-nostdin",
            "-ss",
            f"{seconds:.3f}",
            "-i",
            str(path),
            "-frames:v",
            "1",
            "-vf",
            f"crop=2:2:{x}:{y}",
            "-pix_fmt",
            "rgb24",
            "-f",
            "rawvideo",
            "pipe:1",
        ],
        cwd=REPOSITORY_ROOT,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0 or len(result.stdout) < 3:
        raise AssertionError(result.stderr.decode(errors="replace"))
    data = result.stdout
    return data[0], data[1], data[2]


def _audio_samples(path: Path) -> tuple[list[float], list[float]]:
    assert FFMPEG is not None
    result = subprocess.run(
        [
            FFMPEG,
            "-hide_banner",
            "-loglevel",
            "error",
            "-nostdin",
            "-i",
            str(path),
            "-map",
            "0:a:0",
            "-t",
            "0.2",
            "-ac",
            "2",
            "-ar",
            "48000",
            "-f",
            "f32le",
            "pipe:1",
        ],
        cwd=REPOSITORY_ROOT,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise AssertionError(result.stderr.decode(errors="replace"))
    values = array.array("f")
    values.frombytes(result.stdout)
    channels = (list(values[0::2]), list(values[1::2]))
    return channels


def _frequency_score(samples: list[float], frequency: float, sample_rate: int = 48000) -> float:
    if len(samples) < 256:
        return 0.0
    samples = samples[128:]
    step = 2.0 * math.pi * frequency / sample_rate
    cosine = sum(value * math.cos(step * index) for index, value in enumerate(samples))
    sine = sum(value * math.sin(step * index) for index, value in enumerate(samples))
    return math.hypot(cosine, sine) / len(samples)


def _assert_stereo_tones(
    test_case: unittest.TestCase,
    path: Path,
    expected_tones: tuple[int, int],
    all_tones: tuple[int, ...],
) -> None:
    left, right = _audio_samples(path)
    left_scores = {tone: _frequency_score(left, tone) for tone in all_tones}
    right_scores = {tone: _frequency_score(right, tone) for tone in all_tones}
    expected_left, expected_right = expected_tones
    test_case.assertGreater(left_scores[expected_left], 0.001)
    test_case.assertGreater(right_scores[expected_right], 0.001)
    test_case.assertGreater(
        left_scores[expected_left],
        max(score for tone, score in left_scores.items() if tone != expected_left) * 1.5,
    )
    test_case.assertGreater(
        right_scores[expected_right],
        max(score for tone, score in right_scores.items() if tone != expected_right) * 1.5,
    )


class SourceOutputFunctionalityTests(unittest.TestCase):
    def setUp(self) -> None:
        if FFMPEG is None or FFPROBE is None:
            self.skipTest("FFmpeg and ffprobe are required for TICKET113 functionality")
        filters = _run([FFMPEG, "-hide_banner", "-filters"], cwd=REPOSITORY_ROOT)
        if "minterpolate" not in filters.stdout:
            self.skipTest("Required FFmpeg minterpolate filter is unavailable")

    def test_public_source_only_render_produces_stable_verified_reels(self):
        with TemporaryDirectory(
            dir=Path(__file__).resolve().parent,
            prefix=".ticket113-functionality-",
        ) as folder:
            root = Path(folder)
            project, source_paths, project_path, published = _saved_project(root)
            source_hashes = {path: _sha256(path) for path in source_paths}

            result = _run_export(project_path, published / "edited.mp4")

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = _result_payload(result.stdout)
            export = cast(dict[str, Any], payload["export"])
            self.assertTrue(export["verified"])
            self.assertFalse(export["partial_success"])
            self.assertNotIn("final", export)
            outputs = export["source_outputs"]
            self.assertEqual(len(outputs), 6)
            identities = [
                (item["identity"]["track_id"], item["identity"]["source_id"]) for item in outputs
            ]
            self.assertEqual(
                identities,
                [
                    ("Track/One", "source-a"),
                    ("Track/One", "source-b"),
                    ("Track:Two", "source-a"),
                    ("Track:Two", "source-c"),
                    ("Track Three", "source-b"),
                    ("Track-Four", "source-c"),
                ],
            )
            self.assertEqual(
                [item["request"]["segment_ids"] for item in outputs],
                [
                    ["a-first", "a-copy"],
                    ["b-first"],
                    ["a-second-track"],
                    ["c-second-track"],
                    ["b-third-track"],
                    ["c-fourth-track"],
                ],
            )
            active_plan = outputs[0]["plan"]["segments"]
            self.assertEqual(
                [segment["segment_id"] for segment in active_plan[:2]],
                ["a-first", "a-copy"],
            )
            self.assertEqual(active_plan[1]["visual_transform"]["zoom"], 1.25)
            self.assertIsNotNone(active_plan[1]["triplicate"])

            expected_durations = {
                ("Track/One", "source-a"): 0.4,
                ("Track/One", "source-b"): 0.2,
                ("Track:Two", "source-a"): 0.2,
                ("Track:Two", "source-c"): 0.6,
                ("Track Three", "source-b"): 0.2,
                ("Track-Four", "source-c"): 0.6,
            }
            expected_tones = {
                "source-a": (440, 880),
                "source-b": (550, 1100),
                "source-c": (660, 1320),
            }
            all_tones = tuple(tone for pair in expected_tones.values() for tone in pair)
            for item in outputs:
                identity = (
                    item["identity"]["track_id"],
                    item["identity"]["source_id"],
                )
                destination = Path(item["request"]["destination"])
                self.assertTrue(destination.is_file(), destination)
                media = probe_media(destination)
                self.assertEqual((media.width, media.height), (1920, 1080))
                self.assertEqual(media.frame_rate, "24/1")
                self.assertTrue(media.has_audio_stream)
                self.assertEqual(media.audio_channels, 2)
                self.assertAlmostEqual(
                    media.duration_seconds,
                    expected_durations[identity],
                    delta=0.12,
                )
                self.assertAlmostEqual(
                    _frame_count(destination),
                    round(expected_durations[identity] * 24),
                    delta=3,
                )
                _assert_stereo_tones(self, destination, expected_tones[identity[1]], all_tones)

            first_a = Path(outputs[0]["request"]["destination"])
            second_a = Path(outputs[2]["request"]["destination"])
            first_rgb = _sample_rgb(first_a, 0.05, 960, 540)
            copied_rgb = _sample_rgb(first_a, 0.30, 960, 540)
            second_track_rgb = _sample_rgb(second_a, 0.05, 960, 540)
            self.assertGreater(first_rgb[0], 150)
            self.assertLess(first_rgb[1], 100)
            self.assertLess(first_rgb[2], 100)
            self.assertGreater(copied_rgb[0], 150)
            self.assertGreater(copied_rgb[1], 150)
            self.assertLess(copied_rgb[2], 120)
            self.assertGreater(second_track_rgb[2], second_track_rgb[0] + 60)
            self.assertGreater(second_track_rgb[2], second_track_rgb[1] + 60)
            for x in (320, 960, 1600):
                triplicate_rgb = _sample_rgb(first_a, 0.30, x, 540)
                self.assertGreater(triplicate_rgb[0], 120)
                self.assertGreater(triplicate_rgb[1], 120)
                self.assertLess(triplicate_rgb[2], 140)

            self.assertEqual({path: _sha256(path) for path in source_paths}, source_hashes)
            self.assertEqual(
                len(list((published / "edited-sources").rglob("*.mp4"))),
                6,
            )

    def test_public_source_only_failure_reports_partial_success_and_no_failed_publish(self):
        with TemporaryDirectory(
            dir=Path(__file__).resolve().parent,
            prefix=".ticket113-functionality-",
        ) as folder:
            root = Path(folder)
            project, source_paths, project_path, published = _saved_project(root)
            output_base = published / "failed-run.mp4"
            source_plan = plan_project_outputs(project, output_base)
            failed_index = len(source_plan.source_outputs) - 1
            failed_request = source_plan.source_outputs[failed_index]
            candidate_destination = (
                root / "candidates" / f"{_safe_name(failed_request.identity, failed_index)}"
                f"{failed_request.destination.suffix}"
            )
            token = _source_output_execution_destination(candidate_destination).name
            wrapper = root / "fail-one-ffmpeg"
            real_ffmpeg = shlex.quote(FFMPEG or "ffmpeg")
            wrapper.write_text(
                "\n".join(
                    (
                        "#!/bin/sh",
                        "last=",
                        'for argument do last="$argument"; done',
                        f'case "$last" in *{shlex.quote(token)}*) exit 77 ;; esac',
                        f'exec {real_ffmpeg} "$@"',
                    ),
                )
                + "\n",
                encoding="utf-8",
            )
            wrapper.chmod(0o755)
            source_hashes = {path: _sha256(path) for path in source_paths}

            result = _run_export(
                project_path,
                output_base,
                ffmpeg=str(wrapper),
            )

            self.assertNotEqual(result.returncode, 0)
            error_lines = [
                json.loads(line) for line in result.stderr.splitlines() if line.startswith("{")
            ]
            self.assertTrue(error_lines, result.stderr)
            error = error_lines[-1]
            self.assertFalse(error["ok"])
            self.assertEqual(error["error"]["code"], "export_failed")
            details = error["error"]["details"]
            self.assertTrue(details["partial_success"])
            failed_outputs = [item for item in details["source_outputs"] if not item["verified"]]
            verified_outputs = [item for item in details["source_outputs"] if item["verified"]]
            self.assertEqual(len(failed_outputs), 1)
            self.assertEqual(len(verified_outputs), 5)
            failed_destination = Path(failed_outputs[0]["request"]["destination"])
            self.assertFalse(failed_destination.exists())
            for item in verified_outputs:
                self.assertTrue(Path(item["request"]["destination"]).is_file())
            self.assertEqual({path: _sha256(path) for path in source_paths}, source_hashes)

    def test_fractional_rve_source_outputs_use_real_backend_and_reuse_high_rate_source(self):
        target_rate = Fraction(60000, 1001)
        validation = validate_interpolation_backend(
            "rve-4.26",
            source_rate=Fraction(30000, 1001),
            target_rate=target_rate,
            ffmpeg_path=FFMPEG or "ffmpeg",
        )
        if not validation.available:
            self.skipTest(f"BLOCKED: configured RVE backend unavailable: {validation.reason}")

        with TemporaryDirectory(
            dir=Path(__file__).resolve().parent,
            prefix=".ticket113-rve-functionality-",
        ) as folder:
            root = Path(folder)
            project, source_paths = _make_fractional_rve_project(root / "fixtures")
            project_path = root / "fractional-rve.framestudio.json"
            save_project(project, project_path)
            self.assertTrue(project_path.is_file())
            source_hashes = {path: _sha256(path) for path in source_paths}

            output_root = root / "published"
            output_root.mkdir()
            output_plan = plan_project_outputs(
                project,
                output_root / "fractional.mp4",
                mode=SOURCE_ONLY_OUTPUT_MODE,
            )
            self.assertIsNone(output_plan.final_output)
            self.assertEqual(len(output_plan.source_outputs), 2)
            frame_rate_policy = FrameRatePolicy(
                choice="custom",
                custom_rate=target_rate,
                target_rate=target_rate,
                enhancement_enabled=True,
                backend="rve-4.26",
            )
            upscale_policy = UpscalePolicy(enhancement_enabled=False)
            plans = plan_source_outputs(
                project,
                output_plan.source_outputs,
                ffmpeg_path=FFMPEG or "ffmpeg",
                ffprobe_path=FFPROBE or "ffprobe",
                frame_rate_policy=frame_rate_policy,
                upscale_policy=upscale_policy,
            )
            plans_by_source = {plan.identity.source_id: plan for plan in plans}
            self.assertEqual(set(plans_by_source), {"fractional-low", "fractional-high"})
            low_plan = plans_by_source["fractional-low"]
            high_plan = plans_by_source["fractional-high"]
            self.assertEqual(low_plan.frame_rate_policy.target_rate, target_rate)
            self.assertEqual(high_plan.frame_rate_policy.target_rate, target_rate)
            self.assertEqual(low_plan.frame_rate_policy.backend, "rve-4.26")
            self.assertEqual(high_plan.frame_rate_policy.backend, "rve-4.26")
            self.assertEqual(low_plan.export_plan.route, "enhanced")
            self.assertNotEqual(high_plan.export_plan.route, "enhanced")
            low_rate_decision = low_plan.export_plan.rate_decisions[0]
            high_rate_decision = high_plan.export_plan.rate_decisions[0]
            self.assertEqual(
                low_rate_decision.action
                if isinstance(low_rate_decision, SourceRateDecision)
                else low_rate_decision["action"],
                "interpolate",
            )
            self.assertEqual(
                high_rate_decision.action
                if isinstance(high_rate_decision, SourceRateDecision)
                else high_rate_decision["action"],
                "passthrough",
            )
            self.assertEqual(len(low_plan.derived_project.sources or ()), 1)
            self.assertEqual(len(high_plan.derived_project.sources or ()), 1)

            stages_by_source: dict[str | None, list[str]] = {}
            results = []
            for plan in plans:
                stages: list[str] = []

                def record_progress(
                    progress: ExportProgress,
                    stage_log: list[str] = stages,
                ) -> None:
                    stage_log.append(progress.stage)

                result = render_source_output(
                    plan,
                    ffmpeg_path=FFMPEG or "ffmpeg",
                    ffprobe_path=FFPROBE or "ffprobe",
                    progress_callback=record_progress,
                )
                stages_by_source[plan.identity.source_id] = stages
                results.append(result)
                self.assertTrue(result.verified, result.error)
                self.assertIsNotNone(result.output_media)

            low_stages = stages_by_source["fractional-low"]
            high_stages = stages_by_source["fractional-high"]
            self.assertTrue(
                any(stage.startswith("interpolation") for stage in low_stages),
                low_stages,
            )
            self.assertFalse(
                any(stage.startswith("interpolation") for stage in high_stages),
                high_stages,
            )
            self.assertTrue(validation.artifact_status == "validated")

            expected_tones = {
                "fractional-low": (330, 660),
                "fractional-high": (550, 1100),
            }
            all_tones = tuple(tone for pair in expected_tones.values() for tone in pair)
            destinations = {result.identity.source_id: result.destination for result in results}
            for source_id, destination in destinations.items():
                if source_id is None:
                    self.fail("Source output result did not retain source identity")
                media = probe_media(destination)
                self.assertEqual((media.width, media.height), (1920, 1080))
                self.assertEqual(media.frame_rate, "60000/1001")
                self.assertAlmostEqual(media.duration_seconds, 0.6006, delta=0.03)
                self.assertTrue(media.has_audio_stream)
                self.assertEqual(media.audio_channels, 2)
                self.assertEqual(_frame_count(destination), 36)
                _assert_stereo_tones(self, destination, expected_tones[source_id], all_tones)

            low_rgb = _sample_rgb(destinations["fractional-low"], 0.2, 960, 540)
            high_rgb = _sample_rgb(destinations["fractional-high"], 0.2, 960, 540)
            self.assertGreater(low_rgb[0], low_rgb[2] + 60)
            self.assertGreater(high_rgb[2], high_rgb[0] + 60)
            self.assertEqual({path: _sha256(path) for path in source_paths}, source_hashes)


if __name__ == "__main__":
    unittest.main()
