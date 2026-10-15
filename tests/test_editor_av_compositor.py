from __future__ import annotations

import subprocess
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from framestudio.audio_compositor import build_audio_plan
from framestudio.media import probe_media
from framestudio.upscale_policy import UpscalePolicy
from framestudio.video_compositor import plan_project_video
from tests.test_editor_av_compositor_functionality import (
    _build_dynamic_project,
    _make_audio_stage,
    _require_av_compositor,
    _safe_frame_rate_policy,
    isolated_directory,
)
from tests.test_editor_video_compositor_functionality import _sha256


def _mock_child_results(
    plan,
    video_destination: Path,
    audio_destination: Path,
    *,
    output_probe=None,
):
    video_result = SimpleNamespace(
        destination=video_destination,
        output_probe=output_probe,
        actual_frames=plan.video_plan.expected_frames,
        expected_frames=plan.video_plan.expected_frames,
        source_hashes_unchanged=True,
        processing_fallbacks=(),
    )
    audio_result = SimpleNamespace(
        output_path=audio_destination,
        sample_rate=48_000,
        channels=2,
        sample_count=plan.audio_plan.final_sample_count,
        peak=0.1,
        plan=plan.audio_plan,
    )
    return video_result, audio_result


class AVCompositorUnitTests(TestCase):
    def test_public_boundary_exposes_typed_planning_and_execution_errors(self):
        av = _require_av_compositor(self)
        self.assertTrue(callable(av.plan_project_av))
        self.assertTrue(callable(av.render_project_av))
        self.assertTrue(
            isinstance(getattr(av, "AVCompositorPlanningError", None), type),
            "AVCompositorPlanningError is the public planning failure type",
        )
        self.assertTrue(
            isinstance(getattr(av, "AVCompositorExecutionError", None), type),
            "AVCompositorExecutionError is the public execution failure type",
        )

    def test_planner_reuses_video_layout_for_the_audio_plan(self):
        av = _require_av_compositor(self)
        with isolated_directory() as root:
            project, _, _ = _build_dynamic_project(root / "fixtures")
            destination = root / "combined.mp4"
            video_plan = plan_project_video(
                project,
                destination,
                frame_rate_policy=_safe_frame_rate_policy(),
                upscale_policy=UpscalePolicy(enhancement_enabled=False),
            )
            audio_plan = build_audio_plan(project, video_plan.layout_plan)
            with (
                patch.object(av, "plan_project_video", return_value=video_plan) as plan_video,
                patch.object(av, "build_audio_plan", return_value=audio_plan) as plan_audio,
            ):
                combined_plan = av.plan_project_av(
                    project,
                    destination,
                    frame_rate_policy=_safe_frame_rate_policy(),
                    upscale_policy=UpscalePolicy(enhancement_enabled=False),
                )

            self.assertTrue(plan_video.called)
            self.assertTrue(plan_audio.called)
            self.assertIs(combined_plan.video_plan, video_plan)
            self.assertIs(combined_plan.audio_plan, audio_plan)
            self.assertIs(plan_audio.call_args.args[0], project)
            layout_argument = (
                plan_audio.call_args.args[1]
                if len(plan_audio.call_args.args) > 1
                else plan_audio.call_args.kwargs["layout_plan"]
            )
            self.assertIs(layout_argument, video_plan.layout_plan)

    def test_planning_is_filesystem_pure_without_a_caller_cleanup_path(self):
        av = _require_av_compositor(self)
        with isolated_directory() as root:
            project, _, _ = _build_dynamic_project(root / "fixtures")
            destination = root / "not-created-yet" / "combined.mp4"
            before = tuple(sorted(path.relative_to(root) for path in root.rglob("*")))

            plan = av.plan_project_av(
                project,
                destination,
                frame_rate_policy=_safe_frame_rate_policy(),
                upscale_policy=UpscalePolicy(enhancement_enabled=False),
            )

            after = tuple(sorted(path.relative_to(root) for path in root.rglob("*")))
            self.assertEqual(after, before)
            self.assertFalse(destination.parent.exists())
            self.assertEqual(plan.video_plan.destination, destination.resolve())
            self.assertFalse(hasattr(plan, "staging_directory"))
            with self.assertRaises(TypeError):
                replace(plan, staging_directory=root)

    def test_live_destination_guard_protects_planned_unused_alias_after_plan_change(self):
        av = _require_av_compositor(self)
        with isolated_directory() as root:
            project, sources, _ = _build_dynamic_project(root / "fixtures")
            unused_source = sources[-1]
            unused_alias = root / "unused-source-alias.mp4"
            unused_alias.symlink_to(unused_source)
            unused_reference = next(
                source
                for source in project.sources or ()
                if Path(source.path) == unused_source.resolve()
            )
            project.sources = tuple(
                replace(
                    source,
                    uri=unused_alias.as_uri(),
                )
                if source.source_id == unused_reference.source_id
                else source
                for source in project.sources or ()
            )
            plan = av.plan_project_av(
                project,
                root / "combined.mp4",
                frame_rate_policy=_safe_frame_rate_policy(),
                upscale_policy=UpscalePolicy(enhancement_enabled=False),
            )
            original_bytes = unused_source.read_bytes()
            project.sources = tuple(
                source
                for source in project.sources or ()
                if source.source_id != unused_reference.source_id
            )
            stale_plan = replace(plan, destination=unused_alias)

            with self.assertRaises(av.AVCompositorPlanningError):
                av.render_project_av(stale_plan)

            self.assertEqual(unused_source.read_bytes(), original_bytes)
            self.assertTrue(unused_alias.is_symlink())
            self.assertEqual(unused_alias.resolve(), unused_source.resolve())
            self.assertFalse(hasattr(stale_plan, "staging_directory"))
            self.assertEqual(
                tuple(root.glob(f".{stale_plan.destination.name}*")),
                (),
            )

    def test_planning_rejects_every_original_source_and_resolved_alias(self):
        av = _require_av_compositor(self)
        with isolated_directory() as root:
            project, sources, _ = _build_dynamic_project(root / "fixtures")
            destination = root / "combined.mp4"
            planning_error = av.AVCompositorPlanningError
            for source in sources:
                with self.subTest(source=source.name):
                    with self.assertRaises(planning_error):
                        av.plan_project_av(
                            project,
                            Path(source),
                            frame_rate_policy=_safe_frame_rate_policy(),
                            upscale_policy=UpscalePolicy(enhancement_enabled=False),
                        )

            alias = root / "source-alias.mp4"
            alias.symlink_to(sources[0])
            with self.assertRaises(planning_error):
                av.plan_project_av(
                    project,
                    alias,
                    frame_rate_policy=_safe_frame_rate_policy(),
                    upscale_policy=UpscalePolicy(enhancement_enabled=False),
                )

            plan = av.plan_project_av(
                project,
                destination,
                frame_rate_policy=_safe_frame_rate_policy(),
                upscale_policy=UpscalePolicy(enhancement_enabled=False),
            )
            self.assertEqual(plan.destination, destination.resolve())

    def test_injected_mux_failure_preserves_destination_sources_and_partial_cleanup(self):
        av = _require_av_compositor(self)
        with isolated_directory() as root:
            project, sources, _ = _build_dynamic_project(root / "fixtures")
            destination = root / "combined.mp4"
            destination.write_bytes(b"existing-final")
            source_hashes = {path.name: _sha256(path) for path in sources}
            audio_stage = root / "audio-stage.wav"
            _make_audio_stage(sources[0], audio_stage)
            plan = av.plan_project_av(
                project,
                destination,
                frame_rate_policy=_safe_frame_rate_policy(),
                upscale_policy=UpscalePolicy(enhancement_enabled=False),
            )
            video_result, audio_result = _mock_child_results(
                plan,
                sources[0],
                audio_stage,
            )
            execution_error = av.AVCompositorExecutionError
            with (
                patch.object(av, "render_project_video", return_value=video_result),
                patch.object(av, "render_audio", return_value=audio_result),
                patch.object(
                    av.subprocess,
                    "run",
                    return_value=subprocess.CompletedProcess(
                        ["ffmpeg"],
                        1,
                        stdout="",
                        stderr="injected mux failure",
                    ),
                ),
            ):
                with self.assertRaisesRegex(execution_error, "injected mux failure"):
                    av.render_project_av(plan)

            self.assertEqual(destination.read_bytes(), b"existing-final")
            self.assertEqual(
                {path.name: _sha256(path) for path in sources},
                source_hashes,
            )
            self.assertEqual(
                tuple(root.glob(f".{destination.name}*partial*")),
                (),
            )

    def test_injected_verification_failure_preserves_destination_and_sources(self):
        av = _require_av_compositor(self)
        with isolated_directory() as root:
            project, sources, _ = _build_dynamic_project(root / "fixtures")
            destination = root / "verification-failure.mp4"
            destination.write_bytes(b"verified-old")
            source_hashes = {path.name: _sha256(path) for path in sources}
            plan = av.plan_project_av(
                project,
                destination,
                frame_rate_policy=_safe_frame_rate_policy(),
                upscale_policy=UpscalePolicy(enhancement_enabled=False),
            )
            video_stage = sources[0]
            audio_stage = root / "audio-stage.wav"
            _make_audio_stage(video_stage, audio_stage)
            invalid_probe = root / "invalid-ffprobe"
            invalid_probe.write_text("#!/bin/sh\nprintf '{}'\n", encoding="utf-8")
            invalid_probe.chmod(0o755)
            video_result, audio_result = _mock_child_results(
                plan,
                video_stage,
                audio_stage,
                output_probe=probe_media(video_stage),
            )
            execution_error = av.AVCompositorExecutionError
            with (
                patch.object(av, "render_project_video", return_value=video_result),
                patch.object(av, "render_audio", return_value=audio_result),
            ):
                with self.assertRaises(execution_error):
                    av.render_project_av(
                        plan,
                        ffprobe_path=str(invalid_probe),
                    )

            self.assertEqual(destination.read_bytes(), b"verified-old")
            self.assertEqual(
                {path.name: _sha256(path) for path in sources},
                source_hashes,
            )
            self.assertEqual(
                tuple(root.glob(f".{destination.name}*partial*")),
                (),
            )

    def test_changed_original_source_cannot_publish_a_combined_output(self):
        av = _require_av_compositor(self)
        with isolated_directory() as root:
            project, sources, _ = _build_dynamic_project(root / "fixtures")
            destination = root / "source-change.mp4"
            destination.write_bytes(b"before-source-change")
            plan = av.plan_project_av(
                project,
                destination,
                frame_rate_policy=_safe_frame_rate_policy(),
                upscale_policy=UpscalePolicy(enhancement_enabled=False),
            )
            unused_source = sources[-1]
            unused_source.write_bytes(unused_source.read_bytes() + b"changed")
            with self.assertRaises(av.AVCompositorExecutionError):
                av.render_project_av(plan)
            self.assertEqual(destination.read_bytes(), b"before-source-change")
            self.assertEqual(
                tuple(root.glob(f".{destination.name}*partial*")),
                (),
            )


if __name__ == "__main__":
    import unittest

    unittest.main()
