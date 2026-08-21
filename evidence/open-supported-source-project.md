# Evidence - TICKET-002

**Phase:** PHASE-001
**Feature:** FEAT-001
**Ticket:** TICKET-002
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Status:** passedWithConcerns
**Planning chain:** `OBJ-001 -> SCOPE-001 -> CAP-001/CAP-012 -> PHASE-001 ->
FEAT-001 -> TICKET-002`
**Source references:** `resolve_editor/media.py`,
`resolve_editor/model.py`, `resolve_editor/app.py`,
`tests/test_editor_media.py`, `tests/test_editor_model.py`
**Evidence path:** `evidence/open-supported-source-project.md`

## E-201 - Source and project focused tests

- **Category:** implementation
- **Command:** `python3 -m unittest tests.test_editor_media
  tests.test_editor_model`
- **Expected:** Supported metadata maps into a one-source project and missing,
  invalid, and unsupported source states are explicit.
- **Observed:** 7 tests ran and passed.
- **Status:** passed
- **Artifacts:** focused unittest output.
- **Failure:** none
- **Fix:** none

## E-202 - Full regression suite

- **Category:** regression
- **Command:** `python3 -m unittest discover -s tests`
- **Expected:** Existing workflows and new editor tests remain green.
- **Observed:** 50 tests ran and passed.
- **Status:** passed
- **Artifacts:** full unittest output.
- **Failure:** none
- **Fix:** none

## E-203 - Real source-opening smoke flow

- **Category:** functionality
- **Steps:** Generate a temporary 320x180 H.264 MP4 with FFmpeg and run
  `python3 resolve_editor.py --source <fixture> --smoke-test
  --smoke-project <project>`.
- **Expected:** The editor probes the source, creates a project, initializes
  the preview, and writes valid project state.
- **Observed:** The command exited successfully and wrote schema version 1
  JSON with a bounded playhead.
- **Status:** passedWithConcerns
- **Artifacts:** temporary fixture and project were removed after the run.
- **Failure:** no persistent-media test was retained.
- **Fix:** none
- **Accepted warning:** The session could not provide visual screenshot
  evidence because the configured X11 display was unavailable.

## Protected flows

Existing media-preparation commands, scripts, tests, and original source
preservation remain unchanged.

## Readiness

The source-opening implementation is complete and covered by focused,
regression, and generated-media evidence.

- **Passed:** E-201 and E-202.
- **Passed with concerns:** E-203.
- **Failed:** none.
- **Blocked:** none for source opening.
- **Skipped:** target-workstation visual UI evidence; the environment has no
  usable X11 display.
- **Open coverage gap:** visual/manual UI evidence is recorded in
  `evidence/preview-timeline-interaction.md`.
