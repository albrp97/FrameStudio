# Refine Export Planning and Enhanced Smart Render Evidence

**Phase:** PHASE-007
**Feature:** FEAT-021
**Ticket:** TICKET-060
**Branch:** `ticket/define-target-fps-selection-and-enhancement-scope`
**Base revision:** `93b49e8`
**Evidence started:** 2026-08-24

## Planning chain

`OBJ-001 -> SCOPE-001 -> CAP-005/CAP-011/CAP-012 -> PHASE-007 ->
FEAT-021 -> TICKET-060`

## Acceptance coverage

- The GTK export plan is compact and exposes the final duration, estimated
  processing time, and estimated output size.
- New export planning defaults to 60 FPS with enhancement enabled, while
  explicit persisted settings remain authoritative.
- Lowest/highest FPS labels include their resolved rates.
- A missing preferred RVE environment selects the validated FFmpeg fallback
  instead of blocking a valid plan.
- A compatible single-source full edit runs interpolation once and does not
  invoke a second fallback re-encode.
- Existing verification, cancellation, atomic publication, source
  preservation, ordinary routes, and legacy behavior remain protected.

## Evidence entries

### E-060-BASELINE-001 - Protected baseline before implementation

- **Timestamp:** 2026-08-24
- **Category:** baseline
- **Commands:** `make check PYTHON=.venv/bin/python`; `make contract
  PYTHON=.venv/bin/python`; `make smoke PYTHON=.venv/bin/python`
- **Expected:** Existing repository checks pass before corrective changes.
- **Observed:** 240 repository tests passed, 29 CLI contract tests passed,
  generated-media smoke completed successfully, Python compilation passed,
  and `git diff --check` passed.
- **Status:** passed

### E-060-REGRESSION-001 - Focused regressions before implementation

- **Timestamp:** 2026-08-24
- **Category:** regression
- **Command:** `.venv/bin/python -m unittest
  tests.test_editor_fps_policy tests.test_editor_persistence
  tests.test_editor_export_panel
  tests.test_editor_export_execution.EditorExportExecutionTests.test_single_full_source_enhancement_does_not_reencode_after_interpolation`
- **Expected:** The new default, panel, backend-fallback, estimate, and
  direct-enhancement regressions fail against the current implementation.
- **Observed:** The policy and persistence tests still resolved the old
  highest/non-enhanced defaults, the panel regression could not import the
  not-yet-existing named-choice helper, and the direct-enhancement regression
  observed the fallback payload instead of direct interpolation output.
- **Status:** passedWithConcerns
- **Meaning:** The failures reproduce the requested defects and establish the
  implementation starting point; the import failure is the expected missing
  helper for the new panel contract.

## Readiness

Implementation and verification have not been completed. The ticket remains
open until technical gates and required target-workstation/user validation are
terminal.

### E-060-IMPLEMENTATION-001 - Corrective implementation completed

- **Timestamp:** 2026-08-24T13:14:41+02:00
- **Category:** implementation
- **Requirement:** Compact export planning, usable FPS defaults, validated
  fallback behavior, and direct publication for eligible enhanced exports.
- **Observed:** New export plans default to 60 FPS with enhancement enabled;
  saved explicit policies remain authoritative; lowest/highest choices include
  resolved rates; the GTK panel uses a compact summary grid; output-size
  estimates and fallback notices are exposed as structured state; and eligible
  single-source interpolation results are verified and published without a
  second fallback render. README behavior documentation was updated.
- **Status:** passed
- **Source references:** `framestudio/fps_policy.py`,
  `framestudio/export_panel.py`, `framestudio/export_estimates.py`,
  `framestudio/export_interpolation.py`, `framestudio/app_export.py`,
  `README.md`

### E-060-REGRESSION-002 - Focused export regression and real-media coverage

- **Timestamp:** 2026-08-24T13:14:41+02:00
- **Category:** regression
- **Command:** `.venv/bin/python -m unittest
  tests.test_editor_fps_policy tests.test_editor_persistence
  tests.test_editor_export_panel tests.test_editor_export_planning
  tests.test_editor_export_execution`
- **Expected:** Defaults, persisted policy behavior, named choices, compact
  summary data, output-size estimates, fallback selection, ordinary routes,
  enhanced cut delivery, and direct enhanced publication pass.
- **Observed:** 33 tests passed, including generated-media verification of a
  1920x1080 stereo source interpolated from 10 FPS to 20 FPS with no fallback
  re-encode, matching duration, output dimensions, audio presence, and source
  preservation.
- **Status:** passed

### E-060-GATE-001 - Protected repository checks

- **Timestamp:** 2026-08-24T13:14:41+02:00
- **Category:** gate
- **Command:** `make check PYTHON=.venv/bin/python`
- **Expected:** Existing tests, compilation, and diff checks pass.
- **Observed:** 244 tests passed; Python compilation and `git diff --check`
  passed.
- **Status:** passed

### E-060-GATE-002 - CLI contract and generated-media smoke checks

- **Timestamp:** 2026-08-24T13:14:41+02:00
- **Category:** gate
- **Commands:** `make contract PYTHON=.venv/bin/python`;
  `make smoke PYTHON=.venv/bin/python`
- **Expected:** CLI contracts and editor generated-media smoke flows pass.
- **Observed:** 29 CLI contract tests passed and generated-media smoke
  completed successfully, including project reopen behavior.
- **Status:** passed

### E-060-QUALITY-001 - Configured local quality suite

- **Timestamp:** 2026-08-24T13:14:41+02:00
- **Category:** staticAnalysis
- **Command:** `make quality PYTHON=.venv/bin/python`
- **Expected:** Repository-configured formatter, lint, type, complexity,
  duplication, dependency, security, test, and churn checks complete.
- **Observed:** The suite passed with Ruff format/lint, mypy, complexity,
  repository dependency analysis, pip-audit (`No known vulnerabilities
  found`), Bandit with no findings, jscpd report generation, and churn report
  generation. Reports are retained under `evidence/static-analysis/`.
  jscpd still reports the repository's known helper/test overlap; this remains
  a non-blocking review warning rather than new functional evidence.
- **Status:** passedWithConcerns
- **Artifacts:** `evidence/static-analysis/jscpd-report.json`,
  `evidence/static-analysis/pip-audit.json`,
  `evidence/static-analysis/bandit.json`,
  `evidence/static-analysis/dependencies.json`,
  `evidence/static-analysis/churn.json`

### E-060-FIX-REGRESSION-001 - Missing-RVE fallback regression is red

- **Timestamp:** 2026-08-25T20:40:50+02:00
- **Category:** regression
- **Command:** `python3 -m unittest
  tests.test_fps.FpsTests.test_missing_rve_uses_ffmpeg_fallback`
- **Expected:** A generated 10-FPS source completes at the requested target
  rate through the FFmpeg fallback, with the expected rational frame count and
  an explicit fallback notice.
- **Observed:** The test errored in `run_interpolation_rve` before output
  creation with `RVE Python environment was not found`.
- **Status:** failed
- **Failure:** The current legacy pipeline has no fallback dispatch when the
  default RVE prerequisite is absent.

