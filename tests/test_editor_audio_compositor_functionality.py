import shutil
import subprocess
import unittest
from array import array
from hashlib import sha256
from math import cos, hypot, log10, pi, sin
from pathlib import Path
from tempfile import TemporaryDirectory

from framestudio.audio_compositor import AUDIO_SAMPLE_RATE, AudioRenderError, render_audio
from framestudio.layout_plan import plan_project_layout
from framestudio.model import Project, Segment, SourceReference
from framestudio.model_timeline import TimelineTrack
from framestudio.model_types import SCHEMA_VERSION
from framestudio.persistence import load_project, save_project
from tests.test_editor_audio_compositor import _audio_settings as _create_audio_settings

_REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def _run(command: list[str]) -> None:
    subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def _metadata(
    *,
    duration: float,
    channels: int,
    layout: str | None,
    audio: bool = True,
    codec: str = "pcm_s16le",
) -> dict[str, object]:
    return {
        "duration_seconds": duration,
        "width": 320,
        "height": 180,
        "frame_rate": "10/1",
        "video_codec": "rawvideo",
        "audio_codec": codec if audio else None,
        "audio_stream_present": audio,
        "audio_sample_rate": AUDIO_SAMPLE_RATE,
        "audio_channels": channels,
        "audio_channel_layout": layout,
        "format_name": "wav",
    }


def _audio_settings(
    source: SourceReference,
    *,
    gain_db: float = 0.0,
    peak_db: float = -20.0,
    sample_count: int = 2 * AUDIO_SAMPLE_RATE,
) -> dict[str, object]:
    return _create_audio_settings(
        source,
        gain_db=gain_db,
        peak_db=peak_db,
        sample_count=sample_count,
    )


def _source(
    root: Path,
    source_id: str,
    *,
    frequency: int | None,
    channels: int = 1,
    layout: str | None = "mono",
    duration: float = 2.0,
    amplitude: float = 0.08,
    audio: bool = True,
) -> SourceReference:
    path = root / f"{source_id}.wav"
    if frequency is None:
        _run(
            [
                "ffmpeg",
                "-hide_banner",
                "-loglevel",
                "error",
                "-f",
                "lavfi",
                "-i",
                "anullsrc=r=48000:cl=stereo",
                "-t",
                str(duration),
                "-c:a",
                "pcm_s16le",
                "-ar",
                "48000",
                "-ac",
                "2",
                str(path),
            ]
        )
    elif channels == 1:
        _run(
            [
                "ffmpeg",
                "-hide_banner",
                "-loglevel",
                "error",
                "-f",
                "lavfi",
                "-i",
                f"sine=frequency={frequency}:sample_rate=48000:duration={duration}",
                "-filter:a",
                f"volume={amplitude}",
                "-c:a",
                "pcm_s16le",
                "-ar",
                "48000",
                "-ac",
                "1",
                str(path),
            ]
        )
    else:
        _run(
            [
                "ffmpeg",
                "-hide_banner",
                "-loglevel",
                "error",
                "-f",
                "lavfi",
                "-i",
                f"sine=frequency={frequency}:sample_rate=48000:duration={duration}",
                "-f",
                "lavfi",
                "-i",
                f"sine=frequency={frequency + 440}:sample_rate=48000:duration={duration}",
                "-filter_complex",
                (
                    f"[0:a]volume={amplitude}[left];"
                    f"[1:a]volume={amplitude / 2.0}[right];"
                    "[left][right]amerge=inputs=2[a]"
                ),
                "-map",
                "[a]",
                "-c:a",
                "pcm_s16le",
                "-ar",
                "48000",
                "-ac",
                "2",
                str(path),
            ]
        )
    return SourceReference.from_path(
        path,
        _metadata(duration=duration, channels=channels, layout=layout, audio=audio),
        source_id=source_id,
    )


