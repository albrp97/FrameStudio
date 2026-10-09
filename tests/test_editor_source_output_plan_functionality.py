from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import unittest
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory

from framestudio.audio import pending_audio_decision
from framestudio.composition import VisualTransform
from framestudio.media import probe_media
from framestudio.model import Project, Segment, SourceReference
from framestudio.model_timeline import SegmentTimeline, TimelineTrack
from framestudio.model_types import SCHEMA_VERSION
from framestudio.output_plan import (
    COMBINED_OUTPUT_MODE,
    FINAL_ONLY_OUTPUT_MODE,
    SOURCE_ONLY_OUTPUT_MODE,
    OutputPlanError,
    plan_project_outputs,
    set_output_selection,
)
from framestudio.persistence import load_project, save_project

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _make_fixture(path: Path, color: str, frequency: int) -> None:
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
            f"color=c={color}:s=320x180:r=12",
            "-f",
            "lavfi",
            "-i",
            f"sine=frequency={frequency}:sample_rate=48000",
            "-t",
            "1.2",
            "-shortest",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "64k",
            str(path),
        ],
        cwd=REPOSITORY_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise AssertionError(f"Could not create {path.name}: {result.stderr}")


def _block(
    source_id: str,
    segment_id: str,
    start: float,
    end: float,
    timeline_start: float,
    track_id: str,
    *,
    deleted: bool = False,
    zoom: float = 1.0,
) -> Segment:
    return Segment.create(
        start,
        end,
        source_id=source_id,
        segment_id=segment_id,
        block_id=f"block-{segment_id}",
        timeline_start_seconds=timeline_start,
        timeline_end_seconds=timeline_start + (end - start),
        track_id=track_id,
        deleted=deleted,
        visual_transform=VisualTransform(zoom=zoom),
    )


def _source_reference(path: Path, source_id: str) -> SourceReference:
    return SourceReference.from_path(
        path,
        probe_media(path).metadata(),
        source_id=source_id,
    )


def _make_project(root: Path) -> tuple[Project, tuple[Path, ...]]:
    source_specs = (
        ("first", "Shared?.mp4", "red", 440, "source-a"),
        ("second", "Shared*.mp4", "blue", 550, "source-b"),
        ("third", "C:clip.mp4", "green", 660, "source-c"),
        ("fourth", "unused.mp4", "yellow", 770, "source-d"),
    )
    sources: list[SourceReference] = []
    source_paths: list[Path] = []
    for directory, name, color, frequency, source_id in source_specs:
        path = root / directory / name
        path.parent.mkdir(parents=True, exist_ok=True)
        _make_fixture(path, color, frequency)
        source_paths.append(path)
        sources.append(_source_reference(path, source_id))
    durations = {source.source_id: float(source.metadata["duration_seconds"]) for source in sources}
    tracks = (
        TimelineTrack(
            "Track/One",
            (
                _block("source-a", "a-first", 0.0, 0.2, 0.0, "Track/One", zoom=1.1),
                _block("source-b", "b-first", 0.1, 0.3, 0.45, "Track/One"),
                _block("source-a", "a-copy", 0.4, 0.6, 0.9, "Track/One", zoom=1.35),
                _block(
                    "source-b",
                    "b-excluded",
                    0.7,
                    0.9,
                    1.3,
                    "Track/One",
                    deleted=True,
                ),
            ),
        ),
        TimelineTrack(
            "Track:One",
            (
                _block("source-a", "a-second-track", 0.6, 0.8, 0.0, "Track:One", zoom=1.2),
                _block("source-c", "c-second-track", 0.2, 0.4, 0.5, "Track:One"),
            ),
        ),
        TimelineTrack("empty-track"),
        TimelineTrack(
            "excluded-track",
            (
                _block(
                    "source-d",
                    "d-excluded",
                    0.0,
                    0.2,
                    0.0,
                    "excluded-track",
                    deleted=True,
                ),
            ),
        ),
    )
    timeline = SegmentTimeline.from_tracks(
        tracks,
        source_durations=durations,
        active_track_id="Track/One",
    )
    project = Project(
        project_id="ticket-112-functionality",
        source=sources[0],
        duration_seconds=timeline.timeline_duration_seconds,
        schema_version=SCHEMA_VERSION,
        segment_timeline=timeline,
        sources=tuple(sources),
        source_settings={
            source.source_id: {
                "audio": pending_audio_decision(source).to_dict(),
            }
            for source in sources
        },
    )
    project.validate()
    return project, tuple(source_paths)


