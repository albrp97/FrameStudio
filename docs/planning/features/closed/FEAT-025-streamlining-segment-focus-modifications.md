# FEAT-025 - Streamlining Segment Focus Modifications

**Feature ID:** FEAT-025
**Parent links:** OBJ-001, SCOPE-001, PHASE-008
**Capability links:** CAP-003, CAP-009, CAP-010, CAP-012
**Status:** complete
**Closure:** previously closed on 2026-08-26 after the interaction contract,
scroll controls, zoom-dependent bounds, persistence/CLI parity, regressions,
and target-workstation user validation were accepted; reopened for TICKET-082
after the default-zoom triplicate offset correction request.
**Horizon:** future
**Priority:** 2
**Owner:** repository planning; maintainer identity is not recorded
**Approval:** user-authorized on 2026-08-26 to break down PHASE-008; ticket
execution remains separately gated by the configured approval policy
**Last updated:** 2026-08-28
**Source paths:** `docs/planning/phases/open/PHASE-008-optimizing-responsive-preview-and-media-strategy.md`,
`docs/specs/future-product-direction.md`, `framestudio/app_ui.py`,
`framestudio/app_timeline_actions.py`, `framestudio/composition.py`,
`framestudio/model_types.py`, `framestudio/operations.py`,
`tests/test_editor_composition.py`, `tests/test_editor_operations.py`,
`.github/aidd-config.yml`
**Dependencies:** PHASE-006 visual-modification and triplicate semantics;
timeline selection and pointer routing; versioned project persistence; CLI
focus operations
**Risks:** scroll events may be delivered differently by devices and GTK
versions; control hit areas may steal timeline navigation; high zoom can make
offset bounds or triplicate crops unreachable
**Affected surfaces:** focus controls, timeline event routing, preview
composition, model bounds, project persistence, CLI parity, and GUI tests
**Evidence path:** `evidence/phase-008-focus-controls.md`
**Planned tickets:** TICKET-065, TICKET-066, TICKET-067, TICKET-068, TICKET-082
**Path history:** `features/open/FEAT-025-streamlining-segment-focus-modifications.md`
-> `features/closed/FEAT-025-streamlining-segment-focus-modifications.md`
-> `features/open/FEAT-025-streamlining-segment-focus-modifications.md`
-> `features/closed/FEAT-025-streamlining-segment-focus-modifications.md`

## Outcome

The user can adjust a selected segment's zoom and X/Y focus directly from the
editor, while ordinary timeline scrolling still navigates the playhead and
high-zoom focus remains bounded and usable.

## Scope

- Define the focus-control interaction area and feedback.
- Use scroll input over the focus control to increase or decrease the
  applicable modification.
- Keep scroll input outside that area as timeline cursor navigation.
- Make X/Y offset bounds and coordinate mapping explicit for zoom 2x and 4x,
  including all four corners and relevant edges.
- Allow bounded horizontal source-region selection for triplicate segments at
  the default 1x zoom without changing the normal segment path.
- Preserve the same modification state through project persistence and
  deterministic CLI operations.

## Explicit non-goals

- Keyframed transforms, animated focus, or arbitrary effects.
- Replacing the existing triplicate group model.
- Sharing mutable modification state between unrelated segment identities.
- Changing output canvas or source media.

## Observable requirements

- Given a selected segment and focus-control pointer, scrolling should adjust
  only the intended zoom or offset value and refresh the preview.
- Given a pointer outside the focus-control area, scrolling should move the
  timeline cursor using the existing semantics.
- Given zoom 2x or 4x, valid offsets should reach each corner and relevant
  edge without exposing an invalid crop or making a reachable region
  inaccessible.
- Given an enabled triplicate segment at 1x zoom, horizontal X offsets should
  move the repeated source region left or right while Y remains centered.
- Given save/reopen or an equivalent CLI operation, the selected zoom and
  offsets should round-trip with the same bounded meaning.
- Given invalid or out-of-range input, the editor should report or clamp
  according to the approved contract without corrupting the last valid state.

## Validation and evidence

- Model tests for normalized bounds and zoom-dependent coordinate mapping.
- GTK interaction tests for focus-area scroll versus timeline scroll.
- Preview evidence at 2x and 4x for all corners and edges, including
  non-landscape and triplicate compositions where applicable.
- Default-zoom triplicate left/center/right crop evidence.
- Persistence and CLI parity evidence.

## Protected behaviors

Existing click, drag, wheel, keyboard, split, selection, triplicate, save,
reopen, export, and source-preservation behavior remains intact outside the
new focus-control interaction.

## Definition of done

- Direct focus adjustments work without repeated modal or button actions.
- Timeline scrolling remains available outside the focus-control area.
- Zoom 2x and 4x corner/edge navigation is tested and visually confirmed.
- Triplicate default-zoom horizontal offsets are tested and visually confirmed.
- Persisted and CLI representations match GUI behavior.

## Closure

FEAT-025 is complete. TICKET-082 completed the default-zoom triplicate
horizontal-offset correction, and the user confirmed the feature was
manually validated and requested closure of all tickets on 2026-08-28.
The existing 2x/4x coordinate contract, triplicate linkage, and documented
physical-gesture limitation remain protected.
