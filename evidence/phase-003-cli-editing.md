# Evidence - TICKET-014

**Phase:** PHASE-003  
**Feature:** FEAT-008  
**Ticket:** TICKET-014  
**Objective:** OBJ-001  
**Scope:** SCOPE-001  
**Status:** implementation-complete  
**Planning chain:** `OBJ-001 -> SCOPE-001 -> CAP-004/CAP-006/CAP-012 ->
PHASE-003 -> FEAT-008 -> TICKET-014`  
**Repository:** `/home/ghiki/code/resolve-media-tui`  
**Branch:** `main`  
**Base revision:** `150d2f7`  
**Dependency evidence:** `evidence/phase-003-cli-contract.md`,
`evidence/phase-003-cli-inspection.md`,
`evidence/persist-cut-state-recovery.md`  
**Evidence path:** `evidence/phase-003-cli-editing.md`

## Requirements and protected behavior

- Import/open, split, delete, restore/toggle, duration, save, and reopen
  through deterministic commands.
- Address segments by stable identifiers rather than list positions.
- Preserve timeline invariants, atomic writes, source identity, and last-valid
  state on invalid operations or failed saves.
- Keep the original scripts and GUI workflow available.

## E-1401 - Focused command verification

- **Category:** implementation
- **Command:** `python3 -m unittest tests.test_editor_cli_editing`
- **Expected:** Import uses media metadata; split/delete/restore/duration
  round-trip; repeated delete is idempotent; invalid split preserves state;
  save/reopen preserves the project contract.
- **Observed:** 5 tests passed.
- **Status:** passed
- **Artifacts:** `resolve_editor/cli.py`,
  `tests/test_editor_cli_editing.py`.
- **Failure:** none.
- **Fix:** none.

## E-1402 - Disposable CLI edit round trip

- **Category:** functionality
- **Command or steps:** Generated a disposable source, imported it, split at
  an interior position, deleted the second stable segment, queried duration,
  and reopened the project through the executable.
- **Expected:** The project remains valid, source media is untouched, and
  edited duration reflects retained segments.
- **Observed:** The flow completed successfully and produced the expected
  structured command results; disposable files were removed.
- **Status:** passed
- **Artifacts:** disposable CLI smoke output; `resolve_editor/model.py`,
  `resolve_editor/persistence.py`.
- **Failure:** none.
- **Fix:** none.

## Final readiness

- **Passed:** E-1401 and E-1402.
- **Passed with concerns:** repository-wide gates inherit the existing
  PyGObject warning.
- **Blocked:** no local editing blocker.
- **Remote checks:** unavailable and not claimed as passed.
- **Readiness:** TICKET-014 implementation and local evidence are complete;
  the planning record remains open for configured review/closeout.
