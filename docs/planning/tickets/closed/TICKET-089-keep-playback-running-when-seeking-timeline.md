# TICKET-089 - Keep Playback Running When Seeking on the Timeline

**Ticket ID:** TICKET-089
**Title:** Keep playback running when seeking on the timeline
**Status:** complete
**Parent feature:** FEAT-029
**Parent phase:** PHASE-008
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Capability links:** CAP-002, CAP-012
**Owner:** repository implementation in the active worktree
**Approval:** Explicitly authorized by the 2026-09-04 user request
**Last updated:** 2026-09-07
**Dependencies:** Existing playback controller and timeline preview request path
**Affected surfaces:** `framestudio/app_playback.py`, timeline playback tests,
GTK timeline interaction
**Risks:** seeking could lose play state, restart from the wrong time, or
surface a preview error without restoring the prior state
**Evidence path:** `evidence/ticket-089-keep-playback-running-when-seeking-timeline.md`

## Observable requirements

- Given the preview is playing, clicking or dragging to another timeline
  position should seek to that position and continue playing.
- Given the preview is paused, clicking or dragging to another timeline
  position should seek to that position and remain paused.
- Given seek or resume fails, the editor should surface the backend error and
  not report a false playing state.

## Scope

- Preserve the controller's play/pause state across timeline preview seeks.
- Add focused regression coverage for playing and paused timeline seeks.

## Non-goals

- Replacing the FFmpeg playback backend or changing timeline time mapping.
- Changing explicit play/pause controls or keyboard shortcuts.

## Validation

- Focused playback/timeline unit tests.
- Existing editor suite and compile/diff checks.
- Target-workstation GTK timeline click/drag while playing and while paused.

## Definition of done

- Focused regressions pass and no protected playback behavior regresses.
- User-visible play-state behavior is validated or an explicit environment
  limitation is recorded.

**Path history:** Created in `docs/planning/tickets/open/` on 2026-09-04.
Moved to `docs/planning/tickets/closed/` on 2026-09-07 after user
validation.
