from __future__ import annotations

import hashlib
import shutil
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from benchmarks import multitrack_architecture_benchmark as benchmark


class ArchitectureBenchmarkTests(unittest.TestCase):
    def test_hashing_streams_without_python311_file_digest(self):
        payload = b"abc" * 400_000
        with TemporaryDirectory(
            prefix=".architecture-hash-", dir=Path(__file__).parent
        ) as directory:
            path = Path(directory) / "fixture.bin"
            path.write_bytes(payload)
            with patch.object(
                benchmark.hashlib,
                "file_digest",
                create=True,
                side_effect=AssertionError("Unavailable in Python 3.10"),
            ):
                self.assertEqual(benchmark.sha256(path), hashlib.sha256(payload).hexdigest())

    def test_frame_chunks_cover_remainder_without_overlap(self):
        self.assertEqual(benchmark.frame_chunks(7, 3), ((0, 3), (3, 5), (5, 7)))
        with self.assertRaises(ValueError):
            benchmark.frame_chunks(2, 3)

    def test_dependencies_keep_crop_and_triplicate_not_other_tracks(self):
        graph = (
            "[0:v]split=2[a][b];[a]crop=3:8[c];[b]crop=4:8[d];"
            "[c][d]hstack=inputs=2[trip];[1:v]scale=9:8[other];"
            "[trip][other]xstack=inputs=2:layout=0_0|7_0[out]"
        )
        selected = benchmark.graph_dependencies(graph, "trip")
        self.assertIn("crop=3:8", selected)
        self.assertIn("hstack=inputs=2", selected)
        self.assertNotIn("scale=9:8", selected)
        self.assertNotIn("xstack", selected)

    def test_missing_dependency_is_not_silently_accepted(self):
        with self.assertRaises(ValueError):
            benchmark.graph_dependencies("[0:v]null[out]", "missing")

    def test_counterbalance_rotates_all_candidates(self):
        rows = ("monolithic", "tracks-1", "chunks-1")
        orders = [benchmark.counterbalanced(rows, trial) for trial in range(3)]
        self.assertEqual([order[0] for order in orders], list(rows))
        self.assertTrue(all(set(order) == set(rows) for order in orders))

    def test_lossless_output_has_no_delivery_encoder(self):
        command = [
            "ffmpeg",
            "-i",
            "a.mp4",
            "-filter_complex",
            "[0:v]null[vout]",
            "-map",
            "[vout]",
            "-an",
            "-r",
            "30",
            "-frames:v",
            "2",
            "-c:v",
            "libx264",
            "-preset",
            "ultrafast",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            "out.mp4",
        ]
        lossless = benchmark.lossless_command(command, "[0:v]null[vout]", Path("tile.mkv"), 2)
        self.assertIn("ffv1", lossless)
        self.assertIn("yuv444p", lossless)
        self.assertNotIn("libx264", lossless)
        self.assertNotIn("+faststart", lossless)

    def test_checkpoint_reopen_reuses_only_matching_identity(self):
        with TemporaryDirectory(
            prefix=".architecture-cache-", dir=Path(__file__).parent
        ) as directory:
            root = Path(directory).resolve()
            produced = []

            def produce(path):
                produced.append(path)
                path.write_bytes(b"lossless-fixture")

            def validate(path):
                self.assertEqual(path.read_bytes(), b"lossless-fixture")
                return {"valid": True}

            request = {"source_sha256": "source-a", "geometry": [640, 1080]}
            first = benchmark.RenderPreparations(root).materialize(
                "experimental-test",
                request,
                produce,
                validate,
                suffix=".bin",
            )
            reopened = benchmark.RenderPreparations(root)
            second = reopened.materialize(
                "experimental-test",
                request,
                produce,
                validate,
                suffix=".bin",
            )
            changed = reopened.materialize(
                "experimental-test",
                {**request, "source_sha256": "source-b"},
                produce,
                validate,
                suffix=".bin",
            )
            self.assertEqual(first, second)
            self.assertNotEqual(first, changed)
            self.assertEqual(len(produced), 2)
            self.assertEqual(reopened.hits, 1)

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg required")
    def test_tiny_real_comparator_and_checkpoint_restart(self):
        with TemporaryDirectory(
            prefix=".architecture-test-", dir=Path(__file__).parent
        ) as directory:
            root = Path(directory).resolve()
            args = benchmark.parser().parse_args(
                [
                    "--duration",
                    "0.1",
                    "--tracks",
                    "3",
                    "--segments",
                    "2",
                    "--workers",
                    "2",
                    "--trials",
                    "1",
                    "--triplicate-track",
                    "2",
                    "--combined",
                    "--artifact-root",
                    str(root / "artifacts"),
                    "--report",
                    str(root / "report.json"),
                    "--recovery-demo",
                ]
            )
            report = benchmark.run_benchmark(args)
            self.assertEqual(len(report["rows"]), 4)
            for row in report["rows"]:
                self.assertEqual(row["status"], "eligible", row)
                self.assertEqual(row["verification"]["frames"], 3)
                self.assertTrue(row["verification"]["exact_frame_hashes"])
                self.assertTrue(row["verification"]["source_hashes_unchanged"])
            self.assertTrue(report["recovery"]["reused_finished_artifact"])
            self.assertTrue(report["recovery"]["same_artifact_hash"])
            self.assertTrue(report["recovery"]["cancellation_observed"])
            self.assertTrue(report["recovery"]["resumed_output_matches_oracle"])
            self.assertTrue(
                all(
                    item["speedup_vs_monolithic"] is not None for item in report["medians"].values()
                )
            )
            self.assertTrue((root / "report.json").is_file())


if __name__ == "__main__":
    unittest.main()
