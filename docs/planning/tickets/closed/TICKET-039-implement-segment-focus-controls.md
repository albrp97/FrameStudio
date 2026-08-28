# TICKET-039 - Implement Segment Focus Controls

**Ticket ID:** TICKET-039
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Phase:** PHASE-006
**Feature:** FEAT-017
**Capability links:** CAP-009, CAP-012
**Status:** complete
**Closure:** user-approved on 2026-08-23 after PHASE-006 implementation,
automated verification, shared target-workstation validation, review, and
local delivery evidence; remote checks remain unavailable and are recorded as
an accepted warning.
**Horizon:** future
**Priority:** 2
**Owner:** repository planning; maintainer identity is not recorded
**Approval:** user-authorized on 2026-08-22 to create and implement the
PHASE-006 ticket set; the completed outcome was confirmed by the user on
2026-08-23
**Provider:** auto; base and target branches are not configured in
`.github/aidd-config.yml`
**Source paths:** `docs/planning/tickets/open/TICKET-038-define-segment-visual-modification-contract.md`,
`docs/planning/features/open/FEAT-017-editing-reusable-visual-focus-controls.md`,
`docs/planning/phases/open/PHASE-006-focusing-and-composing-important-action.md`,
`framestudio/model_project.py`, `framestudio/operations.py`,
`framestudio/app_ui.py`, `.github/aidd-config.yml`
**Dependencies:** TICKET-038; stable segment and selection operations
**Risks:** UI actions can update only part of a selected group, invalid values
can leak into preview state, and clean/reset can accidentally alter timing
**Affected surfaces:** segment model, transform operations, timeline
selection, GUI controls, status/error handling, tests, and evidence
**Evidence path:** `evidence/phase-006-visual-focus-controls.md`
**Last updated:** 2026-08-23
**Path history:** `tickets/open/TICKET-039-implement-segment-focus-controls.md`
-> `tickets/closed/TICKET-039-implement-segment-focus-controls.md`

## Outcome

The editor lets a user apply zoom and X/Y focus values to one or more
selected segments and clean those values without changing timeline content.

## Scope

- Add segment-owned zoom and X/Y values using the TICKET-038 contract.
- Apply a single validated value set to the current selection.
- Provide visible transform controls and a **Clean modifications** action.
- Keep each selected segment's identity and state independent.
- Surface invalid values through the existing explicit error/status path.

## Explicit non-goals

- Triplicate layout or linked-group behavior.
- Transform persistence and CLI command expansion, which belong to FEAT-019.
- Final renderer or output-policy changes.
- Keyframes, arbitrary effects, or 60 FPS enhancement.

## Observable requirements

- Given one selected segment, changing zoom or X/Y should update its
  modification bundle and leave its source interval unchanged.
- Given several selected segments, applying values should update all selected
  bundles without merging their identities.
- Given a modified segment, **Clean modifications** should restore defaults
  without changing color, deletion state, position, or duration.
- Given invalid transform input, the editor should clamp or report the
  contract-defined error without partially applying the operation.

## Commands and quality gates

- `python3 -m unittest discover -s tests`
- `make check`
- `make contract`
- `make quality PYTHON=.venv/bin/python`

## Functionality flows

- Select one segment and apply, inspect, and clean a focus adjustment.
- Select a range and a Ctrl-click group and apply shared values.
- Submit invalid values and verify explicit diagnostics and unchanged state.

## User validation before closure

Apply zoom and X/Y changes to one segment and a multi-selection, use
**Clean modifications**, and confirm visible focus changes without timeline or
source changes. Return `PASS`, `FAIL`, or `BLOCKED` with evidence.

## Protected behavior

Existing selection semantics, segment colors and ordering, split/delete
behavior, source-level audio decisions, fixed output canvas, project safety,
and legacy scripts remain unchanged.

## Definition of done

- Transform controls and clean/reset are implemented against the approved
  contract.
- Focused model, UI, and failure-path tests pass.
- User-facing evidence confirms timeline and source state are preserved.

## Closure

Segment focus controls and clean/reset behavior are complete under the
reviewed PHASE-006 delivery checkpoint. Provider-side checks remain
unavailable because no remote or upstream is configured.
