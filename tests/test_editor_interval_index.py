import unittest
from pathlib import Path

from benchmarks.playback_performance import make_layout
from framestudio.composed_playback import FfmpegSynchronizedPlaybackBackend
from framestudio.layout_plan import FramingDomain, LayoutInterval, LayoutPlan, PixelRect


class NoScanTuple(tuple):
    def __iter__(self):
        raise AssertionError("An unchanged preview must not scan the complete project")


class IntervalIndexTests(unittest.TestCase):
    def plan(self, intervals):
        return LayoutPlan(
            PixelRect(0, 0, 1920, 1080),
            "absolute",
            FramingDomain.FINAL_SLOT,
            100_000,
            (),
            (),
            intervals,
        )

    def test_large_lookup_does_not_iterate_all_intervals(self):
        intervals = NoScanTuple(
            LayoutInterval(index * 10, (index + 1) * 10, (), ()) for index in range(10_000)
        )
        plan = self.plan(intervals)
        for tick in (0, 9, 10, 50_005, 99_999):
            self.assertIs(plan.interval_at(tick), intervals[tick // 10])

    def test_half_open_boundaries_and_missing_intervals(self):
        intervals = (
            LayoutInterval(10, 20, (), ()),
            LayoutInterval(30, 40, (), ()),
        )
        plan = self.plan(intervals)
        for tick in (0, 9, 20, 29, 40, 99_999, 100_000, -1, True, 10.5):
            self.assertIsNone(plan.interval_at(tick))
        self.assertIs(plan.interval_at(10), intervals[0])
        self.assertIs(plan.interval_at(19), intervals[0])
        self.assertIs(plan.interval_at(30), intervals[1])
        self.assertIsNone(self.plan(()).interval_at(0))

    def test_command_building_does_not_scan_inactive_sources(self):
        sources, layout = make_layout(Path("fixture.mp4"), 1920, 1080)
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
        self.addCleanup(backend.close)
        backend._source_items = NoScanTuple(backend._source_items)
        interval = backend._interval_at(4.125)
        command = backend._frame_command(4.125, interval)
        self.assertEqual(command.count("-i"), 1)
        self.assertEqual(command[command.index("-ss") + 1], "0.125")


if __name__ == "__main__":
    unittest.main()
