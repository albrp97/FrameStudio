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
from resolve_editor.media import MediaProbe
from resolve_editor.model import Project
from resolve_editor.persistence import save_project


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
