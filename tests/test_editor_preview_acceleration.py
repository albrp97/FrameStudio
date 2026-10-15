"""Conservative optional CUDA policy, ownership and explicit hardware verification."""

import importlib.util
import json
import os
import subprocess
import sys
import unittest
from enum import Enum
from fractions import Fraction
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from framestudio import preview_acceleration as acceleration


class SideDataType(Enum):
    SEI_UNREGISTERED = 1
    DISPLAYMATRIX = 2


class SideData(SimpleNamespace):
    def __bytes__(self):
        return b"metadata"


def stream(**changes):
    codec = SimpleNamespace(
        name="h264",
        format=SimpleNamespace(name="yuv420p"),
        colorspace=2,
        color_range=0,
        color_primaries=2,
        color_trc=2,
        sample_aspect_ratio=Fraction(1),
    )
    result = SimpleNamespace(
        codec_context=codec,
        start_time=0,
        duration=122880,
        time_base=Fraction(1, 15360),
        average_rate=Fraction(30),
        base_rate=Fraction(30),
        guessed_rate=Fraction(30),
        sample_aspect_ratio=Fraction(1),
        metadata={},
    )
    for key, value in changes.items():
        if key.startswith("codec_"):
            setattr(codec, key.removeprefix("codec_"), value)
        else:
            setattr(result, key, value)
    return result


def frame(**changes):
    result = SimpleNamespace(
        format=SimpleNamespace(name="nv12"),
        width=1920,
        height=1080,
        pts=17920,
        dts=17920,
        duration=512,
        time_base=Fraction(1, 15360),
        colorspace=2,
        color_range=0,
        color_primaries=2,
        color_trc=2,
        rotation=0,
        interlaced_frame=False,
        side_data={},
    )
    result.__dict__.update(changes)
    return result


class SharedColorPolicyTests(unittest.TestCase):
    def test_only_exact_verified_color_tuples_are_supported_without_mutation(self):
        names = ("colorspace", "color_primaries", "color_trc", "color_range")
        accepted = ((2, 2, 2, 0), (1, 1, 1, 1), (1, 1, 1, 2))
        rejected = (
            (1, 1, 1, 0),
            (1, 2, 1, 1),
            (1, 1, 2, 1),
            (2, 1, 1, 1),
            (2, 2, 2, 1),
            (1, 1, 16, 1),
            (None, 1, 1, 1),
        )
        for metadata in accepted + rejected:
            with self.subTest(metadata=metadata):
                values = dict(zip(names, metadata, strict=True))
                source = SimpleNamespace(**values)
                self.assertEqual(acceleration.supported_color(source), metadata in accepted)
                self.assertEqual(vars(source), values)
        self.assertFalse(acceleration.supported_color(object()))


class EligibilityTests(unittest.TestCase):
    def test_untagged_progressive_eight_bit_h264_with_known_timing_is_eligible(self):
        self.assertTrue(acceleration.is_eligible(stream()))

    def test_exact_bt709_limited_and_full_color_combinations_are_eligible(self):
        for color_range in (1, 2):
            for pixel_format in ("yuv420p", "yuvj420p"):
                with self.subTest(color_range=color_range, pixel_format=pixel_format):
                    candidate = stream(
                        codec_colorspace=1,
                        codec_color_primaries=1,
                        codec_color_trc=1,
                        codec_color_range=color_range,
                        codec_format=SimpleNamespace(name=pixel_format),
                    )
                    self.assertEqual(
                        acceleration.is_eligible(candidate),
                        pixel_format == "yuv420p" or color_range == 2,
                    )

    def test_other_codecs_formats_color_tags_and_uncertain_timing_are_rejected(self):
        rejected = (
            {"codec_name": "ffv1"},
            {"codec_format": SimpleNamespace(name="yuv420p10le")},
            {"codec_format": SimpleNamespace(name="cuda")},
            {"codec_colorspace": 1},
            {"codec_color_range": 1},
            {"codec_color_range": 2},
            {"codec_color_primaries": 1},
            {"codec_color_trc": 1},
            {"codec_color_trc": 16},
            {
                "codec_colorspace": 1,
                "codec_color_primaries": 1,
                "codec_color_trc": 1,
                "codec_color_range": 0,
            },
            {
                "codec_colorspace": 1,
                "codec_color_primaries": 1,
                "codec_color_trc": 16,
                "codec_color_range": 1,
            },
            {"codec_format": SimpleNamespace(name="yuvj420p")},
            {"codec_colorspace": None},
            {"codec_sample_aspect_ratio": Fraction(4, 3)},
            {"sample_aspect_ratio": Fraction(4, 3)},
            {"start_time": None},
            {"start_time": 1},
            {"duration": None},
            {"duration": 0},
            {"time_base": None},
            {"time_base": Fraction(-1)},
            {"average_rate": None},
            {"base_rate": Fraction(25)},
            {"guessed_rate": Fraction(25)},
            {"metadata": {"rotate": "90"}},
            {"metadata": {"rotate": "nan"}},
            {"metadata": {"rotate": "unknown"}},
        )
        for changes in rejected:
            with self.subTest(changes=changes):
                self.assertFalse(acceleration.is_eligible(stream(**changes)))

    def test_explicit_zero_rotation_is_eligible(self):
        self.assertTrue(acceleration.is_eligible(stream(metadata={"rotate": "0"})))


