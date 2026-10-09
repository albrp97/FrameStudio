from __future__ import annotations

import shutil
import unittest
import uuid
from contextlib import contextmanager
from copy import deepcopy
from pathlib import Path

from framestudio.model import (
    Project,
    ProjectValidationError,
    Segment,
    TriplicateGroup,
    VisualTransform,
)
from framestudio.operations import remove_segments, undo_remove
from framestudio.persistence import load_project, save_project

_ARTIFACT_ROOT = Path(__file__).resolve().parent / ".ticket110-runtime"


@contextmanager
def isolated_directory():
    directory = _ARTIFACT_ROOT / f"case-{uuid.uuid4().hex}"
    directory.mkdir(parents=True, exist_ok=False)
    try:
        yield directory
    finally:
        shutil.rmtree(directory, ignore_errors=True)


def metadata(duration: float = 30.0) -> dict[str, object]:
    return {
        "duration_seconds": duration,
        "width": 320,
        "height": 180,
        "frame_rate": "10/1",
        "video_codec": "h264",
        "audio_codec": None,
        "format_name": "mp4",
    }


def _block(
    segment_id: str,
    source_id: str,
    source_start: int,
    source_end: int,
    timeline_start: int,
    timeline_end: int,
    track_id: str,
    *,
    deleted: bool = False,
    color_index: int | None = None,
    state: dict[str, object] | None = None,
    transform: VisualTransform | None = None,
    triplicate: TriplicateGroup | None = None,
) -> Segment:
    return Segment.create(
        source_start / 1_000_000,
        source_end / 1_000_000,
        segment_id=segment_id,
        block_id=f"block-{segment_id}",
        source_id=source_id,
        timeline_start_seconds=timeline_start / 1_000_000,
        timeline_end_seconds=timeline_end / 1_000_000,
        deleted=deleted,
        color_index=color_index,
        state=state,
        visual_transform=transform,
        triplicate=triplicate,
        track_id=track_id,
    )


def make_project(root: Path) -> Project:
    source = root / "source.mp4"
    source.write_bytes(b"ripple-removal-source")
    project = Project.create_synchronized(
        source,
        metadata(),
        project_id="ripple-removal-project",
    )
    timeline = project.timeline
    timeline.add_track("track-2")
    timeline.add_track("track-3")
    source_id = project.source.source_id
    transform = VisualTransform(zoom=1.35, offset_x=24.0, offset_y=-12.0)
    triplicate = TriplicateGroup.create(transform, group_id="triplicate-a")
    timeline.replace_track_blocks(
        "track-1",
        (
            _block(
                segment_id="a",
                source_id=source_id,
                source_start=0,
                source_end=2_000_000,
                timeline_start=0,
                timeline_end=2_000_000,
                track_id="track-1",
                color_index=0,
                state={"opaque": {"label": "keep", "values": [1, 2, 3]}},
                transform=transform,
                triplicate=triplicate,
            ),
            _block(
                segment_id="b",
                source_id=source_id,
                source_start=2_000_000,
                source_end=4_000_000,
                timeline_start=5_000_000,
                timeline_end=7_000_000,
                track_id="track-1",
                color_index=1,
            ),
            _block(
                segment_id="c",
                source_id=source_id,
                source_start=4_000_000,
                source_end=6_000_000,
                timeline_start=10_000_000,
                timeline_end=12_000_000,
                track_id="track-1",
                color_index=2,
            ),
            _block(
                segment_id="d",
                source_id=source_id,
                source_start=6_000_000,
                source_end=8_000_000,
                timeline_start=15_000_000,
                timeline_end=17_000_000,
                track_id="track-1",
                deleted=True,
                color_index=3,
            ),
            _block(
                segment_id="e",
                source_id=source_id,
                source_start=8_000_000,
                source_end=10_000_000,
                timeline_start=20_000_000,
                timeline_end=22_000_000,
                track_id="track-1",
                color_index=4,
            ),
        ),
    )
    timeline.replace_track_blocks(
        "track-2",
        (
            _block(
                segment_id="x",
                source_id=source_id,
                source_start=10_000_000,
                source_end=11_000_000,
                timeline_start=1_000_000,
                timeline_end=2_000_000,
                track_id="track-2",
                color_index=5,
            ),
            _block(
                segment_id="y",
                source_id=source_id,
                source_start=11_000_000,
                source_end=14_000_000,
                timeline_start=4_000_000,
                timeline_end=7_000_000,
                track_id="track-2",
                deleted=True,
                color_index=6,
            ),
            _block(
                segment_id="z",
                source_id=source_id,
                source_start=14_000_000,
                source_end=16_000_000,
                timeline_start=9_000_000,
                timeline_end=11_000_000,
                track_id="track-2",
                color_index=7,
            ),
            _block(
                segment_id="w",
                source_id=source_id,
                source_start=16_000_000,
                source_end=17_000_000,
                timeline_start=14_000_000,
                timeline_end=15_000_000,
                track_id="track-2",
                color_index=8,
            ),
        ),
    )
    timeline.replace_track_blocks(
        "track-3",
        (
            _block(
                segment_id="unaffected",
                source_id=source_id,
                source_start=18_000_000,
                source_end=19_000_000,
                timeline_start=2_000_000,
                timeline_end=3_000_000,
                track_id="track-3",
                color_index=9,
            ),
        ),
    )
    project.set_playhead(21.0)
    return project


