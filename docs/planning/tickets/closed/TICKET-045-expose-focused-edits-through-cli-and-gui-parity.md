# TICKET-045 - Expose Focused Edits Through CLI and GUI Parity

**Ticket ID:** TICKET-045
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Phase:** PHASE-006
**Feature:** FEAT-019
**Capability links:** CAP-005, CAP-009, CAP-010, CAP-012
**Status:** complete
**Closure:** user-approved on 2026-08-23 after PHASE-006 implementation,
automated verification, shared target-workstation validation, review, and
local delivery evidence; remote checks remain unavailable and are recorded as
an accepted warning.
**Horizon:** future
**Priority:** 8
**Owner:** repository planning; maintainer identity is not recorded
**Approval:** user-authorized on 2026-08-22 to create and implement the
PHASE-006 ticket set; the completed outcome was confirmed by the user on
2026-08-23
**Provider:** auto; base and target branches are not configured in
`.github/aidd-config.yml`
**Source paths:** `docs/planning/tickets/open/TICKET-044-persist-focused-composition-state.md`,
`docs/planning/features/open/FEAT-019-delivering-focused-compositions-safely.md`,
`docs/specs/cli-contract.md`, `framestudio/cli.py`,
`framestudio/cli_payload.py`, `framestudio/app_ui.py`,
`framestudio/operations.py`, `.github/aidd-config.yml`
**Dependencies:** TICKET-044; existing deterministic CLI and shared GUI/CLI
domain operations
**Risks:** CLI and GUI can expose different defaults, structured errors can
lose linked-state detail, and automation can imply unsupported behavior
**Affected surfaces:** CLI parser and payloads, GUI controls and status,
shared operations, documentation, tests, and evidence
**Evidence path:** `evidence/phase-006-focused-composition-surfaces.md`
**Last updated:** 2026-08-23
**Path history:** `tickets/open/TICKET-045-expose-focused-edits-through-cli-and-gui-parity.md`
-> `tickets/closed/TICKET-045-expose-focused-edits-through-cli-and-gui-parity.md`

## Outcome

The GUI and deterministic CLI expose the same transform and triplicate state,
operations, diagnostics, and persisted values.

## Scope

- Extend inspection payloads with transform bundles and linked-group state.
- Expose deterministic operations for applying, cleaning, enabling, and
  disabling supported focused edits.
- Route GUI and CLI actions through shared domain operations.
- Report pending, invalid, unsupported, and failed states explicitly.
- Update the CLI contract and user-facing documentation without changing
  existing command behavior.

## Explicit non-goals

- New rendering or output-policy behavior.
- Natural-language orchestration, arbitrary effects, or 60 FPS enhancement.
- Separate per-surface defaults or hidden automatic focus decisions.

## Observable requirements

- Given a focused project, GUI and CLI inspection should return equivalent
  values, group identities, roles, and statuses.
- Given a supported focused edit command, the CLI and GUI should produce the
  same persisted domain state.
- Given invalid or unsupported input, both surfaces should expose the same
  structured diagnostic without a success-shaped response.
- Given a project with several segments, output should distinguish
  segment-owned values from source-level audio decisions.

## Commands and quality gates

- `python3 -m unittest discover -s tests`
- `make check`
- `make contract`
- `make quality PYTHON=.venv/bin/python`

## Functionality flows

- Inspect, modify, clean, and inspect a focused project through the CLI.
- Perform the same operations in the GUI and compare reopened project state.
- Trigger invalid and unsupported cases and compare structured errors.

## User validation before closure

Run equivalent GUI and CLI operations on a disposable focused project,
save/reopen it, and confirm values, linked groups, statuses, and errors match.

## Protected behavior

Existing CLI JSON contracts, GUI/CLI shared operations, project compatibility,
source identity, segment colors, audio decisions, fixed output canvas, source
preservation, and legacy scripts remain unchanged.

## Definition of done

- Focused state and operations are exposed consistently through GUI and CLI.
- Contract, parity, success, and failure tests pass.
- User-validation evidence demonstrates equivalent persisted state.

## Closure

Focused composition GUI/CLI parity is complete under the reviewed PHASE-006
delivery checkpoint. Provider-side checks remain unavailable because no
remote or upstream is configured.
