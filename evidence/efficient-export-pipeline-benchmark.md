# Efficient export pipeline benchmark

This report compares the protected per-segment route with adaptive grouped source preparation on the same generated mixed-source fixture. Each strategy has 3 repetition(s).

| Strategy | Status | Median wall (s) | Min (s) | Max (s) | Child CPU (s) | FFmpeg processes | Normalize processes | Interpolation calls | Boundary-safe | Source preserved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| per-segment | passed | 68.2237 | 68.175 | 68.3439 | 77.3358 | 11 | 3 | 2 | True | True |
| adaptive | passed | 67.8984 | 67.8779 | 68.0519 | 77.253 | 8 | 2 | 2 | True | True |

Selected strategy: `adaptive`.

Selected the fastest candidate that passed the technical integrity gates.

## Comparison

| Metric | Adaptive vs per-segment |
|---|---:|
| Wall-time change | 0.3253 seconds (0.48%) |
| FFmpeg process change | -3 |
| Normalization process change | -1 |
| Interpolation-call change | 0 |

## Stage timing

| Strategy | Stage | Median seconds |
|---|---|---:|
| per-segment | composing enhanced segments | 0.7451 |
| per-segment | concatenating enhanced segments | 0.0398 |
| per-segment | cut 1/1 | 0.0524 |
| per-segment | interpolation | 12.8759 |
| per-segment | interpolation segment 1/3 | 25.7872 |
| per-segment | interpolation segment 2/3 | 25.7501 |
| per-segment | normalizing source | 0.79 |
| adaptive | composing enhanced segments | 0.7518 |
| adaptive | concatenating enhanced segments | 0.0398 |
| adaptive | interpolation | 12.8606 |
| adaptive | interpolation segment 1/3 | 25.7916 |
| adaptive | interpolation segment 2/3 | 25.7287 |
| adaptive | normalizing source | 0.5225 |
| adaptive | normalizing source run | 0.208 |

The benchmark is hardware- and fixture-specific. It does not replace the target-workstation visual review or the resumability functionality tests. The operating-system file cache was not flushed between repetitions, and GPU values are point-in-time observations rather than averages.

## 2026-10-16 multitrack research and renewed experiment protocol

The results above are historical. They do not measure the current multitrack
renderer or the candidates below. Ownership remains PHASE-009 / FEAT-030,
FEAT-031 / TICKET-102 through TICKET-104.

Four explicitly requested initial research tracks ran in parallel: two
GPT-6.1 Sol workers examined the current architecture and experiment design;
two Haiku 5.5 high-reasoning workers examined community/papers and other
editors. Repository findings distinguish already implemented reuse from
new candidates. Equal native source-range preparations and shared video
inputs already exist and cannot be counted as a new gain.

The representative saved project was inspected read-only, without rendering,
changing it, or recording source names: three tracks, 114 included blocks,
35 active sources, 54 unique source ranges, 116 layout intervals, no triplicate
blocks, and about 493 seconds of output. Three tracks are active for about
458 seconds. Source range starts have a median of 2,330 seconds and a maximum
of 4,060 seconds. Consequently, common-triplicate-scale factoring alone cannot
explain an improvement for this workload. Source-prefix decoding, large graph
scheduling, and audio decoder reuse require separate measurements.

### Candidate and combination inventory

| Method | Reason to compare | Correctness or selection constraint |
|---|---|---|
| Share identical triplicate scale/format before split | Eliminate three equal scalers | Exact decoded frames; no benefit expected on non-triplicate edits |
| Share repeated audio inputs | Avoid a decoder per interval/source occurrence | Keep separate resampler/pan/limiter state; exact PCM |
| Bound complex-filter threading | Avoid graph oversubscription | Same codec settings and exact outputs; workstation-specific |
| Input-window seeking | Avoid decoding long unused source prefixes | Prove original PTS/frame selection, VFR, B-frames and sample phase; experimental until then |
| Lossless per-track slot layers | Parallel track work, then one final composition | Render into global slots, not already-cropped standalone reels |
| Lossless temporal interval groups | Bound graph size, enable finer recovery | Global cumulative frame lattice; one final delivery encode |
| Bounded parallel track/chunk jobs | Use otherwise idle cores | Account for per-job threads, memory and intermediate I/O |
| Derived geometry assets | Reuse equal framed content across outputs | Key actual geometry and sampling phase; lossless storage |
| GPU-resident geometry and encode | Avoid CPU work and transfers | Different scalers/encoder are not automatically quality-equivalent |
| Layered native/enhancement/composition caches | Invalidate only affected work | Existing native reuse retained; no stale recipe reuse |

