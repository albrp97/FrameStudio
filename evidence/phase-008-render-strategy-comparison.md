# PHASE-008 mixed-FPS render strategy comparison

## Scope and protocol

This report covers TICKET-069 through TICKET-072. The benchmark is a
dependency-free Python harness using the repository's FFmpeg fallback route;
it does not change production routing.

- Fixture: two generated landscape MP4 sources, `source_a` at 10 FPS and
  `source_b` at 15 FPS, each 1.2 seconds, 320x180, H.264/yuv420p, AAC
  48 kHz stereo.
- Target: 30/1 FPS, 320x180 MP4, H.264/yuv420p, AAC 48 kHz stereo.
- Strategy A: prepare both sources at the minimum (10 FPS), concatenate the
  prepared master, then run one `minterpolate` enhancement pass.
- Strategy B: prepare each source at its native FPS, enhance each separately
  to 30 FPS, then concatenate the enhanced outputs.
- One cold repetition per strategy; no cache warm-up. Both routes use the same
  generated sources, output profile, target FPS, and verification gates.
- Gates: FFprobe metadata/frame count, FFmpeg decode/playability, SHA-256 source
  preservation, and work-artifact cleanup. Subjective quality is not inferred
  from metadata.

Command:

```sh
python3 benchmarks/render_strategy_benchmark.py \
  --report evidence/phase-008-render-strategy-comparison.json
```

## Measured results

| Measure | Strategy A: concat-first | Strategy B: per-source |
| --- | ---: | ---: |
| Stage wall time (seconds) | 0.5927 | 0.5867 |
| Intermediate bytes | 280,999 | 301,164 |
| Final bytes | 145,252 | 246,805 |
| Output duration | 2.400000 s | 2.400000 s |
| Output FPS / frames | 30 / 72 | 30 / 72 |
| Audio | AAC, 48 kHz, stereo | AAC, 48 kHz, stereo |
| Decode/playability | passed | passed |
| Frame and target-rate checks | passed | passed |

Strategy A stages were preparation of `source_a` (0.0490 s, 72,844 bytes),
preparation of `source_b` (0.0523 s, 74,352 bytes), prepared concatenation
(0.0665 s, 133,803 bytes), one master enhancement (0.3599 s, 145,252 bytes),
metadata/frame verification (0.0343 s), and playability verification
(0.0307 s). Strategy B stages were native-FPS preparation of `source_a`
(0.0505 s, 72,844 bytes), native-FPS preparation of `source_b` (0.0503 s,
88,407 bytes), enhancement of `source_a` (0.1859 s, 73,297 bytes),
enhancement of `source_b` (0.1722 s, 66,616 bytes), final concatenation
(0.0728 s, 246,805 bytes), metadata/frame verification (0.0286 s), and
playability verification (0.0264 s).

The child-process CPU/RSS observations are recorded per stage in the JSON
report. RSS is a cumulative Linux child-process observation, not a
hardware-independent peak claim.

## Correctness, cleanup, and quality

Both strategies produced a playable output with matching 30 FPS and 72-frame
results, exact 2.4-second duration, and matching audio metadata. Generated
source hashes were unchanged. The harness removed its work directory after the
run; no source or production files were modified.

No subjective visual review was performed by the automated run. Manual review
must separately inspect motion continuity, the source boundary, audio sync,
and interpolation artifacts. The harness intentionally records this as a
quality-review gap rather than converting metadata into a quality score.

## TICKET-072 decision

**Decision: retain the current concat-first production route unchanged and
defer conditional routing.** Strategy B was 0.0060 seconds (about 1.0%) faster
in this single synthetic run, used about 7.2% more intermediate storage, and
produced a larger final file in this encoding profile (246,805 vs 145,252
bytes). The small timing difference does not justify changing production
routing.
Both routes passed the measured integrity gates, so the small timing difference
does not justify production routing changes or a second default. There is no
automated visual-quality evidence, no RVE run, and only one low-resolution
fixture/repetition; these limits prevent a universal conclusion.

