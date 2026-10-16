# Evidence - PHASE-009 Efficient Export Pipeline

**Tickets:** TICKET-102, TICKET-103, TICKET-104  
**Status:** verifying  
**Last updated:** 2026-09-09

## Outcome

FrameStudio now has a measured adaptive preparation route for enhanced
exports. Compatible retained segments from one source can be normalized in a
single FFmpeg process while remaining separate output artifacts, so
interpolation never receives a stream that crosses a deleted boundary. The
existing per-segment route remains selectable with
`pipeline_strategy="per-segment"` and remains the fallback for ineligible
upscale/restoration work.

## Implementation evidence

- `framestudio/export_strategy.py` derives compatible active source runs from
  source identity, source/target rate, rate action, and upscale profile.
- `framestudio/export_smart_render.py` builds independent filter branches and
  output maps for grouped preparation, then reuses the existing per-segment
  interpolation, cache, verification, and publication contracts.
- Grouped preparation accepts only supported rate actions. Unsupported or
  unknown actions stay on the existing explicit error path instead of being
  allowed to bypass validation.
- The normalization filter graph is shared by the concatenating and grouped
  builders. Video-only multi-segment normalization is covered explicitly.
- `framestudio/export_interpolation.py` validates and persists the internal
  `adaptive` or `per-segment` strategy without passing it to interpolation or
  restoration backends.
- `benchmarks/efficient_export_pipeline_benchmark.py` compares both routes
  with equivalent generated mixed-source inputs, repeated measurements, source
  hashes, output metadata, process counts, stage timing, boundary samples,
  intermediate storage, and resource observations.
- `tests/test_editor_export_execution.py` exercises adaptive generated-media
  export and cancellation/reopen/resume. The resume functionality test proves
  grouped source preparation is not run again after its artifacts are cached.

## Benchmark evidence

The machine-readable and Markdown reports are:

- `evidence/efficient-export-pipeline-benchmark.json`
- `evidence/efficient-export-pipeline-benchmark.md`

The three interleaved repetitions on the generated mixed-source fixture
selected `adaptive`:

| Metric | Per-segment baseline | Adaptive |
|---|---:|---:|
| Median wall time | 68.2237 s | 67.8984 s |
| Wall-time change | — | -0.3253 s (-0.48%) |
| FFmpeg processes | 11 | 8 |
| Normalization processes | 3 | 2 |
| Production interpolation calls | 2 | 2 |
| Boundary-safe | yes | yes |
| Source preserved | yes | yes |

Both outputs were 1920x1080 H.264 `yuv420p`, 60 FPS, 240 frames, approximately
4.021 seconds, with AAC stereo audio at 48 kHz. The deleted green range was
absent at the sampled red/blue boundary.

This result is fixture- and workstation-specific. The operating-system file
cache was not flushed between repetitions, GPU values are point-in-time
observations, and the interpolation-process metric includes FFmpeg
artifact-preflight work. A comparable RVE grouped benchmark was not run
because the current adaptive route intentionally keeps restoration per
segment.

## Verification

- The unsupported-rate regression test failed before the fix because grouped
  preparation bypassed the expected error, then passed after the guard was
  added.
- `python3 -m unittest discover -s tests` — 470 tests passed after the fix.
- `python3 -m unittest
  tests.test_editor_export_execution.EditorExportExecutionTests.test_cancelled_enhanced_export_reuses_completed_interpolation_after_resume`
  — passed; grouped preparation ran once across cancellation and resume.
- Focused export regression tests — 42 passed.
- Repository compilation — passed.
- Repository formatting and Ruff lint — passed.
- Repository complexity check — passed.
- Repository duplication check — passed with the reviewed baseline.
- Mypy — passed for all configured source, benchmark, and tool targets.
- Dependency boundary check — passed.
- `pip-audit` — no known vulnerabilities found.
- Bandit security analysis — passed.
- Churn analysis — passed.
- CLI contract tests — 39 passed.
- Generated-media smoke flow — passed.
- `git diff --check` — passed.

## User validation

Technical evidence is complete. The earlier user validation PASS was
superseded by the scoped unsupported-rate guard, so the real-project check
must be repeated before closing the active tickets.

1. Use a project with two retained segments from one source separated by a
   deleted range, plus a second source with a different frame rate or
   dimensions.
2. Export once with the normal export controls and confirm the output plays,
   has the expected duration and 1920x1080/target-FPS metadata, preserves
   audio, and contains no deleted-range content.
3. Cancel or close the export after preparation or interpolation has produced
   checkpoints.
4. Reopen the same project and destination, choose **Resume**, and confirm
   that completed preparation/interpolation work is reused rather than
   repeated.
5. Inspect the final output around the deleted boundary and confirm source
   files are unchanged.

Expected response: `PASS`, `FAIL`, `BLOCKED`, or approved `NOT APPLICABLE`,
with any observed output path or limitation.

## Superseding review and validation evidence

- Review finding: grouped preparation could bypass the explicit unsupported
  rate-decision error when a run contained multiple segments.
- Baseline reproduction: the new regression test failed because no
  `ExportExecutionError` was raised.
- Fix: grouped preparation now accepts only `interpolate`, `passthrough`,
  `convert`, and `convert-down` actions. Unsupported or unknown actions use
  the existing per-segment validation path.
- Focused verification: 42 export regression tests passed, including the
  unsupported-rate regression and grouped cancellation/resume functionality.
- Complete verification after the fix: `make quality PYTHON=.venv/bin/python
  NPX=npx` passed with 470 tests, compilation, formatting, lint, mypy,
  complexity, duplication baseline, dependency checks, `pip-audit`, Bandit,
  churn, and `git diff --check`.
