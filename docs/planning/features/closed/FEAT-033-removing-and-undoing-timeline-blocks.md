# FEAT-033 - Removing and Undoing Timeline Blocks

**Feature ID:** FEAT-033
**Parents:** OBJ-001, SCOPE-001, PHASE-010
**Capability links:** CAP-003, CAP-006, CAP-012
**Status:** complete
**Approval:** planning approved 2026-10-09; subsequent orchestration request
authorizes execution/delegation; CHG-014 supplies autonomous routine approval,
with exact-profile automatic validation and delivery gates retained
**Last updated:** 2026-10-09
**Requirements:** DISC-010 / REQ-010-02
**Dependencies:** FEAT-035 model interface (TICKET-115);
UI integration after TICKET-117, not blanket FEAT-035 completion
**Ticket links:** TICKET-110, TICKET-111
**Evidence plan:** `evidence/ticket-110-ripple-removal-undo.md`,
`evidence/ticket-111-backspace-controls.md` (future)
**Affected surfaces:** model operations/history, persistence, selection,
timeline shortcuts, CLI and tests
**Risks:** cross-track ripple, double-counted removal, stale Undo, text-entry capture
**Path history:** created in `features/open/` on 2026-10-09
Moved unchanged-ID to `features/closed/` on 2026-10-09 (UTC) after required tickets completed.
**Completion evidence:** `evidence/ticket-125-phase010-functionality.md`,
source `981e5e2a`, CI `38004558177`, exact validator turns 18/19.

## Outcome, scope, and acceptance

Given selected segments, Backspace removes the instances and ripples only
their tracks; Undo restores exact pre-operation state. Given Delete, retain
existing excluded-block/restore behavior. Given multi-selection, removal is
one atomic transaction. Preserve original media and unrelated tracks.

No general-purpose undo/redo or cross-restart history guarantee. Removal
history semantics must be approved before coding in TICKET-110.

## Dependencies and parallel work

TICKET-110 can proceed after model/migration stabilization alongside
export-plan/layout work, but conflicts with TICKET-116 model writes must be
serialized. TICKET-111 follows TICKET-110 and track-drag integration TICKET-117.

## Verification and closeout

Command-boundary removal/save/reopen/Undo tests plus GTK keyboard/selection
tests cover the requirements. Guided user checks compare Delete with Backspace
and Undo; technical/review/delivery evidence is required before closure.
