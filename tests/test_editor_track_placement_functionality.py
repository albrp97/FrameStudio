import hashlib
import shutil
import subprocess
import unittest
from pathlib import Path

from framestudio.media import probe_media
from framestudio.model import ProjectValidationError, SourceReference, VisualTransform
from framestudio.operations import (
    create_project_from_source,
    move_segment,
    paste_segments,
)
from framestudio.persistence import load_project, save_project
from tests.test_editor_track_placement import isolated_directory


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_source(root: Path, name: str, duration: float) -> Path:
    path = root / name
    subprocess.run(
        [
            shutil.which("ffmpeg") or "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"testsrc=size=320x180:rate=10:duration={duration}",
            "-an",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            str(path),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )
    return path


class TrackPlacementFunctionalityTests(unittest.TestCase):
    def test_persisted_real_media_track_editing_round_trips_exactly(self):
        if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
            self.skipTest("FFmpeg and ffprobe are required")
        with isolated_directory() as root:
            source = make_source(root, "source-1.mp4", 4.0)
            second_source_path = make_source(root, "source-2.mp4", 2.0)
            source_hash = sha256(source)
            second_source_hash = sha256(second_source_path)
            self.assertGreater(probe_media(source).duration_seconds, 0.0)

            project = create_project_from_source(source)
            project.convert_to_synchronized(confirm=True)
            timeline = project.timeline
            timeline.add_track("track-2")
            timeline.add_track("track-3")
            timeline.add_track("track-4")
            self.assertEqual(timeline.track_count, 4)
            with self.assertRaisesRegex(ProjectValidationError, "at most 4"):
                timeline.add_track("track-5")

            original = timeline.blocks[0]
            first, second = timeline.split_block(
                original.segment_id,
                position_ticks=1_000_000,
                coordinate="timeline",
            )
            timeline.set_deleted(second.segment_id, True)
            source_ranges = {
                first.segment_id: (first.source_start_ticks, first.source_end_ticks),
                second.segment_id: (second.source_start_ticks, second.source_end_ticks),
            }
            timeline.set_visual_transform([first.segment_id], VisualTransform(zoom=1.2))
            timeline.enable_triplicate([first.segment_id])

            self.assertTrue(
                move_segment(
                    project,
                    first.segment_id,
                    timeline_start_ticks=1_500_000,
                )
            )
            moved = timeline.find(first.segment_id)
            self.assertEqual(
                (moved.timeline_start_ticks, moved.timeline_end_ticks),
                (4_000_000, 5_000_000),
            )
            self.assertEqual(timeline.find(second.segment_id).timeline_start_ticks, 1_000_000)
            self.assertEqual(project.duration_seconds, 5.0)
            self.assertEqual(
                (moved.source_start_ticks, moved.source_end_ticks),
                source_ranges[first.segment_id],
            )

            copies = timeline.copy_blocks([first.segment_id])
            pasted_at_five = paste_segments(
                project,
                copies,
                at_ticks=5_000_000,
                target_track_id="track-1",
            )
            pasted_at_six_five = paste_segments(
                project,
                copies,
                at_ticks=6_500_000,
                target_track_id="track-1",
            )
            self.assertEqual(
                [
                    (block.timeline_start_ticks, block.timeline_end_ticks)
                    for block in (*pasted_at_five, *pasted_at_six_five)
                ],
                [
                    (5_000_000, 6_000_000),
                    (6_500_000, 7_500_000),
                ],
            )
            for pasted in (*pasted_at_five, *pasted_at_six_five):
                self.assertNotEqual(pasted.segment_id, first.segment_id)
                self.assertEqual(
                    (pasted.source_start_ticks, pasted.source_end_ticks),
                    source_ranges[first.segment_id],
                )
                self.assertEqual(pasted.visual_transform, moved.visual_transform)
                self.assertIsNotNone(pasted.triplicate)
                self.assertNotEqual(
                    pasted.triplicate.group_id,
                    moved.triplicate.group_id,
                )

            timeline.set_visual_transform(
                [pasted_at_five[0].segment_id],
                VisualTransform(zoom=1.3),
            )
            timeline.disable_triplicate([pasted_at_five[0].segment_id])
            self.assertEqual(timeline.find(first.segment_id).visual_transform.zoom, 1.2)
            self.assertIsNotNone(timeline.find(first.segment_id).triplicate)
            self.assertIsNone(timeline.find(pasted_at_five[0].segment_id).triplicate)

            existing_placements = {
                segment_id: (
                    timeline.find(segment_id).timeline_start_ticks,
                    timeline.find(segment_id).timeline_end_ticks,
                )
                for segment_id in (
                    first.segment_id,
                    pasted_at_five[0].segment_id,
                    pasted_at_six_five[0].segment_id,
                )
            }
            revision_before_long_move = timeline.revision
            self.assertTrue(
                move_segment(
                    project,
                    second.segment_id,
                    timeline_start_ticks=4_000_000,
                )
            )
            moved_long = timeline.find(second.segment_id)
            self.assertEqual(
                (moved_long.timeline_start_ticks, moved_long.timeline_end_ticks),
                (7_500_000, 10_500_000),
            )
            self.assertEqual(
                (moved_long.source_start_ticks, moved_long.source_end_ticks),
                source_ranges[second.segment_id],
            )
            self.assertEqual(timeline.revision, revision_before_long_move + 1)
            for segment_id, placement in existing_placements.items():
                self.assertEqual(
                    (
                        timeline.find(segment_id).timeline_start_ticks,
                        timeline.find(segment_id).timeline_end_ticks,
                    ),
                    placement,
                )
            self.assertEqual(timeline.included_duration_ticks, 3_000_000)
            self.assertEqual(timeline.editing_duration_ticks, 10_500_000)
            self.assertEqual(timeline.final_duration_ticks, 7_500_000)
            self.assertEqual(project.duration_seconds, 10.5)

            touching_revision = timeline.revision
            self.assertFalse(
                move_segment(
                    project,
                    pasted_at_five[0].segment_id,
                    timeline_start_ticks=5_000_000,
                )
            )
            self.assertEqual(timeline.revision, touching_revision)

            timeline.set_active_track("track-2")
            self.assertTrue(
                move_segment(
                    project,
                    first.segment_id,
                    timeline_start_ticks=0,
                    target_track_id="track-2",
                )
            )
            moved_cross_track = timeline.find(first.segment_id)
            self.assertEqual(moved_cross_track.track_id, "track-2")
            self.assertEqual(moved_cross_track.timeline_start_ticks, 0)
            self.assertEqual(
                (moved_cross_track.source_start_ticks, moved_cross_track.source_end_ticks),
                source_ranges[first.segment_id],
            )
            cross_track_paste = paste_segments(
                project,
                copies,
                at_ticks=2_000_000,
                target_track_id="track-2",
            )
            self.assertEqual(cross_track_paste[0].track_id, "track-2")
            self.assertEqual(cross_track_paste[0].timeline_start_ticks, 2_000_000)
            with self.assertRaisesRegex(ProjectValidationError, "Only empty tracks"):
                timeline.remove_track("track-1")
            timeline.remove_track("track-4")
            self.assertEqual(timeline.track_ids, ("track-1", "track-2", "track-3"))

            imported = SourceReference.from_path(
                second_source_path,
                probe_media(second_source_path).metadata(),
            )
            project.append_sources((imported,))
            imported_blocks = [
                block for block in project.timeline.blocks if block.source_id == imported.source_id
            ]
            self.assertEqual(len(imported_blocks), 1)
            self.assertEqual(imported_blocks[0].track_id, "track-2")
            self.assertEqual(
                (imported_blocks[0].timeline_start_ticks, imported_blocks[0].timeline_end_ticks),
                (3_000_000, 5_000_000),
            )

            project_path = root / "edited.framestudio.json"
            save_project(project, project_path)
            persisted_payload = project.to_dict()
            restored = load_project(project_path)
            self.assertEqual(restored.to_dict(), persisted_payload)
            self.assertEqual(restored.timeline.revision, 0)
            self.assertEqual(sha256(source), source_hash)
            self.assertEqual(sha256(second_source_path), second_source_hash)

            before = restored.to_dict()
            revision = restored.timeline.revision
            with self.assertRaisesRegex(ProjectValidationError, "Unknown track"):
                move_segment(
                    restored,
                    first.segment_id,
                    0,
                    target_track_id="track-unknown",
                )
            self.assertEqual(restored.to_dict(), before)
            self.assertEqual(restored.timeline.revision, revision)


if __name__ == "__main__":
    unittest.main()