Compare the low-risk independent candidates both alone and together. Compare
track/chunk architectures against the same current monolithic oracle, not
against the historical pre-dedup baseline. Audio remains continuous and
separate in video-only architecture experiments. Reject reduced-resolution
proxies, lossy intermediate generations, and output-contract changes as
speedup substitutes. Independently encoded delivery chunks can change GOP,
rate control and decoded pixels even with identical encoder settings.

### Verified external sources and evidence limits

- [FFmpeg CLI documentation](https://ffmpeg.org/ffmpeg.html) and
  [filter documentation](https://ffmpeg.org/ffmpeg-filters.html):
  input versus output seek, trim/reset timestamps, graph thread budgets,
  split/stack/overlay, framesync and concat constraints. These document
  semantics, not a measured winner for FrameStudio.
- [DaVinci Resolve 19 reference manual](https://documents.blackmagicdesign.com/UserManuals/DaVinci_Resolve_19_Reference_Manual.pdf),
  chapter 8, pp. 191-201: independent clip/node/output caches and delivery
  from render cache. The manual does not establish that Resolve exports
  each whole track independently. ProRes/DNxHR are not lossless.
- [MLT tractor source](https://github.com/mltframework/mlt/blob/a5639e5efc525c3754feae98791f8be8a4298428/src/framework/mlt_tractor.c),
  lines 423-449: requests track frames at one output position. This is
  evidence about MLT, not proprietary-editor internals.
- [ExCamera, NSDI 2017](https://www.usenix.org/conference/nsdi17/technical-sessions/presentation/fouladi):
  fine-grained parallel video work and encoder-state rebasing. Its custom
  VP8/cloud implementation and performance numbers are not a local FFmpeg
  speedup claim or an available H.264 rebasing primitive.
- [Scanner, TOG 2018](https://arxiv.org/abs/1805.07339),
  DOI `10.1145/3197517.3201394`: decode-aware graph scheduling, keyframe
  indexing, slicing/state resets and warm-up for temporal operators.
- [Halide, PLDI 2013](https://people.csail.mit.edu/jrk/halide-pldi13.pdf):
  the verified abstract separates algorithm from scheduling and the tradeoff
  between locality, parallelism and recomputation. Its image-processing
  measurements are not video-export predictions.

Reddit returned HTTP 403 and was not bypassed. VEGAS and Premiere primary
smart-rendering documentation could not be retrieved through their current
help indexes; no claims about their undocumented internals are used.
Community metadata without article bodies is not treated as verified advice.

### Fresh baseline and measurement rules

Source revision: `5f69d5441de9969450a1ac425e2693bc28bff85c`, with the
intentional pre-existing dirty worktree preserved. A 37-file SHA256 baseline
manifest is retained in the session artifacts as
`multitrack-baseline-manifest.json`
(SHA256 `1a77e6ee7144ca67ccdf74ff5513181541f1c6b3ada8daa87233950744b31951`).
It fingerprints the baseline before prototype integration; later planning
and report additions are not performance changes.

The current-worktree baseline command ran 31 tests successfully in 209.362
seconds, including generated-media per-item restart, multioutput recovery,
journal failure/kill behavior, timing, and GTK/CLI progress:

```sh
python3 -m unittest tests.test_editor_render_preparations \
  tests.test_editor_render_preparations_functionality \
  tests.test_editor_export_recovery \
  tests.test_editor_export_recovery_functionality \
  tests.test_editor_flexible_output_recovery_functionality
```

Automatic-validation profile: `rubber-duck / gpt-5.6-luna / high /
all-validation`. Runtime availability was established by successful execution
under this exact profile. Initial and refined planning reviews permit isolated
experiments, not unmeasured production adoption or final delivery readiness.

All comparison media and caches are experiment-owned. The user's paused full
export and checkpoints remain excluded. Use repeated, counterbalanced,
nonconcurrent measurements; distinguish fresh application caches from OS
page-cache state and from warm checkpoint reuse. Verify exact video/PCM
where promised, frame counts/timing, source preservation and publication
behavior. Record failed or unsupported rows rather than selecting from raw
time alone. Current candidate measurements and selection are pending.

## 2026-10-16 measured multitrack selection

This entry supersedes the pending-measurement status above. The selected
implementation is integrated locally on `perf/multitrack-export-20261016`;
commit, push, merge and lifecycle closeout are not implied.

### Correctness prerequisite

The first controlled screen failed even with the untouched renderer: 45
decoded frames instead of 56. The generated H.264 B-frame fixtures had zero
video/audio origins. Concat emitted 56 frames but only 43 distinct PTS because
it could not infer the duration of one-frame layout intervals; final CFR
encoding dropped frames. The final graph now assigns the planned reciprocal
time base and `setpts=N`. Ordered pre-encode pixels remain unchanged, with
contiguous timestamps and the correct encoded frame count.

The original failed report remains `multitrack-screen.json` in session
artifacts. It is not a speed baseline. All measured comparisons below use the
same correctness-only repaired baseline, retaining previous deduplication and
checkpoints. Video/mux preparation recipe version changes from 2 to 3; native,
upscale, interpolation and independent audio identities remain unchanged.
Strict final receipt revalidation remains enabled.

### Actual selected production policy

- With at least three distinct consumed video paths, use two complex-filter
  threads and one decoder thread per input. Decoder flags precede their
  respective `-i`; final encoder options are unchanged. One/two-path renders,
  native processing, muxing and output validation retain automatic behavior.
- Share triplicate scale/format only when all crop plans have equal scale
  dimensions. Preserve full chroma before odd-width crops and retain the
  original branches for unequal dimensions.
- Share equal audio paths through explicit `asplit`; preserve separate
  per-occurrence trim, resampling, pan, mixing and limiter state.

The final comparison disables harness thread overrides (`auto`, decoder `0`)
and measures these exact production source files. Earlier global-thread
screens also capped unrelated FFmpeg validation/mux stages and are not the
adoption measurements. Candidate file hashes and supplemental contract checks
are persisted in [`multitrack-render-results.json`](multitrack-render-results.json).

| Fresh workload | Corrected baseline median (range), s | Selected median (range), s | Speedup | Less time |
| --- | ---: | ---: | ---: | ---: |
| 3 tracks / 35 sources / 114 blocks / 116 intervals, no triplicate | 11.468 (11.396-12.062) | 8.027 (7.933-8.057) | 1.43x | 30.0% |
| 3 tracks / 3 sources / triplicate, 4 s output | 2.525 (2.514-2.692) | 1.776 (1.776-1.782) | 1.42x | 29.7% |
| Repeated ranges / 6 native FPS preparations, 2 s enhanced output | 3.628 (3.611-3.811) | 3.552 (3.537-3.558) | 1.02x | 2.1% |

Each value is the median of three sequential counterbalanced trials, with no
other benchmark/test workers running. Power mode was temporarily `performance`
and restored to `power-saver`. Hardware: Ryzen 5 9600X, 6 cores/12 logical CPUs,
RTX 5070 Ti; FFmpeg n9.0.2, Python 3.14.8. Source fixtures are 320x180 H.264
B-frame video with stereo PCM; delivery remains 1920x1080 H.264/AAC. The large
fixture has 344 output frames, not the real project's 493-second duration,
mixed source resolutions/rates or long source prefixes.

Fresh AV timing includes fixture analysis, planning and verified AV rendering;
fixture generation and post-timing decoded-signature scans are excluded.
These numbers are not whole-batch timings including individual source reels,
nor a prediction for the paused real project or AI inference throughput.

The large fixture's audio inputs fall from 342 to 35. Audio sharing alone is
not a standalone speed winner (11.585 s versus 11.468 s total); the measured
combination wins. Median sampled aggregate process-tree RSS falls from
8.38 GB to 6.47 GB, and triplicate RSS from 1.67 GB to 1.09 GB. This sampling
sums resident pages across processes and can double-count shared pages; it is
not an allocated-physical-memory or universal memory-bound claim.

### Alternatives and combinations actually tried

| Experimental strategy | Comparator scope | Median result |
| --- | --- | --- |
| Lossless per-track slot layers, 3 workers | 5 s static video only; identical explicit final encoder threads | 3.529 s versus 1.044 s monolithic, 3.38x slower |
| Lossless temporal chunks, 3 workers | Same controlled video-only oracle | 4.290 s, 4.11x slower |
| Combined track/time shards, 3 workers | Same controlled video-only oracle | 3.911 s, 3.75x slower |
| Input-window seek | One generated H.264 source, window at 113 s | 1.223 s versus 1.575 s production-auto baseline |
| NVDEC without changing CPU geometry/encoder | Same late-window fixture | 1.947 s, slower |
| Seek + NVDEC + sharing | Same late-window fixture | 1.385 s; slower than seek alone |

Track/chunk prototypes render the real global slot geometry, not cropped
standalone full-canvas reels. Intermediates are lossless FFV1/yuv444p, followed
by one delivery encode. Their preparation/verification/I/O cost outweighed
parallelism here. The temporal prototype still processes preceding prefixes;
these static video-only results do not prove every future chunk scheduler
would lose on long dynamic projects.

Seek remains an isolated prototype: its generated single-source guard and
additional B-frame/VFR/offset checks do not establish a general production
multisource/discontinuity/prepared-input policy. It was not enabled silently.
No NVDEC, GPU scaler/encoder or lossy intermediate was adopted.

### Checkpoint observations and equivalence

Enhanced baseline/selected runs retained exact ordered decoded frame hashes
and signed 32-bit stereo PCM hashes/sample counts in fresh, checkpoint-warm
and controlled stop-after-video/resume modes. Selected remaining-render medians
were 0.048 s for a completed AV checkpoint and 0.459 s after the video
checkpoint. These timers exclude warm preflight/planning, so they must not be
compared with fresh 3.552 s as a full-export speedup.

The architecture recovery demonstration retained a finished shard with the
same artifact hash and completed remaining shards after reopening. Production
continues using its existing individually verified native/enhancement and
video/audio/mux checkpoints rather than adopting slower shard intermediates.
An interrupted unfinished encoder/inference item can still require redoing
that item; no frame-level process-state resume is claimed.

Supplemental checks probed every retained encoded output for matching
H.264/AAC codec, stereo layout, SAR and audio/video time bases, rehashed
decoded artifacts and asserted the planned frame and PCM sample counts.
Original raw reports are unchanged. The harness now records these extra
contract fields and rejects wrong decoded counts independently of parity.
It also exits nonzero if no eligible exact fresh baseline/winner exists.

Automatic-validation owner: `rubber-duck / gpt-5.6-luna / high /
all-validation`. Bounded reviews approved the correctness repair and measured
combination for integration, not final delivery readiness. Final quality,
functionality and review evidence belongs in the implementation record.

### Reproduction

Use the preserved **correctness-only baseline snapshot**, not the current
optimized checkout as its own baseline:

```sh
python3 benchmarks/multitrack_render_benchmark.py \
  --baseline-root "$CORRECTED_BASELINE_ROOT" \
  --video-candidate framestudio/video_compositor.py \
  --audio-candidate framestudio/audio_compositor.py \
  --tracks 3 --source-count 35 --intervals 38 --stagger-frames 1 \
  --duration 0.3 --strategies baseline,video,audio,combined \
  --thread-budgets auto --decoder-threads 0 --trials 3 \
  --report "$OWNED_RESULTS/large.json" \
  --artifact-root "$OWNED_RESULTS/large-artifacts"
```

The baseline snapshot, original failed/corrected screens, global-thread
screens and complete raw final reports remain in session artifacts. The
portable JSON record includes their hashes, final trial distributions,
sampled resource/stage observations and supplemental verification. The private
project, source media and paused export checkpoints were not used as benchmark
fixtures or modified.
