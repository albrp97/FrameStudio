# TICKET-071 - Benchmark Per-Source Enhancement Strategy

**Ticket ID:** TICKET-071
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Phase:** PHASE-008
**Feature:** FEAT-026
**Capability links:** CAP-005, CAP-011, CAP-012
**Status:** complete
**Closure:** closed on 2026-08-26 after Strategy B completed its matched
per-source run with terminal output-integrity, playability, cleanup, and
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
`tests/test_editor_interpolation.py`, `.github/aidd-config.yml`
**Dependencies:** TICKET-069 protocol; PHASE-005 audio/delivery policy;
PHASE-007 interpolation and output verification
**Risks:** repeated model startup and concatenation can dominate time; joining
independently enhanced clips can introduce timing, audio, or boundary drift
**Affected surfaces:** per-source smart rendering, repeated interpolation,
final concatenation, temporary storage, output verification, and evidence
**Evidence path:** `evidence/phase-008-render-strategy-comparison.md`
**Path history:** `tickets/open/TICKET-071-benchmark-per-source-enhancement-strategy.md`
-> `tickets/closed/TICKET-071-benchmark-per-source-enhancement-strategy.md`
**Protected behaviors:** no production per-source route is enabled by this
benchmark; source preservation and safe cleanup remain mandatory

## Outcome

Strategy B is measured end to end: smart-render each source or clip with its
modifications, enhance each result to the target FPS, then concatenate the
final outputs.

## Scope

- Run the matched fixture and project from TICKET-069.
- Record per-source preparation, each enhancement invocation, final
  concatenation, verification, and publication timing.
- Record output frame count/FPS, duration, audio, playability, sizes, resource
  use, boundary behavior, and visual observations.
- Verify whether source frame rates are preserved before enhancement and
  whether final timing remains exact.

## Explicit non-goals

- Changing the production route or adding a second default.
- Comparing a different model, output profile, or quality setting.
- Treating more preserved input frames as sufficient evidence by itself.

## Observable requirements

- Given the benchmark protocol, every repeated stage and intermediate file
  should be visible in the report.
- Given mixed input FPS, the report should show per-source frame-rate
  preservation and final target-frame behavior.
- Given a failed stage or boundary mismatch, no unverified final output should
  be reported as successful.

## Definition of done

- Strategy-B results are complete and reproducible.
- Timing, storage, correctness, and visual data are comparable with strategy A.
- Boundary, audio, and cleanup behavior are explicitly evidenced.

## User-validation plan

- **Setup:** use the exact fixture and protocol from TICKET-069.
- **Steps:** run each per-source stage, inspect intermediate and final output,
  probe metadata, and compare boundaries and visual observations.
- **Expected result:** the route either completes with verified output or
  reports a bounded failure without source changes.
- **Failure paths:** repeated backend errors, drift, invalid output, or
  cleanup failures remain blockers in the report.
- **Cleanup:** remove partial/intermediate artifacts after verification.
- **Evidence response:** return the full stage, storage, and output report.
- **Pass criteria:** strategy B is measured with terminal correctness evidence.

## Closure

TICKET-071 was closed after the report recorded native-FPS preparation,
per-source enhancement, final concatenation, metadata/frame verification,
playability, cleanup, and source preservation.
