from __future__ import annotations

import copy
import hashlib
import importlib
import json
import os
import subprocess
import threading
import unittest
from contextlib import contextmanager
from dataclasses import replace
from fractions import Fraction
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Callable

from framestudio.composition import VisualTransform
from framestudio.export_session import discard_export_session, session_root
from framestudio.fps_policy import FrameRatePolicy
from framestudio.model import Project
from framestudio.output_plan import OutputIdentity, OutputRequest, plan_project_outputs
from framestudio.upscale_policy import UpscalePolicy

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def _require_recovery(test_case: unittest.TestCase):
    try:
        module = importlib.import_module("framestudio.export_coordinator")
    except ModuleNotFoundError as error:
        if error.name == "framestudio.export_coordinator":
            test_case.fail(
                "framestudio.export_coordinator is not implemented; "
                "TICKET-124 unit coverage is intentionally fail-first",
            )
        raise
    for name in (
        "ExportCoordinator",
        "ExportResultState",
        "build_output_fingerprint",
    ):
        test_case.assertTrue(
            hasattr(module, name),
            f"framestudio.export_coordinator.{name} must be public",
        )
    return module


def _output_key(request: OutputRequest) -> str:
    return json.dumps(
        request.identity.to_dict(),
        sort_keys=True,
        separators=(",", ":"),
    )


