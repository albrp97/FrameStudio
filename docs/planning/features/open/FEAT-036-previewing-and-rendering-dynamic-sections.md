# FEAT-036 - Previewing and Rendering Dynamic Sections

**Feature ID:** FEAT-036
**Parents:** OBJ-001, SCOPE-001, PHASE-010
**Capability links:** CAP-002, CAP-005, CAP-009, CAP-010, CAP-011, CAP-012, CAP-013
**Status:** active
**Approval:** planning approved 2026-10-09; subsequent orchestration request
authorizes execution/delegation; CHG-014 supplies autonomous routine approval,
with exact-profile automatic validation and delivery gates retained
**Last updated:** 2026-10-09
**Requirements:** DISC-010 / REQ-010-05; silent preview in REQ-010-06
**Dependencies:** FEAT-035 timing/model TICKET-115;
interactive preview after TICKET-117; render after TICKET-104 integrity gate
**Ticket links:** TICKET-119, TICKET-120, TICKET-121
**Evidence plan:** `evidence/ticket-119-active-layout-contract.md`,
`evidence/ticket-120-silent-composed-preview.md`,
`evidence/ticket-121-dynamic-video-render.md` (future)
**Affected surfaces:** interval/layout resolution, composition, playback,
per-segment focus/triplicate, enhanced render and tests
**Risks:** off-by-one interval changes, wrong center/transform order,
decoder drift, cross-cut interpolation, resource use and render/preview mismatch
**Path history:** created in `features/open/` on 2026-10-09

## Outcome, scope, and acceptance

Given 1/2/3/4 included clips active now, show full canvas, equal vertical
halves, equal vertical thirds, or equal row-major 2x2 quadrants. Track order
assigns slots; inactive tracks consume none. With no active clips, use black.
Duration reaches the last included endpoint across tracks.

Center-crop each source into its section. Preserve independent zoom/offsets
and triplicate within that section. Preview remains silent and shares exact
framing/timing semantics with rendering. Fixed output FPS, dimensions, source
preservation, and selective enhancement remain protected.

No visual pan added to simulate stereo pan, animated transitions, or new
playback/AI dependency without approval.

## Dependencies and parallel work

119 -> {120, 121}. TICKET-120 also needs TICKET-117 interactive controls.
Shared layout contract can be consumed by audio TICKET-122 in parallel with
preview work. Reserve shared composition/export helpers with TICKET-113.

## Verification and closeout

Project-to-plan interval charters, real GTK decoded-frame snapshots, and
generated-media render pixel/frame probes prove changing layouts, gaps,
centering, transforms, nested triplicate, and preview/export parity.
