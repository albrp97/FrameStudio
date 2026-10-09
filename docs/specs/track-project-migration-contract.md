# Track Project Migration and Timing Contract

**Design ID:** DESIGN-010-115
**Parents:** DISC-010 / REQ-010-04 / PHASE-010 / FEAT-035 / TICKET-115
**Status:** approved for implementation, not implemented or verified
**Prepared:** 2026-10-09
**Owner:** orchestrator; grounded draft from GPT-5.6 Luna max design agent
**Product contract:** `multi-track-editing-contract.md`
**Ticket:** `../planning/tickets/open/TICKET-115-track-project-migration.md`

## Approved product decisions

Existing one-track edits keep excluded blocks visible but concatenate only
included blocks for playback/export. A synchronized absolute timeline cannot
both retain that occupied excluded span and compact later blocks to the same
space without violating same-track collision rules.

The user approved these choices through the orchestration clarification:

1. In absolute multi-track projects, Delete leaves the block's occupied
   position unchanged and excludes it from active composition. That time is
   filled by another active track or black/silence. Backspace is the operation
   that removes occupied time and ripples the affected track.
2. Legacy projects retain exact existing one-track output until an explicit
   conversion to synchronized placement. Conversion requires confirmation and
   preserves visible block positions, acknowledging changed output gaps.
   Never silently change timings or discard restorable blocks.

The user also approved schema v4, the existing integer microsecond timebase,
stable IDs, atomic migration and compatibility views subject to these choices.
Approval is a design decision, not passing implementation evidence.

## Proposed representation

Use schema v4 with timeline model version 1, extending the existing model,
not introducing a new persistence or playback framework.

- Reuse the existing integer microsecond timebase, `1/1000000`, and existing
  deterministic tick conversion. Reject booleans, negative/non-integer ticks,
  invalid ranges and non-finite legacy numeric values.
- Persist one to four ordered tracks with stable IDs and an active-track ID.
  Track array order defines display/layout order.
- Every block retains its segment/block/source identity, exclusion,
  modifications, triplicate, state and source range, and gains a track ID
  plus an absolute occupied range.
- Source range and occupied range are half-open and have equal positive
  durations. Speed changes remain out of scope.
- Persist one authoritative block representation under each track. Existing
  flattened/seconds accessors remain derived compatibility views, not a
  second mutable persisted copy.
- Persist `legacy-ripple` versus `absolute` timing mode to implement the
  approved compatibility strategy.

Do not persist new cached duration/count fields merely for convenience.
Prefer derived values; where existing compatibility serialization requires
them, validate them against canonical blocks. Source/output settings remain
unchanged by this migration.

## Distinct time projections

Source time is source-local and immutable during placement. Editing time
contains every occupied block, including excluded ones. Output time is derived
from the approved timing mode:

| Projection | Included blocks | Excluded spans and placement gaps |
|---|---|---|
| Legacy retained output | Concatenate in existing order | Omitted as before |
| Absolute final composition | Preserve absolute starts | Other active tracks or black/silence |
| Independent track/source reel | Concatenate only that pair's included blocks | Omitted |

An absolute composition ends at the last included endpoint, not the last
excluded block. Track/source reels never receive final split-screen framing or
layout audio pan. The same source on two tracks remains two independent pairs.

## Invariants and atomic validation

- Track and segment IDs are unique, active/source/track references resolve.
- Empty tracks survive save/reopen. Adding a fifth track or removing a
  populated track fails before mutation.
- Same-track overlap is forbidden, including excluded blocks; touching
  endpoints are valid. Cross-track overlap is permitted.
- Source ranges remain within their original source duration.
- Empty project state is valid for editing; export rejects no included output.
- Candidate mutation/migration validates completely before attaching state or
  atomically saving. Invalid input leaves current state and disk unchanged.
- Selection is persisted where already supported but does not change render
  identity. Track/source identity, timing mode and edits do.

## Legacy migration

Load v1-v3 FrameStudio/Resolve JSON without modifying the original file.
Normalize into one deterministic track and preserve all existing IDs, source
order/ranges, occupied positions, exclusions, visual state and output policy.
Where v1 has no segment ID, derive a stable ID from existing project/source
identity and legacy position, rather than generating a different ID on every
load. Existing `.resolve.json` and `resolve_editor` compatibility remain.

An old sequence containing included `[0,4)`, excluded `[4,6)` and included
`[6,10)` retains visible occupied spans and an eight-second concatenated
legacy output. It must not silently become a ten-second output with a hole.
The approved explicit conversion policy governs adding synchronized tracks.

Migration is pure normalization plus validation. Existing atomic
save/load/autosave/recovery boundaries perform writes only after success.
Saving a migrated copy writes canonical v4. Source fingerprints and original
fixture/source bytes remain protected. Report migration truthfully; do not
rewrite projects on inspect.

## Shared consumer interfaces

Freeze a minimal concrete API during approved TICKET-115 implementation:

- Ordered track/block lookup, active-track identity and occupancy.
- Legacy/absolute active interval projections and unambiguous source mapping.
- Stable `(track_id, source_id)` grouping for independent source reels.
- Editing occupancy, included-duration sums and actual final duration with
  distinct names and meanings.
- A mutation revision suitable for TICKET-110's bounded removal receipt.

TICKET-110 owns atomic track-local removal and stale-Undo rejection.
TICKET-116 owns collision-safe placement. Neither changes source ranges.
TICKET-119 consumes one shared active-interval projection for layout.
TICKET-112 consumes stable pairs; TICKET-124 owns finalized output/checkpoint
fingerprints. Do not implement those tickets incidentally in migration.

## Scope and ownership

TICKET-115 primarily owns existing `model_types.py`, `model_timeline.py`,
`model_timeline_validation.py`, `model_project.py` and required persistence
adapters, plus isolated migration tests. Consumers receive minimal compatible
updates necessary to preserve current behavior, not premature multi-track UI
or rendering implementation. Reserve overlapping `app_project.py` writes
until TICKET-109 integration is finished.

After the verified interface is available, TICKET-112 and TICKET-119 can
proceed independently. TICKET-110 and TICKET-116 share model/operation seams
and must serialize those writes or use one integration owner. No dependent
ticket is ready from this draft alone.

## Required executable functionality

Create and run:

```sh
python3 -m unittest tests.test_editor_track_migration_functionality.TrackMigrationFunctionalityTests.test_track_project_migration
```

Use actual supported JSON/CLI/persistence/autosave boundaries. Inspect legacy
v1/v2/v3 fixtures, save copies, reopen/recover and assert identities, ranges,
exclusions, modifications, output settings and exact retained timing. Verify
one to four tracks, gaps, cross-track overlap, empty tracks and active identity.
Invalid fifth tracks, overlap, reference and tick inputs must leave disk/current
state unchanged. Hash original fixtures/media before and after. Compare old
one-track render plans without claiming multi-track rendering exists.

This is a future test, not an implemented or passing test. Unit cases are
supplemental. CHG-014 supersedes guided waits with exact-profile
`automaticValidation` by Rubber Duck GPT-5.6 Luna high `all-validation`.
TICKET-104's export-integrity gate and actual review/delivery requirements
remain separate; no implementation pass is inferred from this contract.