- Post-fix CLI contract tests — 39 passed.
- Post-fix generated-media smoke flow — passed.
- User validation: the maintainer repeated the real-project mixed-source
  export, deleted-boundary, source-preservation, and cancel/reopen/resume
  checks after the fix and returned `PASS`.
- The earlier PASS was superseded by the fix and is not used as current
  evidence.

## Review readiness

Technical evidence, local quality gates, review remediation, and user
validation are terminal. The active tickets remain in `open/` with
`verifying` evidence until the configured delivery operation is performed.
No commit, remote check, push, or pull request has been started for this
worktree, so those delivery gates remain outstanding.

## CURRENT-WORKTREE-VERIFICATION-001

- Context: Final verification of the authorized combined worktree on branch
  `ticket/randomize-multi-clip-add-order`, based on
  `06a1a8d433aec26dff53b6bdcb1dcd7372eeb1fd`.
- Requirement/flow: Preserve the export output contract, atomic delivery,
  cancellation and cache reuse while validating all combined ticket changes.
- Commands:
  - `make quality PYTHON=.venv/bin/python`
  - `make smoke PYTHON=.venv/bin/python`
  - `make contract PYTHON=.venv/bin/python`
  - `git diff --check`
- Expected: All 489 repository tests and configured deterministic checks
  pass; generated-media smoke, CLI contract, and whitespace checks succeed.
- Observed: Quality passed 489 tests, compilation, Ruff formatting/lint,
  mypy, complexity, duplication baseline (1.780%, 0 new clones), dependency
  checks, `pip-audit` (no known vulnerabilities), Bandit, and churn. Smoke
  and contract passed; contract ran 39 tests. The generated-media composition
  functionality test verifies 1920x1080 output, six frames, both visible
  source edges, and unchanged source bytes.
- Static-analysis artifacts:
  `evidence/static-analysis/jscpd-report.json`,
  `evidence/static-analysis/dependencies.json`,
  `evidence/static-analysis/pip-audit.json`,
  `evidence/static-analysis/bandit.json`, and
  `evidence/static-analysis/churn.json`.
- Churn interpretation: The report's three highest-scoring files are skill
  test files; no changed implementation file appears in the report. Churn is
  used only to guide review depth.
- Local/PR parity: `unavailable`. The PR workflow runs the same
  `make quality PYTHON=.venv/bin/python` command on Ubuntu 24.04 and installs
  its pinned Python/npm quality dependencies, but the local interpreter is
  Python 3.14.7 rather than the workflow's Ubuntu system Python 3.12. No PR
  run exists for this uncommitted branch.
- User validation: The earlier export-specific real-project `PASS` remains
  evidence for that export flow, but validation of the complete combined
  worktree received a new user `PASS` response. The user stated they tested
  the combined behavior but declined to provide output paths, metadata,
  source-hash results, or screenshot paths.
- User-validation status: `passedWithConcerns`; the configured UI evidence
  requirement is still blocked by missing before/after screenshots and
  per-flow observations.
- Status: `passedWithConcerns` for local technical checks and the user's
  response.
- Blockers: Required UI artifacts, remote PR checks/parity, and PR approval
  remain outstanding. TICKET-104 stays open in `verifying`.

## TICKET-104-DOCUMENTS-PROJECT-RESUME-001

- Context: 2026-09-24 target-workstation investigation of the single editor
  project in `Documents/edit`, under PHASE-009 / FEAT-031 / TICKET-104.
- Requirement: Given a compatible cancelled export session with unchanged
  sources, resume at its saved destination without discarding reusable work,
  surface active progress, and verify the final output before delivery.
- Baseline: The prior session was `cancelled` during preparation, with 0/5
  stages complete, no destination output, no partial output, and zero cached
  media artifacts. All four project sources were available and unchanged.
  The saved project policy matched the checkpoint: enhanced 60 FPS using
  `rve-4.26`, adaptive strategy; no source was eligible for restoration.
  RVE/CUDA/TensorRT preflight passed.
- Action: Resumed the matching destination session through the editor CLI
  with `--resume --human-progress`. No restart or checkpoint deletion was
  requested. Because there were no completed stages or cached media artifacts
  at the start, preparation necessarily ran again.
- Reproduction: The human progress reporter emitted only the initial 0.0%
  line while progress callbacks remained below its one-percentage-point
  reporting threshold. During the same interval, FFmpeg was active at
  approximately 984-1050% CPU and the cache grew from 422,593,463 to
  475,284,407 bytes in 30 seconds. This is evidence of ongoing computation,
  not an export exception or idle process.
- Regression: The existing four console tests passed before the change. A new
  test for repeated same-percent progress failed because only one line was
  emitted; after adding a five-second heartbeat, all five console tests
  passed.
- Fix: `framestudio/export_console.py` now emits a human-readable heartbeat
  every five seconds when a progress stage remains active without crossing
  the percentage threshold. The heartbeat preserves the observed percentage
  and reports current frame/elapsed time; it does not alter the export path.
- Current status: `blocked` pending completion of the resumed real-media
  export and final metadata, playback, and source-preservation checks. The
  active export process was started with the prior reporter loaded, so this
  run itself will not display the new heartbeat behavior.
- Artifacts: `tests/test_editor_export_console.py`,
  `framestudio/export_console.py`, and the active destination session/cache
  under the user-selected project directory.
- Blockers: No final export exists yet. Since no completed work was available
  at resume time, this attempt cannot skip any prior completed render stage.

