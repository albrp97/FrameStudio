# CHG-006 - Run REAL Video Enhancer Restoration Benchmark

**Change ID:** CHG-006
**Type:** Material planning change
**Status:** approved-and-applied
**Date:** 2026-08-26
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Owner:** repository planning; maintainer identity is not recorded
**Approval:** User-authorized by the request to benchmark a supplied degraded
video, include REAL Video Enhancer, and proceed without a separate acceptance
pause.
**Affected IDs:** FEAT-027, TICKET-074, TICKET-075, TICKET-077, PHASE-008
**Source paths:** `docs/research/video-restoration-strategies.md`,
`evidence/phase-008-restoration-research.md`,
`docs/planning/features/open/FEAT-027-researching-video-restoration-and-upscaling.md`,
`https://github.com/TNTwise/REAL-Video-Enhancer/tree/2.4.1`,
`.github/aidd-config.yml`
**Last updated:** 2026-08-26

## Request and classification

The user supplied a local compressed 480p-class video and authorized a
personal-use benchmark of restoration and upscaling options, including REAL
Video Enhancer, with no commercial-distribution constraint. The request adds a
concrete representative sample, a pinned external tool revision, generated
comparison outputs, and measured runtime/size/metadata evidence to the
previously blocked restoration benchmark work.

This is a material planning change because it changes the missing benchmark
dependency and adds a new external runtime/model evaluation boundary. It does
not authorize production integration or a change to the editor's default
export path.

## Decision

1. Add TICKET-077 under FEAT-027 for the concrete benchmark and comparison
   deliverables.
2. Treat the user-provided source as local-only test data; do not copy the
   original into the repository or persist its private path in evidence.
3. Build a reproducible fixture from three seeded, distinct 15-second source
   windows. The resulting fixture is 45 seconds; the request's "1 minute"
   description is not used to silently add a fourth clip.
4. Run the researched FFmpeg candidates and every locally available compatible
   restoration/upscaling path from the pinned REAL Video Enhancer checkout.
   Mark unavailable models, runtimes, and incompatible candidates explicitly.
5. Store generated comparison media and machine-readable measurements under
   an uncommitted evidence artifact directory. Preserve source hashes and
   keep production routing unchanged.

## Boundaries and gates

- No editor integration, dependency-manifest change, model default, or codec
  policy change is included.
- Every candidate writes to a new output path and is checked for playability,
  duration, frame count, resolution, audio, and output size.
- Runtime, GPU/backend, model, and license details are recorded separately
  from subjective visual observations.
- The result may recommend a future route but cannot claim universal quality
  or speed.
