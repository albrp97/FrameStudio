# TICKET-078 - Expand Cross-Model Restoration Benchmark

**Ticket ID:** TICKET-078
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Phase:** PHASE-008
**Feature:** FEAT-027
**Capability links:** CAP-005, CAP-011, CAP-012
**Status:** complete
**Horizon:** future
**Priority:** 2
**Last updated:** 2026-08-28
**Owner:** repository implementation in the active worktree
**Approval:** User-authorized on 2026-08-27 by the request to compare the named
restoration and upscaling candidates with the same metrics; execution remains
separately gated by the configured approval policy
**Source paths:** `docs/planning/reviews/CHG-007-expand-restoration-benchmark-matrix.md`,
`docs/planning/features/open/FEAT-027-researching-video-restoration-and-upscaling.md`,
`docs/planning/tickets/closed/TICKET-073-survey-video-upscaling-denoise-and-compression-recovery.md`,
`docs/planning/tickets/open/TICKET-077-benchmark-real-video-enhancer-restoration.md`,
`docs/research/video-restoration-strategies.md`,
`FPS-ENHANCEMENT-RESEARCH.md`,
`benchmarks/`,
`https://github.com/k4yt3x/video2x`,
`.github/aidd-config.yml`
**Dependencies:** TICKET-073 survey; TICKET-077 fixture and baseline
evidence; FFmpeg/ffprobe; a pinned Video2X release or commit; candidate
runtimes and weights where available; exact model/license documentation;
sufficient local storage and GPU/runtime support
**Risks:** candidate families solve different restoration problems; model
scales and temporal windows may not be equivalent; proprietary Topaz execution
may be unavailable on Linux; Video2X is a wrapper rather than a model; model
weights may have separate licenses; GPU memory, warm-up, encoder settings,
and hidden preprocessing can distort comparisons; subjective quality scoring
can overfit one source
**Affected surfaces:** research benchmark harness, candidate adapters and
manifest, temporary media, model/runtime discovery, GPU/resource telemetry,
common output normalization, metadata verification, contact sheets, reports,
and evidence
**Evidence path:** `evidence/ticket-078-cross-model-restoration-benchmark.md`
**Protected behaviors:** existing editor and export routes, RVE/RIFE FPS
behavior, fixed delivery policy, source preservation, atomic publication,
verification, cleanup, legacy scripts, and the research-only boundary
**Path history:** created at
`tickets/open/TICKET-078-expand-cross-model-restoration-benchmark.md` -> moved
to `tickets/closed/TICKET-078-expand-cross-model-restoration-benchmark.md`

## Outcome

The restoration experiment provides a reproducible, apples-to-apples
comparison matrix for the requested candidates, existing controls, and the
available RVE baseline. It distinguishes model quality observations from
runtime performance, output integrity, licensing, and availability, so a
future recommendation can be made without treating an unavailable or
incomparable candidate as a pass.

## Scope

- Reuse the deterministic fixture and source-safety protocol from TICKET-077.
  If its artifact is unavailable, regenerate the same three-window fixture
  using the recorded selection and seed without persisting the private source
  path.
- Define a versioned candidate manifest with the exact model/checkpoint,
  runtime, backend, revision, weight hash where permitted, scale, temporal
  window, preprocessing, postprocessing, and license status.
- Add explicit candidate rows for:
  - Topaz Video AI Gaia, only when a licensed local installation and a
    documented non-interactive or repeatable execution path are available.
  - Nomos2 and `4xNomos2_otf_esrgan`, with the exact checkpoint and runtime
    recorded rather than assuming Video2X compatibility.
  - EDVR, BasicVSR, and BasicVSR++ when the exact requested or compatible
    checkpoint is available.
  - TecoGAN as a temporal video-super-resolution candidate.
  - Real-ESRGAN, using an exact model such as `x4plus` when available.
  - Video2X, pinned to a release or commit and measured in filtering/upscale
    mode with its underlying model and Vulkan/ncnn backend recorded. Do not
    combine its filtering and frame-interpolation modes in this restoration
    comparison.
