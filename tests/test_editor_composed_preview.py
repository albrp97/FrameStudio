from __future__ import annotations

import hashlib
import shutil
import subprocess
import threading
import time
import unittest
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from framestudio.app_playback import poll_playback, stop_backend
from framestudio.app_project import attach_project, refresh_playback_backend
from framestudio.audio import AUDIO_POLICY_VERSION
from framestudio.composed_playback import FfmpegSynchronizedPlaybackBackend
from framestudio.composition import TriplicateGroup, VisualTransform
from framestudio.ffmpeg_playback import VideoFrame
from framestudio.layout_plan import CropPlan, LayoutPlan, plan_project_layout
from framestudio.media import probe_media
from framestudio.model import Project, ProjectValidationError
from framestudio.operations import remove_blocks, undo_removed_blocks
from framestudio.persistence import load_project, save_project
from framestudio.playback import PlaybackState
from tests.test_editor_layout_plan_functionality import make_block as _make_block
from tests.test_editor_video_compositor_functionality import _marker_centroid

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
TEST_ROOT = Path(__file__).resolve().parent
CANVAS_WIDTH = 1920
CANVAS_HEIGHT = 1080
EXPECTED_FIXTURE_INTERVALS = (
    (),
    ("red-main",),
    ("red-main", "green-main"),
    ("red-main", "green-main", "blue-triplicate"),
    ("red-main", "green-main", "blue-triplicate", "yellow-main"),
    ("red-main", "blue-triplicate", "yellow-main"),
    (),
    ("blue-tail",),
    ("red-tail", "blue-tail"),
    ("red-tail",),
)


@dataclass(frozen=True)
class PreviewFixture:
    root: Path
    sources: tuple[Path, ...]
    project_path: Path
    project: Project
    layout: LayoutPlan
    source_hashes: dict[Path, str]
    source_backgrounds: dict[str, tuple[int, int, int]]
    marker_dimensions: dict[str, tuple[int, int]]


@contextmanager
def isolated_directory(prefix: str):
    root = TEST_ROOT / f".{prefix}-{uuid.uuid4().hex}"
    root.mkdir()
    try:
        yield root
    finally:
        shutil.rmtree(root, ignore_errors=True)


