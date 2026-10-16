import subprocess
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from framestudio.post_export import (
    PostExportActionError,
    execute_post_export_action,
    failure_log_path,
    write_export_failure_log,
)


class EditorPostExportTests(unittest.TestCase):
    def test_batch_failure_preserves_the_output_error_for_ui_and_failure_log(self):
        from framestudio.app_export import ExportBatchExecutionError
        from framestudio.export_coordinator import (
            ExportBatchResult,
            ExportOutputResult,
            ExportResultState,
        )
        from framestudio.output_plan import OutputIdentity

        detail = "Rendered output verification failed: empty interval"
        failed = ExportOutputResult(
            identity=OutputIdentity(
                mode="final-only",
                output_kind="final",
                track_id=None,
                source_id=None,
                framing="dynamic",
                audio_intent="timeline",
                render_profile="project",
            ),
            destination=Path("output.mp4"),
            fingerprint="fixture",
            state=ExportResultState.FAILED,
            error={"code": "render-failed", "message": detail},
        )
        batch = ExportBatchResult(
            results=(failed,),
            mode="final-only",
            complete=False,
            partial_success=False,
        )
        error = ExportBatchExecutionError(batch)
        self.assertIn(detail, str(error))
        self.assertIs(error.result, batch)
        with TemporaryDirectory() as temporary:
            log = write_export_failure_log(
                project_path=Path(temporary) / "edit.framestudio.json",
                destination=failed.destination,
                message=str(error),
                action="nothing",
            )
            self.assertIn(detail, log.read_text())

    def test_failure_log_prefers_the_saved_project_directory(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            project = root / "edit.framestudio.json"
            destination = root / "exports" / "output.mp4"

            self.assertEqual(
                failure_log_path(project, destination),
                root / "edit.framestudio.export-failure.log",
            )

    def test_failure_log_is_written_atomically_with_actionable_context(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            project = root / "edit.framestudio.json"
            destination = root / "output.mp4"

            result = write_export_failure_log(
                project_path=project,
                destination=destination,
                message="FFmpeg failed",
                action="sleep",
            )

            self.assertEqual(result, root / "edit.framestudio.export-failure.log")
            content = result.read_text(encoding="utf-8")
            self.assertIn("FFmpeg failed", content)
            self.assertIn("Action: sleep", content)
            self.assertIn("Destination: output.mp4", content)

    def test_sleep_dispatch_uses_systemctl_suspend(self):
        with (
            patch("framestudio.post_export.shutil.which", return_value="/usr/bin/systemctl"),
            patch("framestudio.post_export.subprocess.run") as run,
        ):
            execute_post_export_action("sleep")

        run.assert_called_once_with(
            ["/usr/bin/systemctl", "suspend"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            timeout=15,
        )

    def test_default_dispatch_uses_current_module_dependencies(self):
        with (
            patch(
                "framestudio.post_export.shutil.which",
                return_value="/usr/bin/systemctl",
            ) as which,
            patch("framestudio.post_export.subprocess.run") as run,
        ):
            execute_post_export_action("shutdown")

        which.assert_called_once_with("systemctl")
        run.assert_called_once_with(
            ["/usr/bin/systemctl", "poweroff"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            timeout=15,
        )

    def test_unavailable_post_export_action_is_reported(self):
        with patch("framestudio.post_export.shutil.which", return_value=None):
            with self.assertRaisesRegex(PostExportActionError, "not available"):
                execute_post_export_action("shutdown")

    def test_failed_post_export_command_is_reported(self):
        error = subprocess.CalledProcessError(
            1,
            ["/usr/bin/systemctl", "poweroff"],
            stderr="permission denied",
        )
        with (
            patch("framestudio.post_export.shutil.which", return_value="/usr/bin/systemctl"),
            patch("framestudio.post_export.subprocess.run", side_effect=error),
        ):
            with self.assertRaisesRegex(PostExportActionError, "permission denied"):
                execute_post_export_action("shutdown")


if __name__ == "__main__":
    unittest.main()