- Retain the TICKET-077 no-restoration, Lanczos, FFmpeg cleanup, and RVE rows
  as controls or historical baselines where their protocol is compatible.
- Build or extend a benchmark adapter contract that gives each runnable
  candidate the same input fixture and declared output target. An adapter may
  invoke a local binary, an isolated Python environment, a licensed local
  application, or a pinned external wrapper, but must report unavailable
  capabilities explicitly.
- Keep the restoration benchmark at the source frame rate. Do not combine
  spatial restoration results with RIFE or Video2X frame interpolation in the
  primary ranking.
- Normalize successful outputs to the common 1920x1080 comparison profile
  used by TICKET-077, preserving aspect ratio with contain scaling and
  letterboxing rather than stretching or cropping. Keep model output and
  common final encoding stages distinguishable.
- Use the same color/range policy, audio remux or preservation policy,
  container, codec, pixel format, and duration/frame-count checks for every
  comparable candidate. If a tool owns encoding or cannot preserve audio,
  record both the native result and the normalized comparison result.
- Measure, for every attempted candidate:
  - availability, license, revision, model, backend, and configuration;
  - cold setup/model-load time and at least one timed warm run;
  - repeated warm-run median and spread when the candidate can be repeated;
  - inference time separately from decode, normalization, and final encode;
  - processed source FPS, output FPS, real-time factor, GPU utilization,
    power, VRAM, CPU use, peak RSS, and temporary storage when observable;
  - output bytes, bitrate, duration, frame count, dimensions, codec, pixel
    format, audio presence/codec/rate/channels, and decode/playability;
  - source hash before and after, cleanup result, and any failure detail.
- Use a common visual review rubric at fixed timestamps for blocking,
  ringing, noise, sharpness, edge halos, faces/text, color shifts,
  hallucinated detail, temporal flicker, motion stability, and boundary
  behavior. Keep rubric scores and written observations separate from
  measured metadata.
- Calculate PSNR, SSIM, or another existing objective metric only when a
  clean reference is available for the exact degraded sample. Do not add a
  new metric dependency solely to produce a numeric ranking, and do not use
  synthetic-reference scores as universal evidence.
- Produce a machine-readable report, human-readable comparison report,
  candidate availability table, representative contact sheets, and
  redacted per-candidate command/configuration records under the uncommitted
  evidence artifact directory.

## Candidate comparison rules

| Candidate | Comparison treatment |
|---|---|
| Topaz Gaia | Commercial reference; local licensed installation only; record exact application/model/preset; no redistribution |
| Nomos2 | Single-frame or model-specific restoration; record exact checkpoint and temporal limitations |
| `4xNomos2_otf_esrgan` | Exact 4x checkpoint; compare at the common output target and record any post-downscale or aspect handling |
| EDVR | Temporal restoration; record task checkpoint, frame window, and sequence padding |
| BasicVSR / BasicVSR++ | Temporal propagation; record the exact variant and checkpoint separately |
| TecoGAN | Temporal video super-resolution; record recurrent state/reset behavior at fixture boundaries |
| Real-ESRGAN | Direct model baseline; label frame-independent behavior and any temporal flicker risk |
| Video2X | Wrapper/runtime row; pin release/commit, underlying model, backend, and filter mode; do not count the wrapper as a new model |

## Explicit non-goals

- Adding restoration or upscaling to production editor exports.
- Changing the Strategy B render default, RVE/RIFE FPS path, output codec
  policy, project schema, or user-facing editor controls.
- Adding permanent dependencies or vendoring Video2X, Topaz software, model
  weights, checkpoints, or external source code into the repository.
- Automatically downloading proprietary software, licensed models, or private
  media; no license circumvention or redistribution.
- Claiming that every named candidate is runnable on Linux, on the RTX 5070
  Ti, or through Video2X.
- Treating a wrapper and its underlying model as independent quality wins.
- Producing a single weighted score that hides temporal instability,
  hallucination, license restrictions, or incomparable settings.
- Ranking candidates from a failed, unavailable, non-comparable, or
  unverified output.

## Observable requirements

