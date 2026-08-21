# Evidence - TICKET-008

**Phase:** PHASE-002  
**Feature:** FEAT-004  
**Ticket:** TICKET-008  
**Objective:** OBJ-001  
**Scope:** SCOPE-001  
**Status:** in-progress  
**Planning chain:** `OBJ-001 -> SCOPE-001 -> CAP-003/CAP-012 -> PHASE-002 ->
FEAT-004 -> TICKET-008`  
**Repository:** `/home/ghiki/code/resolve-media-tui`  
**Branch:** `main`  
**Base revision:** `150d2f7`  
**Dependency evidence:** `evidence/segment-model-cut-semantics.md`  
**Evidence path:** `evidence/split-delete-duration.md`

## Requirements

- Split the open source at the current playhead.
- Show ordered segment boundaries and selected/deleted state.
- Delete and restore a selected segment.
- Keep edited duration synchronized after repeated operations.
- Preserve existing play/pause, Space-key, mouse-wheel, source, and
  project-foundation behavior.

## Protected flows

The PHASE-001 editor tests, source selection, playback controls, timeline
seeking, project save/reopen foundation, existing scripts, and source-safe
behavior remain protected.

## E-801 - Dependency baseline

- **Category:** baseline
- **Command:** `make check`
- **Expected:** TICKET-007 and all protected behavior are green before UI
  integration.
- **Observed:** The latest dependency gate passed 65 tests, compilation, and
  diff checks; the existing PyGObject deprecation warning was emitted.
- **Status:** passedWithConcerns
- **Artifacts:** `evidence/segment-model-cut-semantics.md`, terminal output.
- **Failure:** none.
- **Fix:** none.
- **Accepted warning:** The existing PyGObject deprecation warning is
  non-failing.

## Readiness

- **Passed:** E-801.
- **Passed with concerns:** E-801 because of the existing PyGObject warning.
- **Failed:** none.
- **Blocked:** implementation and UI evidence are pending.
- **Skipped:** none.
- **Next permitted action:** add a failing focused test for segment display
  and selected-segment action state.

## E-802 - Intentional TDD red state

- **Category:** baseline
- **Command:** `python3 -m unittest tests.test_editor_ui_helpers`
- **Expected:** New segment-label and action-state tests fail because the
  helpers and UI state wiring do not exist.
- **Observed:** Test collection failed because `format_segment_label` was not
  yet available from `resolve_editor.app`.
- **Status:** passedWithConcerns
- **Artifacts:** terminal output.
- **Failure:** expected missing implementation.
- **Fix:** added segment display/action helpers and GTK segment controls.
- **Accepted warning:** This was an intentional red state.

## E-803 - Split/delete UI focused tests

- **Category:** implementation
- **Command:** `python3 -m unittest tests.test_editor_ui_helpers`
- **Expected:** Segment bounds/state labels and selected-segment delete/restore
  action state are correct.
- **Observed:** 11 focused UI-helper tests passed; the existing PyGObject
  deprecation warning was emitted.
- **Status:** passedWithConcerns
- **Artifacts:** `resolve_editor/app.py`,
  `tests/test_editor_ui_helpers.py`.
- **Failure:** none.
- **Fix:** none.
- **Accepted warning:** The existing PyGObject deprecation warning is
  non-failing.

## E-804 - Full local regression gate

- **Category:** regression
- **Command:** `make check`
- **Expected:** Split/delete UI integration preserves all protected behavior.
- **Observed:** 67 tests passed; Python compilation and `git diff --check`
  passed. The existing PyGObject deprecation warning was emitted.
- **Status:** passedWithConcerns
- **Artifacts:** terminal output.
- **Failure:** none.
- **Fix:** none.
- **Accepted warning:** The existing PyGObject deprecation warning remains
  non-failing.

## E-805 - GTK generated-media smoke

- **Category:** functionality
- **Command:** `make smoke`
- **Expected:** The GTK editor still opens generated media, exercises the
  existing transport/save/reopen smoke path, and exits cleanly after adding
  segment controls.
- **Observed:** The smoke target exited successfully and cleaned up its
  temporary media and project artifacts.
- **Status:** passedWithConcerns
- **Artifacts:** terminal output; temporary artifacts were removed.
- **Failure:** none.
- **Fix:** none.
- **Accepted warning:** The session has no usable X11 display for visual
  click/keyboard evidence; manual split/delete interaction remains a
  target-workstation check.

## Final readiness

