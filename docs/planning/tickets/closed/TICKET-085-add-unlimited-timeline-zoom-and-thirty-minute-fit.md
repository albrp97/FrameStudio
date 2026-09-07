# TICKET-085 - Add Unlimited Timeline Zoom and 30-Minute Fit

**Ticket ID:** TICKET-085
**Title:** Add unlimited timeline zoom and 30-minute fit
**Status:** complete
**Parent feature:** FEAT-029
**Parent phase:** PHASE-008
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Capability links:** CAP-002, CAP-003
**Owner:** repository implementation in the active worktree
**Approval:** Explicitly authorized by the 2026-08-28 user request; no
additional ticket approval is required before implementation
**Last updated:** 2026-09-07
**Dependencies:** existing timeline geometry and ruler contract; TICKET-081
  editor lifecycle baseline; fixed timeline viewport behavior
**Affected surfaces:** `framestudio/timeline_geometry.py`,
`framestudio/timeline.py`, `framestudio/app_timeline_actions.py`,
`framestudio/app.py`, `framestudio/app_ui.py`, timeline tests, README
**Risks:** extreme scales may overflow geometry, make navigation unusable, or
  accidentally alter the separate focus/composition zoom bounds
**Evidence path:** `evidence/ticket-085-timeline-fit-and-unlimited-zoom.md`

## Scope

- Remove the artificial upper limit that stopped normal timeline zoom at
  1200%, while retaining a safe lower bound for ordinary manual zooming.
- Continue geometric zoom progression at scales above the former maximum.
- Add a **30 min** action that fits a 30-minute reference window to the
  timeline viewport, including short projects without forcing an unusable
  minimum scale.
- Keep ruler, segment, playhead, scrolling, and duration calculations
  consistent at manual and fit-mode scales.

## Non-goals

- Unlimited focus/composition transform zoom, changes to the fixed output
  canvas, or new timeline editing operations.
- Persisting a new project-schema setting unless already required by the
  existing UI contract.

## Acceptance criteria

- Given a timeline at the old 1200% limit, another zoom-in action increases
  the scale and renders the correct segment geometry.
- Given any project duration, **30 min** makes the 1800-second reference
  window span the available timeline viewport.
- Given a project shorter than 30 minutes, fit mode preserves the full project
  and keeps the ruler range understandable.
- Given a manual zoom action after fit mode, the timeline returns to normal
  manual zoom behavior without stale fit calculations.
- Segment hit testing, playhead mapping, and horizontal scrolling remain
  correct at both extreme manual zoom and fit-mode scales.

## Verification

- Add geometry and canvas regressions for zoom progression, fit calculations,
  short projects, ruler mapping, and playhead/hit-test coordinates.
- Exercise manual zoom and **30 min** in GTK with a short and a long project.
- Run the existing editor tests, compile checks, and configured quality gates.

## Protected behavior

Existing segment editing, timeline duration display, playback seeking,
scrolling, and focus/composition zoom limits remain unchanged.

## Path history

Created in `docs/planning/tickets/open/` on 2026-08-28.
Moved to `docs/planning/tickets/closed/` on 2026-09-07 after user
validation.