def _project(root: Path, sources: tuple[SourceReference, ...]) -> Project:
    project = Project.create_multi(sources)
    project.schema_version = SCHEMA_VERSION
    source_by_id = {source.source_id: source for source in sources}
    left = source_by_id["left"]
    right = source_by_id["right"]
    silent = source_by_id["silent"]
    blocks = (
        Segment.create(
            0.0,
            1.0,
            segment_id="left-a",
            block_id="left-a",
            source_id=left.source_id,
            timeline_start_seconds=0.0,
            timeline_end_seconds=1.0,
            track_id="track-1",
        ),
        Segment.create(
            1.0,
            1.5,
            segment_id="left-b",
            block_id="left-b",
            source_id=left.source_id,
            timeline_start_seconds=2.0,
            timeline_end_seconds=2.5,
            track_id="track-1",
        ),
        Segment.create(
            0.0,
            1.0,
            segment_id="right-a",
            block_id="right-a",
            source_id=right.source_id,
            timeline_start_seconds=0.5,
            timeline_end_seconds=1.5,
            track_id="track-2",
        ),
        Segment.create(
            0.0,
            1.0,
            segment_id="silent-a",
            block_id="silent-a",
            source_id=silent.source_id,
            timeline_start_seconds=0.5,
            timeline_end_seconds=1.5,
            track_id="track-3",
        ),
    )
    project.segment_timeline = project.timeline.__class__.from_tracks(
        (
            TimelineTrack("track-1", (blocks[0], blocks[1])),
            TimelineTrack("track-2", (blocks[2],)),
            TimelineTrack("track-3", (blocks[3],)),
        ),
        source_durations={
            source.source_id: float(source.metadata["duration_seconds"]) for source in sources
        },
        active_track_id="track-1",
    )
    project.duration_seconds = 2.5
    for source in sources:
        project.set_source_audio_settings(source.source_id, _audio_settings(source))
    return project


def _single_source_project(source: SourceReference, *, duration: float = 1.0) -> Project:
    project = Project.create_multi((source,))
    project.schema_version = SCHEMA_VERSION
    block = Segment.create(
        0.0,
        duration,
        segment_id=f"{source.source_id}-block",
        block_id=f"{source.source_id}-block",
        source_id=source.source_id,
        timeline_start_seconds=0.0,
        timeline_end_seconds=duration,
        track_id="track-1",
    )
    project.segment_timeline = project.timeline.__class__.from_tracks(
        (TimelineTrack("track-1", (block,)),),
        source_durations={
            source.source_id: float(source.metadata["duration_seconds"]),
        },
        active_track_id="track-1",
    )
    project.duration_seconds = duration
    project.set_source_audio_settings(source.source_id, _audio_settings(source))
    return project


def _sole_panned_project(
    root: Path,
    *,
    amplitude: float,
    gain_db: float,
) -> tuple[Project, SourceReference, float]:
    visual_only_left = _source(root, "left", frequency=None, audio=False)
    visual_only_right = _source(root, "right", frequency=None, audio=False)
    panned = _source(
        root,
        "silent",
        frequency=440,
        channels=2,
        layout="stereo",
        amplitude=amplitude,
        duration=2.0,
    )
    project = _project(root, (visual_only_left, visual_only_right, panned))
    panned_samples, _, _ = _decoded_pcm(Path(panned.path))
    measured_peak = max(abs(value) for value in panned_samples)
    project.set_source_audio_settings(
        panned.source_id,
        _audio_settings(
            panned,
            gain_db=gain_db,
            peak_db=20.0 * log10(measured_peak),
        ),
    )
    return project, panned, measured_peak


