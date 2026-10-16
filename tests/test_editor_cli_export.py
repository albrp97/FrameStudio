import argparse
import io
import json
import os
import shlex
import shutil
import signal
import subprocess
import sys
import threading
import time
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from framestudio.cli import cli_main
from framestudio.export import (
    ExportExecutionError,
    ExportPlan,
    ExportProgress,
)
from framestudio.export_session import ExportSession, session_root
from framestudio.fps_policy import resolve_frame_rate_policy
from framestudio.media import MediaProbe, probe_media
from framestudio.model import Project
from framestudio.persistence import save_project
from framestudio.upscale_policy import UpscalePolicy, resolve_upscale_policy
from tests.test_editor_source_outputs_functionality import _make_constant_source


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
    def test_synchronized_planning_propagates_cancellation_to_every_output(self):
        from framestudio.cli_export import _build_output_plans
        from framestudio.output_plan import plan_project_outputs

        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            legacy = make_project(root)
            project = Project.create_synchronized_multi(
                ((Path(legacy.source.path), legacy.source.metadata),)
            )
            outputs = plan_project_outputs(project, root / "out.mp4", mode="final-only")
            event = threading.Event()
            with (
                patch("framestudio.cli_export.ensure_project_audio_analysis"),
                patch("framestudio.cli_export.plan_project_av") as plan_final,
                patch(
                    "framestudio.cli_export.plan_source_outputs", return_value=()
                ) as plan_sources,
            ):
                _build_output_plans(
                    argparse.Namespace(),
                    project,
                    outputs,
                    lambda *_a, **_k: None,
                    cancel_event=event,
                )
            self.assertIs(plan_final.call_args.kwargs.get("cancel_event"), event)
            self.assertIs(plan_sources.call_args.kwargs.get("cancel_event"), event)
            self.assertIs(
                plan_final.call_args.kwargs.get("runtime_cache"),
                plan_sources.call_args.kwargs.get("runtime_cache"),
            )

    def test_sigint_during_synchronized_audio_planning_is_structured_and_cleans_child(self):
        self._assert_audio_planning_cancellation(synchronized=True)

    def test_sigint_during_legacy_audio_planning_is_structured_and_cleans_child(self):
        self._assert_audio_planning_cancellation(synchronized=False)

    def test_sigint_during_source_only_audio_planning_is_structured_and_cleans_child(self):
        self._assert_audio_planning_cancellation(synchronized=True, output_mode="source-only")

    def test_sigterm_is_logged_and_cancels_analysis_without_leaving_child_process(self):
        self._assert_audio_planning_cancellation(synchronized=True, signum=signal.SIGTERM)

    def _assert_audio_planning_cancellation(
        self,
        *,
        synchronized: bool,
        output_mode: str = "final-only",
        signum: int = signal.SIGINT,
    ) -> None:
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = root / "source.mp4"
            _make_constant_source(
                source,
                color="red",
                frame_rate=24,
                width=320,
                height=180,
                frequencies=(440, 880),
                duration=4.0,
            )
            metadata = probe_media(source).metadata()
            project = (
                Project.create_synchronized_multi(((source, metadata),))
                if synchronized
                else Project.create(source, metadata)
            )
            project_path = root / "edit.framestudio.json"
            save_project(project, project_path)
            source_before = source.read_bytes()
            project_before = project_path.read_bytes()
            destination = root / "edited.mp4"
            child_marker = root / "analysis-child.pid"
            wrapper = root / "analysis-ffmpeg"
            wrapper.write_text(
                f"#!{sys.executable}\n"
                "import os, sys\n"
                "from pathlib import Path\n"
                "arguments = sys.argv[1:]\n"
                "if 'pcm_f32le' in arguments:\n"
                f"    Path({str(child_marker)!r}).write_text(str(os.getpid()))\n"
                "    arguments.insert(arguments.index('-i'), '-re')\n"
                f"os.execv({shutil.which('ffmpeg')!r}, ['ffmpeg', *arguments])\n",
                encoding="utf-8",
            )
            wrapper.chmod(0o755)
            repository_root = Path(__file__).resolve().parents[1]
            process = subprocess.Popen(
                [
                    sys.executable,
                    str(repository_root / "framestudio.py"),
                    "export",
                    str(project_path),
                    "--output",
                    str(destination),
                    "--output-mode",
                    output_mode,
                    "--no-enhance-fps",
                    "--no-upscale-enhancement",
                    "--ffmpeg",
                    str(wrapper),
                ],
                cwd=repository_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            child_pid = None
            try:
                deadline = time.monotonic() + 10.0
                while not child_marker.exists() and process.poll() is None:
                    self.assertLess(time.monotonic(), deadline, "audio analysis did not start")
                    time.sleep(0.01)
                self.assertTrue(child_marker.exists(), "export exited before audio analysis")
                child_pid = int(child_marker.read_text())
                self.assertIsNone(process.poll())
                process.send_signal(signum)
                stdout, stderr = process.communicate(timeout=2.0)
                self.assertEqual(process.returncode, 5, stderr)
                progress = [json.loads(line) for line in stdout.splitlines()]
                self.assertTrue(all(item["event"] == "progress" for item in progress))
                self.assertTrue(all(item["progress"]["overall_percent"] < 100 for item in progress))
                payload = json.loads(stderr)
                self.assertFalse(payload["ok"])
                self.assertEqual(payload["error"]["code"], "export_cancelled")
                from framestudio.export_journal import journal_path

                journal = journal_path(destination)
                self.assertTrue(journal.is_file())
                entries = [json.loads(line) for line in journal.read_text().splitlines()]
                self.assertEqual(entries[-1]["event"], "cancelled")
                self.assertFalse(destination.exists())
                self.assertFalse(Path(f"/proc/{child_pid}").exists())
                self.assertEqual(source.read_bytes(), source_before)
                self.assertEqual(project_path.read_bytes(), project_before)
            finally:
                if process.poll() is None:
                    process.terminate()
                    process.communicate(timeout=10.0)
                if child_pid is not None and Path(f"/proc/{child_pid}").exists():
                    os.kill(child_pid, signal.SIGTERM)

    def test_export_resumes_after_cli_process_restart(self):
        if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
            self.skipTest("FFmpeg and ffprobe are required")
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = root / "source.mp4"
            subprocess.run(
                [
                    shutil.which("ffmpeg") or "ffmpeg",
                    "-hide_banner",
                    "-loglevel",
                    "error",
                    "-f",
                    "lavfi",
                    "-i",
                    "testsrc=size=1920x1080:rate=10",
                    "-t",
                    "3",
                    "-c:v",
                    "libx264",
                    "-g",
                    "1",
                    "-pix_fmt",
                    "yuv420p",
                    str(source),
                ],
                check=True,
            )
            probe = probe_media(source)
            source_before = source.read_bytes()
            project = Project.create(source, probe.metadata())
            project.segment_timeline.split(1.0)
            project_path = root / "edit.framestudio.json"
            save_project(project, project_path)
            destination = root / "edited.mp4"
            counter = root / "ffmpeg-wrapper.count"
            wrapper = root / "ffmpeg-wrapper"
            real_ffmpeg = shutil.which("ffmpeg") or "ffmpeg"
            wrapper.write_text(
                "\n".join(
                    (
                        "#!/bin/sh",
                        'case " $* " in',
                        f'  *" -version "*|*" --version "*) exec {shlex.quote(real_ffmpeg)} "$@" ;;',
                        "esac",
                        f"count_file={shlex.quote(str(counter))}",
                        "count=0",
                        'if [ -f "$count_file" ]; then count=$(cat "$count_file"); fi',
                        "count=$((count + 1))",
                        'printf "%s" "$count" > "$count_file"',
                        f'{shlex.quote(real_ffmpeg)} "$@"',
                        "status=$?",
                        'if [ "$count" -eq 2 ]; then sleep 5; fi',
                        'exit "$status"',
                    )
                )
                + "\n",
                encoding="utf-8",
            )
            wrapper.chmod(0o755)
            repository_root = Path(__file__).resolve().parents[1]
            command = [
                sys.executable,
                str(repository_root / "framestudio.py"),
                "export",
                str(project_path),
                "--output",
                str(destination),
                "--fps-choice",
                "lowest",
                "--no-enhance-fps",
                "--no-upscale-enhancement",
                "--ffmpeg",
                str(wrapper),
                "--ffprobe",
                shutil.which("ffprobe") or "ffprobe",
            ]
            process = subprocess.Popen(
                command,
                cwd=repository_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            checkpoint_found = False
            deadline = time.monotonic() + 30.0
            while time.monotonic() < deadline:
                for manifest_path in session_root(destination).rglob("manifest.json"):
                    try:
                        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                    except (OSError, json.JSONDecodeError):
                        manifest = None
                    if (
                        isinstance(manifest, dict)
                        and manifest.get("stages", {}).get("cut-0", {}).get("status") == "complete"
                    ):
                        checkpoint_found = True
                        break
                if checkpoint_found:
                    break
                if process.poll() is not None:
                    break
                time.sleep(0.05)
            self.assertIsNone(process.poll(), "export exited before a checkpoint was persisted")
            self.assertTrue(checkpoint_found, "no owned child cut checkpoint was persisted")
            process.send_signal(signal.SIGINT)
            stdout, stderr = process.communicate(timeout=15.0)
            self.assertNotEqual(process.returncode, 0)
            self.assertFalse(destination.exists())
            self.assertTrue(stderr or stdout)

            resumed = subprocess.run(
                [*command, "--resume"],
                cwd=repository_root,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(resumed.returncode, 0, resumed.stderr)
            lines = [json.loads(line) for line in resumed.stdout.splitlines()]
            session_events = [line for line in lines if line["command"] == "export.session"]
            result_events = [line for line in lines if line["command"] == "export"]
            self.assertEqual(session_events[0]["session"]["mode"], "resume")
            self.assertTrue(result_events[-1]["export"]["verified"])
            self.assertTrue(result_events[-1]["export"]["session"]["resumed"])
            self.assertGreaterEqual(
                result_events[-1]["export"]["session"]["previous_completed_stage_count"],
                1,
            )
            self.assertTrue(destination.is_file())
            self.assertFalse(session_root(destination).exists())
            self.assertAlmostEqual(probe_media(destination).duration_seconds, 3.0, delta=0.2)
            self.assertEqual(source.read_bytes(), source_before)
            running_ffmpeg = [
                line
                for line in subprocess.check_output(
                    ["ps", "-eo", "args="],
                    text=True,
                ).splitlines()
                if "ffmpeg" in line and str(source) in line
            ]
            self.assertEqual(running_ffmpeg, [])

    def test_export_resume_emits_session_event_and_preserves_json_lines(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            project_path = root / "edit.framestudio.json"
            destination = root / "edited.mp4"
            project = make_project(root)
            save_project(project, project_path)
            plan = ExportPlan(
                route="fallback",
                source=root / "source.mp4",
                destination=destination,
                segments=tuple(project.segment_timeline.segments),
                expected_duration_seconds=10.0,
                reason="target policy",
            )
            output_probe = make_probe(destination)

            def fake_execute(execution_plan, **_kwargs):
                execution_plan.destination.write_bytes(b"verified")
                return execution_plan.destination

            with (
                patch("framestudio.cli.plan_project_export", return_value=plan),
                patch(
                    "framestudio.cli.execute_export",
                    side_effect=[ExportExecutionError("interrupted"), fake_execute],
                ) as execute,
                patch("framestudio.cli.probe_media", return_value=output_probe),
                patch(
                    "framestudio.cli_export.verify_planned_output",
                    return_value={"verified": True, "metadata": output_probe.metadata()},
                ),
            ):
                interrupted, _stdout, _stderr = run_cli(
                    "export",
                    str(project_path),
                    "--output",
                    str(destination),
                )
                self.assertNotEqual(interrupted, 0)
                execute.side_effect = fake_execute
                result, stdout, stderr = run_cli(
                    "export",
                    str(project_path),
                    "--output",
                    str(destination),
                    "--resume",
                )
            self.assertEqual(execute.call_count, 2)

            self.assertEqual(result, 0)
            self.assertEqual(stderr.getvalue(), "")
            lines = [json.loads(line) for line in stdout.getvalue().splitlines()]
            self.assertEqual(lines[0]["command"], "export.session")
            self.assertEqual(lines[0]["session"]["mode"], "resume")
            self.assertEqual(lines[-1]["command"], "export")
            self.assertTrue(lines[-1]["export"]["session"]["resumed"])

    def test_export_discard_removes_session_without_starting_media_work(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            project_path = root / "edit.framestudio.json"
            destination = root / "edited.mp4"
            project = make_project(root)
            save_project(project, project_path)
            session = ExportSession.open(destination, {"request": "discard"}, ("render",))
            session.close()
            plan = ExportPlan(
                route="fallback",
                source=root / "source.mp4",
                destination=destination,
                segments=tuple(project.segment_timeline.segments),
                expected_duration_seconds=10.0,
                reason="target policy",
            )

            with (
                patch("framestudio.cli.plan_project_export", return_value=plan),
                patch("framestudio.cli.execute_export") as execute,
            ):
                result, stdout, stderr = run_cli(
                    "export",
                    str(project_path),
                    "--output",
                    str(destination),
                    "--discard",
                )

            self.assertEqual(result, 0)
            self.assertEqual(stderr.getvalue(), "")
            payload = json.loads(stdout.getvalue())
            self.assertTrue(payload["export"]["session"]["discarded"])
            self.assertFalse(session_root(destination).exists())
            self.assertFalse(execute.called)

    def test_export_resolves_unavailable_default_rve_to_ffmpeg_fallback(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            project_path = root / "edit.framestudio.json"
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
                    "framestudio.cli.resolve_frame_rate_policy_with_fallback",
                    return_value=(fallback, (), "RVE unavailable"),
                ),
                patch(
                    "framestudio.cli.plan_project_export",
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
            project_path = root / "edit.framestudio.json"
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
                    "framestudio.cli.plan_project_export",
                    return_value=plan,
                ) as plan_export,
                patch(
                    "framestudio.cli.execute_export",
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
            project_path = root / "edit.framestudio.json"
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
            project_path = root / "edit.framestudio.json"
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
            project_path = root / "edit.framestudio.json"
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
            project_path = root / "edit.framestudio.json"
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
                    "framestudio.cli.resolve_frame_rate_policy_with_fallback",
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
                    "framestudio.cli.plan_project_export",
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
            project_path = root / "edit.framestudio.json"
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
                    "framestudio.cli.resolve_frame_rate_policy_with_fallback",
                    return_value=(policy, (), None),
                ),
                patch(
                    "framestudio.cli.plan_project_export",
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
            project_path = root / "edit.framestudio.json"
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
                print("[C-----] 0/5 frames")
                print("Parallel normalization: 1/2 parts complete")
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
                plan.destination.write_bytes(b"verified")
                return plan.destination

            with (
                patch(
                    "framestudio.cli.probe_media",
                    return_value=output_probe,
                ),
                patch(
                    "framestudio.cli.plan_project_export",
                    return_value=plan,
                ),
                patch(
                    "framestudio.cli.execute_export",
                    side_effect=fake_execute,
                ),
                patch(
                    "framestudio.cli_export.verify_planned_output",
                    return_value={"verified": True, "metadata": output_probe.metadata()},
                ),
            ):
                result, stdout, stderr = run_cli(
                    "export",
                    str(project_path),
                    "--output",
                    str(destination),
                )
            self.assertEqual(result, 0)
            lines = [json.loads(line) for line in stdout.getvalue().splitlines()]
            self.assertEqual(lines[0]["command"], "export.progress")
            encoding = [
                line["progress"]
                for line in lines
                if line.get("event") == "progress" and line["progress"]["stage"] == "encoding"
            ]
            self.assertEqual(encoding[0]["percent"], 50.0)
            self.assertEqual(encoding[0]["current_percent"], 50.0)
            self.assertLess(encoding[0]["overall_percent"], 100.0)
            self.assertEqual(lines[-1]["command"], "export")
            self.assertTrue(lines[-1]["export"]["verified"])
            self.assertEqual(lines[-1]["export"]["route"], "stream-copy")
            self.assertEqual(lines[-1]["export"]["destination"], "edited.mp4")
            self.assertIn("[C-----] 0/5 frames", stderr.getvalue())
            self.assertIn("Parallel normalization: 1/2 parts complete", stderr.getvalue())
            self.assertNotIn(str(root), stdout.getvalue())

    def test_export_failure_returns_structured_error_without_success_result(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            project_path = root / "edit.framestudio.json"
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
                    "framestudio.cli.probe_media",
                    return_value=source_probe,
                ),
                patch(
                    "framestudio.cli.plan_project_export",
                    return_value=plan,
                ),
                patch(
                    "framestudio.cli.execute_export",
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
            project_path = root / "edit.framestudio.json"
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
                    "framestudio.cli.plan_project_export",
                    return_value=plan,
                ) as plan_export,
                patch(
                    "framestudio.cli.execute_export",
                    return_value=project_path,
                ) as execute,
                patch(
                    "framestudio.cli.probe_media",
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
