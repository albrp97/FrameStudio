import subprocess
import threading
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from framestudio.app_export import cancel_export, run_export_job, start_export
from framestudio.export import ExportExecutionError
from framestudio.performance import PerformanceMode


def fake_performance_mode_factory(events):
    class FakePerformanceMode:
        def __init__(self, mode: str):
            self.mode = mode

        def __enter__(self):
            events.append(("enter", self.mode))
            return self

        def __exit__(self, error_type, _error, _traceback):
            events.append(("exit", error_type))
            return False

    return FakePerformanceMode


def performance_profile_commands():
    return [
        subprocess.CompletedProcess([], 0, stdout="balanced\n", stderr=""),
        subprocess.CompletedProcess([], 0, stdout="", stderr=""),
        subprocess.CompletedProcess([], 0, stdout="performance\n", stderr=""),
        subprocess.CompletedProcess([], 0, stdout="", stderr=""),
    ]


class EditorPerformanceModeTests(unittest.TestCase):
    def test_start_export_passes_an_immutable_project_snapshot_to_worker(self):
        project = SimpleNamespace(segment_timeline=SimpleNamespace(segments=["before"]))
        destination = Path("output.mp4")
        window = SimpleNamespace(
            project=project,
            project_path=None,
            segment_timeline=project.segment_timeline,
            _export_in_progress=False,
            _export_cancel_event=None,
            _export_project_snapshot=None,
            _update_segment_controls=MagicMock(),
            _set_status=MagicMock(),
            export_progress_panel=MagicMock(),
            export_progress_bar=MagicMock(),
            export_progress_label=MagicMock(),
            cancel_export_button=MagicMock(),
        )
        glib = SimpleNamespace(idle_add=MagicMock())
        plan = SimpleNamespace(route="stream-copy", reason="test")

        with (
            patch(
                "framestudio.app_export.run_export_job",
                return_value=(destination, plan),
            ) as run_job,
            patch("framestudio.app_export.threading.Thread") as thread,
        ):
            start_export(window, destination, glib)
            snapshot = window._export_project_snapshot
            project.segment_timeline.segments.append("after")
            thread.call_args.kwargs["target"]()

        self.assertIsNot(snapshot, project)
        self.assertEqual(snapshot.segment_timeline.segments, ["before"])
        self.assertIs(run_job.call_args.args[0], snapshot)

    def test_performance_mode_restores_previous_profile_after_success(self):
        commands = performance_profile_commands()

        with (
            patch("framestudio.performance.shutil.which", return_value="/usr/bin/powerprofilesctl"),
            patch("framestudio.performance.subprocess.run", side_effect=commands) as run,
        ):
            with PerformanceMode("on"):
                pass

        self.assertEqual(
            [call.args[0] for call in run.call_args_list],
            [
                ["/usr/bin/powerprofilesctl", "get"],
                ["/usr/bin/powerprofilesctl", "set", "performance"],
                ["/usr/bin/powerprofilesctl", "get"],
                ["/usr/bin/powerprofilesctl", "set", "balanced"],
            ],
        )

    def test_performance_mode_restores_previous_profile_after_error(self):
        commands = performance_profile_commands()

        with (
            patch("framestudio.performance.shutil.which", return_value="/usr/bin/powerprofilesctl"),
            patch("framestudio.performance.subprocess.run", side_effect=commands) as run,
        ):
            with self.assertRaisesRegex(RuntimeError, "export failed"):
                with PerformanceMode("on"):
                    raise RuntimeError("export failed")

        self.assertEqual(run.call_count, 4)
        self.assertEqual(run.call_args_list[-1].args[0][-1], "balanced")

    def test_export_job_restores_mode_on_success_error_and_cancel(self):
        for outcome in ("success", "error", "cancel"):
            with self.subTest(outcome=outcome):
                events: list[tuple[str, object | None]] = []
                fake_performance_mode = fake_performance_mode_factory(events)

                with (
                    patch("framestudio.app_export.PerformanceMode", fake_performance_mode),
                    patch("framestudio.app_export.plan_project_export", return_value="plan"),
                    patch(
                        "framestudio.app_export.execute_export",
                        return_value=Path("output.mp4") if outcome == "success" else None,
                        side_effect=None
                        if outcome == "success"
                        else ExportExecutionError(
                            "Export cancelled" if outcome == "cancel" else "export failed"
                        ),
                    ) as execute,
                ):
                    if outcome == "success":
                        output, plan = run_export_job(
                            object(),
                            Path("output.mp4"),
                            progress_callback=None,
                            cancel_event=None,
                            frame_rate_policy=None,
                        )
                        self.assertEqual(output, Path("output.mp4"))
                        self.assertEqual(plan, "plan")
                    else:
                        with self.assertRaises(ExportExecutionError):
                            run_export_job(
                                object(),
                                Path("output.mp4"),
                                progress_callback=None,
                                cancel_event=None,
                                frame_rate_policy=None,
                            )

                self.assertEqual(events[0], ("enter", "on"))
                self.assertEqual(events[1][0], "exit")
                if outcome == "success":
                    self.assertIsNone(events[1][1])
                else:
                    self.assertIs(events[1][1], ExportExecutionError)
                self.assertEqual(execute.call_count, 1)

    def test_cancel_export_waits_for_publication_lock(self):
        cancel_event = threading.Event()
        publication_lock = threading.Lock()
        finished = threading.Event()
        window = SimpleNamespace(
            _export_cancel_event=cancel_event,
            _export_cancellation_lock=publication_lock,
            cancel_export_button=MagicMock(),
            _set_status=MagicMock(),
        )
        publication_lock.acquire()

        def cancel():
            cancel_export(window)
            finished.set()

        thread = threading.Thread(target=cancel)
        thread.start()
        self.assertFalse(finished.wait(timeout=0.05))
        publication_lock.release()
        self.assertTrue(finished.wait(timeout=1.0))
        thread.join(timeout=1.0)

        self.assertTrue(cancel_event.is_set())


if __name__ == "__main__":
    unittest.main()
