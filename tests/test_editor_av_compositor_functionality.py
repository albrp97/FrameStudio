from __future__ import annotations

import importlib
import json
import math
import shutil
import subprocess
import unittest
from fractions import Fraction
from pathlib import Path

from framestudio.audio_compositor import AUDIO_SAMPLE_RATE, build_audio_plan
from framestudio.fps_policy import FrameRatePolicy
from framestudio.media import probe_media
from framestudio.model import Project
from framestudio.model_types import SCHEMA_VERSION
from framestudio.persistence import load_project, save_project
from framestudio.upscale_policy import UpscalePolicy
from framestudio.video_compositor import plan_project_video
from tests.test_editor_audio_compositor import _audio_settings as _create_audio_settings
from tests.test_editor_audio_compositor_functionality import (
    _decoded_pcm,
    _tone_amplitude,
)
from tests.test_editor_layout_plan_functionality import make_block
from tests.test_editor_video_compositor_functionality import (
    _decode_frame,
    _interval_index_for_frame,
    _make_marker_source,
    _marker_center,
    _mean_luma,
    _run,
    _scaled_region,
    _sha256,
    _white_centroid,
    isolated_directory,
)


def _require_av_compositor(test_case: unittest.TestCase):
    try:
        module = importlib.import_module("framestudio.av_compositor")
    except ModuleNotFoundError as error:
        if error.name == "framestudio.av_compositor":
            test_case.fail(
                "framestudio.av_compositor is not implemented; "
                "the TICKET-123 functionality boundary is intentionally red",
            )
        raise
    test_case.assertTrue(
        callable(getattr(module, "plan_project_av", None)),
        "framestudio.av_compositor.plan_project_av must be public",
    )
    test_case.assertTrue(
        callable(getattr(module, "render_project_av", None)),
        "framestudio.av_compositor.render_project_av must be public",
    )
    return module


def _make_av_source(
    root: Path,
    name: str,
    *,
    duration: float,
    color: str,
    frequency: int | None,
) -> Path:
    video = _make_marker_source(
        root,
        f".{name}-video.mp4",
        320,
        180,
        "10/1",
        color,
    )
    destination = root / f"{name}.mp4"
    if frequency is None:
        _run(
            [
                "ffmpeg",
                "-hide_banner",
                "-loglevel",
                "error",
                "-nostdin",
                "-y",
                "-i",
                str(video),
                "-t",
                str(duration),
                "-map",
                "0:v:0",
                "-an",
                "-c:v",
                "copy",
                "-movflags",
                "+faststart",
                str(destination),
            ],
        )
    else:
        _run(
            [
                "ffmpeg",
                "-hide_banner",
                "-loglevel",
                "error",
                "-nostdin",
                "-y",
                "-i",
                str(video),
                "-f",
                "lavfi",
                "-i",
                f"sine=frequency={frequency}:sample_rate={AUDIO_SAMPLE_RATE}:duration={duration}",
                "-filter:a",
                "volume=0.08",
                "-t",
                str(duration),
                "-map",
                "0:v:0",
                "-map",
                "1:a:0",
                "-c:v",
                "copy",
                "-c:a",
                "pcm_s16le",
                "-ar",
                str(AUDIO_SAMPLE_RATE),
                "-ac",
                "1",
                "-channel_layout",
                "mono",
                "-shortest",
                "-movflags",
                "+faststart",
                str(destination),
            ],
        )
    return destination


