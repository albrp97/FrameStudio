# TICKET-043 - Preserve Triplicate Group Lifecycle

**Ticket ID:** TICKET-043
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Phase:** PHASE-006
**Feature:** FEAT-018
**Capability links:** CAP-009, CAP-010, CAP-012
**Status:** complete
**Closure:** user-approved on 2026-08-23 after PHASE-006 implementation,
automated verification, shared target-workstation validation, review, and
local delivery evidence; remote checks remain unavailable and are recorded as
an accepted warning.
**Horizon:** future
**Priority:** 6
**Owner:** repository planning; maintainer identity is not recorded
**Approval:** user-authorized on 2026-08-22 to create and implement the
PHASE-006 ticket set; the completed outcome was confirmed by the user on
2026-08-23
**Provider:** auto; base and target branches are not configured in
`.github/aidd-config.yml`
**Source paths:** `docs/planning/tickets/open/TICKET-040-preserve-visual-modifications-through-block-edits.md`,
`docs/planning/tickets/open/TICKET-041-define-triplicate-group-and-layout-policy.md`,
`docs/planning/tickets/open/TICKET-042-implement-linked-triplicate-composition.md`,
`docs/planning/features/open/FEAT-018-creating-linked-triplicate-compositions.md`,
`framestudio/operations.py`, `framestudio/model_project.py`,
`.github/aidd-config.yml`
**Dependencies:** TICKET-040, TICKET-041, and TICKET-042; approved linked
group identity and atomic block operations
**Risks:** cloned groups may accidentally share state, deletion may leave
orphaned instances, and clean may reset only part of a group
**Affected surfaces:** timeline operations, linked-group identity, split and
copy/paste, delete/restore, clean/reset, selection, tests, and evidence
**Evidence path:** `evidence/phase-006-triplicate-lifecycle.md`
**Last updated:** 2026-08-23
**Path history:** `tickets/open/TICKET-043-preserve-triplicate-group-lifecycle.md`
-> `tickets/closed/TICKET-043-preserve-triplicate-group-lifecycle.md`

## Outcome

Triplicate groups remain independent, recoverable, and atomically editable
through the full segment lifecycle.

## Scope

- Clone a fresh linked group when a triplicate segment is split or
  copy/pasted.
- Preserve group state when blocks move, reorder, delete, or restore.
- Clean or disable all three instances atomically.
- Prevent shared mutable state between original and cloned groups.
- Add invariants for group membership, instance roles, and orphan cleanup.

## Explicit non-goals

- New triplicate layout policy or base controls.
- Project persistence, CLI exposure, final rendering, or 60 FPS enhancement.
- Changes to ordinary non-triplicate block identity or color semantics.

## Observable requirements

- Given a triplicate segment is split, each resulting segment should have a
  fresh independent group with cloned values.
- Given a triplicate segment is copied/pasted, the inserted segment should
  have a fresh group and the original should remain unchanged.
- Given a group moves, deletes, restores, or reorders, its three instances
  should remain associated and ordered correctly.
- Given a group is cleaned or disabled, all instances should reset atomically
  without changing source intervals, colors, or duration.
- Given a cloned group is edited, no value in the original group should change.

## Commands and quality gates

- `python3 -m unittest discover -s tests`
- `make check`
- `make contract`
- `make quality PYTHON=.venv/bin/python`

## Functionality flows

- Activate triplicate, adjust values, split, and compare both groups.
- Copy/paste a triplicate block and mutate only the inserted group.
- Move, delete/restore, reorder, and clean a group while checking invariants.

## User validation before closure

Confirm that split and copy/paste create independent linked groups, all
three instances move and clean together, and ordinary segment colors,
identities, source ranges, and duration remain correct.

## Protected behavior

Existing atomic segment operations, colors, selection, source-level audio
decisions, fixed output canvas, source preservation, and legacy workflows
remain unchanged.

## Definition of done

- Group lifecycle and cloning are deterministic and tested.
- No orphaned or shared linked-group state remains after supported edits.
- User-facing lifecycle evidence is recorded.

## Closure

The triplicate group lifecycle is complete under the reviewed PHASE-006
delivery checkpoint. Provider-side checks remain unavailable because no
remote or upstream is configured.