Bounded follow-up: run repeated target-workstation comparisons with real
representative media, RVE when its validated artifacts are available, and
independent subjective boundary/motion review before reconsidering conditional
routing. This report does not enable a third strategy or alter exporter code.

## Validation and limitations

Focused harness tests:

```sh
python3 -m unittest tests.test_render_strategy_benchmark
```

Focused export/interpolation regressions and the complete repository suite also
passed:

```sh
python3 -m unittest tests.test_render_strategy_benchmark \
  tests.test_editor_smart_render tests.test_editor_interpolation \
  tests.test_editor_export_execution tests.test_editor_export
python3 -m unittest discover -s tests
```

The generated-media benchmark passed for both strategies. Environment:
Linux, Python 3.14.7, FFmpeg and FFprobe available. RVE artifacts were not
exercised. Results are specific to this workstation, generated fixture, single
repetition, and FFmpeg fallback backend; they are not a universal performance
claim. `make smoke` was not run because its repository command writes fixtures
under `/tmp`, which is outside this task's permitted file-operation boundary.

## Remediation addendum — 2026-08-26

The benchmark verification gate now checks the declared protocol's duration,
dimensions, H.264 video codec, yuv420p pixel format, FPS, frame count, AAC
audio codec, audio presence, audio sample rate, stereo channel count, and MP4
container. Cleanup is explicit rather than advisory: removal errors or a
remaining work directory fail the cleanup gate. Source-hash preservation and
cleanup are combined with both strategy statuses into an explicit top-level
benchmark status.
The benchmark command now exits nonzero whenever that terminal status is not
`passed`, so automation cannot treat a failed gate as a successful run.
Missing FFmpeg/FFprobe runs now produce the same structured cleanup and
terminal-status fields instead of raising while printing the result.

The regenerated benchmark passed with both strategies and these global gates:

```text
status: passed
strategies_passed: true
source_preservation_passed: true
cleanup_passed: true
```

Current rerun totals were 0.5653 seconds for Strategy A and 0.5581 seconds for
Strategy B on the same short generated fixture. The output-integrity and
playability stages passed for both routes. New unit tests cover each metadata
mismatch plus cleanup and global-gate failures.

## Remediation addendum — 2026-08-26 (final verification)

The CLI now rejects `--target-fps <= 0` before invoking the benchmark, and the
callable benchmark path rejects the same invalid target. The regression suite
covers the CLI guard and confirms that the benchmark is not started for an
invalid rate.

The regenerated report passed all strategy, metadata, playability, source
preservation, and cleanup gates:

```text
status: passed
Strategy A total wall time: 0.732 seconds
Strategy B total wall time: 0.731 seconds
```

The final repository quality run passed the complete 290-test suite and all
configured formatting, lint, type, complexity, duplication, dependency,
security, and churn checks. The benchmark remains a synthetic single
workstation comparison and does not replace subjective motion, boundary, or
audio-sync review.

## Remediation addendum - 2026-08-26 (protected export cancellation)

The final review's cancellation findings were remediated without changing the
selected concat-first production route. FFmpeg progress execution now
terminates silently-running processes through bounded escalation, VapourSynth
and RVE waits remain cancellation-aware and bounded, and GUI cancellation is
serialized with the final verified publication check and atomic replacement.

The focused cancellation regression suite passed four tests. The complete
quality suite passed 304 tests and all configured local gates. The CLI contract
suite passed 31 tests, generated-media smoke passed, and this report was
regenerated with both Strategy A and Strategy B plus global cleanup and
integrity gates reporting `passed`.

**Status:** passedWithConcerns

The benchmark remains a synthetic, single-workstation comparison and does not
replace target-workstation GTK validation, physical focus gestures, visual
motion review, or real RVE/model-quality validation. No remote or upstream is
configured.

## User-validation addendum - 2026-08-26

The target-workstation handoff requested an active export cancellation check,
confirmation that cancellation leaves the destination and partial outputs
safe, followed by a normal playable export and source-preservation check.

**User response:** `PASS`

**Status:** passed

No separate evidence paths were supplied with the response. The automated
benchmark remains synthetic and the real RVE/model-quality limitation remains
separate from this user-validation result.