### E-060-FIX-IMPLEMENTATION-001 - Legacy FPS fallback dispatch

- **Timestamp:** 2026-08-25T20:40:50+02:00
- **Category:** implementation
- **Requirement:** Given the preferred RVE runtime is unavailable, direct and
  unified FPS commands should use the validated FFmpeg interpolation route
  while preserving exact target frame timing and safe publication.
- **Observed:** Added preflight detection for missing RVE prerequisites,
  explicit `ffmpeg-minterpolate` engine selection, rational target-rate
  filtering with bounded frame output, progress reporting, atomic partial
  publication, cleanup, and process cancellation handling. The unified
  `framestudio-concat` parser accepts the same explicit fallback backend.
- **Status:** passed
- **Source references:** `framestudio_fps.py`, `framestudio_concat.py`,
  `tests/test_fps.py`, `README.md`

### E-060-FIX-REGRESSION-002 - Missing-RVE fallback regression is green

- **Timestamp:** 2026-08-25T20:40:50+02:00
- **Category:** regression
- **Command:** `python3 -m unittest
  tests.test_fps.FpsTests.test_missing_rve_uses_ffmpeg_fallback`
- **Expected:** A generated 10-FPS source completes through the fallback at the
  requested target rate, with the rational frame count and explicit notice.
- **Observed:** The test passed; the fallback produced the requested target
  rate and frame count without modifying the source.
- **Status:** passed

### E-060-FIX-GATE-001 - Protected checks after implementation

- **Timestamp:** 2026-08-25T20:40:50+02:00
- **Category:** gate
- **Command:** `make check`
- **Expected:** Protected tests, compilation, and diff checks remain green.
- **Observed:** 253 tests passed; Python compilation and
  `git diff --check` passed.
- **Status:** passed

### E-060-FIX-QUALITY-001 - Initial quality run found a typing regression

- **Timestamp:** 2026-08-25T20:40:50+02:00
- **Category:** staticAnalysis
- **Command:** `make quality PYTHON=.venv/bin/python`
- **Expected:** All configured quality checks pass after the implementation.
- **Observed:** Tests, compilation, formatting, lint, complexity, duplication,
  and dependency checks completed, but mypy rejected `select_engine` for
  returning the dynamically typed `argparse.Namespace.engine` value.
- **Status:** failed
- **Failure:** `framestudio_fps.py:1063` reported `no-any-return`.
- **Fix:** Added an explicit string type guard before returning the selected
  engine.

### E-060-FUNCTIONALITY-001 - Target-workstation GTK export flow

- **Timestamp:** 2026-08-24T13:14:41+02:00
- **Category:** functionality
- **Setup:** GTK 4/PyGObject imported successfully; a temporary 320x180,
  10-FPS, 2-second FFmpeg test source was opened with
  `framestudio.py --source`.
- **Steps:** Opened **Export video**, inspected the export summary, opened the
  output-FPS dropdown, and started the export with the default settings.
- **Expected:** The panel is readable without an assumptions wall of text,
  defaults to 60 FPS with enhancement on, names lowest/highest choices with
  their rates, reports the FFmpeg fallback when RVE is unavailable, and
  completes a verified export.
- **Observed:** The panel showed final duration, estimated processing time,
  estimated output size, backend, 60 FPS, enhancement On, and the validated
  FFmpeg fallback notice. The dropdown showed `Lowest input FPS (10 FPS)`,
  `Highest input FPS (10 FPS)`, `Custom FPS`, and `60 FPS`. The export
  completed at 100% with a 1920x1080, 60-FPS, 2-second MP4; the source
  remained unchanged.
- **Status:** passed
- **Artifacts:** `evidence/screenshots/ticket-060-export-panel.png`,
  `evidence/screenshots/ticket-060-export-panel-fps-choices.png`,
  `evidence/screenshots/ticket-060-export-progress-or-complete.png`

### E-060-REVIEW-001 - Review readiness assessment

- **Timestamp:** 2026-08-24T13:14:41+02:00
- **Category:** review
- **Expected:** The final implementation is covered by planning links,
  requirements, tests, protected flows, quality evidence, documentation, and
  user-validation readiness.
- **Observed:** The implementation, focused regressions, protected checks,
  contract/smoke flows, local quality suite, and target-workstation GTK flow
  are terminal. The configured PR workflow invokes the same `make quality`
  command, but no remote check has run and no Git remote/upstream is
  configured. The required human user-validation response is also pending.
- **Status:** passedWithConcerns
- **Blockers:** User validation and remote checks remain unavailable; the
  ticket must stay in `verifying` and must not be committed or closed until
  the configured approval and delivery gates are satisfied.

## Required user-validation handoff

The ticket remains `verifying` until the user returns one of the following
terminal responses:

```text
PASS: every required check succeeded; evidence: <paths or notes>
FAIL: <failed check and observed result>
BLOCKED: <missing service, data, permission, or capability>
NOT APPLICABLE: <reason and approval>
```

### Changed behavior to validate

The GTK **Export video** flow now opens a compact planning panel. New plans
default to `60 FPS` with FPS enhancement enabled, the lowest/highest choices
include their resolved rates, missing RVE artifacts use a validated FFmpeg
fallback when eligible, and compatible full-source enhancement avoids a
second render.

### Prerequisites and representative data

- Run from the repository root with `python3`, GTK 4/PyGObject, `ffmpeg`, and
  `ffprobe` available.
- Use one short 1080p source below 60 FPS with AAC 48 kHz stereo audio for the
  direct smart-render check. Also use one non-1080p or cut source to confirm
  the ordinary fallback route.

### Exact steps and expected results

1. Start the editor with `make editor ARGS="--source <video>"`.
2. Click **Export video**. Confirm the panel shows a compact summary with
   inputs, final duration, output FPS, enhancement state, processing-time
   estimate, output-size estimate, and backend; no assumptions paragraph
   should dominate the panel.
3. Confirm the default is **60 FPS** and enhancement is **On**.
4. Open the FPS menu and confirm the lowest and highest entries include their
   resolved rates, alongside **Custom FPS** and **60 FPS**.
5. With the preferred RVE environment unavailable, confirm the panel reports
   the validated FFmpeg fallback and leaves **Start export** enabled when the
   source is eligible.
6. Export the compatible uncut 1080p source. Confirm the result is playable,
   has the requested target FPS and expected duration, and does not trigger a
   second ordinary render.
7. Export the cut or dimension-mismatched source. Confirm it uses the safe
   fallback route, preserves the source, and publishes only after
   verification.

### Failure paths, cleanup, and evidence

- If the source is variable-frame-rate, unsupported, or the destination is
  unsafe, confirm the panel explains the blocker and does not start export.
- If export fails or is cancelled, confirm partial output is removed and the
  source and existing output remain unchanged.
- Remove only the temporary test outputs after validation.
- Return the response above with screenshots or notes, the output path and
  `ffprobe` metadata, and any observed failure message. Use the existing
  evidence screenshots as the before/after comparison:
  `evidence/screenshots/phase-007-editor-open.png`,
  `evidence/screenshots/ticket-060-export-panel.png`, and
  `evidence/screenshots/ticket-060-export-panel-fps-choices.png`.