## TICKET-104-SILENT-OUTPUT-VALIDATION-HEARTBEATS-002

- Context: 2026-09-24 follow-up for PHASE-009 / FEAT-031 / TICKET-104 on
  `ticket/randomize-multi-clip-add-order`, based at `06a1a8d`.
- Requirement: Given a long frame-count or decoded-output verification scan,
  human-readable export progress periodically identifies that validation is
  still running without restarting completed render work.
- Baseline: The real FFprobe regression test failed with
  `TypeError: probe_frame_count() got an unexpected keyword argument
  'heartbeat_callback'`. Blocking FFprobe frame counting and full-output
  decoding emitted no progress callbacks.
- Fix: Frame-count probes and decoded-output validation now run with a
  five-second timeout heartbeat when a progress callback is available.
  Progress is propagated through output verification, cached-output
  validation, and exact-frame-count checks/correction; the existing
  subprocess path remains unchanged when progress reporting is not requested.
- Regression and functionality: The two real-media FFprobe/FFmpeg heartbeat
  tests and frame-count-repair tests passed (5 tests). The affected export
  regression modules passed (60 tests). Final
  `make quality PYTHON=.venv/bin/python` passed all 493 unit tests,
  compilation, diff checks, format, lint, type, complexity, duplication,
  dependency, audit, security, and churn checks. `make smoke` passed;
  `make contract` passed all 39 CLI contract tests.
- Static analysis: Ruff, mypy, complexity, repository dependency boundaries,
  pip-audit, Bandit, duplication baseline, and churn completed through the
  CI-configured quality command. There were no Bandit findings, no known
  audited dependency vulnerabilities, and no new duplication clones. Reports
  are under `evidence/static-analysis/`. The churn report's three highest
  entries are unrelated skill test files, not changed export files.
- Local/PR parity: `.github/workflows/quality.yml` runs the same
  `make quality PYTHON=.venv/bin/python` command. Local Python is 3.14.7 and
  local FFmpeg/FFprobe are 9.0.1; the workflow uses the Ubuntu 24.04 system
  runtime and apt-installed media tools. Runtime parity is therefore
  `mismatch`, and no remote PR run exists.
- Real export: The resumed real-media export was not restarted. Its
  pre-existing canceled session had no completed stage or reusable artifacts,
  so preparation and rendering ran again. The current run reached final
  output verification after approximately 1 hour 11 minutes; FFprobe was
  actively using CPU during frame counting. This process started before the
  heartbeat fix was loaded, so it cannot demonstrate the new terminal
  heartbeat behavior. At this evidence point, publication and final metadata,
  playback, and source-preservation checks remain pending.
- Delivery: The worktree remains unstaged on
  `ticket/randomize-multi-clip-add-order`; no commit, push, PR, or merge was
  performed. Required user validation, exact local/PR runtime parity, remote
  checks, PR approval, and final real-export verification remain blockers.
- Status: `blocked` pending the running export, user-visible output
  validation, and configured delivery gates.

## TICKET-104-REAL-EXPORT-AND-QUALITY-CLOSEOUT-003

- Context: Final closeout for the authorized `Documents/edit` project export
  and TICKET-104 progress-heartbeat remediation.
- Real export: The resumed export completed successfully through Step 5/5,
  `Export complete`, after 1 hour 18 minutes 36 seconds. It was not restarted
  during final verification. The canceled session initially had zero completed
  stages and no reusable media artifacts, so its preparation/render work
  ran once within this resumed attempt, followed by verification; no completed
  stage was restarted.
- Output verification: The exporter completed its full frame-count and
  decoded-output validation before atomic publication. A follow-up FFprobe
  metadata query confirmed H.264, 1920x1080, 60/1 average and nominal frame
  rate, 87,037 video frames, 1,450.633334 seconds, and AAC stereo audio at
  48 kHz. The publication source-preservation check passed.
- Heartbeat remediation: A new regression proves cached-output verification
  does not advance the monotonic progress reporter to 99%/final-frame before
  a cache is accepted; fallback rendering can still report its real progress.
  The shared validation-heartbeat factory removed duplicated setup identified
  by the duplication gate.
- Final verification: `make quality PYTHON=.venv/bin/python` passed all 494
  unit tests, compilation, diff checks, formatting, Ruff, mypy, complexity,
  duplication baseline (50 existing clones, 0 new), dependency checks,
  pip-audit, Bandit, and churn. `make smoke` passed and `make contract`
  passed all 39 CLI contract tests. The focused export suite passed 22 tests.
- Static-analysis artifacts: `evidence/static-analysis/`. Bandit reported
  zero findings; pip-audit reported no known vulnerabilities; repository
  dependency checks found no boundary violations. The churn report's highest
  entries remain unrelated skill test files.
- Parity and delivery: The local quality command matches
  `.github/workflows/quality.yml`, but runtime parity remains a mismatch
  (local Python 3.14.7/FFmpeg 9.0.1 versus the Ubuntu 24.04 system runtime
  used in CI). No PR run exists. The worktree remains unstaged on
  `ticket/randomize-multi-clip-add-order`; no commit, push, PR, or merge was
  performed.
- User validation: Pending visual playback review of the published file,
  including seeking across edits and checking picture/audio continuity.
- Readiness: The export and local technical gates passed. Ticket delivery
  remains `blocked` on user validation, local/PR runtime parity, remote checks,
  and PR approval.

## TICKET-104-USER-VALIDATION-004

- Requirement: User playback validation confirms the published result opens,
  seeks across edits, preserves expected picture ordering, and has continuous
  synchronized audio with the expected output profile.
