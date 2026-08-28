import unittest
from dataclasses import dataclass

from benchmarks.preview_responsiveness import summarize_preview_benchmark
from framestudio.preview_strategy import PreviewFrameCache


@dataclass(frozen=True)
class Frame:
    position_seconds: float


class PreviewStrategyTests(unittest.TestCase):
    def test_cache_reuses_frame_by_source_frame_index(self):
        cache = PreviewFrameCache(max_entries=2, frame_rate=10.0)
        frame = Frame(0.2)

        cache.put(frame)

        self.assertIs(cache.get(0.201), frame)
        self.assertEqual(cache.hits, 1)
        self.assertEqual(cache.misses, 0)

    def test_cache_evicts_oldest_frame_when_bounded(self):
        cache = PreviewFrameCache(max_entries=2, frame_rate=10.0)
        first = Frame(0.0)
        second = Frame(0.1)
        third = Frame(0.2)

        cache.put(first)
        cache.put(second)
        cache.put(third)

        self.assertIsNone(cache.get(0.0))
        self.assertIs(cache.get(0.1), second)
        self.assertIs(cache.get(0.2), third)
        self.assertEqual(cache.evictions, 1)

    def test_preview_benchmark_status_fails_when_trace_samples_fail(self):
        result = {
            "failure_probe": {"reported": True},
            "conditions": {
                "cold": {
                    "failed_samples": 1,
                    "errors": [],
                    "rapid_pointer": {
                        "latency_ms": 1.0,
                        "newest_request_rendered": True,
                    },
                },
            },
        }

        summary = summarize_preview_benchmark(result)

        self.assertEqual(summary["status"], "failed")
        self.assertFalse(summary["conditions_passed"])
        self.assertTrue(summary["failure_probe_passed"])

    def test_preview_benchmark_status_fails_when_rapid_pointer_is_stale(self):
        result = {
            "failure_probe": {"reported": True},
            "conditions": {
                "cached": {
                    "failed_samples": 0,
                    "errors": [],
                    "rapid_pointer": {
                        "latency_ms": 1.0,
                        "newest_request_rendered": False,
                    },
                },
            },
        }

        summary = summarize_preview_benchmark(result)

        self.assertEqual(summary["status"], "failed")
        self.assertFalse(summary["conditions_passed"])


if __name__ == "__main__":
    unittest.main()
