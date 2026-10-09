import unittest
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
QUALITY_WORKFLOW = REPOSITORY_ROOT / ".github" / "workflows" / "quality.yml"
STALE_WORKFLOW = REPOSITORY_ROOT / ".github" / "workflows" / "workflow-evals.yml"


class EditorCIParityTests(unittest.TestCase):
    def test_quality_workflow_uses_native_quality_and_functionality_commands(self):
        self.assertTrue(QUALITY_WORKFLOW.is_file())
        if not QUALITY_WORKFLOW.is_file():
            return

        workflow = QUALITY_WORKFLOW.read_text(encoding="utf-8")
        for command in (
            "make quality PYTHON=.venv/bin/python",
            "make contract PYTHON=.venv/bin/python",
            "make smoke PYTHON=.venv/bin/python",
        ):
            self.assertIn(command, workflow)

        self.assertIn("/usr/bin/python3 -m venv --system-site-packages .venv", workflow)
        self.assertIn("pip install --requirement requirements-dev.txt", workflow)
        self.assertIn("npm ci", workflow)
        self.assertIn("xvfb-run", workflow)
        self.assertIn("ffmpeg", workflow)
        self.assertIn("ffprobe", workflow)
        self.assertIn(
            "tests.test_phase010_functionality.Phase010FunctionalityTests."
            "test_complete_edit_and_delivery_journey",
            workflow,
        )
        self.assertIn("gir1.2-gtk-4.0", workflow)
        self.assertIn("python3-gi", workflow)
        self.assertIn("python3-gi-cairo", workflow)
        self.assertIn('gi.require_foreign("cairo")', workflow)
        self.assertIn("python3-venv", workflow)
        self.assertIn("xauth", workflow)
        self.assertIn("xvfb", workflow)
        self.assertNotIn("eval_workflows.py", workflow)
        self.assertNotIn("workflow-contracts.json", workflow)
        self.assertNotIn("duplication-baseline", workflow)
        self.assertNotIn("--update-baseline", workflow)

    def test_stale_workflow_eval_definition_is_removed(self):
        self.assertFalse(STALE_WORKFLOW.exists())

    def test_quality_display_supports_native_x11_input(self):
        workflow = QUALITY_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("xdotool", workflow)
        self.assertIn("command -v xdotool", workflow)
        self.assertGreaterEqual(workflow.count("GDK_BACKEND=x11"), 4)
        for command in workflow.splitlines():
            if command.strip().startswith("xvfb-run "):
                self.assertIn("-screen 0 1920x1200x24", command)


if __name__ == "__main__":
    unittest.main()
