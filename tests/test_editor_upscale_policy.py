import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from framestudio.export import plan_export
from framestudio.media import MediaProbe
from framestudio.model import Project, SegmentTimeline
from framestudio.persistence import load_project, save_project
from framestudio.upscale_policy import (
    UpscalePolicy,
    resolve_upscale_policy,
)


def metadata(
    *,
    source_id: str = "source",
    width: int = 640,
    height: int = 360,
) -> dict[str, object]:
    return {
        "source_id": source_id,
        "width": width,
        "height": height,
        "frame_rate": "30/1",
    }


class EditorUpscalePolicyTests(unittest.TestCase):
    def test_enabled_landscape_selects_superultracompact_and_1080_short_side(self):
        resolved = resolve_upscale_policy(
            (metadata(width=640, height=360),),
            enabled=True,
        )

        decision = resolved.decisions[0]
        self.assertEqual(decision.action, "enhance")
        self.assertTrue(decision.eligible)
        self.assertEqual(decision.model, "SuperUltraCompact")
        self.assertEqual((decision.target_width, decision.target_height), (1920, 1080))

    def test_enabled_portrait_selects_1080_short_side_without_downscale(self):
        resolved = resolve_upscale_policy(
            (metadata(width=720, height=1280),),
            enabled=True,
        )

        decision = resolved.decisions[0]
        self.assertEqual(decision.action, "enhance")
        self.assertEqual((decision.target_width, decision.target_height), (1080, 1920))
        self.assertEqual(decision.source_short_side, 720)

    def test_enabled_square_and_above_threshold_sources_passthrough(self):
        resolved = resolve_upscale_policy(
            (
                metadata(source_id="square", width=1080, height=1080),
                metadata(source_id="large", width=1920, height=1080),
            ),
            enabled=True,
        )

        self.assertEqual(
            [(item.action, item.eligible, item.model) for item in resolved.decisions],
            [("passthrough", False, None), ("passthrough", False, None)],
        )
        self.assertEqual(resolved.eligible_source_ids, ())

    def test_disabled_policy_passthroughs_eligible_source(self):
        resolved = resolve_upscale_policy(
            (metadata(width=640, height=360),),
            enabled=False,
        )

        self.assertEqual(resolved.policy.to_dict()["enhancement_enabled"], False)
        self.assertEqual(resolved.decisions[0].action, "passthrough")
        self.assertIn("disabled", resolved.decisions[0].reason)

    def test_policy_round_trip_accepts_enabled_alias(self):
        policy = UpscalePolicy(enabled=True)

        restored = UpscalePolicy.from_dict(json.loads(json.dumps(policy.to_dict())))

        self.assertTrue(restored.enhancement_enabled)
        self.assertTrue(restored.enabled)
        self.assertEqual(restored.model, "SuperUltraCompact")

    def test_missing_policy_defaults_on_and_explicit_disable_survives_reopen(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = root / "source.mp4"
            source.write_bytes(b"fixture")
            project = Project.create(source, {**metadata(), "duration_seconds": 10.0})
            destination = root / "project.framestudio.json"

            self.assertTrue(project.get_upscale_policy().enhancement_enabled)
            project.set_upscale_policy(UpscalePolicy(enhancement_enabled=False))
            save_project(project, destination)
            restored = load_project(destination)

            self.assertFalse(restored.get_upscale_policy().enhancement_enabled)

            payload = json.loads(destination.read_text(encoding="utf-8"))
            payload["output_settings"].pop("upscale_policy")
            destination.write_text(json.dumps(payload), encoding="utf-8")
            old_project = load_project(destination)
            self.assertTrue(old_project.get_upscale_policy().enhancement_enabled)

    def test_policy_without_enabled_field_defaults_on(self):
        restored = UpscalePolicy.from_dict({"version": 1})

        self.assertTrue(restored.enhancement_enabled)

    def test_upscale_policy_marks_upscale_only_export_as_enhanced(self):
        probe = MediaProbe(
            path=Path("/tmp/source.mp4"),
            duration_seconds=10.0,
            width=640,
            height=360,
            frame_rate="30/1",
            video_codec="h264",
            audio_codec=None,
            format_name="mp4",
        )

        plan = plan_export(
            probe,
            SegmentTimeline(10.0),
            Path("/tmp/edited.mp4"),
            upscale_policy=UpscalePolicy(enhancement_enabled=True),
        )

        self.assertEqual(plan.route, "enhanced")
        self.assertEqual(plan.upscale_policy.enhancement_enabled, True)
        self.assertEqual(plan.upscale_decisions[0].action, "enhance")


if __name__ == "__main__":
    unittest.main()
