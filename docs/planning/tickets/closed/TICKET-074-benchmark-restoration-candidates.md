# TICKET-074 - Benchmark Restoration Candidates

**Ticket ID:** TICKET-074
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Phase:** PHASE-008
**Feature:** FEAT-027
**Capability links:** CAP-005, CAP-011, CAP-012
**Status:** complete
**Prior blocker:** no approved representative degraded clip was available,
and the required AI restoration runtimes and weights were not installed during
the original generic benchmark path.
**Horizon:** future
**Priority:** 2
**Owner:** repository planning; maintainer identity is not recorded
**Approval:** user-authorized on 2026-08-26 for PHASE-008 planning; execution
requires the configured preimplementation and approval gates
**Last updated:** 2026-08-28
**Source paths:** `docs/planning/features/open/FEAT-027-researching-video-restoration-and-upscaling.md`,
`docs/planning/tickets/open/TICKET-073-survey-video-upscaling-denoise-and-compression-recovery.md`,
`framestudio/export_delivery.py`, `framestudio/export_smart_render.py`,
`benchmarks/`, `FAST-CONCAT-RESEARCH.md`, `FPS-ENHANCEMENT-RESEARCH.md`,
`.github/aidd-config.yml`
**Dependencies:** TICKET-073 candidate matrix; representative degraded or
publicly reproducible samples; available local runtimes and storage
**Risks:** synthetic degradation may not represent real footage; model
warm-up, GPU memory, and subjective scoring can distort comparisons
**Affected surfaces:** research benchmark harness, temporary media, quality
assessment, resource measurements, and restoration evidence
**Evidence path:** `evidence/phase-008-restoration-research.md`
**Protected behaviors:** benchmarking is isolated; no production route,
dependency, source file, or project schema is changed

## Outcome

Selected restoration candidates have comparable quality and performance
observations on defined degradation classes.

## Scope

- Choose a bounded set of candidates from TICKET-073.
- Use representative or clearly described degraded samples.
- Measure runtime, resource use, output size, temporal stability, artifact
  behavior, and subjective quality with an explicit rubric.
- Record unavailable models, runtimes, or hardware as limitations.

## Explicit non-goals

- Benchmarking every model or hardware platform.
- Treating a synthetic sample as universal evidence.
- Adding models or pipeline code to the editor.

## Observable requirements

- Given the same sample and degradation class, candidates should use
  comparable settings and report warm-up and processing time.
- Given output quality, the report should separate rubric observations from
  metadata and measured runtime.
- Given a missing dependency or model, the candidate should be marked
  unavailable rather than silently omitted.

## Definition of done

- Candidate benchmark results are reproducible or their limitations are
  documented.
- Quality, temporal stability, performance, license, and resource evidence
  can be compared.
- TICKET-075 can make a bounded recommendation without production code.

## User-validation plan

- **Setup:** review the sample descriptions, candidate settings, and rubric.
- **Steps:** inspect outputs or captured comparisons, timing, resource, and
  artifact notes for each candidate.
- **Expected result:** the report makes tradeoffs visible rather than hiding
  hallucination, ringing, or temporal instability.
- **Failure paths:** unavailable candidate, corrupted output, or irreproducible
  sample is recorded with reduced confidence.
- **Cleanup:** remove temporary models, media, and output artifacts.
- **Evidence response:** return the comparison matrix and confidence limits.
- **Pass criteria:** candidate results are sufficient for a future pipeline
  recommendation.

## Closure

TICKET-074 is complete. The later, explicitly approved concrete benchmark
under TICKET-077 supplied representative local degraded media and runnable
restoration paths, while TICKET-078 expanded the candidate matrix and retained
unavailable candidates as explicit limitation rows. Those results supersede
the original generic availability blocker without erasing its historical
record.

The user explicitly confirmed that all tickets were done and requested their
closure on 2026-08-28. The bounded benchmark scope, unavailable candidates,
and confidence limits remain documented in the linked evidence.

**Path history:** created at
`tickets/open/TICKET-074-benchmark-restoration-candidates.md` -> moved to
`tickets/closed/TICKET-074-benchmark-restoration-candidates.md`.
