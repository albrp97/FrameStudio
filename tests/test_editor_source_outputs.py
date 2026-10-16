from __future__ import annotations

import io
import json
import unittest
from dataclasses import replace
from fractions import Fraction
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import Mock, patch

from framestudio.cli_export import CliError, handle_export
from framestudio.composition import TriplicateGroup, TriplicateInstance, VisualTransform
from framestudio.export import ExportExecutionError, ExportPlan
from framestudio.export_coordinator import (
    ExportBatchResult,
    ExportOutputResult,
    ExportResultState,
)
from framestudio.fps_policy import FrameRatePolicy
from framestudio.media import MediaProbe
from framestudio.model import Project, Segment, SourceReference
from framestudio.model_types import ONE_SOURCE_SCHEMA_VERSION
from framestudio.output_plan import (
    SOURCE_ONLY_OUTPUT_MODE,
    OutputRequest,
    plan_project_outputs,
    set_output_selection,
)
from framestudio.source_outputs import (
    SourceOutputPlan,
    SourceOutputPlanningError,
    derive_standalone_source_project,
    plan_source_output,
    plan_source_outputs,
    render_source_output,
    render_source_outputs,
)
from framestudio.upscale_policy import UpscalePolicy


def _source(
    root: Path,
    source_id: str,
    *,
    frame_rate: str = "24/1",
    width: int = 320,
    height: int = 180,
) -> SourceReference:
    path = root / f"{source_id}.mp4"
    path.write_bytes((source_id + "-fixture").encode("utf-8"))
    return SourceReference.from_path(
        path,
        {
            "duration_seconds": 6.0,
            "width": width,
            "height": height,
            "frame_rate": frame_rate,
            "video_codec": "h264",
            "audio_codec": "aac",
            "audio_stream_present": True,
            "format_name": "mp4",
        },
        source_id=source_id,
    )


def _segment(
    source_id: str,
    segment_id: str,
    start: float,
    end: float,
    *,
    track_id: str,
    timeline_start: float,
    deleted: bool = False,
    zoom: float = 1.0,
    offset_x: float = 0.0,
    offset_y: float = 0.0,
    triplicate: TriplicateGroup | None = None,
) -> Segment:
    transform = VisualTransform(zoom=zoom, offset_x=offset_x, offset_y=offset_y)
    return Segment.create(
        start,
        end,
        segment_id=segment_id,
        block_id=f"block-{segment_id}",
        source_id=source_id,
        timeline_start_seconds=timeline_start,
        timeline_end_seconds=timeline_start + end - start,
        track_id=track_id,
        deleted=deleted,
        color_index=7,
        visual_transform=transform,
        triplicate=triplicate,
    )


def _project(root: Path) -> tuple[Project, tuple[SourceReference, ...]]:
    source_a = _source(root, "source-a", frame_rate="24/1")
    source_b = _source(root, "source-b", frame_rate="60/1", width=640, height=360)
    source_c = _source(root, "source-c", frame_rate="12/1", width=180, height=320)
    project = Project.create_synchronized_multi(
        (source_a, source_b, source_c),
        project_id="ticket-113",
    )
    project.timeline.add_track("track-2")
    triplicate_transform = VisualTransform(zoom=1.25, offset_x=90.0, offset_y=-30.0)
    triplicate = TriplicateGroup(
        "triplicate-1",
        shared_transform=triplicate_transform,
        instances=(
            TriplicateInstance("left"),
            TriplicateInstance("center"),
            TriplicateInstance("right"),
        ),
    )
    project.timeline.replace_track_blocks(
        "track-1",
        (
            _segment(
                "source-a",
                "a-first",
                0.0,
                1.0,
                track_id="track-1",
                timeline_start=0.0,
                zoom=1.2,
                offset_x=20.0,
            ),
            _segment(
                "source-b",
                "b-first",
                0.0,
                0.5,
                track_id="track-1",
                timeline_start=1.0,
            ),
            _segment(
                "source-a",
                "a-copy",
                4.0,
                5.0,
                track_id="track-1",
                timeline_start=1.5,
                zoom=1.25,
                offset_x=90.0,
                offset_y=-30.0,
                triplicate=triplicate,
            ),
            _segment(
                "source-b",
                "b-deleted",
                2.0,
                3.0,
                track_id="track-1",
                timeline_start=2.5,
                deleted=True,
            ),
        ),
    )
    project.timeline.replace_track_blocks(
        "track-2",
        (
            _segment(
                "source-a",
                "a-other-track",
                2.0,
                3.0,
                track_id="track-2",
                timeline_start=0.0,
            ),
            _segment(
                "source-c",
                "c-other-track",
                1.0,
                2.0,
                track_id="track-2",
                timeline_start=1.0,
            ),
        ),
    )
    project.duration_seconds = project.timeline.timeline_duration_seconds
    project.validate()
    return project, (source_a, source_b, source_c)


