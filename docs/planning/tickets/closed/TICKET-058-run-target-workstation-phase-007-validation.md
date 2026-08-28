# TICKET-058 - Run Target Workstation Phase 007 Validation

**Ticket ID:** TICKET-058
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Phase:** PHASE-007
**Feature:** FEAT-023
**Capability links:** CAP-005, CAP-006, CAP-011, CAP-012
**Status:** complete
**Closure:** user-approved on 2026-08-26 after implementation, testing,
review, and acceptance of the Phase 007 validation scope; unavailable remote
and target-specific checks remain explicitly recorded as accepted warnings.
**Horizon:** future
**Priority:** 11
**Owner:** repository planning; maintainer identity is not recorded
**Approval:** user-authorized on 2026-08-24 to create the PHASE-007 planning
set; implementation and closure require TICKET-057 plus configured
ticket-execution and user-validation approval
**Provider:** auto; base and target branches are not configured in
`.github/aidd-config.yml`
**Source paths:** `docs/planning/phases/closed/PHASE-007-producing-validated-60-fps-edits.md`,
`docs/planning/features/closed/FEAT-023-verifying-safe-enhanced-delivery.md`,
`docs/planning/tickets/closed/TICKET-057-verify-enhanced-output-integrity-and-regressions.md`,
`README.md`, `AGENTS.md`, `.github/aidd-config.yml`
**Dependencies:** TICKET-057; target-workstation GTK/FFmpeg/RIFE or validated
fallback availability; representative disposable portrait, landscape, and
mixed-rate media
**Risks:** workstation-only behavior may not generalize, visual quality is
partly subjective, and long renders can expose runtime or thermal failures
**Affected surfaces:** GUI, CLI, playback, export, interpolation backend,
progress/ETA, benchmark evidence, screenshots, output inspection, and
source-safety validation
**Evidence path:** `evidence/phase-007-safe-enhanced-delivery.md`
**Protected behaviors:** all existing editor operations, non-enhanced exports,
legacy scripts, source-level audio, fixed output canvas, project persistence,
and source preservation
**Last updated:** 2026-08-26
**Path history:** created at
`tickets/open/TICKET-058-run-target-workstation-phase-007-validation.md` ->
`tickets/closed/TICKET-058-run-target-workstation-phase-007-validation.md`

## Outcome

PHASE-007 has terminal target-workstation evidence for enhanced and ordinary
exports, including performance estimates, visual artifact review, and safe
failure behavior.

## Scope

- Run the complete export-panel flow with one-source and mixed-rate projects.
- Exercise lowest, highest, custom, and 60 FPS choices with enhancement on and
  off where supported.
- Compare estimated interpolation/render/verification/total time with actual
  progress and wall-clock results.
- Inspect target FPS, exact frame count, duration, audio, playability,
  dimensions, scene cuts, artifacts, and source preservation.
- Capture configured window-only UI evidence and retain benchmark metadata
  without sensitive local paths.
- Record unavailable tools, backends, remote checks, or visual coverage as
  blocked/skipped with reasons.

## Explicit non-goals

- Universal hardware-performance claims.
- Testing unsupported operating systems or cloud environments.
- Introducing new product behavior during validation.

## Observable requirements

- Given a supported target workstation and disposable media, enhanced export
  should complete with all required measurable and visual evidence.
- Given enhancement disabled, the ordinary export should complete with the
  existing behavior.
- Given a failed or canceled run, source media, project state, and last valid
  output should remain intact.
- Given an unavailable backend or remote check, evidence should remain
  explicitly blocked or skipped rather than marked passed.

## Commands and quality gates

- `python3 -m unittest discover -s tests`
- `make contract`
- `make smoke`
- `make check`
- `make quality PYTHON=.venv/bin/python`
- Target-workstation GTK, FFmpeg, ffprobe, interpolation, and window-only
  evidence steps

## Functionality flows

- Run enhanced 29.97-to-60 FPS and mixed-rate exports.
- Run ordinary exports with the same projects and compare output/safety.
- Compare estimate versus measured duration and inspect sampled artifacts.
- Repeat cancellation, missing-tool, backend-failure, and collision paths.

## User validation before closure

Follow the full target-workstation charter with disposable media. Confirm the
export panel, estimate, progress, output metadata, visual result, audio,
failure recovery, and source preservation. Return `PASS`, `FAIL`, or
`BLOCKED`; include the exact unavailable checks if blocked.

## Definition of done

- Every PHASE-007 exit condition has terminal evidence or an explicit
  blocked/skipped reason.
- Local measurements are labeled as workstation-specific.
- PHASE-007 can be reviewed without inferring success from an incomplete
  backend, visual, or remote check.

## Closure

TICKET-058 was closed on 2026-08-26 after the user confirmed the completed
ticket set was approved, accepted, and tested. Evidence continues to
distinguish local fallback results from unavailable target-specific checks.