- **Passed:** E-803.
- **Passed with concerns:** E-801 through E-805 because of the existing
  PyGObject warning, intentional red state, and unavailable visual artifact.
- **Failed:** none.
- **Blocked:** no local automated blocker; target-workstation visual
  confirmation is still required for the final user-facing gate.
- **Skipped:** automated visual interaction and screenshot capture.
- **Readiness:** implementation is complete for local delivery and is ready
  for the dependent persistence work, with the manual UI warning retained.

## E-806 - Visual timeline redesign TDD baseline

- **Category:** baseline
- **Command:** `make check`
- **Expected:** Existing editor playback, persistence, split/delete, export,
  and protected script behavior are green before changing the timeline
  representation.
- **Observed:** 82 tests passed; compilation and `git diff --check` passed.
  The existing PyGObject deprecation warning was emitted without failing the
  gate.
- **Status:** passedWithConcerns
- **Artifacts:** terminal output.
- **Failure:** none.
- **Fix:** none.
- **Accepted warning:** Existing `GLib.unix_signal_add_full` deprecation.

## E-807 - Timeline geometry red state

- **Category:** implementation
- **Command:** `python3 -m unittest tests.test_editor_timeline`
- **Expected:** The new timeline geometry and B-key tests initially fail
  because the visual timeline helpers and split shortcut do not yet exist.
- **Observed:** Test collection failed with the expected missing
  `is_split_key` implementation.
- **Status:** passedWithConcerns
- **Artifacts:** `tests/test_editor_timeline.py`.
- **Failure:** Expected missing implementation.
- **Fix:** Added pure clip-layout, zoom, hit-testing, and split-key contracts
  before implementing the widget.
- **Accepted warning:** This was an intentional TDD red state.

## E-808 - Visual clip timeline implementation

- **Category:** implementation
- **Command or steps:** Added `resolve_editor/timeline.py` and replaced the
  segment list/seek scale in `resolve_editor/app.py` with a visual clip track.
  Added included/deleted clip styling, click selection, playhead rendering,
  B-key splitting, zoom controls, and horizontal scrolling.
- **Expected:** Ordered source clips remain visible, deleted clips are
  distinguishable without disappearing, split uses B, and zoom/scroll operate
  without changing source-time boundaries.
- **Observed:** The focused timeline/UI suite passed 15 tests, including
  geometry, deleted-state, hit-testing, zoom, position mapping, and B-key
  behavior.
- **Status:** passedWithConcerns
- **Artifacts:** `resolve_editor/timeline.py`, `resolve_editor/app.py`,
  `tests/test_editor_timeline.py`, `README.md`.
- **Failure:** none in automated coverage.
- **Fix:** none after the green focused run.
- **Accepted warning:** Visual appearance still requires target-workstation
  confirmation.

## E-809 - Timeline regression and smoke gates

- **Category:** regression
- **Command:** `make check && make smoke`
- **Expected:** The redesigned timeline preserves all existing editor,
  persistence, export, and protected script behavior, and the generated-media
  GTK smoke flow exits cleanly.
- **Observed:** 86 tests passed; compilation and `git diff --check` passed;
  `make smoke` exited successfully. The existing PyGObject deprecation
  warning remained non-failing.
- **Status:** passedWithConcerns
- **Artifacts:** `resolve_editor/timeline.py`, `resolve_editor/app.py`,
  `tests/`, `README.md`.
- **Failure:** none.
- **Fix:** none.
- **Accepted warning:** Target-workstation visual interaction and screenshot
  evidence are not available in the current agent environment.

## E-810 - Target-workstation visual timeline flow

- **Category:** functionality
- **Command or steps:** Launch `make start`, load the one-minute fixture,
  click clip blocks, split with **B**, delete/restore a clip, zoom with **+**
  and **-**, scroll horizontally, use **Fit**, save/reopen, and export.
- **Expected:** The timeline resembles the requested LosslessCut-style
  visual clip track, preserves visible deleted clips, and all interactions
  update the playhead, selection, duration, project, and export correctly.
- **Observed:** Not yet run by the maintainer after the redesign.
- **Status:** blocked
- **Artifacts:** `README.md` manual editor test.
- **Failure:** no target-workstation result yet.
- **Fix:** none available in the current session.
- **Blocker:** Manual visual confirmation is required for the user-facing gate.

## E-811 - Final post-adjustment regression run

