from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import unittest
import uuid
from contextlib import contextmanager
from pathlib import Path

from framestudio.media import probe_media
from framestudio.model import Project, SourceReference
from framestudio.operations import move_segment, paste_segments, split_segment
from framestudio.persistence import load_project, save_project

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
_ARTIFACT_ROOT = Path(__file__).resolve().parent / ".ticket118-functionality-runtime"


@contextmanager
def isolated_directory():
    directory = _ARTIFACT_ROOT / f"case-{uuid.uuid4().hex}"
    directory.mkdir(parents=True, exist_ok=False)
    try:
        yield directory
    finally:
        shutil.rmtree(directory, ignore_errors=True)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_source(
    root: Path,
    name: str,
    duration: float,
    source: str,
    *,
    rate: int = 10,
) -> Path:
    path = root / name
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        raise unittest.SkipTest("ffmpeg is required")
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
            f"{source}:rate={rate}",
            "-t",
            str(duration),
            "-an",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            str(path),
        ],
        cwd=REPOSITORY_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise AssertionError(f"Could not create {name}: {result.stderr}")
    return path


def run_public(*arguments: str):
    result = subprocess.run(
        [
            sys.executable,
            str(REPOSITORY_ROOT / "framestudio.py"),
            *arguments,
        ],
        cwd=REPOSITORY_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    payload = None
    if result.stdout:
        payload = json.loads(result.stdout)
    elif result.stderr:
        payload = json.loads(result.stderr)
    return result, payload


def semantic_state(project: Project) -> dict[str, object]:
    timeline = project.timeline
    tracks = []
    for track in timeline.tracks or ():
        tracks.append(
            {
                "track_id": track.track_id,
                "blocks": [
                    {
                        "segment_id": block.segment_id,
                        "block_id": block.block_id,
                        "source_id": block.source_id,
                        "source_start_ticks": block.source_start_ticks,
                        "source_end_ticks": block.source_end_ticks,
                        "timeline_start_ticks": block.timeline_start_ticks,
                        "timeline_end_ticks": block.timeline_end_ticks,
                        "deleted": block.deleted,
                        "state": block.state,
                        "visual_transform": block.visual_transform.to_dict(),
                        "triplicate": (
                            None if block.triplicate is None else block.triplicate.to_dict()
                        ),
                    }
                    for block in track.blocks
                ],
            }
        )
    return {
        "project_id": project.project_id,
        "schema_version": project.schema_version,
        "timing_mode": timeline.timing_mode,
        "track_ids": list(timeline.track_ids),
        "active_track_id": timeline.active_track_id,
        "editing_duration_ticks": timeline.editing_duration_ticks,
        "included_duration_ticks": timeline.included_duration_ticks,
        "final_duration_ticks": timeline.final_duration_ticks,
        "tracks": tracks,
    }


def semantic_state_without_generated_ids(project: Project) -> dict[str, object]:
    state = semantic_state(project)
    tracks = []
    for track in state["tracks"]:
        tracks.append(
            {
                "track_id": track["track_id"],
                "blocks": [
                    {
                        key: value
                        for key, value in block.items()
                        if key not in {"segment_id", "block_id"}
                    }
                    for block in track["blocks"]
                ],
            }
        )
    state["tracks"] = tracks
    return state


class TrackCliFunctionalityTests(unittest.TestCase):
    def test_legacy_timeline_coordinate_split_preserves_legacy_project(self):
        if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
            self.skipTest("FFmpeg and ffprobe are required")
        with isolated_directory() as root:
            source_a = make_source(
                root,
                "blue.mp4",
                0.5,
                "color=c=blue:size=64x36",
                rate=20,
            )
            source_b = make_source(
                root,
                "red.mp4",
                0.5,
                "color=c=red:size=64x36",
                rate=20,
            )
            source_project_path = root / "legacy-source.framestudio.json"
            output_project_path = root / "legacy-split.framestudio.json"
            project = Project.create_multi(
                tuple((path, probe_media(path).metadata()) for path in (source_a, source_b))
            )
            self.assertEqual(project.schema_version, 3)
            self.assertEqual(project.timeline.timing_mode, "legacy-ripple")
            save_project(project, source_project_path)
            source_project_bytes = source_project_path.read_bytes()
            source_hashes = {path: sha256(path) for path in (source_a, source_b)}
            source_ids = tuple(source.source_id for source in project.sources)
            second_segment_id = project.timeline.segment_items[1].segment_id

            result, payload = run_public(
                "split",
                str(source_project_path),
                "--segment",
                second_segment_id,
                "--position",
                "0.75",
                "--coordinate",
                "timeline",
                "--output",
                str(output_project_path),
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(payload["ok"])
            self.assertEqual(payload["project"]["timeline"]["timing_mode"], "legacy-ripple")
            self.assertEqual(source_project_path.read_bytes(), source_project_bytes)
            output_project = load_project(output_project_path)
            self.assertEqual(output_project.timeline.timing_mode, "legacy-ripple")
            self.assertEqual(
                tuple(source.source_id for source in output_project.sources),
                source_ids,
            )
            blocks = output_project.timeline.segment_items
            self.assertEqual(
                [block.source_id for block in blocks],
                [source_ids[0], source_ids[1], source_ids[1]],
            )
            self.assertEqual(
                [
                    (
                        round(block.start_seconds, 6),
                        round(block.end_seconds, 6),
                        round(block.timeline_start, 6),
                        round(block.timeline_end, 6),
                    )
                    for block in blocks
                ],
                [
                    (0.0, 0.5, 0.0, 0.5),
                    (0.0, 0.25, 0.5, 0.75),
                    (0.25, 0.5, 0.75, 1.0),
                ],
            )
            self.assertEqual(
                [
                    block.source_id
                    for block in load_project(source_project_path).timeline.segment_items
                ],
                [source_ids[0], source_ids[1]],
            )
            for source_path, expected_hash in source_hashes.items():
                self.assertEqual(sha256(source_path), expected_hash)

    def test_track_cli_roundtrip(self):
        if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
            self.skipTest("FFmpeg and ffprobe are required")
        with isolated_directory() as root:
            source_a = make_source(root, "source-a.mp4", 4.0, "testsrc=size=320x180")
            source_b = make_source(root, "source-b.mp4", 2.0, "color=c=blue:size=320x180")
            source_hashes = {path: sha256(path) for path in (source_a, source_b)}
            project_path = root / "track-cli.framestudio.json"
            domain_path = root / "domain.framestudio.json"

            result, imported = run_public(
                "import",
                str(source_a),
                "--project",
                str(project_path),
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(imported["ok"])
            shutil.copy2(project_path, domain_path)

            result, inspected = run_public("inspect", str(project_path))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(inspected["project"]["timeline"]["timing_mode"], "legacy-ripple")
            self.assertNotIn(str(root), result.stdout)

            for command in (
                ("track-convert", "--confirm-legacy-conversion"),
                ("track-add", "--track-id", "track-2"),
                ("track-select", "--track-id", "track-2"),
                ("add", str(source_b)),
            ):
                result, payload = run_public(command[0], str(project_path), *command[1:])
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertTrue(payload["ok"])

            domain = load_project(domain_path)
            domain.convert_to_synchronized(confirm=True)
            domain.timeline.add_track("track-2")
            domain.timeline.set_active_track("track-2")
            cli_after_add = load_project(project_path)
            incoming_id = next(
                source.source_id
                for source in cli_after_add.sources
                if Path(source.path) == source_b.resolve()
            )
            incoming = SourceReference.from_path(
                source_b,
                probe_media(source_b).metadata(),
                source_id=incoming_id,
            )
            domain.append_sources((incoming,))
            save_project(domain, domain_path)

            cli_project = load_project(project_path)
            self.assertEqual(
                semantic_state_without_generated_ids(cli_project),
                semantic_state_without_generated_ids(domain),
            )
            self.assertEqual(cli_project.timeline.active_track_id, "track-2")
            source_b_block = next(
                block
                for block in cli_project.timeline.blocks
                if block.source_id == incoming.source_id
            )
            self.assertEqual(source_b_block.track_id, "track-2")
            self.assertEqual(
                (source_b_block.timeline_start_ticks, source_b_block.timeline_end_ticks),
                (0, 2_000_000),
            )
            domain_source_b_block = next(
                block for block in domain.timeline.blocks if block.source_id == incoming.source_id
            )

            source_a_block = next(
                block
                for block in cli_project.timeline.blocks
                if block.source_id == cli_project.source.source_id
            )
            result, moved_payload = run_public(
                "move",
                str(project_path),
                "--segment",
                source_b_block.segment_id,
                "--timeline-start-ticks",
                "4_000_000",
                "--target-track-id",
                "track-1",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(moved_payload["operation"]["timeline_start_ticks"], 4_000_000)
            move_segment(
                domain,
                domain_source_b_block.segment_id,
                timeline_start_ticks=4_000_000,
                target_track_id="track-1",
            )
            save_project(domain, domain_path)
            self.assertEqual(
                semantic_state_without_generated_ids(load_project(project_path)),
                semantic_state_without_generated_ids(domain),
            )

            result, split_payload = run_public(
                "split",
                str(project_path),
                "--segment",
                source_a_block.segment_id,
                "--position-ticks",
                "1_000_000",
                "--coordinate",
                "timeline",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            split_ids = split_payload["operation"]["segment_ids"]
            domain_split = split_segment(
                domain.timeline,
                segment_id=source_a_block.segment_id,
                coordinate="timeline",
                position_ticks=1_000_000,
            )
            save_project(domain, domain_path)
            self.assertEqual(len(split_ids), 2)
            self.assertEqual(
                [
                    (
                        block.timeline_start_ticks,
                        block.timeline_end_ticks,
                    )
                    for block in load_project(project_path).timeline.track_by_id("track-1").blocks
                    if block.segment_id in split_ids
                ],
                [(0, 1_000_000), (1_000_000, 4_000_000)],
            )
            self.assertEqual(
                [
                    (
                        block.source_start_ticks,
                        block.source_end_ticks,
                        block.timeline_start_ticks,
                        block.timeline_end_ticks,
                    )
                    for block in domain_split
                ],
                [
                    (
                        block["source_start_ticks"],
                        block["source_end_ticks"],
                        block["timeline_start_ticks"],
                        block["timeline_end_ticks"],
                    )
                    for block in split_payload["project"]["timeline"]["tracks"][0]["blocks"]
                    if block["segment_id"] in split_ids
                ],
            )

            result, copied = run_public(
                "copy",
                str(project_path),
                "--segment",
                split_ids[0],
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            copied_block = copied["operation"]["blocks"][0]
            self.assertEqual(copied_block["source_start_ticks"], 0)
            self.assertEqual(copied_block["source_end_ticks"], 1_000_000)

            result, pasted = run_public(
                "paste",
                str(project_path),
                "--segment",
                split_ids[0],
                "--at-ticks",
                "6_000_000",
                "--target-track-id",
                "track-1",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            pasted_id = pasted["operation"]["pasted_segment_ids"][0]
            self.assertNotIn(pasted_id, split_ids)
            domain_source_id = domain_split[0].segment_id
            domain_copy = domain.timeline.copy_blocks([domain_source_id])
            domain_pasted = paste_segments(
                domain,
                domain_copy,
                at_ticks=6_000_000,
                target_track_id="track-1",
            )
            save_project(domain, domain_path)
            cli_project = load_project(project_path)
            pasted_block = cli_project.timeline.find(pasted_id)
            self.assertEqual(
                (pasted_block.timeline_start_ticks, pasted_block.timeline_end_ticks),
                (6_000_000, 7_000_000),
            )
            self.assertEqual(
                semantic_state_without_generated_ids(cli_project),
                semantic_state_without_generated_ids(domain),
            )
            self.assertNotEqual(domain_pasted[0].segment_id, domain_source_id)

            for track_id in ("track-3", "track-4"):
                result, _payload = run_public(
                    "track-add",
                    str(project_path),
                    "--track-id",
                    track_id,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                domain.timeline.add_track(track_id)
            save_project(domain, domain_path)

            before_fifth = project_path.read_bytes()
            result, error = run_public(
                "track-add",
                str(project_path),
                "--track-id",
                "track-5",
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(error["error"]["code"], "invalid_operation")
            self.assertEqual(project_path.read_bytes(), before_fifth)

            before_invalid_move = project_path.read_bytes()
            result, error = run_public(
                "move",
                str(project_path),
                "--segment",
                pasted_id,
                "--timeline-start-ticks",
                "-1",
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(error["error"]["code"], "invalid_operation")
            self.assertEqual(project_path.read_bytes(), before_invalid_move)

            before_populated_remove = project_path.read_bytes()
            result, error = run_public(
                "track-remove",
                str(project_path),
                "--track-id",
                "track-1",
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(error["error"]["code"], "invalid_operation")
            self.assertEqual(project_path.read_bytes(), before_populated_remove)

            result, _payload = run_public(
                "track-select",
                str(project_path),
                "--track-id",
                "track-3",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            domain.timeline.set_active_track("track-3")
            result, _payload = run_public(
                "track-remove",
                str(project_path),
                "--track-id",
                "track-4",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            domain.timeline.remove_track("track-4")
            save_project(domain, domain_path)

            copy_path = root / "saved-copy.framestudio.json"
            result, saved = run_public(
                "save",
                str(project_path),
                "--output",
                str(copy_path),
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            result, reopened = run_public("reopen", str(copy_path))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(
                saved["project"]["timeline"],
                reopened["project"]["timeline"],
            )
            self.assertEqual(
                semantic_state_without_generated_ids(load_project(project_path)),
                semantic_state_without_generated_ids(domain),
            )
            for source_path, expected_hash in source_hashes.items():
                self.assertEqual(sha256(source_path), expected_hash)


if __name__ == "__main__":
    unittest.main()
