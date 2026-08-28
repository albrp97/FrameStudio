# Delivery Evidence: TICKET-078

**Ticket:** TICKET-078 - Expand Cross-Model Restoration Benchmark
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Phase:** PHASE-008
**Feature:** FEAT-027
**Planning chain:** `OBJ-001 -> SCOPE-001 -> CAP-005/CAP-011/CAP-012 ->
PHASE-008 -> FEAT-027 -> TICKET-078`
**Status:** verifying
**Branch:** `ticket/phase-008-responsive-preview-media-strategy`
**Base revision:** `93b49e8bd3d93dab3cdf00a6c315d116cadf9998`
**Evidence date:** 2026-08-27

## Context and boundary

This record covers the implementation and local execution of the approved
cross-model restoration benchmark. It is research-only. It does not add a
production editor route, change an export default, add runtime dependencies,
download proprietary software, or modify source media.

Generated benchmark media, logs, contact sheets, and reports are retained
outside the repository at:

`~/Documents/edit/restoration-cross-model-20260827/`

Private source paths and model locations are redacted from committed evidence.
External model files remain local user data and are not copied into the
repository.

## Acceptance requirements

- The manifest contains explicit rows for Topaz Gaia, Nomos2,
  `4xNomos2_otf_esrgan`, EDVR, BasicVSR, TecoGAN, Real-ESRGAN, and Video2X,
  plus controls and the prior RVE baseline.
- The same fixture, output target, frame-rate policy, color policy, audio
  policy, integrity gates, and reporting fields are applied to every runnable
  candidate.
- Video2X is recorded as a pinned wrapper/runtime with its underlying model,
  backend, and filtering mode; it is not counted as an independent model.
- Every unavailable, failed, excluded-license, or non-comparable candidate
  remains visible with an explicit reason.
- Reports contain measured performance, output metadata, resource telemetry,
  availability/license data, visual-review placeholders or observations,
  contact sheets, and explicit source-preservation evidence.
- No production behavior, dependency manifest, project schema, or original
  source media is changed; the benchmark harness, tests, documentation, and
  planning/evidence records are in scope.

## Protected regression flows

- Existing test, compile, contract, smoke, quality, and legacy-script behavior.
- Source preservation and redacted local-data handling.
- Atomic/partial-output semantics used by any reused FFmpeg or RVE path.
- Existing RVE/RIFE FPS behavior and editor/export routing.

## Evidence entries

### E-078-BASELINE-001 - Protected repository baseline

- **Timestamp:** 2026-08-27
- **Category:** baseline
- **Requirement:** Existing repository behavior is known before benchmark
  implementation changes.
- **Command/steps:** `make check PYTHON=.venv/bin/python`
- **Expected:** Existing tests, Python compilation, and diff checks pass.
- **Observed:** 312 tests passed; compilation passed; `git diff --check`
  passed. The baseline emitted an existing GLib deprecation warning only.
- **Status:** passed
- **Artifacts:** command output in session evidence

### E-078-ENVIRONMENT-001 - Candidate runtime discovery

- **Timestamp:** 2026-08-27
- **Category:** baseline
- **Requirement:** Runtime, model, and license availability are explicit
  before candidate execution.
- **Command/steps:** Probe FFmpeg, FFprobe, NVIDIA telemetry, VapourSynth,
  Video2X, Real-ESRGAN, local model files, and the existing RVE checkout
  without downloading or modifying external files.
- **Expected:** Available capabilities are recorded; missing capabilities are
  retained as unavailable or non-comparable rows.
- **Observed:** FFmpeg, FFprobe, `nvidia-smi`, VapourSynth, the existing RVE
  checkout, and local RVE restoration weights are available. No `video2x`,
  Real-ESRGAN CLI, Topaz Gaia installation, Nomos2 weights, EDVR weights,
  BasicVSR weights, or TecoGAN weights were found in the local search scope.
- **Status:** passedWithConcerns
- **Accepted warning:** Candidate availability is workstation-specific and
  the benchmark must not infer quality from an unavailable runtime.

## Implementation evidence

Implementation, focused tests, candidate execution, output verification,
contact-sheet generation, visual review, static analysis, and user-validation
entries will be appended here in chronological order. Earlier entries are
never rewritten to hide a failure.

## Readiness (initial; superseded by appended latest status)

**Technical readiness:** pending implementation and benchmark execution.
**User validation:** pending.
**Delivery readiness:** not ready; the configured user-validation, review,
local-quality, and remote-check gates are not terminal.

## Open blockers and accepted warnings

- Direct requested model runtimes and weights may remain unavailable; each
  candidate must retain a terminal status and reason.
- Topaz Gaia requires a licensed local installation and repeatable execution
  path; no proprietary software may be downloaded or redistributed.
- TICKET-077 remains `verifying`; its existing fixture and evidence are used
  as the declared baseline, but its pending user response remains a planning
  dependency for final recommendation closure.
- No repository remote/upstream is configured, so remote checks will be
  unavailable unless repository configuration changes.

## Subsequent evidence (append-only)

### E-078-IMPLEMENTATION-001 - Research benchmark harness and matrix

- **Timestamp:** 2026-08-27
- **Category:** implementation
- **Requirement:** The approved candidate matrix is executable, comparable,
  and explicit about unavailable or non-comparable rows without changing
  production behavior.
- **Changed surfaces:** `benchmarks/restoration_benchmark.py`,
  `benchmarks/restoration_candidates.json`, `tests/test_restoration_benchmark.py`,
  `Makefile`, `README.md`, and the linked planning records.
- **Observed:** The harness creates or reuses one declared fixture, applies the
  common 1920x1080 contain/H.264/yuv420p/AAC delivery contract, preserves
  native source FPS, records cold and repeated warm timings, samples GPU
  telemetry, verifies outputs, redacts local paths in commands/logs, creates
  fixed 7s/22s/37s contact-sheet windows, and retains every requested
  candidate with a terminal availability status. Video2X is represented as a
  wrapper row rather than an independent model.
- **Status:** passed

### E-078-TEST-001 - Focused and protected regression validation

- **Timestamp:** 2026-08-27
- **Category:** regression
- **Command/steps:** `python3 -m unittest tests.test_restoration_benchmark -v`;
  `python3 -m unittest discover -s tests`; repository compilation and
  `git diff --check`; pinned `make quality PYTHON=.venv/bin/python`.
