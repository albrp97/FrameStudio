import io
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from framestudio.app_project import _build_source_project, _finish_source_load
from framestudio.cli import cli_main
from framestudio.model import Project
from framestudio.persistence import load_project, save_project


def metadata(duration=3.0):
    return {
        "duration_seconds": duration,
        "width": 320,
        "height": 180,
        "frame_rate": "24/1",
        "video_codec": "h264",
        "audio_codec": None,
        "audio_stream_present": False,
        "format_name": "mp4",
    }


def make_project(paths):
    return Project.create_multi(tuple((path, metadata()) for path in paths))


def make_source_paths(root):
    paths = tuple(root / name for name in ("existing.mp4", "first.mp4", "second.mp4"))
    for path in paths:
        path.write_bytes(path.name.encode())
    return paths


class RandomizedClipAddFunctionalityTests(unittest.TestCase):
    def test_adding_multiple_gui_clips_shuffles_the_appended_timeline_order(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            existing_path, first_path, second_path = make_source_paths(root)

            existing = Project.create(existing_path, metadata())
            window = SimpleNamespace(
                _source_load_generation=1,
                _source_load_in_progress=True,
                project=existing,
                project_path=root / "edit.framestudio.json",
                _show_error=MagicMock(),
                _set_status=MagicMock(),
                _update_segment_controls=MagicMock(),
            )

            with (
                patch(
                    "framestudio.app_project.create_project_from_sources",
                    side_effect=lambda paths, **_kwargs: make_project(paths),
                ),
                patch("random.shuffle", side_effect=lambda paths: paths.reverse()),
                patch("framestudio.app_project.attach_project"),
            ):
                incoming = _build_source_project((first_path, second_path))
                _finish_source_load(
                    window,
                    1,
                    (first_path, second_path),
                    incoming,
                    None,
                )

            appended_paths = [Path(source.path).name for source in existing.sources[1:]]
            self.assertEqual(appended_paths, ["second.mp4", "first.mp4"])
            self.assertEqual(
                [block.source_id for block in existing.timeline.blocks[1:]],
                [source.source_id for source in existing.sources[1:]],
            )
            window._show_error.assert_not_called()

    def test_cli_add_shuffles_multiple_new_clips_before_appending(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            existing_path, first_path, second_path = make_source_paths(root)
            project_path = root / "edit.framestudio.json"
            save_project(Project.create(existing_path, metadata()), project_path)
            stdout = io.StringIO()
            stderr = io.StringIO()

            with (
                patch(
                    "framestudio.cli.create_project_from_sources",
                    side_effect=lambda paths, **_kwargs: make_project(paths),
                ),
                patch("random.shuffle", side_effect=lambda paths: paths.reverse()),
            ):
                result = cli_main(
                    ["add", str(project_path), str(first_path), str(second_path)],
                    stdout=stdout,
                    stderr=stderr,
                )

            self.assertEqual(result, 0, stderr.getvalue())
            restored = load_project(project_path)
            self.assertEqual(
                [Path(source.path).name for source in restored.sources[1:]],
                ["second.mp4", "first.mp4"],
            )
            self.assertEqual(
                [block.source_id for block in restored.timeline.blocks[1:]],
                [source.source_id for source in restored.sources[1:]],
            )