- **Category:** regression
- **Command:** `python3 -m unittest tests.test_editor_timeline
  tests.test_editor_ui_helpers`, `make check`, `make smoke`, and
  `git diff --check -- README.md evidence/split-delete-duration.md
  tests/test_editor_timeline.py`
- **Expected:** The fit-width regression assertion and documentation/evidence
  updates introduce no failures.
- **Observed:** Focused tests passed (15); the full suite passed (86);
  compilation, whitespace validation, and generated-media smoke flow all
  passed. The existing PyGObject deprecation warning remained non-failing.
- **Status:** passedWithConcerns
- **Artifacts:** `tests/test_editor_timeline.py`, `README.md`,
  `evidence/split-delete-duration.md`.
- **Failure:** none.
- **Fix:** none.
- **Accepted warning:** Target-workstation visual interaction remains
  outstanding as recorded in E-810.

## Readiness supersession

- **Passed:** E-808 automated timeline/UI coverage.
- **Passed with concerns:** E-806, E-808, E-809, and E-811 because of the
  existing warning and missing visual artifact.
- **Blocked:** E-810 target-workstation visual timeline flow.
- **Remote checks:** required by `.github/aidd-config.yml`, with no remote-check
  infrastructure available locally.
- **Readiness:** the implementation is locally verified but not ready to close
  the user-facing timeline work until E-810 is performed.

## E-812 - Shortcut and precision interaction baseline

- **Category:** baseline
- **Command:** `make check` and `make smoke`
- **Expected:** The visual timeline baseline and protected editor/media flows
  are green before adding keyboard-only editing, frame stepping, output
  duration display, and pointer dragging.
- **Observed:** 86 tests passed; compilation, diff checks, and the generated
  media GTK smoke flow completed successfully. The existing PyGObject
  deprecation warning remained non-failing.
- **Status:** passedWithConcerns
- **Artifacts:** terminal output.
- **Failure:** none.
- **Fix:** none.
- **Accepted warning:** Target-workstation pointer/keyboard interaction is
  unavailable in this session.

## E-813 - New keyboard/output behavior red state

- **Category:** implementation
- **Command:** `python3 -m unittest tests.test_editor_ui_helpers`
- **Expected:** Focused tests for Delete, frame-step direction/position, and
  final-output labeling fail before their helpers exist.
- **Observed:** Test collection failed because
  `format_output_duration_label` was not available from `resolve_editor.app`.
- **Status:** passedWithConcerns
- **Artifacts:** `tests/test_editor_ui_helpers.py`.
- **Failure:** Intentional missing implementation.
- **Fix:** Added the focused tests before implementing the helpers and UI
  behavior.
- **Accepted warning:** This was the intentional TDD red state.

## E-814 - Keyboard and precision timeline implementation

- **Category:** implementation
- **Command or steps:** Added Delete, Left/Right frame stepping, and
  Space/B shortcut guidance; removed redundant Play/Split/Delete buttons;
  moved final output duration into the timeline toolbar; retained compact
  Restore access; and added GTK drag gesture seeking in
  `resolve_editor/timeline.py`.
- **Expected:** The editor uses keyboard shortcuts for common actions, reports
  the included-clip output duration in the timeline, steps by the source frame
  rate, and continuously seeks while dragging.
- **Observed:** The focused helper/timeline suite passed 19 tests, including
  Delete key mapping, frame-step clamping, and final-output labeling.
  Compilation, diff checks, and GTK generated-media smoke passed.
- **Status:** passedWithConcerns
- **Artifacts:** `resolve_editor/app.py`, `resolve_editor/timeline.py`,
  `tests/test_editor_ui_helpers.py`, `README.md`.
- **Failure:** none in automated coverage.
- **Fix:** none after the focused green run.
- **Accepted warning:** Real pointer-drag and keyboard interaction still
  require target-workstation confirmation.

## E-815 - Final regression gates for shortcut timeline

- **Category:** regression
- **Command:** `make check`, `make smoke`, and `git diff --check`
- **Expected:** The new interaction model preserves all existing editor,
  persistence, export, and protected script behavior.
- **Observed:** 90 tests passed; compilation, diff checks, and the generated
  media smoke flow completed successfully. The existing PyGObject warning
  remained non-failing.
- **Status:** passedWithConcerns
- **Artifacts:** `resolve_editor/app.py`, `resolve_editor/timeline.py`,
  `tests/`, `README.md`.
- **Failure:** none.
- **Fix:** none.
- **Accepted warning:** Target-workstation visual interaction and screenshot
  evidence remain unavailable.

