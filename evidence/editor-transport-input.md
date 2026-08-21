# Evidence - Editor Transport Input

**Ticket:** editor-transport-input
**Phase:** PHASE-001
**Feature:** FEAT-002
**Scope:** Improve timeline hit area, mouse-wheel seeking, Space playback
toggle, and source/project labeling without expanding the one-source model.
**Method:** codeTdd and real-media smoke verification
**Evidence path:** `evidence/editor-transport-input.md`

## Requirements

- The timeline is easier to click and drag.
- Mouse-wheel movement over the timeline seeks forward/backward.
- Space toggles play/pause when the editor has an opened source.
- Source `.mp4` media and saved `.resolve.json` projects are clearly
  distinguished in the interface.
- Existing source, playback, persistence, and protected workflows remain
  functional.

## E-901 - Protected baseline

- **Category:** baseline
- **Command:** `make check`
- **Expected:** Existing implementation remains green before the transport
  changes.
- **Observed:** 53 tests passed, compilation passed, and diff checks passed.
- **Status:** passed
- **Artifacts:** terminal output.
- **Failure:** none
- **Fix:** none

## E-902 - Intentional TDD red state

- **Category:** baseline
- **Command:** `python3 -m unittest tests.test_editor_ui_helpers`
- **Expected:** New scroll/key tests fail because the helpers do not exist.
- **Observed:** Import failed for the missing
  `resolve_editor.app.is_play_pause_key` helper.
- **Status:** passedWithConcerns
- **Artifacts:** terminal output.
- **Failure:** expected missing implementation.
- **Fix:** added tested scroll-position and Space-key behavior helpers.
- **Accepted warning:** This was an intentional red state.

## E-903 - Focused green tests

- **Category:** implementation
- **Command:** `python3 -m unittest tests.test_editor_ui_helpers`
- **Expected:** Scroll direction/clamping and Space-key behavior pass.
- **Observed:** 8 focused tests passed.
- **Status:** passed
- **Artifacts:** `tests/test_editor_ui_helpers.py`.
- **Failure:** none
- **Fix:** none

## E-904 - GTK transport wiring

- **Category:** integration
- **Commands:** GTK introspection and construction of a vertical
  `Gtk.EventControllerScroll` with capture propagation.
- **Expected:** The installed GTK supports the scroll controller used by the
  timeline.
- **Observed:** Controller construction and capture configuration succeeded.
- **Status:** passed
- **Artifacts:** `resolve_editor/app.py`.
- **Failure:** none
- **Fix:** none

## E-905 - Full local quality gate

- **Category:** regression
- **Command:** `make check`
- **Expected:** All tests, compilation, and diff checks remain green.
- **Observed:** 56 tests passed; compilation and diff checks passed.
- **Status:** passed
- **Artifacts:** terminal output.
- **Failure:** none
- **Fix:** none

## E-906 - Generated-media smoke

- **Category:** functionality
- **Command:** `make smoke`
- **Expected:** The editor smoke flow still opens, plays, seeks, saves, and
  reopens a generated source.
- **Observed:** The target exited successfully.
- **Status:** passed
- **Artifacts:** temporary smoke media/project were cleaned up.
- **Failure:** none
- **Fix:** none

## E-907 - 1080p fixture smoke

- **Category:** functionality
- **Command:** Run source and project smoke flows against
  `~/Videos/editor-test-1m.mp4`.
- **Expected:** The 1920x1080, 60-second source opens and persists as a valid
  editor project.
- **Observed:** Both flows exited successfully; the project recorded the
  expected source name and 60-second duration.
- **Status:** passed
- **Artifacts:** temporary project removed after the run.
- **Failure:** none
- **Fix:** none

## Readiness

- **Passed:** E-901, E-903, E-904, E-905, E-906, and E-907.
- **Passed with concerns:** E-902.
- **Failed:** none.
- **Blocked:** target-workstation visual/manual confirmation of click,
  wheel, and Space interactions remains blocked when no usable X11 session is
  available.
