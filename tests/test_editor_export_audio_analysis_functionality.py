import json
import shutil
import subprocess
import sys
import threading
import time
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from framestudio.app import create_editor_application
from framestudio.audio import (
    AudioAnalysisCancelled,
    analyze_sources_audio,
    audio_analysis_worker_count,
)
from framestudio.media import probe_media
from framestudio.model import Project, SourceReference
from framestudio.persistence import load_autosave, save_project


class ExportAudioAnalysisFunctionalityTests(unittest.TestCase):
    def test_repeated_three_track_render_reports_progress_and_cancels_preparation(self):
        from framestudio.app_export import ExportBatchExecutionError, run_output_choice_job
        from framestudio.fps_policy import FrameRatePolicy
        from framestudio.upscale_policy import UpscalePolicy
        from tests.test_editor_layout_plan_functionality import make_block
        from tests.test_editor_source_outputs_functionality import _make_constant_source

        with TemporaryDirectory(prefix="framestudio-three-track-") as temporary:
            root = Path(temporary)
            source_path = root / "source.mp4"
            _make_constant_source(
                source_path,
                color="red",
                frame_rate=24,
                width=320,
                height=180,
                frequencies=(440, 880),
                duration=0.5,
            )
            original = source_path.read_bytes()
            project = Project.create_synchronized_multi(
                ((source_path, probe_media(source_path).metadata()),)
            )
            for track in ("track-2", "track-3"):
                project.timeline.add_track(track)
            for index, track in enumerate(project.timeline.tracks):
                project.timeline.replace_track_blocks(
                    track.track_id,
                    (
                        make_block(
                            segment_id=f"copy-{index}",
                            source_id=project.source.source_id,
                            track_id=track.track_id,
                            source_start=0.0,
                            source_end=0.5,
                            timeline_start=0.0,
                            timeline_end=0.5,
                        ),
                    ),
                )
            project.validate()
            options = {
                "output_mode": "final-only",
                "frame_rate_policy": FrameRatePolicy(
                    choice="custom",
                    target_rate=24,
                    custom_rate=24,
                    enhancement_enabled=False,
                ),
                "upscale_policy": UpscalePolicy(enhancement_enabled=False),
            }
            stages = []
            destination = root / "combined.mp4"
            with patch.dict("os.environ", {"XDG_CACHE_HOME": str(root / "cache")}):
                run_output_choice_job(
                    project,
                    destination,
                    **options,
                    progress_callback=lambda progress: stages.append(progress.stage),
                    cancel_event=threading.Event(),
                )
                media = probe_media(destination)
                self.assertEqual((media.width, media.height), (1920, 1080))
                self.assertTrue(media.has_audio_stream)
                self.assertAlmostEqual(media.duration_seconds, 0.5, delta=0.1)
                self.assertIn("Planning export outputs", stages)
                self.assertIn("Inspecting export sources", stages)
                self.assertIn("video composition", stages)
                event = threading.Event()

                def cancel_preparation(progress):
                    if progress.stage == "Preparing video segments":
                        event.set()

                cancelled_destination = root / "cancelled.mp4"
                with self.assertRaises(ExportBatchExecutionError):
                    run_output_choice_job(
                        project,
                        cancelled_destination,
                        **options,
                        progress_callback=cancel_preparation,
                        cancel_event=event,
                    )
            self.assertTrue(event.is_set())
            self.assertFalse(cancelled_destination.exists())
            self.assertEqual(source_path.read_bytes(), original)

    def test_completed_audio_is_reused_by_a_fresh_export_process(self):
        with TemporaryDirectory(prefix="framestudio-durable-audio-") as temporary:
            root = Path(temporary)
            tone = root / "tone.wav"
            subprocess.run(
                [
                    "ffmpeg",
                    "-hide_banner",
                    "-loglevel",
                    "error",
                    "-f",
                    "lavfi",
                    "-i",
                    "sine=frequency=440:sample_rate=48000:duration=0.5",
                    str(tone),
                ],
                check=True,
                capture_output=True,
            )
            source = self._audio_sources(root, tone, 1)[0]
            project = Project.create_multi((source,))
            project_path = root / "pending.framestudio.json"
            save_project(project, project_path)
            trace = root / "analysis-starts.txt"
            wrapper = root / "ffmpeg-traced"
            wrapper.write_text(
                f"#!{sys.executable}\n"
                "import os, sys\n"
                f"with open({str(trace)!r}, 'a') as log: log.write('scan\\n')\n"
                f"os.execv({shutil.which('ffmpeg')!r}, ['ffmpeg', *sys.argv[1:]])\n",
                encoding="utf-8",
            )
            wrapper.chmod(0o755)
            script = (
                "import json, sys\n"
                "from framestudio.persistence import load_project\n"
                "from framestudio.operations import ensure_project_audio_analysis\n"
                "project = load_project(sys.argv[1])\n"
                "print(json.dumps(ensure_project_audio_analysis(project, ffmpeg_path=sys.argv[2])))\n"
            )
            with patch.dict("os.environ", {"XDG_CACHE_HOME": str(root / "cache")}):
                results = [
                    subprocess.run(
                        [sys.executable, "-c", script, str(project_path), str(wrapper)],
                        check=True,
                        capture_output=True,
                        text=True,
                    )
                    for _ in range(2)
                ]
            self.assertEqual(json.loads(results[0].stdout), json.loads(results[1].stdout))
            self.assertEqual(trace.read_text().splitlines(), ["scan"])
            self.assertEqual(json.loads(results[1].stdout)[source.source_id]["status"], "ready")

    def test_cancelling_native_segment_extraction_terminates_the_owned_child(self):
        from framestudio.export_types import ExportExecutionError
        from framestudio.video_compositor import _extract_block

        with TemporaryDirectory(prefix="framestudio-cancel-extraction-") as temporary:
            root = Path(temporary)
            trace = root / "pid.txt"
            wrapper = root / "ffmpeg-blocking"
            wrapper.write_text(
                f"#!{sys.executable}\nimport os, time\n"
                f"with open({str(trace)!r}, 'w') as log: log.write(str(os.getpid()))\n"
                "time.sleep(60)\n",
                encoding="utf-8",
            )
            wrapper.chmod(0o755)
            event = threading.Event()
            failures = []

            def extract():
                try:
                    _extract_block(
                        root / "source.mp4",
                        root / "partial.mp4",
                        0.0,
                        1.0,
                        30,
                        str(wrapper),
                        cancel_event=event,
                    )
                except ExportExecutionError as error:
                    failures.append(error)

            worker = threading.Thread(target=extract)
            worker.start()
            try:
                deadline = time.monotonic() + 5
                while (not trace.exists() or not trace.read_text()) and time.monotonic() < deadline:
                    time.sleep(0.01)
                self.assertTrue(trace.exists(), "native extraction subprocess did not start")
                pid = int(trace.read_text())
            finally:
                started = time.monotonic()
                event.set()
                worker.join(timeout=5)
            self.assertFalse(worker.is_alive())
            self.assertLess(time.monotonic() - started, 3)
            self.assertEqual(len(failures), 1)
            self.assertIn("cancelled", str(failures[0]).casefold())
            self.assertFalse(Path(f"/proc/{pid}").exists())
            self.assertFalse((root / "partial.mp4").exists())

    @unittest.skipUnless(audio_analysis_worker_count(2) > 1, "Two CPU cores are required")
    def test_parallel_scans_match_serial_measurements_and_use_distinct_workers(self):
        with TemporaryDirectory(prefix="framestudio-parallel-audio-") as temporary:
            root = Path(temporary)
            tone = root / "tone.wav"
            subprocess.run(
                [
                    "ffmpeg",
                    "-hide_banner",
                    "-loglevel",
                    "error",
                    "-f",
                    "lavfi",
                    "-i",
                    "sine=frequency=440:sample_rate=48000:duration=30",
                    str(tone),
                ],
                check=True,
                capture_output=True,
            )
            sources = self._audio_sources(root, tone, 4)
            serial_start = time.monotonic()
            serial = analyze_sources_audio(sources, max_workers=1)
            serial_seconds = time.monotonic() - serial_start
            trace = root / "workers.jsonl"
            wrapper = root / "ffmpeg-traced"
            wrapper.write_text(
                f"#!{sys.executable}\n"
                "import json, os, sys, time\n"
                f"with open({str(trace)!r}, 'a') as log:\n"
                "    log.write(json.dumps({'worker': os.getppid(), 'started': time.monotonic()}) + '\\n')\n"
                f"os.execv({shutil.which('ffmpeg')!r}, ['ffmpeg', *sys.argv[1:]])\n",
                encoding="utf-8",
            )
            wrapper.chmod(0o755)
            parallel_start = time.monotonic()
            parallel = analyze_sources_audio(sources, ffmpeg_path=str(wrapper), max_workers=4)
            parallel_seconds = time.monotonic() - parallel_start
            self.assertEqual(parallel, serial)
            entries = [json.loads(line) for line in trace.read_text().splitlines()]
            worker_count = len({entry["worker"] for entry in entries})
            self.assertGreater(worker_count, 1)
            print(
                f"Audio benchmark: four 30s sources, serial={serial_seconds:.3f}s, "
                f"parallel={parallel_seconds:.3f}s, workers={worker_count}"
            )

    @unittest.skipUnless(audio_analysis_worker_count(2) > 1, "Two CPU cores are required")
    def test_cancelling_parallel_scans_stops_all_owned_ffmpeg_processes(self):
        with TemporaryDirectory(prefix="framestudio-cancel-audio-") as temporary:
            root = Path(temporary)
            fixture = root / "fixture.wav"
            fixture.write_bytes(b"cancel fixture")
            sources = self._audio_sources(root, fixture, 2)
            trace = root / "processes.txt"
            wrapper = root / "ffmpeg-blocking"
            wrapper.write_text(
                f"#!{sys.executable}\n"
                "import os, sys, time\n"
                f"with open({str(trace)!r}, 'a') as log:\n"
                "    log.write(str(os.getpid()) + '\\n')\n"
                "while True:\n"
                "    sys.stdout.buffer.write(b'\\0' * 4096)\n"
                "    sys.stdout.buffer.flush()\n"
                "    time.sleep(0.01)\n",
                encoding="utf-8",
            )
            wrapper.chmod(0o755)
            event = threading.Event()
            failures = []

            def analyze():
                try:
                    analyze_sources_audio(
                        sources,
                        ffmpeg_path=str(wrapper),
                        max_workers=2,
                        cancel_event=event,
                    )
                except AudioAnalysisCancelled as error:
                    failures.append(error)

            worker = threading.Thread(target=analyze)
            worker.start()
            try:
                deadline = time.monotonic() + 15
                pids = []
                while time.monotonic() < deadline:
                    if trace.exists():
                        pids = [int(line) for line in trace.read_text().splitlines()]
                        if len(pids) == 2:
                            break
                    time.sleep(0.01)
                self.assertEqual(len(pids), 2)
            finally:
                event.set()
                worker.join(timeout=5)
            self.assertFalse(worker.is_alive())
            self.assertEqual(len(failures), 1)
            for pid in pids:
                self.assertFalse(Path(f"/proc/{pid}").exists())

    @staticmethod
    def _audio_sources(root, fixture, count):
        sources = []
        for index in range(count):
            path = root / f"audio-{index}.mp4"
            shutil.copyfile(fixture, path)
            sources.append(
                SourceReference.from_path(
                    path,
                    {
                        "duration_seconds": 30.0,
                        "width": 64,
                        "height": 64,
                        "frame_rate": "10/1",
                        "audio_stream_present": True,
                        "audio_codec": "pcm_s16le",
                        "audio_sample_rate": 48000,
                        "audio_channels": 1,
                        "audio_channel_layout": "mono",
                    },
                )
            )
        return sources

    def test_gtk_scans_only_exported_sources_after_start_export(self):
        import gi

        gi.require_version("Gtk", "4.0")
        from gi.repository import Gio, GLib, Gtk

        self.assertTrue(Gtk.init_check(), "GTK display is required")
        with TemporaryDirectory(prefix="framestudio-export-audio-") as temporary:
            root = Path(temporary)
            with patch.dict("os.environ", {"XDG_STATE_HOME": str(root / "state")}):
                fixture = root / "first.mp4"
                subprocess.run(
                    [
                        "ffmpeg",
                        "-hide_banner",
                        "-loglevel",
                        "error",
                        "-f",
                        "lavfi",
                        "-i",
                        "color=c=blue:s=64x64:r=10:d=0.5",
                        "-f",
                        "lavfi",
                        "-i",
                        "sine=frequency=440:sample_rate=48000:duration=0.5",
                        "-c:v",
                        "libx264",
                        "-pix_fmt",
                        "yuv420p",
                        "-c:a",
                        "aac",
                        "-shortest",
                        str(fixture),
                    ],
                    check=True,
                    capture_output=True,
                )
                paths = (fixture, root / "second.mp4", root / "unused.mp4")
                for path in paths[1:]:
                    shutil.copyfile(fixture, path)
                source_bytes = fixture.read_bytes()
                application, factory = create_editor_application()
                application.set_application_id(
                    f"io.github.framestudio.editor.test_{root.name.replace('-', '_')}"
                )
                application.set_flags(application.get_flags() | Gio.ApplicationFlags.NON_UNIQUE)
                self.assertTrue(application.register(None))
                window = factory(application)
                try:
                    window._load_source(paths[:2])
                    self._wait(GLib, lambda: not window._source_load_in_progress)
                    self.assertFalse(window._audio_analysis_in_progress)
                    window._load_source(paths[2:])
                    self._wait(GLib, lambda: not window._source_load_in_progress)
                    self.assertFalse(window._audio_analysis_in_progress)
                    unused = window.project.sources[-1]
                    window.project.timeline.set_deleted(
                        window.project.timeline.blocks[-1].segment_id, True
                    )
                    window._refresh_timeline()
                    project_path = root / "edit.framestudio.json"
                    window._save_to(project_path)
                    window._load_project_path(project_path)
                    self.assertFalse(window._audio_analysis_in_progress)
                    for source in window.project.sources:
                        self.assertEqual(
                            window.project.source_audio_settings(source.source_id)["status"],
                            "pending",
                        )
                    window.export_button.emit("clicked")
                    panel = window.export_planning_window
                    widgets = tuple(self._widgets(panel))
                    for widget in widgets:
                        if isinstance(widget, Gtk.CheckButton):
                            label = widget.get_label() or ""
                            if "Enhance sources" in label or "Upscale" in label:
                                widget.set_active(False)
                        if isinstance(widget, Gtk.Entry) and widget.get_text().endswith(".mp4"):
                            widget.set_text("export.mp4")
                    start = next(
                        widget
                        for widget in widgets
                        if isinstance(widget, Gtk.Button) and widget.get_label() == "Start export"
                    )
                    self._wait(GLib, start.get_sensitive)
                    self.assertFalse(window._audio_analysis_in_progress)
                    for source in window.project.sources:
                        self.assertEqual(
                            window.project.source_audio_settings(source.source_id)["status"],
                            "pending",
                        )
                    start.emit("clicked")
                    self._wait(GLib, lambda: not window._export_in_progress, timeout=90)
                    self.assertNotIn("Error:", window.status_label.get_text())
                    output = probe_media(root / "export.mp4")
                    self.assertTrue(output.has_audio_stream)
                    self.assertAlmostEqual(output.duration_seconds, 1.0, delta=0.15)
                    persisted = load_autosave()
                    for source in persisted.sources:
                        expected = "pending" if source.source_id == unused.source_id else "ready"
                        self.assertEqual(
                            persisted.source_audio_settings(source.source_id)["status"], expected
                        )
                    for path in paths:
                        self.assertEqual(path.read_bytes(), source_bytes)
                finally:
                    window.close()
                    application.quit()

    @staticmethod
    def _widgets(widget):
        yield widget
        child = widget.get_first_child()
        while child is not None:
            yield from ExportAudioAnalysisFunctionalityTests._widgets(child)
            child = child.get_next_sibling()

    def _wait(self, glib, predicate, timeout=30):
        deadline = time.monotonic() + timeout
        context = glib.MainContext.default()
        while time.monotonic() < deadline:
            if context.pending():
                context.iteration(False)
            if predicate():
                return
            time.sleep(0.01)
        self.fail("GTK operation did not complete within the bounded wait")