### E-060-REGRESSION-003 - Requested-backend fallback notice

- **Timestamp:** 2026-08-24T13:19:21+02:00
- **Category:** regression
- **Command:** `.venv/bin/python -m unittest
  tests.test_editor_export_panel`
- **Expected:** A fallback notice identifies the preferred backend that was
  requested, including when it is a non-default RVE identifier.
- **Observed:** The regression first failed because the notice always named
  `rve-4.26`; after the focused fix, all 7 export-panel tests passed and the
  notice names the requested backend.
- **Status:** passed
- **Source references:** `framestudio/export_panel.py`,
  `tests/test_editor_export_panel.py`

### E-060-QUALITY-002 - Quality suite after final panel fix

- **Timestamp:** 2026-08-24T13:19:21+02:00
- **Category:** staticAnalysis
- **Command:** `make quality PYTHON=.venv/bin/python`
- **Expected:** The repository-configured quality suite remains terminal after
  the final export-panel change.
- **Observed:** 245 tests passed; compilation, diff checks, Ruff formatting and
  lint, mypy, complexity, duplication, dependency checks, pip-audit, Bandit,
  and churn completed successfully. Pip-audit reported no known
  vulnerabilities and Bandit reported no findings.
- **Status:** passed

### E-060-FUNCTIONALITY-002 - User-reported enhanced export stall

- **Timestamp:** 2026-08-24T13:23:00+02:00
- **Category:** userValidation
- **Requirement:** Given an enhanced export is running, the editor should
  expose ongoing interpolation progress and complete the selected export
  route without appearing permanently idle.
- **Steps:** The user started a real enhanced export with the FFmpeg fallback
  and reported that the video did not really export and remained stuck at the
  initial interpolation progress state.
- **Expected:** The progress panel should advance beyond the initial
  interpolation event and the export should either complete or surface an
  explicit failure/cancellation state.
- **Observed:** The panel remained at an initial frame-0 interpolation update.
  A corresponding FFmpeg process was active and consuming CPU, but no
  interpolation progress callback reached the UI.
- **Status:** failed
- **Failure:** The interpolation backend dropped the export progress callback.

### E-060-BASELINE-002 - Protected baseline before progress correction

- **Timestamp:** 2026-08-24T13:24:00+02:00
- **Category:** baseline
- **Commands:** `make check PYTHON=.venv/bin/python`; `make contract
  PYTHON=.venv/bin/python`; `make smoke PYTHON=.venv/bin/python`
- **Expected:** Protected repository, CLI contract, and generated-media
  flows pass before the corrective implementation.
- **Observed:** 245 repository tests passed with compilation and diff checks;
  29 CLI contract tests passed; and generated-media smoke completed.
- **Status:** passed

### E-060-REGRESSION-004 - Interpolation progress regressions before fix

- **Timestamp:** 2026-08-24T13:26:00+02:00
- **Category:** regression
- **Command:** `.venv/bin/python -m unittest
  tests.test_interpolation.EditorInterpolationTests.test_ffmpeg_interpolation_forwards_progress_callback
  tests.test_editor_export_execution.EditorExportExecutionTests.test_explicit_ffmpeg_interpolation_route_is_verified_end_to_end`
- **Expected:** The interpolation callback reaches FFmpeg and generated
  enhanced exports emit nonzero interpolation frame/FPS progress.
- **Observed:** The low-level regression failed because `run_ffmpeg` received
  no `progress_callback`; the generated-media regression found no nonzero
  interpolation frame progress.
- **Status:** passedWithConcerns
- **Failure:** The failures reproduced the reported callback-plumbing defect.

### E-060-IMPLEMENTATION-002 - Thread interpolation progress to FFmpeg

- **Timestamp:** 2026-08-24T13:28:00+02:00
- **Category:** implementation
- **Requirement:** Interpolation progress emitted by FFmpeg must reach the
  export worker with the existing stage, elapsed-time, FPS, frame, and ETA
  fields.
- **Observed:** Added explicit progress parameters through
  `run_source_interpolation()`, `_run_interpolation_backend()`, and
  `_interpolate_probe()`. Enhanced exports now map local interpolation
  progress into the existing `interpolation N/M` stage range while preserving
  cancellation, artifact validation, verification, cleanup, and atomic
  publication.
- **Status:** passed
- **Source references:** `framestudio/interpolation.py`,
  `framestudio/export_interpolation.py`,
  `tests/test_editor_interpolation.py`,
  `tests/test_editor_export_execution.py`

### E-060-REGRESSION-005 - Corrected interpolation progress and media export

- **Timestamp:** 2026-08-24T13:30:00+02:00
- **Category:** regression
- **Commands:** `.venv/bin/python -m unittest
  tests.test_editor_interpolation tests.test_editor_export_execution`; a
  generated 320x180, 10-FPS, 2-second source exported at 60 FPS through the
  enhanced route with a progress callback.
- **Expected:** Focused interpolation/export tests pass; the generated export
  completes; interpolation events report advancing frames and FPS values.
- **Observed:** 18 focused tests passed. The generated export completed in
  approximately 3 seconds and emitted interpolation events beyond frame 0
  before verified publication.
- **Status:** passed

### E-060-GATE-003 - Protected gates after progress correction

- **Timestamp:** 2026-08-24T13:32:00+02:00
- **Category:** gate
- **Commands:** `make check PYTHON=.venv/bin/python`; `make contract
  PYTHON=.venv/bin/python`; `make smoke PYTHON=.venv/bin/python`
- **Expected:** Protected repository, CLI contract, and generated-media
  flows remain terminal after the correction.
- **Observed:** 246 repository tests passed with compilation and diff checks;
  29 CLI contract tests passed; and generated-media smoke completed.
- **Status:** passed

### E-060-QUALITY-003 - Configured quality suite after progress correction

- **Timestamp:** 2026-08-24T13:32:30+02:00
- **Category:** staticAnalysis
- **Command:** `make quality PYTHON=.venv/bin/python`
- **Expected:** Repository-configured format, lint, type, complexity,
  duplication, dependency, security, test, and churn checks pass.
- **Observed:** 246 tests passed; Ruff format/lint, mypy, complexity,
  dependency checks, pip-audit, Bandit, jscpd, and churn completed. Pip-audit
  reported no known vulnerabilities and Bandit reported no findings.
- **Status:** passed
- **Artifacts:** `evidence/static-analysis/jscpd-report.json`,
  `evidence/static-analysis/pip-audit.json`,
  `evidence/static-analysis/bandit.json`,
  `evidence/static-analysis/dependencies.json`,
  `evidence/static-analysis/churn.json`

### E-060-REVIEW-002 - Progress correction review readiness

- **Timestamp:** 2026-08-24T13:34:00+02:00
- **Category:** review
- **Expected:** The corrected export flow has terminal technical evidence,
  local-to-PR parity, and required user-validation evidence.
