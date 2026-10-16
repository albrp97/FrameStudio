import importlib.util
import json
import shutil
import subprocess
import sys
import unittest
import uuid
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "benchmarks/multitrack_render_benchmark.py"
SPEC = importlib.util.spec_from_file_location("multitrack_benchmark", SCRIPT)
benchmark = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = benchmark
SPEC.loader.exec_module(benchmark)


class MultitrackBenchmarkTests(unittest.TestCase):
    def test_main_returns_failure_when_no_fresh_baseline_or_winner_is_eligible(self):
        report = {
            "rows": [{"status": "failed"}],
            "fastest_measured_exact_fresh": None,
            "summary": [],
        }
        with (
            patch.object(sys, "argv", [str(SCRIPT), "--report", "report.json"]),
            patch.object(benchmark, "run", return_value=report),
            patch("builtins.print"),
        ):
            with self.assertRaises(SystemExit) as raised:
                benchmark.main()
        self.assertEqual(raised.exception.code, 1)

    def test_counterbalancing_covers_each_position(self):
        rows = ["baseline", "video", "audio", "combined"]
        orders = [benchmark.trial_order(rows, index) for index in range(4)]
        for index in range(4):
            self.assertEqual({order[index] for order in orders}, set(rows))

    def test_filter_and_decoder_budgets_never_change_final_encoder_threads(self):
        command = ["ffmpeg", "-y", "-i", "one.mp4", "-i", "two.mp4", "-c:v", "libx264", "out.mp4"]
        result = benchmark.thread_command(command, 2, 1)
        self.assertEqual(result.count("-threads"), 2)
        self.assertIn("-filter_complex_threads", result)
        self.assertEqual(command.count("-threads"), 0)
        self.assertEqual(benchmark.thread_command(command, 0), command)
        overridden = benchmark.thread_command(command, 6, 1)
        self.assertEqual(overridden[overridden.index("-filter_complex_threads") + 1], "6")
        self.assertEqual(overridden[overridden.index("-threads") + 1], "1")
        self.assertNotIn("-threads", overridden[overridden.index("-c:v") :])

    def test_nvdec_changes_only_input_decoding_not_encoder_or_filters(self):
        command = [
            "ffmpeg",
            "-i",
            "one.mp4",
            "-i",
            "two.mp4",
            "-filter_complex",
            "[0:v][1:v]hstack[v]",
            "-map",
            "[v]",
            "-c:v",
            "libx264",
            "out.mp4",
        ]
        result = benchmark.nvdec_command(command)
        self.assertEqual(result.count("-hwaccel"), 2)
        self.assertIn("libx264", result)
        self.assertNotIn("-hwaccel_output_format", result)
        self.assertEqual(
            result[result.index("-filter_complex") + 1],
            command[command.index("-filter_complex") + 1],
        )

    def test_seek_is_explicit_fixture_only_and_rebases_both_streams(self):
        source = Path("source.mkv").resolve()
        video = [
            "ffmpeg",
            "-i",
            str(source),
            "-filter_complex",
            "[0:v]trim=start=8.000000000:end=9.000000000,setpts=PTS-STARTPTS[v]",
            "-map",
            "[v]",
            "out.mp4",
        ]
        audio = [
            "ffmpeg",
            "-i",
            str(source),
            "-filter_complex",
            "[0:a]atrim=start_sample=384000:end_sample=432000[a]",
            "-map",
            "[a]",
            "out.wav",
        ]
        for command, expected in (
            (video, "trim=start=0.000000000:end=1.000000000"),
            (audio, "atrim=start_sample=0:end_sample=48000"),
        ):
            result = benchmark.seek_fixture_command(command, source, 8, "rebase")
            self.assertEqual(result[result.index("-ss") + 1], "8.000000000")
            self.assertIn(expected, " ".join(result))
        with self.assertRaises(ValueError):
            benchmark.seek_fixture_command(video, Path("other.mkv"), 8)
        copyts = benchmark.seek_fixture_command(video, source, 8, "copyts")
        self.assertIn("-noaccurate_seek", copyts)
        self.assertIn("-copyts", copyts)
        self.assertIn("-start_at_zero", copyts)
        self.assertEqual(
            copyts[copyts.index("-filter_complex") + 1], video[video.index("-filter_complex") + 1]
        )

    def test_selection_requires_every_trial_and_exact_av_parity(self):
        signature = {
            "video_sha256": "v",
            "video_frames": 4,
            "audio_sha256": "a",
            "audio_samples": 6400,
            "audio_channels": 2,
            "audio_rate": 48000,
        }
        rows = [
            {
                "trial": trial,
                "strategy": strategy,
                "budget": 1,
                "status": "completed",
                "signature": signature.copy(),
                "wall_seconds": wall,
                "source_preserved": True,
            }
            for trial in range(2)
            for strategy, wall in (("baseline", 10), ("combined", 5), ("audio", 6))
        ]
        rows[-1]["signature"]["audio_sha256"] = "different"
        rows.extend(
            {
                "trial": trial,
                "strategy": "baseline",
                "budget": 0,
                "status": "completed",
                "signature": signature.copy(),
                "wall_seconds": 12,
                "source_preserved": True,
            }
            for trial in range(2)
        )
        result = benchmark.summarize(rows, 2)
        combined = next(row for row in result if row["strategy"] == "combined")
        audio = next(row for row in result if row["strategy"] == "audio")
        self.assertTrue(combined["eligible_exact"])
        self.assertEqual(combined["speedup_vs_baseline"], 2)
        self.assertEqual(combined["speedup_vs_current_baseline_auto"], 2.4)
        self.assertFalse(audio["eligible_exact"])
        self.assertTrue(all("exact_parity" in row for row in rows))

    def test_missing_baseline_or_failed_trial_cannot_win(self):
        rows = [
            {"trial": 0, "strategy": "video", "budget": 2, "status": "failed", "wall_seconds": 1}
        ]
        self.assertFalse(benchmark.summarize(rows, 2)[0]["eligible_exact"])

    def test_output_hash_parser_counts_decoded_frames_without_timestamp_headers(self):
        payload = b"#format: frame checksums\n0, 0, 0, 1, 6, abcd\n0, 1, 1, 1, 6, ef01\n"
        self.assertEqual(benchmark.frame_signature(payload)[1], 2)
        self.assertEqual(
            benchmark.frame_signature(payload)[0],
            benchmark.frame_signature(
                payload.replace(b"#format: frame checksums", b"#different header")
            )[0],
        )

    def test_equally_wrong_decoded_counts_cannot_qualify_by_parity(self):
        signature = {"video_frames": 10, "audio_pcm_frames": 100}
        benchmark.validate_decoded_counts(signature, 10, 100)
        for expected_frames, expected_samples in ((9, 100), (10, 99)):
            with self.subTest(frames=expected_frames, samples=expected_samples):
                with self.assertRaisesRegex(ValueError, "Decoded .* expected"):
                    benchmark.validate_decoded_counts(signature, expected_frames, expected_samples)

    def test_parser_validates_workload_without_starting_ffmpeg(self):
        parser = benchmark.argument_parser()
        args = parser.parse_args(
            [
                "--baseline-root",
                ".",
                "--tracks",
                "4",
                "--repeats",
                "3",
                "--thread-budgets",
                "1,2,auto",
                "--report",
                "report.json",
                "--artifact-root",
                "artifacts",
            ]
        )
        benchmark.validate_args(args)
        self.assertEqual(args.budgets, [1, 2, 0])
        args.duration = 0
        with self.assertRaises(ValueError):
            benchmark.validate_args(args)

    def test_parser_accepts_many_source_and_late_range_workloads(self):
        args = benchmark.argument_parser().parse_args(
            [
                "--baseline-root",
                ".",
                "--source-count",
                "35",
                "--tracks",
                "3",
                "--intervals",
                "38",
                "--source-start",
                "110",
                "--source-duration",
                "120",
                "--strategies",
                "baseline,seek,nvdec,combined-seek-nvdec",
                "--report",
                "report.json",
                "--artifact-root",
                "artifacts",
            ]
        )
        benchmark.validate_args(args)
        self.assertEqual(args.source_count, 35)
        self.assertEqual(args.late_start, 110)
        self.assertFalse(args.triplicate)
        args.source_duration = 100
        with self.assertRaises(ValueError):
            benchmark.validate_args(args)

    def test_make_project_uses_multiple_sources_and_repeated_ranges_without_io(self):
        from framestudio.model import SourceReference

        sources = [Path("first.mkv"), Path("second.mkv"), Path("third.mkv")]
        metadata = {
            "duration_seconds": 120.0,
            "width": 320,
            "height": 180,
            "frame_rate": "30/1",
            "video_codec": "h264",
            "audio_codec": "pcm_s16le",
            "audio_stream_present": True,
            "audio_sample_rate": 48000,
            "audio_channels": 2,
            "audio_channel_layout": "stereo",
            "format_name": "matroska",
        }
        # Construct real project/timeline objects, mocking only filesystem/media acquisition.
        original = SourceReference.from_path

        def reference(path, values):
            with (
                patch.object(Path, "is_file", return_value=True),
                patch.object(
                    Path, "stat", return_value=SimpleNamespace(st_size=100, st_mtime_ns=1)
                ),
            ):
                return original(path, values)

        config = {
            "tracks": 3,
            "repeats": 2,
            "range_count": 2,
            "intervals": 0,
            "duration": 0.2,
            "late_start": 110,
            "triplicate": False,
        }
        with (
            patch(
                "framestudio.media.probe_media",
                return_value=SimpleNamespace(metadata=lambda: metadata),
            ),
            patch.object(SourceReference, "from_path", side_effect=reference),
            patch("framestudio.operations.ensure_project_audio_analysis"),
        ):
            project = benchmark.make_project(sources, config)
        self.assertEqual(len(project.timeline.tracks), 3)
        blocks = [block for track in project.timeline.tracks for block in track.blocks]
        self.assertEqual(len(blocks), 12)
        self.assertEqual(len({block.source_id for block in blocks}), 3)
        self.assertTrue(all(block.triplicate is None for block in blocks))
        self.assertEqual({round(block.start_seconds, 1) for block in blocks}, {110, 110.2})
        self.assertAlmostEqual(project.timeline.timeline_duration_seconds, 0.8)
        config.update(intervals=38, stagger_frames=1)
        with (
            patch(
                "framestudio.media.probe_media",
                return_value=SimpleNamespace(metadata=lambda: metadata),
            ),
            patch.object(SourceReference, "from_path", side_effect=reference),
            patch("framestudio.operations.ensure_project_audio_analysis"),
        ):
            larger = benchmark.make_project(sources, config)
        from framestudio.layout_plan import plan_project_layout

        layout = plan_project_layout(larger)
        self.assertEqual(sum(len(track.blocks) for track in larger.timeline.tracks), 114)
        self.assertEqual(len(layout.intervals), 116)


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg tools required")
class MultitrackBenchmarkFunctionalityTests(unittest.TestCase):
    def run_fixture(self, stagger: int):
        root = Path("tests") / f".multitrack-functionality-{uuid.uuid4().hex}"
        root.mkdir()
        self.addCleanup(shutil.rmtree, root)
        report = root / "report.json"
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--baseline-root",
                str(SCRIPT.parents[1]),
                "--tracks",
                "3",
                "--source-count",
                "2",
                "--intervals",
                "2",
                "--stagger-frames",
                str(stagger),
                "--duration",
                ".3",
                "--strategies",
                "baseline",
                "--thread-budgets",
                "1",
                "--decoder-threads",
                "1",
                "--trials",
                "1",
                "--report",
                str(report),
                "--artifact-root",
                str(root / "artifacts"),
            ],
            capture_output=True,
            text=True,
            timeout=90,
        )
        self.assertTrue(report.is_file(), completed.stderr)
        result = json.loads(report.read_text())
        for source in result["fixture"]["sources"]:
            metadata = json.loads(
                subprocess.run(
                    [
                        "ffprobe",
                        "-v",
                        "error",
                        "-show_entries",
                        "stream=codec_type,start_time,has_b_frames:format=start_time",
                        "-of",
                        "json",
                        source["path"],
                    ],
                    check=True,
                    capture_output=True,
                    text=True,
                ).stdout
            )
            self.assertEqual(float(metadata["format"]["start_time"]), 0)
            self.assertTrue(all(float(stream["start_time"]) == 0 for stream in metadata["streams"]))
            video = next(
                stream for stream in metadata["streams"] if stream["codec_type"] == "video"
            )
            self.assertGreater(video["has_b_frames"], 0)
        return completed, result

    def test_real_multisource_av_export_keeps_exact_hashes_and_source(self):
        completed, report = self.run_fixture(stagger=0)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertTrue(report["source_preserved"])
        self.assertIsNotNone(report["fastest_measured_exact_fresh"])
        for row in report["rows"]:
            self.assertEqual(row["status"], "completed", row.get("reason"))
            self.assertEqual(row["signature"]["video_frames"], 18)
            self.assertGreater(row["signature"]["audio_pcm_frames"], 0)
            self.assertTrue(row["exact_parity"])

    def test_real_dynamic_multisource_result_keeps_frame_gate_and_exit_status(self):
        completed, report = self.run_fixture(stagger=1)
        self.assertTrue(report["source_preserved"])
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(report["status"], "completed")
        for row in report["rows"]:
            self.assertEqual(row["signature"]["video_frames"], 20)
            self.assertTrue(row["exact_parity"])


if __name__ == "__main__":
    unittest.main()
