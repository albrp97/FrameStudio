import io
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from framestudio.cli import cli_main
from framestudio.model import Project
from framestudio.persistence import load_project, save_project


def metadata(duration, width, height, frame_rate):
    return {
        "duration_seconds": duration,
        "width": width,
        "height": height,
        "frame_rate": frame_rate,
        "video_codec": "h264",
        "audio_codec": None,
        "audio_stream_present": False,
        "format_name": "mp4",
    }


def run_cli(*arguments):
    stdout = io.StringIO()
    stderr = io.StringIO()
    result = cli_main(list(arguments), stdout=stdout, stderr=stderr)
    return result, stdout, stderr


class MixedSourceCliTests(unittest.TestCase):
    def make_project(self, root):
        first = root / "one.mp4"
        second = root / "two.mp4"
        first.write_bytes(b"one")
        second.write_bytes(b"two")
        return Project.create_multi(
            (
                (first, metadata(4.0, 320, 180, "24/1")),
                (second, metadata(3.0, 180, 320, "30/1")),
            )
        )

    def test_inspect_exposes_sources_and_redacts_every_path(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            project_path = root / "mixed.framestudio.json"
            save_project(self.make_project(root), project_path)

            result, stdout, stderr = run_cli("inspect", str(project_path))

            self.assertEqual(result, 0)
            self.assertEqual(stderr.getvalue(), "")
            payload = json.loads(stdout.getvalue())
            self.assertEqual(len(payload["project"]["sources"]), 2)
            self.assertNotIn(str(root), stdout.getvalue())
            self.assertEqual(
                len(payload["project"]["timeline"]["blocks"]),
                2,
            )
            self.assertTrue(
                all(
                    isinstance(block["color_index"], int)
                    for block in payload["project"]["timeline"]["blocks"]
                )
            )

    def test_add_appends_source_without_replacing_existing_cuts(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            first_path = root / "one.mp4"
            first_path.write_bytes(b"one")
            project = Project.create(first_path, metadata(4.0, 320, 180, "24/1"))
            project.timeline.split(2.0)
            deleted_id = project.timeline.blocks[1].segment_id
            project.timeline.set_deleted(deleted_id, True)
            project_path = root / "edit.framestudio.json"
            save_project(project, project_path)
            added_path = root / "added.mp4"
            added_path.write_bytes(b"added")
            incoming = Project.create(added_path, metadata(3.0, 180, 320, "30/1"))

            with patch(
                "framestudio.cli.create_project_from_source",
                return_value=incoming,
            ):
                result, stdout, stderr = run_cli(
                    "add",
                    str(project_path),
                    str(added_path),
                )

            self.assertEqual(result, 0)
            self.assertEqual(stderr.getvalue(), "")
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["command"], "add")
            self.assertEqual(payload["operation"]["source_count"], 2)
            self.assertEqual(
                payload["operation"]["added_source_ids"],
                [incoming.source.source_id],
            )
            restored = load_project(project_path)
            self.assertTrue(restored.timeline.find(deleted_id).deleted)
            self.assertEqual(restored.timeline.blocks[-1].source_id, restored.sources[1].source_id)

    def test_move_and_paste_are_deterministic_and_persisted(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            project_path = root / "mixed.framestudio.json"
            project = self.make_project(root)
            save_project(project, project_path)
            first_id = project.timeline.blocks[0].segment_id
            second_id = project.timeline.blocks[1].segment_id

            result, stdout, stderr = run_cli(
                "move",
                str(project_path),
                "--segment",
                second_id,
                "--direction",
                "left",
            )
            self.assertEqual(result, 0)
            self.assertEqual(stderr.getvalue(), "")
            moved = json.loads(stdout.getvalue())
            self.assertEqual(
                [block["segment_id"] for block in moved["project"]["timeline"]["blocks"]],
                [second_id, first_id],
            )

            result, stdout, stderr = run_cli(
                "paste",
                str(project_path),
                "--segment",
                first_id,
                "--at",
                "0",
            )
            self.assertEqual(result, 0)
            self.assertEqual(stderr.getvalue(), "")
            pasted = json.loads(stdout.getvalue())
            ids = [block["segment_id"] for block in pasted["project"]["timeline"]["blocks"]]
            self.assertEqual(len(ids), 3)
            self.assertNotEqual(ids[0], first_id)
            self.assertEqual(ids[1:], [second_id, first_id])
            self.assertEqual(
                pasted["operation"]["pasted_segment_ids"],
                [ids[0]],
            )
            self.assertEqual(len(set(ids)), 3)
            self.assertEqual(
                load_project(project_path).timeline.blocks[0].source_id,
                project.timeline.blocks[0].source_id,
            )
            self.assertEqual(
                [block["color_index"] for block in pasted["project"]["timeline"]["blocks"]],
                [block.color_index for block in load_project(project_path).timeline.blocks],
            )

    def test_relink_reports_source_identity_for_a_missing_source(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            project = self.make_project(root)
            project_path = root / "mixed.framestudio.json"
            save_project(project, project_path)
            source = project.sources[0]
            old_path = Path(source.path)
            old_path.unlink()
            moved = root / "relocated.mp4"
            moved.write_bytes(b"one")

            result, stdout, stderr = run_cli(
                "relink",
                str(project_path),
                "--source",
                source.source_id,
                "--path",
                str(moved),
            )

            self.assertEqual(result, 0)
            self.assertEqual(stdout.getvalue().count("\n"), 1)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(
                payload["operation"]["source_id"],
                source.source_id,
            )
            self.assertEqual(stderr.getvalue(), "")


if __name__ == "__main__":
    unittest.main()
