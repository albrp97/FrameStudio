# Evidence - TICKET-001

**Phase:** PHASE-001
**Feature:** FEAT-001
**Ticket:** TICKET-001
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Status:** passedWithConcerns
**Repository:** `resolve-media-tui`
**Branch:** `main`
**Base revision:** `150d2f7`
**Evidence path:** `evidence/selecting-editor-foundation.md`
**Decision artifact:** `docs/specs/editor-foundation-decision.md`

## Planning chain

`OBJ-001 -> SCOPE-001 -> CAP-MAP-001 -> PHASE-001 -> FEAT-001 ->
TICKET-001`

## Requirements covered

- Select an evidence-backed Linux GUI/runtime and playback approach.
- Define the one-source project/source contract and missing/moved-source
  behavior.
- Define the local setup and target-workstation manual smoke path.
- Preserve existing scripts, commands, tests, and source-safe behavior.

## Baseline and environment

### E-001 - Protected baseline

- **Category:** baseline
- **Command:** `python3 -m unittest discover -s tests`
- **Expected:** Existing regression suite passes without editor changes.
- **Observed:** 34 tests ran and passed in 0.335s.
- **Status:** passed
- **Artifacts:** terminal output from the baseline command.
- **Failure:** none
- **Fix:** none

### E-002 - Target runtime inventory

- **Category:** planning
- **Commands:**
  - `python3 --version`
  - `ffmpeg -version | head -1`
  - `ffprobe -version | head -1`
  - Python module availability probe for `gi`, `tkinter`, `PyQt6`,
    `PySide6`, `av`, and `cv2`
  - GTK 3/4 and GStreamer 1.0 introspection probes
  - `gst-inspect-1.0` probes for playback and GTK-compatible sinks
  - `mpv --version`, `ffplay -version`, and `gst-launch-1.0 --version`
- **Expected:** Identify a locally available, testable GUI and playback path.
- **Observed:** Python 3.14.7, FFmpeg/ffprobe n9.0.1, GTK 4.22, GTK 3.24,
  GStreamer 1.28.6, PyGObject, GStreamer video bindings, mpv, ffplay, and
  gst-launch are available. Qt bindings, PyAV, and OpenCV are absent.
  `gtksink`, `gtk4paintablesink`, and `gtkglsink` are absent. Tk import
  fails at runtime because `libtk8.6.so` is unavailable.
- **Status:** passedWithConcerns
- **Artifacts:** `docs/specs/editor-foundation-decision.md`
- **Failure:** native GTK GStreamer sinks and Tk runtime are unavailable.
- **Fix:** Use GStreamer `appsink` with GTK 4 `Gdk.MemoryTexture` presentation.
- **Accepted warning:** The initial preview uses CPU-visible frame transfer
  and must record dropped-frame or seek limitations during the smoke test.

### E-003 - Playback candidate probe

- **Category:** functionality
- **Command:** Generated a one-second 320x180 H.264 MP4 with FFmpeg and
  attempted a GStreamer `playbin` plus `appsink` decode, then attempted a
  managed FFmpeg rawvideo pipe.
- **Expected:** A candidate playback path should decode a frame from a common
  local video without an unreported dependency failure.
- **Observed:** GStreamer reached a missing-plugin error for QuickTime/MP4
  (`qtdemux` was unavailable). The FFmpeg rawvideo pipe produced one complete
  320x180 RGBA frame (230400 bytes).
- **Status:** passedWithConcerns
- **Artifacts:** `docs/specs/editor-foundation-decision.md`
- **Failure:** GStreamer `playbin` cannot decode the generated MP4 on this
  workstation with the installed plugin set.
- **Fix:** Select a managed FFmpeg frame pipe for the initial playback
  backend; retain GStreamer as a future optional backend after plugin
  availability is addressed.
- **Accepted warning:** The selected preview transfers frames through Python
  memory and does not yet provide audio playback.

### E-004 - Initial editor test red state

- **Category:** baseline
- **Command:** `python3 -m unittest tests.test_editor_model
  tests.test_editor_media tests.test_editor_persistence
  tests.test_editor_playback tests.test_editor_ui_helpers`
- **Expected:** The new isolated editor tests fail before the implementation
  exists, for the intended missing-module reason.
- **Observed:** Five test modules failed to import because the
  `framestudio` package did not yet exist.
- **Status:** passedWithConcerns
- **Artifacts:** terminal output from the focused test command.
- **Failure:** editor implementation modules were not present.
- **Fix:** Begin the implementation with the tested domain contracts below.
- **Accepted warning:** This is an intentional TDD red state, not a
  regression in the protected suite.

### E-005 - Foundation implementation smoke flow

- **Category:** functionality
- **Commands:** Generate a local 320x180 H.264 MP4 with FFmpeg, then run:
  `python3 framestudio.py --source <fixture> --smoke-test
  --smoke-project <project>` and
  `python3 framestudio.py --project <project> --smoke-test`.
