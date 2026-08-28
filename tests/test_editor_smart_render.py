import unittest
from dataclasses import replace
from fractions import Fraction
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from framestudio.export_smart_render import (
    PreparedSource,
    build_concat_copy_command,
    build_lossless_cut_command,
    build_source_normalization_command,
)
from framestudio.export_types import OutputPolicy
from framestudio.fps_policy import FrameRatePolicy
from framestudio.media import MediaProbe
from framestudio.model import Segment


def make_probe(
    path: Path,
    *,
    frame_rate: str = "30/1",
    duration: float = 2.0,
    width: int = 1920,
    height: int = 1080,
) -> MediaProbe:
    return MediaProbe(
        path=path,
        duration_seconds=duration,
        width=width,
        height=height,
        frame_rate=frame_rate,
        video_codec="h264",
        audio_codec="aac",
        format_name="mp4",
        audio_stream_present=True,
        audio_sample_rate=48000,
        audio_channels=2,
        audio_channel_layout="stereo",
    )


class EditorSmartRenderCommandTests(unittest.TestCase):
    def test_lossless_cut_command_uses_stream_copy_without_video_filters(self):
        command = build_lossless_cut_command(
            Path("source.mp4"),
            Path("cut.mp4"),
            start_seconds=1.5,
            duration_seconds=2.5,
            has_audio=True,
            ffmpeg_path="ffmpeg",
        )

        self.assertIn("-ss", command)
        self.assertEqual(command[command.index("-ss") + 1], "1.500000")
        self.assertEqual(command[command.index("-t") + 1], "2.500000")
        self.assertEqual(command[command.index("-c") + 1], "copy")
        self.assertNotIn("-vf", command)
        self.assertNotIn("-filter_complex", command)

    def test_source_normalization_applies_audio_gain_once_before_concat(self):
        policy = OutputPolicy(
            width=1920,
            height=1080,
            scaling_mode="contain-letterbox",
            frame_rate="60/1",
            timebase="1/1000000",
            container="mp4",
            video_codec="libx264",
            audio_codec="aac",
            pixel_format="yuv420p",
            audio_stream_present=True,
            requires_normalization=True,
            reason="test",
        )
        segments = (
            Segment.create(0.0, 1.0),
            Segment.create(1.0, 2.0),
        )

        command = build_source_normalization_command(
            Path("source.mp4"),
            Path("prepared.mp4"),
            segments,
            target_rate=Fraction(30, 1),
            policy=policy,
            audio_decision={"status": "ready", "gain_db": 3.0},
            has_audio=True,
            ffmpeg_path="ffmpeg",
        )

        filter_graph = command[command.index("-filter_complex") + 1]
        self.assertEqual(filter_graph.count("volume=3.00dB"), 1)
        self.assertIn("concat=n=2:v=1:a=1", filter_graph)
        self.assertIn("fps=30/1", filter_graph)
        self.assertIn("atrim=start=1.000000:duration=1.000000", filter_graph)
        self.assertEqual(command[command.index("-c:v") + 1], "libx264")
        self.assertEqual(command[command.index("-c:a") + 1], "aac")

    def test_source_normalization_allocates_segment_frames_cumulatively(self):
        policy = OutputPolicy(
            width=1920,
            height=1080,
            scaling_mode="contain-letterbox",
            frame_rate="60/1",
            timebase="1/1000000",
            container="mp4",
            video_codec="libx264",
            audio_codec="aac",
            pixel_format="yuv420p",
            audio_stream_present=True,
            requires_normalization=True,
            reason="test",
        )
        segments = (
            Segment.create(0.0, 2.1484375),
            Segment.create(2.1484375, 3.02180733267717),
        )

        command = build_source_normalization_command(
            Path("source.mp4"),
            Path("prepared.mp4"),
            segments,
            target_rate=Fraction(30, 1),
            policy=policy,
            audio_decision={"status": "ready", "gain_db": 0.0},
            has_audio=True,
            ffmpeg_path="ffmpeg",
        )

        filter_graph = command[command.index("-filter_complex") + 1]
        self.assertIn("trim=end_frame=64", filter_graph)
        self.assertIn("trim=end_frame=27", filter_graph)

    def test_concat_command_uses_fast_concat_demuxer_and_stream_copy(self):
        command = build_concat_copy_command(
            Path("concat-list.txt"),
            Path("master.mp4"),
            has_audio=True,
            ffmpeg_path="ffmpeg",
        )

        self.assertEqual(command[command.index("-f") + 1], "concat")
        self.assertIn("-safe", command)
        self.assertEqual(command[command.index("-safe") + 1], "0")
        self.assertEqual(command[command.index("-c") + 1], "copy")