- **Observed:** The focused regression, protected gates, configured quality
  suite, source-safety behavior, and generated-media export are terminal. The
  local quality command and scope match the configured pull-request workflow,
  but no remote check has run and the target-workstation/user validation has
  not yet been repeated after the fix. The CPU FFmpeg fallback remains
  materially slower for a user-sized 1080p cut export than the generated
  fixture.
- **Status:** passedWithConcerns
- **Blockers:** Required user validation and remote checks remain pending.
- **Accepted warning:** The current FFmpeg motion-compensated fallback can take
  several minutes for long 1080p ranges when the preferred RVE environment is
  unavailable; the correction makes that work visible but does not change the
  interpolation algorithm.

### E-060-FUNCTIONALITY-004 - User-sized cut export after progress correction

- **Timestamp:** 2026-08-24T13:41:00+02:00
- **Category:** functionality
- **Steps:** Generated a 1920x1080, 30-FPS, 5-second source with stereo AAC,
  split at 4 seconds, deleted the trailing segment, and exported the retained
  cut at 60 FPS through the FFmpeg interpolation fallback with a progress
  callback.
- **Expected:** The cut export completes through the enhanced route, emits
  interpolation progress beyond frame 0, verifies and publishes the output,
  and leaves the source unchanged.
- **Observed:** The export completed in approximately 77 seconds, emitted
  273 interpolation events including advancing frame/FPS updates, published a
  1920x1080 60-FPS 4-second MP4, and preserved the source bytes.
- **Status:** passedWithConcerns
- **Accepted warning:** This workstation measured the CPU motion-compensated
  fallback at roughly 15 seconds per source second for this 1080p workload,
  so a one-minute export can still take many minutes even though progress is
  now visible.

### E-060-QUALITY-004 - Final configured quality suite

- **Timestamp:** 2026-08-24T13:36:00+02:00
- **Category:** staticAnalysis
- **Command:** `make quality PYTHON=.venv/bin/python`
- **Expected:** The final source and regression changes pass all configured
  local quality checks.
- **Observed:** 246 tests passed; compilation, diff checks, Ruff format/lint,
  mypy, complexity, duplication, dependency checks, pip-audit, Bandit, and
  churn completed successfully. Pip-audit reported no known vulnerabilities
  and Bandit reported no findings.
- **Status:** passed
- **Artifacts:** `evidence/static-analysis/jscpd-report.json`,
  `evidence/static-analysis/pip-audit.json`,
  `evidence/static-analysis/bandit.json`,
  `evidence/static-analysis/dependencies.json`,
  `evidence/static-analysis/churn.json`

### E-060-GATE-004 - Final contract and smoke gates

- **Timestamp:** 2026-08-24T13:38:00+02:00
- **Category:** gate
- **Commands:** `make contract PYTHON=.venv/bin/python`; `make smoke
  PYTHON=.venv/bin/python`
- **Expected:** Final CLI contracts and generated-media smoke flows pass.
- **Observed:** 29 CLI contract tests passed and generated-media smoke
  completed successfully.
- **Status:** passed

### E-060-REVIEW-003 - Final review result

- **Timestamp:** 2026-08-24T13:39:00+02:00
- **Category:** review
- **Expected:** Review identifies whether the scoped correction is technically
  ready for delivery and records any remaining required gates.
- **Observed:** The callback is now preserved through the FFmpeg interpolation
  path; focused and generated-media regressions pass; the user-sized cut
  flow completes with live interpolation updates; protected checks, CLI
  contracts, smoke, and configured quality are terminal; no introduced
  static-analysis findings were reported. The configured PR workflow runs the
  same `make quality PYTHON=.venv/bin/python` command, but no remote check or
  post-fix human GTK validation has run, and no remote/upstream is configured.
- **Status:** passedWithConcerns
- **Blockers:** Required user validation and remote checks are still pending;
  TICKET-060 must remain `verifying` and must not be committed or closed.
- **Accepted warning:** The CPU FFmpeg fallback remains slow for long 1080p
  ranges when RVE is unavailable; this fix makes its progress visible without
  changing the approved interpolation algorithm.

### E-060-BASELINE-005 - Smart-render correction baseline

- **Timestamp:** 2026-08-24T14:00:00+02:00
- **Category:** baseline
- **Commands:** `make test PYTHON=.venv/bin/python`; `make smoke
  PYTHON=.venv/bin/python`
- **Expected:** Protected unit and generated-media flows pass before the
  concat-first correction is implemented.
- **Observed:** 246 tests passed and the generated-media smoke flow completed
  successfully. The existing enhanced path still performs interpolation before
  source preparation and the requested staged master does not yet exist.
- **Status:** passed

### E-060-REGRESSION-006 - Concat-first enhanced master

- **Timestamp:** 2026-08-24T14:02:00+02:00
- **Category:** regression
- **Expected:** Smart-render command builders and enhanced orchestration should
  cut retained ranges losslessly, apply one source-level audio decision,
  concatenate prepared media at the slowest input FPS, and invoke interpolation
  exactly once on the unified master.
- **Observed:** The new regression module could not import the not-yet-created
  `framestudio.export_smart_render` surface. This is the expected failing
  regression before implementation.
- **Status:** failed-before-fix
- **Failure:** `ModuleNotFoundError: No module named
  'framestudio.export_smart_render'`

### E-060-IMPLEMENTATION-003 - Concat-first smart-render staging

- **Timestamp:** 2026-08-24
- **Category:** implementation
- **Requirement:** Enhanced edits with cuts or multiple sources should prepare
  retained ranges before one unified interpolation pass.
- **Observed:** Added smart-render staging that probes keyframes, uses
  stream-copy cuts when boundaries are safe, normalizes each source once at
  the slowest selected input FPS with its persisted source-level audio
  decision, concatenates prepared sources with stream copy, and sends one
  prepared master to interpolation. Non-keyframe boundaries retain the
  decoded safe route.
- **Status:** passed
- **Source references:** `framestudio/export_smart_render.py`,
  `framestudio/export_interpolation.py`,
  `tests/test_editor_smart_render.py`,
  `tests/test_editor_export_execution.py`

### E-060-REGRESSION-007 - Smart-render focused regressions

- **Timestamp:** 2026-08-24
- **Category:** regression
- **Command:** `.venv/bin/python -m unittest
  tests.test_editor_smart_render`
- **Expected:** Smart-render command construction and enhanced orchestration
  cover lossless cuts, source-level gain, concat-demuxer joining, one-master
  interpolation, and incompatible single-source routing.
- **Observed:** 5 focused tests passed.
- **Status:** passed

### E-060-FUNCTIONALITY-005 - Generated mixed-source enhanced delivery

- **Timestamp:** 2026-08-24
- **Category:** functionality
- **Steps:** Generated 10-FPS and 20-FPS sources with different dimensions,
  selected retained ranges, assigned distinct source-level audio gains, and
  exported the mixed edit at 20 FPS through the FFmpeg fallback.
- **Expected:** Sources are normalized before concatenation, one interpolation
  stage receives the prepared master, output metadata matches the target
  policy, progress is monotonic, and source bytes remain unchanged.
