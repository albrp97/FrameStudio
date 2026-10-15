from __future__ import annotations

import hashlib
import io
import shutil
import subprocess
import threading
import unittest
import uuid
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from framestudio.composition import TriplicateGroup, VisualTransform
from framestudio.ffmpeg_playback import (
    FfmpegComposedPlaybackBackend,
    _PreviewRequestCancelled,
)
from framestudio.layout_plan import PixelRect, plan_project_layout
from framestudio.model import Project, SegmentTimeline, SourceReference
from framestudio.playback import PlaybackBackendError
from framestudio.sequential_playback import FfmpegSequentialPlaybackBackend


def project_with_sources(count=3, path=None, duration=2.0):
    sources = []
    for index in range(count):
        source_path = (path or Path(f"source-{index}.mp4")).resolve()
        sources.append(
            SourceReference(
                f"source-{index}",
                str(source_path),
                source_path.as_uri(),
                0,
                0,
                {
                    "duration_seconds": duration,
                    "width": 160,
                    "height": 90,
                    "frame_rate": "10/1",
                    "audio_stream_present": False,
                },
            )
        )
    return Project.create_multi(sources)


def backend_for(project, **options):
    width = options.pop("width", 192)
    height = options.pop("height", 108)
    return FfmpegSequentialPlaybackBackend(
        tuple((source.source_id, Path(source.path)) for source in project.sources),
        project.timeline.segment_items,
        plan_project_layout(project, canvas=PixelRect(0, 0, width, height)),
        width,
        height,
        options.pop("frame_rate", 10),
        options.pop("on_frame", lambda _frame: None),
        options.pop("on_error", lambda _error: None),
        options.pop("on_end", lambda: None),
        **options,
    )


def with_blocks(project, blocks):
    return replace(
        project,
        segment_timeline=SegmentTimeline.from_blocks(
            blocks,
            duration_seconds=project.duration_seconds,
            source_durations={
                source.source_id: source.metadata["duration_seconds"] for source in project.sources
            },
        ),
    )


