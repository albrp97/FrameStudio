from __future__ import annotations

import unittest
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from framestudio.model import Project, Segment, SourceReference
from framestudio.output_plan import (
    COMBINED_OUTPUT_MODE,
    FINAL_ONLY_OUTPUT_MODE,
    SOURCE_ONLY_OUTPUT_MODE,
    OutputPlanError,
    plan_project_outputs,
    resolve_output_selection,
    set_output_selection,
)
from framestudio.persistence import load_project, save_project


def _source(
    root: Path, directory: str, name: str, source_id: str
) -> tuple[Path, dict[str, object]]:
    folder = root / directory
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / name
    path.write_bytes(f"{source_id}-fixture".encode("utf-8"))
    return (
        path,
        {
            "duration_seconds": 12.0,
            "width": 320,
            "height": 180,
            "frame_rate": "24/1",
            "video_codec": "h264",
            "audio_codec": "aac",
            "audio_stream_present": True,
            "format_name": "mp4",
        },
    )


def _block(
    source_id: str,
    segment_id: str,
    start: float,
    end: float,
    *,
    timeline_start: float,
    track_id: str,
    deleted: bool = False,
    zoom: float = 1.0,
) -> Segment:
    from framestudio.composition import VisualTransform

    return Segment.create(
        start,
        end,
        segment_id=segment_id,
        block_id=f"block-{segment_id}",
        source_id=source_id,
        timeline_start_seconds=timeline_start,
        timeline_end_seconds=timeline_start + (end - start),
        track_id=track_id,
        deleted=deleted,
        visual_transform=VisualTransform(zoom=zoom),
    )


def _synchronized_project(root: Path) -> tuple[Project, dict[str, Path]]:
    source_entries = (
        _source(root, "first", "Shared!.mp4", "source-a"),
        _source(root, "second", "Shared?.mp4", "source-b"),
        _source(root, "third", "C:clip.mp4", "source-c"),
        _source(root, "unused", "unused.mp4", "source-unused"),
    )
    project = Project.create_synchronized_multi(
        tuple(
            SourceReference.from_path(path, metadata, source_id=source_id)
            for (path, metadata), source_id in zip(
                source_entries,
                ("source-a", "source-b", "source-c", "source-unused"),
                strict=True,
            )
        ),
        project_id="output-plan",
    )
    project.timeline.add_track("Track:Two")
    project.timeline.add_track("empty-track")
    project.timeline.add_track("excluded-track")
    source_ids = {source.source_id: Path(source.path) for source in project.sources or ()}
    project.timeline.replace_track_blocks(
        "track-1",
        (
            _block(
                "source-a",
                "a-first",
                0.0,
                2.0,
                timeline_start=0.0,
                track_id="track-1",
                zoom=1.2,
            ),
            _block(
                "source-b",
                "b-middle",
                0.0,
                1.0,
                timeline_start=3.0,
                track_id="track-1",
            ),
            _block(
                "source-a",
                "a-second",
                4.0,
                6.0,
                timeline_start=5.0,
                track_id="track-1",
                zoom=1.4,
            ),
            _block(
                "source-b",
                "b-excluded",
                2.0,
                3.0,
                timeline_start=8.0,
                track_id="track-1",
                deleted=True,
            ),
        ),
    )
    project.timeline.replace_track_blocks(
        "Track:Two",
        (
            _block(
                "source-a",
                "a-other-track",
                6.0,
                8.0,
                timeline_start=0.0,
                track_id="Track:Two",
                zoom=1.3,
            ),
            _block(
                "source-c",
                "c-other-track",
                1.0,
                2.0,
                timeline_start=3.0,
                track_id="Track:Two",
            ),
        ),
    )
    project.timeline.replace_track_blocks(
        "excluded-track",
        (
            _block(
                "source-unused",
                "unused-excluded",
                0.0,
                1.0,
                timeline_start=0.0,
                track_id="excluded-track",
                deleted=True,
            ),
        ),
    )
    project.duration_seconds = project.timeline.timeline_duration_seconds
    return project, source_ids


