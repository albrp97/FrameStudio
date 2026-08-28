# TICKET-073 - Survey Video Upscaling, Denoise, and Compression Recovery

**Ticket ID:** TICKET-073
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Phase:** PHASE-008
**Feature:** FEAT-027
**Capability links:** CAP-005, CAP-011, CAP-012
**Status:** complete
**Closure:** closed on 2026-08-26 after the source-linked candidate survey,
license exclusions, runtime constraints, bounded benchmark set, and
research-only pipeline recommendation were recorded; unavailable candidate
execution remains open in TICKET-074.
**Horizon:** future
**Priority:** 1
**Owner:** repository planning; maintainer identity is not recorded
**Approval:** user-authorized on 2026-08-26 for PHASE-008 planning; execution
requires the configured preimplementation and approval gates
**Last updated:** 2026-08-26
**Source paths:** `docs/planning/features/open/FEAT-027-researching-video-restoration-and-upscaling.md`,
`docs/specs/future-product-direction.md`, `FAST-CONCAT-RESEARCH.md`,
`FPS-ENHANCEMENT-RESEARCH.md`, `resolve_concat.py`, `resolve_fps.py`,
`.github/aidd-config.yml`
**Dependencies:** public technical/model documentation; license information;
local GPU/runtime constraints; representative degradation classes
**Risks:** papers and demos can overstate quality, models can hallucinate
detail, and licenses or model weights may be incompatible with distribution
**Affected surfaces:** future restoration pipeline, model/runtime choices,
quality gates, output policy, documentation, and evidence
**Evidence path:** `evidence/phase-008-restoration-research.md`
**Path history:** `tickets/open/TICKET-073-survey-video-upscaling-denoise-and-compression-recovery.md`
-> `tickets/closed/TICKET-073-survey-video-upscaling-denoise-and-compression-recovery.md`
**Protected behaviors:** no production code, model, dependency, download, or
export route is added by this research ticket

## Outcome

The project has a source-linked survey of classical and AI approaches for
upscaling, denoising, deblocking, deblurring, and low-bitrate artifact
recovery.

## Scope

- Compare candidate algorithm families and representative models.
- Record the artifact classes each approach targets and may worsen.
- Record temporal stability, input/output constraints, model size, hardware
  and runtime requirements, license, and maintenance considerations.
- Identify candidates for the benchmark in TICKET-074.

## Explicit non-goals

- Downloading or integrating production models.
- Claiming restored detail is factual source detail.
- Selecting a production default before measured evidence.

## Observable requirements

- Given each candidate, the survey should identify intended artifacts,
  limitations, temporal behavior, resources, and licensing.
- Given a model or algorithm with unavailable documentation, the uncertainty
  should be explicit.
- Given candidate output claims, the report should distinguish measured
  evidence from vendor or paper claims.

## Definition of done

- A candidate matrix is source-linked and license-aware.
- Candidate selection criteria and exclusions are explicit.
- TICKET-074 can choose bounded candidates without inventing assumptions.

## User-validation plan

- **Setup:** review the candidate matrix and source links.
- **Steps:** inspect quality claims, limitations, license, resource, and
  maintenance columns for each candidate family.
- **Expected result:** the survey is useful without promising impossible
  recovery or production support.
- **Failure paths:** missing sources, ambiguous license, or unsupported
  quality claims remain research gaps.
- **Cleanup:** remove any temporary research downloads not required by the
  evidence.
- **Evidence response:** return the matrix, exclusions, and open questions.
- **Pass criteria:** candidate selection for TICKET-074 is bounded and
  traceable.

## Closure

TICKET-073 was closed after the restoration matrix, source links, license
boundaries, exclusions, and candidate-selection criteria were captured. It
does not claim local model-quality measurements or production support.