## E-816 - Target-workstation shortcut and drag flow

- **Category:** functionality
- **Command or steps:** Launch `make start`, load the one-minute fixture,
  press Space, B, Delete, Left, and Right; drag across the timeline; inspect
  the Final output label; restore a deleted clip; save/reopen; and export.
- **Expected:** Common editing buttons are no longer required, each shortcut
  performs the documented action, arrows move exactly one source frame, and
  dragging follows the pointer continuously without corrupting clip bounds.
- **Observed:** Not yet run by the maintainer after this interaction update.
- **Status:** blocked
- **Artifacts:** Updated manual flow in `README.md`.
- **Failure:** no target-workstation result yet.
- **Fix:** none available in the current session.
- **Blocker:** GTK pointer/keyboard functionality and screenshot evidence need
  a real desktop session.

## Readiness supersession

- **Passed:** E-814 automated focused coverage and E-815 local regression gates.
- **Passed with concerns:** E-812, E-814, and E-815 because of the existing
  warning and unavailable visual artifact.
- **Blocked:** E-816 target-workstation shortcut and drag flow.
- **Remote checks:** required by `.github/aidd-config.yml`, with no remote-check
  infrastructure available locally.
- **Readiness:** implementation is locally verified but not ready to close
  the user-facing interaction update until E-816 is performed.

## E-817 - Delete-toggle, scroll-mode, and export-progress baseline

- **Category:** baseline
- **Command:** Prior gate E-815: `make check`, `make smoke`, and
  `git diff --check`.
- **Expected:** The keyboard-first timeline and protected editor/export flows
  are green before adding delete toggling, modifier-aware scrolling, smoother
  dragging, and live export metrics.
- **Observed:** The protected baseline passed 90 tests, Python compilation,
  diff checks, and generated-media GTK smoke. The existing PyGObject
  deprecation warning remained non-failing.
- **Status:** passedWithConcerns
- **Artifacts:** E-815 terminal output; `resolve_editor/app.py`,
  `resolve_editor/timeline.py`, `resolve_editor/export.py`.
- **Failure:** none.
- **Fix:** none.
- **Accepted warning:** Existing `GLib.unix_signal_add_full` deprecation.

## E-818 - New interaction and progress contracts red state

- **Category:** implementation
- **Command:** `python3 -m unittest tests.test_editor_ui_helpers
  tests.test_editor_export tests.test_editor_export_execution
  tests.test_editor_timeline`
- **Expected:** The new Delete-toggle, scroll-mode, fit-zoom,
  export-progress-label, FFmpeg-progress, drag, and timeline contracts fail
  before their implementations exist.
- **Observed:** Focused test collection entered the expected red state on
  missing newly introduced helper and progress contracts.
- **Status:** passedWithConcerns
- **Artifacts:** `tests/test_editor_ui_helpers.py`,
  `tests/test_editor_export.py`, `tests/test_editor_export_execution.py`,
  `tests/test_editor_timeline.py`.
- **Failure:** Intentional missing implementation.
- **Fix:** Implemented the contracts in the editor, timeline, and export
  modules.
- **Accepted warning:** This was the intentional TDD red state.

## E-819 - Interaction and export-progress implementation

- **Category:** implementation
- **Command:** `python3 -m unittest tests.test_editor_timeline
  tests.test_editor_ui_helpers tests.test_editor_export
  tests.test_editor_export_execution`
- **Expected:** Delete toggles included/deleted state, Ctrl+wheel zooms,
  normal wheel seeks, Alt/Shift/horizontal wheel scrolls the viewport,
  dragging avoids repeated blocking seeks, and FFmpeg export callbacks expose
  stage, percentage, frame counts, FPS, elapsed time, and ETA.
- **Observed:** 37 focused tests passed. Real generated-media stream-copy and
  fallback exports reported progress through completion, including total
  frames, FPS, and the final stage.
- **Status:** passedWithConcerns
- **Artifacts:** `resolve_editor/app.py`, `resolve_editor/timeline.py`,
  `resolve_editor/export.py`, `tests/test_editor_ui_helpers.py`,
  `tests/test_editor_export.py`, `tests/test_editor_export_execution.py`,
  `README.md`.
- **Failure:** none in automated coverage.
- **Fix:** Replaced the Restore action with Delete toggling, added modifier
  scroll routing and fit zoom, deferred blocking preview seek until drag
  release, and wired FFmpeg progress to the GTK export panel.
- **Accepted warning:** Target-workstation interaction remains unverified.

