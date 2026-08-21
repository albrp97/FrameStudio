# TICKET-014 - Implement Deterministic One-Source Edit Commands

**Ticket ID:** TICKET-014  
**Objective:** OBJ-001  
**Scope:** SCOPE-001  
**Phase:** PHASE-003  
**Feature:** FEAT-008  
**Capability links:** CAP-004, CAP-006, CAP-012  
**Status:** complete  
**Closure:** user-authorized on 2026-08-21 after edit-command, persistence,
and local quality evidence; remote checks remain unavailable and are recorded
as an accepted warning.  
**Path history:** `tickets/open/TICKET-014-implement-one-source-edit-commands.md`
-> `tickets/closed/TICKET-014-implement-one-source-edit-commands.md`  
**Horizon:** first  
**Priority:** 3  
**Owner:** repository planning; implementer is not assigned  
**Approval:** user-approved on 2026-08-21 for implementation and testing;
configured remote checks remain unavailable  
**Provider:** auto; base and target branches are not configured in
`.github/aidd-config.yml`  
**Source paths:** `vision.md`, `docs/specs/project-scope.md`,
`docs/specs/capability-map.md`,
`docs/planning/phases/open/PHASE-003-repeating-the-basic-edit-through-agents.md`,
`docs/planning/features/open/FEAT-008-applying-one-source-edits-through-cli.md`,
`docs/planning/tickets/open/TICKET-012-select-deterministic-cli-contract-and-inspection-schema.md`,
`docs/planning/tickets/open/TICKET-013-implement-deterministic-project-inspection.md`,
`AGENTS.md`, `.github/aidd-config.yml`  
**Dependencies:** TICKET-012 and TICKET-013; completed one-source domain
operations and persistence behavior  
**Risks:** GUI/CLI semantic drift, invalid ranges, unsafe retries, partial
  saves, and unstable segment identifiers  
**Affected surfaces:** CLI adapter, project/timeline model, persistence,
structured errors, documentation, and tests  
**Evidence path:** `evidence/phase-003-cli-editing.md`

## Outcome

An agent can perform the supported one-source import/open, split, delete or
restore toggle, duration inspection, save, and reopen operations through
deterministic commands that preserve the existing project contract.

## Scope

- Implement first-horizon mutation commands using stable source and segment
  identifiers.
- Reuse the same validation and timeline semantics as the editor.
- Define and implement repeated-operation behavior for supported commands.
- Preserve atomic project writes and last-valid-state recovery.
- Return contract-compliant results and structured errors.

## Explicit non-goals

- Export execution, which is covered by TICKET-015.
- Multiple sources, tracks, segment movement, copy/paste, composition, audio,
  FPS, or natural-language orchestration.
- Replacing the existing media-preparation scripts.

## Observable requirements

- Given a valid one-source project, supported CLI edits produce the documented
  segment state, identifiers, deletion state, and edited duration.
- Given an invalid range or unknown identifier, the command fails
  deterministically without mutating valid project state.
- Given a repeated idempotent request, the result is deterministic and does
  not duplicate or corrupt segments.
- Given an interrupted or failed save, the last valid project remains
  reopenable and the source remains unchanged.

## Definition of done

- Import/open, split, delete/restore, duration, save, and reopen commands are
  documented and tested.
- Results and errors conform to TICKET-012.
- Existing editor behavior remains protected through shared domain validation.
- FEAT-008 edit evidence is recorded.

## Validation and evidence

- Command-level unit and persistence tests.
- Failure/retry tests for invalid ranges and failed writes.
- Disposable-media CLI round-trip smoke test with source-preservation evidence.