def _decoded_pcm(path: Path) -> tuple[list[float], int, int]:
    probe = subprocess.run(
        [
            "ffprobe",
            "-hide_banner",
            "-v",
            "error",
            "-show_entries",
            "stream=sample_rate,channels",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout.splitlines()
    sample_rate, channels = int(probe[0]), int(probe[1])
    raw = subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(path),
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
    samples = array("f")
    samples.frombytes(raw)
    return list(samples), sample_rate, channels


def _tone_amplitude(
    samples: list[float],
    *,
    start_frame: int,
    end_frame: int,
    frequency: float,
    channel: int,
) -> float:
    count = end_frame - start_frame
    real = 0.0
    imaginary = 0.0
    for frame in range(start_frame, end_frame):
        value = samples[frame * 2 + channel]
        angle = 2.0 * pi * frequency * frame / AUDIO_SAMPLE_RATE
        real += value * cos(angle)
        imaginary += value * sin(angle)
    return 2.0 * hypot(real, imaginary) / count


def _sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _encode_aac(source: Path, destination: Path) -> None:
    _run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(source),
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            str(destination),
        ]
    )


def _render_channel_marker_fixture(root: Path, channel_layout: str) -> list[float]:
    path = (
        root / f"markers-{channel_layout.replace('.', '-').replace('(', '-').replace(')', '')}.wav"
    )
    frequencies = (440, 550, 660, 770, 880, 990)
    inputs = []
    for frequency in frequencies:
        inputs.extend(
            [
                "-f",
                "lavfi",
                "-i",
                f"sine=frequency={frequency}:sample_rate=48000:duration=1",
            ]
        )
    channels = "".join(f"[{index}:a]" for index in range(6))
    _run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            *inputs,
            "-filter_complex",
            f"{channels}amerge=inputs=6[a]",
            "-map",
            "[a]",
            "-c:a",
            "pcm_f32le",
            "-ar",
            "48000",
            "-channel_layout",
            channel_layout,
            str(path),
        ]
    )
    source = SourceReference.from_path(
        path,
        _metadata(duration=1.0, channels=6, layout=channel_layout, codec="pcm_f32le"),
        source_id=f"surround-{channel_layout}",
    )
    project = Project.create_multi((source,))
    project.schema_version = SCHEMA_VERSION
    project.set_source_audio_settings(
        source.source_id,
        _audio_settings(source, peak_db=-18.0, sample_count=AUDIO_SAMPLE_RATE),
    )
    project.segment_timeline = project.timeline.__class__.from_tracks(
        (
            TimelineTrack(
                "track-1",
                (
                    Segment.create(
                        0.0,
                        1.0,
                        segment_id=f"surround-block-{channel_layout}",
                        block_id=f"surround-block-{channel_layout}",
                        source_id=source.source_id,
                        timeline_start_seconds=0.0,
                        timeline_end_seconds=1.0,
                        track_id="track-1",
                    ),
                ),
            ),
        ),
        source_durations={source.source_id: 1.0},
        active_track_id="track-1",
    )
    output = (
        root
        / f"surround-output-{channel_layout.replace('.', '-').replace('(', '-').replace(')', '')}.wav"
    )
    render_audio(project, plan_project_layout(project), output)
    samples, _, _ = _decoded_pcm(output)
    return samples


