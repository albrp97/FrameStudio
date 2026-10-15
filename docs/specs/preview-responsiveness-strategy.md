# Preview Responsiveness Strategy

## Decision

The editor keeps the existing FFmpeg raw-frame playback contract and a
bounded eight-frame LRU preview cache. Preview requests still use generation
checks so a frame decoded for an obsolete cursor position is never delivered.
Cache keys use the nearest source frame index. A cache hit is presented at the
requested cursor position while `VideoFrame.decoded_position_seconds` preserves
the timestamp from which the cached pixels were decoded.

The cache is scoped to one backend instance and is not used by export or
persistence.

Ordinary sequential imports use `FfmpegSequentialPlaybackBackend`, an
active-only interval adapter that preserves the original sequential
contain/pad/zoom/crop/fps pixels. They no longer open a whole-project concat
graph for one preview. Their uncached paused seeks deliberately use exact
FFmpeg rather than the pixel-changing synchronized native graph. Audio-enabled
compatibility callers without this silent-preview route retain the original
composed backend.

Synchronized/composited playback now streams frames through one persistent
FFmpeg process per active layout interval. Random exact seeks use the retained
native helper when available, or the reference one-frame FFmpeg path otherwise.
Layout changes, discontinuities, generation changes, and close
dispose of the old decoder. Decoder-only processes are killed and reaped
immediately so an unread raw-video pipe cannot delay a transition while FFmpeg
tries to flush it. Finite interval frame counts, bounded decoder/filter threads,
and the absence of a Python frame queue bound work and memory.

The GTK timeline caches validated geometry by model identity/revision and view
parameters, reuses it for drawing and hit testing, and bounds expensive Cairo
primitives to the visible viewport. Immutable row/start/prefix-end indexes now
select visible clips without a full cached-geometry scan; drawing order,
offscreen selection, hit testing and drag previews are retained. Interval
lookup uses binary search and active source IDs use a retained path map.
Edits, scroll adjustments, zoom, track
activation, and resize invalidate the relevant state. Unchanged playheads do
not request idle redraws. Export, source files, preview dimensions, exact seek
accuracy, and export-only audio analysis are unchanged.

## Evidence

The reproducible harness is `benchmarks/preview_responsiveness.py`. It sends
cursor, click, seek, and scroll-like requests, then records request-to-frame
latency, displayed versus requested position, timeout failures, cancellation
and coalescing observations, stale frames, and cache hits. The captured
one-source and mixed-source outputs are:

- `evidence/phase-008-preview-benchmark-one-source.json`
- `evidence/phase-008-preview-benchmark-mixed-source.json`

On the captured 10 FPS H.264 fixtures, cold cache misses were approximately
29 ms (one source) and 32 ms (mixed source). Warm cache hits were approximately
0.01 ms median in both cases. Rapid traces delivered only the newest decoded
frame with the current cache disabled; cache hits delivered several already
decoded frames immediately. The failure probe reported the missing decoder
explicitly. These are local measurements, not universal codec or hardware
claims.

## Lossless Cut research boundary

Additional inspection used public LosslessCut revision
`d90a1336ed61c2fa0d73ef44b8a4f074cefc5f89`, also GPL-2.0-only. Its HTML5 video
playback relies on a continuing decoder rather than launching an external
decoder for every displayed frame. Its bounded keyframe-window work is another
useful hypothesis, not an adopted requirement. FrameStudio independently
implements continuous decoding in its existing FFmpeg raw-frame backend; no
LosslessCut source or dependency is copied.

Lossless Cut revision `e1f4348637575bb21fe9bc2ba70e0f9a70cbafaf` was inspected
from its public repository on 2026-08-26. `package.json` declares
`GPL-2.0-only`, and its `LICENSE` is GPL version 2. The disposable checkout was
removed after inspection; no source, dependency, or generated file was copied.

Transferable hypotheses were:

- `src/renderer/src/hooks/useVideo.ts:35-59`: retain only the latest pending
  scrub target while a seek is in flight.
