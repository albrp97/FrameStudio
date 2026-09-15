import unittest

from benchmarks.efficient_export_pipeline_benchmark import (
    _recommend,
    _summarize_candidate_runs,
)


class EfficientExportPipelineBenchmarkTests(unittest.TestCase):
    def test_recommendation_rejects_unsafe_or_unpreserved_candidates(self):
        results = {
            "unsafe-fast": {
                "status": "passed",
                "source_preserved": True,
                "boundary_safe": False,
                "wall_seconds": 1.0,
            },
            "changed-source": {
                "status": "passed",
                "source_preserved": False,
                "boundary_safe": True,
                "wall_seconds": 2.0,
            },
        }

        recommendation = _recommend(results)

        self.assertIsNone(recommendation["selected_strategy"])

    def test_recommendation_selects_fastest_acceptable_candidate(self):
        results = {
            "baseline": {
                "strategy": "baseline",
                "status": "passed",
                "source_preserved": True,
                "boundary_safe": True,
                "wall_seconds": 12.0,
            },
            "adaptive": {
                "strategy": "adaptive",
                "status": "passed",
                "source_preserved": True,
                "boundary_safe": True,
                "wall_seconds": 8.0,
                "normalization_process_count": 2,
                "interpolation_calls": 2,
            },
        }

        recommendation = _recommend(results)

        self.assertEqual(recommendation["selected_strategy"], "adaptive")
        self.assertEqual(recommendation["wall_seconds"], 8.0)

    def test_candidate_summary_uses_median_timing_and_preserves_all_runs(self):
        template = {
            "strategy": "adaptive",
            "status": "passed",
            "wall_seconds": 10.0,
            "child_user_seconds": 8.0,
            "child_system_seconds": 1.0,
            "child_max_rss_kb_cumulative": 100.0,
            "ffmpeg_process_count": 8,
            "normalization_process_count": 2,
            "interpolation_process_count": 4,
            "interpolation_calls": 2,
            "restoration_calls": 0,
            "stage_seconds": {"normalizing source run": 1.0},
            "intermediate_peak_bytes": 100,
            "output_bytes": 200,
            "output": {"frames": 10},
            "source_hashes_before": {"source.mp4": "same"},
            "source_hashes_after": {"source.mp4": "same"},
            "source_preserved": True,
            "boundary_safe": True,
            "boundary_samples": {"before_deleted_gap": "red"},
            "error": None,
        }
        runs = [
            {**template, "wall_seconds": 9.0},
            {**template, "wall_seconds": 11.0},
            {**template, "wall_seconds": 10.0},
        ]

        summary = _summarize_candidate_runs(runs)

        self.assertEqual(summary["wall_seconds"], 10.0)
        self.assertEqual(summary["run_count"], 3)
        self.assertEqual(summary["interpolation_calls"], 2)
        self.assertEqual(summary["runs"], runs)