- **Expected:** Benchmark contracts and protected repository behavior pass
  without introducing lint, complexity, security, duplication, or quality
  gate findings.
- **Observed:** Focused benchmark tests passed (8); the full repository suite
  passed (320); compilation and diff checks passed; pinned quality checks
  passed, including Ruff, complexity, Bandit, pip-audit, and duplication
  thresholds. The warm-run contract was tightened to require at least one
  timed warm run and now defaults to two.
- **Status:** passed

### E-078-BENCHMARK-001 - Cross-model matrix execution

- **Timestamp:** 2026-08-27
- **Category:** integration
- **Command/steps:** Run the benchmark with the reused TICKET-077 fixture,
  `--warm-runs 2`, NVIDIA telemetry, and the declared output directory.
- **Expected:** Every manifest row remains visible; runnable rows receive the
  common native-FPS output contract, repeated timing, telemetry, integrity
  checks, and review artifacts.
- **Observed:** The 24-row report is `passedWithConcerns`: 6 FFmpeg controls
  passed, 9 requested external candidates are explicitly unavailable, 9
  historical RVE rows are explicitly not comparable, and 0 rows failed.
  The passed controls have two warm runs with median and spread; for example,
  Lanczos measured 4.0047 seconds cold, 3.95205 seconds warm median, 0.1445
  seconds spread, 268.934 processed FPS, and 11.242x real-time factor.
  Output integrity, contact-sheet generation, cleanup, and source preservation
  passed. The source hash remained unchanged before and after all runs.
- **Artifacts:** `~/Documents/edit/restoration-cross-model-20260827/`
  (`restoration-cross-model.json`, `restoration-cross-model.md`,
  `candidate-availability.csv`, `visual-review-template.md`,
  `contact-sheets/`, `commands/`, `logs/`, `outputs/`,
  `source-preservation.json`)
- **Status:** passedWithConcerns
- **Accepted warning:** This workstation has no licensed Topaz Gaia install,
  requested external runtimes/checkpoints, or pinned Video2X execution path.
  Reused RVE outputs remain historical because their 1,079 CFR frames do not
  match this fixture's 1,077 native frames.

### E-078-STATIC-001 - Deterministic quality and parity review

- **Timestamp:** 2026-08-27
- **Category:** quality
- **Command/steps:** `make quality PYTHON=.venv/bin/python`, with the
  repository workflow at `.github/workflows/quality.yml` used as the PR
  comparison.
- **Expected:** The local quality suite and the configured PR command agree,
  with no introduced formatter, lint, type, complexity, dependency, security,
  or duplication findings.