- `src/renderer/src/MediaSourcePlayer.tsx:196-231`: throttle reads when a
  bounded buffer is sufficiently ahead, and remove old buffered ranges.
- `src/renderer/src/hooks/useThumbnails.ts:20-55`: debounce viewport changes
  and abort obsolete asynchronous thumbnail work.
- `src/renderer/src/MediaSourcePlayer.tsx:252-304`: periodically resynchronize
  a slave stream to the authoritative player and adjust playback rate when
  drift is small.

Those concepts are not direct implementation matches: this editor uses GTK 4,
PyGObject, subprocess FFmpeg, and raw RGBA frames rather than Chromium
`HTMLVideoElement`/MediaSource. The adopted cache and generation checks are
repository-native implementations, not derivative code.

## Tradeoffs and limits

The cache improves repeated nearby scrubs but cannot reduce the first decode.
Nearest-frame keys can show a decoded frame slightly before or after the
requested timestamp; both the requested presentation position and decoded
position remain available for diagnostics. Eight frames bounds memory but may be insufficient for long
timelines or high-resolution canvases. No GTK/display session was available
for that earlier cache-only run. The subsequent measurements below include
actual GTK draw callbacks as well as separate decoder throughput.

## Large-project playback measurements

The comparison baseline is `e4cc773`. Reproducible harnesses are
`benchmarks/playback_performance.py` and
`benchmarks/large_timeline_performance.py`. Experiments were serialized by an
exclusive resource lock on one Linux workstation with 12 available logical
CPUs, FFmpeg n9.0.2, Python 3.14.7, and GTK 4.24.1.

The media fixtures are generated, high-detail H.264 with a 120-frame GOP and
B-frames, at 1920x1080 and 3840x2160. The output remains 1920x1080 at a requested
30 FPS. Two paired 4.5-second playback samples include startup and two layout
transitions. The 200 logical sources and 40 hours are synthetic metadata; each
encoded fixture is only eight seconds. These are not 40-hour playback/soak
results, and backend delivery is not a GTK-painted-FPS measurement.

| Metric | Per-frame reference | Persistent interval decoder |
| --- | --- | --- |
| 1080p delivered preview FPS | 8.00-8.22 | 29.11 |
| 4K delivered preview FPS | 3.11 | 26.00-26.67 |
| 1080p p95 inter-frame gap | 149-158 ms | 34.9-35.0 ms |
| 4K p95 inter-frame gap | 393-407 ms | 35.5-35.8 ms |

Mean paired delivery improves approximately 3.6x for 1080p and 8.5x for 4K.
The requested 30 FPS is the ceiling, not a claim of unlimited decoding speed.
Cold-seek implementation is unchanged; observed seek-time variation is not
attributed to this optimization.

Four additional 5.2-second checks used the actual mapped FrameStudio window.
Distinct preview paintables were counted at the frame clock's `after-paint`
signal, with 1920x1080 textures and the same transient 200-source/40-hour
metadata. The comparison switches only the decoder between the per-frame
reference and final streaming path inside the identical final GUI; it is not
a benchmark of the entire old GUI. This verifies GTK consumption, not
physical monitor presentation feedback.

| Input | Reference painted updates/s | Final painted updates/s |
| --- | --- | --- |
| 1080p | 8.08 | 29.18 |
| 4K | 3.27 | 27.11 |

For 4K, p95 paint-update gaps fell from 401.8 ms to 42.3 ms, and gaps above
250 ms fell from 15 to zero within the observed sample. Source hashes,
timestamps, project/canvas playhead agreement, and absence of idle audio
analysis were checked. These short generated-media checks are not a
40-hour soak test or a universal workstation guarantee.

Actual GTK-main-thread timeline draw callbacks, 30 samples at a 1200x300
viewport, use a separate synthetic 200-source, 40-hour timeline:

