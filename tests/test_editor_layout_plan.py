import unittest

from framestudio.composition import TriplicateGroup, VisualTransform
from framestudio.layout_plan import (
    CANVAS_HEIGHT,
    CANVAS_WIDTH,
    FramingDomain,
    LayoutPlanError,
    PixelRect,
    SourceGeometry,
    partition_pixels,
    plan_crop,
    plan_project_layout,
    slot_rects,
)
from framestudio.model import Project, Segment
from framestudio.model_timeline import TimelineTrack


class LayoutPlanGeometryTests(unittest.TestCase):
    def test_layout_slots_use_contract_partitioning(self):
        self.assertEqual(slot_rects(0), ())
        self.assertEqual(
            slot_rects(1),
            (PixelRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT),),
        )
        self.assertEqual(
            tuple(rect.width for rect in slot_rects(3)),
            (640, 640, 640),
        )
        self.assertEqual(
            tuple((rect.x, rect.y, rect.width, rect.height) for rect in slot_rects(4)),
            (
                (0, 0, 960, 540),
                (960, 0, 960, 540),
                (0, 540, 960, 540),
                (960, 540, 960, 540),
            ),
        )
        self.assertEqual(partition_pixels(640, 3), (213, 214, 213))

    def test_native_cover_uses_sar_and_clamps_source_bounds(self):
        source = SourceGeometry(
            source_id="portrait",
            width=1080,
            height=1920,
            sar_num=1,
            sar_den=1,
        )
        target = PixelRect(0, 0, 960, 1080)
        plan = plan_crop(
            source,
            target,
            VisualTransform(zoom=1.5, offset_x=120.0, offset_y=200.0),
        )
        self.assertEqual((plan.scaled_width, plan.scaled_height), (1440, 2560))
        self.assertEqual((plan.crop_x, plan.crop_y), (300, 940))
        self.assertLessEqual(plan.crop_x, plan.scaled_width - target.width)
        self.assertLessEqual(plan.crop_y, plan.scaled_height - target.height)

        non_square = SourceGeometry(
            source_id="anamorphic",
            width=720,
            height=576,
            sar_num=16,
            sar_den=15,
        )
        sar_plan = plan_crop(non_square, PixelRect(0, 0, 1920, 1080))
        self.assertGreaterEqual(sar_plan.scaled_width, 1920)
        self.assertGreaterEqual(sar_plan.scaled_height, 1080)
        self.assertEqual(sar_plan.source_sar, (16, 15))

    def test_triplicate_keeps_uneven_subrects_inside_assigned_slot(self):
        source = SourceGeometry("source", 1080, 1920)
        project = _project_with_blocks(
            (
                Segment.create(
                    0.0,
                    3.0,
                    segment_id="triplicate",
                    block_id="triplicate",
                    source_id="source",
                    timeline_start_seconds=0.0,
                    timeline_end_seconds=3.0,
                    track_id="track-1",
                    visual_transform=VisualTransform(zoom=1.5, offset_x=120, offset_y=-80),
                    triplicate=TriplicateGroup.create(
                        VisualTransform(zoom=1.5, offset_x=120, offset_y=-80),
                        group_id="group-1",
                    ),
                ),
                Segment.create(
                    0.0,
                    3.0,
                    segment_id="second",
                    block_id="second",
                    source_id="source",
                    timeline_start_seconds=0.0,
                    timeline_end_seconds=3.0,
                    track_id="track-2",
                ),
                Segment.create(
                    0.0,
                    3.0,
                    segment_id="third",
                    block_id="third",
                    source_id="source",
                    timeline_start_seconds=0.0,
                    timeline_end_seconds=3.0,
                    track_id="track-3",
                ),
            ),
            track_ids=("track-1", "track-2", "track-3"),
        )
        plan = plan_project_layout(project, {"source": source})
        slot = plan.intervals[0].slots[0]
        self.assertTrue(slot.requires_yuv444_intermediate)
        self.assertEqual(
            tuple(crop.target.width for crop in slot.triplicate_crops),
            (213, 214, 213),
        )

    def test_absolute_boundaries_are_half_open_and_track_ordered(self):
        source = SourceGeometry("source", 1600, 900)
        project = _project_with_blocks(
            (
                Segment.create(
                    0.0,
                    2.0,
                    segment_id="track-1-first",
                    block_id="track-1-first",
                    source_id="source",
                    timeline_start_seconds=1.0,
                    timeline_end_seconds=3.0,
                    track_id="track-1",
                ),
                Segment.create(
                    0.0,
                    2.0,
                    segment_id="track-2-second",
                    block_id="track-2-second",
                    source_id="source",
                    timeline_start_seconds=2.0,
                    timeline_end_seconds=4.0,
                    track_id="track-2",
                ),
                Segment.create(
                    0.0,
                    1.0,
                    segment_id="excluded",
                    block_id="excluded",
                    source_id="source",
                    timeline_start_seconds=10.0,
                    timeline_end_seconds=11.0,
                    track_id="track-2",
                    deleted=True,
                ),
            ),
            track_ids=("track-1", "track-2"),
        )
        plan = plan_project_layout(project, {"source": source})
        self.assertEqual(plan.boundaries, (0, 1_000_000, 2_000_000, 3_000_000, 4_000_000))
        self.assertEqual(plan.final_duration_ticks, 4_000_000)
        self.assertEqual(plan.interval_at(999_999).active_block_ids, ())
        self.assertEqual(
            plan.interval_at(2_000_000).active_block_ids,
            ("track-1-first", "track-2-second"),
        )
        self.assertEqual(
            plan.interval_at(3_000_000).active_block_ids,
            ("track-2-second",),
        )
        self.assertIsNone(plan.interval_at(4_000_000))

    def test_opaque_state_does_not_change_canonical_membership(self):
        source = SourceGeometry("source", 1600, 900)
        project = _project_with_blocks(
            (
                Segment.create(
                    0.0,
                    2.0,
                    segment_id="opaque-state",
                    block_id="opaque-state",
                    source_id="source",
                    timeline_start_seconds=3.0,
                    timeline_end_seconds=5.0,
                    track_id="track-1",
                    state={"included": False, "inactive": True},
                ),
            ),
        )
        plan = plan_project_layout(project, {"source": source})
        self.assertEqual(plan.final_duration_ticks, 5_000_000)
        self.assertEqual(
            plan.interval_at(3_000_000).active_block_ids,
            ("opaque-state",),
        )

    def test_legacy_projection_compacts_exclusions_without_absolute_gaps(self):
        source = SourceGeometry("source", 1600, 900)
        project = _project_with_blocks(
            (
                Segment.create(
                    0.0,
                    2.0,
                    segment_id="kept-a",
                    block_id="kept-a",
                    source_id="source",
                    timeline_start_seconds=0.0,
                    timeline_end_seconds=2.0,
                    track_id="track-1",
                ),
                Segment.create(
                    2.0,
                    4.0,
                    segment_id="deleted",
                    block_id="deleted",
                    source_id="source",
                    timeline_start_seconds=2.0,
                    timeline_end_seconds=4.0,
                    track_id="track-1",
                    deleted=True,
                ),
                Segment.create(
                    4.0,
                    5.0,
                    segment_id="kept-b",
                    block_id="kept-b",
                    source_id="source",
                    timeline_start_seconds=4.0,
                    timeline_end_seconds=5.0,
                    track_id="track-1",
                ),
            ),
            track_ids=("track-1",),
            timing_mode="legacy-ripple",
        )
        plan = plan_project_layout(project, {"source": source})
        self.assertEqual(plan.final_duration_ticks, 3_000_000)
        self.assertEqual(plan.boundaries, (0, 2_000_000, 3_000_000))
        self.assertEqual(
            tuple(
                (
                    block.segment_id,
                    block.source_range.timeline_start_tick,
                    block.source_range.timeline_end_tick,
                )
                for block in plan.included_blocks
            ),
            (
                ("kept-a", 0, 2_000_000),
                ("kept-b", 2_000_000, 3_000_000),
            ),
        )

    def test_preparation_domains_are_explicit_and_never_alias(self):
        source = SourceGeometry("source", 1080, 1920)
        native = plan_crop(
            source,
            PixelRect(0, 0, 960, 1080),
            output_domain=FramingDomain.FINAL_SLOT,
        )
        self.assertEqual(native.framing_identity.input_domain, FramingDomain.NATIVE_SOURCE)
        with self.assertRaisesRegex(LayoutPlanError, "native-source"):
            plan_crop(
                SourceGeometry(
                    "source",
                    CANVAS_WIDTH,
                    CANVAS_HEIGHT,
                    input_domain=FramingDomain.FULL_CANVAS_REEL,
                ),
                PixelRect(0, 0, 960, 1080),
                output_domain=FramingDomain.FINAL_SLOT,
            )
        standalone = plan_crop(
            source,
            PixelRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT),
            output_domain=FramingDomain.FULL_CANVAS_REEL,
        )
        self.assertNotEqual(native.framing_identity, standalone.framing_identity)
        self.assertEqual(
            standalone.framing_identity.output_domain,
            FramingDomain.FULL_CANVAS_REEL,
        )

    def test_metadata_rejects_fractional_and_boolean_dimensions_or_sar(self):
        with self.assertRaisesRegex(LayoutPlanError, "width and height"):
            SourceGeometry.from_metadata(
                "fractional",
                {"width": 10.9, "height": 20},
            )
        with self.assertRaisesRegex(LayoutPlanError, "width and height"):
            SourceGeometry.from_metadata(
                "boolean",
                {"width": True, "height": 20},
            )
        with self.assertRaisesRegex(LayoutPlanError, "sample aspect ratio"):
            SourceGeometry.from_metadata(
                "fractional-sar",
                {"width": 100, "height": 100, "sar_num": 10.9, "sar_den": 1},
            )
        with self.assertRaisesRegex(LayoutPlanError, "sample aspect ratio"):
            SourceGeometry.from_metadata(
                "boolean-sar",
                {"width": 100, "height": 100, "sar_num": True, "sar_den": 1},
            )


