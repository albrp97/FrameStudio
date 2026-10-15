from __future__ import annotations

import subprocess
import threading
from contextlib import contextmanager
from dataclasses import replace
from fractions import Fraction
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from framestudio.export_types import ExportExecutionError
from framestudio.fps_policy import DEFAULT_FPS_FALLBACK_BACKEND
from framestudio.layout_plan import SourceGeometry
from framestudio.media import MediaProbe
from framestudio.model import Project, Segment
from framestudio.video_compositor import (
    VideoCompositorExecutionError,
    VideoCompositorPlanningError,
    VideoRenderPlan,
    VideoSourceProbe,
    _asset_stem,
    _prepare_assets,
    _probe_source,
    _sha256,
    _verify_rendered_output,
    cumulative_frame_boundaries,
    plan_project_video,
    render_project_video,
)


class VideoCompositorUnitTests(TestCase):
    def test_planning_hash_cache_is_batch_local_and_invalidates_changed_files(self):
        import threading

        with TemporaryDirectory() as temporary:
            path = Path(temporary) / "source.bin"
            path.write_bytes(b"first")
            cache = {}
            original = _sha256(path, source_hash_cache=cache)
            with patch.object(Path, "open", side_effect=AssertionError("repeated file read")):
                self.assertEqual(_sha256(path, source_hash_cache=cache), original)
            path.write_bytes(b"second")
            self.assertNotEqual(_sha256(path, source_hash_cache=cache), original)
            event = threading.Event()
            event.set()
            with self.assertRaisesRegex(ExportExecutionError, "cancelled"):
                _sha256(path, source_hash_cache=cache, cancel_event=event)

    def test_planning_probes_only_included_sources_and_observes_cancellation(self):
        import threading

        source_path = Path(__file__).resolve()
        other_path = source_path.with_name("test_editor_av_compositor.py")
        project = Project.create_synchronized_multi(
            tuple(
                (path, {"duration_seconds": 2.0, "width": 720, "height": 720, "frame_rate": "30/1"})
                for path in (source_path, other_path)
            )
        )
        project.timeline.set_deleted(project.timeline.segment_items[1].segment_id, True)
        probe = _fake_probe(
            project.sources[0].source_id, source_path, width=720, height=720, frame_rate="30/1"
        )
        progress = []
        event = threading.Event()
        with patch("framestudio.video_compositor._probe_source", return_value=probe) as inspect:
            plan = plan_project_video(
                project,
                source_path.with_name("included-only.mp4"),
                target_rate=30,
                cancel_event=event,
                progress_callback=progress.append,
            )
        self.assertEqual(inspect.call_count, 1)
        self.assertEqual(len(plan.probed_metadata), 1)
        self.assertTrue(progress)
        event.set()
        with (
            patch("framestudio.video_compositor._probe_source") as inspect,
            self.assertRaisesRegex(
                (VideoCompositorPlanningError, ExportExecutionError), "cancelled"
            ),
        ):
            plan_project_video(project, source_path.with_name("cancelled.mp4"), cancel_event=event)
        inspect.assert_not_called()

    def test_cumulative_frame_boundaries_use_half_up_rational_positions(self):
        ticks = (0, 500_000, 1_000_001, 1_500_000)

        boundaries = cumulative_frame_boundaries(
            ticks,
            Fraction(60_000, 1_001),
        )

        expected = tuple(
            (Fraction(tick, 1_000_000) * Fraction(60_000, 1_001) + Fraction(1, 2)).numerator
            // (Fraction(tick, 1_000_000) * Fraction(60_000, 1_001) + Fraction(1, 2)).denominator
            for tick in ticks
        )
        self.assertEqual(boundaries, expected)
        self.assertEqual(
            tuple(
                right - left for left, right in zip(boundaries[:-1], boundaries[1:], strict=True)
            ),
            (30, 30, 30),
        )

    def test_plan_binds_original_sar_to_native_final_slot_identity(self):
        source_path = Path(__file__).resolve()
        project = Project.create_synchronized(
            source_path,
            {
                "duration_seconds": 2.0,
                "width": 720,
                "height": 576,
                "frame_rate": "30000/1001",
            },
            project_id="video-compositor-unit",
        )
        source_id = project.source.source_id
        probe = _fake_probe(
            source_id,
            source_path,
            width=720,
            height=576,
            frame_rate="30000/1001",
            sar=(16, 15),
        )

        with patch(
            "framestudio.video_compositor._probe_source",
            return_value=probe,
        ):
            plan = plan_project_video(
                project,
                source_path.with_name("unit-render.mp4"),
                target_rate=Fraction(60_000, 1_001),
            )

        self.assertEqual(plan.probed_metadata[0].sample_aspect_ratio, (16, 15))
        self.assertEqual(plan.layout_plan.output_domain.value, "final-slot")
        self.assertEqual(
            plan.preparation_identities[0].output_domain,
            "native-preparation",
        )
        crop = plan.layout_plan.intervals[0].slots[0].crop
        self.assertIsNotNone(crop)
        assert crop is not None
        self.assertEqual(crop.source_sar, (16, 15))
        self.assertEqual(crop.framing_identity.input_domain.value, "native-source")
        self.assertEqual(crop.framing_identity.output_domain.value, "final-slot")
        self.assertFalse(plan.include_audio)
        self.assertEqual(sum(plan.interval_frame_counts), plan.expected_frames)

    def test_plan_reports_boundary_safe_fallback_without_claiming_ai(self):
        source_path = Path(__file__).resolve()
        project = Project.create_synchronized(
            source_path,
            {
                "duration_seconds": 2.0,
                "width": 540,
                "height": 960,
                "frame_rate": "30000/1001",
            },
            project_id="video-compositor-policy",
        )
        source_id = project.source.source_id
        probe = _fake_probe(
            source_id,
            source_path,
            width=540,
            height=960,
            frame_rate="30000/1001",
        )

        with patch(
            "framestudio.video_compositor._probe_source",
            return_value=probe,
        ):
            plan = plan_project_video(
                project,
                source_path.with_name("policy-render.mp4"),
                target_rate=Fraction(60_000, 1_001),
            )

        route = plan.processing_routes[0]
        self.assertEqual(route.fps_action, "interpolate")
        self.assertIn(route.fps_backend, {"rve-4.26", "ffmpeg", "ffmpeg-minterpolate"})
        self.assertNotEqual(route.fps_status, "fake-ai")
        if route.upscale_requested:
            self.assertIn(route.upscale_status, {"available", "unavailable", "applied"})
            if route.upscale_status == "unavailable":
                self.assertTrue(route.upscale_reason)

    def test_plan_rejects_every_project_source_as_destination(self):
        source_paths = (
            Path(__file__).resolve(),
            Path(__file__).with_name("test_editor_video_compositor_functionality.py").resolve(),
        )
        project = Project.create_synchronized_multi(
            tuple(
                (
                    path,
                    {
                        "duration_seconds": 2.0,
                        "width": 720,
                        "height": 720,
                        "frame_rate": "30000/1001",
                    },
                )
                for path in source_paths
            ),
            project_id="video-compositor-source-guard",
        )
        probes = {
            source.source_id: _fake_probe(
                source.source_id,
                Path(source.path),
                width=720,
                height=720,
                frame_rate="30000/1001",
            )
            for source in project.sources or ()
        }

        with patch(
            "framestudio.video_compositor._probe_source",
            side_effect=lambda source_id, path, ffprobe_path="ffprobe": probes[source_id],
        ):
            with self.assertRaises(VideoCompositorPlanningError):
                plan_project_video(project, source_paths[1])

    def test_render_rechecks_destination_after_plan_replacement(self):
        source_path = Path(__file__).resolve()
        protected_path = (
            Path(__file__)
            .with_name(
                "test_editor_video_compositor_functionality.py",
            )
            .resolve()
        )
        project = Project.create_synchronized(
            source_path,
            {
                "duration_seconds": 2.0,
                "width": 720,
                "height": 720,
                "frame_rate": "30000/1001",
            },
            project_id="video-compositor-render-source-guard",
        )
        probe = _fake_probe(
            project.source.source_id,
            source_path,
            width=720,
            height=720,
            frame_rate="30000/1001",
        )

        with patch(
            "framestudio.video_compositor._probe_source",
            return_value=probe,
        ):
            plan = plan_project_video(
                project,
                source_path.with_name("render-source-guard.mp4"),
                target_rate=Fraction(30_000, 1_001),
            )

        altered_plan = replace(plan, destination=protected_path)
        with self.assertRaises(VideoCompositorExecutionError):
            render_project_video(altered_plan)

        replacement_project = Project.create_synchronized(
            protected_path,
            project.source.metadata,
        )
        changed_project_plan = replace(
            plan,
            project=replacement_project,
            destination=source_path,
        )
        with self.assertRaisesRegex(VideoCompositorExecutionError, "source media"):
            render_project_video(changed_project_plan)

        with TemporaryDirectory() as directory:
            root = Path(directory)
            missing_source_plan = replace(
                plan,
                destination=root / "render.mp4",
                probed_metadata=(replace(probe, path=root / "removed-source.mp4"),),
            )
            with patch("framestudio.video_compositor.shutil.which", return_value="ffmpeg"):
                with self.assertRaisesRegex(VideoCompositorExecutionError, "removed-source"):
                    render_project_video(missing_source_plan)
            self.assertEqual(tuple(root.iterdir()), ())

    def test_zero_frame_interval_is_retained_in_cumulative_plan(self):
        source_path = Path(__file__).resolve()
        project = Project.create_synchronized(
            source_path,
            {
                "duration_seconds": 2.0,
                "width": 720,
                "height": 720,
                "frame_rate": "30000/1001",
            },
            project_id="video-compositor-zero-frame-interval",
        )
        source_id = project.source.source_id
        project.timeline.replace_track_blocks(
            "track-1",
            (
                Segment.create(
                    0.0,
                    1.0,
                    segment_id="first",
                    block_id="first",
                    source_id=source_id,
                    timeline_start_seconds=0.0,
                    timeline_end_seconds=1.0,
                    track_id="track-1",
                ),
                Segment.create(
                    1.0,
                    2.0,
                    segment_id="second",
                    block_id="second",
                    source_id=source_id,
                    timeline_start_seconds=1.000001,
                    timeline_end_seconds=2.000001,
                    track_id="track-1",
                ),
            ),
        )
        project.duration_seconds = project.timeline.timeline_duration_seconds
        project.validate()
        probe = _fake_probe(
            source_id,
            source_path,
            width=720,
            height=720,
            frame_rate="30000/1001",
        )

        with patch(
            "framestudio.video_compositor._probe_source",
            return_value=probe,
        ):
            plan = plan_project_video(
                project,
                source_path.with_name("zero-frame-interval.mp4"),
                target_rate=Fraction(60_000, 1_001),
            )

        self.assertEqual(plan.interval_frame_counts, (60, 0, 60))
        self.assertEqual(plan.expected_frames, 120)
        self.assertEqual(
            tuple(interval.active_block_ids for interval in plan.layout_plan.intervals),
            (("first",), (), ("second",)),
        )

    def test_block_asset_names_remain_unique_after_readable_sanitization(self):
        self.assertNotEqual(_asset_stem("a/b"), _asset_stem("a_b"))

    def test_interpolation_export_error_uses_verified_fallback(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            plan = _unit_render_plan(root / "fallback-render.mp4")
            workspace = root / "workspace"
            workspace.mkdir()
            fallbacks: list[str] = []

            def make_native_asset(
                source: Path,
                destination: Path,
                start_seconds: float,
                end_seconds: float,
                expected_frames: int,
                ffmpeg_path: str,
                **_options,
            ) -> None:
                destination.touch()

            with (
                patch(
                    "framestudio.video_compositor._extract_block",
                    side_effect=make_native_asset,
                ),
                patch("framestudio.video_compositor._verify_preparation"),
                patch(
                    "framestudio.video_compositor.run_source_interpolation",
                    side_effect=(
                        ExportExecutionError("primary interpolation failed"),
                        None,
                    ),
                ) as interpolate,
            ):
                assets = _prepare_assets(
                    plan,
                    workspace,
                    ffmpeg_path="ffmpeg",
                    ffprobe_path="ffprobe",
                    fallbacks=fallbacks,
                )

            self.assertEqual(len(assets), 1)
            self.assertEqual(interpolate.call_count, 2)
            self.assertEqual(
                interpolate.call_args_list[0].kwargs["backend"],
                plan.processing_routes[0].fps_backend,
            )
            self.assertEqual(
                interpolate.call_args_list[1].kwargs["backend"],
                DEFAULT_FPS_FALLBACK_BACKEND,
            )
            self.assertEqual(len(fallbacks), 1)
            self.assertIn("verified FFmpeg minterpolate fallback used", fallbacks[0])

    def test_successful_fps_fallback_is_reported_on_public_result(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            destination = root / "reported-fallback.mp4"
            plan = _unit_render_plan(destination)
            output = _output_probe(plan, destination)
            with (
                patch(
                    "framestudio.video_compositor._extract_block",
                    side_effect=_make_native_asset,
                ),
                patch("framestudio.video_compositor._verify_preparation"),
                patch(
                    "framestudio.video_compositor.run_source_interpolation",
                    side_effect=(ExportExecutionError("primary interpolation failed"), None),
                ),
            ):
                with _render_output_patches(plan, output):
                    result = render_project_video(plan)

            self.assertTrue(
                any(
                    "verified FFmpeg minterpolate fallback used" in item
                    for item in result.processing_fallbacks
                )
            )
            self.assertTrue(destination.is_file())

    def test_failed_interpolation_fallback_is_explicit_and_publishes_nothing(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            destination = root / "failed-fallback.mp4"
            plan = _unit_render_plan(destination)
            workspace_prefix = f".{destination.name}.video-compositor-"

            with (
                patch("framestudio.video_compositor.shutil.which", return_value="/usr/bin/fake"),
                patch(
                    "framestudio.video_compositor._extract_block",
                    side_effect=_make_native_asset,
                ),
                patch("framestudio.video_compositor._verify_preparation"),
                patch(
                    "framestudio.video_compositor.run_source_interpolation",
                    side_effect=(
                        ExportExecutionError("primary interpolation failed"),
                        ExportExecutionError("fallback interpolation failed"),
                    ),
                ),
            ):
                with self.assertRaisesRegex(
                    VideoCompositorExecutionError,
                    "primary interpolation failed.*fallback interpolation failed",
                ):
                    render_project_video(plan)

            self.assertFalse(destination.exists())
            self.assertEqual(tuple(root.glob(f"{workspace_prefix}*")), ())
            self.assertEqual(tuple(root.glob(".*.partial-*.mp4")), ())

    def test_decode_export_error_is_normalized_with_cause(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            plan = _unit_render_plan(root / "decode-error.mp4")
            partial = root / "partial.mp4"
            partial.write_bytes(b"partial")
            output = _output_probe(plan, partial)

            with (
                patch("framestudio.video_compositor.probe_media", return_value=output),
                patch(
                    "framestudio.video_compositor.probe_frame_count",
                    return_value=plan.expected_frames,
                ),
                patch(
                    "framestudio.video_compositor.validate_decoded_output",
                    side_effect=ExportExecutionError("decode validation failed"),
                ),
            ):
                with self.assertRaisesRegex(
                    VideoCompositorExecutionError,
                    "decode validation failed",
                ) as raised:
                    _verify_rendered_output(
                        partial,
                        plan,
                        ffprobe_path="ffprobe",
                        ffmpeg_path="ffmpeg",
                    )

            self.assertIsInstance(raised.exception.__cause__, ExportExecutionError)

    def test_source_inspection_does_not_decode_entire_video_to_count_unused_frames(self):
        source_path = Path(__file__).resolve()
        media = MediaProbe(
            path=source_path,
            duration_seconds=2.0,
            width=720,
            height=720,
            frame_rate="30000/1001",
            video_codec="h264",
            audio_codec=None,
            format_name="mp4",
            audio_stream_present=False,
        )
        with (
            patch("framestudio.video_compositor.probe_media", return_value=media),
            patch("framestudio.video_compositor._probe_sample_aspect_ratio", return_value=(1, 1)),
            patch(
                "framestudio.video_compositor.probe_frame_count",
                side_effect=ExportExecutionError("frame probe failed"),
            ),
        ):
            inspected = _probe_source("source", source_path)
        self.assertIsNone(inspected.frame_count)

    def test_publication_observes_the_same_cancellation_event_as_rendering(self):
        with TemporaryDirectory() as directory:
            destination = Path(directory) / "cancel-at-publication.mp4"
            plan = _unit_render_plan(destination)
            output = _output_probe(plan, destination)
            event = threading.Event()
            with (
                patch("framestudio.video_compositor._prepare_assets", return_value={}),
                patch("framestudio.video_compositor.run_ffmpeg"),
                patch("framestudio.video_compositor.publish_verified_export") as publish,
                _render_output_patches(plan, output),
            ):
                render_project_video(plan, cancel_event=event)
            self.assertIs(publish.call_args.kwargs["cancel_event"], event)

    def test_source_preservation_failure_prevents_publication(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            destination = root / "source-changed.mp4"
            plan = _unit_render_plan(destination)
            output = _output_probe(plan, destination)

            with (
                patch("framestudio.video_compositor._prepare_assets", return_value={}),
                patch("framestudio.video_compositor.publish_verified_export") as publish,
            ):
                with _render_output_patches(plan, output, source_hash="changed-hash"):
                    with self.assertRaisesRegex(
                        VideoCompositorExecutionError,
                        "source changed during rendering",
                    ):
                        render_project_video(plan)

            publish.assert_not_called()
            self.assertFalse(destination.exists())
            self.assertEqual(tuple(root.glob(".*.partial-*.mp4")), ())

    def test_publication_export_error_is_normalized_with_cause(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            destination = root / "publication-error.mp4"
            plan = _unit_render_plan(destination)
            output = _output_probe(plan, destination)

            with (
                patch("framestudio.video_compositor._prepare_assets", return_value={}),
                patch(
                    "framestudio.video_compositor.publish_verified_export",
                    side_effect=ExportExecutionError("publication verification failed"),
                ),
            ):
                with _render_output_patches(plan, output):
                    with self.assertRaisesRegex(
                        VideoCompositorExecutionError,
                        "publication verification failed",
                    ) as raised:
                        render_project_video(plan)

            self.assertIsInstance(raised.exception.__cause__, ExportExecutionError)
            self.assertFalse(destination.exists())
            self.assertEqual(tuple(root.glob(".*.partial-*.mp4")), ())


@contextmanager
def _render_output_patches(
    plan: VideoRenderPlan,
    output: MediaProbe,
    *,
    source_hash: str = "unit-hash",
):
    with (
        patch(
            "framestudio.video_compositor._build_render_command",
            side_effect=_build_command,
        ),
        patch(
            "framestudio.video_compositor.subprocess.run",
            side_effect=_create_partial_output,
        ),
        patch("framestudio.video_compositor._verify_rendered_output"),
        patch("framestudio.video_compositor.probe_media", return_value=output),
        patch(
            "framestudio.video_compositor.probe_frame_count",
            return_value=plan.expected_frames,
        ),
        patch("framestudio.video_compositor._sha256", return_value=source_hash),
        patch("framestudio.video_compositor.shutil.which", return_value="/usr/bin/fake"),
    ):
        yield


def _output_probe(plan: VideoRenderPlan, path: Path) -> MediaProbe:
    return MediaProbe(
        path=path,
        duration_seconds=plan.expected_duration_seconds,
        width=1920,
        height=1080,
        frame_rate=str(plan.target_rate),
        video_codec="h264",
        audio_codec=None,
        format_name="mp4",
        audio_stream_present=False,
    )


def _make_native_asset(
    source: Path,
    output: Path,
    start_seconds: float,
    end_seconds: float,
    expected_frames: int,
    ffmpeg_path: str,
    **_options,
) -> None:
    output.touch()


def _build_command(
    render_plan: object,
    assets: object,
    *,
    output: Path,
    ffmpeg_path: str,
) -> list[str]:
    return [ffmpeg_path, str(output)]


def _create_partial_output(
    command: list[str],
    **kwargs: object,
) -> subprocess.CompletedProcess[str]:
    Path(command[-1]).write_bytes(b"partial")
    return subprocess.CompletedProcess(command, 0, "", "")


def _fake_probe(
    source_id: str,
    path: Path,
    *,
    width: int,
    height: int,
    frame_rate: str,
    sar: tuple[int, int] = (1, 1),
) -> VideoSourceProbe:
    media = MediaProbe(
        path=path,
        duration_seconds=2.0,
        width=width,
        height=height,
        frame_rate=frame_rate,
        video_codec="h264",
        audio_codec=None,
        format_name="mp4",
        audio_stream_present=False,
    )
    return VideoSourceProbe(
        source_id=source_id,
        path=path,
        media=media,
        geometry=SourceGeometry(
            source_id,
            width,
            height,
            sar_num=sar[0],
            sar_den=sar[1],
        ),
        sample_aspect_ratio=sar,
        frame_count=60,
        source_hash="unit-hash",
        source_stat=path.stat(),
    )


def _unit_render_plan(destination: Path):
    source_path = Path(__file__).resolve()
    project = Project.create_synchronized(
        source_path,
        {
            "duration_seconds": 2.0,
            "width": 720,
            "height": 720,
            "frame_rate": "30000/1001",
        },
        project_id="video-compositor-error-boundary",
    )
    probe = _fake_probe(
        project.source.source_id,
        source_path,
        width=720,
        height=720,
        frame_rate="30000/1001",
    )
    with (
        patch("framestudio.video_compositor._probe_source", return_value=probe),
        patch(
            "framestudio.video_compositor.validate_interpolation_backend",
            return_value=SimpleNamespace(available=True),
        ),
    ):
        return plan_project_video(
            project,
            destination,
            target_rate=Fraction(60_000, 1_001),
        )


if __name__ == "__main__":
    import unittest

    unittest.main()
