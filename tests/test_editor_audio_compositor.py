import math
import shutil
import subprocess
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from framestudio.audio import AUDIO_POLICY_VERSION
from framestudio.audio_compositor import (
    AUDIO_SAMPLE_RATE,
    AudioCompositionError,
    AudioLayoutError,
    build_audio_plan,
    classify_audio_layout,
    fixed_pan_vector,
    render_audio,
    sample_boundary,
)
from framestudio.layout_plan import plan_project_layout
from framestudio.model import Project, Segment, SourceReference
from framestudio.model_timeline import TimelineTrack
from framestudio.persistence import load_project, save_project

_REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def _source(
    root: Path,
    source_id: str,
    *,
    channels: int = 1,
    layout: str | None = "mono",
    audio: bool = True,
    codec: str | None = "pcm_s16le",
    duration: float = 1.0,
) -> SourceReference:
    path = root / f"{source_id}.wav"
    path.write_bytes(b"fixture")
    if audio and shutil.which("ffmpeg"):
        path.unlink()
        subprocess.run(
            [
                "ffmpeg",
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-f",
                "lavfi",
                "-i",
                f"sine=frequency=440:sample_rate=48000:duration={duration}",
                "-c:a",
                "pcm_s16le",
                "-ar",
                "48000",
                "-ac",
                str(channels),
                str(path),
            ],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    return SourceReference.from_path(
        path,
        {
            "duration_seconds": duration,
            "width": 320,
            "height": 180,
            "frame_rate": "10/1",
            "video_codec": "rawvideo",
            "audio_codec": codec,
            "audio_stream_present": audio,
            "audio_sample_rate": AUDIO_SAMPLE_RATE,
            "audio_channels": channels,
            "audio_channel_layout": layout,
            "format_name": "wav",
        },
        source_id=source_id,
    )


def _audio_settings(
    source: SourceReference,
    *,
    gain_db: float = 0.0,
    peak_db: float = -20.0,
    sample_count: int = AUDIO_SAMPLE_RATE,
) -> dict[str, object]:
    return {
        "status": "ready",
        "gain_db": gain_db,
        "policy_version": AUDIO_POLICY_VERSION,
        "source_fingerprint": {
            "size_bytes": source.size_bytes,
            "modified_time_ns": source.modified_time_ns,
        },
        "measurements": {
            "peak_db": peak_db,
            "mean_rms_db": peak_db - 3.0,
            "median_db": peak_db - 3.0,
            "sample_count": sample_count,
        },
    }


def _project(
    root: Path,
    sources: tuple[SourceReference, ...],
    *,
    duration: float = 1.0,
) -> Project:
    project = Project.create_multi(sources)
    project.duration_seconds = duration
    for source in sources:
        project.set_source_audio_settings(source.source_id, _audio_settings(source))
    return project


def _set_tracks(project: Project, tracks: tuple[TimelineTrack, ...], duration: float) -> None:
    sources = tuple(project.sources or (project.source,))
    project.segment_timeline = project.timeline.__class__.from_tracks(
        tracks,
        source_durations={
            source.source_id: float(source.metadata["duration_seconds"]) for source in sources
        },
        active_track_id=tracks[0].track_id,
    )
    project.duration_seconds = duration


class AudioCompositorContractTests(unittest.TestCase):
    def test_sample_boundary_uses_shared_half_up_48k_rounding(self):
        self.assertEqual(sample_boundary(0), 0)
        self.assertEqual(sample_boundary(10), 0)
        self.assertEqual(sample_boundary(11), 1)
        self.assertEqual(sample_boundary(31), 1)

    def test_fixed_pan_vectors_are_not_configurable(self):
        self.assertEqual(fixed_pan_vector(1), (0.0,))
        self.assertEqual(fixed_pan_vector(2), (-25.0, 25.0))
        self.assertEqual(fixed_pan_vector(3), (-25.0, 0.0, 25.0))
        self.assertEqual(fixed_pan_vector(4), (-25.0, 25.0, -50.0, 50.0))
        with self.assertRaises(AudioCompositionError):
            fixed_pan_vector(5)

    def test_channel_layout_policy_distinguishes_absent_stereo_metadata(self):
        self.assertEqual(classify_audio_layout(2, None), "stereo")
        self.assertEqual(classify_audio_layout(2, "2.0"), "stereo")
        self.assertEqual(classify_audio_layout(1, "mono"), "mono")
        self.assertEqual(classify_audio_layout(6, "5.1"), "5.1")
        self.assertEqual(classify_audio_layout(6, "5.1(side)"), "5.1(side)")
        for channels, layout in ((3, "3.0"), (6, None), (2, "5.1"), (2, "unknown")):
            with self.subTest(channels=channels, layout=layout):
                with self.assertRaises(AudioLayoutError):
                    classify_audio_layout(channels, layout)

    def test_plan_preserves_visual_slot_for_absent_audio_and_uses_source_ranges(self):
        with TemporaryDirectory(dir=str(_REPOSITORY_ROOT)) as temporary_directory:
            root = Path(temporary_directory)
            first = _source(root, "first", channels=1, layout="mono", duration=2.0)
            silent = _source(
                root,
                "silent",
                channels=2,
                layout=None,
                audio=False,
                codec=None,
                duration=2.0,
            )
            project = _project(root, (first, silent), duration=2.0)
            first_block = Segment.create(
                0.0,
                2.0,
                segment_id="first-block",
                block_id="first-block",
                source_id=first.source_id,
                timeline_start_seconds=0.0,
                timeline_end_seconds=2.0,
                track_id="track-1",
            )
            silent_block = Segment.create(
                0.0,
                2.0,
                segment_id="silent-block",
                block_id="silent-block",
                source_id=silent.source_id,
                timeline_start_seconds=0.0,
                timeline_end_seconds=2.0,
                track_id="track-2",
            )
            _set_tracks(
                project,
                (
                    TimelineTrack("track-1", (first_block,)),
                    TimelineTrack("track-2", (silent_block,)),
                ),
                2.0,
            )
            layout = plan_project_layout(project)

            plan = build_audio_plan(project, layout)

        self.assertEqual(plan.final_sample_count, 2 * AUDIO_SAMPLE_RATE)
        interval = plan.intervals[-1]
        self.assertEqual(tuple(block.pan_percent for block in interval.blocks), (-25.0, 25.0))
        self.assertEqual(interval.blocks[1].audio_status, "not-applicable")
        self.assertEqual(interval.blocks[0].source_start_sample, 0)
        self.assertEqual(interval.blocks[0].source_end_sample, 2 * AUDIO_SAMPLE_RATE)

    def test_effective_row_bound_includes_persisted_source_gain_once(self):
        with TemporaryDirectory(dir=str(_REPOSITORY_ROOT)) as temporary_directory:
            root = Path(temporary_directory)
            source = _source(root, "positive", duration=1.0)
            project = _project(root, (source,))
            project.set_source_audio_settings(
                source.source_id,
                _audio_settings(
                    source,
                    gain_db=20.510149966878604,
                    peak_db=-60.0,
                ),
            )
            plan = build_audio_plan(project, plan_project_layout(project))

        block = plan.intervals[0].blocks[0]
        expected_gain = 10.0 ** (20.510149966878604 / 20.0)
        self.assertAlmostEqual(block.gain_linear, expected_gain, places=10)
        self.assertAlmostEqual(
            block.effective_row_abs_sums[0],
            expected_gain * math.sqrt(0.5),
            places=8,
        )

    def test_unsupported_layout_fails_before_any_destination_change(self):
        with TemporaryDirectory(dir=str(_REPOSITORY_ROOT)) as temporary_directory:
            root = Path(temporary_directory)
            source = _source(root, "unsupported", channels=3, layout="3.0")
            project = _project(root, (source,))
            layout = plan_project_layout(project)
            destination = root / "unsupported-output.wav"
            destination.write_bytes(b"preserve")

            with self.assertRaisesRegex(AudioLayoutError, "3.0"):
                render_audio(project, layout, destination, ffmpeg_path="missing-ffmpeg")

            self.assertEqual(destination.read_bytes(), b"preserve")
            self.assertEqual(tuple(root.glob(".*.partial")), ())

    def test_pending_analysis_fails_before_publication_and_preserves_destination(self):
        with TemporaryDirectory(dir=str(_REPOSITORY_ROOT)) as temporary_directory:
            root = Path(temporary_directory)
            source = _source(root, "pending")
            project = Project.create_multi((source,))
            layout = plan_project_layout(project)
            destination = root / "render.wav"
            destination.write_bytes(b"original")

            with self.assertRaisesRegex(AudioCompositionError, "pending"):
                render_audio(project, layout, destination, ffmpeg_path="missing-ffmpeg")

            self.assertEqual(destination.read_bytes(), b"original")
            self.assertFalse((root / ".render.wav.partial").exists())

    def test_malformed_ready_peak_fails_before_render_or_destination_change(self):
        with TemporaryDirectory(dir=str(_REPOSITORY_ROOT)) as temporary_directory:
            root = Path(temporary_directory)
            source = _source(root, "invalid-peak")
            project = _project(root, (source,))
            layout = plan_project_layout(project)
            destination = root / "render.wav"
            destination.write_bytes(b"original")
            source_bytes = Path(source.path).read_bytes()
            for peak_db in (None, True, "invalid", math.nan, math.inf, -math.inf, 100_000.0):
                with self.subTest(peak_db=peak_db):
                    settings = project.source_audio_settings(source.source_id)
                    settings["measurements"]["peak_db"] = peak_db
                    project.set_source_audio_settings(source.source_id, settings)
                    with self.assertRaisesRegex(AudioCompositionError, "peak measurement"):
                        render_audio(project, layout, destination, ffmpeg_path="missing-ffmpeg")
                    self.assertEqual(destination.read_bytes(), b"original")
                    self.assertEqual(Path(source.path).read_bytes(), source_bytes)
                    self.assertEqual(tuple(root.glob(".*.partial")), ())

    @unittest.skipUnless(
        shutil.which("ffmpeg") and shutil.which("ffprobe"),
        "FFmpeg and ffprobe are required",
    )
    def test_render_publishes_verified_pcm_atomically_and_project_round_trips(self):
        with TemporaryDirectory(dir=str(_REPOSITORY_ROOT)) as temporary_directory:
            root = Path(temporary_directory)
            source = _source(root, "render")
            project = _project(root, (source,))
            layout = plan_project_layout(project)
            project_path = root / "project.framestudio.json"
            save_project(project, project_path)
            restored = load_project(project_path)
            destination = root / "render-output.wav"

            result = render_audio(restored, layout, destination)

            self.assertEqual(result.sample_rate, AUDIO_SAMPLE_RATE)
            self.assertEqual(result.channels, 2)
            self.assertEqual(result.sample_count, AUDIO_SAMPLE_RATE)
            self.assertTrue(destination.is_file())
            self.assertTrue(math.isfinite(result.peak))
            self.assertLessEqual(result.peak, 1.0 + 1e-6)


if __name__ == "__main__":
    unittest.main()
