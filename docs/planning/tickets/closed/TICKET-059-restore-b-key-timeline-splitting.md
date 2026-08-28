# TICKET-059 - Restore B-Key Timeline Splitting

**Ticket ID:** TICKET-059
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Phase:** PHASE-002
**Feature:** FEAT-004
**Capability links:** CAP-003, CAP-012
**Status:** complete
**Closure:** user-approved on 2026-08-26 after the B-key regression fix was
implemented, tested, reviewed, and accepted; unavailable remote and
target-specific checks remain recorded as accepted warnings.
**Horizon:** first
**Priority:** 1
**Owner:** repository implementation in the active worktree
**Approval:** user-reported and implementation-authorized on 2026-08-24
**Provider:** auto; base and target branches are not configured in
`.github/aidd-config.yml`
**Source paths:** `docs/planning/tickets/closed/TICKET-008-split-delete-editor-workflow.md`,
`framestudio/app_playback.py`, `framestudio/app_timeline_actions.py`,
`framestudio/model_timeline.py`, and the user-reported B-key failure
**Dependencies:** Existing split/delete editor workflow and playback/timeline
position mapping
**Risks:** splitting at the wrong coordinate could corrupt segment boundaries,
selection, or saved playhead state
**Affected surfaces:** GTK keyboard handling, playback position mapping,
timeline split action, focused UI integration tests, and user-facing editor
behavior
**Evidence path:** `evidence/b-key-split-regression.md`
**Last updated:** 2026-08-26
**Path history:** `tickets/open/TICKET-059-restore-b-key-timeline-splitting.md`
-> `tickets/closed/TICKET-059-restore-b-key-timeline-splitting.md`
**Protected behaviors:** CLI/domain split validation, mixed-source timeline
semantics, playback, delete/restore, project persistence, export behavior,
legacy scripts, and source preservation

## Outcome

The user can press **B** or **b** while a clip is selected and split that clip
at the current visible timeline playhead, including after deleted or reordered
blocks.

## Scope

- Convert the playback controller's edited-output position to the visible
  timeline coordinate before invoking a timeline-backed split.
- Preserve selected-block and post-split selection behavior.
- Cover one-source timelines with deleted preceding blocks and explicit
  mixed-source timeline blocks.
- Keep the shared domain operation and CLI boundary validation unchanged.

## Explicit non-goals

- Changing split boundary semantics or source media.
- Adding new keyboard shortcuts, undo behavior, or timeline editing features.
- Modifying PHASE-007 FPS/export behavior.

## Observable requirements

- Given a selected clip and a playhead strictly inside its visible timeline
  bounds, pressing **B** should create two valid ordered blocks.
- Given deleted or reordered preceding blocks, pressing **B** should split at
  the visible timeline playhead rather than at the concatenated playback
  position.
- Given a mixed-source timeline block, pressing **B** should preserve the
  block's source interval and split its timeline interval correctly.
- Given a boundary or missing selection, the existing explicit validation error
  should remain state-safe.

## Validation and evidence

- Run the protected split/UI baseline before implementation.
- Add and prove a failing B-key integration regression.
- Run focused split, mixed-source, playback, and UI tests after the fix.
- Run the configured applicable check, smoke, contract, quality, and review
  gates; record unavailable remote or target-workstation checks explicitly.
- Provide a target-workstation validation handoff before closure.

## Definition of done

- B-key splitting works from the live editor at the visible playhead.
- Existing split/domain/CLI behavior remains unchanged.
- Focused regression and protected gates are evidenced.
- User validation is terminally recorded before the ticket is closed.

## Closure

TICKET-059 was closed on 2026-08-26 after the user confirmed the completed
ticket set was approved, accepted, and tested.
