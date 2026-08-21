# TICKET-004 - Build Preview and Timeline Interaction

**Ticket ID:** TICKET-004
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Phase:** PHASE-001
**Feature:** FEAT-002
**Capability links:** CAP-002, CAP-012
**Status:** complete
**Horizon:** first
**Priority:** 4
**Owner:** repository planning; implementer is not assigned
**Approval:** user-approved on 2026-08-21 before execution
**Source paths:** `vision.md`, `docs/specs/project-scope.md`,
`docs/planning/phases.md`, `docs/planning/features.md`,
`docs/planning/backlog.md`,
`docs/planning/tickets/closed/TICKET-003-playback-control-state.md`,
`AGENTS.md`, `.github/aidd-config.yml`
**Dependencies:** TICKET-003; selected GUI/runtime and playback setup; a
target-workstation manual smoke-test path
**Risks:** UI blocking or dropped frames; preview/timeline desynchronization;
poor feedback during slow seeks; backend-specific rendering limitations
**Affected surfaces:** primary editor interface, preview presentation,
timeline controls, playback binding, user-facing errors, GUI smoke test
**Evidence path:** `evidence/preview-timeline-interaction.md`

## Resolution

The implementation and automated smoke flow are complete. The user confirmed
the target-workstation interaction check, so the dependency blocker is
resolved; the evidence record retains the absence of a screenshot artifact as
an accepted concern.

## Outcome

Given an opened source project, the primary editor interface presents a
real-time preview and understandable timeline controls for play, pause, seek,
current position, and source duration.

## Scope

- Bind the selected playback state to the primary editor interface.
- Present the real-time preview and a timeline representation.
- Provide play, pause, and seek interactions with visible current position
  and duration.
- Keep preview position and timeline state synchronized during playback and
  seeking.
- Surface buffering, unavailable backends, seek limitations, and playback
  failures without losing valid project state.
- Add focused interface/state coverage where the selected runtime supports
  deterministic tests.

## Explicit non-goals

- Split, delete, move, copy, paste, or export operations.
- Multiple sources, multiple tracks, mixed-media normalization, composition,
  audio normalization, or FPS enhancement.
- Final visual polish unrelated to comprehension, accessibility, or
  responsiveness.

## Observable requirements

- Given an opened supported source, the interface should show a preview and
  a timeline with a readable current position and duration.
- Given play or pause, the preview and timeline should advance or stop
  consistently.
- Given a valid seek, the preview and timeline should converge on the
  requested position or show an explicit limitation.
- Given a playback failure, the interface should show an actionable error and
  preserve the source/project state.

## Validation and evidence

- Run focused interface/state tests when the selected runtime permits.
- Run the protected baseline command:
  `python3 -m unittest discover -s tests`.
- Perform the target-workstation manual smoke test for import, preview,
  play/pause, seek, position, duration, and backend failure behavior.
- Record timing/seek observations and unavailable checks at
  `evidence/preview-timeline-interaction.md`.

## Protected behavior

Existing command names, curses workflows, media-processing scripts, tests,
and source-safe behavior remain available and unchanged.

## Definition of done

- The primary interface provides a usable real-time preview and synchronized
  play, pause, seek, position, and duration behavior.
- Failure and limitation states are visible and recoverable.
- Automated coverage where practical, baseline results, and target-
  workstation GUI evidence are recorded.
- No segment editing, export, or future-phase behavior is claimed.
