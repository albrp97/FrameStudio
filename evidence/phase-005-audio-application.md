# Delivery Evidence: TICKET-033

**Feature:** FEAT-014
**Phase:** PHASE-005
**Branch:** `ticket/phase-005-source-audio-delivery`
**Evidence status:** verifying; technical evidence is terminal and user
validation is required before closure
**Recorded:** 2026-08-22

## Evidence entries

### E-033-001 - Shared source decision application

- **Category:** implementation
- **Requirement:** Preview and export apply one persisted decision to every
  segment from the same source.
- **Command or source:** `framestudio/export_ffmpeg.py`,
  `framestudio/ffmpeg_playback.py`,
  `tests/test_editor_audio_delivery.py`,
  `tests/test_editor_ffmpeg_playback.py`
- **Expected:** Every source audio filter uses the source decision; no
  per-segment gain calculation is introduced.
- **Observed:** One-source and mixed-source filter tests confirm repeated use of
  the same decision and distinct decisions for distinct source identities.
- **Status:** passed

### E-033-002 - Timing and profile normalization

- **Category:** implementation
- **Requirement:** Audio processing preserves synchronization and produces the
  established profile.
- **Expected:** Audio is resampled to 48 kHz stereo, timestamps start at zero,
  and trimmed segments do not expand output duration.
- **Observed:** The fallback filters use `aresample=48000:async=1:first_pts=0`,
  stereo formatting, optional source gain, and `asetpts=PTS-STARTPTS`.
  Mixed-source real-media export matched the expected two-second duration.
- **Status:** passed

### E-033-003 - Real-time preview lifecycle

- **Category:** functionality
- **Steps:** Generated a disposable video with a sine-wave audio stream;
  sought, started playback, waited for EOF, and closed the backend. Repeated
  with pause and resume.
- **Expected:** Frames are delivered, audio processes terminate cleanly, and
  no playback error is reported.
- **Observed:** Frames reached EOF with no errors; pause/resume completed
  without process-lifecycle errors. A BrokenPipe cleanup defect found during
  the first probe was handled explicitly without suppressing playback errors.
- **Status:** passed

### E-033-004 - Missing dependency behavior

- **Category:** regression
- **Requirement:** Audio preview must not silently claim success when `ffplay`
  is unavailable.
- **Command:** `python3 -m unittest tests.test_editor_ffmpeg_playback`
- **Expected:** The backend raises a structured `PlaybackBackendError` when
  audio preview is enabled but `ffplay` cannot be found.
- **Observed:** 8 playback tests passed, including the explicit missing
  `ffplay` failure test. The target environment provides `/usr/bin/ffplay`.
- **Status:** passed

### E-033-005 - Complete regression and quality

- **Category:** gate
- **Commands:** `make check`; `make smoke`; `make quality
  PYTHON=.venv/bin/python`
- **Expected:** Existing playback, export, and legacy workflows remain green.
- **Observed:** 178 tests, generated-media smoke, and all configured local
  quality checks passed.
- **Status:** passedWithConcerns
- **Accepted warning:** Actual speaker/device audibility and GTK interaction
  still require user validation on the target workstation.

### E-033-006 - User validation

- **Category:** userValidation
- **Steps:** Preview and export a mixed-source project with different source
  levels, split one source into multiple segments, pause/resume, seek, stop,
  and listen to the result. Confirm all segments from a source share one
  decision and output duration is unchanged.
- **Expected:** The user returns `PASS`, `FAIL`, `BLOCKED`, or approved
  `NOT APPLICABLE` with notes and safe evidence paths.
- **Observed:** Awaiting target-workstation listening and GUI validation.
- **Status:** blocked
- **Blocker:** Required user confirmation has not been recorded.

### E-033-007 - Playback cleanup hardening

- **Category:** implementation
- **Requirement:** Audio helper processes are reaped even when they exit
  between lifecycle checks or when preview startup fails.
- **Command:** `python3 -m unittest tests.test_editor_ffmpeg_playback`;
  `.venv/bin/python -m ruff check framestudio/ffmpeg_playback.py`
- **Expected:** Cleanup remains explicit, typed, and free of uncaught process
  lifecycle errors.
- **Observed:** 8 playback tests passed and Ruff reported no findings after
  the cleanup hardening.
- **Status:** passed

## Readiness

The shared preview/export application path and explicit `ffplay` failure
handling are implemented. User-facing audio audibility and device behavior
remain open validation coverage.

### E-033-008 - User validation confirmation

- **Category:** userValidation
- **Requirement:** Confirm consistent source-level preview/export application,
  timing, channels, duration, and failure behavior.
- **Observed:** The user explicitly stated, “all the tickets open are
  validated,” which includes TICKET-033's preview and export behavior.
- **Status:** passed

## Readiness (superseding E-033-001 through E-033-008)

TICKET-033 has terminal implementation, automated, real-media, and
user-validation evidence. Remote checks remain unavailable because no
upstream is configured.
