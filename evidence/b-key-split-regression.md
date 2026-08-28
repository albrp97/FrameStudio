# Evidence - TICKET-059

**Phase:** PHASE-002  
**Feature:** FEAT-004  
**Ticket:** TICKET-059  
**Objective:** OBJ-001  
**Scope:** SCOPE-001  
**Status:** verifying  
**Planning chain:** `OBJ-001 -> SCOPE-001 -> CAP-003/CAP-012 -> PHASE-002 ->
FEAT-004 -> TICKET-059`  
**Repository:** `/home/ghiki/code/resolve-media-tui`  
**Branch:** `ticket/define-target-fps-selection-and-enhancement-scope`  
**Evidence path:** `evidence/b-key-split-regression.md`

## Requirement

- Given a selected clip and a playhead strictly inside its visible timeline
  bounds, pressing **B** or **b** should split that clip at the visible
  playhead.
- Given deleted or reordered preceding blocks, the split should use the
  visible timeline coordinate rather than the concatenated playback position.
- Existing domain and CLI boundary validation must remain unchanged.

## Protected flows

Existing split/delete, mixed-source timeline, playback/seek, persistence,
export, legacy scripts, and source-preservation behavior remain protected.

## E-901 - Protected baseline

- **Category:** baseline
- **Command:** `python3 -m unittest tests.test_editor_ui_helpers
  tests.test_editor_operations tests.test_editor_mixed_source
  tests.test_editor_cli_parity`
- **Expected:** Existing split, UI, mixed-source, and CLI parity behavior is
  green before the corrective change.
- **Observed:** 43 tests passed. The existing PyGObject deprecation warning
  was emitted without failing the command.
- **Status:** passedWithConcerns
- **Artifacts:** terminal output; existing source and test suite.
- **Failure:** none.
- **Fix:** none.
- **Accepted warning:** Existing `GLib.unix_signal_add_full` deprecation.

## E-902 - B-key regression red state

- **Category:** implementation
- **Command:** `python3 -m unittest
  tests.test_editor_composition.EditorCompositionTests.test_b_key_splits_at_visible_playhead_after_deleted_block`
- **Expected:** A selected clip after a deleted preceding block should split
  when the controller reports the corresponding edited-output position.
- **Observed:** The test failed as expected because the handler passed the
  edited-output position directly to the source split path and reported
  `Split position must be strictly inside the selected block`.
- **Status:** failed
- **Artifacts:** user-reported GTK failure; `framestudio/app_playback.py`,
  `framestudio/app_timeline_actions.py`,
  `framestudio/model_timeline.py`, and the new regression test.
- **Failure:** Edited playback position `4.0` was used for a selected source
  block whose visible timeline interval was `7.0` to `10.0`.
- **Fix:** none.

## E-903 - Corrected B-key coordinate mapping

- **Category:** implementation
- **Command:** `python3 -m unittest
  tests.test_editor_composition.EditorCompositionTests.test_b_key_splits_at_visible_playhead_after_deleted_block
  tests.test_editor_composition.EditorCompositionTests.test_b_key_splits_mixed_block_at_visible_playhead_after_deleted_block`
- **Expected:** B-key handling maps the controller's edited-output position to
  the visible timeline before splitting one-source and mixed-source blocks.
- **Observed:** Both regression tests passed. The selected block split at the
  visible timeline position, and the post-split selection/status remained
  correct.
- **Status:** passed
- **Artifacts:** `framestudio/app_timeline_actions.py`,
  `tests/test_editor_composition.py`.
- **Failure:** none after the fix.
- **Fix:** Convert the playback position with
  `SegmentTimeline.edited_to_timeline_position()` before invoking the existing
  source or timeline split operation.

## E-904 - Protected regression and quality gates

- **Category:** regression
- **Commands:** `python3 -m unittest tests.test_editor_composition
  tests.test_editor_ui_helpers tests.test_editor_operations
  tests.test_editor_mixed_source tests.test_editor_cli_parity`, `make check`,
  `make contract`, `make smoke`, and `make quality
  PYTHON=.venv/bin/python`
- **Expected:** The corrective change preserves the affected editor flows,
  the complete repository suite, generated-media smoke, CLI contract, and
  configured local quality gates.