class NormalizationTests(unittest.TestCase):
    def setUp(self):
        # Pure normalization doubles must not require the optional runtime.
        self.runtime = patch.object(
            acceleration,
            "import_module",
            return_value=SimpleNamespace(FFmpegError=RuntimeError),
        )
        self.runtime.start()
        self.addCleanup(self.runtime.stop)

    def test_only_selected_hardware_frame_downloads_before_unchanged_host_normalization(self):
        for metadata in ((2, 2, 2, 0), (1, 1, 1, 1), (1, 1, 1, 2)):
            with self.subTest(metadata=metadata):
                values = dict(
                    zip(
                        ("colorspace", "color_primaries", "color_trc", "color_range"),
                        metadata,
                        strict=True,
                    )
                )
                source = frame(format=SimpleNamespace(name="cuda"), **values)
                host = frame(**values)
                expected = frame(format=SimpleNamespace(name="yuv420p"), **values)
                source.reformat = Mock(return_value=host)
                host.reformat = Mock(return_value=expected)
                self.assertIs(acceleration.normalize_frame(source), expected)
                source.reformat.assert_called_once_with(format="nv12")
                host.reformat.assert_called_once_with(format="yuv420p")
                self.assertEqual(source.pts, expected.pts)

    def test_invalid_hardware_metadata_is_rejected_before_any_host_download(self):
        for changes in (
            {"colorspace": 1},
            {"pts": None},
            {"rotation": 90},
            {"interlaced_frame": True},
            {
                "side_data": {
                    SideDataType.DISPLAYMATRIX: SimpleNamespace(type=SideDataType.DISPLAYMATRIX)
                }
            },
        ):
            with self.subTest(changes=changes):
                source = frame(format=SimpleNamespace(name="cuda"), **changes)
                source.reformat = Mock()
                with self.assertRaises(acceleration.CudaUnavailable):
                    acceleration.normalize_frame(source)
                source.reformat.assert_not_called()

    def test_hardware_download_must_preserve_format_dimensions_and_actual_metadata(self):
        for changes in (
            {"format": SimpleNamespace(name="cuda")},
            {"pts": 17921},
            {"dts": 17921},
            {"duration": 1024},
            {"time_base": Fraction(1, 90000)},
            {"colorspace": 1},
            {"color_primaries": 1},
            {"color_trc": 1},
            {"color_range": 1},
            {"width": 960},
            {"height": 540},
            {"rotation": 90},
            {"interlaced_frame": True},
        ):
            with self.subTest(changes=changes):
                source = frame(format=SimpleNamespace(name="cuda"))
                host = frame(**changes)
                source.reformat = Mock(return_value=host)
                with self.assertRaises(acceleration.CudaUnavailable):
                    acceleration.normalize_frame(source)
                source.reformat.assert_called_once_with(format="nv12")

    @unittest.skipUnless(importlib.util.find_spec("av"), "optional PyAV runtime is not installed")
    def test_hardware_transfer_capability_errors_request_explicit_fallback(self):
        import av

        self.runtime.stop()
        for error in (av.error.ExternalError(1, "download"), NotImplementedError("transfer")):
            with self.subTest(error=error):
                source = frame(format=SimpleNamespace(name="cuda"))
                source.reformat = Mock(side_effect=error)
                with self.assertRaises(acceleration.CudaUnavailable) as caught:
                    acceleration.normalize_frame(source)
                self.assertIs(caught.exception.__cause__, error)

    def test_side_data_mapping_accepts_harmless_sei_on_the_initial_frame(self):
        kind = SideDataType.SEI_UNREGISTERED
        source = frame(pts=0, side_data={kind: SideData(type=kind)})
        expected = frame(
            pts=0,
            format=SimpleNamespace(name="yuv420p"),
            side_data={kind: SideData(type=kind)},
        )
        source.reformat = Mock(return_value=expected)
        self.assertIs(acceleration.normalize_frame(source), expected)

    def test_exact_tagged_bt709_downloads_preserve_all_color_values(self):
        for color_range in (1, 2):
            with self.subTest(color_range=color_range):
                metadata = {
                    "colorspace": 1,
                    "color_primaries": 1,
                    "color_trc": 1,
                    "color_range": color_range,
                }
                source = frame(**metadata)
                expected = frame(format=SimpleNamespace(name="yuv420p"), **metadata)
                source.reformat = Mock(return_value=expected)
                self.assertIs(acceleration.normalize_frame(source), expected)
                source.reformat.assert_called_once_with(format="yuv420p")
                for name, value in metadata.items():
                    self.assertEqual(getattr(expected, name), value)

    def test_downloaded_nv12_becomes_planar_without_rewriting_timestamps_or_color(self):
        source = frame()
        expected = frame(format=SimpleNamespace(name="yuv420p"))
        source.reformat = Mock(return_value=expected)
        self.assertIs(acceleration.normalize_frame(source), expected)
        source.reformat.assert_called_once_with(format="yuv420p")
        self.assertEqual((expected.pts, expected.time_base), (source.pts, source.time_base))

    def test_planar_frames_are_returned_unchanged(self):
        source = frame(format=SimpleNamespace(name="yuv420p"))
        self.assertIs(acceleration.normalize_frame(source), source)

    def test_unsupported_metadata_rotation_interlace_and_formats_are_not_silently_changed(self):
        rejected = (
            {"format": SimpleNamespace(name="p010le")},
            {"colorspace": 1},
            {"color_range": 1},
            {"rotation": 90},
            {"interlaced_frame": True},
            {"pts": None},
            {"time_base": None},
            {
                "side_data": {
                    SideDataType.DISPLAYMATRIX: SimpleNamespace(type=SideDataType.DISPLAYMATRIX)
                }
            },
        )
        for changes in rejected:
            with self.subTest(changes=changes), self.assertRaises(acceleration.CudaUnavailable):
                acceleration.normalize_frame(frame(**changes))

    def test_a_conversion_that_changes_metadata_is_rejected(self):
        source = frame()
        source.reformat = Mock(return_value=frame(colorspace=1))
        with self.assertRaises(acceleration.CudaUnavailable):
            acceleration.normalize_frame(source)


