import math
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from resolve_editor.model import (
    Project,
    ProjectValidationError,
    SegmentTimeline,
)


def metadata(duration=12.5):
    return {
        "duration_seconds": duration,
        "width": 320,
        "height": 180,
        "frame_rate": "10/1",
        "video_codec": "h264",
        "audio_codec": "aac",
        "format_name": "mov,mp4,m4a,3gp,3g2,mj2",
    }


class EditorModelTests(unittest.TestCase):
    def test_project_creation_records_source_identity_and_timeline(self):
        with TemporaryDirectory() as temporary_directory:
            source = Path(temporary_directory) / "source.mp4"
            source.write_bytes(b"fixture")

            project = Project.create(source, metadata())

            self.assertEqual(project.source.path, str(source.resolve()))
            self.assertEqual(project.source.uri, source.resolve().as_uri())
            self.assertEqual(project.duration_seconds, 12.5)
            self.assertEqual(project.playhead_seconds, 0.0)
            self.assertEqual(project.to_dict()["schema_version"], 2)
            self.assertEqual(
                project.segment_timeline.edited_duration_seconds,
                12.5,
            )

    def test_playhead_is_clamped_to_timeline(self):
        with TemporaryDirectory() as temporary_directory:
            source = Path(temporary_directory) / "source.mp4"
            source.write_bytes(b"fixture")
            project = Project.create(source, metadata(10.0))

            project.set_playhead(-1)
            self.assertEqual(project.playhead_seconds, 0.0)
            project.set_playhead(20)
            self.assertEqual(project.playhead_seconds, 10.0)

            with self.assertRaises(ProjectValidationError):
                project.set_playhead(math.nan)

    def test_source_status_reports_missing_source_without_relinking(self):
        with TemporaryDirectory() as temporary_directory:
            source = Path(temporary_directory) / "source.mp4"
            source.write_bytes(b"fixture")
            project = Project.create(source, metadata())
            source.unlink()

            status = project.source.status()

            self.assertFalse(status.available)
            self.assertFalse(status.changed)
            self.assertIn("missing", status.reason.lower())

    def test_unknown_project_schema_is_rejected(self):
        with self.assertRaises(ProjectValidationError):
            Project.from_dict(
                {
                    "schema_version": 99,
                    "project_id": "project",
                    "source": {},
                    "timeline": {},
                }
            )

    def test_segment_timeline_starts_with_exact_source_coverage(self):
        timeline = SegmentTimeline(12.5)

        self.assertEqual(len(timeline.segments), 1)
        segment = timeline.segments[0]
        self.assertTrue(segment.segment_id)
        self.assertEqual(segment.start_seconds, 0.0)
        self.assertEqual(segment.end_seconds, 12.5)
        self.assertFalse(segment.deleted)
        self.assertEqual(timeline.edited_duration_seconds, 12.5)

    def test_split_creates_ordered_segments_without_changing_duration(self):
        timeline = SegmentTimeline(12.5)
        original_id = timeline.segments[0].segment_id

        timeline.split(4.5)

        self.assertEqual(len(timeline.segments), 2)
        first, second = timeline.segments
        self.assertNotEqual(first.segment_id, second.segment_id)
        self.assertNotEqual(first.segment_id, original_id)
        self.assertEqual((first.start_seconds, first.end_seconds), (0.0, 4.5))
        self.assertEqual((second.start_seconds, second.end_seconds), (4.5, 12.5))
        self.assertEqual(timeline.edited_duration_seconds, 12.5)

    def test_split_rejects_boundaries_and_preserves_last_valid_state(self):
        timeline = SegmentTimeline(12.5)
        before = timeline.segments

        for position in (0.0, 12.5, -1.0, 13.0, math.nan):
            with self.assertRaises(ProjectValidationError):
                timeline.split(position)

        self.assertEqual(timeline.segments, before)

    def test_delete_and_restore_update_edited_duration(self):
        timeline = SegmentTimeline(12.5)
        timeline.split(4.5)
        second_id = timeline.segments[1].segment_id

        timeline.set_deleted(second_id, True)
        self.assertTrue(timeline.segments[1].deleted)
        self.assertEqual(timeline.edited_duration_seconds, 4.5)

        timeline.set_deleted(second_id, False)
        self.assertFalse(timeline.segments[1].deleted)
        self.assertEqual(timeline.edited_duration_seconds, 12.5)

    def test_repeated_operations_preserve_order_and_duration_invariants(self):
        timeline = SegmentTimeline(12.5)
        timeline.split(3.0)
        timeline.split(8.0)
        middle_id = timeline.segments[1].segment_id
        timeline.set_deleted(middle_id, True)
        timeline.validate()

        self.assertEqual(
            [(segment.start_seconds, segment.end_seconds) for segment in timeline.segments],
            [(0.0, 3.0), (3.0, 8.0), (8.0, 12.5)],
        )
        self.assertEqual(timeline.edited_duration_seconds, 7.5)

    def test_split_of_deleted_segment_keeps_deletion_state(self):
        timeline = SegmentTimeline(12.5)
        timeline.set_deleted(timeline.segments[0].segment_id, True)

        timeline.split(4.5)

        self.assertTrue(all(segment.deleted for segment in timeline.segments))
        self.assertEqual(timeline.edited_duration_seconds, 0.0)

    def test_segment_operations_reject_invalid_identifiers_and_deletion_values(self):
        timeline = SegmentTimeline(12.5)

        with self.assertRaises(ProjectValidationError):
            timeline.set_deleted("missing", True)
        with self.assertRaises(ProjectValidationError):
            timeline.set_deleted(timeline.segments[0].segment_id, "yes")

    def test_project_persists_segment_state_and_edited_duration(self):
        with TemporaryDirectory() as temporary_directory:
            source = Path(temporary_directory) / "source.mp4"
            source.write_bytes(b"fixture")
            project = Project.create(source, metadata())
            project.segment_timeline.split(4.5)
            project.segment_timeline.delete_segment(project.segment_timeline.segments[1].segment_id)

            payload = project.to_dict()
            restored = Project.from_dict(payload)

            self.assertEqual(payload["schema_version"], 2)
            self.assertEqual(
                restored.segment_timeline.to_dict(),
                project.segment_timeline.to_dict(),
            )
            self.assertEqual(
                restored.segment_timeline.edited_duration_seconds,
                4.5,
            )

    def test_legacy_project_schema_migrates_to_an_active_initial_segment(self):
        with TemporaryDirectory() as temporary_directory:
            source = Path(temporary_directory) / "source.mp4"
            source.write_bytes(b"fixture")
            project = Project.create(source, metadata())
            payload = project.to_dict()
            payload["schema_version"] = 1
            payload["timeline"].pop("segments", None)
            payload["timeline"].pop("edited_duration_seconds", None)

            restored = Project.from_dict(payload)

            self.assertEqual(restored.schema_version, 2)
            self.assertEqual(len(restored.segment_timeline.segments), 1)
            self.assertEqual(
                restored.segment_timeline.edited_duration_seconds,
                12.5,
            )

    def test_inconsistent_persisted_edited_duration_is_rejected(self):
        with TemporaryDirectory() as temporary_directory:
            source = Path(temporary_directory) / "source.mp4"
            source.write_bytes(b"fixture")
            payload = Project.create(source, metadata()).to_dict()
            payload["timeline"]["edited_duration_seconds"] = 4.0

            with self.assertRaises(ProjectValidationError):
                Project.from_dict(payload)

    def test_invalid_segment_replacement_preserves_last_valid_state(self):
        timeline = SegmentTimeline(12.5)
        before = timeline.segments

        with self.assertRaises(ProjectValidationError):
            timeline._replace_segments(timeline.segments + (timeline.segments[0],))

        self.assertEqual(timeline.segments, before)


if __name__ == "__main__":
    unittest.main()
