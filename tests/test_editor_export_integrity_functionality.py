from __future__ import annotations

import hashlib
import json
import math
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

from framestudio.export_session import session_root

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
_ARTIFACT_DIR = os.environ.get("FRAMESTUDIO_TICKET104_ARTIFACT_DIR", "").strip()
ARTIFACT_PARENT = Path(_ARTIFACT_DIR).expanduser().resolve() if _ARTIFACT_DIR else None


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _run(
    command: list[str],
    *,
    cwd: Path = REPOSITORY_ROOT,
    env: dict[str, str] | None = None,
    timeout: float = 300.0,
) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        command,
        cwd=cwd,
        env=env,
        capture_output=True,
        timeout=timeout,
        check=False,
    )


def _probe(ffprobe: str, media: Path) -> dict[str, Any]:
    result = _run(
        [
            ffprobe,
            "-v",
            "error",
            "-count_frames",
            "-show_streams",
            "-show_format",
            "-of",
            "json",
            str(media),
        ],
    )
    if result.returncode != 0:
        raise AssertionError(
            f"ffprobe failed for {media.name}: {result.stderr.decode(errors='replace')}",
        )
    return json.loads(result.stdout)


def _tone_power(samples: list[float], sample_rate: int, frequency: float) -> float:
    if not samples:
        return 0.0
    bin_index = max(1, round(len(samples) * frequency / sample_rate))
    omega = 2.0 * math.pi * bin_index / len(samples)
    coefficient = 2.0 * math.cos(omega)
    previous = 0.0
    previous_previous = 0.0
    for sample in samples:
        current = sample + coefficient * previous - previous_previous
        previous_previous = previous
        previous = current
    return previous_previous**2 + previous**2 - coefficient * previous * previous_previous


def _tone_powers(
    left_channel: list[float],
    right_channel: list[float],
) -> dict[str, float]:
    return {
        "left_440": _tone_power(left_channel, 48_000, 440.0),
        "left_550": _tone_power(left_channel, 48_000, 550.0),
        "left_660": _tone_power(left_channel, 48_000, 660.0),
        "left_880": _tone_power(left_channel, 48_000, 880.0),
        "left_1100": _tone_power(left_channel, 48_000, 1100.0),
        "left_1320": _tone_power(left_channel, 48_000, 1320.0),
        "right_440": _tone_power(right_channel, 48_000, 440.0),
        "right_550": _tone_power(right_channel, 48_000, 550.0),
        "right_660": _tone_power(right_channel, 48_000, 660.0),
        "right_880": _tone_power(right_channel, 48_000, 880.0),
        "right_1100": _tone_power(right_channel, 48_000, 1100.0),
        "right_1320": _tone_power(right_channel, 48_000, 1320.0),
    }


def _power_ratio(
    powers: dict[str, float],
    numerator_key: str,
    denominator_key: str,
) -> float:
    denominator = powers[denominator_key]
    if denominator <= 0.0:
        raise AssertionError(f"Measured power for {denominator_key} must be positive")
    return powers[numerator_key] / denominator


def _decode_audio_channels(
    ffmpeg: str,
    media: Path,
    *,
    start_seconds: float,
    duration_seconds: float,
) -> tuple[list[float], list[float]]:
    result = _run(
        [
            ffmpeg,
            "-hide_banner",
            "-loglevel",
            "error",
            "-nostdin",
            "-i",
            str(media),
            "-ss",
            f"{start_seconds:.3f}",
            "-t",
            f"{duration_seconds:.3f}",
            "-map",
            "0:a:0",
            "-ac",
            "2",
            "-ar",
            "48000",
            "-f",
            "f32le",
            "-",
        ],
    )
    if result.returncode != 0:
        raise AssertionError(
            f"Could not decode output PCM: {result.stderr.decode(errors='replace')}",
        )
    usable_bytes = len(result.stdout) - (len(result.stdout) % 8)
    values = struct.unpack(f"<{usable_bytes // 4}f", result.stdout[:usable_bytes])
    return list(values[::2]), list(values[1::2])


