from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import threading
import unittest
import uuid
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, cast

from framestudio.app import create_editor_application
from framestudio.audio_compositor import AUDIO_SAMPLE_RATE
from framestudio.media import probe_media
from framestudio.model import Project
from framestudio.model_types import SCHEMA_VERSION
from framestudio.output_plan import (
    COMBINED_OUTPUT_MODE,
    FINAL_ONLY_OUTPUT_MODE,
    SOURCE_ONLY_OUTPUT_MODE,
    OutputRequest,
)
from framestudio.persistence import save_project
from tests import test_phase010_functionality as phase010_functionality
from tests.test_editor_audio_compositor import _audio_settings as _create_audio_settings
from tests.test_editor_audio_compositor_functionality import (
    _decoded_pcm,
    _tone_amplitude,
)
from tests.test_editor_flexible_output_recovery import (
    _fingerprint_payload,
    _output_key,
)
from tests.test_editor_layout_plan_functionality import make_block
from tests.test_editor_video_compositor_functionality import (
    _decode_frame,
    _sha256,
    _white_centroid,
)
from tests.test_phase010_functionality import _pump_events, _visible_widget_text

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
FFMPEG = shutil.which("ffmpeg")
FFPROBE = shutil.which("ffprobe")


def _run(command: list[str], *, cwd: Path = REPOSITORY_ROOT) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )


def _make_audio_marker_source(
    root: Path,
    name: str,
    *,
    color: str,
    frequency: int,
    duration: float = 4.0,
    stereo: bool,
) -> Path:
    from tests.test_editor_video_compositor_functionality import _make_marker_source

    video = _make_marker_source(root, f".{name}-video.mp4", 320, 180, "10/1", color)
    destination = root / f"{name}.mp4"
    command = [
        FFMPEG or "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-nostdin",
        "-y",
        "-i",
        str(video),
        "-f",
        "lavfi",
        "-i",
        f"sine=frequency={frequency}:sample_rate={AUDIO_SAMPLE_RATE}:duration={duration}",
    ]
    if stereo:
        command.extend(
            [
                "-f",
                "lavfi",
                "-i",
                f"sine=frequency={frequency * 2}:sample_rate={AUDIO_SAMPLE_RATE}:duration={duration}",
                "-filter_complex",
                "[1:a][2:a]amerge=inputs=2[a]",
                "-map",
                "0:v:0",
                "-map",
                "[a]",
                "-ac",
                "2",
                "-channel_layout",
                "stereo",
            ],
        )
    else:
        command.extend(
            [
                "-map",
                "0:v:0",
                "-map",
                "1:a:0",
                "-ac",
                "1",
                "-channel_layout",
                "mono",
            ],
        )
    command.extend(
        [
            "-t",
            str(duration),
            "-c:v",
            "copy",
            "-c:a",
            "pcm_s16le",
            "-ar",
            str(AUDIO_SAMPLE_RATE),
            "-shortest",
            "-movflags",
            "+faststart",
            str(destination),
        ],
    )
    result = _run(command, cwd=root)
    if result.returncode != 0:
        raise AssertionError(f"Could not create {destination.name}: {result.stderr}")
    return destination