- Given the same pinned fixture and comparison target, each candidate should
  receive the same source frames, color/range policy, target dimensions,
  source frame-rate policy, audio policy, and verification checks.
- Given a runnable candidate, the report should include its exact model,
  runtime, backend, revision, configuration, cold/warm timing, resource
  measurements, output metadata, playability, output size, and artifact paths.
- Given a candidate that cannot run, lacks a compatible license, or cannot
  satisfy the common output contract, the report should retain a row with
  status and an explicit reason rather than silently omitting it.
- Given Video2X execution, the report should identify the pinned wrapper
  version, underlying model, backend, filtering mode, and native versus
  normalized timing.
- Given a successful output, the report should separate measured metadata and
  resource facts from visual rubric observations and any objective metric.
- Given a clean reference, objective quality metrics should be computed with
  the same crop, scale, color space, and frame alignment for every eligible
  candidate; otherwise the report should state why they are unavailable.
- Given a failed, cancelled, or invalid run, temporary artifacts should be
  removed or listed with an explicit cleanup failure, and the source hash
  should remain unchanged.
- Given all candidate results, the report should identify confidence limits
  and avoid a universal recommendation from one source or one workstation.

## Definition of done

- The benchmark manifest contains every requested candidate name and labels
  controls, direct models, temporal models, commercial software, and wrappers
  distinctly.
- Video2X has a pinned execution attempt or a terminal, evidence-backed
  unavailable result; its model/backend is never hidden.
- Every runnable candidate has the same required integrity and performance
  fields, and every unavailable/failed/excluded candidate has a reason.
- A machine-readable report, human-readable report, contact sheets, and
  redacted configuration records are available under the evidence path.
- The report contains separate measured, objective-quality, subjective, and
  licensing sections plus a bounded recommendation or explicit inability to
  recommend.
- The fixture and original source are verified unchanged; temporary artifacts
  are cleaned or explicitly accounted for.
- No production route, default, dependency manifest, or project schema is
  changed.
- TICKET-074 and TICKET-075 remain historically intact unless separately
  replanned; TICKET-077 remains the RVE baseline record.

## User-validation plan

- **Setup:** Open the uncommitted TICKET-078 comparison directory and review
  the fixture, control outputs, candidate outputs, contact sheets, JSON
  report, Markdown report, license/availability table, and source-preservation
  notes.
- **Steps:** Compare outputs at the same timestamps; inspect faces, text,
  edges, motion, fixture boundaries, color, noise, ringing, invented detail,
  flicker, and temporal stability. Check that the Video2X row names its
  wrapper, underlying model, backend, and mode. Confirm that the timing and
  resource columns distinguish setup, inference, encoding, and end-to-end
  work.
- **Expected result:** Each runnable candidate is directly comparable at the
  declared target profile, and every unavailable or incomparable candidate is
  visible with an explicit reason. The recommendation reflects both measured
  performance and visual behavior rather than bitrate alone.
- **Failure paths:** A missing runtime, missing weight, license ambiguity,
  unsupported model mode, OOM, corrupt output, mismatched duration/frame
  count, failed decode, or source hash change must be recorded as a blocker
  or limitation and must not be presented as a passing candidate.
- **Cleanup:** Remove generated comparison media, temporary model outputs,
  and fixture artifacts after inspection when no longer needed. Never remove
  the original source or any pre-existing valid output.
- **Evidence response:** Return one of:

  ```text
  PASS: every required check succeeded; evidence: <paths or notes>
  FAIL: <failed check and observed result>
  BLOCKED: <missing service, data, permission, or capability>
  NOT APPLICABLE: <reason and approval>
  ```

- **Pass criteria:** The candidate matrix is complete, the common metrics and
  output contract are applied consistently, Video2X is explicitly resolved,
  all limitations are recorded, and source preservation is confirmed.

## Closure

TICKET-078 is complete. The expanded candidate matrix, explicit unavailable
rows, normalized outputs, reports, and source-preservation evidence were
manually validated by the user, who requested closure of all tickets on
2026-08-28. Its license, runtime, and confidence limitations remain
documented.
