# TICKET-112 - Plan Final and Independent Track/Source Outputs

**Ticket ID:** TICKET-112
**Parents:** OBJ-001, SCOPE-001, PHASE-010, FEAT-034
**Capability links:** CAP-004, CAP-005, CAP-007, CAP-012
**Status:** verifying
**Approval:** execution/delegation authorized by the 2026-10-09 orchestration
request and CHG-014 autonomous authorization; dependencies and exact-profile
automatic validation remain required
**Requirements:** DISC-010 / REQ-010-03, refined by CHG-013
**Dependencies:** TICKET-115
**Affected surfaces:** persisted output choices, export planning/naming,
source grouping and tests
**Risks:** folder/name collision, wrong pair grouping/order, cross-track deduplication
**Evidence path:** `evidence/ticket-112-source-output-plans.md`
**Path history:** created in `tickets/open/` on 2026-10-09

## Scope and acceptance

- Given Track 1 A/B and Track 2 A/C, should plan four independently edited
  outputs in track subfolders, keyed by stable track/source IDs. Retain
  included order, copies and per-track modifications; exclude placement gaps.
  Folder/file names should be sanitized, collision-safe and source-preserving.
- Given settings, should default to final-only, support combined/source-only,
  persist choices and reject neither-output/entirely empty edits. One to four
  populated tracks should allow source outputs; empty/excluded-only tracks
  and unused sources should produce none.

Define per-output request/result identity for TICKET-113/124. No rendering
implementation here. Plan standalone full-canvas/normal-source-audio jobs,
distinct from final split-screen/mixed-pan jobs. Preserve current final-only
planning and do not add whole-track combined files.

## Automated functionality charter

Implemented executable:
`python3 -m unittest tests.test_editor_source_output_plan_functionality.SourceOutputPlanFunctionalityTests.test_source_output_plan_roundtrip`

Use the supported export-plan/project-save boundary with1..4 tracks,
interleaved A/B/C, the same source on different tracks with different
modifications, copied/excluded blocks, gaps and colliding folder/file names.
Save/reopen and plan all mode combinations plus empty/excluded-only tracks.
Assert exact pair/output lists and ordering, standalone framing/audio intent,
safe destinations, explicit invalid errors and unchanged sources.

## Automatic functionality validation and completion

Execute this charter as the agent under CHG-014. Record `automaticValidation`
using Rubber Duck GPT-5.6 Luna high `all-validation`, never `userValidation`.

Setup: Track 1 contains A/B, Track 2 contains A/C, plus an empty track.
Inspect planned outputs and toggle final/source modes after controls exist.
Expected: four track/source files, no empty-track folder, source-only permitted
with multiple populated tracks, and explicit refusal of no-output choice.
Cleanup: close planner without rendering.
Record agent PASS/FAIL/BLOCKED. Require baseline/design readiness and terminal
functionality/local/automatic-validation/review/delivery gates before completion.

## Parallel ownership

Independent of placement/layout consumers after115; reserve persisted output
settings and planner writes against track migration and source-render work.

The exact-profile implementation review released113 after deterministic
hash-seed checks and final/source path-separation regressions. Whole-project
delivery and actual rendering remain separate gates.
