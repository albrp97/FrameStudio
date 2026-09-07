# TICKET-100 Evidence - Offer Export Resume, Restart, and Discard Controls

**Status:** verifying
**Date:** 2026-09-06
**Repository:** `/home/ghiki/code/FrameStudio`
**Branch:** `ticket/defer-audio-analysis-during-import`
**Planning chain:** OBJ-001 -> SCOPE-001 -> PHASE-008 -> FEAT-029 -> TICKET-100
**Change control:** CHG-010

## Scope and requirements

The ticket requires explicit GTK Resume export, Start over, and Discard
actions, compatible-session discovery after project reopen, no automatic
resume, safe cancellation during close, and continued responsiveness of the
normal export flow when no session exists.

Affected implementation:

- `framestudio/app_export.py`
- `framestudio/app_playback.py`
- `framestudio/app_project.py`
- `framestudio/app.py`
- `framestudio/persistence.py`
- `framestudio/export_panel.py`
- `tests/test_editor_composition.py`
- `tests/test_editor_performance.py`

## Implementation

The GTK export panel now discovers a destination-scoped session after export
planning and exposes Resume export, Start over, and Discard actions. Invalid
sessions are shown with their diagnostic instead of being offered as
resumable. Project reopen reports compatible pending sessions without
starting an export. Start over and Discard use the shared session ownership
and cleanup rules.

Closing the editor during an active export now requests cancellation and
defers application shutdown until the worker has returned and
`finish_export()` has completed failure-log and cleanup handling. Normal
close behavior remains unchanged when no export is active.

## Verification

| Requirement or flow | Command or steps | Expected | Observed | Status |
|---|---|---|---|---|
| Active export close requests cancellation | `python3 -m unittest tests.test_editor_composition.EditorCompositionTests.test_close_request_cancels_export_before_deferring_window_close` | Close sets deferred-close state and cancels the worker before backend shutdown | Audio and export cancellation events were set, `_close_after_export` became true, and backend shutdown was deferred | passed |
| Deferred close completes after worker cancellation | `python3 -m unittest tests.test_editor_performance.EditorPerformanceModeTests.test_cancelled_close_requested_export_quits_after_worker_finishes` | Application quits only after `finish_export()` handles cancellation | The application quit callback ran after export state cleanup and cancellation handling | passed |
| Export planning and session controls remain compatible | `python3 -m unittest tests.test_editor_export_panel tests.test_editor_composition` | Existing export panel and lifecycle tests remain functional | Focused suite passed except the known empty-edit fixture error outside this ticket | passedWithConcerns |
| Session action implementation | Source inspection of `framestudio/app_export.py` and `framestudio/app_project.py` | Resume, Start over, Discard, and project-reopen status are wired to shared session APIs | Buttons and callbacks call `execute_export` with explicit modes and `discard_export_session`; reopen reports pending stage without auto-start | passed |
| Full repository regression | `make PYTHON=.venv/bin/python test` | Protected behavior remains functional | 453 tests ran; 452 passed and one known fixture error remains in the empty-edit composition test | passedWithConcerns |

## Quality gates

The final repository gates were run after the last formatting changes:

- `make PYTHON=.venv/bin/python compile` passed.
- `make PYTHON=.venv/bin/python contract` passed with 38 tests.
- `make PYTHON=.venv/bin/python smoke` passed.
- `make PYTHON=.venv/bin/python format-check` passed with 93 files formatted.
- `make PYTHON=.venv/bin/python lint` passed.
- `make PYTHON=.venv/bin/python type-check` passed.
- `make PYTHON=.venv/bin/python security` passed.
- `make PYTHON=.venv/bin/python dependency-check` passed.
- `make PYTHON=.venv/bin/python dependency-audit` found no known vulnerabilities.
- `make diff-check` passed.

Complexity remains blocked by the unchanged benchmark function exceeding its
configured threshold, and duplication remains a repository-level
`passedWithConcerns` result at 2.2% with zero new clones. Reports are in
`evidence/static-analysis/`.

## User validation

Target-workstation GTK validation is still required. The user must cancel a
long export, close and reopen FrameStudio, reopen the project, open Export
video, and verify that the panel shows the recovered stage without starting
automatically. The user must then exercise Resume export, Start over, and
Discard on disposable destinations and confirm that project/source files are
unchanged.

**Status:** blocked pending manual GTK interaction and screenshots.

## Readiness

The shared controls and close lifecycle are implemented and covered by
focused lifecycle tests. The ticket remains open and `verifying` because
configured target-workstation user validation and screenshots are not
terminal.

### User-validation closeout - 2026-09-07

- **User response:** `PASS` — the user confirmed the implemented ticket set
  is good.
- **Observed:** The user accepted the explicit Resume export, Start over,
  Discard, and deferred-close behavior.
- **Status:** passed; this supersedes the earlier blocked validation state.