class DeviceSessionTests(unittest.TestCase):
    def setUp(self):
        self.ffmpeg_error = type("FFmpegFailure", (RuntimeError,), {})
        self.runtime = SimpleNamespace(FFmpegError=self.ffmpeg_error, open=Mock())
        video = stream()
        video.codec_context.is_hwaccel = True
        self.runtime.open.return_value.streams = SimpleNamespace(video=[video])
        self.device = Mock()
        self.hwdevice = Mock(return_value=self.device)
        self.accel = Mock()
        self.hwaccel = Mock(return_value=self.accel)
        self.loader = patch.object(
            acceleration, "_load_runtime", return_value=(self.runtime, self.hwaccel, self.hwdevice)
        )
        self.loader.start()
        self.addCleanup(self.loader.stop)

    def test_device_is_retained_once_and_each_open_keeps_device_owned_frames(self):
        session = acceleration.CudaDeviceSession()
        try:
            first = session.open(Path("first.mp4"))
            second = session.open(Path("second.mp4"))
            self.assertIs(first, self.runtime.open.return_value)
            self.assertIs(second, first)
            self.hwdevice.assert_called_once_with("cuda", options={"primary_ctx": "1"})
            self.hwaccel.assert_called_once_with(
                "cuda",
                options={"primary_ctx": "1"},
                allow_software_fallback=False,
                is_hw_owned=True,
            )
            self.assertEqual(self.runtime.open.call_count, 2)
            self.assertEqual(self.runtime.open.call_args.kwargs, {"hwaccel": self.accel})
        finally:
            session.close()
        self.runtime.open.return_value.close.assert_not_called()
        self.assertIsNone(session._device)
        self.assertIsNone(session._accel)
        session.close()

    def test_open_after_close_is_a_programming_error_not_a_capability_fallback(self):
        session = acceleration.CudaDeviceSession()
        session.close()
        with self.assertRaisesRegex(RuntimeError, "closed") as caught:
            session.open(Path("first.mp4"))
        self.assertNotIsInstance(caught.exception, acceleration.CudaUnavailable)
        self.runtime.open.assert_not_called()

    def test_device_initialization_capability_errors_are_precise(self):
        for error in (self.ffmpeg_error("no CUDA device"), NotImplementedError("unsupported")):
            with self.subTest(error=error):
                self.hwdevice.side_effect = error
                with self.assertRaises(acceleration.CudaUnavailable) as caught:
                    acceleration.CudaDeviceSession()
                self.assertIs(caught.exception.__cause__, error)

    def test_unrelated_initialization_errors_are_not_reclassified(self):
        self.hwdevice.side_effect = TypeError("programming error")
        with self.assertRaises(TypeError):
            acceleration.CudaDeviceSession()

    def test_unsupported_hardware_codec_is_a_capability_failure(self):
        session = acceleration.CudaDeviceSession()
        try:
            self.runtime.open.side_effect = NotImplementedError("No supported hardware config")
            with self.assertRaises(acceleration.CudaUnavailable):
                session.open(Path("unsupported.mkv"))
        finally:
            session.close()

    def test_missing_source_and_other_decode_errors_are_not_hidden_by_fallback(self):
        session = acceleration.CudaDeviceSession()
        try:
            for error in (FileNotFoundError("source"), self.ffmpeg_error("bad media")):
                self.runtime.open.side_effect = error
                with self.subTest(error=error), self.assertRaises(type(error)) as caught:
                    session.open(Path("broken.mp4"))
                self.assertIs(caught.exception, error)
        finally:
            session.close()

    def test_inactive_hardware_or_unsupported_tags_close_the_rejected_container(self):
        for hardware, colorspace in ((False, 2), (True, 1)):
            with self.subTest(hardware=hardware, colorspace=colorspace):
                video = self.runtime.open.return_value.streams.video[0]
                video.codec_context.is_hwaccel = hardware
                video.codec_context.colorspace = colorspace
                session = acceleration.CudaDeviceSession()
                try:
                    with self.assertRaises(acceleration.CudaUnavailable):
                        session.open(Path("rejected.mp4"))
                    self.runtime.open.return_value.close.assert_called()
                finally:
                    session.close()


