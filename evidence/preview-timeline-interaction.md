# Evidence - TICKET-004

**Phase:** PHASE-001
**Feature:** FEAT-002
**Ticket:** TICKET-004
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Status:** passedWithConcerns
**Planning chain:** `OBJ-001 -> SCOPE-001 -> CAP-002/CAP-012 -> PHASE-001 ->
FEAT-002 -> TICKET-004`
**Source references:** `framestudio/app.py`, `framestudio/ui.py`,
`framestudio.py`, `tests/test_editor_ui_helpers.py`
**Evidence path:** `evidence/preview-timeline-interaction.md`

## E-401 - Editor startup and source preview smoke

- **Category:** functionality
- **Steps:** Generate a temporary MP4 and run
  `python3 framestudio.py --source <fixture> --smoke-test
  --smoke-project <project>`.
- **Expected:** The primary GTK application opens the source, initializes
  preview/timeline state, exercises play, pause, and seek, and exits.
- **Observed:** The smoke command exited successfully and produced valid
  project state after the playback and seek sequence.
- **Status:** passedWithConcerns
- **Artifacts:** temporary fixture/project removed after the run.
- **Failure:** no independent visual interaction harness was available.
- **Fix:** none
- **Accepted warning:** The smoke path validates application callbacks and
  backend lifecycle but cannot assess subjective visual smoothness.

## E-402 - Project reopen preview smoke

- **Category:** functionality
- **Steps:** Run
  `python3 framestudio.py --project <project> --smoke-test` against the
  project produced by E-401.
- **Expected:** The saved source and playhead reopen and the preview lifecycle
  remains usable.
- **Observed:** The command exited successfully.
- **Status:** passed
- **Artifacts:** temporary project removed after the run.
- **Failure:** none
- **Fix:** none

## E-403 - UI screenshot gate

- **Category:** gate
- **Steps:** Attempt X11 window discovery and ImageMagick `import` capture.
- **Expected:** A screenshot is available at the configured UI evidence path.
- **Observed:** `xdpyinfo` and X11 window discovery failed for
  `DISPLAY=:0`; no screenshot was captured.
- **Status:** skippedWithReason
- **Artifacts:** none
- **Failure:** no usable X11 display/window manager in this session.
- **Fix:** none; rerun in a graphical workstation session.
- **Blocker:** The configured visual UI gate remains incomplete.

## Protected flows

Existing command names, curses workflows, media scripts, and tests remain
available and unchanged.

## Readiness

The preview/timeline implementation and callback smoke flow are complete, but
the configured visual screenshot gate is an environment coverage gap.

- **Passed:** E-402.
- **Passed with concerns:** E-401.
- **Failed:** none.
- **Blocked:** E-403 blocks the required target-workstation UI gate.
- **Skipped:** screenshot capture and independent manual interaction because
  X11 is unavailable.
- **Artifacts:** `framestudio/app.py`, `framestudio/ui.py`, and this
  evidence record.

## E-404 - User-confirmed target-workstation interaction

- **Category:** user-facing
- **Steps:** The user launched the editor, exercised the documented preview,
  timeline, playback, and input interactions, and reported completion.
- **Expected:** The target-workstation preview/timeline flow is usable and the
  interaction gate can be unblocked.
- **Observed:** User confirmation: “okay done and checked. i think we can
  unblock the not implemented tickets /aidd-tdd”.
- **Status:** passedWithConcerns
- **Artifacts:** none retained.
- **Failure:** no screenshot or detailed manual step log was supplied.
- **Fix:** supersedes E-403 as the environment blocker for this ticket.
- **Accepted warning:** The result is based on direct user confirmation
  without a retained visual artifact.

## Superseding readiness

- **Passed:** E-402.
- **Passed with concerns:** E-401 and E-404 because no screenshot artifact
  was retained.
- **Failed:** none.
- **Blocked:** none after user confirmation.
- **Skipped:** screenshot capture remains unavailable in the agent session.