| Segments | Baseline p50 / p95 | Final p50 / p95 | p50 speedup |
| --- | --- | --- | --- |
| 200 | 2.216 / 2.325 ms | 0.411 / 0.504 ms | 5.4x |
| 2,000 | 11.375 / 12.639 ms | 1.009 / 1.119 ms | 11.3x |
| 10,000 | 56.475 / 66.265 ms | 3.840 / 4.199 ms | 14.7x |

Geometry caching and viewport culling were also measured independently; their
combination was substantially better than either alone. Reducing FFmpeg
decoder threads indiscriminately worsened long-GOP 4K seeks/playback. A
960x540 preview candidate did not remove the per-frame restart bottleneck and
was rejected instead of silently reducing preview quality. The retained
streaming budget bounds aggregate input decoder threads to four, complex
filter threads to two, and the raw encoder to one.

Correctness checks compare moving-source, fractional-tail, framing, triplicate,
four-source, and black-gap stream pixels against exact seeks. Additional checks
cover fractional FPS, terminal-end cleanup, actual mixed-resolution source
paths, decoder restart counts, saved/reopened edits, and preserved source
hashes. At that checkpoint, model validation still cost work after real edits;
geometry culling still scanned cached geometry, and cold seeks/layout restarts had startup
cost. There is no new hardware decoder, proxy pipeline, background indexing,
or audio scan.

## Cursor seek dispatch measurements

The follow-up baseline is the accepted persistent-playback working tree above,
not `e4cc773`. Absolute-timeline cursor callbacks bypassed the existing
asynchronous preview worker and called synchronous `PlaybackController.seek`
on the GTK main thread. They now use the existing exact preview worker,
latest-target cancellation, and eight-frame cache. Queued GTK frames are
invalidated when a newer request starts. Identical targets are deduplicated
within one drag gesture, without a debounce delay; new gestures still dispatch
immediately. Initial project attachment retains its synchronous contract.

Actual mapped-window measurements correlate the requested frame with a changed
`Gtk.Picture` paintable at frame-clock `after-paint`. The final integrated run
also verifies seeking during playback and subsequent pause. These are GTK
paint observations, not physical monitor scanout.

| Metric | 1080p before / after | 4K before / after |
| --- | --- | --- |
| Six-target rapid drag, first input to final correct paint | 1431 / 255 ms | 3579 / 675 ms |
| Repeated exact target to correct paint, median | 224 / 13 ms | 611 / 12 ms |
| Cold seek handler blocking time, median | 203 / 0.27 ms | 586 / 0.29 ms |
| Cold isolated seek to correct paint, median | 220 / 202 ms | 601 / 597 ms |

Rapid-drag completion improved approximately 5.6x and 5.3x respectively.
Repeated-target gains depend on the bounded cache. Isolated uncached 4K
preview latency remains essentially unchanged: this repairs UI blocking and
redundant/obsolete work, not the source's GOP decode cost. Four unique cold
targets, two intentionally repeated targets, and six previously unrequested
rapid targets are bounded samples, not universal latency distributions.

The same generated eight-second GOP120/B-frame media and synthetic
200-source/40-hour metadata are used. Each resolution has two distinct physical
paths with byte-identical content; this is not 200 distinct encoded videos or a
40-hour soak. Source hashes remain unchanged. Separate actual XWayland pointer
checks reproduced the nonblocking handler and unchanged cold-decode cost.

`python -m benchmarks.seek_performance --fixtures <fixture-directory>
--lock <exclusive-lock-path> --output <report.json>` reproduces cache-disabled
decoder experiments with different 1080p/4K physical files, fractional targets,
source PTS, pixel hashes, and segment boundaries. The harness owns its lock;
do not wrap it in another `flock`. Raw-output threading, filter threading,
input threading, bounded probing, a simpler single-slot graph, and optional
CUDA were compared. No repeatable substantial safe decoder improvement was
found. CUDA was slower and changed reference pixels, so it was rejected.
Production decoder flags and preview quality remain unchanged.

