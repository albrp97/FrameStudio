# TICKET-079 - Production Upscale Enhancement Evidence

**Phase:** PHASE-008
**Feature:** FEAT-028
**Ticket:** TICKET-079
**Planning change:** CHG-008
**Branch:** `ticket/phase-008-responsive-preview-media-strategy`
**Evidence status:** in progress
**Evidence path:** `evidence/ticket-079-production-upscale-enhancement.md`

## Context

This record covers the approved opt-in SuperUltraCompact upscale path,
orientation-aware no-downscale behavior, GUI/CLI parity, integration with
per-source FPS enhancement and composition, safe output delivery, and
protected existing export behavior.

## Planning chain

`OBJ-001 -> SCOPE-001 -> PHASE-008 -> FEAT-028 -> TICKET-079`

## Requirements and protected flows

- R1: Landscape sources with short side at or below 1000 pixels resolve to a
  1080-pixel short-side target when upscale is enabled.
- R2: Portrait sources with short side at or below 720 pixels resolve to a
  1080-pixel short-side target when upscale is enabled.
- R3: Disabled or ineligible sources do not invoke the model and preserve the
  existing route.
- R4: SuperUltraCompact restoration and spatial preparation occur before
  per-source FPS interpolation when both policies are enabled.
- R5: Normal and triplicate composition do not downscale an enhanced source.
- R6: Project persistence, GUI/CLI plan parity, audio, frame count, duration,
  atomic publication, cancellation, cleanup, and source preservation remain
  safe.

## Entries

### Planning

- **Status:** passed
- **Expected:** The material production-scope change is recorded with stable
  parent links, a focused feature, two bounded tickets, and synchronized
  indexes before implementation.
- **Observed:** CHG-008, FEAT-028, TICKET-079, and TICKET-080 were created;
  PHASE-008, `features.md`, and `backlog.md` were updated with current links.
- **Artifacts:** `docs/planning/reviews/CHG-008-add-production-upscale-enhancement.md`,
  `docs/planning/features/open/FEAT-028-adding-optional-upscale-enhancement.md`,
  `docs/planning/tickets/open/TICKET-079-implement-optional-upscale-enhancement.md`,
  `docs/planning/tickets/open/TICKET-080-benchmark-upscale-render-strategies.md`

### Baseline

- **Status:** passed
- **Expected:** Existing editor export, model, composition, CLI, and
  interpolation tests pass before source changes.
- **Command:** `python3 -m unittest tests.test_editor_export tests.test_editor_export_execution tests.test_editor_model tests.test_editor_composition tests.test_editor_cli_export tests.test_editor_cli_parity tests.test_editor_interpolation`
- **Observed:** 102 tests passed before production upscale implementation.
- **Artifacts:** protected test command output retained in the session
  execution history.

## Open blockers and warnings

- User visual validation is pending by policy.
- Target-workstation RVE and real-media export evidence is pending.
- TICKET-080 benchmark execution depends on this implementation.

## Readiness

Implementation and technical verification are not complete. Do not close the
ticket or claim delivery readiness until required tests, real-media evidence,
user validation, static analysis, review, and configured delivery gates are
terminal.

### CLI FPS override regression fix

- **Status:** passed for the focused regression; ticket remains open.
- **Requirement:** Given an export plan carrying a `FrameRatePolicy` object
  with enhancement disabled, the CLI should report that disabled policy rather
  than falling back to the persisted project policy.
- **Baseline:** The new regression test failed with
  `enhancement_enabled` reported as `True` despite `--no-enhance-fps`.
- **Fix:** `framestudio/cli_export.py` now preserves `FrameRatePolicy`
  instances when selecting the policy used for export reporting and estimates.
- **Focused test:** `python3 -m unittest tests.test_editor_cli_export.EditorCliExportTests.test_export_plan_reports_frame_rate_policy_object_override`
- **Observed:** 1 test passed.
- **Regression suite:** `python3 -m unittest tests.test_editor_cli_export`
- **Observed:** 10 tests passed.
- **Compilation:** `python3 -m py_compile framestudio/cli_export.py tests/test_editor_cli_export.py`
- **Observed:** passed.
- **Real CLI check:** `python3 framestudio.py export-plan ... --no-enhance-fps --upscale-enhancement`
- **Observed:** emitted `enhancement_enabled: false`.
- **Remaining gaps:** Mixed-source frame-rate conversion, portrait/triplicate
  real-media export, user validation, review, and configured delivery gates
  remain open.

