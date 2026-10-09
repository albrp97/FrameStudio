import os
import shutil
import unittest
import uuid
from contextlib import contextmanager
from pathlib import Path

from framestudio.model import (
    Project,
    ProjectValidationError,
    Segment,
    SourceReference,
    VisualTransform,
)
from framestudio.persistence import load_project, save_project

_ARTIFACT_ROOT = Path(
    os.environ.get(
        "FRAMESTUDIO_TICKET116_ARTIFACT_ROOT",
        str(Path(__file__).resolve().parent / ".ticket116-runtime"),
    )
)


@contextmanager
def isolated_directory():
    directory = _ARTIFACT_ROOT / f"case-{uuid.uuid4().hex}"
    directory.mkdir(parents=True, exist_ok=False)
    try:
        yield directory
    finally:
        shutil.rmtree(directory, ignore_errors=True)


def metadata(duration=12.0):
    return {
        "duration_seconds": duration,
        "width": 320,
        "height": 180,
        "frame_rate": "10/1",
        "video_codec": "h264",
        "audio_codec": None,
        "format_name": "mp4",
    }


def canonical_block(
    segment_id: str,
    *,
    track_id: str,
    source_id: str = "source-1",
    source_start_ticks: int,
    source_end_ticks: int,
    timeline_start_ticks: int,
    timeline_end_ticks: int,
    deleted: bool = False,
    state: dict | None = None,
) -> Segment:
    return Segment.from_canonical_dict(
        {
            "segment_id": segment_id,
            "block_id": f"block-{segment_id}",
            "track_id": track_id,
            "source_id": source_id,
            "source_start_ticks": source_start_ticks,
            "source_end_ticks": source_end_ticks,
            "timeline_start_ticks": timeline_start_ticks,
            "timeline_end_ticks": timeline_end_ticks,
            "deleted": deleted,
            "state": {} if state is None else state,
            "color_index": None,
            "visual_transform": VisualTransform().to_dict(),
            "triplicate": None,
        },
        expected_track_id=track_id,
    )


def make_project(root: Path) -> Project:
    source = root / "source.mp4"
    source.write_bytes(b"source-1")
    project = Project.create_synchronized(
        source,
        metadata(),
        project_id="placement-project",
    )
    source_id = project.source.source_id
    project.timeline.replace_track_blocks(
        "track-1",
        (
            canonical_block(
                "dragged",
                track_id="track-1",
                source_id=source_id,
                source_start_ticks=0,
                source_end_ticks=1_000_000,
                timeline_start_ticks=0,
                timeline_end_ticks=1_000_000,
                state={"preserve": "yes"},
            ),
            canonical_block(
                "occupied",
                track_id="track-1",
                source_id=source_id,
                source_start_ticks=1_000_000,
                source_end_ticks=3_000_000,
                timeline_start_ticks=2_000_000,
                timeline_end_ticks=4_000_000,
            ),
            canonical_block(
                "chained",
                track_id="track-1",
                source_id=source_id,
                source_start_ticks=3_000_000,
                source_end_ticks=5_000_000,
                timeline_start_ticks=4_500_000,
                timeline_end_ticks=6_500_000,
            ),
            canonical_block(
                "excluded",
                track_id="track-1",
                source_id=source_id,
                source_start_ticks=5_000_000,
                source_end_ticks=6_000_000,
                timeline_start_ticks=8_000_000,
                timeline_end_ticks=9_000_000,
                deleted=True,
            ),
        ),
    )
    project.timeline.add_track("track-2")
    return project


