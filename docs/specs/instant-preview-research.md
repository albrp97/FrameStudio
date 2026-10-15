# Exact preview latency investigation

## Contract and order of work

This follow-up investigates the remaining cursor-preview delay after retained
CPU/CUDA decoding was introduced. The user requested four concurrent research
threads, followed only after all four reports finished by implementation and
comparative benchmarks. That research barrier was observed. Research used
Haiku 5.5/high; isolated implementation workers use GPT-6.1 Sol/medium.

The selection rule is the fastest **correct** measured path. A cached revisit,
approximate keyframe, reduced-resolution image or pre-generated proxy is not
reported as a genuinely uncached exact seek. Source PTS, complete output RGBA,
colors, the 1920x1080 canvas, focus/triplicate composition and source preservation
remain protected. Audio analysis still starts only at confirmed export.

The production selection combines hardware-owned frames, bounded forward
continuation, an exact opaque-canvas composition shortcut, and startup-only
garbage-collector preparation. The COLD5 follow-up below adds retained exact
color/scale pipelines. The experiments distinguish their measured
effects from the final integrated GTK comparison.

## Starting observations

The preceding matched CPU/GPU experiment measured actual input-to-matching-GTK
paint medians of 132/69 ms at 1080p and 418/153 ms at 4K. Both modes already
retained decoder contexts. Those GPU numbers therefore cannot be improved by
claiming that decoder reuse or NVDEC has just been enabled.

Analysis of those existing CUDA traces places approximately 62/146 ms before
the decoded callback and 8/6 ms between callback and matching paint. These are
separate medians, not an additive decomposition of one median request.
Decoder/transfer work is the primary investigation target.

## Verified research

| System or source | What was established | What is not established |
| --- | --- | --- |
| LosslessCut, revision `d90a1336` | Normal seeking uses the browser video element's `currentTime`; pending seeks retain only the latest target. Its conditional compatibility player transcodes to an all-intra buffered stream. | No direct latency benchmark or verified proprietary browser GPU-surface implementation. The compatibility path is not equivalent to full-resolution source-exact cold decoding. |
| MLT/Shotcut/Kdenlive | MLT can decode forward for bounded nearby targets rather than always seek/flush. Image caching, seek coalescing, preview scaling and chunk previews are distinct mechanisms. | Preview scaling does not prove reduced source-decoder work. Cached/chunk/proxy results are not uncached source seeks. |
| mpv | Exact seeking decodes/discards to a target after decodable demux positioning; keyframe and exact seek modes differ. | No assumption that default relative keyframe seeking is equivalent to this editor's exact cursor contract. |
| DaVinci Resolve 20 manual | Documents Performance Mode, half/quarter timeline preview, optimized media, proxy media and background render caching. | Proprietary decoder/cache internals are unknown. Reduced-quality or prepared-media interactivity is not evidence for instantaneous full-quality arbitrary source seeks. |
| PyAV 19.0.1 source | With `is_hw_owned=False`, every decoded hardware frame is transferred to software before Python receives it. | The fraction of local latency attributable to these copies requires measurement. |
| NVIDIA/GTK documentation | GPU frames can remain on device; GTK can import supported GL/dma-buf textures with precise format/modifier/lifetime requirements. | No tested existing CUDA-to-GTK zero-copy bridge was established for this application. Literal zero CPU orchestration is not possible. |
| Current PyNvVideoCodec 2.2.3 | An official Python 3.14 Linux wheel was installed only in an isolated experiment. Its indexed decoder produced actual GPU NV12 surfaces and the expected selected pixels. | Its returned PTS disagreed with the physical frame content. Legacy VPF internals do not prove how this current package works. |

The most actionable finding is the PyAV transfer boundary. The old helper
checks a frame's timestamp **after** `packet.decode()` returns it. With
automatic hardware download, all intervening decoded frames have already been
copied to host, although only one will be displayed. Hardware-owned decoding
can select by timestamp first and download just the selected frame, leaving
the proven CPU color/composition path unchanged.

### Community evidence and access limits

Public PyAV and decoder issue reports describe GPU initialization, transfer and
threading overhead. They are hypotheses to test, not workstation measurements.
The research also attempted Reddit: HTML redirected to login and its search
endpoint returned HTTP 403. No Reddit discussion is claimed as inspected.
Stack Overflow HTML was likewise unavailable; metadata or search snippets were
not treated as verified answers. Historical NVIDIA multi-instance encode
reports were not substituted for current exact-seek results.

