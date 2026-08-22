# TICKET-035 - Route Audio-Aware and Mixed-Source Exports Safely

**Ticket ID:** TICKET-035
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Phase:** PHASE-005
**Feature:** FEAT-015
**Capability links:** CAP-005, CAP-008, CAP-012
**Status:** verifying
**Horizon:** future
**Priority:** 5
**Owner:** repository planning and implementation in the active worktree
**Approval:** user-authorized on 2026-08-22 to implement all approved
PHASE-005 tickets, including source-level audio balancing, with the legacy
`resolve_concat.py` mean/median policy applied once per input source
**Provider:** auto; base and target branches are not configured in
`.github/aidd-config.yml`
**Source paths:** `docs/planning/features/open/FEAT-015-selecting-tested-delivery-routes.md`,
`docs/planning/tickets/open/TICKET-033-apply-source-audio-decisions-consistently.md`,
`docs/planning/tickets/open/TICKET-034-benchmark-and-document-delivery-profiles.md`,
`docs/planning/tickets/closed/TICKET-024-defining-mixed-source-output-canvas-and-timing-policy.md`,
`docs/planning/tickets/closed/TICKET-026-implement-verified-mixed-source-export.md`,
`resolve_editor/export.py`, `resolve_editor/operations.py`,
`.github/aidd-config.yml`
**Dependencies:** TICKET-033; TICKET-034; existing verified export and
temporary-output boundaries; validated FFmpeg/ffprobe
**Risks:** incorrect route eligibility can create missing audio, invalid
timestamps, duration drift, or an exposed partial output
**Affected surfaces:** export planner, FFmpeg command construction, process
execution, output verification, progress reporting, GUI, CLI, tests, and
evidence
**Evidence path:** `evidence/phase-005-audio-aware-export-routing.md`
**Protected behaviors:** source files are never overwritten, partial files
are cleaned, verified outputs publish atomically, and existing eligible
one-source stream-copy behavior remains available
**Last updated:** 2026-08-22

## Outcome

Every audio-aware or mixed-source export takes an explainable valid route and
cannot publish an unverified or source-damaging result.

## Scope

- Extend route planning to account for source-level audio changes, mixed
  inputs, fixed-canvas rendering, incompatible streams, and selected profiles.
- Keep stream copy only when all approved eligibility conditions remain true.
- Route other edits through the documented fallback render.
- Preserve progress events, cancellation, temporary partial files, output
  verification, cleanup, and atomic publication.
- Report the route and reason consistently through GUI and CLI.

## Explicit non-goals

- Choosing a new audio policy or delivery profile.
- Per-segment audio decisions.
- Triplicate composition, visual transforms, or 60 FPS enhancement.
- Publishing output before independent validation.

## Observable requirements

- Given an edit with source-level audio processing, the planner should report
  why stream copy is unavailable and select a validated render route.
- Given a mixed-source edit, the planner should preserve the fixed 1920x1080
  canvas and established delivery profile.
- Given an eligible unchanged one-source edit, existing fast-path behavior
  should remain eligible.
- Given an encode, validation, cancellation, or publication failure, sources,
  project state, and the last valid output should remain intact.
- Given a successful export, route, reason, duration, streams, metadata, and
  playability should be verified before publication.

## Commands and quality gates

- `python3 -m unittest discover -s tests`
- `make contract`
- `make check`
- `make smoke`
- `make quality PYTHON=.venv/bin/python`

## Functionality flows

- Export unchanged eligible one-source, source-audio-processed, and
  mixed-source projects and compare route explanations.
- Cancel or invalidate an export and confirm partial cleanup and recovery.
- Inspect progress and final verification through GUI and CLI.

## User validation before closure

Export disposable projects through the fast and fallback routes, review the
route explanation and progress, inspect output metadata and duration, and
confirm original sources and the last valid output remain unchanged after a
failed or cancelled attempt.

## Definition of done

- Route selection is deterministic and explainable.
- Audio-aware and mixed-source outputs use validated fallback behavior.
- Fast-path eligibility remains protected where still valid.
- Failure, cancellation, verification, and source-safety evidence is recorded.
