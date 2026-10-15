from __future__ import annotations

import hashlib
import importlib.util
import os
import shutil
import subprocess
import threading
import time
import unittest
import uuid
import weakref
from fractions import Fraction
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from framestudio.app_project import _create_synchronized_preview_backend
from framestudio.composed_playback import FfmpegSynchronizedPlaybackBackend
from framestudio.composition import VisualTransform
from framestudio.export import resolve_output_policy
from framestudio.ffmpeg_playback import VideoFrame, _PreviewRequestCancelled
from framestudio.layout_plan import (
    FramingDomain,
    LayoutInterval,
    LayoutPlan,
    PixelRect,
    PlannedBlock,
    SlotPlan,
    SourceGeometry,
    SourceRangePlan,
    plan_crop,
    plan_project_layout,
    plan_triplicate,
    slot_rects,
)
from framestudio.media import probe_media
from framestudio.model import Project
from framestudio.preview_strategy import PreviewFrameCache


def layout_for(paths, *, focus=False, triplicate=False, sar=(1, 1)):
    canvas = PixelRect(0, 0, 192, 108)
    blocks, slots = [], []
    for index, _ in enumerate(paths):
        source_id = f"source-{index}"
        geometry = SourceGeometry(source_id, 320, 180, *sar)
        transform = VisualTransform(1.5, 120, -80) if focus else VisualTransform()
        block = PlannedBlock(
            source_id,
            source_id,
            source_id,
            index,
            source_id,
            geometry,
            SourceRangePlan(0, 1_000_000, 0, 1_000_000),
            transform,
            triplicate,
        )
        rect = slot_rects(len(paths), canvas=canvas)[index]
        slot = (
            SlotPlan(block, rect, triplicate_crops=plan_triplicate(geometry, rect, transform))
            if triplicate
            else SlotPlan(block, rect, crop=plan_crop(geometry, rect, transform))
        )
        slots.append(slot)
        blocks.append(block)
    return LayoutPlan(
        canvas,
        "absolute",
        FramingDomain.FINAL_SLOT,
        2_000_000,
        (0, 1_000_000, 2_000_000),
        tuple(blocks),
        (
            LayoutInterval(0, 1_000_000, tuple(blocks), tuple(slots)),
            LayoutInterval(1_000_000, 2_000_000, (), ()),
        ),
    )