- **Observed:** The suite passed with 321 tests. Compilation, diff checks,
  Ruff format/lint, mypy (including the benchmark module), complexity,
  dependency checks, pip-audit, Bandit, and churn completed successfully.
  jscpd reported 1.9756% duplication, 0 new clones, and 0 new duplicated
  lines. Pip-audit reported no known vulnerabilities and Bandit reported no
  findings. The local command matches the workflow's `make quality
  PYTHON=.venv/bin/python` invocation; no repository remote is configured for
  remote-check execution.
- **Status:** passedWithConcerns
- **Accepted warning:** Remote provider checks are unavailable because the
  worktree has no configured upstream; this is a delivery-gate limitation,
  not a local quality failure.

### E-078-REVIEW-001 - Scope, architecture, and delivery review

- **Timestamp:** 2026-08-27
- **Category:** review
- **Scope reviewed:** TICKET-078 acceptance criteria, manifest, benchmark
  harness, focused tests, README/Makefile wiring, planning synchronization,
  generated report, and static-analysis artifacts.
- **Observed:** The requested candidates are represented explicitly;
  Video2X is a wrapper row with its underlying model still required; missing
  runtimes and license capabilities remain visible; production editor/export
  routing, project schema, source media, and dependency manifests were not
  changed. No high-confidence introduced code, security, dependency-boundary,
  or test-coverage blocker was found. Planning indexes and open-record status
  now agree on `TICKET-078` being `verifying`.
- **Blockers:** Required human validation has not been returned. The
  configured remote-check gate cannot run without a repository remote.
- **Follow-up:** To obtain a true neural-model ranking, install and pin the
  requested runtimes/checkpoints, declare Video2X's underlying model/backend,
  and rerun the same fixture. Rerun RVE under the native-frame contract
  instead of using the historical CFR outputs.
- **Status:** passedWithConcerns

### E-078-USER-VALIDATION-001 - Review handoff

- **Timestamp:** 2026-08-27
- **Category:** functionality
- **Setup:** Inspect the uncommitted artifact directory
  `~/Documents/edit/restoration-cross-model-20260827/`.
- **Steps:** Open the Markdown and JSON reports, availability CSV, six
  normalized control outputs, available RVE contact sheets, and the visual
  review template. Compare each available output at 7s, 22s, and 37s for
  blocking/ringing, noise/detail, faces/text, color/halos, hallucination,
  flicker, motion stability, and boundary behavior. Confirm that every
  unavailable or non-comparable candidate has an explicit reason and that
  the Video2X row identifies its wrapper/model/backend requirements.
- **Expected visible result:** The report clearly separates measured
  performance from visual observations and does not rank unavailable or
  non-comparable candidates. The common target profile is 1920x1080,
  native source FPS, H.264/yuv420p, and AAC 48 kHz stereo.
- **Expected persisted/external effect:** `source-preservation.json` shows
  an unchanged source hash; no repository or original-media mutation occurs.
- **Cleanup:** Keep the artifacts for review or remove only the generated
  comparison directory after inspection; never remove the original source.
- **Evidence response required:** Return exactly one of:

  ```text
  PASS: every required check succeeded; evidence: <paths or notes>
  FAIL: <failed check and observed result>
  BLOCKED: <missing service, data, permission, or capability>
  NOT APPLICABLE: <reason and approval>
  ```

- **Status:** pending

## Current readiness (latest)

**Technical readiness:** passedWithConcerns; implementation, benchmark
execution, source preservation, output integrity, tests, and local quality
are terminal.
**Review readiness:** passedWithConcerns; no introduced high-confidence
finding blocks the ticket, but unavailable candidates and historical
non-comparable RVE rows remain explicit limitations.
**User validation:** pending the required response above.
**Delivery readiness:** blocked until user validation and the configured
remote-check policy are resolved; no commit, push, or pull request was created.

### E-078-STATIC-002 - Final post-report-change quality rerun

- **Timestamp:** 2026-08-27
- **Category:** quality
- **Command/steps:** `make quality PYTHON=.venv/bin/python` after adding the
  warm-spread column to the human-readable report.
- **Observed:** 321 tests passed; compilation, diff checks, Ruff, mypy,
  complexity, dependency checks, pip-audit, Bandit, duplication, and churn
  all completed successfully. The benchmark module remains included in the
  configured type-check scope.
- **Status:** passed

### E-078-BENCHMARK-002 - Verified neural supplemental executions

- **Timestamp:** 2026-08-27
- **Category:** functionality
- **Requirement:** Runnable neural candidates receive the same native-FPS
  fixture and final output contract, while adapter behavior and failures
  remain explicit.
- **Command/steps:** Run the temporary RVE CUDA runner against the declared
  1920x1080 fixture with PyTorch float16 and no interpolation; run the
  official BasicVSR REDS4 checkpoint in the isolated MMagic environment; run
  Video2X 6.4.0 with Vulkan `realesrgan-plus` in filtering/upscale-only mode.
  Commands and private model paths are retained in the uncommitted artifact
  directory with sensitive local paths redacted from committed evidence.
- **Expected:** Each attempted model reports model/runtime configuration,
  model-stage and normalization timing where available, processed FPS, GPU
  and process telemetry, output metadata, playability, contract verification,
  and an explicit terminal result.
- **Observed:** Eight native RVE runs passed the common 1920x1080, 30-FPS,
  1,350-frame contract. Measured model-stage results were: SuperUltraCompact
  41.972 seconds / 32.164 FPS / 98.31% average GPU; RTMoSR 390.202 seconds /
  3.460 FPS / 99.34%; SPAN 191.046 seconds / 7.066 FPS / 97.76%; DnCNN
  135.560 seconds / 9.959 FPS / 96.89%; DRUNET 264.820 seconds / 5.098 FPS /
  97.66%; SCUNet 664.319 seconds / 2.032 FPS / 99.09%; NAFNet 124.404
  seconds / 10.852 FPS / 94.81%; and RealisticVideo 260.347 seconds /
  5.185 FPS / 87.63%. All completed native runs reached a 99% or 100% GPU
  utilization peak. Native PLKSR exceeded the 1,800-second limit; its
  declared 480x270 adapter completed in 83.006 seconds at 16.264 FPS and is
  not ranked as a native-resolution result. BasicVSR passed through its
  declared 480x270 input adapter at 16.622 FPS, with 76.51% average GPU
  utilization, 5,319 MB peak VRAM, and 228.68 W average power. Video2X
  6.4.0 plus RealESRGAN `realesrgan-plus` ran at 4.74 FPS with 83.12%
  average GPU utilization, 2,161 MB peak VRAM, and 253.77 W average power
  after the declared two-endpoint-frame padding adapter.
- **Status:** passedWithConcerns
- **Artifacts:** `~/Documents/edit/restoration-cross-model-20260827-1m/restoration-cross-model-final.json`,
  `~/Documents/edit/restoration-cross-model-20260827-1m/restoration-cross-model-final.md`,
  `~/Documents/edit/restoration-cross-model-20260827-neural/rve-verified-results.json`,
  `~/Documents/edit/restoration-cross-model-20260827-neural/rve-native/`,
  `~/Documents/edit/restoration-cross-model-20260827-neural/rve-adapter/`,
  `~/Documents/edit/restoration-cross-model-20260827-neural/basicvsr/`, and
  `~/Documents/edit/restoration-cross-model-20260827-neural/video2x-native/`
- **Failure:** Native PLKSR timed out. Video2X dropped two boundary frames on
  the unpadded 1,350-frame input and on a video-only retry.
- **Fix:** Retained the PLKSR timeout and partial artifact; used a declared
  480x270 PLKSR adapter for supplemental evidence; used explicit endpoint
  padding and post-run audio remuxing for the frame-complete Video2X artifact.
- **Accepted warning:** BasicVSR, PLKSR adapter, and Video2X are adapter
  measurements and must not be presented as identical native-resolution
  rankings. No subjective quality winner is claimed before user review.

### E-078-INTEGRITY-002 - Supplemental output and source verification

- **Timestamp:** 2026-08-27
- **Category:** regression
- **Requirement:** Successful supplemental artifacts satisfy the common output
  contract, remain playable, and do not mutate the original source.
- **Command/steps:** Probe and decode the completed RVE, BasicVSR, and
  frame-complete Video2X outputs with FFprobe/FFmpeg and the benchmark
  verification helpers; compare the protected source SHA-256 before and
  after all executions.
- **Expected:** Final artifacts are 1920x1080, native 30/1 FPS, 1,350 frames,
  H.264/yuv420p MP4, AAC 48 kHz stereo, duration within the declared
  tolerance, and playable. The source hash remains
  `1dda0b6774fef33f48d55007d84dc897fe73615f990e0a00966659d7a2feb6ee`.
- **Observed:** Every completed supplemental final output passed dimensions,
  FPS, frame count, codec, pixel format, audio, duration, container, and
  playability checks. The BasicVSR artifact is
  `basicvsr/basicvsr-reds4-45s-resource.mp4` (92,831,062 bytes, SHA-256
  `dd243ba7c99aed82076693c8b7146c4eb7d3d69c63e6bef8e8a7dcd0411b64f3`);
  the Video2X artifact is
  `video2x-native/video2x-realesrgan-plus-x4-comparable.mp4` (18,171,805
  bytes, SHA-256
  `a42966db104378b0e7edf86fd321c26aca855cc7cbc20ee2de52548f05381267`).
  The protected source hash is unchanged.
- **Status:** passed
- **Artifacts:** `~/Documents/edit/restoration-cross-model-20260827-1m/source-preservation.json`,
  supplemental output metadata in
  `~/Documents/edit/restoration-cross-model-20260827-1m/restoration-cross-model-final.json`,
  and generated supplemental contact sheets.

### E-078-REPORT-002 - Aggregate report and comparison boundary

- **Timestamp:** 2026-08-27
- **Category:** implementation
- **Requirement:** The machine-readable and human-readable reports include
  all 24 requested matrix rows plus the verified supplemental runs, with
  native, adapter, unavailable, timeout, historical, licensing, telemetry,
  and quality limitations kept distinct.
- **Command/steps:** Aggregate the original primary matrix report with the
  verified RVE, BasicVSR, and Video2X records; validate the aggregate JSON;
  generate fixed-timestamp contact sheets for the final supplemental
  outputs.
- **Expected:** The report provides complete artifact paths and measured
  numbers without ranking unavailable, timed-out, historical, or
  adapter-qualified candidates as equivalent native runs.
- **Observed:** `restoration-cross-model-final.json` and
  `restoration-cross-model-final.md` contain the 24-row matrix, eight
  completed native RVE rows, one PLKSR native timeout plus its adapter run,
  BasicVSR adapter evidence, Video2X wrapper evidence, seven still-unavailable
  requested candidates, output checks, telemetry summaries, contact sheets,
  source-preservation evidence, and a bounded recommendation. Objective
  quality remains explicitly unavailable because no clean aligned reference
  exists.
- **Status:** passedWithConcerns
- **Artifacts:** `~/Documents/edit/restoration-cross-model-20260827-1m/restoration-cross-model-final.json`,
  `~/Documents/edit/restoration-cross-model-20260827-1m/restoration-cross-model-final.md`,
  and the supplemental artifact root.
- **Accepted warning:** The report is one-fixture/one-workstation evidence;
  adapter-qualified measurements and unavailable runtimes limit universal
  conclusions.

### E-078-USER-VALIDATION-002 - Supplemental review handoff

- **Timestamp:** 2026-08-27
- **Category:** userValidation
- **Setup:** Open
  `~/Documents/edit/restoration-cross-model-20260827-1m/restoration-cross-model-final.md`
  and `restoration-cross-model-final.json`, then inspect the linked outputs
  and contact sheets under
  `~/Documents/edit/restoration-cross-model-20260827-neural/`.
- **Steps:** Compare the six FFmpeg controls, eight native RVE outputs,
  the PLKSR adapter output, BasicVSR adapter output, and the final Video2X
  output at 7s, 22s, and 37s. Check blocking/ringing, noise/detail,
  faces/text, halos and color, hallucinated detail, temporal flicker, motion
  stability, and boundary behavior. Confirm that PLKSR timeout, Video2X
  endpoint padding, BasicVSR input downscale, unavailable candidates, and
  the wrapper/underlying-model distinction are visible in the reports.
- **Expected visible result:** Measured speed and resource data are separate
  from subjective observations; no unavailable, timed-out, historical, or
  adapter-qualified candidate is silently ranked as an equivalent native
  result.
- **Expected persisted/external effect:** The source-preservation record
  retains the unchanged protected-source hash and all reviewed output paths
  resolve to the generated artifact directory.
- **Cleanup:** Keep the generated comparison artifacts for review, or remove
  only the named comparison directories after inspection. Never remove the
  original source media.
- **Evidence response required:** Return exactly one of:

  ```text
  PASS: every required check succeeded; evidence: <paths or notes>
  FAIL: <failed check and observed result>
  BLOCKED: <missing service, data, permission, or capability>
  NOT APPLICABLE: <reason and approval>
  ```

- **Status:** pending

### E-078-READINESS-002 - Current delivery state after supplemental runs

- **Timestamp:** 2026-08-27
- **Category:** gate
- **Requirement:** Do not close or deliver the ticket before required user
  validation and configured delivery checks are terminal.
- **Observed:** Technical benchmark execution, source preservation, output
  integrity, contact-sheet generation, focused tests, full-suite regression,
  and local quality evidence are terminal. User validation is still pending.
  No repository upstream is configured, so the required remote-check gate is
  unavailable. No commit, push, or pull request was created.
- **Status:** blocked
- **Blocker:** Required user validation and the configured remote-check policy
  remain unresolved.
- **Accepted warning:** The ticket remains `verifying`; no readiness, commit,
  or publication claim is made.

## Current readiness (latest)

**Technical readiness:** passedWithConcerns; the primary matrix and verified
supplemental RVE, BasicVSR, and Video2X executions have terminal local
evidence, including output integrity and source preservation.
**Review readiness:** passedWithConcerns; native, adapter, timeout, historical,
and unavailable cases are explicitly separated. No high-confidence
introduced code blocker was found in the prior review.
**User validation:** pending the required response in `E-078-USER-VALIDATION-002`.
**Delivery readiness:** blocked until user validation and the configured
remote-check policy are resolved; no commit, push, or pull request exists.

### E-078-READINESS-005 - User-validation response recorded

- **Timestamp:** 2026-08-28T08:06:41+02:00
- **Category:** gate
- **Requirement:** Keep the expanded benchmark open until required
  validation and delivery gates are represented by terminal evidence.
- **Observed:** User validation is now recorded as passed from the user's
  explicit manual-validation statement. The report's availability,
  licensing, and confidence limitations remain unchanged.
- **Status:** passedWithConcerns
- **Accepted warning:** The existing no-remote delivery limitation remains
  unresolved; no commit, push, or pull request has been created.

### E-078-BENCHMARK-003 - Current four-segment neural completion

- **Timestamp:** 2026-08-27
- **Category:** functionality
- **Requirement:** Every runnable candidate must be measured against the same
  four-window real-video fixture with native frame rate, common output
  metadata, resource telemetry, and preserved output artifacts.
- **Command/steps:** Reused the deterministic seed-770 fixture made from four
  random 15-second windows; ran all nine native RVE models with PyTorch
  CUDA/float16; ran the MMagic BasicVSR REDS4 adapter at 480x270; ran
  Video2X 6.4.0 Vulkan device 0 with both the pinned
  `realesr-animevideov3` configuration and the heavier `realesrgan-plus`
  comparison configuration. Model and private local paths are retained only
  in the external artifact directory.
- **Expected:** The fixture contains 1,436 frames at 24000/1001 FPS. Each
  completed output is 1920x1080 H.264/yuv420p MP4 with AAC 48 kHz stereo,
  and every run has measured timing and GPU telemetry.
- **Observed:** Nine native RVE models passed. Model-stage measurements were:
  SuperUltraCompact 7.7172 seconds / 186.078 FPS; RTMoSR 92.2245 seconds /
  15.571 FPS; SPAN 47.5528 seconds / 30.198 FPS; PLKSR 515.3300 seconds /
  2.787 FPS; DnCNN 35.9062 seconds / 39.993 FPS; DRUNET 67.9246 seconds /
  21.141 FPS; SCUNet 163.3810 seconds / 8.789 FPS; NAFNet 33.3790 seconds /
  43.021 FPS; and RealisticVideo 69.0455 seconds / 20.798 FPS. BasicVSR
  passed its 480x270 adapter at 15.533 FPS inference and 114.690588 seconds
  end to end. Video2X `realesr-animevideov3` completed at 79.78 reported FPS
  and 76.22 wall FPS in 18.970340 seconds end to end; `realesrgan-plus`
  completed at 4.68 reported FPS and 4.66 wall FPS in 308.312780 seconds.
- **Resource observations:** BasicVSR reached 72.94% average / 100% peak
  GPU utilization, 5,496 MB peak VRAM, and 221.13 W average power.
  `realesr-animevideov3` reached 29.81% average / 59% peak utilization,
  1,499 MB peak VRAM, and 101.18 W average power. The heavier
  `realesrgan-plus` run reached 83.25% average / 97% peak utilization,
  2,543 MB peak VRAM, and 248.19 W average power.
- **Status:** passedWithConcerns
- **Artifacts:** `~/Documents/edit/restoration-cross-model-20260827-480p-4x15s/`,
  including the current fixture, 18 final output videos, raw RVE results,
  BasicVSR telemetry, both Video2X output directories, and 18 contact sheets.
- **Accepted warning:** BasicVSR and both Video2X configurations use a
  480x270 adapter and must not be presented as native-resolution rankings.
  The two Video2X measurements remain one wrapper candidate with two model
  configurations.

### E-078-EXECUTION-003 - Video2X boundary and runner fixes

- **Timestamp:** 2026-08-27
- **Category:** implementation
- **Requirement:** Video2X output must retain the complete native-frame count
  and the benchmark must retain failures and fixes rather than hiding them.
- **Observed failure:** The first current-fixture invocation failed before
  processing because `/usr/bin/time` is not installed. The rerun used the
  shell `time` builtin and completed. The first audio remux used `-shortest`
  and produced 1,435 output frames even though the Video2X stage contained
  1,436 frames.
- **Fix:** Kept the Video2X stage output, remuxed the source AAC stream with
  video/audio stream copying and without `-shortest`, and reran the common
  metadata/playability checks.
- **Observed after fix:** Both final Video2X outputs contain 1,436 frames,
  pass the common contract, and decode successfully. No partial output
  remains.
- **Status:** passedWithConcerns
- **Artifacts:** `neural/video2x/animevideov3/`,
  `neural/video2x/realesrgan-plus/`, and
  `neural/completed-output-verification.json` under the external artifact
  root.
- **Accepted warning:** The lighter anime model has lower GPU utilization
  because its workload is smaller; the heavy model run demonstrates that the
  Vulkan model path reaches high utilization on this GPU.

### E-078-INTEGRITY-003 - Current output and source verification

- **Timestamp:** 2026-08-27
- **Category:** regression
- **Requirement:** Completed outputs must satisfy the common contract and the
  original source must remain unchanged.
- **Command/steps:** Applied the benchmark verification helpers and full
  FFmpeg decode checks to six controls, nine RVE outputs, BasicVSR, and both
  Video2X final outputs; generated contact sheets at 7s, 22s, 37s, and 52s;
  compared the protected source hash before and after execution.
- **Expected:** All completed outputs pass dimensions, native FPS, frame count,
  H.264/yuv420p, AAC 48 kHz stereo, MP4, duration tolerance, playability, and
  contact-sheet generation. The source hash remains unchanged.
- **Observed:** 18 of 18 outputs passed every output-contract and playability
  check, and 18 of 18 contact sheets were generated. The protected source
  hash remained
  `acf6420455324e66d9c68d644888c3cb2977282d609d514d80c169c9918a7d2f`.
- **Status:** passed
- **Artifacts:** `neural/completed-output-verification.json`,
  `source-preservation.json`, and `contact-sheets/` under the external
  artifact root.

### E-078-REPORT-003 - Repository benchmark reports

- **Timestamp:** 2026-08-27
- **Category:** implementation
- **Requirement:** The completed measurements and artifact paths must be
  reviewable in the repository without tracking private source media or
  generated multi-gigabyte media.
- **Observed:** Added the machine-readable aggregate report
  `benchmarks/results/ticket-078-480p-4x15s.json` and the human-readable
  report `benchmarks/results/ticket-078-480p-4x15s.md`. The reports contain
  the 24 candidate rows, 18 completed runs, timing/resource values, output
  hashes and metadata, availability reasons, Video2X configuration details,
  limitations, and bounded review suggestions. README now links the reports
  and the external artifact root.
- **Status:** passedWithConcerns
- **Accepted warning:** Generated media and raw telemetry remain outside the
  repository; the reports intentionally use relative paths and a redacted
  source path.

### E-078-READINESS-003 - Current benchmark delivery state

- **Timestamp:** 2026-08-27
- **Category:** gate
- **Requirement:** Do not close or deliver the ticket before user validation
  and configured delivery gates are terminal.
- **Observed:** Current-fixture benchmark execution, output integrity, source
  preservation, contact sheets, and repository reports are terminal.
  Objective quality remains unavailable without a clean aligned reference.
  User visual validation is still pending, and no repository upstream is
  configured for remote checks. No commit, push, or pull request was created.
- **Status:** blocked
- **Blocker:** Required user visual validation and the configured remote-check
  policy remain unresolved.
- **Accepted warning:** The final report recommends candidates for visual
  review but does not claim a quality winner.

## Current readiness (latest)

**Technical readiness:** passedWithConcerns; all nine native RVE models,
BasicVSR, both Video2X configurations, six controls, output verification,
source preservation, and contact sheets have terminal evidence on the
four-segment fixture.
**Review readiness:** passedWithConcerns; the repository reports distinguish
native runs, adapter runs, wrapper configurations, unavailable candidates,
license exclusion, output integrity, and objective-quality limitations.
**User validation:** pending the required response in
`E-078-USER-VALIDATION-002`.
**Delivery readiness:** blocked until user validation and the configured
remote-check policy are resolved; no commit, push, or pull request exists.

### E-078-VIDEO2X-OPTIMIZATION-001 - Documentation and configuration investigation

- **Timestamp:** 2026-08-27
- **Category:** investigation
- **Requirement:** The Video2X comparison must use a documented, explicitly
  selected GPU/model configuration and distinguish model throughput from
  encoder or decode limitations.
- **Sources:** Video2X 6.4.0 `--help`;
  `https://docs.video2x.org/running/command-line.html`;
  `https://raw.githubusercontent.com/k4yt3x/video2x/6.4.0/README.md`.