class SourceOutputPlanFunctionalityTests(unittest.TestCase):
    def test_source_output_plan_roundtrip(self):
        if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
            self.skipTest("FFmpeg and ffprobe are required")
        with TemporaryDirectory(
            dir=Path(__file__).resolve().parent,
            prefix=".ticket112-",
        ) as temporary_directory:
            root = Path(temporary_directory)
            project, source_paths = _make_project(root / "fixtures")
            source_hashes = {path: _sha256(path) for path in source_paths}
            expected_pairs = (
                ("Track/One", "source-a"),
                ("Track/One", "source-b"),
                ("Track:One", "source-a"),
                ("Track:One", "source-c"),
            )
            mode_expectations = (
                (FINAL_ONLY_OUTPUT_MODE, True, 0),
                (COMBINED_OUTPUT_MODE, True, 4),
                (SOURCE_ONLY_OUTPUT_MODE, False, 4),
            )
            for mode, expects_final, source_count in mode_expectations:
                set_output_selection(project, mode=mode)
                project_path = root / f"{mode}.framestudio.json"
                save_project(project, project_path)
                reopened = load_project(project_path)
                plan = plan_project_outputs(reopened, root / f"{mode}.mp4")

                self.assertEqual(plan.mode, mode)
                self.assertEqual(plan.final_request is not None, expects_final)
                self.assertEqual(len(plan.source_outputs), source_count)
                self.assertEqual(
                    tuple((item.track_id, item.source_id) for item in plan.source_outputs),
                    expected_pairs if source_count else (),
                )
                self.assertEqual(
                    [item.framing for item in plan.source_outputs],
                    ["standalone-full-canvas"] * source_count,
                )
                self.assertEqual(
                    [item.audio_intent for item in plan.source_outputs],
                    ["normal-source-audio"] * source_count,
                )
                self.assertEqual(
                    [item.segment_ids for item in plan.source_outputs],
                    [
                        ("a-first", "a-copy"),
                        ("b-first",),
                        ("a-second-track",),
                        ("c-second-track",),
                    ]
                    if source_count
                    else [],
                )
                self.assertNotIn("empty-track", {item.track_id for item in plan.source_outputs})
                self.assertNotIn(
                    "excluded-track",
                    {item.track_id for item in plan.source_outputs},
                )
                if plan.final_request is not None:
                    self.assertEqual(plan.final_request.framing, "final-composition")
                    self.assertEqual(plan.final_request.audio_intent, "mixed-layout-pan")
                    self.assertEqual(plan.final_request.expected_duration_seconds, 1.1)

                for request in plan.source_outputs:
                    self.assertTrue(request.destination.name.endswith(".mp4"))
                    self.assertNotEqual(
                        request.destination.resolve(),
                        request.source_path.resolve() if request.source_path else None,
                    )
                    self.assertEqual(
                        _sha256(request.source_path),
                        source_hashes[request.source_path],
                    )
                self.assertEqual(
                    {path: _sha256(path) for path in source_paths},
                    source_hashes,
                )

                if mode == COMBINED_OUTPUT_MODE:
                    published_final = root / "combined.mp4"
                    published_final.write_bytes(b"published-final")
                    replanned = plan_project_outputs(reopened, published_final)
                    self.assertEqual(
                        [request.destination for request in plan.source_outputs],
                        [request.destination for request in replanned.source_outputs],
                    )
                    self.assertEqual(
                        replanned.source_output_root,
                        (root / "combined-sources").resolve(),
                    )

            explicit_source_root = root / "published.reels.v1"
            explicit_source_root.mkdir()
            explicit_plan = plan_project_outputs(
                project,
                root / "source-plan.mp4",
                mode=SOURCE_ONLY_OUTPUT_MODE,
                source_output_root=explicit_source_root,
            )
            self.assertEqual(explicit_plan.source_output_root, explicit_source_root.resolve())

            source_alias = root / "fixtures" / "source-alias.mp4"
            source_alias.symlink_to(source_paths[0])
            with self.assertRaisesRegex(OutputPlanError, "would overwrite source"):
                plan_project_outputs(
                    project,
                    source_alias,
                    mode=COMBINED_OUTPUT_MODE,
                )

            with self.assertRaisesRegex(OutputPlanError, "At least one output"):
                set_output_selection(
                    project,
                    include_final=False,
                    include_source_outputs=False,
                )
            empty_project = deepcopy(project)
            for track in empty_project.timeline.tracks or ():
                empty_project.timeline.replace_track_blocks(
                    track.track_id,
                    tuple(replace(block, deleted=True) for block in track.blocks),
                )
            empty_project.duration_seconds = empty_project.timeline.timeline_duration_seconds
            set_output_selection(empty_project, mode=SOURCE_ONLY_OUTPUT_MODE)
            with self.assertRaisesRegex(OutputPlanError, "empty edit"):
                plan_project_outputs(empty_project, root / "empty.mp4")

            source_only_path = root / "cli-source-only.framestudio.json"
            set_output_selection(project, mode=SOURCE_ONLY_OUTPUT_MODE)
            save_project(project, source_only_path)
            cli = subprocess.run(
                [
                    sys.executable,
                    str(REPOSITORY_ROOT / "framestudio.py"),
                    "export-plan",
                    str(source_only_path),
                    "--output",
                    str(root / "cli-final.mp4"),
                    "--full-paths",
                ],
                cwd=REPOSITORY_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(cli.returncode, 0, cli.stderr)
            self.assertEqual(cli.stderr, "")
            payload = json.loads(cli.stdout)
            self.assertTrue(payload["ok"])
            output_plan = payload["export"]["output_plan"]
            self.assertEqual(output_plan["mode"], SOURCE_ONLY_OUTPUT_MODE)
            self.assertIsNone(output_plan["final"])
            self.assertEqual(
                tuple(
                    (item["identity"]["track_id"], item["identity"]["source_id"])
                    for item in output_plan["source_outputs"]
                ),
                expected_pairs,
            )
            self.assertEqual(
                {path: _sha256(path) for path in source_paths},
                source_hashes,
            )


if __name__ == "__main__":
    unittest.main()
