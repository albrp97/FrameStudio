# TICKET-034 - Benchmark and Document Delivery Profiles

**Ticket ID:** TICKET-034
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Phase:** PHASE-005
**Feature:** FEAT-015
**Capability links:** CAP-005, CAP-012
**Status:** verifying
**Horizon:** future
**Priority:** 4
**Owner:** repository planning and implementation in the active worktree
**Approval:** user-authorized on 2026-08-22 to implement all approved
PHASE-005 tickets, including source-level audio balancing, with the legacy
`resolve_concat.py` mean/median policy applied once per input source
**Provider:** auto; base and target branches are not configured in
`.github/aidd-config.yml`
**Source paths:** `docs/planning/features/open/FEAT-015-selecting-tested-delivery-routes.md`,
`docs/planning/tickets/open/TICKET-031-define-source-level-audio-policy.md`,
`docs/planning/tickets/closed/TICKET-024-defining-mixed-source-output-canvas-and-timing-policy.md`,
`docs/specs/phase-002-export-policy.md`, `FAST-CONCAT-RESEARCH.md`,
`.github/aidd-config.yml`
**Dependencies:** PHASE-004A complete; fixed 1920x1080 output and established
render profile; TICKET-031 audio policy; target-workstation FFmpeg runtime
**Risks:** benchmark results can be mistaken for universal guarantees,
hardware encoders may vary, and a profile can be fast while producing
incompatible or invalid output
**Affected surfaces:** delivery profile documentation, benchmark fixtures,
FFmpeg options, output metadata, compatibility checks, evidence, and tests
**Evidence path:** `evidence/phase-005-delivery-profiles.md`
**Protected behaviors:** the fixed 1920x1080 canvas, established render
profile authority, source-safe temporary output, verification, and current
one-source fast path remain protected
**Last updated:** 2026-08-22

## Outcome

The supported workstation has measured preview, intermediate, and final
delivery profiles with explicit compatibility and fallback boundaries.

## Scope

- Benchmark representative mixed-source dimensions, frame rates, codecs,
  containers, channels, and source-level audio decisions.
- Record speed, output size, quality indicators, playability, metadata, and
  compatibility for candidate profiles.
- Document the fixed 1920x1080 canvas and established render profile as the
  output authority.
- Define profile selection and fallback criteria without silently selecting a
  different profile from source codec/container names.

## Explicit non-goals

- Universal hardware or codec guarantees outside the supported workstation.
- Implementing audio analysis or filter application.
- Triplicate composition, visual transforms, or 60 FPS enhancement.
- Replacing the established render profile without measured approval.

## Observable requirements

- Given candidate profiles and representative fixtures, the evidence should
  record reproducible speed, compatibility, quality, and fallback results.
- Given inputs with different codecs or containers, profile selection should
  remain governed by the established output policy.
- Given a fixed-canvas or audio-processing requirement, the documented route
  should identify whether decoding and re-encoding are required.
- Given an invalid candidate output, the profile should be rejected rather
  than treated as a successful fast path.

## Commands and quality gates

- `make smoke`
- `make check`
- `make quality PYTHON=.venv/bin/python`
- Run the documented disposable-media FFmpeg/ffprobe benchmark matrix.

## Functionality flows

- Benchmark portrait, landscape, mixed-dimension, mixed-frame-rate, and
  mixed-codec fixtures.
- Inspect output dimensions, streams, duration, playability, and profile
  metadata.
- Compare the fast path with the validated fallback on the same edit.

## User validation before closure

Review the benchmark table and sample outputs on the target workstation,
confirm the selected profiles and fallback boundaries, and confirm that input
codec/container differences do not silently change the established delivery
policy.

## Definition of done

- Profile choices and measured limitations are documented in the evidence path.
- Candidate outputs pass metadata, playability, and source-safety checks.
- The selected policy is approved before routing implementation begins.
- No universal performance claim is made from local benchmark evidence.
