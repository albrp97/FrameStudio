import hashlib
import json
import os
import subprocess
import sys
import threading
import unittest
from dataclasses import replace
from fractions import Fraction
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from framestudio import av_compositor as av
from framestudio import video_compositor as video
from framestudio.export_session import session_root
from framestudio.fps_policy import FrameRatePolicy
from framestudio.media import probe_media
from framestudio.model import Project, TriplicateGroup, VisualTransform
from framestudio.persistence import save_project
from framestudio.render_preparations import RenderPreparations
from framestudio.upscale_policy import UpscalePolicy
from tests.test_editor_layout_plan_functionality import make_block
from tests.test_editor_source_outputs_functionality import _make_constant_source

_RUN_EXPORT = """
import json, os, sys, threading
from contextlib import redirect_stdout
from pathlib import Path
from framestudio import av_compositor as av, video_compositor as video
from framestudio.app_export import run_output_choice_job, ExportBatchExecutionError
from framestudio.fps_policy import FrameRatePolicy
from framestudio.upscale_policy import UpscalePolicy
from framestudio.persistence import load_project
project_path, destination, trace, mode, cancel_stage = sys.argv[1:]
for module, attribute, label in (
    (video, '_extract_block', 'extract'),
    (video, 'run_source_interpolation', 'interpolate'),
    (av, 'render_project_video', 'video'),
    (av, 'render_audio', 'audio'),
    (av, '_mux_stages', 'mux'),
    (av, '_verify_muxed_output', 'verify_mux'),
):
    original = getattr(module, attribute)
    def traced(*args, _fn=original, _label=label, **kwargs):
        with open(trace, 'a') as log: log.write(mode + ':' + _label + '\\n')
        if _label == 'interpolate':
            with open(trace, 'a') as log:
                log.write(mode + ':backend=' + kwargs['backend'] + '\\n')
        return _fn(*args, **kwargs)
    setattr(module, attribute, traced)
event = threading.Event()
checkpoint_count = 0
cancel_name, _, cancel_number = cancel_stage.partition('@')
def progress(update):
    global checkpoint_count
    if cancel_name and update.stage == 'Checkpointed ' + cancel_name:
        checkpoint_count += 1
        if checkpoint_count == int(cancel_number or '1'):
            event.set()
try:
    with redirect_stdout(sys.stderr):
        run_output_choice_job(
            load_project(Path(project_path)), Path(destination), output_mode='final-only',
            frame_rate_policy=FrameRatePolicy(
                choice='custom', custom_rate=60, target_rate=60,
                backend=os.environ.get('FRAMESTUDIO_TEST_BACKEND', 'ffmpeg-minterpolate'),
                enhancement_enabled=True,
            ),
            upscale_policy=UpscalePolicy(enhancement_enabled=False),
            progress_callback=progress, cancel_event=event, resume_mode=mode,
        )
except ExportBatchExecutionError:
    if not event.is_set(): raise
    print(json.dumps({'cancelled': True}))
else:
    print(json.dumps({'cancelled': False}))
"""


