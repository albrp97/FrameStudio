# TICKET-005 - Persist a Versioned One-Source Project

**Ticket ID:** TICKET-005
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Phase:** PHASE-001
**Feature:** FEAT-003
**Capability links:** CAP-004, CAP-012
**Status:** complete
**Horizon:** first
**Priority:** 3
**Owner:** repository planning; implementer is not assigned
**Approval:** user-approved on 2026-08-21 before execution
**Source paths:** `vision.md`, `docs/specs/project-scope.md`,
`docs/planning/phases.md`, `docs/planning/features.md`,
`docs/planning/backlog.md`,
`docs/planning/tickets/closed/TICKET-001-editor-foundation-contract.md`,
`docs/planning/tickets/closed/TICKET-002-open-supported-source.md`,
`AGENTS.md`, `.github/aidd-config.yml`
**Dependencies:** TICKET-001 and TICKET-002; approved one-source project
contract; local filesystem access
**Risks:** partial writes; incompatible versions; stale or moved source paths;
persisting ambiguous metadata; accidental source mutation
**Affected surfaces:** project serialization, source identity, filesystem
  persistence, validation, migration boundary, automated tests
**Evidence path:** `evidence/versioned-project-persistence.md`

## Dependency resolution

TICKET-001 and TICKET-002 are complete. The initial project/source contract
and source metadata mapping are covered by the linked evidence records.

## Outcome

The editor can persist and reload a valid one-source project through a
versioned machine-readable representation without changing the source or
replacing the last valid project after a failed write.

## Scope

- Implement the initial versioned one-source project representation from the
  TICKET-001 contract.
- Serialize source identity, required metadata, and foundation timeline or
  playback state.
- Use a temporary/partial write and atomic replacement policy for saves.
- Validate project version, required fields, and source availability when
  reopening.
- Surface invalid, incompatible, missing-source, and moved-source conditions
  without silently relinking or discarding valid state.
- Add focused tests for serialization, round trips, validation, and failed
  writes.

## Explicit non-goals

- GUI save/reopen actions or playback presentation.
- Split, delete, export, CLI, multiple-source, multiple-track, composition,
  audio-normalization, or FPS settings.
- Destructive source modification, silent relinking, or source deletion.
- Future migration implementations beyond the initial compatibility
  boundary.

## Observable requirements

- Given a valid one-source project, saving should create a versioned
  machine-readable file without changing the source.
- Given a valid saved project, reopening should restore the source identity,
  required metadata, and foundation state.
- Given an invalid or incompatible project, loading should return a clear
  error and preserve the last valid project state.
- Given a failed or interrupted save, the previously valid project file should
  remain usable.

## Validation and evidence

- Run focused project serialization and atomic-write failure tests.
- Run the protected baseline command:
  `python3 -m unittest discover -s tests`.
- Record project validity, round-trip behavior, failure handling, and source
  preservation at `evidence/versioned-project-persistence.md`.
- Redact private source paths and record unavailable filesystem checks with a
  reason.

## Protected behavior

Original media, existing scripts, command names, tests, and source-safe
partial-output behavior remain available and unchanged.

## Definition of done

- The initial versioned one-source project representation is implemented and
  validates required source/foundation state.
- Save/reopen round trips, invalid versions, missing sources, and failed
  writes are covered by focused tests.
- Source-preservation and baseline evidence is recorded.
- GUI integration and future editing capabilities remain outside this
  ticket.
