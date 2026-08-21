# TICKET-003 - Implement Source Playback Control State

**Ticket ID:** TICKET-003
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Phase:** PHASE-001
**Feature:** FEAT-002
**Capability links:** CAP-002, CAP-012
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
**Dependencies:** TICKET-001 and TICKET-002; selected playback backend and
source/project contract
**Risks:** backend-specific seek behavior; position drift; blocking media
  work on the interface thread; ambiguous timing for variable-frame-rate
  sources
**Affected surfaces:** playback service/state, source metadata, timeline
  position model, error handling, automated tests
**Evidence path:** `evidence/playback-control-state.md`

## Dependency resolution

TICKET-001 and TICKET-002 are complete. Their runtime/playback decision and
source-opening contract are covered by the linked evidence records.

## Outcome

Given an opened one-source project, the editor has a deterministic playback
state that can start, pause, and seek through the source while exposing
current position and duration and preserving explicit backend failures.

## Scope

- Implement the playback control boundary selected by TICKET-001.
- Model play, pause, stopped, seeking, position, duration, and failure
  transitions needed by the primary interface.
- Translate valid seek requests into backend operations and publish the
  resulting position or an explicit limitation.
- Keep playback failures and unavailable backends separate from valid project
  state.
- Add focused tests for state transitions, invalid positions, and backend
  failures.

## Explicit non-goals

- Building the final GUI layout or timeline controls.
- Splitting, deleting, moving, copying, pasting, or exporting segments.
- Multiple sources, multiple tracks, composition, audio normalization, or
  FPS enhancement.
- Project save/reopen integration beyond consuming the source contract.

## Observable requirements

- Given an opened supported source, play should enter an observable playing
  state and pause should stop advancement without losing the source.
- Given a valid position, seek should update the playback position or return
  an explicit backend limitation.
- Given an invalid position or backend failure, the state should expose a
  structured error and remain recoverable.
- Given source duration metadata, the playback state should expose a
  consistent duration and current position for the timeline.

## Validation and evidence

- Run focused playback/state tests with deterministic backend doubles or
  fixtures following repository conventions.
- Run the protected baseline command:
  `python3 -m unittest discover -s tests`.
- Record backend limitations, unavailable checks, and failure behavior at
  `evidence/playback-control-state.md`.
- Do not retain private media paths or sensitive metadata in durable evidence.

## Protected behavior

Existing curses workflows, media-processing commands, tests, and source-safe
output behavior remain available and unchanged.

## Definition of done

- Playback state supports play, pause, seek, position, duration, and explicit
  failure behavior through the selected backend boundary.
- Focused automated coverage verifies normal and failure transitions.
- Existing tests remain green and evidence records known timing/seek limits.
- No GUI or future editing feature is claimed beyond this ticket.
