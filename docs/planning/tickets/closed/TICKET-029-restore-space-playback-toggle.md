# TICKET-029 - Restore Space Playback Toggle

**Ticket ID:** TICKET-029
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Phase:** PHASE-001
**Feature:** FEAT-002
**Capability links:** CAP-002, CAP-012
**Status:** complete
**Closure:** user-approved on 2026-08-22 after successful implementation,
review, target-workstation validation, and local delivery evidence; remote
checks remain unavailable and are recorded as an accepted warning.
**Reopened:** user-reported on 2026-08-22 after playback stopped advancing
when Space was pressed following a timeline cursor seek.
**Path history:** `tickets/open/TICKET-029-restore-space-playback-toggle.md`
-> `tickets/closed/TICKET-029-restore-space-playback-toggle.md`
-> `tickets/open/TICKET-029-restore-space-playback-toggle.md`
-> `tickets/closed/TICKET-029-restore-space-playback-toggle.md`
**Horizon:** first
**Priority:** 1
**Owner:** repository implementation in the active worktree
**Approval:** user-reported and implementation-authorized on 2026-08-22
**Provider:** auto; base and target branches are not configured in
`.github/aidd-config.yml`
**Source paths:** `docs/planning/tickets/closed/TICKET-003-playback-control-state.md`,
`docs/planning/tickets/closed/TICKET-004-preview-timeline-interaction.md`,
`resolve_editor/app.py`, `resolve_editor/playback.py`,
`resolve_editor/ffmpeg_playback.py`, and the user-reported Space playback
failure
**Dependencies:** TICKET-003 and TICKET-004; existing FFmpeg playback backend
**Risks:** keyboard focus, duplicate toggles, stale transport state, burst
frame delivery after seek, and backend failures being presented as successful
playback
**Affected surfaces:** GTK transport controls, keyboard handling, playback
state presentation, focused UI tests, and target-workstation evidence
**Evidence path:** `evidence/space-playback-toggle.md`

## Outcome

The user can start and pause an opened editor project reliably with Space or
an explicit Play/Pause control, regardless of which editor child currently has
focus, including after moving the timeline cursor.

## Scope

- Keep Space as the documented play/pause shortcut.
- Accept the standard translated Space key and equivalent GTK hardware/keypad
  variants.
- Ensure the editor window requests focus when it is presented.
- Provide a visible transport button whose label follows the playback state.
- Pace raw preview frames at the configured frame rate after cursor seeks and
  preserve pause/resume behavior.
- Surface backend failures through the existing status/error path.

## Explicit non-goals

- Audio preview, automatic level handling, FPS enhancement, or codec changes.
- New timeline editing, visual modifications, or composition behavior.
- Changes to the established FFmpeg render profile.

## Observable requirements

- Given an opened project paused at a valid position, pressing Space changes the
  state to playing and advances the preview position.
- Given a project paused after a timeline cursor seek, pressing Space delivers
  successive preview frames at approximately the configured frame rate.
- Given an opened project playing, pressing Space changes the state to paused
  without losing the current position.
- Given a focused editor control, Space still toggles playback once rather than
  activating the control and toggling again.
- Given a loaded project, the visible transport button says `Play` while
  paused and `Pause` while playing.
- Given a playback backend failure, the editor preserves project state and
  reports the existing actionable error.

## Validation and evidence

- Run the protected playback/UI baseline before implementation.
- Run focused key, transport, playback, and FFmpeg tests.
- Run the pacing regression against the pre-fix behavior and the corrected
  implementation.
- Run the configured `make check`, `make contract`, `make smoke`, and
  `make quality PYTHON=.venv/bin/python` gates.
- Perform a real-media GTK flow using `/home/ghiki/Videos/portrait-test-720p.mp4`
  and retain window-only before/playing/paused screenshots.

## Protected behavior

Existing playback state transitions, timeline seeking, frame stepping,
selection shortcuts, project persistence, export behavior, legacy scripts,
and source-preservation guarantees remain unchanged.

## Definition of done

- Space reliably toggles playback in the live editor.
- The visible Play/Pause control mirrors the playback state.
- Focused automated and real-media evidence is recorded.
- The ticket reaches `complete` through user-approved validation; configured
  remote delivery checks remain unavailable and are recorded as an accepted
  warning.

## Closure

The post-seek pacing correction, Space transport behavior, and live GTK
validation are complete in local commit
`6aebb26121eb7e4088b4c3678b670038116be2be`.