- **Observed:** The export completed with a 1920x1080, 20-FPS, 1-second MP4
  containing 48 kHz stereo AAC. Progress included one
  `concatenating prepared sources` stage and one `interpolation master` stage,
  and source preservation checks passed.
- **Status:** passed

### E-060-QUALITY-005 - Final configured quality suite after lint remediation

- **Timestamp:** 2026-08-24
- **Category:** staticAnalysis
- **Command:** `make quality PYTHON=.venv/bin/python`
- **Expected:** All configured tests, compilation, formatting, lint, type,
  complexity, duplication, dependency, security, and churn checks pass.
- **Observed:** 252 tests passed; compilation, `git diff --check`, Ruff
  format/lint, mypy, complexity, jscpd, dependency checks, pip-audit, Bandit,
  and churn completed successfully. Ruff reported no findings, pip-audit
  reported no known vulnerabilities, and Bandit reported no findings.
- **Status:** passed
- **Artifacts:** `evidence/static-analysis/jscpd-report.json`,
  `evidence/static-analysis/pip-audit.json`,
  `evidence/static-analysis/bandit.json`,
  `evidence/static-analysis/dependencies.json`,
  `evidence/static-analysis/churn.json`

### E-060-GATE-005 - Final contract and smoke gates

- **Timestamp:** 2026-08-24T14:34:00+02:00
- **Category:** gate
- **Commands:** `make contract PYTHON=.venv/bin/python`; `make smoke
  PYTHON=.venv/bin/python`
- **Expected:** The CLI contract and generated-media smoke flows pass after
  the smart-render correction.
- **Observed:** 29 CLI contract tests passed and generated-media smoke
  completed successfully.
- **Status:** passed

### E-060-REVIEW-004 - Smart-render correction review result

- **Timestamp:** 2026-08-24T14:35:00+02:00
- **Category:** review
- **Expected:** The final diff, planning chain, static analysis, protected
  behavior, functionality evidence, and delivery gates support a readiness
  decision.
- **Observed:** The active ticket remains linked to
  `OBJ-001 -> SCOPE-001 -> PHASE-007 -> FEAT-021`. The configured local
  quality command matches the pull-request workflow command and scope;
  current churn output did not rank changed production files as hotspots; no
  introduced static-analysis findings remain; generated-media and user-sized
  enhanced exports complete through concat-first preparation; and source,
  cancellation, verification, and atomic publication boundaries remain
  covered. No Git remote or configured upstream is available, so required
  remote checks cannot run. Post-correction human GTK validation and the
  required user-validation response are also pending.
- **Status:** passedWithConcerns
- **Blockers:** Remote checks and required user validation are unavailable;
  TICKET-060 must remain `verifying` and must not be committed or closed.
- **Accepted warnings:** The CPU FFmpeg motion-compensated fallback remains
  materially slower than stream-copy work for long 1080p ranges when RVE is
  unavailable. This correction changes staging and progress visibility, not
  the approved interpolation algorithm. A timed old-versus-new 1080p
  comparison is not available in this worktree.

### E-060-FIX-REPRO-001 - Direct FPS command blocks without optional RVE runtime

- **Timestamp:** 2026-08-25T20:40:50+02:00
- **Category:** regression
- **Requirement:** Given the preferred RVE runtime is unavailable, the direct
  FPS command should select the validated FFmpeg fallback and continue without
  changing the source.
- **Command:** Generate a disposable 10-FPS fixture and run
  `python3 framestudio_fps.py <fixture> --output <output> --performance-mode off`.
- **Expected:** The command selects a usable fallback or reports a clear
  fallback-specific blocker; it must not fail solely because the preferred RVE
  environment is absent.
- **Observed:** The command exited with status 1 before processing and printed
  `RVE Python environment was not found`.
- **Status:** failed
- **Failure:** `framestudio_fps.py` always dispatches the default `rve` engine
  directly and has no legacy-command FFmpeg fallback.

### E-060-FIX-BASELINE-001 - Protected checks before the corrective regression

- **Timestamp:** 2026-08-25T20:40:50+02:00
- **Category:** baseline
- **Commands:** `make check`; `make contract`; `make smoke`;
  `make quality PYTHON=.venv/bin/python`
- **Expected:** Existing tests, compilation, CLI contracts, generated-media
  smoke flows, static analysis, dependency checks, security checks, and churn
  complete before the fix.
- **Observed:** `make check` passed 252 tests, compilation, and
  `git diff --check`; `make contract` passed 29 tests; `make smoke`
  completed successfully; and the configured quality suite passed formatting,
  lint, mypy, complexity, duplication, dependency, pip-audit, Bandit, and
  churn checks.
- **Status:** passed
- **Artifacts:** `evidence/static-analysis/jscpd-report.json`,
  `evidence/static-analysis/pip-audit.json`,
  `evidence/static-analysis/bandit.json`,
  `evidence/static-analysis/dependencies.json`,
  `evidence/static-analysis/churn.json`

### E-060-FIX-REGRESSION-003 - Final fallback regression coverage

- **Timestamp:** 2026-08-25T20:54:27+02:00
- **Category:** regression
- **Commands:** `python3 -m unittest
  tests.test_fps.FpsTests.test_ffmpeg_fallback_engine_is_selectable
  tests.test_fps.FpsTests.test_missing_rve_uses_ffmpeg_fallback`;
  `python3 -m unittest tests.test_fps`
- **Expected:** The explicit fallback engine is accepted, and a missing RVE
  runtime selects it without changing source media while preserving target
  rate, frame count, and audio.
- **Observed:** The focused checks and all 10 FPS tests passed. The generated
  fallback fixture retained its source bytes, produced the rational target
  rate and exact frame count, and retained AAC audio.
- **Status:** passed

### E-060-FIX-FUNCTIONALITY-001 - Final real legacy-command fallback flow

- **Timestamp:** 2026-08-25T20:54:27+02:00
- **Category:** functionality
- **Command:** Generated a disposable 10-FPS, 0.5-second source with AAC
  audio and ran `python3 framestudio_fps.py <source> --output <output>
  --encoder libx264 --performance-mode off`.
- **Expected:** The missing RVE environment is reported, the FFmpeg fallback
  completes at 60 FPS, source media is unchanged, and partial output is
  cleaned up.
- **Observed:** The command selected the FFmpeg minterpolate fallback and
  completed. `ffprobe` reported H.264 video at `60/1` with 30 frames, AAC
  audio, and 0.5 seconds; the source hash was unchanged and no partial file
  remained.
- **Status:** passed

### E-060-FIX-GATE-002 - Final protected, contract, and smoke gates

- **Timestamp:** 2026-08-25T20:55:59+02:00
- **Category:** gate
- **Commands:** `make check`; `make contract`; `make smoke`
- **Expected:** Protected tests, compilation, diff checks, CLI contracts, and
  generated-media smoke flows remain green after the final correction.
- **Observed:** 254 repository tests passed; 29 CLI contract tests passed;
  generated-media smoke completed successfully; Python compilation and
  `git diff --check` passed.
- **Status:** passed

