# TICKET-019 - Implement Mixed-Source Import, Probing, and Persistence

**Ticket ID:** TICKET-019
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Phase:** PHASE-004
**Feature:** FEAT-010
**Capability links:** CAP-007, CAP-012
**Status:** complete
**Closure:** user-approved on 2026-08-22 after successful implementation,
review evidence, and target-workstation validation; remote checks remain
unavailable and are recorded as an accepted warning.
**Path history:** `tickets/open/TICKET-019-implement-mixed-source-import-probing-and-persistence.md`
-> `tickets/closed/TICKET-019-implement-mixed-source-import-probing-and-persistence.md`
**Horizon:** future
**Priority:** 2
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
`docs/planning/tickets/open/TICKET-018-defining-multi-source-project-identity-and-relinking.md`,
`AGENTS.md`, `.github/aidd-config.yml`
**Dependencies:** TICKET-018; FFmpeg/ffprobe; representative files with
different dimensions, orientations, frame rates, codecs, and audio streams
**Risks:** partial imports, incorrect probe metadata, source mutation,
non-atomic project writes, and invalid recovery after a missing source
**Affected surfaces:** import flow, media probing, project model, persistence,
relinking/error presentation, CLI, GUI, and tests
**Evidence path:** `evidence/phase-004-mixed-source-import.md`

## Outcome

The user can add several local videos to one project and save/reopen the
project with complete source metadata while original files remain untouched.

## Scope

- Import multiple sources using the TICKET-018 identity contract.
- Probe and retain media characteristics required by timeline and export
  decisions.
- Persist source registry and source-level settings atomically.
- Reopen projects with deterministic ordering and explicit missing-source
  recovery.
- Expose import results and failures through the GUI and CLI boundaries.

## Explicit non-goals

- Timeline ordering, movement, multi-selection, or segment editing.
- Preview composition, output normalization, audio gain, triplicate layouts,
  or FPS enhancement.
- Copying, moving, deleting, or transcoding original source media.

## Observable requirements

- Given two or more readable videos, import creates distinct stable source
  entries with correct probe metadata.
- Given a failed probe or partial import, valid project state and all source
  files remain unchanged.
- Given a saved multi-source project, reopening restores source identities,
  metadata, settings, and deterministic order.
- Given one missing source, the user and CLI receive an actionable error while
  unaffected source state remains recoverable.

## Commands and quality gates

- `make test`
- `make check`
- `make contract`
- `make quality PYTHON=.venv/bin/python`
- `make smoke` with disposable mixed-source media

## Functionality flows

- Import generated landscape and portrait fixtures and inspect their metadata.
- Save, reopen, and compare source identities and metadata.
- Remove access to one disposable source and verify safe recovery.

## User validation before closure

Import at least two local videos with different dimensions or frame rates,
save and reopen the project, verify each source identity and metadata, and
confirm no source file was modified.

## Protected behavior

Single-source import, schema versioning, source-path redaction, atomic saves,
last-valid-project recovery, and the existing media-preparation scripts remain
unchanged.

## Definition of done

- Multi-source import and probing are implemented through the approved schema.
- Save/reopen and missing-source recovery are covered by focused and real-media
  evidence.
- Source-preservation and one-source regression evidence is recorded.