class EditorSourceOutputPlanTests(unittest.TestCase):
    def test_output_selection_defaults_persists_and_rejects_neither(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source_path, metadata = _source(root, "source", "source.mp4", "source")
            project = Project.create(source_path, metadata, project_id="settings")

            self.assertEqual(resolve_output_selection(project).mode, FINAL_ONLY_OUTPUT_MODE)
            set_output_selection(
                project,
                include_final=True,
                include_source_outputs=True,
            )
            self.assertEqual(resolve_output_selection(project).mode, COMBINED_OUTPUT_MODE)

            project_path = root / "settings.framestudio.json"
            save_project(project, project_path)
            restored = load_project(project_path)
            self.assertEqual(resolve_output_selection(restored).mode, COMBINED_OUTPUT_MODE)

            set_output_selection(restored, mode=SOURCE_ONLY_OUTPUT_MODE)
            self.assertEqual(
                resolve_output_selection(restored).to_dict(),
                {
                    "include_final": False,
                    "include_source_outputs": True,
                    "mode": SOURCE_ONLY_OUTPUT_MODE,
                },
            )
            before = dict(restored.output_settings)
            with self.assertRaisesRegex(OutputPlanError, "At least one output"):
                set_output_selection(
                    restored,
                    include_final=False,
                    include_source_outputs=False,
                )
            self.assertEqual(restored.output_settings, before)

    def test_plans_stable_track_source_pairs_in_track_and_timeline_order(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            project, source_paths = _synchronized_project(root)
            set_output_selection(project, mode=SOURCE_ONLY_OUTPUT_MODE)

            plan = plan_project_outputs(project, root / "edited.mp4")

            self.assertEqual(plan.mode, SOURCE_ONLY_OUTPUT_MODE)
            self.assertIsNone(plan.final_request)
            self.assertEqual(
                [(item.track_id, item.source_id) for item in plan.source_outputs],
                [
                    ("track-1", "source-a"),
                    ("track-1", "source-b"),
                    ("Track:Two", "source-a"),
                    ("Track:Two", "source-c"),
                ],
            )
            first, second, third, fourth = plan.source_outputs
            self.assertEqual(first.segment_ids, ("a-first", "a-second"))
            self.assertEqual(second.segment_ids, ("b-middle",))
            self.assertEqual(third.segment_ids, ("a-other-track",))
            self.assertEqual(fourth.segment_ids, ("c-other-track",))
            self.assertEqual(first.expected_duration_seconds, 4.0)
            self.assertEqual(first.framing, "standalone-full-canvas")
            self.assertEqual(first.audio_intent, "normal-source-audio")
            self.assertEqual(first.identity.output_kind, "source")
            self.assertEqual(first.identity.track_id, "track-1")
            self.assertEqual(first.identity.source_id, "source-a")
            self.assertEqual(first.segments[0].visual_transform.zoom, 1.2)
            self.assertEqual(first.segments[1].visual_transform.zoom, 1.4)
            self.assertEqual(first.source_path, source_paths["source-a"])

            self.assertEqual(
                plan.to_dict()["source_outputs"][0]["identity"],
                first.identity.to_dict(),
            )
            self.assertNotIn("unused", {item.source_id for item in plan.source_outputs})
            self.assertNotIn(
                "excluded-track",
                {item.track_id for item in plan.source_outputs},
            )

    def test_destinations_are_safe_collision_free_and_never_source_paths(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            project, source_paths = _synchronized_project(root)
            set_output_selection(project, mode=SOURCE_ONLY_OUTPUT_MODE)
            plan = plan_project_outputs(project, root / "Shared!.mp4")

            destinations = [item.destination for item in plan.source_outputs]
            self.assertEqual(len(destinations), len(set(destinations)))
            self.assertEqual(
                len({destination.parent for destination in destinations}),
                2,
            )
            for destination in destinations:
                self.assertRegex(destination.parent.name, r"^[A-Za-z0-9._-]+$")
                self.assertRegex(destination.name, r"^[A-Za-z0-9._-]+$")
                self.assertNotIn(
                    destination.resolve(), {path.resolve() for path in source_paths.values()}
                )
                self.assertTrue(destination.name.lower().endswith(".mp4"))

            existing_source_root = root / "existing-source-outputs"
            existing_source_root.mkdir()
            directory_plan = plan_project_outputs(project, existing_source_root)
            self.assertEqual(directory_plan.source_output_root, existing_source_root.resolve())

            collision_source = root / "collision" / "track-1" / "source.mp4"
            collision_source.parent.mkdir(parents=True)
            collision_source.write_bytes(b"collision")
            collision_project = Project.create(
                collision_source,
                {
                    "duration_seconds": 1.0,
                    "width": 320,
                    "height": 180,
                    "frame_rate": "24/1",
                    "video_codec": "h264",
                    "audio_codec": None,
                    "format_name": "mp4",
                },
                project_id="collision",
            )
            set_output_selection(collision_project, mode=SOURCE_ONLY_OUTPUT_MODE)
            safe_plan = plan_project_outputs(
                collision_project,
                collision_source.parent.parent / "final.mp4",
                source_output_root=collision_source.parent.parent,
            )
            self.assertNotEqual(safe_plan.source_outputs[0].destination, collision_source)
            with self.assertRaisesRegex(OutputPlanError, "would overwrite source"):
                plan_project_outputs(
                    collision_project,
                    collision_source,
                    mode=FINAL_ONLY_OUTPUT_MODE,
                )
            source_alias = root / "collision" / "source-alias.mp4"
            source_alias.symlink_to(collision_source)
            with self.assertRaisesRegex(OutputPlanError, "would overwrite source"):
                plan_project_outputs(
                    collision_project,
                    source_alias,
                    mode=FINAL_ONLY_OUTPUT_MODE,
                )

    def test_source_reels_use_mp4_names_for_non_mp4_sources(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            for suffix in (".mkv", ".webm"):
                source_path, metadata = _source(
                    root,
                    suffix.removeprefix("."),
                    f"clip{suffix}",
                    f"source{suffix}",
                )
                project = Project.create(source_path, metadata, project_id=f"project{suffix}")
                set_output_selection(project, mode=COMBINED_OUTPUT_MODE)

                plan = plan_project_outputs(project, root / f"edited{suffix}.mp4")

                self.assertEqual(len(plan.source_outputs), 1)
                self.assertEqual(plan.source_outputs[0].destination.name, "clip.mp4")

    def test_replanning_preserves_published_destinations_and_explicit_dotted_root(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            project, _ = _synchronized_project(root)
            set_output_selection(project, mode=SOURCE_ONLY_OUTPUT_MODE)
            source_root = root / "reels.v1"
            source_root.mkdir()

            first = plan_project_outputs(
                project,
                root / "source-plan.mp4",
                source_output_root=source_root,
            )
            for request in first.source_outputs:
                request.destination.parent.mkdir(parents=True, exist_ok=True)
                request.destination.write_bytes(b"published")

            second = plan_project_outputs(
                project,
                root / "source-plan.mp4",
                source_output_root=source_root,
            )

            self.assertEqual(
                [request.destination for request in first.source_outputs],
                [request.destination for request in second.source_outputs],
            )
            self.assertEqual(second.source_output_root, source_root.resolve())

    def test_existing_final_destination_infers_source_root_before_file_validation(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            project, _ = _synchronized_project(root)
            set_output_selection(project, mode=COMBINED_OUTPUT_MODE)
            final_destination = root / "edited.mp4"
            final_destination.write_bytes(b"published-final")

            plan = plan_project_outputs(project, final_destination)

            self.assertEqual(
                plan.source_output_root,
                (root / "edited-sources").resolve(),
            )

    def test_derived_source_root_file_is_rejected(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            project, _ = _synchronized_project(root)
            set_output_selection(project, mode=COMBINED_OUTPUT_MODE)
            derived_root = root / "edited-sources"
            derived_root.write_bytes(b"not-a-directory")

            with self.assertRaisesRegex(OutputPlanError, "source output root must be a directory"):
                plan_project_outputs(project, root / "edited.mp4")

    def test_source_alias_check_reports_io_errors_without_private_paths(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            project, _ = _synchronized_project(root)
            permission_error = PermissionError(13, "Permission denied")

            for mode in (COMBINED_OUTPUT_MODE, SOURCE_ONLY_OUTPUT_MODE):
                set_output_selection(project, mode=mode)
                with patch.object(Path, "samefile", side_effect=permission_error):
                    with self.assertRaises(OutputPlanError) as context:
                        plan_project_outputs(project, root / f"{mode}.mp4")

                message = str(context.exception)
                self.assertTrue(message.startswith("Could not verify source preservation for "))
                self.assertRegex(message, r"\.mp4: Permission denied$")
                self.assertNotIn(str(root), message)

    def test_combined_no_suffix_infers_separate_source_root(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            project, _ = _synchronized_project(root)
            set_output_selection(project, mode=COMBINED_OUTPUT_MODE)

            plan = plan_project_outputs(project, root / "render")

            self.assertIsNotNone(plan.final_request)
            assert plan.final_request is not None
            self.assertEqual(plan.final_request.destination, (root / "render").resolve())
            self.assertEqual(plan.source_output_root, (root / "render-sources").resolve())
            self.assertTrue(
                all(
                    request.destination.is_relative_to(plan.source_output_root)
                    for request in plan.source_outputs
                ),
            )
            self.assertNotEqual(plan.final_request.destination, plan.source_output_root)

    def test_source_only_no_suffix_keeps_literal_folder(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            project, _ = _synchronized_project(root)
            set_output_selection(project, mode=SOURCE_ONLY_OUTPUT_MODE)

            plan = plan_project_outputs(project, root / "reels")

            self.assertIsNone(plan.final_request)
            self.assertEqual(plan.source_output_root, (root / "reels").resolve())

    def test_explicit_source_root_equal_or_nested_under_final_is_rejected(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            project, _ = _synchronized_project(root)
            set_output_selection(project, mode=COMBINED_OUTPUT_MODE)
            final_destination = root / "render.mp4"

            for source_root in (final_destination, final_destination / "nested"):
                with self.assertRaisesRegex(OutputPlanError, "nested under final output"):
                    plan_project_outputs(
                        project,
                        final_destination,
                        source_output_root=source_root,
                    )

    def test_absolute_source_only_planning_does_not_call_unsupported_final_planner(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            project, _ = _synchronized_project(root)
            set_output_selection(project, mode=SOURCE_ONLY_OUTPUT_MODE)

            with patch(
                "framestudio.operations.plan_project_export",
                side_effect=AssertionError("final planner must not run"),
            ):
                plan = plan_project_outputs(project, root / "final.mp4")

            self.assertEqual(len(plan.source_outputs), 4)

    def test_final_destination_cannot_conflict_with_a_reel_or_track_directory(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            project, _ = _synchronized_project(root)
            source_root = root / "reels"
            source_plan = plan_project_outputs(
                project,
                source_root,
                mode=SOURCE_ONLY_OUTPUT_MODE,
            )
            reel = source_plan.source_outputs[0].destination
            for final_destination in (reel, reel.parent, reel / "final.mp4"):
                with self.subTest(final_destination=final_destination):
                    with self.assertRaisesRegex(OutputPlanError, "destinations must not overlap"):
                        plan_project_outputs(
                            project,
                            final_destination,
                            mode=COMBINED_OUTPUT_MODE,
                            source_output_root=source_root,
                        )

    def test_final_request_has_distinct_composition_identity_and_empty_edits_fail(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            project, _ = _synchronized_project(root)
            set_output_selection(project, mode=COMBINED_OUTPUT_MODE)
            plan = plan_project_outputs(project, root / "final.mp4")

            self.assertIsNotNone(plan.final_request)
            assert plan.final_request is not None
            self.assertEqual(plan.final_request.identity.output_kind, "final")
            self.assertEqual(plan.final_request.track_id, None)
            self.assertEqual(plan.final_request.source_id, None)
            self.assertEqual(plan.final_request.framing, "final-composition")
            self.assertEqual(plan.final_request.audio_intent, "mixed-layout-pan")
            self.assertEqual(plan.final_request.expected_duration_seconds, 7.0)

            empty_project, _ = _synchronized_project(root / "empty")
            for track in empty_project.timeline.tracks or ():
                empty_project.timeline.replace_track_blocks(
                    track.track_id,
                    tuple(replace(block, deleted=True) for block in track.blocks),
                )
            set_output_selection(empty_project, mode=SOURCE_ONLY_OUTPUT_MODE)
            with self.assertRaisesRegex(OutputPlanError, "empty edit"):
                plan_project_outputs(empty_project, root / "empty-final.mp4")


if __name__ == "__main__":
    unittest.main()