## Candidate experiments

| Candidate | Expected change | Correctness constraint | State |
| --- | --- | --- | --- |
| Selected-frame GPU download | Keep run-up frames on CUDA; transfer only the selected exact frame. | Same source PTS, NV12/planar metadata and complete RGBA; bounded surface lifetimes and correct cleanup. | Selected. |
| Bounded forward decoder continuation | Reuse decoder progress for small forward moves instead of unconditional seek/flush. | Preserve pending B-frames, current cancellation generation, rounding/VFR semantics and reset behavior. | Selected, within 32 average-rate frames and at most two seconds. |
| Opaque full-canvas composition shortcut | Avoid creating/blending a black background when one opaque crop already covers the canvas. | Preserve the general graph's color-conversion roundtrip, not merely the nominal output format. | Selected; other layouts retain the general graph. |
| Startup-only GC preparation | Freeze long-lived imports before creating the control thread, decoder pool, or request graphs. | Keep normal collection enabled and collect disposable native graph cycles after every render. | Selected; not a freeze of live decoders or graphs. |
| Direct RGBA shortcut without roundtrip | Remove the background and color roundtrip together. | Would need unchanged complete RGBA. | **Rejected:** faster but changed reference pixels. |
| Explicit `h264_cuvid` decoder | Compare a different NVIDIA parser/decoder wrapper. | Exact pixels/PTS and actual metadata must still satisfy production policy. | **Rejected:** slower; its standalone normalization bypass is not allowed in production. |
| PyNvVideoCodec 2.2.3 indexed seek | Compare the current vendor decoder, rather than assuming legacy VPF behavior. | Exact selected pixels and trustworthy source timestamps, without cache-confounded speed claims. | **Ineligible:** timestamp/content disagreement; no demonstrated fair performance win. |
| Larger IPC pipes | Increase pipe capacity without changing global kernel settings. | Measure transport separately from video/paint. | **Rejected:** no observed benefit. |
| Extra full-media packet indexing | Avoid demux lookup work. | Must first show index lookup is the bottleneck; no heavyweight import scan. | Not selected without evidence; native container seeking already uses available indexes. |
| Broad prefetch, proxies or approximate keyframes | Shift work earlier or display different prepared frames. | Cannot hide preprocessing, quality changes or cache hits inside cold-exact metrics. | Not silently adopted. |
| GPU scaling/color and native zero-copy display bridge | Remove further CPU filtering/readback/upload. | Existing reference pixels, source color state, synchronization and surface lifetimes must be proven. | Architecture-heavy; not an existing-runtime switch and not claimed implemented. |

The local composition experiment illustrates why speed alone is insufficient.
At 1080p, removing the roundtrip reduced composition-only median time from
17.5 to 4.0 ms, but the pixels differed. Retaining the roundtrip while avoiding
the unnecessary black overlay measured 8.8 ms and matched the complete RGBA.
At 4K input, the corresponding general/roundtrip-preserving medians were
23.9/16.8 ms. Focused crops also matched in this prototype. These are seven
paired **composition-only** samples per case, not end-to-end cursor timings.

## COLD4 comparison and selected route

### Isolated methods

These numbers are not interchangeable with input-to-paint latency.

| Experiment and boundary | Reference | Candidate | Result |
| --- | --- | --- | --- |
| Selected-download retained client, 1080p late GOP | 69.80 ms | 51.19 ms | Fewer unnecessary transfers. |
| Selected-download retained client, 4K late GOP | 147.92 ms | 141.42 ms | Small gain; decoding still dominates. |
| Forward one frame, 4K CPU native render | 117.10 ms | 24.26 ms | Avoid restarting the GOP. |
| Forward one frame, 4K CUDA native render | 81.74 ms | 27.83 ms | Same unique exact frame, not a cached image. |
| Forward 32 frames, 4K CUDA native render | 89.14 ms | 60.18 ms | Supports the selected bounded continuation. |
| Opaque 1080p composition | 17.49 ms | 8.78 ms | Preserves the general graph's color roundtrip. |
| Opaque 4K composition | 23.92 ms | 16.81 ms | Same output canvas and pixels. |
| Opaque composition plus collection after startup GC preparation, 1080p / 4K | 8.78 / 16.81 ms | 5.06 / 13.01 ms | Import objects no longer scanned on every request. |
| Explicit CUVID retained 1080p / 4K native experiment | 33.30 / 110.86 ms | 74.44 / 214.49 ms | Slower; not selected. |
| 8.29 MB synthetic IPC, 64 KiB / 256 KiB / 1 MiB pipe | 2.584 ms | 2.630 / 2.683 ms | No useful gain; not a video benchmark. |
| Current SDK indexed NV12 decode plus host bytes, 1080p / 4K | Not a valid paired ranking | 52.81 / 208.95 ms | Source PTS incorrect; ineligible. |

