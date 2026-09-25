# TICKET-106 - Set Practical Timeline Wheel Seek Pacing

**Ticket ID:** TICKET-106
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Phase:** PHASE-008
**Feature:** FEAT-029
**Capability links:** CAP-002, CAP-003, CAP-012
**Status:** verifying
**Horizon:** future
**Priority:** 2
**Owner:** repository implementation in the active worktree
**Approval:** User-authorized as part of the complete-worktree delivery under
CHG-011.
**Last updated:** 2026-09-24
**Source paths:** `docs/planning/reviews/CHG-011-deliver-authorized-existing-worktree-changes.md`,
`docs/planning/features/open/FEAT-029-strengthening-editor-recovery-and-export-observability.md`,
`framestudio/app_helpers.py`, `framestudio/app_ui.py`,
`framestudio/app_timeline_actions.py`, `tests/test_editor_ui_helpers.py`,
`tests/test_editor_composition.py`, `.github/aidd-config.yml`
**Dependencies:** existing timeline seek contract and timeline viewport
gesture routing
**Risks:** coarse seeking may make small corrections difficult or conflict
with horizontal scrolling, modified wheel gestures, or focus controls
**Affected surfaces:** timeline scroll handling, seek position, GTK tooltip,
and UI tests
**Evidence path:** `evidence/ticket-106-timeline-wheel-seek-pacing.md`
**Protected behaviors:** seek positions remain clamped to project duration;
modified/horizontal scrolling and focus-control gestures retain their current
meaning

## Outcome

Normal mouse-wheel input provides a practical coarse timeline seek for long
projects, while other scroll gestures retain their existing behavior.

## Scope

- Use a 30-second seek step per normal vertical wheel unit.
- Keep seeking bounded by the project duration.
- Describe the behavior in the timeline tooltip and retain existing gesture
  routing for horizontal, modified, and focus-control scrolling.

## Explicit non-goals

- Changing timeline zoom, duration, frame stepping, or playback rate.
- Changing scroll behavior in focus controls or the timeline viewport.

## Observable acceptance criteria

- Given the playhead at a valid position, one normal wheel unit moves it by
  30 seconds in the indicated direction.
- Given a playhead near either end, wheel seeking clamps at zero or project
  duration.
- Given horizontal or modified wheel input, timeline viewport scrolling
  remains unchanged.
- Given focus controls, their existing scroll-driven adjustment remains
  unchanged.

## Validation

- Automated functionality coverage for routed GUI scroll actions, both seek
  directions, duration clamping, and preserved modified/horizontal gestures.
- Existing editor UI, composition, smoke, and repository quality checks.
- Target-workstation confirmation on a long timeline with window-only
  before/after evidence.

## User-validation plan

- **Setup:** open a project longer than one minute and position the playhead
  near the middle.
- **Steps:** scroll the normal wheel once in each direction, repeat near the
  start and end, then test horizontal and modified wheel gestures and focus
  controls.
- **Expected result:** normal wheel seeks 30 seconds per unit and clamps at
  the project boundaries; other gestures retain their previous behavior.
- **Failure paths:** incorrect seek direction/step, seeking outside the
  timeline, or changed horizontal/modified/focus gestures.
- **Cleanup:** leave the playhead at a convenient position and close without
  modifying source media.
- **Evidence response:** return `PASS`, `FAIL`, or `BLOCKED` with observations
  and window-only screenshot paths.
- **Pass criteria:** coarse seeking is accurate, bounded, and does not alter
  other timeline gestures.