def _project_with_blocks(
    blocks: tuple[Segment, ...],
    *,
    track_ids: tuple[str, ...] = ("track-1",),
    timing_mode: str = "absolute",
) -> Project:
    tracks = []
    by_track = {track_id: [] for track_id in track_ids}
    for block in blocks:
        by_track.setdefault(block.track_id or "track-1", []).append(block)
    for track_id in track_ids:
        tracks.append(TimelineTrack(track_id, tuple(by_track.get(track_id, ()))))
    timeline = Project.create_synchronized(
        source_path=__file__,  # replaced below by the test-only project constructor
        metadata={"duration_seconds": 12.0, "width": 1600, "height": 900},
        project_id="layout-unit",
    ).timeline
    timeline = timeline.__class__.from_tracks(
        tuple(tracks),
        source_durations={"source": 12.0},
        active_track_id=track_ids[0],
        ripple=(timing_mode == "legacy-ripple"),
        timing_mode=timing_mode,
    )
    project = Project.create_synchronized(
        source_path=__file__,
        metadata={"duration_seconds": 12.0, "width": 1600, "height": 900},
        project_id="layout-unit",
    )
    project.segment_timeline = timeline
    project.sources = (
        project.source.__class__.from_path(
            __file__,
            {"duration_seconds": 12.0, "width": 1600, "height": 900},
            source_id="source",
        ),
    )
    project.source = project.sources[0]
    project.source_settings = {"source": {}}
    project.duration_seconds = timeline.timeline_duration_seconds
    project.validate()
    return project


if __name__ == "__main__":
    unittest.main()
