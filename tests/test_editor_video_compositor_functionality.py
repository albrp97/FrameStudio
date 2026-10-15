from __future__ import annotations

import hashlib
import shutil
import subprocess
import unittest
from contextlib import contextmanager
from dataclasses import replace
from fractions import Fraction
from pathlib import Path
from unittest import mock

from framestudio import video_compositor
from framestudio.layout_plan import CropPlan, plan_triplicate
from framestudio.media import probe_media
from framestudio.model import Project, TriplicateGroup, VisualTransform
from framestudio.persistence import load_project, save_project
from framestudio.upscale_policy import UpscalePolicy
from framestudio.video_compositor import (
    VideoCompositorExecutionError,
    VideoCompositorPlanningError,
    VideoRenderPlan,
    plan_project_video,
    render_project_video,
)
from tests.test_editor_layout_plan_functionality import make_block


@contextmanager
def isolated_directory():
    with mock.patch("tempfile.gettempdir", return_value=str(Path(__file__).parent)):
        with __import__("tempfile").TemporaryDirectory(
            dir=Path(__file__).resolve().parent,
            prefix=".ticket121-video-",
        ) as raw_path:
            yield Path(raw_path)


class VideoCompositorFunctionalityTests(unittest.TestCase):
    def test_dynamic_sections_render_with_real_ffmpeg_and_preserve_sources(self):
        if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
            self.skipTest("FFmpeg and ffprobe are required")
        with isolated_directory() as root:
            fixture_root = root / "fixtures"
            fixture_root.mkdir()
            sources = (
                _make_marker_source(
                    fixture_root,
                    "portrait.mp4",
                    540,
                    960,
                    "30000/1001",
                    "red",
                ),
                _make_marker_source(
                    fixture_root,
                    "landscape.mp4",
                    960,
                    540,
                    "60000/1001",
                    "green",
                ),
                _make_marker_source(
                    fixture_root,
                    "ultrawide-sar.mp4",
                    1280,
                    480,
                    "30000/1001",
                    "blue",
                    sar="16/15",
                ),
                _make_marker_source(
                    fixture_root,
                    "square.mp4",
                    720,
                    720,
                    "60000/1001",
                    "yellow",
                ),
                _make_marker_source(
                    fixture_root,
                    "unused.mp4",
                    640,
                    360,
                    "30000/1001",
                    "magenta",
                ),
            )
            source_hashes = {path.name: _sha256(path) for path in sources}
            project = Project.create_synchronized_multi(
                tuple((path, probe_media(path).metadata()) for path in sources),
                project_id="ticket-121-functionality",
            )
            for track_id in ("track-2", "track-3", "track-4"):
                project.timeline.add_track(track_id)
            source_ids = tuple(source.source_id for source in project.sources or ())
            transform = VisualTransform(zoom=1.5, offset_x=120.0, offset_y=-80.0)
            triplicate = TriplicateGroup.create(transform, group_id="ticket-121-triplicate")
            project.timeline.replace_track_blocks(
                "track-1",
                (
                    make_block(
                        segment_id="portrait-a",
                        source_id=source_ids[0],
                        track_id="track-1",
                        source_start=0.0,
                        source_end=1.5,
                        timeline_start=0.5,
                        timeline_end=2.0,
                    ),
                    make_block(
                        segment_id="portrait-b",
                        source_id=source_ids[0],
                        track_id="track-1",
                        source_start=1.0,
                        source_end=1.5,
                        timeline_start=3.5,
                        timeline_end=4.0,
                    ),
                ),
            )
            project.timeline.replace_track_blocks(
                "track-2",
                (
                    make_block(
                        segment_id="landscape",
                        source_id=source_ids[1],
                        track_id="track-2",
                        source_start=0.0,
                        source_end=1.25,
                        timeline_start=1.0,
                        timeline_end=2.25,
                    ),
                ),
            )
            project.timeline.replace_track_blocks(
                "track-3",
                (
                    make_block(
                        segment_id="ultrawide-triplicate",
                        source_id=source_ids[2],
                        track_id="track-3",
                        source_start=0.0,
                        source_end=1.25,
                        timeline_start=1.25,
                        timeline_end=2.5,
                        visual_transform=transform,
                        triplicate=triplicate,
                    ),
                ),
            )
            project.timeline.replace_track_blocks(
                "track-4",
                (
                    make_block(
                        segment_id="square",
                        source_id=source_ids[3],
                        track_id="track-4",
                        source_start=0.0,
                        source_end=1.5,
                        timeline_start=1.5,
                        timeline_end=3.0,
                    ),
                    make_block(
                        segment_id="excluded-tail",
                        source_id=source_ids[3],
                        track_id="track-4",
                        source_start=1.0,
                        source_end=1.5,
                        timeline_start=4.0,
                        timeline_end=4.5,
                        deleted=True,
                    ),
                ),
            )
            project.duration_seconds = project.timeline.timeline_duration_seconds
            project.validate()

            project_path = fixture_root / "persisted-project.framestudio.json"
            save_project(project, project_path)
            reopened = load_project(project_path)
            destination = root / "dynamic-render.mp4"

            plan = plan_project_video(
                reopened,
                destination,
                target_rate=Fraction(60_000, 1_001),
            )
            self.assertEqual(
                tuple(interval.active_block_ids for interval in plan.layout_plan.intervals),
                (
                    (),
                    ("portrait-a",),
                    ("portrait-a", "landscape"),
                    ("portrait-a", "landscape", "ultrawide-triplicate"),
                    ("portrait-a", "landscape", "ultrawide-triplicate", "square"),
                    ("landscape", "ultrawide-triplicate", "square"),
                    ("ultrawide-triplicate", "square"),
                    ("square",),
                    (),
                    ("portrait-b",),
                ),
            )
            self.assertEqual(
                tuple(
                    slot.triplicate_crops[0].target.width
                    for slot in plan.layout_plan.intervals[3].slots
                    if slot.is_triplicate
                ),
                (213,),
            )
            self.assertEqual(
                next(
                    item for item in plan.probed_metadata if item.source_id == source_ids[2]
                ).sample_aspect_ratio,
                (16, 15),
            )
            self.assertNotIn("excluded-tail", plan.layout_plan.included_blocks)
            self.assertEqual(sum(plan.interval_frame_counts), plan.expected_frames)
            self.assertEqual(
                {len(interval.active_blocks) for interval in plan.layout_plan.intervals},
                {0, 1, 2, 3, 4},
            )
            routes = {route.source_id: route for route in plan.processing_routes}
            self.assertEqual(routes[source_ids[0]].fps_action, "interpolate")
            self.assertEqual(routes[source_ids[1]].fps_action, "passthrough")
            self.assertEqual(routes[source_ids[2]].fps_action, "interpolate")
            self.assertEqual(routes[source_ids[3]].fps_action, "passthrough")
            self.assertNotIn(source_ids[4], routes)
            self.assertNotIn(source_ids[4], {probe.source_id for probe in plan.probed_metadata})
            self.assertFalse(routes[source_ids[3]].upscale_requested)
            for route in routes.values():
                if route.upscale_requested and route.upscale_status == "unavailable":
                    self.assertTrue(route.upscale_reason)

            renderable_block_ids = {
                slot.block.block_id
                for interval, frame_count in zip(
                    plan.layout_plan.intervals,
                    plan.interval_frame_counts,
                    strict=True,
                )
                if frame_count > 0
                for slot in interval.slots
            }
            expected_restore_calls = sum(
                route.upscale_status == "available"
                for block in plan.layout_plan.included_blocks
                if block.block_id in renderable_block_ids
                for route in (routes[block.source_id],)
                if route.upscale_requested
            )
            expected_interpolation_calls = sum(
                route.fps_action == "interpolate"
                for block in plan.layout_plan.included_blocks
                if block.block_id in renderable_block_ids
                for route in (routes[block.source_id],)
            )

            with (
                mock.patch(
                    "framestudio.video_compositor._run_rve_restoration",
                    wraps=video_compositor._run_rve_restoration,
                ) as restoration,
                mock.patch(
                    "framestudio.video_compositor.run_source_interpolation",
                    wraps=video_compositor.run_source_interpolation,
                ) as interpolation,
                mock.patch(
                    "framestudio.video_compositor._extract_block",
                    wraps=video_compositor._extract_block,
                ) as extraction,
            ):
                result = render_project_video(plan)

            self.assertEqual(restoration.call_count, expected_restore_calls)
            self.assertEqual(interpolation.call_count, expected_interpolation_calls)
            self.assertEqual(expected_interpolation_calls, 3)
            if all(routes[source_id].upscale_status == "available" for source_id in source_ids[:3]):
                self.assertEqual(expected_restore_calls, 4)
            prepared_sources = {Path(call.args[0]).name for call in extraction.call_args_list}
            self.assertNotIn("unused.mp4", prepared_sources)
            self.assertNotIn("square.mp4", prepared_sources)
            self.assertNotIn("fake-ai", " ".join(result.processing_fallbacks).lower())

            self.assertEqual(result.destination, destination)
            self.assertEqual(result.output_probe.path, destination)
            self.assertEqual((result.output_probe.width, result.output_probe.height), (1920, 1080))
            self.assertEqual(
                Fraction(result.output_probe.frame_rate),
                Fraction(60_000, 1_001),
            )
            self.assertFalse(result.output_probe.has_audio_stream)
            self.assertEqual(result.actual_frames, plan.expected_frames)
            self.assertTrue(result.source_hashes_unchanged)
            self.assertEqual(
                {path.name: _sha256(path) for path in sources},
                source_hashes,
            )
            self.assertTrue(destination.is_file())

            with self.assertRaises(VideoCompositorPlanningError):
                plan_project_video(reopened, sources[0])
            altered_plan = replace(plan, destination=sources[4])
            with self.assertRaises(VideoCompositorExecutionError):
                render_project_video(altered_plan)
            self.assertEqual(
                {path.name: _sha256(path) for path in sources},
                source_hashes,
            )

            tiny_project = Project.create_synchronized(
                sources[3],
                probe_media(sources[3]).metadata(),
                project_id="ticket-121-tiny-boundary",
            )
            tiny_source_id = tiny_project.source.source_id
            tiny_project.timeline.replace_track_blocks(
                "track-1",
                (
                    make_block(
                        segment_id="tiny-a",
                        source_id=tiny_source_id,
                        track_id="track-1",
                        source_start=0.0,
                        source_end=0.5,
                        timeline_start=0.0,
                        timeline_end=0.5,
                    ),
                    make_block(
                        segment_id="tiny-b",
                        source_id=tiny_source_id,
                        track_id="track-1",
                        source_start=0.5,
                        source_end=0.75,
                        timeline_start=1.0,
                        timeline_end=1.25,
                    ),
                    make_block(
                        segment_id="tiny-c",
                        source_id=tiny_source_id,
                        track_id="track-1",
                        source_start=0.75,
                        source_end=1.0,
                        timeline_start=1.250001,
                        timeline_end=1.500001,
                    ),
                ),
            )
            tiny_project.duration_seconds = tiny_project.timeline.timeline_duration_seconds
            tiny_project.validate()
            tiny_destination = root / "tiny-boundary-render.mp4"
            tiny_plan = plan_project_video(
                tiny_project,
                tiny_destination,
                target_rate=Fraction(60_000, 1_001),
                upscale_policy=UpscalePolicy(enhancement_enabled=False),
            )
            self.assertEqual(
                tuple(interval.active_block_ids for interval in tiny_plan.layout_plan.intervals),
                (("tiny-a",), (), ("tiny-b",), (), ("tiny-c",)),
            )
            self.assertEqual(tiny_plan.interval_frame_counts, (30, 30, 15, 0, 15))
            self.assertEqual(tiny_plan.expected_frames, 90)
            tiny_result = render_project_video(tiny_plan)
            self.assertEqual(tiny_result.actual_frames, 90)
            self.assertEqual(tiny_result.expected_frames, 90)
            self.assertLess(_mean_luma(_decode_small_frame(tiny_destination, 30)), 8.0)
            self.assertGreater(_mean_luma(_decode_small_frame(tiny_destination, 60)), 25.0)
            self.assertEqual(
                {path.name: _sha256(path) for path in sources},
                source_hashes,
            )

            decoded: dict[int, bytes] = {}

            def frame_at(frame_index: int) -> bytes:
                if frame_index not in decoded:
                    decoded[frame_index] = _decode_frame(destination, frame_index)
                return decoded[frame_index]

            for boundary in plan.frame_boundaries[1:-1]:
                for frame_index in (boundary - 1, boundary):
                    if not 0 <= frame_index < plan.expected_frames:
                        continue
                    interval_index = _interval_index_for_frame(plan, frame_index)
                    interval = plan.layout_plan.intervals[interval_index]
                    frame = frame_at(frame_index)
                    if interval.is_black:
                        self.assertLess(_mean_luma(frame), 8.0)
                        continue
                    for slot in interval.slots:
                        crops = slot.triplicate_crops if slot.triplicate_crops else (slot.crop,)
                        for crop in crops:
                            self.assertIsNotNone(crop)
                            assert crop is not None
                            expected = _marker_center(crop)
                            expected_scaled = (
                                expected[0] * 384 / 1920,
                                expected[1] * 216 / 1080,
                            )
                            actual = _white_centroid(
                                frame,
                                _scaled_region(
                                    crop.target.x,
                                    crop.target.y,
                                    crop.target.width,
                                    crop.target.height,
                                ),
                            )
                            marker_tolerance = (
                                24.0
                                if routes[slot.block.source_id].upscale_status == "available"
                                else 8.0
                            )
                            self.assertAlmostEqual(
                                actual[0],
                                expected_scaled[0],
                                delta=marker_tolerance,
                                msg=(
                                    f"frame={frame_index} interval={interval_index} "
                                    f"block={slot.block.block_id} role={crop.role} "
                                    f"actual={actual} expected={expected_scaled}"
                                ),
                            )
                            self.assertAlmostEqual(
                                actual[1],
                                expected_scaled[1],
                                delta=marker_tolerance,
                                msg=(
                                    f"frame={frame_index} interval={interval_index} "
                                    f"block={slot.block.block_id} role={crop.role} "
                                    f"actual={actual} expected={expected_scaled}"
                                ),
                            )

            triplicate_interval = plan.layout_plan.intervals[3]
            triplicate_slot = next(slot for slot in triplicate_interval.slots if slot.is_triplicate)
            self.assertEqual(
                tuple(crop.target.width for crop in triplicate_slot.triplicate_crops),
                (213, 214, 213),
            )
            default_crops = plan_triplicate(
                triplicate_slot.block.source_geometry,
                triplicate_slot.slot,
                VisualTransform(),
            )
            transformed_crop = triplicate_slot.triplicate_crops[0]
            transformed_marker = _marker_center(transformed_crop)
            default_marker = _marker_center(default_crops[0])
            transformed_frame = frame_at(plan.frame_boundaries[3])
            transformed_actual = _white_centroid(
                transformed_frame,
                _scaled_region(
                    transformed_crop.target.x,
                    transformed_crop.target.y,
                    transformed_crop.target.width,
                    transformed_crop.target.height,
                ),
            )
            self.assertGreater(
                abs(transformed_marker[0] - default_marker[0]) * 384 / 1920,
                2.0,
            )
            self.assertGreater(
                abs(transformed_actual[0] - default_marker[0] * 384 / 1920),
                2.0,
            )

            decoded = {
                frame_index: _decode_small_frame(destination, frame_index)
                for boundary in plan.frame_boundaries[1:-1]
                if 0 < boundary < plan.expected_frames
                for frame_index in (boundary - 1, boundary)
            }
            self.assertEqual(
                set(decoded),
                {
                    frame_index
                    for boundary in plan.frame_boundaries[1:-1]
                    if 0 < boundary < plan.expected_frames
                    for frame_index in (boundary - 1, boundary)
                },
            )
            for frame in decoded.values():
                self.assertEqual(len(frame), 32 * 18 * 3)
            self.assertTrue(any(_mean_luma(frame) < 8.0 for frame in decoded.values()))
            self.assertTrue(any(_mean_luma(frame) > 25.0 for frame in decoded.values()))
            for interval, start, count in zip(
                plan.layout_plan.intervals,
                plan.frame_boundaries[:-1],
                plan.interval_frame_counts,
                strict=True,
            ):
                if count <= 0:
                    continue
                sample = _decode_small_frame(destination, start)
                if interval.is_black:
                    self.assertLess(_mean_luma(sample), 8.0)
                else:
                    self.assertGreater(_mean_luma(sample), 25.0)