Selected GPU transfer tests reduced 55/57 automatic downloads to **one**
selected download. Complete NV12, normalized planar bytes, source metadata and
RGBA were compared, not only a thumbnail or average pixel error. The forward
experiment compared 8-, 16- and 32-frame bounds, including 1,296 exact
candidate/reference RGBA-and-PTS comparisons. A second alternating-order
control retained the forward improvement. Non-reuse traces varied, including
a 17.6% slower 1080p CUDA random-trace median and a 6.2% slower 4K CPU backward
median. This is not a universal speed guarantee for every individual seek.

The continuation keeps at most one unselected decoded frame between requests.
Oversized decode/flush batches retire continuation rather than pinning a GOP
of device surfaces. Backward, distant, invalid-rate, cancelled, failed and
exhausted requests reset to exact seeking. Cancellation is evaluated for the
current request, and the saved physical timestamp is not the mutable frame PTS
used by composition. Native per-render cycle collection and export cleanup
remain in place.

The current SDK experiment was run only after two additional read-only
API/runtime reports finished. Its official wheel was hash-verified and used in
an isolated environment, without changing application dependencies. All six
unseen frame-228 NV12 results matched the software and native reference bytes,
but `getPTS()`/`timestamp` reported 115712 rather than the content's 116736,
with timebase 1/15360: two frames behind. No constant offset or metadata
rewriting was added to hide this discrepancy. Its grouped native comparator
also produced anomalously slow 4K results, so those timings do not establish
an SDK speedup. Repeated alternate targets are explicitly not counted as
uncached. Legacy VPF source research is not evidence for current 2.x internals.

### Integrated production GTK comparison

The final matrix contains **24 completed fresh mapped GTK windows**: three
repetitions of baseline/selected, CPU/CUDA, and 1080p/4K. Variant and engine
order alternate between repetitions. Each configuration has 12 independent
uncached observations and 36 unique nearby forward observations. Native request
IDs verify that neither group is an image-cache revisit. The baseline is the
accepted GPU/CPU helper before this follow-up, not the original FFmpeg process.

| Decoder | Input | Request to matching GTK after-paint, median | Before | Selected | Speedup |
| --- | --- | --- | --- | --- | --- |
| CUDA | 1080p | Unique nearby forward | 38.84 ms | **18.33 ms** | **2.12x** |
| CUDA | 4K | Unique nearby forward | 79.93 ms | **26.96 ms** | **2.96x** |
| CPU | 1080p | Unique nearby forward | 58.31 ms | **17.84 ms** | **3.27x** |
| CPU | 4K | Unique nearby forward | 152.70 ms | **25.48 ms** | **5.99x** |
| CUDA | 1080p | Independent uncached | 57.57 ms | **43.85 ms** | **1.31x** |
| CUDA | 4K | Independent uncached | 150.89 ms | **130.46 ms** | **1.16x** |
| CPU | 1080p | Independent uncached | 117.35 ms | 105.80 ms | 1.11x |
| CPU | 4K | Independent uncached | 354.34 ms | 351.40 ms | 1.01x |

The common nearby CUDA result is approximately one to two 60 Hz display
intervals. Its observed p95 is 20.32 ms at 1080p and 29.41 ms at 4K. This does
**not** mean arbitrary source jumps are instantaneous. Independent CUDA p95 is
88.59/212.03 ms; with 12 samples that statistic is the observed maximum, not a
characterized long-session tail.

