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
