import io
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from resolve_editor.cli import cli_main
from resolve_editor.export import (
    ExportExecutionError,
    ExportPlan,
    ExportProgress,
)
from resolve_editor.fps_policy import resolve_frame_rate_policy
from resolve_editor.media import MediaProbe
from resolve_editor.model import Project
from resolve_editor.persistence import save_project
from resolve_editor.upscale_policy import UpscalePolicy, resolve_upscale_policy


def make_project(root: Path) -> Project:
    source = root / "source.mp4"
    source.write_bytes(b"fixture")
    return Project.create(
        source,
        {
            "duration_seconds": 10.0,
            "width": 320,
            "height": 180,
            "frame_rate": "10/1",
            "video_codec": "h264",
            "audio_codec": None,
            "format_name": "mp4",
        },
    )


def make_probe(path: Path) -> MediaProbe:
    return MediaProbe(
        path=path,
        duration_seconds=10.0,
        width=320,
        height=180,
        frame_rate="10/1",
        video_codec="h264",
        audio_codec=None,
        format_name="mp4",
    )


def run_cli(*arguments: str):
    stdout = io.StringIO()
    stderr = io.StringIO()
    result = cli_main(
        list(arguments),
        stdout=stdout,
        stderr=stderr,
    )
    return result, stdout, stderr


