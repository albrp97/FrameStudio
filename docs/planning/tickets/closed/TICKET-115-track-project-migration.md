# TICKET-115 - Persist One to Four Tracks with Legacy Migration

**Ticket ID:** TICKET-115
**Parents:** OBJ-001, SCOPE-001, PHASE-010, FEAT-035
**Capability links:** CAP-003, CAP-004, CAP-007, CAP-012, CAP-013
**Status:** complete
**Approval:** execution/delegation authorized by the 2026-10-09 orchestration
request and CHG-014 autonomous authorization; approved DESIGN-010-115,
dependencies and exact-profile automatic validation remain required
**Requirements:** DISC-010 / REQ-010-04
**Dependencies:** no new ticket; existing project schema/identity/timebase
**Affected surfaces:** `model_*`, persistence, autosave/recovery, schema
validation and tests
**Risks:** legacy timing loss, invalid track references, incompatible project save
**Evidence path:** `evidence/ticket-115-track-project-migration.md`
**Path history:** created in `tickets/open/` on 2026-10-09
Moved unchanged-ID to `tickets/closed/` on 2026-10-09 (UTC) after source provider PASS.
**Completion evidence:** `evidence/ticket-125-phase010-functionality.md`,
source `981e5e2a`, CI `38004558177`, exact validator turns 18/19.

## Scope and acceptance

- Given legacy FrameStudio/Resolve projects, should migrate atomically to
  equivalent one-track edits retaining every source/segment ID, exclusion,
  transform/triplicate, range, output choice and established playback/export.
- Given new projects, should persist up to4 ordered tracks, absolute
  non-negative placement, gaps, active-track identity and populated-track
  count; invalid/fifth tracks should fail before mutation.

Approve a versioned migration/timing contract before code. Explicitly
distinguish source time, original visible excluded-block spans, retained
one-track output timing and simultaneous absolute timing; do not silently
turn existing deleted blocks into new export gaps. Publish shared interfaces
for dependent tickets. No architecture/dependency replacement.

**Approved contract:** `../../../specs/track-project-migration-contract.md`
(DESIGN-010-115, approved 2026-10-09). The design agent identified a real decision about
excluded spans versus absolute synchronized output and explicit conversion
of old projects. The user explicitly approved fixed-time exclusion in
synchronized mode and confirmed legacy conversion preserving visible block
positions. Implementation still requires baseline/functionality evidence;
design approval does not satisfy validation or closure gates.

## Automated functionality charter

Planned test, to create during implementation:
`python3 -m unittest tests.test_editor_track_migration_functionality.TrackMigrationFunctionalityTests.test_track_project_migration`

The implementation module is isolated from TICKET-109's GTK fixture setup so
migration acceptance crosses the CLI/persistence boundary without requiring a
fake application or sharing mutable GUI fixtures.

Load actual legacy/current JSON fixtures via supported persistence commands,
save/reopen, recover autosave and compare IDs/timing/modifications and
one-track render plans. Create1..4 tracks/gaps, verify round trips and
populated-count semantics; invalid fifth/overlap/reference inputs leave
disk/current state unchanged. Assert original fixture/source hashes.

## Automatic functionality validation and completion

Execute this charter as the agent under CHG-014. Record `automaticValidation`
using Rubber Duck GPT-5.6 Luna high `all-validation`, never `userValidation`.

Setup: reopen an existing edit and a new four-track fixture. Save/reopen both.
Expected: old edit unchanged and all new placement/modifications retained.
Failure: lost exclusions, altered timing, silent migration or source mutation.
Cleanup: remove generated project copies only. Record agent PASS/FAIL/BLOCKED.
Require readiness/baseline, migration approval, charter and technical/automatic-validation/
review/delivery gates; dependent work waits for the verified interface.

## Parallel ownership

Independent of109 with strict model/UI ownership. Other model consumers
110/116 start only after this migration contract is stable.
