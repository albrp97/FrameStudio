# TICKET-075 - Recommend Restoration Pipeline and Gates

**Ticket ID:** TICKET-075
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Phase:** PHASE-008
**Feature:** FEAT-027
**Capability links:** CAP-005, CAP-011, CAP-012
**Status:** complete
**Prior blocker:** the original generic TICKET-074 candidate benchmark was
unavailable, so the recommendation began as a bounded research draft.
**Horizon:** future
**Priority:** 3
**Owner:** repository planning; maintainer identity is not recorded
**Approval:** user-authorized on 2026-08-26 for PHASE-008 planning; execution
requires the configured preimplementation and approval gates
**Last updated:** 2026-08-28
**Source paths:** `docs/planning/features/open/FEAT-027-researching-video-restoration-and-upscaling.md`,
`docs/planning/tickets/open/TICKET-073-survey-video-upscaling-denoise-and-compression-recovery.md`,
`docs/planning/tickets/open/TICKET-074-benchmark-restoration-candidates.md`,
`resolve_editor/export_smart_render.py`, `resolve_editor/export_interpolation.py`,
`resolve_editor/export_delivery.py`, `README.md`, `.github/aidd-config.yml`
**Dependencies:** TICKET-073 survey and TICKET-074 benchmark evidence;
review of licenses, runtime constraints, and source-safety boundaries
**Risks:** a recommendation can become an accidental commitment if integration
steps, fallback, and approval boundaries are not explicit
**Affected surfaces:** future export pipeline stages, model/runtime policy,
quality gates, fallback behavior, documentation, and future planning
**Evidence path:** `evidence/phase-008-restoration-research.md`
**Protected behaviors:** existing smart render, interpolation, audio,
verification, atomic publication, legacy scripts, and source preservation

## Outcome

The project has a bounded recommendation for whether and how restoration could
fit the future media pipeline, with explicit quality, safety, licensing, and
runtime gates.

## Scope

- Synthesize survey and benchmark evidence.
- Recommend candidate stages, ordering relative to smart render and FPS
  enhancement, input/output constraints, fallback, and verification.
- Define minimum quality, temporal-stability, playability, source-safety,
  performance, license, and maintenance gates for future implementation.
- State what should not be implemented and identify the smallest follow-up
  planning unit.

## Explicit non-goals

- Implementing or enabling a restoration pipeline.
- Adding model downloads, dependencies, codecs, or UI controls.
- Treating the recommendation as approval for a future implementation.

## Observable requirements

- Given the research evidence, the recommendation should cite candidate
  benefits, failure modes, cost, and licensing.
- Given an integration point, the report should define output verification,
  fallback, cleanup, cancellation, and source-preservation requirements.
- Given insufficient evidence, the recommendation should remain deferred and
  name the missing evidence.

## Definition of done

- A source-linked recommendation and non-recommendation list is complete.
- Future implementation gates and an explicit follow-up boundary are recorded.
- No production code or dependency is added.

## User-validation plan

- **Setup:** review the survey, benchmark matrix, recommendation, and gates.
- **Steps:** inspect the proposed pipeline order, fallback, quality criteria,
  license boundary, and smallest future implementation unit.
- **Expected result:** the recommendation is actionable but cannot be mistaken
  for production support.
- **Failure paths:** unsupported claims, missing gates, or license ambiguity
  block the recommendation.
- **Cleanup:** remove research-only artifacts not needed for traceability.
- **Evidence response:** return the recommendation, exclusions, and follow-up
  boundary.
- **Pass criteria:** a future implementation can be planned without silently
  adding restoration to the current editor.

## Closure

TICKET-075 is complete. The source-linked survey, the concrete TICKET-077
benchmark, and the expanded TICKET-078 comparison now provide the bounded
recommendation, exclusions, implementation gates, and confidence limits
required by this ticket. The recommendation remains research-only and does
not enable restoration in production.

The user explicitly confirmed that all tickets were done and requested their
closure on 2026-08-28.

**Path history:** created at
`tickets/open/TICKET-075-recommend-restoration-pipeline-and-gates.md` -> moved
to `tickets/closed/TICKET-075-recommend-restoration-pipeline-and-gates.md`.
