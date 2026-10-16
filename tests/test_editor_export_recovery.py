import json
import os
import signal
import subprocess
import sys
import threading
import unittest
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from framestudio.export_types import ExportExecutionError, ExportProgress
from framestudio.render_preparations import RenderPreparations


def sample(percent=50.0, stage="interpolation"):
    return ExportProgress(stage, percent, 5, 10, 2.0, 1.0, 1.0)


class ExportRecoveryTests(unittest.TestCase):
    def test_previous_progress_reads_only_overall_progress_from_the_latest_run(self):
        from framestudio.export_journal import journal_path, previous_export_overall_percent

        with TemporaryDirectory() as directory:
            destination = Path(directory) / "output.mp4"
            self.assertIsNone(previous_export_overall_percent(destination))
            events = [
                {"event": "started"},
                {"event": "progress", "progress": {"overall_percent": 98.0}},
                {"event": "failed"},
                {"event": "started"},
                {"event": "progress", "progress": {"percent": 100, "current_percent": 100}},
            ]
            path = journal_path(destination)
            path.write_text("".join(json.dumps(event) + "\n" for event in events))
            self.assertIsNone(previous_export_overall_percent(destination))
            events.extend(
                [
                    {"event": "progress", "progress": {"overall_percent": 89.2935}},
                    {"event": "failed", "progress": {"overall_percent": 89.2935}},
                ]
            )
            path.write_text("".join(json.dumps(event) + "\n" for event in events))
            proof = (path.read_bytes(), path.stat().st_mtime_ns)
            self.assertEqual(previous_export_overall_percent(destination), 89.2935)
            self.assertEqual((path.read_bytes(), path.stat().st_mtime_ns), proof)

    def test_previous_progress_tolerates_partial_tail_and_invalid_records(self):
        from framestudio.export_journal import journal_path, previous_export_overall_percent

        with TemporaryDirectory() as directory:
            destination = Path(directory) / "output.mp4"
            path = journal_path(destination)
            for invalid in (True, False, -1, 101, "99", None, float("nan"), float("inf"), 10**400):
                with self.subTest(invalid=invalid):
                    records = [
                        {"event": "started", "padding": "x" * 70000},
                        {"event": "progress", "progress": {"overall_percent": 89.3}},
                        [],
                        {"progress": "not an object"},
                        {"progress": {"overall_percent": invalid}},
                    ]
                    path.write_bytes(
                        b"\n".join(json.dumps(record).encode() for record in records)
                        + b"\n"
                        + b"[" * 2000
                        + b"]" * 2000
                        + b'\n{"progress":{"overall_percent":'
                        + b"9" * 5000
                        + b'}}\n\xff\n{"event":"failed",'
                    )
                    self.assertEqual(previous_export_overall_percent(destination), 89.3)
            for percent in (0, 100):
                path.write_text(json.dumps({"progress": {"overall_percent": percent}}) + "\n")
                self.assertEqual(previous_export_overall_percent(destination), percent)
            path.write_text(json.dumps({"progress": {"overall_percent": 90}}) + "\n")
            with path.open("a") as stream:
                stream.write("x" * 70000)
            self.assertIsNone(previous_export_overall_percent(destination))

    def test_previous_progress_surfaces_read_failures_and_rejects_nonregular_files(self):
        from framestudio.export_journal import journal_path, previous_export_overall_percent

        with TemporaryDirectory() as directory:
            destination = Path(directory) / "output.mp4"
            with patch(
                "framestudio.export_journal.os.open", side_effect=PermissionError(13, "denied")
            ):
                with self.assertRaisesRegex(ExportExecutionError, "denied"):
                    previous_export_overall_percent(destination)
            os.mkfifo(journal_path(destination))
            with self.assertRaisesRegex(ExportExecutionError, "regular file"):
                previous_export_overall_percent(destination)

    def test_journal_finds_worker_thread_children_and_their_memory(self):
        from framestudio.export_journal import ExportJournal

        started = threading.Event()
        finish = threading.Event()
        processes = []

        def worker():
            process = subprocess.Popen(
                [sys.executable, "-c", "import time; print('ready', flush=True); time.sleep(10)"],
                stdout=subprocess.PIPE,
            )
            processes.append(process)
            process.stdout.readline()
            started.set()
            try:
                finish.wait(timeout=10)
            finally:
                process.terminate()
                process.communicate(timeout=5)

        thread = threading.Thread(target=worker)
        thread.start()
        try:
            self.assertTrue(started.wait(timeout=5))
            with TemporaryDirectory() as directory:
                journal = ExportJournal(Path(directory) / "output.mp4")
                children = journal._children()
                child = next(
                    (child for child in children if child["pid"] == processes[0].pid), None
                )
                self.assertIsNotNone(child, "Export worker's child was missing from diagnostics")
                self.assertGreater(child["memory"]["rss_kib"], 0)
                self.assertIn("swap_kib", child["memory"])
        finally:
            finish.set()
            thread.join(timeout=10)
            self.assertFalse(thread.is_alive())

    def test_heartbeat_callback_failure_is_propagated_and_retains_journal(self):
        from framestudio.export_journal import ExportJournal, journal_path

        def fail():
            raise ExportExecutionError("heartbeat refresh failed")

        with TemporaryDirectory() as directory:
            destination = Path(directory) / "output.mp4"
            with self.assertRaisesRegex(ExportExecutionError, "heartbeat refresh failed"):
                with ExportJournal(destination, heartbeat_seconds=0.01) as journal:
                    journal.heartbeat_callback = fail
                    self.assertIsNotNone(journal._thread)
                    journal._thread.join(timeout=2)
                    self.assertFalse(journal._thread.is_alive())
                    journal.progress(sample())
            self.assertTrue(journal_path(destination).exists())

    def test_overall_elapsed_and_eta_are_separate_from_current_operation_timing(self):
        from framestudio.export_progress import ExportProgressTracker

        updates = []
        with patch("framestudio.export_progress.time.monotonic", return_value=0) as clock:
            tracker = ExportProgressTracker(updates.append)
            tracker.configure((1,))
            tracker.begin_output(0)
            self.assertIsNone(updates[-1].overall_eta_seconds)
            clock.return_value = 10
            tracker(sample(50))
            self.assertEqual(updates[-1].overall_elapsed_seconds, 10)
            self.assertEqual(updates[-1].elapsed_seconds, 1)
            overall = updates[-1].overall_percent
            self.assertAlmostEqual(updates[-1].overall_eta_seconds, 10 * (100 - overall) / overall)
            clock.return_value = 20
            tracker.heartbeat()
            self.assertEqual(updates[-1].overall_elapsed_seconds, 20)
            self.assertEqual(updates[-1].elapsed_seconds, 1)
            self.assertEqual(updates[-1].overall_percent, overall)
            tracker.finish()
            self.assertEqual(updates[-1].overall_eta_seconds, 0)
            count = len(updates)
            tracker.heartbeat()
            self.assertEqual(len(updates), count)

    def test_heartbeat_never_replays_a_checkpoint_milestone(self):
        from framestudio.export_progress import ExportProgressTracker

        def sample(stage, percent):
            return ExportProgress(stage, percent, 0, 0, None, 0.0, None)

        updates = []
        tracker = ExportProgressTracker(updates.append)
        tracker.configure((1,))
        tracker.begin_output(0)
        tracker(sample("interpolated segment", 50))
        tracker(sample("Checkpointed interpolated segment", 100))
        checkpoints = len([u for u in updates if u.stage.startswith("Checkpointed")])
        tracker.heartbeat()
        self.assertEqual(
            len([u for u in updates if u.stage.startswith("Checkpointed")]), checkpoints
        )
        tracker(sample("interpolated segment", 10))
        tracker.heartbeat()
        self.assertEqual(updates[-1].stage, "interpolated segment")

    def test_journal_does_not_modify_sources_through_path_or_hardlink_aliases(self):
        from framestudio.export_journal import ExportJournal, journal_path

        with TemporaryDirectory() as directory:
            destination = Path(directory) / "output.mp4"
            source = journal_path(destination)
            source.write_bytes(b"original media")
            with self.assertRaises(ExportExecutionError):
                with ExportJournal(destination, protected_paths=(source,)):
                    pass
            self.assertEqual(source.read_bytes(), b"original media")
            link = source.with_name("source.mp4")
            os.link(source, link)
            with self.assertRaises(ExportExecutionError):
                with ExportJournal(destination):
                    pass
            self.assertEqual(link.read_bytes(), b"original media")

    def test_pending_corrupt_output_is_validated_and_rebuilt(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            event = threading.Event()
            calls = []

            def produce(path):
                calls.append(path)
                path.write_bytes(b"valid")
                if len(calls) == 1:
                    event.set()

            def validate(path):
                if path.read_bytes() != b"valid":
                    raise ExportExecutionError("corrupt")

            with self.assertRaisesRegex(ExportExecutionError, "cancelled"):
                RenderPreparations(root, cancel_event=event).materialize(
                    "interpolation", {}, produce, validate
                )
            next(root.rglob("*.pending.mp4")).write_bytes(b"broken")
            RenderPreparations(root).materialize("interpolation", {}, produce, validate)
            self.assertEqual(len(calls), 2)

    def test_finished_production_survives_cancellation_before_validation(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            event = threading.Event()
            writes = []

            def produce(path):
                writes.append(path)
                path.write_bytes(b"completed expensive operation")
                event.set()

            cache = RenderPreparations(root, cancel_event=event)
            with self.assertRaisesRegex(ExportExecutionError, "cancelled"):
                cache.materialize("interpolated segment", {}, produce, lambda path: None)
            event.clear()
            RenderPreparations(root).materialize(
                "interpolated segment", {}, produce, lambda path: None
            )
            self.assertEqual(len(writes), 1)

    def test_lookup_reuses_verified_fallback_without_starting_primary_backend(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            cache = RenderPreparations(root)
            path = cache.materialize(
                "interpolated segment",
                {"backend": "fallback"},
                lambda target: target.write_bytes(b"verified"),
                lambda target: None,
            )
            reopened = RenderPreparations(root)
            self.assertIsNone(reopened.reuse("interpolated segment", {"backend": "primary"}))
            self.assertEqual(reopened.reuse("interpolated segment", {"backend": "fallback"}), path)

    def test_global_progress_counts_all_outputs_and_preserves_local_percentage(self):
        from framestudio.export_progress import ExportProgressTracker, progress_scope

        updates = []
        tracker = ExportProgressTracker(updates.append)
        tracker.configure((3.0, 1.0))
        tracker.begin_output(0)
        scoped = progress_scope(tracker, 0, 80)
        scoped(sample(50))
        self.assertAlmostEqual(updates[-1].overall_percent, 32.075)
        self.assertEqual(updates[-1].current_percent, 50)
        tracker.finish_output(0)
        tracker.begin_output(1)
        tracker(sample(20))
        self.assertGreater(updates[-1].overall_percent, 75)
        self.assertLess(updates[-1].overall_percent, 100)
        self.assertEqual((updates[-1].output_index, updates[-1].output_count), (2, 2))
        tracker(sample(0, "verifying"))
        percentages = [p.overall_percent for p in updates]
        self.assertEqual(percentages, sorted(percentages))
        tracker.finish_output(1)
        self.assertLess(updates[-1].overall_percent, 100)
        tracker.finish()
        self.assertEqual(updates[-1].overall_percent, 100)

    def test_journal_records_failure_chain_and_is_removed_only_on_success(self):
        from framestudio.export_journal import ExportJournal, journal_path

        with TemporaryDirectory() as directory:
            destination = Path(directory) / "output.mp4"
            with self.assertRaisesRegex(RuntimeError, "interpolation failed"):
                with ExportJournal(destination) as journal:
                    journal.progress(sample())
                    try:
                        raise ValueError("decoder exited with code 9")
                    except ValueError as cause:
                        raise RuntimeError("interpolation failed") from cause
            path = journal_path(destination)
            records = [json.loads(line) for line in path.read_text().splitlines()]
            self.assertEqual(records[-1]["event"], "failed")
            self.assertIn("decoder exited with code 9", records[-1]["error"])
            self.assertIn("interpolation failed", records[-1]["error"])
            self.assertEqual(records[-1]["progress"]["stage"], "interpolation")
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            with ExportJournal(destination):
                self.assertTrue(path.exists())
            self.assertFalse(path.exists())

    def test_journal_survives_hard_kill_and_identifies_interrupted_previous_run(self):
        from framestudio.export_journal import ExportJournal, journal_path

        with TemporaryDirectory() as directory:
            destination = Path(directory) / "output.mp4"
            script = """
import sys, time
from pathlib import Path
from framestudio.export_journal import ExportJournal
with ExportJournal(Path(sys.argv[1]), heartbeat_seconds=0.05):
    print('ready', flush=True)
    time.sleep(30)
"""
            process = subprocess.Popen(
                [sys.executable, "-c", script, str(destination)],
                stdout=subprocess.PIPE,
                text=True,
            )
            try:
                self.assertEqual(process.stdout.readline().strip(), "ready")
                os.kill(process.pid, signal.SIGKILL)
                process.wait(timeout=5)
                path = journal_path(destination)
                self.assertTrue(path.is_file())
                with self.assertRaisesRegex(RuntimeError, "pause"):
                    with ExportJournal(destination):
                        records = [json.loads(line) for line in path.read_text().splitlines()]
                        self.assertTrue(records[-1]["previous_run_interrupted"])
                        raise RuntimeError("pause")
            finally:
                if process.poll() is None:
                    process.kill()
                    process.wait()
                process.stdout.close()

    def test_console_shows_overall_and_current_without_early_completion(self):
        import io

        from framestudio.export_console import ConsoleProgressReporter

        output = io.StringIO()
        report = ConsoleProgressReporter(stream=output, force=True)
        report(replace(sample(100, "complete"), overall_percent=40.0, current_percent=100.0))
        self.assertIn("Overall 40.0%", output.getvalue())
        self.assertIn("current 100.0%", output.getvalue())
        self.assertNotIn("Export complete.", output.getvalue())