class RenderPreparationFunctionalityTests(unittest.TestCase):
    def test_clock_recipe_invalidates_video_and_mux_but_reuses_native_and_audio(self):
        from framestudio.operations import ensure_project_audio_analysis

        with TemporaryDirectory(prefix="framestudio-clock-recipe-") as temporary:
            root = Path(temporary)
            source = root / "source.mp4"
            _make_constant_source(
                source,
                color="red",
                frame_rate=30,
                width=320,
                height=180,
                frequencies=(440, 880),
                duration=0.5,
            )
            source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
            project = Project.create_synchronized_multi(((source, probe_media(source).metadata()),))
            ensure_project_audio_analysis(project)
            plan = av.plan_project_av(
                project,
                root / "old-recipe.mp4",
                frame_rate_policy=FrameRatePolicy(
                    choice="custom",
                    custom_rate=60,
                    target_rate=60,
                    backend="ffmpeg-minterpolate",
                    enhancement_enabled=True,
                ),
                upscale_policy=UpscalePolicy(enhancement_enabled=False),
            )
            materialize = RenderPreparations.materialize

            def legacy_recipe(preparations, stage, request, *args, **kwargs):
                if stage == "video composition":
                    request = {**request, "composition_version": 2}
                elif stage == "verified AV composition":
                    request = {
                        **request,
                        "video": {**request["video"], "composition_version": 2},
                    }
                return materialize(preparations, stage, request, *args, **kwargs)

            cache = root / "checkpoints"
            with patch.object(RenderPreparations, "materialize", new=legacy_recipe):
                av.render_project_av(plan, preparations=RenderPreparations(cache))

            with (
                patch.object(video, "_extract_block", wraps=video._extract_block) as extract,
                patch.object(
                    video, "run_source_interpolation", wraps=video.run_source_interpolation
                ) as interpolate,
                patch.object(av, "render_project_video", wraps=av.render_project_video) as compose,
                patch.object(av, "render_audio", wraps=av.render_audio) as audio,
                patch.object(av, "_mux_stages", wraps=av._mux_stages) as mux,
            ):
                result = av.render_project_av(
                    replace(plan, destination=root / "new-recipe.mp4"),
                    preparations=RenderPreparations(cache),
                )
            self.assertEqual(result.actual_frames, 30)
            self.assertEqual(
                (extract.call_count, interpolate.call_count, audio.call_count), (0, 0, 0)
            )
            self.assertEqual((compose.call_count, mux.call_count), (1, 1))
            decoded = [
                subprocess.run(
                    [
                        "ffmpeg",
                        "-v",
                        "error",
                        "-i",
                        str(path),
                        "-map",
                        "0:v",
                        "-f",
                        "framemd5",
                        "-",
                    ],
                    check=True,
                    capture_output=True,
                ).stdout
                for path in (plan.destination, result.destination)
            ]
            self.assertEqual(decoded[0], decoded[1])
            self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), source_hash)

    def test_resume_reuses_completed_fallback_instead_of_retrying_failed_rve(self):
        from framestudio.export_types import ExportExecutionError

        with TemporaryDirectory(prefix="framestudio-fallback-resume-") as temporary:
            root = Path(temporary)
            source = root / "source.mp4"
            _make_constant_source(
                source,
                color="red",
                frame_rate=30,
                width=320,
                height=180,
                frequencies=(440, 880),
                duration=0.5,
            )
            project = Project.create_synchronized_multi(((source, probe_media(source).metadata()),))
            from framestudio.operations import ensure_project_audio_analysis

            ensure_project_audio_analysis(project)
            plan = av.plan_project_av(
                project,
                root / "output.mp4",
                frame_rate_policy=FrameRatePolicy(
                    choice="custom",
                    custom_rate=60,
                    target_rate=60,
                    backend="ffmpeg-minterpolate",
                    enhancement_enabled=True,
                ),
                upscale_policy=UpscalePolicy(enhancement_enabled=False),
            )
            route = replace(plan.video_plan.processing_routes[0], fps_backend="rve-4.26")
            plan = replace(plan, video_plan=replace(plan.video_plan, processing_routes=(route,)))
            original = video.run_source_interpolation
            calls = []

            def interpolate(*args, **kwargs):
                calls.append(kwargs["backend"])
                if kwargs["backend"] == "rve-4.26":
                    raise ExportExecutionError("injected backend failure")
                return original(*args, **kwargs)

            event = threading.Event()

            def progress(update):
                if update.stage == "Checkpointed interpolated segment":
                    event.set()

            with patch.object(video, "run_source_interpolation", side_effect=interpolate):
                with self.assertRaisesRegex(av.AVCompositorExecutionError, "cancelled"):
                    av.render_project_av(
                        plan,
                        cancel_event=event,
                        progress_callback=progress,
                        preparations=RenderPreparations(root / "cache", cancel_event=event),
                    )
                event.clear()
                result = av.render_project_av(plan, preparations=RenderPreparations(root / "cache"))
            self.assertEqual(calls, ["rve-4.26", "ffmpeg-minterpolate"])
            self.assertTrue(any("reusing verified" in note for note in result.processing_fallbacks))
            self.assertEqual(result.actual_frames, 30)

    def test_twenty_of_forty_interpolations_survive_process_restart(self):
        with TemporaryDirectory(prefix="framestudio-forty-resume-") as temporary:
            root = Path(temporary)
            source = root / "source.mp4"
            _make_constant_source(
                source,
                color="red",
                frame_rate=30,
                width=320,
                height=180,
                frequencies=(440, 880),
                duration=20.0,
            )
            original = hashlib.sha256(source.read_bytes()).hexdigest()
            project = Project.create_synchronized_multi(((source, probe_media(source).metadata()),))
            project.timeline.replace_track_blocks(
                "track-1",
                tuple(
                    make_block(
                        segment_id=f"segment-{index}",
                        track_id="track-1",
                        source_id=project.source.source_id,
                        source_start=index * 0.5,
                        source_end=(index + 1) * 0.5,
                        timeline_start=index * 0.5,
                        timeline_end=(index + 1) * 0.5,
                    )
                    for index in range(40)
                ),
            )
            project_path = root / "edit.framestudio.json"
            save_project(project, project_path)
            destination, trace = root / "output.mp4", root / "calls.txt"
            from framestudio.export_journal import journal_path

            for mode, stop in (("fresh", "interpolated segment@20"), ("resume", "")):
                result = subprocess.run(
                    [
                        sys.executable,
                        "-c",
                        _RUN_EXPORT,
                        str(project_path),
                        str(destination),
                        str(trace),
                        mode,
                        stop,
                    ],
                    env={**os.environ, "XDG_CACHE_HOME": str(root / "cache")},
                    capture_output=True,
                    text=True,
                    timeout=240,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(json.loads(result.stdout)["cancelled"], mode == "fresh")
                self.assertEqual(journal_path(destination).exists(), mode == "fresh")
                calls = trace.read_text().splitlines()
                self.assertEqual(calls.count(mode + ":interpolate"), 20, calls)
                if mode == "fresh":
                    manifests = list(
                        (session_root(destination) / "render-preparations").glob("*/manifest.json")
                    )
                    completed = [
                        json.loads(path.read_text())["stages"].get("interpolated segment", {})
                        for path in manifests
                    ]
                    self.assertEqual(sum(s.get("status") == "complete" for s in completed), 20)
            self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), original)
            self.assertAlmostEqual(probe_media(destination).duration_seconds, 20, delta=0.1)
            frames = subprocess.run(
                [
                    "ffprobe",
                    "-v",
                    "error",
                    "-count_frames",
                    "-select_streams",
                    "v:0",
                    "-show_entries",
                    "stream=nb_read_frames",
                    "-of",
                    "csv=p=0",
                    str(destination),
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            self.assertEqual(int(frames.stdout.strip()), 1200)

    def test_shared_native_frames_preserve_different_framing_and_triplicate_pixels(self):
        with TemporaryDirectory(prefix="framestudio-framing-reuse-") as temporary:
            root = Path(temporary)
            source = root / "source.mp4"
            subprocess.run(
                [
                    "ffmpeg",
                    "-v",
                    "error",
                    "-f",
                    "lavfi",
                    "-i",
                    "testsrc2=size=320x180:rate=30:duration=0.5",
                    "-c:v",
                    "libx264",
                    "-preset",
                    "ultrafast",
                    "-pix_fmt",
                    "yuv420p",
                    str(source),
                ],
                check=True,
                capture_output=True,
            )
            original = hashlib.sha256(source.read_bytes()).hexdigest()
            project = Project.create_synchronized_multi(((source, probe_media(source).metadata()),))
            for index in range(3):
                track_id = f"track-{index + 1}"
                if index:
                    project.timeline.add_track(track_id)
                transform = VisualTransform(
                    zoom=1.0 + index * 0.25,
                    offset_x=index * 15.0,
                )
                project.timeline.replace_track_blocks(
                    track_id,
                    (
                        make_block(
                            segment_id=f"copy-{index}",
                            track_id=track_id,
                            source_id=project.source.source_id,
                            source_start=0.0,
                            source_end=0.5,
                            timeline_start=0.0,
                            timeline_end=0.5,
                            visual_transform=transform,
                            triplicate=(TriplicateGroup.create(transform) if index == 2 else None),
                        ),
                    ),
                )
            hashes = []
            for strategy in ("separate", "shared"):
                plan = av.plan_project_av(
                    project,
                    root / f"{strategy}.mp4",
                    frame_rate_policy=FrameRatePolicy(
                        choice="custom",
                        custom_rate=Fraction(60),
                        target_rate=Fraction(60),
                        backend="ffmpeg-minterpolate",
                        enhancement_enabled=True,
                    ),
                    upscale_policy=UpscalePolicy(enhancement_enabled=False),
                )
                with patch.object(video, "_extract_block", wraps=video._extract_block) as extract:
                    if strategy == "separate":
                        with patch.object(
                            video.VideoPreparationIdentity,
                            "cache_key",
                            property(lambda identity: identity.block_id),
                        ):
                            av.render_project_av(plan)
                    else:
                        av.render_project_av(
                            plan,
                            preparations=RenderPreparations(root / "checkpoints"),
                        )
                    self.assertEqual(extract.call_count, 3 if strategy == "separate" else 1)
                decoded = subprocess.run(
                    [
                        "ffmpeg",
                        "-v",
                        "error",
                        "-i",
                        str(plan.destination),
                        "-map",
                        "0:v",
                        "-f",
                        "framemd5",
                        "-",
                    ],
                    check=True,
                    capture_output=True,
                ).stdout
                hashes.append(hashlib.sha256(decoded).hexdigest())
            self.assertEqual(hashes[0], hashes[1])
            self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), original)

    def test_copied_ranges_and_completed_steps_survive_cancel_and_process_restart(self):
        with TemporaryDirectory(prefix="framestudio-preparation-resume-") as temporary:
            root = Path(temporary)
            source = root / "source.mp4"
            _make_constant_source(
                source,
                color="red",
                frame_rate=30,
                width=320,
                height=180,
                frequencies=(440, 880),
                duration=1.0,
            )
            source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
            project = Project.create_synchronized_multi(((source, probe_media(source).metadata()),))
            for track in ("track-2", "track-3"):
                project.timeline.add_track(track)
            for track in tuple(project.timeline.tracks or ()):
                project.timeline.replace_track_blocks(
                    track.track_id,
                    tuple(
                        make_block(
                            segment_id=f"{track.track_id}-{index}",
                            track_id=track.track_id,
                            source_id=project.source.source_id,
                            source_start=index * 0.5,
                            source_end=(index + 1) * 0.5,
                            timeline_start=index * 0.5,
                            timeline_end=(index + 1) * 0.5,
                        )
                        for index in range(2)
                    ),
                )
            project_path = root / "edit.framestudio.json"
            save_project(project, project_path)
            for index, stage in enumerate(
                (
                    "interpolated segment",
                    "video composition",
                    "audio composition",
                    "verified AV composition",
                )
            ):
                with self.subTest(stage=stage):
                    case = root / f"case-{index}"
                    case.mkdir()
                    destination, trace = case / "output.mp4", case / "calls.txt"
                    environment = {**os.environ, "XDG_CACHE_HOME": str(root / "cache")}
                    for mode, cancelled in (("fresh", True), ("resume", False)):
                        result = subprocess.run(
                            [
                                sys.executable,
                                "-c",
                                _RUN_EXPORT,
                                str(project_path),
                                str(destination),
                                str(trace),
                                mode,
                                stage if cancelled else "",
                            ],
                            env=environment,
                            capture_output=True,
                            text=True,
                            timeout=60,
                        )
                        self.assertEqual(result.returncode, 0, result.stderr)
                        self.assertEqual(json.loads(result.stdout)["cancelled"], cancelled)
                        self.assertEqual(destination.exists(), not cancelled)
                    calls = trace.read_text().splitlines()
                    backend = os.environ.get("FRAMESTUDIO_TEST_BACKEND", "ffmpeg-minterpolate")
                    self.assertEqual(
                        sum(line.endswith(":backend=" + backend) for line in calls), 2, calls
                    )
                    for label, count in (
                        ("extract", 2),
                        ("interpolate", 2),
                        ("audio", 1),
                        ("mux", 1),
                        ("verify_mux", 2),
                    ):
                        self.assertEqual(
                            sum(line.endswith(":" + label) for line in calls), count, calls
                        )
                    if stage != "interpolated segment":
                        self.assertNotIn("resume:video", calls)
                    if stage in {"audio composition", "verified AV composition"}:
                        self.assertNotIn("resume:audio", calls)
                    if stage == "verified AV composition":
                        self.assertNotIn("resume:mux", calls)
                        self.assertEqual(calls.count("resume:verify_mux"), 1)
                    media = probe_media(destination)
                    self.assertEqual(
                        (media.width, media.height, media.frame_rate), (1920, 1080, "60/1")
                    )
                    self.assertTrue(media.has_audio_stream)
                    self.assertAlmostEqual(media.duration_seconds, 1.0, delta=0.1)
                    self.assertFalse(session_root(destination).exists())
            self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), source_hash)
