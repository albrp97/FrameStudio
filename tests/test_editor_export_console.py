import io
import unittest

from framestudio.export import ExportProgress
from framestudio.export_console import ConsoleProgressReporter


class ExportConsoleTests(unittest.TestCase):
    def test_reporter_emits_numbered_pipeline_stages(self):
        output = io.StringIO()
        clock_values = iter(range(10))
        reporter = ConsoleProgressReporter(
            stream=output,
            force=True,
            clock=lambda: next(clock_values),
        )

        for stage, percent in (
            ("starting", 0.0),
            ("interpolating segment 1/2", 40.0),
            ("concatenating enhanced segments", 90.0),
            ("verifying", 99.0),
            ("complete", 100.0),
        ):
            reporter(
                ExportProgress(
                    stage=stage,
                    percent=percent,
                    frame=10,
                    total_frames=100,
                    fps=30.0,
                    elapsed_seconds=2.0,
                    eta_seconds=1.0 if percent < 100.0 else 0.0,
                )
            )

        lines = output.getvalue().splitlines()
        self.assertIn("Step 1/5 - Preparing sources", lines[0])
        self.assertIn("Step 2/5 - Rendering and enhancing", lines[1])
        self.assertIn("Step 3/5 - Concatenating and composing", lines[2])
        self.assertIn("Step 4/5 - Verifying output", lines[3])
        self.assertIn("Step 5/5 - Publishing output", lines[4])
        self.assertEqual(lines[-1], "Export complete.")

    def test_reporter_suppresses_non_tty_output_without_force(self):
        output = io.StringIO()
        reporter = ConsoleProgressReporter(stream=output)

        reporter(
            ExportProgress(
                stage="starting",
                percent=0.0,
                frame=0,
                total_frames=10,
                fps=None,
                elapsed_seconds=0.0,
                eta_seconds=None,
            )
        )

        self.assertEqual(output.getvalue(), "")

    def test_reporter_emits_heartbeat_when_progress_has_not_advanced(self):
        output = io.StringIO()
        clock_values = iter((0.0, 5.0))
        reporter = ConsoleProgressReporter(
            stream=output,
            force=True,
            clock=lambda: next(clock_values),
        )

        for elapsed, frame in ((0.0, 100), (5.0, 200)):
            reporter(
                ExportProgress(
                    stage="normalizing source run",
                    percent=0.2,
                    frame=frame,
                    total_frames=87037,
                    fps=1.0,
                    elapsed_seconds=elapsed,
                    eta_seconds=None,
                )
            )

        lines = output.getvalue().splitlines()
        self.assertEqual(len(lines), 2)
        self.assertIn("frame 200/87037", lines[-1])
        self.assertIn("elapsed 00:05", lines[-1])

    def test_intermediate_publication_stays_in_rendering_stage(self):
        output = io.StringIO()
        reporter = ConsoleProgressReporter(stream=output, force=True)

        reporter(
            ExportProgress(
                stage="publishing interpolated output",
                percent=95.0,
                frame=10,
                total_frames=10,
                fps=None,
                elapsed_seconds=1.0,
                eta_seconds=None,
            )
        )

        self.assertIn("Step 2/5 - Rendering and enhancing", output.getvalue())

    def test_composing_stage_uses_composition_step(self):
        output = io.StringIO()
        reporter = ConsoleProgressReporter(stream=output, force=True)

        reporter(
            ExportProgress(
                stage="composing",
                percent=50.0,
                frame=5,
                total_frames=10,
                fps=None,
                elapsed_seconds=1.0,
                eta_seconds=None,
            )
        )

        self.assertIn("Step 3/5 - Concatenating and composing", output.getvalue())


if __name__ == "__main__":
    unittest.main()
