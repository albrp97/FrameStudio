import shutil
import subprocess
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from resolve_editor.export import execute_export, plan_export, plan_mixed_export
from resolve_editor.export_ffmpeg import fallback_filter, mixed_fallback_filter
from resolve_editor.media import MediaProbe, probe_media
from resolve_editor.model import Segment, SegmentTimeline
from resolve_editor.operations import (
    analyze_project_audio,
    create_project_from_sources,
    plan_project_export,
)
from resolve_editor.upscale_policy import UpscalePolicy


def make_probe(
    path: Path,
    *,
    width: int = 1920,
    height: int = 1080,
    audio: bool = True,
    sample_rate: int | None = 48000,
    channels: int | None = 2,
) -> MediaProbe:
    return MediaProbe(
        path=path,
        duration_seconds=2.0,
        width=width,
        height=height,
        frame_rate="10/1",
        video_codec="h264",
        audio_codec="aac" if audio else None,
        format_name="mp4",
        audio_stream_present=audio,
        audio_sample_rate=sample_rate,
        audio_channels=channels,
        audio_channel_layout="stereo" if channels == 2 else None,
    )


class EditorAudioDeliveryTests(unittest.TestCase):
    def test_source_gain_forces_fallback_with_an_explainable_route(self):
        source = Path("/tmp/source.mp4")
        probe = make_probe(source)
        timeline = SegmentTimeline(2.0)

        plan = plan_export(
            probe,
            timeline,
            Path("/tmp/edited.mp4"),
            keyframe_timestamps=(),
            audio_decision={"status": "ready", "gain_db": 3.0},
        )

        self.assertEqual(plan.route, "fallback")
        self.assertIn("source-level audio normalization", plan.reason)

    def test_unchanged_audio_profile_remains_stream_copy_eligible(self):
        probe = make_probe(Path("/tmp/source.mp4"))
        timeline = SegmentTimeline(2.0)

        plan = plan_export(
            probe,
            timeline,
            Path("/tmp/edited.mp4"),
            keyframe_timestamps=(),
            audio_decision={"status": "ready", "gain_db": 0.0},
        )

        self.assertEqual(plan.route, "stream-copy")

    def test_one_source_filter_normalizes_audio_before_segment_splits(self):
        segments = (
            Segment.create(0.0, 1.0),
            Segment.create(1.0, 2.0),
        )

        rendered = fallback_filter(
            segments,
            True,
            audio_decision={"status": "ready", "gain_db": 2.5},
        )

        self.assertEqual(rendered.count("volume=2.50dB"), 1)
        self.assertEqual(rendered.count("[0:a]"), 1)
        self.assertIn("[normalized_audio]asplit=2", rendered)
        self.assertEqual(rendered.count("atrim=start="), 2)

    def test_mixed_source_filter_uses_each_source_decision(self):
        first = make_probe(Path("/tmp/first.mp4"))
        second = make_probe(
            Path("/tmp/second.mp4"),
            width=720,
            height=1280,
        )
        first_id = "first"
        second_id = "second"
        timeline = SegmentTimeline.from_blocks(
            (
                Segment.create(
                    0.0,
                    1.0,
                    source_id=first_id,
                    timeline_start_seconds=0.0,
                    timeline_end_seconds=1.0,
                ),
                Segment.create(
                    1.0,
                    2.0,
                    source_id=first_id,
                    timeline_start_seconds=1.0,
                    timeline_end_seconds=2.0,
                ),
                Segment.create(
                    0.0,
                    2.0,
                    source_id=second_id,
                    timeline_start_seconds=2.0,
                    timeline_end_seconds=4.0,
                ),
            ),
            duration_seconds=4.0,
            source_durations={first_id: 2.0, second_id: 2.0},
        )
        plan = plan_mixed_export(
            (first, second),
            timeline,
            Path("/tmp/mixed.mp4"),
            source_ids=(first_id, second_id),
            audio_decisions={
                first_id: {"status": "ready", "gain_db": 2.0},
                second_id: {"status": "ready", "gain_db": -3.0},
            },
        )

        rendered = mixed_fallback_filter(plan, (first, second))

        self.assertIn("[normalized_audio_0_0]atrim=start=0.000000:duration=1.000000", rendered)
        self.assertIn("volume=2.00dB", rendered)
        self.assertIn("[normalized_audio_0_1]atrim=start=1.000000:duration=1.000000", rendered)
        self.assertIn("[normalized_audio_1]atrim=start=0.000000:duration=2.000000", rendered)
        self.assertIn("volume=-3.00dB", rendered)
        self.assertEqual(rendered.count("volume=2.00dB"), 1)
        self.assertEqual(rendered.count("volume=-3.00dB"), 1)
        self.assertIn("[normalized_audio_0]asplit=2", rendered)
        self.assertEqual(
            set(plan.to_dict()["audio_decisions"]),
            {first_id, second_id},
        )

    def test_mixed_plan_excludes_sources_without_active_timeline_segments(self):
        first_id = "first"
        second_id = "second"
        unused_id = "unused"
        first_path = Path("/tmp/first.mp4")
        second_path = Path("/tmp/second.mp4")
        unused_path = Path("/tmp/unused.mp4")
        first = make_probe(first_path)
        second = make_probe(second_path, width=720, height=1280)
        unused = make_probe(unused_path, width=640, height=360)
        timeline = SegmentTimeline.from_blocks(
            (
                Segment.create(
                    0.0,
                    1.0,
                    source_id=first_id,
                    timeline_start_seconds=0.0,
                    timeline_end_seconds=1.0,
                ),
                Segment.create(
                    0.0,
                    1.0,
                    source_id=second_id,
                    timeline_start_seconds=1.0,
                    timeline_end_seconds=2.0,
                ),
            ),
            duration_seconds=2.0,
            source_durations={first_id: 2.0, second_id: 2.0, unused_id: 2.0},
        )

        plan = plan_mixed_export(
            (first, second, unused),
            timeline,
            Path("/tmp/mixed.mp4"),
            source_ids=(first_id, second_id, unused_id),
            audio_decisions={
                first_id: {"status": "ready", "gain_db": 0.0},
                second_id: {"status": "ready", "gain_db": 0.0},
                unused_id: {"status": "ready", "gain_db": 0.0},
            },
        )

        self.assertEqual(plan.source_ids, (first_id, second_id))
        self.assertEqual(plan.source_paths, (first_path.resolve(), second_path.resolve()))
        self.assertEqual(set(plan.to_dict()["audio_decisions"]), {first_id, second_id})

    @unittest.skipUnless(
        shutil.which("ffmpeg") and shutil.which("ffprobe"),
        "FFmpeg and ffprobe are required",
    )
    def test_mixed_export_applies_source_decisions_and_preserves_sources(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            first = root / "first.mp4"
            second = root / "second.mp4"
            for path, size, frequency in (
                (first, "320x180", "440"),
                (second, "180x320", "880"),
            ):
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
                        f"testsrc=size={size}:rate=10",
                        "-f",
                        "lavfi",
                        "-i",
                        f"sine=frequency={frequency}:sample_rate=48000",
                        "-t",
                        "0.6",
                        "-c:v",
                        "libx264",
                        "-pix_fmt",
                        "yuv420p",
                        "-c:a",
                        "aac",
                        "-ac",
                        "2",
                        "-shortest",
                        str(path),
                    ],
                    check=True,
                )
            source_bytes = {path: path.read_bytes() for path in (first, second)}
            project = create_project_from_sources((first, second))
            decisions = analyze_project_audio(project)
            project.timeline.split_block(
                project.timeline.blocks[0].segment_id,
                0.3,
                coordinate="timeline",
            )
            destination = root / "mixed.mp4"
            plan = plan_project_export(
                project,
                destination,
                upscale_policy=UpscalePolicy(enhancement_enabled=False),
            )
            execute_export(plan)

            output_probe = probe_media(destination)

            self.assertEqual(plan.route, "fallback")
            self.assertEqual(set(decisions), set(project.source_settings))
            self.assertEqual(output_probe.width, 1920)
            self.assertEqual(output_probe.height, 1080)
            self.assertTrue(output_probe.has_audio_stream)
            self.assertEqual(output_probe.audio_sample_rate, 48000)
            self.assertEqual(output_probe.audio_channels, 2)
            self.assertAlmostEqual(
                output_probe.duration_seconds,
                project.timeline.edited_duration_seconds,
                delta=0.15,
            )
            self.assertEqual(
                {path: path.read_bytes() for path in (first, second)},
                source_bytes,
            )


if __name__ == "__main__":
    unittest.main()