class OptionalRuntimeTests(unittest.TestCase):
    def test_import_does_not_require_pyav(self):
        script = (
            "import builtins; original=builtins.__import__\n"
            "def guarded(name,*args,**kwargs):\n"
            " if name=='av' or name.startswith('av.'): raise AssertionError(name)\n"
            " return original(name,*args,**kwargs)\n"
            "builtins.__import__=guarded\n"
            "from types import SimpleNamespace\n"
            "from framestudio.preview_acceleration import supported_color\n"
            "assert supported_color(SimpleNamespace(colorspace=1,color_primaries=1,"
            "color_trc=1,color_range=1))\n"
        )
        subprocess.run([sys.executable, "-c", script], check=True, capture_output=True)

    def test_missing_optional_runtime_has_an_explicit_capability_error(self):
        missing = ModuleNotFoundError("No module named av", name="av")
        with (
            patch.object(acceleration, "import_module", side_effect=missing),
            self.assertRaises(acceleration.CudaUnavailable),
        ):
            acceleration._load_runtime()

    def test_a_broken_runtime_dependency_is_not_misreported_as_missing_pyav(self):
        missing = ModuleNotFoundError("broken dependency", name="unrelated_dependency")
        with (
            patch.object(acceleration, "import_module", side_effect=missing),
            self.assertRaises(ModuleNotFoundError) as caught,
        ):
            acceleration._load_runtime()
        self.assertIs(caught.exception, missing)


