import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from framestudio.app_timeline_actions import update_selected_clip_label
from framestudio.model import Project


def _metadata(
    *,
    width: int = 320,
    height: int = 180,
    frame_rate: str = "24/1",
    duration: float = 1.0,
) -> dict[str, object]:
    return {
        "duration_seconds": duration,
        "width": width,
        "height": height,
        "frame_rate": frame_rate,
        "video_codec": "h264",
        "audio_codec": None,
        "audio_stream_present": False,
        "format_name": "mp4",
    }


def _project(root: Path) -> Project:
    source_a = root / "fixture_a.mp4"
    source_b = root / "fixture_b.mp4"
    source_a.write_bytes(b"fixture-a")
    source_b.write_bytes(b"fixture-b")
    return Project.create_multi(
        (
            (source_a, _metadata(width=320, height=180, frame_rate="24/1")),
            (source_b, _metadata(width=640, height=360, frame_rate="30/1")),
        ),
    )


class SelectedVideoDetailsTests(unittest.TestCase):
    def setUp(self):
        self._temporary_directory = tempfile.TemporaryDirectory(
            prefix="phase010-selected-details-",
            dir=str(Path(__file__).resolve().parents[1].parent),
        )
        self.addCleanup(self._temporary_directory.cleanup)
        self.project = _project(Path(self._temporary_directory.name))
        self.segments = self.project.timeline.segment_items
        self.label = SimpleNamespace(text=None)

        def set_text(value):
            self.label.text = value

        self.label.set_text = set_text
        self.window = SimpleNamespace(
            project=self.project,
            segment_timeline=self.project.timeline,
            selected_segment_id=self.segments[0].segment_id,
            selected_segment_ids=(
                self.segments[0].segment_id,
                self.segments[1].segment_id,
            ),
            timeline_selection_label=self.label,
        )

    def test_selected_source_details_use_the_focused_segment_only(self):
        update_selected_clip_label(self.window)

        self.assertEqual(
            self.label.text,
            "Selected video: fixture_a.mp4 | Dimensions: 320×180 | FPS: 24",
        )

        self.window.selected_segment_id = self.segments[1].segment_id
        update_selected_clip_label(self.window)

        self.assertEqual(
            self.label.text,
            "Selected video: fixture_b.mp4 | Dimensions: 640×360 | FPS: 30",
        )
        self.assertNotIn("Audio", self.label.text)
        self.assertNotIn("selected", self.label.text)

    def test_no_selection_and_missing_metadata_are_truthful_neutral_states(self):
        self.window.selected_segment_id = None
        self.window.selected_segment_ids = ()
        update_selected_clip_label(self.window)
        self.assertEqual(self.label.text, "No video selected")

        self.window.selected_segment_id = self.segments[1].segment_id
        self.project.source_by_id(self.segments[1].source_id).metadata.pop("width")
        update_selected_clip_label(self.window)

        self.assertEqual(self.label.text, "Selected video: metadata unavailable")
        self.assertNotIn("640", self.label.text)
        self.assertNotIn("360", self.label.text)

    def test_nonfinite_metadata_is_unavailable_without_crashing(self):
        segment = self.segments[0]
        self.window.selected_segment_id = segment.segment_id
        self.window.selected_segment_ids = (segment.segment_id,)
        source = self.project.source_by_id(segment.source_id)
        original_metadata = dict(source.metadata)
        for key in ("width", "height", "frame_rate"):
            for value in (float("nan"), float("inf"), float("-inf")):
                with self.subTest(key=key, value=value):
                    source.metadata[key] = value
                    update_selected_clip_label(self.window)
                    self.assertEqual(
                        self.label.text,
                        "Selected video: metadata unavailable",
                    )
                    source.metadata.clear()
                    source.metadata.update(original_metadata)
