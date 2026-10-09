import hashlib
import shutil
import subprocess
import unittest
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory

from framestudio.layout_plan import plan_project_layout, source_geometries_from_project
from framestudio.media import probe_media
from framestudio.model import (
    ABSOLUTE_TIMING_MODE,
    LEGACY_TIMING_MODE,
    Project,
    Segment,
    SegmentTimeline,
    TimelineTrack,
    TriplicateGroup,
    VisualTransform,
)
from framestudio.persistence import load_project, save_project

REPOSITORY = Path(__file__).resolve().parents[1]


@contextmanager
def isolated_directory():
    with TemporaryDirectory(
        dir=Path(__file__).resolve().parent,
        prefix=".ticket119-layout-",
    ) as raw_path:
        yield Path(raw_path)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_marker_source(root: Path, name: str, width: int, height: int) -> Path:
    path = root / name
    marker_width = max(24, width // 8)
    marker_height = max(24, height // 8)
    filter_graph = ",".join(
        (
            f"drawbox=x={width // 12}:y={height // 12}:w={marker_width}:h={marker_height}:"
            "color=red:t=fill",
            f"drawbox=x={width - width // 12 - marker_width}:y={height // 12}:"
            f"w={marker_width}:h={marker_height}:color=green:t=fill",
            f"drawbox=x={width // 12}:y={height - height // 12 - marker_height}:"
            f"w={marker_width}:h={marker_height}:color=blue:t=fill",
            f"drawbox=x={width - width // 12 - marker_width}:"
            f"y={height - height // 12 - marker_height}:w={marker_width}:"
            f"h={marker_height}:color=yellow:t=fill",
            f"drawbox=x={width // 2 - marker_width // 2}:"
            f"y={height // 2 - marker_height // 2}:w={marker_width}:"
            f"h={marker_height}:color=white:t=fill",
        )
    )
    subprocess.run(
        [
            shutil.which("ffmpeg") or "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-nostdin",
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"color=c=black:s={width}x{height}:r=1:d=8",
            "-vf",
            filter_graph,
            "-c:v",
            "libx264",
            "-preset",
            "ultrafast",
            "-pix_fmt",
            "yuv420p",
            "-an",
            str(path),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )
    return path


def make_block(
    *,
    segment_id: str,
    source_id: str,
    track_id: str,
    source_start: float,
    source_end: float,
    timeline_start: float,
    timeline_end: float,
    deleted: bool = False,
    state: dict[str, object] | None = None,
    visual_transform: VisualTransform | None = None,
    triplicate: TriplicateGroup | None = None,
) -> Segment:
    return Segment.create(
        source_start,
        source_end,
        segment_id=segment_id,
        block_id=segment_id,
        source_id=source_id,
        timeline_start_seconds=timeline_start,
        timeline_end_seconds=timeline_end,
        track_id=track_id,
        deleted=deleted,
        state=state,
        visual_transform=visual_transform,
        triplicate=triplicate,
    )


class LayoutPlanFunctionalityTests(unittest.TestCase):
    def test_saved_four_track_project_plans_from_real_ffmpeg_sources(self):
        if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
            self.skipTest("FFmpeg and ffprobe are required")
        with isolated_directory() as root:
            fixture_root = root / "fixtures"
            fixture_root.mkdir()
            sources = (
                make_marker_source(fixture_root, "portrait.mp4", 1080, 1920),
                make_marker_source(fixture_root, "landscape.mp4", 1600, 900),
                make_marker_source(fixture_root, "ultrawide.mp4", 2400, 900),
                make_marker_source(fixture_root, "square.mp4", 1000, 1000),
            )
            probes = tuple(probe_media(path) for path in sources)
            source_hashes = {path.name: sha256(path) for path in sources}

            project = Project.create_synchronized_multi(
                tuple(
                    (path, probe.metadata()) for path, probe in zip(sources, probes, strict=True)
                ),
                project_id="layout-functionality",
            )
            for track_id in ("track-2", "track-3", "track-4"):
                project.timeline.add_track(track_id)
            source_ids = tuple(source.source_id for source in project.sources)
            shared_transform = VisualTransform(zoom=1.5, offset_x=120.0, offset_y=-80.0)
            triplicate = TriplicateGroup.create(shared_transform, group_id="triplicate-c")
            project.timeline.replace_track_blocks(
                "track-1",
                (
                    make_block(
                        segment_id="a",
                        source_id=source_ids[0],
                        track_id="track-1",
                        source_start=0.0,
                        source_end=2.0,
                        timeline_start=1.0,
                        timeline_end=3.0,
                    ),
                ),
            )
            project.timeline.replace_track_blocks(
                "track-2",
                (
                    make_block(
                        segment_id="b",
                        source_id=source_ids[1],
                        track_id="track-2",
                        source_start=1.0,
                        source_end=3.0,
                        timeline_start=2.0,
                        timeline_end=4.0,
                    ),
                    make_block(
                        segment_id="excluded-tail",
                        source_id=source_ids[1],
                        track_id="track-2",
                        source_start=3.0,
                        source_end=4.0,
                        timeline_start=10.0,
                        timeline_end=11.0,
                        deleted=True,
                    ),
                ),
            )
            project.timeline.replace_track_blocks(
                "track-3",
                (
                    make_block(
                        segment_id="c-triplicate",
                        source_id=source_ids[2],
                        track_id="track-3",
                        source_start=0.0,
                        source_end=2.0,
                        timeline_start=2.25,
                        timeline_end=4.25,
                        visual_transform=shared_transform,
                        triplicate=triplicate,
                    ),
                    make_block(
                        segment_id="c-standalone",
                        source_id=source_ids[2],
                        track_id="track-3",
                        source_start=2.0,
                        source_end=3.0,
                        timeline_start=5.5,
                        timeline_end=6.5,
                    ),
                ),
            )
            project.timeline.replace_track_blocks(
                "track-4",
                (
                    make_block(
                        segment_id="d",
                        source_id=source_ids[3],
                        track_id="track-4",
                        source_start=0.0,
                        source_end=2.0,
                        timeline_start=2.5,
                        timeline_end=4.5,
                    ),
                    make_block(
                        segment_id="d-standalone",
                        source_id=source_ids[3],
                        track_id="track-4",
                        source_start=2.0,
                        source_end=4.0,
                        timeline_start=7.0,
                        timeline_end=9.0,
                        state={"included": False, "inactive": True},
                    ),
                    make_block(
                        segment_id="excluded-final-tail",
                        source_id=source_ids[3],
                        track_id="track-4",
                        source_start=4.0,
                        source_end=5.0,
                        timeline_start=11.0,
                        timeline_end=12.0,
                        deleted=True,
                    ),
                ),
            )
            project.duration_seconds = project.timeline.timeline_duration_seconds
            project.validate()

            project_path = fixture_root / "four-track.framestudio.json"
            save_project(project, project_path)
            reopened = load_project(project_path)
            self.assertEqual(reopened.to_dict(), project.to_dict())
            self.assertEqual(reopened.schema_version, 4)
            self.assertEqual(reopened.timeline.timing_mode, ABSOLUTE_TIMING_MODE)
            self.assertEqual(
                reopened.timeline.track_ids,
                ("track-1", "track-2", "track-3", "track-4"),
            )
            self.assertEqual(
                reopened.timeline.find("c-triplicate").visual_transform,
                shared_transform,
            )
            self.assertEqual(
                reopened.timeline.find("c-triplicate").triplicate,
                triplicate,
            )

            source_geometries = source_geometries_from_project(reopened)
            self.assertEqual(
                tuple((geometry.width, geometry.height) for geometry in source_geometries.values()),
                ((1080, 1920), (1600, 900), (2400, 900), (1000, 1000)),
            )
            plan = plan_project_layout(reopened, source_geometries)
            self.assertEqual(plan, plan_project_layout(reopened))
            self.assertEqual(plan.final_duration_ticks, 9_000_000)
            self.assertEqual(
                plan.boundaries,
                (
                    0,
                    1_000_000,
                    2_000_000,
                    2_250_000,
                    2_500_000,
                    3_000_000,
                    4_000_000,
                    4_250_000,
                    4_500_000,
                    5_500_000,
                    6_500_000,
                    7_000_000,
                    9_000_000,
                ),
            )
            self.assertEqual(plan.interval_at(0).active_block_ids, ())
            self.assertEqual(plan.interval_at(2_000_000).active_block_ids, ("a", "b"))
            self.assertEqual(
                plan.interval_at(2_250_000).active_block_ids,
                ("a", "b", "c-triplicate"),
            )
            self.assertEqual(
                plan.interval_at(2_500_000).active_block_ids,
                ("a", "b", "c-triplicate", "d"),
            )
            self.assertEqual(
                plan.interval_at(3_000_000).active_block_ids,
                ("b", "c-triplicate", "d"),
            )
            three_slots_after_a = plan.interval_at(3_000_000).slots
            self.assertEqual(
                tuple(slot.block.segment_id for slot in three_slots_after_a),
                ("b", "c-triplicate", "d"),
            )
            self.assertEqual(
                tuple(
                    (
                        slot.slot.x + slot.slot.width // 2,
                        slot.slot.y + slot.slot.height // 2,
                    )
                    for slot in three_slots_after_a
                ),
                ((320, 540), (960, 540), (1600, 540)),
            )
            self.assertEqual(
                plan.interval_at(4_000_000).active_block_ids,
                ("c-triplicate", "d"),
            )
            self.assertEqual(
                plan.interval_at(4_250_000).active_block_ids,
                ("d",),
            )
            self.assertEqual(plan.interval_at(4_500_000).active_block_ids, ())
            self.assertEqual(
                plan.interval_at(5_500_000).active_block_ids,
                ("c-standalone",),
            )
            self.assertEqual(plan.interval_at(6_500_000).active_block_ids, ())
            self.assertEqual(plan.interval_at(7_000_000).active_block_ids, ("d-standalone",))
            self.assertIsNone(plan.interval_at(9_000_000))

            two_slots = plan.interval_at(2_000_000).slots
            self.assertEqual(
                tuple((slot.slot.x, slot.slot.width) for slot in two_slots),
                ((0, 960), (960, 960)),
            )
            self.assertEqual(
                tuple(slot.slot.x + slot.slot.width // 2 for slot in two_slots),
                (480, 1440),
            )
            three_slots = plan.interval_at(2_250_000).slots
            self.assertEqual(
                plan.interval_at(2_250_000).active_block_ids,
                ("a", "b", "c-triplicate"),
            )
            self.assertEqual(
                tuple(
                    (slot.slot.x + slot.slot.width // 2, slot.slot.y + slot.slot.height // 2)
                    for slot in three_slots
                ),
                ((320, 540), (960, 540), (1600, 540)),
            )
            triplicate_slot = three_slots[2]
            self.assertTrue(triplicate_slot.is_triplicate)
            self.assertEqual(
                tuple(crop.target.width for crop in triplicate_slot.triplicate_crops),
                (213, 214, 213),
            )
            self.assertEqual(
                tuple(crop.target.x for crop in triplicate_slot.triplicate_crops),
                (1280, 1493, 1707),
            )
            four_slots = plan.interval_at(2_500_000).slots
            self.assertEqual(
                tuple(
                    (slot.slot.x + slot.slot.width // 2, slot.slot.y + slot.slot.height // 2)
                    for slot in four_slots
                ),
                ((480, 270), (1440, 270), (480, 810), (1440, 810)),
            )
            self.assertEqual(
                tuple(slot.block.segment_id for slot in four_slots),
                ("a", "b", "c-triplicate", "d"),
            )
            triplicate_block = next(
                block for block in plan.included_blocks if block.segment_id == "c-triplicate"
            )
            self.assertEqual(
                triplicate_block.source_range.source_tick_at(2_250_000),
                0,
            )
            self.assertEqual(
                triplicate_block.source_range.source_tick_at(4_249_999),
                1_999_999,
            )
            self.assertEqual(
                next(
                    block for block in plan.included_blocks if block.segment_id == "d-standalone"
                ).source_range.source_tick_at(7_000_000),
                2_000_000,
            )

            legacy_timeline = SegmentTimeline.from_tracks(
                (
                    TimelineTrack(
                        "track-1",
                        (
                            reopened.timeline.track_by_id("track-1").blocks[0],
                            make_block(
                                segment_id="legacy-deleted",
                                source_id=source_ids[0],
                                track_id="track-1",
                                source_start=2.0,
                                source_end=4.0,
                                timeline_start=8.0,
                                timeline_end=10.0,
                                deleted=True,
                            ),
                            make_block(
                                segment_id="legacy-kept",
                                source_id=source_ids[0],
                                track_id="track-1",
                                source_start=4.0,
                                source_end=5.0,
                                timeline_start=10.0,
                                timeline_end=11.0,
                            ),
                        ),
                    ),
                ),
                source_durations={
                    source_id: probe.duration_seconds
                    for source_id, probe in zip(source_ids, probes, strict=True)
                },
                active_track_id="track-1",
                ripple=True,
                timing_mode=LEGACY_TIMING_MODE,
            )
            legacy = load_project(project_path)
            legacy.segment_timeline = legacy_timeline
            legacy.duration_seconds = legacy_timeline.timeline_duration_seconds
            legacy_path = fixture_root / "legacy-v4.framestudio.json"
            save_project(legacy, legacy_path)
            legacy_reopened = load_project(legacy_path)
            legacy_plan = plan_project_layout(legacy_reopened)
            self.assertEqual(legacy_plan.timing_mode, LEGACY_TIMING_MODE)
            self.assertEqual(legacy_plan.final_duration_ticks, 3_000_000)
            self.assertEqual(
                tuple(block.segment_id for block in legacy_plan.included_blocks),
                ("a", "legacy-kept"),
            )
            self.assertEqual(
                tuple(
                    (
                        block.source_range.timeline_start_tick,
                        block.source_range.timeline_end_tick,
                    )
                    for block in legacy_plan.included_blocks
                ),
                ((0, 2_000_000), (2_000_000, 3_000_000)),
            )

            for path in sources:
                self.assertEqual(sha256(path), source_hashes[path.name])
                metadata = probe_media(path).metadata()
                self.assertEqual(
                    (metadata["width"], metadata["height"]),
                    (probe_media(path).width, probe_media(path).height),
                )


if __name__ == "__main__":
    unittest.main()
