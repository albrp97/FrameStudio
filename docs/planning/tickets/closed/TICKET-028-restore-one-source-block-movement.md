# TICKET-028 - Restore One-Source Block Movement

**Ticket ID:** TICKET-028
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Phase:** PHASE-002
**Feature:** FEAT-004
**Capability links:** CAP-003, CAP-012
**Status:** complete
**Closure:** user-approved on 2026-08-22 after successful implementation,
review evidence, and target-workstation validation; remote checks remain
unavailable and are recorded as an accepted warning.
**Path history:** `tickets/open/TICKET-028-restore-one-source-block-movement.md`
-> `tickets/closed/TICKET-028-restore-one-source-block-movement.md`
**Horizon:** first
**Priority:** 1
**Owner:** repository implementation in the active worktree
**Approval:** user-reported and implementation-authorized on 2026-08-22
**Provider:** auto; base and target branches are not configured in
`.github/aidd-config.yml`
**Source paths:** `docs/specs/project-scope.md`,
`docs/specs/capability-map.md`,
`docs/planning/phases/open/PHASE-002-cutting-and-exporting-one-source-safely.md`,
`docs/planning/features/open/FEAT-004-removing-unwanted-portions-from-one-source.md`,
`framestudio/app.py`, `framestudio/model.py`, and the user-provided
failure screenshot
**Dependencies:** TICKET-007 and TICKET-008; existing shared movement
operation and timeline persistence
**Risks:** incorrect ordering, changed source ranges, lost block state, and
GUI/CLI behavior drift
**Affected surfaces:** one-source timeline model, shared operations, GTK
keyboard movement, CLI movement, persistence, and regression evidence
**Evidence path:** `evidence/one-source-block-movement.md`

## Outcome

The user can split a one-source video into blocks and move a selected block
left or right with `Shift+Left` or `Shift+Right` without changing the source
media or losing block-owned state.

## Scope

- Allow one-source timelines to reorder complete segment blocks.
- Reuse the existing atomic movement and reflow semantics, with explicit
  timeline placement separate from each block's source interval.
- Preserve source intervals, deletion state, state, color, identity, and final
  duration while changing only block order.
- Keep the behavior available through the shared GUI and CLI domain paths.
- Report boundary moves as deterministic no-ops without mutating valid state.

## Explicit non-goals

- Multi-source placement changes, visual modifications, triplicate layouts,
  audio normalization, or FPS enhancement.
- Destructive source modification.

## Observable requirements

- Given a one-source timeline split into three blocks, moving the selected
  middle block left or right changes the block order.
- Given a moved one-source block, its source interval, identity, deletion state,
  owned state, and display color remain attached to that block.
- Given a move at either boundary, the operation reports no change and
  preserves the valid timeline.
- Given a one-source move through the GUI or CLI, the persisted project order
  and final duration remain equivalent after save/reopen.
- Given a moved one-source timeline, playback and subsequent timeline splits
  follow the reordered timeline while reading the preserved source intervals.

## Validation and evidence

- Add a failing model regression for one-source block movement.
- Add shared CLI coverage for one-source movement and persistence.
- Run the configured baseline, contract, smoke, and local quality commands.
- Capture a focused GTK flow showing the selected block changing position.
- Record the user-validation handoff and terminal maintainer result in
  `evidence/one-source-block-movement.md`.

## Definition of done

- `Shift+Left` and `Shift+Right` reorder one-source blocks.
- Existing mixed-source movement behavior remains unchanged.
- Source ranges, state, colors, duration, and persistence remain correct.
- Preview and timeline seeking follow the persisted block order.
- Focused regression, baseline, and applicable quality evidence is recorded.
- Maintainer validation is terminally `PASS`; configured commit and remote
  delivery closeout remain pending.
