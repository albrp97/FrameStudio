from __future__ import annotations

import argparse
import importlib
import io
import json
import unittest
from pathlib import Path
from typing import Any

from framestudio.app_removal import remove_selected_blocks, undo_last_removal
from framestudio.cli import cli_main
from framestudio.model import Project, ProjectValidationError, VisualTransform
from framestudio.persistence import load_project, save_project
from tests.test_editor_ripple_removal import isolated_directory, make_project

APP_REMOVAL_MODULE = "framestudio.app_removal"
CLI_REMOVAL_MODULE = "framestudio.cli_removal"


def _require_callable(test_case: unittest.TestCase, module_name: str, name: str):
    try:
        module = importlib.import_module(module_name)
    except Exception as error:
        test_case.fail(
            f"{module_name} is required for TICKET-111 {name}; "
            f"production wiring is missing: {type(error).__name__}: {error}",
        )
    callback = getattr(module, name, None)
    if not callable(callback):
        test_case.fail(
            f"{module_name}.{name} is the TICKET-111 test contract and must be callable",
        )
    return callback


def _run_cli(*arguments: str):
    stdout = io.StringIO()
    stderr = io.StringIO()
    try:
        result = cli_main(
            list(arguments),
            stdout=stdout,
            stderr=stderr,
        )
    except SystemExit as error:
        raise AssertionError(
            f"CLI removal command is not wired into the public parser: exit {error.code}",
        ) from error
    return result, stdout, stderr


def _track_positions(project) -> dict[str, tuple[int, int, str, bool]]:
    return {
        block.segment_id: (
            block.timeline_start_ticks,
            block.timeline_end_ticks,
            block.track_id,
            block.deleted,
        )
        for block in project.timeline.blocks
    }


def _fresh_legacy_project(root: Path, *, mixed: bool) -> Project:
    metadata = {"duration_seconds": 3.0, "frame_rate": "24/1", "width": 320, "height": 180}
    first = root / "legacy-a.mp4"
    first.write_bytes(b"legacy-a-source")
    if mixed:
        second = root / "legacy-b.mp4"
        second.write_bytes(b"legacy-b-source")
        project = Project.create_multi(((first, metadata), (second, metadata)))
    else:
        project = Project.create(first, metadata)
    project.timeline.split(1.0)
    project.timeline.split(2.0)
    return project


