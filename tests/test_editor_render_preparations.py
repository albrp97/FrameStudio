import errno
import json
import threading
import unittest
from dataclasses import replace
from fractions import Fraction
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from framestudio.export_types import ExportExecutionError


class RenderPreparationTests(unittest.TestCase):
    def test_cache_publication_copy_is_cancellable_without_modifying_checkpoint(self):
        from framestudio import av_compositor as av
        from framestudio.export_process import check_export_cancelled

        with TemporaryDirectory() as directory:
            root = Path(directory)
            cached, staged = root / "cached.mp4", root / "staged.mp4"
            content = b"a" * (3 * 1024 * 1024)
            cached.write_bytes(content)
            event = threading.Event()
            checks = []

            def cancel_during_copy(cancel_event):
                checks.append(True)
                if len(checks) == 3:
                    event.set()
                check_export_cancelled(cancel_event)

            with (
                patch.object(av.os, "link", side_effect=OSError(errno.EXDEV, "cross-device")),
                patch.object(av, "check_export_cancelled", side_effect=cancel_during_copy),
                self.assertRaisesRegex(ExportExecutionError, "cancelled"),
            ):
                av._stage_cached_mux(cached, staged, event)
            self.assertEqual(cached.read_bytes(), content)
            self.assertLess(staged.stat().st_size, len(content))
            staged.unlink()
            with patch.object(av.os, "link", side_effect=OSError(errno.EXDEV, "cross-device")):
                av._stage_cached_mux(cached, staged, None)
            self.assertEqual(staged.read_bytes(), content)

    def test_malformed_metadata_is_rebuilt_and_checkpoint_io_does_not_trigger_fallback(self):
        from framestudio.render_preparations import PreparationCacheError, RenderPreparations

        with TemporaryDirectory() as directory:
            root = Path(directory)
            writes = []

            def produce(path):
                writes.append(path)
                path.write_bytes(b"verified")

            RenderPreparations(root).materialize("native", {}, produce, lambda path: None)
            manifest = next(root.rglob("manifest.json"))
            data = json.loads(manifest.read_text())
            data["stages"]["native"]["metadata"] = []
            manifest.write_text(json.dumps(data))
            RenderPreparations(root).materialize("native", {}, produce, lambda path: None)
            self.assertEqual(len(writes), 2)
            with (
                patch("framestudio.render_preparations.file_digest", side_effect=OSError("disk")),
                self.assertRaises(PreparationCacheError),
            ):
                RenderPreparations(root).materialize("fps", {}, produce, lambda path: None)
            self.assertFalse(list(root.rglob("*.partial-*")))

    def test_custom_model_content_changes_invalidate_identity(self):
        from framestudio.render_preparations import RenderPreparations

        with TemporaryDirectory() as directory:
            root = Path(directory)
            model = root / "model.pth"
            model.write_bytes(b"model-one")
            first = RenderPreparations(root / "cache").model_identity(model)
            model.write_bytes(b"model-two")
            second = RenderPreparations(root / "cache").model_identity(model)
            self.assertNotEqual(first["sha256"], second["sha256"])

    def test_native_identity_ignores_copy_track_and_final_framing_but_not_source_range(self):
        from framestudio.video_compositor import VideoPreparationIdentity

        first = VideoPreparationIdentity(
            block_id="one",
            source_id="source",
            source_hash="same bytes",
            source_range_ticks=(0, 500000),
            target_rate=Fraction(60),
            modification_identity=("zoom", 1),
        )
        copy = replace(
            first, block_id="other", source_id="reimport", modification_identity=("zoom", 2)
        )
        self.assertEqual(first.cache_key, copy.cache_key)
        self.assertNotEqual(
            first.cache_key, replace(copy, source_range_ticks=(500000, 1000000)).cache_key
        )

    def test_verified_stage_survives_reopening_and_incomplete_stage_is_not_reused(self):
        from framestudio.render_preparations import RenderPreparations

        with TemporaryDirectory() as directory:
            root = Path(directory)
            writes = []

            def produce(path):
                writes.append(path)
                path.write_bytes(b"verified media")

            request = {"source_hash": "first", "range": [0, 500000]}
            first = RenderPreparations(root)
            result = first.materialize("native", request, produce, lambda path: None)
            again = RenderPreparations(root)
            self.assertEqual(
                again.materialize("native", request, produce, lambda path: None), result
            )
            self.assertEqual(len(writes), 1)
            result.write_bytes(b"corrupt")
            again = RenderPreparations(root)
            again.materialize("native", request, produce, lambda path: None)
            self.assertEqual(len(writes), 2)

            def interrupted(path):
                path.write_bytes(b"incomplete")
                raise ExportExecutionError("Export cancelled")

            with self.assertRaises(ExportExecutionError):
                again.materialize("fps", request, interrupted, lambda path: None)
            RenderPreparations(root).materialize("fps", request, produce, lambda path: None)
            self.assertEqual(len(writes), 3)
            self.assertFalse(list(root.rglob("*.partial-*")))

    def test_policy_identity_invalidates_and_completed_checkpoint_precedes_cancel(self):
        from framestudio.render_preparations import RenderPreparations

        with TemporaryDirectory() as directory:
            root = Path(directory)
            event = threading.Event()
            writes = []

            def produce(path):
                writes.append(path)
                path.write_bytes(b"media")

            def cancel_after_checkpoint(progress):
                if progress.stage.startswith("Checkpointed"):
                    event.set()

            cache = RenderPreparations(
                root, cancel_event=event, progress_callback=cancel_after_checkpoint
            )
            cache.materialize("native", {"rate": 30}, produce, lambda path: None)
            with self.assertRaisesRegex(ExportExecutionError, "cancelled"):
                cache.materialize("fps", {"rate": 60}, produce, lambda path: None)
            cache = RenderPreparations(root)
            cache.materialize("native", {"rate": 30}, produce, lambda path: None)
            cache.materialize("native", {"rate": 60}, produce, lambda path: None)
            self.assertEqual(len(writes), 2)
