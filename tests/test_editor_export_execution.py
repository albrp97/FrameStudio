import json
import shutil
import subprocess
import threading
import unittest
from dataclasses import replace
from fractions import Fraction
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from framestudio import export_ffmpeg, export_interpolation
from framestudio.export import (
    ExportExecutionError,
    ExportPlan,
    discover_export_session,
    execute_export,
    plan_export,
    plan_mixed_export,
)
from framestudio.export_cache import ExportCacheError
from framestudio.export_interpolation import execute_enhanced_export
from framestudio.export_process import publish_verified_export, run_ffmpeg
from framestudio.export_smart_render import PreparedSource
from framestudio.fps_policy import FrameRatePolicy, resolve_frame_rate_policy
from framestudio.media import MediaProbe, probe_media
from framestudio.model import Segment, SegmentTimeline
from framestudio.upscale_policy import UpscalePolicy, resolve_upscale_policy


@unittest.skipUnless(
    shutil.which("ffmpeg") and shutil.which("ffprobe"),
    "FFmpeg and ffprobe are required",
)
class EditorExportExecutionTests(unittest.TestCase):
    def make_source(
        self,
        root: Path,
        *,
        name: str = "source.mp4",
        size: str = "64x64",
        rate: int = 10,
        frequency: int = 880,
        audio_channels: int | None = None,
        duration: float = 1.0,
        gop: int = 5,
    ) -> Path:
        source = root / name
        command = [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "lavfi",
            "-i",
            f"testsrc=size={size}:rate={rate}",
            "-f",
            "lavfi",
            "-i",
            f"sine=frequency={frequency}:sample_rate=48000",
            "-t",
            str(duration),
            "-c:v",
            "libx264",
            "-g",
            str(gop),
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-shortest",
        ]
        if audio_channels is not None:
            command.extend(["-ac", str(audio_channels)])
        command.append(str(source))
        subprocess.run(command, check=True)
        return source

    def make_boundary_source(self, root: Path) -> Path:
        source = root / "boundary-source.mp4"
        subprocess.run(
            [
                "ffmpeg",
                "-hide_banner",
                "-loglevel",
                "error",
                "-f",
                "lavfi",
                "-i",
                "color=c=0x646464:s=64x64:r=10:d=0.5",
                "-f",
                "lavfi",
                "-i",
                "color=c=0x6e6e6e:s=64x64:r=10:d=0.5",
                "-filter_complex",
                "[0:v][1:v]concat=n=2:v=1:a=0[outv]",
                "-map",
                "[outv]",
                "-c:v",
                "libx264",
                "-g",
                "10",
                "-pix_fmt",
                "yuv420p",
                str(source),
            ],
            check=True,
        )
        return source

    def test_fallback_export_is_verified_and_preserves_source(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = self.make_source(root)
            source_before = source.read_bytes()
            probe = probe_media(source)
            timeline = SegmentTimeline(probe.duration_seconds)
            timeline.split(0.5)
            timeline.delete_segment(timeline.segments[1].segment_id)
            destination = root / "edited.mp4"
            plan = plan_export(
                probe,
                timeline,
                destination,
                keyframe_timestamps=(),
            )
            progress = []

            result = execute_export(
                plan,
                progress_callback=progress.append,
            )

            self.assertEqual(result, destination)
            self.assertTrue(destination.is_file())
            self.assertEqual(source.read_bytes(), source_before)
            output = probe_media(destination)
            self.assertAlmostEqual(output.duration_seconds, 0.5, delta=0.15)
            self.assertEqual((output.width, output.height), (1920, 1080))
            self.assertIsNotNone(output.audio_codec)
            self.assertEqual(progress[-1].stage, "complete")
            self.assertTrue(any(item.fps is not None for item in progress))

    def test_failed_export_can_resume_from_persisted_assembly(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = root / "source.mp4"
            source.write_bytes(b"source")
            destination = root / "resumed.mp4"
            source_probe = MediaProbe(
                path=source,
                duration_seconds=1.0,
                width=64,
                height=64,
                frame_rate="10/1",
                video_codec="h264",
                audio_codec=None,
                format_name="mp4",
            )
            plan = plan_export(
                source_probe,
                SegmentTimeline(1.0),
                destination,
                keyframe_timestamps=(),
            )
            render_calls = 0
            publish_calls = 0

            def fake_render(_plan, _probe, partial, _ffmpeg_path, **_kwargs):
                nonlocal render_calls
                render_calls += 1
                partial.write_bytes(b"assembled")

            def fake_verify(_plan, _probe, _candidate, **_kwargs):
                return source_probe

            def fake_publish(partial, output, *_args, **_kwargs):
                nonlocal publish_calls
                publish_calls += 1
                if publish_calls == 1:
                    raise ExportExecutionError("late publication failure")
                partial.replace(output)

            with (
                patch("framestudio.export_delivery.probe_media", return_value=source_probe),
                patch(
                    "framestudio.export_delivery.execute_fallback",
                    side_effect=fake_render,
                ),
                patch(
                    "framestudio.export_delivery.verify_export_output",
                    side_effect=fake_verify,
                ),
                patch(
                    "framestudio.export_delivery.publish_verified_export",
                    side_effect=fake_publish,
                ),
            ):
                with self.assertRaises(ExportExecutionError):
                    execute_export(plan)
                self.assertEqual(render_calls, 1)

                result = execute_export(plan, resume_mode="resume")

            self.assertEqual(result, destination)
            self.assertEqual(render_calls, 1)
            self.assertEqual(publish_calls, 2)
            self.assertEqual(destination.read_bytes(), b"assembled")

    def test_explicit_ffmpeg_interpolation_route_is_verified_end_to_end(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = self.make_source(root, size="64x64")
            source_before = source.read_bytes()
            probe = probe_media(source)
            timeline = SegmentTimeline(probe.duration_seconds)
            policy = FrameRatePolicy(
                choice="custom",
                custom_rate="20/1",
                target_rate="20/1",
                enhancement_enabled=True,
                backend="ffmpeg-minterpolate",
            )
            plan = plan_export(
                probe,
                timeline,
                root / "enhanced.mp4",
                keyframe_timestamps=(),
                frame_rate_policy=policy,
            )
            progress = []

            result = execute_export(plan, progress_callback=progress.append)

            self.assertEqual(result, root / "enhanced.mp4")
            self.assertEqual(source.read_bytes(), source_before)
            output = probe_media(result)
            self.assertEqual(output.frame_rate, "20/1")
            self.assertAlmostEqual(output.duration_seconds, probe.duration_seconds, delta=0.15)
            self.assertIsNotNone(output.audio_codec)
            interpolation_progress = [
                item for item in progress if item.stage.startswith("interpolation")
            ]
            self.assertTrue(any(item.frame > 0 for item in interpolation_progress))
            self.assertTrue(any(item.fps is not None for item in interpolation_progress))

    def test_enhanced_export_resume_reuses_persisted_assembly(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = root / "source.mp4"
            source.write_bytes(b"source")
            source_probe = MediaProbe(
                path=source,
                duration_seconds=1.0,
                width=64,
                height=64,
                frame_rate="10/1",
                video_codec="h264",
                audio_codec=None,
                format_name="mp4",
            )
            destination = root / "enhanced-resumed.mp4"
            plan = plan_export(
                source_probe,
                SegmentTimeline(1.0),
                destination,
                keyframe_timestamps=(),
                frame_rate_policy=FrameRatePolicy(
                    choice="custom",
                    custom_rate="20/1",
                    target_rate="20/1",
                    enhancement_enabled=True,
                    backend="ffmpeg-minterpolate",
                ),
            )
            render_calls = 0
            publish_calls = 0

            def fake_render(_plan, _probes, _decisions, *, partial, **_kwargs):
                nonlocal render_calls
                render_calls += 1
                partial.write_bytes(b"enhanced-assembly")

            def fake_verify(_plan, _probe, _candidate, **_kwargs):
                return source_probe

            def fake_publish(partial, output, *_args, **_kwargs):
                nonlocal publish_calls
                publish_calls += 1
                if publish_calls == 1:
                    raise ExportExecutionError("late enhanced publication failure")
                partial.replace(output)

            with (
                patch(
                    "framestudio.export_interpolation.prepare_export_sources",
                    return_value=((source.stat(),), (source_probe,)),
                ),
                patch(
                    "framestudio.export_interpolation._execute_per_source_enhanced_render",
                    side_effect=fake_render,
                ),
                patch(
                    "framestudio.export_interpolation.publish_verified_export",
                    side_effect=fake_publish,
                ),
            ):
                with self.assertRaises(ExportExecutionError):
                    execute_enhanced_export(
                        plan,
                        ffmpeg_path="ffmpeg",
                        ffprobe_path="ffprobe",
                        progress_callback=None,
                        verify_single_output=fake_verify,
                        verify_mixed_output=lambda *_args, **_kwargs: source_probe,
                    )
                result = execute_enhanced_export(
                    plan,
                    ffmpeg_path="ffmpeg",
                    ffprobe_path="ffprobe",
                    progress_callback=None,
                    verify_single_output=fake_verify,
                    verify_mixed_output=lambda *_args, **_kwargs: source_probe,
                    resume_mode="resume",
                )

            self.assertEqual(result, destination)
            self.assertEqual(render_calls, 1)
            self.assertEqual(publish_calls, 2)
            self.assertEqual(destination.read_bytes(), b"enhanced-assembly")

    def test_upscale_only_export_restores_then_preserves_source_resolution(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = self.make_source(root, size="64x36", rate=10)
            source_before = source.read_bytes()
            probe = probe_media(source)
            destination = root / "upscaled.mp4"
            plan = plan_export(
                probe,
                SegmentTimeline(probe.duration_seconds),
                destination,
                keyframe_timestamps=(),
                upscale_policy=UpscalePolicy(enhancement_enabled=True),
            )
            restoration_calls = []

            def fake_restore(restoration_probe, output, **_kwargs):
                shutil.copyfile(restoration_probe.path, output)
                restoration_calls.append(output)
                return probe_media(output)

            with patch(
                "framestudio.export_smart_render._run_source_restoration",
                side_effect=fake_restore,
            ):
                result = execute_export(plan)

            output = probe_media(result)
            self.assertEqual((output.width, output.height), (1920, 1080))
            self.assertAlmostEqual(output.duration_seconds, probe.duration_seconds, delta=0.15)
            self.assertEqual(source.read_bytes(), source_before)
            self.assertEqual(len(restoration_calls), 1)

    def test_mixed_export_resolved_policies_ignore_inactive_sources(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            first_path = root / "first.mp4"
            second_path = root / "second.mp4"
            first_path.write_bytes(b"first")
            second_path.write_bytes(b"second")
            first_metadata = {
                "source_id": "first",
                "duration_seconds": 2.0,
                "width": 1920,
                "height": 1080,
                "frame_rate": "30/1",
                "video_codec": "h264",
                "audio_codec": None,
                "format_name": "mp4",
            }
            second_metadata = {
                "source_id": "second",
                "duration_seconds": 2.0,
                "width": 640,
                "height": 360,
                "frame_rate": "15/1",
                "video_codec": "h264",
                "audio_codec": None,
                "format_name": "mp4",
            }
            timeline = SegmentTimeline.from_blocks(
                (
                    Segment.create(
                        0.0,
                        2.0,
                        source_id="first",
                        timeline_start_seconds=0.0,
                        timeline_end_seconds=2.0,
                    ),
                    Segment.create(
                        0.0,
                        2.0,
                        source_id="second",
                        timeline_start_seconds=2.0,
                        timeline_end_seconds=4.0,
                    ),
                ),
                duration_seconds=4.0,
                source_durations={"first": 2.0, "second": 2.0},
            )
            timeline.set_deleted(timeline.segments[1].segment_id, True)
            resolved_fps = resolve_frame_rate_policy(
                (first_metadata, second_metadata),
                choice="custom",
                custom_rate="30/1",
                enhancement_enabled=True,
                backend="ffmpeg-minterpolate",
            )
            resolved_upscale = resolve_upscale_policy(
                (first_metadata, second_metadata),
                policy=UpscalePolicy(enhancement_enabled=True),
            )
            probes = (
                MediaProbe(
                    path=first_path,
                    duration_seconds=2.0,
                    width=1920,
                    height=1080,
                    frame_rate="30/1",
                    video_codec="h264",
                    audio_codec=None,
                    format_name="mp4",
                ),
                MediaProbe(
                    path=second_path,
                    duration_seconds=2.0,
                    width=640,
                    height=360,
                    frame_rate="15/1",
                    video_codec="h264",
                    audio_codec=None,
                    format_name="mp4",
                ),
            )

            plan = plan_mixed_export(
                probes,
                timeline,
                root / "edited.mp4",
                source_ids=("first", "second"),
                frame_rate_policy=resolved_fps,
                upscale_policy=resolved_upscale,
            )
            raw_policy_plan = plan_mixed_export(
                probes,
                timeline,
                root / "edited.mp4",
                source_ids=("first", "second"),
                frame_rate_policy=resolved_fps.policy,
                upscale_policy=resolved_upscale.policy,
            )

            self.assertEqual(plan.source_ids, ("first",))
            self.assertEqual(plan.to_dict(), raw_policy_plan.to_dict())
            self.assertEqual(
                tuple(item.source_id for item in plan.rate_decisions),
                ("first",),
            )
            self.assertEqual(
                tuple(item.source_id for item in plan.upscale_decisions),
                ("first",),
            )
            self.assertFalse(plan.upscale_decisions[0].eligible)
            self.assertEqual(plan.route, "fallback")

    def test_mixed_enhanced_export_prepares_and_interpolates_each_timeline_segment(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            first_path = self.make_source(
                root,
                name="first.mp4",
                size="320x180",
                rate=10,
                frequency=440,
            )
            second_path = self.make_source(
                root,
                name="second.mp4",
                size="180x320",
                rate=20,
                frequency=880,
            )
            first = probe_media(first_path)
            second = probe_media(second_path)
            first_id = "first"
            second_id = "second"
            timeline = SegmentTimeline.from_blocks(
                (
                    Segment.create(
                        0.0,
                        0.5,
                        source_id=first_id,
                        timeline_start_seconds=0.0,
                        timeline_end_seconds=0.5,
                    ),
                    Segment.create(
                        0.0,
                        0.5,
                        source_id=second_id,
                        timeline_start_seconds=0.5,
                        timeline_end_seconds=1.0,
                    ),
                ),
                duration_seconds=1.0,
                source_durations={
                    first_id: first.duration_seconds,
                    second_id: second.duration_seconds,
                },
            )
            policy = FrameRatePolicy(
                choice="custom",
                custom_rate="20/1",
                target_rate="20/1",
                enhancement_enabled=True,
                backend="ffmpeg-minterpolate",
            )
            plan = plan_mixed_export(
                (first, second),
                timeline,
                root / "mixed-enhanced.mp4",
                source_ids=(first_id, second_id),
                audio_decisions={
                    first_id: {"status": "ready", "gain_db": 1.0},
                    second_id: {"status": "ready", "gain_db": -1.0},
                },
                frame_rate_policy=policy,
                upscale_policy=UpscalePolicy(enhancement_enabled=False),
            )
            progress = []

            result = execute_export(plan, progress_callback=progress.append)

            output = probe_media(result)
            self.assertEqual(output.frame_rate, "20/1")
            self.assertEqual((output.width, output.height), (1920, 1080))
            self.assertAlmostEqual(output.duration_seconds, 1.0, delta=0.15)
            self.assertEqual(output.audio_sample_rate, 48000)
            self.assertEqual(output.audio_channels, 2)
            self.assertTrue(
                any(item.stage.startswith("interpolation segment ") for item in progress)
            )
            self.assertFalse(any(item.stage == "interpolation master" for item in progress))
            self.assertEqual(
                sum(item.stage == "concatenating enhanced segments" for item in progress), 1
            )
            self.assertTrue(
                all(
                    following.percent + 1e-6 >= current.percent
                    for current, following in zip(progress, progress[1:], strict=False)
                )
            )

    def test_mixed_upscale_export_preserves_target_frame_rate_with_audio_padding(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            first_path = self.make_source(
                root,
                name="first.mp4",
                size="320x180",
                rate=24,
                frequency=440,
            )
            second_path = self.make_source(
                root,
                name="second.mp4",
                size="180x320",
                rate=30,
                frequency=880,
            )
            first = probe_media(first_path)
            second = probe_media(second_path)
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
                        0.0,
                        1.0,
                        source_id=second_id,
                        timeline_start_seconds=1.0,
                        timeline_end_seconds=2.0,
                    ),
                ),
                duration_seconds=2.0,
                source_durations={
                    first_id: first.duration_seconds,
                    second_id: second.duration_seconds,
                },
            )
            frame_rate_policy = FrameRatePolicy(
                choice="60",
                target_rate="60/1",
                enhancement_enabled=False,
            )
            plan = plan_mixed_export(
                (first, second),
                timeline,
                root / "mixed-upscaled.mp4",
                source_ids=(first_id, second_id),
                audio_decisions={
                    first_id: {"status": "ready", "gain_db": 0.0},
                    second_id: {"status": "ready", "gain_db": 0.0},
                },
                frame_rate_policy=frame_rate_policy,
                upscale_policy=UpscalePolicy(enhancement_enabled=True),
            )

            def fake_restore(restoration_probe, output, **_kwargs):
                shutil.copyfile(restoration_probe.path, output)
                return probe_media(output)

            with patch(
                "framestudio.export_smart_render._run_source_restoration",
                side_effect=fake_restore,
            ):
                result = execute_export(plan)

            output = probe_media(result)
            self.assertEqual(output.frame_rate, "60/1")
            self.assertAlmostEqual(output.duration_seconds, 2.0, delta=0.15)

    def test_mixed_upscale_export_restores_only_eligible_sources(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            eligible_path = self.make_source(
                root,
                name="eligible.mp4",
                size="320x180",
                rate=30,
                frequency=440,
            )
            ineligible_path = self.make_source(
                root,
                name="ineligible.mp4",
                size="1920x1080",
                rate=30,
                frequency=880,
            )
            eligible_before = eligible_path.read_bytes()
            ineligible_before = ineligible_path.read_bytes()
            eligible = probe_media(eligible_path)
            ineligible = probe_media(ineligible_path)
            eligible_id = "eligible"
            ineligible_id = "ineligible"
            timeline = SegmentTimeline.from_blocks(
                (
                    Segment.create(
                        0.0,
                        1.0,
                        source_id=eligible_id,
                        timeline_start_seconds=0.0,
                        timeline_end_seconds=1.0,
                    ),
                    Segment.create(
                        0.0,
                        1.0,
                        source_id=ineligible_id,
                        timeline_start_seconds=1.0,
                        timeline_end_seconds=2.0,
                    ),
                ),
                duration_seconds=2.0,
                source_durations={
                    eligible_id: eligible.duration_seconds,
                    ineligible_id: ineligible.duration_seconds,
                },
            )
            frame_rate_policy = FrameRatePolicy(
                choice="custom",
                custom_rate="30/1",
                target_rate="30/1",
                enhancement_enabled=False,
            )
            plan = plan_mixed_export(
                (eligible, ineligible),
                timeline,
                root / "mixed-upscale-selection.mp4",
                source_ids=(eligible_id, ineligible_id),
                frame_rate_policy=frame_rate_policy,
                upscale_policy=UpscalePolicy(enhancement_enabled=True),
            )
            restoration_calls = []

            def fake_restore(restoration_probe, output, **_kwargs):
                restoration_calls.append(restoration_probe.path)
                shutil.copyfile(restoration_probe.path, output)
                return probe_media(output)

            with patch(
                "framestudio.export_smart_render._run_source_restoration",
                side_effect=fake_restore,
            ):
                result = execute_export(plan)

            output = probe_media(result)
            self.assertEqual(
                [decision.source_id for decision in plan.upscale_decisions if decision.eligible],
                [eligible_id],
            )
            self.assertEqual(restoration_calls, [eligible_path])
            self.assertEqual((output.width, output.height), (1920, 1080))
            self.assertEqual(output.frame_rate, "30/1")
            self.assertAlmostEqual(output.duration_seconds, 2.0, delta=0.15)
            self.assertEqual(eligible_path.read_bytes(), eligible_before)
            self.assertEqual(ineligible_path.read_bytes(), ineligible_before)

    def test_video_only_assembly_stream_copies_audio_bearing_segments(self):
        from framestudio.export_interpolation import _execute_enhanced_clip_assembly
        from framestudio.export_types import OutputPolicy

        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            first_path = self.make_source(root, name="first.mp4", rate=10, frequency=440)
            second_path = self.make_source(root, name="second.mp4", rate=10, frequency=880)
            first_before = first_path.read_bytes()
            second_before = second_path.read_bytes()
            probes = (probe_media(first_path), probe_media(second_path))
            policy = OutputPolicy(
                width=64,
                height=64,
                scaling_mode="source-native",
                frame_rate="10/1",
                timebase="1/1000000",
                container="mp4",
                video_codec="libx264",
                audio_codec=None,
                pixel_format="yuv420p",
                audio_stream_present=False,
                requires_normalization=False,
                reason="video-only assembly",
            )
            temporary = root / "temporary"
            temporary.mkdir()
            partial = root / "output.partial.mp4"

            _execute_enhanced_clip_assembly(
                (first_path, second_path),
                probes,
                policy,
                partial,
                temporary,
                ffmpeg_path="ffmpeg",
                ffprobe_path="ffprobe",
                progress_callback=None,
                started=0.0,
                expected_duration_seconds=2.0,
                total_frames=20,
                cancel_event=None,
            )

            output = probe_media(partial)
            self.assertFalse(output.has_audio_stream)
            self.assertEqual(output.video_codec, "h264")
            self.assertEqual(output.frame_rate, "10/1")
            self.assertAlmostEqual(output.duration_seconds, 2.0, delta=0.15)
            self.assertEqual(first_path.read_bytes(), first_before)
            self.assertEqual(second_path.read_bytes(), second_before)

    def test_single_full_source_enhancement_does_not_reencode_after_interpolation(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = root / "source.mp4"
            source.write_bytes(b"source")
            probe = MediaProbe(
                path=source,
                duration_seconds=1.0,
                width=1920,
                height=1080,
                frame_rate="10/1",
                video_codec="h264",
                audio_codec="aac",
                format_name="mp4",
                audio_stream_present=True,
                audio_sample_rate=48000,
                audio_channels=2,
            )
            policy = FrameRatePolicy(
                choice="custom",
                custom_rate="20/1",
                target_rate="20/1",
                enhancement_enabled=True,
                backend="ffmpeg-minterpolate",
            )
            destination = root / "enhanced.mp4"
            plan = plan_export(
                probe,
                SegmentTimeline(1.0),
                destination,
                keyframe_timestamps=(),
                frame_rate_policy=policy,
                upscale_policy=UpscalePolicy(enhancement_enabled=False),
            )

            def fake_interpolate(
                _probe,
                *,
                destination,
                source_id,
                decision,
                ffprobe_path,
                ffmpeg_path,
                backend_kwargs,
                ranges,
                target_frames,
                cancel_event,
                progress_callback=None,
                progress_stage="interpolation",
                progress_started=None,
            ):
                destination.write_bytes(b"interpolated")
                return MediaProbe(
                    path=destination,
                    duration_seconds=1.0,
                    width=1920,
                    height=1080,
                    frame_rate="20/1",
                    video_codec="h264",
                    audio_codec="aac",
                    format_name="mp4",
                    audio_stream_present=True,
                    audio_sample_rate=48000,
                    audio_channels=2,
                )

            def fake_fallback(_plan, _probe, partial, _ffmpeg_path, **_kwargs):
                partial.write_bytes(b"fallback")

            def fake_verify(_plan, _source_probe, candidate, **_kwargs):
                self.assertTrue(candidate.is_file())
                return probe

            with (
                patch(
                    "framestudio.export_interpolation.prepare_export_sources",
                    return_value=((source.stat(),), (probe,)),
                ),
                patch(
                    "framestudio.export_interpolation._interpolate_probe",
                    side_effect=fake_interpolate,
                ),
                patch(
                    "framestudio.export_interpolation.execute_fallback",
                    side_effect=fake_fallback,
                ) as fallback,
            ):
                result = execute_enhanced_export(
                    plan,
                    ffmpeg_path="ffmpeg",
                    ffprobe_path="ffprobe",
                    progress_callback=None,
                    verify_single_output=fake_verify,
                    verify_mixed_output=lambda *_args, **_kwargs: probe,
                )

            self.assertEqual(result, destination)
            self.assertEqual(destination.read_bytes(), b"interpolated")
            fallback.assert_not_called()

    def test_single_full_source_enhancement_publishes_real_interpolation_output(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = self.make_source(root, size="1920x1080", audio_channels=2)
            probe = probe_media(source)
            policy = FrameRatePolicy(
                choice="custom",
                custom_rate="20/1",
                target_rate="20/1",
                enhancement_enabled=True,
                backend="ffmpeg-minterpolate",
            )
            destination = root / "enhanced-direct.mp4"
            plan = plan_export(
                probe,
                SegmentTimeline(probe.duration_seconds),
                destination,
                keyframe_timestamps=(),
                frame_rate_policy=policy,
            )

            with patch(
                "framestudio.export_interpolation.execute_fallback",
                side_effect=AssertionError("direct interpolation must not reencode"),
            ):
                result = execute_export(plan)

            output = probe_media(result)
            self.assertEqual(output.frame_rate, "20/1")
            self.assertAlmostEqual(output.duration_seconds, probe.duration_seconds, delta=0.15)
            self.assertEqual((output.width, output.height), (1920, 1080))
            self.assertIsNotNone(output.audio_codec)

    def test_failed_enhanced_export_reuses_interpolation_cache_on_retry(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = self.make_source(root, size="64x64", rate=10)
            source_probe = probe_media(source)
            destination = root / "retry.mp4"
            frame_policy = FrameRatePolicy(
                choice="custom",
                custom_rate="20/1",
                target_rate="20/1",
                enhancement_enabled=True,
                backend="ffmpeg-minterpolate",
            )
            plan = plan_export(
                source_probe,
                SegmentTimeline(source_probe.duration_seconds),
                destination,
                keyframe_timestamps=(),
                frame_rate_policy=frame_policy,
                upscale_policy=UpscalePolicy(enhancement_enabled=False),
            )
            prepared = PreparedSource(
                source_id="source",
                segment_index=0,
                path=source,
                probe=source_probe,
                source_rate=Fraction(10, 1),
            )
            interpolated_probe = MediaProbe(
                path=destination,
                duration_seconds=source_probe.duration_seconds,
                width=source_probe.width,
                height=source_probe.height,
                frame_rate="20/1",
                video_codec="h264",
                audio_codec="aac",
                format_name="mp4",
                audio_stream_present=True,
                audio_sample_rate=48000,
                audio_channels=2,
            )
            interpolation_calls = []
            verification_calls = 0

            def fake_interpolate(_probe, *, destination, **_kwargs):
                destination.write_bytes(b"interpolated")
                interpolation_calls.append(destination)
                return replace(interpolated_probe, path=destination)

            def verify(_plan, _source_probe, candidate, **_kwargs):
                nonlocal verification_calls
                verification_calls += 1
                self.assertTrue(candidate.is_file())
                if verification_calls == 1:
                    raise ExportExecutionError("verification failure")
                return interpolated_probe

            def probe_cached(path, _ffprobe_path="ffprobe"):
                return replace(interpolated_probe, path=path)

            with (
                patch(
                    "framestudio.export_interpolation.prepare_export_sources",
                    return_value=((source.stat(),), (source_probe,)),
                ),
                patch(
                    "framestudio.export_interpolation.prepare_enhanced_sources",
                    return_value=(prepared,),
                ),
                patch(
                    "framestudio.export_interpolation._interpolate_probe",
                    side_effect=fake_interpolate,
                ) as interpolate,
                patch(
                    "framestudio.export_interpolation.probe_media",
                    side_effect=probe_cached,
                ),
                patch(
                    "framestudio.export_interpolation.probe_frame_count",
                    return_value=20,
                ),
                patch("framestudio.export_interpolation.run_artifact_gate"),
            ):
                with self.assertRaises(ExportExecutionError):
                    execute_enhanced_export(
                        plan,
                        ffmpeg_path="ffmpeg",
                        ffprobe_path="ffprobe",
                        progress_callback=None,
                        verify_single_output=verify,
                        verify_mixed_output=lambda *_args, **_kwargs: interpolated_probe,
                    )

                cache_directory = (
                    destination.parent / f".{destination.name}.framestudio-intermediates"
                )
                self.assertTrue(cache_directory.is_dir())
                self.assertEqual(interpolate.call_count, 1)

                result = execute_enhanced_export(
                    plan,
                    ffmpeg_path="ffmpeg",
                    ffprobe_path="ffprobe",
                    progress_callback=None,
                    verify_single_output=verify,
                    verify_mixed_output=lambda *_args, **_kwargs: interpolated_probe,
                )

            self.assertEqual(result, destination)
            self.assertEqual(interpolate.call_count, 1)
            self.assertFalse(cache_directory.exists())

    def test_published_export_succeeds_when_cache_cleanup_fails(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = root / "source.mp4"
            source.write_bytes(b"source")
            source_probe = MediaProbe(
                path=source,
                duration_seconds=1.0,
                width=64,
                height=64,
                frame_rate="10/1",
                video_codec="h264",
                audio_codec="aac",
                format_name="mp4",
                audio_stream_present=True,
                audio_sample_rate=48000,
                audio_channels=2,
            )
            destination = root / "published.mp4"
            plan = plan_export(
                source_probe,
                SegmentTimeline(1.0),
                destination,
                keyframe_timestamps=(),
                frame_rate_policy=FrameRatePolicy(
                    choice="custom",
                    custom_rate="20/1",
                    target_rate="20/1",
                    enhancement_enabled=True,
                    backend="rve-4.26",
                ),
                upscale_policy=UpscalePolicy(enhancement_enabled=False),
            )

            def fake_render(_plan, _probes, _decisions, *, partial, **_kwargs):
                partial.write_bytes(b"published")

            def fake_publish(partial, destination, *_args, **_kwargs):
                shutil.copyfile(partial, destination)

            def verify(_plan, _source_probe, candidate, **_kwargs):
                self.assertTrue(candidate.is_file())
                return source_probe

            with (
                patch(
                    "framestudio.export_interpolation.prepare_export_sources",
                    return_value=((source.stat(),), (source_probe,)),
                ),
                patch(
                    "framestudio.export_interpolation._execute_per_source_enhanced_render",
                    side_effect=fake_render,
                ),
                patch(
                    "framestudio.export_interpolation.publish_verified_export",
                    side_effect=fake_publish,
                ),
                patch(
                    "framestudio.export_interpolation.ExportCache.discard_after_success",
                    side_effect=ExportCacheError("cache cleanup failed"),
                ),
            ):
                with self.assertWarnsRegex(RuntimeWarning, "cache cleanup failed"):
                    result = execute_enhanced_export(
                        plan,
                        ffmpeg_path="ffmpeg",
                        ffprobe_path="ffprobe",
                        progress_callback=None,
                        verify_single_output=verify,
                        verify_mixed_output=lambda *_args, **_kwargs: source_probe,
                    )

            self.assertEqual(result, destination)
            self.assertEqual(destination.read_bytes(), b"published")
            manifest = json.loads(
                (
                    destination.parent
                    / f".{destination.name}.framestudio-intermediates"
                    / "manifest.json"
                ).read_text(encoding="utf-8")
            )
            self.assertIn(
                "interpolation.rve_model",
                manifest["request"]["runtime_paths"],
            )

    def test_interpolation_does_not_blend_across_deleted_edit_boundary(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = self.make_boundary_source(root)
            probe = probe_media(source)
            timeline = SegmentTimeline(probe.duration_seconds)
            timeline.split(0.5)
            timeline.delete_segment(timeline.segments[1].segment_id)
            policy = FrameRatePolicy(
                choice="custom",
                custom_rate="20/1",
                target_rate="20/1",
                enhancement_enabled=True,
                backend="ffmpeg-minterpolate",
            )
            plan = plan_export(
                probe,
                timeline,
                root / "boundary-safe.mp4",
                keyframe_timestamps=(),
                frame_rate_policy=policy,
            )
            progress = []

            execute_export(plan, progress_callback=progress.append)

            sample = subprocess.check_output(
                [
                    "ffmpeg",
                    "-hide_banner",
                    "-loglevel",
                    "error",
                    "-i",
                    str(root / "boundary-safe.mp4"),
                    "-vf",
                    r"select=eq(n\,9),crop=2:2:960:540,scale=1:1,format=rgb24",
                    "-frames:v",
                    "1",
                    "-f",
                    "rawvideo",
                    "-pix_fmt",
                    "rgb24",
                    "-",
                ],
            )

        self.assertEqual(tuple(sample[:3]), (100, 100, 100))
        interpolation_progress = [
            item for item in progress if item.stage.startswith("interpolation")
        ]
        self.assertTrue(any(item.frame > 0 for item in interpolation_progress))

    def test_stream_copy_export_is_verified(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = self.make_source(root, size="1920x1080")
            probe = probe_media(source)
            timeline = SegmentTimeline(probe.duration_seconds)
            destination = root / "copied.mp4"
            plan = plan_export(
                probe,
                timeline,
                destination,
                keyframe_timestamps=(),
            )

            self.assertEqual(plan.route, "stream-copy")
            result = execute_export(plan)

            self.assertEqual(result, destination)
            output = probe_media(destination)
            self.assertAlmostEqual(
                output.duration_seconds,
                probe.duration_seconds,
                delta=0.15,
            )

    def test_cancelled_stream_copy_reuses_completed_cuts_after_resume(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = self.make_source(root, duration=3.0, gop=1)
            source_before = source.read_bytes()
            segments = (
                Segment.create(0.0, 1.0),
                Segment.create(1.0, 2.0),
                Segment.create(2.0, 3.0),
            )
            destination = root / "resumable.mp4"
            plan = ExportPlan(
                route="stream-copy",
                source=source,
                destination=destination,
                segments=segments,
                expected_duration_seconds=3.0,
                reason="generated-media resume coverage",
            )
            cancel_event = threading.Event()
            first_attempt_calls = 0
            original_run_ffmpeg = export_ffmpeg.run_ffmpeg

            def cancel_after_first_cut(command, **kwargs):
                nonlocal first_attempt_calls
                first_attempt_calls += 1
                result = original_run_ffmpeg(command, **kwargs)
                if first_attempt_calls == 1:
                    cancel_event.set()
                return result

            with patch(
                "framestudio.export_ffmpeg.run_ffmpeg",
                side_effect=cancel_after_first_cut,
            ):
                with self.assertRaisesRegex(ExportExecutionError, "cancelled"):
                    execute_export(plan, cancel_event=cancel_event)

            session_info = discover_export_session(destination)
            self.assertTrue(session_info.exists)
            self.assertEqual(session_info.state, "cancelled")
            self.assertEqual(session_info.last_completed_stage, "cut-0")
            manifest = json.loads((session_info.root / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["stages"]["cut-0"]["status"], "complete")
            self.assertNotEqual(manifest["stages"]["cut-1"]["status"], "complete")
            self.assertFalse(destination.exists())

            resumed_calls = 0

            def count_resumed_ffmpeg(command, **kwargs):
                nonlocal resumed_calls
                resumed_calls += 1
                return original_run_ffmpeg(command, **kwargs)

            progress = []
            with patch(
                "framestudio.export_ffmpeg.run_ffmpeg",
                side_effect=count_resumed_ffmpeg,
            ):
                result = execute_export(
                    plan,
                    progress_callback=progress.append,
                    resume_mode="resume",
                )

            self.assertEqual(result, destination)
            self.assertEqual(resumed_calls, 3)
            self.assertFalse(
                any(item.stage == "cut 1/3" for item in progress),
            )
            self.assertEqual(source.read_bytes(), source_before)
            output = probe_media(destination)
            self.assertAlmostEqual(output.duration_seconds, 3.0, delta=0.2)
            self.assertFalse(discover_export_session(destination).exists)

    def test_export_reports_progress_metrics(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = self.make_source(root)
            probe = probe_media(source)
            timeline = SegmentTimeline(probe.duration_seconds)
            destination = root / "progress.mp4"
            plan = plan_export(
                probe,
                timeline,
                destination,
                keyframe_timestamps=(),
            )
            progress = []

            execute_export(plan, progress_callback=progress.append)

            self.assertTrue(progress)
            self.assertEqual(progress[0].stage, "starting")
            self.assertEqual(progress[-1].stage, "complete")
            self.assertEqual(progress[-1].percent, 100.0)
            self.assertGreater(progress[-1].total_frames, 0)
            self.assertTrue(any(item.fps is not None for item in progress))
            self.assertTrue(any(item.stage == "verifying" for item in progress))

    def test_cancelled_enhanced_export_reuses_completed_interpolation_after_resume(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = self.make_source(root, duration=2.0, gop=1)
            source_before = source.read_bytes()
            probe = probe_media(source)
            timeline = SegmentTimeline(probe.duration_seconds)
            timeline.split(1.0)
            destination = root / "enhanced-resumable.mp4"
            frame_policy = FrameRatePolicy(
                choice="custom",
                custom_rate="20/1",
                target_rate="20/1",
                enhancement_enabled=True,
                backend="ffmpeg-minterpolate",
            )
            plan = plan_export(
                probe,
                timeline,
                destination,
                keyframe_timestamps=(),
                frame_rate_policy=frame_policy,
                upscale_policy=UpscalePolicy(enhancement_enabled=False),
            )
            self.assertEqual(plan.route, "enhanced")
            cancel_event = threading.Event()
            first_attempt_calls = 0
            original_interpolate = export_interpolation._interpolate_probe

            def cancel_after_first_interpolation(*args, **kwargs):
                nonlocal first_attempt_calls
                first_attempt_calls += 1
                result = original_interpolate(*args, **kwargs)
                if first_attempt_calls == 1:
                    cancel_event.set()
                return result

            with patch(
                "framestudio.export_interpolation._interpolate_probe",
                side_effect=cancel_after_first_interpolation,
            ):
                with self.assertRaisesRegex(ExportExecutionError, "cancelled"):
                    execute_export(plan, cancel_event=cancel_event)

            session_info = discover_export_session(destination)
            self.assertTrue(session_info.exists)
            self.assertEqual(session_info.state, "cancelled")
            cache_root = destination.parent / f".{destination.name}.framestudio-intermediates"
            cache_manifest = json.loads((cache_root / "manifest.json").read_text(encoding="utf-8"))
            self.assertIn("enhanced-segment-0", cache_manifest["artifacts"])
            self.assertNotIn("enhanced-segment-1", cache_manifest["artifacts"])
            self.assertFalse(destination.exists())

            resumed_calls = 0

            def count_resumed_interpolation(*args, **kwargs):
                nonlocal resumed_calls
                resumed_calls += 1
                return original_interpolate(*args, **kwargs)

            with patch(
                "framestudio.export_interpolation._interpolate_probe",
                side_effect=count_resumed_interpolation,
            ):
                result = execute_export(plan, resume_mode="resume")

            self.assertEqual(result, destination)
            self.assertEqual(resumed_calls, 1)
            self.assertEqual(source.read_bytes(), source_before)
            output = probe_media(destination)
            self.assertEqual(output.frame_rate, "20/1")
            self.assertAlmostEqual(output.duration_seconds, 2.0, delta=0.2)
            self.assertFalse(discover_export_session(destination).exists)
            self.assertFalse(cache_root.exists())

    def test_failed_export_keeps_existing_destination_and_cleans_partial(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = self.make_source(root)
            probe = probe_media(source)
            timeline = SegmentTimeline(probe.duration_seconds)
            timeline.split(0.5)
            destination = root / "edited.mp4"
            destination.write_bytes(b"last valid output")
            plan = plan_export(
                probe,
                timeline,
                destination,
                keyframe_timestamps=(),
            )

            with self.assertRaises(ExportExecutionError):
                execute_export(plan, ffmpeg_path="/missing/ffmpeg")

            self.assertEqual(
                destination.read_bytes(),
                b"last valid output",
            )
            self.assertEqual(
                list(root.glob(".edited.mp4.partial-*")),
                [],
            )

    def test_cancelled_export_does_not_publish_or_modify_existing_output(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = self.make_source(root)
            probe = probe_media(source)
            timeline = SegmentTimeline(probe.duration_seconds)
            destination = root / "edited.mp4"
            destination.write_bytes(b"last valid output")
            plan = plan_export(
                probe,
                timeline,
                destination,
                keyframe_timestamps=(),
            )
            cancel_event = threading.Event()
            cancel_event.set()

            with self.assertRaisesRegex(ExportExecutionError, "cancelled"):
                execute_export(plan, cancel_event=cancel_event)

            self.assertEqual(destination.read_bytes(), b"last valid output")
            self.assertEqual(
                list(root.glob(".edited.mp4.partial-*")),
                [],
            )

    def test_ffmpeg_cancellation_uses_bounded_process_termination(self):
        cancel_event = threading.Event()

        class Output:
            def __iter__(self):
                cancel_event.set()
                yield "progress=continue\n"

            def close(self):
                return None

        class Process:
            def __init__(self):
                self.stdout = Output()
                self.returncode = -15
                self.terminated = False
                self.killed = False

            def poll(self):
                return None if not self.killed else self.returncode

            def terminate(self):
                self.terminated = True

            def kill(self):
                self.killed = True

            def wait(self, timeout=None):
                if timeout is None and not self.killed:
                    raise AssertionError("process termination must be bounded")
                if timeout is not None and not self.killed:
                    raise subprocess.TimeoutExpired("ffmpeg", timeout)
                return self.returncode

        process = Process()
        with patch(
            "framestudio.export_process.subprocess.Popen",
            return_value=process,
        ):
            with self.assertRaisesRegex(ExportExecutionError, "cancelled"):
                run_ffmpeg(
                    ["ffmpeg", "-i", "source.mp4", "output.mp4"],
                    progress_callback=lambda _progress: None,
                    cancel_event=cancel_event,
                )

        self.assertTrue(process.terminated)
        self.assertTrue(process.killed)

    def test_publication_lock_rejects_cancellation_before_replacing_destination(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = root / "source.mp4"
            partial = root / "partial.mp4"
            destination = root / "destination.mp4"
            source.write_bytes(b"source")
            partial.write_bytes(b"partial")
            destination.write_bytes(b"previous")
            cancel_event = threading.Event()
            publication_lock = threading.Lock()
            publication_lock.acquire()
            errors = []
            completed = threading.Event()

            def publish():
                try:
                    publish_verified_export(
                        partial,
                        destination,
                        (source,),
                        (source.stat(),),
                        cancel_event=cancel_event,
                        cancellation_lock=publication_lock,
                        progress_callback=None,
                        expected_duration_seconds=1.0,
                        total_frames=10,
                        started=0.0,
                    )
                except Exception as error:
                    errors.append(error)
                finally:
                    completed.set()

            thread = threading.Thread(target=publish)
            thread.start()
            self.assertFalse(completed.wait(timeout=0.05))
            cancel_event.set()
            publication_lock.release()
            self.assertTrue(completed.wait(timeout=1.0))
            thread.join(timeout=1.0)

            self.assertIsInstance(errors[0], ExportExecutionError)
            self.assertEqual(destination.read_bytes(), b"previous")
            self.assertTrue(partial.is_file())


if __name__ == "__main__":
    unittest.main()
