import copy
import hashlib
import json
import os
import shutil
import subprocess
import sys
import unittest
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from framestudio.media import probe_media
from framestudio.model import Project, Segment
from framestudio.operations import apply_visual_transform, enable_triplicate
from framestudio.persistence import (
    ProjectPersistenceError,
    load_autosave,
    load_project,
    save_autosave,
    save_project,
)

REPOSITORY = Path(__file__).resolve().parents[1]


@contextmanager
def isolated_directory():
    with TemporaryDirectory(
        dir=Path(__file__).resolve().parent,
        prefix=".ticket115-",
    ) as raw_path:
        yield Path(raw_path)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_source(root: Path, name: str, duration: float) -> tuple[Path, dict[str, object]]:
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
            f"color=c=black:s=320x180:r=10:d={duration}",
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
    return path, probe_media(path).metadata()


def make_legacy_v2(root: Path) -> Project:
    source, source_metadata = make_source(root, "legacy-v2-source.mp4", 10.0)
    project = Project.create(source, source_metadata, project_id="legacy-v2")
    project.timeline.split(4.0)
    project.timeline.split(7.0)
    project.timeline.set_deleted(project.timeline.segment_items[1].segment_id, True)
    project.output_settings = {"custom": {"quality": "high"}}
    apply_visual_transform(
        project,
        [project.timeline.segment_items[0].segment_id],
        zoom=1.25,
        offset_x=0.1,
        offset_y=-0.1,
    )
    enable_triplicate(project, [project.timeline.segment_items[0].segment_id])
    return project


def make_legacy_v1(project: Project) -> dict:
    return {
        "schema_version": 1,
        "composition_version": project.composition_version,
        "project_id": "legacy-v1",
        "source": project.source.to_dict(),
        "timeline": {
            "duration_seconds": project.duration_seconds,
            "playhead_seconds": project.playhead_seconds,
        },
        "source_settings": project.source_settings,
        "output_settings": project.output_settings,
    }


def make_legacy_v3(root: Path) -> Project:
    first, first_metadata = make_source(root, "legacy-v3-first.mp4", 4.0)
    second, second_metadata = make_source(root, "legacy-v3-second.mp4", 3.0)
    project = Project.create_multi(
        (
            (first, first_metadata),
            (second, second_metadata),
        ),
        project_id="legacy-v3",
    )
    project.timeline.set_deleted(project.timeline.blocks[1].segment_id, True)
    project.output_settings = {"custom": {"quality": "draft"}}
    return project


