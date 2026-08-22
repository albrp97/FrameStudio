# TICKET-023 - Expose Mixed-Source Timeline Operations Through the CLI

**Ticket ID:** TICKET-023
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Phase:** PHASE-004
**Feature:** FEAT-011
**Capability links:** CAP-002, CAP-003, CAP-007, CAP-012
**Status:** complete
**Closure:** user-approved on 2026-08-22 after successful implementation,
review evidence, and target-workstation validation; remote checks remain
unavailable and are recorded as an accepted warning.
**Path history:** `tickets/open/TICKET-023-exposing-mixed-source-timeline-operations-through-the-cli.md`
-> `tickets/closed/TICKET-023-exposing-mixed-source-timeline-operations-through-the-cli.md`
**Horizon:** future
**Priority:** 6
**Owner:** repository implementation in the active Phase 4 worktree
**Approval:** user-authorized on 2026-08-21 to prepare and implement all
current PHASE-004 open tickets; human validation remains required before
closure
**Provider:** auto; base and target branches are not configured in
`.github/aidd-config.yml`
**Source paths:** `vision.md`, `docs/specs/project-scope.md`,
`docs/specs/capability-map.md`,
`docs/planning/phases/open/PHASE-004-combining-mixed-source-footage.md`,
`docs/planning/features/open/FEAT-011-arranging-and-editing-a-mixed-source-timeline.md`,
`docs/planning/tickets/open/TICKET-019-implement-mixed-source-import-probing-and-persistence.md`,
`docs/planning/tickets/open/TICKET-021-implement-mixed-source-placement-and-move-operations.md`,
`docs/planning/tickets/open/TICKET-022-extending-segment-editing-and-multi-selection-across-sources.md`,
`docs/specs/cli-contract.md`, `AGENTS.md`, `.github/aidd-config.yml`
**Dependencies:** TICKET-019, TICKET-021, and TICKET-022; shared domain
operations; versioned CLI contract
**Risks:** GUI/CLI drift, ambiguous identifiers, non-deterministic retries,
incomplete error coverage, and accidental serialization of presentation state
**Affected surfaces:** CLI adapter, shared operations, project serialization,
structured errors, GUI action routing, documentation, and tests
**Evidence path:** `evidence/phase-004-cli-timeline-parity.md`

## Outcome

An agent can inspect and modify mixed-source ordering, atomic block movement,
selection, split, delete/restore, copy/paste, and duration through the same
deterministic domain behavior used by the editor.

## Scope

- Extend the versioned CLI contract for mixed-source inspection and edits.
- Expose source, clip, segment block, placement, insertion-cursor, selection,
  and duration identifiers.
- Expose deterministic operations for moving, copying, and pasting one or
  several blocks while preserving relative order and returning fresh
  identities for pasted instances.
- Route GUI and CLI requests through the same validation and mutation
  boundaries.
- Return structured errors for invalid cross-source operations and retries.
- Keep UI-only focus, pointer, and playback presentation out of persisted CLI
  state.

## Explicit non-goals

- Preview rendering or export execution.
- Visual modification authoring or cleaning, triplicate composition, audio
  normalization, or FPS enhancement.
- Replacing the existing first-horizon command contract.

## Observable requirements

- Given the same project and operation sequence, GUI and CLI produce equivalent
  persisted mixed-source state and duration.
- Given the documented block sequence, repeated CLI copy/paste and movement
  commands produce equivalent order, fresh identities, and source coverage.
- Given an invalid operation, both paths expose the same error category and
  preserve valid state.
- Given repeated idempotent commands, source, segment, selection-independent
  edit state, and identifiers remain stable.
- Given an inspection request, output is deterministic and redacts paths by
  default.

## Commands and quality gates

- `make test`
- `make contract`
- `make check`
- `make quality PYTHON=.venv/bin/python`
- CLI mixed-source smoke flow with redacted output

## Functionality flows

- Import, inspect, move, select, split, delete/restore, copy/paste, save, and
  reopen a mixed-source fixture through CLI commands.
- Run the same operation sequence through GUI-domain and CLI-domain adapters.
- Repeat a successful and failed command and compare state and errors.

## User validation before closure

Run the documented CLI flow on a disposable two-source project, including a
block copy/paste and move sequence, compare its reopened state with the GUI
workflow, and confirm that full paths are not emitted unless explicitly
requested.

## Protected behavior

The existing versioned JSON output, structured errors, path redaction,
one-source commands, GUI action semantics, and source-preservation boundary
remain protected.

## Definition of done

- Mixed-source CLI inspection, block editing, copy/paste, and edit commands
  are documented and tested.
- GUI/CLI parity, idempotency, error, and redaction evidence is recorded.