class EditorCliExportTests(unittest.TestCase):
    def test_export_resolves_unavailable_default_rve_to_ffmpeg_fallback(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            project_path = root / "edit.resolve.json"
            destination = root / "edited.mp4"
            project = make_project(root)
            save_project(project, project_path)
            fallback = resolve_frame_rate_policy(
                (
                    {
                        **project.source.metadata,
                        "source_id": project.source.source_id,
                    },
                ),
                choice="60",
                enhancement_enabled=True,
                backend="ffmpeg-minterpolate",
            )
            plan = ExportPlan(
                route="fallback",
                source=root / "source.mp4",
                destination=destination,
                segments=tuple(project.timeline.segments),
                expected_duration_seconds=10.0,
                reason="target policy",
                frame_rate_policy=fallback.policy.to_dict(),
            )

            with (
                patch(
                    "resolve_editor.cli.resolve_frame_rate_policy_with_fallback",
                    return_value=(fallback, (), "RVE unavailable"),
                ),
                patch(
                    "resolve_editor.cli.plan_project_export",
                    return_value=plan,
                ) as plan_export,
            ):
                result, stdout, stderr = run_cli(
                    "export-plan",
                    str(project_path),
                    "--output",
                    str(destination),
                )

            self.assertEqual(result, 0)
            self.assertEqual(stderr.getvalue(), "")
            self.assertEqual(
                plan_export.call_args.kwargs["frame_rate_policy"].policy.backend,
                "ffmpeg-minterpolate",
            )
            payload = json.loads(stdout.getvalue())
            self.assertEqual(
                payload["export"]["frame_rate_policy"]["backend"],
                "ffmpeg-minterpolate",
            )

    def test_export_plan_can_resolve_smart_destination_without_starting_execution(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            project_path = root / "edit.resolve.json"
            project = make_project(root)
            save_project(project, project_path)
            plan = ExportPlan(
                route="fallback",
                source=root / "source.mp4",
                destination=root / "edit-edited.mp4",
                segments=tuple(project.timeline.segments),
                expected_duration_seconds=10.0,
                reason="target policy",
                source_paths=(root / "source.mp4",),
                source_ids=("source",),
            )

            with (
                patch(
                    "resolve_editor.cli.plan_project_export",
                    return_value=plan,
                ) as plan_export,
                patch(
                    "resolve_editor.cli.execute_export",
                ) as execute,
            ):
                result, stdout, stderr = run_cli(
                    "export-plan",
                    str(project_path),
                )

            self.assertEqual(result, 0)
            self.assertEqual(stderr.getvalue(), "")
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["command"], "export-plan")
            self.assertTrue(payload["export"]["planned"])
            self.assertFalse(payload["export"]["verified"])
            self.assertEqual(payload["export"]["plan"]["source"], "source.mp4")
            self.assertEqual(payload["export"]["plan"]["destination"], "edit-edited.mp4")
            self.assertEqual(payload["export"]["plan"]["source_paths"], ["source.mp4"])
            self.assertNotIn(str(root), stdout.getvalue())
            self.assertTrue(plan_export.called)
            self.assertFalse(execute.called)

    def test_set_fps_policy_persists_a_machine_readable_policy(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            project_path = root / "edit.resolve.json"
            save_project(make_project(root), project_path)

            result, stdout, stderr = run_cli(
                "set-fps-policy",
                str(project_path),
                "--choice",
                "60",
                "--enhance-fps",
                "--fps-backend",
                "ffmpeg-minterpolate",
            )

            self.assertEqual(result, 0)
            self.assertEqual(stderr.getvalue(), "")
            payload = json.loads(stdout.getvalue())
            policy = payload["project"]["frame_rate_policy"]
            self.assertEqual(policy["choice"], "60")
            self.assertEqual(policy["target_rate"], "60")
            self.assertTrue(policy["enhancement_enabled"])
            self.assertEqual(policy["backend"], "ffmpeg-minterpolate")

    def test_set_fps_policy_keeps_existing_enhancement_when_toggle_is_omitted(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            project_path = root / "edit.resolve.json"
            project = make_project(root)
            project.set_frame_rate_policy(
                {
                    "choice": "custom",
                    "custom_rate": "20/1",
                    "target_rate": "20/1",
                    "enhancement_enabled": True,
                    "backend": "ffmpeg-minterpolate",
                }
            )
            save_project(project, project_path)

            result, stdout, stderr = run_cli(
                "set-fps-policy",
                str(project_path),
                "--choice",
                "60",
                "--fps-backend",
                "ffmpeg-minterpolate",
            )

            self.assertEqual(result, 0)
            self.assertEqual(stderr.getvalue(), "")
            payload = json.loads(stdout.getvalue())
            self.assertTrue(payload["project"]["frame_rate_policy"]["enhancement_enabled"])

    def test_set_upscale_policy_persists_the_enhancement_policy(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            project_path = root / "edit.resolve.json"
            save_project(make_project(root), project_path)

            result, stdout, stderr = run_cli(
                "set-upscale-policy",
                str(project_path),
                "--enable-upscale",
                "--upscale-model",
                "SuperUltraCompact",
                "--upscale-backend",
                "rve-restoration",
            )

            self.assertEqual(result, 0)
            self.assertEqual(stderr.getvalue(), "")
            payload = json.loads(stdout.getvalue())
            policy = payload["project"]["upscale_policy"]
            self.assertTrue(policy["enhancement_enabled"])
            self.assertEqual(policy["model"], "SuperUltraCompact")
            self.assertEqual(policy["backend"], "rve-restoration")
            self.assertEqual(policy["decisions"][0]["action"], "enhance")

    def test_export_plan_accepts_upscale_override_and_reports_decisions(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            project_path = root / "edit.resolve.json"
            project = make_project(root)
            save_project(project, project_path)
            destination = root / "edited.mp4"
            policy = UpscalePolicy(enhancement_enabled=True)
            resolved_upscale = resolve_upscale_policy(
                (
                    {
                        **project.source.metadata,
                        "source_id": project.source.source_id,
                    },
                ),
                policy=policy,
            )
            plan = ExportPlan(
                route="enhanced",
                source=root / "source.mp4",
                destination=destination,
                segments=tuple(project.timeline.segments),
                expected_duration_seconds=10.0,
                reason="upscale enhancement",
                upscale_policy=policy,
                upscale_decisions=resolved_upscale.decisions,
            )

            with (
                patch(
                    "resolve_editor.cli.resolve_frame_rate_policy_with_fallback",
                    return_value=(
                        resolve_frame_rate_policy(
                            (
                                {
                                    **project.source.metadata,
                                    "source_id": project.source.source_id,
                                },
                            ),
                            choice="60",
                            enhancement_enabled=False,
                        ),
                        (),
                        None,
                    ),
                ) as fps_policy,
                patch(
                    "resolve_editor.cli.plan_project_export",
                    return_value=plan,
                ) as plan_export,
            ):
                result, stdout, stderr = run_cli(
                    "export-plan",
                    str(project_path),
                    "--output",
                    str(destination),
                    "--no-enhance-fps",
                    "--upscale-enhancement",
                )

            self.assertEqual(result, 0)
            self.assertEqual(stderr.getvalue(), "")
            self.assertTrue(fps_policy.called)
            self.assertTrue(
                plan_export.call_args.kwargs["upscale_policy"].policy.enhancement_enabled
            )
            payload = json.loads(stdout.getvalue())
            self.assertTrue(payload["export"]["upscale_policy"]["enhancement_enabled"])
            self.assertEqual(
                payload["export"]["upscale_policy"]["decisions"][0]["action"],
                "enhance",
            )

    def test_export_plan_reports_frame_rate_policy_object_override(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            project_path = root / "edit.resolve.json"
            destination = root / "edited.mp4"
            project = make_project(root)
            save_project(project, project_path)
            policy = resolve_frame_rate_policy(
                (
                    {
                        **project.source.metadata,
                        "source_id": project.source.source_id,
                    },
                ),
                choice="60",
                enhancement_enabled=False,
            )
            plan = ExportPlan(
                route="fallback",
                source=root / "source.mp4",
                destination=destination,
                segments=tuple(project.timeline.segments),
                expected_duration_seconds=10.0,
                reason="target policy",
                frame_rate_policy=policy.policy,
            )

            with (
                patch(
                    "resolve_editor.cli.resolve_frame_rate_policy_with_fallback",
                    return_value=(policy, (), None),
                ),
                patch(
                    "resolve_editor.cli.plan_project_export",
                    return_value=plan,
                ),
            ):
                result, stdout, stderr = run_cli(
                    "export-plan",
                    str(project_path),
                    "--output",
                    str(destination),
                    "--no-enhance-fps",
                )

            self.assertEqual(result, 0)
            self.assertEqual(stderr.getvalue(), "")
            payload = json.loads(stdout.getvalue())
            self.assertFalse(payload["export"]["frame_rate_policy"]["enhancement_enabled"])

    def test_export_reports_progress_route_and_verified_output(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            project_path = root / "edit.resolve.json"
            destination = root / "edited.mp4"
            project = make_project(root)
            save_project(project, project_path)
            destination.write_bytes(b"verified")
            source_probe = make_probe(root / "source.mp4")
            output_probe = make_probe(destination)
            plan = ExportPlan(
                route="stream-copy",
                source=source_probe.path,
                destination=destination,
                segments=tuple(project.segment_timeline.segments),
                expected_duration_seconds=10.0,
                reason="No internal cut boundaries require re-encoding",
            )

            def fake_execute(plan, **kwargs):
                kwargs["progress_callback"](
                    ExportProgress(
                        stage="encoding",
                        percent=50.0,
                        frame=50,
                        total_frames=100,
                        fps=10.0,
                        elapsed_seconds=1.0,
                        eta_seconds=1.0,
                    )
                )
                return plan.destination

            with (
                patch(
                    "resolve_editor.cli.probe_media",
                    return_value=output_probe,
                ),
                patch(
                    "resolve_editor.cli.plan_project_export",
                    return_value=plan,
                ),
                patch(
                    "resolve_editor.cli.execute_export",
                    side_effect=fake_execute,
                ),
            ):
                result, stdout, stderr = run_cli(
                    "export",
                    str(project_path),
                    "--output",
                    str(destination),
                )

            self.assertEqual(result, 0)
            self.assertEqual(stderr.getvalue(), "")
            lines = [json.loads(line) for line in stdout.getvalue().splitlines()]
            self.assertEqual(lines[0]["command"], "export.progress")
            self.assertEqual(lines[0]["progress"]["percent"], 50.0)
            self.assertEqual(lines[-1]["command"], "export")
            self.assertTrue(lines[-1]["export"]["verified"])
            self.assertEqual(lines[-1]["export"]["route"], "stream-copy")
            self.assertEqual(lines[-1]["export"]["destination"], "edited.mp4")
            self.assertNotIn(str(root), stdout.getvalue())

    def test_export_failure_returns_structured_error_without_success_result(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            project_path = root / "edit.resolve.json"
            destination = root / "edited.mp4"
            project = make_project(root)
            save_project(project, project_path)
            source_probe = make_probe(root / "source.mp4")
            plan = ExportPlan(
                route="fallback",
                source=source_probe.path,
                destination=destination,
                segments=tuple(project.segment_timeline.segments),
                expected_duration_seconds=10.0,
                reason="cut boundary requires re-encoding",
                fallback_video_codec="libx264",
                fallback_container="mp4",
                fallback_pixel_format="yuv420p",
            )

            with (
                patch(
                    "resolve_editor.cli.probe_media",
                    return_value=source_probe,
                ),
                patch(
                    "resolve_editor.cli.plan_project_export",
                    return_value=plan,
                ),
                patch(
                    "resolve_editor.cli.execute_export",
                    side_effect=ExportExecutionError("validation failed"),
                ),
            ):
                result, stdout, stderr = run_cli(
                    "export",
                    str(project_path),
                    "--output",
                    str(destination),
                )

            self.assertEqual(result, 5)
            self.assertNotIn('"command": "export"', stdout.getvalue())
            payload = json.loads(stderr.getvalue())
            self.assertFalse(payload["ok"])
            self.assertEqual(payload["error"]["code"], "export_failed")
            self.assertIn("validation failed", payload["error"]["message"])
            self.assertFalse(destination.exists())

    def test_export_rejects_project_path_without_replacing_project(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            project_path = root / "edit.resolve.json"
            project = make_project(root)
            save_project(project, project_path)
            before = project_path.read_bytes()
            source_probe = make_probe(root / "source.mp4")
            plan = ExportPlan(
                route="stream-copy",
                source=source_probe.path,
                destination=project_path,
                segments=tuple(project.segment_timeline.segments),
                expected_duration_seconds=10.0,
                reason="No internal cut boundaries require re-encoding",
            )

            with (
                patch(
                    "resolve_editor.cli.plan_project_export",
                    return_value=plan,
                ) as plan_export,
                patch(
                    "resolve_editor.cli.execute_export",
                    return_value=project_path,
                ) as execute,
                patch(
                    "resolve_editor.cli.probe_media",
                    return_value=source_probe,
                ) as probe,
            ):
                result, stdout, stderr = run_cli(
                    "export",
                    str(project_path),
                    "--output",
                    str(project_path),
                )

            self.assertEqual(result, 3)
            self.assertEqual(stdout.getvalue(), "")
            payload = json.loads(stderr.getvalue())
            self.assertFalse(payload["ok"])
            self.assertEqual(payload["error"]["code"], "invalid_arguments")
            self.assertIn("project file", payload["error"]["message"])
            self.assertEqual(project_path.read_bytes(), before)
            self.assertFalse(plan_export.called)
            self.assertFalse(execute.called)
            self.assertFalse(probe.called)


if __name__ == "__main__":
    unittest.main()