class SequentialPlaybackTests(unittest.TestCase):
    def make_backend(self, project=None, **options):
        backend = backend_for(project or project_with_sources(), **options)
        self.addCleanup(backend.close)
        return backend

    def test_two_hundred_sources_open_only_the_active_input_and_one_segment_graph(self):
        project = project_with_sources(200)
        backend = self.make_backend(project)
        for position, source_index, offset in ((0, 0, 0), (203.125, 101, 1.125)):
            with self.subTest(position=position):
                interval = backend._interval_at(position)
                for continuous in (False, True):
                    command = backend._video_command(position, interval, continuous=continuous)
                    self.assertEqual(command.count("-i"), 1)
                    self.assertEqual(
                        command[command.index("-i") + 1], project.sources[source_index].path
                    )
                    self.assertAlmostEqual(float(command[command.index("-ss") + 1]), offset)
                    graph = command[command.index("-filter_complex") + 1]
                    self.assertEqual(graph.count("trim=start="), 1)
                    self.assertIn("concat=n=1:v=1:a=0", graph)
                    self.assertNotIn("lanczos", graph)
                    self.assertNotIn("overlay", graph)
                    self.assertIn("fps=10", graph)

    def test_saved_legacy_timeline_compacts_deleted_blocks_and_maps_source_offsets(self):
        project = project_with_sources()
        blocks = list(project.timeline.segment_items)
        blocks[0] = replace(
            blocks[0],
            start_seconds=0.5,
            end_seconds=1.5,
            timeline_start_seconds=0,
            timeline_end_seconds=1,
        )
        blocks[1] = replace(blocks[1], deleted=True)
        project = Project.from_dict(with_blocks(project, blocks).to_dict())
        backend = self.make_backend(project)
        self.assertEqual(backend.duration_seconds, 3)
        for position, source_id, source_offset in (
            (0, "source-0", 0.5),
            (0.75, "source-0", 1.25),
            (1, "source-2", 0),
            (2.5, "source-2", 1.5),
        ):
            interval = backend._interval_at(position)
            self.assertEqual(interval.active_blocks[0].source_id, source_id)
            command = backend._frame_command(position, interval)
            self.assertEqual(float(command[command.index("-ss") + 1]), source_offset)
        self.assertIsNone(backend._interval_at(3))
        self.assertEqual(backend._decode_preview_frame(3).data, backend._black_frame)

    def test_paused_budget_is_cpu_bounded_and_streaming_keeps_its_playback_budget(self):
        backend = self.make_backend()
        interval = backend._interval_at(0.5)
        for available, expected in ((12, 8), (2, 2), (None, 1)):
            with self.subTest(available=available), patch("os.cpu_count", return_value=available):
                command = backend._frame_command(0.5, interval)
                self.assertIn("-threads", command)
                self.assertEqual(command[command.index("-threads") + 1], str(expected))
                self.assertEqual(command[command.index("-filter_complex_threads") + 1], "2")
                self.assertEqual(command[command.index("-threads:v") + 1], "1")
        stream = backend._video_command(0.5, interval, continuous=True)
        self.assertEqual(stream[stream.index("-threads") + 1], "4")

    def test_native_request_is_explicit_reference_ffmpeg_fallback_without_helper(self):
        warnings = []
        backend = self.make_backend(preview_backend="cuda", on_warning=warnings.append)
        self.assertIsNone(backend._precise_preview)
        self.assertEqual(backend.precise_preview_stats()["selected_engine"], "ffmpeg")
        self.assertIn("sequential", backend.precise_preview_stats()["fallback_reason"].lower())
        self.assertIn("not validated", backend.precise_preview_stats()["fallback_reason"])
        self.assertTrue(warnings)

    def test_invalid_requested_engine_and_nonsequential_layout_are_rejected(self):
        with self.assertRaises(PlaybackBackendError):
            backend_for(project_with_sources(), preview_backend="unknown")
        project = project_with_sources()
        layout = plan_project_layout(project, canvas=PixelRect(0, 0, 192, 108))
        with self.assertRaisesRegex(ValueError, "legacy-ripple"):
            FfmpegSequentialPlaybackBackend(
                tuple((source.source_id, Path(source.path)) for source in project.sources),
                project.timeline.segment_items,
                replace(layout, timing_mode="absolute"),
                192,
                108,
                10,
                lambda _: None,
                lambda _: None,
                lambda: None,
            )

    def test_fractional_tail_command_preserves_trim_and_bounds_continuous_frames(self):
        project = project_with_sources(1, duration=1.05)
        backend = self.make_backend(project)
        interval = backend._interval_at(0.9)
        command = backend._video_command(0.9, interval, continuous=True)
        self.assertIn("trim=start=0.000000:duration=0.150000", " ".join(command))
        self.assertEqual(command[command.index("-frames:v") + 1], "2")
        still = backend._frame_command(0.9, interval)
        self.assertEqual(still[still.index("-frames:v") + 1], "1")

    def process(self, backend, count=30):
        class Process:
            returncode = 0
            stdin = None
            stdout = io.BytesIO(
                b"".join(bytes([index]) * backend.frame_size for index in range(count))
            )
            stderr = io.BytesIO()

            def poll(self):
                return 0

            def wait(self, timeout=None):
                return 0

        return Process()

    def test_realtime_decoder_reused_until_compacted_clip_boundary_and_release(self):
        backend = self.make_backend()
        first, second = self.process(backend), self.process(backend)
        with patch(
            "framestudio.composed_playback.subprocess.Popen", side_effect=(first, second)
        ) as start:
            for position in (0, 0.1, 0.2):
                frame = backend._frame_for_interval(
                    position,
                    backend._interval_at(position),
                    process_attribute="_realtime_decode_process",
                )
                self.assertAlmostEqual(frame.decoded_position_seconds, position)
            self.assertEqual(start.call_count, 1)
            backend._frame_for_interval(
                2, backend._interval_at(2), process_attribute="_realtime_decode_process"
            )
            self.assertEqual(start.call_count, 2)
            self.assertTrue(first.stdout.closed)
            backend.release_preview_resources()
        self.assertTrue(second.stdout.closed)
        self.assertIsNone(backend._realtime_decoder)
        self.assertIsNone(backend._realtime_decode_process)

    def test_cancelled_generation_does_not_deliver_stale_preview(self):
        frames, errors = [], []
        first_started, latest_finished = threading.Event(), threading.Event()
        delivered = threading.Event()

        def receive(frame):
            frames.append(frame)
            delivered.set()

        backend = self.make_backend(on_frame=receive, on_error=errors.append)
        original = backend._run_decode_command

        def decode(command, *, cancel_check, process_attribute):
            offset = float(command[command.index("-ss") + 1])
            if offset == 0.1:
                first_started.set()
                self.assertTrue(latest_finished.wait(2))
                if cancel_check():
                    raise _PreviewRequestCancelled
            return bytes([int(offset * 10)]) * backend.frame_size, b""

        try:
            backend._run_decode_command = decode
            backend.request_preview(0.1)
            self.assertTrue(first_started.wait(2))
            backend.request_preview(2.5)
            latest_finished.set()
            self.assertTrue(delivered.wait(3))
            self.assertEqual(errors, [])
            self.assertEqual([frame.position_seconds for frame in frames], [2.5])
            self.assertEqual(frames[0].data[0], 5)
        finally:
            latest_finished.set()
            backend.close()
            backend._run_decode_command = original

    def test_close_and_stop_release_persistent_decoders(self):
        for action in ("stop", "close"):
            with self.subTest(action=action):
                backend = self.make_backend()
                process = self.process(backend)
                with patch("framestudio.composed_playback.subprocess.Popen", return_value=process):
                    backend._frame_for_interval(
                        0,
                        backend._interval_at(0),
                        process_attribute="_realtime_decode_process",
                    )
                    getattr(backend, action)()
                self.assertTrue(process.stdout.closed)
                self.assertIsNone(backend._realtime_decoder)

    def test_cache_identity_separates_original_framing_and_replaced_source(self):
        project = project_with_sources(1)
        original = self.make_backend(project)
        block = project.timeline.segment_items[0]
        focused = self.make_backend(
            with_blocks(project, (replace(block, visual_transform=VisualTransform(1.7, 12, -8)),))
        )
        triplicate = self.make_backend(
            with_blocks(project, (replace(block, triplicate=TriplicateGroup.create()),))
        )
        namespaces = {
            backend._preview_cache_namespace(0) for backend in (original, focused, triplicate)
        }
        self.assertEqual(len(namespaces), 3)
        with patch("pathlib.Path.stat") as stat:
            stat.return_value.st_dev = 1
            stat.return_value.st_ino = 2
            stat.return_value.st_size = 3
            stat.return_value.st_mtime_ns = 4
            first = original._preview_cache_namespace(0)
            stat.return_value.st_mtime_ns = 5
            self.assertNotEqual(first, original._preview_cache_namespace(0))

    def test_mismatched_original_block_range_cannot_silently_render_wrong_source_time(self):
        project = project_with_sources(1)
        blocks = (replace(project.timeline.segment_items[0], start_seconds=0.5),)
        with self.assertRaisesRegex(ValueError, "does not match"):
            FfmpegSequentialPlaybackBackend(
                ((project.source.source_id, Path(project.source.path)),),
                blocks,
                plan_project_layout(project, canvas=PixelRect(0, 0, 192, 108)),
                192,
                108,
                10,
                lambda _: None,
                lambda _: None,
                lambda: None,
            )