def _sample_rgba(ffmpeg: str, media: Path, frame: int) -> tuple[int, int, int, int]:
    result = _run(
        [
            ffmpeg,
            "-hide_banner",
            "-loglevel",
            "error",
            "-nostdin",
            "-i",
            str(media),
            "-vf",
            f"select=eq(n\\,{frame}),crop=2:2:960:540,scale=1:1,format=rgba",
            "-frames:v",
            "1",
            "-f",
            "rawvideo",
            "-pix_fmt",
            "rgba",
            "-",
        ],
    )
    if result.returncode != 0 or len(result.stdout) != 4:
        raise AssertionError(
            f"Could not sample frame {frame}: {result.stderr.decode(errors='replace')}",
        )
    red, green, blue, alpha = result.stdout
    return red, green, blue, alpha


class EditorExportIntegrityFunctionalityTests(unittest.TestCase):
    """Real CLI/FFmpeg route-integrity evidence for TICKET-104."""

    def _subprocess_environment(self, root: Path) -> dict[str, str]:
        state = root / "xdg-state"
        cache = root / "xdg-cache"
        config = root / "xdg-config"
        data = root / "xdg-data"
        temporary = root / "tmp"
        for directory in (state, cache, config, data, temporary):
            directory.mkdir(parents=True, exist_ok=True)
        environment = os.environ.copy()
        environment.update(
            {
                "TMPDIR": str(temporary),
                "XDG_STATE_HOME": str(state),
                "XDG_CACHE_HOME": str(cache),
                "XDG_CONFIG_HOME": str(config),
                "XDG_DATA_HOME": str(data),
                "PYTHONHASHSEED": "0",
                "FRAMESTUDIO_TICKET104_FFMPEG_LOG": str(root / "ffmpeg-wrapper.jsonl"),
            },
        )
        return environment

    def _run_cli(
        self,
        root: Path,
        environment: dict[str, str],
        label: str,
        *arguments: str,
        timeout: float = 360.0,
    ) -> list[dict[str, Any]]:
        command = [
            sys.executable,
            str(REPOSITORY_ROOT / "framestudio.py"),
            *arguments,
        ]
        result = subprocess.run(
            command,
            cwd=REPOSITORY_ROOT,
            env=environment,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        cli_log = root / "cli"
        cli_log.mkdir(parents=True, exist_ok=True)
        (cli_log / f"{label}.command").write_text(
            json.dumps(command, indent=2) + "\n",
            encoding="utf-8",
        )
        (cli_log / f"{label}.stdout").write_text(result.stdout, encoding="utf-8")
        (cli_log / f"{label}.stderr").write_text(result.stderr, encoding="utf-8")
        if result.returncode != 0:
            raise AssertionError(
                f"CLI {label} failed with exit code {result.returncode}\n"
                f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}",
            )
        try:
            return [json.loads(line) for line in result.stdout.splitlines() if line.strip()]
        except json.JSONDecodeError as error:
            raise AssertionError(f"CLI {label} did not emit JSON lines") from error

    @staticmethod
    def _payload(
        payloads: list[dict[str, Any]],
        command: str,
    ) -> dict[str, Any]:
        matches = [payload for payload in payloads if payload.get("command") == command]
        if not matches:
            raise AssertionError(f"CLI did not emit a {command!r} payload")
        return matches[-1]

    @staticmethod
    def _create_fixture(ffmpeg: str, destination: Path) -> None:
        result = _run(
            [
                ffmpeg,
                "-hide_banner",
                "-loglevel",
                "error",
                "-nostdin",
                "-y",
                "-f",
                "lavfi",
                "-i",
                "color=c=blue:size=64x36:rate=24:duration=0.5",
                "-f",
                "lavfi",
                "-i",
                "color=c=green:size=64x36:rate=24:duration=0.5",
                "-f",
                "lavfi",
                "-i",
                "color=c=red:size=64x36:rate=24:duration=0.5",
                "-f",
                "lavfi",
                "-i",
                "sine=frequency=440:sample_rate=48000:duration=0.5",
                "-f",
                "lavfi",
                "-i",
                "sine=frequency=660:sample_rate=48000:duration=0.5",
                "-f",
                "lavfi",
                "-i",
                "sine=frequency=550:sample_rate=48000:duration=0.5",
                "-f",
                "lavfi",
                "-i",
                "sine=frequency=880:sample_rate=48000:duration=0.5",
                "-f",
                "lavfi",
                "-i",
                "sine=frequency=1320:sample_rate=48000:duration=0.5",
                "-f",
                "lavfi",
                "-i",
                "sine=frequency=1100:sample_rate=48000:duration=0.5",
                "-filter_complex",
                "[0:v][1:v][2:v]concat=n=3:v=1:a=0[v];"
                "[3:a][4:a][5:a]concat=n=3:v=0:a=1[left];"
                "[6:a][7:a][8:a]concat=n=3:v=0:a=1[right];"
                "[left][right]amerge=inputs=2[a]",
                "-map",
                "[v]",
                "-map",
                "[a]",
                "-t",
                "1.5",
                "-c:v",
                "libx264",
                "-preset",
                "ultrafast",
                "-g",
                "12",
                "-pix_fmt",
                "yuv420p",
                "-c:a",
                "aac",
                "-b:a",
                "96k",
                "-ar",
                "48000",
                "-ac",
                "2",
                "-movflags",
                "+faststart",
                str(destination),
            ],
            timeout=120.0,
        )
        if result.returncode != 0:
            raise AssertionError(
                f"Could not create generated media fixture: "
                f"{result.stderr.decode(errors='replace')}",
            )

    @staticmethod
    def _create_ffmpeg_wrapper(root: Path) -> Path:
        wrapper = root / "ffmpeg-wrapper.py"
        wrapper.write_text(
            """#!/usr/bin/env python3
import json
import os
import subprocess
import sys
from pathlib import Path

log_path = Path(os.environ["FRAMESTUDIO_TICKET104_FFMPEG_LOG"])
log_path.parent.mkdir(parents=True, exist_ok=True)
with log_path.open("a", encoding="utf-8") as stream:
    stream.write(json.dumps({"argv": sys.argv[1:]}, sort_keys=True) + "\\n")
    stream.flush()
completed = subprocess.run([os.environ["FRAMESTUDIO_TICKET104_REAL_FFMPEG"], *sys.argv[1:]])
raise SystemExit(completed.returncode)
""",
            encoding="utf-8",
        )
        wrapper.chmod(0o755)
        return wrapper

    @staticmethod
    def _retain_artifacts(root: Path) -> Path | None:
        if ARTIFACT_PARENT is None:
            return None
        ARTIFACT_PARENT.mkdir(parents=True, exist_ok=True)
        retained = Path(
            tempfile.mkdtemp(
                prefix="verified-",
                dir=str(ARTIFACT_PARENT),
            ),
        )
        for relative in (
            "source.mp4",
            "edit.framestudio.json",
            "output.mp4",
            "ffmpeg-wrapper.jsonl",
            "integrity-result.json",
        ):
            source = root / relative
            if source.is_file():
                destination = retained / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, destination)
        cli_source = root / "cli"
        if cli_source.is_dir():
            shutil.copytree(cli_source, retained / "cli")
        return retained

    def _assert_audio_window(
        self,
        powers: dict[str, float],
        *,
        left_frequency: int,
        right_frequency: int,
        excluded_frequencies: tuple[int, ...] = (),
    ) -> None:
        left_distractors = (440, 550, 660, 880, 1100, 1320)
        right_distractors = (440, 550, 660, 880, 1100, 1320)
        left_key = f"left_{left_frequency}"
        right_key = f"right_{right_frequency}"
        for frequency in left_distractors:
            if frequency != left_frequency:
                self.assertGreater(
                    powers[left_key],
                    powers[f"left_{frequency}"] * 2.0,
                )
        for frequency in right_distractors:
            if frequency != right_frequency:
                self.assertGreater(
                    powers[right_key],
                    powers[f"right_{frequency}"] * 2.0,
                )
        for frequency in excluded_frequencies:
            self.assertGreater(
                powers[left_key],
                powers[f"left_{frequency}"] * 100.0,
            )
            self.assertGreater(
                powers[right_key],
                powers[f"right_{frequency}"] * 100.0,
            )

    def _measure_audio_windows(
        self,
        ffmpeg: str,
        media: Path,
        windows: tuple[tuple[str, float, int, int], ...],
        *,
        excluded_frequencies: tuple[int, ...] = (),
    ) -> dict[str, dict[str, float]]:
        measurements: dict[str, dict[str, float]] = {}
        for name, start_seconds, left_frequency, right_frequency in windows:
            left_channel, right_channel = _decode_audio_channels(
                ffmpeg,
                media,
                start_seconds=start_seconds,
                duration_seconds=0.2,
            )
            self.assertGreater(len(left_channel), 6_000)
            self.assertEqual(len(left_channel), len(right_channel))
            powers = _tone_powers(left_channel, right_channel)
            self._assert_audio_window(
                powers,
                left_frequency=left_frequency,
                right_frequency=right_frequency,
                excluded_frequencies=excluded_frequencies,
            )
            measurements[name] = powers
        return measurements

    def test_real_cli_adaptive_grouped_export_preserves_route_and_output_contract(self):
        ffmpeg = shutil.which("ffmpeg")
        ffprobe = shutil.which("ffprobe")
        if ffmpeg is None or ffprobe is None:
            self.fail("FFmpeg and ffprobe are required for TICKET-104 functionality evidence")

        runtime_parent = ARTIFACT_PARENT or REPOSITORY_ROOT
        runtime_parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(
            prefix="runtime-",
            dir=str(runtime_parent),
        ) as temporary_directory:
            root = Path(temporary_directory)
            environment = self._subprocess_environment(root)
            environment["FRAMESTUDIO_TICKET104_REAL_FFMPEG"] = ffmpeg
            source = root / "source.mp4"
            project = root / "edit.framestudio.json"
            output = root / "output.mp4"
            wrapper = self._create_ffmpeg_wrapper(root)
            self._create_fixture(ffmpeg, source)
            source_hash_before = _sha256(source)

            imported = self._run_cli(
                root,
                environment,
                "import",
                "import",
                str(source),
                "--project",
                str(project),
                "--ffprobe",
                ffprobe,
            )
            imported_project = self._payload(imported, "import")
            project_id = imported_project["project"]["project_id"]

            self._run_cli(
                root,
                environment,
                "split-050",
                "split",
                str(project),
                "--at",
                "0.5",
            )
            self._run_cli(
                root,
                environment,
                "split-100",
                "split",
                str(project),
                "--at",
                "1.0",
            )
            inspected_before_delete = self._payload(
                self._run_cli(root, environment, "inspect-before-delete", "inspect", str(project)),
                "inspect",
            )
            before_delete_segments = inspected_before_delete["project"]["timeline"]["segments"]
            self.assertEqual(len(before_delete_segments), 3)
            self.assertEqual(
                [
                    (segment["start_seconds"], segment["end_seconds"], segment["deleted"])
                    for segment in before_delete_segments
                ],
                [
                    (0.0, 0.5, False),
                    (0.5, 1.0, False),
                    (1.0, 1.5, False),
                ],
            )
            deleted_segment_id = before_delete_segments[1]["segment_id"]
            self._run_cli(
                root,
                environment,
                "delete",
                "delete",
                str(project),
                "--segment",
                deleted_segment_id,
            )
            inspected = self._payload(
                self._run_cli(root, environment, "inspect", "inspect", str(project)),
                "inspect",
            )
            inspected_project = inspected["project"]
            self.assertEqual(inspected_project["project_id"], project_id)
            segments = inspected_project["timeline"]["segments"]
            self.assertEqual(
                [
                    (segment["start_seconds"], segment["end_seconds"], segment["deleted"])
                    for segment in segments
                ],
                [
                    (0.0, 0.5, False),
                    (0.5, 1.0, True),
                    (1.0, 1.5, False),
                ],
            )
            self.assertAlmostEqual(
                inspected_project["timeline"]["edited_duration_seconds"],
                1.0,
            )
            project_hash_before_export = _sha256(project)

            plan_payloads = self._run_cli(
                root,
                environment,
                "export-plan",
                "export-plan",
                str(project),
                "--output",
                str(output),
                "--fps-choice",
                "60",
                "--enhance-fps",
                "--fps-backend",
                "ffmpeg-minterpolate",
                "--no-upscale-enhancement",
                "--ffprobe",
                ffprobe,
            )
            plan_result = self._payload(plan_payloads, "export-plan")
            plan = plan_result["export"]["plan"]
            self.assertEqual(plan["route"], "enhanced")
            self.assertEqual(plan["frame_rate_policy"]["backend"], "ffmpeg-minterpolate")
            self.assertEqual(plan["frame_rate_policy"]["target_rate"], "60")
            self.assertEqual(plan["output_policy"]["width"], 1920)
            self.assertEqual(plan["output_policy"]["height"], 1080)
            self.assertEqual(plan["output_policy"]["video_codec"], "libx264")
            self.assertEqual(plan["output_policy"]["audio_codec"], "aac")
            self.assertEqual(plan["output_policy"]["audio_sample_rate"], 48000)
            self.assertEqual(plan["output_policy"]["audio_channels"], 2)
            self.assertEqual(plan["output_policy"]["pixel_format"], "yuv420p")
            self.assertEqual(plan["output_policy"]["container"], "mp4")
            self.assertEqual(
                [
                    (segment["start_seconds"], segment["end_seconds"])
                    for segment in plan["segments"]
                ],
                [(0.0, 0.5), (1.0, 1.5)],
            )
            self.assertTrue(plan["rate_decisions"][0]["eligible"])
            self.assertEqual(plan["rate_decisions"][0]["action"], "interpolate")
            self.assertEqual(plan["rate_decisions"][0]["source_rate"], "24")
            self.assertEqual(plan["rate_decisions"][0]["target_rate"], "60")

            export_payloads = self._run_cli(
                root,
                environment,
                "export",
                "export",
                str(project),
                "--output",
                str(output),
                "--fps-choice",
                "60",
                "--enhance-fps",
                "--fps-backend",
                "ffmpeg-minterpolate",
                "--no-upscale-enhancement",
                "--ffmpeg",
                str(wrapper),
                "--ffprobe",
                ffprobe,
                "--human-progress",
            )
            export_result = self._payload(export_payloads, "export")
            progress_stages = [
                payload["progress"]["stage"]
                for payload in export_payloads
                if payload.get("command") == "export.progress"
            ]
            self.assertIn("normalizing source run", progress_stages)
            self.assertIn("interpolation segment 1/2", progress_stages)
            self.assertIn("interpolation segment 2/2", progress_stages)
            self.assertEqual(export_result["export"]["route"], "enhanced")
            self.assertTrue(export_result["export"]["verified"])
            self.assertEqual(export_result["export"]["session"]["mode"], "fresh")
            self.assertEqual(export_result["export"]["output"]["frame_rate"], "60/1")
            self.assertEqual(export_result["export"]["output"]["width"], 1920)
            self.assertEqual(export_result["export"]["output"]["height"], 1080)
            self.assertEqual(export_result["export"]["output"]["video_codec"], "h264")
            self.assertEqual(export_result["export"]["output"]["audio_codec"], "aac")

            self.assertTrue(output.is_file())
            self.assertGreater(output.stat().st_size, 0)
            source_hash_after = _sha256(source)
            project_hash_after = _sha256(project)
            self.assertEqual(source_hash_after, source_hash_before)
            self.assertEqual(project_hash_after, project_hash_before_export)
            self.assertEqual(export_result["project"]["project_id"], project_id)

            output_probe = _probe(ffprobe, output)
            video_stream = next(
                stream for stream in output_probe["streams"] if stream["codec_type"] == "video"
            )
            audio_stream = next(
                stream for stream in output_probe["streams"] if stream["codec_type"] == "audio"
            )
            output_format = output_probe["format"]
            self.assertEqual(video_stream["width"], 1920)
            self.assertEqual(video_stream["height"], 1080)
            self.assertEqual(video_stream["avg_frame_rate"], "60/1")
            self.assertEqual(video_stream["nb_read_frames"], "60")
            self.assertEqual(video_stream["codec_name"], "h264")
            self.assertEqual(video_stream["pix_fmt"], "yuv420p")
            self.assertEqual(audio_stream["codec_name"], "aac")
            self.assertEqual(audio_stream["sample_rate"], "48000")
            self.assertEqual(audio_stream["channels"], 2)
            self.assertIn("mp4", output_format["format_name"])
            self.assertAlmostEqual(float(output_format["duration"]), 1.0, delta=0.08)

            decoded = _run(
                [
                    ffmpeg,
                    "-hide_banner",
                    "-loglevel",
                    "error",
                    "-nostdin",
                    "-i",
                    str(output),
                    "-map",
                    "0:v:0",
                    "-map",
                    "0:a:0",
                    "-f",
                    "null",
                    "-",
                ],
            )
            self.assertEqual(decoded.returncode, 0, decoded.stderr.decode(errors="replace"))

            rgba_samples = {
                str(frame): _sample_rgba(ffmpeg, output, frame) for frame in (0, 29, 30, 59)
            }
            blue = rgba_samples["29"]
            red = rgba_samples["30"]
            self.assertGreater(blue[2], 180)
            self.assertLess(blue[0], 80)
            self.assertLess(blue[1], 100)
            self.assertGreater(red[0], 180)
            self.assertLess(red[1], 80)
            self.assertLess(red[2], 80)
            for sample in rgba_samples.values():
                self.assertEqual(sample[3], 255)
                self.assertGreater(max(sample[0], sample[2]), sample[1] + 40)

            source_audio_windows = self._measure_audio_windows(
                ffmpeg,
                source,
                (
                    ("blue", 0.12, 440, 880),
                    ("green", 0.62, 660, 1320),
                    ("red", 1.12, 550, 1100),
                ),
            )
            output_audio_windows = self._measure_audio_windows(
                ffmpeg,
                output,
                (
                    ("first-retained-blue", 0.12, 440, 880),
                    ("second-retained-red", 0.62, 550, 1100),
                ),
                excluded_frequencies=(660, 1320),
            )
            output_audio_green_ratios = {
                "first-retained-blue": {
                    "left_440_over_left_660": _power_ratio(
                        output_audio_windows["first-retained-blue"],
                        "left_440",
                        "left_660",
                    ),
                    "right_880_over_right_1320": _power_ratio(
                        output_audio_windows["first-retained-blue"],
                        "right_880",
                        "right_1320",
                    ),
                },
                "second-retained-red": {
                    "left_550_over_left_660": _power_ratio(
                        output_audio_windows["second-retained-red"],
                        "left_550",
                        "left_660",
                    ),
                    "right_1100_over_right_1320": _power_ratio(
                        output_audio_windows["second-retained-red"],
                        "right_1100",
                        "right_1320",
                    ),
                },
            }

            wrapper_log = [
                json.loads(line)
                for line in (root / "ffmpeg-wrapper.jsonl").read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            grouped_commands = [
                entry["argv"]
                for entry in wrapper_log
                if (
                    "-filter_complex" in entry["argv"]
                    and any("run-0-segment-0-prepared.mp4" in item for item in entry["argv"])
                    and any("run-0-segment-1-prepared.mp4" in item for item in entry["argv"])
                )
            ]
            self.assertEqual(len(grouped_commands), 1)

            partials = list(root.glob(f".{output.name}.partial-*"))
            self.assertEqual(partials, [])
            self.assertFalse(session_root(output).exists())
            self.assertFalse(
                (output.parent / f".{output.name}.framestudio-intermediates").exists(),
            )

            summary = {
                "source_sha256": source_hash_before,
                "project_sha256": project_hash_before_export,
                "output_sha256": _sha256(output),
                "output_metadata": {
                    "duration": float(output_format["duration"]),
                    "frames": int(video_stream["nb_read_frames"]),
                    "width": video_stream["width"],
                    "height": video_stream["height"],
                    "frame_rate": video_stream["avg_frame_rate"],
                    "video_codec": video_stream["codec_name"],
                    "pixel_format": video_stream["pix_fmt"],
                    "audio_codec": audio_stream["codec_name"],
                    "audio_sample_rate": int(audio_stream["sample_rate"]),
                    "audio_channels": audio_stream["channels"],
                },
                "rgba_samples": rgba_samples,
                "source_audio_windows": source_audio_windows,
                "output_audio_windows": output_audio_windows,
                "output_audio_green_power_ratios": output_audio_green_ratios,
                "grouped_command_count": len(grouped_commands),
                "backend": "ffmpeg-minterpolate",
                "route": "enhanced",
                "verified": True,
            }
            (root / "integrity-result.json").write_text(
                json.dumps(summary, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            retained = self._retain_artifacts(root)
            if retained is not None:
                self.assertTrue(retained.is_dir())
