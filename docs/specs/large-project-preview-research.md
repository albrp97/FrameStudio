# Large-project preview and playback research

## Scope and research gate

The 2026-10-15 request authorizes research, isolated experiments, matched
benchmarks, and integration of the fastest correct large-project strategy.
This is a scoped local continuation of the existing performance work, not
publication or closure of unrelated planning records. Preserve full-resolution
preview, physical source timestamps, framing, source files, saved project
semantics, and export-only audio analysis.

Three independently scoped Haiku 5.5/high research agents completed their
reports before any experiment began. The integration owner separately traced
the production import/seek route and developed five local hypotheses.
Implementation/benchmark workers use GPT-6.1 Sol/medium. Raw technical results
are distinct from the configured automatic-validation decision.

The earlier large-project measurements exercised absolute timelines with 200
logical sources over two physical files. They do not establish performance for
the ordinary sequential import route or 200 distinct source files.

## Confirmed production-path discrepancy

Ordinary `Project.create_multi` creates a sequential, legacy-ripple timeline.
`app_project.attach_project` and backend refresh select
`FfmpegComposedPlaybackBackend` for that timeline. Its `_append_inputs` adds
every source to FFmpeg; its `_command` creates filters and concat nodes for
every remaining block, even when only one preview frame is requested.

The previous persistent-interval and CPU/CUDA exact-preview work belongs to
`FfmpegSynchronizedPlaybackBackend`, selected for absolute timelines.
Consequently, an ordinary large imported project was not using that optimized
path. This is code evidence of unnecessary work, not yet a claim that it
accounts for every delay in the user's media.

## Ten strategies

| ID | Origin | Strategy | Experiment or evaluation |
| --- | --- | --- | --- |
| L1 | Local trace | Use a persistent, active-interval decoder for ordinary sequential projects too | Compare the actual production route with an exact sequential interval adapter |
| L2 | Local trace | Retain a bounded five-source working set rather than two | Compare revisit traces, context opens, RSS and GPU memory; do not assume five is better |
| L3 | Local trace | Index viewport geometry rather than scanning all cached clips | Compare 200, 2,000 and 10,000-block draws, with exact pixels and drag behavior protected |
| L4 | Local trace | Binary-search active intervals and retain source lookup maps | Compare lookup/command-construction work independently and in the final UI |
| L5 | Local trace | Build only the needed render graph, never a whole-project concat for one frame | Compare whole-tail, five-block window and one-active-block commands |
| E1 | External | Byte-budgeted parked decoder residency and adjacent prewarming | Compare bounded residency; speculative background work must justify its contention and memory |
| E2 | External | Demand priority, cancellable/coalesced work and suspended prefetch | Existing latest-target behavior is the control; prefetch is not automatically a new improvement |
| E3 | External | Indexed exact-time lookup and viewport-driven view virtualization | Combine with L3/L4, keeping the complete model and selection state |
| E4 | External | Explicit lazy native-resource release independent of model metadata | Existing close/export-release behavior is protected; hiding a clip is not resource release |
| E5 | External | Active-set-only render graph materialization | Combine with L1/L5; only the sources contributing at the playhead should decode |

These are ten researched strategies, not ten independent implementations.
Several describe the same transferable mechanism. Benchmark meaningful
variants and combinations, rather than manufacturing duplicate experiments.

## External evidence and limitations

### Decoder residency and demand scheduling