| Additional CUDA boundary, median | 1080p before / selected | 4K before / selected |
| --- | --- | --- |
| Retained-source independent seek, excluding first new-source opens | 52.73 / 40.50 ms | 146.28 / 127.42 ms |
| First second-source open after device initialization | 89.78 / 79.17 ms | 226.23 / 208.24 ms |
| Initial project attachment/helper/device startup | 298.37 / 293.24 ms | 360.12 / 354.71 ms |
| Cached revisit | 10.64 / 10.19 ms | 9.88 / 9.64 ms |
| Six-target rapid drag to final correct paint | 117.48 / 97.52 ms | 215.34 / 201.21 ms |

CPU-only 4K independent seeks are essentially unchanged, and CPU 4K startup
was slightly slower, 215.92 to 224.81 ms. CPU is competitive with CUDA for
nearby continuation, but substantially slower on cold seeks. Automatic mode
therefore retains the conditional native CUDA decoder rather than opening a
second CPU decoder to chase a small adjacent-frame difference. No configuration
is claimed fastest for every individual target.

Every completed window checked actual decoder provenance, at most two contexts
and one pending unselected frame, matching latest-target paint, play/seek/pause,
source hashes and release/restart. All **48 recorded helper PIDs** were gone
after their windows closed. One additional baseline CPU/4K attempt timed out
waiting for a scroll target's paint without a reported backend error. Its
failure log was retained, timeout diagnostics were added to the session probe,
and the incomplete matrix was explicitly resumed without changing the
application or discarding its six completed windows. The interrupted window is
not included in the 24 completed-window distributions.

### Reproduction and evidence

The session artifacts retain:

- `cold4-contract.json`, `cold4-research-barrier.json`, the four condensed
  research reports, and the current-SDK experiment's API/install/result records.
- `cold4-gpu-{api,benchmark,steady-benchmark}.*`,
  `cold4-forward-{benchmark,control}*`, `cold4-compose*`,
  `cold4-cuvid-*`, `cold4-pnvc-*`, and `cold4-transport-*` for isolated methods.
- `cold4-final-paired.py` and `cold4-seek-dispatch-probe.py` for the real GTK
  comparison. Run the former with the repository preview Python; its children
  acquire the exclusive `playback-benchmark.lock`. A frozen
  `cold4-baseline-worktree` holds the accepted pre-change source.
- `cold4-reviewed-paired-summary.json`, individual
  `cold4-reviewed-{baseline,selected}-{auto,cpu}-<resolution>-r<1..3>.json`,
  their logs and the explicit `first-failure.log`.
- `cold4-integration-evidence.json`, focused native/editor/media results,
  full configured static-analysis reports, auto/CPU smoke, and the real
  X11 edit/save/reopen/active-playback export/cancel/restart charter.

Initial combined verification exposed an unrealistic demux test double; it was
changed to the same closable-generator contract as PyAV. A related transfer
fallback was also hardened: the actual CPU replacement frame is color-checked
and supplies its own SAR/color provenance. Corrected test-first baseline
failures reproduce both defects. The source color whitelist was not weakened
to obtain benchmark eligibility.

## Measurement boundaries

Benchmarks must distinguish first helper/device initialization, first physical
source open, independent uncached seeks, forward continuation and frame-cache
hits. The previous generated inputs are eight-second GOP120 H.264 at 1080p/4K,
with two byte-identical physical paths per resolution. The 200-source/40-hour
timeline is synthetic metadata, not a 200-distinct-input or 40-hour soak.
OS caches are not purged. Matching GTK `after-paint` is not physical scanout.
No faster-than-Resolve/LosslessCut head-to-head claim follows from source
research or these local tests.

## Commercial-editor follow-up and retained rendering (COLD5)

Three concurrent, narrowly scoped research agents covered Resolve, VEGAS and
other editors. Vendor-document retrieval follow-ups also finished before any
new prototype or benchmark. Resolve's PDF was downloaded and extracted locally;
VEGAS's initially empty HTML shell was resolved through its help-system XML and
alias table to the actual static topics. A failed link or binary fetch was not
treated as evidence that the documented feature was inaccessible.

### What the editors actually document

