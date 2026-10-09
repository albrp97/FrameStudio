from __future__ import annotations

import io
import json
import shutil
import unittest
import uuid
from contextlib import contextmanager
from pathlib import Path

from framestudio.cli import cli_main
from framestudio.model import Project
from framestudio.persistence import load_project, save_project

_ARTIFACT_ROOT = Path(__file__).resolve().parent / ".ticket118-runtime"


@contextmanager
def isolated_directory():
    directory = _ARTIFACT_ROOT / f"case-{uuid.uuid4().hex}"
    directory.mkdir(parents=True, exist_ok=False)
    try:
        yield directory
    finally:
        shutil.rmtree(directory, ignore_errors=True)


def metadata(duration: float = 8.0) -> dict[str, object]:
    return {
        "duration_seconds": duration,
        "width": 320,
        "height": 180,
        "frame_rate": "10/1",
        "video_codec": "h264",
        "audio_codec": None,
        "format_name": "mp4",
    }


def run_cli(*arguments: str):
    stdout = io.StringIO()
    stderr = io.StringIO()
    result = cli_main(list(arguments), stdout=stdout, stderr=stderr)
    return result, stdout, stderr


def make_legacy_project(root: Path) -> Project:
    source = root / "source.mp4"
    source.write_bytes(b"track-cli-fixture")
    project = Project.create(source, metadata(), project_id="track-cli-project")
    project.timeline.split(2.0)
    return project