### E-060-FIX-QUALITY-002 - Final configured quality suite

- **Timestamp:** 2026-08-25T20:55:59+02:00
- **Category:** staticAnalysis
- **Command:** `make quality PYTHON=.venv/bin/python`
- **Expected:** The configured formatter, lint, type, complexity, duplication,
  dependency, security, test, and churn checks pass.
- **Observed:** 254 tests passed; Ruff format/lint, mypy, complexity, jscpd,
  dependency checks, pip-audit, Bandit, and churn completed successfully.
  Pip-audit reported no known vulnerabilities and Bandit reported no findings.
- **Status:** passed
- **Artifacts:** `evidence/static-analysis/jscpd-report.json`,
  `evidence/static-analysis/pip-audit.json`,
  `evidence/static-analysis/bandit.json`,
  `evidence/static-analysis/dependencies.json`,
  `evidence/static-analysis/churn.json`

### E-060-FIX-REVIEW-001 - Final fallback correction review

- **Timestamp:** 2026-08-25T20:55:59+02:00
- **Category:** review
- **Expected:** The corrective scope is technically reviewed against the
  active ticket, protected behavior, configured analysis, and delivery gates.
- **Observed:** `framestudio_fps.py` keeps RVE as the preferred backend, selects
  the validated FFmpeg fallback when RVE prerequisites are absent, and
  preserves atomic output, cleanup, source safety, audio copying, and exact
  frame limits. `framestudio_concat.py` accepts the explicit fallback engine.
  The local quality command and `.github/workflows/quality.yml` use the same
  `make quality PYTHON=.venv/bin/python` workflow. No Git remote or upstream
  is configured, so remote checks cannot run.
- **Status:** passedWithConcerns
- **Blockers:** Required human user validation and remote checks remain
  unavailable. TICKET-060 must remain `verifying` and must not be committed
  or closed.
- **Accepted warning:** The fallback uses the existing validated FFmpeg
  `libx264` profile rather than the legacy RVE/NVENC encoder option, and can
  be materially slower than RVE on long 1080p media. It is an explicit
  reliability fallback, not a claim of RVE-equivalent quality or speed.

### E-060-FIX-IMPLEMENTATION-002 - Blackwell-compatible RVE runtime validation

- **Timestamp:** 2026-08-25T21:27:39+02:00
- **Category:** implementation
- **Requirement:** Given the preferred RVE backend is selected on the RTX
  5070 Ti, the runtime should execute real CUDA kernels and load the corrected
  TensorRT profile instead of treating CUDA availability alone as readiness.
- **Observed:** RVE preflight now runs and synchronizes a CUDA tensor probe,
  reports the detected GPU/capability, and prepends the CUDA 13, TensorRT, and
  CUDA runtime library directories before importing the RVE subprocess. The
  active runtime uses PyTorch 2.10.0+cu128, Torch-TensorRT 2.10.0, and
  TensorRT 10.14.1.48.post1 with RIFE 4.26 and the selective
  `aten.pixel_shuffle` PyTorch fallback.
- **Status:** passed
- **Source references:** `framestudio_fps.py`, `tests/test_fps.py`,
  `FPS-ENHANCEMENT-RESEARCH.md`, `tools/rve-corrected-profile.patch`

### E-060-FUNCTIONALITY-006 - Corrected RVE one-minute 1080p benchmark

- **Timestamp:** 2026-08-25T21:27:39+02:00
- **Category:** functionality
- **Source:** `/home/ghiki/Videos/editor-test-1m.mp4`
- **Expected:** The real RVE/TensorRT path should produce clean 60-FPS output
  at or above the approximately 109.1 effective output-FPS reference while
  preserving duration, audio, dimensions, and source safety.
- **Observed:** With warm TensorRT engines, the corrected RVE run completed in
  32.341 seconds, reported 122.74 end-to-end output FPS, and measured 111.31
  effective output FPS including preflight and startup. Peak GPU utilization
  was 81%, peak board power was 210.32 W, and peak VRAM was 3,482 MiB. The
  result contained exactly 3,600 frames at 60 FPS, preserved 48 kHz AAC audio,
  retained 1920x1080 BT.709 limited-range metadata, and left the source
  unchanged.
- **Status:** passed
- **Reference:** `FPS-ENHANCEMENT-RESEARCH.md`

### E-060-FIX-REGRESSION-004 - Environment-independent export collision test

- **Timestamp:** 2026-08-25T21:27:39+02:00
- **Category:** regression
- **Command:** `python3 -m unittest tests.test_editor_export_panel`
- **Expected:** The collision-name regression should exercise the validated
  FFmpeg fallback deterministically regardless of whether the local RVE cache
  happens to be installed.
- **Observed:** The test now supplies one shared mocked backend-validation
  helper that marks RVE unavailable and FFmpeg available. All 7 export-panel
  tests passed, including the expected `-1` collision suffix and fallback
  notice behavior.
- **Status:** passed
- **Source references:** `tests/test_editor_export_panel.py`

### E-060-FIX-QUALITY-003 - Duplication-gate remediation and final quality

- **Timestamp:** 2026-08-25T21:27:39+02:00
- **Category:** staticAnalysis
- **Commands:** `make quality PYTHON=.venv/bin/python`
- **Expected:** The configured quality suite should pass after the final
  test-environment correction.
- **Observed:** The first post-test-change run exposed a 2.1% jscpd result,
  above the configured 2.0% threshold, due to repeated mocked validation
  helpers in the export-panel tests. The helper was consolidated, after which
  the full suite passed: 256 tests, compilation, diff checks, Ruff format/lint,
  mypy, complexity, jscpd, dependency checks, pip-audit, Bandit, and churn.
  Pip-audit reported no known vulnerabilities and Bandit reported no findings.
- **Status:** passed
- **Artifacts:** `evidence/static-analysis/jscpd-report.json`,
  `evidence/static-analysis/pip-audit.json`,
  `evidence/static-analysis/bandit.json`,
  `evidence/static-analysis/dependencies.json`,
  `evidence/static-analysis/churn.json`

### E-060-FIX-GATE-003 - Final protected, contract, smoke, and quality gates

- **Timestamp:** 2026-08-25T21:27:39+02:00
- **Category:** gate
- **Commands:** `make check PYTHON=.venv/bin/python`; `make contract
  PYTHON=.venv/bin/python`; `make smoke PYTHON=.venv/bin/python`; `make
  quality PYTHON=.venv/bin/python`
- **Expected:** All configured local protected, contract, integration, and
  quality gates remain green after the final corrective changes.
- **Observed:** `make check` and the quality suite each passed 256 tests with
  compilation and `git diff --check`; 29 CLI contract tests passed; generated
  media smoke completed successfully; and all configured static-analysis,
  dependency, security, and churn checks passed.
- **Status:** passed

### E-060-FIX-REVIEW-002 - Final local readiness review

- **Timestamp:** 2026-08-25T21:27:39+02:00
- **Category:** review
- **Expected:** The final scoped changes should have terminal local evidence
  without weakening the preferred RVE path or protected export behavior.
