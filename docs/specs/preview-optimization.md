# Preview and playback optimization

This document describes how FrameStudio's preview and playback path works now,
which optimizations are in place, which alternatives were measured and
rejected, and what remains unsolved. Detailed experiment logs live in
[preview-responsiveness-strategy.md](preview-responsiveness-strategy.md),
[instant-preview-research.md](instant-preview-research.md), and
[large-project-preview-research.md](large-project-preview-research.md).

## Problem

Small projects felt instant. Large ordinary projects (200 sources, long
timelines, 1080p and 4K) made the cursor preview and playback slow.

The main cause was not the timeline widget. Ordinary imports create a
sequential, legacy-ripple timeline. That route used
`FfmpegComposedPlaybackBackend`, which opened every source in the project and
built a concat graph for the whole remaining timeline, even when one preview
frame was requested. Scanning hundreds of clips cost much less than that.

## Current design

### 1. Active-only sequential decoding (main win)

`framestudio/sequential_playback.py` is the exact adapter for ordinary
sequential projects. For a requested time it:

- finds the active layout interval with a binary search;
- opens only the source(s) contributing at the playhead;
- builds a graph for those blocks only, not the whole tail;
- keeps the original sequential scale/pad/fps/framing filter contract, so
  pixels are unchanged.

The complete project model stays loaded. Nothing is hidden, removed, or
re-encoded in the saved project, and source files are not modified.

Routing is in `framestudio/app_project.py` (backend factory, attach, and
refresh). Source-to-command lookups use a retained path map in
`framestudio/composed_playback.py`.

### 2. Persistent interval playback

During continuous playback one decoder per active interval keeps running and
is restarted only when the active layout changes or the playhead seeks. Thread
budget: 4 decoder threads, 2 filter threads, 1 raw encoder thread.

### 3. Paused exact preview

When paused, each uncached seek runs asynchronously in the existing exact
FFmpeg path. Budget: `min(8, available CPUs)` decoder threads, 2 filter
threads, 1 raw encoder thread.

- Rapid cursor changes keep only the latest target. Stale results are dropped.
- Repeated positions reuse a bounded frame cache (eight frames).
- The GTK handler never blocks on decoding.

### 4. Native helper for absolute (synchronized) timelines

The optional preview runtime (`requirements-preview.txt`, `av==19.0.1`) runs a
helper in `framestudio/precise_preview_worker.py`. It keeps decoder contexts
and per-source color/scale graphs alive:

- `framestudio/precise_preview_native.py` (`DecoderPool`, `CompositionCache`)
  holds the residency policy.
- Run-up frames stay on the GPU; only the selected frame is downloaded.
- Nearby forward moves continue decoding instead of seeking back to a
  keyframe.
- Residency is demand-loaded only. No adjacent videos are decoded in the
  background.

Residency budget:

| Working set | Decoders / graphs | Notes |
| --- | --- | --- |
| All-CUDA, normal helper RSS budget | 5 / 5 | Selected. Post-render RSS retirement still applies. |
| CPU or mixed | 2 / 2 | Retained CPU budget. CPU fallback prunes extra contexts. |
| Smaller helper RSS budget | 2 / 2 | CUDA residency is limited to two. |

`FRAMESTUDIO_PREVIEW_BACKEND=auto|cpu|cuda|ffmpeg` chooses the engine. `auto`
uses supported acceleration and reports fallbacks.

### 5. Indexed timeline geometry

The timeline caches validated layout geometry until the model changes. It uses
a visible-viewport index (`framestudio/timeline_geometry.py`,
`timeline_rendering.py`, `timeline.py`) instead of scanning all clips. Paint
order, selection, deleted styles, offscreen selection, and drag previews are
preserved. Scrolling, zooming, selection, and edits invalidate the relevant
view.

### 6. Export-only audio analysis

Import, adding clips, reopening, recovery, and preview never run audio scans.
Audio analysis starts only after **Start export** is confirmed. It scans only
the sources used by the selected outputs, reuses valid saved results, and runs
independent scans in CPU-parallel processes with cancellation. Playback is
paused and streaming/native preview resources are released before export.
They reopen lazily after export.

### 7. Warning priority

Asynchronous backend fallback warnings no longer overwrite a higher-priority
error such as an invalid frame rate. `framestudio/app_playback.py`
(`handle_backend_warning`) keeps the current warning, preserves error
priority, and ignores stale generations.

## Measured results

Values are from the final production harness
(`benchmarks/large_project_preview.py`) on a 12-logical-CPU workstation with an
RTX 5070 Ti. "Cold" means a preview-frame-cache miss, not a cold OS cache.

### Seek latency, small vs large project (matched 0.5 s offset)

| Input / sources | First / middle cold seek | Cache-miss paint median / p95 | Playback updates/s | Owned RSS peak |
| --- | --- | --- | --- | --- |
| 1080p / 2 | 106.5 / 109.1 ms | 133.8 / 184.0 ms | 26.7 | 596 MiB |
| 1080p / 200 | 111.3 / 105.6 ms | 130.3 / 159.5 ms | 27.2 | 616 MiB |
| 4K / 2 | 268.9 / 272.1 ms | 358.4 / 577.3 ms | 18.0 | 842 MiB |
| 4K / 200 | 290.6 / 288.0 ms | 365.1 / 520.3 ms | 17.9 | 852 MiB |

Small and large projects now cost about the same per uncached seek. The
200-source whole-tail alternative exceeded the 2 GiB guard during attach and
never produced a preview, which is why active-only routing was needed.