LosslessCut's inspected `src/main/ffmpeg.ts` uses input-side seeking, already
present here, and an all-intra MediaSource encoding branch. Hardware decode is
opt-in there. Its browser buffering/encoding pipeline is not directly
transferable to this GTK raw-frame path. Proxies, all-intra preparation, and
approximate keyframe previews remain unadopted scope/quality changes.

## Persistent exact-seek decoder investigation

The next investigation compared the accepted asynchronous seek implementation,
not the original per-frame playback implementation. Public-source research
identified a separate source of latency: subprocess/container/decoder startup
on every exact cache miss, plus decoding from the preceding keyframe.

The selected design retains libav demux/decoder contexts through optional
PyAV 19.0.1 in a separate helper process. CPU decoding is the general path;
CUDA is a conditional H.264 optimization, not a universal codec or color
guarantee. GPU frames are downloaded and normalized to the host planar format
before the same composition operations. GTK still receives the same canvas
and exact requested frame. Continuous playback and export keep their existing
FFmpeg implementations.

The initial helper retained at most two physical-source contexts, not one context per
logical clip. CPU decoder threads are bounded by affinity and a 16-thread
ceiling; native filter graphs use two threads. Requests have a 15-second client
deadline, bounded metadata, and at most a 64 MiB pixel payload. Latest-request
cancellation and process isolation permit obsolete or unresponsive native work
to be interrupted and reaped without waiting on a GTK I/O lock.
Deterministic graph cleanup and a request-boundary RSS retirement threshold
limit accumulating native allocations. The default threshold is the smaller
of 1536 MiB and one quarter of available RAM, with a 256 MiB floor. This is a
soft RSS limit, not an instantaneous allocator or VRAM quota.
Dependency/capability fallback is diagnostic and explicit. Native decode errors
are not silently converted into a successful approximate preview.

Only verified untagged and BT709 limited/full color combinations enter the
native composition path. CUDA additionally requires compatible H.264 8-bit
4:2:0, timestamps, rates, SAR, and display metadata. Unsupported hardware uses
CPU decoding; unproven native color handling uses reference FFmpeg. Actual
source color matrix and range are supplied to the filter source before graph
configuration, including full-range material. Requested microseconds and
physical source PTS are transported separately using integer ticks and rational
timebases.

Confirmed export fences and reaps the streaming decoder and retained native
resources before audio analysis or rendering, including exports started during
playback. Ordinary pause does not destroy decoder reuse; the next uncached
seek after release creates a helper lazily.

The development runtime includes the optional preview requirements. Application
startup must not require importing PyAV: older or minimal installations keep
the existing FFmpeg path. Python 3.12 or newer is required only for the pinned
optional helper runtime, not for the existing Python 3.10 application.

### Research comparison

