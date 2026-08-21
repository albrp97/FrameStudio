# Evidence - TICKET-016

**Phase:** PHASE-003  
**Feature:** FEAT-009  
**Ticket:** TICKET-016  
**Objective:** OBJ-001  
**Scope:** SCOPE-001  
**Status:** implementation-complete  
**Planning chain:** `OBJ-001 -> SCOPE-001 -> CAP-004/CAP-006/CAP-012 ->
PHASE-003 -> FEAT-009 -> TICKET-016`  
**Repository:** `/home/ghiki/code/resolve-media-tui`  
**Branch:** `main`  
**Base revision:** `150d2f7`  
**Dependency evidence:** `evidence/phase-003-cli-editing.md`,
`evidence/phase-003-cli-export.md`  
**Evidence path:** `evidence/phase-003-gui-cli-parity.md`

## Requirements and protected behavior

- Route source creation, split, deletion, and export planning through shared
  domain operation boundaries.
- Keep GTK-only presentation/playback state outside the CLI contract.
- Preserve existing GUI behavior and structured CLI errors.

## E-1601 - Shared operation verification

- **Category:** implementation
- **Command:** `python3 -m unittest tests.test_editor_operations`
- **Expected:** Shared source creation, split, deletion, toggle, and export
  planning boundaries preserve model invariants.
- **Observed:** 3 tests passed.
- **Status:** passed
- **Artifacts:** `resolve_editor/operations.py`,
  `tests/test_editor_operations.py`.
- **Failure:** none.
- **Fix:** none.

## E-1602 - GUI adapter routing

- **Category:** review
- **Command or steps:** Updated `resolve_editor/app.py` to use shared
  operations for source creation, split, delete/restore toggle, and export
  planning while retaining UI-specific state, playback, and status handling.
- **Expected:** GUI and CLI use equivalent domain decisions without changing
  presentation responsibilities.
- **Observed:** The existing GUI helper tests and the complete repository
  suite remained green.
- **Status:** passed
- **Artifacts:** `resolve_editor/app.py`,
  `resolve_editor/operations.py`.
- **Failure:** none.
- **Fix:** none.

## Final readiness

- **Passed:** E-1601 and E-1602.
- **Passed with concerns:** local gates inherit the existing PyGObject warning.
- **Blocked:** no local shared-domain blocker.
- **Remote checks:** unavailable and not claimed as passed.
- **Readiness:** TICKET-016 implementation and local evidence are complete;
  the planning record remains open for configured review/closeout.

## TICKET-017 - Parity and idempotent round trips

**Ticket:** TICKET-017  
**Outcome:** Verify GUI-domain and CLI parity, deterministic retries, project
round trips, and the real executable path.  
**Evidence path:** `evidence/phase-003-gui-cli-parity.md`

### E-1701 - Parity and idempotency verification

- **Category:** regression
- **Command:** `python3 -m unittest tests.test_editor_cli_parity`
- **Expected:** Direct shared-domain edits and CLI edits produce equivalent
  timeline shape, deletion state, duration, source identity, and failure
  behavior; the executable dispatches CLI commands without starting GTK.
- **Observed:** 4 tests passed.
- **Status:** passed
- **Artifacts:** `tests/test_editor_cli_parity.py`,
  `resolve_editor.py`.
- **Failure:** none.
- **Fix:** none.

### E-1702 - Complete local quality gate

- **Category:** gate
- **Command:** `make check`
- **Expected:** All repository tests, compilation, and whitespace checks pass
  after the Phase 3 implementation.
- **Observed:** 121 tests passed; Python compilation and
  `git diff --check` passed.
- **Status:** passedWithConcerns
- **Artifacts:** `tests/`, `Makefile`, terminal output.
- **Failure:** none.
- **Fix:** none.
- **Accepted warning:** The existing PyGObject deprecation warning remains
  non-failing.

### E-1703 - GTK smoke regression

- **Category:** functionality
- **Command:** `make smoke`
- **Expected:** The existing generated-media GTK smoke flow remains green.
- **Observed:** The smoke target exited successfully and cleaned up its
  temporary artifacts.
- **Status:** passedWithConcerns
- **Artifacts:** `Makefile`, terminal output.
- **Failure:** none.
- **Fix:** none.
- **Accepted warning:** Visual screenshot evidence is not available in this
  agent session.

### TICKET-017 readiness

- **Passed:** E-1701.
- **Passed with concerns:** E-1702 and E-1703 because of the existing GTK
  warning and unavailable screenshot/remote artifacts.
- **Blocked:** no local automated or disposable-media blocker.
- **Remote checks:** required by `.github/aidd-config.yml`, unavailable, and
  not claimed as passed.
- **Readiness:** TICKET-017 implementation, parity tests, local quality gate,
  GUI smoke regression, and disposable CLI flow are complete locally; the
  planning record remains open for configured review/closeout.
