from __future__ import annotations

import hashlib
import os
import subprocess
import sys
import threading
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from framestudio.export_types import ExportExecutionError
from framestudio.video_compositor import _sha256


class SourceHashCacheTests(unittest.TestCase):
    def test_source_modified_while_hashing_is_not_persisted(self):
        from itertools import count

        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source.bin"
            source.write_bytes(b"x" * (2 * 1024 * 1024))
            cache = root / "cache"
            with (
                patch.dict(os.environ, XDG_CACHE_HOME=str(cache)),
                patch("framestudio.source_hash_cache.time.monotonic", side_effect=count()),
                self.assertRaisesRegex(ExportExecutionError, "Source changed"),
            ):
                _sha256(
                    source,
                    persistent=True,
                    heartbeat_callback=lambda: source.write_bytes(b"changed"),
                )
            self.assertFalse(cache.exists())

    def test_persistent_cache_reuses_hash_without_reading_source(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source.bin"
            source.write_bytes(b"source identity")
            with patch.dict(os.environ, XDG_CACHE_HOME=str(root / "cache")):
                digest = _sha256(source, persistent=True)
                original_open = Path.open

                def guarded_open(path, *args, **kwargs):
                    if path == source:
                        raise AssertionError("unchanged source was read again")
                    return original_open(path, *args, **kwargs)

                with patch.object(Path, "open", guarded_open):
                    self.assertEqual(_sha256(source, persistent=True), digest)
                self.assertEqual(digest, hashlib.sha256(b"source identity").hexdigest())
                # Output/checkpoint verification must still read actual content.
                with patch.object(Path, "open", guarded_open), self.assertRaises(AssertionError):
                    _sha256(source)

    def test_same_size_change_with_restored_mtime_invalidates_cache(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source.bin"
            source.write_bytes(b"first")
            with patch.dict(os.environ, XDG_CACHE_HOME=str(root / "cache")):
                before = source.stat()
                original = _sha256(source, persistent=True)
                source.write_bytes(b"other")
                os.utime(source, ns=(before.st_atime_ns, before.st_mtime_ns))
                self.assertNotEqual(_sha256(source, persistent=True), original)

    def test_corrupt_cache_is_an_explicit_error_and_cancelled_hash_is_not_saved(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source.bin"
            source.write_bytes(b"source")
            cache = root / "cache"
            with patch.dict(os.environ, XDG_CACHE_HOME=str(cache)):
                event = threading.Event()
                event.set()
                with self.assertRaisesRegex(ExportExecutionError, "cancel"):
                    _sha256(source, persistent=True, cancel_event=event)
                self.assertFalse(cache.exists())
                _sha256(source, persistent=True)
                record = next(cache.rglob("*.json"))
                record.write_text('{"version": 1, "sha256": "invalid"}')
                with self.assertRaisesRegex(ExportExecutionError, "source.hash cache"):
                    _sha256(source, persistent=True)


class SourceHashCacheFunctionalityTests(unittest.TestCase):
    def test_export_planning_reuses_hashes_across_fresh_processes(self):
        import shutil

        from framestudio.media import probe_media
        from framestudio.model import Project
        from framestudio.persistence import save_project
        from tests.test_editor_video_compositor_functionality import _make_marker_source

        if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
            self.skipTest("FFmpeg and ffprobe are required")
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = _make_marker_source(root, "source.mp4", 320, 180, "30", "red")
            project_path = root / "project.framestudio.json"
            save_project(
                Project.create_synchronized(source, probe_media(source).metadata()), project_path
            )
            script = """
import os, sys
from pathlib import Path
from framestudio.av_compositor import plan_project_av
from framestudio.persistence import load_project
from framestudio.upscale_policy import UpscalePolicy
source = Path(sys.argv[2])
original_open = Path.open
def guarded_open(path, *args, **kwargs):
    if os.environ.get("DENY_SOURCE_READ") and path == source:
        raise AssertionError("source hash was recomputed after process restart")
    return original_open(path, *args, **kwargs)
Path.open = guarded_open
plan = plan_project_av(load_project(Path(sys.argv[1])), source.with_name("output.mp4"),
    target_rate=30, upscale_policy=UpscalePolicy(enabled=False))
print(plan.source_hashes[0])
"""
            command = [sys.executable, "-c", script, str(project_path), str(source)]
            environment = {**os.environ, "XDG_CACHE_HOME": str(root / "cache")}
            first = subprocess.run(
                command, env=environment, check=True, capture_output=True, text=True
            )
            resumed = subprocess.run(
                command,
                env={**environment, "DENY_SOURCE_READ": "1"},
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertEqual(first.stdout, resumed.stdout)
            self.assertEqual(first.stdout.strip(), hashlib.sha256(source.read_bytes()).hexdigest())