### Sequential graph comparison (guarded, first/middle requests)

| Input / sources | Whole-tail graph | Five-block window | Active-only (selected) |
| --- | --- | --- | --- |
| 1080p / 20 | 638 / 453 ms | 264 / 270 ms | 153 / 153 ms |
| 1080p / 200 | stopped above RSS guard | 274 / 259 ms | 154 / 160 ms |
| 4K / 20 | stopped above RSS guard | 925 / 861 ms | 474 / 470 ms |
| 4K / 200 | stopped above RSS guard | 829 / 854 ms | 480 / 475 ms |

At 200 sources, sampled RSS was 360 MiB (active-only) versus 467 MiB
(five-block) at 1080p, and 436 versus 816 MiB at 4K.

### Native revisit (absolute timelines, five distinct files)

| Input / engine | Decoders / graphs | Revisit median |
| --- | --- | --- |
| 1080p CUDA | 2 / 2 (previous) | 63.4 ms |
| 1080p CUDA | 5 / 5 (selected) | 9.4 ms |
| 4K CUDA | 2 / 2 (previous) | 145.2 ms |
| 4K CUDA | 5 / 5 (selected) | 15.4 ms |

Net effect: about 6.7x at 1080p and 9.4x at 4K for native revisits. Pixels
match the CPU reference in every completed sample.

### Viewport and interval lookup (12 visible clips, 60 samples)

| Clips | Old / indexed query | Old / indexed draw |
| --- | --- | --- |
| 200 | 0.015 / 0.002 ms | 1.00 / 0.98 ms |
| 2,000 | 0.136 / 0.003 ms | 1.11 / 1.00 ms |
| 10,000 | 0.663 / 0.003 ms | 1.65 / 1.08 ms |

These gains matter for very large clip counts but are small in absolute terms.
They did not cause the seconds-long delays.

### Correctness and stability checks

- All 156 evaluated legacy-reference images match exactly.
- Rapid batches paint the latest target with zero observed stale frames.
- Edit, save, and reopen on 2- and 200-source projects keep source hashes and
  the source list. Zero audio scans run during preview. Zero FFmpeg children
  remain after close.
- Full suite on X11: 920 tests, 9 explicit skips, exit 0. Functionality
  charters: 10 passing. Full static analysis and churn: exit 0.

## Rejected alternatives

| Method | Why rejected |
| --- | --- |
| Whole-tail sequential graph | 200 sources exceed the 2 GiB guard during attach; multi-second latency. |
| Five-block eager window | Opens irrelevant sources at the same latency, with about 1.3x (1080p) and 1.9x (4K) the RSS of active-only at 200 sources. |
| Synchronized renderer for sequential projects | Changes about 2.5 million channels per frame (max diff 45/47 at 1080p, 27/28 at 4K). Not a speed fix. |
| Adjacent-source prewarming | Adds about 75 ms (1080p) and 68 ms (4K) of total work and competes with playback. |
| CPU residency of five contexts globally | 4K peak 1,746 MiB, above the 1,536 MiB helper threshold. |
| Exact direct `-hwaccel cuda` in the paused CLI path | Pixel mismatches until forced to YUV420P. Once exact, slower than the eight-thread CPU path (about 294 ms vs 111 ms at 1080p). |
| GPU-resident run-up in the fresh CLI | Exact, but 254 ms vs 111 ms at 1080p. Useful only inside the persistent helper. |
| Lower-resolution proxies or approximate previews | Violates the full-resolution, exact-framing requirement. |

## Thread budgets

| Mode | Decoder threads | Filter threads | Raw encoder threads |
| --- | --- | --- | --- |
| Paused exact preview | `min(8, CPUs)` | 2 | 1 |
| Continuous playback | 4 | 2 | 1 |

Eight paused decoder threads had the lowest total work across the paused
comparison (974 ms vs 1,006 ms for automatic threading at 1080p, and
2,768 ms vs 2,849 ms at 4K).

## GPU versus CPU

- Native CUDA residency with the 5/5 budget is the fastest for absolute
  timelines' repeated revisits.
- For single uncached seeks on the sequential path, CPU decoding with the
  budgets above is faster than CUDA because device startup, format negotiation,
  and transfer outweigh decode work.

## Limits

- Uncached 4K long-GOP seeks still take about 0.3 to 0.5 seconds. Decoding
  from the nearest keyframe is the limit.
- Source-boundary startup reduces painted FPS in short samples. Sustained
  30 FPS at 4K boundary playback is not proven.
- The 200-source fixtures are generated copies of two 8-second 1080p/4K
  H.264 clips (1,600 seconds of encoded media). They do not represent a
  40-hour project, heterogeneous cameras, codecs, or network storage.
- The benchmark measures GTK after-paint, not physical monitor scanout.
- The GDK `gdk_frame_timings_presented()` duplicate-call warning is not
  confirmed fixed.
- Local results come from one workstation. CI (Xvfb and system FFmpeg) differs
  from the local runtime.

## Running the benchmarks

```sh
make test                      # unit and integration suite
PYTHONPATH=. python3 benchmarks/large_project_preview.py --artifact-dir benchmark-run \
  --counts 2 20 200 --modes legacy-tail active-ffmpeg production
```

The harness acquires its own exclusive benchmark lock, so run it serially.
Each case runs in an isolated process with an RSS watchdog. Fixtures are
copied, not linked, so the 200-source case uses distinct files with the same
encoded content. Real GUI tests need an X11 display (`GDK_BACKEND=x11`);
Wayland breaks the XTest-based checks.
