# FEAT-022 - Running Validated Motion Interpolation

**Feature ID:** FEAT-022
**Parent links:** OBJ-001, SCOPE-001, PHASE-007
**Capability links:** CAP-005, CAP-011, CAP-012
**Status:** complete
**Closure:** user-approved on 2026-08-26 after TICKET-053 through TICKET-055
passed implementation, automated validation, review, and user acceptance;
unavailable remote and target-specific checks remain recorded as accepted
warnings.
**Horizon:** future
**Priority:** 3
**Owner:** repository planning; maintainer identity is not recorded
**Approval:** user-authorized on 2026-08-24 to break down PHASE-007; ticket
execution remains separately gated by the configured approval policy
**Source paths:** `docs/planning/phases/closed/PHASE-007-producing-validated-60-fps-edits.md`,
`resolve_fps.py`, `resolve_concat.py`, `FPS-ENHANCEMENT-RESEARCH.md`,
`FLOWFRAMES-RESEARCH.md`, `benchmarks/fps.vpy`, `.github/aidd-config.yml`
**Dependencies:** FEAT-020 target-rate policy; PHASE-005 audio and output
policy; validated RIFE/RVE research; target-workstation runtime and GPU
artifacts
**Risks:** interpolation can hallucinate motion, create artifacts at
occlusions or cuts, drift from exact timing, or fail after a runtime/model
upgrade
**Affected surfaces:** interpolation adapter, raw-frame pipeline, scene-cut
handling, timing math, audio remux, backend selection, GPU/CPU fallback,
benchmarks, tests, and evidence
**Evidence path:** `evidence/phase-007-motion-interpolation.md`
**Planned tickets:** TICKET-053, TICKET-054, TICKET-055
**Last updated:** 2026-08-26
**Path history:** created at
`features/open/FEAT-022-running-validated-motion-interpolation.md` ->
`features/closed/FEAT-022-running-validated-motion-interpolation.md`

## Outcome

An opted-in edit can be processed through a validated motion-interpolation
path that reaches the selected target rate without sacrificing timing, audio
synchronization, or scene-cut safety.

## Scope

- Select an evidence-backed backend and profile for the supported workstation.
- Use the corrected RIFE/RVE path and its documented precision/fallback
  boundaries rather than the known unsafe pure TensorRT FP16 path.
- Preserve exact rational frame-count and duration behavior, including final
  frame handling required by the selected target rate.
- Prevent synthetic frames from crossing hard scene cuts according to the
  approved policy.
- Preserve or remux audio independently so interpolation does not introduce
  progressive synchronization drift.
- Surface unavailable runtimes, model files, and failed artifact gates as
  explicit failures or validated fallbacks.

## Explicit non-goals

- Diffusion-based interpolation as the default.
- Unvalidated pure TensorRT FP16 execution.
- Frame duplication, blending, or display-only frame generation as equivalent
  enhancement.
- Universal quality or throughput claims outside the supported workstation.

## Observable requirements

- Given enhancement enabled and a supported target, the pipeline should report
  its backend/profile and produce the exact approved output frame count.
- Given a hard scene cut, the pipeline should not synthesize a frame across the
  cut when the selected policy forbids it.
- Given a missing or failed backend/artifact gate, the pipeline should block
  or choose an explicitly validated fallback and report the reason.
- Given an audio-bearing source, the enhanced output should preserve
  synchronization and the approved audio policy.

## Validation intent

- Run raw-frame artifact checks before long renders.
- Compare exact frame counts, duration, frame rate, scene boundaries, audio
  start/end, and playability on representative inputs.
- Repeat the same checks after a backend/runtime cache rebuild or fallback.
- Label target-workstation measurements and unavailable environments
  explicitly.

## Protected behaviors

Legacy `resolve_fps.py` and `resolve_concat.py` command names and behavior,
source-level audio decisions, fixed 1920x1080 output, source preservation,
partial-output cleanup, and existing non-enhanced editor exports remain
protected.

## Definition of done

- The selected backend/profile is validated on raw and encoded output.
- Exact timing, scene-cut, audio, artifact, and fallback behavior is covered.
- Failed or unavailable enhancement never becomes a success-shaped export.

## Closure

FEAT-022 was closed on 2026-08-26 after its child tickets and linked evidence
were accepted as tested by the user. The explicit FFmpeg fallback remains
documented as a bounded alternative to unavailable RVE/RIFE validation.
