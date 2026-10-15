"""Preview-only decoder policy and opt-in real-system performance regression."""

import fcntl
import io
import json
import os
import shutil
import threading
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from benchmarks import playback_performance as benchmark
from benchmarks.playback_performance import fixture, make_layout, measure
from framestudio.composed_playback import FfmpegSynchronizedPlaybackBackend
from framestudio.ffmpeg_playback import (
    FfmpegComposedPlaybackBackend,
    FfmpegPlaybackBackend,
    _PreviewRequestCancelled,
)
from framestudio.model import Segment
from framestudio.playback import PlaybackBackendError


class BenchmarkToolTests(unittest.TestCase):
    def test_missing_required_tool_fails_instead_of_using_a_partial_path(self):
        with (
            patch("benchmarks.playback_performance.shutil.which", return_value=None),
            self.assertRaisesRegex(RuntimeError, "ffprobe is required"),
        ):
            benchmark._executable("ffprobe")


class PreviewDecoderPolicyTests(unittest.TestCase):
    def test_single_source_preview_and_realtime_preserve_accurate_input_seek(self):
        backend = FfmpegPlaybackBackend(
            Path("source.mp4"),
            1920,
            1080,
            30,
            8,
            lambda _frame: None,
            lambda _error: None,
            lambda: None,
        )
        try:
            for realtime in (False, True):
                command = backend._command(1.5, realtime=realtime)
                self.assertLess(command.index("-ss"), command.index("-i"))
                self.assertEqual(command[command.index("-ss") + 1], "1.500000")
                self.assertNotIn("-skip_frame", command)
        finally:
            backend.close()

    def test_composed_trim_mapping_and_audio_policy_remain_unchanged(self):
        backend = FfmpegComposedPlaybackBackend(
            (("source", Path("source.mp4")),),
            (Segment.create(2, 4, source_id="source"),),
            1920,
            1080,
            30,
            2,
            lambda _frame: None,
            lambda _error: None,
            lambda: None,
        )
        try:
            command = backend._command(0.5, realtime=False, frame_count=1)
            self.assertIn("2.500000", command)
            self.assertIn("trim=start=0.000000:duration=1.500000", " ".join(command))
            # Audio policy is deliberately independent of the video decoder budget.
            audio = backend._audio_command(0.5, realtime=True)
            self.assertNotIn("-threads", audio)
        finally:
            backend.close()

    def test_large_synchronized_project_opens_only_active_source_with_exact_seek(self):
        sources, layout = make_layout(Path("source.mp4"), 3840, 2160)
        backend = FfmpegSynchronizedPlaybackBackend(
            sources,
            layout,
            1920,
            1080,
            30,
            lambda _frame: None,
            lambda _error: None,
            lambda: None,
        )
        try:
            interval = backend._interval_at(4.125)
            command = backend._frame_command(4.125, interval)
            self.assertEqual(command.count("-i"), 1)
            self.assertEqual(command[command.index("-ss") + 1], "0.125")
            self.assertIn("flags=lanczos", " ".join(command))
            self.assertEqual(layout.final_duration_seconds, 40 * 3600)
        finally:
            backend.close()


