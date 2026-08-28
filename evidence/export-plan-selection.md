# Evidence - TICKET-010

**Phase:** PHASE-002  
**Feature:** FEAT-005  
**Ticket:** TICKET-010  
**Objective:** OBJ-001  
**Scope:** SCOPE-001  
**Status:** in-progress  
**Planning chain:** `OBJ-001 -> SCOPE-001 -> CAP-005/CAP-012 -> PHASE-002 ->
FEAT-005 -> TICKET-010`  
**Repository:** `/home/ghiki/code/resolve-media-tui`  
**Branch:** `main`  
**Base revision:** `150d2f7`  
**Dependency evidence:** `evidence/segment-model-cut-semantics.md`,
`evidence/split-delete-duration.md`,
`evidence/persist-cut-state-recovery.md`  
**Evidence path:** `evidence/export-plan-selection.md`

## Requirements

- Select stream copy only for an explicitly eligible edit.
- Select a documented H.264/AAC MP4 fallback when fast-path conditions fail.
- Explain every fallback reason.
- Reject empty edits, source/destination collisions, duration mismatches, and
  unavailable probing tools before command execution.
- Return deterministic structured plans without writing output.

## Protected flows

Existing source probing, project persistence, segment invariants, UI
transport, atomic save behavior, legacy scripts, and source-safe output
behavior remain protected.

## E-1001 - Dependency baseline

- **Category:** baseline
- **Command:** `make check`
- **Expected:** TICKET-009 and all prior protected behavior are green before
  adding export planning.
- **Observed:** The dependency gate passed 70 tests, compilation, and diff
  checks; the existing PyGObject deprecation warning was emitted.
- **Status:** passedWithConcerns
- **Artifacts:** dependency evidence records and terminal output.
- **Failure:** none.
- **Fix:** none.
- **Accepted warning:** The existing PyGObject warning is non-failing.

## E-1002 - Intentional TDD red state

- **Category:** baseline
- **Command:** `python3 -m unittest tests.test_editor_export`
- **Expected:** New planner requirements fail before the export planner exists.
- **Observed:** Test collection failed because `framestudio.export` did not
  exist.
- **Status:** passedWithConcerns
- **Artifacts:** terminal output.
- **Failure:** expected missing implementation.
- **Fix:** added the structured planner and policy.
- **Accepted warning:** This was an intentional red state.

## E-1003 - Export planner focused tests

- **Category:** implementation
- **Command:** `python3 -m unittest tests.test_editor_export`
- **Expected:** Eligible, ineligible, unsupported, empty, invalid-tool, and
  deterministic planning cases are handled explicitly.
- **Observed:** 8 focused planner tests passed.
- **Status:** passed
- **Artifacts:** `framestudio/export.py`,
  `tests/test_editor_export.py`.
- **Failure:** none.
- **Fix:** none.

## E-1004 - Real-media keyframe planning

- **Category:** integration
- **Command:** The focused export test generated a short H.264 fixture,
  probed it with `ffprobe`, and planned a cut without injected keyframes.
- **Expected:** FFprobe JSON keyframe discovery succeeds and returns a
  deterministic fast or fallback plan.
- **Observed:** The real-media planner test passed.
- **Status:** passed
- **Artifacts:** temporary fixture removed after the test.
- **Failure:** none.
- **Fix:** replaced fragile CSV parsing with structured FFprobe JSON parsing.

## E-1005 - Full local regression gate

- **Category:** regression
- **Command:** `make check`
- **Expected:** Export planning preserves all protected behavior.
- **Observed:** 78 tests passed; Python compilation and `git diff --check`
  passed. The existing PyGObject deprecation warning was emitted.
- **Status:** passedWithConcerns
- **Artifacts:** terminal output.
- **Failure:** none.
- **Fix:** none.
- **Accepted warning:** The existing PyGObject warning remains non-failing.

## E-1006 - Export policy review

- **Category:** review
- **Steps:** Compare planner routes and fallback fields with the approved
  FEAT-005 boundaries and the export policy specification.
- **Expected:** Fast-path eligibility, fallback reasons, unsupported-state
  errors, and no-output planner behavior are explicit.
- **Observed:** The planner and
  `docs/specs/phase-002-export-policy.md` agree; command execution and
  output publication remain outside TICKET-010.
- **Status:** passed
- **Artifacts:** `framestudio/export.py`,
  `docs/specs/phase-002-export-policy.md`.
- **Failure:** none.
- **Fix:** none.

## Final readiness

- **Passed:** E-1003, E-1004, and E-1006.
- **Passed with concerns:** E-1001, E-1002, and E-1005 because of the
  existing PyGObject warning and intentional red-state record.
- **Failed:** none.
- **Blocked:** configured remote checks are unavailable; this remains a
  PR-readiness concern.
- **Skipped:** output execution and publication are intentionally deferred to
  TICKET-011.
- **Readiness:** TICKET-010 is complete for local delivery and unblocks
  TICKET-011.
