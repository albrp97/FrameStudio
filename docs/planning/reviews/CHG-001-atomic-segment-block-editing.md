# CHG-001 - Atomic Segment Block Editing and Modification Inheritance

**Change ID:** CHG-001
**Type:** Material planning change
**Status:** approved-and-applied
**Date:** 2026-08-21
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Owner:** repository planning; maintainer identity is not recorded
**Approval:** User-authorized in the 2026-08-21 planning request; parent
PHASE-004 and FEAT-011 records are confirmed.
**Source paths:** `vision.md`, `docs/specs/project-scope.md`,
`docs/specs/capability-map.md`, `docs/specs/future-product-direction.md`,
`docs/planning/phases/open/PHASE-004-combining-mixed-source-footage.md`,
`docs/planning/phases/open/PHASE-006-focusing-and-composing-important-action.md`,
`docs/planning/features.md`,
`docs/planning/features/open/FEAT-011-arranging-and-editing-a-mixed-source-timeline.md`,
`.github/aidd-config.yml`
**Affected IDs:** PHASE-004, FEAT-011, TICKET-020, TICKET-021, TICKET-022,
TICKET-023, TICKET-027, CAP-003, CAP-009, CAP-010, PHASE-006
**Last updated:** 2026-08-21

## Request and classification

The user clarified that segments must behave as atomic blocks when moved or
copied/pasted. The requested examples are:

```text
s1 s2 s3 s4
delete s2       -> s1 s3 s4
copy/paste s3   -> s1 s3 s3 s4
paste at start  -> s3 s1 s3 s3 s4
move s1 left    -> s1 s3 s3 s3 s4
```

The user also requires segment-level zoom, triplicate, and X/Y offset
modifications to travel with a copied segment and to be inherited by both
children after a split, plus a **Clean modifications** action.

This is a material planning change because it expands the approved PHASE-004
timeline-editing outcome and adds cross-phase state-inheritance requirements.
It does not expand the first horizon or authorize application implementation.

## Decision

1. PHASE-004 now includes structural atomic-block movement, copy/paste,
   multi-selection, and split inheritance. Visual modification authoring and
   cleaning remain deferred to PHASE-006.
2. TICKET-020 owns the timebase, placement, insertion-anchor, identity, and
   split-inheritance rules. TICKET-021 owns block movement. TICKET-022 owns
   block copy/paste, split/delete/restore, and multi-selection. TICKET-023
   exposes the same operations through the CLI. TICKET-027 verifies the
   complete sequence.
3. PHASE-006 now owns the visual modification bundle: zoom, X/Y offsets,
   triplicate state, and layout parameters. Moving preserves it; splitting
   and copying clone it; cleaning resets it.
4. Copied and split triplicate segments receive fresh, independent linked
   groups. Cleaning a triplicate segment resets its linked group atomically.
5. No stable ID is renamed or moved. No ticket status changes, implementation
   branch, commit, push, or application-code change is part of this update.

## Normative behavior

- A segment block includes its source identity, source interval, deletion
  state, and segment-owned persisted state.
- Deletion remains non-destructive. A deleted block is excluded from active
  output and remains recoverable in the project model.
- Copying one or several blocks creates fresh segment identities, clones the
  persisted block state, preserves selected-block relative order, and leaves
  the originals unchanged.
- Pasting inserts the copied block sequence at an explicit timeline cursor.
- Moving reorders the complete block without changing its source interval or
  owned state.
- Splitting creates fresh child identities covering the original source range;
  both children inherit the parent's block-owned state and deletion state.
- In PHASE-006, the modification bundle includes zoom, X/Y offsets,
  triplicate mode, and layout parameters. **Clean modifications** resets that
  bundle to defaults without changing source coverage.

## Affected-artifact inventory

| Artifact | Previous contract | Approved change | Action |
|---|---|---|---|
| PHASE-004 | Mixed-source movement and selection; copy/paste was not explicit | Include atomic block movement, copy/paste, and split inheritance | Updated in place |
| FEAT-011 | Segment copy/paste excluded | Include structural block copy/paste and fresh identities | Updated in place |
| TICKET-020 | Timebase and placement only | Define insertion anchors, block identity, cloning, and split inheritance | Updated in place |
| TICKET-021 | Move clips/segments | Move complete atomic blocks and preserve state | Updated in place |
| TICKET-022 | Split/delete and multi-selection | Add atomic block copy/paste and state cloning | Updated in place |
| TICKET-023 | CLI ordering, movement, selection, and cuts | Add deterministic block copy/paste operations | Updated in place |
| TICKET-027 | End-to-end mixed-source editing without copy/paste | Verify block sequences, fresh IDs, and state preservation | Updated in place |
| PHASE-006 | Visual transform copy/paste was underspecified | Define modification inheritance and clean/reset behavior | Updated in place |
| CAP-003, CAP-009, CAP-010 | General future operation statements | Separate structural block semantics from visual bundle semantics | Updated in place |
| Future product direction and scope | Feature inventory without inheritance rules | Preserve the requested examples and reset behavior as durable context | Updated in place |

## Coverage and remaining gates

The planning records now preserve the requested behavior across the current
PHASE-004 ticket set and the future PHASE-006 composition boundary. No
application behavior is claimed as implemented. TICKET-018 remains the first
dependency-ordered PHASE-004 ticket, and every ticket still requires its own
preimplementation checklist, baseline, evidence, configured quality gates,
and user validation before execution or closure.

## Validation record

- Configuration, objective, scope, capability map, phase records, feature
  records, current ticket records, and future-product context were inspected
  before mutation.
- Existing open/closed lifecycle paths were preserved; no record was moved or
  duplicated.
- The feature index and backlog were synchronized with the clarified
  PHASE-004 contract.
- Repository-wide review found that FEAT-001 through FEAT-006 retain the older
  metadata shape and omit some newer fields such as explicit dependencies,
  risks, or evidence paths. This pre-existing planning-hygiene warning is
  outside CHG-001 and was not rewritten.
- This change is planning-only; application tests and delivery gates are not
  applicable until an implementation ticket is approved.
