# Delivery Evidence: TICKET-029

- Phase: `PHASE-001` - Opening and Resuming a Source Edit
- Feature: `FEAT-002` - Controlling Playback and Navigating the Source Timeline
- Ticket: `TICKET-029` - Restore Space Playback Toggle
- Status: `verifying`
- Branch: `ticket/phase-004-mixed-source-footage`
- Evidence path: `evidence/space-playback-toggle.md`

## SPACE-BASELINE-001

- Requirement/flow: Preserve existing playback state, FFmpeg frame delivery,
  and GTK shortcut behavior before the corrective change.
- Command: `.venv/bin/python -m unittest tests.test_editor_playback
  tests.test_editor_ui_helpers`
- Observed: 23 tests passed before adding the new regression cases.
- Status: `passed`

## SPACE-RED-001

- Requirement/flow: Recognize standard, keypad, and hardware-keycode Space
  events and expose a visible playback action state.
- Command: `.venv/bin/python -m unittest tests.test_editor_ui_helpers`
- Expected: The new tests fail before implementation.
- Observed: Test collection failed because `KEYCODE_SPACE` was not yet
  exported by `resolve_editor.app`.
- Status: `passed`
- Note: This was the intentional TDD red state.

## SPACE-FIX-001

- Requirement/flow: Make Space transport handling resilient and visible in the
  GTK editor.
- Observed: Space matching now accepts the translated Space symbol, keypad
  Space, and the standard hardware keycode fallback. The editor requests
  focus when presented, and the transport row exposes a `Play`/`Pause` button
  whose label follows the playback state.
- Evidence: `resolve_editor/app.py`, `tests/test_editor_ui_helpers.py`, and
  `README.md`.
- Status: `passed`

## SPACE-REGRESSION-001

- Commands:
  - `.venv/bin/python -m unittest tests.test_editor_ui_helpers
    tests.test_editor_playback`
  - `make check PYTHON=.venv/bin/python`
  - `make contract PYTHON=.venv/bin/python`
  - `make smoke PYTHON=.venv/bin/python`
  - `make quality PYTHON=.venv/bin/python`
- Observed: The focused suite passed 25 tests, the full regression suite
  passed 158 tests, the CLI contract suite passed 25 tests, generated-media
  smoke passed, and all configured local quality checks completed
  successfully.
- Status: `passed`
- Accepted warning: GTK emitted the existing
  `GLib.unix_signal_add_full` deprecation warning during UI tests.

## SPACE-LIVE-001

- Requirement/flow: Validate Space play/pause with real media in the GTK
  window and retain window-only visual evidence.
- Command: `make editor PYTHON=.venv/bin/python
  ARGS='--source /home/ghiki/Videos/portrait-test-720p.mp4'`
- Steps:
  1. Open the 720x1280 portrait fixture.
  2. Capture the initial transport state.
  3. Press Space and capture the running state.
  4. Press Space again and capture the paused state.
- Expected: The transport changes from `Play` to `Pause`, the playhead
  advances, and the second Space press restores `Play` without advancing.
- Observed: The live editor showed `Play` initially, `Pause` while playback
  was running with the playhead advancing, and `Play` after the second Space
  press at a retained position.
- Evidence:
  - `evidence/screenshots/space-playback-before.png`
  - `evidence/screenshots/space-playback-playing.png`
  - `evidence/screenshots/space-playback-paused.png`
- Status: `passed`

## SPACE-USER-001

- Requirement/flow: Confirm the corrected Space and visible Play/Pause
  transport behavior on the maintainer workstation.
- Status: `pending`
- Blocker: Configured user validation and remote checks are not terminal.
