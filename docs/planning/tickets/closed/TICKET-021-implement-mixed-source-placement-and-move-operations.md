# TICKET-021 - Implement Mixed-Source Placement and Move Operations

**Ticket ID:** TICKET-021
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Phase:** PHASE-004
**Feature:** FEAT-011
**Capability links:** CAP-002, CAP-003, CAP-007, CAP-012
**Status:** complete
**Closure:** user-approved on 2026-08-22 after successful implementation,
review evidence, and target-workstation validation; remote checks remain
unavailable and are recorded as an accepted warning.
**Path history:** `tickets/open/TICKET-021-implement-mixed-source-placement-and-move-operations.md`
-> `tickets/closed/TICKET-021-implement-mixed-source-placement-and-move-operations.md`
**Horizon:** future
**Priority:** 4
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
`docs/planning/tickets/open/TICKET-020-defining-mixed-source-timebase-and-placement-semantics.md`,
`AGENTS.md`, `.github/aidd-config.yml`
**Dependencies:** TICKET-019 and TICKET-020; shared project/timeline
operations; persistence and structured errors
**Risks:** misplaced clips, source identity loss, incorrect ripple/gap
duration, unsafe retries, and GUI/CLI semantic drift
**Affected surfaces:** timeline model, placement operations, duration display,
GUI timeline, CLI operations, persistence, and tests
**Evidence path:** `evidence/phase-004-mixed-source-movement.md`

## Outcome

The user can order multiple source clips in one timeline and move atomic
segment blocks left or right using deterministic placement rules while source
identity, block state, and final duration remain correct.

## Scope

- Represent mixed-source clip and segment-block placement using TICKET-020
  semantics.
- Implement deterministic insertion and left/right movement operations that
  move each selected block as one unit.
- Preserve each moved block's source interval, deletion state, and persisted
  segment-owned state and display color without splitting or mutating its
  identity.
- Update gaps, ordering, source boundaries, and final duration after movement.
- Persist movement decisions and expose structured invalid-operation errors.
- Keep movement behavior available through shared GUI and CLI domain paths.

## Explicit non-goals

- Multi-selection, split/delete expansion, or copy/paste.
- Preview composition, output normalization, audio handling, triplicate
  layouts, or FPS enhancement.
- Replacing or mutating source media.

## Observable requirements

- Given several imported sources, moving a clip produces the documented order
  and gap state without changing source identity.
- Given ordered blocks, moving a selected block left or right preserves its
  complete source interval, owned state, and display color while changing only
  its placement.
- Given a move at either timeline boundary, the operation is deterministic and
  reports invalid requests without mutating valid state.
- Given a moved clip, edited duration and persisted placement are identical
  after save/reopen.
- Given the same operation through GUI-domain and CLI-domain paths, the
  persisted project state is equivalent.

## Commands and quality gates

- `make test`
- `make contract`
- `make check`
- `make quality PYTHON=.venv/bin/python`
- `make smoke` with disposable mixed-source media

## Functionality flows

- Import three sources, reorder them, and inspect source boundaries.
- Move a block across a gap and compare final duration before and after.
- Move the first block left and a later block right, then verify block
  identity, source coverage, and order.
- Retry an invalid move and verify valid project state is unchanged.

## User validation before closure

Arrange at least three disposable clips, move each in both directions, confirm
the visual order and final duration, then save/reopen and confirm placement is
preserved.

## Protected behavior

One-source timeline navigation, final-duration display, split/delete state,
atomic persistence, and deterministic first-horizon CLI operations remain
unchanged.

## Definition of done

- Mixed-source placement and movement are implemented through shared domain
  operations with deterministic errors.
- Moving a block preserves its display color in the timeline and after
  save/reopen.
- Persistence, duration, GUI/CLI parity, and source-preservation evidence is
  recorded.
