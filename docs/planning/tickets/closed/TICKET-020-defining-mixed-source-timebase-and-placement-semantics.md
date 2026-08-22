# TICKET-020 - Define Mixed-Source Timebase and Placement Semantics

**Ticket ID:** TICKET-020
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Phase:** PHASE-004
**Feature:** FEAT-011
**Capability links:** CAP-002, CAP-003, CAP-007, CAP-012
**Status:** complete
**Closure:** user-approved on 2026-08-22 after successful implementation,
review evidence, and target-workstation validation; remote checks remain
unavailable and are recorded as an accepted warning.
**Path history:** `tickets/open/TICKET-020-defining-mixed-source-timebase-and-placement-semantics.md`
-> `tickets/closed/TICKET-020-defining-mixed-source-timebase-and-placement-semantics.md`
**Horizon:** future
**Priority:** 3
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
`docs/planning/tickets/open/TICKET-018-defining-multi-source-project-identity-and-relinking.md`,
`docs/planning/tickets/open/TICKET-019-implement-mixed-source-import-probing-and-persistence.md`,
`docs/specs/phase-002-cut-semantics.md`, `AGENTS.md`,
`.github/aidd-config.yml`
**Dependencies:** TICKET-018 and TICKET-019; representative mixed timebases;
approved source and segment identity
**Risks:** frame rounding, variable-frame-rate drift, ambiguous gaps,
unexpected ripple behavior, and duration disagreement between GUI and CLI
**Affected surfaces:** timeline model, timebase conversion, ordering,
placement, gaps, duration calculations, project schema, CLI, and tests
**Evidence path:** `evidence/phase-004-timebase-policy.md`

## Outcome

The project has explicit, deterministic rules for converting mixed-source
media into one timeline, including timebase, ordering, gaps, placement, source
boundaries, atomic segment blocks, copy/paste insertion, and final-duration
semantics.

## Scope

- Select and document the canonical project timeline timebase.
- Define source-to-timeline frame/time conversion and rounding behavior.
- Define ordering, insertion, gaps, ripple behavior, and boundary ownership.
- Define atomic block movement and copy/paste insertion-anchor semantics,
  including relative order, fresh identities, and state cloning.
- Define split inheritance for block-owned state and deletion state.
- Define edited-duration calculation for included and deleted intervals.
- Define behavior for variable-frame-rate sources and ambiguous timestamps.
- Provide representative examples and machine-checkable invariants.

## Explicit non-goals

- Implementing timeline UI or movement/copy/paste commands.
- Output-canvas scaling, audio normalization, triplicate layouts, or FPS
  enhancement.
- Professional multi-track behavior.

## Observable requirements

- Given sources with different frame rates, the same source intervals map to
  the same timeline positions on repeated runs.
- Given a gap or moved clip, final duration follows the documented inclusion
  and ripple rules.
- Given an atomic block move or copy/paste insertion, source coverage, block
  order, relative order, fresh identities, and owned-state cloning follow the
  same documented rules on repeated runs.
- Given a split block, both children inherit the parent's block-owned state and
  deletion state without changing source coverage.
- Given an ambiguous timestamp or unsupported timebase, the system reports a
  structured limitation instead of inventing timing.
- Given a one-source project, the existing frame-accurate cut semantics remain
  unchanged.

## Commands and quality gates

- `make test`
- `make contract`
- `make check`
- `make quality PYTHON=.venv/bin/python`
- Review of timebase examples and invariants

## Functionality flows

- Calculate placements for fixtures at 24, 30, and 60 FPS.
- Compare duration with and without explicit gaps.
- Evaluate the block sequence `s1 s2 s3 s4` after deleting `s2`, copying and
  pasting `s3`, pasting at the beginning, and moving `s1` left.
- Exercise a variable-frame-rate or ambiguous-timestamp fixture and inspect
  the documented limitation.

## User validation before closure

Review a timeline example containing two sources with different frame rates,
confirm the ordering/gap/ripple choices, confirm the block copy/paste and
split-inheritance examples, and confirm how final output duration is
calculated.

## Protected behavior

The existing one-source frame stepping, split boundaries, delete/restore
duration, and export timing semantics remain the compatibility baseline.

## Definition of done

- Timebase, placement, gap, rounding, duration, atomic-block, copy/paste, and
  split-inheritance rules are approved and documented with representative
  fixtures.
- Timeline invariants and one-source regression behavior are covered.
- FEAT-011 is implementation-ready without unresolved timing ambiguity.