| System | Verified mechanism | Meaning for this exact-preview path |
| --- | --- | --- |
| Resolve 20, printed pp.99 and 101 | GPU effects processing and H.264/HEVC hardware decoding have separate preferences. CUDA is recommended for Linux NVIDIA effects processing. | Already using CUDA decoding is not proof of matching Resolve's proprietary pipeline. Its frame residency, source-seek scheduling and context lifetimes remain unknown. |
| Resolve 20, pp.194-203 | Automatic Performance Mode preserves full-quality output, but the on-screen image may differ. Timeline Proxy, raw decode-quality settings, optimized media and render cache trade preview processing or prepared media for interactivity. | These do not establish an instantaneous, full-RGBA, genuinely uncached original-source seek. No silent quality mode or background preprocessing was adopted. |
| VEGAS Pro 22 official help | Dynamic RAM Preview explicitly renders each frame in a selected region into reserved RAM using Shift+B. Full/Half/Quarter preview and selective prerender are distinct features. Excessive RAM reservation can reduce performance. | This is prebuilt caching or a preview-quality tradeoff, not a new cold-seek technique. Its decoder internals and hardware scheduling are not disclosed by these topics. |
| MLT `filter_avfilter.c` and mpv `f_lavfi.c` | Retain filter graphs across frames and rebuild when input format/geometry/color properties change. | A genuinely new, transferable mechanism: the previous FrameStudio opaque path reconstructed its exact scale/color graph for every request. |
| FFmpeg buffersrc and PyAV 19 filter API | Normal frame pushes allow streaming; pushing `None` signals EOF. Some input-property changes are not safely rejected by every filter. | Retain only this stateless opaque chain, use a complete reuse key, do not send per-frame EOF, and verify complete pixels and physical timestamps. |

No Premiere/FCP proprietary implementation or direct commercial-editor latency
comparison was established. The source evidence above supports MLT/mpv graph
reuse, not an assertion that every Shotcut/Kdenlive path uses that same graph.
NVIDIA's NVDEC guide documents decoder retention/reconfiguration, but rebinding
raw decoders across independent sources is not a proven PyAV toggle. It was not
substituted for the previously slower explicit-CUVID or timestamp-ineligible SDK
experiments.

Opening files ahead of the request would shift work earlier rather than remove
it. Existing COLD4 observations attribute 15.25/56.48 ms to new-source
container/device open at 1080p/4K, within 79.17/208.24 ms matching-paint totals.
They do not separately establish decoder-creation cost. No preopening,
reduced probing, speculative decoding, or import-time analysis was added.

### Competing graph methods and selection

The disposable prototype compared retained graphs at 1/2/4/8/12 threads with
the accepted two-thread one-shot path, alternating order and checking complete
RGBA. A fresh eight-thread control showed that simply increasing thread count
can make graph setup slower. A final fresh-four-thread control confirmed the
distinction between setup and steady reuse.

Composition-only medians below include collection, but exclude decode, transfer,
IPC and GTK. Each case has 14 measured observations per method after two
warm-ups. Full-canvas and focused cases, backward/duplicate physical timestamps
and source hashes were checked; these are not independent uncached seeks.

| Input and crop | Accepted fresh graph, 2 threads | Retained graph, 4 threads | Fresh graph, 4 threads |
| --- | --- | --- | --- |
| 1080p full canvas | 5.41 ms | 2.52 ms | 4.98 ms |
| 1080p focused | 14.78 ms | 4.69 ms | 14.85 ms |
| 4K full canvas | 13.65 ms | 4.79 ms | 13.39 ms |
| 4K focused | 17.69 ms | 5.83 ms | 16.89 ms |

Eight or twelve threads sometimes win the isolated warmed microbenchmark, but
that is not the UI selection criterion. Twelve additional paired CUDA GTK
windows compared four with eight threads. Matching-paint nearby medians were
effectively tied at 23.5-23.7 ms. Four reduced the measured 4K first-new-source
median from 214.23 to 207.53 ms and startup from 346.95 to 338.98 ms; retained
cold medians differed by less than 0.6 ms. The 1080p startup comparison went the
other way, 284.36 to 288.60 ms. These small samples do not establish universal
per-request superiority.

**Selected:** retained exact graphs capped at four logical CPU threads and
two physical-source-aware entries, alongside the existing CUDA decoder. The
two-entry bound matches the decoder working set: a single retained graph would
unnecessarily rebuild when switching between the two retained sources. This is
a bounded refinement of the initial one-graph prototype, not unbounded caching
or background rendering.