- **Observed:** The installed CLI reports Vulkan device 0 as the NVIDIA
  GeForce RTX 5070 Ti and supports `--benchmark`, `--hwaccel`, `--device`,
  `--codec`, and extra encoder options. The upstream example uses
  `realesr-animevideov3`; the prior benchmark used the heavier
  `realesrgan-plus` model. A 1-second probe measured approximately 4.00 FPS
  for `realesrgan-plus`, 9.33 FPS for `realesrgan-plus-anime`, and 28.00 FPS
  for `realesr-animevideov3` on the same device and fixture. Explicit
  `hwaccel=cuda` failed because Video2X's swscale conversion rejected CUDA
  input frames. NVENC with default B-frames failed MP4 muxing with
  `pts < dts`; `--max-b-frames 0` produced a valid output. Each probe
  temporarily used the `performance` power profile and restored the prior
  `power-saver` profile.
- **Status:** passedWithConcerns
- **Accepted warning:** The faster model is a different, lighter anime-video
  model; its speed is not a quality-equivalent acceleration of
  `realesrgan-plus`.
- **Artifacts:** `~/Documents/edit/restoration-cross-model-20260827-neural/video2x-native/video2x-benchmark-1s-cuda-decode.mp4`,
  `~/Documents/edit/restoration-cross-model-20260827-neural/video2x-native/video2x-1s-nvenc.log`,
  and the short model-probe outputs under the same artifact directory.

