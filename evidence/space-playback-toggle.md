# Delivery Evidence: TICKET-029

- Phase: `PHASE-001` - Opening and Resuming a Source Edit
- Feature: `FEAT-002` - Controlling Playback and Navigating the Source Timeline
- Ticket: `TICKET-029` - Restore Space Playback Toggle
- Status: `verifying`
- Branch: `ticket/phase-005-source-audio-delivery`
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

## SPACE-RED-002

- Requirement/flow: After seeking the timeline cursor, Space playback must
  deliver successive preview frames at the configured rate instead of
  emitting the entire decoded stream in one burst.
- Command: `python3 -m unittest
  tests.test_editor_ffmpeg_playback.FfmpegPlaybackTests.test_playback_delivers_frames_at_real_time_after_seek`
- Expected: The new pacing regression fails before the fix.
- Observed: The test failed before the fix because adjacent frames arrived
  only `0.000021661` seconds apart instead of at the required interval.
- Status: `passed`
- Note: This was the intentional TDD red state.

## SPACE-FIX-002

- Requirement/flow: Pace raw preview delivery after a timeline cursor seek and
  keep pause/resume responsive.
- Observed: `FfmpegPlaybackBackend` now uses frame deadlines based on the
  configured frame rate, interrupts waits on stop, and resets pacing while
  paused so resumed playback does not burst or skip to the latest frame.
- Evidence: `resolve_editor/ffmpeg_playback.py` and
  `tests/test_editor_ffmpeg_playback.py`.
- Status: `passed`

## SPACE-REGRESSION-002

- Commands:
  - `python3 -m unittest
    tests.test_editor_ffmpeg_playback.FfmpegPlaybackTests.test_playback_delivers_frames_at_real_time_after_seek
    tests.test_editor_ffmpeg_playback.FfmpegPlaybackTests.test_seek_presents_a_frame_and_playback_emits_frames`
  - `python3 -m unittest
    tests.test_editor_ffmpeg_playback.FfmpegPlaybackTests.test_pause_and_resume_hold_and_restart_frame_delivery`
  - `make quality PYTHON=.venv/bin/python`
  - `make contract PYTHON=.venv/bin/python`
  - `make smoke PYTHON=.venv/bin/python`
- Observed: The focused pacing and existing frame-delivery tests passed. The
  focused pause/resume test also passed. The full configured quality run
  passed 180 tests, compilation, formatting,
  linting, type checks, complexity, duplication, dependency checks, security,
  dependency audit, and churn. Contract and generated-media smoke flows also
  passed.
- Status: `passed`
- Accepted warning: GTK emitted the existing
  `GLib.unix_signal_add_full` deprecation warning during UI tests.

## SPACE-LIVE-002

- Requirement/flow: Validate timeline-cursor playback and pause in the live
  GTK window with active-window screenshots.
- Command: `python3 resolve_editor.py --source
  /home/ghiki/Videos/portrait-test-720p.mp4`; `wtype -k space`; `make
  screenshot LABEL=timeline-playback-playing-1`; `make screenshot
  LABEL=timeline-playback-playing-2`; `wtype -k space`; `make screenshot
  LABEL=timeline-playback-paused-1`; `make screenshot
  LABEL=timeline-playback-paused-2`
- Expected: Successive playing screenshots differ, while successive paused
  screenshots remain identical.
- Observed: Playing screenshots had different SHA-256 hashes, and the paused
  screenshots had the same SHA-256 hash. The editor process exited cleanly
  after the verification.
- Evidence:
  - `evidence/screenshots/timeline-playback-before.png`
  - `evidence/screenshots/timeline-playback-playing-1.png`
  - `evidence/screenshots/timeline-playback-playing-2.png`
  - `evidence/screenshots/timeline-playback-paused-1.png`
  - `evidence/screenshots/timeline-playback-paused-2.png`
- Status: `passed`

## SPACE-LIVE-003

- Requirement/flow: Validate that Space starts visible playback after a real
  timeline cursor seek and pauses it without losing the selected position.