def _source_fingerprint(path: Path) -> dict[str, object]:
    stat = path.stat()
    return {
        "path": str(path.resolve()),
        "stat": {
            "size_bytes": stat.st_size,
            "modified_time_ns": stat.st_mtime_ns,
            "mode": stat.st_mode,
        },
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def _fingerprint_payload(request: OutputRequest, sources: tuple[Path, ...]) -> dict[str, object]:
    blocks = [
        {
            "track_id": request.track_id,
            "block_id": f"block-{index}",
            "source_id": source_id,
            "copy_index": index,
            "repeat_index": 0,
            "source_start_tick": index * 48000,
            "source_end_tick": (index + 1) * 48000,
            "timeline_start_tick": index * 48000,
            "timeline_end_tick": (index + 1) * 48000,
            "excluded": False,
            "transform": {
                "zoom": 1.0,
                "offset_x": 0.0,
                "offset_y": 0.0,
            },
            "triplicate": None,
        }
        for index, source_id in enumerate(request.source_ids or ("final-source",))
    ]
    return {
        "sources": [_source_fingerprint(path) for path in sources],
        "tracks": [
            {
                "order": 0,
                "track_id": request.track_id or "final-track",
                "sanitized_label": "Track-1",
            }
        ],
        "blocks": blocks,
        "source_audio": {
            "gain_db": 0.0,
            "channel_map": ["FL", "FR"],
            "pan_law": "equal-power-v2",
            "layout_version": "audio-layout-v2",
        },
        "render": {
            "resolved_fps": "24/1",
            "rve_route": "ffmpeg",
            "upscale_enabled": False,
            "upscale_decision": "disabled",
        },
        "output": {
            "mode": request.identity.mode,
            "selection": request.identity.to_dict(),
            "destination": str(request.destination.resolve()),
            "safe_naming": "stable-v1",
        },
        "tools": {
            "ffmpeg": "/usr/bin/ffmpeg",
            "ffprobe": "/usr/bin/ffprobe",
        },
        "versions": {
            "compositor": "t124-video-audio-v1",
            "schema": "project-v6",
        },
    }


def _request(
    root: Path,
    *,
    output_kind: str,
    mode: str,
    track_id: str | None = None,
    source_id: str | None = None,
    source_paths: tuple[Path, ...] = (),
    source_ids: tuple[str, ...] = (),
    name: str,
) -> OutputRequest:
    identity = OutputIdentity(
        mode=mode,
        output_kind=output_kind,
        track_id=track_id,
        source_id=source_id,
        framing="full-canvas" if output_kind == "source" else "final-layout",
        audio_intent="normal-audio",
        render_profile="ffmpeg-v1",
    )
    return OutputRequest(
        identity=identity,
        destination=root / "published" / name,
        segments=(),
        expected_duration_seconds=1.0,
        source_paths=source_paths,
        source_ids=source_ids,
    )


def _coordinator(
    module: Any,
    requests: tuple[OutputRequest, ...],
    root: Path,
    payloads: dict[str, dict[str, object]],
    render_output: Callable[[OutputRequest, Path, threading.Event], Path],
    verify_output: Callable[[OutputRequest, Path, threading.Event], dict[str, object]],
    *,
    on_published: Callable[[OutputRequest, Path], None] | None = None,
    policy_versions: dict[str, object] | None = None,
    protected_source_paths: tuple[Path, ...] = (),
    protected_receipt_paths: tuple[Path, ...] = (),
) -> Any:
    return module.ExportCoordinator(
        output_requests=requests,
        session_destination=root / "batch-output.mp4",
        output_fingerprints={
            _output_key(request): module.build_output_fingerprint(payloads[_output_key(request)])
            for request in requests
        },
        render_output=render_output,
        verify_output=verify_output,
        publication_lock=threading.Lock(),
        on_published=on_published,
        policy_versions=policy_versions,
        protected_source_paths=protected_source_paths,
        protected_receipt_paths=protected_receipt_paths,
    )


class FlexibleOutputRecoveryUnitTests(unittest.TestCase):
    def setUp(self) -> None:
        self.module = _require_recovery(self)

    def _fixture_requests(
        self,
        root: Path,
        *,
        mode: str = "source-only",
    ) -> tuple[tuple[OutputRequest, ...], dict[str, dict[str, object]], tuple[Path, ...]]:
        fixture_root = root / "fixtures"
        fixture_root.mkdir(parents=True)
        source_a = fixture_root / "A.mp4"
        source_b = fixture_root / "B.mp4"
        source_a.write_bytes(b"source-A")
        source_b.write_bytes(b"source-B")
        requests = (
            _request(
                root,
                output_kind="source",
                mode=mode,
                track_id="track-1",
                source_id="source-a",
                source_paths=(source_a,),
                source_ids=("source-a",),
                name="track-1-source-a.mp4",
            ),
            _request(
                root,
                output_kind="source",
                mode=mode,
                track_id="track-1",
                source_id="source-b",
                source_paths=(source_b,),
                source_ids=("source-b",),
                name="track-1-source-b.mp4",
            ),
        )
        payloads = {
            _output_key(request): _fingerprint_payload(request, request.source_paths)
            for request in requests
        }
        return requests, payloads, (source_a, source_b)

    def _successful_callbacks(
        self,
        *,
        calls: list[str],
        content: dict[str, bytes],
        fail_key: str | None = None,
        verify_failure_key: str | None = None,
        cancel_key: str | None = None,
    ) -> tuple[
        Callable[[OutputRequest, Path, threading.Event], Path],
        Callable[[OutputRequest, Path, threading.Event], dict[str, object]],
    ]:
        def render(
            request: OutputRequest,
            candidate: Path,
            event: threading.Event,
        ) -> Path:
            key = _output_key(request)
            calls.append(f"render:{key}")
            if event.is_set():
                raise self.module.ExportCancelled("render cancelled")
            if cancel_key == key:
                raise self.module.ExportCancelled("intentional output cancellation")
            if fail_key == key:
                raise RuntimeError("intentional second-output failure")
            candidate.parent.mkdir(parents=True, exist_ok=True)
            candidate.write_bytes(content[key])
            return candidate

        def verify(
            request: OutputRequest,
            candidate: Path,
            event: threading.Event,
        ) -> dict[str, object]:
            key = _output_key(request)
            calls.append(f"verify:{key}")
            if event.is_set():
                raise self.module.ExportCancelled("verification cancelled")
            if verify_failure_key == key:
                raise RuntimeError("intentional verification failure")
            expected = content[key]
            if candidate.read_bytes() != expected:
                raise RuntimeError("candidate bytes do not match expected proof")
            return {
                "verified": True,
                "bytes": len(expected),
                "sha256": hashlib.sha256(expected).hexdigest(),
            }

        return render, verify

    def _fixture_batch_inputs(
        self,
        root: Path,
        *,
        content_prefix: str = "stable",
        distinct_content: bool = False,
        calls: list[str] | None = None,
        fail_key: str | None = None,
        verify_failure_key: str | None = None,
        cancel_key: str | None = None,
        fail_index: int | None = None,
        verify_failure_index: int | None = None,
        cancel_index: int | None = None,
    ) -> tuple[
        tuple[OutputRequest, ...],
        dict[str, dict[str, object]],
        tuple[Path, ...],
        dict[str, bytes],
        list[str],
        Callable[[OutputRequest, Path, threading.Event], Path],
        Callable[[OutputRequest, Path, threading.Event], dict[str, object]],
    ]:
        requests, payloads, sources = self._fixture_requests(root)
        callback_calls = [] if calls is None else calls
        content = {
            _output_key(request): (
                f"{content_prefix}-{index}" if distinct_content else content_prefix
            ).encode()
            for index, request in enumerate(requests)
        }
        fail_key = _output_key(requests[fail_index]) if fail_index is not None else fail_key
        verify_failure_key = (
            _output_key(requests[verify_failure_index])
            if verify_failure_index is not None
            else verify_failure_key
        )
        cancel_key = _output_key(requests[cancel_index]) if cancel_index is not None else cancel_key
        render, verify = self._successful_callbacks(
            calls=callback_calls,
            content=content,
            fail_key=fail_key,
            verify_failure_key=verify_failure_key,
            cancel_key=cancel_key,
        )
        return requests, payloads, sources, content, callback_calls, render, verify

    @contextmanager
    def _temporary_root(self):
        with TemporaryDirectory(dir=str(REPOSITORY_ROOT / "tests")) as directory:
            yield Path(directory)

    def _resume_fixture(
        self,
        root: Path,
        requests: tuple[OutputRequest, ...],
        payloads: dict[str, dict[str, object]],
        content: dict[str, bytes],
    ) -> tuple[Any, list[str]]:
        calls: list[str] = []
        render, verify = self._successful_callbacks(calls=calls, content=content)
        result = _coordinator(
            self.module,
            requests,
            root,
            payloads,
            render,
            verify,
        ).run(mode="resume", cancel_event=threading.Event())
        return result, calls

    def _assert_receipt_discard_preserves(
        self,
        root: Path,
        protected: Path,
        expected_hash: str,
    ) -> None:
        with self.assertRaises(self.module.ExportSessionError):
            self.module.discard_batch_receipt(
                root / "batch-output.mp4",
                protected_source_paths=(protected,),
            )
        self.assertEqual(
            hashlib.sha256(protected.read_bytes()).hexdigest(),
            expected_hash,
        )

    def _tool_fingerprint_payload(
        self,
        project: Project,
        request: OutputRequest,
        policy: UpscalePolicy,
        tool: Path,
    ) -> dict[str, object]:
        return self.module.build_project_output_fingerprint_payload(
            project,
            request,
            frame_rate_policy=FrameRatePolicy(
                choice="custom",
                target_rate=Fraction(24, 1),
                custom_rate=Fraction(24, 1),
                enhancement_enabled=False,
            ),
            upscale_policy=policy,
            ffmpeg_path=str(tool),
            ffprobe_path=str(tool),
        )

    def test_public_coordinator_has_typed_states_and_result_contract(self):
        state = self.module.ExportResultState
        self.assertEqual(
            {member.value for member in state},
            {"pending", "running", "verified", "failed", "cancelled", "skipped"},
        )
        self.assertTrue(hasattr(self.module, "ExportBatchResult"))
        self.assertTrue(hasattr(self.module, "ExportOutputResult"))
        self.assertTrue(hasattr(self.module, "ExportCancelled"))

    def test_fingerprint_covers_required_mutation_axes_and_not_track_name(self):
        with TemporaryDirectory(dir=str(REPOSITORY_ROOT / "tests")) as temporary_directory:
            root = Path(temporary_directory)
            requests, payloads, sources = self._fixture_requests(root)
            payload = payloads[_output_key(requests[0])]
            baseline = self.module.build_output_fingerprint(payload)
            self.assertNotIn("track_name", json.dumps(payload, sort_keys=True))

            mutations: dict[str, Callable[[dict[str, object]], None]] = {
                "source path": lambda value: value["sources"][0].update(
                    {"path": str(root / "renamed-A.mp4")}
                ),
                "source stat": lambda value: value["sources"][0]["stat"].update(
                    {"size_bytes": 999}
                ),
                "source mtime": lambda value: value["sources"][0]["stat"].update(
                    {"modified_time_ns": 999}
                ),
                "same-size content": lambda value: value["sources"][0].update({"sha256": "0" * 64}),
                "ordered track id": lambda value: value["tracks"].__setitem__(
                    0,
                    {
                        **value["tracks"][0],
                        "track_id": "track-2",
                    },
                ),
                "reversed track order": lambda value: value.update(
                    {
                        "tracks": [
                            *reversed(
                                [
                                    *value["tracks"],
                                    {
                                        "order": 1,
                                        "track_id": "track-2",
                                        "sanitized_label": "Track-2",
                                    },
                                ]
                            )
                        ]
                    }
                ),
                "sanitized label": lambda value: value["tracks"][0].update(
                    {"sanitized_label": "Renamed-Track"}
                ),
                "block id": lambda value: value["blocks"][0].update({"block_id": "changed"}),
                "copy index": lambda value: value["blocks"][0].update({"copy_index": 1}),
                "repeat index": lambda value: value["blocks"][0].update({"repeat_index": 1}),
                "cut ticks": lambda value: value["blocks"][0].update({"source_end_tick": 47000}),
                "timeline ticks": lambda value: value["blocks"][0].update(
                    {"timeline_end_tick": 47000}
                ),
                "exclusion": lambda value: value["blocks"][0].update({"excluded": True}),
                "transform": lambda value: value["blocks"][0]["transform"].update({"zoom": 1.25}),
                "triplicate": lambda value: value["blocks"][0].update(
                    {"triplicate": {"group_id": "triplicate-1"}}
                ),
                "audio policy": lambda value: value["source_audio"].update({"pan_law": "legacy"}),
                "audio gain": lambda value: value["source_audio"].update({"gain_db": 3.0}),
                "audio channel map": lambda value: value["source_audio"].update(
                    {"channel_map": ["FR", "FL"]}
                ),
                "audio layout version": lambda value: value["source_audio"].update(
                    {"layout_version": "audio-layout-v3"}
                ),
                "explicit audio layout": lambda value: value["source_audio"].update(
                    {"layout": "5.1"}
                ),
                "explicit pan law": lambda value: value["source_audio"].update(
                    {"pan_law": "equal-power-v3"}
                ),
                "fps route": lambda value: value["render"].update({"resolved_fps": "60/1"}),
                "rve route": lambda value: value["render"].update({"rve_route": "rve"}),
                "upscale enabled": lambda value: value["render"].update({"upscale_enabled": True}),
                "upscale decision": lambda value: value["render"].update(
                    {"upscale_decision": "rve"}
                ),
                "output selection": lambda value: value["output"].update({"mode": "combined"}),
                "destination naming": lambda value: value["output"].update(
                    {"safe_naming": "changed"}
                ),
                "destination": lambda value: value["output"].update(
                    {"destination": str(root / "other-output.mp4")}
                ),
                "tool identity": lambda value: value["tools"].update({"ffmpeg": "/other/ffmpeg"}),
                "ffprobe identity": lambda value: value["tools"].update(
                    {"ffprobe": "/other/ffprobe"}
                ),
                "compositor version": lambda value: value["versions"].update(
                    {"compositor": "t124-video-audio-v2"}
                ),
                "schema version": lambda value: value["versions"].update({"schema": "project-v7"}),
            }
            for label, mutate in mutations.items():
                with self.subTest(label=label):
                    changed = copy.deepcopy(payload)
                    mutate(changed)
                    self.assertNotEqual(
                        baseline,
                        self.module.build_output_fingerprint(changed),
                    )
            original_stat = sources[0].stat()
            sources[0].write_bytes(b"X" * original_stat.st_size)
            os.utime(
                sources[0],
                ns=(original_stat.st_atime_ns, original_stat.st_mtime_ns),
            )
            changed_source_payload = copy.deepcopy(payload)
            changed_source_payload["sources"][0] = _source_fingerprint(sources[0])
            self.assertNotEqual(
                baseline,
                self.module.build_output_fingerprint(changed_source_payload),
            )

    def test_cancellation_after_first_publication_leaves_next_output_pending(self):
        with TemporaryDirectory(dir=str(REPOSITORY_ROOT / "tests")) as temporary_directory:
            root = Path(temporary_directory)
            requests, payloads, _, content, calls, render, verify = self._fixture_batch_inputs(
                root,
                content_prefix="published",
                distinct_content=True,
            )
            cancel_event = threading.Event()

            def after_published(request: OutputRequest, _destination: Path) -> None:
                if request == requests[0]:
                    cancel_event.set()

            result = _coordinator(
                self.module,
                requests,
                root,
                payloads,
                render,
                verify,
                on_published=after_published,
            ).run(mode="fresh", cancel_event=cancel_event)

            self.assertEqual(result.results[0].state, self.module.ExportResultState.VERIFIED)
            self.assertEqual(result.results[1].state, self.module.ExportResultState.PENDING)
            self.assertTrue(requests[0].destination.is_file())
            self.assertEqual(
                requests[0].destination.read_bytes(),
                content[_output_key(requests[0])],
            )
            self.assertFalse(requests[1].destination.exists())
            self.assertFalse(any(call == f"render:{_output_key(requests[1])}" for call in calls))

    def test_production_fingerprint_builder_normalizes_fresh_legacy_projects(self):
        with TemporaryDirectory(dir=str(REPOSITORY_ROOT / "tests")) as temporary_directory:
            root = Path(temporary_directory)
            source = root / "legacy-source.mp4"
            source.write_bytes(b"legacy-source")
            metadata = {
                "duration_seconds": 2.0,
                "width": 320,
                "height": 180,
                "frame_rate": "24/1",
                "video_codec": "h264",
                "audio_codec": "aac",
                "audio_stream_present": True,
            }
            for schema_version in (1, 2):
                with self.subTest(schema_version=schema_version):
                    project = Project.create(
                        source,
                        metadata,
                        project_id=f"legacy-{schema_version}",
                    )
                    project.schema_version = schema_version
                    request = plan_project_outputs(
                        project,
                        root / f"legacy-{schema_version}.mp4",
                    ).output_requests[0]
                    payload = self.module.build_project_output_fingerprint_payload(
                        project,
                        request,
                        upscale_policy=UpscalePolicy(enabled=False),
                    )
                    self.assertEqual(payload["project"]["schema_version"], 4)
                    self.assertEqual(len(payload["blocks"]), 1)
                    self.assertEqual(payload["blocks"][0]["source_id"], project.source.source_id)
                    self.assertTrue(payload["sources"][0]["sha256"])

    def test_production_builder_changes_for_real_project_edits_and_tool_identity(self):
        from tests.test_editor_source_outputs import _project

        with TemporaryDirectory(dir=str(REPOSITORY_ROOT / "tests")) as temporary_directory:
            root = Path(temporary_directory)
            project, sources = _project(Path(temporary_directory))
            request = plan_project_outputs(project, root / "edited.mp4").output_requests[0]
            policy = UpscalePolicy(enabled=False)

            def fingerprint(candidate: Project) -> str:
                return self.module.build_output_fingerprint(
                    self.module.build_project_output_fingerprint_payload(
                        candidate,
                        request,
                        upscale_policy=policy,
                    )
                )

            baseline = fingerprint(project)
            edited = copy.deepcopy(project)
            edited.timeline.set_deleted("a-first", True)
            edited.timeline.set_visual_transform(
                ("a-copy",),
                VisualTransform(zoom=1.4, offset_x=42.0, offset_y=-12.0),
            )
            edited.timeline.set_active_track("track-2")
            edited.output_settings["layout_version"] = "layout-v2"
            edited.source_settings[edited.source.source_id]["gain_db"] = 3.0
            self.assertNotEqual(baseline, fingerprint(edited))

            reordered = copy.deepcopy(project)
            reordered.timeline._replace_tracks(
                tuple(reversed(reordered.timeline.tracks)),
                active_track_id="track-2",
            )
            self.assertNotEqual(baseline, fingerprint(reordered))

            cut = copy.deepcopy(project)
            cut.timeline.split_block("a-first", 0.5)
            self.assertNotEqual(baseline, fingerprint(cut))

            copied = copy.deepcopy(project)
            copied_blocks = copied.timeline.copy_blocks(("a-first",))
            copied.timeline.paste_blocks(
                copied_blocks,
                at_seconds=3.5,
                target_track_id="track-2",
            )
            self.assertNotEqual(baseline, fingerprint(copied))

            panlaw_changed = copy.deepcopy(project)
            panlaw_changed.source_settings[panlaw_changed.source.source_id]["audio"]["pan_law"] = (
                "pan-law-v3"
            )
            self.assertNotEqual(baseline, fingerprint(panlaw_changed))

            layout_changed = copy.deepcopy(project)
            layout_changed.output_settings["layout_version"] = "layout-v3"
            self.assertNotEqual(baseline, fingerprint(layout_changed))

            fps_changed = self.module.build_project_output_fingerprint_payload(
                project,
                request,
                frame_rate_policy=FrameRatePolicy(
                    choice="custom",
                    target_rate=Fraction(30, 1),
                    custom_rate=Fraction(30, 1),
                    enhancement_enabled=True,
                    backend="rve-test",
                ),
                upscale_policy=policy,
            )
            self.assertNotEqual(
                self.module.build_output_fingerprint(fps_changed),
                baseline,
            )

            upscale_changed = self.module.build_project_output_fingerprint_payload(
                project,
                request,
                frame_rate_policy=FrameRatePolicy(
                    choice="custom",
                    target_rate=Fraction(24, 1),
                    custom_rate=Fraction(24, 1),
                    enhancement_enabled=False,
                ),
                upscale_policy=UpscalePolicy(
                    enabled=True,
                    model="test-model",
                    backend="test-backend",
                ),
            )
            self.assertNotEqual(
                self.module.build_output_fingerprint(upscale_changed),
                baseline,
            )

            source_path = Path(sources[0].path)
            original_stat = source_path.stat()
            source_path.write_bytes(b"Z" * original_stat.st_size)
            os.utime(
                source_path,
                ns=(original_stat.st_atime_ns, original_stat.st_mtime_ns),
            )
            self.assertNotEqual(baseline, fingerprint(project))

            tool = root / "tool-identity"
            tool.write_bytes(b"tool-v1")
            tool_payload = self._tool_fingerprint_payload(
                project,
                request,
                policy,
                tool,
            )
            tool.write_bytes(b"tool-v2")
            changed_tools = self._tool_fingerprint_payload(
                project,
                request,
                policy,
                tool,
            )
            self.assertNotEqual(
                self.module.build_output_fingerprint(tool_payload),
                self.module.build_output_fingerprint(changed_tools),
            )

    def test_production_fingerprint_normalizes_ui_and_cli_policy_representations(self):
        from framestudio.fps_policy import policy_source_metadata, resolved_from_policy
        from framestudio.output_plan import active_export_sources
        from framestudio.upscale_policy import resolved_from_policy as resolve_upscale
        from tests.test_editor_source_outputs import _project

        with TemporaryDirectory(dir=str(REPOSITORY_ROOT / "tests")) as temporary_directory:
            root = Path(temporary_directory)
            project, _ = _project(root)
            request = plan_project_outputs(project, root / "edited.mp4").output_requests[0]
            metadata = policy_source_metadata(active_export_sources(project))
            fps = project.get_frame_rate_policy()
            upscale = project.get_upscale_policy()
            resolved_fps = resolved_from_policy(metadata, fps)
            resolved_upscale = resolve_upscale(metadata, upscale)

            def payload(frame_rate_policy, upscale_policy):
                return self.module.build_project_output_fingerprint_payload(
                    project,
                    request,
                    frame_rate_policy=frame_rate_policy,
                    upscale_policy=upscale_policy,
                    tool_identities={},
                )

            legacy_cli = payload(resolved_fps, resolved_upscale)
            self.assertEqual(legacy_cli["render"]["resolved_fps"], resolved_fps.to_dict())
            self.assertEqual(legacy_cli["render"]["upscale"], resolved_upscale.to_dict())
            self.assertIsNone(legacy_cli["render"]["rve_route"])
            for label, selected_fps, selected_upscale in (
                ("UI", fps, upscale),
                ("mapping", fps.to_dict(), upscale.to_dict()),
                ("resolved mapping", resolved_fps.to_dict(), resolved_upscale.to_dict()),
                ("defaults", None, None),
            ):
                with self.subTest(representation=label):
                    self.assertEqual(payload(selected_fps, selected_upscale), legacy_cli)

    def test_canonical_fingerprint_rejects_unsupported_and_nonfinite_values(self):
        with self.assertRaises(TypeError):
            self.module.build_output_fingerprint({"unsupported": object()})
        with self.assertRaises(ValueError):
            self.module.build_output_fingerprint({"nonfinite": float("nan")})

    def test_post_publication_bookkeeping_failure_keeps_verified_output(self):
        with self._temporary_root() as root:
            requests, payloads, _, content, _, render, verify = self._fixture_batch_inputs(
                root,
                content_prefix="published",
                distinct_content=True,
            )

            def fail_after_publication(_request: OutputRequest, _destination: Path) -> None:
                raise RuntimeError("injected post-publication failure")

            result = _coordinator(
                self.module,
                requests,
                root,
                payloads,
                render,
                verify,
                on_published=fail_after_publication,
            ).run(mode="fresh", cancel_event=threading.Event())

            self.assertFalse(result.complete)
            self.assertTrue(result.partial_success)
            self.assertEqual(result.results[0].state, self.module.ExportResultState.VERIFIED)
            self.assertTrue(result.results[0].published)
            self.assertEqual(
                requests[0].destination.read_bytes(),
                content[_output_key(requests[0])],
            )
            self.assertEqual(result.error["code"], "bookkeeping")

    def test_post_replace_manifest_failure_keeps_verified_output_and_stops_siblings(self):
        with self._temporary_root() as root:
            requests, payloads, _, content, _, render, verify = self._fixture_batch_inputs(
                root,
                content_prefix="published",
                distinct_content=True,
            )
            coordinator = _coordinator(
                self.module,
                requests,
                root,
                payloads,
                render,
                verify,
            )
            original_save = coordinator._save_batch_manifest
            save_calls = 0

            def fail_after_first_publication(
                session: Any,
                results: Any,
                *,
                mode: str,
                error: Any = None,
            ) -> None:
                nonlocal save_calls
                save_calls += 1
                if save_calls == 3:
                    raise RuntimeError("injected manifest save failure after replace")
                original_save(session, results, mode=mode, error=error)

            coordinator._save_batch_manifest = fail_after_first_publication
            result = coordinator.run(mode="fresh", cancel_event=threading.Event())

            self.assertFalse(result.complete)
            self.assertTrue(result.partial_success)
            self.assertEqual(result.error["code"], "bookkeeping")
            self.assertEqual(result.results[0].state, self.module.ExportResultState.VERIFIED)
            self.assertTrue(result.results[0].published)
            self.assertEqual(result.results[1].state, self.module.ExportResultState.PENDING)
            self.assertEqual(
                requests[0].destination.read_bytes(),
                content[_output_key(requests[0])],
            )
            self.assertFalse(requests[1].destination.exists())
            manifest = json.loads(
                (session_root(root / "batch-output.mp4") / "manifest.json").read_text(
                    encoding="utf-8",
                ),
            )
            first_record = manifest["outputs"][_output_key(requests[0])]
            self.assertEqual(first_record["state"], "verified")
            self.assertEqual(
                first_record["published_hash"],
                hashlib.sha256(requests[0].destination.read_bytes()).hexdigest(),
            )

    def test_batch_policy_version_mismatch_is_explicitly_stale(self):
        with TemporaryDirectory(dir=str(REPOSITORY_ROOT / "tests")) as temporary_directory:
            root = Path(temporary_directory)
            requests, payloads, _ = self._fixture_requests(root)
            content = {_output_key(request): b"stable" for request in requests}
            render, verify = self._successful_callbacks(calls=[], content=content)
            first = _coordinator(
                self.module,
                requests,
                root,
                payloads,
                render,
                verify,
                policy_versions={"fps": 1, "upscale": 1},
            ).run(mode="fresh", cancel_event=threading.Event())
            self.assertTrue(first.complete)
            resumed = _coordinator(
                self.module,
                requests,
                root,
                payloads,
                render,
                verify,
                policy_versions={"fps": 2, "upscale": 1},
            ).run(mode="resume", cancel_event=threading.Event())
            self.assertTrue(resumed.stale)
            self.assertEqual(resumed.error["code"], "stale_session")

    def test_receipt_proof_mismatch_is_stale_and_source_alias_is_protected(self):
        with TemporaryDirectory(dir=str(REPOSITORY_ROOT / "tests")) as temporary_directory:
            root = Path(temporary_directory)
            requests, payloads, sources = self._fixture_requests(root)
            content = {_output_key(request): b"stable" for request in requests}
            render, verify = self._successful_callbacks(calls=[], content=content)
            coordinator = _coordinator(
                self.module,
                requests,
                root,
                payloads,
                render,
                verify,
            )
            first = coordinator.run(mode="fresh", cancel_event=threading.Event())
            self.assertTrue(first.complete)
            receipt = root / ".batch-output.mp4.framestudio-batch-receipt.json"
            value = json.loads(receipt.read_text(encoding="utf-8"))
            value["tools"] = {"ffmpeg": {"sha256": "changed"}}
            receipt.write_text(json.dumps(value), encoding="utf-8")
            resumed = _coordinator(
                self.module,
                requests,
                root,
                payloads,
                render,
                verify,
            ).run(mode="resume", cancel_event=threading.Event())
            self.assertTrue(resumed.stale)
            self.assertEqual(resumed.error["code"], "stale_session")

            protected_request = replace(
                requests[0],
                destination=sources[0],
            )
            with self.assertRaises(self.module.ExportSessionError):
                self.module.ExportCoordinator(
                    output_requests=(protected_request,),
                    session_destination=root / "protected.mp4",
                    output_fingerprints={
                        _output_key(protected_request): "fingerprint",
                    },
                    render_output=render,
                    verify_output=verify,
                    publication_lock=threading.Lock(),
                    protected_source_paths=(sources[0],),
                )

            receipt_path = root / ".batch-output.mp4.framestudio-batch-receipt.json"
            receipt_request = replace(requests[0], destination=receipt_path)
            with self.assertRaises(self.module.ExportSessionError):
                self.module.ExportCoordinator(
                    output_requests=(receipt_request,),
                    session_destination=root / "batch-output.mp4",
                    output_fingerprints={
                        _output_key(receipt_request): "fingerprint",
                    },
                    render_output=render,
                    verify_output=verify,
                    publication_lock=threading.Lock(),
                )

            source = root / "project-source.mp4"
            source.write_bytes(b"project-source")
            project = Project.create(
                source,
                {
                    "duration_seconds": 1.0,
                    "width": 320,
                    "height": 180,
                    "frame_rate": "24/1",
                    "video_codec": "h264",
                    "audio_codec": "aac",
                    "audio_stream_present": True,
                },
                project_id="protected-project",
            )
            project_path = root / "project.framestudio.json"
            planned_output = root / "planned.mp4"
            protected = self.module.protected_receipt_paths(
                project,
                project_path=project_path,
                planned_outputs=(planned_output,),
            )
            self.assertIn(project_path.resolve(), protected)
            self.assertIn(planned_output.resolve(), protected)
            self.assertIn(source.resolve(), protected)

    def test_receipt_write_and_discard_protect_project_and_output_aliases(self):
        with TemporaryDirectory(dir=str(REPOSITORY_ROOT / "tests")) as temporary_directory:
            root = Path(temporary_directory)
            requests, payloads, sources = self._fixture_requests(root)
            content = {_output_key(request): b"stable" for request in requests}
            render, verify = self._successful_callbacks(calls=[], content=content)
            receipt = root / ".batch-output.mp4.framestudio-batch-receipt.json"

            receipt.write_bytes(b"project-file")
            project_hash = hashlib.sha256(receipt.read_bytes()).hexdigest()
            with self.assertRaises(self.module.ExportSessionError):
                _coordinator(
                    self.module,
                    requests,
                    root,
                    payloads,
                    render,
                    verify,
                    protected_receipt_paths=(receipt,),
                )
            self._assert_receipt_discard_preserves(root, receipt, project_hash)
            receipt.unlink()

            planned = requests[0].destination
            planned.parent.mkdir(parents=True, exist_ok=True)
            planned.write_bytes(b"planned-output")
            planned_hash = hashlib.sha256(planned.read_bytes()).hexdigest()
            os.link(planned, receipt)
            with self.assertRaises(self.module.ExportSessionError):
                _coordinator(
                    self.module,
                    requests,
                    root,
                    payloads,
                    render,
                    verify,
                )
            self._assert_receipt_discard_preserves(root, planned, planned_hash)
            receipt.unlink()

            temporary = receipt.with_name(f".{receipt.name}.tmp")
            temporary.symlink_to(planned)
            with self.assertRaises(self.module.ExportSessionError):
                _coordinator(
                    self.module,
                    requests,
                    root,
                    payloads,
                    render,
                    verify,
                )
            self.assertEqual(
                hashlib.sha256(planned.read_bytes()).hexdigest(),
                planned_hash,
            )
            temporary.unlink()

            receipt.symlink_to(planned)
            self._assert_receipt_discard_preserves(root, planned, planned_hash)
            receipt.unlink()

            temporary.symlink_to(sources[0])
            source_hash = hashlib.sha256(sources[0].read_bytes()).hexdigest()
            self._assert_receipt_discard_preserves(root, sources[0], source_hash)
            temporary.unlink()

    def test_second_output_failure_keeps_verified_sibling_and_all_identity_results(self):
        with TemporaryDirectory(dir=str(REPOSITORY_ROOT / "tests")) as temporary_directory:
            root = Path(temporary_directory)
            requests, payloads, _, content, calls, render, verify = self._fixture_batch_inputs(
                root,
                content_prefix="published",
                distinct_content=True,
                fail_index=1,
            )
            result = _coordinator(
                self.module,
                requests,
                root,
                payloads,
                render,
                verify,
            ).run(mode="fresh", cancel_event=threading.Event())

            self.assertTrue(result.partial_success)
            self.assertFalse(result.complete)
            self.assertEqual(len(result.results), 2)
            self.assertEqual(result.results[0].state, self.module.ExportResultState.VERIFIED)
            self.assertEqual(result.results[1].state, self.module.ExportResultState.FAILED)
            self.assertEqual(
                tuple(item.identity.to_dict() for item in result.results),
                tuple(request.identity.to_dict() for request in requests),
            )
            self.assertEqual(
                requests[0].destination.read_bytes(), content[_output_key(requests[0])]
            )
            self.assertFalse(requests[1].destination.exists())
            self.assertTrue(session_root(root / "batch-output.mp4").is_dir())

            manifest = json.loads(
                (session_root(root / "batch-output.mp4") / "manifest.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(
                manifest["outputs"][_output_key(requests[0])]["state"],
                "verified",
            )
            self.assertEqual(
                manifest["outputs"][_output_key(requests[1])]["state"],
                "failed",
            )
            self.assertEqual(
                set(manifest["outputs"]),
                {_output_key(request) for request in requests},
            )

    def test_verification_failure_preserves_existing_destination_and_published_siblings(self):
        with TemporaryDirectory(dir=str(REPOSITORY_ROOT / "tests")) as temporary_directory:
            root = Path(temporary_directory)
            requests, payloads, _ = self._fixture_requests(root)
            requests[1].destination.parent.mkdir(parents=True)
            requests[1].destination.write_bytes(b"old-destination")
            content = {
                _output_key(request): f"new-{index}".encode()
                for index, request in enumerate(requests)
            }
            calls: list[str] = []
            render, verify = self._successful_callbacks(
                calls=calls,
                content=content,
                verify_failure_key=_output_key(requests[1]),
            )
            result = _coordinator(
                self.module,
                requests,
                root,
                payloads,
                render,
                verify,
            ).run(mode="fresh", cancel_event=threading.Event())

            self.assertEqual(result.results[0].state, self.module.ExportResultState.VERIFIED)
            self.assertEqual(result.results[1].state, self.module.ExportResultState.FAILED)
            self.assertEqual(requests[1].destination.read_bytes(), b"old-destination")
            self.assertEqual(
                requests[0].destination.read_bytes(), content[_output_key(requests[0])]
            )
            self.assertFalse(any(item.startswith("publish-failed") for item in calls))

    def test_cancel_during_running_child_propagates_and_publishes_nothing(self):
        with TemporaryDirectory(dir=str(REPOSITORY_ROOT / "tests")) as temporary_directory:
            root = Path(temporary_directory)
            requests, payloads, _ = self._fixture_requests(root)
            calls: list[str] = []
            child_started = threading.Event()
            child_finished = threading.Event()
            child_holder: dict[str, subprocess.Popen[bytes]] = {}

            def render(
                request: OutputRequest,
                candidate: Path,
                event: threading.Event,
            ) -> Path:
                calls.append(f"render:{_output_key(request)}")
                child = subprocess.Popen(
                    ["python3", "-c", "import time; time.sleep(30)"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                child_holder["process"] = child
                child_started.set()
                while child.poll() is None:
                    if event.wait(0.01):
                        child.terminate()
                        child.wait(timeout=5)
                        child_finished.set()
                        raise RuntimeError("child stopped after cancellation")
                raise RuntimeError("child ended without cancellation")

            def verify(
                request: OutputRequest,
                candidate: Path,
                event: threading.Event,
            ) -> dict[str, object]:
                raise AssertionError("verification must not run after child cancellation")

            cancel_event = threading.Event()
            result_holder: dict[str, Any] = {}

            def run() -> None:
                result_holder["result"] = _coordinator(
                    self.module,
                    requests,
                    root,
                    payloads,
                    render,
                    verify,
                ).run(mode="fresh", cancel_event=cancel_event)

            worker = threading.Thread(target=run)
            worker.start()
            self.assertTrue(child_started.wait(timeout=10))
            cancel_event.set()
            worker.join(timeout=15)
            self.assertFalse(worker.is_alive())
            self.assertTrue(child_finished.is_set())
            self.assertIsNotNone(child_holder["process"].poll())
            result = result_holder["result"]
            self.assertEqual(result.results[0].state, self.module.ExportResultState.CANCELLED)
            self.assertFalse(requests[0].destination.exists())
            self.assertEqual(
                result.results[1].state,
                self.module.ExportResultState.PENDING,
            )

    def test_matching_verified_output_is_skipped_after_real_reverification_on_resume(self):
        with self._temporary_root() as root:
            (
                requests,
                payloads,
                _,
                content,
                _,
                first_render,
                first_verify,
            ) = self._fixture_batch_inputs(
                root,
                content_prefix="stable",
                distinct_content=True,
                cancel_index=1,
            )
            cancel_event = threading.Event()
            first = _coordinator(
                self.module,
                requests,
                root,
                payloads,
                first_render,
                first_verify,
            ).run(mode="fresh", cancel_event=cancel_event)
            self.assertEqual(first.results[0].state, self.module.ExportResultState.VERIFIED)
            self.assertEqual(first.results[1].state, self.module.ExportResultState.CANCELLED)
            original_bytes = requests[0].destination.read_bytes()

            resumed, resume_calls = self._resume_fixture(
                root,
                requests,
                payloads,
                content,
            )

            self.assertEqual(resumed.results[0].state, self.module.ExportResultState.SKIPPED)
            self.assertEqual(resumed.results[1].state, self.module.ExportResultState.VERIFIED)
            self.assertFalse(
                any(call == f"render:{_output_key(requests[0])}" for call in resume_calls)
            )
            self.assertIn(f"verify:{_output_key(requests[0])}", resume_calls)
            self.assertEqual(requests[0].destination.read_bytes(), original_bytes)
            self.assertTrue(resumed.complete)

    def test_invalid_completed_output_is_pending_and_renders_again(self):
        with self._temporary_root() as root:
            (
                requests,
                payloads,
                _,
                content,
                _,
                first_render,
                first_verify,
            ) = self._fixture_batch_inputs(
                root,
                content_prefix="valid",
                distinct_content=True,
            )
            first = _coordinator(
                self.module,
                requests,
                root,
                payloads,
                first_render,
                first_verify,
            ).run(mode="fresh", cancel_event=threading.Event())
            self.assertTrue(first.complete)
            requests[0].destination.write_bytes(b"same-size")

            resumed, resume_calls = self._resume_fixture(
                root,
                requests,
                payloads,
                content,
            )

            self.assertEqual(resumed.results[0].state, self.module.ExportResultState.VERIFIED)
            self.assertTrue(any(_output_key(requests[0]) in call for call in resume_calls))
            self.assertEqual(
                requests[0].destination.read_bytes(), content[_output_key(requests[0])]
            )

    def test_resume_request_mismatch_is_explicit_stale_and_does_not_reuse_output(self):
        with TemporaryDirectory(dir=str(REPOSITORY_ROOT / "tests")) as temporary_directory:
            root = Path(temporary_directory)
            requests, payloads, _ = self._fixture_requests(root)
            content = {_output_key(request): b"stable" for request in requests}
            calls: list[str] = []
            render, verify = self._successful_callbacks(calls=calls, content=content)
            _coordinator(
                self.module,
                requests,
                root,
                payloads,
                render,
                verify,
            ).run(mode="fresh", cancel_event=threading.Event())

            changed_payloads = copy.deepcopy(payloads)
            changed_payloads[_output_key(requests[0])]["output"]["safe_naming"] = "changed"
            resume_render, resume_verify = self._successful_callbacks(
                calls=[],
                content=content,
            )
            result = _coordinator(
                self.module,
                requests,
                root,
                changed_payloads,
                resume_render,
                resume_verify,
            ).run(mode="resume", cancel_event=threading.Event())
            self.assertTrue(result.stale)
            self.assertEqual(result.error["code"], "stale_session")
            self.assertTrue(requests[0].destination.is_file())

    def test_restart_and_discard_clean_owned_session_only(self):
        with TemporaryDirectory(dir=str(REPOSITORY_ROOT / "tests")) as temporary_directory:
            root = Path(temporary_directory)
            requests, payloads, sources = self._fixture_requests(root)
            requests[0].destination.parent.mkdir(parents=True)
            requests[0].destination.write_bytes(b"published-before-restart")
            content = {_output_key(request): b"new-content" for request in requests}
            calls: list[str] = []
            render, verify = self._successful_callbacks(
                calls=calls,
                content=content,
                fail_key=_output_key(requests[0]),
            )
            restarted = _coordinator(
                self.module,
                requests,
                root,
                payloads,
                render,
                verify,
            ).run(mode="restart", cancel_event=threading.Event())
            self.assertEqual(restarted.results[0].state, self.module.ExportResultState.FAILED)
            self.assertEqual(
                requests[0].destination.read_bytes(),
                b"published-before-restart",
            )
            self.assertTrue(all(path.is_file() for path in sources))
            discarded = discard_export_session(root / "batch-output.mp4")
            self.assertFalse(discarded.exists)
            self.assertFalse(session_root(root / "batch-output.mp4").exists())
            self.assertTrue(requests[0].destination.is_file())
            self.assertTrue(all(path.is_file() for path in sources))


if __name__ == "__main__":
    unittest.main()
