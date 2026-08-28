# TICKET-065 - Define Direct Focus Modification Interactions

**Ticket ID:** TICKET-065
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Phase:** PHASE-008
**Feature:** FEAT-025
**Capability links:** CAP-003, CAP-009, CAP-010, CAP-012
**Status:** complete
**Closure:** closed on 2026-08-26 after the direct focus interaction contract,
timeline-scroll boundary, feedback rules, keyboard parity, and triplicate
semantics were implemented and validated.
**Horizon:** future
**Priority:** 1
**Owner:** repository planning; maintainer identity is not recorded
**Approval:** user-authorized on 2026-08-26 for PHASE-008 planning; execution
requires the configured preimplementation and approval gates
**Last updated:** 2026-08-26
**Source paths:** `docs/planning/features/closed/FEAT-025-streamlining-segment-focus-modifications.md`,
`docs/specs/future-product-direction.md`, `resolve_editor/app_ui.py`,
`resolve_editor/app_timeline_actions.py`, `resolve_editor/composition.py`,
`resolve_editor/model_types.py`, `tests/test_editor_ui_helpers.py`,
`.github/aidd-config.yml`
**Dependencies:** PHASE-006 focus/triplicate model; existing timeline
selection and wheel routing; GTK event behavior on the target workstation
**Risks:** ambiguous control ownership, device-specific scroll direction,
accessibility, and accidental timeline movement can make direct controls
unpredictable
**Affected surfaces:** focus-control layout, pointer/scroll routing, feedback,
keyboard parity, triplicate controls, and interaction tests
**Evidence path:** `evidence/phase-008-focus-controls.md`
**Path history:** `tickets/open/TICKET-065-define-direct-focus-modification-interactions.md`
-> `tickets/closed/TICKET-065-define-direct-focus-modification-interactions.md`
**Protected behaviors:** ordinary timeline scroll, click/drag seeking,
selection, split, keyboard controls, and current focus semantics

## Outcome

The editor has an approved interaction contract for direct zoom and X/Y focus
adjustments, including the boundary between focus controls and timeline
navigation.

## Scope

- Define the visible focus-control targets and their hit areas.
- Define scroll direction, increment, feedback, reset behavior, and
  accessibility/keyboard equivalents for zoom and offsets.
- Define that scrolling outside the focus-control area moves the timeline
  cursor using existing semantics.
- Define how the contract applies to normal and triplicate segments.

## Explicit non-goals

- Implementing the controls in this ticket.
- Adding keyframes or new visual effects.
- Changing the project schema or transform math before the contract is
  reviewed.

## Observable requirements

- Given a pointer location, the contract should unambiguously identify whether
  focus modification or timeline navigation owns the scroll.
- Given a zoom or offset adjustment, the contract should define visible
  feedback and valid-value behavior.
- Given a triplicate segment, the contract should preserve shared-group
  semantics without sharing unrelated segment identities.

## Definition of done

- A focused interaction contract covers zoom, X/Y, scroll, click, keyboard,
  feedback, invalid values, and triplicate behavior.
- The contract is implementable by TICKET-066 and testable by TICKET-068.
- Unresolved device or accessibility behavior is recorded as a decision gap.

## User-validation plan

- **Setup:** review the proposed control layout and interaction table.
- **Steps:** perform representative pointer and scroll actions conceptually
  or in a prototype and inspect ownership, feedback, and direction.
- **Expected result:** a user can predict how to adjust focus without repeated
  modal/button actions or losing timeline navigation.
- **Failure paths:** ambiguous hit areas or direction are returned for
  correction before implementation.
- **Cleanup:** remove any prototype-only UI.
- **Evidence response:** return the approved interaction table and open
  questions.
- **Pass criteria:** TICKET-066 has no unresolved interaction ownership.

## Closure

TICKET-065 was closed after the focus-control interaction contract and its
timeline ownership rules were captured in the focus evidence. The user's
target-workstation validation passed for the resulting interaction behavior.
