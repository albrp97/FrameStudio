# FEAT-011 - Arrange and Edit a Mixed-Source Timeline

**Feature ID:** FEAT-011
**Parent links:** OBJ-001, SCOPE-001, PHASE-004
**Capability links:** CAP-002, CAP-003, CAP-007, CAP-012
**Status:** complete
**Closure:** user-approved on 2026-08-22 after successful implementation,
review evidence, and target-workstation validation; remote checks remain
unavailable and are recorded as an accepted warning.
**Path history:** `features/open/FEAT-011-arranging-and-editing-a-mixed-source-timeline.md`
-> `features/closed/FEAT-011-arranging-and-editing-a-mixed-source-timeline.md`
**Horizon:** future
**Priority:** 2
**Owner:** repository planning; maintainer identity is not recorded
**Approval:** user-authorized on 2026-08-21 to continue with PHASE-004 ticket planning
**Source paths:** `vision.md`, `docs/specs/project-scope.md`,
`docs/specs/capability-map.md`,
`docs/planning/phases/open/PHASE-004-combining-mixed-source-footage.md`,
`docs/specs/future-product-direction.md`, `.github/aidd-config.yml`
**Dependencies:** FEAT-010 source identity; approved timebase, ordering, gap,
placement, atomic block, selection, and duration semantics
**Risks:** mixed timebases, timestamp drift, ambiguous gaps, ripple behavior,
duplicate block identities, lost segment-owned state, selection errors, and
inconsistent GUI/CLI edits
**Affected surfaces:** timeline model, segment operations, selection state,
playback navigation, GUI, CLI, persistence, and tests
**Evidence path:** `evidence/phase-004-mixed-source-movement.md`
**Planned tickets:** TICKET-020, TICKET-021, TICKET-022, TICKET-023

## Outcome

The user can arrange multiple source clips in one understandable sequence,
treat segments as atomic blocks for movement and copy/paste, edit them without
losing source identity or block state, select several segments for shared
timeline operations, and see the resulting final duration.

## Included

- Define a common timeline timebase and explicit source-to-timeline mapping.
- Represent clip order, source boundaries, gaps, placement, and edited
  duration.
- Treat each segment as an atomic block whose source interval and owned state
  move together.
- Move clips or blocks left and right using deterministic placement rules.
- Copy and paste one or several blocks at an explicit timeline cursor,
  preserving relative order, cloning persisted block state, and assigning
  fresh identities to pasted instances.
- Split a block into fresh child identities that inherit its segment-owned
  state.
- Keep each block's display color attached to its identity across movement,
  copy/paste, delete/restore, and persistence; assign fresh colors to split
  children.
- Preserve and extend split/delete behavior for segments from multiple
  sources.
- Select multiple clips or segments and apply supported shared timeline
  operations.
- Replace selection with a normal click, toggle membership with Ctrl-click,
  and select an inclusive ordered range with Shift-click.
- Navigate the composed timeline with clear source boundaries and frame/time
  semantics.

## Explicit non-goals

- Authoring or clearing visual modification bundles; structural block
  operations preserve state for the later PHASE-006 modification model.
- Triplicate composition, keyframed transforms, automatic audio normalization,
  or 60 FPS enhancement.
- Unspecified multi-track professional-NLE behavior.

## Acceptance outcomes

- Given sources with different frame rates and durations, timeline placement
  and final duration are deterministic under the approved timebase policy.
- Given a clip or segment move, ordering, gaps, source identity, and duration
  update without mutating source media.
- Given segments `s1 s2 s3 s4`, deleting `s2`, copying/pasting `s3`, pasting
  that block at the beginning, and moving `s1` left produces the corresponding
  active order `s1 s3 s3 s3 s4` with fresh identities for pasted blocks.
- Given a copied block, its source interval, deletion state, and persisted
  segment-owned state are cloned while the original remains unchanged.
- Given a moved or copied block, its display color follows the block; given a
  split block, its children have distinct fresh colors.
- Given a split block, both fresh children inherit the parent's segment-owned
  state and source coverage.
- Given a multi-selection, shared supported operations affect exactly the
  selected items and leave other items unchanged.
- Given a selected block, Ctrl+C followed by Ctrl+V inserts a fresh copy
  immediately after that block and shifts later blocks forward; the copied
  state and color remain attached to the new block.
- Given a split or delete/restore operation, source boundaries and edited
  duration remain correct after save/reopen.

## Evidence plan

- Timeline invariant and block-transformation tests across mixed timebases.
- GUI and CLI operation tests for order, movement, copy/paste, selection,
  split, delete, restore, and duration.
- Manual mixed-source navigation and editing evidence on representative media.

## Protected behavior

The one-source timeline, frame stepping, split/delete toggle, final-duration
display, source preservation, and deterministic Phase 3 operations remain
valid when a project contains only one source.