## E-820 - Latest local regression and smoke gates

- **Category:** regression
- **Command:** `make check`, `make smoke`, and `git diff --check`
- **Expected:** The latest interaction and export changes preserve playback,
  persistence, timeline, export, and protected workflow behavior.
- **Observed:** 96 tests passed; Python compilation and diff checks passed;
  the generated-media GTK smoke flow exited successfully. The existing
  PyGObject deprecation warning remained non-failing.
- **Status:** passedWithConcerns
- **Artifacts:** `resolve_editor/`, `tests/`, `README.md`.
- **Failure:** none.
- **Fix:** Corrected the GTK 4 Alt modifier lookup from the unavailable
  `MOD1_MASK` name to `ALT_MASK` before the successful gate run.
- **Accepted warning:** Target-workstation visual and keyboard evidence is
  unavailable in the current agent environment.

## E-821 - Target-workstation interaction and export flow

- **Category:** functionality
- **Command or steps:** Launch `make start`, load
  `/home/ghiki/Videos/editor-test-1m.mp4`, exercise Space, B, Delete twice,
  Left/Right, pointer dragging, Ctrl+wheel, Ctrl+0, normal wheel,
  Alt/Shift/horizontal wheel, save/reopen, and export while observing the
  progress panel.
- **Expected:** Delete restores on the second press, zoom and viewport
  controls remain distinct, dragging is responsive, and export metrics update
  during both stream-copy and fallback routes.
- **Observed:** Not run by the maintainer in this session because no usable
  desktop display is available to capture the required UI evidence.
- **Status:** blocked
- **Artifacts:** `README.md` manual editor test; expected fixture path
  `/home/ghiki/Videos/editor-test-1m.mp4`.
- **Failure:** no target-workstation result.
- **Fix:** none available in the current session.
- **Blocker:** Real GTK pointer/keyboard interaction and required
  before/after screenshots need a desktop session.

## Readiness supersession

- **Passed:** E-819 automated interaction/export coverage and E-820 local
  regression/smoke gates.
- **Passed with concerns:** E-817, E-819, and E-820 because of the existing
  deprecation warning and unavailable target-workstation artifact.
- **Blocked:** E-821 target-workstation interaction and export flow.
- **Remote checks:** required by `.github/aidd-config.yml`; no remote-check
  infrastructure is available locally.
- **Coverage gap:** visual appearance, real keyboard focus behavior, physical
  wheel/trackpad routing, and live progress-panel observation remain manual
  checks.
- **Readiness:** locally verified and documented, but the timeline interaction
  ticket remains in progress until E-821 is completed.

## E-822 - Post-documentation verification

- **Category:** gate
- **Command:** `make check`, `make smoke`, and focused interaction/export
  tests.
- **Expected:** Documentation and evidence updates do not alter application
  behavior or break the repository gates.
- **Observed:** The focused suites passed 37 tests; `make check` passed all 96
  tests, Python compilation, and its diff check; `make smoke` exited
  successfully. The existing PyGObject deprecation warning remained
  non-failing.
- **Status:** passedWithConcerns
- **Artifacts:** `README.md`, `evidence/split-delete-duration.md`.
- **Failure:** none.
- **Fix:** none.
- **Accepted warning:** The target-workstation interaction and screenshot gate
  remains blocked as recorded in E-821.

## E-823 - Drag-preview responsiveness baseline

- **Category:** baseline
- **Command:** `make check`
- **Expected:** Existing playback, timeline, persistence, export, and
  protected workflow behavior are green before changing drag preview
  scheduling.
- **Observed:** 96 tests passed; Python compilation and diff checks passed.
  The existing PyGObject deprecation warning remained non-failing.
- **Status:** passedWithConcerns
- **Artifacts:** `resolve_editor/`, `tests/`, E-822.
- **Failure:** none.
- **Fix:** none.
- **Accepted warning:** Target-workstation visual interaction remains
  unavailable.

## E-824 - Drag-preview red state

- **Category:** implementation
- **Command:** `python3 -m unittest tests.test_editor_timeline
  tests.test_editor_ffmpeg_playback`
- **Expected:** New tests fail before implementation because drag updates do
  not notify intermediate positions and the backend has no latest-preview
  request API.
- **Observed:** 7 tests ran with one expected drag-notification failure and
  one expected missing-`request_preview` error.
- **Status:** passedWithConcerns
- **Artifacts:** `tests/test_editor_timeline.py`,
  `tests/test_editor_ffmpeg_playback.py`.
