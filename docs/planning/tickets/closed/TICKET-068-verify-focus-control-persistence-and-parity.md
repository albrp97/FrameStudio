# TICKET-068 - Verify Focus-Control Persistence and Parity

**Ticket ID:** TICKET-068
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Phase:** PHASE-008
**Feature:** FEAT-025
**Capability links:** CAP-003, CAP-006, CAP-009, CAP-010, CAP-012
**Status:** complete
**Closure:** closed on 2026-08-26 after persistence, CLI parity, triplicate
linkage, bounded-value tests, and target-workstation validation passed.
**Horizon:** future
**Priority:** 3
**Owner:** repository planning; maintainer identity is not recorded
**Approval:** user-authorized on 2026-08-26 for PHASE-008 planning; execution
requires the configured preimplementation and approval gates
**Last updated:** 2026-08-26
**Source paths:** `docs/planning/features/closed/FEAT-025-streamlining-segment-focus-modifications.md`,
`docs/planning/tickets/closed/TICKET-066-implement-scroll-driven-focus-modifications.md`,
`docs/planning/tickets/closed/TICKET-067-correct-zoomed-focus-coordinate-bounds.md`,
`framestudio/persistence.py`, `framestudio/cli.py`,
`framestudio/cli_payload.py`, `framestudio/operations.py`,
`tests/test_editor_persistence.py`, `tests/test_editor_cli_editing.py`,
`tests/test_editor_cli_parity.py`, `.github/aidd-config.yml`
**Dependencies:** TICKET-066 and TICKET-067; existing versioned project and
CLI contracts; GUI test access
**Risks:** GUI and CLI can disagree on units or clamp behavior; reopened
projects may lose group linkage or stale preview state
**Affected surfaces:** JSON persistence, CLI focus operations, GUI state,
triplicate groups, round-trip tests, and user-facing documentation
**Evidence path:** `evidence/phase-008-focus-controls.md`
**Path history:** `tickets/open/TICKET-068-verify-focus-control-persistence-and-parity.md`
-> `tickets/closed/TICKET-068-verify-focus-control-persistence-and-parity.md`
**Protected behaviors:** project versioning, CLI structured errors, source
preservation, existing focus/triplicate state, and safe export

## Outcome

Direct focus changes have the same bounded meaning in the GUI, saved project,
reopened project, and deterministic CLI.

## Scope

- Add or update round-trip tests for zoom and X/Y values at normal, 2x, and
  4x bounds.
- Verify triplicate group persistence and shared-focus behavior.
- Verify CLI inspection and focus commands expose the same values and errors.
- Provide the exact user-facing setup and evidence for the controls.

## Explicit non-goals

- Adding new CLI commands unrelated to focus.
- Migrating the project schema without an approved compatibility need.
- Declaring the controls usable without the target-workstation check.

## Observable requirements

- Given a GUI focus adjustment, save/reopen should preserve its bounded value.
- Given an equivalent CLI operation, GUI inspection and CLI output should
  agree.
- Given invalid values, both surfaces should report or clamp consistently.
- Given a triplicate segment, linkage and shared values should survive the
  round trip.

## Definition of done

- Persistence and CLI parity tests pass for focus and triplicate state.
- User-facing setup, expected results, failure paths, and cleanup are recorded.
- Target-workstation evidence covers direct controls and reopened state.

## User-validation plan

- **Setup:** create or open a project with normal and triplicate segments.
- **Steps:** adjust focus in the GUI, save, reopen, inspect through CLI, apply
  an equivalent CLI change, and compare the visible result.
- **Expected result:** values, bounds, group links, and preview meaning agree.
- **Failure paths:** lost values, mismatched units, or structured-error drift
  block the ticket.
- **Cleanup:** restore or remove the temporary project without touching source
  media.
- **Evidence response:** return GUI/CLI payload comparison and round-trip
  observations.
- **Pass criteria:** parity and persistence are terminally evidenced.

## Closure

TICKET-068 was closed after GUI, saved-project, reopened-project, and CLI
values matched for normal, 2x, and 4x focus states, including triplicate
linkage. The user's target-workstation validation returned `PASS`.
