import subprocess
import unittest
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory

from framestudio.audio_compositor import (
    AUDIO_SAMPLE_RATE,
    AudioPlan,
    _render_command,
    build_audio_plan,
)
from framestudio.layout_plan import LayoutPlan, plan_project_layout
from framestudio.model import Project, Segment
from framestudio.model_timeline import TimelineTrack
from framestudio.model_types import SCHEMA_VERSION
from tests.test_editor_audio_compositor_functionality import _audio_settings, _source

_REPOSITORY_ROOT = Path(__file__).resolve().parents[1]

# (track, source key, source start, source end, timeline start, timeline end)
_MANY_BRANCH_BLOCKS = (
    ("track-1", "tone", 0.00, 0.20, 0.00, 0.20),
    ("track-1", "pair", 0.10, 0.35, 0.30, 0.55),
    ("track-1", "tone", 0.50, 0.70, 0.60, 0.80),
    ("track-2", "tone", 0.20, 0.55, 0.10, 0.45),
    ("track-2", "hot", 0.00, 0.20, 0.50, 0.70),
    ("track-2", "pair", 0.60, 0.80, 0.75, 0.95),
    ("track-3", "tone", 0.80, 0.90, 0.05, 0.15),
    ("track-3", "hot", 0.30, 0.45, 0.15, 0.30),
    ("track-3", "pair", 0.60, 0.85, 0.40, 0.65),
    ("track-3", "silent", 0.00, 0.25, 0.65, 0.90),
)

_SINGLE_SOURCE_BLOCKS = (
    ("track-1", "tone", 0.00, 0.20, 0.00, 0.20),
    ("track-2", "tone", 0.30, 0.60, 0.10, 0.40),
    ("track-3", "tone", 0.80, 0.90, 0.50, 0.60),
    ("track-3", "tone", 0.05, 0.15, 0.70, 0.80),
)


def _fixture(
    root: Path,
    blocks: tuple[tuple[str, str, float, float, float, float], ...],
) -> tuple[Project, LayoutPlan]:
    keys = sorted({block[1] for block in blocks})
    sources = {}
    if "tone" in keys:
        sources["tone"] = _source(root, "tone", frequency=440, duration=1.0)
    if "pair" in keys:
        sources["pair"] = _source(
            root,
            "pair",
            frequency=880,
            channels=2,
            layout="stereo",
            duration=1.0,
        )
    if "hot" in keys:
        sources["hot"] = _source(root, "hot", frequency=660, duration=1.0)
    if "silent" in keys:
        sources["silent"] = _source(root, "silent", frequency=None, audio=False, duration=1.0)
    project = Project.create_multi(tuple(sources[key] for key in keys))
    project.schema_version = SCHEMA_VERSION
    segments_by_track: dict[str, list[Segment]] = {}
    for index, (track_id, key, source_start, source_end, start, end) in enumerate(blocks):
        source = sources[key]
        segment = Segment.create(
            source_start,
            source_end,
            segment_id=f"{key}-{index}",
            block_id=f"{key}-{index}",
            source_id=source.source_id,
            timeline_start_seconds=start,
            timeline_end_seconds=end,
            track_id=track_id,
        )
        segments_by_track.setdefault(track_id, []).append(segment)
    project.segment_timeline = project.timeline.__class__.from_tracks(
        tuple(
            TimelineTrack(track_id, tuple(segments))
            for track_id, segments in segments_by_track.items()
        ),
        source_durations={
            source.source_id: float(source.metadata["duration_seconds"])
            for source in sources.values()
        },
        active_track_id=next(iter(segments_by_track)),
    )
    project.duration_seconds = 1.0
    for key, source in sources.items():
        settings = {"tone": {}, "pair": {"gain_db": -9.0}, "hot": {"gain_db": 6.0, "peak_db": -1.0}}
        project.set_source_audio_settings(
            source.source_id,
            _audio_settings(source, **settings.get(key, {})),
        )
    return project, plan_project_layout(project)


def _audible_branch_count(plan: AudioPlan) -> int:
    return sum(len(interval.audible_blocks) for interval in plan.intervals)


def _input_count(command: list[str]) -> int:
    return command.count("-i")


def _render_pcm(
    root: Path,
    project: Project,
    plan: AudioPlan,
    name: str,
    *,
    reuse_inputs: bool,
) -> tuple[str, int]:
    destination = root / f"{name}.wav"
    command, _ = _render_command(project, plan, destination, "ffmpeg", reuse_inputs=reuse_inputs)
    subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    raw = subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(destination),
            "-f",
            "f32le",
            "-ar",
            str(AUDIO_SAMPLE_RATE),
            "-ac",
            "2",
            "pipe:1",
        ],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout
    frame_bytes = 2 * 4
    return sha256(raw).hexdigest(), len(raw) // frame_bytes


class AudioInputReuseFunctionalityTests(unittest.TestCase):
    def test_repeated_source_across_tracks_and_intervals_maps_to_one_input(self):
        with TemporaryDirectory(dir=str(_REPOSITORY_ROOT)) as temporary_directory:
            root = Path(temporary_directory)
            project, layout = _fixture(root, _MANY_BRANCH_BLOCKS)
            plan = build_audio_plan(project, layout)
            branches = _audible_branch_count(plan)
            self.assertGreaterEqual(branches, 24)

            shared, shared_filter = _render_command(
                project,
                plan,
                root / "shared.wav",
                "ffmpeg",
            )
            legacy, _ = _render_command(
                project,
                plan,
                root / "legacy.wav",
                "ffmpeg",
                reuse_inputs=False,
            )

            self.assertEqual(_input_count(legacy), branches)
            self.assertEqual(_input_count(shared), 3)
            self.assertIn("asplit=", shared_filter)

    def test_single_source_repeated_across_staggered_tracks_maps_to_one_input(self):
        with TemporaryDirectory(dir=str(_REPOSITORY_ROOT)) as temporary_directory:
            root = Path(temporary_directory)
            project, layout = _fixture(root, _SINGLE_SOURCE_BLOCKS)
            plan = build_audio_plan(project, layout)
            branches = _audible_branch_count(plan)

            shared, _ = _render_command(project, plan, root / "shared.wav", "ffmpeg")
            legacy, _ = _render_command(
                project,
                plan,
                root / "legacy.wav",
                "ffmpeg",
                reuse_inputs=False,
            )

            self.assertGreater(branches, 1)
            self.assertEqual(_input_count(legacy), branches)
            self.assertEqual(_input_count(shared), 1)

    def test_shared_inputs_render_identical_decoded_pcm_to_legacy_inputs(self):
        cases = (
            ("many-branch", _MANY_BRANCH_BLOCKS),
            ("single-source", _SINGLE_SOURCE_BLOCKS),
        )
        for name, blocks in cases:
            with (
                self.subTest(case=name),
                TemporaryDirectory(
                    dir=str(_REPOSITORY_ROOT),
                ) as temporary_directory,
            ):
                root = Path(temporary_directory)
                project, layout = _fixture(root, blocks)
                plan = build_audio_plan(project, layout)

                legacy_hash, legacy_samples = _render_pcm(
                    root,
                    project,
                    plan,
                    f"{name}-legacy",
                    reuse_inputs=False,
                )
                shared_hash, shared_samples = _render_pcm(
                    root,
                    project,
                    plan,
                    f"{name}-shared",
                    reuse_inputs=True,
                )

                self.assertEqual(legacy_samples, plan.final_sample_count)
                self.assertEqual(shared_samples, plan.final_sample_count)
                self.assertEqual(shared_hash, legacy_hash)


if __name__ == "__main__":
    unittest.main()
