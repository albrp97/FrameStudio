# FEAT-008 - Apply One-Source Edits Through the CLI

**Feature ID:** FEAT-008
**Parent links:** OBJ-001, SCOPE-001, PHASE-003
**Capability links:** CAP-004, CAP-006, CAP-012
**Status:** complete
**Closure:** user-approved on 2026-08-22 after successful implementation,
review evidence, and target-workstation validation; remote checks remain
unavailable and are recorded as an accepted warning.
**Path history:** `features/open/FEAT-008-applying-one-source-edits-through-cli.md`
-> `features/closed/FEAT-008-applying-one-source-edits-through-cli.md`
**Horizon:** first
**Priority:** 2
**Owner:** repository planning; maintainer identity is not recorded
**Approval:** user-approved on 2026-08-21 to continue PHASE-003 planning
**Source paths:** `vision.md`, `docs/specs/project-scope.md`,
`docs/specs/capability-map.md`, `docs/planning/phases/open/PHASE-003-repeating-the-basic-edit-through-agents.md`,
`docs/specs/future-product-direction.md`, `.github/aidd-config.yml`
**Dependencies:** FEAT-007 CLI contract; PHASE-001/PHASE-002 project and
timeline domain behavior; completed TICKET-011 export boundary
**Risks:** CLI edits diverging from interface semantics, unsafe retries,
partial project writes, invalid ranges, and export decisions that differ from
the editor
**Affected surfaces:** CLI commands, project model, timeline operations,
persistence, export integration, structured errors, and automation tests
**Evidence path:** `evidence/phase-003-cli-editing.md`

## Outcome

Given a one-source project, an agent can import or open it, split and delete
segments, inspect duration, save and reopen state, and export through the same
safe domain behavior used by the editor.

## Included

- Deterministic commands for first-horizon source import/open, split, delete,
  restore/toggle where supported, duration inspection, save, reopen, and export.
- Stable source and segment identifiers in mutation requests and results.
- Explicit idempotency and repeated-operation behavior.
- Reuse of the verified export boundary, output validation, and source
  preservation behavior.
- Actionable structured errors for invalid ranges, missing sources,
  unsupported media, unavailable tools, failed saves, and failed exports.

## Explicit non-goals

- Multiple-source timelines, multiple tracks, segment movement across sources,
  copy/paste, composition, triplicate layouts, audio normalization, or FPS
  enhancement.
- A natural-language command interpreter or remote project service.
- Replacing the existing media-preparation scripts.

## Acceptance outcomes

- Given a valid one-source project, each supported CLI operation produces the
  same observable project state and edited duration as the corresponding domain
  operation in the interface.
- Given a repeated idempotent operation, the result is deterministic and does
  not corrupt or duplicate segment state.
- Given a failed mutation or export, the last valid project, source, and last
  valid output remain intact.
- Given a successful export, the CLI reports the verified output path and
  validation result without exposing an unverified partial file.

## Evidence plan

- Command-level tests for import/open, split, delete, duration, save/reopen,
  and export.
- Failure and retry tests covering invalid ranges, missing tools, and partial
  output recovery.
- Disposable-media CLI smoke test with ffprobe metadata and source
  preservation evidence.
- Machine-readable examples documenting successful and failed operations.
