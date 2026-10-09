# CHG-013 - Independent Track-and-Source Exports

**Status:** approved for planning; implementation not authorized
**Date:** 2026-10-09
**Parents:** OBJ-001, SCOPE-001, CAP-MAP-001, PHASE-010
**Discovery:** `../../specs/multi-track-editing-contract.md` (DISC-010)
**Prior change:** CHG-012
**Approval:** User confirmed source files within each track and requested the
final planning update on 2026-10-09.
**Owner:** repository planning
**Affected subtree:** FEAT-034 / TICKET-112 through TICKET-114;
FEAT-038 / TICKET-124 and TICKET-125; contract, scope, capability coverage,
phase and indexes

## Decision

Supersede CHG-012's initial restriction disabling source-grouped export in a
multi-track project. Group separate edited outputs by stable track identity
and source identity, treating each track independently as a single timeline.

Track 1 containing A/B and Track 2 containing A/C produces
`Track 1/A.mp4`, `Track 1/B.mp4`, `Track 2/A.mp4`, `Track 2/C.mp4`.
Repeated source identities on different tracks remain separate; repeated
included blocks within a track remain in that track's source reel.

Each file joins that track/source pair's included blocks in track order,
without project placement gaps, other sources, or other tracks. Render on the
full 1920x1080 canvas with individual segment modifications and the existing
single-timeline framing, audio and smart-enhancement policies. No split-screen
slot crop, spatial pan, or other-track audio is applied.

Source exports remain optional/default-off; final export remains default-on
and can be omitted. Empty/excluded-only tracks or sources produce no files.
Reject no-output or entirely empty export requests explicitly.

## Impact and sequencing

- Keep PHASE-010, FEAT-034 and existing ticket IDs/paths; this is a refinement
  of one output feature, not a duplicate source-export feature.
- Output planning, safe folder naming, GUI/CLI results, checkpoint identity,
  media acceptance and guided validation must use track/source pairs.
- The final composition remains simultaneous, with dynamic layouts and fixed
  stereo mixing; independent source files have normal source audio.
- Source-export implementation does not depend on the simultaneous stereo
  compositor. Retain TICKET-115 -> TICKET-112 -> TICKET-113 -> TICKET-114 and
  the existing TICKET-104 render-integrity gate. Integration TICKET-124/125
  still consumes final-video and source-output paths.
- No track-only combined A+B export or synchronized source-layer mode is added.
- No application code, test implementation, staging, commit, push, or
  implementation-readiness claim is authorized.

## Verification focus

Generated two/four-track fixtures must prove distinct full-canvas versions of
the same source, exact per-track cuts/order/duplicates/modifications,
normal stereo audio without layout pan, mixed FPS/upscale routing, safe folder
collisions, empty-track omission, truthful partial success, and output-specific
resume/invalidation. Planned charters remain unimplemented until execution.
