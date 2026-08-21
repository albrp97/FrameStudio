# Evidence - TICKET-011

**Phase:** PHASE-002  
**Feature:** FEAT-005  
**Ticket:** TICKET-011  
**Objective:** OBJ-001  
**Scope:** SCOPE-001  
**Status:** complete  
**Planning chain:** `OBJ-001 -> SCOPE-001 -> CAP-005/CAP-012 -> PHASE-002 ->
FEAT-005 -> TICKET-011`  
**Repository:** `/home/ghiki/code/resolve-media-tui`  
**Branch:** `main`  
**Base revision:** `150d2f7`  
**Dependency evidence:** `evidence/split-delete-duration.md`,
`evidence/export-plan-selection.md`  
**Evidence path:** `evidence/verified-safe-export.md`

## Requirements

- Execute the structured fast or fallback export plan.
- Keep source and existing destination untouched until validation succeeds.
- Verify playability, expected duration, video presence, audio presence, and
  relevant dimensions before publication.
- Publish atomically only after validation.
- Preserve source, project, and last valid output on command or validation
  failure.
- Integrate export into the editor with explicit status and error handling.

## Protected flows

Existing scripts, source probing, segment invariants, project persistence,
playback/transport behavior, atomic project saves, and all prior tests remain
protected.

## E-1101 - Dependency baseline

- **Category:** baseline
- **Command:** `make check`
- **Expected:** TICKET-008, TICKET-009, and TICKET-010 behavior are green
  before export execution changes.
- **Observed:** The latest dependency gate passed 78 tests, compilation, and
  diff checks; the existing PyGObject deprecation warning was emitted.
- **Status:** passedWithConcerns
- **Artifacts:** dependency evidence records and terminal output.
- **Failure:** none.
- **Fix:** none.
- **Accepted warning:** The existing PyGObject warning is non-failing.

## Readiness

- **Passed:** E-1101.
- **Passed with concerns:** E-1101 because of the existing PyGObject warning.
- **Failed:** none.
- **Blocked:** implementation and export evidence are pending.
- **Skipped:** none.
- **Next permitted action:** add failing execution tests and implement safe
  export publication.

## E-1102 - Safe export execution implementation

- **Category:** implementation
- **Command or steps:** Implemented `execute_export`, output verification,
  temporary partial paths, atomic publication, source-stat checks, failure
  cleanup, and the GTK **Export video** action in `resolve_editor/export.py`
  and `resolve_editor/app.py`.
- **Expected:** An export command must not publish output until the candidate
  is playable and matches the edited duration, dimensions, and source audio
  presence; source and existing destination remain protected on failure.
- **Observed:** Stream-copy and fallback routes execute through unique partial
  files. FFprobe and FFmpeg validate the candidate before `os.replace`
  publishes it. Existing destinations and source files are preserved when
  execution fails.
- **Status:** passedWithConcerns
- **Artifacts:** `resolve_editor/export.py`, `resolve_editor/app.py`,
  `tests/test_editor_export_execution.py`
- **Failure:** none in the implementation path.
- **Fix:** Added explicit audio-stream presence tracking so an unknown audio
  codec cannot be mistaken for an absent audio stream.
- **Accepted warning:** GTK export interaction still requires target-workstation
  manual confirmation.

## E-1103 - Focused export execution evidence

- **Category:** integration
- **Command:** `python3 -m unittest tests.test_editor_export_execution`
- **Expected:** Real FFmpeg fallback and stream-copy exports pass; output is
  verified; source preservation and failed-export recovery pass.
- **Observed:** 3 tests passed, including real-media fallback export,
  stream-copy export, source preservation, and partial-output cleanup.
- **Status:** passed
- **Artifacts:** `tests/test_editor_export_execution.py`
- **Failure:** none.
- **Fix:** none.
- **Blocker:** none.

## E-1104 - Full local quality gate after export completion

- **Category:** gate
- **Command:** `make check && make smoke`
- **Expected:** The complete repository test suite, Python compilation,
  whitespace checks, and generated-media GTK smoke flow pass.
- **Observed:** 82 tests passed; compilation and `git diff --check` passed;
  `make smoke` exited successfully. The existing PyGObject deprecation
  warning was emitted without failing the gate.
- **Status:** passedWithConcerns
- **Artifacts:** `Makefile`, `tests/`
- **Failure:** none.
- **Fix:** none.
- **Accepted warning:** `GLib.unix_signal_add_full` emits the existing
  non-failing PyGObject deprecation warning.

## E-1105 - Real 1080p fixture export

- **Category:** functionality
- **Command:** A disposable Python flow loaded
  `/home/ghiki/Videos/editor-test-1m.mp4`, split at 20 seconds, deleted the
  second segment, planned and executed export to a temporary MP4, probed the
  output, and removed the temporary output.
- **Expected:** The fallback route is selected for a non-keyframe cut; the
  published candidate is playable, 1920x1080, approximately 20 seconds, and
  retains AAC audio.
- **Observed:** Route `fallback`; reason `one or more cut boundaries are not
  keyframe-aligned`; expected duration `20.0`; actual duration `20.0`;
  dimensions `1920x1080`; video `h264`; audio `aac`. The source remained
  present and its size was unchanged during the flow.
- **Status:** passed
- **Artifacts:** `/home/ghiki/Videos/editor-test-1m.mp4` (pre-existing local
  fixture; not committed), `resolve_editor/export.py`
- **Failure:** none.
- **Fix:** none.

## E-1106 - Target-workstation manual export flow