## Prior artifact snapshot — 2026-08-26

The previous machine-readable report contained a later cold-run snapshot than
the earlier prose addenda:

| Measure | Strategy A: concat-first | Strategy B: per-source |
| --- | ---: | ---: |
| Total wall time | 0.8367 s | 0.7918 s |
| Intermediate bytes | 280,999 | 301,164 |
| Final bytes | 145,252 | 246,805 |

Both strategies reported `passed` with 2.400000 seconds, 30 FPS, 72 frames,
AAC 48 kHz stereo, playable output, unchanged source hashes, and successful
cleanup. The earlier recorded snapshots (0.5927/0.5867, 0.5653/0.5581, and
0.732/0.731 seconds for A/B) remain separate single-run measurements. The
stream-copy rerun below supersedes this snapshot for the concat-size
comparison.

## Stream-copy concat rerun — 320x180, 30 FPS — 2026-08-26

The benchmark concat stage now uses the repository's
`build_concat_copy_command`: FFmpeg's concat demuxer with `-c copy`. It no
longer re-encodes the prepared or FPS-enhanced streams, matching the
production smart-render join and the inference route's audio-preserving
behavior.

| Measure | Strategy A: concat-first | Strategy B: per-source |
| --- | ---: | ---: |
| Total wall time | 0.8717 s | 0.6832 s |
| Intermediate bytes | 293,169 | 301,164 |
| Final bytes | 154,373 | 138,629 |
| Output duration | 2.400000 s | 2.421354 s |
| Output FPS / frames | 30 / 72 | 30 / 72 |
| Audio | AAC, 48 kHz, stereo | AAC, 48 kHz, stereo |
| Integrity/playability/source/cleanup gates | passed | passed |

Strategy B was 0.1885 seconds faster (21.6%) and its final file was 15,744
bytes smaller (10.2%). Its intermediate workspace was 7,995 bytes larger
because it retains native-rate and per-source enhanced artifacts. The
21.354 ms duration difference is within the benchmark's 50 ms tolerance and
comes from stream-copy timestamp handling.

For this narrow, matched FFmpeg fallback experiment, Strategy B is the better
candidate: it preserves each source's native frame rate before enhancement,
avoids a final re-encode, and is both faster and smaller. Keep this as a
conditional recommendation rather than changing the broad production default
yet: the run is one synthetic low-resolution repetition, does not exercise
RVE, and does not cover mixed dimensions or composition effects that may
require a final re-encode.

## Default 1080p/60 FPS rerun — 2026-08-26

The benchmark defaults now match the requested editor output: generated
1920x1080 sources, 60 FPS target, and the repository's default FFmpeg
`minterpolate` interpolation command. Both final outputs contained 144 frames
at 60 FPS and passed metadata, playability, source-preservation, and cleanup
gates.

| Measure | Strategy A: concat-first | Strategy B: per-source |
| --- | ---: | ---: |
| Total wall time | 51.8419 s | 39.6163 s |
| Intermediate bytes | 4,280,899 | 4,734,621 |
| Final bytes | 2,233,222 | 2,287,886 |
| Output duration | 2.400000 s | 2.421354 s |
| Output dimensions | 1920x1080 | 1920x1080 |
| Output FPS / frames | 60 / 144 | 60 / 144 |
| Video / pixel format | H.264 / yuv420p | H.264 / yuv420p |
| Audio | AAC, 48 kHz, stereo | AAC, 48 kHz, stereo |

Strategy B completed 12.2256 seconds faster (23.6%), but its final file was
54,664 bytes larger (2.4%) and its intermediate workspace was 453,722 bytes
larger (10.6%). The 21.354 ms duration difference remains within the 50 ms
benchmark tolerance and is caused by stream-copy timestamp handling.

At the requested 1080p/60 FPS default, Strategy A is now the recommended
production default: it is materially faster and produces the smaller final
file. Strategy B still preserves each source's native FPS before interpolation
but has no size or time advantage in this higher-resolution run. This remains
a single cold run using synthetic 1.2-second sources and the FFmpeg fallback;
RVE performance and visual quality were not measured.
