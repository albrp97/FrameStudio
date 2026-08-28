import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from framestudio.media import MediaProbeError, probe_media


class EditorMediaTests(unittest.TestCase):
    def test_probe_maps_video_metadata(self):
        payload = {
            "streams": [
                {
                    "codec_type": "video",
                    "codec_name": "h264",
                    "width": 320,
                    "height": 180,
                    "avg_frame_rate": "10/1",
                },
                {"codec_type": "audio", "codec_name": "aac"},
            ],
            "format": {
                "duration": "12.5",
                "format_name": "mov,mp4,m4a,3gp,3g2,mj2",
            },
        }
        with TemporaryDirectory() as temporary_directory:
            source = Path(temporary_directory) / "source.mp4"
            source.write_bytes(b"fixture")
            completed = type(
                "Completed", (), {"returncode": 0, "stdout": json.dumps(payload), "stderr": ""}
            )()

            with patch("framestudio.media.subprocess.run", return_value=completed):
                result = probe_media(source)

        self.assertEqual(result.duration_seconds, 12.5)
        self.assertEqual(result.width, 320)
        self.assertEqual(result.height, 180)
        self.assertEqual(result.frame_rate, "10/1")
        self.assertEqual(result.audio_codec, "aac")
        self.assertTrue(result.has_audio_stream)

    def test_probe_rejects_media_without_video(self):
        payload = {
            "streams": [{"codec_type": "audio", "codec_name": "aac"}],
            "format": {"duration": "12.5"},
        }
        with TemporaryDirectory() as temporary_directory:
            source = Path(temporary_directory) / "audio.m4a"
            source.write_bytes(b"fixture")
            completed = type(
                "Completed", (), {"returncode": 0, "stdout": json.dumps(payload), "stderr": ""}
            )()

            with patch("framestudio.media.subprocess.run", return_value=completed):
                with self.assertRaisesRegex(MediaProbeError, "video stream"):
                    probe_media(source)

    def test_missing_ffprobe_is_reported(self):
        with TemporaryDirectory() as temporary_directory:
            source = Path(temporary_directory) / "source.mp4"
            source.write_bytes(b"fixture")

            with patch(
                "framestudio.media.subprocess.run",
                side_effect=FileNotFoundError,
            ):
                with self.assertRaisesRegex(MediaProbeError, "ffprobe"):
                    probe_media(source)


if __name__ == "__main__":
    unittest.main()
