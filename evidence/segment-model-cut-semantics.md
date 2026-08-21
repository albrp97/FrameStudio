# Evidence - TICKET-007

**Phase:** PHASE-002  
**Feature:** FEAT-004  
**Ticket:** TICKET-007  
**Objective:** OBJ-001  
**Scope:** SCOPE-001  
**Status:** passedWithConcerns  
**Planning chain:** `OBJ-001 -> SCOPE-001 -> CAP-003/CAP-012 -> PHASE-002 ->
FEAT-004 -> TICKET-007`  
**Repository:** `/home/ghiki/code/resolve-media-tui`  
**Branch:** `main`  
**Base revision:** `150d2f7`  
**Evidence path:** `evidence/segment-model-cut-semantics.md`

## Requirements

- A valid source starts with one segment covering the source exactly.
- A valid interior split creates two ordered segments without changing source
  coverage.
- Delete and restore preserve valid segment state and update edited duration
  according to the approved policy.
- Invalid edits report an actionable error and preserve the last valid state.
- Segment editing never modifies source media.

## Protected flows

Existing scripts, command names, curses workflows, source-safe output
behavior, project persistence, playback/timeline behavior, and PHASE-001
tests remain available.

## E-701 - Protected automated baseline

- **Category:** baseline
- **Command:** `python3 -m unittest discover -s tests`
- **Expected:** All protected tests pass before TICKET-007 implementation.
- **Observed:** 57 tests passed in 0.513 seconds. The existing PyGObject
  deprecation warning for `GLib.unix_signal_add_full` was emitted.
- **Status:** passedWithConcerns
- **Artifacts:** terminal output.
- **Failure:** none.
- **Fix:** none.
- **Accepted warning:** The deprecation warning is pre-existing and does not
  fail the test run.

## Readiness

- **Passed:** E-701.
- **Passed with concerns:** E-701 because of the existing PyGObject warning.
- **Failed:** none.
- **Blocked:** implementation and downstream evidence are pending.
- **Skipped:** none.
- **Next permitted action:** implement the smallest failing requirement for
  the segment model under TICKET-007.

## E-702 - Intentional TDD red state

- **Category:** baseline
- **Command:** `python3 -m unittest tests.test_editor_model`
- **Expected:** The new segment requirements fail because the segment model
  has not been implemented.
- **Observed:** Test collection failed because `SegmentTimeline` was not yet
  available from `resolve_editor.model`.
- **Status:** passedWithConcerns
- **Artifacts:** terminal output.
- **Failure:** expected missing implementation.
- **Fix:** added the segment model and validation operations.
- **Accepted warning:** This was an intentional red state.

## E-703 - Segment model focused tests

- **Category:** implementation
- **Command:** `python3 -m unittest tests.test_editor_model`
- **Expected:** Segment construction, split, delete, restore, repeated
  operations, invalid positions, and identifier validation pass.
- **Observed:** 11 focused model tests passed.
- **Status:** passed
- **Artifacts:** `resolve_editor/model.py`, `tests/test_editor_model.py`.
- **Failure:** none.
- **Fix:** none.

## E-704 - Cut semantics decision

- **Category:** implementation
- **Steps:** Record source-time half-open intervals, strict interior splits,
  retained-segment ripple behavior, edited-duration calculation, and
  timestamp/keyframe limitations in the phase specification.
- **Expected:** The model policy is explicit and downstream UI/export layers
  do not need to infer boundary or duration behavior.
- **Observed:** The policy is documented at
  `docs/specs/phase-002-cut-semantics.md` and is exercised by the focused
  model tests.
- **Status:** passed
- **Artifacts:** `docs/specs/phase-002-cut-semantics.md`.
- **Failure:** none.
- **Fix:** none.

## Current readiness

- **Passed:** E-701, E-703, and E-704.
- **Passed with concerns:** E-701 and E-702 due to the pre-existing
  PyGObject warning and intentional red state.
- **Failed:** none.
- **Blocked:** final regression and local-quality evidence are pending.
- **Skipped:** none.

## E-705 - Full local regression gate

- **Category:** regression
- **Command:** `make check`
- **Expected:** The segment model and all protected repository behavior pass
  tests, compilation, and diff checks.
- **Observed:** 64 tests passed; Python compilation and `git diff --check`
  passed. The existing PyGObject deprecation warning was emitted.
- **Status:** passedWithConcerns
- **Artifacts:** terminal output.
- **Failure:** none.
- **Fix:** none.
- **Accepted warning:** The pre-existing PyGObject deprecation warning remains
  non-failing.

## E-706 - TICKET-007 completion review

- **Category:** review
- **Steps:** Compare the implementation with the approved ticket scope,
  cut-semantics decision, protected behaviors, and definition of done.
- **Expected:** The ticket is complete without claiming UI, persistence, or
  export behavior.
- **Observed:** The model, invariants, reversible deletion state, strict
  interior split behavior, decision document, focused tests, and full
  regression evidence are present. Downstream behavior remains explicitly
  outside this ticket.
- **Status:** passed
- **Artifacts:** `resolve_editor/model.py`,
  `tests/test_editor_model.py`,
  `docs/specs/phase-002-cut-semantics.md`.
- **Failure:** none.
- **Fix:** none.

## Final readiness

- **Passed:** E-703, E-704, and E-706.
- **Passed with concerns:** E-701, E-702, and E-705 because of the
  pre-existing PyGObject warning and the intentional red-state record.
- **Failed:** none.
- **Blocked:** configured remote checks are unavailable in this repository;
  this remains a PR-readiness concern.
- **Skipped:** no manual UI flow was required for this domain-only ticket.
- **Readiness:** TICKET-007 is complete for local delivery and unblocks
  TICKET-008, TICKET-009, and TICKET-010 planning dependencies.

## E-707 - Review-fix atomic replacement regression

- **Category:** review
- **Command:** `python3 -m unittest tests.test_editor_model`
- **Expected:** An invalid candidate segment replacement leaves the previous
  valid timeline unchanged.
- **Observed:** 12 focused model tests passed, including the atomic
  replacement regression.
- **Status:** passed
- **Artifacts:** `resolve_editor/model.py`,
  `tests/test_editor_model.py`.
- **Failure:** none.
- **Fix:** validate candidate segments before committing them and restore the
  previous tuple if validation fails.

## E-708 - Superseding full local regression gate

- **Category:** regression
- **Command:** `make check`
- **Expected:** The review fix preserves all protected behavior and passes
  tests, compilation, and diff checks.
- **Observed:** 65 tests passed; Python compilation and `git diff --check`
  passed. The existing PyGObject deprecation warning was emitted.
- **Status:** passedWithConcerns
- **Artifacts:** terminal output.
- **Failure:** none.
- **Fix:** none.
- **Accepted warning:** The pre-existing PyGObject deprecation warning remains
  non-failing.

## Superseding final readiness

- **Passed:** E-703, E-704, E-706, and E-707.
- **Passed with concerns:** E-701, E-702, E-705, and E-708.
- **Failed:** none.
- **Blocked:** configured remote checks are unavailable in this repository;
  this remains a PR-readiness concern.
- **Skipped:** no manual UI flow was required for this domain-only ticket.
- **Readiness:** TICKET-007 remains complete and its review finding is closed.