@unittest.skipUnless(
    shutil.which("ffmpeg") and shutil.which("ffprobe"),
    "FFmpeg and ffprobe are required",
)
class AudioCompositorFunctionalityTests(unittest.TestCase):
    def test_public_audio_boundary_preserves_safe_centered_stereo_without_mix_or_limiter(self):
        with TemporaryDirectory(dir=str(_REPOSITORY_ROOT)) as temporary_directory:
            root = Path(temporary_directory)
            source = _source(
                root,
                "centered-safe",
                frequency=440,
                channels=2,
                layout="stereo",
                amplitude=7.6,
                duration=1.0,
            )
            project = _single_source_project(source)
            destination = root / "centered-safe-render.wav"
            original, _, _ = _decoded_pcm(Path(source.path))

            result = render_audio(project, plan_project_layout(project), destination)
            rendered, sample_rate, channels = _decoded_pcm(destination)

        self.assertEqual(result.sample_count, AUDIO_SAMPLE_RATE)
        self.assertEqual(sample_rate, AUDIO_SAMPLE_RATE)
        self.assertEqual(channels, 2)
        self.assertLessEqual(max(abs(value) for value in original), 0.96)
        self.assertGreater(max(abs(value) for value in original), 0.90)
        self.assertEqual(len(rendered), len(original))
        self.assertLess(
            max(abs(left - right) for left, right in zip(rendered, original, strict=True)),
            2e-5,
        )

    def test_public_audio_boundary_bounds_unsafe_positive_gain_for_sole_panned_source(self):
        with TemporaryDirectory(dir=str(_REPOSITORY_ROOT)) as temporary_directory:
            root = Path(temporary_directory)
            project, _, _ = _sole_panned_project(root, amplitude=7.6, gain_db=6.0)
            destination = root / "unsafe-panned-render.wav"

            result = render_audio(project, plan_project_layout(project), destination)
            rendered, sample_rate, channels = _decoded_pcm(destination)

        self.assertEqual(sample_rate, AUDIO_SAMPLE_RATE)
        self.assertEqual(channels, 2)
        self.assertEqual(result.sample_count, int(2.5 * AUDIO_SAMPLE_RATE))
        self.assertLessEqual(result.peak, 0.91)
        self.assertGreater(
            _tone_amplitude(
                rendered,
                start_frame=int(0.5 * AUDIO_SAMPLE_RATE),
                end_frame=int(1.0 * AUDIO_SAMPLE_RATE),
                frequency=880,
                channel=1,
            ),
            0.1,
        )

    def test_public_audio_boundary_preserves_safe_sole_panned_peak_below_unity(self):
        with TemporaryDirectory(dir=str(_REPOSITORY_ROOT)) as temporary_directory:
            root = Path(temporary_directory)
            project, panned, measured_peak = _sole_panned_project(
                root,
                amplitude=10.75,
                gain_db=0.0,
            )
            panned_samples, _, _ = _decoded_pcm(Path(panned.path))
            expected_peak = max(
                0.75 * max(abs(value) for value in panned_samples[0::2]),
                max(abs(value) for value in panned_samples[1::2]),
            )
            destination = root / "safe-panned-render.wav"

            result = render_audio(project, plan_project_layout(project), destination)

        self.assertGreater(measured_peak, 0.93)
        self.assertGreater(expected_peak, 0.7)
        self.assertAlmostEqual(result.peak, expected_peak, delta=0.01)

    def test_public_audio_boundary_skips_zero_sample_microtick_interval(self):
        with TemporaryDirectory(dir=str(_REPOSITORY_ROOT)) as temporary_directory:
            root = Path(temporary_directory)
            source_a = _source(root, "micro-a", frequency=440, duration=1.1)
            source_b = _source(root, "micro-b", frequency=880, duration=1.1)
            project = Project.create_multi((source_a, source_b))
            project.schema_version = SCHEMA_VERSION
            first = Segment.create(
                0.0,
                1.0,
                segment_id="micro-a-block",
                block_id="micro-a-block",
                source_id=source_a.source_id,
                timeline_start_seconds=0.0,
                timeline_end_seconds=1.0,
                track_id="track-a",
            )
            second = Segment.create(
                0.0,
                0.999999,
                segment_id="micro-b-block",
                block_id="micro-b-block",
                source_id=source_b.source_id,
                timeline_start_seconds=0.000001,
                timeline_end_seconds=1.0,
                track_id="track-b",
            )
            project.segment_timeline = project.timeline.__class__.from_tracks(
                (
                    TimelineTrack("track-a", (first,)),
                    TimelineTrack("track-b", (second,)),
                ),
                source_durations={
                    source_a.source_id: 1.1,
                    source_b.source_id: 1.1,
                },
                active_track_id="track-a",
            )
            project.duration_seconds = 1.0
            project.set_source_audio_settings(source_a.source_id, _audio_settings(source_a))
            project.set_source_audio_settings(source_b.source_id, _audio_settings(source_b))
            layout = plan_project_layout(project)
            destination = root / "microtick-render.wav"
            audio_plan = render_audio(project, layout, destination).plan
            samples, sample_rate, channels = _decoded_pcm(destination)

        self.assertEqual(layout.final_duration_ticks, 1_000_000)
        self.assertEqual(len(audio_plan.intervals), 1)
        interval = audio_plan.intervals[0]
        self.assertEqual((interval.start_tick, interval.end_tick), (1, 1_000_000))
        self.assertEqual((interval.start_sample, interval.end_sample), (0, 48_000))
        self.assertEqual(audio_plan.final_sample_count, 48_000)
        self.assertEqual(sample_rate, AUDIO_SAMPLE_RATE)
        self.assertEqual(channels, 2)
        self.assertEqual(len(samples), 2 * 48_000)
        self.assertEqual(
            {
                (
                    block.source_id,
                    block.source_start_sample,
                    block.source_end_sample,
                )
                for block in interval.blocks
            },
            {
                (source_a.source_id, 0, 48_000),
                (source_b.source_id, 0, 48_000),
            },
        )
        self.assertGreater(
            _tone_amplitude(
                samples,
                start_frame=0,
                end_frame=48_000,
                frequency=440,
                channel=0,
            ),
            0.001,
        )
        self.assertGreater(
            _tone_amplitude(
                samples,
                start_frame=0,
                end_frame=48_000,
                frequency=880,
                channel=1,
            ),
            0.001,
        )

    def test_public_audio_boundary_renders_fixed_pan_with_exact_gap_and_peak_bounds(self):
        with TemporaryDirectory(dir=str(_REPOSITORY_ROOT)) as temporary_directory:
            root = Path(temporary_directory)
            left = _source(root, "left", frequency=440)
            right = _source(root, "right", frequency=880)
            silent = _source(root, "silent", frequency=None, channels=2, layout=None)
            unused = _source(root, "unused", frequency=1760)
            project = _project(root, (left, right, silent, unused))
            project.set_source_audio_settings(
                left.source_id,
                _audio_settings(
                    left,
                    gain_db=20.510149966878604,
                    peak_db=-60.0,
                ),
            )
            project.set_source_audio_settings(
                right.source_id,
                _audio_settings(
                    right,
                    gain_db=-36.39083042137054,
                    peak_db=-3.098039347634684,
                ),
            )
            hashes_before = {
                source.source_id: _sha256(Path(source.path))
                for source in (left, right, silent, unused)
            }
            project_path = root / "audio-project.framestudio.json"
            save_project(project, project_path)
            restored = load_project(project_path)
            layout = plan_project_layout(restored)
            destination = root / "composed.wav"

            result = render_audio(restored, layout, destination)
            samples, sample_rate, channels = _decoded_pcm(destination)
            aac_output = root / "composed.m4a"
            _encode_aac(destination, aac_output)
            aac_samples, _, _ = _decoded_pcm(aac_output)
            with self.assertRaises(AudioRenderError):
                render_audio(restored, layout, Path(unused.path))
            hashes_after = {
                source.source_id: _sha256(Path(source.path))
                for source in (left, right, silent, unused)
            }

        self.assertEqual(sample_rate, AUDIO_SAMPLE_RATE)
        self.assertEqual(channels, 2)
        self.assertEqual(result.sample_count, int(2.5 * AUDIO_SAMPLE_RATE))
        self.assertEqual(len(samples), 2 * result.sample_count)
        self.assertLessEqual(max(abs(value) for value in samples), 1.0 + 1e-6)
        self.assertLess(max(abs(value) for value in aac_samples), 0.95)
        self.assertGreater(
            _tone_amplitude(
                samples,
                start_frame=0,
                end_frame=int(0.5 * AUDIO_SAMPLE_RATE),
                frequency=440,
                channel=0,
            ),
            0.0,
        )
        left_440 = _tone_amplitude(
            samples,
            start_frame=int(0.5 * AUDIO_SAMPLE_RATE),
            end_frame=int(1.0 * AUDIO_SAMPLE_RATE),
            frequency=440,
            channel=0,
        )
        right_440 = _tone_amplitude(
            samples,
            start_frame=int(0.5 * AUDIO_SAMPLE_RATE),
            end_frame=int(1.0 * AUDIO_SAMPLE_RATE),
            frequency=440,
            channel=1,
        )
        self.assertAlmostEqual(left_440 / right_440, 1.496606, delta=0.08)
        left_880 = _tone_amplitude(
            samples,
            start_frame=int(0.5 * AUDIO_SAMPLE_RATE),
            end_frame=int(1.0 * AUDIO_SAMPLE_RATE),
            frequency=880,
            channel=0,
        )
        right_880 = _tone_amplitude(
            samples,
            start_frame=int(0.5 * AUDIO_SAMPLE_RATE),
            end_frame=int(1.0 * AUDIO_SAMPLE_RATE),
            frequency=880,
            channel=1,
        )
        self.assertGreater(left_880, 0.0)
        self.assertAlmostEqual(left_880 / right_880, 1.0, delta=0.05)
        self.assertEqual(
            max(
                abs(value)
                for value in samples[
                    2 * int(1.5 * AUDIO_SAMPLE_RATE) : 2 * int(2.0 * AUDIO_SAMPLE_RATE)
                ]
            ),
            0.0,
        )
        self.assertGreater(
            max(abs(value) for value in samples[2 * int(2.0 * AUDIO_SAMPLE_RATE) :]),
            0.0,
        )
        self.assertEqual(
            hashes_before,
            hashes_after,
        )

    def test_public_audio_boundary_renders_four_active_slots_with_stereo_identity(self):
        with TemporaryDirectory(dir=str(_REPOSITORY_ROOT)) as temporary_directory:
            root = Path(temporary_directory)
            sources = (
                _source(root, "slot-one", frequency=440),
                _source(root, "slot-two", frequency=880),
                _source(root, "slot-three", frequency=1320),
                _source(
                    root,
                    "slot-four",
                    frequency=1760,
                    channels=2,
                    layout="stereo",
                ),
            )
            project = Project.create_multi(sources)
            project.schema_version = SCHEMA_VERSION
            for source in sources:
                project.set_source_audio_settings(
                    source.source_id,
                    _audio_settings(source, peak_db=-18.0),
                )
            project.segment_timeline = project.timeline.__class__.from_tracks(
                tuple(
                    TimelineTrack(
                        f"track-{index}",
                        (
                            Segment.create(
                                0.0,
                                1.0,
                                segment_id=f"slot-{index}",
                                block_id=f"slot-{index}",
                                source_id=source.source_id,
                                timeline_start_seconds=0.0,
                                timeline_end_seconds=1.0,
                                track_id=f"track-{index}",
                            ),
                        ),
                    )
                    for index, source in enumerate(sources, start=1)
                ),
                source_durations={
                    source.source_id: float(source.metadata["duration_seconds"])
                    for source in sources
                },
                active_track_id="track-1",
            )
            project.duration_seconds = 1.0
            output = root / "four-slot-output.wav"
            render_audio(project, plan_project_layout(project), output)
            samples, _, _ = _decoded_pcm(output)

        tone_440_left = _tone_amplitude(
            samples,
            start_frame=0,
            end_frame=AUDIO_SAMPLE_RATE,
            frequency=440,
            channel=0,
        )
        tone_440_right = _tone_amplitude(
            samples,
            start_frame=0,
            end_frame=AUDIO_SAMPLE_RATE,
            frequency=440,
            channel=1,
        )
        tone_880_left = _tone_amplitude(
            samples,
            start_frame=0,
            end_frame=AUDIO_SAMPLE_RATE,
            frequency=880,
            channel=0,
        )
        tone_880_right = _tone_amplitude(
            samples,
            start_frame=0,
            end_frame=AUDIO_SAMPLE_RATE,
            frequency=880,
            channel=1,
        )
        tone_1320_left = _tone_amplitude(
            samples,
            start_frame=0,
            end_frame=AUDIO_SAMPLE_RATE,
            frequency=1320,
            channel=0,
        )
        tone_1320_right = _tone_amplitude(
            samples,
            start_frame=0,
            end_frame=AUDIO_SAMPLE_RATE,
            frequency=1320,
            channel=1,
        )
        tone_1760_left = _tone_amplitude(
            samples,
            start_frame=0,
            end_frame=AUDIO_SAMPLE_RATE,
            frequency=1760,
            channel=0,
        )
        tone_1760_right = _tone_amplitude(
            samples,
            start_frame=0,
            end_frame=AUDIO_SAMPLE_RATE,
            frequency=1760,
            channel=1,
        )
        tone_2200_left = _tone_amplitude(
            samples,
            start_frame=0,
            end_frame=AUDIO_SAMPLE_RATE,
            frequency=2200,
            channel=0,
        )
        tone_2200_right = _tone_amplitude(
            samples,
            start_frame=0,
            end_frame=AUDIO_SAMPLE_RATE,
            frequency=2200,
            channel=1,
        )
        self.assertAlmostEqual(tone_440_left / tone_440_right, 1.496606, delta=0.08)
        self.assertAlmostEqual(tone_880_left / tone_880_right, 1.0 / 1.496606, delta=0.08)
        self.assertAlmostEqual(tone_1320_left / tone_1320_right, 2.414214, delta=0.12)
        self.assertGreater(tone_1760_left, 0.0)
        self.assertLess(tone_1760_right, tone_1760_left * 0.05)
        self.assertGreater(tone_2200_right, 0.0)
        self.assertLess(tone_2200_left, tone_2200_right * 0.05)

    def test_public_audio_boundary_maps_real_51_channel_markers(self):
        with TemporaryDirectory(dir=str(_REPOSITORY_ROOT)) as temporary_directory:
            root = Path(temporary_directory)
            for channel_layout in ("5.1", "5.1(side)"):
                with self.subTest(channel_layout=channel_layout):
                    samples = _render_channel_marker_fixture(root, channel_layout)
                    left_fl = _tone_amplitude(
                        samples,
                        start_frame=0,
                        end_frame=AUDIO_SAMPLE_RATE,
                        frequency=440,
                        channel=0,
                    )
                    right_fr = _tone_amplitude(
                        samples,
                        start_frame=0,
                        end_frame=AUDIO_SAMPLE_RATE,
                        frequency=550,
                        channel=1,
                    )
                    self.assertGreater(left_fl, 0.0)
                    self.assertGreater(right_fr, 0.0)
                    self.assertAlmostEqual(
                        _tone_amplitude(
                            samples,
                            start_frame=0,
                            end_frame=AUDIO_SAMPLE_RATE,
                            frequency=660,
                            channel=0,
                        )
                        / left_fl,
                        0.7071067812,
                        delta=0.08,
                    )
                    self.assertAlmostEqual(
                        _tone_amplitude(
                            samples,
                            start_frame=0,
                            end_frame=AUDIO_SAMPLE_RATE,
                            frequency=770,
                            channel=0,
                        )
                        / left_fl,
                        0.5,
                        delta=0.08,
                    )
                    self.assertAlmostEqual(
                        _tone_amplitude(
                            samples,
                            start_frame=0,
                            end_frame=AUDIO_SAMPLE_RATE,
                            frequency=880,
                            channel=0,
                        )
                        / left_fl,
                        0.7071067812,
                        delta=0.08,
                    )
                    self.assertLess(
                        _tone_amplitude(
                            samples,
                            start_frame=0,
                            end_frame=AUDIO_SAMPLE_RATE,
                            frequency=440,
                            channel=1,
                        ),
                        left_fl * 0.05,
                    )


if __name__ == "__main__":
    unittest.main()