- **Observed:** The affected editor suites passed 60 tests; `make check`
  passed 240 tests, compilation, and diff checks; `make contract` passed 29
  tests; `make smoke` completed successfully; and the configured quality
  suite passed formatting, lint, type, complexity, duplication, dependency,
  security, audit, and churn checks.
- **Status:** passedWithConcerns
- **Artifacts:** terminal output; `framestudio/app_timeline_actions.py`,
  `tests/test_editor_composition.py`, and generated quality reports.
- **Failure:** none.
- **Fix:** none after the focused coordinate-mapping change.
- **Accepted warnings:** Existing PyGObject deprecation warning. Remote checks
  and target-workstation visual keyboard confirmation are unavailable in this
  session.

## Readiness

- **Passed:** E-901, E-903, and E-904.
- **Passed with concerns:** E-901 and E-904 because of the existing
  deprecation warning and unavailable remote/target-workstation gates.
- **Failed:** E-902 is the intentional pre-fix regression failure and is
  superseded by E-903.
- **Blocked:** User-facing target-workstation confirmation of pressing **B** in
  the live GTK editor remains required.
- **Skipped:** None.

## E-905 - Final review and static-analysis gate

- **Category:** review
- **Commands:** `make quality PYTHON=.venv/bin/python`; `git diff --check`
  on the focused fix paths; CI parity comparison against
  `.github/workflows/quality.yml`.
- **Expected:** The final corrective diff has no introduced deterministic
  findings, remains within the approved ticket scope, and matches the
  repository's configured pull-request quality commands.
- **Observed:** The configured formatter, linter, type, complexity,
  duplication, dependency-boundary, dependency-audit, security, and churn
  checks passed. `evidence/static-analysis/baseline.json` contains no
  findings; the changed editor action and regression tests are not reported
  as churn hotspots. The local quality command and configuration match the
  pull-request workflow's quality command and pinned tool/configuration
  inputs. The focused implementation changes only the playback-to-timeline
  coordinate conversion and regression coverage.
- **Status:** passedWithConcerns
- **Artifacts:** `.github/workflows/quality.yml`,
  `evidence/static-analysis/baseline.json`,
  `evidence/static-analysis/churn.json`,
  `evidence/static-analysis/jscpd-report.json`,
  `evidence/static-analysis/dependencies.json`,
  `evidence/static-analysis/pip-audit.json`,
  `evidence/static-analysis/bandit.json`,
  `framestudio/app_timeline_actions.py`, and
  `tests/test_editor_composition.py`.
- **Failure:** None.
- **Fix:** None required.
- **Blockers:** Required live GTK target-workstation confirmation of pressing
  **B** after deleting a preceding block is still outstanding. Remote CI
  checks cannot run because this checkout has no configured remote or
  upstream.
- **Accepted warnings:** Existing `GLib.unix_signal_add_full` deprecation
  warning; unrelated PHASE-007 changes remain uncommitted and are outside
  this corrective scope.

## Readiness (superseding E-904 summary)

- **Passed:** E-901, E-903, E-904, and E-905.
- **Passed with concerns:** E-901, E-904, and E-905 because of the existing
  deprecation warning and unavailable remote/target-workstation gates.
- **Failed:** E-902 is the intentional pre-fix regression failure and is
  superseded by E-903.
- **Blocked:** Target-workstation B-key validation and configured remote
  checks remain required before commit readiness.
- **Skipped:** None.
- **Next permitted action:** Run the target-workstation B-key validation and
  return `PASS`, `FAIL`, or `BLOCKED` with the exact result.

### E-906 — User acceptance for closure

- **Timestamp:** 2026-08-26
- **Category:** userValidation
- **Requirement/flow:** Confirm the corrected B-key split behavior is accepted
  after testing.
- **Observed:** User confirmed: “all the tickets are approved and accepted and
  tested, close all done tickets, features and phases.”
- **Status:** passed
- **Accepted warnings:** The historical target-workstation and remote-check
  limitations remain explicit; no unavailable result is claimed as passed.

## Closure disposition

User acceptance is terminal for TICKET-059. Its corrective record is eligible
for closure while the parent feature and phase history remain preserved.