class PersistentPlaybackTests(unittest.TestCase):
    def setUp(self):
        sources, layout = make_layout(Path("source.mp4"), 1920, 1080, 160, 90)
        self.backend = FfmpegSynchronizedPlaybackBackend(
            sources,
            layout,
            160,
            90,
            10,
            lambda _frame: None,
            lambda _error: None,
            lambda: None,
        )
        self.addCleanup(self.backend.close)

    def process(self, data=None):
        size = self.backend.frame_size

        class Process:
            returncode = 0
            stdin = None
            stdout = io.BytesIO(
                b"".join(bytes([index]) * size for index in range(20)) if data is None else data
            )
            stderr = io.BytesIO()

            def poll(self):
                return 0

            def wait(self, timeout=None):
                return 0

            def communicate(self, timeout=None):
                return bytes(size), b""

        return Process()

    def decode(self, position, cancel_check=lambda: False):
        return self.backend._frame_for_interval(
            position,
            self.backend._interval_at(position),
            cancel_check=cancel_check,
            process_attribute="_realtime_decode_process",
        )

    def test_realtime_reuses_decoder_and_labels_pixels_with_their_decoded_time(self):
        with patch(
            "framestudio.composed_playback.subprocess.Popen", return_value=self.process()
        ) as start:
            frames = [self.decode(position) for position in (0, 0.1, 0.2)]
        self.assertEqual(start.call_count, 1)
        self.assertEqual([frame.data[0] for frame in frames], [0, 1, 2])
        self.assertEqual([frame.position_seconds for frame in frames], [0, 0.1, 0.2])
        command = start.call_args.args[0]
        self.assertEqual(command[command.index("-threads") + 1], "4")
        self.assertEqual(command[command.index("-filter_complex_threads") + 1], "2")
        self.assertEqual(command[command.index("-threads:v") + 1], "1")
        self.assertIn("r=10:d=2", " ".join(command))

    def test_late_frames_are_discarded_without_relabeling_old_pixels_as_current(self):
        with patch(
            "framestudio.composed_playback.subprocess.Popen", return_value=self.process()
        ) as start:
            first = self.decode(0)
            late = self.decode(0.35)
        self.assertEqual(start.call_count, 1)
        self.assertEqual(first.data[0], 0)
        self.assertEqual(late.data[0], 3)
        self.assertAlmostEqual(late.position_seconds, 0.3)
        self.assertAlmostEqual(late.decoded_position_seconds, 0.3)
        self.assertEqual(self.backend.playback_stats()["dropped_frames"], 2)

    def test_interval_transition_restarts_only_active_input_at_exact_source_offset(self):
        first, second = self.process(), self.process()
        with patch(
            "framestudio.composed_playback.subprocess.Popen", side_effect=(first, second)
        ) as start:
            self.decode(0)
            frame = self.decode(2.125)
        self.assertEqual(start.call_count, 2)
        self.assertTrue(first.stdout.closed)
        command = start.call_args.args[0]
        self.assertEqual(command.count("-i"), 1)
        self.assertEqual(command[command.index("-ss") + 1], "0.125")
        self.assertEqual(frame.position_seconds, 2.125)

    def test_truncated_stream_is_an_explicit_failure_not_a_successful_end(self):
        with (
            patch(
                "framestudio.composed_playback.subprocess.Popen", return_value=self.process(b"x")
            ),
            self.assertRaisesRegex(PlaybackBackendError, "incomplete synchronized playback"),
        ):
            self.decode(0)

    def test_generation_invalidated_during_start_never_registers_decoder(self):
        process = self.process()

        def start(*args, **kwargs):
            self.backend._playback_generation += 1
            return process

        with (
            patch("framestudio.composed_playback.subprocess.Popen", side_effect=start),
            self.assertRaises(_PreviewRequestCancelled),
        ):
            self.decode(0)
        self.assertIsNone(self.backend._realtime_decode_process)
        self.assertIsNone(self.backend._realtime_decoder)
        self.assertTrue(process.stdout.closed)

    def test_interval_release_kills_decoder_without_waiting_for_an_unread_pipe_to_flush(self):
        process = self.process()
        killed = []
        process.poll = lambda: -9 if killed else None
        process.kill = lambda: killed.append(True)

        def terminate():
            self.fail("Graceful FFmpeg termination can block flushing an unread raw pipe")

        process.terminate = terminate
        try:
            with patch("framestudio.composed_playback.subprocess.Popen", return_value=process):
                self.decode(0)
                self.backend._release_realtime_decoder()
            self.assertEqual(killed, [True])
            self.assertTrue(process.stdout.closed)
        finally:
            process.poll = lambda: 0

    def test_error_reader_start_failure_reaps_unregistered_decoder(self):
        process = self.process()
        with (
            patch("framestudio.composed_playback.subprocess.Popen", return_value=process),
            patch("framestudio.composed_playback.threading.Thread.start", side_effect=RuntimeError),
            self.assertRaisesRegex(PlaybackBackendError, "error reader"),
        ):
            self.decode(0)
        self.assertIsNone(self.backend._realtime_decoder)
        self.assertTrue(process.stdout.closed)