- **Category:** functionality
- **Command or steps:** Launch `make start`, load the one-minute 1080p fixture,
  split at an interior playhead position, delete and restore a segment, save
  and reopen the project, then export to a new MP4 and inspect it with
  `ffprobe`.
- **Expected:** The segment state, edited duration, export status, output
  metadata, and source-preservation behavior are confirmed in the GTK UI.
- **Observed:** Not executable in this agent session because no usable X11
  display is available. The repeatable procedure is documented in `README.md`.
- **Status:** blocked
- **Artifacts:** `README.md`
- **Failure:** no target-workstation display.
- **Fix:** none available in the current session.
- **Blocker:** Maintainer must perform the GTK interaction on the target
  workstation.

## Readiness supersession

- **Passed:** E-1103 and E-1105.
- **Passed with concerns:** E-1102 and E-1104 because target-workstation UI
  confirmation and the existing GTK deprecation warning remain.
- **Blocked:** E-1106 target-workstation manual export flow.
- **Remote checks:** required by `.github/aidd-config.yml`, but no remote-check
  infrastructure is available locally.
- **Readiness:** TICKET-011 remains `needs-review`; implementation and local
  evidence are complete, but the configured user-facing manual gate and
  remote checks are not terminally evidenced.
- **Next permitted action:** run the documented GTK manual flow on the target
  workstation, then append the result and complete the ticket only if the
  output metadata, duration, playability, and source-preservation checks pass.

## E-1107 - User-confirmed target-workstation export flow

- **Category:** functionality
- **Command or steps:** The maintainer completed the documented target-
  workstation flow for the one-minute fixture, including editor interaction,
  save/reopen, and export checks.
- **Expected:** The user-facing export flow confirms segment state, edited
  duration, progress/status behavior, output validity, and source
  preservation.
- **Observed:** User confirmation: “good. everything was checked so you can
  unblock the ticket 11 and continue using the appropiate skills”.
- **Status:** passedWithConcerns
- **Artifacts:** `README.md`; local fixture
  `/home/ghiki/Videos/editor-test-1m.mp4`.
- **Failure:** none reported by the maintainer.
- **Fix:** none.
- **Accepted warning:** No screenshot artifact or remote-check result was
  provided in this session; the confirmation is recorded as the manual
  user-facing evidence.

## Readiness supersession

- **Passed:** E-1103, E-1105, and E-1107.
- **Passed with concerns:** E-1102 and E-1104 because of the existing GTK
  deprecation warning; E-1107 because screenshots and remote checks remain
  unavailable in this session.
- **Blocked:** none for the documented local and target-workstation export
  flow.
- **Remote checks:** still required by `.github/aidd-config.yml` and not
  available in the local environment.
- **Readiness:** TICKET-011's implementation, local integration evidence, and
  user-facing manual gate are complete; remote-check readiness remains an
  external delivery concern.

## E-1108 - TICKET-011 lifecycle gate transition

- **Category:** gate
- **Command or steps:** Applied the configured lifecycle transition after
  E-1107 user confirmation and the read-only ticket review.
- **Expected:** The cleared manual blocker is reflected without claiming
  unavailable remote checks passed.
- **Observed:** TICKET-011 is now `gated` in the open lifecycle directory.
  Local implementation, integration, output-validation, source-preservation,
  and user-facing evidence are terminal; remote checks remain explicitly
  outstanding.
- **Status:** passedWithConcerns
- **Artifacts:** `docs/planning/tickets/open/TICKET-011-verified-safe-export.md`,
  `docs/planning/backlog.md`, this evidence record.
- **Failure:** none.
- **Fix:** Updated the ticket and synchronized indexes to the `gated` state.
- **Accepted warning:** The configured remote-check and screenshot
  requirements are not available in this environment.

## Readiness supersession

- **Passed:** E-1103, E-1105, and the local review of TICKET-011.
- **Passed with concerns:** E-1102, E-1104, E-1107, and E-1108 because of
  the existing GTK warning and unavailable remote/screenshot artifacts.
- **Blocked:** none for local or user-confirmed manual export behavior.
- **Remote checks:** still required by `.github/aidd-config.yml` and not
  available locally.
- **Readiness:** TICKET-011 is unblocked and `gated`; it remains open until
  provider-specific remote checks and any required visual artifacts are
  terminally handled.

## E-1109 - User-authorized TICKET-011 closure

- **Category:** gate
- **Command or steps:** Applied the user's explicit request to close
  TICKET-011 after the documented manual flow was confirmed.
- **Expected:** The same ticket record moves to the configured closed
  directory with its stable ID, evidence, and accepted warnings preserved.
- **Observed:** TICKET-011 is `complete` at
  `docs/planning/tickets/closed/TICKET-011-verified-safe-export.md`; backlog
  and migration inventory paths are synchronized.
- **Status:** passedWithConcerns
- **Artifacts:** the closed ticket record, `docs/planning/backlog.md`,
  `docs/planning/migration-report.md`, and this evidence record.
- **Failure:** none reported for the user-confirmed workflow.
- **Fix:** Moved the existing ticket record without recreating it and retained
  the unavailable remote-check and screenshot requirements as warnings.
- **Accepted warning:** Remote checks and required visual artifacts were not
  available locally and were not claimed as passed.

## Final lifecycle state

- **Ticket:** `TICKET-011` is complete and closed by explicit user
  authorization.
- **Evidence:** local implementation, integration, output-validation,
  source-preservation, and target-workstation manual evidence are terminal.
- **Warnings:** configured remote checks and screenshot artifacts remain
  unavailable.
