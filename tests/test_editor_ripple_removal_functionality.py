from __future__ import annotations

import hashlib
import shutil
import subprocess
import unittest
from copy import deepcopy
from pathlib import Path

from framestudio.media import probe_media
from framestudio.model import (
    Project,
    ProjectValidationError,
    SourceReference,
    TriplicateGroup,
    VisualTransform,
)
from framestudio.operations import (
    create_project_from_source,
    remove_segments,
    undo_remove,
)
from framestudio.persistence import load_project, save_project
from tests.test_editor_ripple_removal import _block, isolated_directory


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _make_media(root: Path, name: str, source: str, duration: float) -> Path:
    destination = root / name
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        raise unittest.SkipTest("FFmpeg is required")
    result = subprocess.run(
        [
            ffmpeg,
            "-hide_banner",
            "-loglevel",
            "error",
            "-nostdin",
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"{source}:rate=10",
            "-t",
            str(duration),
            "-an",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            str(destination),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise AssertionError(f"Could not create {name}: {result.stderr}")
    return destination


class RippleRemovalFunctionalityTests(unittest.TestCase):
    def test_real_ffmpeg_media_ripple_remove_undo_persistence_boundary(self):
        if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
            self.skipTest("FFmpeg and ffprobe are required")
        with isolated_directory() as root:
            source_a = _make_media(root, "source-a.mp4", "testsrc=size=320x180", 8.0)
            source_b = _make_media(root, "source-b.mp4", "color=c=blue:size=640x360", 8.0)
            source_a_hash = _sha256(source_a)
            source_b_hash = _sha256(source_b)
            metadata_a = probe_media(source_a).metadata()
            metadata_b = probe_media(source_b).metadata()
            project = Project.create_synchronized_multi(
                ((source_a, metadata_a), (source_b, metadata_b)),
                project_id="ripple-real-media",
            )
            timeline = project.timeline
            timeline.add_track("track-2")
            source_a_id = project.sources[0].source_id
            source_b_id = project.sources[1].source_id
            surviving_transform = VisualTransform(zoom=1.35, offset_x=24.0, offset_y=-12.0)
            removed_transform = VisualTransform(zoom=1.6, offset_x=-30.0, offset_y=15.0)
            surviving_triplicate = TriplicateGroup.create(
                surviving_transform,
                group_id="surviving-triplicate",
            )
            removed_triplicate = TriplicateGroup.create(
                removed_transform,
                group_id="removed-triplicate",
            )
            removed_track_two_triplicate = TriplicateGroup.create(
                removed_transform,
                group_id="removed-track-two-triplicate",
            )
            timeline.replace_track_blocks(
                "track-1",
                (
                    _block(
                        "a1",
                        source_a_id,
                        0,
                        1_000_000,
                        0,
                        1_000_000,
                        "track-1",
                        color_index=0,
                        state={"role": "surviving", "opaque": {"values": [1, 2, 3]}},
                        transform=surviving_transform,
                        triplicate=surviving_triplicate,
                    ),
                    _block(
                        "a2",
                        source_a_id,
                        1_000_000,
                        2_000_000,
                        2_000_000,
                        3_000_000,
                        "track-1",
                        color_index=1,
                        state={"role": "removed", "opaque": {"values": [4, 5]}},
                        transform=removed_transform,
                        triplicate=removed_triplicate,
                    ),
                    _block(
                        "b1",
                        source_b_id,
                        0,
                        1_000_000,
                        5_000_000,
                        6_000_000,
                        "track-1",
                        deleted=True,
                        color_index=2,
                        state={"role": "removed-excluded", "opaque": {"flag": True}},
                    ),
                    _block(
                        "a3", source_a_id, 2_000_000, 3_000_000, 8_000_000, 9_000_000, "track-1"
                    ),
                ),
            )
            timeline.replace_track_blocks(
                "track-2",
                (
                    _block(
                        "b2", source_b_id, 1_000_000, 2_000_000, 1_000_000, 2_000_000, "track-2"
                    ),
                    _block(
                        "b3",
                        source_b_id,
                        2_000_000,
                        4_000_000,
                        4_000_000,
                        6_000_000,
                        "track-2",
                        deleted=True,
                        color_index=4,
                        state={"role": "removed-excluded", "opaque": {"values": ["b3"]}},
                        transform=removed_transform,
                        triplicate=removed_track_two_triplicate,
                    ),
                    _block(
                        "b4",
                        source_b_id,
                        4_000_000,
                        5_000_000,
                        8_000_000,
                        9_000_000,
                        "track-2",
                        color_index=5,
                        state={"role": "surviving", "opaque": {"values": ["b4"]}},
                        transform=surviving_transform,
                    ),
                ),
            )
            project.set_playhead(8.5)
            before_payload = deepcopy(project.to_dict())
            before_timeline = deepcopy(timeline.to_dict())

            receipt = remove_segments(
                project,
                ("a2", "b1", "b3"),
                selection_ids=("a2", "b1", "b3"),
                focused_segment_id="b3",
            )
            self.assertEqual(
                [
                    (block.segment_id, block.timeline_start_ticks, block.timeline_end_ticks)
                    for block in timeline.track_by_id("track-1").blocks
                ],
                [("a1", 0, 1_000_000), ("a3", 6_000_000, 7_000_000)],
            )
            self.assertEqual(
                [
                    (block.segment_id, block.timeline_start_ticks, block.timeline_end_ticks)
                    for block in timeline.track_by_id("track-2").blocks
                ],
                [("b2", 1_000_000, 2_000_000), ("b4", 6_000_000, 7_000_000)],
            )
            self.assertEqual(project.duration_seconds, 7.0)
            self.assertLessEqual(project.playhead_seconds, project.duration_seconds)
            self.assertEqual(_sha256(source_a), source_a_hash)
            self.assertEqual(_sha256(source_b), source_b_hash)

            removed_timeline = deepcopy(timeline.to_dict())
            removed_revision = timeline.revision
            for invalid_ids in (("a1", "a1"), ("missing",)):
                with self.assertRaises(ProjectValidationError):
                    remove_segments(project, invalid_ids)
                self.assertEqual(timeline.to_dict(), removed_timeline)
                self.assertEqual(timeline.revision, removed_revision)

            receipt.before_state.tracks[0].blocks[0].state["opaque"]["values"].append("poison")
            second_receipt = remove_segments(
                project,
                ("a3", "b4"),
                selection_ids=("a3", "b4"),
                focused_segment_id="b4",
            )
            project_path = root / "removed.framestudio.json"
            save_project(project, project_path)
            reopened = load_project(project_path)
            self.assertEqual(
                {block.segment_id for block in reopened.timeline.blocks},
                {"a1", "b2"},
            )
            self.assertEqual(reopened.timeline.to_dict(), project.timeline.to_dict())
            with self.assertRaisesRegex(ProjectValidationError, "stale|unknown|history"):
                undo_remove(reopened, second_receipt)
            second_undo = undo_remove(project, second_receipt)
            self.assertEqual(second_undo.restored_selection_ids, ("a3", "b4"))
            self.assertEqual(timeline.to_dict(), removed_timeline)
            self.assertEqual(project.duration_seconds, 7.0)
            self.assertLessEqual(project.playhead_seconds, project.duration_seconds)
            first_undo = undo_remove(project, receipt)
            self.assertEqual(first_undo.restored_selection_ids, ("a2", "b1", "b3"))
            self.assertEqual(first_undo.focused_segment_id, "b3")
            self.assertEqual(timeline.to_dict(), before_timeline)
            restored_payload = project.to_dict()
            self.assertEqual(
                restored_payload["timeline"]["tracks"],
                before_payload["timeline"]["tracks"],
            )
            self.assertEqual(project.duration_seconds, 9.0)
            self.assertLessEqual(project.playhead_seconds, project.duration_seconds)
            self.assertEqual(_sha256(source_a), source_a_hash)
            self.assertEqual(_sha256(source_b), source_b_hash)

            stale_project = create_project_from_source(source_a)
            stale_project.convert_to_synchronized(confirm=True)
            stale_project.timeline.split_block(
                stale_project.timeline.blocks[0].segment_id,
                position_ticks=1_000_000,
                coordinate="timeline",
            )
            stale_id = stale_project.timeline.blocks[0].segment_id
            stale_receipt = remove_segments(stale_project, (stale_id,))
            remaining_id = stale_project.timeline.blocks[0].segment_id
            stale_project.timeline.set_deleted(remaining_id, True)
            with self.assertRaisesRegex(ProjectValidationError, "stale|unknown|history"):
                undo_remove(stale_project, stale_receipt)
            self.assertTrue(stale_project.timeline.find(remaining_id).deleted)

            move_project = create_project_from_source(source_a)
            move_project.convert_to_synchronized(confirm=True)
            move_project.timeline.split_block(
                move_project.timeline.blocks[0].segment_id,
                position_ticks=1_000_000,
                coordinate="timeline",
            )
            move_receipt = remove_segments(
                move_project,
                (move_project.timeline.blocks[0].segment_id,),
            )
            move_remaining_id = move_project.timeline.blocks[0].segment_id
            move_project.timeline.move_block(
                move_remaining_id,
                timeline_start_ticks=3_000_000,
            )
            with self.assertRaisesRegex(ProjectValidationError, "stale|unknown|history"):
                undo_remove(move_project, move_receipt)

            transform_project = create_project_from_source(source_a)
            transform_project.convert_to_synchronized(confirm=True)
            transform_project.timeline.split_block(
                transform_project.timeline.blocks[0].segment_id,
                position_ticks=1_000_000,
                coordinate="timeline",
            )
            transform_receipt = remove_segments(
                transform_project,
                (transform_project.timeline.blocks[0].segment_id,),
            )
            transform_remaining_id = transform_project.timeline.blocks[0].segment_id
            transform_project.timeline.set_visual_transform(
                [transform_remaining_id],
                VisualTransform(zoom=1.4, offset_x=20.0, offset_y=-10.0),
            )
            with self.assertRaisesRegex(ProjectValidationError, "stale|unknown|history"):
                undo_remove(transform_project, transform_receipt)

            import_project = create_project_from_source(source_a)
            import_project.convert_to_synchronized(confirm=True)
            import_receipt = remove_segments(
                import_project,
                (import_project.timeline.blocks[0].segment_id,),
            )
            import_project.append_sources((SourceReference.from_path(source_b, metadata_b),))
            with self.assertRaisesRegex(ProjectValidationError, "stale|unknown|history"):
                undo_remove(import_project, import_receipt)

            empty_project = create_project_from_source(source_a)
            empty_project.convert_to_synchronized(confirm=True)
            empty_id = empty_project.timeline.blocks[0].segment_id
            empty_receipt = remove_segments(empty_project, (empty_id,))
            self.assertEqual(empty_project.duration_seconds, 0.0)
            empty_path = root / "empty.framestudio.json"
            save_project(empty_project, empty_path)
            empty_reopened = load_project(empty_path)
            self.assertEqual(empty_reopened.timeline.blocks, ())
            self.assertEqual(empty_reopened.duration_seconds, 0.0)
            self.assertEqual(_sha256(source_a), source_a_hash)
            undo_remove(empty_project, empty_receipt)
            self.assertEqual(
                [block.segment_id for block in empty_project.timeline.blocks],
                [empty_id],
            )


if __name__ == "__main__":
    unittest.main()
