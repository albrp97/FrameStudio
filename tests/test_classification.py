import unittest
from pathlib import Path

from framestudio_media import (
    Classification,
    MediaInfo,
    build_parser,
    classify,
    effective_jobs,
    ffmpeg_command,
    normalize_profile,
    output_format,
    output_path,
)


def info(video=(), audio=()):
    streams = [
        {"codec_type": "video", "codec_name": codec} for codec in video
    ] + [
        {"codec_type": "audio", "codec_name": codec} for codec in audio
    ]
    return MediaInfo(Path("fixture"), streams, {"duration": "10"})


class ClassificationTests(unittest.TestCase):
    def test_ffv1_pcm_is_ready(self):
        result = classify(info(("ffv1",), ("pcm_s16le",)))
        self.assertTrue(result.ready)
        self.assertEqual(result.label, "READY")

    def test_h264_aac_needs_both(self):
        result = classify(info(("h264",), ("aac",)))
        self.assertFalse(result.ready)
        self.assertTrue(result.needs_video)
        self.assertTrue(result.needs_audio)

    def test_safe_video_bad_audio_only_converts_audio(self):
        result = classify(info(("prores",), ("aac",)))
        self.assertFalse(result.needs_video)
        self.assertTrue(result.needs_audio)

    def test_audio_only_flac_is_ready(self):
        self.assertTrue(classify(info((), ("flac",))).ready)


class CommandAndCliTests(unittest.TestCase):
    def test_fast_profile_is_the_default(self):
        self.assertEqual(build_parser().parse_args([]).profile, "fast")
        self.assertEqual(normalize_profile("dnxhr"), "fast")
        self.assertEqual(build_parser().parse_args([]).jobs, 0)
        self.assertEqual(build_parser().parse_args([]).performance_mode, "auto")
        self.assertEqual(effective_jobs("fast", 0, cpu_count=12), 3)
        self.assertEqual(effective_jobs("fast", 0, cpu_count=2), 1)
        self.assertEqual(effective_jobs("lossless", 0, cpu_count=12), 1)
        self.assertEqual(effective_jobs("lossless", 3, cpu_count=12), 1)
        self.assertEqual(effective_jobs("fast", 2, cpu_count=12), 2)

    def test_deletion_defaults_on_and_can_be_disabled(self):
        self.assertTrue(build_parser().parse_args([]).delete_originals)
        self.assertFalse(build_parser().parse_args(["--keep-originals"]).delete_originals)
        self.assertTrue(build_parser().parse_args(["--delete-originals"]).delete_originals)

    def test_gpu_option_is_exposed(self):
        self.assertEqual(build_parser().parse_args([]).gpu, "on")
        self.assertEqual(build_parser().parse_args(["--gpu", "off"]).gpu, "off")

    def test_fast_command_uses_dnxhr_sq_pcm_and_mxf(self):
        source = Path("fixture.mp4")
        partial = Path("fixture.partial.mxf")
        media = MediaInfo(
            source,
            [
                {"codec_type": "video", "codec_name": "h264", "pix_fmt": "yuv420p"},
                {"codec_type": "audio", "codec_name": "aac"},
            ],
            {"duration": "10"},
        )
        command = ffmpeg_command(media, source, partial, "fast", use_gpu=True)
        self.assertIn("dnxhd", command)
        self.assertIn("dnxhr_sq", command)
        self.assertIn("pcm_s16le", command)
        self.assertNotIn("h264_cuvid", command)
        self.assertEqual(command[command.index("-f") + 1], "mxf")
        self.assertEqual(output_format(media, "fast"), "mxf")
        self.assertEqual(output_path(source, "fast", media).suffix, ".mxf")

    def test_fast_10_bit_command_uses_dnxhr_hqx(self):
        media = MediaInfo(
            Path("fixture.mp4"),
            [{"codec_type": "video", "codec_name": "hevc", "pix_fmt": "yuv420p10le"}],
            {"duration": "10"},
        )
        command = ffmpeg_command(media, media.path, Path("fixture.partial.mxf"), "fast")
        self.assertIn("dnxhr_hqx", command)
        self.assertIn("yuv422p10le", command)

    def test_fast_audio_only_command_uses_matroska(self):
        media = MediaInfo(
            Path("fixture.m4a"),
            [{"codec_type": "audio", "codec_name": "aac"}],
            {"duration": "10"},
        )
        command = ffmpeg_command(media, media.path, Path("fixture.partial.mkv"), "fast")
        self.assertNotIn("dnxhd", command)
        self.assertIn("pcm_s32le", command)
        self.assertEqual(command[command.index("-f") + 1], "matroska")

    def test_gpu_lossless_command_uses_cuda_and_vulkan(self):
        source = Path("fixture.mp4")
        partial = Path("fixture.partial.mkv")
        media = MediaInfo(
            source,
            [
                {"codec_type": "video", "codec_name": "h264", "pix_fmt": "yuv420p"},
                {"codec_type": "audio", "codec_name": "aac"},
            ],
            {"duration": "10"},
        )
        command = ffmpeg_command(media, source, partial, "lossless", use_gpu=True)
        self.assertIn("h264_cuvid", command)
        self.assertIn("ffv1_vulkan", command)
        self.assertTrue(any("hwupload" in item for item in command))

    def test_cpu_lossless_command_remains_available(self):
        source = Path("fixture.mp4")
        partial = Path("fixture.partial.mkv")
        media = MediaInfo(
            source,
            [{"codec_type": "video", "codec_name": "h264", "pix_fmt": "yuv420p"}],
            {"duration": "10"},
        )
        command = ffmpeg_command(media, source, partial, "lossless", use_gpu=False)
        self.assertIn("ffv1", command)
        self.assertNotIn("ffv1_vulkan", command)


if __name__ == "__main__":
    unittest.main()
