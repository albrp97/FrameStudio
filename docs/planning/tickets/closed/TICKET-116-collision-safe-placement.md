# TICKET-116 - Move Blocks Across Tracks Without Collisions

**Ticket ID:** TICKET-116
**Parents:** OBJ-001, SCOPE-001, PHASE-010, FEAT-035
**Capability links:** CAP-003, CAP-012, CAP-013
**Status:** complete
**Approval:** execution/delegation authorized by the 2026-10-09 orchestration
request and CHG-014 autonomous authorization; dependencies and exact-profile
automatic validation remain required
**Requirements:** DISC-010 / REQ-010-04
**Dependencies:** TICKET-115
**Affected surfaces:** domain placement/split/copy/paste, track lifecycle,
source import target and tests
**Risks:** invalid overlap, pushing existing clips, partial multi-block mutation
**Evidence path:** `evidence/ticket-116-collision-safe-placement.md`
**Path history:** created in `tickets/open/` on 2026-10-09
Moved unchanged-ID to `tickets/closed/` on 2026-10-09 (UTC) after source provider PASS.
**Completion evidence:** `evidence/ticket-125-phase010-functionality.md`,
source `981e5e2a`, CI `38004558177`, exact validator turns 18/19.

## Scope and acceptance

- Given a moved block overlapping occupied/excluded blocks, should advance
  only that block to the first complete fitting interval after collisions.
  Existing blocks never shift; cross-track concurrency and gaps are allowed.
- Given move/split/copy/paste/import, should preserve source/segment state,
  active-track assignment and invariants. Add/remove empty tracks explicitly;
  reject destructive populated-track removal and invalid operations atomically.

Touching half-open boundaries do not collide. No arbitrary snap/grid policy,
auto-pushing, fifth track or source mutation.

## Automated functionality charter

Implemented executable:
`python3 -m unittest tests.test_editor_track_placement_functionality.TrackPlacementFunctionalityTests.test_persisted_real_media_track_editing_round_trips_exactly`

Through supported editing commands on a persisted fixture, move a long block
through chained collisions and insufficient gaps, across tracks and to a
touching boundary; split/copy/paste and import into active track. Assert
exact starts, no existing-block movement, independent cloned visual state,
excluded occupancy, valid track removal errors and unchanged source hashes.

## Automatic functionality validation and completion

Execute this charter as the agent under CHG-014. Record `automaticValidation`
using Rubber Duck GPT-5.6 Luna high `all-validation`, never `userValidation`.

Setup: track1 with separated blocks, track2 with gaps. Move a block into an
occupied interval and a free gap through eventual UI/CLI.
Expected: only moved block snaps forward, source modifications survive.
Failure: overlap, existing-block push or destructive track removal.
Cleanup: discard fixture edits. Record agent PASS/FAIL/BLOCKED.
Require readiness/baseline, charter/local checks, automatic-validation/review/delivery gates.

## Parallel ownership

After115, overlap112/119 with isolated ownership. Serialize shared model
operations with110; publish placement interface before117/118.