class EditorTrackPlacementTests(unittest.TestCase):
    def test_import_advances_revision_for_legacy_project_epochs(self):
        with isolated_directory() as root:
            first_path = root / "first.mp4"
            second_path = root / "second.mp4"
            third_path = root / "third.mp4"
            first_path.write_bytes(b"first")
            second_path.write_bytes(b"second")
            third_path.write_bytes(b"third")

            legacy_v4 = Project.create(
                first_path,
                metadata(2.0),
                project_id="legacy-v4-revision",
            )._migrate_legacy_to_v4()
            v2 = Project.create(first_path, metadata(2.0), project_id="v2-revision")
            v3 = Project.create_multi(
                ((first_path, metadata(2.0)),),
                project_id="v3-revision",
            )

            for project, incoming_path in (
                (legacy_v4, second_path),
                (v2, second_path),
                (v3, third_path),
            ):
                with self.subTest(schema=project.schema_version):
                    project.timeline.set_deleted(project.timeline.blocks[0].segment_id, True)
                    before_import = project.timeline.revision
                    incoming = SourceReference.from_path(
                        incoming_path,
                        metadata(1.0),
                    )

                    project.append_sources((incoming,))

                    self.assertEqual(project.timeline.revision, before_import + 1)

    def test_move_block_uses_earliest_fit_and_preserves_occupied_blocks(self):
        with isolated_directory() as root:
            project = make_project(root)
            timeline = project.timeline
            dragged_before = timeline.find("dragged")
            occupied_before = timeline.find("occupied")
            chained_before = timeline.find("chained")
            excluded_before = timeline.find("excluded")
            revision = timeline.revision

            changed = timeline.move_block("dragged", 2_500_000)

            self.assertTrue(changed)
            self.assertEqual(timeline.revision, revision + 1)
            dragged = timeline.find("dragged")
            self.assertEqual(
                (dragged.timeline_start_ticks, dragged.timeline_end_ticks),
                (6_500_000, 7_500_000),
            )
            self.assertEqual(dragged.source_start_ticks, dragged_before.source_start_ticks)
            self.assertEqual(dragged.source_end_ticks, dragged_before.source_end_ticks)
            self.assertEqual(dragged.segment_id, dragged_before.segment_id)
            self.assertEqual(dragged.block_id, dragged_before.block_id)
            self.assertEqual(dragged.state, dragged_before.state)
            self.assertEqual(timeline.find("occupied"), occupied_before)
            self.assertEqual(timeline.find("chained"), chained_before)
            self.assertEqual(timeline.find("excluded"), excluded_before)

            touching_revision = timeline.revision
            self.assertTrue(timeline.move_block("dragged", 7_000_000))
            self.assertEqual(timeline.find("dragged").timeline_start_ticks, 7_000_000)
            self.assertEqual(timeline.revision, touching_revision + 1)

    def test_move_block_can_cross_tracks_without_moving_existing_occupancy(self):
        with isolated_directory() as root:
            project = make_project(root)
            timeline = project.timeline
            revision = timeline.revision

            self.assertTrue(
                timeline.move_block(
                    "occupied",
                    1_000_000,
                    target_track_id="track-2",
                )
            )

            self.assertEqual(timeline.revision, revision + 1)
            self.assertNotIn(
                "occupied", {block.segment_id for block in timeline.track_by_id("track-1").blocks}
            )
            moved = timeline.track_by_id("track-2").blocks
            self.assertEqual([block.segment_id for block in moved], ["occupied"])
            self.assertEqual(moved[0].track_id, "track-2")
            self.assertEqual(moved[0].timeline_start_ticks, 1_000_000)
            self.assertEqual(timeline.find("dragged").timeline_start_ticks, 0)

    def test_noop_and_invalid_move_leave_revision_and_state_unchanged(self):
        with isolated_directory() as root:
            project = make_project(root)
            timeline = project.timeline
            before = timeline.to_dict()
            revision = timeline.revision

            self.assertFalse(timeline.move_block("dragged", 0))
            self.assertEqual(timeline.to_dict(), before)
            self.assertEqual(timeline.revision, revision)

            with self.assertRaisesRegex(ProjectValidationError, "Unknown track"):
                timeline.move_block("dragged", 0, target_track_id="track-unknown")
            self.assertEqual(timeline.to_dict(), before)
            self.assertEqual(timeline.revision, revision)

    def test_split_copy_and_paste_are_single_atomic_tick_operations(self):
        with isolated_directory() as root:
            project = make_project(root)
            timeline = project.timeline

            revision = timeline.revision
            first, second = timeline.split_block(
                "occupied",
                position_ticks=3_000_000,
                coordinate="timeline",
            )
            self.assertEqual(timeline.revision, revision + 1)
            self.assertEqual(
                [
                    (block.timeline_start_ticks, block.timeline_end_ticks)
                    for block in (first, second)
                ],
                [(2_000_000, 3_000_000), (3_000_000, 4_000_000)],
            )
            self.assertEqual(first.track_id, "track-1")
            self.assertEqual(second.track_id, "track-1")

            copies = timeline.copy_blocks([first.segment_id, second.segment_id])
            self.assertNotEqual(
                {copy.segment_id for copy in copies},
                {first.segment_id, second.segment_id},
            )
            paste_revision = timeline.revision
            pasted = timeline.paste_blocks(
                copies,
                at_ticks=9_000_000,
                target_track_id="track-1",
            )
            self.assertEqual(timeline.revision, paste_revision + 1)
            self.assertEqual(
                [(block.timeline_start_ticks, block.timeline_end_ticks) for block in pasted],
                [(9_000_000, 10_000_000), (10_000_000, 11_000_000)],
            )
            self.assertEqual([block.track_id for block in pasted], ["track-1", "track-1"])

    def test_track_lifecycle_and_active_import_are_atomic_and_persisted(self):
        with isolated_directory() as root:
            project = make_project(root)
            project.timeline.set_active_track("track-2")
            second_source_path = root / "source-2.mp4"
            second_source_path.write_bytes(b"source-2")
            second_source = SourceReference.from_path(second_source_path, metadata(2.0))

            revision = project.timeline.revision
            project.append_sources((second_source,))

            self.assertEqual(project.timeline.revision, revision + 1)
            imported = [
                block
                for block in project.timeline.blocks
                if block.source_id == second_source.source_id
            ]
            self.assertEqual(len(imported), 1)
            self.assertEqual(imported[0].track_id, "track-2")
            self.assertEqual(imported[0].timeline_start_ticks, 0)
            self.assertEqual(imported[0].timeline_end_ticks, 2_000_000)
            self.assertEqual(project.timeline.active_track_id, "track-2")
            self.assertEqual(project.duration_seconds, 9.0)

            project.timeline.add_track("track-3")
            self.assertEqual(project.timeline.track_ids, ("track-1", "track-2", "track-3"))
            project.timeline.remove_track("track-3")
            self.assertEqual(project.timeline.track_ids, ("track-1", "track-2"))
            with self.assertRaisesRegex(ProjectValidationError, "Only empty tracks"):
                project.timeline.remove_track("track-1")

            destination = root / "placement.framestudio.json"
            save_project(project, destination)
            restored = load_project(destination)
            self.assertEqual(restored.to_dict(), project.to_dict())
            self.assertEqual(restored.timeline.revision, 0)

    def test_duration_playhead_and_failure_atomicity_follow_timeline_commit(self):
        with isolated_directory() as root:
            project = make_project(root)
            project.set_playhead(12.0)
            self.assertEqual(project.playhead_seconds, 9.0)
            timeline = project.timeline
            before = timeline.to_dict()
            revision = timeline.revision

            with self.assertRaisesRegex(ProjectValidationError, "overlaps"):
                source_id = project.source.source_id
                timeline.replace_track_blocks(
                    "track-1",
                    (
                        canonical_block(
                            "bad-a",
                            track_id="track-1",
                            source_id=source_id,
                            source_start_ticks=0,
                            source_end_ticks=1_000_000,
                            timeline_start_ticks=0,
                            timeline_end_ticks=1_000_000,
                        ),
                        canonical_block(
                            "bad-b",
                            track_id="track-1",
                            source_id=source_id,
                            source_start_ticks=1_000_000,
                            source_end_ticks=2_000_000,
                            timeline_start_ticks=500_000,
                            timeline_end_ticks=1_500_000,
                        ),
                    ),
                )
            self.assertEqual(timeline.to_dict(), before)
            self.assertEqual(timeline.revision, revision)
            self.assertEqual(project.duration_seconds, 9.0)
            self.assertEqual(project.playhead_seconds, 9.0)

            timeline.replace_track_blocks(
                "track-1",
                tuple(
                    block
                    for block in timeline.track_by_id("track-1").blocks
                    if block.segment_id != "excluded"
                ),
            )
            self.assertEqual(project.duration_seconds, 6.5)
            self.assertEqual(project.playhead_seconds, 6.5)


if __name__ == "__main__":
    unittest.main()