- Command: `python3 resolve_editor.py --source
  /home/ghiki/Videos/portrait-test-720p.mp4`; click the active timeline near
  `00:01`; `wtype -k space`; `make screenshot
  LABEL=timeline-playback-seeked-real-playing-1`; `make screenshot
  LABEL=timeline-playback-seeked-real-playing-2`; `wtype -k space`; `make
  screenshot LABEL=timeline-playback-seeked-real-paused-1`; `make screenshot
  LABEL=timeline-playback-seeked-real-paused-2`
- Expected: The cursor seek updates the visible position, the first Space
  press changes `Play` to `Pause` and successive screenshots differ, and the
  second Space press pauses the preview with identical successive screenshots.
- Observed: The active window showed `00:01` and the playhead moved to the
  clicked timeline position. Playing screenshots differed by SHA-256 hash, and
  paused screenshots matched exactly. The editor process exited cleanly after
  verification.
- Evidence:
  - `evidence/screenshots/timeline-playback-seeked-real.png`
  - `evidence/screenshots/timeline-playback-seeked-real-playing-1.png`
  - `evidence/screenshots/timeline-playback-seeked-real-playing-2.png`
  - `evidence/screenshots/timeline-playback-seeked-real-paused-1.png`
  - `evidence/screenshots/timeline-playback-seeked-real-paused-2.png`
- Note: The fixture's audio preview path reported its existing process-stop
  status message after the seek; video frame delivery and transport behavior
  remained correct, and audio preview is outside this ticket's scope.
- Status: `passed`

## SPACE-USER-001

- Requirement/flow: Confirm the corrected Space and visible Play/Pause
  transport behavior on the maintainer workstation.
- Status: `pending`
- Blocker: Configured user validation and remote checks are not terminal.

## SPACE-USER-002

- Requirement/flow: Confirm post-seek play, pause, and resume behavior in the
  maintainer's live editor workflow.
- Setup: `.venv/bin/python resolve_editor.py --source
  /home/ghiki/Videos/portrait-test-720p.mp4`
- Steps: Move the timeline cursor to about `00:01`, press Space to start,
  press Space to pause, press Space again to resume, and close the editor.
- Expected: The transport label follows each state, the preview/playhead
  advances while playing, and the position remains stable while paused.
- Observed: The maintainer returned `PASS`.
- Status: `passed`
- Accepted warning: Remote checks remain unavailable because no remote or
  upstream branch is configured.

## SPACE-REVIEW-001

- Requirement/flow: Review the corrected playback behavior and the complete
  PHASE-005 delivery scope before commit.
- Commands:
  - `make quality PYTHON=.venv/bin/python`
  - `make contract PYTHON=.venv/bin/python`
  - `make smoke PYTHON=.venv/bin/python`
  - `git diff --check`
- Observed: The configured quality suite passed 180 tests and all configured
  formatting, lint, type, complexity, duplication, dependency, security,
  audit, and churn checks. Contract passed 26 tests, generated-media smoke
  passed, and no actionable introduced findings were identified in the
  implementation or review. Planning records, evidence paths, and protected
  legacy surfaces are synchronized with the reviewed scope.
- Static-analysis artifacts:
  - `evidence/static-analysis/dependencies.json` reports zero findings.
  - `evidence/static-analysis/pip-audit.json` reports zero known
    vulnerabilities.
  - `evidence/static-analysis/bandit.json` reports zero findings.
  - `evidence/static-analysis/jscpd-report.json` reports 1.649% duplication,
    zero new clones, and zero new duplicated lines.
  - `evidence/static-analysis/churn.json` reports no changed-file hotspot.
- Local/PR parity: `unavailable`; the repository workflow defines the same
  `make quality PYTHON=.venv/bin/python` command, but no remote or upstream is
  configured to execute or compare provider checks.
- Non-blocking follow-up: `resolve_editor/ffmpeg_playback.py` remains a large
  adapter module and can be split further around audio lifecycle and composed
  playback in a later structural ticket.
- Accepted warning: Remote checks and PR state cannot be terminally evidenced
  without a configured remote.
- Status: `passedWithConcerns`
