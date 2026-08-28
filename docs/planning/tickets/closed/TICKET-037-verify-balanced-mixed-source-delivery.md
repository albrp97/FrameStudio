# TICKET-037 - Verify Balanced Mixed-Source Delivery

**Ticket ID:** TICKET-037
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Phase:** PHASE-005
**Feature:** FEAT-016
**Capability links:** CAP-005, CAP-008, CAP-012
**Status:** complete
**Closure:** user-approved on 2026-08-22 after implementation, automated and
real-media verification, review, user validation, and local delivery evidence;
remote checks remain unavailable and are recorded as an accepted warning.
**Path history:** `tickets/open/TICKET-037-verify-balanced-mixed-source-delivery.md`
-> `tickets/closed/TICKET-037-verify-balanced-mixed-source-delivery.md`
**Horizon:** future
**Priority:** 7
**Owner:** repository planning and implementation in the active worktree
**Approval:** user-authorized on 2026-08-22 to implement all approved
PHASE-005 tickets, including source-level audio balancing, with the legacy
`framestudio_concat.py` mean/median policy applied once per input source
**Provider:** auto; base and target branches are not configured in
`.github/aidd-config.yml`
**Source paths:** `docs/planning/features/open/FEAT-016-synchronizing-media-decisions-and-verification.md`,
`docs/planning/tickets/open/TICKET-033-apply-source-audio-decisions-consistently.md`,
`docs/planning/tickets/open/TICKET-035-route-audio-aware-and-mixed-source-exports-safely.md`,
`docs/planning/tickets/open/TICKET-036-expose-synchronized-media-decisions.md`,
`docs/planning/phases/open/PHASE-005-balancing-sources-and-delivering-consistent-media.md`,
`AGENTS.md`, `.github/aidd-config.yml`
**Dependencies:** TICKET-033, TICKET-035, and TICKET-036; representative
mixed-source media; target-workstation listening and measurement access
**Risks:** metadata and waveform measurements cannot fully predict perceived
balance, test fixtures may miss real-world channel layouts, and manual
listening results are environment-dependent
**Affected surfaces:** end-to-end fixtures, GUI, CLI, preview, export,
ffprobe verification, audio measurements, source-preservation checks, and
evidence
**Evidence path:** `evidence/phase-005-balanced-delivery-verification.md`
**Protected behaviors:** all existing one-source and mixed-source editing,
persistence, output safety, GUI/CLI parity, and legacy helper workflows
remain required regression baselines
**Last updated:** 2026-08-22

## Outcome

PHASE-005 has reproducible evidence that source-level audio decisions and
delivery routes produce playable, synchronized, source-safe mixed-source
outputs.

## Scope

- Exercise representative quiet, loud, clipped, silent, mono, stereo,
  multi-channel, mixed-codec, mixed-dimension, and mixed-frame-rate sources.
- Compare source decisions, preview, CLI inspection, save/reopen state,
  export route, output metadata, duration, channels, and playability.
- Measure peak safety and other approved audio criteria.
- Perform target-workstation manual listening and document limitations.
- Verify source files, project state, and last valid outputs survive failures.

## Explicit non-goals

- Adding new product behavior not covered by FEAT-014 through FEAT-016.
- Automatic focus, triplicate composition, visual transforms, or 60 FPS
  enhancement.
- Treating JSON equality, metadata, or a fast command alone as proof of media
  correctness.

## Observable requirements

- Given the same mixed-source fixture and operation sequence, GUI and CLI
  should produce equivalent source decisions, route explanations, persisted
  state, and final duration.
- Given a successful export, output should satisfy the approved peak,
  channels, duration, dimensions, stream, metadata, and playability checks.
- Given representative listening, the evidence should distinguish subjective
  balance from measurable compliance.
- Given an invalid or failed operation, sources, project state, and last valid
  output should remain intact.

## Commands and quality gates

- `python3 -m unittest discover -s tests`
- `make contract`
- `make check`
- `make smoke`
- `make quality PYTHON=.venv/bin/python`
- Target-workstation FFmpeg/ffprobe and manual listening verification.

## Functionality flows

- Run the complete GUI flow from mixed-source import through analysis,
  inspection, editing, preview, save/reopen, and export.
- Run the equivalent CLI flow and compare source decisions, route, project
  state, duration, output metadata, and errors.
- Repeat successful and failed export paths and verify source preservation.

## User validation before closure

Use at least two disposable local videos with different audio levels and
media parameters. Confirm source-level consistency across split segments,
inspect GUI/CLI parity, listen to the output, verify metadata and duration
with ffprobe, and confirm original sources remain unchanged.

## Definition of done

- Automated, real-media, GUI/CLI, persistence, output, source-safety, and
  manual-listening evidence is recorded.
- Every PHASE-005 exit condition has terminal evidence or an explicit blocked
  or skipped reason.
- The feature does not claim triplicate, visual-transform, or 60 FPS support.

## Closure

PHASE-005 integrated delivery verification is complete in local delivery
checkpoint `6aebb26121eb7e4088b4c3678b670038116be2be`.
