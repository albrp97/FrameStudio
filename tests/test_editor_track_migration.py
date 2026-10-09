import copy
import json
import tempfile
import unittest
from contextlib import contextmanager
from dataclasses import replace
from pathlib import Path

from framestudio.model import Project, ProjectValidationError, Segment, SegmentTimeline
from framestudio.persistence import load_project, save_project


@contextmanager
def isolated_directory():
    with tempfile.TemporaryDirectory(
        dir=Path(__file__).resolve().parent,
        prefix=".ticket115-",
    ) as raw_path:
        yield Path(raw_path)


def metadata(duration=10.0):
    return {
        "duration_seconds": duration,
        "width": 320,
        "height": 180,
        "frame_rate": "10/1",
        "video_codec": "h264",
        "audio_codec": None,
        "format_name": "mp4",
    }


def make_project(root: Path) -> Project:
    source = root / "source.mp4"
    source.write_bytes(b"track-migration-fixture")
    return Project.create(source, metadata(), project_id="project-115")


class EditorTrackMigrationTests(unittest.TestCase):
    def test_synchronized_delete_tail_saves_and_reopens_with_editing_duration(self):
        with isolated_directory() as root:
            source = root / "source.mp4"
            source.write_bytes(b"source")
            project = Project.create_synchronized(
                source,
                metadata(),
                project_id="delete-tail-115",
            )
            project.timeline.set_deleted(project.timeline.blocks[0].segment_id, True)
            destination = root / "delete-tail.framestudio.json"

            save_project(project, destination)
            restored = load_project(destination)

            self.assertEqual(project.duration_seconds, 10.0)
            self.assertEqual(project.timeline.editing_duration_ticks, 10_000_000)
            self.assertEqual(project.timeline.final_duration_ticks, 0)
            self.assertEqual(restored.duration_seconds, 10.0)
            self.assertEqual(restored.playhead_seconds, 0.0)
            self.assertEqual(restored.timeline.editing_duration_ticks, 10_000_000)
            self.assertEqual(restored.timeline.final_duration_ticks, 0)

    def test_sub_microsecond_source_metadata_round_trips_with_canonical_ticks(self):
        with isolated_directory() as root:
            source = root / "source.mp4"
            source.write_bytes(b"source")
            project = Project.create_synchronized(
                source,
                metadata(10.0000004),
                project_id="rounded-source-115",
            )
            destination = root / "rounded-source.framestudio.json"

            save_project(project, destination)
            restored = load_project(destination)

            self.assertEqual(
                restored.source.metadata["duration_seconds"],
                10.0000004,
            )
            self.assertEqual(
                restored.timeline.to_dict()["source_durations_ticks"][restored.source.source_id],
                10_000_000,
            )
            self.assertEqual(
                restored.timeline.blocks[0].source_end_ticks,
                10_000_000,
            )

    def test_legacy_load_normalizes_to_v4_legacy_ripple_without_absolute_conversion(self):
        with isolated_directory() as root:
            project = make_project(root)
            project.timeline.split(4.0)
            project.timeline.split(7.0)
            project.timeline.set_deleted(project.timeline.segment_items[1].segment_id, True)
            legacy_payload = project.to_dict()
            legacy_payload["schema_version"] = 2

            restored = Project.from_dict(legacy_payload)

            self.assertEqual(restored.schema_version, 4)
            self.assertEqual(restored.timeline.timing_mode, "legacy-ripple")
            self.assertEqual(restored.timeline.track_ids, ("track-1",))
            self.assertEqual(restored.duration_seconds, 10.0)
            self.assertEqual(restored.timeline.final_duration_seconds, 7.0)
            self.assertTrue(restored.timeline.blocks[1].deleted)
            with self.assertRaisesRegex(ProjectValidationError, "confirmation"):
                restored.timeline.add_track("track-2")
            with self.assertRaisesRegex(ProjectValidationError, "confirmation"):
                restored.convert_to_synchronized()

            normalized = restored.to_dict()
            reopened = Project.from_dict(normalized)
            self.assertEqual(reopened.to_dict(), normalized)
            self.assertEqual(reopened.timeline.timing_mode, "legacy-ripple")

    def test_legacy_ripple_public_edit_operations_keep_track_identity(self):
        with isolated_directory() as root:
            project = make_project(root)
            project.timeline.split(4.0)
            project.timeline.split(7.0)
            legacy_payload = project.to_dict()
            legacy_payload["schema_version"] = 2
            restored = Project.from_dict(legacy_payload)

            original_ids = [block.segment_id for block in restored.timeline.blocks]
            restored.timeline.split(2.0)
            self.assertTrue(all(block.track_id == "track-1" for block in restored.timeline.blocks))
            self.assertEqual(restored.timeline.timeline_duration_seconds, 10.0)
            self.assertTrue(
                restored.timeline.move_block(restored.timeline.blocks[0].segment_id, "right")
            )
            copied = restored.timeline.copy_blocks([restored.timeline.blocks[0].segment_id])
            restored.timeline.paste_blocks(copied)
            self.assertTrue(restored.timeline.blocks)
            self.assertNotEqual(
                original_ids, [block.segment_id for block in restored.timeline.blocks]
            )

    def test_legacy_one_source_normalization_keeps_single_source_projection(self):
        with isolated_directory() as root:
            project = make_project(root)
            project.timeline.split(4.0)
            legacy_payload = project.to_dict()
            legacy_payload["schema_version"] = 2

            restored = Project.from_dict(legacy_payload)

            self.assertEqual(restored.schema_version, 4)
            self.assertEqual(restored.timeline.timing_mode, "legacy-ripple")
            self.assertFalse(restored.timeline.mixed_source)

    def test_ordinary_one_track_project_stays_legacy_until_explicit_conversion(self):
        with isolated_directory() as root:
            project = make_project(root)
            project.timeline.split(4.0)
            project.timeline.split(7.0)
            project.timeline.set_deleted(project.timeline.segment_items[1].segment_id, True)

            self.assertEqual(project.schema_version, 2)
            self.assertEqual(project.timeline.edited_duration_seconds, 7.0)

            with self.assertRaisesRegex(
                ProjectValidationError,
                "confirmation",
            ):
                project.convert_to_synchronized()

            project.convert_to_synchronized(confirm=True)

            self.assertEqual(project.schema_version, 4)
            self.assertEqual(project.timeline.timing_mode, "absolute")
            self.assertEqual(project.timeline.track_ids, ("track-1",))
            self.assertEqual(project.timeline.editing_duration_ticks, 10_000_000)
            self.assertEqual(project.timeline.included_duration_ticks, 7_000_000)
            self.assertEqual(project.timeline.final_duration_ticks, 10_000_000)
            self.assertEqual(
                [block.segment_id for block in project.timeline.blocks],
                [block.segment_id for block in project.timeline.segment_items],
            )

    def test_synchronized_tracks_round_trip_and_preserve_empty_tracks(self):
        with isolated_directory() as root:
            source = root / "source.mp4"
            source.write_bytes(b"source")
            project = Project.create_synchronized(
                source,
                metadata(),
                project_id="synchronized-115",
            )

            self.assertEqual(project.schema_version, 4)
            self.assertEqual(project.timeline.timing_mode, "absolute")
            self.assertEqual(project.timeline.track_ids, ("track-1",))
            self.assertEqual(project.timeline.mutation_revision, 0)

            project.timeline.add_track("track-2")
            project.timeline.add_track("track-3")
            project.timeline.set_active_track("track-3")
            self.assertEqual(project.timeline.revision, 2)

            payload = project.to_dict()
            self.assertEqual(
                [track["track_id"] for track in payload["timeline"]["tracks"]],
                ["track-1", "track-2", "track-3"],
            )
            self.assertEqual(payload["timeline"]["active_track_id"], "track-3")
            self.assertNotIn("populated_track_count", payload["timeline"])
            self.assertEqual(
                [track["blocks"] for track in payload["timeline"]["tracks"][1:]],
                [[], []],
            )

            destination = root / "synchronized.framestudio.json"
            save_project(project, destination)
            restored = load_project(destination)

            self.assertEqual(restored.to_dict(), payload)
            self.assertEqual(restored.timeline.track_ids, ("track-1", "track-2", "track-3"))
            self.assertEqual(restored.timeline.active_track_id, "track-3")
            self.assertEqual(restored.timeline.populated_track_count, 1)

    def test_synchronized_delete_preserves_absolute_occupancy_and_track_identity(self):
        with isolated_directory() as root:
            (root / "source.mp4").write_bytes(b"source")
            project = Project.create_synchronized(
                root / "source.mp4",
                metadata(),
                project_id="delete-115",
            )
            project.timeline.add_track("track-2")
            first = project.timeline.track_by_id("track-1").blocks[0]
            project.timeline.set_deleted(first.segment_id, True)

            deleted = project.timeline.track_by_id("track-1").blocks[0]
            self.assertTrue(deleted.deleted)
            self.assertEqual(deleted.track_id, "track-1")
            self.assertEqual(deleted.timeline_start, 0.0)
            self.assertEqual(deleted.timeline_end, 10.0)
            self.assertEqual(project.timeline.editing_duration_seconds, 10.0)
            self.assertEqual(project.timeline.included_duration_seconds, 0.0)
            self.assertEqual(project.timeline.final_duration_seconds, 0.0)
            self.assertEqual(
                project.timeline.legacy_active_intervals("track-1"),
                (),
            )
            with self.assertRaisesRegex(ProjectValidationError, "require a track_id"):
                project.timeline.legacy_active_intervals()

    def test_synchronized_track_replacement_preserves_source_ranges_atomically(self):
        with isolated_directory() as root:
            source = root / "source.mp4"
            source.write_bytes(b"source")
            project = Project.create_synchronized(
                source,
                metadata(),
                project_id="immutable-range-115",
            )
            original = project.timeline.track_by_id("track-1").blocks[0]
            changed_range = Segment.create(
                1.0,
                3.0,
                segment_id=original.segment_id,
                block_id=original.block_id,
                source_id=original.source_id,
                timeline_start_seconds=0.0,
                timeline_end_seconds=2.0,
                track_id="track-1",
            )
            before = project.to_dict()

            with self.assertRaisesRegex(ProjectValidationError, "immutable"):
                project.timeline.replace_track_blocks("track-1", (changed_range,))

            self.assertEqual(project.to_dict(), before)

    def test_v4_requires_ticks_and_rejects_same_track_overlap_including_excluded_blocks(self):
        with isolated_directory() as root:
            (root / "source.mp4").write_bytes(b"source")
            project = Project.create_synchronized(
                root / "source.mp4",
                metadata(),
                project_id="validation-115",
            )
            payload = project.to_dict()
            first = payload["timeline"]["tracks"][0]["blocks"][0]
            first["deleted"] = False
            overlapping = copy.deepcopy(first)
            overlapping["segment_id"] = "overlap"
            overlapping["block_id"] = "overlap"
            overlapping["deleted"] = True
            overlapping["source_start_ticks"] = 2_000_000
            overlapping["source_end_ticks"] = 4_000_000
            overlapping["timeline_start_ticks"] = 1_000_000
            overlapping["timeline_end_ticks"] = 3_000_000
            payload["timeline"]["tracks"][0]["blocks"].append(overlapping)

            with self.assertRaisesRegex(ProjectValidationError, "overlap"):
                Project.from_dict(payload)

            missing_ticks = project.to_dict()
            block = missing_ticks["timeline"]["tracks"][0]["blocks"][0]
            del block["timeline_start_ticks"]
            with self.assertRaisesRegex(ProjectValidationError, "timeline_start_ticks"):
                Project.from_dict(missing_ticks)

    def test_v4_rejects_boolean_version_and_unhashable_timing_mode_as_project_errors(self):
        with isolated_directory() as root:
            (root / "source.mp4").write_bytes(b"source")
            project = Project.create_synchronized(
                root / "source.mp4",
                metadata(),
                project_id="strict-v4-115",
            )
            payload = project.to_dict()

            boolean_version = copy.deepcopy(payload)
            boolean_version["timeline"]["timeline_model_version"] = True
            with self.assertRaisesRegex(ProjectValidationError, r"(?i)timeline.*version"):
                Project.from_dict(boolean_version)
            with self.assertRaisesRegex(ProjectValidationError, r"(?i)timeline.*version"):
                SegmentTimeline.from_dict(boolean_version["timeline"])
            with self.assertRaisesRegex(ProjectValidationError, r"(?i)timeline.*version"):
                replace(project.timeline, timeline_model_version=True)

            for invalid_timing_mode in ([], {}):
                malformed = copy.deepcopy(payload)
                malformed["timeline"]["timing_mode"] = invalid_timing_mode
                with self.assertRaisesRegex(ProjectValidationError, "timing_mode"):
                    Project.from_dict(malformed)
                with self.assertRaisesRegex(ProjectValidationError, "timing_mode"):
                    SegmentTimeline.from_dict(malformed["timeline"])

    def test_cross_track_overlap_is_valid_and_legacy_conversion_preserves_ids_and_state(self):
        with isolated_directory() as root:
            project = make_project(root)
            project.timeline.split(4.0)
            project.timeline.split(7.0)
            changed = replace(
                project.timeline.segment_items[1],
                deleted=True,
                state={"marker": "preserve"},
            )
            project.timeline._replace_segments(
                tuple(
                    changed if segment is project.timeline.segment_items[1] else segment
                    for segment in project.timeline.segment_items
                )
            )
            project.timeline.validate()
            before = project.to_dict()
            before_ids = [segment["segment_id"] for segment in before["timeline"]["segments"]]

            project.convert_to_synchronized(confirm=True)
            payload = project.to_dict()
            second_track = {
                "track_id": "track-2",
                "blocks": [
                    {
                        **copy.deepcopy(payload["timeline"]["tracks"][0]["blocks"][0]),
                        "segment_id": "track-2-block",
                        "block_id": "track-2-block",
                        "track_id": "track-2",
                        "timeline_start_ticks": 1_000_000,
                        "timeline_end_ticks": (
                            1_000_000
                            + payload["timeline"]["tracks"][0]["blocks"][0]["source_end_ticks"]
                            - payload["timeline"]["tracks"][0]["blocks"][0]["source_start_ticks"]
                        ),
                    }
                ],
            }
            payload["timeline"]["tracks"].append(second_track)

            restored = Project.from_dict(payload)

            self.assertEqual(restored.timeline.track_ids, ("track-1", "track-2"))
            self.assertEqual(
                [block.segment_id for block in restored.timeline.track_by_id("track-1").blocks],
                before_ids,
            )
            self.assertEqual(
                restored.timeline.track_by_id("track-1").blocks[1].state,
                {"marker": "preserve"},
            )
            self.assertEqual(restored.timeline.populated_track_count, 2)

    def test_invalid_track_reference_does_not_replace_existing_project_file(self):
        with isolated_directory() as root:
            (root / "source.mp4").write_bytes(b"source")
            project = Project.create_synchronized(
                root / "source.mp4",
                metadata(),
                project_id="atomic-115",
            )
            destination = root / "project.framestudio.json"
            save_project(project, destination)
            before_bytes = destination.read_bytes()

            invalid = json.loads(before_bytes)
            invalid["timeline"]["tracks"][0]["blocks"][0]["track_id"] = "missing"
            invalid_path = root / "invalid.framestudio.json"
            invalid_path.write_text(json.dumps(invalid), encoding="utf-8")

            with self.assertRaises(ProjectValidationError):
                Project.from_dict(invalid)

            self.assertEqual(destination.read_bytes(), before_bytes)
            self.assertEqual(load_project(destination).to_dict(), project.to_dict())

    def test_gaps_and_cross_track_overlap_are_distinct_from_included_sum(self):
        with isolated_directory() as root:
            root.joinpath("source.mp4").write_bytes(b"source")
            project = Project.create_synchronized(
                root / "source.mp4",
                metadata(),
                project_id="geometry-115",
            )
            payload = project.to_dict()
            first = payload["timeline"]["tracks"][0]["blocks"][0]
            first.update(
                {
                    "source_end_ticks": 5_000_000,
                    "timeline_end_ticks": 5_000_000,
                }
            )
            second = copy.deepcopy(first)
            second.update(
                {
                    "segment_id": "segment-2",
                    "block_id": "block-2",
                    "source_start_ticks": 5_000_000,
                    "source_end_ticks": 10_000_000,
                    "timeline_start_ticks": 7_000_000,
                    "timeline_end_ticks": 12_000_000,
                }
            )
            payload["timeline"]["tracks"][0]["blocks"] = [first, second]
            cross_track = copy.deepcopy(first)
            cross_track.update(
                {
                    "segment_id": "segment-3",
                    "block_id": "block-3",
                    "track_id": "track-2",
                    "source_start_ticks": 0,
                    "source_end_ticks": 4_000_000,
                    "timeline_start_ticks": 3_000_000,
                    "timeline_end_ticks": 7_000_000,
                }
            )
            payload["timeline"]["tracks"].append({"track_id": "track-2", "blocks": [cross_track]})
            payload["timeline"]["tracks"].append({"track_id": "track-3", "blocks": []})
            payload["timeline"]["duration_ticks"] = 12_000_000

            restored = Project.from_dict(payload)

            self.assertEqual(restored.timeline.editing_duration_ticks, 12_000_000)
            self.assertEqual(restored.timeline.included_duration_ticks, 14_000_000)
            self.assertEqual(restored.timeline.final_duration_ticks, 12_000_000)
            self.assertEqual(restored.timeline.populated_track_count, 2)
            self.assertEqual(restored.timeline.included_track_count, 2)
            restored.timeline.add_track("track-4")
            with self.assertRaisesRegex(ProjectValidationError, "at most 4"):
                restored.timeline.add_track("track-5")


if __name__ == "__main__":
    unittest.main()