@unittest.skipUnless(importlib.util.find_spec("av"), "optional PyAV runtime is not installed")
class NativeNormalizationTests(unittest.TestCase):
    def test_transfer_fallback_rechecks_actual_cpu_color_and_provenance(self):
        from framestudio import precise_preview_native as native

        path = Path(__file__)
        key = (*native.identity(path), 0, 1920, 1080, "auto")
        for supported in (True, False):
            with self.subTest(supported=supported):
                gpu = frame(format=SimpleNamespace(name="cuda"))
                cpu = (
                    frame(colorspace=1, color_primaries=1, color_trc=1, color_range=2)
                    if supported
                    else frame(color_range=1)
                )
                gpu_details = {"sar_num": 1, "sar_den": 1}
                cpu_details = {"sar_num": 4, "sar_den": 3, "engine": "cpu"}
                original = SimpleNamespace(
                    engine="cuda", close=Mock(), frame=Mock(return_value=(gpu, gpu_details))
                )
                fallback = SimpleNamespace(frame=Mock(return_value=(cpu, cpu_details)))
                pool = native.DecoderPool("auto")
                pool.acceleration = acceleration
                slot = {"path": str(path), "source_tick": 100000}
                with (
                    patch.object(pool, "get", return_value=(original, key, 7)),
                    patch.object(
                        acceleration,
                        "normalize_frame",
                        side_effect=acceleration.CudaUnavailable("download unavailable"),
                    ),
                    patch.object(native.av, "open"),
                    patch.object(native, "Decoder", return_value=fallback),
                    patch.object(native, "compose", return_value=b"exact") as compose,
                ):
                    if not supported:
                        with self.assertRaises(native.UnsupportedSource) as caught:
                            pool.render(
                                {"width": 1920, "height": 1080, "slots": [slot]}, lambda: False
                            )
                        self.assertIsInstance(
                            caught.exception.__cause__, acceleration.CudaUnavailable
                        )
                        compose.assert_not_called()
                    else:
                        pixels, details = pool.render(
                            {"width": 1920, "height": 1080, "slots": [slot]}, lambda: False
                        )
                        self.assertEqual(pixels, b"exact")
                        self.assertEqual(slot["source_sar"], "4/3")
                        self.assertEqual(
                            details["physical_frames"][0]["source_color"],
                            {
                                "colorspace": cpu.colorspace,
                                "range": cpu.color_range,
                                "primaries": cpu.color_primaries,
                                "transfer": cpu.color_trc,
                            },
                        )
                original.close.assert_called_once()

    def test_native_pool_downloads_selected_frame_not_discarded_decode_batch(self):
        from framestudio import precise_preview_native as native

        decoded = []
        for pts in (0, 512, 1024, 1536, 2048):
            device = frame(format=SimpleNamespace(name="cuda"), pts=pts)
            host = frame(pts=pts)
            normalized = frame(format=SimpleNamespace(name="yuv420p"), pts=pts)
            device.reformat = Mock(return_value=host)
            host.reformat = Mock(return_value=normalized)
            decoded.append(device)
        video = stream()
        packet = SimpleNamespace(
            pts=0, time_base=video.time_base, decode=Mock(return_value=decoded)
        )
        container = SimpleNamespace(
            streams=SimpleNamespace(video=[video]),
            start_time=0,
            seek=Mock(),
            demux=Mock(side_effect=lambda _stream: (item for item in (packet,))),
        )
        path = Path(__file__)
        decoder = native.Decoder(path, container, "cuda", "test hardware selection")
        key = (*native.identity(path), 0, 1920, 1080, "cuda")
        pool = native.DecoderPool("cuda")
        pool.acceleration = acceleration
        with (
            patch.object(pool, "get", return_value=(decoder, key, 0)),
            patch.object(native, "compose", return_value=b"exact RGBA"),
        ):
            pixels, details = pool.render(
                {
                    "width": 1920,
                    "height": 1080,
                    "slots": [{"path": str(path), "source_tick": 100000}],
                },
                lambda: False,
            )
        self.assertEqual(pixels, b"exact RGBA")
        self.assertEqual(details["physical_frames"][0]["pts"], 1536)
        self.assertEqual(details["physical_frames"][0]["engine"], "cuda")
        for index, device in enumerate(decoded):
            if index == 3:
                device.reformat.assert_called_once_with(format="nv12")
            else:
                device.reformat.assert_not_called()

    def test_actual_host_conversion_preserves_all_supported_color_metadata(self):
        import av

        color_names = ("colorspace", "color_primaries", "color_trc", "color_range")
        for metadata in ((2, 2, 2, 0), (1, 1, 1, 1), (1, 1, 1, 2)):
            with self.subTest(metadata=metadata):
                source = av.VideoFrame(32, 18, "nv12")
                for plane in source.planes:
                    plane.update(bytes(plane.buffer_size))
                source.pts = 17920
                source.time_base = Fraction(1, 15360)
                for name, value in zip(color_names, metadata, strict=True):
                    setattr(source, name, value)
                result = acceleration.normalize_frame(source)
                self.assertEqual(result.format.name, "yuv420p")
                for name in (
                    "pts",
                    "time_base",
                    "colorspace",
                    "color_range",
                    "color_primaries",
                    "color_trc",
                ):
                    self.assertEqual(getattr(result, name), getattr(source, name))


