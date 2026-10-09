# FEAT-035 - Arranging Four Synchronized Tracks

**Feature ID:** FEAT-035
**Parents:** OBJ-001, SCOPE-001, PHASE-010
**Capability links:** CAP-002, CAP-003, CAP-004, CAP-006, CAP-007, CAP-012, CAP-013
**Status:** complete
**Approval:** planning approved 2026-10-09; subsequent orchestration request
authorizes execution/delegation; CHG-014 supplies autonomous routine approval,
with exact-profile automatic validation and delivery gates retained
**Last updated:** 2026-10-09
**Requirements:** DISC-010 / REQ-010-04
**Dependencies:** existing source/project identities and timebase;
no new feature prerequisite
**Ticket links:** TICKET-115, TICKET-116, TICKET-117, TICKET-118
**Evidence plan:** `evidence/ticket-115-track-project-migration.md`,
`evidence/ticket-116-collision-safe-placement.md`,
`evidence/ticket-117-track-drag-controls.md`,
`evidence/ticket-118-track-cli-parity.md` (future)
**Affected surfaces:** project/schema, timeline model/geometry, GUI, CLI,
persistence/autosave and tests
**Risks:** migration loss, hidden collisions, changed source boundaries,
invalid selection and conflicting domain/UI writes
**Path history:** created in `features/open/` on 2026-10-09
Moved unchanged-ID to `features/closed/` on 2026-10-09 (UTC) after required tickets completed.
**Completion evidence:** `evidence/ticket-125-phase010-functionality.md`,
source `981e5e2a`, CI `38004558177`, exact validator turns 18/19.

## Outcome, scope, and acceptance

Given existing projects, migrate to one equivalent track. Given up to four
ordered tracks, place blocks at non-negative absolute times with intentional
gaps and cross-track concurrency. Given a colliding drop, move only the
dragged block forward until its whole duration fits; never push existing
blocks. Preserve all segment/source/visual state when moving tracks.

Add/remove empty tracks explicitly; reject a fifth or destructive populated
track removal. Active track owns new imports. Preserve split/copy/paste and
save/reopen/autosave/CLI behavior with one shared playhead.

No standalone audio tracks, hidden fifth track, silent data-loss migration,
or unrelated editor redesign.

## Dependencies and parallel work

115 -> 116 -> {117, 118}. 117 and 118 can be independent with GUI/CLI
ownership reserved. TICKET-115 publishes the interface consumed by
FEAT-033/034/036; they need not wait for all UI/CLI tickets to close.

## Verification and closeout

Actual legacy/current JSON round trips, placement commands, GTK drag events,
CLI editing, and source-preservation checks are required. Approve schema and
timebase migration before execution; never mark a contract decision as tested
runtime behavior.
