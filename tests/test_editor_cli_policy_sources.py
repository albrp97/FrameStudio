import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from framestudio.cli import _policy_metadata
from framestudio.fps_policy import policy_source_metadata
from framestudio.model import Project, Segment
from framestudio.model_timeline import SegmentTimeline, TimelineTrack
from framestudio.model_types import SCHEMA_VERSION, SourceReference
from framestudio.output_plan import active_export_sources


class CliPolicySourceSetTests(unittest.TestCase):
    def test_cli_policy_metadata_uses_only_active_export_sources(self):
        metadata = {
            "duration_seconds": 2.0,
            "width": 1920,
            "height": 1080,
            "frame_rate": "30/1",
            "video_codec": "h264",
            "audio_codec": None,
            "format_name": "mp4",
        }
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            sources = []
            for source_id in ("first", "unused"):
                path = root / f"{source_id}.mp4"
                path.write_bytes(source_id.encode())
                sources.append(
                    SourceReference.from_path(
                        path,
                        {**metadata, "source_id": source_id},
                        source_id=source_id,
                    )
                )
            tracks = (
                TimelineTrack(
                    "track-one",
                    (
                        Segment.create(
                            0.0,
                            2.0,
                            source_id="first",
                            segment_id="first-block",
                            timeline_start_seconds=0.0,
                            timeline_end_seconds=2.0,
                            track_id="track-one",
                        ),
                        Segment.create(
                            0.0,
                            2.0,
                            source_id="unused",
                            segment_id="unused-block",
                            timeline_start_seconds=2.0,
                            timeline_end_seconds=4.0,
                            track_id="track-one",
                            deleted=True,
                        ),
                    ),
                ),
            )
            timeline = SegmentTimeline.from_tracks(
                tracks,
                source_durations={"first": 2.0, "unused": 2.0},
                active_track_id="track-one",
            )
            project = Project(
                project_id="cli-policy-sources",
                source=sources[0],
                duration_seconds=timeline.timeline_duration_seconds,
                schema_version=SCHEMA_VERSION,
                segment_timeline=timeline,
                sources=tuple(sources),
            )
            project.validate()

            active_ids = tuple(source.source_id for source in active_export_sources(project))
            cli_ids = tuple(item["source_id"] for item in _policy_metadata(project))
            gui_ids = tuple(
                item["source_id"] for item in policy_source_metadata(active_export_sources(project))
            )

            self.assertEqual(active_ids, ("first",))
            self.assertEqual(cli_ids, active_ids)
            self.assertEqual(cli_ids, gui_ids)


if __name__ == "__main__":
    unittest.main()
