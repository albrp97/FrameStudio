from __future__ import annotations

import shutil
import subprocess
import unittest
from dataclasses import replace
from fractions import Fraction
from pathlib import Path
from unittest.mock import patch

from framestudio.media import probe_media
from framestudio.model import Project, TriplicateGroup, VisualTransform
from framestudio.upscale_policy import UpscalePolicy
from framestudio.video_compositor import (
    _build_render_command,
    _PreparedAsset,
    plan_project_video,
)
from tests.test_editor_layout_plan_functionality import make_block
from tests.test_editor_video_compositor import _fake_probe
from tests.test_editor_video_compositor_functionality import isolated_directory


def _project(source: Path, *, zoom: float = 1.25, triplicate: bool = True) -> Project:
    project = Project.create_synchronized(
        source,
        {
            "duration_seconds": 0.8,
            "width": 160,
            "height": 96,
            "frame_rate": "30000/1001",
        },
        project_id="triplicate-factoring-experiment",
    )
    transform = VisualTransform(zoom=zoom, offset_x=123.0, offset_y=-47.0 if zoom > 1 else 0.0)
    group = TriplicateGroup.create(transform) if triplicate else None
    step = 0.167
    for index in range(1, 5):
        track = f"track-{index}"
        if index > 1:
            project.timeline.add_track(track)
        start = step * index
        blocks = [
            make_block(
                segment_id=f"block-{index}",
                source_id=project.source.source_id,
                track_id=track,
                source_start=0.12,
                source_end=0.12 + step * 5 - start,
                timeline_start=start,
                timeline_end=step * 5,
                visual_transform=transform,
                triplicate=group if index == 1 else None,
            ),
        ]
        if index == 1:
            blocks.append(
                make_block(
                    segment_id="repeated",
                    source_id=project.source.source_id,
                    track_id=track,
                    source_start=0.20,
                    source_end=0.20 + step,
                    timeline_start=step * 6,
                    timeline_end=step * 7,
                    visual_transform=transform,
                    triplicate=TriplicateGroup.create(transform) if triplicate else None,
                ),
            )
        project.timeline.replace_track_blocks(track, tuple(blocks))
    project.duration_seconds = project.timeline.timeline_duration_seconds
    project.validate()
    return project


def _graph(command: list[str]) -> str:
    return command[command.index("-filter_complex") + 1]