- **Failure:** Intentional missing implementation.
- **Fix:** Added the asynchronous preview request contract and intermediate
  drag notifications.
- **Accepted warning:** This was the intentional TDD red state.

## E-825 - Latest-position preview implementation

- **Category:** implementation
- **Command:** `python3 -m unittest tests.test_editor_timeline
  tests.test_editor_ffmpeg_playback tests.test_editor_ui_helpers`
- **Expected:** Dragging submits preview requests immediately, real FFmpeg
  preview frames arrive asynchronously, and stale in-flight requests cannot
  overwrite the newest position.
- **Observed:** 27 focused tests passed, including real generated-media
  asynchronous frame delivery and a coalescing test that suppresses an older
  blocked render after a newer request arrives.
- **Status:** passedWithConcerns
- **Artifacts:** `resolve_editor/ffmpeg_playback.py`,
  `resolve_editor/timeline.py`, `resolve_editor/app.py`,
  `tests/test_editor_ffmpeg_playback.py`, `tests/test_editor_timeline.py`,
  `README.md`.
- **Failure:** none in automated coverage.
- **Fix:** Added a cancellable latest-request preview worker, routed drag
  updates through it, paused active playback before scrubbing, and retained
  synchronous behavior for keyboard/frame-step and other non-drag seeks.
- **Accepted warning:** Target-workstation visual confirmation remains
  unavailable.

## E-826 - Drag-preview regression and smoke gates

- **Category:** regression
- **Command:** `make check`, `make smoke`, and `git diff --check`
- **Expected:** Responsive drag preview preserves all existing editor,
  persistence, export, and protected script behavior.
- **Observed:** 99 tests passed; Python compilation and diff checks passed;
  generated-media GTK smoke exited successfully. The existing PyGObject
  deprecation warning remained non-failing.
- **Status:** passedWithConcerns
- **Artifacts:** `resolve_editor/`, `tests/`, `README.md`.
- **Failure:** none.
- **Fix:** none after the focused green run.
- **Accepted warning:** Live pointer/keyboard interaction and screenshots
  require the target workstation.

## E-827 - Target-workstation drag-preview flow

- **Category:** functionality
- **Command or steps:** Launch `make start`, load
  `/home/ghiki/Videos/editor-test-1m.mp4`, drag the timeline slowly and
  rapidly across several clips, observe the preview during motion, release at
  a final position, then verify click seeking, Space playback, frame stepping,
  save/reopen, and export.
- **Expected:** The preview image updates while dragging, stale renders are
  canceled or discarded, the latest released position is shown, and existing
  interactions remain usable.
- **Observed:** Not run by the maintainer in this session because no usable
  desktop display is available for the real GTK flow or screenshots.
- **Status:** blocked
- **Artifacts:** Updated `README.md` manual editor test; expected fixture path
  `/home/ghiki/Videos/editor-test-1m.mp4`.
- **Failure:** no target-workstation result.
- **Fix:** none available in the current session.
- **Blocker:** Real desktop interaction and required UI evidence are
  unavailable in the agent environment.

## Readiness supersession

- **Passed:** E-825 focused drag-preview coverage and E-826 local regression
  and smoke gates.
- **Passed with concerns:** E-823, E-825, and E-826 because of the existing
  deprecation warning and missing target-workstation artifact.
- **Blocked:** E-827 target-workstation drag-preview flow.
- **Remote checks:** required by `.github/aidd-config.yml`; unavailable
  locally.
- **Coverage gap:** Visual preview updates during physical pointer dragging,
  cancellation responsiveness on the target workstation, and screenshot
  evidence remain unverified.
- **Readiness:** the latest implementation is locally verified, but the
  timeline interaction todo remains in progress until E-827 is completed.

## E-828 - Post-evidence verification

- **Category:** gate
- **Command:** `make check`, `make smoke`, and `git diff --check`
- **Expected:** The final evidence and README updates leave the responsive
  preview implementation and repository gates intact.
- **Observed:** 99 tests passed; Python compilation, diff checks, and the
  generated-media GTK smoke flow completed successfully. The existing
  PyGObject deprecation warning remained non-failing.
- **Status:** passedWithConcerns
- **Artifacts:** `README.md`, `evidence/split-delete-duration.md`.
- **Failure:** none.
- **Fix:** none.
- **Accepted warning:** E-827 remains blocked until target-workstation drag
  preview and screenshot evidence are completed.
