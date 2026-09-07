# TICKET-086 - Preserve Triplicate Playhead and Play State

**Ticket ID:** TICKET-086
**Title:** Preserve triplicate playhead and play state
**Status:** complete
**Parent feature:** FEAT-029
**Parent phase:** PHASE-008
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Capability links:** CAP-002, CAP-003, CAP-010, CAP-012
**Owner:** repository implementation in the active worktree
**Approval:** Explicitly authorized by the 2026-08-28 user request; no
additional ticket approval is required before implementation
**Last updated:** 2026-09-07
**Dependencies:** live playback backend/controller position; composition refresh
  lifecycle; TICKET-082 triplicate offset behavior
**Affected surfaces:** `framestudio/app_timeline_actions.py`,
`framestudio/app_project.py`, `framestudio/app.py`, composition and timeline
tests, README
**Risks:** stale model state may overwrite the live backend position, preview
  rebuilds may restart playback, or an edited-time/timeline-time conversion may
  shift the visible playhead
**Evidence path:** `evidence/ticket-086-triplicate-playhead-preservation.md`

## Scope

- Capture the live playback position before enabling or disabling triplicate
  composition.
- Preserve the equivalent project/timeline and canvas playhead after the
  composed preview refreshes.
- Preserve whether playback was active or paused through the refresh.
- Fall back to the controller snapshot when a live backend position is not
  available, without silently resetting to zero.

## Non-goals

- Changing triplicate layout semantics, focus transforms, output composition,
  source audio behavior, or playback backend selection.

## Acceptance criteria

- Given playback at a nonzero position, enabling triplicate leaves the
  playhead at the same visible timeline position.
- Given playback at a nonzero position, disabling triplicate leaves the
  playhead at the same visible timeline position.
- Given an actively playing preview, the triplicate toggle does not leave the
  preview unexpectedly paused; a paused preview remains paused.
- Given a backend without a current position, the controller snapshot is used
  and the refresh does not jump to the timeline start.
- Given edits and source offsets, the restored timeline position maps to the
  same edited playback time within the existing precision.

## Verification

- Add composition regressions for enable/disable, backend position precedence,
  controller fallback, edited-time mapping, and play/pause preservation.
- Exercise both toggles during playback and pause in the GTK editor.
- Run existing composition, timeline, compile, and configured quality checks.

## Protected behavior

Triplicate layout rendering, linked focus modifications, source preservation,
and normal play/pause/seek behavior remain unchanged.

## Path history

Created in `docs/planning/tickets/open/` on 2026-08-28.
Moved to `docs/planning/tickets/closed/` on 2026-09-07 after user
validation.