- Handoff: The user was asked to open the exported MP4, seek at the beginning,
  middle, end, and edit boundaries, check picture/audio continuity, and confirm
  duration/profile metadata.
- User response: `PASS`, returned through the validation form. No additional
  notes or artifact paths were supplied.
- Status: `passed` for the requested user-visible export validation. Ticket
  delivery remains blocked on local/PR runtime parity, remote checks, and PR
  approval; no commit, push, PR, or merge was performed.

## TICKET-104-FINAL-REVIEW-005

- Review scope: Final export heartbeat implementation, regression tests,
  documentation, evidence, and the active TICKET-104 delivery context.
- Findings: The final code review found no remaining actionable introduced
  code findings. An intermediate duplication-gate failure found repeated
  heartbeat setup; the shared factory was added, and the final configured
  duplication check passed with zero new clones.
- Static analysis: Final `make quality PYTHON=.venv/bin/python` passed all
  configured local checks and 494 tests. `evidence/static-analysis/` contains
  the final raw reports. The local command matches the PR workflow command.
- Parity: `mismatch` because the available host uses Python 3.14.7 and FFmpeg
  9.0.1, while CI is configured for Ubuntu 24.04 system Python and apt media
  tools. No Python 3.12, Docker, Podman, or `act` runner is available locally.
  No PR exists, so remote checks and approval are unavailable.
- User validation: `PASS` received for the export playback/seek/audio
  checklist and appended above. The user supplied no additional artifact paths.
- Delivery blockers: Required runtime parity, remote checks, PR approval, and
  the previously recorded missing per-flow UI artifacts for the other
  authorized worktree changes remain unresolved. The current multi-ticket
  worktree is unstaged on `ticket/randomize-multi-clip-add-order`; it has not
  been committed, pushed, or merged.
- Readiness: `blocked`; the export is complete, but the aggregate delivery
  gates for the authorized worktree are not terminal.

## MULTITRACK-20261016-RESEARCH-AND-BASELINE

- Context: PHASE-009 / FEAT-030, FEAT-031 / TICKET-102 through TICKET-104,
  current dirty baseline at `5f69d5441de9969450a1ac425e2693bc28bff85c`.
  The older aggregate readiness statements above are historical, not a
  current-worktree pass.
- Authorization: The current user explicitly requests four parallel research
  workers, subsequent individual and combined implementations, benchmarks,
  and adoption of the fastest acceptable route. The integration owner retains
  all production-selection, shared verification and delivery responsibilities.
  Historical planning-only PHASE-010 wording is superseded by its subsequent
  execution authorization and this current bounded optimization request;
  protected output semantics are not superseded.
- Research: Two GPT-6.1 Sol and two Haiku 5.5 high-reasoning workers completed
  the initial investigation. Verified findings, source links, inaccessible
  sources, workload shape and candidate matrix are appended to
  `efficient-export-pipeline-benchmark.md`.
- Validation owner: `rubber-duck / gpt-5.6-luna / high / all-validation`,
  confirmed available by actual successful task execution. Initial and
  refined planning reviews permit isolated experiments; they do not certify
  any unmeasured candidate or final readiness.
- Baseline: The exact command recorded in the benchmark report completed
  31 generated-media/recovery/progress/multioutput tests in 209.362 seconds,
  raw log `/tmp/multitrack-baseline.log`. New production code had not been
  integrated. The pre-existing dirty worktree and six untracked source/test
  files were preserved.
- Provenance: A 37-file SHA256 manifest fingerprints the current dirty
  baseline. Three disjoint video/audio/benchmark experiment worktrees plus a
  separate architecture experiment worktree were created from that snapshot.
  Workers cannot edit the integration worktree, shared plans, evidence,
  configuration, or another worker's files.
- Prototype boundaries: Exact-pixel triplicate graph factoring, exact-PCM
  audio input sharing, bounded filter/input decoder threads, and guarded
  source-window seek experiments are separate from lossless per-track/chunk
  architecture comparisons. Codec/quality changes and unsafe sample-phase
  changes cannot win on speed alone. Production adoption requires fresh
  TICKET-102 comparison and TICKET-104 integrity evidence.
- Planning repair: PHASE-009 now points to the reopened PHASE-008/FEAT-028
  records and explicitly depends on their previously delivered export
  baseline, not closure of independent CHG-011 follow-ups.
- Safety: The private full export is still paused and excluded. Representative
  shape was inspected read-only; generated sources, cache and outputs belong
  to experiments. Timed comparisons must not compete concurrently. The
  original system power profile must be restored after each measured batch.
- Current status: experiments in progress; no new implementation benchmark
  winner, production adoption, commit, push or lifecycle closure is claimed.

## MULTITRACK-20261016-MEASURED-INTEGRATION

- Context: PHASE-009 / FEAT-030, FEAT-031 / TICKET-102 through TICKET-104.
  The integration branch is `perf/multitrack-export-20261016`. All prior dirty
  changes remain preserved; no commit, push, PR or closed-record move occurred.
- Validation profile for the decisions in this entry:
  `rubber-duck / gpt-5.6-luna / high / all-validation`, successfully executed.
  A bounded review approved the clock repair/corrected baseline, and another
  approved the actual measured combination for integration. Neither is a
  final delivery-readiness decision or human confirmation.
- Baseline failure and fix: the original controlled screen's untouched
  renderer emitted 45 of 56 expected frames. Concat's single-frame interval
  durations overlapped PTS. Final `settb=<reciprocal rate>,setpts=N` retains
  all ordered pre-encode pixels with the expected CFR frame lattice. Original
  failure data remains retained, not overwritten or used as a speed baseline.