The reuse key includes physical source identity, dimensions, pixel format,
time base, SAR, colorspace/range/primaries/transfer, chroma location,
rotation/interlace state, crop/scale geometry, output dimensions and thread
budget. A changed source or input/framing key rebuilds that source's graph.
Cancellation, errors, unsupported/general composition and helper closure clear
retained graphs. Backward/distant decoder seeks can reuse this stateless chain;
there are no temporal or framesync filters and every push is followed by one
matching pull. The physical input frame's PTS/time base is not overwritten by
the retained path. The proven color roundtrip and the general overlay path
remain unchanged. Post-render collection still disposes retired native cycles.

### Final paired production results

The final comparison uses **24 fresh mapped GTK windows on the workstation's
existing X11 display**, three repetitions with alternating variant/engine
order. The control is the preserved, accepted COLD4 implementation, not Git
HEAD or an earlier FFmpeg-only path. Each configuration has 12 independent
uncached and 36 unique nearby observations. Both groups have distinct native
request IDs, not image-cache hits. All 48 final helper PIDs were reaped; source
hashes, two-context/two-graph bounds, latest-target paint, play/pause and
release/restart assertions held.

| Decoder/input | Boundary | COLD4 control | Selected COLD5 | Median reduction |
| --- | --- | --- | --- | --- |
| CUDA 1080p | Independent uncached to matching paint | 44.46 ms | 42.45 ms | 4.5% |
| CUDA 4K | Independent uncached to matching paint | 133.99 ms | 124.77 ms | 6.9% |
| CUDA 1080p | Unique nearby to matching paint | 23.59 ms | 23.62 ms | No measured gain |
| CUDA 4K | Unique nearby to matching paint | 28.08 ms | 23.79 ms | 15.3% |
| CPU 1080p | Independent uncached to matching paint | 107.75 ms | 103.90 ms | 3.6% |
| CPU 4K | Independent uncached to matching paint | 337.06 ms | 328.56 ms | 2.5% |
| CPU 1080p | Unique nearby to matching paint | 23.45 ms | 23.61 ms | No measured gain |
| CPU 4K | Unique nearby to matching paint | 27.34 ms | 23.55 ms | 13.9% |

| Additional CUDA boundary, median | 1080p control / selected | 4K control / selected |
| --- | --- | --- |
| Retained-source independent seek | 42.19 / 38.77 ms | 127.80 / 118.18 ms |
| First second-source open | 89.37 / 89.62 ms | 205.62 / 208.76 ms |
| Helper/device/project attachment | 286.75 / 284.79 ms | 352.03 / 349.38 ms |
| Cached revisit | 22.26 / 23.38 ms | 25.68 / 23.77 ms |
| Six-target rapid drag | 96.86 / 99.35 ms | 201.83 / 207.26 ms |

This is a **modest further improvement**, not instant arbitrary 4K seeking.
The larger composition-only gains do not turn into equally large paint gains;
in particular 1080p nearby paint stayed essentially unchanged. First source
opens and rapid traces did not improve in the final control. CPU 4K first-open
median was 368.78/382.18 ms, despite lower retained/nearby costs. That regression
is disclosed, not hidden inside an overall median. The chosen route is the best
measured balance here, not a guarantee that every first open or individual seek
is faster. CUDA remains substantially faster than CPU for cold 4K work.

The earlier COLD4 nearby measurements should not be subtracted from this
round's results: the current fresh X11 controls and selected windows share
paint pacing; historical paint observations had different observed pacing.
GTK `after-paint` is still not physical scanout. Generated eight-second GOP120
files and 200-logical-source/40-hour metadata still do not constitute a real
200-distinct-video/40-hour soak. OS caches were not purged.

### COLD5 evidence and reproduction

The session evidence retains `cold5-contract.json`, `cold5-research.json`,
`cold5-research-barrier.json`, official-source caches, the preserved COLD4
manifest/files and `cold5-baseline-worktree`. `cold5-retained-graph-experiment.py`
and its initial, extended and fresh-control results cover competing methods.
`cold5-paired.py` uses the existing matching-paint probe and an exclusive
`playback-benchmark.lock` for each child.