@unittest.skipUnless(
    os.environ.get("FRAMESTUDIO_CUDA_TEST_SOURCE"), "CUDA fixture test is explicitly opt-in"
)
class ActualCudaTests(unittest.TestCase):
    def test_actual_h264_decode_matches_ffmpeg_native_source_pixels_and_pts(self):
        import av

        source = Path(os.environ["FRAMESTUDIO_CUDA_TEST_SOURCE"])
        with av.open(str(source)) as probe:
            preflight = next(probe.decode(video=0))
            self.assertEqual(preflight.pts, 0)
            self.assertTrue(acceleration.is_eligible(probe.streams.video[0]))
        session = acceleration.CudaDeviceSession()
        try:
            with session.open(source) as container:
                video = container.streams.video[0]
                self.assertTrue(video.codec_context.is_hwaccel)
                for target in (Fraction(0), Fraction("7.6"), Fraction("7.7"), Fraction("1.137")):
                    if target:
                        container.seek(int(target / video.time_base), stream=video, backward=True)
                    decoded = next(
                        f for f in container.decode(video) if f.pts * f.time_base >= target
                    )
                    self.assertEqual(decoded.format.name, "cuda")
                    metadata = acceleration._frame_metadata(decoded)
                    physical_pts = decoded.pts * decoded.time_base
                    if not target:
                        self.assertIn("SEI_UNREGISTERED", [kind.name for kind in decoded.side_data])
                    self.assertLess(physical_pts - target, Fraction(1, 30))
                    normalized = acceleration.normalize_frame(decoded)
                    self.assertEqual(acceleration._frame_metadata(normalized), metadata)
                    assert normalized.pts is not None
                    self.assertEqual(normalized.pts * normalized.time_base, physical_pts)
                    self.assertEqual(normalized.format.name, "yuv420p")
                    actual = b"".join(
                        bytes(plane)[row * plane.line_size : row * plane.line_size + plane.width]
                        for plane in normalized.planes
                        for row in range(plane.height)
                    )
                    expected = subprocess.run(
                        [
                            "ffmpeg",
                            "-hide_banner",
                            "-loglevel",
                            "error",
                            "-nostdin",
                            "-ss",
                            str(float(target)),
                            "-noautorotate",
                            "-i",
                            str(source),
                            "-frames:v",
                            "1",
                            "-an",
                            "-sn",
                            "-dn",
                            "-f",
                            "rawvideo",
                            "-pix_fmt",
                            "yuv420p",
                            "pipe:1",
                        ],
                        capture_output=True,
                        check=True,
                        timeout=30,
                    ).stdout
                    self.assertEqual(actual, expected)
        finally:
            session.close()

    def test_tagged_bt709_limited_and_full_range_use_actual_cuda_without_metadata_rewrites(self):
        import av

        paths = json.loads(os.environ.get("FRAMESTUDIO_CUDA_TEST_TAGGED_SOURCES", "[]"))
        self.assertEqual(len(paths), 2, "Supply both tagged limited/full fixture paths")
        session = acceleration.CudaDeviceSession()
        try:
            for path in paths:
                with self.subTest(path=Path(path).name):
                    with av.open(path) as probe:
                        source = probe.streams.video[0]
                        self.assertTrue(acceleration.is_eligible(source))
                        names = ("colorspace", "color_range", "color_primaries", "color_trc")
                        metadata = tuple(getattr(source.codec_context, name) for name in names)
                    with session.open(Path(path)) as container:
                        video = container.streams.video[0]
                        self.assertTrue(video.codec_context.is_hwaccel)
                        target = Fraction("1.137")
                        container.seek(int(target / video.time_base), stream=video, backward=True)
                        decoded = next(
                            f for f in container.decode(video) if f.pts * f.time_base >= target
                        )
                        self.assertEqual(decoded.format.name, "cuda")
                        pts = decoded.pts * decoded.time_base
                        normalized = acceleration.normalize_frame(decoded)
                        assert normalized.pts is not None
                        self.assertEqual(normalized.pts * normalized.time_base, pts)
                        self.assertEqual(
                            tuple(getattr(normalized, name) for name in names), metadata
                        )
        finally:
            session.close()


if __name__ == "__main__":
    unittest.main()