- **Expected:** The editor opens the source/project, exercises play, pause,
  seek, save, and project reopen, then exits cleanly.
- **Observed:** Both smoke runs exited successfully and the saved JSON
  contained schema version 1 with a bounded playhead.
- **Status:** passedWithConcerns
- **Artifacts:** generated project was temporary and removed; no private media
  was retained.
- **Failure:** no automated audio-preview check is available.
- **Fix:** none required for the ticket scope.
- **Accepted warning:** The smoke path validates GTK application logic and
  preview lifecycle but does not provide visual screenshot evidence.

### E-006 - UI screenshot gate

- **Category:** gate
- **Steps:** Attempted to locate the editor window through X11 and capture a
  window screenshot with ImageMagick `import`.
- **Expected:** A target-workstation screenshot should be captured for the
  configured UI evidence gate.
- **Observed:** `xdpyinfo` and X11 window discovery failed for the configured
  `DISPLAY=:0`; no screenshot could be safely captured.
- **Status:** skippedWithReason
- **Artifacts:** none
- **Failure:** the current session has no usable X11 display/window manager.
- **Fix:** none; rerun the screenshot step in a graphical workstation session.
- **Accepted warning:** The UI gate remains an environment coverage gap and
  prevents a full delivery-readiness claim.

### E-007 - Foundation implementation and quality closeout

- **Category:** implementation
- **Commands:**
  - `python3 -m unittest discover -s tests`
  - `python3 -m py_compile framestudio.py framestudio/*.py
    tests/test_editor_*.py`
  - `git diff --check`
- **Expected:** The selected foundation is implemented without regressing
  protected workflows or introducing syntax/whitespace failures.
- **Observed:** 50 tests passed; Python compilation passed; diff checks passed.
  Downstream evidence records cover source opening, playback, preview,
  persistence, and save/reopen integration.
- **Status:** passedWithConcerns
- **Artifacts:** `evidence/open-supported-source-project.md`,
  `evidence/playback-control-state.md`,
  `evidence/preview-timeline-interaction.md`,
  `evidence/versioned-project-persistence.md`,
  `evidence/save-reopen-recovery.md`
- **Failure:** target-workstation X11 screenshot/manual interaction evidence
  remains unavailable in this session.
- **Fix:** none; rerun the user-facing gate on a graphical workstation.
- **Accepted warning:** No audio preview is claimed in this foundation.

## Decision

DECISION-001 selects Python/PyGObject, GTK 4, a managed FFmpeg raw-frame
playback process, and the existing FFmpeg/ffprobe commands. The one-source
JSON contract, explicit missing-source behavior, atomic persistence contract,
and manual validation path are recorded in
`docs/specs/editor-foundation-decision.md`.

## Open evidence

- Target-workstation visual/manual UI evidence remains unavailable because
  this session has no usable X11 display.

## Protected flows

- Existing `framestudio_media.py`, `framestudio_concat.py`, and `framestudio_fps.py`
  command behavior.
- Existing unittest coverage and safe partial-output behavior.
- Original source media remains untouched.

## Readiness

The foundation decision and implementation evidence are complete with an
accepted concern for the unavailable workstation UI gate. TICKET-002,
TICKET-003, and TICKET-005 have terminal implementation evidence; TICKET-004
and TICKET-006 remain blocked only by the target-workstation user-facing gate.

- **Passed:** E-001.
- **Passed with concerns:** E-002, E-003, E-004, E-005, and E-007.
- **Failed:** none.
- **Blocked:** downstream user-facing readiness remains blocked by the
  unavailable workstation gate.
- **Skipped:** E-006 screenshot capture.
- **Artifacts:** `docs/specs/editor-foundation-decision.md` and the five
  downstream evidence records.

## E-008 - User-confirmed target-workstation acceptance

- **Category:** user-facing
- **Steps:** The user manually launched and checked the editor workflow on
  the target workstation.
- **Expected:** The previously unavailable visual/manual UI gate can be
  unblocked after the user's real-workstation check.
- **Observed:** User confirmation: “okay done and checked. i think we can
  unblock the not implemented tickets /aidd-tdd”.
- **Status:** passedWithConcerns
- **Artifacts:** none retained.
- **Failure:** no screenshot or detailed manual step log was supplied.
- **Fix:** supersedes the environment blocker for downstream ticket status.
- **Accepted warning:** The acceptance is based on direct user confirmation
  without a retained visual artifact.

## Superseding readiness

- **Passed:** E-001.
- **Passed with concerns:** E-002, E-003, E-004, E-005, E-007, and E-008
  because the final UI artifact was not retained.
- **Failed:** none.
- **Blocked:** none for PHASE-001 ticket dependencies after user acceptance.
- **Skipped:** agent-side screenshot capture remains unavailable.