- **Observed:** RVE remains the preferred backend when its corrected runtime
  validates; missing-RVE direct and unified workflows retain the FFmpeg
  fallback; source preservation, exact frame limits, audio handling, cleanup,
  verification, and atomic publication remain covered. The environment-
  independent collision regression and all configured local gates are green.
  No Git remote or upstream is configured, so remote checks cannot run, and
  the required human user-validation response remains pending.
- **Status:** passedWithConcerns
- **Blockers:** User validation and remote checks remain unavailable.
  TICKET-060 must remain `verifying` and must not be committed or closed.

### E-060-FIX-BASELINE-003 - Frame-count correction protected baseline

- **Timestamp:** 2026-08-25T21:55:48+02:00
- **Category:** baseline
- **Command:** `make check`
- **Expected:** Protected tests, compilation, and diff checks pass before the
  frame-count correction.
- **Observed:** 256 tests passed; Python compilation and `git diff --check`
  passed.
- **Status:** passed

### E-060-FIX-REGRESSION-005 - Mixed export frame-count mismatch

- **Timestamp:** 2026-08-25T21:55:48+02:00
- **Category:** regression
- **Command:** `.venv/bin/python -m unittest tests.test_editor_smart_render`
- **Expected:** Cumulative segment allocation should retain the rounded
  source timeline count, and concat-first interpolation should receive the
  globally rounded target frame count.
- **Observed:** Before the implementation, the focused suite reported one
  failure for the second cumulative segment count and one error because the
  interpolation call omitted the required global target-frame argument.
- **Status:** failed-before-fix
- **Failure:** Independent segment rounding produced 26 frames instead of the
  cumulative 27-frame allocation, and the mixed project path attempted 668
  frames where the edited duration requires 671.

### E-060-FIX-IMPLEMENTATION-003 - Exact concat-first frame targeting

- **Timestamp:** 2026-08-25T21:55:48+02:00
- **Category:** implementation
- **Requirement:** Given an enhanced cut or mixed-source edit, the prepared
  master and final interpolation should preserve the edited duration's
  globally rounded target frame count.
- **Observed:** Source normalization now allocates integer segment frames from
  cumulative boundaries, avoiding frame loss from independent rounding.
  Concat-first interpolation now receives the export plan's global target
  frame count, while direct and legacy interpolation retain their existing
  source-derived behavior and validation.
- **Status:** passed
- **Source references:** `framestudio/export_smart_render.py`,
  `framestudio/export_interpolation.py`,
  `tests/test_editor_smart_render.py`

### E-060-FIX-REGRESSION-006 - Frame-count correction focused verification

- **Timestamp:** 2026-08-25T21:55:48+02:00
- **Category:** regression
- **Commands:** `.venv/bin/python -m unittest tests.test_editor_smart_render`;
  `.venv/bin/python -m unittest tests.test_editor_export_execution`
- **Expected:** The new frame-allocation and global-target regressions pass
  without breaking enhanced, ordinary, cancellation, source-safety, or
  progress behavior.
- **Observed:** 6 smart-render tests and 10 export-execution tests passed.
- **Status:** passed

### E-060-FIX-FUNCTIONALITY-002 - User project FFmpeg fallback export

- **Timestamp:** 2026-08-25T21:55:48+02:00
- **Category:** functionality
- **Requirement:** Given the reported mixed project with cuts, transforms,
  and two 30-FPS sources, enhanced export should complete through the
  concat-first path and pass frame-count verification.
- **Observed:** The project completed through the validated FFmpeg fallback
  with 671 frames at 60 FPS, 11.183333 seconds, 1920x1080 video, and AAC
  48 kHz stereo audio. Progress reached `671/671`, and verified publication
  completed.
- **Status:** passed

### E-060-FIX-FUNCTIONALITY-003 - User project preferred RVE export

- **Timestamp:** 2026-08-25T21:55:48+02:00
- **Category:** functionality
- **Requirement:** Given the preferred validated RVE backend, the same
  mixed-source edit should accept the corrected target count and publish a
  verified output.
- **Observed:** The RVE export completed with 671 frames at 60 FPS,
  11.201333 seconds, 1920x1080 video, and AAC 48 kHz stereo audio.
  The RVE progress reached `671/671` and the mixed-output verifier passed.
- **Status:** passed

### E-060-FIX-GATE-004 - Final protected and contract gates

- **Timestamp:** 2026-08-25T21:55:48+02:00
- **Category:** gate
- **Commands:** `make check`; `make contract`; `make smoke`
- **Expected:** Protected tests, compilation, diff checks, CLI contracts,
  and generated-media smoke remain green after the correction.
- **Observed:** `make check` passed 257 tests with compilation and
  `git diff --check`; 29 CLI contract tests passed; and generated-media
  smoke completed successfully.
- **Status:** passed

### E-060-FIX-QUALITY-004 - Final configured quality suite

- **Timestamp:** 2026-08-25T21:55:48+02:00
- **Category:** staticAnalysis
- **Command:** `make quality PYTHON=.venv/bin/python`
- **Expected:** The repository-configured formatter, lint, type, complexity,
  duplication, dependency, security, test, and churn checks pass.
- **Observed:** 257 tests passed; Ruff format/lint, mypy, complexity, jscpd,
  dependency checks, pip-audit, Bandit, and churn completed successfully.
  Pip-audit reported no known vulnerabilities and Bandit reported no
  findings. The local command matches `.github/workflows/quality.yml`.
- **Status:** passed
- **Artifacts:** `evidence/static-analysis/jscpd-report.json`,
  `evidence/static-analysis/pip-audit.json`,
  `evidence/static-analysis/bandit.json`,
  `evidence/static-analysis/dependencies.json`,
  `evidence/static-analysis/churn.json`

### E-060-FIX-REVIEW-003 - Final frame-count correction review

- **Timestamp:** 2026-08-25T21:55:48+02:00
- **Category:** review
- **Expected:** The scoped correction should satisfy the active ticket's
  exact-frame-count requirement without weakening smart-render, output
  verification, or delivery safety.
- **Observed:** The red regression is green; both FFmpeg and preferred RVE
  real-media exports of the reported mixed project verify at 671 frames;
  protected, contract, smoke, and quality gates are terminal; the changed
  modules remain within TICKET-060's approved export scope; and current
  churn output did not rank the changed production files as hotspots. No
  configured Git remote or upstream is present, so remote checks cannot run.
- **Status:** passedWithConcerns
- **Blockers:** Required human user validation and remote checks remain
  pending. TICKET-060 must remain `verifying` and must not be committed or
  closed.

### E-060-FIX-BASELINE-004 - Performance-mode protected baseline

- **Timestamp:** 2026-08-25T22:05:04+02:00
- **Category:** baseline
- **Command:** `make check`
- **Expected:** Protected tests, compilation, and diff checks pass before
  changing the editor export lifecycle.
- **Observed:** 257 tests passed; Python compilation and `git diff --check`
  passed.
- **Status:** passed

### E-060-FIX-REGRESSION-007 - Export performance scope is missing

