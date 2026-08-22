# TICKET-022 - Extend Segment Editing and Multi-Selection Across Sources

**Ticket ID:** TICKET-022
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Phase:** PHASE-004
**Feature:** FEAT-011
**Capability links:** CAP-002, CAP-003, CAP-007, CAP-012
**Status:** complete
**Closure:** user-approved on 2026-08-22 after successful implementation,
review evidence, and target-workstation validation; remote checks remain
unavailable and are recorded as an accepted warning.
**Path history:** `tickets/open/TICKET-022-extending-segment-editing-and-multi-selection-across-sources.md`
-> `tickets/closed/TICKET-022-extending-segment-editing-and-multi-selection-across-sources.md`
**Horizon:** future
**Priority:** 5
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
`docs/planning/tickets/open/TICKET-020-defining-mixed-source-timebase-and-placement-semantics.md`,
`docs/planning/tickets/open/TICKET-021-implement-mixed-source-placement-and-move-operations.md`,
`AGENTS.md`, `.github/aidd-config.yml`
**Dependencies:** TICKET-020 and TICKET-021; stable segment identity; existing
split/delete/restore semantics
**Risks:** selecting the wrong source interval, cross-source boundary errors,
inconsistent delete/restore duration, and accidental non-selected mutations
**Affected surfaces:** segment model, selection model, split/delete operations,
timeline UI, CLI, persistence, and tests
**Evidence path:** `evidence/phase-004-multi-selection-editing.md`

## Outcome

The user can select several clips or segments in a mixed-source timeline and
apply supported split, delete, restore, copy/paste, and shared timeline
operations without losing source, block, or segment identity.

## Scope

- Extend existing split and delete/restore semantics to mixed-source projects.
- Treat each segment as an atomic block for editing and copying.
- Copy and paste one block or a selected group at an explicit timeline cursor;
  preserve relative order and clone source interval, deletion state, and
  persisted segment-owned state into fresh identities without changing the
  originals.
- Split a block into fresh child identities that inherit the parent's
  segment-owned state and deletion state.
- Keep each block's persisted display color attached to its identity: movement
  and copy/paste preserve it, while split children receive distinct fresh
  colors and delete/restore does not lose it.
- Implement multi-selection with clear selected and non-selected boundaries.
- Support normal-click replacement, Ctrl-click add/remove selection, and
  inclusive Shift-click range selection across the ordered timeline.
- Insert pasted blocks immediately after the selected block in both one-source
  and mixed-source timelines, shifting later blocks forward and expanding the
  timeline duration as needed.
- Apply supported shared timeline operations only to selected items.
- Recalculate final duration and preserve deleted items visibly and safely.
- Persist selection-independent edit state and expose deterministic CLI results.

## Explicit non-goals

- Authoring or clearing visual modification bundles; the structural block
  contract must preserve state for the later PHASE-006 modification model.
- Triplicate composition, keyframes, audio normalization, or FPS enhancement.
- Unspecified multi-track editing or source mutation.

## Observable requirements

- Given segments from multiple sources, split/delete/restore preserves stable
  source and segment identity and correct duration.
- Given `s1 s2 s3 s4`, deleting `s2`, copying/pasting `s3`, pasting at the
  beginning, and moving `s1` left produces active order `s1 s3 s3 s3 s4`;
  pasted blocks have fresh identities and originals remain unchanged.
- Given a copied or split block, its source interval, deletion state, and
  segment-owned state are cloned to the independent result.
- Given a moved or copied block, its display color follows the block; given a
  split block, each child has a distinct color from the parent and sibling.
- Given a multi-selection, a shared operation changes exactly the selected
  items and leaves all other items unchanged.
- Given one source split into blocks, copying a block and pasting it after the
  selected block creates a fresh block with the same source interval, state,
  deletion state, and color while preserving the original source duration and
  expanding only the timeline duration.
- Given a deleted segment, it remains visible and reversible while excluded
  from final duration and export planning.
- Given an invalid cross-source range or unknown identifier, valid state is
  preserved and a structured error is returned.

## Commands and quality gates

- `make test`
- `make contract`
- `make check`
- `make quality PYTHON=.venv/bin/python`
- `make smoke` with disposable mixed-source media

## Functionality flows

- Select segments from two sources, apply a shared supported operation, and
  inspect untouched segments.
- Split a selected segment, delete/restore one result, and verify duration.
- Copy/paste one block and then a selected group at different timeline
  cursors, checking relative order and fresh identities.
- Save/reopen after multi-selection editing and compare persisted state.

## User validation before closure

Select segments from at least two source clips, split one, toggle delete and
restore on selected items, copy/paste a block and a group, and confirm only
the intended blocks change and the final duration is correct.

## Protected behavior

The existing Delete toggle, visible deleted-segment treatment, frame stepping,
split-at-playhead behavior, stable IDs, and one-source CLI commands remain
compatible.

## Definition of done

- Multi-selection, atomic block, copy/paste, and cross-source segment
  operations are independently tested.
- Stable block colors survive movement, copy/paste, delete/restore, and
  persistence, while split children receive fresh colors.
- Invalid selection/range failures preserve valid state.
- GUI, CLI, persistence, duration, and real-media evidence is recorded.
