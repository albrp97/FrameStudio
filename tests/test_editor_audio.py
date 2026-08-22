import math
import os
import shutil
import subprocess
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from resolve_editor.audio import (
    AudioStats,
    analyze_audio,
    analyze_source_audio,
    audio_filter,
    audio_gain_db,
)
from resolve_editor.model import Project, SourceReference
from resolve_editor.operations import (
    analyze_project_audio,
    copy_segments,
    ensure_project_audio_analysis,
    paste_segments,
)
from resolve_editor.persistence import load_project, save_project


def source_reference(
    root: Path,
    *,
    filename: str = "source.mp4",
    audio: bool = True,
    codec: str | None = "aac",
) -> SourceReference:
    source = root / filename
    source.write_bytes(b"fixture")
    return SourceReference.from_path(
        source,
        {
            "duration_seconds": 1.0,
            "width": 320,
            "height": 180,
            "frame_rate": "10/1",
            "video_codec": "h264",
            "audio_codec": codec,
            "audio_stream_present": audio,
            "audio_sample_rate": 48000,
            "audio_channels": 2,
            "audio_channel_layout": "stereo",
            "format_name": "mp4",
        },
    )


class EditorAudioPolicyTests(unittest.TestCase):
    def test_gain_matches_legacy_mean_median_and_peak_policy(self):
        self.assertAlmostEqual(
            audio_gain_db(
                AudioStats(
                    peak_db=-6.0,
                    mean_rms_db=-34.0,
                    median_db=-54.0,
                )
            ),
            1.5,
        )
        self.assertAlmostEqual(
            audio_gain_db(
                AudioStats(
                    peak_db=2.0,
                    mean_rms_db=-40.0,
                    median_db=-60.0,
                )
            ),
            -3.0,
        )

    def test_silent_stats_use_an_explicit_zero_gain_fallback(self):
        stats = AudioStats(
            peak_db=-math.inf,
            mean_rms_db=-math.inf,
            median_db=-200.0,
            sample_count=10,
        )

        self.assertEqual(audio_gain_db(stats), 0.0)

    def test_audio_filter_applies_one_decision_without_segment_specific_values(self):
        decision = {
            "status": "ready",
            "gain_db": 2.5,
        }

        rendered = audio_filter(decision)

        self.assertIn("aresample=48000:async=1:first_pts=0", rendered)
        self.assertIn("aformat=sample_rates=48000:channel_layouts=stereo", rendered)
        self.assertIn("volume=2.50dB", rendered)
        self.assertTrue(rendered.endswith("asetpts=PTS-STARTPTS"))

    def test_sources_without_audio_are_not_applicable(self):
        with TemporaryDirectory() as temporary_directory:
            decision = analyze_source_audio(
                source_reference(Path(temporary_directory), audio=False, codec=None),
            )

        self.assertEqual(decision.status, "not-applicable")
        self.assertEqual(decision.gain_db, 0.0)
        self.assertIn("no audio", decision.diagnostic.lower())

    def test_missing_audio_codec_is_an_explicit_unsupported_state(self):
        with TemporaryDirectory() as temporary_directory:
            decision = analyze_source_audio(
                source_reference(Path(temporary_directory), audio=True, codec=None),
            )

        self.assertEqual(decision.status, "unsupported")
        self.assertEqual(decision.gain_db, 0.0)
        self.assertIn("codec", decision.diagnostic.lower())

    def test_analysis_failure_is_persistable_and_explicit(self):
        with TemporaryDirectory() as temporary_directory:
            decision = analyze_source_audio(
                source_reference(Path(temporary_directory)),
                ffmpeg_path="/missing/ffmpeg",
            )

        self.assertEqual(decision.status, "failed")
        self.assertEqual(decision.gain_db, 0.0)
        self.assertIn("ffmpeg", decision.diagnostic.lower())

    @unittest.skipUnless(
        shutil.which("ffmpeg") and shutil.which("ffprobe"),
        "FFmpeg and ffprobe are required",
    )
    def test_real_pcm_measurement_is_deterministic_and_non_empty(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = root / "tone.mp4"
            subprocess.run(
                [
                    "ffmpeg",
                    "-hide_banner",
                    "-loglevel",
                    "error",
                    "-f",
                    "lavfi",
                    "-i",
                    "testsrc=size=32x32:rate=10",
                    "-f",
                    "lavfi",
                    "-i",
                    "sine=frequency=880:sample_rate=48000",
                    "-t",
                    "0.5",
                    "-c:v",
                    "libx264",
                    "-pix_fmt",
                    "yuv420p",
                    "-c:a",
                    "aac",
                    "-shortest",
                    str(source),
                ],
                check=True,
            )
            first = analyze_audio(source)
            second = analyze_audio(source)

        self.assertGreater(first.sample_count, 0)
        self.assertEqual(first, second)
        self.assertTrue(math.isfinite(first.peak_db))
        self.assertTrue(math.isfinite(first.mean_rms_db))

    def test_project_round_trip_preserves_source_audio_settings(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = root / "source.mp4"
            source.write_bytes(b"fixture")
            project = Project.create(
                source,
                {
                    "duration_seconds": 1.0,
                    "width": 320,
                    "height": 180,
                    "frame_rate": "10/1",
                    "video_codec": "h264",
                    "audio_codec": "aac",
                    "audio_stream_present": True,
                    "format_name": "mp4",
                },
            )
            settings = project.source_audio_settings(project.source.source_id)
            settings["status"] = "ready"
            settings["gain_db"] = 1.25
            project.set_source_audio_settings(project.source.source_id, settings)
            destination = root / "project.resolve.json"

            save_project(project, destination)
            restored = load_project(destination)

        restored_settings = restored.source_audio_settings(restored.source.source_id)
        self.assertEqual(restored_settings["status"], "ready")
        self.assertEqual(restored_settings["gain_db"], 1.25)
        self.assertEqual(
            restored_settings["source_fingerprint"],
            settings["source_fingerprint"],
        )

    def test_source_decision_is_reused_after_split_copy_and_paste(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = root / "source.mp4"
            source.write_bytes(b"fixture")
            project = Project.create(
                source,
                {
                    "duration_seconds": 4.0,
                    "width": 320,
                    "height": 180,
                    "frame_rate": "10/1",
                    "video_codec": "h264",
                    "audio_codec": "aac",
                    "audio_stream_present": True,
                    "format_name": "mp4",
                },
            )

            decisions = analyze_project_audio(project, ffmpeg_path="/missing/ffmpeg")
            project.timeline.split(2.0)
            copied = copy_segments(project, [project.timeline.segments[0].segment_id])
            paste_segments(project, copied, at_index=1)
            project.validate()

        source_id = project.source.source_id
        self.assertEqual(set(decisions), {source_id})
        self.assertEqual(
            set(project.source_settings),
            {source_id},
        )
        self.assertEqual(
            project.source_audio_settings(source_id),
            decisions[source_id].to_dict(),
        )
        self.assertEqual(len(project.timeline.segment_items), 3)

    def test_multi_source_analysis_keeps_independent_source_decisions(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            first = source_reference(root, filename="first.mp4")
            second = source_reference(root, filename="second.mp4")
            project = Project.create_multi((first, second))

            decisions = analyze_project_audio(project, ffmpeg_path="/missing/ffmpeg")

        self.assertEqual(
            set(decisions),
            {first.source_id, second.source_id},
        )
        self.assertIsNot(
            decisions[first.source_id],
            decisions[second.source_id],
        )
        self.assertEqual(
            project.source_audio_settings(first.source_id)["status"],
            "failed",
        )
        self.assertEqual(
            project.source_audio_settings(second.source_id)["status"],
            "failed",
        )

    def test_changed_relinked_source_marks_decision_stale_until_reanalyzed(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = source_reference(root)
            project = Project.create_multi((source,))
            analyze_project_audio(project, ffmpeg_path="/missing/ffmpeg")
            original_settings = project.source_audio_settings(source.source_id)

            replacement_path = root / "replacement.mp4"
            replacement_path.write_bytes(b"fixture")
            os.utime(
                replacement_path,
                ns=(source.modified_time_ns + 1, source.modified_time_ns + 1),
            )
            replacement = project.relink_source(
                source.source_id,
                replacement_path,
                source.metadata,
            )

            self.assertEqual(
                ensure_project_audio_analysis(
                    project,
                    ffmpeg_path="/missing/ffmpeg",
                )[source.source_id]["status"],
                "failed",
            )
            refreshed_settings = project.source_audio_settings(source.source_id)

        self.assertNotEqual(
            original_settings["source_fingerprint"],
            refreshed_settings["source_fingerprint"],
        )
        self.assertEqual(
            refreshed_settings["source_fingerprint"]["modified_time_ns"],
            replacement.modified_time_ns,
        )
        self.assertEqual(
            refreshed_settings["status"],
            "failed",
        )


if __name__ == "__main__":
    unittest.main()