- [NVIDIA NVDEC programming guide](https://docs.nvidia.com/video-technologies/video-codec-sdk/13.0/nvdec-video-decoder-api-prog-guide/index.html)
  documents decode/output surfaces and minimum decode-surface requirements.
  Decoder count is not a useful memory budget by itself. A 3840x2160 NV12
  surface is about 11.9 MiB before pitch/alignment; 32 such surfaces are about
  380 MiB. This is arithmetic, not a measured per-decoder allocation.
- [FFmpeg NVDEC implementation](https://github.com/FFmpeg/FFmpeg/blob/afead441653f3905e8c043878cc436b706c2f344/libavcodec/nvdec.c)
  and [decode pool sizing](https://github.com/FFmpeg/FFmpeg/blob/afead441653f3905e8c043878cc436b706c2f344/libavcodec/decode.c)
  show surface/thread budgets. Indexed revisions are not asserted to equal the
  workstation's exact FFmpeg build.
- [mpv demux defaults](https://github.com/mpv-player/mpv/blob/492bae0768f5e826991bf9fb222fa303371e8498/demux/demux.c)
  provide bounded byte/time readahead, not unlimited decoded-frame retention.
- [Blender prefetch](https://github.com/blender/blender/blob/main/source/blender/sequencer/intern/prefetch.cc)
  suspends speculative work during scrubbing and when the cache is full;
  its prefetch start is gated against playing/scrubbing. This supports
  contention-aware scheduling, not always-running background decoding.
- [Python Future cancellation](https://docs.python.org/3/library/concurrent.futures.html#concurrent.futures.Future.cancel)
  cannot cancel already-running work. Frame-boundary cooperative checks and
  explicit worker/resource disposal remain necessary.

No primary-source NVDEC concurrent-session limit for the RTX 5070 Ti was
established. An NVENC encode-session limit must not be described as a decode
limit. Two-left/two-right prewarming is a hypothesis, not an adopted default.

### Indexed views and resource release

- [Olive exact-time lookup](https://github.com/olive-editor/olive/blob/7e0e94abf6610026aebb9ddce8564c39522fac6e/app/node/output/track/track.cpp)
  implements binary search in `Track::GetBlockIndexAtTime`.
- [Pitivi previewers](https://github.com/pitivi/pitivi/blob/a6473c5844353eefd2495aa60584538a0b33661e/pitivi/timeline/previewers.py)
  materialize/reuse thumbnail widgets for the visible positions and remove
  stale widgets. `stop_generation` tears down its pipeline. View culling and
  decoder teardown are different operations.
- [MLT playlist](https://github.com/mltframework/mlt/blob/9076d2e24f660dabaa3ba8c60c3c737756a7e46a/src/framework/mlt_playlist.c)
  locates the playhead clip, with an `autoclose` path closing passed producers.
  Its locate implementation itself is linear, not an interval tree.
- [Olive decoder management](https://github.com/olive-editor/olive/blob/7e0e94abf6610026aebb9ddce8564c39522fac6e/app/render/rendermanager.cpp)
  has explicit old-decoder collection, rather than assuming hidden views free
  native resources.
- [Python bisect](https://docs.python.org/3/library/bisect.html)
  provides logarithmic searches. Searches must operate on stable sorted
  snapshots, not concurrently mutated lists.

No surveyed editor established a general immutable-revision or interval-tree
implementation. Those remain repository-specific algorithm choices.
Viewport unloading must never remove project segments or change export.
FrameStudio has no thumbnail-generation workload to disable in this scope.

### Active-set graph evaluation

- [MLT playlist](https://github.com/mltframework/mlt/blob/9076d2e24f660dabaa3ba8c60c3c737756a7e46a/src/framework/mlt_playlist.c)
  seeks the located clip rather than every playlist entry.
- [Blender render stack](https://github.com/blender/blender/blob/main/source/blender/sequencer/intern/render.cc)
  queries/render-evaluates contributing strips rather than decoding all
  project media for each output.
- [FFmpeg stream probing](https://github.com/FFmpeg/FFmpeg/blob/afead441653f3905e8c043878cc436b706c2f344/libavformat/demux.c)
  and [input seeking](https://github.com/FFmpeg/FFmpeg/blob/afead441653f3905e8c043878cc436b706c2f344/fftools/ffmpeg_demux.c)
  explain per-input work. The application should avoid creating irrelevant
  inputs, rather than relying on unused inputs being free.
- [FFmpeg framesync](https://github.com/FFmpeg/FFmpeg/blob/afead441653f3905e8c043878cc436b706c2f344/libavfilter/framesync.c)
  requests frames from participating inputs. Framesync details must not be
  generalized to every filter or described as measured CLI startup latency.

Commercial editor internals were not established. No proprietary latency
claim or copied editor source is part of this implementation.

## Early correctness experiment: reject naive backend substitution

The one-source paired control uses the existing eight-second high-detail
1080p/4K H.264 fixtures, a 1920x1080 RGBA canvas, and seeks at 0.5 and
1.533333 seconds. Both commands returned complete frames, but substituting
the existing synchronized composition path for the sequential path changed
approximately 2.5 million channels per frame. Maximum channel differences
were 45/47 at 1080p and 27/28 at 4K.

This is not acceptable as a speed optimization. The sequential renderer uses
its original contain/pad/zoom/crop filter path; the synchronized renderer uses
a different scaling and overlay/color-conversion path. The candidate must
reuse the sequential visual contract while reducing irrelevant inputs.

Raw paired artifact: `large-color-probe.json` in the session evidence directory.
These initial single-sample timings are diagnostic controls, not the final
performance comparison.

## Benchmark contract

- Compare small and large ordinary sequential projects, not just absolute
  timelines. Use 200 distinct regular source files with distinct inodes, not
  200 aliases of two files.
- Generated copies share encoded fixture content. State this explicitly:
  distinct physical inputs test open/context/graph scaling, not heterogeneous
  cameras, codecs or storage. Eight-second inputs do not establish a 40-hour
  media soak.
- Measure the same clip/offset in small and large projects; include first,
  middle, last, neighbor revisits, distant jumps, rapid latest-target changes
  and playback across source boundaries.
- Separate handler blocking, backend callback and matching GTK `after-paint`.
  Report medians, tails, errors/timeouts, resource use, decoder opens/evictions
  and source preservation. GTK paint is not physical monitor scanout.
- Use an exclusive workstation benchmark lock. Guard legacy whole-project
  subprocesses against runaway memory/time and label a guarded failure;
  never fabricate a latency from a timeout.
- Compare exact pixels/PTS against the original sequential one-active-clip
  reference, including framing, triplicate, SAR and fractional boundaries.
- Select the fastest correct supported combination, not the smallest isolated
  number or an approximate/lower-quality frame.

## Distinct-source graph comparison

`benchmarks/large_project_preview.py` runs fresh actual mapped GTK editors at
2, 20 and 200 sources for both resolutions. Each input is an eight-second
high-detail H.264 fixture copied to distinct regular files/inodes. The 200-file
case therefore contains 1,600 seconds of encoded media, not 40 hours.

This first comparison deliberately applies one decoder thread per input and
two filter threads to every case. It is **guarded, not unmodified production**.
The owned-process-tree RSS watchdog stops at 2,048 MiB, with possible sampled
overshoot. Values below are individual first/middle requests at the same
0.5-second source offset, including matching GTK after-paint.

| Input / sources | Whole-tail graph | Five-block window | One-active exact sequential graph |
| --- | --- | --- | --- |
| 1080p / 2 | 182 / 158 ms | 184 / 155 ms | 152 / 157 ms |
| 1080p / 20 | 638 / 453 ms | 264 / 270 ms | 153 / 153 ms |
| 1080p / 200 | Stopped during attach above RSS guard | 274 / 259 ms | 154 / 160 ms |
| 4K / 2 | 568 / 506 ms | 565 / 471 ms | 468 / 471 ms |
| 4K / 20 | Stopped during attach above RSS guard | 925 / 861 ms | 474 / 470 ms |
| 4K / 200 | Stopped during attach above RSS guard | 829 / 854 ms | 480 / 475 ms |

All completed CPU comparisons preserve the original sequential pixels.
At 200 sources, sampled application RSS is 467 versus 360 MiB for the
five-block versus active-only 1080p cases, and 816 versus 436 MiB at 4K.
The guarded whole-tail cases reach approximately 2,073/2,250 MiB before being
stopped; they have no completed preview latency to report.

The active-only graph is selected, not a five-video eager window. It avoids
opening, probing and negotiating irrelevant inputs, while preserving the
complete project model and saved/exported content. Its small/large uncached
latencies are comparable; this does not make an uncached 4K seek instant.

Raw command, case reports, source hashes and watchdog outcomes are in the
session's `large-project-benchmarks/summary.json` and case directories.

## Paused CPU budgets and actual CUDA alternatives

A separate serialized one-active-command comparison uses three repetitions at
0.5, 1.533333 and 4.533333 seconds, full 1920x1080 RGBA output, and exact hashes
against the original command. The bounded profiles use two filter threads and
one raw encoder thread. These are decoder/process timings, not GTK timings.

| Paused input decoder budget | 1080p median | 4K median | Exact pixels |
| --- | --- | --- | --- |
| Original automatic threading | 113.79 ms | 331.91 ms | Yes |
| One thread | 165.45 ms | 569.37 ms | Yes |
| Four threads | 110.48 ms | 351.03 ms | Yes |
| Eight threads | 113.02 ms | 319.04 ms | Yes |

Eight threads has the lowest total work at both resolutions
(974.46/2,767.54 ms across nine requests, versus 1,006.17/2,849.08 ms for
automatic threading), and the lowest 4K median. The small improvement over
automatic threading is not claimed as a universal tuning result. Production
paused commands use `min(8, available CPUs)`, filters two and raw encoder one.
Continuous playback retains its separately validated 4/2/1 budget.

The direct `-hwaccel cuda` candidate really selects the hardware decoder,
but all 12 initial GTK comparisons change pixels and are rejected. A follow-up
explicit YUV420P normalization fixes that difference: all 18 comparison
frames match, and debug diagnostics confirm CUDA in all 18 requests. However,
fresh-process medians are 293.97/379.13 ms at 1080p/4K, slower than the exact
CPU path. GPU use alone is not an optimization when process/device startup,
transfer and format negotiation outweigh the decode work.

Artifacts are `large-paused-thread-probe.json`,
`large-paused-cuda420-probe.json`, and the preserved probe script in the
session evidence directory.

The GPU-resident alternative explicitly sets CUDA output surfaces and performs
`hwdownload,format=nv12,format=yuv420p` only at the graph input. All eighteen
hardware-confirmed comparison frames remain exact. Its 254.01/369.82 ms
medians are still slower than the simultaneously compared production
eight-thread CPU command's 110.61/314.41 ms. Retaining run-up on GPU is useful
in the persistent native helper, but does not overcome fresh CLI/device
startup here. This candidate is also not selected.
Artifact: `large-paused-cuda-resident-probe.json`.

## Bounded native working set for absolute timelines

This is a separate absolute/synchronized native-helper experiment, not a
claim that native decoding is used by ordinary sequential imports. Five
distinct copied files are revisited at previously uncached 0.6/0.7-second
offsets after a 0.5-second first cycle. The canvas remains 1920x1080.

| Input / engine | Decoder / graph cap | Revisit median | Peak RSS | Sampled compute GPU memory | Outcome |
| --- | --- | --- | --- | --- | --- |
| 1080p CPU | 2 / 2 | 39.56 ms | 393 MiB | 0 | Retained CPU budget |
| 1080p CPU | 5 / 2 | 9.89 ms | 575 MiB | 0 | Not a safe global CPU policy |
| 1080p CUDA | 2 / 2 | 63.38 ms | 426 MiB | 352 MiB | Previous budget |
| 1080p CUDA | 5 / 2 | 11.77 ms | 550 MiB | 540 MiB | Faster residency |
| 1080p CUDA | 5 / 5 | 9.43 ms | 598 MiB | 540 MiB | Selected all-CUDA budget |
| 4K CPU | 2 / 2 | 126.68 ms | 1,045 MiB | 0 | Retained CPU budget |
| 4K CPU | 5 / 2 | Not measured | 1,746 MiB | 0 | Rejected above 1,536 MiB helper threshold |
| 4K CUDA | 2 / 2 | 145.15 ms | 684 MiB | 616 MiB | Previous budget |
| 4K CUDA | 5 / 2 | 25.82 ms | 1,145 MiB | 1,201 MiB | Faster residency |
| 4K CUDA | 5 / 5 | 15.45 ms | 1,203 MiB | 1,201 MiB | Selected all-CUDA budget |

Five decoders plus five graphs reduces measured native revisit work about
6.7x/9.4x versus the previous two/two CUDA budget. Every completed sample's
pixels match the CPU two-context reference; CUDA cap/cache variants also match
the reference physical PTS. The rejected CPU 4K case matches on its five
completed first-cycle frames, but has no successful revisit result.

Five is permitted only for all-CUDA decoder residency with the normal helper
RSS budget. CPU/mixed pools stay at two; CPU fallback prunes extra contexts
before CPU frame decoding. Smaller helper budgets also use two CUDA contexts.
Composition retention follows the selected engine budget, and release/close
clears all graphs, packet iterators and decoders. This is a bounded count plus
existing post-render RSS retirement, not a hard pre-allocation byte guarantee
for arbitrary codecs or resolutions.

Always-on adjacent prewarming is rejected. With five CUDA decoders and two
graphs, it increases total prewarm-plus-demand work from 521.92 to 596.37 ms
at 1080p and from 1,032.74 to 1,100.70 ms at 4K. Its apparently fast subsequent
demand stage merely moves work earlier and would compete with playback.
The selected policy is **lazy demand-loaded retention**, not automatically
loading two videos left and right of every cursor position.

Raw results are `large-residency-*` JSON files in session evidence.
GPU accounting samples compute allocations, not all graphics allocations.
Native render timings exclude worker IPC, texture upload and GTK painting.

## Indexed viewport and interval lookup

The view comparison uses identical Cairo pixels, twelve visible clips, sixty
samples and the preserved pre-task renderer. It measures indexed candidate
selection separately from the complete draw.

| Clips | Previous / indexed query median | Previous / indexed draw median |
| --- | --- | --- |
| 200 | 0.01487 / 0.00248 ms | 1.00485 / 0.98240 ms |
| 2,000 | 0.13562 / 0.00268 ms | 1.11073 / 0.99627 ms |
| 10,000 | 0.66293 / 0.00274 ms | 1.64775 / 1.07660 ms |

The index adds small one-time build cost: 25.41 versus 22.60 ms at 10,000
clips. It retains original paint order, deleted/selected styles, offscreen
selection and drag previews. Long overlapping rows can still require many
candidates; this is not a worst-case constant-time interval tree.

Near-end active-interval lookup medians improve from
0.00401/0.04159/0.19590 ms to 0.00039/0.00048/0.00056 ms at
200/2,000/10,000 intervals. Source command/cache lookups use a retained map.
These sub-millisecond improvements do not by themselves explain seconds of
preview delay; removing the whole-project decoder graph is the material fix.
The complete model remains loaded. No offscreen clips are removed or hidden
from saving/export.

Artifacts are `large-view-results.jsonl` and `large-lookup-results.json`.

## Final production large/small comparison

The final harness selects the real application factory, with no thread/GPU
injection, two full trace repetitions and boundary playback. Captured commands
confirm paused 8/2/1 and streaming 4/2/1 on this twelve-logical-CPU workstation.
The frame cache is not disabled, OS caches are not dropped, and cold below
means **preview-cache miss**, not cold filesystem/device startup.

| Input / sources | Matched first / middle cold seeks | Cache-miss paint median / p95 | Painted playback updates/s | Sampled owned RSS peak |
| --- | --- | --- | --- | --- |
| 1080p / 2 | 106.53 / 109.10 ms | 133.84 / 183.99 ms | 26.74 | 596 MiB |
| 1080p / 200 | 111.34 / 105.56 ms | 130.26 / 159.46 ms | 27.16 | 616 MiB |
| 4K / 2 | 268.90 / 272.06 ms | 358.38 / 577.33 ms | 17.98 | 842 MiB |
| 4K / 200 | 290.55 / 287.99 ms | 365.10 / 520.29 ms | 17.92 | 852 MiB |

Matched cold seeks use the same 0.5-second source offset. They are individual
samples, not a statistically powered claim that project size has exactly zero
cost. Conditional miss distributions contain different physical offsets and
sample counts; playback includes cold startup and a source boundary within
the 2.5-second observation, so it is below nominal 30 FPS, particularly at 4K.
RSS includes the edit/save/reopen functionality phases and temporary overlap
while replaced backends close asynchronously, unlike the earlier bounded
seek-only comparison. Reference-decode phases are excluded from reported
application RSS but remain inside the safety guard.

Small-project full-trace medians are approximately fourteen milliseconds
because many targets collapse onto the same two sources and fit in the
eight-frame cache. Large-project traces touch more distinct uncached targets.
Comparing that all-sample small median directly with a large miss median would
misrepresent the improvement. The matched cold rows and separate cache-hit
distributions are the appropriate comparisons.

All 156 evaluated legacy-reference images match; all eight rapid batches
paint the latest target with zero observed stale frames, and no sampled
boundary failures occur. All four 2/200-source edit/save/reopen charters retain
project edits, source hashes and complete source lists, invoke zero audio
scans and leave zero owned FFmpeg children after close. Paused handlers for
misses remain asynchronous; observer SHA256 work affects synchronous cache
hits and painting and is included, not subtracted from the table.

Raw reports and the reproduction command are in
`large-project-production-final/summary.json` in session evidence. These are
generated-media, short workstation observations, not heterogeneous cameras,
network storage, forty-hour playback or physical monitor presentation tests.

## Selected combination and remaining limits

Use L1/L5/E5 together: an exact active-only sequential graph with persistent
interval playback, rather than whole-tail or five-block eager graphs.
Use L2/E1/E4 together on the absolute native path: lazy five/five all-CUDA
residency within the existing helper retirement policy, two/two CPU/mixed
residency and explicit disposal. Keep E2's existing latest-demand priority,
cancellation and no speculative work. Use L3/L4/E3 for indexed visible
geometry, logarithmic interval lookup and retained source maps.

The material large-project problem was unrelated inputs being opened for a
single sequential frame, not merely a timeline widget scanning two hundred
items. Indexed view work helps much larger clip counts but is not credited
with the multi-second decoder fix.

Cold long-GOP 4K seeks still cost roughly 0.3-0.5 seconds in these traces and
source-boundary startup still reduces short painted-FPS samples. The original
sequential visual contract prevents blindly replacing this path with the
faster, different native composition graph. No universal instant preview,
steady 30-FPS boundary playback, fixed GDK timing warning, or forty-hour
stability guarantee is claimed.

Integration regression exposed a queued fallback warning overwriting an
invalid-frame-rate error. The preserved pre-task code passes the existing
functionality test; the candidate initially failed. The warning handler now
records the current warning while preserving higher-priority error text and
discarding stale generations. The original actual X11 functionality test and
new priority guards verify the fix; the assertion was not weakened.

## Local verification and automatic-validation decision

The final actual X11 `make check smoke PYTHON=.venv/bin/python` exits zero:
920 tests complete with nine explicit skips, all Python surfaces compile,
whitespace checks pass and the generated-media GTK smoke completes. The
separate X11 functionality command completes ten removal/error-priority and
PHASE-010 detail/edit/save/reopen/export/cancel/recovery charters. The
configured full static-analysis/churn command exits zero, with zero dependency
vulnerabilities and zero Bandit findings. Introduced formatting, duplication
and closure-binding findings were fixed without changing the baseline or
adding exclusions.

The configured **Rubber Duck / GPT-5.6 Luna / high / all-validation** validator
records **PASS for scoped local `automaticValidation` only**, with no new
blocking correctness defect found. This is agent validation, not human
confirmation or planning-record closure.

The original duplication baseline remains
`a2bd1fc526d47a69a8c24d6c9d26a5c7870c3c22e2ca512e5159939879963d55`.
The same pinned Makefile analyzer commands/rules run locally, but local real
X11/Python/GTK/FFmpeg runtime differs from CI's Xvfb/system runtime. Actual
provider/CI parity, publication, merge and global delivery readiness remain
unestablished. The branch and its pre-existing accepted changes remain local;
this request did not stage, commit or push them.

Raw terminal logs are `large-final-check.log`, `large-final-functionality.log`
and `large-final-static.log` in session evidence. The initial wrong-display
full-suite failure and introduced warning race are preserved in earlier logs,
not hidden or counted as passing.