def _make_marker_source(
    root: Path,
    name: str,
    width: int,
    height: int,
    frame_rate: str,
    color: str,
    *,
    sar: str = "1/1",
) -> Path:
    path = root / name
    marker_width = max(12, width // 64)
    marker_height = max(12, height // 64)
    filter_graph = (
        f"drawbox=x={width // 2 - marker_width // 2}:"
        f"y={height // 2 - marker_height // 2}:"
        f"w={marker_width}:h={marker_height}:color=white:t=fill,"
        f"setsar={sar}"
    )
    _run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-nostdin",
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"color=c={color}:s={width}x{height}:r={frame_rate}:d=4",
            "-vf",
            filter_graph,
            "-an",
            "-c:v",
            "libx264",
            "-preset",
            "ultrafast",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(path),
        ]
    )
    return path


def _decode_frame(
    path: Path,
    frame_index: int,
    *,
    width: int = 384,
    height: int = 216,
) -> bytes:
    result = subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-nostdin",
            "-i",
            str(path),
            "-vf",
            f"select='eq(n\\,{frame_index})',scale={width}:{height}:flags=neighbor",
            "-fps_mode",
            "passthrough",
            "-frames:v",
            "1",
            "-an",
            "-f",
            "rawvideo",
            "-pix_fmt",
            "rgb24",
            "pipe:1",
        ],
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise AssertionError(result.stderr.decode(errors="replace"))
    if len(result.stdout) != width * height * 3:
        raise AssertionError(f"Unexpected decoded frame size: {len(result.stdout)}")
    return result.stdout