- Implementation: equal triplicate scale/format is shared before split;
  equal audio paths use explicit `asplit` with independent branch DSP;
  video graphs with at least three distinct consumed input paths use two
  complex-filter threads and one decoder thread per input. One/two-path
  behavior, final encoder settings, native processing, mux and validation
  settings remain unchanged.
- Cache migration: only AV video/mux preparation recipe version changes from
  2 to 3. Native/upscale/FPS and independent audio keys are unchanged.
  `COMPOSITOR_VERSION` stays unchanged; existing final receipt revalidation
  still checks the strict output contract.
- Measured implementation: three sequential counterbalanced trials without
  harness thread overrides. The large 35-source/114-block/116-interval fixture
  improves 11.468 s to 8.027 s (30.0% less time); triplicate improves 2.525 s to
  1.776 s (29.7%). Enhanced/recovery gains are small. Source fixtures are
  generated 320x180 media; output remains 1920x1080. These are not measurements
  of the private full project or of source-reel batch completion.
- Selection scope: existing native range reuse is baseline behavior, not a
  new gain. Audio input count falls 342 to 35, but audio sharing alone is not
  a standalone speed winner. Video-only lossless track/chunk combinations
  were slower; seek/NVDEC remain experimental. No encoder-quality change,
  GPU scaler/encoder or lossy intermediate was selected.
- Artifacts: `multitrack-render-results.json` contains individual trial
  times, medians/ranges, sampled process-tree RSS, stage/input observations,
  candidate hashes, raw-report hashes and supplemental contract checks.
  Full raw reports, fixture outputs and the preserved correction-only baseline
  remain under the session's `files/multitrack-*` artifacts.
- Additional contract review: the bounded validator requested explicit codec,
  layout, SAR/time-base and planned PCM-count gates. Every retained final
  output was subsequently probed and its decoded artifacts rehashed. All
  planned frame/sample counts and baseline/candidate contracts agree.
  The harness now records these extra fields and independently rejects wrong
  decoded counts, rather than allowing two equally wrong outputs to qualify.
  An all-ineligible comparison now exits nonzero while retaining diagnostics.

### Observed technical and automated functionality evidence

These are agent-run results; terminal automatic validation of the final
integrated evidence remains pending below.

| Category / protected outcome | Executable command or test | Observed result |
| --- | --- | --- |
| Corrected baseline / dynamic layouts | `.venv/bin/python -m unittest tests.test_multitrack_render_benchmark tests.test_multitrack_architecture_benchmark tests.test_editor_video_compositor tests.test_editor_av_compositor` | Initial combined run had 45 passing tests and one architecture-parser incompatibility with the new final clock. The parser was corrected; its real comparator/restart test then passed. |
| Recipe invalidation / retained completed work | `.venv/bin/python -m unittest tests.test_editor_render_preparations_functionality.RenderPreparationFunctionalityTests.test_clock_recipe_invalidates_video_and_mux_but_reuses_native_and_audio` | Real FFmpeg AV exports pass in 2.130 s; zero repeated extraction/interpolation/audio jobs, one new video and mux, identical decoded frames and unchanged source SHA256. |
| Prior full-suite environment failures | `env GDK_BACKEND=x11 GSK_RENDERER=cairo .venv/bin/python -m unittest tests.test_editor_precise_preview_functionality.ForwardDecoderStateTests tests.test_editor_removal_controls_functionality.NativeRemovalControlsFunctionalityTests tests.test_phase010_functionality.Phase010FunctionalityTests.test_complete_edit_and_delivery_journey` | 11 tests pass in 59.497 s using existing Xwayland and the quality environment's PyAV. The system-Python/Wayland baseline's missing-PyAV/X11 failures were environmental; `xvfb-run` is absent and was not falsely reported as run. |
| Partial batch failure / truthful progress | `.venv/bin/python -m unittest tests.test_editor_source_outputs.EditorSourceOutputTests.test_cli_partial_success_includes_final_and_source_results` | Passes both partial-failure subcases. The stale empty-stdout assertion now permits only `export.progress` JSON Lines, never a terminal export-success response. |
| Selected graph equivalence | Final production large/triplicate/recovery benchmark commands in `efficient-export-pipeline-benchmark.md` and recorded JSON groups | All 42 final production-policy rows preserve exact ordered decoded video and signed 32-bit PCM, counts, metadata and source inputs. Recovery rows include fresh, warm and controlled cancellation/reopen boundaries. |
| Experimental alternatives | `benchmarks/multitrack_architecture_benchmark.py --duration 5 --tracks 3 --segments 3 --workers 1,2,3 --trials 3 --combined --recovery-demo` and late-window render harness | All 30 architecture rows and 15 late-window rows complete their equality gates. Their distinct timing scopes/limits are recorded; they are not production routes. |

### Static findings and final verification state

- New benchmark/test files are included in Makefile format/lint/type,
  complexity, duplication and Bandit scopes so CI consumes the same scope.
- Format, configured types/complexity, dependency graph/audit, compilation
  and diff checks ran. The audit found no known vulnerabilities.
- Two introduced benchmark hash-helper clones were removed using the existing
  production hasher for the architecture harness and a bounded-buffer
  implementation for the isolated-runtime harness. The approved baseline was
  copied unchanged to the session report directory, never inflated:
  41 total clones, 0.644%, **zero new clones**.