### E-078-VIDEO2X-OPTIMIZATION-002 - Full documented Video2X rerun

- **Timestamp:** 2026-08-27
- **Category:** functionality
- **Requirement:** A documented Video2X model/configuration should be rerun
  against the same padded fixture with throughput, resource telemetry,
  output integrity, and source-preservation evidence.
- **Command/steps:** Video2X 6.4.0 with ncnn/Vulkan, RTX 5070 Ti device 0,
  `realesr-animevideov3`, scale 4, `hwaccel=none`, `h264_nvenc`,
  `cq=18`, `preset=p5`, and `--max-b-frames 0`; one endpoint frame was
  duplicated before and after processing, then source audio was remuxed.
  The workstation was temporarily set to `performance` and restored to
  `power-saver`.
- **Expected:** The padded 1,352-frame input produces 1,350 output frames
  at 1920x1080, native 30 FPS, H.264/yuv420p, AAC 48 kHz stereo, and remains
  playable without changing the protected source.
- **Observed:** Video2X `--benchmark` mode processed 1,350 frames at 90.00
  FPS in 16.440 seconds. The full NVENC stage processed 1,350 frames at
  79.41 reported FPS, 74.457 FPS by wall time, and 18.131 seconds. Audio
  remux took 1.174 seconds; end-to-end time was 19.305 seconds. GPU
  telemetry was 50.73% average / 61% peak utilization, 1,390 MB peak VRAM,
  and 152.41 W average power. The Video2X process used 74.34% average /
  165% peak CPU and 493.84 MB peak RSS. The lower GPU utilization is
  consistent with the lighter model and does not indicate CPU fallback.