class TriplicateFactoringGraphTests(unittest.TestCase):
    def setUp(self):
        source = Path(__file__).resolve()
        project = _project(source)
        probe = _fake_probe(
            project.source.source_id,
            source,
            width=160,
            height=96,
            frame_rate="30000/1001",
            sar=(16, 15),
        )
        with patch("framestudio.video_compositor._probe_source", return_value=probe):
            self.plan = plan_project_video(
                project,
                source.with_name("factoring-output.mp4"),
                target_rate=Fraction(30_000, 1_001),
                upscale_policy=UpscalePolicy(enhancement_enabled=False),
            )

    def command(self, plan=None, assets=None, **kwargs):
        return _build_render_command(
            plan or self.plan,
            assets or {},
            output=Path("factoring-output.mp4"),
            ffmpeg_path="ffmpeg",
            **kwargs,
        )

    def test_composition_budget_requires_three_distinct_actual_input_paths(self):
        automatic_command = self.command()
        encoder_options = automatic_command[automatic_command.index("-map") :]
        for distinct_paths in (1, 2, 3, 4):
            assets = {
                block.block_id: _PreparedAsset(
                    Path(f"prepared-{index % distinct_paths}.mkv"),
                    fps_converted=False,
                )
                for index, block in enumerate(self.plan.layout_plan.included_blocks)
            }
            assets["unused-block"] = _PreparedAsset(Path("unused.mkv"), fps_converted=False)
            for reuse_inputs in (False, True):
                with self.subTest(distinct_paths=distinct_paths, reuse_inputs=reuse_inputs):
                    command = self.command(assets=assets, reuse_inputs=reuse_inputs)
                    inputs = [index for index, option in enumerate(command) if option == "-i"]
                    self.assertEqual(
                        len({command[index + 1] for index in inputs}),
                        distinct_paths,
                    )
                    if distinct_paths >= 3:
                        budget = command.index("-filter_complex_threads")
                        self.assertLess(budget, inputs[0])
                        self.assertEqual(command[budget + 1], "2")
                        self.assertEqual(command.count("-threads"), len(inputs))
                        for index in inputs:
                            self.assertEqual(command[index - 2 : index], ["-threads", "1"])
                    else:
                        self.assertNotIn("-filter_complex_threads", command)
                        self.assertNotIn("-threads", command)
                    self.assertEqual(command[command.index("-map") :], encoder_options)
                    self.assertNotIn("-threads", command[inputs[-1] + 2 :])

    def test_default_factors_identical_scale_and_format_before_triplicate_split(self):
        legacy = self.command(factor_triplicate=False)
        factored = self.command()
        old_graph, graph = _graph(legacy), _graph(factored)
        triplicate_slots = [
            slot
            for interval in self.plan.layout_plan.intervals
            for slot in interval.slots
            if slot.is_triplicate
        ]
        self.assertTrue(triplicate_slots)
        self.assertEqual(
            old_graph.count("scale=") - graph.count("scale="),
            2 * len(triplicate_slots),
        )
        self.assertEqual(old_graph.count("crop="), graph.count("crop="))
        self.assertEqual(
            legacy[: legacy.index("-filter_complex")],
            factored[: factored.index("-filter_complex")],
        )
        self.assertEqual(
            legacy[legacy.index("-map") :],
            factored[factored.index("-map") :],
        )
        for old_chain, chain in zip(old_graph.split(";"), graph.split(";"), strict=True):
            if "split=3" in chain:
                self.assertIn("setsar=1,scale=", chain)
                self.assertIn(":flags=lanczos,format=yuv444p,split=3", chain)
                self.assertEqual(old_chain.split("setsar=1,")[0], chain.split("setsar=1,")[0])
            elif "split" in chain.split("]")[0]:
                self.assertNotIn("scale=", chain)
                self.assertIn("crop=", chain)
            else:
                self.assertEqual(old_chain, chain)
        self.assertTrue(
            any(
                tuple(crop.target.width for crop in slot.triplicate_crops) == (213, 214, 213)
                for slot in triplicate_slots
            )
        )

    def test_prepared_fps_ready_assets_keep_sampling_and_do_not_add_fps(self):
        assets = {
            block.block_id: _PreparedAsset(Path("prepared.mkv"), fps_converted=True)
            for block in self.plan.layout_plan.included_blocks
        }
        legacy = _graph(self.command(assets=assets, factor_triplicate=False))
        candidate = _graph(self.command(assets=assets))
        self.assertNotIn("fps=", candidate)
        self.assertEqual(
            [part.split("setsar=1,")[0] for part in legacy.split(";") if "trim=start=" in part],
            [part.split("setsar=1,")[0] for part in candidate.split(";") if "trim=start=" in part],
        )
        self.assertIn("trim=start=0.000000000", candidate)
        self.assertLess(candidate.count("scale="), legacy.count("scale="))

    def test_different_scale_dimensions_retain_legacy_branches(self):
        intervals = []
        for interval in self.plan.layout_plan.intervals:
            slots = []
            for slot in interval.slots:
                if slot.is_triplicate:
                    crops = slot.triplicate_crops
                    slot = replace(
                        slot,
                        triplicate_crops=(
                            replace(crops[0], scaled_width=crops[0].scaled_width + 2),
                            *crops[1:],
                        ),
                    )
                slots.append(slot)
            intervals.append(replace(interval, slots=tuple(slots)))
        plan = replace(
            self.plan,
            layout_plan=replace(self.plan.layout_plan, intervals=tuple(intervals)),
        )
        self.assertEqual(self.command(plan), self.command(plan, factor_triplicate=False))

    def test_nontriplicate_graph_is_unchanged(self):
        intervals = tuple(
            replace(
                interval,
                slots=tuple(
                    replace(slot, crop=slot.triplicate_crops[0], triplicate_crops=())
                    if slot.is_triplicate
                    else slot
                    for slot in interval.slots
                ),
            )
            for interval in self.plan.layout_plan.intervals
        )
        plan = replace(self.plan, layout_plan=replace(self.plan.layout_plan, intervals=intervals))
        self.assertEqual(self.command(plan), self.command(plan, factor_triplicate=False))


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg is required")
class TriplicateFactoringMediaTests(unittest.TestCase):
    def test_single_frame_layout_intervals_preserve_content_and_output_frame_lattice(self):
        self._assert_single_frame_layout_intervals(Fraction(30))

    def test_fractional_single_frame_layout_intervals_preserve_content_and_output_frame_lattice(
        self,
    ):
        self._assert_single_frame_layout_intervals(Fraction(30_000, 1_001))

    def test_fps_ready_vfr_preparations_preserve_content_and_output_frame_lattice(self):
        self._assert_single_frame_layout_intervals(Fraction(30_000, 1_001), prepared_vfr=True)

    def _assert_single_frame_layout_intervals(self, rate: Fraction, *, prepared_vfr: bool = False):
        def rows(command):
            result = subprocess.run(command, check=True, capture_output=True, text=True)
            return tuple(
                line.split(",")
                for line in result.stdout.splitlines()
                if line and not line.startswith("#")
            )

        with isolated_directory() as root:
            source = root / "zero-origin-bframes.mkv"
            subprocess.run(
                [
                    "ffmpeg",
                    "-hide_banner",
                    "-loglevel",
                    "error",
                    "-nostdin",
                    "-y",
                    "-f",
                    "lavfi",
                    "-i",
                    f"testsrc2=s=160x96:r={rate}:d=0.6",
                    "-vf",
                    "select='not(eq(mod(n,5),0))'" if prepared_vfr else "null",
                    "-fps_mode",
                    "vfr",
                    "-c:v",
                    "libx264",
                    "-preset",
                    "ultrafast",
                    "-g",
                    "300",
                    "-bf",
                    "3",
                    "-threads",
                    "1",
                    str(source),
                ],
                check=True,
                capture_output=True,
            )
            original = source.read_bytes()
            project = Project.create_synchronized(source, probe_media(source).metadata())
            for index in range(3):
                track = f"track-{index + 1}"
                if index:
                    project.timeline.add_track(track)
                start = index * 33_333 / 1_000_000
                project.timeline.replace_track_blocks(
                    track,
                    (
                        make_block(
                            segment_id=f"stagger-{index}",
                            source_id=project.source.source_id,
                            track_id=track,
                            source_start=0.0,
                            source_end=0.3,
                            timeline_start=start,
                            timeline_end=start + 0.3,
                        ),
                    ),
                )
            project.duration_seconds = project.timeline.timeline_duration_seconds
            output = root / "single-frame-intervals.mp4"
            plan = plan_project_video(
                project,
                output,
                target_rate=rate,
                upscale_policy=UpscalePolicy(enhancement_enabled=False),
            )
            self.assertEqual(plan.interval_frame_counts, (1, 1, 7, 1, 1))
            assets = {}
            if prepared_vfr:
                native = rows(
                    [
                        "ffmpeg",
                        "-hide_banner",
                        "-loglevel",
                        "error",
                        "-nostdin",
                        "-threads",
                        "1",
                        "-i",
                        str(source),
                        "-an",
                        "-fps_mode",
                        "passthrough",
                        "-f",
                        "framemd5",
                        "-",
                    ],
                )
                native_pts = [int(row[2]) for row in native]
                self.assertGreater(
                    len(
                        {
                            right - left
                            for left, right in zip(native_pts[:-1], native_pts[1:], strict=True)
                        }
                    ),
                    1,
                )
                prepared = root / "prepared-0.mkv"
                subprocess.run(
                    [
                        "ffmpeg",
                        "-hide_banner",
                        "-loglevel",
                        "error",
                        "-nostdin",
                        "-y",
                        "-threads",
                        "1",
                        "-i",
                        str(source),
                        "-vf",
                        f"trim=start=0:end=0.3,setpts=PTS-STARTPTS,fps={rate}",
                        "-an",
                        "-c:v",
                        "ffv1",
                        "-threads",
                        "1",
                        str(prepared),
                    ],
                    check=True,
                    capture_output=True,
                )
                for index in range(3):
                    path = root / f"prepared-{index}.mkv"
                    if index:
                        path.write_bytes(prepared.read_bytes())
                    assets[f"stagger-{index}"] = _PreparedAsset(path, fps_converted=True)
            command = _build_render_command(
                plan,
                assets,
                output=output,
                ffmpeg_path="ffmpeg",
                factor_triplicate=False,
            )
            if prepared_vfr:
                self.assertNotIn("fps=", _graph(command))
            if "-filter_complex_threads" not in command:
                command[1:1] = ["-threads", "1", "-filter_complex_threads", "1"]
            command[-1:-1] = ["-threads", "1"]
            raw_command = command[: command.index("-map")] + [
                "-map",
                "[vout]",
                "-an",
                "-fps_mode",
                "passthrough",
                "-threads",
                "1",
                "-f",
                "framemd5",
                "-",
            ]
            raw = rows(raw_command)
            self.assertEqual(len(raw), plan.expected_frames)
            self.assertEqual([int(row[2]) for row in raw], list(range(plan.expected_frames)))
            if prepared_vfr:
                serial_command = raw_command.copy()
                budget_index = serial_command.index("-filter_complex_threads") + 1
                self.assertEqual(serial_command[budget_index], "2")
                serial_command[budget_index] = "1"
                self.assertEqual(rows(serial_command), raw)

            legacy_command = raw_command.copy()
            graph_index = legacy_command.index("-filter_complex") + 1
            legacy_command[graph_index] = legacy_command[graph_index].replace(
                f",settb=expr={rate.denominator}/{rate.numerator},setpts=N",
                "",
            )
            legacy = rows(legacy_command)
            self.assertLess(len({int(row[2]) for row in legacy}), plan.expected_frames)
            self.assertEqual([row[-1] for row in legacy], [row[-1] for row in raw])

            subprocess.run(command, check=True, capture_output=True)
            decoded = rows(
                [
                    "ffmpeg",
                    "-hide_banner",
                    "-loglevel",
                    "error",
                    "-nostdin",
                    "-i",
                    str(output),
                    "-map",
                    "0:v",
                    "-fps_mode",
                    "passthrough",
                    "-f",
                    "framemd5",
                    "-",
                ]
            )
            self.assertEqual(len(decoded), plan.expected_frames)
            self.assertEqual([int(row[2]) for row in decoded], list(range(plan.expected_frames)))
            self.assertAlmostEqual(
                probe_media(output).duration_seconds,
                plan.expected_duration_seconds,
                delta=0.001,
            )
            self.assertEqual(source.read_bytes(), original)

    def test_experimental_original_pts_seek_matches_bframes_vfr_and_timestamp_offsets(self):
        def ffmpeg(arguments):
            return subprocess.run(
                [
                    "ffmpeg",
                    "-hide_banner",
                    "-loglevel",
                    "error",
                    "-nostdin",
                    "-y",
                    *arguments,
                ],
                check=True,
                capture_output=True,
            ).stdout

        def records(arguments):
            return tuple(
                line
                for line in ffmpeg([*arguments, "-fps_mode", "passthrough", "-f", "framemd5", "-"])
                .decode()
                .splitlines()
                if line and not line.startswith("#")
            )

        with isolated_directory() as root:
            for name, vfr, audio, shifted in (
                ("cfr", False, False, False),
                ("nonzero", False, False, True),
                ("vfr", True, False, False),
                ("vfr-nonzero", True, False, True),
                ("av-offset", False, True, False),
                ("av-offset-nonzero", False, True, True),
            ):
                with self.subTest(case=name):
                    source = root / f"{name}.mp4"
                    inputs = ["-itsoffset", "0.137"] if audio else []
                    inputs += [
                        "-f",
                        "lavfi",
                        "-i",
                        "testsrc2=s=160x96:r=30000/1001:d=8",
                    ]
                    if audio:
                        inputs += [
                            "-f",
                            "lavfi",
                            "-i",
                            "sine=frequency=331:sample_rate=48000:duration=8",
                            "-c:a",
                            "aac",
                        ]
                    ffmpeg(
                        [
                            *inputs,
                            "-vf",
                            "select='not(eq(mod(n,5),0))'" if vfr else "null",
                            "-fps_mode",
                            "vfr",
                            "-c:v",
                            "libx264",
                            "-preset",
                            "medium",
                            "-g",
                            "120",
                            "-bf",
                            "3",
                            "-x264-params",
                            "scenecut=0",
                            "-threads",
                            "1",
                            *(["-output_ts_offset", "2.75"] if shifted else []),
                            str(source),
                        ]
                    )
                    source_bytes = source.read_bytes()
                    raw, decoded = [], []
                    for seek in (False, True):
                        arguments = (
                            ["-ss", "7", "-noaccurate_seek", "-copyts", "-start_at_zero"]
                            if seek
                            else []
                        )
                        arguments += [
                            "-i",
                            str(source),
                            "-vf",
                            "trim=start=7.137000000:end=7.737000000,setpts=PTS-STARTPTS",
                            "-frames:v",
                            "18",
                            "-an",
                        ]
                        raw.append(records(arguments))
                        output = root / f"{name}-{seek}.mp4"
                        ffmpeg(
                            [
                                *arguments,
                                "-c:v",
                                "libx264",
                                "-preset",
                                "ultrafast",
                                "-pix_fmt",
                                "yuv420p",
                                "-threads",
                                "1",
                                str(output),
                            ]
                        )
                        decoded.append(records(["-i", str(output), "-map", "0:v"]))
                    self.assertTrue(raw[0])
                    self.assertEqual(raw[0], raw[1])
                    self.assertEqual(decoded[0], decoded[1])
                    self.assertEqual(len(raw[0]), len(decoded[0]))
                    self.assertEqual(source.read_bytes(), source_bytes)

    def test_ordered_decoded_frames_match_legacy_with_offsets_layouts_gaps_and_rational_fps(self):
        with isolated_directory() as root:
            source = root / "moving-sar.mkv"
            subprocess.run(
                [
                    "ffmpeg",
                    "-hide_banner",
                    "-loglevel",
                    "error",
                    "-nostdin",
                    "-y",
                    "-f",
                    "lavfi",
                    "-i",
                    "testsrc2=s=160x96:r=30000/1001:d=0.8",
                    "-vf",
                    "setsar=16/15",
                    "-an",
                    "-c:v",
                    "ffv1",
                    "-threads",
                    "1",
                    str(source),
                ],
                check=True,
                capture_output=True,
            )
            original = source.read_bytes()
            for zoom, target_rate, reuse_inputs in (
                (1.0, Fraction(30_000, 1_001), True),
                (1.25, Fraction(24_000, 1_001), False),
            ):
                with self.subTest(zoom=zoom, target_rate=target_rate, reuse_inputs=reuse_inputs):
                    project = _project(source, zoom=zoom)
                    plan = plan_project_video(
                        project,
                        root / "planned.mp4",
                        target_rate=target_rate,
                        upscale_policy=UpscalePolicy(enhancement_enabled=False),
                    )
                    self.assertEqual(
                        {len(interval.slots) for interval in plan.layout_plan.intervals},
                        {0, 1, 2, 3, 4},
                    )
                    self.assertEqual(plan.probed_metadata[0].sample_aspect_ratio, (16, 15))
                    decoded = []
                    for factor in (False, True):
                        output = root / f"{zoom}-{factor}.mp4"
                        command = _build_render_command(
                            plan,
                            {},
                            output=output,
                            ffmpeg_path="ffmpeg",
                            reuse_inputs=reuse_inputs,
                            factor_triplicate=factor,
                        )
                        command[1:1] = ["-filter_complex_threads", "1"]
                        command[-1:-1] = ["-threads", "1"]
                        subprocess.run(command, check=True, capture_output=True)
                        probe = probe_media(output)
                        self.assertEqual((probe.width, probe.height), (1920, 1080))
                        self.assertEqual(probe.frame_rate, str(target_rate))
                        self.assertFalse(probe.audio_stream_present)
                        self.assertAlmostEqual(
                            probe.duration_seconds,
                            plan.expected_duration_seconds,
                            delta=1 / float(target_rate) + 1e-6,
                        )
                        result = subprocess.run(
                            [
                                "ffmpeg",
                                "-hide_banner",
                                "-loglevel",
                                "error",
                                "-nostdin",
                                "-i",
                                str(output),
                                "-map",
                                "0:v",
                                "-fps_mode",
                                "passthrough",
                                "-f",
                                "framemd5",
                                "-",
                            ],
                            check=True,
                            capture_output=True,
                            text=True,
                        )
                        frames = tuple(
                            line
                            for line in result.stdout.splitlines()
                            if line and not line.startswith("#")
                        )
                        self.assertEqual(len(frames), plan.expected_frames)
                        self.assertGreater(len({line.rsplit(",", 1)[1] for line in frames}), 3)
                        decoded.append(frames)
                    self.assertEqual(decoded[0], decoded[1])
                    self.assertEqual(source.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