- Bandit findings were addressed with resolved executable paths and clearer
  CLI-argument names. The shared-temp-root rejection guard's B108 false
  positive is annotated narrowly; it rejects `/tmp` and `/var/tmp`, rather
  than using them as artifact roots. Original raw findings remain in the
  first static log. Final Bandit reports zero findings.
- Full-scope Ruff still exits nonzero for the pre-existing B905 at
  `tests/test_editor_precise_preview_functionality.py:263`; that file is not
  modified by this task. This finding is preserved, not claimed fixed.
- Raw static artifacts: session `files/multitrack-final-static/`;
  `/tmp/multitrack-final-static.log` and
  `/tmp/multitrack-final-static-rerun.log`.
- Final full integrated suite is running under the quality Python/X11
  environment. Its result, real-media workstation charter and final
  exact-profile automatic review must be appended before a terminal claim.
- Required local/PR runtime parity remains a separate delivery gate: the
  available host is Python 3.14/FFmpeg 9/Xwayland, whereas configured CI uses
  Ubuntu 24.04 system Python/media tools and Xvfb. Matching Makefile scopes do
  not prove matching runtimes or remote check results. Tickets remain open
  in `verifying`; no delivery-ready claim is made.

## MULTITRACK-20261016-FINAL-OBSERVED-VERIFICATION

- Context/profile: the same PHASE-009 / FEAT-030/031 / TICKET-102/103/104
  scope and exact configured
  `rubber-duck / gpt-5.6-luna / high / all-validation` decision owner.
  The following are raw observed results, submitted to that final validator
  rather than self-classified as an automatic pass.
- Full-suite command:
  `env GDK_BACKEND=x11 GSK_RENDERER=cairo FRAMESTUDIO_PHASE010_ARTIFACT_DIR=<session>/files/multitrack-final-functionality make test PYTHON=.venv/bin/python`.
  **1030 tests ran in 800.131 s; two failures, 11 skipped, no errors.**
  Export, benchmark, PCM/video equality, cache transition and recovery tests
  did not fail. Do not report the overall suite as green.
- The extreme-zoom real-pointer snap assertion failed with exactly the same
  `2.1370430297637473 != 2.137` on both the preserved pre-optimization
  worktree and current implementation. The PHASE-010 pointer-click journey
  failed during the full run but passed in both isolated baseline/current
  comparisons. Commands:
  `env GDK_BACKEND=x11 GSK_RENDERER=cairo <quality-python> -m unittest tests.test_editor_keyboard_functionality.EditorKeyboardFunctionalityTests.test_real_pointer_click_with_small_hand_movement_still_snaps_at_extreme_zoom tests.test_phase010_functionality.Phase010FunctionalityTests.test_complete_edit_and_delivery_journey`.
  Each comparison ran two tests (baseline 51.744 s; current 51.303 s), with
  only the identical extreme-zoom failure. The unrelated pointer behavior was
  not rewritten to clear the gate; raw failures remain visible.
- Automated functionality test **MULTITRACK-REAL-MEDIA-AV-PARITY**:
  session script `files/multitrack-real-media-check.py`, executable with
  `env GDK_BACKEND=x11 GSK_RENDERER=cairo .venv/bin/python <session-script> --project <read-only-local-project> --current-root <repository> --baseline-root <preserved-corrected-baseline> --artifact-root <new-direct-session-child> --report <session>/files/multitrack-real-media-result.json`.
  It stream-copies short excerpts from three active local HD inputs, creates
  a separate three-track/six-block project with repeats and a triplicate
  interval, and exports through actual analysis, AV planning, checkpointed
  rendering and persisted MP4 verification. Baseline/current outputs have
  exactly equal ordered decoded video and signed-32-bit PCM:
  30 frames, 48000 stereo PCM frames, 1920x1080, H.264/yuv420p, AAC/48 kHz,
  square pixels and equal time bases.
- The same executable then opens the resulting video through actual GTK
  `--source <output> --smoke-test --smoke-project <owned-project>`.
  It asserts excerpt SHA256 preservation, original media size/mtime/ctime
  preservation and original project SHA256 preservation. All assertions and
  playback smoke passed. This is a real-media correctness check, **not** a
  real-project speed measurement, enhancement run or resumed original export.
  Private media and paths stay outside repository evidence.
- The charter's first attempt failed in the **baseline** because the new
  session-only helper lacked Python's multiprocessing `__main__` guard.
  Added that guard and reran in a fresh owned directory; no production
  fallback or disabled parallel audio analysis was introduced. The first
  traceback and subsequent successful result remain retained locally.
  Performance mode was restored to the prior `power-saver` after both attempts.
- `make contract PYTHON=.venv/bin/python`: **45 tests pass in 23.897 s**.
  `env TMPDIR=<new-owned-session-directory> GDK_BACKEND=x11 GSK_RENDERER=cairo make smoke PYTHON=.venv/bin/python`:
  **both generated-media GTK creation/reopen flows exit 0**; the isolated
  temporary directory was removed after its own fixtures were cleaned.
- Final deterministic command:
  `make -k static-analysis compile diff-check PYTHON=.venv/bin/python STATIC_ANALYSIS_DIR=<session>/files/multitrack-final-static`.
  Exit 2 remains solely the documented pre-existing Ruff B905. Format:
  193 files compliant; all configured mypy calls pass, including both new
  harnesses; complexity, dependency graph, dependency audit, Bandit,
  compilation and whitespace checks pass. Duplication remains 41 clones /
  0.644% / zero new against the unchanged approved baseline. Final Bandit
  has no findings or malformed-annotation warnings.
- Churn artifact contains only three JavaScript skill-test entries, no
  compositor/harness entries. It supplies **no useful Python hotspot ranking**
  for this change and is not substituted for functional or review evidence.