- **Timestamp:** 2026-08-25T22:05:04+02:00
- **Category:** regression
- **Command:** `python3 -m unittest tests.test_editor_performance`
- **Expected:** The editor export job should enter a temporary performance
  scope and restore it after success, failure, and cancellation.
- **Observed:** The new regression could not import the not-yet-existing
  `run_export_job` integration surface.
- **Status:** failed-before-fix
- **Failure:** `ImportError: cannot import name 'run_export_job' from
  framestudio.app_export`.

### E-060-FIX-IMPLEMENTATION-004 - Temporary editor export performance mode

- **Timestamp:** 2026-08-25T22:05:04+02:00
- **Category:** implementation
- **Requirement:** When an editor export starts, select the system
  performance profile for the worker lifetime and restore the captured
  profile on every terminal path.
- **Observed:** Added the shared `framestudio.performance` helper,
  retained the legacy scripts' public `PerformanceMode` import behavior,
  wrapped editor planning and execution in `run_export_job`, and routed
  profile errors through the existing GTK completion/error path. If
  `powerprofilesctl` is unavailable, the export continues without claiming
  that a profile change occurred.
- **Status:** passed
- **Source references:** `framestudio/performance.py`,
  `framestudio/app_export.py`, `framestudio_concat.py`,
  `tests/test_editor_performance.py`

### E-060-FIX-REGRESSION-008 - Performance restoration focused verification

- **Timestamp:** 2026-08-25T22:05:04+02:00
- **Category:** regression
- **Commands:** `python3 -m unittest tests.test_editor_performance
  tests.test_editor_export_execution tests.test_editor_export_panel
  tests.test_fps`
- **Expected:** The editor job restores mode on success, error, and
  cancellation; the shared helper restores a previous profile; and existing
  editor/legacy export behavior remains green.
- **Observed:** 32 tests passed. Mocked profile transitions restored
  `balanced` after both normal and exceptional exits, and the editor job
  exited its performance scope for all three terminal outcomes.
- **Status:** passed

### E-060-FIX-QUALITY-005 - Initial quality remediation

- **Timestamp:** 2026-08-25T22:05:04+02:00
- **Category:** staticAnalysis
- **Command:** `make quality PYTHON=.venv/bin/python`
- **Expected:** The configured quality suite passes after the implementation.
- **Observed:** The first run reported Ruff formatting for the new test and
  then, after formatting, import-order and closure-capture lint findings.
  The test was formatted and the test helper was moved to a factory that
  binds its event log without loop capture.
- **Status:** failed
- **Failure:** Ruff format-check and lint findings in
  `tests/test_editor_performance.py` and import ordering in
  `framestudio/app_export.py`.
- **Fix:** Applied the repository Ruff formatter and made the focused lint
  corrections.

### E-060-FIX-GATE-005 - Final performance-mode local gates

- **Timestamp:** 2026-08-25T22:05:04+02:00
- **Category:** gate
- **Commands:** `make check`; `make contract`; `make smoke`
- **Expected:** Protected tests, compilation, diff checks, CLI contracts, and
  generated-media smoke remain green after the export lifecycle change.
- **Observed:** `make check` passed 260 tests with compilation and
  `git diff --check`; 29 CLI contract tests passed; and generated-media
  smoke completed successfully.
- **Status:** passed

### E-060-FIX-QUALITY-006 - Final configured quality suite

- **Timestamp:** 2026-08-25T22:05:04+02:00
- **Category:** staticAnalysis
- **Command:** `make quality PYTHON=.venv/bin/python`
- **Expected:** The configured formatter, lint, type, complexity, duplication,
  dependency, security, test, and churn checks pass.
- **Observed:** 260 tests passed; Ruff formatting/lint, mypy, complexity,
  jscpd, repository dependency analysis, pip-audit, Bandit, and churn
  completed successfully. Pip-audit reported no known vulnerabilities and
  Bandit reported no findings. The local command matches
  `.github/workflows/quality.yml`.
- **Status:** passed
- **Artifacts:** `evidence/static-analysis/jscpd-report.json`,
  `evidence/static-analysis/pip-audit.json`,
  `evidence/static-analysis/bandit.json`,
  `evidence/static-analysis/dependencies.json`,
  `evidence/static-analysis/churn.json`

### E-060-FIX-REVIEW-004 - Performance-mode export review

- **Timestamp:** 2026-08-25T22:05:04+02:00
- **Category:** review
- **Expected:** The scoped export lifecycle change should preserve existing
  delivery behavior while restoring the prior system profile on every
  terminal export outcome.
- **Observed:** The shared profile helper has no dependency-cycle finding,
  the configured quality suite is green, and focused tests cover successful,
  failed, and cancelled editor jobs plus actual profile command sequencing.
  The configured CI workflow invokes the same quality command. The current
  environment has `powerprofilesctl` available and is already in
  `performance`; no Git remote or upstream is configured.
- **Status:** passedWithConcerns
- **Blockers:** Required human GTK/user validation and remote checks remain
  pending. TICKET-060 must remain `verifying` and must not be committed or
  closed.

### E-060-FIX-USER-VALIDATION-001 - Export performance restoration accepted

- **Timestamp:** 2026-08-25T22:07:06.861+02:00
- **Category:** userValidation
- **Requirement:** Given an editor export starts, the system performance
  profile should be used for the export and the previous profile should be
  restored after completion, failure, or cancellation.
- **Steps:** User exercised the corrected editor export flow after the
  performance-mode change.
- **Expected:** Export completes normally and the requested behavior works
  without leaving the system in the temporary performance profile.
- **Observed:** User response: `works perfect`.
- **Status:** passed
- **Source references:** `framestudio/app_export.py`,
  `framestudio/performance.py`

### E-060-FIX-REVIEW-005 - User-validation gate resolved

- **Timestamp:** 2026-08-25T22:07:06.861+02:00
- **Category:** review
- **Expected:** The user-facing performance-mode requirement has terminal
  validation before delivery closeout.
- **Observed:** Human user validation is terminal with a positive response.
  Local tests, protected gates, CLI contracts, smoke, and configured quality
  are already terminal. No Git remote or upstream is configured, so the
  required remote-check gate remains unavailable.
- **Status:** passedWithConcerns
- **Blockers:** Remote checks remain unavailable. TICKET-060 must remain
  `verifying` and must not be committed or closed until the configured
  remote-check requirement is resolved or explicitly approved.

### E-060-CLOSURE-001 - User acceptance for closure

- **Timestamp:** 2026-08-26
- **Category:** userValidation
- **Requirement/flow:** Confirm the completed export-panel, fallback,
  concat-first smart-render, frame-count, and performance-mode changes are
  accepted after testing.
- **Observed:** User confirmed: “all the tickets are approved and accepted and
  tested, close all done tickets, features and phases.”
- **Status:** passed
- **Accepted warnings:** The historical remote and target-environment
  limitations remain explicit, and the FFmpeg path remains documented as a
  fallback rather than an RVE-equivalent claim.

## Closure disposition

User acceptance is terminal for TICKET-060. The corrective export record is
eligible for closure with the existing fallback and environment warnings
preserved.