def _build_recovery_project(root: Path) -> tuple[Project, tuple[Path, ...], dict[str, int]]:
    root.mkdir(parents=True, exist_ok=True)
    sources = (
        _make_audio_marker_source(root, "A", color="red", frequency=440, stereo=True),
        _make_audio_marker_source(root, "B", color="blue", frequency=660, stereo=False),
        _make_audio_marker_source(root, "C", color="green", frequency=990, stereo=False),
    )
    metadata = []
    for path in sources:
        item = probe_media(path).metadata()
        if item.get("audio_channels") == 1:
            item["audio_channel_layout"] = "mono"
        else:
            item["audio_channel_layout"] = "stereo"
        metadata.append((path, item))
    project = Project.create_synchronized_multi(
        tuple(metadata),
        project_id="ticket-124-flexible-recovery",
    )
    project.schema_version = SCHEMA_VERSION
    project.timeline.add_track("track-2")
    project.timeline.add_track("empty-track")
    project.timeline.add_track("excluded-only")
    source_ids = tuple(source.source_id for source in project.sources or ())
    project.timeline.replace_track_blocks(
        "track-1",
        (
            make_block(
                segment_id="track1-a",
                source_id=source_ids[0],
                track_id="track-1",
                source_start=0.0,
                source_end=1.2,
                timeline_start=0.0,
                timeline_end=1.2,
            ),
            make_block(
                segment_id="track1-b",
                source_id=source_ids[1],
                track_id="track-1",
                source_start=0.0,
                source_end=1.2,
                timeline_start=1.2,
                timeline_end=2.4,
            ),
        ),
    )
    project.timeline.replace_track_blocks(
        "track-2",
        (
            make_block(
                segment_id="track2-a",
                source_id=source_ids[0],
                track_id="track-2",
                source_start=1.2,
                source_end=2.4,
                timeline_start=0.0,
                timeline_end=1.2,
            ),
            make_block(
                segment_id="track2-c",
                source_id=source_ids[2],
                track_id="track-2",
                source_start=0.0,
                source_end=1.2,
                timeline_start=1.2,
                timeline_end=2.4,
            ),
        ),
    )
    project.timeline.replace_track_blocks("empty-track", ())
    project.timeline.replace_track_blocks(
        "excluded-only",
        (
            make_block(
                segment_id="excluded-only-block",
                source_id=source_ids[1],
                track_id="excluded-only",
                source_start=0.0,
                source_end=0.5,
                timeline_start=0.0,
                timeline_end=0.5,
                deleted=True,
            ),
        ),
    )
    project.duration_seconds = project.timeline.timeline_duration_seconds
    for source in project.sources or ():
        project.set_source_audio_settings(
            source.source_id,
            _create_audio_settings(
                source,
                peak_db=-20.0,
                sample_count=round(float(source.metadata["duration_seconds"]) * AUDIO_SAMPLE_RATE),
            ),
        )
    project.validate()
    return project, sources, {source_ids[0]: 440, source_ids[1]: 660, source_ids[2]: 990}


def _json_lines(value: str) -> list[dict[str, Any]]:
    payloads: list[dict[str, Any]] = []
    for line in value.splitlines():
        if not line.strip().startswith("{"):
            continue
        parsed = json.loads(line)
        if isinstance(parsed, dict):
            payloads.append(cast(dict[str, Any], parsed))
    return payloads


def _export_payload(result: subprocess.CompletedProcess[str]) -> dict[str, Any]:
    payloads = _json_lines(result.stdout) + _json_lines(result.stderr)
    exports = [payload for payload in payloads if payload.get("command") == "export"]
    if not exports:
        raise AssertionError(
            f"No export JSONL payload found:\nstdout={result.stdout}\nstderr={result.stderr}"
        )
    return exports[-1]


def _output_destination(item: dict[str, Any]) -> Path:
    request = item.get("request")
    if isinstance(request, dict) and isinstance(request.get("destination"), str):
        return Path(request["destination"])
    if isinstance(item.get("destination"), str):
        return Path(item["destination"])
    raise AssertionError(f"Output result has no destination: {item}")


def _frame_count(path: Path) -> int:
    result = _run(
        [
            FFPROBE or "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-count_frames",
            "-show_entries",
            "stream=nb_read_frames",
            "-of",
            "default=nw=1:nk=1",
            str(path),
        ],
    )
    if result.returncode != 0:
        raise AssertionError(result.stderr)
    return int(result.stdout.strip())