def _build_dynamic_project(root: Path) -> tuple[Project, tuple[Path, ...], dict[str, int]]:
    root.mkdir(parents=True, exist_ok=True)
    sources = (
        _make_av_source(
            root,
            "slot-a",
            duration=2.0,
            color="red",
            frequency=440,
        ),
        _make_av_source(
            root,
            "slot-b",
            duration=2.0,
            color="green",
            frequency=880,
        ),
        _make_av_source(
            root,
            "slot-c",
            duration=1.5,
            color="blue",
            frequency=1320,
        ),
        _make_av_source(
            root,
            "slot-d",
            duration=0.5,
            color="yellow",
            frequency=1760,
        ),
        _make_av_source(
            root,
            "slot-e",
            duration=0.5,
            color="magenta",
            frequency=2200,
        ),
        _make_av_source(
            root,
            "silent-visual",
            duration=0.5,
            color="cyan",
            frequency=None,
        ),
        _make_av_source(
            root,
            "slot-g",
            duration=0.5,
            color="orange",
            frequency=2640,
        ),
        _make_av_source(
            root,
            "unused-source",
            duration=1.0,
            color="white",
            frequency=3520,
        ),
    )
    source_metadata = []
    for path in sources:
        metadata = probe_media(path).metadata()
        if metadata["audio_channels"] == 1:
            metadata["audio_channel_layout"] = "mono"
        source_metadata.append((path, metadata))
    project = Project.create_synchronized_multi(
        tuple(source_metadata),
        project_id="ticket-123-av-functionality",
    )
    project.schema_version = SCHEMA_VERSION
    for track_id in ("track-2", "track-3", "track-4"):
        project.timeline.add_track(track_id)

    source_ids = tuple(source.source_id for source in project.sources or ())
    project.timeline.replace_track_blocks(
        "track-1",
        (
            make_block(
                segment_id="slot-a-block",
                source_id=source_ids[0],
                track_id="track-1",
                source_start=0.0,
                source_end=2.0,
                timeline_start=0.0,
                timeline_end=2.0,
            ),
            make_block(
                segment_id="silent-visual-block",
                source_id=source_ids[5],
                track_id="track-1",
                source_start=0.0,
                source_end=0.5,
                timeline_start=3.0,
                timeline_end=3.5,
            ),
            make_block(
                segment_id="slot-g-block",
                source_id=source_ids[6],
                track_id="track-1",
                source_start=0.0,
                source_end=0.5,
                timeline_start=3.5,
                timeline_end=4.0,
            ),
        ),
    )
    project.timeline.replace_track_blocks(
        "track-2",
        (
            make_block(
                segment_id="slot-b-block",
                source_id=source_ids[1],
                track_id="track-2",
                source_start=0.0,
                source_end=2.0,
                timeline_start=0.5,
                timeline_end=2.5,
            ),
        ),
    )
    project.timeline.replace_track_blocks(
        "track-3",
        (
            make_block(
                segment_id="slot-c-block",
                source_id=source_ids[2],
                track_id="track-3",
                source_start=0.0,
                source_end=1.5,
                timeline_start=1.0,
                timeline_end=2.5,
            ),
        ),
    )
    project.timeline.replace_track_blocks(
        "track-4",
        (
            make_block(
                segment_id="slot-d-block",
                source_id=source_ids[3],
                track_id="track-4",
                source_start=0.0,
                source_end=0.5,
                timeline_start=1.5,
                timeline_end=2.0,
            ),
            make_block(
                segment_id="slot-e-block",
                source_id=source_ids[4],
                track_id="track-4",
                source_start=0.0,
                source_end=0.5,
                timeline_start=2.0,
                timeline_end=2.5,
            ),
        ),
    )
    project.duration_seconds = project.timeline.timeline_duration_seconds
    for source in project.sources or ():
        metadata = source.metadata
        if metadata.get("audio_stream_present") is False:
            project.set_source_audio_settings(
                source.source_id,
                {
                    "status": "not-applicable",
                    "gain_db": 0.0,
                },
            )
        else:
            project.set_source_audio_settings(
                source.source_id,
                _create_audio_settings(
                    source,
                    peak_db=-20.0,
                    sample_count=round(
                        float(metadata["duration_seconds"]) * AUDIO_SAMPLE_RATE,
                    ),
                ),
            )
    project.validate()
    frequencies = {
        "slot-a-block": 440,
        "slot-b-block": 880,
        "slot-c-block": 1320,
        "slot-d-block": 1760,
        "slot-e-block": 2200,
        "slot-g-block": 2640,
    }
    return project, sources, frequencies


def _safe_frame_rate_policy(
    target_rate: Fraction = Fraction(10, 1),
) -> FrameRatePolicy:
    return FrameRatePolicy(
        choice="custom",
        target_rate=target_rate,
        custom_rate=target_rate,
        enhancement_enabled=False,
        backend="ffmpeg",
    )


