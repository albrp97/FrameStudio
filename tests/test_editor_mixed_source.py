import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from resolve_editor.export import resolve_output_policy
from resolve_editor.model import (
    Project,
    ProjectTimeline,
    ProjectValidationError,
    Segment,
    seconds_to_ticks,
    ticks_to_seconds,
)
from resolve_editor.operations import (
    copy_segments,
    move_segment,
    paste_segments,
    split_segment,
)
from resolve_editor.persistence import load_project, save_project


def metadata(duration, width, height, frame_rate):
    return {
        "duration_seconds": duration,
        "width": width,
        "height": height,
        "frame_rate": frame_rate,
        "video_codec": "h264",
        "audio_codec": "aac",
        "audio_stream_present": True,
        "format_name": "mp4",
    }


class MixedSourceModelTests(unittest.TestCase):
    def make_sources(self, root):
        first = root / "landscape.mp4"
        second = root / "portrait.mp4"
        first.write_bytes(b"first")
        second.write_bytes(b"second")
        return (
            (first, metadata(4.0, 1920, 1080, "24/1")),
            (second, metadata(3.0, 1080, 1920, "30/1")),
        )

    def test_multi_source_project_round_trips_identity_and_block_ownership(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            project = Project.create_multi(self.make_sources(root))

            self.assertEqual(project.schema_version, 3)
            self.assertEqual(len(project.sources), 2)
            self.assertEqual(
                [block.source_id for block in project.timeline.blocks],
                [source.source_id for source in project.sources],
            )
            self.assertEqual(project.duration_seconds, 7.0)
            payload = project.to_dict()
            restored = Project.from_dict(payload)

            self.assertEqual(restored.to_dict(), payload)
            self.assertEqual(
                [block.source_id for block in restored.timeline.blocks],
                [source.source_id for source in restored.sources],
            )

    def test_relink_requires_explicit_identity_and_matching_media_metadata(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            project = Project.create_multi(self.make_sources(root))
            source = project.sources[0]
            source.unlink() if False else None
            moved = root / "moved.mp4"
            moved.write_bytes(b"first")

            relinked = project.relink_source(
                source.source_id,
                moved,
                source.metadata,
            )

            self.assertEqual(relinked.source_id, source.source_id)
            self.assertEqual(project.sources[0].path, str(moved.resolve()))
            with self.assertRaises(ProjectValidationError):
                project.relink_source(
                    "missing-source",
                    moved,
                    source.metadata,
                )

            mismatched = dict(source.metadata)
            mismatched["width"] = 1
            with self.assertRaises(ProjectValidationError):
                project.relink_source(source.source_id, moved, mismatched)

    def test_atomic_blocks_copy_paste_move_and_split_clone_state(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            project = Project.create_multi(self.make_sources(root))
            timeline = project.timeline
            first, second = timeline.blocks
            timeline.split_block(
                first.segment_id,
                2.0,
            )
            split_children = timeline.blocks[:2]
            self.assertEqual(
                [child.source_id for child in split_children],
                [first.source_id, first.source_id],
            )
            self.assertEqual(
                [child.state for child in split_children],
                [{}, {}],
            )

            copied = copy_segments(project, [split_children[1].segment_id])
            self.assertEqual(len(copied), 1)
            self.assertNotEqual(copied[0].segment_id, split_children[1].segment_id)
            paste_segments(project, copied, at_index=0)
            self.assertEqual(len(project.timeline.blocks), 4)
            self.assertEqual(
                project.timeline.blocks[0].source_id,
                split_children[1].source_id,
            )

            before_ids = [block.segment_id for block in project.timeline.blocks]
            move_segment(project, before_ids[-1], "left")
            self.assertEqual(
                [block.segment_id for block in project.timeline.blocks],
                [before_ids[0], before_ids[1], before_ids[3], before_ids[2]],
            )

    def test_move_and_copy_paste_preserve_block_colors(self):
        timeline = ProjectTimeline.from_blocks(
            (
                Segment.create(
                    0.0,
                    2.0,
                    source_id="source-a",
                    timeline_start_seconds=0.0,
                    timeline_end_seconds=2.0,
                    color_index=1,
                ),
                Segment.create(
                    0.0,
                    3.0,
                    source_id="source-b",
                    timeline_start_seconds=2.0,
                    timeline_end_seconds=5.0,
                    color_index=2,
                ),
            )
        )
        blue_id = timeline.blocks[0].segment_id
        blue_color = timeline.blocks[0].color_index
        green_color = timeline.blocks[1].color_index

        self.assertTrue(timeline.move_block(blue_id, "right"))
        self.assertEqual(
            [block.color_index for block in timeline.blocks],
            [green_color, blue_color],
        )

        copied = timeline.copy_blocks([blue_id])
        self.assertEqual(copied[0].color_index, blue_color)
        timeline.paste_blocks(copied, at_index=0)
        self.assertEqual(
            [block.color_index for block in timeline.blocks],
            [blue_color, green_color, blue_color],
        )

    def test_block_colors_round_trip_through_project_persistence(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            project = Project.create_multi(self.make_sources(root))
            colors = [block.color_index for block in project.timeline.blocks]

            restored = Project.from_dict(project.to_dict())

            self.assertEqual(
                [block.color_index for block in restored.timeline.blocks],
                colors,
            )

    def test_split_operation_uses_timeline_position_for_mixed_blocks(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            project = Project.create_multi(self.make_sources(root))
            original_color = project.timeline.blocks[1].color_index

            first, second = split_segment(project.timeline, 5.0)

            self.assertEqual(first.source_id, project.sources[1].source_id)
            self.assertEqual(second.source_id, project.sources[1].source_id)
            self.assertEqual(first.timeline_start, 4.0)
            self.assertEqual(first.timeline_end, 5.0)
            self.assertEqual(second.timeline_start, 5.0)
            self.assertEqual(second.timeline_end, 7.0)
            self.assertNotEqual(first.color_index, second.color_index)
            self.assertNotEqual(first.color_index, original_color)
            self.assertNotEqual(second.color_index, original_color)

    def test_copy_preserves_deleted_state_and_owned_state_without_sharing(self):
        timeline = ProjectTimeline.from_blocks(
            (
                Segment.create(
                    0.0,
                    2.0,
                    source_id="source-a",
                    timeline_start_seconds=0.0,
                    timeline_end_seconds=2.0,
                    deleted=True,
                    state={"zoom": 1.5, "offset": {"x": 2}},
                ),
            )
        )
        copied = timeline.copy_blocks([timeline.blocks[0].segment_id])

        self.assertTrue(copied[0].deleted)
        self.assertEqual(copied[0].state, timeline.blocks[0].state)
        self.assertIsNot(copied[0].state, timeline.blocks[0].state)
        self.assertNotEqual(copied[0].segment_id, timeline.blocks[0].segment_id)
        copied[0].state["offset"]["x"] = 99
        self.assertEqual(timeline.blocks[0].state["offset"]["x"], 2)

    def test_project_save_reopen_preserves_mixed_sources(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            project = Project.create_multi(self.make_sources(root))
            destination = root / "mixed.resolve.json"

            save_project(project, destination)
            restored = load_project(destination)

            self.assertEqual(restored.to_dict(), project.to_dict())

    def test_canonical_timebase_rounds_deterministically(self):
        self.assertEqual(seconds_to_ticks(1.2345674), 1234567)
        self.assertEqual(seconds_to_ticks(1.2345676), 1234568)
        self.assertEqual(ticks_to_seconds(1234568), 1.234568)

    def test_mixed_output_policy_uses_fixed_1080p_render_canvas(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            project = Project.create_multi(self.make_sources(root))
            source_metadata = [dict(source.metadata) for source in project.sources]
            source_metadata[1]["video_codec"] = "vp9"
            source_metadata[1]["audio_codec"] = "opus"
            source_metadata[1]["format_name"] = "webm"
            policy = resolve_output_policy(
                source_metadata,
            )

            self.assertEqual((policy.width, policy.height), (1920, 1080))
            self.assertEqual(policy.scaling_mode, "contain-letterbox")
            self.assertEqual(policy.frame_rate, "30/1")
            self.assertEqual(policy.container, "mp4")
            self.assertEqual(policy.video_codec, "libx264")
            self.assertEqual(policy.audio_codec, "aac")
            self.assertNotIn("stream formats", policy.reason)
            self.assertTrue(policy.requires_normalization)


if __name__ == "__main__":
    unittest.main()
