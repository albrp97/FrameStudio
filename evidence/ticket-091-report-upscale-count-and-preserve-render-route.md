# TICKET-091 - Report Upscale Count and Preserve the Render Route

**Ticket:** TICKET-091
**Feature:** FEAT-029
**Phase:** PHASE-008
**Branch:** `ticket/defer-audio-analysis-during-import`
**Base:** `main` at `2702d68`
**Status:** verifying
**Evidence date:** 2026-09-04

## Context and planning chain

The ticket is authorized under the user's request to show how many videos
will be upscaled and to verify that the upscale render path still works.
The planning chain is `OBJ-001 -> SCOPE-001 -> PHASE-008 -> FEAT-029 ->
TICKET-091`. The implementation is limited to source-level count reporting,
responsive planning-panel presentation, and regression coverage for the
existing SuperUltraCompact/RVE route.

## Requirements

- The export panel promptly shows the number of unique eligible source videos
  while asynchronous planning is still running.
- Disabled upscale explicitly reports zero videos to upscale and retains the
  non-upscale route.
- Only eligible sources reach restoration/upscale processing.
- A successful upscale export preserves the fixed delivery profile, expected
  timing, and source bytes.
- Failed or unavailable upscale processing surfaces an error, does not publish
  a substitute output, and retains only the established retry intermediates.

## Entries

### Planning and baseline - 2026-09-04

- **Source:** `docs/planning/tickets/open/TICKET-091-report-upscale-count-and-preserve-render-route.md`
- **Expected:** the ticket has explicit source-level requirements, affected
  surfaces, non-goals, validation, and a user-validation path.
- **Observed:** the ticket is linked to FEAT-029, PHASE-008, OBJ-001,
  SCOPE-001, CAP-005, and CAP-012. It preserves orientation thresholds,
  target dimensions, model selection, safe publication, and source
  preservation as protected behavior.
- **Status:** passed

### Failing regression and implementation - 2026-09-04

- **Expected:** panel state and the pending GTK planning view expose an
  explicit source-level count.
- **Observed before the fix:** the panel exposed an ambiguous
  `Upscale-eligible sources` summary only after expensive planning completed;
  the new pending-display regression initially failed because the reusable
  count helper was not present.
- **Status:** failed
- **Fix:** `framestudio/export_panel.py` now exposes
  `eligible_source_count` and `source_count`, centralizes the policy/display
  calculation in `resolve_upscale_panel_policy()` and
  `upscale_panel_rows()`, and labels the visible row `Videos to upscale`.
  `framestudio/app_export.py` renders those lightweight rows immediately
  before the existing worker performs backend validation and estimates.

### Focused regression coverage - 2026-09-04

- **Command:** `.venv/bin/python -m unittest
  tests.test_editor_export_panel tests.test_editor_export_execution
  tests.test_editor_performance`
- **Expected:** enabled, disabled, mixed-eligibility, zero-eligible, pending
  display, source-selection, and responsive planning behavior pass.
- **Observed:** 38 tests passed.
- **Status:** passed
- **Sources:** `tests/test_editor_export_panel.py`,
  `tests/test_editor_export_execution.py`,
  `tests/test_editor_performance.py`

### Protected repository verification - 2026-09-04

- **Commands:** `make check PYTHON=.venv/bin/python`,
  `make contract PYTHON=.venv/bin/python`, and
  `make smoke PYTHON=.venv/bin/python`.
- **Expected:** existing tests, compilation, diff checks, CLI contracts, and
  generated-media GTK smoke flows remain functional.
- **Observed:** 412 repository tests passed; compilation and diff checks
  passed; 35 CLI contract tests passed; generated-media smoke passed.
- **Status:** passed

### Target-workstation UI functionality - 2026-09-04

- **Environment:** target Linux Wayland workstation with GTK 4/PyGObject,
  FFmpeg/ffprobe, CUDA/TensorRT RVE integration, and a generated 320x180
  source.
- **Steps:** launch the source in the editor, click **Export video**, observe
  the initial planning panel, toggle **Upscale eligible videos
  (SuperUltraCompact)** off and on, and observe the summary while planning
  continues and after it completes.
- **Expected:** the panel remains responsive; the count is visible without
  waiting for backend planning; disabling reports zero; re-enabling restores
  the eligible count.
- **Observed:** the panel immediately displayed `Videos to upscale: 1`.
  With upscale disabled it displayed `Upscale enhancement: Off` and
  `Videos to upscale: 0`; after re-enabling it returned to
  `Upscale enhancement: On`, `SuperUltraCompact`, and
  `Videos to upscale: 1`. The panel remained interactive throughout.
- **Status:** passed
- **Artifacts:**
  - `evidence/screenshots/ticket-091-upscale-count-enabled.png`
  - `evidence/screenshots/ticket-091-upscale-count-disabled.png`
  - `evidence/screenshots/ticket-091-upscale-count-reenabled.png`

### Real RVE upscale functionality - 2026-09-04

- **Setup:** generated a one-second 320x180, 10 FPS H.264/AAC source and a
  versioned FrameStudio project. The local RVE checkout, TensorRT Python
  environment, CUDA device, and `deH264_SuperUltraCompact.safetensors`
  model were available.
- **Command:** `.venv/bin/python framestudio.py export
  <project>/source.framestudio.json --output <project>/upscaled.mp4
  --fps-choice lowest --no-enhance-fps --upscale-enhancement
  --human-progress`
