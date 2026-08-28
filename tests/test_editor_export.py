import shutil
import subprocess
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from resolve_editor.export import (
    ExportExecutionError,
    ExportPlan,
    ExportPlanningError,
    OutputPolicy,
    parse_ffmpeg_progress_values,
    plan_export,
)
from resolve_editor.export_delivery import verify_mixed_export_output
from resolve_editor.fps_policy import FrameRatePolicy
from resolve_editor.media import MediaProbe, probe_media
from resolve_editor.model import SegmentTimeline
from resolve_editor.upscale_policy import UpscalePolicy


def media_probe(
    root: Path,
    *,
    format_name: str = "mov,mp4,m4a,3gp,3g2,mj2",
) -> MediaProbe:
    source = root / "source.mp4"
    return MediaProbe(
        path=source,
        duration_seconds=10.0,
        width=1920,
        height=1080,
        frame_rate="30/1",
        video_codec="h264",
        audio_codec="aac",
        format_name=format_name,
    )


class EditorExportPlannerTests(unittest.TestCase):
    def test_mixed_enhanced_output_rejects_an_incorrect_frame_count(self):
        with TemporaryDirectory() as temporary_directory:
            candidate = Path(temporary_directory) / "enhanced.mp4"
            candidate.write_bytes(b"candidate")
            plan = ExportPlan(
                route="enhanced",
                source=Path("first.mp4"),
                destination=candidate,
                segments=(),
                expected_duration_seconds=1.0,
                reason="enhancement",
                source_paths=(Path("first.mp4"), Path("second.mp4")),
                source_ids=("first", "second"),
                output_policy=OutputPolicy(
                    width=1920,
                    height=1080,
                    scaling_mode="contain-letterbox",
                    frame_rate="20/1",
                    timebase="1/1000000",
                    container="mp4",
                    video_codec="libx264",
                    audio_codec=None,
                    pixel_format="yuv420p",
                    audio_stream_present=False,
                    requires_normalization=True,
                    reason="test",
                ),
            )
            output_probe = MediaProbe(
                path=candidate,
                duration_seconds=1.0,
                width=1920,
                height=1080,
                frame_rate="20/1",
                video_codec="h264",
                audio_codec=None,
                format_name="mp4",
            )

            with (
                patch("resolve_editor.export_delivery.probe_media", return_value=output_probe),
                patch("resolve_editor.export_delivery.probe_frame_count", return_value=19),
                patch("resolve_editor.export_delivery.validate_decoded_output"),
            ):
                with self.assertRaisesRegex(
                    ExportExecutionError,
                    "frame count",
                ):
                    verify_mixed_export_output(
                        plan,
                        candidate,
                        ffmpeg_path="ffmpeg",
                        ffprobe_path="ffprobe",
                    )

    def test_selected_target_rate_is_persisted_on_the_plan_and_forces_conversion(self):
        probe = media_probe(Path("/tmp"))
        timeline = SegmentTimeline(10.0)
        policy = FrameRatePolicy(
            choice="60",
            target_rate="60/1",
            enhancement_enabled=False,
        )

        plan = plan_export(
            probe,
            timeline,
            Path("/tmp/edited.mp4"),
            frame_rate_policy=policy,
        )

        self.assertEqual(plan.route, "fallback")
        self.assertEqual(plan.output_policy.frame_rate, "60")
        self.assertEqual(plan.frame_rate_policy.to_dict(), policy.to_dict())
        self.assertEqual(plan.rate_decisions[0].action, "convert")

    def test_enabled_supported_rate_selects_explicit_enhanced_route(self):
        probe = media_probe(Path("/tmp"))
        timeline = SegmentTimeline(10.0)
        policy = FrameRatePolicy(
            choice="60",
            target_rate="60/1",
            enhancement_enabled=True,
        )

        plan = plan_export(
            probe,
            timeline,
            Path("/tmp/edited.mp4"),
            frame_rate_policy=policy,
        )

        self.assertEqual(plan.route, "enhanced")
        self.assertEqual(plan.rate_decisions[0].action, "interpolate")

    def test_fractional_rve_enhancement_selects_gpu_route(self):
        probe = MediaProbe(
            path=Path("/tmp/source.mp4"),
            duration_seconds=10.0,
            width=1920,
            height=1080,
            frame_rate="24/1",
            video_codec="h264",
            audio_codec=None,
            format_name="mp4",
        )
        policy = FrameRatePolicy(
            choice="60",
            target_rate="60/1",
            enhancement_enabled=True,
        )

        plan = plan_export(
            probe,
            SegmentTimeline(10.0),
            Path("/tmp/edited.mp4"),
            frame_rate_policy=policy,
        )

        self.assertEqual(plan.route, "enhanced")
        self.assertEqual(plan.rate_decisions[0].action, "interpolate")

    def test_ffmpeg_progress_values_include_frame_time_fps_and_completion(self):
        progress = parse_ffmpeg_progress_values(
            {
                "frame": "42",
                "fps": "29.97",
                "out_time_us": "5000000",
                "speed": "1.5x",
                "progress": "continue",
            }
        )

        self.assertEqual(progress.frame, 42)
        self.assertAlmostEqual(progress.fps, 29.97)
        self.assertEqual(progress.out_time_seconds, 5.0)
        self.assertEqual(progress.speed, "1.5x")
        self.assertFalse(progress.done)

        completed = parse_ffmpeg_progress_values({"progress": "end"})
        self.assertTrue(completed.done)

    def test_keyframe_aligned_cut_selects_stream_copy(self):
        source = Path("/tmp/source.mp4")
        probe = media_probe(source.parent)
        timeline = SegmentTimeline(10.0)
        timeline.split(5.0)
        destination = Path("/tmp/edited.mp4")

        plan = plan_export(
            probe,
            timeline,
            destination,
            keyframe_timestamps=(0.0, 5.0, 10.0),
        )

        self.assertEqual(plan.route, "stream-copy")
        self.assertEqual(plan.expected_duration_seconds, 10.0)
        self.assertIn("keyframe", plan.reason.lower())
        self.assertEqual(plan.destination, destination)

    def test_pasted_one_source_block_keeps_source_duration_for_export_planning(self):
        probe = media_probe(Path("/tmp"))
        timeline = SegmentTimeline(10.0)
        timeline.split(3.0)
        copied = timeline.copy_blocks([timeline.segments[0].segment_id])
        timeline.paste_blocks(copied, at_index=1)

        plan = plan_export(
            probe,
            timeline,
            Path("/tmp/edited.mp4"),
            keyframe_timestamps=(0.0, 3.0, 10.0),
        )

        self.assertEqual(plan.expected_duration_seconds, 13.0)
        self.assertEqual(len(plan.segments), 3)
        self.assertEqual(timeline.source_duration_seconds, 10.0)

    def test_non_1080p_source_requires_fixed_canvas_fallback(self):
        probe = MediaProbe(
            path=Path("/tmp/source.mp4"),
            duration_seconds=10.0,
            width=320,
            height=180,
            frame_rate="30/1",
            video_codec="h264",
            audio_codec=None,
            format_name="mp4",
        )
        timeline = SegmentTimeline(10.0)

        plan = plan_export(
            probe,
            timeline,
            Path("/tmp/edited.mp4"),
            keyframe_timestamps=(),
            upscale_policy=UpscalePolicy(enhancement_enabled=False),
        )

        self.assertEqual(plan.route, "fallback")
        self.assertEqual(plan.output_policy.width, 1920)
        self.assertEqual(plan.output_policy.height, 1080)
        self.assertIn("1920x1080", plan.reason)

    def test_non_keyframe_cut_selects_explicit_fallback(self):
        probe = media_probe(Path("/tmp"))
        timeline = SegmentTimeline(10.0)
        timeline.split(4.5)

        plan = plan_export(
            probe,
            timeline,
            Path("/tmp/edited.mp4"),
            keyframe_timestamps=(0.0, 10.0),
        )

        self.assertEqual(plan.route, "fallback")
        self.assertIn("keyframe", plan.reason.lower())
        self.assertEqual(plan.fallback_video_codec, "libx264")
        self.assertEqual(plan.fallback_audio_codec, "aac")

    def test_unsupported_container_selects_explicit_fallback(self):
        probe = media_probe(Path("/tmp"), format_name="avi")
        timeline = SegmentTimeline(10.0)

        plan = plan_export(
            probe,
            timeline,
            Path("/tmp/edited.mp4"),
            keyframe_timestamps=(),
        )

        self.assertEqual(plan.route, "fallback")
        self.assertIn("container", plan.reason.lower())

    def test_unknown_audio_codec_keeps_audio_in_fallback_plan(self):
        probe = MediaProbe(
            path=Path("/tmp/source.mp4"),
            duration_seconds=10.0,
            width=1920,
            height=1080,
            frame_rate="30/1",
            video_codec="h264",
            audio_codec=None,
            format_name="mov,mp4",
            audio_stream_present=True,
        )
        timeline = SegmentTimeline(10.0)

        plan = plan_export(
            probe,
            timeline,
            Path("/tmp/edited.mp4"),
        )

        self.assertEqual(plan.route, "fallback")
        self.assertEqual(plan.fallback_audio_codec, "aac")

    def test_empty_edit_is_rejected_before_planning(self):
        probe = media_probe(Path("/tmp"))
        timeline = SegmentTimeline(10.0)
        timeline.delete_segment(timeline.segments[0].segment_id)

        with self.assertRaisesRegex(ExportPlanningError, "empty"):
            plan_export(
                probe,
                timeline,
                Path("/tmp/edited.mp4"),
                keyframe_timestamps=(),
            )

    def test_missing_keyframe_tool_is_an_explicit_planning_error(self):
        probe = media_probe(Path("/tmp"))
        timeline = SegmentTimeline(10.0)
        timeline.split(5.0)

        with self.assertRaisesRegex(ExportPlanningError, "not installed"):
            plan_export(
                probe,
                timeline,
                Path("/tmp/edited.mp4"),
                ffprobe_path="/missing/ffprobe",
            )

    def test_invalid_keyframe_timestamp_is_rejected(self):
        probe = media_probe(Path("/tmp"))
        timeline = SegmentTimeline(10.0)
        timeline.split(5.0)

        with self.assertRaisesRegex(ExportPlanningError, "timestamps"):
            plan_export(
                probe,
                timeline,
                Path("/tmp/edited.mp4"),
                keyframe_timestamps=(0.0, float("nan")),
            )

    def test_plan_is_deterministic_for_equivalent_inputs(self):
        probe = media_probe(Path("/tmp"))
        timeline = SegmentTimeline(10.0)
        timeline.split(5.0)
        destination = Path("/tmp/edited.mp4")

        first = plan_export(
            probe,
            timeline,
            destination,
            keyframe_timestamps=(0.0, 5.0, 10.0),
        )
        second = plan_export(
            probe,
            timeline,
            destination,
            keyframe_timestamps=(0.0, 5.0, 10.0),
        )

        self.assertEqual(first.to_dict(), second.to_dict())

    @unittest.skipUnless(
        shutil.which("ffmpeg") and shutil.which("ffprobe"),
        "FFmpeg and ffprobe are required",
    )
    def test_planner_can_probe_keyframes_from_real_media(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = root / "source.mp4"
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
                    "-t",
                    "1",
                    "-g",
                    "5",
                    "-c:v",
                    "libx264",
                    "-pix_fmt",
                    "yuv420p",
                    str(source),
                ],
                check=True,
            )
            probe = probe_media(source)
            timeline = SegmentTimeline(probe.duration_seconds)
            timeline.split(0.5)

            plan = plan_export(
                probe,
                timeline,
                root / "edited.mp4",
            )

            self.assertIn(plan.route, {"stream-copy", "fallback"})
            self.assertTrue(plan.reason)


if __name__ == "__main__":
    unittest.main()
