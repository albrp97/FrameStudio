# TICKET-121 - Render Dynamic Multi-Track Video Sections

**Ticket ID:** TICKET-121
**Parents:** OBJ-001, SCOPE-001, PHASE-010, FEAT-036
**Capability links:** CAP-005, CAP-009, CAP-010, CAP-011, CAP-012, CAP-013
**Status:** complete
**Approval:** execution/delegation authorized by the 2026-10-09 orchestration
request and CHG-014 autonomous authorization; dependencies and exact-profile
automatic validation remain required
**Requirements:** DISC-010 / REQ-010-05
**Dependencies:** TICKET-119, TICKET-104 (terminal route-integrity baseline)
**Affected surfaces:** export planning/preparation/composition, enhancement
ordering, verified output and tests
**Risks:** incorrect active-set boundaries, processing exclusions, cache aliasing
**Evidence path:** `evidence/ticket-121-dynamic-video-render.md`
**Path history:** created in `tickets/open/` on 2026-10-09
Moved unchanged-ID to `tickets/closed/` on 2026-10-09 (UTC) after source provider PASS.
**Completion evidence:** `evidence/ticket-125-phase010-functionality.md`,
source `981e5e2a`, CI `38004558177`, exact validator turns 18/19.

## Scope and acceptance

- Given a staggered project, should render119's active-only layouts/gaps in
  exact time order, with crop-to-fill centers and isolated transforms/triplicate.
- Given FPS/upscale/cuts, should preserve the existing per-source eligibility,
  hard boundaries and fastest valid verified fallback, fixed1920x1080,
  target FPS/frame count and original media.

Own video composition only;123 integrates the complete audio/video export.
Reuse per-source preparation safely without interpolation across cuts.
No new encoder/AI architecture or misleading universal fast-path claim.

## Automated functionality charter

Implemented functionality selector:
`python3 -m unittest tests.test_editor_video_compositor_functionality`

Initial exact-profile review returned BLOCKED for interpolation fallback and
framing/route evidence. The corrected candidate subsequently received a
bounded PASS, releasing TICKET-123. Fixture-delta confirmation also passed.
Aggregate quality remains pending. The evidence retains the historical
blocked decision and both corrected bounded decisions.

Generate four identifiable clips with staggered starts, a black gap,29.97/
59.94 FPS and varied resolution. Render through the supported export boundary;
probe dimensions/rate/frame count/duration and sample pixels immediately
before/after all layout changes. Assert centered marker positions, transforms,
triplicate confinement, no excluded range and unchanged source hashes.
Exercise validated enhancements when runtime is available; no fake AI pass.

## Automatic functionality validation and completion

Execute this charter as the agent under CHG-014. Record `automaticValidation`
using Rubber Duck GPT-5.6 Luna high `all-validation`, never `userValidation`.

Setup: four-track fixture, render final video. Expected: same framing/timing
as preview and correct transitions in active count; no fifth output section.
Failure: miscentered/warped images, edge bleed or duration loss.
Cleanup: remove generated outputs only. Record agent PASS/FAIL/BLOCKED.
Require readiness/baseline, media functionality and normal technical/automatic-validation/
review/delivery gates; whole export is gated on123/124.

## Parallel ownership

May overlap120/122 with isolated responsibilities; serialize pipeline
helpers with113 and cache integration124.
