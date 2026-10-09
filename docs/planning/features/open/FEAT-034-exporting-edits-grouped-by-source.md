# FEAT-034 - Exporting Edited Sources Independently per Track

**Feature ID:** FEAT-034
**Parents:** OBJ-001, SCOPE-001, PHASE-010
**Capability links:** CAP-004, CAP-005, CAP-006, CAP-007, CAP-008, CAP-011, CAP-012
**Status:** active
**Approval:** planning approved 2026-10-09; subsequent orchestration request
authorizes execution/delegation; CHG-014 supplies autonomous routine approval,
with exact-profile automatic validation and delivery gates retained
**Last updated:** 2026-10-09
**Requirements:** DISC-010 / REQ-010-03, refined by approved CHG-013
**Dependencies:** FEAT-035 stable track/source identity interface TICKET-115;
render integration requires existing TICKET-104 terminal integrity baseline
**Ticket links:** TICKET-112, TICKET-113, TICKET-114
**Evidence plan:** `evidence/ticket-112-source-output-plans.md`,
`evidence/ticket-113-source-output-rendering.md`,
`evidence/ticket-114-export-choice-controls.md` (future)
**Affected surfaces:** output settings/planning, existing smart-render pipeline,
GUI/CLI export controls, tests
**Risks:** confused source-versus-segment grouping, reordered duplicates,
cross-track deduplication, slot crop/pan leakage, naming collisions,
incorrect enhancement or partial success
**Path history:** created in `features/open/` on 2026-10-09

## Outcome, scope, and acceptance

Given Track 1 with A/B and Track 2 with A/C, optional separate export produces
`Track 1/A.mp4`, `Track 1/B.mp4`, `Track 2/A.mp4`, `Track 2/C.mp4`.
Each pair joins its included segments in that track's order, retaining copies
and individual modifications without mixing in other tracks, untouched
source ranges, placement gaps or excluded blocks. Stable track/source IDs
own the outputs, not filenames.

Treat every track independently as a single timeline. Each source reel fills
the full canvas with segment zoom/offsets/triplicate and normal source audio
without split-screen crop or spatial pan. Preserve existing selective
FPS/upscale, fastest-valid route, source audio handling and verified publication.
The same source on multiple tracks remains duplicated in separate files.

Source-only is allowed with one to four populated tracks. Empty/excluded-only
tracks produce no folders/files. Final output can be included or omitted;
default remains final-only. Reject selecting neither output or an empty edit.

No per-segment file explosion, additional whole-track combined output, or
synchronized source-layer mode. Multi-output resume is integrated in FEAT-038.

## Dependencies and parallel work

112 -> 113 -> 114. Planning can run alongside placement/layout work after
TICKET-115; pipeline and `app_export.py` writes need reserved ownership.
FEAT-038 consumes this feature's per-output result contract.
Standalone source rendering has no dependency on the simultaneous layout
renderer or fixed stereo mixer, preserving that independent work path.

## Verification and closeout

Plan/save/reopen commands, generated A/B exports with reordered/duplicated
segments across multiple tracks, decoded full-canvas and normal-stereo
checks, and GTK/CLI output-choice tests cover the requirements. Failure/retry
and final-only/source-only/combined validation complete in TICKET-124/125.
