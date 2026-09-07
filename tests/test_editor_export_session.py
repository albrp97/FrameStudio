import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from framestudio.export_session import (
    ExportSession,
    ExportSessionBusy,
    ExportSessionMismatch,
    ExportSessionNotFound,
    build_export_session_request,
    discard_export_session,
    discover_export_session,
    session_root,
)


class _Plan:
    def __init__(self, destination: Path):
        self.destination = destination

    def to_dict(self):
        return {
            "route": "fallback",
            "destination": str(self.destination),
            "segments": [],
        }


class ExportSessionTests(unittest.TestCase):
    def _request(self, root: Path, destination: Path, *, policy: str = "default"):
        source = root / "source.mp4"
        source.write_bytes(b"source")
        return build_export_session_request(
            plan=_Plan(destination),
            source_paths=(source,),
            source_stats=(source.stat(),),
            options={"policy": policy},
            ffmpeg_path="ffmpeg",
            ffprobe_path="ffprobe",
        )

    def test_manifest_round_trip_records_only_validated_artifacts(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            destination = root / "output.mp4"
            request = self._request(root, destination)

            session = ExportSession.open(
                destination,
                request,
                ("prepare", "compose"),
            )
            source = root / "source.mp4"
            artifact = session.record("prepare", source, metadata={"frames": 1})
            self.assertTrue(artifact.is_file())
            self.assertEqual(session.last_completed_stage, "prepare")
            session.close()

            reopened = ExportSession.open(
                destination,
                request,
                ("prepare", "compose"),
                mode="resume",
            )
            self.assertEqual(reopened.reuse("prepare"), artifact)
            manifest = json.loads(
                (session_root(destination) / "manifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual(manifest["stages"]["prepare"]["status"], "complete")
            reopened.close()

    def test_resume_rejects_request_mismatch_without_clearing_checkpoint(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            destination = root / "output.mp4"
            request = self._request(root, destination, policy="old")
            session = ExportSession.open(destination, request, ("compose",))
            session.record("compose", root / "source.mp4")
            session.close()

            with self.assertRaises(ExportSessionMismatch):
                ExportSession.open(
                    destination,
                    self._request(root, destination, policy="new"),
                    ("compose",),
                    mode="resume",
                )

            info = discover_export_session(destination)
            self.assertTrue(info.resumable)
            self.assertEqual(info.last_completed_stage, "compose")

    def test_resume_requires_an_existing_session(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            destination = root / "output.mp4"
            with self.assertRaises(ExportSessionNotFound):
                ExportSession.open(
                    destination,
                    self._request(root, destination),
                    ("compose",),
                    mode="resume",
                )

    def test_corrupt_manifest_is_reported_and_restart_rebuilds_it(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            destination = root / "output.mp4"
            request = self._request(root, destination)
            session = ExportSession.open(destination, request, ("compose",))
            session.close()
            (session_root(destination) / "manifest.json").write_text("{", encoding="utf-8")

            info = discover_export_session(destination)
            self.assertFalse(info.valid)
            self.assertIn("unreadable", info.reason or "")
            restarted = ExportSession.open(
                destination,
                request,
                ("compose",),
                mode="restart",
            )
            self.assertIsNone(restarted.last_completed_stage)
            restarted.close()

    def test_missing_artifact_invalidates_stage_and_dependents(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            destination = root / "output.mp4"
            request = self._request(root, destination)
            session = ExportSession.open(destination, request, ("prepare", "compose"))
            session.record("prepare", root / "source.mp4")
            session.record("compose", root / "source.mp4")
            session.artifact_path("prepare").unlink()
            self.assertIsNone(session.reuse("prepare"))
            self.assertIsNone(session.reuse("compose"))
            session.close()

    def test_failure_is_persistent_and_success_cleanup_is_terminal(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            destination = root / "output.mp4"
            request = self._request(root, destination)
            session = ExportSession.open(destination, request, ("compose",))
            session.mark_failure("cancelled", cancelled=True)
            session.close()
            self.assertEqual(discover_export_session(destination).state, "cancelled")

            session = ExportSession.open(
                destination,
                request,
                ("compose",),
                mode="resume",
            )
            session.cleanup_after_success()
            self.assertFalse(session_root(destination).exists())

    def test_second_worker_is_rejected(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            destination = root / "output.mp4"
            request = self._request(root, destination)
            session = ExportSession.open(destination, request, ("compose",))
            try:
                with self.assertRaises(ExportSessionBusy):
                    ExportSession.open(destination, request, ("compose",), mode="resume")
            finally:
                session.close()

    def test_discard_removes_only_the_session(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            destination = root / "output.mp4"
            destination.write_bytes(b"published")
            request = self._request(root, destination)
            session = ExportSession.open(destination, request, ("compose",))
            session.close()

            info = discard_export_session(destination)
            self.assertFalse(info.exists)
            self.assertTrue(destination.is_file())


if __name__ == "__main__":
    unittest.main()
