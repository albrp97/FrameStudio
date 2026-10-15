from __future__ import annotations

import copy
import gc
import importlib.util
import unittest
from fractions import Fraction
from itertools import product
from unittest.mock import patch


@unittest.skipUnless(importlib.util.find_spec("av"), "Optional PyAV runtime is required")
class NativeCompositionTests(unittest.TestCase):
    def setUp(self):
        import av

        from framestudio import precise_preview_native

        self.av = av
        self.native = precise_preview_native
        self.request = {
            "width": 192,
            "height": 108,
            "slots": [
                {
                    "x": 0,
                    "y": 0,
                    "source_sar": "1/1",
                    "crops": [
                        {
                            "scaled_width": 192,
                            "scaled_height": 108,
                            "width": 192,
                            "height": 108,
                            "crop_x": 0,
                            "crop_y": 0,
                        }
                    ],
                }
            ],
        }

    def tearDown(self):
        gc.collect()

    def frame(self, color=(2, 2, 2, 0), pixel_format="yuv420p", phase=0):
        frame = self.av.VideoFrame(320, 180, pixel_format)
        for index, plane in enumerate(frame.planes):
            plane.update(
                bytes(
                    (number * 17 + index * 43 + phase * 29) % 256
                    for number in range(plane.buffer_size)
                )
            )
        frame.pts = 15
        frame.time_base = Fraction(1, 30)
        for name, value in zip(
            ("colorspace", "color_primaries", "color_trc", "color_range"), color, strict=True
        ):
            setattr(frame, name, value)
        return frame

    def test_opaque_canvas_matches_general_graph_including_color_roundtrip(self):
        for color, focused, pixel_format in product(
            ((2, 2, 2, 0), (1, 1, 1, 1), (1, 1, 1, 2)),
            (False, True),
            ("yuv420p", "nv12", "yuvj420p"),
        ):
            with self.subTest(color=color, focused=focused, pixel_format=pixel_format):
                request = copy.deepcopy(self.request)
                if focused:
                    request["slots"][0]["crops"][0].update(
                        scaled_width=288, scaled_height=162, crop_x=48, crop_y=26
                    )
                frame = self.frame(color, pixel_format)
                expected = self.native._compose_general(request, [frame])
                with patch.object(
                    self.native, "_compose_general", side_effect=AssertionError("general path")
                ):
                    actual = self.native.compose(request, [frame])
                self.assertEqual(actual, expected)
                self.assertEqual(len(actual), 192 * 108 * 4)

    def test_bounded_cuda_working_set_and_cpu_budget_shrink_preserve_exact_pixels(self):
        cache = self.native.CompositionCache()
        self.addCleanup(cache.clear)
        cache.set_capacity(5)
        expected = self.native._compose_general(self.request, [self.frame()])
        for index in range(5):
            actual = cache.render(
                self.request | {"slots": [self.request["slots"][0] | {"source_sar": "1/1"}]},
                self.frame(),
                (f"source-{index}", 1, index, 1024, 1),
            )
            self.assertEqual(actual, expected)
        self.assertEqual(len(cache.contexts), 5)
        cache.set_capacity(2)
        self.assertEqual(len(cache.contexts), 2)
        self.assertEqual([key[0][0] for key in cache.contexts], ["source-3", "source-4"])
        for cap in (0, 6, True, 2.5):
            with self.subTest(cap=cap), self.assertRaises(ValueError):
                cache.set_capacity(cap)

    def test_alpha_letterbox_triplicate_and_multislot_use_general_graph(self):
        cases = []
        letterbox = copy.deepcopy(self.request)
        letterbox["slots"][0]["crops"][0]["width"] = 190
        cases.append((letterbox, [self.frame()]))
        triplicate = copy.deepcopy(self.request)
        crop = triplicate["slots"][0]["crops"][0]
        crop.update(width=64, scaled_width=192, crop_x=64)
        triplicate["slots"][0]["crops"] = [copy.deepcopy(crop) for _ in range(3)]
        cases.append((triplicate, [self.frame()]))
        multiple = copy.deepcopy(self.request)
        multiple["slots"] *= 2
        cases.append((multiple, [self.frame(), self.frame()]))
        cases.append((self.request, [self.frame(pixel_format="rgba")]))
        for request, frames in cases:
            with self.subTest(slots=len(request["slots"]), format=frames[0].format.name):
                with patch.object(
                    self.native, "_compose_general", return_value=b"general"
                ) as general:
                    self.assertEqual(self.native.compose(request, frames), b"general")
                    general.assert_called_once_with(request, frames)

    def test_packed_rows_do_not_include_alignment_padding(self):
        request = copy.deepcopy(self.request)
        request["width"] = 190
        request["slots"][0]["crops"][0].update(width=190, crop_x=2)
        frame = self.frame()
        self.assertEqual(
            self.native.compose(request, [frame]),
            self.native._compose_general(request, [frame]),
        )
        self.assertEqual(len(self.native.compose(request, [frame])), 190 * 108 * 4)

    def test_retained_graph_matches_fresh_frames_without_mutating_physical_timestamps(self):
        cache = self.native.CompositionCache()
        for color, pixel_format in product(
            ((2, 2, 2, 0), (1, 1, 1, 1), (1, 1, 1, 2)),
            ("yuv420p", "nv12", "yuvj420p"),
        ):
            cache.clear()
            for phase, pts in enumerate((15, 30, 4, 4, 0, 999)):
                with self.subTest(color=color, pixel_format=pixel_format, pts=pts):
                    expected = self.native.compose(
                        self.request, [self.frame(color, pixel_format, phase)]
                    )
                    frame = self.frame(color, pixel_format, phase)
                    frame.pts = pts
                    self.assertEqual(
                        self.native.compose(
                            self.request,
                            [frame],
                            cache=cache,
                            source_identity=("first", 1, 2, 3, 4),
                        ),
                        expected,
                    )
                    self.assertEqual((frame.pts, frame.time_base), (pts, Fraction(1, 30)))
        self.assertGreater(cache.reuses, 0)
        cache.clear()
        self.assertEqual(len(cache.contexts), 0)

    def test_retained_graph_keys_all_input_geometry_color_chroma_and_source_properties(self):
        cache = self.native.CompositionCache()
        variants = (
            ("base", None),
            ("color", None),
            ("sar", None),
            ("chroma", None),
            ("timebase", None),
            ("focus", None),
            ("padding", None),
            ("pixel_format", "nv12"),
            ("source_dimensions", "yuv420p"),
            ("source_identity", None),
        )
        for phase, (name, pixel_format) in enumerate(variants):
            request = copy.deepcopy(self.request)
            frame = self.frame(
                (1, 1, 1, 2) if name == "color" else (2, 2, 2, 0),
                pixel_format or "yuv420p",
                phase,
            )
            if name == "sar":
                request["slots"][0]["source_sar"] = "4/3"
            if name == "chroma":
                frame.chroma_location = 2
            if name == "timebase":
                frame.time_base = Fraction(1, 1000)
            if name == "focus":
                request["slots"][0]["crops"][0].update(
                    scaled_width=288, scaled_height=162, crop_x=48, crop_y=26
                )
            if name == "padding":
                request["width"] = 190
                request["slots"][0]["crops"][0].update(width=190, crop_x=2)
            if name == "source_dimensions":
                frame = frame.reformat(width=640, height=360)
            source = ("first", 1, 2, 3, 5 if name == "source_identity" else 4)
            original_pts = frame.pts
            expected = self.native.compose(request, [frame])
            frame.pts = original_pts
            builds = cache.opens
            self.assertEqual(
                self.native.compose(request, [frame], cache=cache, source_identity=source),
                expected,
                name,
            )
            self.assertEqual(cache.opens, builds + 1, name)
            self.assertEqual(len(cache.contexts), 1)

    def test_retained_graph_cache_is_bounded_and_retires_replaced_sources(self):
        cache = self.native.CompositionCache()
        for phase, name in enumerate(("first", "second", "first", "third", "second")):
            frame = self.frame(phase=phase)
            expected = self.native.compose(self.request, [self.frame(phase=phase)])
            self.assertEqual(
                self.native.compose(
                    self.request,
                    [frame],
                    cache=cache,
                    source_identity=(name, 1, 2, 3, 4),
                ),
                expected,
            )
            self.assertLessEqual(len(cache.contexts), 2)
        self.assertEqual((cache.opens, cache.reuses), (4, 1))
        self.native.compose(
            self.request,
            [self.frame()],
            cache=cache,
            source_identity=("second", 1, 2, 3, 5),
        )
        self.assertEqual(
            sum(key[0][0] == "second" for key in cache.contexts),
            1,
        )
        nonopaque = copy.deepcopy(self.request)
        nonopaque["slots"][0]["crops"][0]["width"] = 190
        expected = self.native.compose(nonopaque, [self.frame()])
        self.assertEqual(self.native.compose(nonopaque, [self.frame()], cache=cache), expected)
        self.assertEqual(len(cache.contexts), 0)

    def test_pool_errors_and_close_retire_retained_graphs(self):
        pool = self.native.DecoderPool("cpu")
        self.native.compose(
            self.request,
            [self.frame()],
            cache=pool.composition,
            source_identity=("first", 1, 2, 3, 4),
        )
        self.assertEqual(len(pool.composition.contexts), 1)
        with self.assertRaises(self.native.DecodeCancelled):
            pool.render({"slots": [None]}, lambda: True)
        self.assertEqual(len(pool.composition.contexts), 0)
        self.native.compose(
            self.request,
            [self.frame()],
            cache=pool.composition,
            source_identity=("first", 1, 2, 3, 4),
        )
        pool.close()
        self.assertEqual(len(pool.composition.contexts), 0)