def _run(command: list[str]) -> None:
    result = subprocess.run(
        command,
        cwd=str(REPOSITORY_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise AssertionError(
            f"Command failed ({result.returncode}): {' '.join(command)}\n{result.stderr}",
        )


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _make_audible_marker_source(
    root: Path,
    name: str,
    *,
    width: int,
    height: int,
    color: str,
    frequency: int,
) -> Path:
    path = root / name
    marker_width = max(24, min(width, height) // 20)
    marker_height = max(24, min(width, height) // 20)
    marker_filter = (
        f"drawbox=x={width // 2 - marker_width // 2}:"
        f"y={height // 2 - marker_height // 2}:"
        f"w={marker_width}:h={marker_height}:color=white:t=fill"
    )
    _run(
        [
            shutil.which("ffmpeg") or "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-nostdin",
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"color=c={color}:s={width}x{height}:r=12:d=4",
            "-f",
            "lavfi",
            "-i",
            f"sine=frequency={frequency}:sample_rate=48000:duration=4",
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-vf",
            marker_filter,
            "-c:v",
            "libx264",
            "-preset",
            "ultrafast",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "64k",
            "-ar",
            "48000",
            "-ac",
            "1",
            "-movflags",
            "+faststart",
            str(path),
        ],
    )
    return path


def _ready_audio_settings(source) -> dict[str, object]:
    return {
        "status": "ready",
        "gain_db": 0.0,
        "policy_version": AUDIO_POLICY_VERSION,
        "source_fingerprint": {
            "size_bytes": source.size_bytes,
            "modified_time_ns": source.modified_time_ns,
        },
        "measurements": {
            "peak_db": -20.0,
            "mean_rms_db": -23.0,
            "median_db": -23.0,
            "sample_count": 48_000,
        },
    }


def build_four_track_fixture(root: Path) -> PreviewFixture:
    fixture_root = root / "fixtures"
    fixture_root.mkdir()
    sources = (
        _make_audible_marker_source(
            fixture_root,
            "red-portrait.mp4",
            width=360,
            height=640,
            color="red",
            frequency=440,
        ),
        _make_audible_marker_source(
            fixture_root,
            "green-landscape.mp4",
            width=640,
            height=360,
            color="green",
            frequency=550,
        ),
        _make_audible_marker_source(
            fixture_root,
            "blue-ultrawide.mp4",
            width=800,
            height=300,
            color="blue",
            frequency=660,
        ),
        _make_audible_marker_source(
            fixture_root,
            "yellow-square.mp4",
            width=480,
            height=480,
            color="yellow",
            frequency=770,
        ),
    )
    probes = tuple(probe_media(path) for path in sources)
    for path, probe in zip(sources, probes, strict=True):
        if not probe.audio_stream_present:
            raise AssertionError(f"Fixture is missing its required audio stream: {path.name}")
        if probe.width <= 0 or probe.height <= 0 or probe.duration_seconds <= 0:
            raise AssertionError(f"Fixture probe is invalid: {path.name}")
    project = Project.create_synchronized_multi(
        tuple((path, probe.metadata()) for path, probe in zip(sources, probes, strict=True)),
        project_id="ticket-120-four-track-fixture",
    )
    for track_id in ("track-2", "track-3", "track-4"):
        project.timeline.add_track(track_id)
    source_ids = tuple(source.source_id for source in project.sources or ())
    transformed = VisualTransform(zoom=1.5, offset_x=120.0, offset_y=-80.0)
    triplicate = TriplicateGroup.create(transformed, group_id="ticket-120-triplicate")
    project.timeline.replace_track_blocks(
        "track-1",
        (
            _make_block(
                segment_id="red-main",
                source_id=source_ids[0],
                track_id="track-1",
                source_start=0.0,
                source_end=3.0,
                timeline_start=0.5,
                timeline_end=3.5,
            ),
            _make_block(
                segment_id="red-tail",
                source_id=source_ids[0],
                track_id="track-1",
                source_start=3.0,
                source_end=3.75,
                timeline_start=4.25,
                timeline_end=5.0,
            ),
        ),
    )
    project.timeline.replace_track_blocks(
        "track-2",
        (
            _make_block(
                segment_id="green-main",
                source_id=source_ids[1],
                track_id="track-2",
                source_start=0.0,
                source_end=2.0,
                timeline_start=1.0,
                timeline_end=3.0,
            ),
        ),
    )
    project.timeline.replace_track_blocks(
        "track-3",
        (
            _make_block(
                segment_id="blue-triplicate",
                source_id=source_ids[2],
                track_id="track-3",
                source_start=0.0,
                source_end=2.0,
                timeline_start=1.5,
                timeline_end=3.5,
                visual_transform=transformed,
                triplicate=triplicate,
            ),
            _make_block(
                segment_id="blue-tail",
                source_id=source_ids[2],
                track_id="track-3",
                source_start=1.5,
                source_end=2.0,
                timeline_start=4.0,
                timeline_end=4.5,
                visual_transform=VisualTransform(zoom=1.2, offset_x=-90.0, offset_y=60.0),
            ),
        ),
    )
    project.timeline.replace_track_blocks(
        "track-4",
        (
            _make_block(
                segment_id="yellow-main",
                source_id=source_ids[3],
                track_id="track-4",
                source_start=0.0,
                source_end=1.5,
                timeline_start=2.0,
                timeline_end=3.5,
            ),
        ),
    )
    project.duration_seconds = project.timeline.timeline_duration_seconds
    for source in project.sources or ():
        project.set_source_audio_settings(source.source_id, _ready_audio_settings(source))
    project.validate()
    layout = plan_project_layout(project)
    if layout.final_duration_ticks != 5_000_000:
        raise AssertionError(f"Unexpected fixture duration: {layout.final_duration_ticks}")
    actual_intervals = tuple(interval.active_block_ids for interval in layout.intervals)
    if actual_intervals != EXPECTED_FIXTURE_INTERVALS:
        raise AssertionError(
            f"Fixture layout is not the changing-count contract: {actual_intervals!r}",
        )
    if not layout.interval_at(3_750_000).is_black:
        raise AssertionError("Fixture gap is not represented as a black interval")
    if not any(slot.is_triplicate for interval in layout.intervals for slot in interval.slots):
        raise AssertionError("Fixture did not retain its triplicate block")

    project_path = root / "four-track.framestudio.json"
    save_project(project, project_path)
    reopened = load_project(project_path)
    if reopened.to_dict() != project.to_dict():
        raise AssertionError("Fixture project did not survive its persistence round trip")
    source_hashes = {path: _sha256(path) for path in sources}
    for path, expected_hash in source_hashes.items():
        if _sha256(path) != expected_hash:
            raise AssertionError(f"Fixture source changed during preflight: {path.name}")
    return PreviewFixture(
        root=root,
        sources=sources,
        project_path=project_path,
        project=reopened,
        layout=plan_project_layout(reopened),
        source_hashes=source_hashes,
        source_backgrounds={
            source_ids[0]: (253, 0, 0),
            source_ids[1]: (0, 127, 0),
            source_ids[2]: (0, 0, 254),
            source_ids[3]: (253, 253, 0),
        },
        marker_dimensions={
            source_ids[0]: (24, 24),
            source_ids[1]: (24, 24),
            source_ids[2]: (24, 24),
            source_ids[3]: (24, 24),
        },
    )


def make_editor_window(
    frames: list[tuple[VideoFrame, int | None]],
    errors: list[tuple[str, int | None]],
    warnings: list[tuple[str, int | None]] | None = None,
):
    warnings = [] if warnings is None else warnings

    def on_frame(frame: VideoFrame, generation: int | None = None) -> None:
        frames.append((frame, generation))

    def on_error(message: str, generation: int | None = None) -> None:
        errors.append((message, generation))

    def on_warning(message: str, generation: int | None = None) -> None:
        warnings.append((message, generation))

    window = SimpleNamespace(
        project=None,
        project_path=None,
        backend=None,
        controller=None,
        source_frame_rate=0.0,
        segment_timeline=None,
        selected_segment_id=None,
        selected_segment_ids=(),
        _playback_generation=0,
        _audio_analysis_generation=0,
        _audio_analysis_cancel_event=None,
        _audio_analysis_in_progress=False,
        audio_preview_enabled=True,
        _frame_lock=threading.Lock(),
        _latest_frame=None,
        _latest_frame_generation=None,
        _frame_delivery_scheduled=False,
        timeline_canvas=MagicMock(),
        audio_status_label=MagicMock(),
        preview=MagicMock(),
        play_button=MagicMock(),
        position_label=MagicMock(),
        _on_frame=on_frame,
        _on_backend_error=on_error,
        _on_backend_end=MagicMock(),
        _on_backend_warning=on_warning,
        _update_selected_clip_label=MagicMock(),
        _update_playback_controls=MagicMock(),
        _update_segment_controls=MagicMock(),
        _autosave_current_project=MagicMock(),
        _show_error=MagicMock(),
        _set_status=MagicMock(),
    )
    window._stop_backend = lambda: stop_backend(window)
    return window


def _attach_synchronized_or_fail(window, project: Project, project_path: Path) -> None:
    try:
        attach_project(window, project, project_path)
    except ProjectValidationError as error:
        raise AssertionError(
            "TICKET-120 synchronized preview is still disabled; "
            f"the legacy absolute-play guard fired: {error}",
        ) from error


def _wait_until(predicate, timeout: float = 4.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(0.01)
    raise AssertionError("Timed out waiting for the synchronized preview condition")


def _assert_video_only_commands(test_case, calls) -> list[list[str]]:
    commands: list[list[str]] = []
    for call in calls:
        command = call.args[0] if call.args else call.kwargs.get("args")
        if isinstance(command, (list, tuple)):
            commands.append(list(command))
    test_case.assertTrue(commands)
    test_case.assertFalse(any(Path(command[0]).name == "ffplay" for command in commands))
    test_case.assertFalse(any("-vn" in command or "s16le" in command for command in commands))
    return commands


def _assert_empty_preview_state(test_case, window) -> None:
    test_case.assertIsNone(window.backend)
    test_case.assertIsNone(window.controller)
    test_case.assertIsNone(window.selected_segment_id)
    test_case.assertEqual(window.selected_segment_ids, ())
    test_case.assertIsNone(window._latest_frame)
    test_case.assertIsNone(window._latest_frame_generation)
    test_case.assertFalse(window._frame_delivery_scheduled)


def _visible_marker_center(
    crop: CropPlan,
    marker_dimensions: tuple[int, int],
) -> tuple[float, float]:
    marker_width, marker_height = marker_dimensions
    source = crop.source
    scaled_marker_width = marker_width * crop.scaled_width / source.width
    scaled_marker_height = marker_height * crop.scaled_height / source.height
    marker_left = (crop.scaled_width - scaled_marker_width) / 2.0
    marker_right = (crop.scaled_width + scaled_marker_width) / 2.0
    marker_top = (crop.scaled_height - scaled_marker_height) / 2.0
    marker_bottom = (crop.scaled_height + scaled_marker_height) / 2.0
    visible_left = max(marker_left, crop.crop_x)
    visible_right = min(marker_right, crop.crop_x + crop.target.width)
    visible_top = max(marker_top, crop.crop_y)
    visible_bottom = min(marker_bottom, crop.crop_y + crop.target.height)
    if visible_left >= visible_right or visible_top >= visible_bottom:
        raise AssertionError("Marker is completely outside the planned crop")
    return (
        crop.target.x + (visible_left + visible_right) / 2.0 - crop.crop_x,
        crop.target.y + (visible_top + visible_bottom) / 2.0 - crop.crop_y,
    )


def _is_white_marker_pixel(red: int, green: int, blue: int) -> bool:
    return (
        min(red, green, blue) >= 180
        and max(red, green, blue)
        - min(
            red,
            green,
            blue,
        )
        <= 35
    )


def _white_centroid(
    frame: bytes,
    width: int,
    region: tuple[int, int, int, int],
) -> tuple[float, float]:
    x_start, y_start, x_end, y_end = region
    points: list[tuple[int, int]] = []
    for y in range(max(0, y_start), min(CANVAS_HEIGHT, y_end)):
        offset = (y * width + max(0, x_start)) * 4
        for x in range(max(0, x_start), min(CANVAS_WIDTH, x_end)):
            red, green, blue = frame[offset : offset + 3]
            if _is_white_marker_pixel(red, green, blue):
                points.append((x, y))
            offset += 4
    return _marker_centroid(points, region)


def _mean_luma(frame: bytes, width: int, height: int) -> float:
    channels = zip(frame[0::4], frame[1::4], frame[2::4], strict=False)
    return sum((red * 3 + green * 6 + blue) / 10.0 for red, green, blue in channels) / (
        width * height
    )


class ComposedPreviewBackendTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for tool in ("ffmpeg", "ffprobe"):
            if shutil.which(tool) is None:
                raise AssertionError(f"{tool} is required for TICKET-120 fixture preflight")
        cls.fixture_context = isolated_directory("ticket120-unit")
        cls.fixture_root = cls.fixture_context.__enter__()
        try:
            cls.fixture = build_four_track_fixture(cls.fixture_root)
        except BaseException:
            cls.fixture_context.__exit__(None, None, None)
            raise

    @classmethod
    def tearDownClass(cls):
        cls.fixture_context.__exit__(None, None, None)

    def setUp(self):
        self.frames: list[tuple[VideoFrame, int | None]] = []
        self.errors: list[tuple[str, int | None]] = []
        self.warnings: list[tuple[str, int | None]] = []
        self.window = make_editor_window(self.frames, self.errors, self.warnings)
        self.addCleanup(lambda: stop_backend(self.window))

    def test_fixture_preflight_is_real_and_preserves_audio_layout_and_sources(self):
        fixture = self.fixture
        self.assertEqual(len(fixture.sources), 4)
        self.assertEqual(
            tuple(interval.active_block_ids for interval in fixture.layout.intervals),
            EXPECTED_FIXTURE_INTERVALS,
        )
        for source in fixture.sources:
            probe = probe_media(source)
            self.assertTrue(probe.audio_stream_present, source.name)
            self.assertEqual(_sha256(source), fixture.source_hashes[source])

    def test_absolute_project_attaches_a_synchronized_backend_and_shared_clock(self):
        fixture = self.fixture
        _attach_synchronized_or_fail(self.window, fixture.project, fixture.project_path)
        self.assertIsNotNone(self.window.backend)
        self.assertIsNotNone(self.window.controller)
        self.assertEqual(self.window.segment_timeline, fixture.project.timeline)
        self.assertEqual(self.window.selected_segment_id, "red-main")

        assert self.window.controller is not None
        self.assertTrue(self.window.controller.seek(2.25))
        poll_playback(self.window)
        self.assertAlmostEqual(self.window.controller.snapshot().position_seconds, 2.25)
        self.assertAlmostEqual(fixture.project.playhead_seconds, 2.25)
        self.assertTrue(self.window.controller.seek(4.5))
        poll_playback(self.window)
        self.assertAlmostEqual(self.window.controller.snapshot().position_seconds, 4.5)
        self.assertAlmostEqual(fixture.project.playhead_seconds, 4.5)

    def test_frame_assembly_uses_active_slots_triplicate_and_black_gap(self):
        fixture = self.fixture
        _attach_synchronized_or_fail(self.window, fixture.project, fixture.project_path)
        assert self.window.controller is not None
        for position in (1.25, 2.25, 3.0, 3.75, 4.5):
            self.frames.clear()
            self.assertTrue(self.window.controller.seek(position))
            self.assertTrue(self.frames)
            frame, _generation = self.frames[-1]
            self.assertEqual((frame.width, frame.height), (CANVAS_WIDTH, CANVAS_HEIGHT))
            interval = fixture.layout.interval_at(round(position * 1_000_000))
            self.assertIsNotNone(interval)
            assert interval is not None
            if interval.is_black:
                self.assertLess(_mean_luma(frame.data, frame.width, frame.height), 8.0)
                continue
            for slot in interval.slots:
                crops = slot.triplicate_crops if slot.triplicate_crops else (slot.crop,)
                for crop in crops:
                    self.assertIsNotNone(crop)
                    assert crop is not None
                    actual = _white_centroid(
                        frame.data,
                        frame.width,
                        (
                            crop.target.x,
                            crop.target.y,
                            crop.target.x + crop.target.width,
                            crop.target.y + crop.target.height,
                        ),
                    )
                    expected_visible = _visible_marker_center(
                        crop,
                        fixture.marker_dimensions[slot.block.source_id],
                    )
                    self.assertAlmostEqual(actual[0], expected_visible[0], delta=24.0)
                    self.assertAlmostEqual(actual[1], expected_visible[1], delta=24.0)

    def test_preview_is_video_only_and_rapid_reload_drops_old_generation(self):
        fixture = self.fixture
        real_popen = subprocess.Popen
        with patch.object(subprocess, "Popen", wraps=real_popen) as popen:
            _attach_synchronized_or_fail(self.window, fixture.project, fixture.project_path)
            assert self.window.controller is not None
            self.window.backend.request_preview(2.25)
            self.window.backend.request_preview(4.5)
            _wait_until(
                lambda: self.frames and abs(self.frames[-1][0].position_seconds - 4.5) < 0.001,
            )
            self.window.controller.play()
            _wait_until(lambda: len(self.frames) >= 3)
            self.window.controller.pause()

        commands = _assert_video_only_commands(self, popen.call_args_list)
        self.assertFalse(
            any(
                "-map" in command and "0:a:0" in command[command.index("-map") + 1 :]
                for command in commands
            ),
        )

        old_generation = self.window._playback_generation
        self.frames.clear()
        refresh_playback_backend(self.window, force=True)
        new_generation = self.window._playback_generation
        self.assertGreater(new_generation, old_generation)
        _wait_until(lambda: bool(self.frames))
        self.assertTrue(
            all(generation == new_generation for _frame, generation in self.frames),
            "a stale decoder generation published a frame after reload",
        )

    def test_decoder_failure_reports_error_and_releases_preview_resources(self):
        fixture = self.fixture
        _attach_synchronized_or_fail(self.window, fixture.project, fixture.project_path)
        assert self.window.backend is not None
        self.window.backend.ffmpeg_path = "framestudio-t120-missing-ffmpeg"
        self.window.backend.request_preview(1.25)
        _wait_until(lambda: bool(self.errors))
        self.assertIn("ffmpeg", self.errors[-1][0].lower())
        self.assertIsNone(getattr(self.window.backend, "_preview_process", None))
        self.assertIsNone(getattr(self.window.backend, "_process", None))
        self.assertNotEqual(self.window.controller.snapshot().state, PlaybackState.PLAYING)

    def test_empty_timeline_detaches_preview_and_undo_restores_sources_and_playback(self):
        fixture = self.fixture
        project = load_project(fixture.project_path)
        _attach_synchronized_or_fail(self.window, project, fixture.project_path)
        source_paths = tuple(source.path for source in project.sources)
        segment_ids = tuple(segment.segment_id for segment in project.timeline.segment_items)
        receipt = remove_blocks(
            project,
            segment_ids,
            selection_ids=segment_ids,
            focused_segment_id=segment_ids[0],
        )
        self.window._latest_frame = object()
        self.window._latest_frame_generation = self.window._playback_generation
        self.window._frame_delivery_scheduled = True

        from framestudio.app_project import refresh_timeline

        refresh_timeline(self.window)

        self.assertEqual(tuple(source.path for source in self.window.project.sources), source_paths)
        _assert_empty_preview_state(self, self.window)
        self.window.preview.set_paintable.assert_called_with(None)
        self.window.play_button.set_sensitive.assert_called_with(False)
        self.window.play_button.set_label.assert_called_with("Play")

        undo_removed_blocks(project, receipt)
        refresh_timeline(self.window)

        self.assertIsNotNone(self.window.backend)
        self.assertIsNotNone(self.window.controller)
        self.assertEqual(self.window.selected_segment_id, segment_ids[0])
        self.assertEqual(tuple(source.path for source in project.sources), source_paths)

    def test_realtime_clock_tracks_wall_time_when_decode_is_slow(self):
        fixture = self.fixture
        delivered: list[tuple[float, float]] = []

        class DelayedBackend(FfmpegSynchronizedPlaybackBackend):
            def __init__(self, *args, **kwargs):
                self.decode_durations: list[float] = []
                super().__init__(*args, **kwargs)

            def _frame_for_interval(self, position_seconds, interval, **kwargs):
                started_at = time.monotonic()
                time.sleep(0.25)
                self.decode_durations.append(time.monotonic() - started_at)
                return VideoFrame(
                    self._black_frame,
                    self.width,
                    self.height,
                    position_seconds,
                    position_seconds,
                )

        backend = DelayedBackend(
            tuple((source.source_id, Path(source.path)) for source in fixture.project.sources),
            fixture.layout,
            CANVAS_WIDTH,
            CANVAS_HEIGHT,
            12.0,
            lambda frame: delivered.append((time.monotonic(), frame.position_seconds)),
            lambda message: self.errors.append((message, None)),
            lambda: None,
        )
        self.window.backend = backend
        self.addCleanup(backend.close)

        started_at = time.monotonic()
        backend.play()
        _wait_until(lambda: len(delivered) >= 4)
        observed_decode_latency = max(backend.decode_durations[-4:])
        callback_time, callback_position = delivered[-1]
        expected_position = max(
            0.0,
            callback_time - started_at - observed_decode_latency,
        )
        self.assertGreaterEqual(
            callback_position,
            expected_position - observed_decode_latency,
        )
        self.assertGreater(
            callback_position,
            2.0 / backend.frame_rate,
            "slow decoding must not advance the shared clock one frame at a time",
        )

    def test_realtime_pause_discards_an_inflight_decode_frame(self):
        fixture = self.fixture
        delivered: list[VideoFrame] = []
        decode_started = threading.Event()
        release_decode = threading.Event()
        decode_returned = threading.Event()

        class GatedBackend(FfmpegSynchronizedPlaybackBackend):
            def _frame_for_interval(self, position_seconds, interval, **kwargs):
                decode_started.set()
                release_decode.wait(timeout=2.0)
                try:
                    return VideoFrame(
                        self._black_frame,
                        self.width,
                        self.height,
                        position_seconds,
                        position_seconds,
                    )
                finally:
                    decode_returned.set()

        backend = GatedBackend(
            tuple((source.source_id, Path(source.path)) for source in fixture.project.sources),
            fixture.layout,
            CANVAS_WIDTH,
            CANVAS_HEIGHT,
            12.0,
            delivered.append,
            lambda message: self.errors.append((message, None)),
            lambda: None,
        )
        self.window.backend = backend
        self.addCleanup(release_decode.set)
        self.addCleanup(backend.close)

        backend.play()
        _wait_until(decode_started.is_set)
        backend.pause()
        release_decode.set()
        _wait_until(decode_returned.is_set)
        time.sleep(0.05)
        self.assertEqual(len(delivered), 0)


if __name__ == "__main__":
    unittest.main()
