# Delivery Evidence: TICKET-034

**Feature:** FEAT-015
**Phase:** PHASE-005
**Branch:** `ticket/phase-005-source-audio-delivery`
**Evidence status:** verifying; technical evidence is terminal and user
validation is required before closure
**Recorded:** 2026-08-22

## Evidence entries

### E-034-001 - Established profile authority

- **Category:** planning
- **Requirement:** The fixed 1920x1080 canvas and established render profile
  remain authoritative; source codec/container names do not silently select a
  different output profile.
- **Source:** `docs/specs/phase-002-export-policy.md`,
  `framestudio/export_types.py`
- **Expected:** MP4, H.264, AAC when audio is present, `yuv420p`, 1920x1080,
  and explicit fallback reasons.
- **Observed:** `OutputPolicy` and fallback routes retain those values.
- **Status:** passed

### E-034-002 - Route benchmark

- **Category:** functionality
- **Steps:** Generated a one-second 1920x1080 H.264 source without audio and a
  one-second 320x180 H.264 source. Imported and exported each through the CLI.
- **Expected:** The matching unchanged source uses stream copy; the
  non-matching canvas uses the validated fallback; both outputs verify.
- **Observed:** Stream-copy route: `0.254 s`, `23,998 bytes`, `1920x1080`,
  verified. Fixed-canvas fallback: `0.343 s`, `72,731 bytes`, `1920x1080`,
  verified.
- **Status:** passedWithConcerns
- **Accepted warning:** These are local disposable-media measurements, not
  universal hardware performance claims.

### E-034-003 - Audio-aware mixed route

- **Category:** functionality
- **Steps:** Generated mixed landscape/portrait sources with different frame
  rates, dimensions, sample rates, and audio levels; analyzed and exported
  them through the CLI.
- **Expected:** The established fallback route is selected with an explainable
  reason and output metadata is verified.
- **Observed:** Fallback was selected because of fixed-canvas composition,
  mixed frame rates, and source-level processing. Output was H.264/AAC,
  1920x1080, 48 kHz stereo, two seconds, and playable.
- **Status:** passed

### E-034-004 - Regression and quality

- **Category:** gate
- **Commands:** `make check`; `make smoke`; `make quality
  PYTHON=.venv/bin/python`
- **Expected:** Existing fast path, fallback, safety, and helper workflows
  remain green.
- **Observed:** All configured local checks passed.
- **Status:** passedWithConcerns
- **Accepted warning:** No remote or upstream is configured.

### E-034-005 - User validation

- **Category:** userValidation
- **Steps:** Review the benchmark results and sample outputs on the target
  workstation; confirm profile and fallback boundaries.
- **Expected:** The user returns a terminal validation result with notes.
- **Observed:** Awaiting user review.
- **Status:** blocked
- **Blocker:** Required user confirmation has not been recorded.

## Readiness

The local route benchmark and profile documentation support the approved
policy. User approval is still required before this delivery-profile ticket
can close.

### E-034-006 - User validation confirmation

- **Category:** userValidation
- **Requirement:** Confirm the measured delivery profiles, fixed output
  authority, and fallback boundaries.
- **Observed:** The user explicitly stated, “all the tickets open are
  validated,” which includes TICKET-034's benchmark and profile decisions.
- **Status:** passed

## Readiness (superseding E-034-001 through E-034-006)

TICKET-034 has terminal planning, benchmark, automated, and user-validation
evidence. Local measurements remain workstation-specific, and remote checks
remain unavailable because no upstream is configured.
