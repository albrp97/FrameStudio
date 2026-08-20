import math
import os

import vapoursynth as vs
from vsrife import rife


core = vs.core
core.std.LoadPlugin(os.environ["BESTSOURCE_PLUGIN"])

clip = core.bs.VideoSource(os.environ["SOURCE"])
limit_seconds = float(os.environ.get("LIMIT_SECONDS", "0"))
if limit_seconds > 0 and clip.fps > 0:
    clip = clip[: math.ceil(limit_seconds * clip.fps)]

target_frames = int(os.environ.get("TARGET_FRAMES", "0"))
boundary_frames = {
    int(value)
    for value in os.environ.get("BOUNDARIES", "").split(",")
    if value.strip()
}
target_fps_num = int(os.environ.get("TARGET_FPS_NUM", "60"))
target_fps_den = int(os.environ.get("TARGET_FPS_DEN", "1"))

input_format = (
    vs.RGBH if os.environ.get("INPUT_FORMAT", "RGBS") == "RGBH" else vs.RGBS
)
clip = clip.resize.Bicubic(
    format=input_format,
    matrix_in_s="709",
    range_in_s=os.environ.get("RANGE_IN", "limited"),
)
scene_clip = clip.resize.Bicubic(format=vs.GRAY8, matrix_s="709")
scene_next = scene_clip[1:] + scene_clip[-1]
scene_stats = scene_next.std.PlaneStats(scene_clip)


def mark_scene_change(n, f):
    output = f[0].copy()
    output.props["_SceneChangeNext"] = int(
        float(f[1].props.get("PlaneStatsDiff", 0.0)) > 0.15
        or n + 1 in boundary_frames
    )
    return output


clip = clip.std.ModifyFrame([clip, scene_stats], mark_scene_change)
clip = rife(
    clip,
    model=os.environ["MODEL"],
    auto_download=True,
    fps_num=target_fps_num,
    fps_den=target_fps_den,
    scale=float(os.environ.get("SCALE", "1.0")),
    sc=True,
    sc_threshold=None,
    trt=os.environ.get("USE_TRT", "1") != "0",
    trt_static_shape=True,
    trt_cache_dir=os.environ["TRT_CACHE"],
)
clip = clip.resize.Bicubic(format=vs.YUV420P10, matrix_s="709")
if target_frames > 0:
    clip = clip[:target_frames]
clip.set_output()
