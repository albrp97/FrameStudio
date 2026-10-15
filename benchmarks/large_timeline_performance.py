"""Measure synthetic 40-hour timeline metadata, not 40 hours of encoded media.

Run under the session's exclusive benchmark flock. --gtk additionally exercises
real GTK scroll, playhead, and generated-media texture delivery on the display.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import statistics
import subprocess
import sys
import tempfile
import threading
import time
from functools import partial
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import cairo

from framestudio.model import Segment, SegmentTimeline
from framestudio.model_timeline import TimelineTrack
from framestudio.timeline import create_timeline_canvas
from framestudio.timeline_geometry import TimelineClipGeometry, layout_timeline_segments


def require_executable(name: str) -> str:
    executable = shutil.which(name)
    if executable is None:
        raise RuntimeError(f"{name} is required for this benchmark operation")
    return executable


def make_timeline(count: int) -> SegmentTimeline:
    duration = 40 * 3600.0
    step = duration / count
    blocks = tuple(
        Segment(
            segment_id=f"segment-{index}",
            start_seconds=0.0,
            end_seconds=step,
            source_id=f"source-{index % 200}",
            timeline_start_seconds=index * step,
            timeline_end_seconds=(index + 1) * step,
            track_id="track-1",
        )
        for index in range(count)
    )
    return SegmentTimeline.from_tracks(
        (TimelineTrack("track-1", blocks),),
        source_durations={f"source-{index}": 720.0 for index in range(200)},
    )


def summary(samples: list[float]) -> dict:
    ordered = sorted(samples)
    return {
        "p50_ms": statistics.median(ordered),
        "p95_ms": ordered[min(len(ordered) - 1, int(len(ordered) * 0.95))],
        "samples": len(ordered),
        "samples_ms": samples,
    }


def measure(callback, repeats: int) -> dict:
    samples = []
    for _ in range(repeats):
        started = time.perf_counter()
        callback()
        samples.append((time.perf_counter() - started) * 1000)
    return summary(samples)


def gtk_modules():
    import gi

    gi.require_foreign("cairo")
    gi.require_version("Gtk", "4.0")
    gi.require_version("Gdk", "4.0")
    from gi.repository import Gdk, GLib, Gtk

    if not Gtk.init_check():
        raise RuntimeError("A working GTK display is required")
    return Gtk, Gdk, GLib


def drain(GLib, seconds=0.05):
    deadline = time.monotonic() + seconds
    context = GLib.MainContext.default()
    while time.monotonic() < deadline:
        while context.pending():
            context.iteration(False)
        time.sleep(0.001)


def install_candidate(canvas, candidate):
    """Isolated experiments, deliberately not used by production code."""
    if candidate == "cached-layout":
        import framestudio.timeline as timeline_module

        original = timeline_module.layout_timeline_segments
        cache: dict[tuple[int, int, float, float], tuple[TimelineClipGeometry, ...]] = {}

        def cached(timeline, width, zoom):
            key = (id(timeline), timeline.revision, width, zoom)
            if key not in cache:
                cache.clear()
                cache[key] = original(timeline, width, zoom)
            return cache[key]

        timeline_module.layout_timeline_segments = cached
        return lambda: setattr(timeline_module, "layout_timeline_segments", original)
    if candidate == "viewport-cull":
        original_draw = canvas._draw
        original_clip = canvas._draw_clip

        def draw(area, context, width, height):
            parent = canvas.get_parent()
            context.save()
            if parent is not None and hasattr(parent, "get_hadjustment"):
                context.rectangle(
                    parent.get_hadjustment().get_value(),
                    parent.get_vadjustment().get_value(),
                    parent.get_width(),
                    parent.get_height(),
                )
                context.clip()
            original_draw(area, context, width, height)
            context.restore()

        def clip(context, geometry):
            left, top, right, bottom = context.clip_extents()
            if (
                geometry.end_x + 12 >= left
                and geometry.x - 12 <= right
                and geometry.end_y + 12 >= top
                and geometry.y - 12 <= bottom
            ):
                original_clip(context, geometry)

        canvas._draw = draw
        canvas._draw_clip = clip
    return lambda: None


def baseline_canvas_factory(ref):
    """Load only owned rendering files from a trusted local Git baseline."""
    with tempfile.TemporaryDirectory(prefix="framestudio-baseline-") as directory:
        for name in ("timeline_rendering", "timeline"):
            source = subprocess.run(
                [require_executable("git"), "show", f"{ref}:framestudio/{name}.py"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout
            path = Path(directory) / f"{name}.py"
            path.write_text(source)
            module_name = f"framestudio.{name}"
            spec = importlib.util.spec_from_file_location(module_name, path)
            if spec is None or spec.loader is None:
                raise RuntimeError(f"Cannot import the requested baseline module {name}")
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            setattr(sys.modules["framestudio"], name, module)
            spec.loader.exec_module(module)
    return sys.modules["framestudio.timeline"].create_timeline_canvas


def benchmark(counts, repeats, gtk=False, media=None, candidate=None, baseline_ref=None):
    Gtk, Gdk, GLib = gtk_modules()
    factory = (
        create_timeline_canvas if baseline_ref is None else baseline_canvas_factory(baseline_ref)
    )
    canvas_type = factory(Gtk)
    rows: list[dict[str, object]] = []
    results: dict[str, object] = {
        "metadata": {
            "source_count": 200,
            "timeline_hours": 40,
            "synthetic_metadata": True,
            "python": sys.version,
            "generated_media": None if media is None else media.name,
            "candidate": candidate,
            "baseline_ref": baseline_ref,
        },
        "scaling": rows,
    }
    for count in counts:
        timeline = make_timeline(count)
        canvas = canvas_type()
        canvas.set_timeline(timeline)
        canvas.set_viewport_width(1200)
        canvas.set_zoom(12)
        cleanup = install_candidate(canvas, candidate)
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 1200, 150)
        context = cairo.Context(surface)
        context.translate(-6000, 0)
        canvas._draw(None, context, 14136, 150)
        row: dict[str, object] = {
            "segments": count,
            "layout_uncached": measure(
                partial(layout_timeline_segments, timeline, 1200, 12), repeats
            ),
            "draw_scrolled": measure(partial(canvas._draw, None, context, 14136, 150), repeats),
            "playhead_update": measure(partial(canvas.set_playhead, 72000), repeats),
        }
        if gtk:
            row["gtk"] = benchmark_gtk(canvas, Gtk, Gdk, GLib, repeats, media)
        rows.append(row)
        cleanup()
    return results


def benchmark_gtk(canvas, Gtk, Gdk, GLib, repeats, media):
    from framestudio.app_playback import deliver_latest_frame, on_frame
    from framestudio.ffmpeg_playback import VideoFrame

    window = Gtk.Window()
    window.set_default_size(1200, 480)
    window.set_resizable(False)
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    preview = Gtk.Picture()
    preview.set_size_request(320, 180)
    box.append(preview)
    scroll = Gtk.ScrolledWindow()
    scroll.set_min_content_height(150)
    scroll.set_vexpand(True)
    scroll.set_child(canvas)
    box.append(scroll)
    window.set_child(box)
    draws = []
    extents = []

    def draw(area, context, width, height):
        started = time.perf_counter()
        extents.append(list(context.clip_extents()))
        canvas._draw(area, context, width, height)
        draws.append((time.perf_counter() - started) * 1000)

    canvas.set_draw_func(draw)
    window.present()
    drain(GLib, 0.15)
    adjustment = scroll.get_hadjustment()
    adjustment.set_value(6000)
    drain(GLib)
    playhead_viewport_dimensions = [scroll.get_width(), scroll.get_height()]
    draws.clear()
    for index in range(repeats):
        canvas.set_playhead(71000 + index / 30)
        drain(GLib, 0.025)
    playhead_draws = summary(draws)
    for index in range(4):
        adjustment.set_value(6000 + index * 200)
        canvas.set_viewport_width(1100 + index * 20)
        drain(GLib)
    texture_results = None
    if media is not None:
        data = subprocess.run(
            [
                require_executable("ffmpeg"),
                "-v",
                "error",
                "-i",
                str(media),
                "-frames:v",
                "1",
                "-vf",
                "scale=320:180",
                "-pix_fmt",
                "rgba",
                "-f",
                "rawvideo",
                "-",
            ],
            check=True,
            capture_output=True,
        ).stdout
        if len(data) != 320 * 180 * 4:
            raise RuntimeError("FFmpeg did not produce a complete benchmark video frame")
        frame_window = SimpleNamespace(
            _frame_lock=threading.Lock(),
            _latest_frame=None,
            _frame_delivery_scheduled=False,
            _playback_generation=1,
            preview=preview,
        )
        frame_window._deliver_latest_frame = lambda: deliver_latest_frame(frame_window, Gdk, GLib)

        def deliver():
            on_frame(frame_window, VideoFrame(data, 320, 180, 1.0), GLib, 1)
            drain(GLib, 0.002)

        texture_results = measure(deliver, repeats)
        if preview.get_paintable() is None:
            raise RuntimeError("The benchmark video frame was not delivered to the GTK preview")
    viewport_dimensions = [scroll.get_width(), scroll.get_height()]
    window.destroy()
    drain(GLib)
    return {
        "playhead_draw": playhead_draws,
        "draw_count_including_viewport_updates": len(draws),
        "cairo_clip_extents_at_scroll": extents[-1],
        "texture_delivery_with_2ms_event_pump": texture_results,
        "playhead_seconds": canvas.get_playhead_seconds(),
        "horizontal_scroll": adjustment.get_value(),
        "texture_dimensions": [320, 180],
        "viewport_dimensions": viewport_dimensions,
        "playhead_viewport_dimensions": playhead_viewport_dimensions,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--counts", type=int, nargs="+", default=[200, 2000, 10000])
    parser.add_argument("--repeats", type=int, default=30)
    parser.add_argument("--gtk", action="store_true")
    parser.add_argument("--media", type=Path)
    parser.add_argument("--candidate", choices=["cached-layout", "viewport-cull"])
    parser.add_argument(
        "--baseline-ref", help="Trusted local Git commit for rendering-only comparison"
    )
    args = parser.parse_args()
    args.output.write_text(
        json.dumps(
            benchmark(
                args.counts, args.repeats, args.gtk, args.media, args.candidate, args.baseline_ref
            ),
            indent=2,
        )
        + "\n"
    )


if __name__ == "__main__":
    main()