def _make_audio_stage(source: Path, destination: Path) -> None:
    _run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-nostdin",
            "-y",
            "-i",
            str(source),
            "-map",
            "0:a:0",
            "-ar",
            str(AUDIO_SAMPLE_RATE),
            "-ac",
            "2",
            "-c:a",
            "pcm_f32le",
            str(destination),
        ],
    )


_AAC_FRAME_SAMPLES = 1024
_AAC_ENCODER_PRIMING_SAMPLES = 1024
_AAC_SAMPLE_COUNT_TOLERANCE = _AAC_ENCODER_PRIMING_SAMPLES + _AAC_FRAME_SAMPLES - 1


def _assert_pan_ratio(
    test_case: unittest.TestCase,
    samples: list[float],
    *,
    start_second: float,
    end_second: float,
    frequency: int,
    pan_percent: float,
) -> None:
    start_frame = round((start_second + 0.10) * AUDIO_SAMPLE_RATE)
    end_frame = round((end_second - 0.10) * AUDIO_SAMPLE_RATE)
    left = _tone_amplitude(
        samples,
        start_frame=start_frame,
        end_frame=end_frame,
        frequency=frequency,
        channel=0,
    )
    right = _tone_amplitude(
        samples,
        start_frame=start_frame,
        end_frame=end_frame,
        frequency=frequency,
        channel=1,
    )
    test_case.assertGreater(max(left, right), 0.001)
    if pan_percent == 0.0:
        test_case.assertAlmostEqual(left / right, 1.0, delta=0.15)
    elif pan_percent < 0.0:
        test_case.assertGreater(left, right)
        test_case.assertAlmostEqual(
            left / right,
            1.496606 if pan_percent == -25.0 else 2.414214,
            delta=0.15,
        )
    else:
        test_case.assertGreater(right, left)
        test_case.assertAlmostEqual(
            right / left,
            1.496606 if pan_percent == 25.0 else 2.414214,
            delta=0.18,
        )


