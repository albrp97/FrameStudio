# TICKET-070 - Benchmark Concat-First Enhancement Strategy

**Ticket ID:** TICKET-070
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Phase:** PHASE-008
**Feature:** FEAT-026
**Capability links:** CAP-005, CAP-011, CAP-012
**Status:** complete
**Closure:** closed on 2026-08-26 after Strategy A completed its matched
concat-first run with terminal output-integrity, playability, cleanup, and
source-preservation evidence.
**Horizon:** future
**Priority:** 2
**Owner:** repository planning; maintainer identity is not recorded
**Approval:** user-authorized on 2026-08-26 for PHASE-008 planning; execution
requires the configured preimplementation and approval gates
**Last updated:** 2026-08-26
**Source paths:** `docs/planning/features/closed/FEAT-026-comparing-mixed-fps-render-strategies.md`,
`docs/planning/tickets/closed/TICKET-069-define-comparable-mixed-fps-render-benchmarks.md`,
`framestudio/export_smart_render.py`, `framestudio/export_interpolation.py`,
`framestudio/export_delivery.py`, `tests/test_editor_smart_render.py`,
`tests/test_editor_export_execution.py`, `.github/aidd-config.yml`
**Dependencies:** TICKET-069 protocol; PHASE-005 audio/delivery policy;
PHASE-007 interpolation fallback and verification
**Risks:** the route may hide per-source work in preparation or lose source
frame-rate detail before enhancement; timing must include every stage
**Affected surfaces:** smart-render preparation, concat, interpolation,
temporary artifacts, output verification, benchmark evidence, and source safety
**Evidence path:** `evidence/phase-008-render-strategy-comparison.md`
**Path history:** `tickets/open/TICKET-070-benchmark-concat-first-enhancement-strategy.md`
-> `tickets/closed/TICKET-070-benchmark-concat-first-enhancement-strategy.md`
**Protected behaviors:** current concat-first implementation and its safe
fallback remain unchanged unless a later decision approves a change

## Outcome

Strategy A is measured end to end: prepare retained content, consolidate at
the minimum input FPS, then enhance the unified master to the target FPS.

## Scope

- Run the matched fixture and project from TICKET-069.
- Record per-source preparation, normalization, concatenation, interpolation,
  verification, and publication timing.
- Record output frame count/FPS, duration, audio, playability, sizes, resource
  use, and visual observations.
- Confirm whether the route preserves the documented audio and source-safety
  behavior.

## Explicit non-goals

- Changing the route or target-FPS policy.
- Comparing against unmatched media or a different output profile.
- Claiming quality from metadata alone.

## Observable requirements

- Given the benchmark protocol, all strategy-A stages should be visible in the
  report and use the same verification gates as strategy B.
- Given mixed input FPS, the report should show the minimum-FPS consolidation
  effect and final target-frame result.
- Given a failure or cancellation, temporary cleanup and source preservation
  should be recorded.

## Definition of done

- Strategy-A results are complete and reproducible.
- Timing and output-integrity data are available for TICKET-072.
- Any discrepancy from the documented route is recorded rather than hidden.

## User-validation plan

- **Setup:** use the exact fixture and protocol from TICKET-069.
- **Steps:** run the route, inspect stage timing, probe the output, and review
  frame/audio/duration and visual observations.
- **Expected result:** the unified-master path completes or reports a clear
  failure with no unsafe publication.
- **Failure paths:** missing backend, invalid output, or cleanup failure blocks
  the result and remains in evidence.
- **Cleanup:** remove partial/intermediate artifacts after verification.
- **Evidence response:** return the full stage and output report.
- **Pass criteria:** strategy A is measured with terminal correctness evidence.

## Closure

TICKET-070 was closed after the report recorded every Strategy A stage,
including minimum-FPS preparation, concatenation, unified enhancement,
metadata/frame verification, playability, cleanup, and source preservation.
