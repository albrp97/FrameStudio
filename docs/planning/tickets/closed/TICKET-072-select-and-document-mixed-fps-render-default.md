# TICKET-072 - Select and Document Mixed-FPS Render Default

**Ticket ID:** TICKET-072
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Phase:** PHASE-008
**Feature:** FEAT-026
**Capability links:** CAP-005, CAP-011, CAP-012
**Status:** complete
**Closure:** closed on 2026-08-26 after the matched A/B measurements and the
decision to retain concat-first production routing were documented with their
hardware, fixture, repetition, and visual-review limitations.
**Horizon:** future
**Priority:** 3
**Owner:** repository planning; maintainer identity is not recorded
**Approval:** user-authorized on 2026-08-26 for PHASE-008 planning; execution
requires the configured preimplementation and approval gates
**Last updated:** 2026-08-26
**Source paths:** `docs/planning/features/closed/FEAT-026-comparing-mixed-fps-render-strategies.md`,
`docs/planning/tickets/closed/TICKET-070-benchmark-concat-first-enhancement-strategy.md`,
`docs/planning/tickets/closed/TICKET-071-benchmark-per-source-enhancement-strategy.md`,
`resolve_editor/export_planning.py`, `resolve_editor/export_smart_render.py`,
`resolve_editor/export_interpolation.py`, `README.md`,
`.github/aidd-config.yml`
**Dependencies:** TICKET-070 and TICKET-071 terminal comparison evidence;
review and user approval for any production routing change
**Risks:** a single default may not fit all projects; changing it without
compatibility evidence can regress ordinary export or source safety
**Affected surfaces:** export routing decision, documentation, benchmark
evidence, project policy, and future follow-up planning
**Evidence path:** `evidence/phase-008-render-strategy-comparison.md`
**Path history:** `tickets/open/TICKET-072-select-and-document-mixed-fps-render-default.md`
-> `tickets/closed/TICKET-072-select-and-document-mixed-fps-render-default.md`
**Protected behaviors:** current safe concat-first route, output profile,
audio decisions, cancellation, verification, and legacy scripts

## Outcome

The project records whether strategy A, strategy B, or conditional routing is
worth adopting, based on measured time and quality/correctness tradeoffs.

## Scope

- Analyze matched strategy results, including lost or preserved source-frame
  detail, total and stage time, storage, resource use, output correctness,
  audio, and visual observations.
- Decide whether to retain strategy A, introduce strategy B, or route
  conditionally by explicit project/media conditions.
- If a production change is justified, define the smallest follow-up
  implementation and approval boundary; do not silently change it here.
- Document the decision and known hardware/media limits.

## Explicit non-goals

- Declaring a universal winner from one workstation.
- Implementing a production route without a separate approved execution scope.
- Treating subjective quality as a replacement for metadata and playability
  gates.

## Observable requirements

- Given both benchmark reports, the decision should cite measured numbers and
  clearly separate facts, subjective observations, and assumptions.
- Given a route choice, the report should explain when it applies and what
  evidence is still missing.
- Given no meaningful benefit, the current route should remain unchanged with
  a documented rationale.

## Definition of done

- A reviewable A/B decision exists with explicit routing recommendation.
- Any implementation work is bounded as a follow-up or separately approved
  ticket.
- Documentation prevents future claims beyond the measured environment.

## User-validation plan

- **Setup:** review the two strategy reports and decision matrix.
- **Steps:** compare time, frame/timing/audio correctness, size, and visual
  observations; inspect the proposed default or conditional rule.
- **Expected result:** the choice reflects the user's speed/quality tradeoff
  and does not hide unresolved risks.
- **Failure paths:** missing metrics, unequal work, or unsupported claims block
  the decision.
- **Cleanup:** no production route changes unless separately approved.
- **Evidence response:** return the decision matrix and follow-up boundary.
- **Pass criteria:** the project has an explicit, evidence-backed default or
  a justified decision to defer change.

## Closure

TICKET-072 was closed with the evidence-backed decision to retain Strategy A
for production. Strategy B's negligible timing difference did not justify a
second route, and the report keeps the single-fixture and no-subjective-review
limitations explicit.