### Mixed-source frame-rate and triplicate export fix

- **Status:** passed for automated and target-workstation fixture checks;
  ticket remains open.
- **Requirement:** Given mixed source rates and enabled spatial enhancement,
  the composed output should retain the selected constant frame rate and exact
  target frame count despite encoded audio padding.
- **Baseline:** The mixed landscape/portrait fixture failed verification with
  `Mixed export frame rate does not match the output policy`; the output
  contained 240 frames but reported `14400/241`.
- **Fix:** Enhanced clip assembly now emits explicit CFR output at the selected
  rate and bounds the final video duration to the edited duration.
- **Regression test:** `python3 -m unittest tests.test_editor_export_execution.EditorExportExecutionTests.test_mixed_upscale_export_preserves_target_frame_rate_with_audio_padding`
- **Observed:** 1 test passed using generated mixed 24 FPS/30 FPS media with
  audio and an enabled upscale route.
- **Affected suites:** `python3 -m unittest tests.test_editor_export_execution tests.test_editor_smart_render tests.test_editor_export`
- **Observed:** 39 tests passed.
- **Real-media fixture:** Exported
  `mixed.framestudio.json` with `--no-enhance-fps --upscale-enhancement` to
  `/tmp/mixed-upscale-fixed-2.mp4`.
- **Observed:** playable MP4, 1920x1080, `60/1`, 240 video frames, no partial
  output remained; the 4.021333-second container duration is within the
  existing verification tolerance for the 4-second edited timeline.
- **Remaining gaps:** Full target-workstation validation matrix, user
  validation, TICKET-080 benchmark execution, review, and configured delivery
  gates remain open.

### Protected suite and quality checks

- **Protected check:** `make check`
- **Observed:** 340 tests passed, Python compilation passed, and
  `git diff --check` passed.
- **CLI contract check:** `make contract` passed with 34 tests.
- **Repository venv quality checks:** Ruff format, Ruff lint, mypy for all
  configured targets, and Bandit passed.
- **Environment note:** The equivalent `make format-check`, `make lint`,
  `make type-check`, and `make security` targets use the system Python, which
  lacks those quality modules; the repository `.venv` supplied the same
  configured tools successfully.
- **Pre-existing blocker:** The configured complexity check still reports
  `benchmarks/restoration_benchmark.py:run_benchmark` at 16 where the limit is
  15; this is outside the two export fixes.

### Default policy correction under TICKET-081

- **Status:** passed for implementation and regression coverage; delivery
  remains governed by TICKET-081's open validation and review gates.
- **Requirement:** Given a new project or a project without a persisted
  upscale decision, eligible sources should use SuperUltraCompact enhancement
  by default while an explicit disabled policy remains respected.
- **Observed:** `UpscalePolicy`, project policy resolution, the GTK export
  panel, CLI payloads, persistence, and protected fallback tests now agree on
  the enabled-by-default behavior. The first post-change full suite exposed
  four stale tests that assumed the former implicit disabled default; those
  tests now pass an explicit disabled policy and the final full suite passes
  351 tests.
- **Contract:** `--no-upscale-enhancement` and
  `set-upscale-policy --disable-upscale` remain available for explicit
  opt-out.

### E-079-USER-VALIDATION-001 - User-confirmed manual validation

- **Timestamp:** 2026-08-28T08:06:41+02:00
- **Category:** userValidation
- **Requirement:** The optional upscale policy, GUI/CLI parity, enhanced
  export behavior, and protected disabled path are manually validated.
- **Steps:** The user stated, "you can close all the tickets i manually
  validated everything and you can then /aidd-commit".
- **Observed:** The user reports that the ticket behavior was manually
  validated. This response did not include a per-ticket output path,
  metadata capture, or separate failure-path notes.
- **Status:** passed
- **Accepted warning:** User validation is terminal, but this evidence record
  still documents incomplete technical/review/delivery gates for TICKET-079.

### E-079-READINESS-001 - Current delivery state after user validation

- **Timestamp:** 2026-08-28T08:06:41+02:00
- **Category:** gate
- **Requirement:** Do not close or deliver the implementation ticket while
  technical, review, and delivery evidence remains incomplete.
- **Observed:** User validation is recorded as passed. The evidence record
  still lacks terminal full technical/review/delivery gates, the branch is
  shared across Phase 8, and no paths are staged.
- **Status:** blocked
- **Blocker:** Technical/review completion and commit-scope prerequisites are
  unresolved.
