# Evidence - Editor Start and Source Selection

**Ticket:** editor-start-selection
**Phase:** PHASE-001
**Feature:** FEAT-002
**Scope:** Add a simple `make start` entry point and an in-app source picker
that follows the approved phase limit.
**Method:** codeTdd and configuration verification
**Evidence path:** `evidence/editor-start-selection.md`

## Requirements

- `make start` launches the editor without requiring a source argument.
- The UI lets the user select local source video files from inside the app.
- PHASE-001 accepts one source per project.
- Selecting several sources is explicit and recoverable rather than silently
  discarding files.
- The selection helper can honor a larger limit when a later phase enables it.

## E-801 - Protected baseline

- **Category:** baseline
- **Command:** `python3 -m unittest discover -s tests`
- **Expected:** Existing behavior passes before the change.
- **Observed:** 50 tests ran and passed.
- **Status:** passed
- **Artifacts:** terminal output.
- **Failure:** none
- **Fix:** none

## E-802 - Intentional TDD red state

- **Category:** baseline
- **Command:** `python3 -m unittest tests.test_editor_ui_helpers`
- **Expected:** The new source-selection tests fail because the helper is not
  implemented yet.
- **Observed:** Import failed for the missing
  `resolve_editor.app.validate_source_selection` helper.
- **Status:** passedWithConcerns
- **Artifacts:** terminal output.
- **Failure:** expected missing implementation.
- **Fix:** implemented the phase-aware selection helper and UI integration.
- **Accepted warning:** This was an intentional red state, not a regression.

## E-803 - Focused green tests

- **Category:** implementation
- **Command:** `python3 -m unittest tests.test_editor_ui_helpers`
- **Expected:** One-source acceptance, multi-source rejection, configurable
  future capacity, duration formatting, and rational metadata handling pass.
- **Observed:** 5 tests ran and passed.
- **Status:** passed
- **Artifacts:** `tests/test_editor_ui_helpers.py`.
- **Failure:** none
- **Fix:** none

## E-804 - Start target and GTK API verification

- **Category:** configuration
- **Commands:** `make -n start`, `make help`, and a GTK introspection probe for
  `Gtk.FileDialog.open_multiple` and `open_multiple_finish`.
- **Expected:** `make start` delegates to the editor, help documents it, and
  the installed GTK version supports multi-file selection.
- **Observed:** `make start` resolves to `python3 resolve_editor.py`, the help
  target lists it, and both GTK APIs are available.
- **Status:** passed
- **Artifacts:** `Makefile`, `resolve_editor/app.py`, and `README.md`.
- **Failure:** none
- **Fix:** none

## E-805 - Full local quality gate

- **Category:** regression
- **Command:** `make check`
- **Expected:** Protected workflows, editor tests, compilation, and diff
  checks remain green.
- **Observed:** 53 tests ran and passed; compilation and diff checks passed.
- **Status:** passed
- **Artifacts:** terminal output.
- **Failure:** none
- **Fix:** none

## E-806 - Generated-media smoke flow

- **Category:** functionality
- **Command:** `make smoke`
- **Expected:** A generated source opens, playback/seek/save/reopen smoke
  logic completes, and temporary media/project files are removed.
- **Observed:** The target exited successfully and both known temporary paths
  were absent afterward.
- **Status:** passed
- **Artifacts:** temporary artifacts were cleaned up.
- **Failure:** none
- **Fix:** none

## Readiness

- **Passed:** E-801, E-803, E-804, E-805, and E-806.
- **Passed with concerns:** E-802.
- **Failed:** none.
- **Blocked:** visual/manual selection evidence remains blocked by the
  unavailable X11 workstation session.
- **Skipped:** actual mouse selection through `make start` in this session.
- **Scope warning:** Multi-source timeline behavior remains deferred; the UI
  reports the current one-source limit.

## E-807 - User-confirmed source-selection check

- **Category:** user-facing
- **Steps:** The user manually launched and checked the in-app start and source
  selection flow on the target workstation.
- **Expected:** The start/selection flow is usable and no longer blocks the
  PHASE-001 interface tickets.
- **Observed:** User confirmation: “okay done and checked. i think we can
  unblock the not implemented tickets /aidd-tdd”.
- **Status:** passedWithConcerns
- **Artifacts:** none retained.
- **Failure:** no screenshot or detailed manual step log was supplied.
- **Fix:** supersedes the session-level X11 availability gap for ticket
  dependency status.
- **Accepted warning:** Direct user confirmation is retained without a visual
  artifact.

## Superseding readiness

- **Passed:** none beyond the automated entries above.
- **Passed with concerns:** E-807.
- **Failed:** none.
- **Blocked:** none for PHASE-001 ticket dependencies after confirmation.
- **Skipped:** agent-side screenshot capture.
