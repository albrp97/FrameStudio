#!/usr/bin/env python3
"""Write a VapourSynth output node as YUV4MPEG2 for an FFmpeg pipeline."""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import vapoursynth as vs


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render a VapourSynth script to YUV4MPEG2 on stdout."
    )
    parser.add_argument("script", type=Path, help="VapourSynth .vpy script")
    return parser.parse_args()


def main() -> int:
    arguments = parse_arguments()
    script_path = arguments.script.expanduser().resolve()
    vs.clear_outputs()
    with script_path.open("rb") as handle:
        namespace = {
            "__file__": str(script_path),
            "__name__": "__vapoursynth__",
        }
        exec(compile(handle.read(), str(script_path), "exec"), namespace)

    output = vs.get_output(0)
    clip = output.clip
    if clip.format is None or clip.format.num_planes != 3:
        raise RuntimeError("The VapourSynth output must be planar YUV.")
    if clip.format.name != "YUV420P10":
        raise RuntimeError(
            f"Expected YUV420P10 output, got {clip.format.name}."
        )

    header = (
        f"YUV4MPEG2 W{clip.width} H{clip.height} "
        f"F{clip.fps_num}:{clip.fps_den} Ip A1:1 "
        "C420p10 XYSCSS=420JPEG XCOLORRANGE=LIMITED\n"
    ).encode("ascii")
    output_stream = sys.stdout.buffer
    output_stream.write(header)

    started = time.monotonic()
    for frame_number in range(clip.num_frames):
        frame = clip.get_frame(frame_number)
        output_stream.write(b"FRAME\n")
        for plane_number in range(frame.format.num_planes):
            output_stream.write(frame[plane_number].tobytes())
        if frame_number == 0 or (frame_number + 1) % 100 == 0:
            elapsed = time.monotonic() - started
            print(
                f"frame={frame_number + 1}/{clip.num_frames} "
                f"elapsed={elapsed:.2f}s",
                file=sys.stderr,
                flush=True,
            )
    output_stream.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