@unittest.skipUnless(
    importlib.util.find_spec("av") and shutil.which("ffmpeg") and shutil.which("ffprobe"),
    "Optional pinned PyAV and media tools are required",
)
class PrecisePreviewFunctionalityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = Path.cwd() / f".precise-preview-fixtures-{uuid.uuid4().hex}"
        cls.root.mkdir()
        cls.paths = {}
        for name in (
            "h264",
            "second",
            "third",
            "vfr",
            "nonzero",
            "tagged",
            "tagged-full",
            "hdr",
            "sar",
            "mixed-tags",
            "untagged-limited",
            "fractional",
        ):
            path = cls.root / (
                name
                + (
                    ".mp4"
                    if name
                    in {
                        "h264",
                        "second",
                        "third",
                        "tagged",
                        "mixed-tags",
                    }
                    else ".mkv"
                )
            )
            command = [
                "ffmpeg",
                "-hide_banner",
                "-loglevel",
                "error",
                "-nostdin",
                "-f",
                "lavfi",
                "-i",
                (
                    "testsrc2=size=320x180:rate=30000/1001:duration=1.2"
                    if name == "fractional"
                    else "testsrc2=size=320x180:rate=25:duration=1.2"
                ),
                "-an",
            ]
            if name in {
                "mixed-tags",
                "untagged-limited",
            }:
                command += [
                    "-c:v",
                    "ffv1" if name == "untagged-limited" else "libx264",
                    "-preset",
                    "ultrafast",
                    "-colorspace",
                    "unknown" if name == "untagged-limited" else "bt709",
                    "-color_primaries",
                    "unknown",
                    "-color_trc",
                    "unknown",
                    "-color_range",
                    "tv",
                ]
            elif name == "vfr":
                command += [
                    "-vf",
                    "select='not(mod(n,2))+not(mod(n,5))'",
                    "-fps_mode",
                    "vfr",
                    "-c:v",
                    "ffv1",
                ]
            else:
                if name == "nonzero":
                    command += ["-vf", "setpts=PTS+5/TB", "-fps_mode", "passthrough"]
                if name == "sar":
                    command += ["-vf", "setsar=4/3"]
                command += ["-c:v", "libx264", "-preset", "ultrafast", "-g", "12", "-bf", "2"]
                if name == "hdr":
                    command += [
                        "-colorspace",
                        "bt2020nc",
                        "-color_primaries",
                        "bt2020",
                        "-color_trc",
                        "smpte2084",
                        "-color_range",
                        "tv",
                    ]
            if name in {"vfr", "nonzero", "sar", "tagged", "tagged-full", "fractional"}:
                full = name == "tagged-full"
                params = (
                    f"setparams=range={'full' if full else 'limited'}:"
                    "colorspace=bt709:color_primaries=bt709:color_trc=bt709"
                )
                if "-vf" in command:
                    command[command.index("-vf") + 1] += f",{params}"
                else:
                    command += ["-vf", params]
                command += [
                    "-colorspace",
                    "bt709",
                    "-color_primaries",
                    "bt709",
                    "-color_trc",
                    "bt709",
                    "-color_range",
                    "pc" if full else "tv",
                ]
            subprocess.run(
                command + ["-pix_fmt", "yuv420p", str(path)],
                check=True,
                capture_output=True,
                timeout=15,
            )
            cls.paths[name] = path
        cls.before = {
            name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in cls.paths.items()
        }

    @classmethod
    def tearDownClass(cls):
        after = {
            name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in cls.paths.items()
        }
        try:
            if after != cls.before:
                raise AssertionError("Preview changed original fixture media")
        finally:
            shutil.rmtree(cls.root)

    def backend(self, names=("h264",), *, engine="cpu", **options):
        paths = tuple(self.paths[name] for name in names)
        layout = layout_for(paths, **options)
        warnings = []
        backend = FfmpegSynchronizedPlaybackBackend(
            tuple((f"source-{i}", path) for i, path in enumerate(paths)),
            layout,
            192,
            108,
            25,
            lambda _: None,
            lambda _: None,
            lambda: None,
            preview_backend=engine,
            preview_cache_size=0,
            on_warning=warnings.append,
        )
        self.addCleanup(backend.close)
        return backend, warnings

    def exact_frame(self, backend, target):
        interval = backend._interval_at(target)
        reference = subprocess.run(
            backend._frame_command(target, interval),
            check=True,
            capture_output=True,
            timeout=15,
        ).stdout
        result = backend._frame_for_interval(target, interval)
        if result.data != reference:
            # PyAV bundles its own libavfilter/libswscale, while the reference
            # is the CLI ffmpeg on PATH (CI installs FFmpeg 6.1, PyAV bundles 9.x).
            # Lanczos yuv->rgba rounding can differ by a few code values across
            # those generations. Accept only the same frame within that rounding:
            # identical alpha and a bounded per-channel delta. Measured same-frame
            # mean deltas are 0.3-1.2 (FFmpeg 6.1.3 vs bundled 9.x). The nearest
            # different source frame measures about 5.7 mean delta, so 2.5 (below
            # that gap, above the observed rounding) separates the two.
            self.assertEqual(len(result.data), len(reference))
            self.assertEqual(result.data[3::4], reference[3::4])
            deltas = [abs(a - b) for a, b in zip(result.data, reference)]
            self.assertLessEqual(max(deltas), 32)
            self.assertLessEqual(sum(deltas) / len(deltas), 2.5)
        return result

    def test_exact_focus_triplicate_mixed_and_odd_width_slots(self):
        for names, options in (
            (("h264",), {"focus": True}),
            (("h264",), {"focus": True, "triplicate": True}),
            (("h264", "second"), {"focus": True}),
            (("h264", "h264", "second"), {"focus": True, "triplicate": True}),
            (("h264", "second", "third"), {"focus": True, "triplicate": True}),
        ):
            with self.subTest(names=names, options=options):
                backend, warnings = self.backend(names, **options)
                self.exact_frame(backend, 0.321)
                self.assertLessEqual(backend.precise_preview_diagnostics["contexts"], 2)
                self.assertIn("cpu", warnings[0])

    def test_initial_frame_zero_uses_actual_application_request_layout(self):
        path = self.paths["h264"]
        project = Project.create_synchronized(path, probe_media(path).metadata())
        sources = project.sources or (project.source,)
        policy = resolve_output_policy([source.metadata for source in sources])
        layout = plan_project_layout(project)
        frames: list[VideoFrame] = []
        errors: list[str] = []
        warnings: list[str] = []
        with patch.dict(os.environ, {"FRAMESTUDIO_PREVIEW_BACKEND": "auto"}):
            backend = _create_synchronized_preview_backend(
                sources,
                layout,
                policy,
                25,
                (frames.append, errors.append, lambda: None, warnings.append),
            )
        self.addCleanup(backend.close)
        interval = backend._interval_at(0)
        assert interval is not None
        reference = subprocess.run(
            backend._frame_command(0, interval),
            check=True,
            capture_output=True,
            timeout=15,
        ).stdout
        # Project attach synchronously seeks to zero before async UI scrubbing.
        backend.seek(0)
        self.assertEqual(errors, [])
        self.assertEqual(frames[-1].data, reference)
        self.assertEqual((frames[-1].width, frames[-1].height), (1920, 1080))
        physical = backend.precise_preview_stats()["physical_frames"][0]
        self.assertEqual(physical["source_tick"], 0)
        self.assertEqual(physical["pts"], 0)
        self.assertIn(physical["engine"], ("cpu", "cuda"))

    def test_uncached_forward_exactness_and_seek_discontinuities(self):
        for engine in ("cpu", "auto"):
            for name in ("tagged", "fractional", "vfr", "nonzero", "sar"):
                with self.subTest(engine=engine, name=name):
                    backend, _ = self.backend(
                        (name,),
                        engine=engine,
                        focus=True,
                        triplicate=True,
                        sar=(4, 3) if name == "sar" else (1, 1),
                    )
                    for target in (0.121, 0.161, 0.201, 0.441, 0.481, 0.521, 0.881):
                        self.exact_frame(backend, target)
                    physical = backend.precise_preview_diagnostics["physical_frames"][0]
                    self.assertGreater(physical["forward_reuses"], 0)
                    for target in (0.041, 0.921, 0.081):
                        self.exact_frame(backend, target)
                        physical = backend.precise_preview_diagnostics["physical_frames"][0]
                        if target != 0.921:
                            self.assertFalse(physical["forward_reused"])
                    self.assertEqual(backend.preview_stats()["cache_hits"], 0)

    def test_retained_composition_is_exact_across_uncached_backward_and_source_changes(self):
        for engine in ("cpu", "auto"):
            with self.subTest(engine=engine):
                backend, _ = self.backend(engine=engine, focus=True)
                for index, (name, target) in enumerate(
                    (
                        ("tagged", 0.121),
                        ("tagged", 0.161),
                        ("second", 0.521),
                        ("tagged", 0.041),
                        ("second", 0.201),
                        ("tagged-full", 0.441),
                        ("vfr", 0.159),
                        ("nonzero", 0.321),
                    )
                ):
                    backend._source_paths["source-0"] = self.paths[name]
                    self.exact_frame(backend, target)
                    diagnostic = backend.precise_preview_diagnostics
                    physical = diagnostic["physical_frames"][0]
                    self.assertLessEqual(
                        diagnostic["composition_contexts"],
                        5 if physical["engine"] == "cuda" else 2,
                    )
                    if index == 1:
                        self.assertGreater(diagnostic["composition_reuses"], 0)
                    time_base = Fraction(physical["time_base_num"], physical["time_base_den"])
                    self.assertGreaterEqual(
                        physical["pts"] * time_base,
                        Fraction(physical["effective_target_pts"]) * time_base,
                    )
                    if name == "nonzero":
                        self.assertGreater(physical["pts"], 0)
                self.assertEqual(backend.preview_stats()["cache_hits"], 0)
                process = backend._precise_preview._process
                backend.release_preview_resources()
                self.assertIsNotNone(process.poll())
                self.exact_frame(backend, 0.521)

    def test_real_render_errors_and_cancellation_clear_graphs_before_exact_recovery(self):
        from framestudio.precise_preview_native import (
            DecodeCancelled,
            DecoderPool,
            UnsupportedSource,
        )

        for engine in ("cpu", "auto"):
            with self.subTest(engine=engine):
                pool = DecoderPool(engine)
                self.addCleanup(pool.close)
                request = {
                    "width": 192,
                    "height": 108,
                    "slots": [
                        {
                            "path": str(self.paths["tagged"]),
                            "source_tick": 161_000,
                            "x": 0,
                            "y": 0,
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
                expected, _ = pool.render(request, lambda: False)
                for failure in ("cancel", "eof", "unsupported"):
                    with self.subTest(failure=failure):
                        self.assertEqual(len(pool.composition.contexts), 1)
                        if failure == "cancel":
                            with self.assertRaises(DecodeCancelled):
                                pool.render(request, lambda: True)
                        elif failure == "eof":
                            request["slots"][0]["source_tick"] = 2_000_000
                            with self.assertRaisesRegex(ValueError, "ended"):
                                pool.render(request, lambda: False)
                        else:
                            request["slots"][0]["path"] = str(self.paths["hdr"])
                            with self.assertRaises(UnsupportedSource):
                                pool.render(request, lambda: False)
                        self.assertEqual(len(pool.composition.contexts), 0)
                        request["slots"][0].update(
                            path=str(self.paths["tagged"]), source_tick=161_000
                        )
                        actual, diagnostic = pool.render(request, lambda: False)
                        self.assertEqual(actual, expected)
                        self.assertEqual(diagnostic["composition_contexts"], 1)
                pool.close()
                self.assertEqual(len(pool.composition.contexts), 0)

    def test_native_forward_physical_pts_end_and_cancel_match_always_seek(self):
        from framestudio.precise_preview_native import DecodeCancelled, DecoderPool

        def rgba(frame):
            converted = frame.reformat(format="rgba")
            plane = converted.planes[0]
            data = memoryview(plane)
            return b"".join(
                data[y * plane.line_size : y * plane.line_size + converted.width * 4]
                for y in range(converted.height)
            )

        for engine in ("cpu", "auto"):
            for name in ("tagged", "fractional", "vfr", "nonzero", "sar"):
                with self.subTest(engine=engine, name=name):
                    pool, reference = DecoderPool(engine), DecoderPool(engine)
                    self.addCleanup(pool.close)
                    self.addCleanup(reference.close)
                    decoder, _, _ = pool.get(self.paths[name], 192, 108)
                    always_seek, _, _ = reference.get(self.paths[name], 192, 108)
                    always_seek.FORWARD_MAX_FRAMES = 0
                    for tick in (
                        121_000,
                        161_000,
                        201_000,
                        441_000,
                        481_000,
                        521_000,
                        881_000,
                        1_080_000,
                        1_120_000,
                    ):
                        frame, actual = decoder.frame(tick, lambda: False)
                        expected_frame, expected = always_seek.frame(tick, lambda: False)
                        self.assertEqual(
                            (actual["pts"], actual["time_base_num"], actual["time_base_den"]),
                            (expected["pts"], expected["time_base_num"], expected["time_base_den"]),
                        )
                        if decoder.engine == "cuda":
                            frame = pool.acceleration.normalize_frame(frame)
                            expected_frame = reference.acceleration.normalize_frame(expected_frame)
                        self.assertEqual(rgba(frame), rgba(expected_frame))
                        frame.pts = 0
                        del frame, expected_frame
                    with self.assertRaisesRegex(ValueError, "ended"):
                        decoder.frame(1_210_000, lambda: False)
                    self.assertIsNone(decoder._packets)
                    with self.assertRaises(DecodeCancelled):
                        decoder.frame(80_000, lambda: True)
                    _, timestamp = decoder.frame(240_000, lambda: False)
                    self.assertFalse(timestamp["forward_reused"])
                    pool.close()
                    reference.close()

    def test_eviction_and_release_drop_forward_iterators_before_containers(self):
        from framestudio.precise_preview_native import DecoderPool

        for engine in ("cpu", "auto"):
            with self.subTest(engine=engine):
                pool = DecoderPool(engine, max_cuda_contexts=2)
                self.addCleanup(pool.close)
                first, _, _ = pool.get(self.paths["tagged"], 192, 108)
                first.frame(121_000, lambda: False)
                self.assertIsNotNone(first._packets)
                second, _, _ = pool.get(self.paths["second"], 192, 108)
                second.frame(121_000, lambda: False)
                pool.get(self.paths["third"], 192, 108)
                self.assertIsNone(first._packets)
                self.assertEqual(len(first._pending), 0)
                self.assertIsNone(first.container)
                pool.close()
                self.assertIsNone(second._packets)
                self.assertEqual(len(second._pending), 0)
                self.assertIsNone(second.container)

    def test_vfr_non_h264_and_nonzero_start_exact_boundaries(self):
        for name in ("vfr", "nonzero"):
            backend, _ = self.backend((name,))
            for target in (0.039, 0.041, 0.159, 0.160001, 0.201):
                with self.subTest(name=name, target=target):
                    result = self.exact_frame(backend, target)
                    physical = backend.precise_preview_diagnostics["physical_frames"][0]
                    self.assertEqual(physical["engine"], "cpu")
                    self.assertEqual(physical["nonref_enabled"], name != "vfr")
                    self.assertGreaterEqual(result.decoded_position_seconds + 0.001, target)
            if name == "nonzero":
                self.assertGreater(physical["origin_tick"], 0)
                self.assertGreater(physical["pts"], 0)

    def test_tagged_bt709_color_is_exact_without_erasing_source_tags(self):
        for names, options in (
            (("tagged",), {}),
            (("tagged-full",), {"focus": True}),
            (("tagged", "tagged-full"), {"focus": True, "triplicate": True}),
            (("tagged", "h264", "tagged-full"), {"focus": True, "triplicate": True}),
        ):
            with self.subTest(names=names):
                backend, warnings = self.backend(names, **options)
                self.exact_frame(backend, 0.321)
                self.assertEqual(backend.precise_preview_stats()["selected_engine"], "cpu")
                self.assertIn("cpu", warnings[0])
                for frame, name in zip(
                    backend.precise_preview_diagnostics["physical_frames"], names, strict=True
                ):
                    if name != "h264":
                        self.assertEqual(frame["source_color"]["colorspace"], 1)
                        self.assertEqual(frame["source_color"]["primaries"], 1)
                        self.assertEqual(frame["source_color"]["transfer"], 1)
                        self.assertEqual(
                            frame["source_color"]["range"], 2 if name == "tagged-full" else 1
                        )

    def test_unproven_hdr_uses_explicit_reference_fallback(self):
        backend, warnings = self.backend(("hdr",))
        self.exact_frame(backend, 0.321)
        self.assertIn("color metadata", warnings[0])
        self.assertIn("reference FFmpeg", warnings[0])
        self.assertEqual(backend.precise_preview_diagnostics["selected_engine"], "ffmpeg")

    def test_unproven_native_context_is_rejected_before_decode(self):
        import av

        from framestudio.precise_preview_native import DecoderPool, UnsupportedSource

        # H264 VUI cannot encode a tagged-but-unknown range. Exercise this
        # native preflight state directly rather than inventing a media claim.
        for tags in ((1, 1, 1, 0), (1, 2, 2, 0), (1, 2, 1, 1), (1, 1, 2, 1)):
            with self.subTest(tags=tags):
                container = av.open(str(self.paths["h264"]))
                codec = container.streams.video[0].codec_context
                (
                    codec.colorspace,
                    codec.color_primaries,
                    codec.color_trc,
                    codec.color_range,
                ) = tags
                pool = DecoderPool("cpu")
                self.addCleanup(pool.close)
                with patch("framestudio.precise_preview_native.av.open", return_value=container):
                    with self.assertRaisesRegex(UnsupportedSource, "selected reference FFmpeg"):
                        pool.get(self.paths["h264"], 192, 108)
                self.assertEqual(len(pool.contexts), 0)

    def test_unproven_mixed_tags_use_reference_fallback(self):
        import av

        for name, expected in (
            ("mixed-tags", (1, 2, 2, 1)),
            ("untagged-limited", (2, 2, 2, 1)),
        ):
            with self.subTest(name=name):
                with av.open(str(self.paths[name])) as container:
                    codec = container.streams.video[0].codec_context
                    self.assertEqual(
                        (
                            codec.colorspace,
                            codec.color_primaries,
                            codec.color_trc,
                            codec.color_range,
                        ),
                        expected,
                    )
                backend, warnings = self.backend((name,))
                self.exact_frame(backend, 0.321)
                self.assertEqual(backend.precise_preview_stats()["selected_engine"], "ffmpeg")
                self.assertIn("color metadata", warnings[0])
                self.assertIn("reference FFmpeg", warnings[0])

    def test_auto_cuda_or_explicit_cpu_selection_stays_exact(self):
        backend, warnings = self.backend(("h264", "second"), engine="auto", focus=True)
        self.exact_frame(backend, 0.321)
        for frame in backend.precise_preview_diagnostics["physical_frames"]:
            self.assertIn(frame["engine"], ("cpu", "cuda"))
            self.assertTrue(frame["reason"])
        self.assertTrue(warnings)
        backend, _ = self.backend(("vfr",), engine="auto")
        self.exact_frame(backend, 0.321)
        frame = backend.precise_preview_diagnostics["physical_frames"][0]
        self.assertEqual(frame["engine"], "cpu")
        self.assertIn("not eligible", frame["reason"])
        snapshot = backend.precise_preview_stats()
        self.assertEqual(snapshot["selected_engine"], "cpu")
        self.assertIsInstance(snapshot["helper_pid"], int)
        self.assertEqual(snapshot["contexts"], 1)
        self.assertEqual(snapshot["requests"], 1)

    def test_black_gap_does_not_start_helper(self):
        backend, _ = self.backend()
        result = backend._frame_for_interval(1.2, backend._interval_at(1.2))
        self.assertEqual(result.data, bytes((0, 0, 0, 255)) * (192 * 108))
        self.assertIsNone(backend._precise_preview._process)

    def test_black_gap_preserves_live_composition_counts_and_release_zeroes_them(self):
        backend, _ = self.backend()
        self.exact_frame(backend, 0.321)
        self.assertEqual(backend.precise_preview_stats()["composition_contexts"], 1)
        backend._frame_for_interval(1.2, backend._interval_at(1.2))
        self.assertEqual(backend.precise_preview_stats()["composition_contexts"], 1)
        backend.release_preview_resources()
        diagnostic = backend.precise_preview_stats()
        self.assertEqual(diagnostic["composition_contexts"], 0)
        self.assertEqual(diagnostic["last_request_composition_contexts"], 1)

    def test_non_square_sar_is_preserved_at_buffer_initialization(self):
        backend, _ = self.backend(("sar",), engine="auto", sar=(4, 3), focus=True)
        self.exact_frame(backend, 0.321)
        physical = backend.precise_preview_diagnostics["physical_frames"][0]
        self.assertEqual((physical["sar_num"], physical["sar_den"]), (4, 3))
        self.assertEqual(physical["engine"], "cpu")

    def test_lru_uses_two_physical_paths_not_logical_source_ids(self):
        backend, _ = self.backend()
        interval = backend._interval_at(0.321)
        for name in ("h264", "second", "third", "h264"):
            backend._source_paths["source-0"] = self.paths[name]
            backend._frame_for_interval(0.321, interval)
        diagnostic = backend.precise_preview_diagnostics
        self.assertEqual(diagnostic["contexts"], 2)
        self.assertEqual(diagnostic["context_opens"], 4)
        self.assertEqual(diagnostic["context_evictions"], 2)

    def test_worker_five_source_revisits_are_exact_with_engine_bounded_residency(self):
        paths = []
        for index in range(5):
            path = self.root / f"resident-{index}.mp4"
            shutil.copyfile(self.paths["h264"], path)
            self.addCleanup(path.unlink)
            paths.append(path)
        backend, _ = self.backend(engine="auto")
        for target in (0.121, 0.161):
            for path in paths:
                backend._source_paths["source-0"] = path
                self.exact_frame(backend, target)
        diagnostic = backend.precise_preview_diagnostics
        gpu = diagnostic["physical_frames"][0]["engine"] == "cuda"
        self.assertEqual(diagnostic["contexts"], 5 if gpu else 2)
        self.assertEqual(diagnostic["composition_contexts"], 5 if gpu else 2)
        self.assertEqual(diagnostic["context_opens"], 5 if gpu else 10)
        self.assertEqual(diagnostic["context_evictions"], 0 if gpu else 8)
        process = backend._precise_preview._process
        backend.release_preview_resources()
        self.assertIsNotNone(process.poll())
        self.assertEqual(backend.precise_preview_stats()["composition_contexts"], 0)

    def test_source_stat_change_invalidates_context_and_cache_namespace(self):
        backend, _ = self.backend()
        target = 0.321
        self.exact_frame(backend, target)
        before = backend._preview_cache_namespace(target)
        path = self.paths["h264"]
        stat = path.stat()
        os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns + 1_000_000))
        self.assertNotEqual(before, backend._preview_cache_namespace(target))
        self.exact_frame(backend, target)
        self.assertEqual(backend.precise_preview_diagnostics["context_opens"], 2)
        self.assertEqual(backend.precise_preview_diagnostics["contexts"], 1)

    def test_cancellation_drains_old_response_and_next_frame_is_exact(self):
        backend, _ = self.backend()
        cancelled = threading.Event()
        cancelled.set()
        with self.assertRaises(_PreviewRequestCancelled):
            backend._frame_for_interval(
                0.321, backend._interval_at(0.321), cancel_check=cancelled.is_set
            )
        cancelled.clear()
        self.exact_frame(backend, 0.521)
        self.assertEqual(backend.precise_preview_diagnostics["id"], 1)

    def test_resource_soft_retirement_restarts_helper(self):
        backend, _ = self.backend()
        with patch.dict(os.environ, {"FRAMESTUDIO_PREVIEW_RSS_LIMIT_MB": "1"}):
            self.exact_frame(backend, 0.321)
            self.assertTrue(backend.precise_preview_diagnostics["retire"])
            self.assertIsNone(backend._precise_preview._process)
            self.exact_frame(backend, 0.521)
            self.assertTrue(backend.precise_preview_diagnostics["retire"])

    def test_stop_reaps_worker_and_next_request_reopens(self):
        backend, _ = self.backend()
        self.exact_frame(backend, 0.321)
        process = backend._precise_preview._process
        backend.stop()
        self.assertIsNotNone(process.poll())
        self.assertEqual(backend.precise_preview_stats()["contexts"], 0)
        self.exact_frame(backend, 0.521)
        self.assertIsNot(backend._precise_preview._process, process)

    def test_release_idle_preview_resources_preserves_state_cache_and_reuse(self):
        backend, _ = self.backend(engine="auto")
        backend._preview_cache = PreviewFrameCache(8, 25)
        frame = self.exact_frame(backend, 0.321)
        backend._preview_cache.put(frame, namespace=backend._preview_cache_namespace(0.321))
        process = backend._precise_preview._process
        before_position = backend.current_position()
        before_cache = dict(backend._preview_cache._frames)
        before_paused = backend._paused
        backend.release_preview_resources()
        self.assertIsNotNone(process.poll())
        self.assertEqual(backend.current_position(), before_position)
        self.assertEqual(backend._paused, before_paused)
        self.assertEqual(dict(backend._preview_cache._frames), before_cache)
        self.assertFalse(backend._precise_preview.snapshot()["closed"])
        self.assertEqual(backend.precise_preview_stats()["contexts"], 0)
        self.exact_frame(backend, 0.521)
        self.assertIsNot(backend._precise_preview._process, process)

    def test_play_pause_export_release_reaps_stream_and_preserves_reuse(self):
        for engine in ("auto", "cpu", "ffmpeg"):
            with self.subTest(engine=engine):
                backend, _ = self.backend(engine=engine)
                backend.seek(0.121)
                native = (
                    backend._precise_preview._process
                    if backend._precise_preview is not None
                    else None
                )
                ready = threading.Event()
                errors = []
                backend.on_frame = lambda _, ready=ready: ready.set()
                backend.on_error = errors.append
                backend.play()
                self.assertTrue(ready.wait(3), errors)
                backend.pause()
                worker = backend._playback_thread
                decoder = backend._realtime_decoder
                self.assertIsNotNone(worker)
                self.assertIsNotNone(decoder)
                self.assertTrue(worker.is_alive())
                self.assertIsNone(decoder.process.poll())
                position = backend.current_position()
                layout, sources = backend._layout, backend._source_items
                cache = dict(backend._preview_cache._frames)
                released = threading.Event()

                def export_handoff(backend=backend, errors=errors, released=released):
                    try:
                        backend.release_preview_resources()
                    except Exception as error:
                        errors.append(str(error))
                    finally:
                        released.set()

                export_worker = threading.Thread(target=export_handoff)
                export_worker.start()
                self.assertTrue(released.wait(5))
                export_worker.join(timeout=1)
                # These are the resources that must be gone before rendering starts.
                self.assertFalse(worker.is_alive())
                self.assertIsNotNone(decoder.process.poll())
                self.assertFalse(decoder.stderr_thread.is_alive())
                self.assertIsNone(backend._realtime_decoder)
                self.assertIsNone(backend._realtime_decode_process)
                if native is not None:
                    self.assertIsNotNone(native.poll())
                self.assertTrue(backend._paused)
                self.assertEqual(backend.current_position(), position)
                self.assertIs(backend._layout, layout)
                self.assertIs(backend._source_items, sources)
                self.assertEqual(dict(backend._preview_cache._frames), cache)
                self.assertEqual(errors, [])
                backend.seek(0.521)
                if native is not None:
                    self.assertIsNot(backend._precise_preview._process, native)
                ready.clear()
                backend.play()
                self.assertTrue(ready.wait(3), errors)
                self.assertIsNot(backend._playback_thread, worker)
                self.assertNotEqual(backend._realtime_decoder.process.pid, decoder.process.pid)
                backend.pause()
                backend.release_preview_resources()

    def test_latest_requests_and_eight_frame_cache_preserve_delivery(self):
        backend, _ = self.backend()
        backend._preview_cache = PreviewFrameCache(8, 25)
        frames = []
        ready = threading.Event()

        def receive(frame):
            frames.append(frame)
            ready.set()

        backend.on_frame = receive
        backend.request_preview(0.321)
        self.assertTrue(ready.wait(3))
        first_id = backend.precise_preview_diagnostics["id"]
        ready.clear()
        backend.request_preview(0.321)
        self.assertTrue(ready.wait(0.1))
        self.assertEqual(backend.precise_preview_diagnostics["id"], first_id)
        self.assertEqual(backend.preview_stats()["cache_hits"], 1)
        for target in (0.121, 0.521, 0.721):
            backend.request_preview(target)
        deadline = time.monotonic() + 3
        while frames[-1].position_seconds != 0.721 and time.monotonic() < deadline:
            time.sleep(0.005)
        self.assertEqual(frames[-1].position_seconds, 0.721)
        reference = subprocess.run(
            backend._frame_command(0.721, backend._interval_at(0.721)),
            check=True,
            capture_output=True,
            timeout=15,
        ).stdout
        self.assertEqual(frames[-1].data, reference)
        self.assertEqual(backend.preview_stats()["failures"], 0)


class ForwardDecoderStateTests(unittest.TestCase):
    def decoder(self, groups):
        from framestudio.precise_preview_native import Decoder

        codec = SimpleNamespace(name="h264", thread_count=1, sample_aspect_ratio=Fraction(1))
        stream = SimpleNamespace(
            codec_context=codec,
            time_base=Fraction(1, 1000),
            average_rate=Fraction(25),
            sample_aspect_ratio=Fraction(1),
        )
        self.seeks = []
        self.closed = []
        self.frame_refs = []
        self.skip_decisions = []

        class Frame:
            def __init__(frame, pts):
                frame.pts, frame.time_base = pts, stream.time_base
                self.frame_refs.append(weakref.ref(frame))

        def demux(_):
            try:
                for pts_values in groups:

                    def decode(pts_values=pts_values):
                        self.skip_decisions.append((pts_values[0], codec.skip_frame))
                        return [Frame(pts) for pts in pts_values]

                    yield SimpleNamespace(
                        pts=pts_values[0],
                        time_base=stream.time_base,
                        decode=decode,
                    )
            finally:
                self.closed.append("iterator")

        container = SimpleNamespace(
            streams=SimpleNamespace(video=[stream]),
            start_time=0,
            seek=lambda *args, **kwargs: self.seeks.append(args[0]),
            demux=demux,
            close=lambda: self.closed.append("container"),
        )
        decoder = Decoder(Path("fake"), container, "cuda", "state test")
        self.addCleanup(lambda: decoder.close() if decoder.container is not None else None)
        return decoder

    def test_retains_pending_b_frames_without_old_callback_or_mutated_pts(self):
        decoder = self.decoder(((0,), (40, 80), (120,)))
        old_cancelled = False
        frame, _ = decoder.frame(40_000, lambda: old_cancelled)
        frame.pts = 0  # Composition owns and rewrites the returned frame.
        old_cancelled = True
        frame, timestamp = decoder.frame(80_000, lambda: False)
        self.assertEqual(frame.pts, 80)
        self.assertEqual(self.seeks, [40])
        self.assertTrue(timestamp["forward_reused"])
        self.assertLessEqual(len(decoder._pending), 2)
        del frame
        self.assertLessEqual(sum(ref() is not None for ref in self.frame_refs), 1)
        decoder.close()
        self.assertFalse(any(ref() is not None for ref in self.frame_refs))
        self.assertEqual(self.closed, ["iterator", "container"])

    def test_cancel_eof_and_backward_reset_before_next_request(self):
        from framestudio.precise_preview_native import DecodeCancelled

        decoder = self.decoder(((0,), (40,), (80,)))
        decoder.frame(0, lambda: False)
        with self.assertRaises(DecodeCancelled):
            decoder.frame(40_000, lambda: True)
        self.assertIsNone(decoder._packets)
        _, timestamp = decoder.frame(40_000, lambda: False)
        self.assertFalse(timestamp["forward_reused"])
        with self.assertRaisesRegex(ValueError, "ended"):
            decoder.frame(120_000, lambda: False)
        self.assertIsNone(decoder._packets)
        _, timestamp = decoder.frame(0, lambda: False)
        self.assertFalse(timestamp["forward_reused"])
        self.assertEqual(len(self.seeks), 3)

    def test_oversized_flush_batch_does_not_retain_hardware_surfaces(self):
        decoder = self.decoder(((0,), (40, 80, 120, 160)))
        decoder.frame(40_000, lambda: False)
        self.assertIsNone(decoder._packets)
        self.assertEqual(len(decoder._pending), 0)
        frame, timestamp = decoder.frame(80_000, lambda: False)
        self.assertEqual(frame.pts, 80)
        self.assertFalse(timestamp["forward_reused"])

    def test_distant_or_same_selected_position_seeks(self):
        decoder = self.decoder(((0,), (40,), (4000,)))
        decoder.frame(0, lambda: False)
        _, timestamp = decoder.frame(4_000_000, lambda: False)
        self.assertFalse(timestamp["forward_reused"])
        _, timestamp = decoder.frame(4_000_000, lambda: False)
        self.assertFalse(timestamp["forward_reused"])
        self.assertEqual(self.seeks, [0, 4000, 4000])

    def test_current_target_controls_nonref_and_mid_decode_cancel_resets(self):
        from framestudio.precise_preview_native import DecodeCancelled

        decoder = self.decoder(((0,), (40,), (80,), (120,)))
        decoder.frame(40_000, lambda: False)
        decoder.frame(120_000, lambda: False)
        self.assertIn((80, "NONREF"), self.skip_decisions)
        decoder.frame(0, lambda: False)
        calls = 0

        def cancel_during_decode():
            nonlocal calls
            calls += 1
            return calls == 3

        with self.assertRaises(DecodeCancelled):
            decoder.frame(80_000, cancel_during_decode)
        self.assertIsNone(decoder._packets)
        self.assertEqual(len(decoder._pending), 0)
        frame, timestamp = decoder.frame(80_000, lambda: False)
        self.assertEqual(frame.pts, 80)
        self.assertFalse(timestamp["forward_reused"])


if __name__ == "__main__":
    unittest.main()