def _fake_export_plan(project: Project, destination: Path, **_kwargs: object) -> ExportPlan:
    assert project.source is not None
    timeline = project.timeline
    return ExportPlan(
        route="fallback",
        source=Path(project.source.path),
        destination=destination,
        segments=tuple(timeline.segment_items),
        expected_duration_seconds=timeline.timeline_duration_seconds,
        reason="ticket-113 test plan",
    )


def _probe(path: Path) -> MediaProbe:
    return MediaProbe(
        path=path,
        duration_seconds=1.0,
        width=1920,
        height=1080,
        frame_rate="24/1",
        video_codec="h264",
        audio_codec="aac",
        format_name="mp4",
        audio_stream_present=True,
        audio_channels=2,
    )


def _source_request_fixture(
    root: Path,
) -> tuple[Project, tuple[SourceReference, ...], OutputRequest]:
    project, sources = _project(root)
    set_output_selection(project, mode=SOURCE_ONLY_OUTPUT_MODE)
    request = plan_project_outputs(project, root / "edited.mp4").source_outputs[0]
    return project, sources, request


def _planned_source_fixture(
    root: Path,
) -> tuple[Project, tuple[SourceReference, ...], OutputRequest, SourceOutputPlan]:
    project, sources, request = _source_request_fixture(root)
    plan = plan_source_output(
        project,
        request,
        plan_project_export_fn=_fake_export_plan,
    )
    return project, sources, request, plan


