import subprocess
import threading
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from framestudio.app_export import (
    _export_panel_result_is_current,
    cancel_export,
    finish_export,
    run_export_job,
    start_export,
    start_export_panel_preparation,
)
from framestudio.export import ExportExecutionError, ExportPlanningError
from framestudio.export_panel import ExportPanelState
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
    def test_export_panel_rejects_stale_and_closed_results(self):
        panel_state = {"closed": False, "generation": 3}

        self.assertTrue(_export_panel_result_is_current(panel_state, 3))
        self.assertFalse(_export_panel_result_is_current(panel_state, 2))

        panel_state["closed"] = True
        self.assertFalse(_export_panel_result_is_current(panel_state, 3))

    def test_export_panel_preparation_runs_off_the_calling_thread(self):
        release = threading.Event()
        started = threading.Event()
        callback_states = []
        project = SimpleNamespace()
        folder = Path("/tmp")
        glib = SimpleNamespace(
            idle_add=lambda callback, state: callback(state),
        )

        def prepare(*_args, **_kwargs):
            started.set()
            self.assertTrue(release.wait(timeout=2))
            return ExportPanelState(
                policy=None,
                destination=None,
                filename="output.mp4",
                estimate=None,
                backend_validation=(),
                valid=False,
                reason="not ready",
            )

        with patch("framestudio.app_export.prepare_export_panel", side_effect=prepare):
            worker = start_export_panel_preparation(
                project,
                folder,
                glib,
                callback_states.append,
            )
            self.assertTrue(started.wait(timeout=1))
            self.assertTrue(worker.is_alive())
            self.assertEqual(callback_states, [])
            release.set()
            worker.join(timeout=2)

        self.assertFalse(worker.is_alive())
        self.assertEqual(len(callback_states), 1)
        self.assertEqual(callback_states[0].reason, "not ready")

    def test_start_export_passes_an_immutable_project_snapshot_to_worker(self):
        project = SimpleNamespace(segment_timeline=SimpleNamespace(segments=["before"]))
        destination = Path("output.mp4")
        window = SimpleNamespace(
            project=project,
            project_path=None,
            segment_timeline=project.segment_timeline,
            _audio_analysis_worker_lock=threading.Lock(),
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
        self.assertIs(
            run_job.call_args.kwargs["analysis_lock"],
            window._audio_analysis_worker_lock,
        )

    def test_failed_export_writes_failure_log_before_post_export_action(self):
        events = []
        project_path = Path("/tmp/project.framestudio.json")
        destination = Path("/tmp/project-edited.mp4")
        window = SimpleNamespace(
            _export_in_progress=True,
            _export_cancel_event=threading.Event(),
            _export_cancellation_lock=threading.Lock(),
            _export_project_snapshot=object(),
            _export_post_export_action="sleep",
            _export_project_path=project_path,
            _export_destination=destination,
            project=None,
            export_progress_label=MagicMock(),
            cancel_export_button=MagicMock(),
            _update_segment_controls=MagicMock(),
            _show_error=MagicMock(),
            _set_status=MagicMock(),
        )

        with (
            patch(
                "framestudio.app_export.write_export_failure_log",
                side_effect=lambda **_kwargs: events.append("log") or Path("/tmp/failure.log"),
            ),
            patch(
                "framestudio.app_export.execute_post_export_action",
                side_effect=lambda _action: events.append("action"),
            ),
        ):
            finish_export(window, None, "render failed")

        self.assertEqual(events, ["log", "action"])

    def test_successful_export_does_not_write_failure_log(self):
        destination = Path("/tmp/output.mp4")
        window = SimpleNamespace(
            _export_in_progress=True,
            _export_cancel_event=threading.Event(),
            _export_cancellation_lock=threading.Lock(),
            _export_project_snapshot=object(),
            _export_post_export_action="shutdown",
            _export_project_path=None,
            _export_destination=destination,
            project=None,
            export_progress_label=MagicMock(),
            cancel_export_button=MagicMock(),
            _update_segment_controls=MagicMock(),
            _show_error=MagicMock(),
            _set_status=MagicMock(),
        )

        with (
            patch("framestudio.app_export.write_export_failure_log") as write_log,
            patch("framestudio.app_export.execute_post_export_action") as action,
        ):
            finish_export(window, destination, "exported")

        write_log.assert_not_called()
        action.assert_called_once_with("shutdown")

    def test_cancelled_close_requested_export_quits_after_worker_finishes(self):
        application = MagicMock()
        window = SimpleNamespace(
            _export_in_progress=True,
            _export_cancel_event=threading.Event(),
            _export_cancellation_lock=threading.Lock(),
            _export_project_snapshot=object(),
            _export_post_export_action="nothing",
            _export_project_path=None,
            _export_destination=Path("/tmp/output.mp4"),
            _close_after_export=True,
            project=None,
            export_progress_label=MagicMock(),
            cancel_export_button=MagicMock(),
            _update_segment_controls=MagicMock(),
            _show_error=MagicMock(),
            _set_status=MagicMock(),
            get_application=MagicMock(return_value=application),
        )

        finish_export(window, None, "Export cancelled")

        application.quit.assert_called_once_with()
        self.assertFalse(window._close_after_export)

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

    def test_export_planning_serializes_with_background_audio_analysis(self):
        analysis_lock = threading.Lock()
        analysis_lock.acquire()
        planned = threading.Event()
        events = []
        plan = SimpleNamespace(route="stream-copy", reason="test")

        def plan_export(*_args, **kwargs):
            self.assertIs(kwargs["cancel_event"], cancel_event)
            planned.set()
            return plan

        cancel_event = threading.Event()
        result = []
        errors = []

        def run_job():
            try:
                result.append(
                    run_export_job(
                        object(),
                        Path("output.mp4"),
                        progress_callback=None,
                        cancel_event=cancel_event,
                        frame_rate_policy=None,
                        analysis_lock=analysis_lock,
                    )
                )
            except Exception as error:
                errors.append(error)

        with (
            patch("framestudio.app_export.PerformanceMode", fake_performance_mode_factory(events)),
            patch("framestudio.app_export.plan_project_export", side_effect=plan_export),
            patch(
                "framestudio.app_export.execute_export",
                return_value=Path("output.mp4"),
            ),
        ):
            worker = threading.Thread(target=run_job)
            worker.start()
            self.assertTrue(worker.is_alive())
            self.assertFalse(planned.is_set())
            analysis_lock.release()
            worker.join(timeout=2)

        self.assertFalse(worker.is_alive())
        self.assertEqual(errors, [])
        self.assertEqual(result, [(Path("output.mp4"), plan)])
        self.assertTrue(planned.is_set())

    def test_export_planning_cancels_while_waiting_for_audio_analysis(self):
        analysis_lock = threading.Lock()
        analysis_lock.acquire()
        cancel_event = threading.Event()
        cancel_event.set()
        events = []

        try:
            with (
                patch(
                    "framestudio.app_export.PerformanceMode",
                    fake_performance_mode_factory(events),
                ),
                patch("framestudio.app_export.plan_project_export") as plan_export,
            ):
                with self.assertRaisesRegex(ExportPlanningError, "Export cancelled"):
                    run_export_job(
                        object(),
                        Path("output.mp4"),
                        progress_callback=None,
                        cancel_event=cancel_event,
                        frame_rate_policy=None,
                        analysis_lock=analysis_lock,
                    )
        finally:
            analysis_lock.release()

        plan_export.assert_not_called()

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