def _decode_small_frame(path: Path, frame_index: int) -> bytes:
    return _decode_frame(path, frame_index, width=32, height=18)


def _interval_index_for_frame(plan: VideoRenderPlan, frame_index: int) -> int:
    for index, (start, count) in enumerate(
        zip(plan.frame_boundaries[:-1], plan.interval_frame_counts, strict=True),
    ):
        if count > 0 and start <= frame_index < start + count:
            return index
    raise AssertionError(f"Frame {frame_index} is not represented by the render plan")


def _marker_center(crop: CropPlan) -> tuple[float, float]:
    return (
        crop.target.x + crop.scaled_width / 2.0 - crop.crop_x,
        crop.target.y + crop.scaled_height / 2.0 - crop.crop_y,
    )


def _scaled_region(
    x: int,
    y: int,
    width: int,
    height: int,
    *,
    output_width: int = 384,
    output_height: int = 216,
) -> tuple[int, int, int, int]:
    return (
        max(0, x * output_width // 1920),
        max(0, y * output_height // 1080),
        min(output_width, (x + width) * output_width // 1920),
        min(output_height, (y + height) * output_height // 1080),
    )


def _marker_centroid(
    points: list[tuple[int, int]],
    region: tuple[int, int, int, int],
) -> tuple[float, float]:
    if not points:
        raise AssertionError(f"No white marker found in region {region}")
    return (
        sum(point[0] for point in points) / len(points),
        sum(point[1] for point in points) / len(points),
    )


def _white_centroid(
    frame: bytes,
    region: tuple[int, int, int, int],
    *,
    width: int = 384,
) -> tuple[float, float]:
    x_start, y_start, x_end, y_end = region
    points: list[tuple[int, int]] = []
    for y in range(y_start, y_end):
        for x in range(x_start, x_end):
            offset = (y * width + x) * 3
            red, green, blue = frame[offset : offset + 3]
            if (
                min(red, green, blue) >= 180
                and max(red, green, blue)
                - min(
                    red,
                    green,
                    blue,
                )
                <= 35
            ):
                points.append((x, y))
    return _marker_centroid(points, region)


def _mean_luma(frame: bytes) -> float:
    return sum(
        (frame[index] * 3 + frame[index + 1] * 6 + frame[index + 2]) / 10.0
        for index in range(0, len(frame), 3)
    ) / (len(frame) // 3)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _run(command: list[str]) -> None:
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise AssertionError(result.stderr)


if __name__ == "__main__":
    unittest.main()
