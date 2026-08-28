# CHG-008 - Add Production Upscale Enhancement

**Change ID:** CHG-008
**Type:** Material planning change
**Status:** approved-and-applied
**Date:** 2026-08-27
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Parent links:** PHASE-008
**Owner:** repository planning; maintainer identity is not recorded
**Approval:** User-authorized by the request to implement optional
SuperUltraCompact upscale enhancement, expose it beside FPS enhancement, and
benchmark the resulting render-order strategies.
**Source paths:** `vision.md`, `docs/specs/project-scope.md`,
`docs/specs/future-product-direction.md`,
`docs/planning/phases/open/PHASE-008-optimizing-responsive-preview-and-media-strategy.md`,
`docs/planning/features/open/FEAT-027-researching-video-restoration-and-upscaling.md`,
`docs/planning/features/open/FEAT-026-comparing-mixed-fps-render-strategies.md`,
`docs/planning/tickets/open/TICKET-076-adopt-per-source-render-strategy.md`,
`FPS-ENHANCEMENT-RESEARCH.md`, `.github/aidd-config.yml`
**Affected IDs:** PHASE-008, FEAT-028, TICKET-079, TICKET-080, CAP-005,
CAP-011, CAP-012
**Coverage links:** existing fixed-canvas export, source-preservation,
per-source enhancement, composition, project persistence, CLI parity, and
render-strategy benchmark evidence
**Evidence path:** `evidence/ticket-079-production-upscale-enhancement.md`
**Last updated:** 2026-08-27

## Request and classification

The user requested a production export option that uses the locally available
SuperUltraCompact model, never downscales source pixels during enhancement,
targets 1080p according to source orientation, works for normal and triplicate
composition, and is available through both the GTK export panel and the CLI.
The user also requested generated mixed-orientation fixtures and a benchmark
of render-order strategies covering smart rendering, FPS enhancement,
upscaling, concatenation, and audio handling.

This is a material planning change because the approved PHASE-008 and FEAT-027
records explicitly kept restoration research-only and prohibited production
upscaling, project-schema changes, and editor controls. The change remains in
the future PHASE-008 boundary and does not expand the first-horizon scope or
replace the existing default when the new option is disabled.

## Decision

1. Add FEAT-028 for an opt-in, policy-driven production upscale path and its
   controlled benchmark.
2. Add TICKET-079 for the implementation and TICKET-080 for the real-media
   render-order benchmark and recommendation.
3. Keep FEAT-027 and TICKET-078 as research records; do not reinterpret the
   cross-model benchmark as production approval for any other model.
4. Use SuperUltraCompact through the existing local RVE runtime. Do not vendor
   model weights, add a dependency manager, or download proprietary assets.
5. Preserve the fixed 1920x1080 output contract, source media, atomic partial
   publication, audio policy, cancellation, and verification behavior.
6. Make the policy disabled by default so existing exports remain unchanged
   unless the user explicitly selects upscale enhancement.
7. Treat missing runtime/model capability as an explicit export error rather
   than silently falling back to a different model or claiming enhancement.

## Required evidence and boundaries

- Orientation thresholds, target dimensions, and no-downscale behavior must be
  covered by unit tests and output metadata checks.
- Project persistence, GUI state, CLI state, combined FPS/upscale routing,
  normal composition, triplicate composition, source preservation, cleanup,
  and failure paths require regression evidence.
- The benchmark must use the requested three 40-second fixtures, the
  concatenated/triplicated 30-second edit, comparable audio and output
  settings, and a redacted machine-readable and human-readable report.
- Timing, output size, metadata, playability, and visual observations must be
  reported separately; a single local fixture must not support universal
  performance claims.
- User visual validation and configured review gates remain pending until the
  implementation and benchmark are complete.

## Superseding implementation note

TICKET-081 records the later user-requested default correction for the editor
and shared project/CLI policy: eligible-source upscale enhancement is enabled
when no explicit policy is persisted, while `--no-upscale-enhancement` and
`set-upscale-policy --disable-upscale` remain supported. This supersedes the
default-disabled wording in decision 6 without changing the optional nature
of the feature, the orientation thresholds, or the source-preservation and
failure-safety requirements.