def block_payload(project: Project) -> dict[str, dict[str, object]]:
    return {
        block.segment_id: block.to_dict(canonical_ticks=True, track_id=block.track_id)
        for block in project.timeline.blocks
    }


class EditorRippleRemovalTests(unittest.TestCase):
    def test_remove_ripples_each_affected_track_from_original_coordinates(self):
        with isolated_directory() as root:
            project = make_project(root)
            timeline = project.timeline
            before = deepcopy(block_payload(project))
            before_timeline = deepcopy(timeline.to_dict())
            before_revision = timeline.revision

            receipt = remove_segments(
                project,
                ("b", "d", "y"),
                selection_ids=("b", "d", "y"),
                focused_segment_id="d",
            )

            self.assertEqual(receipt.removed_segment_ids, ("b", "d", "y"))
            self.assertEqual(receipt.selection_ids, ("b", "d", "y"))
            self.assertEqual(receipt.focused_segment_id, "d")
            self.assertEqual(timeline.revision, before_revision + 1)
            self.assertEqual(
                [
                    (block.segment_id, block.timeline_start_ticks, block.timeline_end_ticks)
                    for block in timeline.track_by_id("track-1").blocks
                ],
                [
                    ("a", 0, 2_000_000),
                    ("c", 8_000_000, 10_000_000),
                    ("e", 16_000_000, 18_000_000),
                ],
            )
            self.assertEqual(
                [
                    (block.segment_id, block.timeline_start_ticks, block.timeline_end_ticks)
                    for block in timeline.track_by_id("track-2").blocks
                ],
                [
                    ("x", 1_000_000, 2_000_000),
                    ("z", 6_000_000, 8_000_000),
                    ("w", 11_000_000, 12_000_000),
                ],
            )
            self.assertEqual(
                timeline.track_by_id("track-3")
                .blocks[0]
                .to_dict(
                    canonical_ticks=True,
                    track_id="track-3",
                ),
                before["unaffected"],
            )
            self.assertEqual(timeline.find("a").to_dict(canonical_ticks=True), before["a"])
            self.assertEqual(
                timeline.find("c").source_start_ticks, before["c"]["source_start_ticks"]
            )
            self.assertEqual(timeline.find("c").source_end_ticks, before["c"]["source_end_ticks"])
            self.assertEqual(timeline.find("a").state, before["a"]["state"])
            self.assertEqual(
                timeline.find("a").visual_transform.to_dict(), before["a"]["visual_transform"]
            )
            self.assertEqual(timeline.find("a").triplicate.to_dict(), before["a"]["triplicate"])
            self.assertEqual(project.duration_seconds, 18.0)
            self.assertLessEqual(project.playhead_seconds, project.duration_seconds)
            self.assertEqual(timeline.active_track_id, "track-1")
            self.assertNotIn("b", {block.segment_id for block in timeline.blocks})
            self.assertNotIn("d", {block.segment_id for block in timeline.blocks})
            self.assertNotIn("y", {block.segment_id for block in timeline.blocks})

            undo_result = undo_remove(project, receipt)

            self.assertEqual(undo_result.restored_selection_ids, ("b", "d", "y"))
            self.assertEqual(undo_result.focused_segment_id, "d")
            self.assertEqual(timeline.to_dict(), before_timeline)
            self.assertEqual(project.duration_seconds, 22.0)
            self.assertLessEqual(project.playhead_seconds, project.duration_seconds)
            self.assertEqual(timeline.revision, before_revision + 2)

    def test_remove_and_undo_preserve_mutable_state_through_receipt_copy(self):
        with isolated_directory() as root:
            project = make_project(root)
            before = deepcopy(block_payload(project))
            receipt = remove_segments(project, ("b",))

            receipt.after_state.tracks[0].blocks[0].state["opaque"]["label"] = "tampered"
            receipt.before_state.tracks[0].blocks[0].state["opaque"]["values"].append(99)

            undo_remove(project, receipt)

            self.assertEqual(block_payload(project), before)
            self.assertEqual(
                project.timeline.find("a").state,
                {"opaque": {"label": "keep", "values": [1, 2, 3]}},
            )
            self.assertEqual(
                project.timeline.find("a").triplicate.group_id,
                "triplicate-a",
            )

    def test_multiple_undo_rebases_only_over_exact_history_owned_state(self):
        with isolated_directory() as root:
            project = make_project(root)
            before = deepcopy(project.timeline.to_dict())

            first = remove_segments(
                project,
                ("b",),
                selection_ids=("b",),
                focused_segment_id="b",
            )
            second = remove_segments(
                project,
                ("d",),
                selection_ids=("d",),
                focused_segment_id="d",
            )

            second_undo = undo_remove(project, second)
            self.assertEqual(second_undo.restored_selection_ids, ("d",))
            first_undo = undo_remove(project, first)
            self.assertEqual(first_undo.restored_selection_ids, ("b",))
            self.assertEqual(project.timeline.to_dict(), before)

            with self.assertRaisesRegex(ProjectValidationError, "stale|unknown|history"):
                undo_remove(project, second)

    def test_invalid_removals_are_atomic_and_do_not_consume_valid_receipt(self):
        with isolated_directory() as root:
            project = make_project(root)
            receipt = remove_segments(project, ("b",))
            before = deepcopy(project.timeline.to_dict())
            revision = project.timeline.revision

            for invalid_ids in ((), ("c", "c"), ("missing",)):
                with self.subTest(invalid_ids=invalid_ids):
                    with self.assertRaises(ProjectValidationError):
                        remove_segments(project, invalid_ids)
                    self.assertEqual(project.timeline.to_dict(), before)
                    self.assertEqual(project.timeline.revision, revision)

            undo_remove(project, receipt)
            self.assertIn("b", {block.segment_id for block in project.timeline.blocks})

    def test_public_operations_reject_invalid_project_before_timeline_mutation(self):
        with isolated_directory() as root:
            project = make_project(root)
            before = deepcopy(project.timeline.to_dict())
            revision = project.timeline.revision
            original_duration = project.duration_seconds
            project.duration_seconds += 1.0

            with self.assertRaises(ProjectValidationError):
                remove_segments(project, ("b",))
            self.assertEqual(project.timeline.to_dict(), before)
            self.assertEqual(project.timeline.revision, revision)

            project.duration_seconds = original_duration
            receipt = remove_segments(project, ("b",))
            removed = deepcopy(project.timeline.to_dict())
            removed_revision = project.timeline.revision
            removed_duration = project.duration_seconds
            project.duration_seconds += 1.0

            with self.assertRaises(ProjectValidationError):
                undo_remove(project, receipt)
            self.assertEqual(project.timeline.to_dict(), removed)
            self.assertEqual(project.timeline.revision, removed_revision)

            project.duration_seconds = removed_duration
            undo_remove(project, receipt)
            self.assertEqual(project.timeline.to_dict(), before)

    def test_non_removal_mutations_invalidate_receipts_without_overwriting_edits(self):
        mutations = (
            ("move", lambda project: project.timeline.move_block("c", 9_000_000)),
            (
                "split",
                lambda project: project.timeline.split_block(
                    "c",
                    position_ticks=9_000_000,
                    coordinate="timeline",
                ),
            ),
            (
                "paste",
                lambda project: project.timeline.paste_blocks(
                    project.timeline.copy_blocks(["c"]),
                    at_ticks=22_000_000,
                    target_track_id="track-1",
                ),
            ),
            ("track", lambda project: project.timeline.add_track("track-4")),
            ("delete", lambda project: project.timeline.set_deleted("c", True)),
            (
                "transform",
                lambda project: project.timeline.set_visual_transform(
                    ["c"],
                    VisualTransform(zoom=1.4),
                ),
            ),
        )
        for name, mutation in mutations:
            with self.subTest(mutation=name), isolated_directory() as root:
                project = make_project(root)
                receipt = remove_segments(project, ("b",))
                mutation(project)
                after_mutation = deepcopy(project.timeline.to_dict())

                with self.assertRaisesRegex(ProjectValidationError, "stale|unknown|history"):
                    undo_remove(project, receipt)
                self.assertEqual(project.timeline.to_dict(), after_mutation)

    def test_track_import_and_reopen_invalidate_receipts(self):
        with isolated_directory() as root:
            project = make_project(root)
            receipt = remove_segments(project, ("b",))
            incoming_path = root / "incoming.mp4"
            incoming_path.write_bytes(b"incoming")
            incoming = project.source.__class__.from_path(incoming_path, metadata(1.0))
            project.append_sources((incoming,))
            imported_state = deepcopy(project.timeline.to_dict())
            with self.assertRaisesRegex(ProjectValidationError, "stale|unknown|history"):
                undo_remove(project, receipt)
            self.assertEqual(project.timeline.to_dict(), imported_state)

            project = make_project(root)
            receipt = remove_segments(project, ("b",))
            destination = root / "reopened.framestudio.json"
            save_project(project, destination)
            reopened = load_project(destination)
            with self.assertRaisesRegex(ProjectValidationError, "stale|unknown|history"):
                undo_remove(reopened, receipt)

    def test_all_removed_timeline_is_valid_empty_and_round_trips(self):
        with isolated_directory() as root:
            project = make_project(root)
            all_ids = tuple(block.segment_id for block in project.timeline.blocks)
            source_path = Path(project.source.path)
            source_bytes = source_path.read_bytes()

            receipt = remove_segments(
                project,
                all_ids,
                selection_ids=all_ids,
                focused_segment_id=all_ids[-1],
            )

            self.assertEqual(project.timeline.blocks, ())
            self.assertEqual(project.timeline.editing_duration_ticks, 0)
            self.assertEqual(project.duration_seconds, 0.0)
            self.assertEqual(project.playhead_seconds, 0.0)
            project.validate()

            destination = root / "empty.framestudio.json"
            save_project(project, destination)
            reopened = load_project(destination)
            self.assertEqual(reopened.timeline.blocks, ())
            self.assertEqual(reopened.duration_seconds, 0.0)
            self.assertEqual(reopened.playhead_seconds, 0.0)
            self.assertEqual(source_path.read_bytes(), source_bytes)

            undo_remove(project, receipt)
            self.assertEqual(
                {block.segment_id for block in project.timeline.blocks},
                set(all_ids),
            )

    def test_history_evicts_oldest_receipt_at_twenty_entries(self):
        with isolated_directory() as root:
            source = root / "long-source.mp4"
            source.write_bytes(b"long-source")
            project = Project.create_synchronized(source, metadata(30.0))
            source_id = project.source.source_id
            blocks = tuple(
                _block(
                    segment_id=f"block-{index}",
                    source_id=source_id,
                    source_start=index * 1_000_000,
                    source_end=(index + 1) * 1_000_000,
                    timeline_start=index * 1_000_000,
                    timeline_end=(index + 1) * 1_000_000,
                    track_id="track-1",
                    color_index=index,
                )
                for index in range(21)
            )
            project.timeline.replace_track_blocks("track-1", blocks)
            receipts = []
            for _ in range(21):
                first_id = project.timeline.track_by_id("track-1").blocks[0].segment_id
                receipts.append(remove_segments(project, (first_id,)))

            with self.assertRaisesRegex(ProjectValidationError, "stale|unknown|history"):
                undo_remove(project, receipts[0])
            for receipt in reversed(receipts[1:]):
                undo_remove(project, receipt)

            self.assertEqual(
                [block.segment_id for block in project.timeline.track_by_id("track-1").blocks],
                [f"block-{index}" for index in range(1, 21)],
            )
            self.assertEqual(project.timeline.revision, 1 + 21 + 20)


if __name__ == "__main__":
    unittest.main()