@unittest.skipUnless(
    shutil.which("ffmpeg") and shutil.which("ffprobe"),
    "FFmpeg and ffprobe are required",
)
class AVCompositorFunctionalityTests(unittest.TestCase):
    def test_resume_rebuilds_shortened_mux_without_repeating_video_or_audio(self):
        from unittest.mock import patch

        from framestudio import av_compositor
        from framestudio.render_preparations import RenderPreparations

        with isolated_directory() as root:
            source = _make_av_source(root, "source", duration=1.0, color="red", frequency=440)
            original_hash = _sha256(source)
            metadata = {**probe_media(source).metadata(), "audio_channel_layout": "mono"}
            project = Project.create_synchronized(source, metadata)
            project.set_source_audio_settings(
                project.source.source_id, _create_audio_settings(project.source)
            )
            project.timeline.replace_track_blocks(
                "track-1",
                (
                    make_block(
                        segment_id="fractional-tail",
                        source_id=project.source.source_id,
                        track_id="track-1",
                        source_start=0.0,
                        source_end=0.994208,
                        timeline_start=0.0,
                        timeline_end=0.994208,
                    ),
                ),
            )
            project.duration_seconds = project.timeline.timeline_duration_seconds
            plan = av_compositor.plan_project_av(
                project,
                root / "resumed.mp4",
                frame_rate_policy=FrameRatePolicy(
                    choice="custom",
                    custom_rate=60,
                    target_rate=60,
                    enhancement_enabled=False,
                ),
                upscale_policy=UpscalePolicy(enhancement_enabled=False),
            )
            self.assertEqual(plan.video_plan.expected_frames, 60)
            self.assertEqual(plan.audio_plan.final_sample_count, 47722)
            original_run = av_compositor.run_ffmpeg

            def legacy_shortest_mux(command, **options):
                if options.get("stage") == "audio/video mux":
                    command = [*command[:-1], "-shortest", command[-1]]
                return original_run(command, **options)

            cache = root / "checkpoints"
            with (
                patch.object(av_compositor, "run_ffmpeg", side_effect=legacy_shortest_mux),
                self.assertRaisesRegex(
                    av_compositor.AVCompositorExecutionError, "59 frames; expected 60"
                ),
            ):
                av_compositor.render_project_av(plan, preparations=RenderPreparations(cache))
            self.assertFalse(plan.destination.exists())
            children = tuple(
                path
                for name in ("video-composition.mp4", "audio-composition.wav")
                for path in cache.rglob(name)
            )
            self.assertEqual(len(children), 2)
            proofs = {path: (_sha256(path), path.stat().st_mtime_ns) for path in children}
            with (
                patch.object(
                    av_compositor,
                    "render_project_video",
                    side_effect=AssertionError("Completed video must be reused"),
                ),
                patch.object(
                    av_compositor,
                    "render_audio",
                    side_effect=AssertionError("Completed audio must be reused"),
                ),
            ):
                result = av_compositor.render_project_av(
                    plan, preparations=RenderPreparations(cache)
                )
            self.assertEqual(result.actual_frames, 60)
            self.assertEqual(
                proofs, {path: (_sha256(path), path.stat().st_mtime_ns) for path in children}
            )
            self.assertGreater(_mean_luma(_decode_frame(plan.destination, 59)), 25)
            self.assertEqual(_sha256(source), original_hash)

    def test_controlled_fixture_builds_pcm_mp4_sources_and_ready_audio_plan(self):
        with isolated_directory() as root:
            project, sources, _ = _build_dynamic_project(root / "fixtures")
            self.assertEqual(len(sources), 8)
            self.assertEqual(
                tuple(
                    round(float(source.metadata["duration_seconds"]), 3)
                    for source in project.sources or ()
                ),
                (2.0, 2.0, 1.5, 0.5, 0.5, 0.5, 0.5, 1.0),
            )
            probed_durations = []
            for source in project.sources or ():
                metadata = probe_media(Path(source.path)).metadata()
                probed_durations.append(round(float(metadata["duration_seconds"]), 3))
                if metadata["audio_stream_present"]:
                    self.assertEqual(metadata["audio_codec"], "pcm_s16le")
                    self.assertEqual(metadata["audio_sample_rate"], AUDIO_SAMPLE_RATE)
                    self.assertEqual(metadata["audio_channels"], 1)
            self.assertEqual(
                tuple(probed_durations),
                (2.0, 2.0, 1.5, 0.5, 0.5, 0.5, 0.5, 1.0),
            )

            video_plan = plan_project_video(
                project,
                root / "fixture-video.mp4",
                frame_rate_policy=_safe_frame_rate_policy(),
                upscale_policy=UpscalePolicy(enhancement_enabled=False),
            )
            audio_plan = build_audio_plan(project, video_plan.layout_plan)
            self.assertEqual(video_plan.expected_frames, 40)
            self.assertEqual(audio_plan.sample_rate, AUDIO_SAMPLE_RATE)
            self.assertEqual(audio_plan.channels, 2)
            self.assertEqual(audio_plan.final_sample_count, 4 * AUDIO_SAMPLE_RATE)
            source_by_name = {Path(source.path).name: source for source in project.sources or ()}
            included_source_ids = {
                source.source_id
                for source in project.sources or ()
                if Path(source.path).name != "unused-source.mp4"
            }
            self.assertEqual(
                {source_plan.source_id for source_plan in audio_plan.source_plans},
                included_source_ids,
            )
            self.assertEqual(
                {
                    source_plan.source_id
                    for source_plan in audio_plan.source_plans
                    if source_plan.status == "not-applicable"
                },
                {source_by_name["silent-visual.mp4"].source_id},
            )
            self.assertTrue(
                all(
                    source_plan.status == "ready"
                    for source_plan in audio_plan.source_plans
                    if source_plan.source_id != source_by_name["silent-visual.mp4"].source_id
                ),
            )

    def test_final_mp4_uses_one_layout_for_exact_video_and_slot_audio(self):
        av = _require_av_compositor(self)
        with isolated_directory() as root:
            fixture_root = root / "fixtures"
            fixture_root.mkdir()
            project, sources, frequencies = _build_dynamic_project(fixture_root)
            destination = root / "layout-audio-final.mp4"
            source_hashes = {path.name: _sha256(path) for path in sources}
            project_path = fixture_root / "project.framestudio.json"
            save_project(project, project_path)

            plan = av.plan_project_av(
                load_project(project_path),
                destination,
                frame_rate_policy=_safe_frame_rate_policy(),
                upscale_policy=UpscalePolicy(enhancement_enabled=False),
            )
            self.assertEqual(plan.video_plan.target_rate, Fraction(10, 1))
            self.assertEqual(plan.video_plan.expected_frames, 40)
            self.assertEqual(plan.audio_plan.sample_rate, AUDIO_SAMPLE_RATE)
            self.assertEqual(plan.audio_plan.channels, 2)
            self.assertEqual(plan.audio_plan.final_sample_count, 4 * AUDIO_SAMPLE_RATE)
            self.assertEqual(
                tuple(
                    (interval.start_tick, interval.end_tick)
                    for interval in plan.video_plan.layout_plan.intervals
                ),
                tuple(
                    (interval.start_tick, interval.end_tick)
                    for interval in plan.audio_plan.intervals
                ),
            )
            self.assertEqual(
                tuple(
                    interval.active_block_ids for interval in plan.video_plan.layout_plan.intervals
                ),
                (
                    ("slot-a-block",),
                    ("slot-a-block", "slot-b-block"),
                    ("slot-a-block", "slot-b-block", "slot-c-block"),
                    (
                        "slot-a-block",
                        "slot-b-block",
                        "slot-c-block",
                        "slot-d-block",
                    ),
                    ("slot-b-block", "slot-c-block", "slot-e-block"),
                    (),
                    ("silent-visual-block",),
                    ("slot-g-block",),
                ),
            )

            result = av.render_project_av(plan)
            self.assertEqual(result.destination, destination)
            self.assertTrue(result.source_hashes_unchanged)

            probe = json.loads(
                subprocess.run(
                    [
                        "ffprobe",
                        "-hide_banner",
                        "-v",
                        "error",
                        "-show_streams",
                        "-show_format",
                        "-of",
                        "json",
                        str(destination),
                    ],
                    check=True,
                    text=True,
                    capture_output=True,
                ).stdout,
            )
            video_stream = next(
                stream for stream in probe["streams"] if stream["codec_type"] == "video"
            )
            audio_stream = next(
                stream for stream in probe["streams"] if stream["codec_type"] == "audio"
            )
            self.assertEqual(
                (int(video_stream["width"]), int(video_stream["height"])),
                (1920, 1080),
            )
            self.assertEqual(Fraction(video_stream["r_frame_rate"]), Fraction(10, 1))
            self.assertEqual(int(audio_stream["sample_rate"]), AUDIO_SAMPLE_RATE)
            self.assertEqual(int(audio_stream["channels"]), 2)

            from framestudio.export_process import probe_frame_count

            self.assertEqual(probe_frame_count(destination, "ffprobe"), 40)
            samples, sample_rate, channels = _decoded_pcm(destination)
            self.assertEqual(sample_rate, AUDIO_SAMPLE_RATE)
            self.assertEqual(channels, 2)
            self.assertLessEqual(
                abs(len(samples) // channels - 4 * AUDIO_SAMPLE_RATE),
                _AAC_SAMPLE_COUNT_TOLERANCE,
            )
            self.assertTrue(all(math.isfinite(value) for value in samples))
            self.assertLessEqual(max(abs(value) for value in samples), 1.0 + 1e-6)

            expected_interval_counts = (1, 2, 3, 4, 3, 0, 1, 1)
            for interval, start_frame, frame_count, expected_count in zip(
                plan.video_plan.layout_plan.intervals,
                plan.video_plan.frame_boundaries[:-1],
                plan.video_plan.interval_frame_counts,
                expected_interval_counts,
                strict=True,
            ):
                self.assertEqual(len(interval.active_blocks), expected_count)
                frame = start_frame + max(0, frame_count // 2)
                decoded = _decode_frame(destination, frame, width=64, height=36)
                if expected_count == 0:
                    self.assertLess(_mean_luma(decoded), 8.0)
                else:
                    self.assertGreater(_mean_luma(decoded), 3.0)

            expected_colors = {
                "slot-a-block": "red",
                "slot-b-block": "green",
                "slot-c-block": "blue",
                "slot-d-block": "yellow",
                "slot-e-block": "magenta",
                "silent-visual-block": "cyan",
                "slot-g-block": "orange",
            }
            transition_frames = {
                0,
                plan.video_plan.expected_frames - 1,
            }
            for boundary in plan.video_plan.frame_boundaries[1:-1]:
                transition_frames.update((boundary - 1, boundary))

            for frame_index in sorted(transition_frames):
                if not 0 <= frame_index < plan.video_plan.expected_frames:
                    continue
                interval_index = _interval_index_for_frame(
                    plan.video_plan,
                    frame_index,
                )
                interval = plan.video_plan.layout_plan.intervals[interval_index]
                frame = _decode_frame(destination, frame_index)
                if interval.is_black:
                    self.assertLess(_mean_luma(frame), 8.0)
                    continue
                for slot in interval.slots:
                    block_id = slot.block.block_id
                    self.assertIn(block_id, expected_colors)
                    crop = slot.crop
                    self.assertIsNotNone(crop)
                    assert crop is not None
                    region = _scaled_region(
                        crop.target.x,
                        crop.target.y,
                        crop.target.width,
                        crop.target.height,
                    )
                    expected_marker = _marker_center(crop)
                    expected_scaled = (
                        expected_marker[0] * 384 / 1920,
                        expected_marker[1] * 216 / 1080,
                    )
                    actual_marker = _white_centroid(frame, region)
                    self.assertAlmostEqual(
                        actual_marker[0],
                        expected_scaled[0],
                        delta=12.0,
                        msg=(
                            f"frame={frame_index} interval={interval_index} "
                            f"block={block_id} marker-x={actual_marker[0]} "
                            f"expected={expected_scaled[0]}"
                        ),
                    )
                    self.assertAlmostEqual(
                        actual_marker[1],
                        expected_scaled[1],
                        delta=12.0,
                        msg=(
                            f"frame={frame_index} interval={interval_index} "
                            f"block={block_id} marker-y={actual_marker[1]} "
                            f"expected={expected_scaled[1]}"
                        ),
                    )

                    x_start, y_start, x_end, y_end = region
                    sample_points = (
                        (
                            x_start + max(1, (x_end - x_start) // 6),
                            y_start + max(1, (y_end - y_start) // 6),
                        ),
                        (
                            x_end - max(2, (x_end - x_start) // 6),
                            y_start + max(1, (y_end - y_start) // 6),
                        ),
                        (
                            x_start + max(1, (x_end - x_start) // 6),
                            y_end - max(2, (y_end - y_start) // 6),
                        ),
                        (
                            x_end - max(2, (x_end - x_start) // 6),
                            y_end - max(2, (y_end - y_start) // 6),
                        ),
                    )
                    rgb_samples = []
                    for x, y in sample_points:
                        offset = (y * 384 + x) * 3
                        rgb_samples.append(frame[offset : offset + 3])
                    red = sum(sample[0] for sample in rgb_samples) / len(rgb_samples)
                    green = sum(sample[1] for sample in rgb_samples) / len(rgb_samples)
                    blue = sum(sample[2] for sample in rgb_samples) / len(rgb_samples)
                    color = expected_colors[block_id]
                    if color == "red":
                        self.assertGreater(red, green + 45)
                        self.assertGreater(red, blue + 45)
                    elif color == "green":
                        self.assertGreater(green, red + 25)
                        self.assertGreater(green, blue + 25)
                    elif color == "blue":
                        self.assertGreater(blue, red + 45)
                        self.assertGreater(blue, green + 45)
                    elif color == "yellow":
                        self.assertGreater(red, blue + 45)
                        self.assertGreater(green, blue + 45)
                    elif color == "magenta":
                        self.assertGreater(red, green + 45)
                        self.assertGreater(blue, green + 45)
                    elif color == "cyan":
                        self.assertGreater(green, red + 45)
                        self.assertGreater(blue, red + 45)
                    else:
                        self.assertGreater(red, green + 15)
                        self.assertGreater(red, blue + 45)

            _assert_pan_ratio(
                self,
                samples,
                start_second=0.0,
                end_second=0.5,
                frequency=frequencies["slot-a-block"],
                pan_percent=0.0,
            )
            _assert_pan_ratio(
                self,
                samples,
                start_second=0.5,
                end_second=1.0,
                frequency=frequencies["slot-a-block"],
                pan_percent=-25.0,
            )
            _assert_pan_ratio(
                self,
                samples,
                start_second=0.5,
                end_second=1.0,
                frequency=frequencies["slot-b-block"],
                pan_percent=25.0,
            )
            _assert_pan_ratio(
                self,
                samples,
                start_second=1.0,
                end_second=1.5,
                frequency=frequencies["slot-b-block"],
                pan_percent=0.0,
            )
            _assert_pan_ratio(
                self,
                samples,
                start_second=1.5,
                end_second=2.0,
                frequency=frequencies["slot-d-block"],
                pan_percent=50.0,
            )
            _assert_pan_ratio(
                self,
                samples,
                start_second=2.0,
                end_second=2.5,
                frequency=frequencies["slot-b-block"],
                pan_percent=-25.0,
            )
            _assert_pan_ratio(
                self,
                samples,
                start_second=2.0,
                end_second=2.5,
                frequency=frequencies["slot-c-block"],
                pan_percent=0.0,
            )
            _assert_pan_ratio(
                self,
                samples,
                start_second=2.0,
                end_second=2.5,
                frequency=frequencies["slot-e-block"],
                pan_percent=25.0,
            )
            gap_start = round(2.60 * AUDIO_SAMPLE_RATE) * 2
            gap_end = round(2.90 * AUDIO_SAMPLE_RATE) * 2
            self.assertLess(max(abs(value) for value in samples[gap_start:gap_end]), 0.005)
            silent_start = round(3.10 * AUDIO_SAMPLE_RATE) * 2
            silent_end = round(3.40 * AUDIO_SAMPLE_RATE) * 2
            self.assertLess(
                max(abs(value) for value in samples[silent_start:silent_end]),
                0.005,
            )
            _assert_pan_ratio(
                self,
                samples,
                start_second=3.5,
                end_second=4.0,
                frequency=frequencies["slot-g-block"],
                pan_percent=0.0,
            )
            self.assertEqual(
                len(plan.audio_plan.intervals),
                len(plan.video_plan.layout_plan.intervals),
            )
            transition_guard_samples = max(
                _AAC_ENCODER_PRIMING_SAMPLES,
                round(0.02 * AUDIO_SAMPLE_RATE),
            )
            transition_window_samples = round(0.08 * AUDIO_SAMPLE_RATE)
            decoded_sample_count = len(samples) // channels
            for interval_index in range(1, len(plan.audio_plan.intervals)):
                left_audio = plan.audio_plan.intervals[interval_index - 1]
                right_audio = plan.audio_plan.intervals[interval_index]
                left_visual = plan.video_plan.layout_plan.intervals[interval_index - 1]
                right_visual = plan.video_plan.layout_plan.intervals[interval_index]
                self.assertEqual(left_audio.end_tick, right_audio.start_tick)
                self.assertEqual(left_audio.end_tick, left_visual.end_tick)
                self.assertEqual(right_audio.start_tick, right_visual.start_tick)
                boundary_sample = left_audio.end_sample
                left_width = min(
                    transition_window_samples,
                    max(1, (left_audio.duration_samples - transition_guard_samples) // 3),
                )
                right_width = min(
                    transition_window_samples,
                    max(1, (right_audio.duration_samples - transition_guard_samples) // 3),
                )
                left_window = (
                    boundary_sample - transition_guard_samples - left_width,
                    boundary_sample - transition_guard_samples,
                )
                right_window = (
                    boundary_sample + transition_guard_samples,
                    boundary_sample + transition_guard_samples + right_width,
                )
                self.assertGreaterEqual(
                    left_window[0],
                    _AAC_ENCODER_PRIMING_SAMPLES,
                )
                self.assertLess(right_window[1], decoded_sample_count)
                for audio_interval, visual_interval, window in (
                    (left_audio, left_visual, left_window),
                    (right_audio, right_visual, right_window),
                ):
                    visual_block_ids = {block.block_id for block in visual_interval.active_blocks}
                    for audio_block in audio_interval.audible_blocks:
                        self.assertIn(audio_block.segment_id, visual_block_ids)
                        amplitude = _tone_amplitude(
                            samples,
                            start_frame=window[0],
                            end_frame=window[1],
                            frequency=frequencies[audio_block.segment_id],
                            channel=0,
                        )
                        self.assertGreater(
                            amplitude,
                            0.001,
                            msg=(
                                f"transition={interval_index} "
                                f"block={audio_block.segment_id} "
                                f"window={window} amplitude={amplitude}"
                            ),
                        )

            self.assertEqual(
                {path.name: _sha256(path) for path in sources},
                source_hashes,
            )

    def test_public_combined_render_preserves_fractional_rate_quantization(self):
        av = _require_av_compositor(self)
        with isolated_directory() as root:
            project, _, _ = _build_dynamic_project(root / "fixtures")
            source_ids = tuple(source.source_id for source in project.sources or ())
            boundary_ticks = (0, 250_250, 500_500, 750_750, 1_001_000)
            blocks = tuple(
                make_block(
                    segment_id=f"fractional-{index}",
                    source_id=source_ids[index],
                    track_id="track-1",
                    source_start=0.0,
                    source_end=(end_tick - start_tick) / 1_000_000,
                    timeline_start=start_tick / 1_000_000,
                    timeline_end=end_tick / 1_000_000,
                )
                for index, (start_tick, end_tick) in enumerate(
                    zip(boundary_ticks[:-1], boundary_ticks[1:], strict=True),
                )
            )
            project.timeline.replace_track_blocks("track-1", blocks)
            for track_id in ("track-2", "track-3", "track-4"):
                project.timeline.replace_track_blocks(track_id, ())
            project.duration_seconds = boundary_ticks[-1] / 1_000_000
            project.validate()

            target_rate = Fraction(30_000, 1_001)
            destination = root / "fractional-rate-final.mp4"
            plan = av.plan_project_av(
                project,
                destination,
                frame_rate_policy=_safe_frame_rate_policy(target_rate),
                upscale_policy=UpscalePolicy(enhancement_enabled=False),
            )

            def round_half_up(value: Fraction) -> int:
                return (value.numerator * 2 + value.denominator) // (2 * value.denominator)

            expected_frame_boundaries = tuple(
                round_half_up(Fraction(tick, 1_000_000) * target_rate) for tick in boundary_ticks
            )
            expected_sample_boundaries = tuple(
                round_half_up(Fraction(tick * AUDIO_SAMPLE_RATE, 1_000_000))
                for tick in boundary_ticks
            )
            expected_frame_counts = tuple(
                right - left
                for left, right in zip(
                    expected_frame_boundaries[:-1],
                    expected_frame_boundaries[1:],
                    strict=True,
                )
            )
            expected_frames = expected_frame_boundaries[-1]
            expected_audio_samples = expected_sample_boundaries[-1]
            self.assertEqual(
                plan.video_plan.layout_plan.boundaries,
                boundary_ticks,
            )
            self.assertEqual(
                plan.video_plan.frame_boundaries,
                expected_frame_boundaries,
            )
            self.assertEqual(plan.video_plan.interval_frame_counts, expected_frame_counts)
            self.assertEqual(plan.video_plan.expected_frames, expected_frames)
            self.assertEqual(
                plan.audio_plan.final_sample_count,
                expected_audio_samples,
            )

            result = av.render_project_av(plan)
            self.assertEqual(result.actual_frames, expected_frames)
            self.assertEqual(result.expected_frames, expected_frames)
            self.assertEqual(
                probe_media(destination).metadata()["audio_codec"],
                "aac",
            )
            from framestudio.export_process import probe_frame_count

            self.assertEqual(probe_frame_count(destination, "ffprobe"), expected_frames)
            samples, sample_rate, channels = _decoded_pcm(destination)
            self.assertEqual(sample_rate, AUDIO_SAMPLE_RATE)
            self.assertEqual(channels, 2)
            decoded_samples = len(samples) // channels
            self.assertLessEqual(
                abs(decoded_samples - expected_audio_samples),
                _AAC_SAMPLE_COUNT_TOLERANCE,
            )


if __name__ == "__main__":
    unittest.main()