class EditorTrackCliTests(unittest.TestCase):
    def test_inspect_exposes_ordered_tracks_placements_active_track_gaps_and_ticks(self):
        with isolated_directory() as root:
            project = make_legacy_project(root)
            project.convert_to_synchronized(confirm=True)
            timeline = project.timeline
            second = timeline.blocks[1]
            timeline.move_block(second.segment_id, 4_000_000)
            timeline.add_track("track-2")
            timeline.set_active_track("track-2")
            project_path = root / "tracks.framestudio.json"
            save_project(project, project_path)

            result, stdout, stderr = run_cli("inspect", str(project_path))

            self.assertEqual(result, 0)
            self.assertEqual(stderr.getvalue(), "")
            payload = json.loads(stdout.getvalue())
            timeline_payload = payload["project"]["timeline"]
            self.assertEqual(timeline_payload["active_track_id"], "track-2")
            self.assertEqual(timeline_payload["track_ids"], ["track-1", "track-2"])
            self.assertEqual(timeline_payload["editing_duration_ticks"], 10_000_000)
            self.assertEqual(timeline_payload["final_duration_ticks"], 10_000_000)
            self.assertEqual(
                [track["track_id"] for track in timeline_payload["tracks"]],
                ["track-1", "track-2"],
            )
            first_track = timeline_payload["tracks"][0]
            self.assertEqual(
                [
                    (
                        block["segment_id"],
                        block["timeline_start_ticks"],
                        block["timeline_end_ticks"],
                    )
                    for block in first_track["blocks"]
                ],
                [
                    (
                        project.timeline.blocks[0].segment_id,
                        0,
                        2_000_000,
                    ),
                    (
                        project.timeline.blocks[1].segment_id,
                        4_000_000,
                        10_000_000,
                    ),
                ],
            )
            self.assertEqual(
                first_track["gaps"],
                [
                    {
                        "start_ticks": 2_000_000,
                        "end_ticks": 4_000_000,
                        "duration_ticks": 2_000_000,
                    },
                ],
            )
            self.assertEqual(
                timeline_payload["tracks"][1]["gaps"],
                [
                    {
                        "start_ticks": 0,
                        "end_ticks": 10_000_000,
                        "duration_ticks": 10_000_000,
                    },
                ],
            )

    def test_legacy_track_editing_requires_confirmation_and_conversion_is_explicit(self):
        with isolated_directory() as root:
            project_path = root / "legacy.framestudio.json"
            save_project(make_legacy_project(root), project_path)
            before = project_path.read_bytes()

            result, stdout, stderr = run_cli(
                "track-add",
                str(project_path),
                "--track-id",
                "track-2",
            )

            self.assertEqual(result, 3)
            self.assertEqual(stdout.getvalue(), "")
            error = json.loads(stderr.getvalue())
            self.assertEqual(error["error"]["code"], "legacy_conversion_required")
            self.assertEqual(project_path.read_bytes(), before)
            self.assertEqual(load_project(project_path).timeline.timing_mode, "legacy-ripple")

            result, stdout, stderr = run_cli(
                "track-convert",
                str(project_path),
                "--confirm-legacy-conversion",
            )

            self.assertEqual(result, 0)
            self.assertEqual(stderr.getvalue(), "")
            conversion = json.loads(stdout.getvalue())
            self.assertTrue(conversion["operation"]["converted"])
            self.assertEqual(load_project(project_path).timeline.timing_mode, "absolute")

    def test_track_lifecycle_rejects_fifth_and_populated_removal_without_writing(self):
        with isolated_directory() as root:
            project = make_legacy_project(root)
            project.convert_to_synchronized(confirm=True)
            project_path = root / "lifecycle.framestudio.json"
            save_project(project, project_path)

            for track_id in ("track-2", "track-3", "track-4"):
                result, _stdout, stderr = run_cli(
                    "track-add",
                    str(project_path),
                    "--track-id",
                    track_id,
                )
                self.assertEqual(result, 0, stderr.getvalue())

            before_fifth = project_path.read_bytes()
            result, stdout, stderr = run_cli(
                "track-add",
                str(project_path),
                "--track-id",
                "track-5",
            )
            self.assertEqual(result, 3)
            self.assertEqual(stdout.getvalue(), "")
            self.assertEqual(json.loads(stderr.getvalue())["error"]["code"], "invalid_operation")
            self.assertEqual(project_path.read_bytes(), before_fifth)

            before_populated_remove = project_path.read_bytes()
            result, stdout, stderr = run_cli(
                "track-remove",
                str(project_path),
                "--track-id",
                "track-1",
            )
            self.assertEqual(result, 3)
            self.assertEqual(stdout.getvalue(), "")
            self.assertEqual(json.loads(stderr.getvalue())["error"]["code"], "invalid_operation")
            self.assertEqual(project_path.read_bytes(), before_populated_remove)

            result, stdout, stderr = run_cli(
                "track-select",
                str(project_path),
                "--track-id",
                "track-3",
            )
            self.assertEqual(result, 0, stderr.getvalue())
            self.assertEqual(
                json.loads(stdout.getvalue())["operation"]["active_track_id"], "track-3"
            )

            result, stdout, stderr = run_cli(
                "track-remove",
                str(project_path),
                "--track-id",
                "track-4",
            )
            self.assertEqual(result, 0, stderr.getvalue())
            self.assertEqual(
                load_project(project_path).timeline.track_ids,
                ("track-1", "track-2", "track-3"),
            )

    def test_tick_move_split_copy_and_paste_use_shared_absolute_operations(self):
        with isolated_directory() as root:
            project = make_legacy_project(root)
            project.convert_to_synchronized(confirm=True)
            project.timeline.add_track("track-2")
            project_path = root / "editing.framestudio.json"
            save_project(project, project_path)
            original = project.timeline.blocks[0]

            result, stdout, stderr = run_cli(
                "move",
                str(project_path),
                "--segment",
                original.segment_id,
                "--timeline-start-ticks",
                "2_000_000",
                "--target-track-id",
                "track-2",
            )
            self.assertEqual(result, 0, stderr.getvalue())
            moved_payload = json.loads(stdout.getvalue())
            self.assertEqual(
                moved_payload["operation"]["timeline_start_ticks"],
                2_000_000,
            )
            moved = load_project(project_path).timeline.find(original.segment_id)
            self.assertEqual(moved.track_id, "track-2")
            self.assertEqual(moved.timeline_start_ticks, 2_000_000)

            result, stdout, stderr = run_cli(
                "split",
                str(project_path),
                "--segment",
                original.segment_id,
                "--position-ticks",
                "3_000_000",
                "--coordinate",
                "timeline",
            )
            self.assertEqual(result, 0, stderr.getvalue())
            split_payload = json.loads(stdout.getvalue())
            split_ids = split_payload["operation"]["segment_ids"]
            self.assertEqual(len(split_ids), 2)
            self.assertEqual(
                [
                    (
                        block["timeline_start_ticks"],
                        block["timeline_end_ticks"],
                    )
                    for block in split_payload["project"]["timeline"]["tracks"][1]["blocks"]
                ],
                [(2_000_000, 3_000_000), (3_000_000, 4_000_000)],
            )

            result, stdout, stderr = run_cli(
                "copy",
                str(project_path),
                "--segment",
                split_ids[0],
            )
            self.assertEqual(result, 0, stderr.getvalue())
            copied = json.loads(stdout.getvalue())["operation"]["blocks"][0]
            self.assertEqual(copied["source_start_ticks"], 0)
            self.assertEqual(copied["source_end_ticks"], 1_000_000)

            result, stdout, stderr = run_cli(
                "paste",
                str(project_path),
                "--segment",
                split_ids[0],
                "--at-ticks",
                "5_000_000",
                "--target-track-id",
                "track-2",
            )
            self.assertEqual(result, 0, stderr.getvalue())
            pasted = json.loads(stdout.getvalue())
            pasted_id = pasted["operation"]["pasted_segment_ids"][0]
            self.assertNotIn(pasted_id, split_ids)
            pasted_block = load_project(project_path).timeline.find(pasted_id)
            self.assertEqual(pasted_block.track_id, "track-2")
            self.assertEqual(
                (pasted_block.timeline_start_ticks, pasted_block.timeline_end_ticks),
                (5_000_000, 6_000_000),
            )

    def test_invalid_tick_and_unknown_track_fail_without_mutating_project(self):
        with isolated_directory() as root:
            project = make_legacy_project(root)
            project.convert_to_synchronized(confirm=True)
            project_path = root / "invalid.framestudio.json"
            save_project(project, project_path)
            segment_id = project.timeline.blocks[0].segment_id

            for arguments, expected_code in (
                (
                    (
                        "move",
                        str(project_path),
                        "--segment",
                        segment_id,
                        "--timeline-start-ticks",
                        "-1",
                    ),
                    "invalid_operation",
                ),
                (
                    (
                        "move",
                        str(project_path),
                        "--segment",
                        segment_id,
                        "--timeline-start-ticks",
                        "1.5",
                    ),
                    "invalid_arguments",
                ),
                (
                    (
                        "track-select",
                        str(project_path),
                        "--track-id",
                        "track-unknown",
                    ),
                    "invalid_operation",
                ),
            ):
                before = project_path.read_bytes()
                result, stdout, stderr = run_cli(*arguments)
                self.assertNotEqual(result, 0)
                self.assertEqual(stdout.getvalue(), "")
                self.assertEqual(json.loads(stderr.getvalue())["error"]["code"], expected_code)
                self.assertEqual(project_path.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
