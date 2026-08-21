# Evidence - TICKET-009

**Phase:** PHASE-002  
**Feature:** FEAT-006  
**Ticket:** TICKET-009  
**Objective:** OBJ-001  
**Scope:** SCOPE-001  
**Status:** in-progress  
**Planning chain:** `OBJ-001 -> SCOPE-001 -> CAP-004/CAP-012 -> PHASE-002 ->
FEAT-006 -> TICKET-009`  
**Repository:** `/home/ghiki/code/resolve-media-tui`  
**Branch:** `main`  
**Base revision:** `150d2f7`  
**Dependency evidence:** `evidence/segment-model-cut-semantics.md`,
`evidence/split-delete-duration.md`  
**Evidence path:** `evidence/persist-cut-state-recovery.md`

## Requirements

- Persist ordered segment boundaries and deletion state.
- Restore segment state, playhead, source identity, and edited duration.
- Migrate PHASE-001 schema-version 1 projects safely.
- Reject malformed or inconsistent segment state without replacing valid state.
- Preserve atomic save and source-safe behavior.

## Protected flows

Existing source opening, playback, Space-key transport, mouse-wheel seeking,
project save/reopen foundation, atomic writes, legacy scripts, and all
previous tests remain protected.

## E-901 - Dependency baseline

- **Category:** baseline
- **Command:** `make check`
- **Expected:** TICKET-007 and TICKET-008 behavior are green before schema
  persistence changes.
- **Observed:** The dependency gate passed 67 tests, compilation, and diff
  checks; the existing PyGObject deprecation warning was emitted.
- **Status:** passedWithConcerns
- **Artifacts:** dependency evidence records and terminal output.
- **Failure:** none.
- **Fix:** none.
- **Accepted warning:** The existing PyGObject warning is non-failing.

## Readiness

- **Passed:** E-901.
- **Passed with concerns:** E-901 because of the existing PyGObject warning.
- **Failed:** none.
- **Blocked:** implementation and recovery evidence are pending.
- **Skipped:** none.
- **Next permitted action:** run the focused persistence red tests and
  implement schema migration and segment round-trip behavior.

## E-902 - Intentional TDD red state

- **Category:** baseline
- **Command:** `python3 -m unittest tests.test_editor_model tests.test_editor_persistence`
- **Expected:** New schema and cut-state persistence requirements fail before
  the project model is extended.
- **Observed:** 18 tests ran with the expected schema mismatch, missing
  `segment_timeline`, and missing edited-duration validation failures.
- **Status:** passedWithConcerns
- **Artifacts:** terminal output.
- **Failure:** expected missing schema integration.
- **Fix:** added schema version 2, segment-state persistence, and version 1
  migration.
- **Accepted warning:** This was an intentional red state.

## E-903 - Cut-state persistence focused tests

- **Category:** implementation
- **Command:** `python3 -m unittest tests.test_editor_model tests.test_editor_persistence`
- **Expected:** Project segment state round-trips, legacy projects migrate,
  inconsistent durations fail, and atomic saves remain safe.
- **Observed:** 18 focused model and persistence tests passed.
- **Status:** passed
- **Artifacts:** `resolve_editor/model.py`,
  `resolve_editor/persistence.py`,
  `tests/test_editor_model.py`,
  `tests/test_editor_persistence.py`.
- **Failure:** none.
- **Fix:** none.

## E-904 - Full local regression gate

- **Category:** regression
- **Command:** `make check`
- **Expected:** Schema changes preserve all protected behavior.
- **Observed:** 70 tests passed; Python compilation and `git diff --check`
  passed. The existing PyGObject deprecation warning was emitted.
- **Status:** passedWithConcerns
- **Artifacts:** terminal output.
- **Failure:** none.
- **Fix:** none.
- **Accepted warning:** The existing PyGObject warning remains non-failing.

## E-905 - Persisted cut-state GTK smoke

- **Category:** functionality
- **Command:** `make smoke`
- **Expected:** The GTK smoke flow opens generated media, performs a
  split/delete edit, saves the versioned project, reopens it, and exits
  cleanly.
- **Observed:** The smoke target exited successfully and cleaned up its
  temporary media and project artifacts.
- **Status:** passedWithConcerns
- **Artifacts:** terminal output; temporary artifacts were removed.
- **Failure:** none.
- **Fix:** none.
- **Accepted warning:** The session has no usable X11 display for visual
  save/reopen interaction evidence.

## Final readiness

- **Passed:** E-903.
- **Passed with concerns:** E-901 through E-905 due to the existing
  PyGObject warning, intentional red state, and unavailable visual artifact.
- **Failed:** none.
- **Blocked:** no local automated blocker; target-workstation save/reopen
  confirmation remains a user-facing concern.
- **Skipped:** automated visual interaction and screenshot capture.
- **Readiness:** TICKET-009 is complete for local delivery and unblocks
  TICKET-011 once TICKET-010 is complete.
