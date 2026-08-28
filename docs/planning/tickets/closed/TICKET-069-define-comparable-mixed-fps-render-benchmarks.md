# TICKET-069 - Define Comparable Mixed-FPS Render Benchmarks

**Ticket ID:** TICKET-069
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Phase:** PHASE-008
**Feature:** FEAT-026
**Capability links:** CAP-005, CAP-011, CAP-012
**Status:** complete
**Closure:** closed on 2026-08-26 after the matched fixture, stage protocol,
output profile, verification gates, and failure-reporting rules were executed
and recorded.
**Horizon:** future
**Priority:** 1
**Owner:** repository planning; maintainer identity is not recorded
**Approval:** user-authorized on 2026-08-26 for PHASE-008 planning; execution
requires the configured preimplementation and approval gates
**Last updated:** 2026-08-26
**Source paths:** `docs/planning/features/closed/FEAT-026-comparing-mixed-fps-render-strategies.md`,
`resolve_editor/export_smart_render.py`, `resolve_editor/export_interpolation.py`,
`resolve_editor/export_delivery.py`, `resolve_concat.py`, `resolve_fps.py`,
`benchmarks/`, `tests/test_editor_smart_render.py`,
`tests/test_editor_interpolation.py`, `.github/aidd-config.yml`
**Dependencies:** PHASE-005 audio policy; PHASE-007 export/interpolation
baseline; representative mixed-FPS sources; target-workstation storage
**Risks:** unequal work, cache state, intermediate-file I/O, or subjective
quality scoring can invalidate an otherwise precise timing comparison
**Affected surfaces:** benchmark definitions, export harness, fixture media,
output verification, resource measurement, and evidence reports
**Evidence path:** `evidence/phase-008-render-strategy-comparison.md`
**Path history:** `tickets/open/TICKET-069-define-comparable-mixed-fps-render-benchmarks.md`
-> `tickets/closed/TICKET-069-define-comparable-mixed-fps-render-benchmarks.md`
**Protected behaviors:** existing concat-first route, delivery profile,
audio decisions, atomic publication, cleanup, cancellation, and source safety

## Outcome

The two requested mixed-FPS rendering strategies have a common benchmark
definition that makes timing, correctness, storage, and quality comparable.

## Scope

- Define matched projects containing different input frame rates and relevant
  source dimensions or modifications.
- Define strategy A and B inputs, stages, target FPS, audio policy, output
  profile, warm/cold conditions, and repetitions.
- Define measurements for stage/total wall time, frame count, FPS, duration,
  audio, playability, intermediate/final size, resource use, and visual
  observations.
- Define how failures, retries, and unavailable hardware are recorded.

## Explicit non-goals

- Running the full comparison in this ticket.
- Changing the production exporter.
- Treating visual preference as a numeric quality substitute.

## Observable requirements

- Given the same project, both strategies should receive equivalent retained
  ranges, audio decisions, target FPS, and verification gates.
- Given a run, the benchmark should distinguish measured facts from subjective
  observations and assumptions.
- Given an unavailable tool or failed run, the procedure should record the
  limitation without excluding the result silently.

## Definition of done

- The benchmark protocol and fixture matrix are written and reviewable.
- TICKET-070 and TICKET-071 can execute matched runs.
- The evidence format captures correctness and cost separately.

## User-validation plan

- **Setup:** review the fixture matrix and benchmark protocol before running.
- **Steps:** inspect each strategy stage, metric, repetition, and failure rule.
- **Expected result:** neither strategy receives hidden advantages or skipped
  verification.
- **Failure paths:** ambiguous input equivalence or missing metrics is returned
  for correction.
- **Cleanup:** no production or source files are changed.
- **Evidence response:** return the approved matrix and protocol.
- **Pass criteria:** both strategy benchmark tickets have identical inputs and
  reporting rules.

## Closure

TICKET-069 was closed after the comparable two-source fixture protocol,
strategy stage definitions, output gates, source-preservation checks, and
cleanup rules were captured in the render-strategy evidence.
