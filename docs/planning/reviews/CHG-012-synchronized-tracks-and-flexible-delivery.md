# CHG-012 - Synchronized Tracks and Flexible Delivery

**Status:** approved for planning; implementation not authorized
**Date:** 2026-10-09
**Parents:** OBJ-001, SCOPE-001, CAP-MAP-001
**Discovery:** `../../specs/multi-track-editing-contract.md` (DISC-010)
**Approval:** User approved the clarified contract and planning artifact writes.
**Owner:** repository planning
**Affected subtree:** new PHASE-010, FEAT-032 through FEAT-038,
TICKET-109 through TICKET-125

## Decision and rationale

Material scope extension: multiple synchronized video tracks were explicitly
deferred by SCOPE-001. Admit at most four tracks, automatic active-clip layouts,
fixed stereo export mixing, optional edited source-group outputs, uncluttered
selection metadata, and undoable track-local Backspace removal as a separate
future horizon. Keep the original delivered one-source horizon unchanged.

## Impact

- Extend existing capabilities CAP-001 through CAP-012 as mapped in DISC-010;
  add CAP-013 for synchronized simultaneous-track composition.
- Persistence/timing, preview, segment history/placement, audio, export,
  checkpoints, GUI, and deterministic CLI surfaces require coordinated work.
- Do not reopen or claim completion of existing phases/features/tickets.
  PHASE-009 and TICKET-104 remain their own delivery work. TICKET-108's
  below-50-FPS behavior is a protected baseline, not a newly passed gate.
- Preserve existing Delete/restore and all source-safety/rendering contracts.
  Silent preview is an approved intentional behavior change.
- The initial source-export restriction based on populated-track count was
  superseded by approved CHG-013 on 2026-10-09. The current contract allows
  independent track/source outputs with full-canvas framing and normal audio.

## Sequencing and approvals

User authorizes the approved parent contract, new phase, feature decomposition,
and focused tickets in this planning-only write. No child becomes execution
ready from this approval. Apply the PHASE-010 dependency graph, shared-file
ownership reservations, and ticket preimplementation gates before execution.
Do not require unrelated phase closure for independent metadata work; export
integration requires the final PHASE-009 route baseline when it is ready.

## Risks and verification focus

Schema incompatibility, same-track overlap, cross-track ripple, stale Undo,
layout-boundary/audio drift, clipped stereo mixes, redundant AI rendering,
cache identity aliasing, partial multi-output success, and GUI responsiveness
need explicit automated functionality evidence and guided user validation.