class EditorSmartRenderPipelineTests(unittest.TestCase):
    def test_video_only_assembly_strips_discarded_audio_before_stream_copy(self):
        from framestudio.export_interpolation import _execute_enhanced_clip_assembly

        policy = OutputPolicy(
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
            reason="video-only output",
        )
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            paths = (root / "first.mp4", root / "second.mp4")
            for path in paths:
                path.write_bytes(b"source")
            probes = tuple(make_probe(path, frame_rate="20/1", duration=0.5) for path in paths)
            video_only_probe = MediaProbe(
                path=root / "video-only.mp4",
                duration_seconds=0.5,
                width=1920,
                height=1080,
                frame_rate="20/1",
                video_codec="h264",
                audio_codec=None,
                format_name="mp4",
                audio_stream_present=False,
            )
            joined_probe = replace(video_only_probe, duration_seconds=1.0)
            commands = []
            temporary = root / "temporary"
            temporary.mkdir()

            def fake_run_ffmpeg(command, **_kwargs):
                commands.append(command)
                Path(command[-1]).write_bytes(b"output")

            with (
                patch(
                    "framestudio.export_interpolation.run_ffmpeg",
                    side_effect=fake_run_ffmpeg,
                ),
                patch(
                    "framestudio.export_interpolation.probe_media",
                    side_effect=(video_only_probe, video_only_probe, joined_probe),
                ),
                patch(
                    "framestudio.export_interpolation.probe_frame_count",
                    return_value=20,
                ),
                patch(
                    "framestudio.export_interpolation._execute_clip_concat_fallback",
                ) as fallback,
            ):
                _execute_enhanced_clip_assembly(
                    paths,
                    probes,
                    policy,
                    root / "output.mp4",
                    temporary,
                    ffmpeg_path="ffmpeg",
                    ffprobe_path="ffprobe",
                    progress_callback=None,
                    started=0.0,
                    expected_duration_seconds=1.0,
                    total_frames=20,
                    cancel_event=None,
                )

            self.assertEqual(len(commands), 3)
            self.assertTrue(all("-an" in command for command in commands[:2]))
            self.assertEqual(commands[0][commands[0].index("-c:v") + 1], "copy")
            self.assertEqual(commands[0][commands[0].index("-map") + 1], "0:v:0")
            self.assertEqual(commands[-1][commands[-1].index("-f") + 1], "concat")
            fallback.assert_not_called()

    def test_video_only_preparation_requests_audio_free_lossless_cuts(self):
        from framestudio.export_smart_render import prepare_enhanced_sources
        from framestudio.export_types import ExportPlan
        from framestudio.fps_policy import SourceRateDecision

        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = root / "source.mp4"
            source.write_bytes(b"source")
            cut = root / "cut.mp4"
            source_probe = make_probe(source, frame_rate="20/1", duration=1.0)
            cut_probe = make_probe(cut, frame_rate="20/1", duration=0.5)
            cut_probe = replace(
                cut_probe,
                audio_codec=None,
                audio_stream_present=False,
                audio_sample_rate=None,
                audio_channels=None,
                audio_channel_layout=None,
            )
            plan = ExportPlan(
                route="enhanced",
                source=source,
                destination=root / "output.mp4",
                segments=(Segment.create(0.0, 0.5),),
                expected_duration_seconds=0.5,
                reason="video-only output",
                output_policy=OutputPolicy(
                    width=1920,
                    height=1080,
                    scaling_mode="source-native",
                    frame_rate="20/1",
                    timebase="1/1000000",
                    container="mp4",
                    video_codec="libx264",
                    audio_codec=None,
                    pixel_format="yuv420p",
                    audio_stream_present=False,
                    requires_normalization=False,
                    reason="video-only output",
                ),
            )
            captured_audio_setting = []

            def fake_lossless_selection(*_args, include_audio, **_kwargs):
                captured_audio_setting.append(include_audio)
                return cut_probe

            with (
                patch(
                    "framestudio.export_smart_render._can_losslessly_select",
                    return_value=True,
                ),
                patch(
                    "framestudio.export_smart_render._execute_lossless_selection",
                    side_effect=fake_lossless_selection,
                ),
            ):
                prepared = prepare_enhanced_sources(
                    plan,
                    (source_probe,),
                    {
                        "source": SourceRateDecision(
                            source_id="source",
                            source_rate=Fraction(20, 1),
                            target_rate=Fraction(20, 1),
                            action="passthrough",
                            eligible=False,
                            reason="already at target",
                        )
                    },
                    root / "temporary",
                    ffmpeg_path="ffmpeg",
                    ffprobe_path="ffprobe",
                    progress_callback=None,
                    started=0.0,
                    cancel_event=None,
                )

            self.assertEqual(captured_audio_setting, [False])
            self.assertEqual(prepared[0].probe.audio_codec, None)

    def test_enhanced_export_does_not_select_concat_first_strategy(self):
        from framestudio.export_interpolation import _should_use_concat_first
        from framestudio.export_types import ExportPlan

        source = Path("portrait.mp4")
        plan = ExportPlan(
            route="enhanced",
            source=source,
            destination=Path("enhanced.mp4"),
            segments=(Segment.create(0.0, 2.0),),
            expected_duration_seconds=2.0,
            reason="source dimensions require normalization",
            output_policy=OutputPolicy(
                width=1920,
                height=1080,
                scaling_mode="contain-letterbox",
                frame_rate="60/1",
                timebase="1/1000000",
                container="mp4",
                video_codec="libx264",
                audio_codec="aac",
                pixel_format="yuv420p",
                audio_stream_present=True,
                requires_normalization=True,
                reason="test",
            ),
            frame_rate_policy=FrameRatePolicy(
                choice="60",
                target_rate="60/1",
                enhancement_enabled=True,
                backend="ffmpeg-minterpolate",
            ),
            rate_decisions=(
                {
                    "source_id": "source",
                    "source_rate": "30/1",
                    "target_rate": "60/1",
                    "action": "interpolate",
                    "eligible": True,
                    "reason": "test",
                },
            ),
        )

        self.assertFalse(
            _should_use_concat_first(
                plan,
                make_probe(source, frame_rate="30/1", width=1080, height=1920),
            )
        )

    def test_enhanced_mixed_export_enhances_each_prepared_segment_then_concats(self):
        from framestudio.export_interpolation import execute_enhanced_export
        from framestudio.export_types import ExportPlan

        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            first_path = root / "first.mp4"
            second_path = root / "second.mp4"
            first_path.write_bytes(b"first")
            second_path.write_bytes(b"second")
            destination = root / "enhanced.mp4"
            first = make_probe(
                first_path,
                frame_rate="30/1",
                duration=6.17864173228346,
            )
            second = make_probe(second_path, frame_rate="60/1", duration=5.0)
            prepared_paths = tuple(root / f"prepared-{index}.mp4" for index in range(5))
            prepared_probes = tuple(
                make_probe(
                    path,
                    frame_rate="30/1" if index < 2 else "60/1",
                    duration=(
                        3.970072588582675
                        if index == 0
                        else 2.208569143700136
                        if index == 1
                        else 0.5
                    ),
                )
                for index, path in enumerate(prepared_paths)
            )
            output_probe = make_probe(
                destination,
                frame_rate="60/1",
                duration=11.17864173228346,
            )
            plan = ExportPlan(
                route="enhanced",
                source=first_path,
                destination=destination,
                segments=(
                    Segment.create(
                        0.0,
                        3.970072588582675,
                        source_id="first",
                        timeline_start_seconds=0.0,
                        timeline_end_seconds=3.970072588582675,
                    ),
                    Segment.create(
                        3.970072588582675,
                        6.17864173228346,
                        source_id="first",
                        timeline_start_seconds=3.970072588582675,
                        timeline_end_seconds=6.17864173228346,
                    ),
                    Segment.create(
                        0.0,
                        2.1484375,
                        source_id="second",
                        timeline_start_seconds=6.17864173228346,
                        timeline_end_seconds=8.327079232283467,
                    ),
                    Segment.create(
                        2.1484375,
                        3.02180733267717,
                        source_id="second",
                        timeline_start_seconds=8.327079232283467,
                        timeline_end_seconds=9.20044906496063,
                    ),
                    Segment.create(
                        3.02180733267717,
                        5.0,
                        source_id="second",
                        timeline_start_seconds=9.20044906496063,
                        timeline_end_seconds=11.17864173228346,
                    ),
                ),
                expected_duration_seconds=11.17864173228346,
                reason="enhancement",
                source_paths=(first_path, second_path),
                source_ids=("first", "second"),
                output_policy=OutputPolicy(
                    width=1920,
                    height=1080,
                    scaling_mode="contain-letterbox",
                    frame_rate="60/1",
                    timebase="1/1000000",
                    container="mp4",
                    video_codec="libx264",
                    audio_codec="aac",
                    pixel_format="yuv420p",
                    audio_stream_present=True,
                    requires_normalization=True,
                    reason="test",
                ),
                audio_decisions=(
                    ("first", {"status": "ready", "gain_db": 2.0}),
                    ("second", {"status": "ready", "gain_db": -1.0}),
                ),
                frame_rate_policy=FrameRatePolicy(
                    choice="60",
                    target_rate="60/1",
                    enhancement_enabled=True,
                    backend="ffmpeg-minterpolate",
                ),
                rate_decisions=(
                    {
                        "source_id": "first",
                        "source_rate": "30/1",
                        "target_rate": "60/1",
                        "action": "interpolate",
                        "eligible": True,
                        "reason": "test",
                    },
                    {
                        "source_id": "second",
                        "source_rate": "60/1",
                        "target_rate": "60/1",
                        "action": "passthrough",
                        "eligible": False,
                        "reason": "test",
                    },
                ),
            )
            interpolation_inputs = []
            decisions = []
            requested_target_frames = []
            concat_commands = []

            def fake_interpolate(
                probe,
                *,
                decision,
                destination,
                target_frames,
                **_kwargs,
            ):
                interpolation_inputs.append(probe.path)
                decisions.append(decision)
                requested_target_frames.append(target_frames)
                destination.write_bytes(b"interpolated")
                return make_probe(
                    destination,
                    frame_rate="60/1",
                    duration=target_frames / 60,
                )

            def fake_verify_mixed(_plan, candidate, **_kwargs):
                self.assertTrue(candidate.is_file())
                return output_probe

            def fake_run_ffmpeg(command, **_kwargs):
                concat_commands.append(command)
                Path(command[-1]).write_bytes(b"concatenated")

            with (
                patch(
                    "framestudio.export_interpolation.prepare_export_sources",
                    return_value=(
                        (first_path.stat(), second_path.stat()),
                        (first, second),
                    ),
                ),
                patch(
                    "framestudio.export_interpolation.prepare_enhanced_sources",
                    return_value=tuple(
                        PreparedSource(
                            source_id="first" if index < 2 else "second",
                            segment_index=index,
                            path=path,
                            probe=probe,
                            source_rate=Fraction(probe.frame_rate),
                        )
                        for index, (path, probe) in enumerate(
                            zip(prepared_paths, prepared_probes, strict=True)
                        )
                    ),
                ) as prepare_sources,
                patch(
                    "framestudio.export_interpolation._interpolate_probe",
                    side_effect=fake_interpolate,
                ) as interpolate,
                patch("framestudio.export_interpolation.run_ffmpeg", side_effect=fake_run_ffmpeg),
                patch(
                    "framestudio.export_interpolation.probe_media",
                    return_value=output_probe,
                ),
                patch(
                    "framestudio.export_interpolation.probe_frame_count",
                    return_value=671,
                ),
            ):
                result = execute_enhanced_export(
                    plan,
                    ffmpeg_path="ffmpeg",
                    ffprobe_path="ffprobe",
                    progress_callback=None,
                    verify_single_output=lambda *_args, **_kwargs: output_probe,
                    verify_mixed_output=fake_verify_mixed,
                )

            self.assertEqual(result, destination)
            prepare_sources.assert_called_once()
            self.assertEqual(interpolate.call_count, 2)
            self.assertEqual(interpolation_inputs, list(prepared_paths[:2]))
            self.assertEqual(
                [(item.source_rate, item.target_rate) for item in decisions],
                [(Fraction(30, 1), Fraction(60, 1))] * 2,
            )
            self.assertEqual(sum(requested_target_frames), 371)
            self.assertEqual(len(concat_commands), 1)
            concat_command = concat_commands[0]
            self.assertEqual(concat_command[concat_command.index("-f") + 1], "concat")
            self.assertEqual(concat_command[concat_command.index("-c") + 1], "copy")


if __name__ == "__main__":
    unittest.main()