- **Expected:** the validated enhanced route invokes RVE restoration for the
  eligible source, verifies a 1920x1080 output, preserves the source, and
  removes partial/intermediate files only after publication.
- **Observed:** the export completed in approximately five seconds with
  `route: enhanced`, `verified: true`, and the SuperUltraCompact decision
  for the eligible 320x180 source. Output metadata was 1920x1080, 10 FPS,
  10 frames, approximately 1.02 seconds, H.264 video, and AAC audio. The
  source SHA-256 before and after export matched, and no partial or
  intermediate files remained after successful publication. Human progress
  reported preparation, rendering/enhancement, verification, and
  publication stages while machine-readable JSON Lines remained valid.
- **Status:** passed
- **Artifacts:**
  - `evidence/ticket-091-real-rve/export.stderr.log`
  - `evidence/ticket-091-real-rve/export.stdout.jsonl`
  - `evidence/ticket-091-real-rve/output.metadata`
  - `evidence/ticket-091-real-rve/source.sha256.before`
  - `evidence/ticket-091-real-rve/source.sha256.after`

### Failure-path observation - 2026-09-04

- **Setup:** an initial one-second 64x36 fixture was intentionally used to
  exercise the same real route.
- **Expected:** the encoder failure is surfaced, no substitute output is
  published, and the retry intermediates remain available according to the
  established cache policy.
- **Observed:** RVE surfaced the NVENC minimum-frame-dimension error, the
  command returned a non-zero result, no final output was published, and the
  intermediate directory remained for retry. The successful 320x180 rerun
  above then completed and cleaned its intermediates.
- **Status:** passedWithConcerns
- **Accepted warning:** the 64x36 failure is a fixture limitation imposed by
  the local NVENC encoder, not a production-source failure.
- **Artifact:** `evidence/ticket-091-real-rve/invalid-fixture-failure.log`

### Static analysis and review - 2026-09-04

- **Commands:** `make quality PYTHON=.venv/bin/python`,
  `make -k complexity duplication dependency-check dependency-audit security
  churn PYTHON=.venv/bin/python`, and the configured formatter/linter/type
  checks.
- **Expected:** changed surfaces have no introduced formatting, lint, typing,
  duplication, dependency, or security findings; existing debt remains
  visible.
- **Observed:** Ruff formatting and linting passed; mypy passed for all
  configured targets; jscpd reported 0 new clones; dependency boundaries
  reported 0 findings; pip-audit reported no known vulnerabilities; Bandit
  reported no findings; churn completed. The repository-wide complexity
  target remains non-zero because of the pre-existing
  `C901` finding at `benchmarks/restoration_benchmark.py:1794`
  (`run_benchmark`, complexity `16 > 15`), outside this ticket's scope.
- **Status:** passedWithConcerns
- **Accepted warning:** the complexity debt is unchanged and is not an
  introduced finding. The local quality command therefore exits at that
  existing finding; the remaining checks were run with `make -k`.
- **Artifacts:**
  - `evidence/static-analysis/jscpd-report.json`
  - `evidence/static-analysis/dependencies.json`
  - `evidence/static-analysis/pip-audit.json`
  - `evidence/static-analysis/bandit.json`
  - `evidence/static-analysis/churn.json`

### Local-to-PR parity and delivery gates - 2026-09-04

- **Source:** `.github/workflows/quality.yml`
- **Expected:** local review uses the same repository quality entry point and
  analyzer configuration as the pull-request workflow.
- **Observed:** the workflow and local review both use
  `make quality PYTHON=.venv/bin/python`, with the same Makefile targets and
  static-analysis configuration. The remote workflow has not run because this
  branch is not published.
- **Status:** blocked
- **Blocker:** configured remote checks are required before delivery readiness
  and cannot run until the branch is published.

### Maintainer validation handoff - pending

- **Required response:** the maintainer must validate the export panel and
  return one of:
  `PASS: every required check succeeded; evidence: <paths or notes>`,
  `FAIL: <failed check and observed result>`,
  `BLOCKED: <missing service, data, permission, or capability>`, or
  `NOT APPLICABLE: <reason and approval>`.
- **Status:** blocked pending user response

## Review judgment

The changed UI and panel state use the same source-level
`resolve_upscale_policy()` decision used by export planning. The immediate
display path performs only metadata-based policy resolution and does not move
backend validation or estimates back onto the GTK main loop. The execution
regression verifies that eligible sources alone invoke restoration, while the
real RVE run verifies the unchanged production route and atomic publication.
No introduced high-confidence correctness, security, or scope finding was
identified.

## Readiness

Implementation, focused regressions, full local verification, target-workstation
UI validation, and real RVE export evidence are complete. The ticket remains
`verifying` because required maintainer validation and remote checks are not
terminal. The pre-existing complexity finding remains an accepted concern
outside the ticket scope.

## Open blockers

- Required maintainer/user validation response is pending.
- Required remote checks are unavailable until the branch is published.
- Existing repository-wide complexity debt remains at
  `benchmarks/restoration_benchmark.py:1794`.

### User-validation closeout - 2026-09-07

- **User response:** `PASS` — the user confirmed the implemented ticket set
  is good.
- **Status:** passed; this supersedes the earlier pending user-validation
  state.