@unittest.skipUnless(
    os.environ.get("FRAMESTUDIO_RUN_PLAYBACK_PERFORMANCE") == "1",
    "opt-in real 1080p/4K decoder benchmark",
)
class PlaybackPerformanceFunctionalityTests(unittest.TestCase):
    def test_actual_1080p_4k_source_transitions_in_large_metadata_layout(self):
        root = Path(os.environ["FRAMESTUDIO_PLAYBACK_PERFORMANCE_DIRECTORY"])
        lock_path = Path(os.environ["FRAMESTUDIO_PLAYBACK_PERFORMANCE_LOCK"])
        with lock_path.open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            first, first_metadata = fixture(root, 1920, 1080)
            second, second_metadata = fixture(root, 3840, 2160)
            result = measure(
                first,
                1920,
                1080,
                synchronized=True,
                repeats=1,
                alternate_source=(second, 3840, 2160),
            )
            (root.parent / "decoder-performance-mixed-functionality.json").write_text(
                json.dumps(
                    {
                        "fixtures": [first_metadata, second_metadata],
                        "result": result,
                        "metadata_only": "200 logical sources/40h; actual fixtures are 8s each",
                    },
                    indent=2,
                )
                + "\n"
            )
            self.assertEqual(result["errors"], [])
            self.assertEqual(result["mixed_source_size"], [3840, 2160])
            self.assertEqual(len(result["source_hashes"]), 2)
            self.assertTrue(result["source_preserved"])
            self.assertEqual(result["playback_stats"]["decoder_starts"], 3)
            self.assertGreater(result["playback"]["delivered_fps"], 18)
            positions = [position for _at, position in result["playback"]["frames"]]
            self.assertTrue(any(2 <= position < 2.3 for position in positions))
            self.assertTrue(any(4 <= position < 4.3 for position in positions))
            fcntl.flock(lock, fcntl.LOCK_UN)

    def test_moving_source_pixels_match_exact_seeks_through_fractional_interval_tail(self):
        root = Path(os.environ["FRAMESTUDIO_PLAYBACK_PERFORMANCE_DIRECTORY"])
        lock_path = Path(os.environ["FRAMESTUDIO_PLAYBACK_PERFORMANCE_LOCK"])
        with lock_path.open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            source, _metadata = fixture(root, 1920, 1080)
            sources, layout = make_layout(source, 1920, 1080, 160, 90)
            backend = FfmpegSynchronizedPlaybackBackend(
                sources,
                layout,
                160,
                90,
                30,
                lambda _frame: None,
                lambda _error: None,
                lambda: None,
            )
            try:
                for frame_index in (0, 3, 59):
                    position = 0.017 + frame_index / 30
                    interval = backend._interval_at(position)
                    reference = backend._frame_for_interval(position, interval)
                    streamed = backend._frame_for_interval(
                        position,
                        interval,
                        process_attribute="_realtime_decode_process",
                    )
                    self.assertAlmostEqual(streamed.position_seconds, position)
                    self.assertEqual(streamed.data, reference.data)
            finally:
                backend.close()
            fcntl.flock(lock, fcntl.LOCK_UN)

    def test_fractional_start_and_terminal_interval_end_cleanly(self):
        root = Path(os.environ["FRAMESTUDIO_PLAYBACK_PERFORMANCE_DIRECTORY"])
        lock_path = Path(os.environ["FRAMESTUDIO_PLAYBACK_PERFORMANCE_LOCK"])
        with lock_path.open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            source, _metadata = fixture(root, 1920, 1080)
            sources, layout = make_layout(source, 1920, 1080, 160, 90)
            layout = replace(
                layout,
                final_duration_ticks=6_000_000,
                intervals=layout.intervals[:3],
                included_blocks=layout.included_blocks[:3],
                boundaries=(0, 2_000_000, 4_000_000, 6_000_000),
            )
            ended = threading.Event()
            errors = []
            positions = []
            backend = FfmpegSynchronizedPlaybackBackend(
                sources,
                layout,
                160,
                90,
                29.97,
                lambda frame: positions.append(frame.position_seconds),
                errors.append,
                ended.set,
            )
            try:
                backend.seek(0.017)
                backend.play()
                self.assertTrue(ended.wait(9), errors)
                self.assertEqual(errors, [])
                self.assertEqual(backend.current_position(), 6)
                self.assertGreater(len(positions), 100)
                self.assertTrue(all(0 <= position < 6 for position in positions))
                self.assertIsNone(backend._realtime_decode_process)
            finally:
                backend.close()
            fcntl.flock(lock, fcntl.LOCK_UN)

    def test_persistent_pixels_match_exact_seek_for_transforms_triplicate_and_black_gaps(self):
        from tests.test_editor_composed_preview import build_four_track_fixture, isolated_directory

        lock_path = Path(os.environ["FRAMESTUDIO_PLAYBACK_PERFORMANCE_LOCK"])
        with lock_path.open("a") as lock, isolated_directory("persistent-composition") as root:
            fcntl.flock(lock, fcntl.LOCK_EX)
            fixture_data = build_four_track_fixture(root)
            backend = FfmpegSynchronizedPlaybackBackend(
                tuple(
                    (source.source_id, Path(source.path)) for source in fixture_data.project.sources
                ),
                fixture_data.layout,
                1920,
                1080,
                12,
                lambda _frame: None,
                lambda _error: None,
                lambda: None,
            )
            try:
                for position in (1.75, 2.25, 3.25, 3.75, 4.375):
                    with self.subTest(position=position):
                        interval = backend._interval_at(position)
                        reference = backend._frame_for_interval(position, interval)
                        streamed = backend._frame_for_interval(
                            position,
                            interval,
                            process_attribute="_realtime_decode_process",
                        )
                        self.assertEqual(streamed.position_seconds, position)
                        self.assertEqual(streamed.data, reference.data)
                import hashlib

                for source, digest in fixture_data.source_hashes.items():
                    self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), digest)
            finally:
                backend.close()
            fcntl.flock(lock, fcntl.LOCK_UN)

    def test_real_long_gop_seek_and_large_project_transitions_preserve_sources(self):
        root = Path(os.environ["FRAMESTUDIO_PLAYBACK_PERFORMANCE_DIRECTORY"])
        lock_path = Path(os.environ["FRAMESTUDIO_PLAYBACK_PERFORMANCE_LOCK"])
        root.mkdir(parents=True, exist_ok=True)
        self.assertTrue(shutil.which("ffmpeg"))
        with lock_path.open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            for width, height in ((1920, 1080), (3840, 2160)):
                with self.subTest(source_size=(width, height)):
                    source, _metadata = fixture(root, width, height)
                    result = measure(
                        source,
                        width,
                        height,
                        synchronized=True,
                        repeats=2,
                    )
                    self.assertEqual(result["errors"], [])
                    self.assertTrue(result["source_preserved"])
                    self.assertEqual(result["preview_stats"]["failures"], 0)
                    self.assertEqual(result["playback_stats"]["decoder_starts"], 3)
                    self.assertLess(result["seek_latency_ms"]["p95"], 1000)
                    self.assertGreater(result["playback"]["delivered_fps"], 18)
                    positions = [position for _at, position in result["playback"]["frames"]]
                    self.assertTrue(any(1.8 < position < 2 for position in positions))
                    self.assertTrue(any(2 <= position < 2.3 for position in positions))
                    self.assertTrue(any(4 <= position < 4.4 for position in positions))
                    for sample in result["samples"]:
                        self.assertAlmostEqual(sample["position"], sample["target"], places=6)
                        self.assertEqual(sample["dimensions"], [1920, 1080])
                        self.assertEqual(sample["frame_bytes"], 1920 * 1080 * 4)
            fcntl.flock(lock, fcntl.LOCK_UN)


if __name__ == "__main__":
    unittest.main()
