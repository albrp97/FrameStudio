# CHG-007 - Expand Cross-Model Restoration Benchmark Matrix

**Change ID:** CHG-007
**Type:** Material planning change
**Status:** approved-and-applied
**Date:** 2026-08-27
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Parent links:** PHASE-008, FEAT-027
**Owner:** repository planning; maintainer identity is not recorded
**Approval:** User-authorized by the request to create a ticket that adds
Topaz Gaia, Nomos2, 4xNomos2_otf_esrgan, EDVR, BasicVSR, TecoGAN,
RealESRGAN, and Video2X to a common benchmark.
**Source paths:** `docs/planning/features/open/FEAT-027-researching-video-restoration-and-upscaling.md`,
`docs/planning/tickets/open/TICKET-077-benchmark-real-video-enhancer-restoration.md`,
`docs/research/video-restoration-strategies.md`,
`FPS-ENHANCEMENT-RESEARCH.md`,
`https://github.com/k4yt3x/video2x`,
`.github/aidd-config.yml`
**Affected IDs:** PHASE-008, FEAT-027, TICKET-074, TICKET-075,
TICKET-077, TICKET-078, CAP-005, CAP-011, CAP-012
**Coverage links:** FEAT-027 restoration research; TICKET-077 focused RVE
baseline; TICKET-078 cross-model matrix
**Evidence path:** `evidence/ticket-078-cross-model-restoration-benchmark.md`
**Last updated:** 2026-08-27

## Request and classification

The user requested a new ticket to expand the restoration experiment so the
named commercial, open-model, temporal-restoration, and wrapper/runtime
options can be compared with the same source, output contract, measurements,
and visual rubric.

This is a material planning change because it expands the external runtime,
model, licensing, and benchmark-availability boundary beyond the focused RVE
run. It remains inside FEAT-027's research-only outcome and does not authorize
production restoration, a new editor dependency, or a change to export
defaults.

## Decision

1. Add TICKET-078 under FEAT-027 for a standardized cross-model benchmark
   matrix and comparison report.
2. Reuse TICKET-077's representative fixture and RVE/classical results where
   available; do not change TICKET-077's status or historical evidence.
3. Include the requested profiles as explicit candidate rows:
   Topaz Gaia, Nomos2, 4xNomos2_otf_esrgan, EDVR, BasicVSR, TecoGAN,
   Real-ESRGAN, and Video2X.
4. Treat Video2X as a pinned C/C++ wrapper/runtime. Its underlying model and
   backend must be recorded separately so a direct Real-ESRGAN run is not
   double-counted as an independent algorithm.
5. Treat proprietary Topaz execution as local-only and license-gated. Do not
   download, redistribute, or reverse-engineer proprietary models.
6. Mark missing runtimes, weights, licenses, or comparable modes explicitly;
   unavailable candidates do not become quality failures or silent omissions.
7. Keep TICKET-074 and TICKET-075 as the original generic blocked path until
   their records are deliberately replanned or closed through their own
   evidence.

## Required evidence and boundaries

- The benchmark must use one pinned fixture, common target dimensions,
  source-frame-rate policy, color handling, audio policy, output profile, and
  verification contract.
- Cold setup, warm processing, model/inference time, final encode time,
  throughput, GPU/CPU/resource observations, output size, and metadata must
  be reported separately.
- Numeric quality metrics may be used only where a clean reference exists;
  visual temporal-stability and hallucination observations remain separate.
- No production code path, editor UI, export default, dependency manifest,
  source media, or private model path is changed by this planning change.
- Any research runtime or weight used during execution remains outside the
  repository unless its license and redistribution terms are separately
  approved.

## Approval and remaining gates

The user request authorizes this bounded planning change. TICKET-078 execution
still requires the configured preimplementation, baseline, evidence,
applicable real-system, local-quality, review, and user-validation gates.
