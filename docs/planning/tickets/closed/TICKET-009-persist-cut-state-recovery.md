# TICKET-009 - Persist and Recover Cut State Safely

**Ticket ID:** TICKET-009  
**Objective:** OBJ-001  
**Scope:** SCOPE-001  
**Phase:** PHASE-002  
**Feature:** FEAT-006  
**Capability links:** CAP-004, CAP-012  
**Status:** complete  
**Horizon:** first  
**Priority:** 3  
**Owner:** repository planning; implementer is not assigned  
**Approval:** user-approved on 2026-08-21 before execution  
**Provider:** auto; base and target branches are not configured in
`.github/aidd-config.yml`  
**Source paths:** `vision.md`, `docs/specs/project-scope.md`,
`docs/planning/phases.md`, `docs/planning/features.md`,
`docs/planning/tickets/closed/TICKET-006-save-reopen-recovery.md`,
`docs/planning/tickets/closed/TICKET-007-segment-model-and-cut-semantics.md`,
`docs/planning/tickets/closed/TICKET-008-split-delete-editor-workflow.md`,
`AGENTS.md`, `.github/aidd-config.yml`  
**Dependencies:** TICKET-007 and TICKET-008; existing atomic versioned
project persistence  
**Risks:** incompatible schema evolution, partial writes, stale source
identity, restoring inconsistent segment state  
**Affected surfaces:** project schema, persistence validation/migration,
save/reopen UI integration, recovery errors, persistence tests  
**Evidence path:** `evidence/persist-cut-state-recovery.md`

## Resolution

The versioned project contract now persists ordered segment boundaries,
deletion state, playhead, and derived edited duration. Schema version 1
projects migrate to an active initial segment, while malformed and
inconsistent state remains explicit and atomic save safety is preserved.

## Outcome

Saving and reopening a cut project restores its segment order, boundaries,
deletion decisions, playhead, and edited duration without modifying the source
or exposing a partial project as valid.

## Scope

- Extend the versioned project contract with segment and deletion state.
- Define compatibility behavior for PHASE-001 projects without segment data.
- Restore segment state and edited duration through the existing save/reopen
  flow.
- Preserve source identity and validate it using the existing source policy.
- Keep failed or interrupted writes from replacing the last valid project.
- Surface malformed, incompatible, or stale cut state as actionable errors.

## Explicit non-goals

- Export execution, output validation, or output recovery; covered by
  TICKET-010 and TICKET-011.
- Automatic source relinking, multiple sources, multiple tracks, CLI parity,
  triplicate layouts, audio normalization, FPS enhancement, or destructive
  media changes.

## Observable requirements

- Given a valid cut project, save then reopen should restore segment order,
  boundaries, deletion state, playhead, and edited duration.
- Given a PHASE-001 project without segment state, reopening should preserve
  its valid foundation behavior under the documented compatibility rule.
- Given malformed or incompatible segment data, reopening should report the
  reason and preserve the last valid project state.
- Given a failed save, the previous valid project remains reopenable and the
  source remains unchanged.

## Validation and evidence

- Add round-trip, compatibility, malformed-data, and failed-write tests.
- Run `python3 -m unittest discover -s tests`, `make check`, and
  `git diff --check`.
- Perform the manual split/delete/save/close/reopen/source-preservation flow.
- Record schema version, migration behavior, recovery observations, and
  artifacts in `evidence/persist-cut-state-recovery.md`.

## Quality gates

- TICKET-007 and TICKET-008 terminal evidence is required.
- Baseline, local quality, persistence integration, and user-facing recovery
  evidence are required.
- Remote checks remain a configured but unavailable PR gate.

## Protected behavior

The PHASE-001 project schema, save/reopen behavior, explicit source
relinking errors, existing scripts, source media, and last-valid-project
preservation remain protected.

## Definition of done

- Cut state round-trips through the versioned project file.
- Compatibility and malformed-state behavior is explicit and tested.
- Failed saves preserve the last valid project and source.
- Focused, baseline, and manual recovery evidence is recorded.
- Export behavior is not claimed as complete by this ticket.

## Completion evidence

- Focused persistence tests:
  `python3 -m unittest tests.test_editor_model tests.test_editor_persistence`
- Full local gate: `make check` (70 tests passed, compilation and diff checks
  passed).
- Persisted edit smoke: `make smoke`.
- Evidence record: `evidence/persist-cut-state-recovery.md`
- Accepted warning: target-workstation visual save/reopen confirmation still
  needs user confirmation; no screenshot artifact is available in this
  session.