- SHA256 of both integrated compositor source files still matches the measured
  candidate hashes in `multitrack-render-results.json`. No production source
  changed after the full-suite run.
- **Remaining gates:** full-suite pointer failure; full-run journey
  intermittency; pre-existing B905; required Ubuntu/Xvfb/PR-runtime parity and
  remote evidence unavailable locally. Final exact-profile review follows.
  Tickets remain open/`verifying`; original project/full export remain paused.

## MULTITRACK-20261016-FINAL-VALIDATOR

- Decision owner actually invoked:
  **rubber-duck / gpt-5.6-luna / high / all-validation**.
  It reviewed the final production implementation, synthetic reports, decoded
  count/contract gates, source hashes, functionality observations, baseline
  comparisons and static/CI configuration. This is `automaticValidation`,
  never `userValidation`.
- **Introduced blocking findings: none.** No new correctness, security or
  optimization-eligibility bug was identified in the selected route.
- **Scoped automated functionality: PASS.** Accepted affected outcomes:
  clock frame retention; triplicate graph equivalence; audio input/PCM reuse;
  cache recipe migration; cancellation/recovery reuse; generated and
  workstation real-media AV output; contract and GTK playback smoke.
- **Measured selection accepted within stated limits:** the combined policy
  is faster on the generated large/triplicate fixtures, with exact decoded
  equality. The review accepted the rejected track/chunk alternatives and
  experimental-only status of seek/NVDEC. It explicitly rejected full-project
  extrapolation or interpreting warm residual timers as fresh export gains.
- **Overall automatic validation: FAILED/BLOCKED.** Full tests and full Ruff
  remain failed despite baseline provenance; the result cannot be changed
  into a pass by calling them pre-existing. Required Ubuntu/Xvfb runtime
  equivalence and remote checks remain unavailable. Churn's Python coverage
  limitation remains explicit.
- **Delivery readiness: BLOCKED.** No commit, push, PR or closure is authorized
  by this result. PHASE-009, FEAT-030/031 and TICKET-102/103/104 stay open;
  the tickets remain `verifying`. Prior uncommitted recovery/progress work
  and original export checkpoints are preserved.
- Portable final decision and sanitized workstation observations are added to
  `multitrack-render-results.json`. Raw test/static/contract/smoke and baseline
  comparison logs are copied from `/tmp` to the persistent session `files/`
  directory under their `multitrack-*` filenames. No private media/path is
  added to repository evidence.
- Next delivery action is to obtain the actual configured Ubuntu 24.04/Xvfb
  quality/remote result and resolve its failed gates under scoped authorization.
  This is a blocker handoff, not a claim that CI was run or permission to bypass
  the current commit gates.
- Final cleanup/verification: both explicitly owned private real-media test
  directories were removed after saving the initial harness failure log and
  successful result outside the repository. Synthetic benchmark artifacts,
  original media, original project and export checkpoints were retained.
  Portable JSON parses successfully, measured compositor hashes still match,
  `git diff --check` passes, power profile is `power-saver`, and no tracked
  shell session remains running.

## MULTITRACK-20261016-QUALITY-REMEDIATION

- The user requested continued autonomous work instead of stopping at the
  previous local quality failures. TICKET-104 now records the bounded
  verification repair scope. The prior failed runs and validator decision
  remain historical evidence, not erased or retroactively marked passed.
- Decision owner remains
  `rubber-duck / gpt-5.6-luna / high / all-validation`; final classification
  awaits the complete rerun and its scoped review below.
- Restored the previously missing CI display tools only after the exact
  `xvfb-run` command failed with exit 127. Official Arch
  `xorg-server-xvfb 21.1.25-2` and `xorg-xauth 1.1.5-1` packages were downloaded,
  their detached signatures verified against the system's official public
  signing keyring, and extracted into session-owned `multitrack-xvfb-tools/`.
  No system package, manifest or production dependency changed. Commands use
  an explicit scoped PATH, authenticated Xvfb, and `-screen 0 1920x1200x24`.
- The isolated display alone did not cure the pointer assertion: baseline
  failure was retained in `multitrack-isolated-pointer-check.log`. Actual GTK
  event traces then established two distinct issues: a segment press suppressed
  initial snap until release; physical test coordinates also omitted the
  native widget-to-surface translation (client-side decoration offsets).
- Regression
  `EditorTrackDragTests.test_uncommitted_segment_press_snaps_before_release`
  failed before production modification (nonzero unsnapped position instead
  of the segment start). `_seek_from_x` now permits snapping while a drag is
  uncommitted, including the initial segment press. Established drag movement
  still bypasses snapping, and the Super modifier still bypasses it.
- Regression
  `EditorTrackDragTests.test_screen_coordinates_include_native_surface_translation`
  failed before the helper accepted a native transform. The common physical
  pointer helper now adds `Gtk.Native.get_surface_transform()` for native
  widget coordinates. Keyboard, drag and removal charters pass their native
  translation; raw root-coordinate checks keep the zero-transform default.
  No assertions were removed or click failures retried into success.
- Initial focused repair exposed six outside-click failures under Xvfb,
  retained in `multitrack-quality-remediation.log`. Traces showed the nominal
  outside point was actually inside the snap zone because of the missing
  decoration transform. Correcting that coordinate conversion resolved them.
- Ruff B905: the preview comparison already asserts equal buffer lengths;
  its `zip` now specifies `strict=True`. Pixel-difference tolerances and
  assertions remain unchanged.
