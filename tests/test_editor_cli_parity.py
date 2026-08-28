import io
import json
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from resolve_editor.cli import cli_main
from resolve_editor.model import Project, ProjectValidationError
from resolve_editor.operations import (
    apply_visual_transform,
    set_segment_deleted,
    split_segment,
)
from resolve_editor.persistence import load_project, save_project


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


def run_cli(*arguments: str):
    stdout = io.StringIO()
    stderr = io.StringIO()
    result = cli_main(
        list(arguments),
        stdout=stdout,
        stderr=stderr,
    )
    return result, stdout, stderr


def timeline_shape(project: Project):
    return [
        (
            segment.start_seconds,
            segment.end_seconds,
            segment.deleted,
        )
        for segment in project.segment_timeline.segments
    ]


class EditorCliParityTests(unittest.TestCase):
    def test_cli_mutations_match_shared_gui_domain_operations(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            gui_path = root / "gui.resolve.json"
            cli_path = root / "cli.resolve.json"
            original = make_project(root)
            save_project(original, gui_path)
            save_project(original, cli_path)
            gui_project = load_project(gui_path)
            cli_project = load_project(cli_path)

            _first, gui_second = split_segment(
                gui_project.segment_timeline,
                4.0,
            )
            set_segment_deleted(
                gui_project.segment_timeline,
                gui_second.segment_id,
                True,
            )
            save_project(gui_project, gui_path)

            result, _stdout, stderr = run_cli(
                "split",
                str(cli_path),
                "--at",
                "4",
            )
            self.assertEqual(result, 0)
            self.assertEqual(stderr.getvalue(), "")
            cli_project = load_project(cli_path)
            cli_second = cli_project.segment_timeline.segments[1]

            result, _stdout, stderr = run_cli(
                "delete",
                str(cli_path),
                "--segment",
                cli_second.segment_id,
            )
            self.assertEqual(result, 0)
            self.assertEqual(stderr.getvalue(), "")
            cli_project = load_project(cli_path)

            self.assertEqual(
                timeline_shape(cli_project),
                timeline_shape(gui_project),
            )
            self.assertEqual(
                cli_project.segment_timeline.edited_duration_seconds,
                gui_project.segment_timeline.edited_duration_seconds,
            )
            self.assertEqual(cli_project.source.to_dict(), gui_project.source.to_dict())

    def test_cli_move_supports_one_source_blocks(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            project_path = root / "edit.resolve.json"
            project = make_project(root)
            project.segment_timeline.split(3.0)
            project.segment_timeline.split(7.0)
            first, middle, last = project.segment_timeline.segments
            save_project(project, project_path)

            result, stdout, stderr = run_cli(
                "move",
                str(project_path),
                "--segment",
                middle.segment_id,
                "--direction",
                "left",
            )

            self.assertEqual(result, 0)
            self.assertEqual(stderr.getvalue(), "")
            payload = json.loads(stdout.getvalue())
            self.assertTrue(payload["operation"]["changed"])
            reopened = load_project(project_path)
            self.assertEqual(
                [segment.segment_id for segment in reopened.segment_timeline.segments],
                [middle.segment_id, first.segment_id, last.segment_id],
            )
            self.assertEqual(
                [
                    (segment.timeline_start_seconds, segment.timeline_end_seconds)
                    for segment in reopened.segment_timeline.segments
                ],
                [(0.0, 4.0), (4.0, 7.0), (7.0, 10.0)],
            )
            self.assertEqual(reopened.segment_timeline.edited_duration_seconds, 10.0)

    def test_repeated_delete_and_reopen_keep_a_deterministic_project_state(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            project_path = root / "edit.resolve.json"
            project = make_project(root)
            project.segment_timeline.split(4.0)
            segment_id = project.segment_timeline.segments[1].segment_id
            save_project(project, project_path)

            result, _stdout, stderr = run_cli(
                "delete",
                str(project_path),
                "--segment",
                segment_id,
            )
            self.assertEqual(result, 0)
            self.assertEqual(stderr.getvalue(), "")
            first_state = load_project(project_path).to_dict()

            result, _stdout, stderr = run_cli(
                "delete",
                str(project_path),
                "--segment",
                segment_id,
            )
            self.assertEqual(result, 0)
            self.assertEqual(stderr.getvalue(), "")
            second_state = load_project(project_path).to_dict()

            self.assertEqual(first_state, second_state)
            reopened = load_project(project_path)
            self.assertEqual(reopened.to_dict(), first_state)

    def test_invalid_domain_operation_and_cli_operation_preserve_state(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            project_path = root / "edit.resolve.json"
            project = make_project(root)
            save_project(project, project_path)
            before = project_path.read_bytes()

            with self.assertRaises(ProjectValidationError):
                split_segment(project.segment_timeline, 0.0)

            result, stdout, stderr = run_cli(
                "split",
                str(project_path),
                "--at",
                "0",
            )

            self.assertEqual(result, 3)
            self.assertEqual(stdout.getvalue(), "")
            self.assertEqual(
                json.loads(stderr.getvalue())["error"]["code"],
                "invalid_operation",
            )
            self.assertEqual(project_path.read_bytes(), before)

    def test_cli_focus_clamps_to_zoom_dependent_bounds_like_domain_operation(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            project_path = root / "edit.resolve.json"
            project = make_project(root)
            segment_id = project.timeline.segments[0].segment_id
            save_project(project, project_path)

            expected = apply_visual_transform(
                project,
                [segment_id],
                zoom=4.0,
                offset_x=99999.0,
                offset_y=-99999.0,
            )
            result, stdout, stderr = run_cli(
                "focus",
                str(project_path),
                "--segment",
                segment_id,
                "--zoom",
                "4",
                "--offset-x",
                "99999",
                "--offset-y",
                "-99999",
            )

            self.assertEqual(result, 0)
            self.assertEqual(stderr.getvalue(), "")
            payload = json.loads(stdout.getvalue())
            transform = payload["project"]["timeline"]["segments"][0]["visual_transform"]
            self.assertEqual(transform["offset_x"], expected.offset_x)
            self.assertEqual(transform["offset_y"], expected.offset_y)

    def test_cli_focus_supports_default_zoom_triplicate_horizontal_offset(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            project_path = root / "edit.resolve.json"
            project = make_project(root)
            segment_id = project.timeline.segments[0].segment_id
            save_project(project, project_path)

            result, _stdout, stderr = run_cli(
                "triplicate-enable",
                str(project_path),
                "--segment",
                segment_id,
            )
            self.assertEqual(result, 0)
            self.assertEqual(stderr.getvalue(), "")

            result, stdout, stderr = run_cli(
                "focus",
                str(project_path),
                "--segment",
                segment_id,
                "--offset-x",
                "640",
            )

            self.assertEqual(result, 0)
            self.assertEqual(stderr.getvalue(), "")
            payload = json.loads(stdout.getvalue())
            transform = payload["project"]["timeline"]["segments"][0]["visual_transform"]
            self.assertEqual(transform["zoom"], 1.0)
            self.assertEqual(transform["offset_x"], 640.0)
            self.assertEqual(
                payload["project"]["timeline"]["segments"][0]["triplicate"]["shared_transform"],
                transform,
            )

    def test_executable_dispatches_non_gui_subcommands(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            project_path = root / "edit.resolve.json"
            save_project(make_project(root), project_path)

            result = subprocess.run(
                [
                    sys.executable,
                    "resolve_editor.py",
                    "duration",
                    str(project_path),
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stderr, "")
            payload = json.loads(result.stdout)
            self.assertEqual(payload["command"], "duration")
            self.assertEqual(payload["duration_seconds"], 10.0)


if __name__ == "__main__":
    unittest.main()