@unittest.skipUnless(shutil.which("ffmpeg"), "FFmpeg is required")
class SequentialReferencePixelsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = Path.cwd() / f".sequential-playback-fixtures-{uuid.uuid4().hex}"
        cls.root.mkdir()
        cls.addClassCleanup(shutil.rmtree, cls.root)
        cls.paths = []
        for index, (size, sar, rate, vfr) in enumerate(
            (
                ("160x90", "1/1", "10", False),
                ("90x160", "4/3", "30000/1001", False),
                ("160x90", "1/1", "30000/1001", True),
            )
        ):
            path = cls.root / f"source-{index}.mkv"
            subprocess.run(
                [
                    "ffmpeg",
                    "-hide_banner",
                    "-loglevel",
                    "error",
                    "-nostdin",
                    "-f",
                    "lavfi",
                    "-i",
                    f"testsrc2=size={size}:rate={rate}:duration=1.4",
                    "-vf",
                    f"setsar={sar}" + (",select='not(eq(mod(n,5),2))'" if vfr else ""),
                    "-fps_mode",
                    "vfr",
                    "-c:v",
                    "ffv1",
                    "-threads",
                    "1",
                    str(path),
                ],
                check=True,
                capture_output=True,
                timeout=15,
            )
            cls.paths.append(path)

    def test_active_only_pixels_match_legacy_reference_for_sar_focus_and_triplicate(self):
        for index, path in enumerate(self.paths):
            original_digest = hashlib.sha256(path.read_bytes()).digest()
            for focused, triplicate in ((False, False), (True, False), (False, True), (True, True)):
                with self.subTest(source=index, focus=focused, triplicate=triplicate):
                    project = project_with_sources(1, path=path, duration=1.35)
                    transform = VisualTransform(1.7, 12, -8) if focused else VisualTransform()
                    block = replace(
                        project.timeline.segment_items[0],
                        visual_transform=transform,
                        triplicate=(TriplicateGroup.create(transform) if triplicate else None),
                    )
                    project = with_blocks(project, (block,))
                    backend = backend_for(project, frame_rate=30000 / 1001)
                    reference = FfmpegComposedPlaybackBackend(
                        ((project.source.source_id, path),),
                        (block,),
                        192,
                        108,
                        30000 / 1001,
                        1.35,
                        lambda _: None,
                        lambda _: None,
                        lambda: None,
                    )
                    try:
                        for position in (0.0, 0.375, 1.1):
                            expected = subprocess.run(
                                reference._command(position, realtime=False, frame_count=1),
                                capture_output=True,
                                check=True,
                                timeout=15,
                            ).stdout
                            actual = backend._decode_preview_frame(position).data
                            self.assertEqual(len(expected), backend.frame_size)
                            self.assertEqual(actual, expected)
                        expected_stream = subprocess.run(
                            reference._command(0.375, realtime=False),
                            capture_output=True,
                            check=True,
                            timeout=15,
                        ).stdout
                        actual_stream = subprocess.run(
                            backend._video_command(
                                0.375, backend._interval_at(0.375), continuous=True
                            ),
                            capture_output=True,
                            check=True,
                            timeout=15,
                        ).stdout
                        self.assertTrue(expected_stream)
                        self.assertEqual(actual_stream[: len(expected_stream)], expected_stream)
                        tail = actual_stream[len(expected_stream) :]
                        self.assertIn(len(tail), (0, backend.frame_size))
                        if tail:
                            self.assertEqual(tail, expected_stream[-backend.frame_size :])
                    finally:
                        backend.close()
                        reference.close()
            self.assertEqual(hashlib.sha256(path.read_bytes()).digest(), original_digest)

    def test_actual_preview_worker_crosses_sources_and_keeps_only_latest_requested_pixels(self):
        sources = tuple(
            replace(
                project_with_sources(1, path=path, duration=1.35).source,
                source_id=f"source-{index}",
            )
            for index, path in enumerate(self.paths[:2])
        )
        project = Project.create_multi(sources)
        frames, errors = [], []
        delivered = threading.Event()

        def receive(frame):
            frames.append(frame)
            delivered.set()

        backend = backend_for(project, on_frame=receive, on_error=errors.append)
        try:
            for target, source_index, offset in ((0.375, 0, 0.375), (1.725, 1, 0.375)):
                block = project.timeline.segment_items[source_index]
                reference = FfmpegComposedPlaybackBackend(
                    ((sources[source_index].source_id, Path(sources[source_index].path)),),
                    (block,),
                    192,
                    108,
                    10,
                    1.35,
                    lambda _: None,
                    lambda _: None,
                    lambda: None,
                )
                try:
                    expected = subprocess.run(
                        reference._command(offset, realtime=False, frame_count=1),
                        check=True,
                        capture_output=True,
                        timeout=15,
                    ).stdout
                finally:
                    reference.close()
                delivered.clear()
                backend.request_preview(target)
                self.assertTrue(delivered.wait(5))
                self.assertEqual(errors, [])
                self.assertEqual(frames[-1].position_seconds, target)
                self.assertEqual(frames[-1].data, expected)

            started, continue_start = threading.Event(), threading.Event()
            real_start = subprocess.Popen

            def start(*args, **kwargs):
                process = real_start(*args, **kwargs)
                started.set()
                self.assertTrue(continue_start.wait(3))
                return process

            delivered.clear()
            with patch("framestudio.composed_playback.subprocess.Popen", side_effect=start):
                backend.request_preview(0.625)
                self.assertTrue(started.wait(3))
                backend.request_preview(1.975)
                continue_start.set()
                self.assertTrue(delivered.wait(5))
            self.assertEqual(errors, [])
            self.assertEqual([frame.position_seconds for frame in frames], [0.375, 1.725, 1.975])
            self.assertIsNone(backend._preview_process)
        finally:
            backend.close()
        self.assertFalse(backend._preview_thread is not None and backend._preview_thread.is_alive())

    def test_fractional_tail_realtime_frames_are_bounded_and_end_reaps_decoder(self):
        project = project_with_sources(1, path=self.paths[0], duration=1.05)
        ended, errors, frames = threading.Event(), [], []
        backend = backend_for(
            project, on_frame=frames.append, on_error=errors.append, on_end=ended.set
        )
        try:
            command = backend._video_command(0.9, backend._interval_at(0.9), continuous=True)
            result = subprocess.run(command, check=True, capture_output=True, timeout=15)
            self.assertEqual(len(result.stdout), backend.frame_size * 2)
            backend._position_seconds = 0.9
            backend.play()
            self.assertTrue(ended.wait(5), errors)
            self.assertEqual(errors, [])
            self.assertTrue(frames)
            self.assertEqual(backend.current_position(), 1.05)
            self.assertIsNone(backend._realtime_decoder)
            self.assertIsNone(backend._realtime_decode_process)
        finally:
            backend.close()

    def test_seek_without_a_physical_frame_in_remaining_trim_is_explicit_legacy_failure(self):
        project = project_with_sources(1, path=self.paths[0], duration=1.35)
        backend = backend_for(project)
        reference = FfmpegComposedPlaybackBackend(
            ((project.source.source_id, self.paths[0]),),
            project.timeline.segment_items,
            192,
            108,
            10,
            1.35,
            lambda _: None,
            lambda _: None,
            lambda: None,
        )
        try:
            expected = subprocess.run(
                reference._command(1.34, realtime=False, frame_count=1),
                capture_output=True,
                check=True,
                timeout=15,
            ).stdout
            self.assertEqual(expected, b"")
            with self.assertRaisesRegex(PlaybackBackendError, "incomplete"):
                backend._decode_preview_frame(1.34)
        finally:
            backend.close()
            reference.close()


if __name__ == "__main__":
    unittest.main()
