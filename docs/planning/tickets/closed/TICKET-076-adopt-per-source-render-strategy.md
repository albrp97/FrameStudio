# TICKET-076 - Adopt Per-Source Render Strategy as the Enhanced Default

**Ticket ID:** TICKET-076
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Phase:** PHASE-008
**Feature:** FEAT-026
**Capability links:** CAP-005, CAP-011, CAP-012
**Status:** complete
**Horizon:** future
**Priority:** 2
**Owner:** repository planning; maintainer identity is not recorded
**Approval:** user-authorized on 2026-08-26 after the corrected 1920x1080/60
FPS Strategy A/B comparison; implementation may proceed under CHG-005
**Last updated:** 2026-08-28
**Source paths:** `docs/planning/reviews/CHG-005-adopt-per-source-render-default.md`,
`evidence/phase-008-render-strategy-comparison.md`,
`docs/planning/tickets/closed/TICKET-072-select-and-document-mixed-fps-render-default.md`,
`resolve_editor/export_interpolation.py`,
`resolve_editor/export_smart_render.py`,
`resolve_editor/export_delivery.py`,
`tests/test_editor_smart_render.py`,
`tests/test_editor_export_execution.py`,
`.github/aidd-config.yml`
**Dependencies:** TICKET-072 comparison evidence; existing output policy,
interpolation artifact gate, mixed-source planning, and safe-export helpers
**Risks:** per-segment preparation may increase temporary files; stream-copy
assembly requires compatible streams; interleaved sources and unsupported
rate conversions must not be reordered or silently degraded
**Affected surfaces:** enhanced-export routing, smart-render preparation,
interpolation, timeline-order assembly, progress, cancellation, verification,
temporary cleanup, and regression tests
**Evidence path:** `evidence/ticket-076-per-source-render-default.md`
**Protected behaviors:** fixed 1920x1080 delivery profile, source-level audio
decisions, atomic publication, output verification, cancellation cleanup,
legacy scripts, and source preservation
**Path history:** created at
`tickets/open/TICKET-076-adopt-per-source-render-strategy.md` -> moved to
`tickets/closed/TICKET-076-adopt-per-source-render-strategy.md`

## Outcome

Enhanced export uses the measured Strategy B route by default: each retained
timeline segment is smart-rendered or normalized at its native rate, eligible
segments are enhanced independently, and final clips are assembled in exact
timeline order with stream copy whenever the output streams are compatible.

## Scope

- Remove concat-first Strategy A from the normal enhanced-export selection.
- Prepare retained segments independently at native source rates while
  applying visual and source-level audio decisions exactly once.
- Interpolate each eligible prepared segment to the selected target rate.
- Concatenate final segments in timeline order without assuming each source is
  contiguous or appears only once.
- Keep a verified fallback for incompatible stream-copy joins, unsupported
  rate actions, and media requiring a filter-complex final render.
- Preserve progress, cancellation, atomic partial output, verification,
  cleanup, and source-preservation behavior.

## Explicit non-goals

- Changing non-enhanced export routing or legacy command behavior.
- Adding restoration, upscaling, denoising, new codecs, or new dependencies.
- Claiming the FFmpeg benchmark applies universally to RVE or other hardware.
- Removing the historical Strategy A benchmark or evidence.

## Observable requirements

- Given a mixed-FPS enhanced export, each retained segment should be prepared
  at its source rate before interpolation, rather than first normalizing all
  sources to the slowest rate.
- Given interleaved source segments, final output order should match timeline
  order and must not concatenate by source identity.
- Given compatible prepared/interpolated streams, final assembly should use
  concat-demuxer stream copy and avoid a second video re-encode.
- Given incompatible streams or unsupported rate actions, the exporter should
  use an explicit verified fallback rather than silently publishing an invalid
  or reordered output.
- Given cancellation, failure, or verification rejection, partial outputs and
  temporary artifacts should be cleaned while original sources remain intact.

## Definition of done

- Strategy B is the default enhanced-export route in production code.
- Focused unit and generated-media tests cover native-rate preparation,
  independent interpolation, timeline order, stream-copy assembly, fallback,
  cancellation, verification, cleanup, and source preservation.
- Existing repository tests and applicable smoke checks pass.
- Evidence records measured routing behavior and any unavailable
  target-workstation or RVE-specific checks.

## User-validation plan

- **Setup:** use a project with mixed dimensions, mixed FPS, cuts, and audio
  decisions; retain the original source files for comparison.
- **Steps:** export with enhancement enabled, inspect progress stages, probe the
  output, and compare source bytes before and after.
- **Expected result:** the output is fixed-profile 1920x1080 at the selected
  target FPS, follows timeline order, and completes through per-source
  enhancement without an unnecessary final re-encode when compatible.
- **Failure paths:** an unsupported backend/action, incompatible join, failed
  verification, cancellation, or missing media must surface explicitly and
  leave no published partial output.
- **Cleanup:** remove generated test media and temporary export artifacts.
- **Evidence response:** record route, output metadata, source preservation,
  progress/failure behavior, and environment limitations.
- **Pass criteria:** all technical and user-validation gates are terminal.

## Closure

TICKET-076 is complete. The user confirmed the implementation was manually
validated and requested closure of all tickets on 2026-08-28. Existing
quality and environment warnings remain preserved in the append-only evidence
record.
