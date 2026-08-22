# TICKET-026 - Implement Verified Mixed-Source Export

**Ticket ID:** TICKET-026
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Phase:** PHASE-004
**Feature:** FEAT-012
**Capability links:** CAP-005, CAP-007, CAP-012
**Status:** complete
**Closure:** user-approved on 2026-08-22 after successful implementation,
review evidence, and target-workstation validation; remote checks remain
unavailable and are recorded as an accepted warning.
**Path history:** `tickets/open/TICKET-026-implement-verified-mixed-source-export.md`
-> `tickets/closed/TICKET-026-implement-verified-mixed-source-export.md`
**Horizon:** future
**Priority:** 9
**Owner:** repository implementation in the active Phase 4 worktree
**Approval:** user-authorized on 2026-08-21 to prepare and implement all
current PHASE-004 open tickets; CHG-002 applies the fixed project render
profile; human validation remains required before closure
**Provider:** auto; base and target branches are not configured in
`.github/aidd-config.yml`
**Source paths:** `vision.md`, `docs/specs/project-scope.md`,
`docs/specs/capability-map.md`,
`docs/planning/phases/open/PHASE-004-combining-mixed-source-footage.md`,
`docs/planning/features/open/FEAT-012-previewing-and-exporting-mixed-source-edits.md`,
`docs/planning/tickets/open/TICKET-024-defining-mixed-source-output-canvas-and-timing-policy.md`,
`docs/planning/tickets/closed/TICKET-011-verified-safe-export.md`,
`docs/specs/phase-002-export-policy.md`, `AGENTS.md`,
`.github/aidd-config.yml`
**Dependencies:** TICKET-024 and CHG-002; mixed-source timeline operations;
validated FFmpeg/ffprobe; output verification and atomic publication behavior
**Risks:** invalid timestamps, missing streams, duration drift, fixed-canvas
scaling cost, unsafe fallback output, partial-file exposure, and source
replacement
**Affected surfaces:** export planner/executor, FFmpeg filters, validation,
progress reporting, CLI, GUI, persistence, and tests
**Evidence path:** `evidence/phase-004-mixed-source-export.md`

## Outcome

The user can export a mixed-source edit through the fastest valid route or an
explicit fallback and receive a verified output without changing source files.

## Scope

- Implement the fixed 1920x1080 TICKET-024 canvas and current timing behavior
  in export planning for one-source and mixed-source projects.
- Contain-scale mixed dimensions and orientations and use the established
  render profile for output container, codecs, audio, and pixel format.
- Reuse temporary-output, progress, ffprobe validation, and atomic publication
  boundaries from the one-source export.
- Report route, normalization reason, output metadata, duration, and failures.
- Keep GUI and CLI export results equivalent.

## Explicit non-goals

- Automatic per-input audio-level normalization.
- Source-driven codec/container selection, triplicate composition, reusable
  transforms, or 60 FPS enhancement.
- Publishing output before validation or overwriting source media.

## Observable requirements

- Given any mixed-source inputs, the exporter renders to 1920x1080 using the
  established profile and reports why composition is required.
- Given a non-1080p one-source input, the exporter renders to 1920x1080 using
  the established fallback profile and reports why scaling is required.
- Given source codec/container differences, the exporter keeps the established
  output profile instead of changing it based on the inputs.
- Given a failed encode, validation, or publication, sources, project state,
  and the last valid output remain intact.
- Given a successful export, duration, dimensions, streams, and metadata match
  the approved output policy.

## Commands and quality gates

- `make test`
- `make contract`
- `make check`
- `make quality PYTHON=.venv/bin/python`
- `make smoke` with generated mixed-source media
- FFmpeg/ffprobe output verification

## Functionality flows

- Export portrait plus landscape fixtures and verify 1920x1080 canvas metadata.
- Exercise mixed inputs with different source codecs and verify the established
  output profile remains selected.
- Interrupt or invalidate an export and verify source/output recovery.

## User validation before closure

Export a disposable mixed-source project, inspect duration/dimensions/streams
with ffprobe, confirm the fixed 1920x1080 canvas and established render
profile, confirm progress information, and verify that all original sources
remain unchanged.

## Protected behavior

The existing one-source progress fields, partial-file cleanup, atomic
publication, output verification, and source-preservation guarantees remain
unchanged. Stream copy remains eligible for one-source inputs that already
match the fixed canvas.

## Definition of done

- Mixed-source export uses the fixed 1920x1080 canvas and established profile.
- Fast/fallback, validation, failure recovery, progress, and source safety
  evidence is recorded for GUI and CLI.