- **Skipped:** automated screenshot evidence.
- **Accepted scope:** export and multi-source timelines remain outside
  PHASE-001; `.mp4` is source media and `.resolve.json` is editor state.

## E-913 - User-confirmed transport interaction

- **Category:** user-facing
- **Steps:** The user manually checked the editor interaction flow on the
  target workstation.
- **Expected:** Timeline clicking, mouse-wheel seeking, and Space playback
  toggle work in the real UI.
- **Observed:** User confirmation: “okay done and checked”.
- **Status:** passedWithConcerns
- **Artifacts:** none retained.
- **Failure:** no screenshot or detailed step log was supplied.
- **Fix:** none
- **Accepted warning:** Direct user confirmation is retained as the manual
  result; visual artifacts were not available to the agent.

## Superseding readiness

- **Passed:** E-913.
- **Passed with concerns:** prior automated UI evidence remains subject to
  the retained PyGObject warning and no screenshot artifact.
- **Failed:** none.
- **Blocked:** none after user confirmation.
- **Skipped:** automated visual capture.

## E-908 - Pre-fix regression baseline

- **Category:** baseline
- **Command:** `make check`
- **Expected:** The existing editor transport implementation is green before
  changing Space-key propagation.
- **Observed:** 56 tests passed; compilation and diff checks passed.
- **Status:** passed
- **Artifacts:** terminal output.
- **Failure:** none
- **Fix:** none

## E-909 - Intentional TDD red state

- **Category:** baseline
- **Command:** `python3 -m unittest tests.test_editor_ui_helpers`
- **Expected:** The new capture-phase regression test fails because the
  controller factory is not implemented yet.
- **Observed:** Import failed for the missing
  `resolve_editor.app.create_play_pause_key_controller` helper.
- **Status:** passedWithConcerns
- **Artifacts:** terminal output.
- **Failure:** expected missing implementation.
- **Fix:** added a capture-phase GTK key-controller factory and wired it to the
  editor window.
- **Accepted warning:** This was an intentional red state.

## E-910 - Focused Space-key regression test

- **Category:** implementation
- **Command:** `python3 -m unittest tests.test_editor_ui_helpers`
- **Expected:** The controller is configured for capture propagation so Space
  is handled before focused buttons.
- **Observed:** 9 focused tests passed, including the GTK propagation-phase
  assertion.
- **Status:** passedWithConcerns
- **Artifacts:** `tests/test_editor_ui_helpers.py`.
- **Failure:** none
- **Fix:** none
- **Accepted warning:** PyGObject emitted an existing deprecation warning
  while loading the GTK test override.

## E-911 - Post-fix local quality gate

- **Category:** regression
- **Command:** `make check`
- **Expected:** All tests, compilation, and diff checks remain green after the
  key-controller change.
- **Observed:** 57 tests passed; compilation and diff checks passed.
- **Status:** passedWithConcerns
- **Artifacts:** terminal output.
- **Failure:** none
- **Fix:** none
- **Accepted warning:** The same PyGObject deprecation warning is emitted by
  the GTK helper test.

## E-912 - Post-fix editor smoke

- **Category:** functionality
- **Command:** `make smoke`
- **Expected:** The editor still opens, plays, seeks, saves, and reopens a
  generated source after the key-controller change.
- **Observed:** The smoke target exited successfully and cleaned up its
  temporary artifacts.
- **Status:** passed
- **Artifacts:** temporary smoke media/project were removed.
- **Failure:** none
- **Fix:** none

## Superseding readiness

- **Passed:** E-908 and E-912.
- **Passed with concerns:** E-910 and E-911.
- **Failed:** none.
- **Blocked:** visual confirmation of Space while a button is focused still
  requires the user's graphical workstation.
- **Skipped:** automated mouse/keyboard GUI interaction because the current
  session has no usable X11 display.