- **Status:** passedWithConcerns
- **Accepted warning:** This is a 480x270 input adapter to the common
  1920x1080 output and is not a native-1080p model ranking result.
- **Artifacts:** `~/Documents/edit/restoration-cross-model-20260827-neural/video2x-native/animevideov3/video2x-benchmark.log`,
  `~/Documents/edit/restoration-cross-model-20260827-neural/video2x-native/animevideov3/video2x-nvenc.log`,
  `~/Documents/edit/restoration-cross-model-20260827-neural/video2x-native/animevideov3/gpu-telemetry-nvenc.csv`,
  and `~/Documents/edit/restoration-cross-model-20260827-neural/video2x-native/animevideov3/wall-time-nvenc.txt`.

### E-078-VIDEO2X-OPTIMIZATION-003 - Optimized output integrity and report update

- **Timestamp:** 2026-08-27
- **Category:** regression
- **Requirement:** The optimized Video2X artifact must satisfy the common
  output contract and be represented as a separate wrapper configuration
  without overwriting the prior `realesrgan-plus` baseline.
- **Command/steps:** Probe and decode the optimized audio-complete output;
  verify dimensions, native frame rate/count, codecs, pixel format, audio,
  duration, container, and contact sheet; compare the protected source hash;
  update the aggregate JSON/Markdown report and pin the configuration in the
  benchmark manifest.
- **Observed:** The optimized output passed every common contract check and
  FFmpeg playability. It contains 1,350 frames at 1920x1080 and 30 FPS,
  H.264/yuv420p video, AAC 48 kHz stereo audio, 45.000 seconds duration,
  and SHA-256
  `326b04dffe2a808e3a92f2a5b269163c30e3bd67fb13e416b030c4f2a335cff1`.
  The source hash remains
  `1dda0b6774fef33f48d55007d84dc897fe73615f990e0a00966659d7a2feb6ee`.
  The report retains the 4.74 FPS `realesrgan-plus` baseline and adds the
  79.41 FPS documented `realesr-animevideov3` configuration under the same
  wrapper row. The manifest now pins Video2X 6.4.0, ncnn/Vulkan, device 0,
  the model, decode choice, NVENC settings, and boundary adapter.
- **Status:** passed
- **Artifacts:** `~/Documents/edit/restoration-cross-model-20260827-neural/video2x-native/animevideov3/video2x-realesr-animevideov3-x4-comparable.mp4`,
  `~/Documents/edit/restoration-cross-model-20260827-neural/video2x-native/animevideov3/video2x-realesr-animevideov3-x4-comparable.jpg`,
  `~/Documents/edit/restoration-cross-model-20260827-1m/restoration-cross-model-final.json`,
  and `~/Documents/edit/restoration-cross-model-20260827-1m/restoration-cross-model-final.md`.

### E-078-TEST-002 - Video2X configuration contract regression

- **Timestamp:** 2026-08-27
- **Category:** regression
- **Command/steps:** `python3 -m unittest tests.test_restoration_benchmark -v`
- **Expected:** The benchmark manifest and generated candidate result retain
  the pinned Video2X version, backend, model, device, decode, codec, and
  B-frame configuration.
- **Observed:** 11 focused restoration benchmark tests passed, including the
  new manifest and candidate-configuration retention tests.
- **Status:** passed

## Current readiness (latest; superseding the prior readiness section)

