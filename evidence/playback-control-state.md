# Evidence - TICKET-003

**Phase:** PHASE-001
**Feature:** FEAT-002
**Ticket:** TICKET-003
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Status:** passedWithConcerns
**Planning chain:** `OBJ-001 -> SCOPE-001 -> CAP-002/CAP-012 -> PHASE-001 ->
FEAT-002 -> TICKET-003`
**Source references:** `framestudio/playback.py`,
`framestudio/ffmpeg_playback.py`, `tests/test_editor_playback.py`,
`tests/test_editor_ffmpeg_playback.py`
**Evidence path:** `evidence/playback-control-state.md`

## E-301 - Playback state and backend tests

- **Category:** implementation
- **Command:** `python3 -m unittest tests.test_editor_playback
  tests.test_editor_ffmpeg_playback`
- **Expected:** Play, pause, seek, clamping, explicit backend errors, and
  real FFmpeg frame delivery behave deterministically.
- **Observed:** 4 tests ran and passed, including a generated-media FFmpeg
  playback flow that delivered RGBA frames and reached end-of-stream.
- **Status:** passed
- **Artifacts:** focused unittest output.
- **Failure:** none
- **Fix:** none

## E-302 - Regression suite

- **Category:** regression
- **Command:** `python3 -m unittest discover -s tests`
- **Expected:** Existing protected workflows remain green.
- **Observed:** 50 tests ran and passed.
- **Status:** passed
- **Artifacts:** full unittest output.
- **Failure:** none
- **Fix:** none

## E-303 - Playback limitations

- **Category:** gate
- **Expected:** Backend limitations are explicit rather than hidden.
- **Observed:** The selected backend uses a managed FFmpeg raw-frame pipe,
  restarts decoding for seeks, and does not yet provide audio preview.
- **Status:** passedWithConcerns
- **Artifacts:** `docs/specs/editor-foundation-decision.md`
- **Failure:** no audio-preview path is implemented in this horizon.
- **Fix:** none; audio preview is outside the approved foundation ticket.
- **Accepted warning:** Frame transfer is CPU-visible and seek accuracy may
  be approximate for variable-frame-rate or keyframe-heavy sources.

## Protected flows

Existing curses workflows, FFmpeg processing commands, tests, and source-safe
output behavior remain available and unchanged.

## Readiness

The playback controller and real FFmpeg backend are implemented and tested.

- **Passed:** E-301 and E-302.
- **Passed with concerns:** E-303.
- **Failed:** none.
- **Blocked:** none for the playback state/backend contract.
- **Skipped:** visual/manual workstation assessment.
- **Accepted warnings:** CPU-visible frame transfer, approximate seeks for
  some media, and no audio preview in this horizon.