class EditorSourceOutputTests(unittest.TestCase):
    def test_derives_compact_legacy_project_without_mutating_original(self):
        with TemporaryDirectory(
            dir=Path(__file__).resolve().parent, prefix=".ticket113-unit-"
        ) as folder:
            root = Path(folder)
            project, sources, request = _source_request_fixture(root)
            before = project.to_dict()

            derived = derive_standalone_source_project(
                project,
                request,
                frame_rate_policy=FrameRatePolicy(
                    choice="custom",
                    target_rate=Fraction(24, 1),
                    custom_rate=Fraction(24, 1),
                    enhancement_enabled=False,
                ),
                upscale_policy=UpscalePolicy(enabled=False),
            )

            self.assertEqual(project.to_dict(), before)
            self.assertEqual(derived.schema_version, ONE_SOURCE_SCHEMA_VERSION)
            self.assertIsNone(derived.timeline.tracks)
            self.assertEqual(derived.source.source_id, "source-a")
            self.assertEqual(
                tuple(source.source_id for source in derived.sources or ()), ("source-a",)
            )
            self.assertEqual(
                tuple(segment.segment_id for segment in derived.timeline.segment_items[:2]),
                ("a-first", "a-copy"),
            )
            self.assertEqual(
                tuple(segment.timeline_start for segment in derived.timeline.segment_items),
                (0.0, 1.0, 2.0, 5.0),
            )
            self.assertEqual(
                tuple(segment.deleted for segment in derived.timeline.segment_items),
                (False, False, True, True),
            )
            self.assertEqual(derived.timeline.timeline_duration_seconds, 6.0)
            self.assertEqual(derived.timeline.segment_items[1].visual_transform.offset_x, 90.0)
            self.assertEqual(
                derived.timeline.segment_items[1].triplicate,
                project.timeline.segment_items[2].triplicate,
            )
            self.assertEqual(
                tuple(Path(source.path) for source in project.sources or ()),
                tuple(Path(source.path) for source in sources),
            )

    def test_planning_filters_fps_and_upscale_to_selected_source(self):
        with TemporaryDirectory(
            dir=Path(__file__).resolve().parent, prefix=".ticket113-unit-"
        ) as folder:
            root = Path(folder)
            project, _sources = _project(root)
            set_output_selection(project, mode=SOURCE_ONLY_OUTPUT_MODE)
            project.set_frame_rate_policy(
                FrameRatePolicy(
                    choice="highest",
                    target_rate=Fraction(60, 1),
                    enhancement_enabled=False,
                ),
            )
            project.set_upscale_policy(UpscalePolicy(enabled=False))
            request = plan_project_outputs(project, root / "edited.mp4").source_outputs[0]
            seen: list[Project] = []

            def planner(derived: Project, destination: Path, **_kwargs: object) -> ExportPlan:
                seen.append(derived)
                return _fake_export_plan(derived, destination)

            plan = plan_source_output(
                project,
                request,
                plan_project_export_fn=planner,
            )

            self.assertEqual(len(seen), 1)
            self.assertEqual(
                tuple(source.source_id for source in seen[0].sources or ()),
                ("source-a",),
            )
            self.assertEqual(plan.frame_rate_policy.choice, "custom")
            self.assertEqual(plan.frame_rate_policy.target_rate, Fraction(60, 1))
            self.assertFalse(plan.upscale_policy.enhancement_enabled)
            self.assertEqual(
                plan.protected_source_paths,
                tuple(Path(source.path) for source in project.sources or ()),
            )

    def test_planning_rejects_original_source_alias_before_planner(self):
        with TemporaryDirectory(
            dir=Path(__file__).resolve().parent, prefix=".ticket113-unit-"
        ) as folder:
            root = Path(folder)
            project, sources, request = _source_request_fixture(root)
            alias = root / "source-c-alias.mp4"
            alias.symlink_to(Path(sources[2].path))
            planner = Mock(side_effect=AssertionError("unsafe request must not be planned"))
            source_hashes = {
                path: path.read_bytes() for path in (Path(source.path) for source in sources)
            }

            with self.assertRaisesRegex(SourceOutputPlanningError, "aliases protected source"):
                plan_source_output(
                    project,
                    replace(request, destination=alias),
                    plan_project_export_fn=planner,
                )

            planner.assert_not_called()
            self.assertEqual(
                {path: path.read_bytes() for path in (Path(source.path) for source in sources)},
                source_hashes,
            )

    def test_planning_rejects_planner_destination_replacement(self):
        with TemporaryDirectory(
            dir=Path(__file__).resolve().parent, prefix=".ticket113-unit-"
        ) as folder:
            root = Path(folder)
            project, sources, request = _source_request_fixture(root)
            source_hashes = {
                path: path.read_bytes() for path in (Path(source.path) for source in sources)
            }

            def planner(derived: Project, destination: Path, **_kwargs: object) -> ExportPlan:
                return replace(
                    _fake_export_plan(derived, destination),
                    destination=Path(sources[2].path),
                )

            with self.assertRaisesRegex(SourceOutputPlanningError, "aliases protected source"):
                plan_source_output(
                    project,
                    request,
                    plan_project_export_fn=planner,
                )

            self.assertEqual(
                {path: path.read_bytes() for path in (Path(source.path) for source in sources)},
                source_hashes,
            )

    def test_render_rejects_replaced_plan_destination_before_execute(self):
        with TemporaryDirectory(
            dir=Path(__file__).resolve().parent, prefix=".ticket113-unit-"
        ) as folder:
            root = Path(folder)
            project, sources, request, plan = _planned_source_fixture(root)
            unsafe_plan = replace(
                plan,
                export_plan=replace(
                    plan.export_plan,
                    destination=Path(sources[2].path),
                ),
            )
            executor = Mock(side_effect=AssertionError("unsafe plan must not execute"))
            source_hashes = {
                path: path.read_bytes() for path in (Path(source.path) for source in sources)
            }

            with self.assertRaisesRegex(SourceOutputPlanningError, "aliases protected source"):
                render_source_output(unsafe_plan, execute_export_fn=executor)

            executor.assert_not_called()
            self.assertEqual(
                {path: path.read_bytes() for path in (Path(source.path) for source in sources)},
                source_hashes,
            )

    def test_render_reports_failure_and_removes_new_unverified_output(self):
        with TemporaryDirectory(
            dir=Path(__file__).resolve().parent, prefix=".ticket113-unit-"
        ) as folder:
            root = Path(folder)
            project, sources, request = _source_request_fixture(root)
            plan = plan_source_output(
                project,
                request,
                frame_rate_policy=FrameRatePolicy(
                    choice="custom",
                    target_rate=Fraction(24, 1),
                    custom_rate=Fraction(24, 1),
                    enhancement_enabled=False,
                ),
                upscale_policy=UpscalePolicy(enabled=False),
                plan_project_export_fn=_fake_export_plan,
            )

            def failing_execute(export_plan: ExportPlan, **_kwargs: object) -> Path:
                export_plan.destination.parent.mkdir(parents=True, exist_ok=True)
                export_plan.destination.write_bytes(b"unverified")
                raise ExportExecutionError("injected output failure")

            result = render_source_output(
                plan,
                execute_export_fn=failing_execute,
                probe_media_fn=Mock(side_effect=AssertionError("probe must not run")),
            )

            self.assertFalse(result.verified)
            self.assertIn("injected output failure", result.error or "")
            self.assertFalse(plan.request.destination.exists())
            self.assertEqual(
                sources[0].path and Path(sources[0].path).read_bytes(), b"source-a-fixture"
            )
            self.assertEqual(
                sources[1].path and Path(sources[1].path).read_bytes(), b"source-b-fixture"
            )
            self.assertEqual(
                sources[2].path and Path(sources[2].path).read_bytes(), b"source-c-fixture"
            )

    def test_source_snapshot_failure_preserves_existing_destination(self):
        with TemporaryDirectory(
            dir=Path(__file__).resolve().parent, prefix=".ticket113-unit-"
        ) as folder:
            root = Path(folder)
            project, sources, request, plan = _planned_source_fixture(root)
            plan.request.destination.parent.mkdir(parents=True, exist_ok=True)
            plan.request.destination.write_bytes(b"existing-output")

            def mutating_execute(export_plan: ExportPlan, **_kwargs: object) -> Path:
                export_plan.destination.parent.mkdir(parents=True, exist_ok=True)
                export_plan.destination.write_bytes(b"new-output")
                Path(sources[2].path).write_bytes(b"changed-during-export")
                return export_plan.destination

            result = render_source_output(
                plan,
                execute_export_fn=mutating_execute,
                probe_media_fn=Mock(side_effect=AssertionError("probe must not run")),
            )

            self.assertFalse(result.verified)
            self.assertIn("changed during export", result.error or "")
            self.assertEqual(plan.request.destination.read_bytes(), b"existing-output")
            self.assertFalse(
                any(root.glob(".*.source-output-stage.mp4")),
            )

    def test_cleanup_failure_is_reported_in_render_result(self):
        with TemporaryDirectory(
            dir=Path(__file__).resolve().parent, prefix=".ticket113-unit-"
        ) as folder:
            root = Path(folder)
            project, _sources, request = _source_request_fixture(root)
            plan = plan_source_output(
                project,
                request,
                plan_project_export_fn=_fake_export_plan,
            )

            def failing_cleanup(export_plan: ExportPlan, **_kwargs: object) -> Path:
                export_plan.destination.parent.mkdir(parents=True, exist_ok=True)
                export_plan.destination.mkdir()
                raise ExportExecutionError("injected output failure")

            result = render_source_output(plan, execute_export_fn=failing_cleanup)

            self.assertFalse(result.verified)
            self.assertIn("injected output failure", result.error or "")
            self.assertIn("could not remove unverified output", result.error or "")

    def test_render_source_batch_plans_all_outputs_and_reports_partial_success(self):
        with TemporaryDirectory(
            dir=Path(__file__).resolve().parent, prefix=".ticket113-unit-"
        ) as folder:
            root = Path(folder)
            project, _sources = _project(root)
            set_output_selection(project, mode=SOURCE_ONLY_OUTPUT_MODE)
            requests = plan_project_outputs(project, root / "edited.mp4").source_outputs
            events: list[str] = []

            def planner(derived: Project, destination: Path, **_kwargs: object) -> ExportPlan:
                events.append(f"plan:{derived.source.source_id}")
                return _fake_export_plan(derived, destination)

            def executor(export_plan: ExportPlan, **_kwargs: object) -> Path:
                events.append(f"execute:{export_plan.source.name}")
                export_plan.destination.parent.mkdir(parents=True, exist_ok=True)
                if export_plan.source.name == "source-b.mp4":
                    raise ExportExecutionError("second output failed")
                export_plan.destination.write_bytes(b"verified")
                return export_plan.destination

            summary = render_source_outputs(
                project,
                requests,
                frame_rate_policy=FrameRatePolicy(
                    choice="custom",
                    target_rate=Fraction(24, 1),
                    custom_rate=Fraction(24, 1),
                    enhancement_enabled=False,
                ),
                upscale_policy=UpscalePolicy(enabled=False),
                plan_project_export_fn=planner,
                execute_export_fn=executor,
                probe_media_fn=lambda path, _ffprobe: _probe(path),
            )

            self.assertEqual(len(summary.plans), 4)
            self.assertEqual(len(summary.results), 4)
            self.assertEqual(summary.verified_count, 3)
            self.assertEqual(summary.failed_count, 1)
            self.assertTrue(summary.partial_success)
            self.assertEqual(
                events[:4], ["plan:source-a", "plan:source-b", "plan:source-a", "plan:source-c"]
            )
            self.assertEqual(
                events[4:],
                [
                    "execute:source-a.mp4",
                    "execute:source-b.mp4",
                    "execute:source-a.mp4",
                    "execute:source-c.mp4",
                ],
            )
            self.assertFalse(summary.results[1].verified)
            self.assertTrue(summary.results[3].verified)
            self.assertEqual(summary.results[1].error, "second output failed")

    def test_cli_partial_success_includes_final_and_source_results(self):
        with TemporaryDirectory(
            dir=Path(__file__).resolve().parent, prefix=".ticket113-unit-"
        ) as folder:
            root = Path(folder)
            project, _sources = _project(root)
            set_output_selection(project, include_final=True, include_source_outputs=True)
            output_plan = plan_project_outputs(project, root / "edited.mp4")
            source_plans = plan_source_outputs(
                project,
                output_plan.source_outputs,
                plan_project_export_fn=_fake_export_plan,
            )
            args = SimpleNamespace(
                project=root / "project.framestudio.json",
                output=root / "edited.mp4",
                command="export",
                full_paths=False,
                plan_only=False,
                resume_mode="fresh",
                ffprobe="ffprobe",
                ffmpeg="ffmpeg",
                frame_rate_policy=None,
                upscale_policy=None,
            )
            for source_verified, final_verified in ((False, True), (True, False)):
                with self.subTest(source_verified=source_verified, final_verified=final_verified):
                    results = tuple(
                        ExportOutputResult(
                            identity=request.identity,
                            destination=request.destination,
                            fingerprint=f"fixture-{index}",
                            state=(
                                ExportResultState.VERIFIED
                                if (
                                    final_verified
                                    if request.output_kind == "final"
                                    else source_verified and index != 2
                                )
                                else ExportResultState.FAILED
                            ),
                        )
                        for index, request in enumerate(output_plan.output_requests)
                    )
                    coordinator = Mock()
                    coordinator.run.return_value = ExportBatchResult(
                        results=results,
                        mode="fresh",
                        complete=False,
                        partial_success=True,
                    )
                    output = io.StringIO()
                    with (
                        patch(
                            "framestudio.cli_export._needs_synchronized_final",
                            return_value=False,
                        ),
                        patch(
                            "framestudio.cli_export.plan_source_outputs",
                            return_value=source_plans,
                        ),
                        patch(
                            "framestudio.cli_export.ExportCoordinator",
                            return_value=coordinator,
                        ) as coordinator_type,
                    ):
                        with self.assertRaises(CliError) as context:
                            handle_export(
                                args,
                                output,
                                progress_output=io.StringIO(),
                                load_project_fn=lambda _path: project,
                                probe_media_fn=Mock(),
                                plan_project_export_fn=_fake_export_plan,
                                execute_export_fn=Mock(),
                            )

                    self.assertTrue(context.exception.details["partial_success"])
                    self.assertFalse(context.exception.details["verified"])
                    messages = [json.loads(line) for line in output.getvalue().splitlines()]
                    self.assertTrue(messages)
                    self.assertTrue(
                        all(message["command"] == "export.progress" for message in messages)
                    )
                    self.assertEqual(
                        [item["state"] for item in context.exception.details["results"]],
                        [result.state.value for result in results],
                    )
                    self.assertEqual(len(context.exception.details["source_outputs"]), 4)
                    self.assertEqual(
                        coordinator_type.call_args.kwargs["output_requests"],
                        output_plan.output_requests,
                    )

    def test_combined_multitrack_routes_to_coordinated_planning_and_execution(self):
        with TemporaryDirectory(
            dir=Path(__file__).resolve().parent, prefix=".ticket113-unit-"
        ) as folder:
            root = Path(folder)
            project, _sources = _project(root)
            set_output_selection(project, include_final=True, include_source_outputs=True)
            args = SimpleNamespace(
                project=root / "project.framestudio.json",
                output=root / "edited.mp4",
                command="export",
                full_paths=False,
                plan_only=False,
                resume_mode="fresh",
            )
            planner = Mock(side_effect=AssertionError("final planning must not run"))
            executor = Mock(side_effect=AssertionError("execution must not run"))

            expected = {"export": {"complete": True}}
            with patch(
                "framestudio.cli_export._handle_coordinated_output_plan",
                return_value=expected,
            ) as coordinated:
                response = handle_export(
                    args,
                    io.StringIO(),
                    progress_output=io.StringIO(),
                    load_project_fn=lambda _path: project,
                    probe_media_fn=Mock(),
                    plan_project_export_fn=planner,
                    execute_export_fn=executor,
                )

            self.assertIs(response, expected)
            self.assertIs(coordinated.call_args.args[1], project)
            output_plan = coordinated.call_args.kwargs["output_plan"]
            self.assertEqual(output_plan.mode, "combined")
            self.assertEqual(len(output_plan.output_requests), 5)
            self.assertIs(
                coordinated.call_args.kwargs["plan_project_export_fn"],
                planner,
            )
            self.assertIs(
                coordinated.call_args.kwargs["execute_export_fn"],
                executor,
            )


if __name__ == "__main__":
    unittest.main()
