# TICKET-110 - Remove Blocks with Track-Local Ripple and Undo

**Ticket ID:** TICKET-110
**Parents:** OBJ-001, SCOPE-001, PHASE-010, FEAT-033
**Capability links:** CAP-003, CAP-012
**Status:** verifying
**Approval:** execution/delegation authorized by the 2026-10-09 orchestration
request and CHG-014 autonomous authorization; contract review, dependencies
and exact-profile automatic validation remain required
**Requirements:** DISC-010 / REQ-010-02
**Dependencies:** TICKET-115
**Affected surfaces:** timeline/project removal operations, history,
persistence adapters and functionality tests
**Risks:** stale history, double-counted ripple, source-coverage invariants
**Evidence path:** `evidence/ticket-110-ripple-removal-undo.md`
**Path history:** created in `tickets/open/` on 2026-10-09

## Scope and acceptance

- Given selected included/excluded blocks on one or several tracks, should
  atomically remove instances and ripple only each affected track by its
  removed durations, preserving unaffected tracks and remaining intentional gaps.
- Given Undo, should restore exact IDs, selection, positions, track, flags,
  source intervals, transforms and triplicate. Invalid removal or stale
  history should fail explicitly without overwriting newer edits.

Approve the bounded removal/history contract before code. Relax legacy
complete-source-coverage validation only for explicitly removed instances;
retain valid half-open source ranges and compatibility. No universal
undo/redo or cross-restart Undo; preserve Delete/restore and source media.

The exact-profile116 validator approved the bounded removal/history contract:
at most20 deep-copied runtime receipts, original-coordinate ripple calculation,
revision plus runtime identity stale checks, monotonic Undo commits and
conservative exact-state history rebasing. Model implementation is serialized
after116; GUI and CLI workers consume its existing placement interface only.

## Automated functionality charter

Implemented functionality selector:
`python3 -m unittest tests.test_editor_ripple_removal_functionality`

The exact-profile validator released the bounded model/API gate. TICKET-111
remains dependent on the separate TICKET-117 GTK release. Aggregate quality,
delivery and lifecycle closeout remain pending.

Through the supported project-command boundary, remove multiple selected
blocks across two tracks, Undo, remove again and save/reopen actual JSON.
Assert exact original restoration before save, correct persisted removal,
source hashes, excluded-block removal, and atomic failures/stale-history
rejection. Test non-adjacent removals to prove durations are counted once.

## Automatic functionality validation and completion

Execute this charter as the agent under CHG-014. Record `automaticValidation`
using Rubber Duck GPT-5.6 Luna high `all-validation`, never `userValidation`.

Setup: two tracks, three blocks and a gap on track 1. Remove its middle block,
Undo, then remove two blocks together through the eventual controls.
Expected: track 2 unchanged, correct left shift and exact restoration.
Failure: other-track drift, lost modifications, wrong duration or stale Undo.
Cleanup: discard the test edit. Record agent PASS/FAIL/BLOCKED with observations.
Require readiness/baseline before coding and charter/local checks, exact-profile
automatic validation, review and delivery before completion.

## Parallel ownership

After TICKET-115, can overlap source-output/layout work with isolated files.
Serialize shared `model_*` writes with TICKET-116; freeze removal API before111.
