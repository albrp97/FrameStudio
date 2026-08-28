# TICKET-077 - Benchmark REAL Video Enhancer Restoration on Degraded Media

**Ticket ID:** TICKET-077
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Phase:** PHASE-008
**Feature:** FEAT-027
**Capability links:** CAP-005, CAP-011, CAP-012
**Status:** complete
**Horizon:** future
**Priority:** 1
**Owner:** repository planning; maintainer identity is not recorded
**Approval:** User-authorized on 2026-08-26 to use the supplied local media,
include REAL Video Enhancer for personal use, generate comparison artifacts,
and proceed without pausing for separate user acceptance.
**Last updated:** 2026-08-28
**Source paths:** `docs/planning/reviews/CHG-006-real-video-enhancer-restoration-benchmark.md`,
`docs/research/video-restoration-strategies.md`,
`evidence/phase-008-restoration-research.md`,
`https://github.com/TNTwise/REAL-Video-Enhancer/tree/2.4.1`,
`/home/ghiki/.cache/framestudio-fps/REAL-Video-Enhancer`,
`.github/aidd-config.yml`
**Dependencies:** TICKET-073 survey; supplied local compressed source;
FFmpeg/FFprobe; NVIDIA GPU if available; compatible RVE models and runtime
artifacts; sufficient temporary storage
**Risks:** the sample may not represent all downloaded/reuploaded media;
restoration may hallucinate or erase detail; 4x models may require a
downscale for the 1080p comparison; GPU backends may fail or exhaust VRAM;
generated media may contain private user data
**Affected surfaces:** restoration research evidence, benchmark harness,
temporary media, GPU/runtime execution, output inspection, and future
pipeline recommendation
**Evidence path:** `evidence/ticket-077-real-video-enhancer-restoration.md`
**Protected behaviors:** original source preservation, existing editor/export
routes, fixed delivery policy, atomic output handling, and legacy scripts
**Path history:** created at
`tickets/open/TICKET-077-benchmark-real-video-enhancer-restoration.md` -> moved
to `tickets/closed/TICKET-077-benchmark-real-video-enhancer-restoration.md`

## Outcome

The project has a reproducible comparison of the researched restoration and
upscaling approaches on a representative compressed video, including visible
outputs, timing, GPU/backend use, output metadata, storage, and a bounded
recommendation.

## Scope

- Use the supplied local compressed source without persisting its private
  path or modifying the original.
- Select three distinct 15-second windows with a recorded deterministic seed,
  concatenate them into a 45-second benchmark fixture, and preserve audio
  where the candidate supports it.
- Run a no-restoration upscale control and the researched FFmpeg candidates:
  Lanczos, `hqdn3d`, `atadenoise`, `deblock`, `pp=hb/vb/dr`, combined cleanup,
  and cleanup followed by mild sharpening.
- Run every compatible locally available REAL Video Enhancer restoration or
  upscale model, including decompression/denoise/upscale paths and available
  CUDA/TensorRT/NCNN backends. Normalize outputs to a comparable 1920x1080
  delivery for inspection.
- Record candidate command/configuration, model/backend availability, wall
  time, GPU and CPU observations, output size, duration, frame count,
  resolution, codec, pixel format, audio, playability, and cleanup.
- Produce representative frame/contact-sheet artifacts and separate
  observations about blocking, ringing, noise, sharpness, faces/text,
  hallucination, temporal flicker, and motion stability.
- Mark researched candidates that cannot run locally, including missing
  runtimes/weights or license/domain exclusions, without treating them as
  benchmark passes.

## Explicit non-goals

- Adding restoration or upscaling to production editor exports.
- Changing the established Strategy B render default or FPS pipeline.
- Downloading private media or publishing the supplied source.
- Treating a higher output bitrate as recovery of discarded source detail.
- Claiming a result is universal beyond this source, workstation, and
  benchmark protocol.

## Observable requirements

- Given the supplied source, the original file should remain byte-for-byte
  unchanged after fixture creation and all candidate runs.
- Given the same 45-second fixture and output target, each runnable candidate
  should produce an inspectable output or an explicit failure record.
- Given each successful output, the report should include reproducible timing,
  backend/model, output metadata, size, playability, and artifact paths.
- Given visual inspection, the report should separate measured metadata from
  subjective quality observations and identify hallucination or temporal
  instability risks.
- Given unavailable candidates, the report should state the exact missing
  capability and leave the candidate unresolved rather than infer quality.

## Definition of done

- The fixture and all runnable candidate outputs are left under the
  uncommitted benchmark artifact directory for user inspection.
- A machine-readable report and human-readable comparison report contain
  timing, resource, metadata, output-size, visual-observation, and limitation
  evidence.
- REAL Video Enhancer's architecture, model families, and backend used in the
  run are recorded with its pinned revision.
- A recommendation identifies the best measured candidate for this sample and
  states confidence limits and the smallest safe future implementation unit.
- Source preservation and artifact cleanup are verified; production code and
  defaults remain unchanged.

## User-validation plan

- **Setup:** Open the generated comparison directory and review the fixture,
  candidate videos, contact sheets, JSON report, and human-readable report.
- **Steps:** Compare each output against the control at matching timestamps,
  inspect faces/text and motion across clip boundaries, and confirm the
  recommendation reflects the visible result rather than only file size or
  speed.
- **Expected result:** Outputs are playable and comparable at 1920x1080, and
  the report clearly distinguishes measured facts from visual judgment.
- **Failure paths:** A missing model/backend, OOM, corrupt output, unexpected
  duration/FPS, or unsafe source change is recorded explicitly.
- **Cleanup:** Remove generated benchmark media after review if no longer
  needed; do not delete the original source.
- **Evidence response:** Return `PASS`, `FAIL`, or `BLOCKED` with notes about
  the preferred output and any artifact that needs another run.
- **Pass criteria:** Every runnable candidate has terminal evidence, every
  unavailable candidate has a recorded limitation, and source preservation is
  confirmed.

## Closure

TICKET-077 is complete. The benchmark artifacts, output comparisons,
source-preservation evidence, and bounded recommendation were manually
validated by the user, who requested closure of all tickets on 2026-08-28.
The research-only boundary and documented candidate limitations remain
unchanged.
