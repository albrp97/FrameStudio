import importlib.util
import tempfile
import unittest
from fractions import Fraction
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

if importlib.util.find_spec("av"):
    from framestudio.precise_preview_native import DecoderPool
else:
    DecoderPool = object


class FakeContainer:
    def __init__(self):
        self.start_time = 0
        self.closed = False
        self.streams = SimpleNamespace(
            video=[SimpleNamespace(time_base=Fraction(1, 30), codec_context=SimpleNamespace())]
        )

    def close(self):
        self.closed = True


class ResidencyPool(DecoderPool):
    def _device(self, stream):
        if self.engine != "cpu":
            self.device = SimpleNamespace(open=lambda _path: FakeContainer(), close=lambda: None)
            self.acceleration = SimpleNamespace(is_eligible=lambda _stream: True)


@unittest.skipUnless(importlib.util.find_spec("av"), "Optional pinned PyAV runtime is required")
class DecoderResidencyTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.paths = [Path(temporary.name) / f"{index}.mp4" for index in range(6)]
        for path in self.paths:
            path.write_bytes(b"fixture")
        self.open_patch = patch(
            "framestudio.precise_preview_native.av.open", new=lambda *a, **k: FakeContainer()
        )
        self.color_patch = patch(
            "framestudio.precise_preview_native.supported_color", return_value=True
        )
        self.open_patch.start()
        self.color_patch.start()
        self.addCleanup(self.open_patch.stop)
        self.addCleanup(self.color_patch.stop)

    def pool(self, engine, **kwargs):
        pool = ResidencyPool(engine, **kwargs)
        self.addCleanup(pool.close)
        return pool

    def test_cuda_retains_five_demand_loaded_sources_not_all_project_sources(self):
        pool = self.pool("cuda")
        for path in self.paths[:5]:
            pool.get(path, 1920, 1080)
        self.assertEqual(len(pool.contexts), 5)
        self.assertEqual(pool.opens, 5)
        self.assertEqual(pool.evictions, 0)
        for path in self.paths[:5]:
            pool.get(path, 1920, 1080)
        self.assertEqual(pool.opens, 5)
        retired = next(iter(pool.contexts.values()))
        pool.get(self.paths[5], 1920, 1080)
        self.assertEqual(len(pool.contexts), 5)
        self.assertIsNone(retired.container)
        self.assertEqual(pool.evictions, 1)
        pool.close()
        self.assertEqual(len(pool.contexts), 0)

    def test_cpu_remains_at_two_contexts(self):
        pool = self.pool("cpu")
        for path in self.paths:
            pool.get(path, 1920, 1080)
            self.assertLessEqual(len(pool.contexts), 2)
        self.assertEqual(pool.evictions, 4)

    def test_low_budget_restricts_cuda_to_two(self):
        pool = self.pool("cuda", max_cuda_contexts=2)
        for path in self.paths:
            pool.get(path, 1920, 1080)
        self.assertEqual(len(pool.contexts), 2)
        self.assertEqual(pool.evictions, 4)

    def test_cpu_fallback_retires_extra_cuda_contexts_before_cpu_decode(self):
        pool = self.pool("cuda")
        for path in self.paths[:5]:
            pool.get(path, 1920, 1080)
        pool.acceleration.is_eligible = lambda _stream: False
        pool._device = lambda _stream: None
        decoder, _key, _ms = pool.get(self.paths[5], 1920, 1080)
        self.assertEqual(decoder.engine, "cpu")
        self.assertEqual(len(pool.contexts), 2)
        self.assertEqual(pool.evictions, 4)

    def test_invalid_budget_is_not_silently_accepted(self):
        for cap in (0, 6, True, 2.5):
            with self.subTest(cap=cap), self.assertRaises(ValueError):
                ResidencyPool("cuda", max_cuda_contexts=cap)


if __name__ == "__main__":
    unittest.main()
