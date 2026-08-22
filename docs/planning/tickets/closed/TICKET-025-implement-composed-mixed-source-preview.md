# TICKET-025 - Implement Composed Mixed-Source Preview

**Ticket ID:** TICKET-025
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Phase:** PHASE-004
**Feature:** FEAT-012
**Capability links:** CAP-002, CAP-005, CAP-007, CAP-012
**Status:** complete
**Closure:** user-approved on 2026-08-22 after successful implementation,
review evidence, and target-workstation validation; remote checks remain
unavailable and are recorded as an accepted warning.
**Path history:** `tickets/open/TICKET-025-implement-composed-mixed-source-preview.md`
-> `tickets/closed/TICKET-025-implement-composed-mixed-source-preview.md`
**Horizon:** future
**Priority:** 8
**Owner:** repository implementation in the active Phase 4 worktree
**Approval:** user-authorized on 2026-08-21 to prepare and implement all
current PHASE-004 open tickets; human validation remains required before
closure
**Provider:** auto; base and target branches are not configured in
`.github/aidd-config.yml`
**Source paths:** `vision.md`, `docs/specs/project-scope.md`,
`docs/specs/capability-map.md`,
`docs/planning/phases/open/PHASE-004-combining-mixed-source-footage.md`,
`docs/planning/features/open/FEAT-012-previewing-and-exporting-mixed-source-edits.md`,
`docs/planning/tickets/open/TICKET-019-implement-mixed-source-import-probing-and-persistence.md`,
`docs/planning/tickets/open/TICKET-020-defining-mixed-source-timebase-and-placement-semantics.md`,
`docs/planning/tickets/open/TICKET-024-defining-mixed-source-output-canvas-and-timing-policy.md`,
`AGENTS.md`, `.github/aidd-config.yml`
**Dependencies:** TICKET-019, TICKET-020, and TICKET-024; mixed-source
playback fixtures; available FFmpeg playback path
**Risks:** preview stutter, stale frames after seeking, incorrect source
boundaries, scaling mismatch, and divergence from export timing
**Affected surfaces:** playback backend, composed preview, timeline source
boundaries, GUI responsiveness, project settings, and tests
**Evidence path:** `evidence/phase-004-mixed-source-preview.md`

## Outcome

The editor previews the composed mixed-source timeline in real time with
clear source boundaries and the approved canvas and timing behavior.

## Scope

- Compose multiple source streams for preview using TICKET-024 policy.
- Show source boundaries, current source identity, and final-duration context.
- Preserve responsive play, pause, seek, frame stepping, and timeline drag.
- Cancel stale preview work when the playhead changes and show the latest
  requested frame.
- Surface unsupported preview media and timing limitations explicitly.

## Explicit non-goals

- Final export execution or automatic audio-level normalization.
- Triplicate composition, reusable transforms, or FPS enhancement.
- Replacing the established one-source preview backend.

## Observable requirements

- Given multiple sources, preview order and source boundaries match persisted
  timeline state.
- Given mixed dimensions, preview follows the approved canvas behavior without
  silent distortion.
- Given rapid timeline seeking, stale frames do not replace the latest
  requested position.
- Given an unavailable decoder or unsupported input, the UI reports an
  actionable limitation instead of a false frame.

## Commands and quality gates

- `make test`
- `make check`
- `make quality PYTHON=.venv/bin/python`
- `make smoke` with disposable mixed-source media
- Target-workstation manual preview flow

## Functionality flows

- Preview two sources with different dimensions and seek across the boundary.
- Drag rapidly through the composed timeline and inspect the final frame.
- Pause, frame-step, resume, and compare the displayed source identity.

## User validation before closure

Preview at least two local videos with different orientations or frame rates,
seek and drag across source boundaries, and confirm the image, source
indicator, and final-duration display remain responsive and correct.

## Protected behavior

One-source play/pause, Space handling, frame stepping, drag preview
responsiveness, source safety, and existing GTK/FFmpeg error presentation
remain protected.

## Definition of done

- Mixed-source preview follows the approved policy and remains responsive.
- Source boundaries, seek behavior, errors, regression, and real-media
  evidence are recorded.
