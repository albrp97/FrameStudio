# FEAT-028 - Adding Optional Upscale Enhancement

**Feature ID:** FEAT-028
**Parent links:** OBJ-001, SCOPE-001, PHASE-008
**Capability links:** CAP-005, CAP-011, CAP-012
**Status:** complete
**Change control:** approved and applied under CHG-008
**Horizon:** future
**Priority:** 2
**Owner:** repository implementation in the active worktree
**Approval:** User-authorized by the request to implement the upscale option
and benchmark its render strategies; execution remains subject to evidence,
user-validation, review, and delivery gates.
**Last updated:** 2026-08-28
**Source paths:** `docs/planning/reviews/CHG-008-add-production-upscale-enhancement.md`,
`docs/planning/phases/open/PHASE-008-optimizing-responsive-preview-and-media-strategy.md`,
`docs/specs/future-product-direction.md`, `FPS-ENHANCEMENT-RESEARCH.md`,
`framestudio/export_planning.py`, `framestudio/export_delivery.py`,
`framestudio/composition_render.py`, `.github/aidd-config.yml`
**Dependencies:** PHASE-007 FPS/export behavior; PHASE-006 composition;
TICKET-076 per-source render strategy; local RVE runtime and
SuperUltraCompact weights; FFmpeg/ffprobe
**Risks:** model availability, restoration cost, aspect-ratio edge cases,
temporary storage, GPU/runtime failure, visual cropping choices, and
interaction between spatial enhancement and FPS processing
**Affected surfaces:** project output settings, export planning and delivery,
RVE integration, FFmpeg scaling/composition, GTK export panel, CLI export,
tests, fixtures, benchmark reports, and evidence
**Evidence path:** `evidence/ticket-079-production-upscale-enhancement.md`
**Planned tickets:** TICKET-079, TICKET-080, TICKET-081
**Path history:** created at
`features/open/FEAT-028-adding-optional-upscale-enhancement.md` ->
`features/closed/FEAT-028-adding-optional-upscale-enhancement.md`

## Outcome

The editor can optionally enhance eligible landscape and portrait sources
toward 1080p with SuperUltraCompact while preserving source media, avoiding
source downscaling during enhancement, and retaining the established safe
export contract. The user can select the policy in the GTK export panel or
through the deterministic CLI, and the chosen render-order strategy is
supported by a reproducible target-workstation benchmark.

## Scope

- Define and persist a versioned upscale policy enabled by default for
  eligible sources, with an explicit opt-out and the SuperUltraCompact model
  selection.
- Enhance landscape sources whose short side is at or below 1000 pixels and
  portrait sources whose short side is at or below 720 pixels to a
  1080-pixel short side, preserving aspect ratio.
- Keep square and already-qualified sources unchanged by the spatial
  enhancement decision.
- Integrate restoration, spatial scaling, FPS enhancement, composition,
  audio, concatenation, verification, cancellation, and atomic publication
  without changing existing behavior when upscale is disabled.
- Benchmark the requested mixed-orientation fixture and render-order
  strategies, then document measured timing, size, output integrity, and
  bounded visual observations.
- Restore responsive source loading, sub-100% timeline zoom, and the
  validated GPU-backed editor interpolation route.

## Explicit non-goals

- Adding multi-track editing, new composition modes, arbitrary crop effects,
  or automatic downscaling.
- Adding other restoration models or treating the research candidate matrix
  as production support.
- Vendoring model weights, external runtimes, proprietary software, or new
  dependency-management infrastructure.
- Changing the fixed 1920x1080 delivery canvas or the existing export default
  when the new option is off.
- Claiming benchmark results are universal beyond the measured workstation
  and fixtures.

## Observable requirements

- Given an enabled policy and an eligible landscape source, the export should
  run SuperUltraCompact and produce an aspect-preserving 1080-pixel
  short-side intermediate without reducing either source dimension.
- Given an enabled policy and an eligible portrait source, the export should
  produce a 1080-pixel short-side intermediate suitable for the 1920x1080
  canvas and triplicate layout without downscaling that intermediate.
- Given a disabled policy or an ineligible source, the existing export path
  should remain selected and the source should not be sent to the model.
- Given combined FPS and upscale policies, spatial enhancement should occur
  in the documented per-source order before the selected FPS interpolation,
  with exact output frame count, duration, audio policy, and timeline order.
- Given missing model/runtime capability or a failed enhancement stage, the
  exporter should report the failure and remove partial output without
  publishing a substitute result.
- Given the benchmark fixture, the report should compare each requested
  render-order strategy with separate measured and visual evidence.

## Definition of done

- TICKET-079 implementation and targeted regression tests are complete.
- TICKET-080 fixtures, outputs, benchmark data, recommendation, and evidence
  are complete or explicitly blocked with the missing capability recorded.
- TICKET-081 editor responsiveness and GPU interpolation regressions have
  focused evidence and remain in the configured verification path until user
  validation is terminal.
- Existing editor, CLI, legacy-script, source-preservation, and export
  verification behavior remains covered.
- User validation, local quality, static analysis, and review are terminal
  before this feature is closed.

## User-validation plan

- **Setup:** use the requested landscape and portrait fixtures on the target
  workstation with the local RVE environment available, then open the
  generated plan and output reports.
- **Steps:** toggle upscale in the GTK panel and CLI, export with and without
  FPS enhancement, inspect normal and triplicate segments, reopen the saved
  project, and compare the source hashes and output metadata.
- **Expected result:** the enabled path identifies SuperUltraCompact, eligible
  sources reach the declared 1080p intermediate without downscaling, the
  output remains playable and fixed-profile, and the disabled path is
  unchanged.
- **Failure paths:** missing runtime/model, unsupported dimensions, failed
  FFmpeg/RVE execution, cancellation, invalid output, or source hash changes
  must remain visible and leave no published partial result.
- **Cleanup:** remove generated fixture and benchmark media only after
  inspection; never remove original source media or valid user outputs.
- **Evidence response:** return `PASS`, `FAIL`, `BLOCKED`, or approved
  `NOT APPLICABLE` with the relevant report and output paths.
- **Pass criteria:** policy, persistence, GUI/CLI parity, no-downscale
  behavior, safe delivery, benchmark evidence, and protected regressions are
  all covered.

## Closure

FEAT-028 is complete. TICKET-079 through TICKET-081 delivered the optional
upscale route, render-order benchmark, editor responsiveness corrections,
and GPU interpolation path. The user confirmed the feature was manually
validated and requested closure of all tickets on 2026-08-28. Existing
environment, remote-check, and benchmark limitations remain documented.
