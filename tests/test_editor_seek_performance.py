"""Real exact-seek checks, with generated small fixtures by default.

FRAMESTUDIO_SEEK_FIXTURE_DIR selects existing high-detail 1080p/4K fixtures.
FRAMESTUDIO_BENCHMARK_LOCK selects the shared exclusive media lock. This
module acquires the lock itself; never wrap its runner in another flock.
"""

from __future__ import annotations

import fcntl
import hashlib
import os
import shutil
import subprocess
import unittest
import uuid
from pathlib import Path
from typing import IO

from benchmarks.playback_performance import make_layout
from benchmarks.seek_performance import (
    Candidate,
    ExperimentBackend,
    SourceTimeline,
    candidate_command,
    distribution,
    exact_output,
    measure_requests,
    probe_timeline,
    resolve_executable,
)


class SeekPerformanceTests(unittest.TestCase):
    def test_output_and_input_thread_experiments_are_independent(self) -> None:
        command = [
            "/usr/bin/ffmpeg",
            "-ss",
            "1.733",
            "-i",
            "first.mp4",
            "-i",
            "second.mp4",
            "-f",
            "rawvideo",
            "pipe:1",
        ]
        output = candidate_command(command, Candidate.OUTPUT)
        self.assertGreater(output.index("-threads:v"), output.index("second.mp4"))
        self.assertNotIn("-threads", output)
        decoder = candidate_command(command, Candidate.INPUT)
        self.assertEqual(decoder.count("-threads"), 2)
        self.assertNotIn("-threads:v", decoder)
        self.assertNotIn("-threads", command)

    def test_distributions_include_tail_and_reject_empty_samples(self) -> None:
        result = distribution([4, 1, 3, 2, 100])
        self.assertEqual((result.p50, result.p95, result.pmax), (3, 100, 100))
        with self.assertRaises(ValueError):
            distribution([])

    def test_fractional_source_position_selects_the_next_observed_frame_pts(self) -> None:
        timeline = SourceTimeline((0.0, 0.033333, 0.066667), (0.0,))
        self.assertEqual(timeline.frame_at(0.033), 0.033333)
        self.assertEqual(timeline.frame_at(0.033333), 0.033333)
        self.assertEqual(timeline.frame_at(0.034), 0.066667)
        with self.assertRaises(ValueError):
            timeline.frame_at(0.1)


@unittest.skipUnless(shutil.which("ffmpeg"), "FFmpeg is required")
class RealSeekFunctionalityTests(unittest.TestCase):
    root: Path
    paths: tuple[Path, Path]
    hashes: dict[Path, str]
    lock: IO[str]
    generated: bool

    @classmethod
    def setUpClass(cls) -> None:
        repository = Path(__file__).resolve().parents[1]
        lock_path = Path(
            os.environ.get(
                "FRAMESTUDIO_BENCHMARK_LOCK", str(repository / ".playback-benchmark.lock")
            )
        )
        cls.lock = lock_path.open("a")
        fcntl.flock(cls.lock, fcntl.LOCK_EX)
        fixtures = os.environ.get("FRAMESTUDIO_SEEK_FIXTURE_DIR")
        cls.generated = fixtures is None
        cls.root = (
            repository / "tests" / f".seek-functionality-{uuid.uuid4().hex}"
            if fixtures is None
            else Path(fixtures)
        )
        cls.paths = (
            cls.root / "high-detail-1920x1080.mp4",
            cls.root / "high-detail-3840x2160.mp4",
        )
        try:
            if cls.generated:
                cls.root.mkdir()
                for path, size in zip(cls.paths, ("320x180", "640x360"), strict=True):
                    subprocess.run(
                        [
                            resolve_executable("ffmpeg"),
                            "-hide_banner",
                            "-loglevel",
                            "error",
                            "-nostdin",
                            "-f",
                            "lavfi",
                            "-i",
                            f"testsrc2=size={size}:rate=30:duration=8",
                            "-c:v",
                            "libx264",
                            "-threads",
                            "2",
                            "-g",
                            "120",
                            "-bf",
                            "3",
                            "-pix_fmt",
                            "yuv420p",
                            str(path),
                        ],
                        capture_output=True,
                        check=True,
                        timeout=30,
                    )
            cls.hashes = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in cls.paths}
        except (OSError, subprocess.SubprocessError):
            cls._cleanup()
            raise

    @classmethod
    def _cleanup(cls) -> None:
        if cls.generated and cls.root.exists():
            shutil.rmtree(cls.root)
        cls.lock.close()

    @classmethod
    def tearDownClass(cls) -> None:
        try:
            after = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in cls.paths}
            if after != cls.hashes:
                raise AssertionError("Real seek functionality changed source bytes")
        finally:
            cls._cleanup()

    def make_backend(self, candidate: Candidate = Candidate.CURRENT) -> ExperimentBackend:
        first_geometry = (320, 180) if self.generated else (1920, 1080)
        second_geometry = (640, 360) if self.generated else (3840, 2160)
        sources, layout = make_layout(
            self.paths[0],
            *first_geometry,
            alternate_source=(self.paths[1], *second_geometry),
        )
        self.assertEqual(len(sources), 200)
        self.assertEqual(layout.final_duration_seconds, 40 * 60 * 60)
        backend = ExperimentBackend(sources, layout, resolve_executable("ffmpeg"), candidate)
        self.addCleanup(backend.close)
        return backend

    def test_fractional_frames_and_physical_segment_boundaries_are_exact(self) -> None:
        reference = self.make_backend()
        candidate = self.make_backend(Candidate.SIMPLE)
        pixels: dict[float, str] = {}
        for target in (0.033, 0.067, 1.733, 1.999, 2.0, 2.033, 3.733, 4.033):
            with self.subTest(target=target):
                command, path, _position = reference.command_at(target)
                expected, _elapsed = exact_output(command, reference.frame_size)
                candidate.request_preview(target)
                actual = candidate.wait_for_position(target)
                self.assertEqual(actual.data, expected)
                self.assertEqual(actual.position_seconds, target)
                self.assertEqual(actual.decoded_position_seconds, target)
                self.assertEqual((actual.width, actual.height), (1920, 1080))
                self.assertEqual(path, self.paths[1] if 2 <= target < 4 else self.paths[0])
                pixels[target] = hashlib.sha256(actual.data).hexdigest()
        self.assertNotEqual(pixels[0.033], pixels[0.067])
        self.assertNotEqual(pixels[1.999], pixels[2.0])
        self.assertEqual(candidate.preview_stats()["cache_hits"], 0)

    def test_rapid_cross_source_bursts_deliver_the_latest_exact_target(self) -> None:
        backend = self.make_backend()
        references: dict[float, str] = {}
        for target in (0.033, 2.033, 1.733, 3.733):
            command, _path, _position = backend.command_at(target)
            output, _elapsed = exact_output(command, backend.frame_size)
            references[target] = hashlib.sha256(output).hexdigest()
        timelines = {path: probe_timeline(path) for path in self.paths}
        receipts = measure_requests(backend, references, timelines)
        self.assertEqual(len(receipts), 4)
        self.assertTrue(all(receipt.exact_reference_equal for receipt in receipts))
        self.assertTrue(
            all(
                receipt.actual_position_seconds == receipt.requested_position_seconds
                for receipt in receipts
            )
        )
        self.assertEqual(backend.preview_stats()["cache_hits"], 0)
        self.assertEqual(backend.preview_stats()["failures"], 0)
        backend.close()
        self.assertIsNone(backend._preview_process)
        self.assertFalse(backend._preview_thread and backend._preview_thread.is_alive())


if __name__ == "__main__":
    unittest.main()
