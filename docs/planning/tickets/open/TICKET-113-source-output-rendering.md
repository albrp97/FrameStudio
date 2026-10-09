# TICKET-113 - Render Verified Edited Sources Independently per Track

**Ticket ID:** TICKET-113
**Parents:** OBJ-001, SCOPE-001, PHASE-010, FEAT-034
**Capability links:** CAP-005, CAP-008, CAP-011, CAP-012
**Status:** verifying
**Approval:** execution/delegation authorized by the 2026-10-09 orchestration
request and CHG-014 autonomous authorization; dependencies and exact-profile
automatic validation remain required
**Requirements:** DISC-010 / REQ-010-03, refined by CHG-013
**Dependencies:** TICKET-112, TICKET-104 (terminal route-integrity baseline)
**Affected surfaces:** existing smart-render/preparation/enhancement route,
per-output verification/publication and functionality tests
**Risks:** repeated model work, wrong enhancement eligibility, mixed partial success
**Evidence path:** `evidence/ticket-113-source-output-rendering.md`
**Path history:** created in `tickets/open/` on 2026-10-09

## Scope and acceptance

- Given final/source requests, should render exactly the requested edited
  outputs with retained cuts/order/duplicates/transforms, audio decisions,
  fixed canvas, selected FPS, conditional below-50-FPS enhancement and upscale.
  Source files are independent track/source reels: full-canvas individual
  zoom/offsets/triplicate and only that source's normal audio, without
  final-video split-screen crop, stereo pan, or other tracks' audio.
- Given incompatible fast path or a failed output, should use the existing
  verified fallback or report per-output failure/partial success. Publish
  only verified files and never replace source media.

Reuse the established route rather than a duplicate renderer; safe artifact
reuse is conditional on matching identities. Multi-output resume belongs to124.
No source-only whole-file shortcuts or universal speed claims.
No cross-track deduplication: the same source on two tracks is rendered into
two independently modified files. Combined multi-track final-video assembly
is integrated in TICKET-124/125, not a hidden dependency of standalone source
rendering on TICKET-121/123.

## Automated functionality charter

Implemented functionality selector:
`python3 -m unittest tests.test_editor_source_outputs_functionality`

The integrated public CLI/FFmpeg cases pass, with exact-profile review
pending. Actual forced AI and 29.97/59.94 source fixtures are not yet proved
by the integer-rate functionality cases. Do not infer those outcomes from
unit eligibility decisions.

Generate A/B/C color/timecode videos with distinct stereo audio,29.97/59.94
FPS and differing resolutions. Render source-only across1..4 tracks and
single-track final-only/combined via supported export commands. Two tracks
containing A/B and A/C must produce four source files, with A's distinct
track-specific modifications preserved. Probe counts/durations/FPS/dimensions,
decoded full-canvas pixels/order/copies, no placement gaps, only each source's
audio and preserved stereo balance without slot pan, and source hashes.
Inject one output failure; assert truthful results/no unverified publication.
Validate AI paths on the configured runtime; unavailable required runtime is
not a pass. Multi-track combined-mode acceptance follows in124/125.

## Automatic functionality validation and completion

Execute this charter as the agent under CHG-014. Record `automaticValidation`
using Rubber Duck GPT-5.6 Luna high `all-validation`, never `userValidation`.

Setup: Track 1 A/B, Track 2 A/C, A modified differently on each track.
Export source-only and inspect all four files; compare single-track combined
mode before final multi-track integration. Expected: four independently
framed source reels, no unwanted final file, and normal audio without pan.
Failure: whole originals, deduplicated A, baked split-screen, wrong order,
other-track audio or unsafe partials. Cleanup: delete only generated outputs.
Record agent PASS/FAIL/BLOCKED with visual observations. Require readiness/baseline,
charter, local checks, automatic validation, review and delivery before completion.

## Parallel ownership

After112/104, audio work can be isolated; serialize pipeline seam edits with121.
