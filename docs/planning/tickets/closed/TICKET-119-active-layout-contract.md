# TICKET-119 - Resolve Active Intervals and Section Framing

**Ticket ID:** TICKET-119
**Parents:** OBJ-001, SCOPE-001, PHASE-010, FEAT-036
**Capability links:** CAP-005, CAP-009, CAP-010, CAP-013
**Status:** complete
**Approval:** execution/delegation authorized by the 2026-10-09 orchestration
request and CHG-014 autonomous authorization; layout/transform contract review
and exact-profile automatic validation remain required
**Requirements:** DISC-010 / REQ-010-05
**Technical contract:** `../../../specs/synchronized-layout-contract.md`
(DESIGN-010-119); bounded geometry/media contract approved by the exact validator.
Verified115 shared-interface gate permits isolated implementation.
**Dependencies:** TICKET-115
**Affected surfaces:** project-to-layout planning, interval/section mapping,
shared composition geometry and tests
**Risks:** boundary frame errors, wrong track order or nested-transform semantics
**Evidence path:** `evidence/ticket-119-active-layout-contract.md`
**Path history:** created in `tickets/open/` on 2026-10-09
Moved unchanged-ID to `tickets/closed/` on 2026-10-09 (UTC) after source provider PASS.
**Completion evidence:** `evidence/ticket-125-phase010-functionality.md`,
source `981e5e2a`, CI `38004558177`, exact validator turns 18/19.

## Scope and acceptance

- Given half-open active intervals, should resolve1/2/3/4 sections in track
  order and no slot for excluded/inactive tracks. Gaps should be black and
  total duration should equal the last included endpoint.
- Given default/modified/triplicate blocks, should map source center to each
  section center using crop-to-fill, preserve independent transforms and keep
  triplicate inside that section, with no visual stereo-pan shift.

Approve shared interval, coordinate and transform-order contracts before code;
publish interfaces for preview/render/audio. No new decoder or runtime here.
Preserve1920x1080, source aspect ratios and hard boundaries.

## Automated functionality charter

Implemented executable:
`python3 -m unittest tests.test_editor_layout_plan_functionality.LayoutPlanFunctionalityTests.test_saved_four_track_project_plans_from_real_ffmpeg_sources`

Load a persisted four-track project via the supported planning boundary.
Inspect plans at exact starts/ends, gaps,1/2/3/4 active clips, exclusions and
nested triplicate. Assert section dimensions/order, center mappings, total
duration and independent transforms after save/reopen. Unit geometry tests
are supplemental; decoded pixel acceptance is121/125.

## Automatic functionality validation and completion

Execute this charter as the agent under CHG-014. Record `automaticValidation`
using Rubber Duck GPT-5.6 Luna high `all-validation`, never `userValidation`.

Setup: staggered clips and one triplicate/zoomed segment. After preview/render
integration, seek each active-count boundary.
Expected: full/halves/thirds/grid, correct center and isolated modifications.
Failure: inactive empty slot or source state leaking into another section.
Cleanup: close fixture. Record agent PASS/FAIL/BLOCKED.
Require design approval/readiness, charter and full normal gates before closure.

## Parallel ownership

After115, can overlap110/112/116 with isolated composition ownership.
120/121/122 consume this single contract; do not fork layout logic.

The exact-profile scoped implementation review released121/122 to consume
`framestudio.layout_plan`. Final decoded preview/render equivalence, aggregate
quality and configured delivery remain separate gates.
