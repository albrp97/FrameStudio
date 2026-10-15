from __future__ import annotations

import hashlib
import shutil
import unittest
import uuid
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import Mock, patch

from benchmarks import large_project_preview as benchmark


class LargeProjectBenchmarkTests(unittest.TestCase):
    def setUp(self):
        self.directory = Path("tests") / f".large-project-{uuid.uuid4().hex}"
        self.directory.mkdir()
        self.addCleanup(shutil.rmtree, self.directory)
        self.fixture = self.directory / "fixture.mp4"
        self.fixture.write_bytes(b"encoded fixture")

    def test_copies_are_regular_distinct_files_with_same_content(self):
        copies = benchmark.copy_sources(self.fixture, self.directory / "sources", 20)
        self.assertEqual(len(copies), 20)
        self.assertEqual(len({path.stat().st_ino for path in copies}), 20)
        self.assertNotIn(self.fixture.stat().st_ino, {path.stat().st_ino for path in copies})
        self.assertTrue(all(not path.is_symlink() for path in copies))
        self.assertEqual(
            {benchmark.sha256(path) for path in copies}, {benchmark.sha256(self.fixture)}
        )

    def test_sha256_covers_empty_files_and_multiple_streaming_buffers(self):
        for payload in (b"", b"exact frame reference" * (128 * 1024)):
            self.fixture.write_bytes(payload)
            self.assertEqual(benchmark.sha256(self.fixture), hashlib.sha256(payload).hexdigest())

    def test_invalid_counts_are_rejected_without_creating_directory(self):
        for count in (0, -1):
            with self.assertRaises(ValueError):
                benchmark.copy_sources(self.fixture, self.directory / "bad", count)
        self.assertFalse((self.directory / "bad").exists())

    def test_default_count_matrix_uses_distinct_inodes(self):
        for count in (2, 20, 200):
            with self.subTest(count=count):
                paths = benchmark.copy_sources(
                    self.fixture, self.directory / f"count-{count}", count
                )
                self.assertEqual(len(paths), count)
                self.assertEqual(
                    len({(path.stat().st_dev, path.stat().st_ino) for path in paths}), count
                )

    def test_active_source_is_half_open_and_end_maps_to_last_frame(self):
        self.assertEqual(benchmark.source_at(0.5, (8.0,) * 20, 30), (0, 0.5))
        self.assertEqual(benchmark.source_at(8.0, (8.0,) * 20, 30), (1, 0.0))
        index, offset = benchmark.source_at(160, (8.0,) * 20, 30)
        self.assertEqual(index, 19)
        self.assertAlmostEqual(offset, 8 - 1 / 30)

    def test_window_has_at_most_five_upcoming_sources_and_correct_offset(self):
        self.assertEqual(benchmark.window_at(9.5, (8.0,) * 20, 30), (1, 6, 8.0))
        self.assertEqual(benchmark.window_at(160, (8.0,) * 20, 30), (19, 20, 152.0))
        self.assertEqual(benchmark.window_at(0, (8.0,) * 2, 30), (0, 2, 0.0))

    def test_traces_have_true_source_offsets_and_six_rapid_targets(self):
        traces = benchmark.make_traces(20, 8.0)
        self.assertEqual(
            [position for name, position in traces if name.startswith("clip-10")],
            [80.5, 81.5, 82.5],
        )
        self.assertEqual(sum(name == "rapid" for name, _ in traces), 6)
        adjacent = [position for name, position in traces if name == "adjacent"]
        self.assertEqual(adjacent, [0.5, 8.5, 16.5, 24.5, 32.5, 0.5])
        self.assertTrue(all(0 <= position < 160 for _, position in traces))

    def test_missing_tool_is_an_explicit_error(self):
        with patch.object(shutil, "which", return_value=None):
            with self.assertRaisesRegex(RuntimeError, "ffmpeg.*required"):
                benchmark.require_tool("ffmpeg")

    def test_cuda_injection_preserves_filters_and_cpu_output_format(self):
        original = [
            "ffmpeg",
            "-ss",
            "0.5",
            "-noautorotate",
            "-i",
            "input.mp4",
            "-filter_complex",
            "legacy-filter",
            "-pix_fmt",
            "rgba",
            "pipe:1",
        ]
        command = benchmark.cuda_input_command(original)
        self.assertEqual(command.count("-i"), 1)
        self.assertEqual(
            command[command.index("-i") - 2 : command.index("-i")], ["-hwaccel", "cuda"]
        )
        self.assertNotIn("-hwaccel_output_format", command)
        self.assertEqual(
            command[command.index("-filter_complex") :],
            original[original.index("-filter_complex") :],
        )
        self.assertNotIn("-hwaccel", original)
        with self.assertRaisesRegex(ValueError, "single"):
            benchmark.cuda_input_command(["ffmpeg", "-i", "a", "-i", "b"])

    def test_bounded_trace_matches_first_and_middle_source_offsets(self):
        self.assertEqual(benchmark.bounded_traces(200, 8), [("first", 0.5), ("middle", 800.5)])
        self.assertEqual(benchmark.bounded_traces(2, 8), [("first", 0.5), ("middle", 8.5)])

    def test_thread_reporting_distinguishes_decoder_filter_and_output_options(self):
        command = [
            "ffmpeg",
            "-filter_complex_threads",
            "2",
            "-threads",
            "4",
            "-i",
            "source.mp4",
            "-threads:v",
            "1",
            "-pix_fmt",
            "rgba",
            "pipe:1",
        ]
        self.assertEqual(
            benchmark.thread_options(command),
            {
                "decoder_threads": ["4"],
                "filter_complex_threads": ["2"],
                "filter_threads": [],
                "output_video_threads": ["1"],
            },
        )
        self.assertEqual(
            benchmark.thread_options(["ffmpeg", "-i", "source.mp4"])["decoder_threads"], []
        )

    def test_no_guard_alias_disables_command_mutation(self):
        with patch.object(
            benchmark.sys, "argv", ["benchmark", "--artifact-dir", "artifacts", "--no-guard"]
        ):
            self.assertTrue(benchmark.parse_args().unmodified_ffmpeg)

    def test_functionality_charter_is_explicit_opt_in(self):
        with patch.object(
            benchmark.sys, "argv", ["benchmark", "--artifact-dir", "artifacts", "--functionality"]
        ):
            self.assertTrue(benchmark.parse_args().functionality)

    def test_functionality_save_cannot_write_user_autosave(self):
        from framestudio import app_project

        window = SimpleNamespace(
            project=object(),
            segment_timeline=SimpleNamespace(segment_items=(1, 2, 3)),
            _attach_project=Mock(),
            _stop_backend=Mock(),
        )

        def save(path):
            path.write_text("{}")
            app_project.autosave_current_project(window)

        window._save_to = save
        window._on_reopen_clicked = lambda _: setattr(window, "project", object())
        result: dict[str, Any] = {"errors": []}
        with (
            patch.object(app_project, "autosave_current_project") as user_autosave,
            patch.object(benchmark, "_audit_edits", return_value={}),
            patch.object(benchmark, "_audit_route_frame", return_value={"exact_legacy": True}),
            patch.object(
                benchmark, "owned_processes", return_value={benchmark.os.getpid(): (0, 0)}
            ),
        ):
            benchmark._optional_functionality(
                {"functionality": True, "timeout": 15},
                result,
                window,
                self.directory,
                Mock(),
                Mock(),
            )
        user_autosave.assert_not_called()
        self.assertEqual(result["functionality"]["status"], "complete")
        self.assertEqual(result["functionality"]["checks"]["audio_scan_calls"], 0)

    def test_edit_charter_selects_new_left_id_after_split_replaces_original(self):
        timeline = SimpleNamespace(
            segment_items=[
                SimpleNamespace(segment_id="original"),
                SimpleNamespace(segment_id="next"),
            ],
            edited_duration_seconds=16,
        )
        window = SimpleNamespace(segment_timeline=timeline, _seek_timeline=Mock())
        selected = []
        window._on_timeline_selection_changed = lambda ids: selected.append(ids[0])

        def split(_button):
            timeline.segment_items = [
                SimpleNamespace(segment_id="left"),
                SimpleNamespace(segment_id="right"),
                SimpleNamespace(segment_id="next"),
            ]

        def toggle(_button):
            if selected[-1] != "left":
                raise AssertionError("Unknown segment selected after split")
            timeline.edited_duration_seconds = 14 if timeline.edited_duration_seconds == 16 else 16

        window._on_split_clicked = split
        window._on_delete_segment_clicked = toggle
        with patch.object(benchmark, "_audit_route_frame", return_value={"exact_legacy": True}):
            benchmark._audit_edits(window, Mock())
        self.assertEqual(selected, ["original", "left"])
        self.assertEqual(timeline.edited_duration_seconds, 16)

    def test_rapid_report_proves_latest_target_and_reports_stale_counter_delta(self):
        result: dict[str, Any] = {
            "repetition": 2,
            "samples": [
                {
                    "painted_position_seconds": 8.5,
                    "backend_stats": {
                        "preview": {
                            "stale_frames": 5,
                            "cancelled_requests": 9,
                            "coalesced_requests": 4,
                        }
                    },
                }
            ],
        }
        benchmark._record_rapid(
            result,
            [0.5, 8.5],
            {
                "stale_frames": 2,
                "cancelled_requests": 3,
                "coalesced_requests": 1,
            },
        )
        report = result["rapid_batches"][0]
        self.assertTrue(report["latest_target_painted"])
        self.assertEqual(report["stale_frames_delta"], 3)
        self.assertEqual(report["cancelled_requests_delta"], 6)
        self.assertEqual(report["coalesced_requests_delta"], 3)

    def test_lock_wait_retries_inside_harness_without_nested_lock(self):
        with (
            patch.object(benchmark.fcntl, "flock", side_effect=[BlockingIOError(), None]) as flock,
            patch.object(benchmark.time, "monotonic", return_value=10),
            patch.object(benchmark.time, "sleep") as sleep,
        ):
            benchmark.acquire_lock(Mock(fileno=lambda: 7), 1)
        self.assertEqual(flock.call_count, 2)
        sleep.assert_called_once()

    def test_quality_rejection_survives_nonzero_worker_exit(self):
        benchmark.write_json(
            self.directory / "result.json", {"status": "rejected-quality", "quality_rejected": True}
        )
        process = Mock(pid=999999999, returncode=1)
        process.poll.return_value = 1
        with (
            patch.object(benchmark.subprocess, "Popen", return_value=process),
            patch.object(benchmark, "gpu_usage", return_value=(None, "not sampled in test")),
        ):
            result = benchmark.run_case({}, self.directory, 15, 2 * 1024**3)
        self.assertEqual(result["status"], "rejected-quality")
        self.assertEqual(result["returncode"], 1)

    def test_guard_limits_each_input_not_output_alone(self):
        command = benchmark.guard_command(
            ["ffmpeg", "-i", "a.mp4", "-ss", "1", "-i", "b.mp4", "pipe:1"]
        )
        self.assertEqual(command.count("-threads"), 2)
        self.assertIn("-filter_complex_threads", command)
        for index, item in enumerate(command):
            if item == "-i":
                self.assertEqual(command[index - 2 : index], ["-threads", "1"])

    def test_real_create_multi_stays_legacy_ripple_and_commands_expose_tail_bug(self):
        from framestudio.composed_playback import FfmpegSynchronizedPlaybackBackend
        from framestudio.ffmpeg_playback import FfmpegComposedPlaybackBackend
        from framestudio.layout_plan import plan_project_layout
        from framestudio.model import Project

        paths = tuple(
            path.resolve()
            for path in benchmark.copy_sources(self.fixture, self.directory / "sources", 20)
        )
        metadata = {
            "duration_seconds": 8.0,
            "width": 1920,
            "height": 1080,
            "frame_rate": "30/1",
            "sample_aspect_ratio": "1:1",
        }
        project = Project.create_multi([(path, metadata) for path in paths])
        timeline = project.segment_timeline
        assert timeline is not None
        self.assertEqual(timeline.timing_mode, "legacy-ripple")
        self.assertEqual(project.duration_seconds, 160)
        sources = tuple(
            (source.source_id, Path(source.path)) for source in project.sources or (project.source,)
        )
        common: dict[str, Any] = dict(
            width=1920,
            height=1080,
            frame_rate=30,
            on_frame=lambda _: None,
            on_error=lambda _: None,
            on_end=lambda: None,
        )
        legacy = FfmpegComposedPlaybackBackend(
            sources,
            timeline.active_blocks(),
            duration_seconds=160,
            **common,
        )
        active = FfmpegSynchronizedPlaybackBackend(sources, plan_project_layout(project), **common)
        self.addCleanup(legacy.close)
        self.addCleanup(active.close)
        tail = legacy._command(9.5, realtime=False, frame_count=1)
        self.assertEqual(tail.count("-i"), 20)
        self.assertIn("concat=n=19:", tail[tail.index("-filter_complex") + 1])
        window = benchmark.window_command(legacy, 9.5, realtime=False, frame_count=1)
        self.assertEqual(window.count("-i"), 5)
        self.assertNotIn(str(paths[0]), window)
        self.assertIn(str(paths[1]), window)
        self.assertNotIn(str(paths[6]), window)
        self.assertIn("concat=n=5:", window[window.index("-filter_complex") + 1])
        end = benchmark.window_command(legacy, 160, realtime=False, frame_count=1)
        self.assertEqual(end.count("-i"), 1)
        self.assertIn(str(paths[-1]), end)
        self.assertNotIn(str(paths[0]), end)
        interval = active._interval_at(9.5)
        assert interval is not None
        command = active._frame_command(9.5, interval)
        self.assertEqual(command.count("-i"), 1)
        self.assertIn(str(paths[1]), command)


if __name__ == "__main__":
    unittest.main()