Run the paired script with the repository preview Python and
`GDK_BACKEND=x11`, using a new `--prefix` for every new implementation. Its
default baseline is `cold5-baseline-worktree`; `--baseline-root`,
`--selected-root`, `--engines` and `--repetitions` support explicit candidate
comparisons. It resumes completed JSON observations, so reusing an old prefix
does not rerun them. An attempted virtual-display command was unavailable;
the existing workstation X11 display was verified and used instead, without
installing tools or changing global graphics settings.

`cold5-final-*` is the initial eight-thread matrix, **not** final production.
`cold5-thread-compare-*` compares eight with four.
**`cold5-reviewed-paired-summary.json` and its windows are the final selected
four-thread evidence.** `cold5-integration-evidence.json` and final validation
record the separate correctness, functionality, static and cleanup gates.

## Primary references

- [LosslessCut seek handling](https://github.com/mifi/lossless-cut/blob/d90a1336ed61c2fa0d73ef44b8a4f074cefc5f89/src/renderer/src/hooks/useVideo.ts)
- [LosslessCut compatibility encoding](https://github.com/mifi/lossless-cut/blob/d90a1336ed61c2fa0d73ef44b8a4f074cefc5f89/src/main/ffmpeg.ts)
- [HTML media seeking](https://html.spec.whatwg.org/multipage/media.html#seeking)
- [MLT avformat producer](https://github.com/mltframework/mlt/blob/9076d2e24f660dabaa3ba8c60c3c737756a7e46a/src/modules/avformat/producer_avformat.c)
- [mpv exact seek implementation](https://github.com/mpv-player/mpv/blob/492bae0768f5e826991bf9fb222fa303371e8498/player/playloop.c)
- [Kdenlive preview chunks](https://github.com/KDE/kdenlive/blob/7a3a84a656b0840fd6e0f6cd755b69cb80cf5cbb/src/timeline2/view/previewmanager.cpp)
- [DaVinci Resolve 20 manual, printed pages 194-217](https://documents.blackmagicdesign.com/UserManuals/DaVinci_Resolve_20_Reference_Manual.pdf)
- [PyAV 19 hardware transfer source](https://github.com/PyAV-Org/PyAV/blob/v19.0.1/av/video/codeccontext.py)
- [PyAV 19 selected-frame reformatter](https://github.com/PyAV-Org/PyAV/blob/v19.0.1/av/video/reformatter.py)
- [GTK dma-buf texture API](https://docs.gtk.org/gdk4/class.DmabufTextureBuilder.html)
- [Current PyNvVideoCodec metadata and official wheel hashes](https://pypi.org/pypi/PyNvVideoCodec/2.2.3/json)
- [PyNvVideoCodec documentation](https://docs.nvidia.com/video-technologies/pynvvideocodec/index.html)
- [Legacy NVIDIA VPF source, not current PyNvVideoCodec internals](https://github.com/NVIDIA/VideoProcessingFramework/tree/529fb192f22ec305b8b237ed9e6014e171339c81)
- [Python GC freeze semantics](https://docs.python.org/3/library/gc.html#gc.freeze)
- [FFmpeg seeking](https://trac.ffmpeg.org/wiki/Seeking)
- [Decoder startup/throughput community discussion](https://github.com/dmlc/decord/issues/359)
- [VEGAS Pro 22 Dynamic RAM Preview](https://help.magix-hub.com/video/vegas/22/en/content/topics/5-preview/using_dynamic_ram_previews.htm)
- [VEGAS Pro 22 preview quality](https://help.magix-hub.com/video/vegas/22/en/content/topics/5-preview/videopreview.htm)
- [VEGAS Pro 22 selective prerender](https://help.magix-hub.com/video/vegas/22/en/content/topics/5-preview/selective_pre-render.htm)
- [MLT retained avfilter graph](https://github.com/mltframework/mlt/blob/9076d2e24f660dabaa3ba8c60c3c737756a7e46a/src/modules/avformat/filter_avfilter.c)
- [mpv retained lavfi graph](https://github.com/mpv-player/mpv/blob/492bae0768f5e826991bf9fb222fa303371e8498/filters/f_lavfi.c)
- [PyAV 19 normal-frame versus EOF push](https://github.com/PyAV-Org/PyAV/blob/v19.0.1/av/filter/context.py)
- [NVIDIA NVDEC lifecycle and mapping guide](https://docs.nvidia.com/video-technologies/video-codec-sdk/13.0/nvdec-video-decoder-api-prog-guide/index.html)
