import io
import os
import subprocess
import threading
import unittest
from contextlib import redirect_stdout
from fractions import Fraction
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

from framestudio_fps import (
    DEFAULT_FALLBACK_ENGINE,
    build_encode_command,
    build_rve_custom_encoder,
    build_rve_normalization_command,
    build_rve_restoration_command,
    default_output,
    parse_arguments,
    probe_video,
    progress_line,
    remux_rve_audio,
    run_pipeline,
    rve_base_frame_count,
    rve_environment,
    rve_interpolation_factor,
    rve_render_frame_count,
    rve_render_rate,
    rve_runtime_unavailable_reason,
    target_frame_count,
)


class FpsTests(unittest.TestCase):
    def test_target_frame_count_preserves_rational_duration(self):
        self.assertEqual(
            target_frame_count(
                Fraction(30000, 1001),
                900,
                Fraction(60, 1),
            ),
            1802,
        )

    def test_single_input_output_name(self):
        output = default_output(
            [Path("/tmp/source.mp4")],
            Path("/tmp"),
            "4.26",
            Fraction(60, 1),
        )
        self.assertEqual(output, Path("/tmp/source-rife4.26-60fps.mp4"))

    def test_encode_command_copies_audio(self):
        command = build_encode_command(
            Path("source.mp4"),
            Path("output.partial.mp4"),
            "h264_nvenc",
        )
        self.assertIn("-c:a", command)
        self.assertEqual(command[command.index("-c:a") + 1], "copy")
        self.assertEqual(command[command.index("-qp") + 1], "18")
        self.assertIn("-f", command)
        self.assertEqual(command[-1], str(Path("output.partial.mp4")))

    def test_rve_is_the_default_engine(self):
        self.assertEqual(parse_arguments([]).engine, "rve")

    def test_ffmpeg_fallback_engine_is_selectable(self):
        self.assertEqual(
            parse_arguments(["--engine", DEFAULT_FALLBACK_ENGINE]).engine,
            DEFAULT_FALLBACK_ENGINE,
        )

    def test_rve_uses_factor_two_and_pads_duration_preserving_output(self):
        source_rate = Fraction(30000, 1001)
        target_rate = Fraction(60, 1)
        self.assertEqual(rve_interpolation_factor(source_rate, target_rate), 2)
        self.assertEqual(
            rve_base_frame_count(source_rate, 900, target_rate),
            1800,
        )
        command = build_rve_custom_encoder(1802, 1800)
        self.assertIn("tpad=stop_mode=clone:stop=2", command)
        self.assertIn("-frames:v 1802", command)
        self.assertIn("-f mp4", command)

    def test_rve_uses_integer_gpu_oversampling_for_fractional_target_rate(self):
        source_rate = Fraction(24000, 1001)
        target_rate = Fraction(60, 1)

        self.assertEqual(rve_interpolation_factor(source_rate, target_rate), 3)
        self.assertEqual(rve_render_rate(source_rate, target_rate), Fraction(72000, 1001))
        self.assertEqual(
            rve_render_frame_count(source_rate, 72, target_rate, 180),
            216,
        )
        command = build_rve_normalization_command(
            Path("rve.mp4"),
            Path("normalized.mp4"),
            target_rate,
            180,
        )
        self.assertTrue(any("fps=60" in value for value in command))
        self.assertTrue(any("tpad=stop_mode=clone:stop=180" in value for value in command))
        self.assertIn("-c:v", command)
        self.assertEqual(command[command.index("-c:v") + 1], "h264_nvenc")
        self.assertIn("-frames:v", command)
        self.assertEqual(command[command.index("-frames:v") + 1], "180")

    def test_rve_restoration_command_uses_only_the_1x_restoration_model(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            model = root / "deH264_SuperUltraCompact.safetensors"
            model.touch()
            arguments = parse_arguments(
                [
                    "--python",
                    str(root / "python"),
                    "--rve-root",
                    str(root / "rve"),
                    "--encoder",
                    "h264_nvenc",
                ]
            )
            backend = arguments.rve_root / "backend"
            (backend / "src" / "pytorch").mkdir(parents=True)
            (backend / "src" / "FFmpegBuffers.py").write_text(
                "RVE_OUTPUT_FPS RVE_RGB_INPUT",
                encoding="utf-8",
            )
            (backend / "src" / "RenderVideo.py").write_text(
                "RVE_EXACT_FRAME_COUNT",
                encoding="utf-8",
            )
            (backend / "rve-backend.py").write_text("backend", encoding="utf-8")
            (backend / "src" / "pytorch" / "TensorRTHandler.py").write_text(
                "RVE_TRT_TORCH_PIXEL",
                encoding="utf-8",
            )
            with patch("framestudio_fps.require_tool", return_value="ffmpeg"):
                command = build_rve_restoration_command(
                    root / "source.mp4",
                    root / "output.partial.mp4",
                    30,
                    root / "cwd",
                    arguments,
                    model,
                )

        self.assertIn("--extra_restoration_models", command)
        self.assertEqual(command[command.index("--extra_restoration_models") + 1], str(model))
        self.assertNotIn("--interpolate_model", command)
        self.assertNotIn("--interpolate_factor", command)
        self.assertIn("-frames:v 30", command[command.index("--custom_encoder") + 1])

    def test_rve_audio_remux_handles_completed_process_output(self):
        process = Mock(returncode=0)
        process.communicate.return_value = ("", "")
        with (
            patch("framestudio_fps.require_tool", return_value="ffmpeg"),
            patch("framestudio_fps.subprocess.Popen", return_value=process) as popen,
        ):
            remux_rve_audio(
                Path("source.mp4"),
                Path("video.mp4"),
                Path("output.mp4"),
            )
        popen.assert_called_once()
        process.communicate.assert_called_once_with()

    def test_rve_runtime_preflight_reports_cuda_and_model(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            python = root / "python"
            model = root / "rife4.26.pkl"
            model.touch()
            arguments = parse_arguments(
                [
                    "--python",
                    str(python),
                    "--rve-model",
                    str(model),
                ]
            )
            completed = subprocess.CompletedProcess(
                [],
                0,
                "CUDA device=NVIDIA GeForce RTX 5070 Ti; model=loaded\n",
                "",
            )
            with patch("framestudio_fps.subprocess.run", return_value=completed) as run:
                reason = rve_runtime_unavailable_reason(arguments)

            self.assertIsNone(reason)
            command = run.call_args.args[0]
            self.assertEqual(command[0], str(python))
            self.assertEqual(command[1], "-c")
            self.assertEqual(command[-1], str(model.resolve()))
            check_script = command[2]
            self.assertIn("torch.cuda.synchronize()", check_script)
            self.assertIn("capability=", check_script)

    def test_rve_environment_exposes_cuda_and_tensorrt_libraries(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            site_packages = root / "site-packages"
            cuda_lib = site_packages / "nvidia" / "cu13" / "lib"
            tensorrt_lib = site_packages / "tensorrt_libs"
            cuda_lib.mkdir(parents=True)
            tensorrt_lib.mkdir()
            arguments = parse_arguments(["--site-packages", str(site_packages)])

            with patch.dict("os.environ", {"LD_LIBRARY_PATH": "/existing"}, clear=False):
                environment = rve_environment(arguments, Fraction(60, 1))

            library_path = environment["LD_LIBRARY_PATH"].split(os.pathsep)
            self.assertEqual(library_path[:2], [str(cuda_lib), str(tensorrt_lib)])
            self.assertIn("/existing", library_path)

    def test_rve_interpolation_stops_before_start_when_cancelled(self):
        cancel_event = threading.Event()
        cancel_event.set()
        arguments = parse_arguments([])

        with self.assertRaisesRegex(RuntimeError, "Export cancelled"):
            from framestudio_fps import run_interpolation_rve

            run_interpolation_rve(
                Path("source.mp4"),
                Path("output.mp4"),
                Fraction(30, 1),
                30,
                Fraction(60, 1),
                60,
                arguments,
                cancel_event=cancel_event,
            )

    def test_vapoursynth_cancellation_uses_bounded_process_termination(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            python = root / "python"
            graph = root / "graph.vpy"
            site_packages = root / "site-packages"
            trt_cache = root / "trt-cache"
            bestsource = root / "bestsource.so"
            source = root / "source.mp4"
            output = root / "output.mp4"
            for path in (python, graph, bestsource, source):
                path.touch()
            site_packages.mkdir()
            trt_cache.mkdir()
            arguments = parse_arguments(
                [
                    "--python",
                    str(python),
                    "--graph",
                    str(graph),
                    "--site-packages",
                    str(site_packages),
                    "--trt-cache",
                    str(trt_cache),
                    "--bestsource",
                    str(bestsource),
                ],
            )
            cancel_event = threading.Event()
            finished = threading.Event()

            class Stream:
                def close(self):
                    return None

            class Process:
                def __init__(self):
                    self.stdout = Stream()
                    self.stderr = Stream()
                    self.returncode = -15
                    self.killed = False

                def poll(self):
                    return None if not self.killed else self.returncode

                def terminate(self):
                    return None

                def kill(self):
                    self.killed = True

                def wait(self, timeout=None):
                    if timeout is None and not self.killed:
                        raise AssertionError("process termination must be bounded")
                    if timeout is not None and not self.killed:
                        raise subprocess.TimeoutExpired("vs-rife", timeout)
                    return self.returncode

            writer = Process()
            encoder = Process()

            def drain(_stream, label, messages):
                cancel_event.set()
                messages.put((label, None))
                finished.set()

            with (
                patch("framestudio_fps.subprocess.Popen", side_effect=(writer, encoder)),
                patch("framestudio_fps.build_encode_command", return_value=["encoder"]),
                patch("framestudio_fps.drain_stderr", side_effect=drain),
            ):
                with self.assertRaisesRegex(RuntimeError, "Export cancelled"):
                    from framestudio_fps import run_interpolation

                    run_interpolation(
                        source,
                        output,
                        Fraction(60, 1),
                        60,
                        arguments,
                        cancel_event=cancel_event,
                    )

            self.assertTrue(finished.is_set())
            self.assertTrue(writer.killed)
            self.assertTrue(encoder.killed)

    def test_progress_line_contains_pacman_metrics(self):
        line = progress_line(50, 100, 0.0, now=10.0)
        self.assertIn("50.00%", line)
        self.assertIn("frame 50/100", line)
        self.assertIn("elapsed 00:00:10", line)
        self.assertIn("ETA 00:00:10", line)
        self.assertIn("C", line)

    def test_single_input_skips_concat(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = root / "source.mp4"
            output = root / "output.mp4"
            source.touch()
            arguments = parse_arguments(
                [str(source), "--output", str(output), "--engine", "vs-rife"]
            )
            with (
                patch(
                    "framestudio_fps.probe_video",
                    return_value=(Fraction(30000, 1001), 900),
                ),
                patch("framestudio_fps.concatenate") as concatenate,
                patch("framestudio_fps.run_interpolation") as run_interpolation,
            ):
                run_pipeline([source], root, arguments)
            concatenate.assert_not_called()
            run_interpolation.assert_called_once()

    def test_missing_rve_uses_ffmpeg_fallback(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = root / "source.mp4"
            output = root / "output.mp4"
            subprocess.run(
                [
                    "ffmpeg",
                    "-hide_banner",
                    "-loglevel",
                    "error",
                    "-y",
                    "-f",
                    "lavfi",
                    "-i",
                    "testsrc=size=64x64:rate=10",
                    "-f",
                    "lavfi",
                    "-i",
                    "sine=frequency=880:sample_rate=48000",
                    "-t",
                    "0.5",
                    "-shortest",
                    "-c:v",
                    "libx264",
                    "-pix_fmt",
                    "yuv420p",
                    "-c:a",
                    "aac",
                    str(source),
                ],
                check=True,
            )
            source_before = source.read_bytes()
            arguments = parse_arguments(
                [
                    str(source),
                    "--output",
                    str(output),
                    "--encoder",
                    "libx264",
                    "--performance-mode",
                    "off",
                    "--python",
                    str(root / "missing-python"),
                    "--site-packages",
                    str(root / "missing-site-packages"),
                    "--rve-root",
                    str(root / "missing-rve"),
                    "--rve-model",
                    str(root / "missing-model.pkl"),
                ]
            )
            console = io.StringIO()
            with redirect_stdout(console):
                result = run_pipeline([source], root, arguments)

            source_rate, source_frames = probe_video(source)
            output_rate, output_frames = probe_video(output)
            self.assertEqual(result, 0)
            self.assertEqual(output_rate, arguments.target_fps)
            self.assertEqual(
                output_frames,
                target_frame_count(source_rate, source_frames, arguments.target_fps),
            )
            self.assertEqual(source.read_bytes(), source_before)
            audio = subprocess.run(
                [
                    "ffprobe",
                    "-v",
                    "error",
                    "-select_streams",
                    "a:0",
                    "-show_entries",
                    "stream=codec_name",
                    "-of",
                    "csv=p=0",
                    str(output),
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            self.assertEqual(audio.stdout.strip(), "aac")
            self.assertIn("FFmpeg minterpolate fallback", console.getvalue())


if __name__ == "__main__":
    unittest.main()
