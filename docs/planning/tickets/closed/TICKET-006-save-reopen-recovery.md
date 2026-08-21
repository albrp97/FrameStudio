# TICKET-006 - Integrate Project Save and Reopen Recovery

**Ticket ID:** TICKET-006
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Phase:** PHASE-001
**Feature:** FEAT-003
**Capability links:** CAP-004, CAP-012
**Status:** complete
**Horizon:** first
**Priority:** 4
**Owner:** repository planning; implementer is not assigned
**Approval:** user-approved on 2026-08-21 before execution
**Source paths:** `vision.md`, `docs/specs/project-scope.md`,
`docs/planning/phases.md`, `docs/planning/features.md`,
`docs/planning/backlog.md`,
`docs/planning/tickets/closed/TICKET-004-preview-timeline-interaction.md`,
`docs/planning/tickets/closed/TICKET-005-versioned-project-persistence.md`,
`AGENTS.md`, `.github/aidd-config.yml`
**Dependencies:** TICKET-004 and TICKET-005; selected GUI/runtime; valid
  project persistence contract
**Risks:** UI state diverging from persisted state; confusing recovery after
  failed saves; stale source references; exposing a partial project as valid
**Affected surfaces:** editor save/open/reopen actions, project status,
playback/timeline state restoration, filesystem errors, manual smoke test
**Evidence path:** `evidence/save-reopen-recovery.md`

## Resolution

The implementation, persistence integration, and automated smoke flow are
complete. The user confirmed the target-workstation interaction check, so the
dependency blocker is resolved; the evidence record retains the absence of a
screenshot artifact as an accepted concern.

## Outcome

The user can save the open source project from the primary interface, close
and reopen it, and recover the same source and foundation state while clear
errors preserve the last valid project.

## Scope

- Add interface actions for saving, choosing or displaying the project path,
  reopening, and reporting project status.
- Connect the interface to the versioned persistence boundary.
- Restore source reference, foundation timeline/playback state, and duration
  after reopening.
- Surface invalid projects, unavailable sources, moved sources, and failed
  saves without silently replacing valid state.
- Add an end-to-end local smoke path for import, playback, save, close,
  reopen, and state comparison.

## Explicit non-goals

- Split, delete, export, CLI, multiple-source timelines, multiple tracks,
  composition, audio normalization, or FPS enhancement.
- Source relinking without an explicit policy and user-visible result.
- Destructive source modification or deletion.

## Observable requirements

- Given an open source project, saving from the interface should create a
  valid versioned project without changing the source.
- Given a valid saved project, reopening should restore the same source
  reference, foundation state, and duration.
- Given an invalid project or unavailable source, reopening should show an
  actionable error and preserve the last valid project state.
- Given a failed save, the previous valid project should remain reopenable.

## Validation and evidence

- Run focused integration tests for interface-to-persistence state transfer.
- Run the protected baseline command:
  `python3 -m unittest discover -s tests`.
- Perform the target-workstation smoke test covering import, play/pause/seek,
  save, close, reopen, duration, and source preservation.
- Record project round-trip and recovery observations at
  `evidence/save-reopen-recovery.md`, omitting private paths where possible.

## Protected behavior

Existing scripts, command names, curses workflows, tests, original media,
and safe partial-output behavior remain available and unchanged.

## Definition of done

- The primary interface can save and reopen the versioned one-source project.
- Reopened source and foundation state match the saved state.
- Invalid-source/project and failed-save paths are explicit and state-safe.
- Focused automated, baseline, and target-workstation evidence is recorded.
- Cutting, export, CLI, and future-phase features are not claimed.
