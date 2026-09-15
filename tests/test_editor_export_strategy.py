import unittest
from fractions import Fraction
from pathlib import Path

from framestudio.export_strategy import build_export_runs
from framestudio.export_types import ExportPlan
from framestudio.fps_policy import SourceRateDecision
from framestudio.model import Segment
from tests.editor_test_helpers import make_output_policy


def make_plan(segments, *, source_ids=("source-a", "source-b")):
    return ExportPlan(
        route="enhanced",
        source=Path("source-a.mp4"),
        destination=Path("output.mp4"),
        segments=tuple(segments),
        expected_duration_seconds=sum(segment.duration_seconds for segment in segments),
        reason="test",
        output_policy=make_output_policy(),
        source_paths=tuple(Path(f"{source_id}.mp4") for source_id in source_ids),
        source_ids=source_ids,
    )


class ExportStrategyTests(unittest.TestCase):
    def test_groups_only_contiguous_compatible_active_segments(self):
        segments = (
            Segment.create(0.0, 1.0, source_id="source-a"),
            Segment.create(1.0, 2.0, source_id="source-a"),
            Segment.create(0.0, 1.0, source_id="source-b"),
            Segment.create(2.0, 3.0, source_id="source-a"),
        )
        plan = make_plan(segments)
        decisions = {
            "source-a": SourceRateDecision(
                source_id="source-a",
                source_rate=Fraction(30, 1),
                target_rate=Fraction(60, 1),
                action="interpolate",
                eligible=True,
                reason="test",
            ),
            "source-b": SourceRateDecision(
                source_id="source-b",
                source_rate=Fraction(60, 1),
                target_rate=Fraction(60, 1),
                action="passthrough",
                eligible=False,
                reason="test",
            ),
        }

        runs = build_export_runs(plan, decisions)

        self.assertEqual(
            [(run.source_id, run.segment_indices) for run in runs],
            [
                ("source-a", (0, 1)),
                ("source-b", (2,)),
                ("source-a", (3,)),
            ],
        )
        self.assertTrue(runs[0].boundary_safe_for_ffmpeg_ranges)
        self.assertEqual(runs[0].source_rate, Fraction(30, 1))

    def test_deleted_segments_do_not_enter_a_run_but_preserve_run_boundaries(self):
        segments = (
            Segment.create(0.0, 1.0, source_id="source-a"),
            Segment.create(1.0, 2.0, source_id="source-a", deleted=True),
            Segment.create(2.0, 3.0, source_id="source-a"),
        )
        plan = make_plan(segments, source_ids=("source-a",))
        decisions = {
            "source-a": SourceRateDecision(
                source_id="source-a",
                source_rate=Fraction(30, 1),
                target_rate=Fraction(60, 1),
                action="interpolate",
                eligible=True,
                reason="test",
            )
        }

        runs = build_export_runs(plan, decisions)

        self.assertEqual(len(runs), 1)
        self.assertEqual(runs[0].segment_indices, (0, 2))
        self.assertEqual(
            tuple(segment.duration_seconds for segment in runs[0].segments),
            (1.0, 1.0),
        )
        self.assertTrue(runs[0].has_deleted_gap)

    def test_upscale_profile_is_part_of_compatibility(self):
        segments = (
            Segment.create(0.0, 1.0, source_id="source-a"),
            Segment.create(1.0, 2.0, source_id="source-a"),
        )
        plan = make_plan(segments, source_ids=("source-a",))
        decision = SourceRateDecision(
            source_id="source-a",
            source_rate=Fraction(30, 1),
            target_rate=Fraction(60, 1),
            action="interpolate",
            eligible=True,
            reason="test",
        )

        runs = build_export_runs(
            plan,
            {"source-a": decision},
            upscale_decisions={
                "source-a": {
                    "eligible": True,
                    "model": "model-a",
                    "target_width": 1920,
                    "target_height": 1080,
                }
            },
        )

        self.assertEqual(len(runs), 1)
        self.assertTrue(runs[0].upscale_eligible)
        self.assertEqual(runs[0].upscale_model, "model-a")