class TrackMigrationFunctionalityTests(unittest.TestCase):
    def test_track_project_migration(self):
        if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
            self.skipTest("FFmpeg and ffprobe are required")
        with isolated_directory() as root:
            fixture_root = root / "fixtures"
            fixture_root.mkdir()
            state_root = root / "state"
            state_root.mkdir()

            legacy_v2 = make_legacy_v2(fixture_root)
            legacy_v2_path = fixture_root / "legacy-v2.framestudio.json"
            save_project(legacy_v2, legacy_v2_path)
            legacy_v2_path.write_text(
                json.dumps(legacy_v2.to_dict(), indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )

            legacy_v1_path = fixture_root / "legacy-v1.resolve.json"
            legacy_v1_path.write_text(
                json.dumps(make_legacy_v1(legacy_v2), indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )

            legacy_v3 = make_legacy_v3(fixture_root)
            legacy_v3_path = fixture_root / "legacy-v3.framestudio.json"
            save_project(legacy_v3, legacy_v3_path)

            fixture_hashes = {
                path.name: sha256(path) for path in (legacy_v1_path, legacy_v2_path, legacy_v3_path)
            }
            source_hashes = {path.name: sha256(path) for path in fixture_root.glob("*.mp4")}

            migrated_paths = []
            for fixture_path in (
                legacy_v1_path,
                legacy_v2_path,
                legacy_v3_path,
            ):
                pre_plan_path = fixture_root / f"{fixture_path.stem}.pre-plan.mp4"
                pre_plan = subprocess.run(
                    [
                        sys.executable,
                        str(REPOSITORY / "framestudio.py"),
                        "export-plan",
                        str(fixture_path),
                        "--output",
                        str(pre_plan_path),
                    ],
                    cwd=REPOSITORY,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertEqual(pre_plan.returncode, 0, pre_plan.stderr)
                self.assertEqual(pre_plan.stderr, "")
                pre_plan_payload = json.loads(pre_plan.stdout)
                self.assertTrue(pre_plan_payload["ok"])
                pre_segments = pre_plan_payload["export"]["plan"]["segments"]

                normalized = load_project(fixture_path)
                normalized_path = fixture_root / f"{fixture_path.stem}.normalized.framestudio.json"
                save_project(normalized, normalized_path)
                normalized_again = load_project(normalized_path)
                self.assertEqual(normalized_again.to_dict(), normalized.to_dict())
                post_plan = subprocess.run(
                    [
                        sys.executable,
                        str(REPOSITORY / "framestudio.py"),
                        "export-plan",
                        str(normalized_path),
                        "--output",
                        str(fixture_root / f"{fixture_path.stem}.post-plan.mp4"),
                    ],
                    cwd=REPOSITORY,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertEqual(post_plan.returncode, 0, post_plan.stderr)
                self.assertEqual(post_plan.stderr, "")
                post_plan_payload = json.loads(post_plan.stdout)
                self.assertTrue(post_plan_payload["ok"])
                post_segments = post_plan_payload["export"]["plan"]["segments"]
                self.assertEqual(
                    [
                        (
                            segment["segment_id"],
                            segment["start_seconds"],
                            segment["end_seconds"],
                        )
                        for segment in post_segments
                    ],
                    [
                        (
                            segment["segment_id"],
                            segment["start_seconds"],
                            segment["end_seconds"],
                        )
                        for segment in pre_segments
                    ],
                )
                self.assertEqual(
                    post_plan_payload["export"]["plan"]["expected_duration_seconds"],
                    pre_plan_payload["export"]["plan"]["expected_duration_seconds"],
                )

                project = load_project(normalized_path)
                legacy_ids = [block.segment_id for block in project.timeline.blocks]
                legacy_timing = {
                    block.segment_id: (
                        block.start_seconds,
                        block.end_seconds,
                        block.timeline_start,
                        block.timeline_end,
                        block.deleted,
                    )
                    for block in project.timeline.blocks
                }
                legacy_output_duration = project.timeline.edited_duration_seconds
                project.convert_to_synchronized(confirm=True)
                destination = fixture_root / f"{fixture_path.stem}.migrated.framestudio.json"
                save_project(project, destination)
                migrated_paths.append(destination)
                reopened = load_project(destination)
                self.assertEqual(reopened.to_dict(), project.to_dict())
                self.assertEqual(reopened.schema_version, 4)
                self.assertEqual(reopened.timeline.track_ids, ("track-1",))
                self.assertEqual(reopened.timeline.active_track_id, "track-1")
                self.assertGreaterEqual(reopened.timeline.populated_track_count, 1)
                self.assertTrue(reopened.timeline.blocks)
                self.assertEqual(reopened.output_settings, project.output_settings)
                self.assertEqual(
                    [block.segment_id for block in reopened.timeline.blocks],
                    legacy_ids,
                )
                self.assertEqual(
                    {
                        block.segment_id: (
                            block.start_seconds,
                            block.end_seconds,
                            block.timeline_start,
                            block.timeline_end,
                            block.deleted,
                        )
                        for block in reopened.timeline.blocks
                    },
                    legacy_timing,
                )
                active_projection = reopened.timeline.legacy_active_intervals("track-1")
                self.assertEqual(
                    0.0 if not active_projection else active_projection[-1][2],
                    legacy_output_duration,
                )
                if fixture_path == legacy_v2_path:
                    self.assertTrue(reopened.timeline.blocks[1].deleted)
                    self.assertTrue(reopened.timeline.blocks[0].has_visual_modifications)
                    self.assertIsNotNone(reopened.timeline.blocks[0].triplicate)

            for fixture_path in (
                legacy_v1_path,
                legacy_v2_path,
                legacy_v3_path,
            ):
                self.assertEqual(sha256(fixture_path), fixture_hashes[fixture_path.name])
            for source_path in fixture_root.glob("*.mp4"):
                self.assertEqual(sha256(source_path), source_hashes[source_path.name])

            synchronized = load_project(migrated_paths[1])
            synchronized.timeline.add_track("track-2")
            synchronized.timeline.add_track("track-3")
            synchronized.timeline.add_track("track-4")
            source_id = synchronized.source.source_id
            gap_first = Segment.create(
                0.0,
                2.0,
                segment_id="gap-first",
                block_id="gap-first",
                source_id=source_id,
                timeline_start_seconds=0.0,
                timeline_end_seconds=2.0,
                track_id="track-2",
            )
            gap_second = Segment.create(
                2.0,
                4.0,
                segment_id="gap-second",
                block_id="gap-second",
                source_id=source_id,
                timeline_start_seconds=5.0,
                timeline_end_seconds=7.0,
                track_id="track-2",
            )
            synchronized.timeline.replace_track_blocks(
                "track-2",
                (gap_first, gap_second),
            )
            synchronized.timeline.set_active_track("track-4")
            synchronized_payload = synchronized.to_dict()
            self.assertEqual(
                [track["track_id"] for track in synchronized_payload["timeline"]["tracks"]],
                ["track-1", "track-2", "track-3", "track-4"],
            )
            self.assertEqual(synchronized.timeline.populated_track_count, 2)

            synchronized_path = fixture_root / "four-track.framestudio.json"
            save_project(synchronized, synchronized_path)
            cli = subprocess.run(
                [
                    sys.executable,
                    str(REPOSITORY / "framestudio.py"),
                    "inspect",
                    str(synchronized_path),
                ],
                cwd=REPOSITORY,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(cli.returncode, 0, cli.stderr)
            self.assertEqual(cli.stderr, "")
            inspected = json.loads(cli.stdout)
            self.assertTrue(inspected["ok"])
            self.assertEqual(inspected["project"]["schema_version"], 4)
            self.assertEqual(
                inspected["project"]["timeline"]["active_track_id"],
                "track-4",
            )
            self.assertEqual(
                [track["track_id"] for track in inspected["project"]["timeline"]["tracks"]],
                ["track-1", "track-2", "track-3", "track-4"],
            )
            self.assertEqual(inspected["project"]["timeline"]["active_track_id"], "track-4")
            self.assertEqual(inspected["project"]["timeline"]["populated_track_count"], 2)
            self.assertEqual(inspected["project"]["timeline"]["final_duration_ticks"], 10_000_000)
            self.assertEqual(
                inspected["project"]["timeline"]["included_duration_ticks"], 11_000_000
            )

            export_destination = fixture_root / "synchronized-output.mp4"
            export_env = os.environ.copy()
            export_env["XDG_STATE_HOME"] = str(state_root)
            before_export = synchronized_path.read_bytes()
            for command in ("export-plan", "export"):
                exported = subprocess.run(
                    [
                        sys.executable,
                        str(REPOSITORY / "framestudio.py"),
                        command,
                        str(synchronized_path),
                        "--output",
                        str(export_destination),
                        "--fps-choice",
                        "lowest",
                        "--no-enhance-fps",
                        "--no-upscale-enhancement",
                    ],
                    cwd=REPOSITORY,
                    env=export_env,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertEqual(exported.returncode, 0, exported.stderr)
                self.assertEqual(exported.stderr, "")
                events = [json.loads(line) for line in exported.stdout.splitlines()]
                self.assertTrue(events[-1]["ok"])
                self.assertEqual(events[-1]["command"], command)
                self.assertEqual(synchronized_path.read_bytes(), before_export)
                self.assertEqual(export_destination.exists(), command == "export")
            decoded = subprocess.run(
                [
                    shutil.which("ffprobe") or "ffprobe",
                    "-v",
                    "error",
                    "-select_streams",
                    "v:0",
                    "-count_frames",
                    "-show_entries",
                    "stream=width,height,nb_read_frames,avg_frame_rate",
                    "-of",
                    "json",
                    str(export_destination),
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            stream = json.loads(decoded.stdout)["streams"][0]
            self.assertEqual((stream["width"], stream["height"]), (1920, 1080))
            self.assertEqual(int(stream["nb_read_frames"]), 100)
            self.assertEqual(stream["avg_frame_rate"], "10/1")
            for name, original_hash in source_hashes.items():
                self.assertEqual(sha256(fixture_root / name), original_hash)

            before_bytes = synchronized_path.read_bytes()
            before_current = synchronized.to_dict()
            invalid_payloads = {}
            fifth = copy.deepcopy(synchronized_payload)
            fifth["timeline"]["tracks"].append({"track_id": "track-5", "blocks": []})
            invalid_payloads["fifth-track"] = fifth
            overlap = copy.deepcopy(synchronized_payload)
            first_block = overlap["timeline"]["tracks"][0]["blocks"][0]
            overlap_block = copy.deepcopy(first_block)
            overlap_block.update(
                {
                    "segment_id": "overlap-block",
                    "block_id": "overlap-block",
                    "timeline_start_ticks": 1_000_000,
                    "timeline_end_ticks": 5_000_000,
                }
            )
            overlap["timeline"]["tracks"][0]["blocks"].append(overlap_block)
            invalid_payloads["same-track-overlap"] = overlap
            reference = copy.deepcopy(synchronized_payload)
            reference["timeline"]["tracks"][0]["blocks"][0]["track_id"] = "missing-track"
            invalid_payloads["track-reference"] = reference
            ticks = copy.deepcopy(synchronized_payload)
            del ticks["timeline"]["tracks"][0]["blocks"][0]["timeline_start_ticks"]
            invalid_payloads["missing-ticks"] = ticks
            for name, invalid in invalid_payloads.items():
                invalid_path = fixture_root / f"invalid-{name}.framestudio.json"
                invalid_path.write_text(
                    json.dumps(invalid, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8",
                )
                with self.assertRaises(ProjectPersistenceError):
                    load_project(invalid_path)
                self.assertEqual(synchronized_path.read_bytes(), before_bytes)
                self.assertEqual(synchronized.to_dict(), before_current)

            with patch.dict(os.environ, {"XDG_STATE_HOME": str(state_root)}):
                autosave = save_autosave(synchronized)
                recovered = load_autosave()
            self.assertEqual(
                autosave,
                state_root / "framestudio" / "autosave.framestudio.json",
            )
            self.assertEqual(recovered.to_dict(), synchronized.to_dict())
            self.assertEqual(
                sha256(source_hash_path := fixture_root / "legacy-v2-source.mp4"),
                source_hashes[source_hash_path.name],
            )


if __name__ == "__main__":
    unittest.main()