- [PyAV seeking](https://pyav.basswood-io.com/docs/stable/api/container.html):
  retain the input container, seek backwards to a keyframe, then decode to the
  desired timestamp. This avoids opening a new container for every target.
- [MLT's avformat producer](https://github.com/mltframework/mlt/blob/master/src/modules/avformat/producer_avformat.c):
  persistent format/codec state and buffer flushing provide a relevant editor
  comparison. Quality-changing frame/loop-filter shortcuts were not copied.
- [LosslessCut](https://github.com/mifi/lossless-cut/tree/d90a1336ed61c2fa0d73ef44b8a4f074cefc5f89):
  latest-target browser seeking and its alternative MediaSource transcoding
  pipeline are distinct from a one-frame GTK RGBA pipe. The all-intra output
  branch does not eliminate source-GOP decoding for every new transcode.
  GStreamer lacked the local MP4 demuxer; libmpv was also benchmarked, but its
  timestamp/color defaults and measured performance made it a poorer fit than
  the exact libav prototype.
- [DaVinci Resolve 20 Reference Manual](https://documents.blackmagicdesign.com/UserManuals/DaVinci_Resolve_20_Reference_Manual.pdf),
  printed pages 194-199 and 203 onwards: documented options include reduced
  timeline working resolution, optimized media, and render caches. Hardware
  H.264/HEVC decode is also documented. These explain available performance
  tradeoffs, not proprietary implementation details. Reduced resolution,
  pre-generated media, and background cache rendering are not adopted here.

Retaining a CUDA primary device amortizes its initialization across source
changes. Merely reusing a Python hardware-acceleration configuration object did
not share the native device. CPU and GPU prototypes both compared complete RGBA
outputs and physical timestamps against the existing exact FFmpeg path.
First-device initialization, new-source open, retained-context cold decode,
and frame-cache hits are separate measurements.

### Integrated exact-preview measurements

Three paired runs after correctness-review remediation compared the final
production `ffmpeg` and `auto` modes in
the same actual mapped GTK window. Each fresh window issued four unique
uncached targets, including late-GOP positions and a second physical input.
Native request IDs confirm that these were decoded, not frame-cache hits.
There are 12 cold samples per resolution and mode. The control is the accepted
asynchronous/persistent-playback implementation, not the original blocking UI.

| Request to matching GTK after-paint | Reference FFmpeg | Final automatic CUDA |
| --- | --- | --- |
| 1080p uncached p50 | 226.4 ms | 67.0 ms |
| 1080p observed p95 / maximum | 257.7 ms | 123.3 ms |
| 4K uncached p50 | 657.0 ms | 160.2 ms |
| 4K observed p95 / maximum | 729.4 ms | 241.9 ms |
| 1080p six-target drag completion, median | 274.5 ms | 125.0 ms |
| 4K six-target drag completion, median | 745.5 ms | 224.0 ms |

Median uncached latency improves 3.38x at 1080p and 4.10x at 4K: reductions of
70.4% and 75.6%, respectively. The sample's p95 is its maximum, not a
well-characterized long-session tail. A first seek into the second physical
source, with the shared device already initialized, takes a median 106.1 ms
at 1080p and 240.7 ms at 4K. Reusing a retained context is distinct from
opening a new source. An additional automatic-mode check outside these paired
runs measured medians of 97.2 ms and 170.6 ms, with maxima of 125.7 ms and
271.6 ms. These observations expose run-to-run variation, not a latency cap.
Earlier cached revisits measured approximately 10-12 ms.

## Hardware-owned frames and bounded forward continuation

The subsequent [exact-preview investigation](instant-preview-research.md)
compares against the accepted automatic CUDA implementation above, not against
the original per-frame FFmpeg process. Its final table also measures CPU-only
operation separately.

CUDA frames now remain device-owned through physical timestamp selection.
Only the selected frame is downloaded and normalized; discarded run-up frames
no longer incur automatic host transfers. Small forward changes continue from
the selected physical position within 32 average-rate frames and two seconds,
instead of unconditionally seeking backwards. The decoder preserves at most
one pending unselected picture between requests, clears continuation after
cancellation/errors or oversized batches, and releases it before container and
device teardown. Backward and distant moves still use exact keyframe seeking.

A single opaque crop covering the full canvas bypasses the unnecessary black
overlay, but retains its color-conversion roundtrip for byte-exact output.
Letterboxing, alpha, triplicate and multiple slots retain the general graph.
The helper freezes only long-lived imports, before creating request/control or
decoder state, so per-render collection need not rescan them. Native graph
cycles are still collected after every render; garbage collection is not
disabled.

The COLD5 commercial-editor follow-up adds source-aware reuse of the exact
opaque color/scale pipeline, following source-verified MLT/mpv graph retention.
COLD5 retained at most two graphs, capped at four CPU threads; changed input or
framing properties rebuild them, and cancellation/errors/export release retire
them. The retained path preserves physical PTS without sending per-frame EOF.
The linked investigation records the four/eight-thread GTK comparison, final
paired gains and first-open regressions; arbitrary long-GOP seeks are still not
instant.

The selected route does not guarantee that every request beats every
alternative. CPU and CUDA are competitive for adjacent frames; CUDA remains
the faster measured path for independent cold H.264 seeks. Arbitrary long-GOP
4K jumps and first physical-source opens remain materially slower than nearby
continuation. No new preprocessing, proxy, source rewrite, or application
dependency was introduced.

Initial project attachment, including first helper/device startup, costs a
median 338 ms at 1080p and 400 ms at 4K, versus 124 ms and 282 ms for reference
FFmpeg. That one-time cost is not hidden inside the retained-decoder numbers.
CPU-only production mode measured 121.8 ms and 392.1 ms uncached medians in
one earlier run of four samples per resolution; it is a compatibility path,
not a promise of GPU performance on other machines.

The COLD5 automatic mode reports actual CUDA decoding, at most two retained
contexts, and observed native-worker RSS below 403 MiB at 1080p and 672 MiB at
4K in these traces. Native resource release takes approximately 170-229 ms
and runs off the GUI thread before export work. Each window verifies helper
reaping, a new uncached request after release, rapid-target correctness,
play/seek/pause, unchanged source hashes, and absence of idle audio analysis.
Separate production-boundary tests compare physical PTS and full RGBA output
against FFmpeg, including initial frame zero, tagged colors, framing,
triplicate, mixed sources, VFR, nonzero starts, and black gaps.

These final numbers include host download, exact composition, process
transport, GTK texture delivery, and a matching frame-clock paint observation.
They are not decoder-only prototype timings or physical scanout measurements.
The workstation uses the RTX 5070 Ti and the environment described above.
The 200-source/40-hour timeline remains synthetic metadata over two physical,
byte-identical eight-second fixtures per resolution; OS file caches are not
purged. Different-content/resolution inputs are exercised separately for
correctness. That COLD5 experiment does not establish 200-distinct-video or
40-hour soak performance.

## Subsequent distinct-source stability follow-up

[Large-project research and all comparisons](large-project-preview-research.md)
records five local and five externally researched strategies, followed by
actual 2/20/200-distinct-file sequential GTK measurements. Those files share
generated encoded content, not heterogeneous forty-hour footage.

The important correction is routing ordinary sequential imports to the exact
active-only adapter. Earlier native CPU/CUDA work had applied only to absolute
timelines, while ordinary imports still opened a whole-project concat graph.
The final mapped-window comparison gives similar matched uncached seek
latencies at two and two hundred sources, with the sequential pixels
preserved. Cold 4K latency and source-boundary startup remain visible; no
universal instant or continuous 30-FPS claim is made.

Current native residency supersedes COLD5's two-context/two-graph policy for
all-CUDA requests: five demand-loaded decoders and graphs when the normal
helper budget permits, two for CPU/mixed or smaller helper budgets, with the
existing post-render RSS retirement. Eager neighbor prewarming is rejected
because measured total work rises. Indexed visible geometry and logarithmic
interval/source lookup supersede the earlier full cached-geometry scan.

## GDK presentation warning

In [GTK 4.24.1's `gdk_frame_timings_presented()`](https://raw.githubusercontent.com/GNOME/gtk/4.24.1/gdk/gdkframetimings.c),
the duplicate-call warning means the same frame received conflicting
presentation timestamps or refresh intervals. The reported `1.791ms` is the
difference between the second timestamp and the first stored timestamp, not
FFmpeg decoding latency. GTK emits this warning once per process.

Twelve bounded six-second probes compared minimal redraw and actual editor
playback on Wayland/Xwayland with GL, Vulkan, and Cairo. None reproduced the
exact warning. That does not establish that longer sessions, different media,
monitor changes, drivers, or compositors cannot trigger it. No renderer/backend
default was changed, and warnings are not suppressed. If it recurs, capture
GTK/compositor/driver versions and presentation-feedback evidence before
choosing an upstream fix or workaround. Explicit `GSK_RENDERER` and
`GDK_BACKEND` choices remain respected; X11 comparisons require a working
X11/Xwayland display.