**Technical readiness:** passedWithConcerns; the documented Video2X
configuration has terminal local execution, telemetry, output-integrity,
playability, and source-preservation evidence, while the prior heavier-model
baseline and all limitations remain visible.
**Review readiness:** passedWithConcerns; the aggregate report distinguishes
the two Video2X configurations, adapter treatment, native results, timeout,
historical, and unavailable candidates. No quality-equivalence claim is made.
**User validation:** pending the required response in
`E-078-USER-VALIDATION-002`.
**Delivery readiness:** blocked until user validation and the configured
remote-check policy are resolved; no commit, push, or pull request exists.

### E-078-TEST-003 - Repository quality gates after report update

- **Timestamp:** 2026-08-27
- **Category:** regression
- **Command/steps:** `make quality PYTHON=.venv/bin/python`
- **Expected:** The protected test suite, compilation, formatting, lint,
  type-check, complexity, duplication, dependency, security, and churn gates
  complete without introduced findings.
- **Observed:** 323 unittest cases passed; Python compilation and
  `git diff --check` passed; Ruff format reported 77 files already formatted;
  Ruff lint and complexity checks passed; all configured mypy targets passed;
  jscpd completed; dependency checks completed; pip-audit reported no known
  vulnerabilities; Bandit completed; and churn analysis completed. The first
  default `make quality` attempt was blocked only because system `python3`
  lacks Ruff; the repository's existing pinned `.venv` was used for the
  successful gate run.
- **Status:** passed
- **Artifacts:** `evidence/static-analysis/jscpd-report.json`,
  `evidence/static-analysis/dependencies.json`,
  `evidence/static-analysis/pip-audit.json`,
  `evidence/static-analysis/bandit.json`, and
  `evidence/static-analysis/churn.json`.

### E-078-VERIFICATION-004 - Post-update artifact and report consistency

- **Timestamp:** 2026-08-27
- **Category:** regression
- **Command/steps:** Load `restoration-cross-model-final.json`; resolve and
  probe every completed RVE, PLKSR adapter, BasicVSR, prior Video2X, and
  optimized Video2X output; run the common contract and FFmpeg playability
  checks; compare the protected source hash.
- **Expected:** Twelve completed supplemental outputs pass the common
  contract and playability checks, the optimized Video2X model/configuration
  is present, and the protected source remains unchanged.
- **Observed:** All 12 completed supplemental outputs passed dimensions,
  native FPS/frame count, codecs, pixel format, audio, duration, container,
  and playability checks. The report contains the documented
  `realesr-animevideov3` result and retains the `realesrgan-plus` baseline.
  The source hash remains
  `1dda0b6774fef33f48d55007d84dc897fe73615f990e0a00966659d7a2feb6ee`.
- **Status:** passed
- **Artifacts:** `~/Documents/edit/restoration-cross-model-20260827-1m/restoration-cross-model-final.json`
  and all output/contact-sheet paths referenced by the aggregate report.

### E-078-TEST-004 - Final configuration assertions and quality rerun

- **Timestamp:** 2026-08-27
- **Category:** regression
- **Command/steps:** `make quality PYTHON=.venv/bin/python`
- **Expected:** The final manifest assertions cover the documented Video2X
  mode, scale, device, decode, codec, encoder options, and B-frame setting;
  the complete repository quality suite remains clean.
- **Observed:** All 323 unittest cases passed. The new Video2X assertions
  passed for filtering/upscale-only mode, scale 4, Vulkan device 0,
  software decode, `h264_nvenc`, `cq=18`, `preset=p5`, and zero B-frames.
  Compilation, diff check, Ruff format/lint/complexity, mypy, jscpd,
  dependency checks, pip-audit, Bandit, and churn all completed successfully.
- **Status:** passed

### E-078-REPRO-001 - Pinned Video2X runtime discovery

- **Timestamp:** 2026-08-27
- **Category:** regression
- **Requirement:** A future benchmark invocation must discover the pinned
  Video2X AppImage even when no `video2x` command is present on `PATH`.
- **Change:** Added the configured
  `~/.cache/framestudio-fps/benchmark-tools/Video2X-6.4.0-x86_64.AppImage`
  executable path to the manifest and taught runtime discovery to report
  explicitly configured executable paths without exposing an absolute home
  directory.
- **Observed:** Runtime discovery reports the pinned AppImage on this
  workstation, alongside the detected RealESRGAN weights. The candidate
  remains correctly classified as a wrapper requiring its declared adapter;
  discovery no longer silently reports it unavailable solely because the
  AppImage is not on `PATH`.
- **Status:** passed

### E-078-TEST-005 - Final quality gates after runtime-discovery change

- **Timestamp:** 2026-08-27
- **Category:** regression
- **Command/steps:** `make quality PYTHON=.venv/bin/python`
- **Expected:** The runtime-discovery change preserves the complete
  repository quality baseline.
- **Observed:** 324 unittest cases passed. Compilation, diff check, Ruff
  format/lint/complexity, mypy, jscpd, dependency checks, pip-audit, Bandit,
  and churn all completed successfully.
- **Status:** passed

### E-078-RESOURCES-002 - Repeat Video2X process telemetry

- **Timestamp:** 2026-08-27
- **Category:** functionality
- **Requirement:** Comparable model runs record CPU use and peak RSS when the
  workstation makes those measurements observable.
- **Command/steps:** Repeat the exact padded Video2X 6.4.0 Vulkan
  `realesrgan-plus` processing stage while sampling the Video2X runner
  process, then compare its raw stage output with the previously verified
  padded output.
- **Expected:** The repeat processes all 1,350 padded-comparison frames,
  reports a terminal result, and records process CPU/RSS without replacing
  the audio-remuxed final comparison artifact.
- **Observed:** The repeat completed successfully in 288.704 seconds at the
  reported 4.69 FPS. Runner-process telemetry captured 42.44% average CPU,
  230% peak CPU, and 1,604.65 MB peak RSS across 1,143 samples. The raw
  Video2X stage output is video-only by design; the final comparable
  audio-remuxed artifact remains verified separately.
- **Status:** passedWithConcerns
- **Artifacts:** `~/Documents/edit/restoration-cross-model-20260827-neural/video2x-native/resource-telemetry.csv`,
  `~/Documents/edit/restoration-cross-model-20260827-neural/video2x-native/video2x-resource.log`,
  and the updated aggregate machine-readable and human-readable reports.
- **Accepted warning:** CPU/RSS sampling covers the runner process only and
  excludes separately spawned encoder processes; GPU telemetry is retained
  from the comparable padded execution.