- Handler/protected-flow command:
  `.venv/bin/python -m unittest tests.test_editor_track_drag tests.test_editor_timeline tests.test_editor_timeline_snapping tests.test_editor_seek_dispatch`.
  **49 tests pass in 0.052 s**, including actual-drag, threshold and bypass
  protections.
- Automated functionality command:
  `PATH=<session-tools>/usr/bin:$PATH xvfb-run --auto-servernum --server-args='-screen 0 1920x1200x24' env GDK_BACKEND=x11 GSK_RENDERER=cairo .venv/bin/python -m unittest tests.test_editor_keyboard_functionality tests.test_editor_track_drag_functionality tests.test_editor_removal_controls_functionality tests.test_phase010_functionality.Phase010FunctionalityTests.test_complete_edit_and_delivery_journey`.
  **27 tests pass in 115.767 s, one native-Wayland-only skip**. These exercise
  actual physical pointer/keyboard events, snapping, Super bypass, cross-track
  dragging, removal, persistence and the full editing/export journey.
- `make contract smoke PYTHON=.venv/bin/python` under a separate authenticated
  Xvfb also exits 0; the contract suite again passes 45 tests.
- A fresh full **`make quality`** is running under authenticated Xvfb, with
  the same Cairo renderer and screen settings as CI. Its raw output is
  persistent at session `files/multitrack-isolated-final-quality.log`.
  Python/media distro versions still differ from Ubuntu CI, so display-wrapper
  restoration alone is not claimed as complete remote/runtime parity.
- Video/audio compositor hashes and the measured policy are unchanged.
  Neither the original full export nor its checkpoints was resumed or removed.

## MULTITRACK-20261016-LOCAL-QUALITY-TERMINAL

- The same scoped TICKET-104 repair now has terminal raw full-gate evidence:
  `PATH=<session-tools>/usr/bin:$PATH xvfb-run --auto-servernum --server-args='-screen 0 1920x1200x24' env GDK_BACKEND=x11 GSK_RENDERER=cairo FRAMESTUDIO_PHASE010_ARTIFACT_DIR=<session>/files/multitrack-isolated-final-functionality make quality PYTHON=.venv/bin/python STATIC_ANALYSIS_DIR=<session>/files/multitrack-final-static`.
  **Exit 0. All 1032 tests complete in 831.295 s, 10 skipped, no failures or
  errors.** Skips remain explicit environment/optional-capability results,
  not successful tests. The earlier pointer and journey failures no longer
  occur in the full run.
- The command also passes compilation, whitespace, format (193 files), full
  Ruff including the previous B905, every configured mypy call, complexity,
  dependency boundaries, dependency advisory audit and Bandit. Duplication:
  41 clones, 0.644%, zero new against the unchanged approved baseline.
  Churn still has no useful Python entries; that limitation is unchanged.
- Raw output is persisted directly at session
  `files/multitrack-isolated-final-quality.log`. Post-run compositor SHA256
  still matches the actual benchmarked candidate files, `git diff --check`
  passes and `powerprofilesctl get` returns `power-saver`.
- The post-repair CLI contract and both GTK smoke flows also pass under
  authenticated Xvfb, as recorded in
  `files/multitrack-isolated-contract-smoke.log`.
- This terminal local result supersedes the earlier failed local quality
  results, without erasing their provenance. The exact configured Rubber Duck
  profile must classify this new result and the narrow repair before recording
  terminal `automaticValidation`.
- No actual Ubuntu/remote CI result has been obtained. Restoring the display
  wrapper is not represented as changing host Python/FFmpeg to Ubuntu versions,
  publishing the branch, fulfilling remote checks or closing delivery records.

## MULTITRACK-20261016-QUALITY-REMEDIATION-VALIDATOR

- The required **rubber-duck / gpt-5.6-luna / high / all-validation**
  validator reviewed the narrow quality repair and latest terminal evidence.
  It found **no introduced blocking issue**. This review supplements the
  earlier optimization review; measured compositor source is unchanged.
- **Scoped `automatedFunctionality`: PASS. Scoped `automaticValidation`:
  PASS.** These are agent-owned outcomes, not user confirmation. The reviewer
  accepted the early segment-press snapping, native-to-surface physical input
  conversion and strict byte-comparison zip correction.
- **Local technical/static quality: PASS**, with explicit skips and the
  unchanged optional Python-churn coverage concern. To avoid counting skips
  as successes, the raw full result is **1032 tests run, 1022 successful,
  10 skipped, zero failures/errors**, in 831.295 s. The full `make quality`
  exits 0. CLI contracts and GTK create/reopen smoke also pass.
- **Original local request: complete.** Research, individual/combined
  experiments, measured safe production selection, resumability/decoded
  parity evidence and the requested continuation's local quality remediation
  have terminal evidence. The previous failed local runs remain preserved;
  the latest passing results supersede them, not conceal them.
- **Publication/lifecycle readiness remains BLOCKED**, independently of that
  local completion: host/Ubuntu-runtime parity and actual remote checks are
  unavailable, the branch is unpublished and the worktree intentionally
  contains unstaged prior work. No commit, push, PR, human-validation claim
  or ticket/feature/phase closure follows from this decision.
- The portable `multitrack-render-results.json` now records the latest passing
  local result and keeps the earlier failed full-suite result as history.
  Planning records remain open/`verifying`. A completed-feature changelog entry
  is deferred because the feature records have not met delivery closeout.
- Next delivery action belongs to `aidd-review`: resolve actual remote
  Ubuntu/CI-runtime evidence and its configured gates before publication or
  lifecycle closeout. This does not authorize a gate bypass or implicit staging.
