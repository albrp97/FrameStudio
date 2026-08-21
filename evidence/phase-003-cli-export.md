# Evidence - TICKET-015

**Phase:** PHASE-003  
**Feature:** FEAT-008  
**Ticket:** TICKET-015  
**Objective:** OBJ-001  
**Scope:** SCOPE-001  
**Status:** implementation-complete  
**Planning chain:** `OBJ-001 -> SCOPE-001 -> CAP-004/CAP-006/CAP-012 ->
PHASE-003 -> FEAT-008 -> TICKET-015`  
**Repository:** `/home/ghiki/code/resolve-media-tui`  
**Branch:** `main`  
**Base revision:** `150d2f7`  
**Dependency evidence:** `evidence/verified-safe-export.md`,
`evidence/phase-003-cli-editing.md`  
**Evidence path:** `evidence/phase-003-cli-export.md`

## Requirements and protected behavior

- Reuse the verified stream-copy/fallback planner and executor.
- Emit structured progress with percentage, frame counts, FPS, elapsed time,
  and ETA before the final result.
- Publish only validated output and report route, reason, and output metadata.
- Preserve source, project, and valid prior output on failure.

## E-1501 - Focused export adapter verification

- **Category:** implementation
- **Command:** `python3 -m unittest tests.test_editor_cli_export`
- **Expected:** Successful progress/final JSON Lines and structured export
  failures are reported without a false final success.
- **Observed:** 2 tests passed.
- **Status:** passed
- **Artifacts:** `resolve_editor/cli.py`,
  `tests/test_editor_cli_export.py`.
- **Failure:** none.
- **Fix:** none.

## E-1502 - Real disposable CLI export

- **Category:** functionality
- **Command or steps:** Generated a one-second source with FFmpeg, imported,
  split, deleted a segment, and exported through
  `python3 resolve_editor.py export`.
- **Expected:** The selected route and verification state are reported; the
  published output is probeable and the source remains unchanged.
- **Observed:** The command reported `stream-copy` and `verified: true`.
  FFprobe found a playable 320x180 H.264 video output; temporary artifacts
  were removed.
- **Status:** passed
- **Artifacts:** `resolve_editor/export.py`,
  `resolve_editor/operations.py`, disposable FFmpeg/ffprobe output.
- **Failure:** none.
- **Fix:** none.
- **Accepted warning:** Stream-copy timing follows the existing conservative
  export tolerance at a keyframe boundary.

## Final readiness

- **Passed:** E-1501 and E-1502.
- **Passed with concerns:** the existing PyGObject warning remains non-failing.
- **Blocked:** no local safe-export blocker.
- **Remote checks:** unavailable and not claimed as passed.
- **Readiness:** TICKET-015 implementation and local evidence are complete;
  the planning record remains open for configured review/closeout.

## Remediation - Project-path export protection

- **Finding:** The CLI accepted an export destination equal to the project
  file, allowing a successful media export to replace the JSON project.
- **Requirement:** Given an export destination that resolves to the project
  file, the CLI should reject the request before planning or executing FFmpeg
  and preserve the project bytes.
- **Fix:** Added a destination guard in `resolve_editor/cli.py` and a regression
  test in `tests/test_editor_cli_export.py`.
- **Focused baseline:** The new regression initially failed with
  `AssertionError: 0 != 3`, confirming the unsafe behavior.
- **Focused verification:** `python3 -m unittest discover -s tests -p
  'test_editor_cli_export.py'` — 3 tests passed.
- **Protected verification:** `make check` — 122 tests passed, compilation
  passed, and `git diff --check` passed.
- **Real verification:** A disposable CLI export to the project path returned
  `invalid_arguments`; the project remained inspectable.
- **Status:** resolved locally; remote checks and configured UI artifacts
  remain unavailable.

## Remediation extension - shared GUI/CLI boundary

- **Finding scope:** The same project-path collision was possible through the
  GTK export dialog when reopening a saved project.
- **Fix:** Added `export_destination_conflicts_with_project` to the shared
  operations boundary and applied it in both CLI and GTK export adapters.
- **Focused verification:** The shared operation tests (4 passed) and CLI
  export tests (3 passed) cover the resolved-path predicate and early rejection.
- **Protected verification:** `make check` — 123 tests passed, compilation
  passed, and `git diff --check` passed; `make smoke` exited successfully.
- **Real verification:** A disposable CLI export to the project path was
  rejected and the project remained inspectable.
- **Status:** resolved locally across both export entry points.
