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