class EditorRemovalControlTests(unittest.TestCase):
    def test_fresh_legacy_removal_preserves_cuts_transform_owner_and_runtime_undo(self):
        for mixed in (False, True):
            with self.subTest(mixed=mixed), isolated_directory() as root:
                project = _fresh_legacy_project(root, mixed=mixed)
                third = project.timeline.segment_items[2]
                transform = VisualTransform(zoom=1.4, offset_x=12.0, offset_y=-8.0)
                project.timeline.set_visual_transform([third.segment_id], transform)
                before = Project.from_dict(project.to_dict()).timeline.to_dict()
                sources = project.sources
                runtime_identity = project.runtime_identity
                middle = project.timeline.segment_items[1]
                receipt = remove_selected_blocks(
                    project, (middle.segment_id,), focused_segment_id=middle.segment_id
                )
                self.assertEqual(project.schema_version, 4)
                self.assertEqual(project.timeline.timing_mode, "legacy-ripple")
                self.assertEqual(receipt.project_runtime_identity, runtime_identity)
                self.assertEqual(receipt.project_runtime_epoch, project.runtime_epoch)
                surviving = project.timeline.find(third.segment_id)
                self.assertEqual(
                    (surviving.source_start_ticks, surviving.timeline_start_ticks),
                    (2_000_000, 1_000_000),
                )
                self.assertEqual(surviving.visual_transform, transform)
                for original, current in zip(sources, project.sources, strict=True):
                    self.assertIs(original, current)
                path = root / "legacy-reopened.framestudio.json"
                save_project(project, path)
                with self.assertRaisesRegex(ProjectValidationError, "stale|unknown|history"):
                    undo_last_removal(load_project(path), receipt)
                undo_last_removal(project, receipt)
                self.assertEqual(project.timeline.to_dict(), before)

    def test_fresh_legacy_remove_all_allows_zero_duration_and_runtime_undo(self):
        for mixed in (False, True):
            with self.subTest(mixed=mixed), isolated_directory() as root:
                project = _fresh_legacy_project(root, mixed=mixed)
                before = Project.from_dict(project.to_dict()).timeline.to_dict()
                receipt = remove_selected_blocks(
                    project, tuple(block.segment_id for block in project.timeline.segment_items)
                )
                self.assertEqual(project.timeline.timing_mode, "legacy-ripple")
                self.assertEqual(project.duration_seconds, 0.0)
                self.assertEqual(project.playhead_seconds, 0.0)
                self.assertEqual(project.timeline.segment_items, ())
                undo_last_removal(project, receipt)
                self.assertEqual(project.timeline.to_dict(), before)

    def test_invalid_fresh_legacy_removal_leaves_original_representation_unchanged(self):
        with isolated_directory() as root:
            project = _fresh_legacy_project(root, mixed=True)
            selected_id = project.timeline.segment_items[0].segment_id
            before = project.to_dict()
            cases = (
                (("unknown",), None),
                ((selected_id, selected_id), None),
                ((selected_id,), "unknown"),
            )
            for selected_ids, focus in cases:
                with self.subTest(selected_ids=selected_ids, focus=focus):
                    with self.assertRaises(ProjectValidationError):
                        remove_selected_blocks(project, selected_ids, focused_segment_id=focus)
                    self.assertEqual(project.to_dict(), before)
                    self.assertIsNone(project.timeline.tracks)

    def test_app_backspace_boundary_ripples_track_locally_and_undoes_exact_state(self):
        remove_selected_blocks = _require_callable(
            self,
            APP_REMOVAL_MODULE,
            "remove_selected_blocks",
        )
        undo_last_removal = _require_callable(
            self,
            APP_REMOVAL_MODULE,
            "undo_last_removal",
        )

        with isolated_directory() as root:
            project = make_project(root)
            before_timeline = project.timeline.to_dict()
            before_positions = _track_positions(project)
            before_a_transform = project.timeline.find("a").visual_transform
            before_revision = project.timeline.revision
            project_path = root / "reopen.framestudio.json"

            receipt = remove_selected_blocks(
                project,
                selected_segment_ids=("b", "d"),
                focused_segment_id="d",
            )

            self.assertEqual(tuple(receipt.removed_segment_ids), ("b", "d"))
            self.assertEqual(receipt.selection_ids, ("b", "d"))
            self.assertEqual(receipt.focused_segment_id, "d")
            self.assertEqual(project.timeline.revision, before_revision + 1)
            self.assertNotIn("b", {block.segment_id for block in project.timeline.blocks})
            self.assertNotIn("d", {block.segment_id for block in project.timeline.blocks})
            self.assertEqual(
                _track_positions(project)["c"],
                (8_000_000, 10_000_000, "track-1", False),
            )
            self.assertEqual(
                _track_positions(project)["e"],
                (16_000_000, 18_000_000, "track-1", False),
            )
            self.assertEqual(
                _track_positions(project)["unaffected"],
                before_positions["unaffected"],
            )
            self.assertEqual(
                project.timeline.find("a").visual_transform,
                before_a_transform,
            )

            save_project(project, project_path)
            reopened = load_project(project_path)
            with self.assertRaisesRegex(ProjectValidationError, "stale|unknown|history"):
                undo_last_removal(reopened, receipt)

            undo_result = undo_last_removal(project, receipt)
            self.assertEqual(undo_result.restored_selection_ids, ("b", "d"))
            self.assertEqual(undo_result.focused_segment_id, "d")
            self.assertEqual(project.timeline.to_dict(), before_timeline)
            self.assertEqual(_track_positions(project), before_positions)
            self.assertEqual(project.timeline.revision, before_revision + 2)

    def test_delete_restore_contract_keeps_blocks_and_differs_from_backspace(self):
        toggle_selected_exclusion = _require_callable(
            self,
            APP_REMOVAL_MODULE,
            "toggle_selected_exclusion",
        )
        remove_selected_blocks = _require_callable(
            self,
            APP_REMOVAL_MODULE,
            "remove_selected_blocks",
        )

        with isolated_directory() as root:
            project = make_project(root)
            before_positions = _track_positions(project)
            before_duration = project.timeline.edited_duration_seconds

            toggle_selected_exclusion(project, selected_segment_ids=("d",))
            self.assertFalse(project.timeline.find("d").deleted)
            restored_positions = _track_positions(project)
            self.assertNotEqual(restored_positions, before_positions)
            self.assertEqual(
                restored_positions["d"][:3],
                before_positions["d"][:3],
            )
            self.assertGreater(project.timeline.edited_duration_seconds, before_duration)

            toggle_selected_exclusion(project, selected_segment_ids=("d",))
            self.assertTrue(project.timeline.find("d").deleted)
            self.assertEqual(_track_positions(project), before_positions)
            self.assertEqual(project.timeline.edited_duration_seconds, before_duration)

            remove_selected_blocks(
                project,
                selected_segment_ids=("b",),
                focused_segment_id="b",
            )
            self.assertNotIn("b", {block.segment_id for block in project.timeline.blocks})
            self.assertEqual(
                _track_positions(project)["c"],
                (8_000_000, 10_000_000, "track-1", False),
            )

    def test_cli_removal_parser_hook_exposes_the_parent_owned_contract(self):
        add_removal_parser = _require_callable(
            self,
            CLI_REMOVAL_MODULE,
            "add_removal_parser",
        )

        parser = argparse.ArgumentParser()
        commands = parser.add_subparsers(dest="command", required=True)
        removal_parser = add_removal_parser(commands)
        self.assertIsNotNone(removal_parser)

        parsed = parser.parse_args(
            [
                "remove",
                "project.framestudio.json",
                "--segment",
                "block-a",
                "--segment",
                "block-b",
                "--output",
                "removed.framestudio.json",
            ],
        )
        self.assertEqual(parsed.command, "remove")
        self.assertEqual(parsed.project, Path("project.framestudio.json"))
        self.assertEqual(parsed.segments, ["block-a", "block-b"])
        self.assertEqual(parsed.output, Path("removed.framestudio.json"))
        self.assertFalse(parsed.full_paths)

    def test_public_cli_remove_is_not_silently_skipped(self):
        with isolated_directory() as root:
            project_path = root / "cli.framestudio.json"
            project = make_project(root)
            save_project(project, project_path)

            result, stdout, stderr = _run_cli(
                "remove",
                str(project_path),
                "--segment",
                "b",
            )

            self.assertEqual(result, 0, stderr.getvalue())
            self.assertEqual(stderr.getvalue(), "")
            payload: dict[str, Any] = json.loads(stdout.getvalue())
            self.assertEqual((payload["ok"], payload["command"]), (True, "remove"))
            self.assertEqual(payload["operation"], {"removed_segment_ids": ["b"]})


if __name__ == "__main__":
    unittest.main()
