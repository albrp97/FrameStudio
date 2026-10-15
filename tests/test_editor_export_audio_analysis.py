import threading
import unittest
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from framestudio.audio import (
    AudioAnalysisCancelled,
    AudioAnalysisError,
    AudioDecision,
    audio_analysis_worker_count,
    pending_audio_decision,
)
from framestudio.export import ExportPlanningError
from framestudio.model import Project
from framestudio.operations import ensure_project_audio_analysis
from tests.test_editor_audio import source_reference


class ExportAudioAnalysisTests(unittest.TestCase):
    def test_cache_errors_are_explicit_and_atomic_writes_preserve_old_records(self):
        from framestudio.audio_cache import load_audio_analysis, save_audio_analysis

        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = source_reference(root)
            ready = {
                **pending_audio_decision(source).to_dict(),
                "status": "ready",
                "gain_db": 0.0,
            }
            with patch.dict("os.environ", {"XDG_CACHE_HOME": str(root / "cache")}):
                save_audio_analysis(source, ready, ffmpeg_path="ffmpeg")
                cache_file = next((root / "cache").rglob("*.json"))
                original = cache_file.read_bytes()
                self.assertEqual(cache_file.stat().st_mode & 0o777, 0o600)
                with patch(
                    "framestudio.audio_cache.os.replace", side_effect=PermissionError("test")
                ):
                    with self.assertRaisesRegex(AudioAnalysisError, "Could not save"):
                        save_audio_analysis(source, ready, ffmpeg_path="ffmpeg")
                self.assertEqual(cache_file.read_bytes(), original)
                self.assertEqual(list(cache_file.parent.glob(".audio-*")), [])
                cache_file.write_text("{invalid")
                with self.assertRaisesRegex(AudioAnalysisError, "Could not read"):
                    load_audio_analysis(source, ffmpeg_path="ffmpeg")

    def test_disk_cache_is_invalidated_when_source_metadata_or_tool_changes(self):
        from framestudio.audio_cache import load_audio_analysis, save_audio_analysis

        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = source_reference(root)
            ready = replace(pending_audio_decision(source), status="ready", gain_db=0.0).to_dict()
            with patch.dict("os.environ", {"XDG_CACHE_HOME": str(root / "cache")}):
                save_audio_analysis(source, ready, ffmpeg_path="ffmpeg")
                self.assertEqual(load_audio_analysis(source, ffmpeg_path="ffmpeg"), ready)
                self.assertIsNone(load_audio_analysis(source, ffmpeg_path="/missing/ffmpeg"))
                changed = replace(source, metadata={**source.metadata, "audio_codec": "flac"})
                self.assertIsNone(load_audio_analysis(changed, ffmpeg_path="ffmpeg"))
                Path(source.path).write_bytes(b"changed media")
                with self.assertRaisesRegex(AudioAnalysisError, "Source changed"):
                    load_audio_analysis(source, ffmpeg_path="ffmpeg")

    def test_audio_cache_survives_cancel_and_a_fresh_project_instance(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = source_reference(root)
            project = Project.create_multi((source,))
            untouched = deepcopy(project)
            ready = replace(pending_audio_decision(source), status="ready", gain_db=0.0)

            def cancel_after_result(_sources, *, result_callback, **_options):
                result_callback(source, ready)
                raise AudioAnalysisCancelled("Audio analysis was cancelled")

            with patch.dict("os.environ", {"XDG_CACHE_HOME": str(root / "cache")}):
                with (
                    patch(
                        "framestudio.operations.analyze_sources_audio",
                        side_effect=cancel_after_result,
                    ),
                    self.assertRaisesRegex(ExportPlanningError, "Export cancelled"),
                ):
                    ensure_project_audio_analysis(project)
                with patch("framestudio.operations.analyze_sources_audio") as analyze:
                    restored = ensure_project_audio_analysis(untouched)
                analyze.assert_not_called()
                self.assertEqual(restored[source.source_id], ready.to_dict())
                self.assertTrue(list((root / "cache").rglob("*.json")))

    def test_sources_without_audio_do_not_start_decoder_or_process_pool(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            sources = tuple(
                source_reference(root, filename=f"silent-{index}.mp4", audio=False, codec=None)
                for index in range(3)
            )
            project = Project.create_multi(sources)
            with (
                patch("framestudio.audio.subprocess.Popen") as decode,
                patch("framestudio.audio.ProcessPoolExecutor") as pool,
            ):
                decisions = ensure_project_audio_analysis(project)
            self.assertEqual(
                {settings["status"] for settings in decisions.values()}, {"not-applicable"}
            )
            decode.assert_not_called()
            pool.assert_not_called()

    def test_analysis_reports_source_progress_during_export_preparation(self):
        with TemporaryDirectory() as temporary:
            source = source_reference(Path(temporary))
            project = Project.create_multi((source,))
            progress = []
            ensure_project_audio_analysis(
                project,
                ffmpeg_path="/missing/ffmpeg",
                progress_callback=progress.append,
            )
            self.assertEqual([item.frame for item in progress], [0, 1])
            self.assertEqual([item.percent for item in progress], [0.0, 100.0])
            self.assertTrue(all(item.stage == "Analyzing export audio" for item in progress))

    def test_worker_count_uses_available_cpu_affinity_without_oversubscribing(self):
        with patch("framestudio.audio.os.sched_getaffinity", return_value={0, 1, 2, 3}):
            self.assertEqual(audio_analysis_worker_count(218), 4)
            self.assertEqual(audio_analysis_worker_count(2), 2)

    def test_export_analysis_excludes_deleted_and_unused_sources(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            sources = tuple(
                source_reference(root, filename=f"source-{index}.mp4") for index in range(3)
            )
            project = Project.create_multi(sources)
            for block in project.timeline.blocks[1:]:
                project.timeline.set_deleted(block.segment_id, True)

            decisions = ensure_project_audio_analysis(project, ffmpeg_path="/missing/ffmpeg")

            self.assertEqual(set(decisions), {sources[0].source_id})
            for source in sources[1:]:
                self.assertEqual(
                    project.source_audio_settings(source.source_id)["status"], "pending"
                )

    def test_selected_output_sources_are_deduplicated_and_cached(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            sources = tuple(
                source_reference(root, filename=f"source-{index}.mp4") for index in range(3)
            )
            project = Project.create_multi(sources)
            selected_ids = (sources[1].source_id, sources[1].source_id)
            decisions = ensure_project_audio_analysis(
                project, source_ids=selected_ids, ffmpeg_path="/missing/ffmpeg"
            )
            self.assertEqual(set(decisions), {sources[1].source_id})
            with patch("framestudio.operations.analyze_sources_audio") as analyze:
                repeated = ensure_project_audio_analysis(project, source_ids=selected_ids)
            analyze.assert_not_called()
            self.assertEqual(repeated, decisions)
            self.assertEqual(
                project.source_audio_settings(sources[0].source_id)["status"], "pending"
            )

    def test_cancelled_export_does_not_start_analysis(self):
        with TemporaryDirectory() as temporary:
            source = source_reference(Path(temporary))
            project = Project.create_multi((source,))
            event = threading.Event()
            event.set()
            with (
                patch("framestudio.operations.analyze_sources_audio") as analyze,
                self.assertRaisesRegex(ExportPlanningError, "Export cancelled"),
            ):
                ensure_project_audio_analysis(project, cancel_event=event)
            analyze.assert_not_called()

    def test_partial_analysis_is_retained_when_export_is_cancelled(self):
        with TemporaryDirectory() as temporary:
            source = source_reference(Path(temporary))
            project = Project.create_multi((source,))
            pending = pending_audio_decision(source)
            ready = AudioDecision(
                status="ready",
                gain_db=0.0,
                policy_version=pending.policy_version,
                measurements=None,
                source_fingerprint=pending.source_fingerprint,
                audio_metadata=pending.audio_metadata,
            )

            def cancel_after_result(_sources, *, result_callback, **_options):
                result_callback(source, ready)
                raise AudioAnalysisCancelled("Audio analysis was cancelled")

            with (
                patch(
                    "framestudio.operations.analyze_sources_audio",
                    side_effect=cancel_after_result,
                ),
                self.assertRaisesRegex(ExportPlanningError, "Export cancelled"),
            ):
                ensure_project_audio_analysis(project)
            self.assertEqual(project.source_audio_settings(source.source_id)["status"], "ready")