def _assert_real_reel(
    test_case: unittest.TestCase,
    path: Path,
    *,
    expected_tones: tuple[int, ...],
    center_marker: bool = False,
) -> None:
    test_case.assertTrue(path.is_file(), f"missing published output: {path}")
    metadata = probe_media(path).metadata()
    test_case.assertEqual((metadata["width"], metadata["height"]), (1920, 1080))
    frames = _frame_count(path)
    test_case.assertGreater(frames, 0)
    decoded = _decode_frame(path, min(frames - 1, 2))
    centroid = _white_centroid(decoded, (0, 0, 384, 216))
    test_case.assertGreaterEqual(centroid[0], 0.0)
    test_case.assertLessEqual(centroid[0], 384.0)
    test_case.assertGreaterEqual(centroid[1], 0.0)
    test_case.assertLessEqual(centroid[1], 216.0)
    if center_marker:
        test_case.assertAlmostEqual(centroid[0], 192.0, delta=35.0)
        test_case.assertAlmostEqual(centroid[1], 108.0, delta=35.0)
    samples, sample_rate, channels = _decoded_pcm(path)
    test_case.assertEqual(sample_rate, AUDIO_SAMPLE_RATE)
    test_case.assertEqual(channels, 2)
    test_case.assertGreater(max(abs(value) for value in samples), 0.001)
    available_frames = len(samples) // channels
    start_frame = min(4800, max(0, available_frames // 2))
    end_frame = min(available_frames, start_frame + 24000)
    test_case.assertGreater(end_frame, start_frame)
    amplitudes = [
        _tone_amplitude(
            samples,
            start_frame=start_frame,
            end_frame=end_frame,
            frequency=frequency,
            channel=0,
        )
        for frequency in expected_tones
    ]
    test_case.assertTrue(any(amplitude > 0.001 for amplitude in amplitudes))


class FlexibleOutputRecoveryCliFunctionalityTests(unittest.TestCase):
    def setUp(self) -> None:
        if FFMPEG is None or FFPROBE is None:
            self.skipTest("FFmpeg and ffprobe are required for TICKET-124 functionality")
        self.runtime = TemporaryDirectory(
            dir=REPOSITORY_ROOT / "tests",
            prefix=".ticket124-recovery-cli-",
        )
        self.addCleanup(self.runtime.cleanup)
        self.root = Path(self.runtime.name)
        self.project, self.source_paths, self.frequencies = _build_recovery_project(
            self.root / "fixtures",
        )
        self.project_path = self.root / "project.framestudio.json"
        save_project(self.project, self.project_path)
        self.source_hashes = {path: _sha256(path) for path in self.source_paths}

    def _run_cli(
        self,
        mode: str,
        destination: Path,
        *,
        ffmpeg: str | None = None,
        resume_mode: str | None = None,
    ) -> subprocess.CompletedProcess[str]:
        command = [
            sys.executable,
            str(REPOSITORY_ROOT / "framestudio.py"),
            "export",
            str(self.project_path),
            "--output",
            str(destination),
            "--output-mode",
            mode,
            "--fps-choice",
            "custom",
            "--custom-fps",
            "10",
            "--no-enhance-fps",
            "--no-upscale-enhancement",
            "--ffmpeg",
            ffmpeg or FFMPEG or "ffmpeg",
            "--ffprobe",
            FFPROBE or "ffprobe",
            "--full-paths",
        ]
        if resume_mode is not None:
            command.append(f"--{resume_mode}")
        return _run(command)

    def test_real_fixture_preflight_proves_markers_stereo_mono_and_source_hashes(self):
        self.assertEqual(
            [probe_media(path).metadata()["audio_channels"] for path in self.source_paths],
            [2, 1, 1],
        )
        for path in self.source_paths:
            metadata = probe_media(path).metadata()
            self.assertEqual((metadata["width"], metadata["height"]), (320, 180))
            frame = _decode_frame(path, 2)
            centroid = _white_centroid(frame, (0, 0, 384, 216))
            self.assertAlmostEqual(centroid[0], 192.0, delta=12.0)
            self.assertAlmostEqual(centroid[1], 108.0, delta=12.0)
            samples, sample_rate, channels = _decoded_pcm(path)
            self.assertEqual(sample_rate, AUDIO_SAMPLE_RATE)
            self.assertEqual(channels, probe_media(path).metadata()["audio_channels"])
            expected = self.frequencies[
                next(
                    source.source_id
                    for source in self.project.sources or ()
                    if Path(source.path) == path
                )
            ]
            amplitude = _tone_amplitude(
                samples,
                start_frame=4800,
                end_frame=min(48000, len(samples) // 2),
                frequency=expected,
                channel=0,
            )
            self.assertGreater(amplitude, 0.001)
        self.assertEqual(
            {path: _sha256(path) for path in self.source_paths},
            self.source_hashes,
        )

    def test_public_cli_final_only_emits_verified_result_and_preserves_sources(self):
        destination = self.root / "published" / "final-only.mp4"
        result = self._run_cli(FINAL_ONLY_OUTPUT_MODE, destination)
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = _export_payload(result)
        export = payload["export"]
        self.assertTrue(export["verified"])
        self.assertFalse(export["partial_success"])
        self.assertEqual(export["output_plan"]["mode"], FINAL_ONLY_OUTPUT_MODE)
        self.assertEqual(len(export["results"]), 1)
        self.assertEqual(export["results"][0]["state"], "verified")
        self.assertEqual(export["results"][0]["identity"]["output_kind"], "final")
        self.assertEqual(export["results"][0]["identity"]["framing"], "final-composition")
        _assert_real_reel(self, destination, expected_tones=(440, 660, 990))
        self.assertEqual(
            {path: _sha256(path) for path in self.source_paths},
            self.source_hashes,
        )

    def test_ui_resumes_cli_export_without_rerendering_verified_output(self):
        from fractions import Fraction

        from framestudio.app_export import run_output_choice_job
        from framestudio.export_coordinator import RECEIPT_SUFFIX
        from framestudio.fps_policy import FrameRatePolicy
        from framestudio.upscale_policy import UpscalePolicy

        destination = self.root / "published" / "cross-interface.mp4"
        result = _run(
            [
                sys.executable,
                str(REPOSITORY_ROOT / "framestudio.py"),
                "export",
                str(self.project_path),
                "--output",
                str(destination),
                "--output-mode",
                "final-only",
                "--fps-choice",
                "custom",
                "--custom-fps",
                "10",
                "--no-enhance-fps",
                "--no-upscale-enhancement",
            ]
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        before = destination.stat()
        output_hash = _sha256(destination)
        receipt_path = destination.parent / f".{destination.name}{RECEIPT_SUFFIX}"
        fingerprint = json.loads(receipt_path.read_text())["batch_fingerprint"]
        holder = {}
        output, _, _, _ = run_output_choice_job(
            self.project,
            destination,
            output_mode=FINAL_ONLY_OUTPUT_MODE,
            frame_rate_policy=FrameRatePolicy(
                choice="custom",
                target_rate=Fraction(10),
                custom_rate=Fraction(10),
                enhancement_enabled=False,
            ),
            upscale_policy=UpscalePolicy(enabled=False),
            progress_callback=None,
            cancel_event=None,
            resume_mode="resume",
            batch_result_holder=holder,
            project_path=self.project_path,
        )
        self.assertEqual(output, destination)
        self.assertTrue(holder["result"].complete)
        self.assertEqual(holder["result"].results[0].state.value, "skipped")
        self.assertEqual(json.loads(receipt_path.read_text())["batch_fingerprint"], fingerprint)
        self.assertEqual(destination.stat().st_mtime_ns, before.st_mtime_ns)
        self.assertEqual(_sha256(destination), output_hash)
        _assert_real_reel(self, destination, expected_tones=(440, 660, 990))
        self.assertEqual(
            {path: _sha256(path) for path in self.source_paths},
            self.source_hashes,
        )

    def test_public_cli_source_only_emits_four_standalone_full_canvas_results(self):
        destination = self.root / "published" / "source-only.mp4"
        result = self._run_cli(SOURCE_ONLY_OUTPUT_MODE, destination)
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = _export_payload(result)
        export = payload["export"]
        self.assertTrue(export["verified"])
        self.assertFalse(export["partial_success"])
        self.assertEqual(export["output_plan"]["mode"], SOURCE_ONLY_OUTPUT_MODE)
        self.assertEqual(len(export["results"]), 4)
        source_ids = tuple(source.source_id for source in self.project.sources or ())
        self.assertEqual(
            {
                (
                    item["identity"]["track_id"],
                    item["identity"]["source_id"],
                )
                for item in export["results"]
            },
            {
                ("track-1", source_ids[0]),
                ("track-1", source_ids[1]),
                ("track-2", source_ids[0]),
                ("track-2", source_ids[2]),
            },
        )
        for item in export["results"]:
            self.assertEqual(item["state"], "verified")
            self.assertEqual(item["identity"]["output_kind"], "source")
            self.assertEqual(item["identity"]["framing"], "standalone-full-canvas")
            self.assertEqual(item["identity"]["audio_intent"], "normal-source-audio")
            _assert_real_reel(
                self,
                _output_destination(item),
                expected_tones=(440, 660, 990),
                center_marker=True,
            )
        published_bytes = {
            _output_destination(item): _output_destination(item).read_bytes()
            for item in export["results"]
        }
        tampered = _make_audio_marker_source(
            self.root / "fixtures",
            "same-shape-tamper",
            color="yellow",
            frequency=123,
            duration=1.2,
            stereo=True,
        )
        tampered_destination = next(iter(published_bytes))
        tampered_destination.write_bytes(tampered.read_bytes())
        resumed = self._run_cli(
            SOURCE_ONLY_OUTPUT_MODE,
            destination,
            resume_mode="resume",
        )
        self.assertEqual(resumed.returncode, 0, resumed.stderr)
        resumed_export = _export_payload(resumed)["export"]
        self.assertTrue(resumed_export["complete"])
        self.assertEqual(
            {item["state"] for item in resumed_export["results"]},
            {"skipped", "verified"},
        )
        tampered_result = next(
            item
            for item in resumed_export["results"]
            if _output_destination(item) == tampered_destination
        )
        self.assertEqual(tampered_result["state"], "verified")
        self.assertEqual(
            {
                _output_destination(item): _output_destination(item).read_bytes()
                for item in resumed_export["results"]
            },
            published_bytes,
        )
        self.assertFalse(destination.exists())
        self.assertEqual(
            {path: _sha256(path) for path in self.source_paths},
            self.source_hashes,
        )

    def test_public_cli_combined_synchronized_tracks_is_recoverable_not_guarded(self):
        destination = self.root / "published" / "combined.mp4"
        result = self._run_cli(COMBINED_OUTPUT_MODE, destination)
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = _export_payload(result)
        export = payload["export"]
        self.assertTrue(export["verified"])
        self.assertFalse(export["partial_success"])
        self.assertEqual(export["output_plan"]["mode"], COMBINED_OUTPUT_MODE)
        self.assertEqual(len(export["results"]), 5)
        self.assertEqual(
            {item["state"] for item in export["results"]},
            {"verified"},
        )
        final = next(
            item for item in export["results"] if item["identity"]["output_kind"] == "final"
        )
        _assert_real_reel(self, _output_destination(final), expected_tones=(440, 660, 990))
        self.assertEqual(
            {path: _sha256(path) for path in self.source_paths},
            self.source_hashes,
        )

    def test_public_cli_failure_returns_all_output_identities_with_truthful_partial_details(self):
        destination = self.root / "published" / "failed-output.mp4"
        result = self._run_cli(COMBINED_OUTPUT_MODE, destination, ffmpeg="/missing/ffmpeg")
        self.assertNotEqual(result.returncode, 0)
        stdout_payloads = _json_lines(result.stdout)
        self.assertFalse(
            any(
                payload.get("ok") is True and payload.get("command") == "export"
                for payload in stdout_payloads
            )
        )
        error_payloads = _json_lines(result.stderr)
        self.assertTrue(error_payloads, result.stderr)
        error_payload = error_payloads[-1]
        self.assertFalse(error_payload.get("ok", True))
        error = error_payload.get("error")
        self.assertIsInstance(error, dict)
        details = error.get("details")
        self.assertIsInstance(details, dict)
        export = details
        self.assertFalse(export["verified"])
        self.assertEqual(len(export["results"]), 5)
        self.assertIsInstance(export["partial_success"], bool)
        self.assertTrue(
            {item["state"] for item in export["results"]} <= {"failed", "cancelled", "pending"},
        )
        self.assertFalse(destination.exists())
        self.assertEqual(
            {path: _sha256(path) for path in self.source_paths},
            self.source_hashes,
        )

    def test_real_running_child_cancellation_is_not_reduced_to_between_output_polling(self):
        from tests.test_editor_flexible_output_recovery import _request

        fixture_root = self.root / "child-fixture"
        fixture_root.mkdir()
        source = self.source_paths[0]
        request = _request(
            self.root,
            output_kind="source",
            mode=SOURCE_ONLY_OUTPUT_MODE,
            track_id="track-1",
            source_id="source-1",
            source_paths=(source,),
            source_ids=("source-1",),
            name="cancelled-child.mp4",
        )
        import importlib

        recovery = importlib.import_module("framestudio.export_coordinator")
        payload = _fingerprint_payload(request, (source,))
        started = threading.Event()
        process_holder: dict[str, subprocess.Popen[bytes]] = {}

        def render(
            current: OutputRequest,
            candidate: Path,
            cancel_event: threading.Event,
        ) -> Path:
            child = subprocess.Popen(
                [
                    FFMPEG or "ffmpeg",
                    "-hide_banner",
                    "-loglevel",
                    "error",
                    "-nostdin",
                    "-f",
                    "lavfi",
                    "-i",
                    "testsrc2=size=1920x1080:rate=30",
                    "-t",
                    "30",
                    "-c:v",
                    "libx264",
                    "-preset",
                    "slow",
                    str(candidate),
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            process_holder["process"] = child
            started.set()
            while child.poll() is None:
                if cancel_event.wait(0.02):
                    child.terminate()
                    child.wait(timeout=10)
                    raise recovery.ExportCancelled("cancelled running child")
            raise RuntimeError("child completed before cancellation")

        def verify(
            current: OutputRequest,
            candidate: Path,
            cancel_event: threading.Event,
        ) -> dict[str, object]:
            raise AssertionError("verification must not run after cancellation")

        cancel_event = threading.Event()
        result_holder: dict[str, Any] = {}
        coordinator = recovery.ExportCoordinator(
            output_requests=(request,),
            session_destination=self.root / "child-batch.mp4",
            output_fingerprints={
                _output_key(request): recovery.build_output_fingerprint(payload),
            },
            render_output=render,
            verify_output=verify,
            publication_lock=threading.Lock(),
        )

        worker = threading.Thread(
            target=lambda: result_holder.setdefault(
                "result",
                coordinator.run(mode="fresh", cancel_event=cancel_event),
            ),
        )
        worker.start()
        self.assertTrue(started.wait(timeout=10))
        cancel_event.set()
        worker.join(timeout=20)
        self.assertFalse(worker.is_alive())
        self.assertIsNotNone(process_holder["process"].poll())
        self.assertEqual(
            result_holder["result"].results[0].state,
            recovery.ExportResultState.CANCELLED,
        )
        self.assertFalse(request.destination.exists())


def _gtk_runtime(
    test_case: unittest.TestCase,
    prefix: str,
) -> tuple[TemporaryDirectory, Path, Path]:
    runtime = TemporaryDirectory(dir=REPOSITORY_ROOT / "tests", prefix=prefix)
    test_case.addCleanup(runtime.cleanup)
    root = Path(runtime.name)
    state_root = root / "xdg-state"
    state_root.mkdir()
    previous = os.environ.get("XDG_STATE_HOME")
    os.environ["XDG_STATE_HOME"] = str(state_root)

    def restore() -> None:
        if previous is None:
            os.environ.pop("XDG_STATE_HOME", None)
        else:
            os.environ["XDG_STATE_HOME"] = previous

    test_case.addCleanup(restore)
    return runtime, root, state_root


class FlexibleOutputRecoveryGtkFunctionalityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        phase010_functionality.Phase010FunctionalityTests.setUpClass.__func__(cls)

    def setUp(self) -> None:
        if FFMPEG is None or FFPROBE is None:
            self.skipTest("FFmpeg and ffprobe are required for TICKET-124 GTK functionality")
        (
            self.runtime,
            self.root,
            self.state_root,
        ) = _gtk_runtime(
            self,
            ".ticket124-recovery-gtk-",
        )
        self.project, self.source_paths, _ = _build_recovery_project(self.root / "fixtures")
        self.project_path = self.root / "project.framestudio.json"
        save_project(self.project, self.project_path)
        self.application, window_factory = create_editor_application(
            project_path=self.project_path,
            application_id=f"io.github.framestudio.ticket124.a{uuid.uuid4().hex}",
        )
        self.application.set_flags(
            self.application.get_flags() | self.Gio.ApplicationFlags.NON_UNIQUE,
        )
        self.assertTrue(self.application.register(None))
        self.window = window_factory(self.application)
        for cleanup in (self._quit_application, self._close_window):
            self.addCleanup(cleanup)
        self._wait_until(
            lambda: (
                self.window.project is not None
                and not self.window._source_load_in_progress
                and self.window.project_path == self.project_path
            ),
            "GTK recovery project did not load",
        )

    _quit_application = phase010_functionality.Phase010FunctionalityTests._quit_application
    _close_window = phase010_functionality.Phase010FunctionalityTests._close_window
    _pump_display_events = phase010_functionality.Phase010FunctionalityTests._pump_display_events
    _wait_until = phase010_functionality.Phase010FunctionalityTests._wait_until

    def _walk_widgets(self, widget: Any):
        if widget is None:
            return
        yield widget
        child = widget.get_first_child() if hasattr(widget, "get_first_child") else None
        while child is not None:
            yield from self._walk_widgets(child)
            child = child.get_next_sibling()

    def _button(self, root: Any, label: str) -> Any:
        for widget in self._walk_widgets(root):
            if isinstance(widget, self.Gtk.Button) and widget.get_label() == label:
                return widget
        raise AssertionError(f"GTK widget tree did not expose button {label!r}")

    def _open_panel(self) -> Any:
        self.window.export_button.emit("clicked")
        self._wait_until(
            lambda: (
                getattr(self.window, "export_planning_window", None) is not None
                and self.window.export_planning_window.get_visible()
            ),
            "GTK export planner did not open",
        )
        return self.window.export_planning_window

    def _set_filename(self, panel: Any, filename: str) -> None:
        for widget in self._walk_widgets(panel):
            if isinstance(widget, self.Gtk.Entry) and widget.get_text().endswith(".mp4"):
                widget.set_text(filename)
                _pump_events(self.GLib, 20)
                return
        raise AssertionError("GTK export planner did not expose a filename entry")

    def _start_and_wait_for_completion(self, panel: Any) -> str:
        start = self._button(panel, "Start export")
        self._wait_until(
            lambda: start.get_sensitive(),
            "GTK export planner did not finish refreshing the selected destination",
            rounds=6000,
        )
        self.assertTrue(start.get_sensitive())
        start.emit("clicked")
        self._wait_until(
            lambda: not self.window._export_in_progress,
            "GTK export job did not complete",
            rounds=30000,
        )
        return self.window.status_label.get_text().lower()

    def test_recovery_label_shows_previous_overall_progress_not_zero_completed_stages(self):
        from framestudio.export_journal import ExportJournal, journal_path
        from framestudio.export_session import ExportSession
        from framestudio.export_types import ExportExecutionError, ExportProgress

        destination = self.root / "gtk-previous-progress.mp4"
        with ExportSession.open(destination, {"test": "previous-progress"}, ("batch",)) as session:
            manifest = session.root / "manifest.json"
        with self.assertRaisesRegex(ExportExecutionError, "simulated failure"):
            with ExportJournal(destination) as journal:
                journal.progress(
                    ExportProgress(
                        "audio track 2/2",
                        99,
                        0,
                        0,
                        None,
                        1.0,
                        None,
                        overall_percent=89.2935,
                    )
                )
                raise ExportExecutionError("simulated failure")
        paths = (manifest, journal_path(destination))
        proofs = {path: (path.read_bytes(), path.stat().st_mtime_ns) for path in paths}
        panel = self._open_panel()
        self._set_filename(panel, destination.name)
        self._wait_until(
            lambda: "Previous run reached 89.3%." in " ".join(_visible_widget_text(panel)),
            "GTK recovery label did not show historical overall progress",
            rounds=6000,
        )
        text = " ".join(_visible_widget_text(panel))
        self.assertIn("Resume checks and reuses saved checkpoints.", text)
        self.assertNotIn("0 completed stage", text)
        self.assertNotIn("no completed stage", text)
        self.assertTrue(self._button(panel, "Resume export").get_visible())
        self.assertEqual(
            proofs, {path: (path.read_bytes(), path.stat().st_mtime_ns) for path in paths}
        )

    def test_recovery_label_without_history_or_with_read_error_preserves_resume(self):
        from unittest.mock import patch

        from framestudio.export_session import ExportSession
        from framestudio.export_types import ExportExecutionError

        destination = self.root / "gtk-missing-progress.mp4"
        with ExportSession.open(destination, {"test": "missing-progress"}, ("batch",)):
            pass
        panel = self._open_panel()
        self._set_filename(panel, destination.name)
        fallback = "Pending export. Resume checks and reuses saved checkpoints."
        self._wait_until(
            lambda: fallback in " ".join(_visible_widget_text(panel)),
            "GTK recovery label did not explain a session without progress history",
            rounds=6000,
        )
        self.assertTrue(self._button(panel, "Resume export").get_visible())
        with patch(
            "framestudio.app_export.previous_export_overall_percent",
            side_effect=ExportExecutionError("history read denied"),
        ):
            self._set_filename(panel, "different-output.mp4")
            self._set_filename(panel, destination.name)
            self._wait_until(
                lambda: "Previous progress unavailable (history read denied)."
                in " ".join(_visible_widget_text(panel)),
                "GTK recovery label did not surface its history read error",
                rounds=6000,
            )
            self.assertTrue(self._button(panel, "Resume export").get_visible())
            self.assertNotIn("0 completed stage", " ".join(_visible_widget_text(panel)))

    def test_native_final_only_export_reports_mode_and_completes_job(self):
        panel = self._open_panel()
        self._wait_until(
            lambda: "Estimated processing time" in _visible_widget_text(panel),
            "GTK final-only planner did not finish preparing",
            rounds=6000,
        )
        self._set_filename(panel, "gtk-final-only.mp4")
        final_toggle = getattr(panel, "final_output_toggle", None)
        source_toggle = getattr(panel, "source_output_toggle", None)
        self.assertTrue(final_toggle.get_active())
        self.assertFalse(source_toggle.get_active())
        status = self._start_and_wait_for_completion(panel)
        self.assertIn("exported", status)
        self.assertTrue((self.root / "gtk-final-only.mp4").is_file())
        batch_result = getattr(self.window, "_last_export_batch_result", None)
        self.assertIsNotNone(batch_result)
        self.assertTrue(batch_result.complete)
        self.assertEqual(len(batch_result.results), 1)
        self.assertEqual(batch_result.results[0].state.value, "verified")

    def test_native_combined_export_reports_mode_and_completes_job(self):
        panel = self._open_panel()
        self._wait_until(
            lambda: "Estimated processing time" in _visible_widget_text(panel),
            "GTK combined planner did not finish preparing",
            rounds=6000,
        )
        self._set_filename(panel, "gtk-combined.mp4")
        source_toggle = getattr(panel, "source_output_toggle", None)
        source_toggle.set_active(True)
        _pump_events(self.GLib, 40)
        self._wait_until(
            lambda: (
                "estimated processing time" in " ".join(_visible_widget_text(panel)).lower()
                and self._button(panel, "Start export").get_sensitive()
            ),
            "GTK combined planner did not become actionable",
            rounds=6000,
        )
        status = self._start_and_wait_for_completion(panel)
        self.assertIn("exported", status)
        self.assertTrue((self.root / "gtk-combined.mp4").is_file())
        batch_result = getattr(self.window, "_last_export_batch_result", None)
        self.assertIsNotNone(batch_result)
        self.assertTrue(batch_result.complete)
        self.assertEqual(len(batch_result.results), 5)
        self.assertEqual(
            {result.state.value for result in batch_result.results},
            {"verified"},
        )

    def test_native_controls_cancel_running_export_and_offer_resume_recovery(self):
        panel = self._open_panel()
        self._wait_until(
            lambda: "Estimated processing time" in _visible_widget_text(panel),
            "GTK export planner did not finish preparing",
            rounds=6000,
        )
        final_toggle = getattr(panel, "final_output_toggle", None)
        source_toggle = getattr(panel, "source_output_toggle", None)
        self.assertIsInstance(final_toggle, self.Gtk.CheckButton)
        self.assertIsInstance(source_toggle, self.Gtk.CheckButton)
        final_toggle.set_active(False)
        source_toggle.set_active(True)
        _pump_events(self.GLib, 20)
        start = self._button(panel, "Start export")
        self.assertTrue(start.get_sensitive())
        start.emit("clicked")
        self._wait_until(
            lambda: bool(
                self.window._export_in_progress and self.window.cancel_export_button.get_visible()
            ),
            "GTK export did not expose a running child cancellation control",
            rounds=1000,
        )
        self.window.cancel_export_button.emit("clicked")
        self._wait_until(
            lambda: not self.window._export_in_progress,
            "GTK export cancellation did not return to an idle state",
            rounds=6000,
        )
        status = self.window.status_label.get_text().lower()
        self.assertTrue(
            "cancel" in status or "partial" in status,
            f"GTK status did not report cancellation/recovery: {status!r}",
        )
        visible_text = " ".join(_visible_widget_text(panel)).lower()
        self.assertIn("resume export", visible_text)
        self.assertIn("discard", visible_text)
        self.assertTrue(self.window.export_button.get_sensitive())


if __name__ == "__main__":
    unittest.main()
