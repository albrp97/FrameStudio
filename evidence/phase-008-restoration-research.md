# Phase 008 Restoration Research Evidence

**Feature:** FEAT-027
**Tickets:** TICKET-073, TICKET-074, TICKET-075
**Branch:** `ticket/phase-008-responsive-preview-media-strategy`
**Date:** 2026-08-26
**Primary report:** `docs/research/video-restoration-strategies.md`

## Scope and protected behavior

This evidence covers the survey, benchmark availability assessment, and
future-pipeline recommendation. No production code, model, weight, dependency,
download, export route, project schema, or UI control was added. Existing
smart render, interpolation, audio, verification, atomic publication, legacy
scripts, and source-preservation behavior remain protected.

## TICKET-073 survey

- 15 candidates were compared: eight FFmpeg/classical options and seven
  representative AI/video-restoration projects.
- Sources include FFmpeg documentation, papers, upstream project
  documentation, and license files. Links and access date are recorded in the
  primary report.
- VRT and RVRT were excluded because their CC-BY-NC-4.0 terms are
  non-commercial. Real-CUGAN was excluded for natural live-action use because
  it is anime-domain and frame-independent. FastDVDnet was excluded from the
  primary set because it expects known Gaussian noise rather than structured
  codec artifacts.
- RealBasicVSR and BasicVSR++ remain the strongest conditional open-license
  temporal candidates, but their runtime and weights are not installed.
- Per-frame AI quality and temporal behavior are paper/vendor claims, not
  local measurements.

## TICKET-074 benchmark availability

The no-install FFmpeg benchmark commands and matched-settings rubric are
documented in the primary report. The approved representative degraded clip
was not available during this phase, so those commands were not executed and
no synthetic result is presented as a quality pass.

| Candidate group | Result | Limitation |
|---|---|---|
| FFmpeg classical filters | Reproducible commands documented | No approved degraded clip for local run |
| Real-ESRGAN variants | Unavailable | Weights/runtime not installed |
| RealBasicVSR | Unavailable | mmcv/mmagic and weights not installed |
| BasicVSR++ | Unavailable | mmcv/mmagic and task weights not installed |
| VRT/RVRT | Excluded | License gate fails before runtime evaluation |

Future runs must report warm-up and processing time, output size, playability,
duration, frame count, audio, resource use, artifact behavior, and separate
visual observations. Where a clean reference exists, PSNR/SSIM must not
replace temporal and hallucination review.

## TICKET-075 recommendation

The bounded recommendation is:

1. Keep the existing source-safe smart-render and verification pipeline.
2. Evaluate an optional classical FFmpeg pre-restoration stage first.
3. Defer AI restoration until model/runtime, license, VRAM, temporal-stability,
   representative-media, and explicit-opt-in gates are approved.
4. If a stage fails a quality or integrity gate, discard its partial output and
   fall back to the last verified input.
5. Keep restoration before FPS enhancement only after timing, audio, and
   resource interactions are measured.

The smallest future implementation unit is an isolated optional
`hqdn3d`/`deblock` batch step using the existing partial-output, verification,
cleanup, cancellation, and source-safety patterns. It must receive a separate
implementation ticket and approval; this phase does not enable it.

## Checks and limitations

| Check | Result |
|---|---|
| Source and license research | 24 public references consulted; license boundaries recorded |
| Survey/matrix structure | Complete in `docs/research/video-restoration-strategies.md` |
| Classical command design | Documented against FFmpeg filter documentation |
| AI model quality benchmark | Unavailable; no models or weights installed |
| Representative degraded-clip benchmark | Unavailable; no clip selected/approved |
| Production integration | Not performed by design |
| Remote repository checks | Unavailable; no repository remote configured |

All unavailable checks are recorded as limitations, not passes. TICKET-073 is
complete; TICKET-074 remains open and blocked until an approved degraded
sample and the required runtimes/weights are available, and TICKET-075 remains
blocked behind it.

## Phase closeout

**Date:** 2026-08-28  
**Phase:** PHASE-008  
**Tickets:** TICKET-074, TICKET-075  
**Category:** user validation and lifecycle closeout  
**Status:** passedWithConcerns

The user explicitly confirmed that the Phase 8 tickets were manually
validated and requested that all done tickets, features, and phases be closed.
This closeout decision supersedes the earlier generic availability blockers for
TICKET-074 and TICKET-075 at the lifecycle level; it does not convert the
historical unavailable generic benchmark checks into technical passes.

The concrete local restoration and comparison evidence is preserved in
TICKET-077 and TICKET-078, including the generated artifacts, timing data,
output metadata, source-preservation checks, and documented runtime
limitations. TICKET-074 and TICKET-075 were therefore closed with their
historical limitations retained, rather than deleting or rewriting the
earlier blocked evidence.

**User response:** “im telling you these are DONE. CLOSE THEM ALL AND THEN
COMMIT”

**Observed:** TICKET-074 through TICKET-082, FEAT-025 through FEAT-028, and
PHASE-008 were marked `complete` and moved to their configured `closed`
directories. The planning indexes were synchronized to those lifecycle paths.

**Accepted warnings:** The generic TICKET-074/TICKET-075 benchmark path still
records unavailable approved inputs and runtimes; remote checks, target
workstation coverage, and other environment-specific limitations remain
explicit in the linked records.
