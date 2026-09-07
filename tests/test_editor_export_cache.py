import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from framestudio.export_cache import ExportCache, ExportCacheError, build_export_cache_request


class EditorExportCacheTests(unittest.TestCase):
    def _build_request(self, plan, source, runtime_paths):
        return build_export_cache_request(
            plan=plan,
            source_paths=(source,),
            source_stats=(source.stat(),),
            options={"backend": "rve-4.26"},
            runtime_paths=runtime_paths,
            ffmpeg_path="ffmpeg",
            ffprobe_path="ffprobe",
        )

    def test_matching_request_reuses_recorded_artifact(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            destination = root / "output.mp4"
            source = root / "source.mp4"
            source.write_bytes(b"source")
            request = {"source": str(source), "policy": "test"}
            cache = ExportCache.open(destination, request)
            artifact = cache.root / "interpolated.mp4"
            artifact.write_bytes(b"interpolated")
            cache.record("interpolation", artifact, metadata={"frames": 10})

            reopened = ExportCache.open(destination, request)
            self.assertEqual(
                reopened.reuse("interpolation", lambda path: path.read_bytes()),
                b"interpolated",
            )

    def test_modified_artifact_is_invalidated_before_rebuilding(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            destination = root / "output.mp4"
            request = {"source": "source", "policy": "test"}
            cache = ExportCache.open(destination, request)
            artifact = cache.root / "interpolated.mp4"
            artifact.write_bytes(b"interpolated")
            cache.record("interpolation", artifact)
            os.utime(artifact, ns=(artifact.stat().st_atime_ns, artifact.stat().st_mtime_ns + 1))

            reopened = ExportCache.open(destination, request)
            self.assertIsNone(reopened.reuse("interpolation", lambda path: path))
            self.assertFalse(artifact.exists())

    def test_changed_request_discards_previous_intermediates(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            destination = root / "output.mp4"
            cache = ExportCache.open(destination, {"policy": "old"})
            artifact = cache.root / "interpolated.mp4"
            artifact.write_bytes(b"old")
            cache.record("interpolation", artifact)

            reopened = ExportCache.open(destination, {"policy": "new"})
            self.assertFalse(artifact.exists())
            self.assertIsNone(reopened.reuse("interpolation", lambda path: path))

    def test_symlinked_cache_root_is_rejected_without_clearing_target(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            destination = root / "output.mp4"
            unrelated = root / "unrelated"
            unrelated.mkdir()
            sentinel = unrelated / "sentinel.txt"
            sentinel.write_text("keep", encoding="utf-8")
            cache_root = root / ".output.mp4.framestudio-intermediates"
            cache_root.symlink_to(unrelated, target_is_directory=True)

            with self.assertRaises(ExportCacheError):
                ExportCache.open(destination, {"policy": "new"})

            self.assertTrue(sentinel.is_file())
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "keep")

    def test_runtime_file_change_discards_previous_intermediates(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            destination = root / "output.mp4"
            source = root / "source.mp4"
            model = root / "model.pkl"
            source.write_bytes(b"source")
            model.write_bytes(b"model")
            plan = type("Plan", (), {"to_dict": lambda self: {"route": "enhanced"}})()
            runtime_paths = {"rve_model": model}
            first_request = self._build_request(plan, source, runtime_paths)
            cache = ExportCache.open(destination, first_request)
            artifact = cache.root / "interpolated.mp4"
            artifact.write_bytes(b"interpolated")
            cache.record("interpolation", artifact)

            os.utime(model, ns=(model.stat().st_atime_ns, model.stat().st_mtime_ns + 1))
            second_request = self._build_request(plan, source, runtime_paths)

            reopened = ExportCache.open(destination, second_request)

            self.assertFalse(artifact.exists())
            self.assertIsNone(reopened.reuse("interpolation", lambda path: path))

    def test_runtime_directory_file_change_discards_previous_intermediates(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            destination = root / "output.mp4"
            source = root / "source.mp4"
            runtime = root / "runtime"
            runtime.mkdir()
            runtime_file = runtime / "runtime.py"
            source.write_bytes(b"source")
            runtime_file.write_bytes(b"runtime")
            plan = type("Plan", (), {"to_dict": lambda self: {"route": "enhanced"}})()
            runtime_paths = {"rve_root": runtime}
            first_request = self._build_request(plan, source, runtime_paths)
            cache = ExportCache.open(destination, first_request)
            artifact = cache.root / "interpolated.mp4"
            artifact.write_bytes(b"interpolated")
            cache.record("interpolation", artifact)

            os.utime(
                runtime_file,
                ns=(runtime_file.stat().st_atime_ns, runtime_file.stat().st_mtime_ns + 1),
            )
            second_request = self._build_request(plan, source, runtime_paths)

            reopened = ExportCache.open(destination, second_request)

            self.assertFalse(artifact.exists())
            self.assertIsNone(reopened.reuse("interpolation", lambda path: path))

    def test_successful_export_removes_only_the_cache_directory(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            destination = root / "output.mp4"
            destination.write_bytes(b"published")
            cache = ExportCache.open(destination, {"policy": "test"})
            artifact = cache.root / "interpolated.mp4"
            artifact.write_bytes(b"interpolated")
            cache.record("interpolation", artifact)

            cache.discard_after_success()

            self.assertFalse(cache.root.exists())
            self.assertTrue(destination.exists())


if __name__ == "__main__":
    unittest.main()
