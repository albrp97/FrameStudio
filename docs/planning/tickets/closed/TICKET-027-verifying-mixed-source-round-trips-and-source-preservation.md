# TICKET-027 - Verify Mixed-Source Round Trips and Source Preservation

**Ticket ID:** TICKET-027
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Phase:** PHASE-004
**Feature:** FEAT-012
**Capability links:** CAP-002, CAP-003, CAP-005, CAP-007, CAP-012
**Status:** complete
**Closure:** user-approved on 2026-08-22 after successful implementation,
review evidence, and target-workstation validation; remote checks remain
unavailable and are recorded as an accepted warning.
**Path history:** `tickets/open/TICKET-027-verifying-mixed-source-round-trips-and-source-preservation.md`
-> `tickets/closed/TICKET-027-verifying-mixed-source-round-trips-and-source-preservation.md`
**Horizon:** future
**Priority:** 10
**Owner:** repository implementation in the active Phase 4 worktree
**Approval:** user-authorized on 2026-08-21 to prepare and implement all
current PHASE-004 open tickets; human validation remains required before
closure
**Provider:** auto; base and target branches are not configured in
`.github/aidd-config.yml`
**Source paths:** `vision.md`, `docs/specs/project-scope.md`,
`docs/specs/capability-map.md`,
`docs/planning/phases/open/PHASE-004-combining-mixed-source-footage.md`,
`docs/planning/features/open/FEAT-010-importing-and-retaining-mixed-source-project-identity.md`,
`docs/planning/features/open/FEAT-011-arranging-and-editing-a-mixed-source-timeline.md`,
`docs/planning/features/open/FEAT-012-previewing-and-exporting-mixed-source-edits.md`,
`docs/planning/tickets/open/TICKET-023-exposing-mixed-source-timeline-operations-through-the-cli.md`,
`docs/planning/tickets/open/TICKET-025-implement-composed-mixed-source-preview.md`,
`docs/planning/tickets/open/TICKET-026-implement-verified-mixed-source-export.md`,
`AGENTS.md`, `.github/aidd-config.yml`
**Dependencies:** TICKET-019, TICKET-021, TICKET-022, TICKET-023, TICKET-025,
and TICKET-026; CHG-002 fixed project canvas; representative generated and local media;
target workstation manual workflow
**Risks:** tests that cover only serialization, missed GUI/CLI drift,
unobserved timestamp errors, non-deterministic retries, and incomplete manual
coverage
**Affected surfaces:** end-to-end fixtures, GUI, CLI, timeline, persistence,
preview, export, evidence, and documentation
**Evidence path:** `evidence/phase-004-mixed-source-round-trip.md`

## Outcome

PHASE-004 has actionable automated, real-media, manual, and source-preservation
evidence showing that mixed-source import, editing, preview, persistence, CLI,
and export work together without losing identity or producing unsafe output.

## Scope

- Build representative fixtures with deliberately different media parameters.
- Exercise import, inspect, order, atomic block movement, copy/paste,
  multi-selection, split, delete/restore, duration, save/reopen, CLI parity,
  preview, and export.
- Compare successful and failed GUI-domain and CLI-domain operations.
- Verify fixed 1920x1080 output metadata, current timing, stream presence, and
  source preservation.
- Record environment limitations and any deferred coverage without claiming
  unsupported capabilities.

## Explicit non-goals

- Adding product behavior not covered by FEAT-010 through FEAT-012.
- Automatic audio normalization, source-driven codec selection, triplicate
  composition, reusable transforms, or 60 FPS enhancement.
- Treating JSON equality alone as proof of media correctness.

## Observable requirements

- Given the same mixed-source fixture and operation sequence, GUI and CLI
  produce equivalent persisted state and final duration.
- Given a save/reopen round trip, source identities, placements, segments,
  deletion state, block-owned state, display colors, and settings remain
  intact.
- Given a block copy/paste and split sequence, pasted and child identities are
  fresh, source intervals and owned state are preserved, and originals remain
  unchanged.
- Given a successful export, output is independently playable, uses the fixed
  1920x1080 canvas and established render profile for one-source and
  mixed-source projects, and every source remains unchanged.
- Given an invalid or failed operation, valid project/output state survives and
  the user receives an actionable error.

## Commands and quality gates

- `make test`
- `make contract`
- `make check`
- `make quality PYTHON=.venv/bin/python`
- `make smoke` with disposable mixed-source media
- Target-workstation GUI preview/edit/export validation
- Evidence review against all PHASE-004 exit conditions

## Functionality flows

- Run the complete mixed-source GUI flow from import through block editing and
  export.
- Run the equivalent CLI flow and compare inspection, saved project, and
  output metadata.
- Repeat successful and failed operations and compare deterministic results.

## User validation before closure

Complete the documented mixed-source workflow with at least two local videos,
confirm order, block movement/copy/paste, selection, editing, preview, final
duration, save/reopen, CLI parity, fixed 1920x1080 export metadata,
established render-profile behavior, and unchanged source files, then report
any environment-specific limitations.

## Protected behavior

All first-horizon one-source editor, CLI, persistence, export, safety, and
legacy-script behavior remains a required regression baseline.

## Definition of done

- Automated, real-media, manual, GUI/CLI parity, and source-preservation
  evidence is recorded.
- Every PHASE-004 exit condition has evidence or an explicitly documented gap.
- No later audio, composition, transform, or 60 FPS capability is claimed.