## Current readiness (latest; superseding the prior readiness section)

**Technical readiness:** passedWithConcerns; all requested runnable paths that
were available on this workstation have terminal local evidence, including
the supplemental process telemetry and final output integrity.
**Review readiness:** passedWithConcerns; the aggregate report distinguishes
native, adapter, timeout, historical, unavailable, and wrapper evidence.
**User validation:** pending the required response in `E-078-USER-VALIDATION-002`.
**Delivery readiness:** blocked until user validation and the configured
remote-check policy are resolved; no commit, push, or pull request exists.

### E-078-VERIFICATION-003 - Final aggregate consistency check

- **Timestamp:** 2026-08-27
- **Category:** regression
- **Requirement:** The final report, artifact paths, output gates, timeout
  record, availability count, and source-preservation claim agree.
- **Command/steps:** Validate `restoration-cross-model-final.json`, probe all
  11 completed supplemental outputs, rerun contract/playability checks, and
  compare the recorded source hash.
- **Expected:** The aggregate JSON is valid; every completed supplemental
  output exists and passes its contract/playability checks; one native timeout
  and seven unavailable requested rows remain recorded; source preservation
  remains true.
- **Observed:** The final aggregate report is valid. All 11 completed
  supplemental outputs passed contract and playability verification. The
  report records one native timeout, seven unavailable rows, and the unchanged
  protected source hash
  `1dda0b6774fef33f48d55007d84dc897fe73615f990e0a00966659d7a2feb6ee`.
- **Status:** passed
- **Artifacts:** `~/Documents/edit/restoration-cross-model-20260827-1m/restoration-cross-model-final.json`
  and the linked supplemental output/contact-sheet directories.

## Current readiness (latest; superseding the prior readiness section)

**Technical readiness:** passedWithConcerns; the final aggregate report and all
completed supplemental artifacts pass the recorded local integrity checks.
**Review readiness:** passedWithConcerns; quality remains pending human visual
review and adapter/timeout limitations remain explicit.
**User validation:** pending the required response in `E-078-USER-VALIDATION-002`.
**Delivery readiness:** blocked until user validation and the configured
remote-check policy are resolved; no commit, push, or pull request exists.

### E-078-REPORT-004 - Current four-segment report consistency

- **Timestamp:** 2026-08-27
- **Category:** regression
- **Requirement:** The repository report must accurately summarize the current
  four-segment fixture and agree with the raw telemetry and completed-run
  records.
- **Command/steps:** `python3 -m json.tool
  benchmarks/results/ticket-078-480p-4x15s.json`; compare the report summary
  and 18 run records with `neural/rve-native/rve-native-results.json`;
  verify that every completed run reports `passed` verification and
  playability; run `python3 -m unittest tests.test_restoration_benchmark`;
  run `git diff --check`.
- **Expected:** The report is valid JSON, retains 24 candidate rows, 17
  passed rows, 18 completed and verified outputs, nine native RVE runs, and
  three adapter runs; RVE GPU sample counts match raw telemetry; focused
  benchmark tests and diff checks pass.
- **Observed:** The aggregate report is valid. Its summary retains the
  expected counts, all 18 completed runs report passed verification and
  playability, and all nine RVE sample counts match raw telemetry
  (28/342/176/1927/133/252/607/124/255). The focused restoration benchmark
  suite passed 13 tests and `git diff --check` passed.
- **Status:** passed
- **Artifacts:** `benchmarks/results/ticket-078-480p-4x15s.json`,
  `benchmarks/results/ticket-078-480p-4x15s.md`, and the linked external
  benchmark artifact root.

### E-078-READINESS-004 - Final current-fixture handoff state

- **Timestamp:** 2026-08-27
- **Category:** gate
- **Requirement:** Keep TICKET-078 in verification until visual user
  validation and configured delivery gates are terminal.
- **Observed:** The current four-segment benchmark, 18 output videos,
  18 contact sheets, source-preservation check, output-contract checks,
  repository reports, focused tests, JSON consistency check, and diff check
  are recorded. The report explicitly retains unavailable, license-excluded,
  and non-comparable candidates and does not claim objective quality without a
  clean aligned reference.
- **Status:** blocked
- **Blocker:** User visual validation is still pending, and no repository
  upstream is configured for the remote-check policy. No commit, push, or pull
  request was created.
- **Artifacts:** `benchmarks/results/ticket-078-480p-4x15s.md`,
  `benchmarks/results/ticket-078-480p-4x15s.json`, and
  `~/Documents/edit/restoration-cross-model-20260827-480p-4x15s/`.

### E-078-USER-VALIDATION-003 - User-confirmed manual validation

- **Timestamp:** 2026-08-28T08:06:41+02:00
- **Category:** userValidation
- **Requirement:** The cross-model comparison outputs, availability rows,
  visual-review artifacts, recommendation limits, and source-preservation
  result are manually validated.
- **Steps:** The user stated, "you can close all the tickets i manually
  validated everything and you can then /aidd-commit".
- **Observed:** The user reports that the ticket outputs and behavior were
  manually validated. This response did not identify individual artifacts or
  provide separate visual observations.
- **Status:** passed
- **Accepted warning:** This terminalizes the user-validation response only.
  The existing remote-check and delivery-policy limitations remain recorded
  and are not converted into passes.

## Current readiness (latest)

**Technical readiness:** passedWithConcerns; the completed current-fixture
matrix has terminal timing, GPU telemetry, output-contract, playability,
contact-sheet, and source-preservation evidence for all 18 output videos.
**Review readiness:** passedWithConcerns; native and adapter runs are
separated, Video2X model configurations are explicit, and unavailable or
license-constrained candidates remain visible.
**User validation:** pending the required visual response in
`E-078-USER-VALIDATION-002`.
**Delivery readiness:** blocked until user validation and the configured
remote-check policy are resolved; no commit, push, or pull request exists.

### E-078-READINESS-006 - Current delivery state after user validation

- **Timestamp:** 2026-08-28T08:06:41+02:00
- **Category:** gate
- **Requirement:** Do not close or deliver the ticket without a scoped,
  reviewed commit and the applicable delivery lifecycle.
- **Observed:** User validation is recorded as passed. The current worktree
  has no staged paths, the branch is shared across Phase 8, and no commit or
  remote delivery exists.
- **Status:** blocked
- **Blocker:** Commit-scope and branch prerequisites are unresolved.
