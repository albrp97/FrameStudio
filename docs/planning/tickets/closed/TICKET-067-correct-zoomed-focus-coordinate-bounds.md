# TICKET-067 - Correct Zoomed Focus Coordinate Bounds

**Ticket ID:** TICKET-067
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Phase:** PHASE-008
**Feature:** FEAT-025
**Capability links:** CAP-009, CAP-010, CAP-012
**Status:** complete
**Closure:** closed on 2026-08-26 after the shared contain/pad coordinate
mapping, 2x/4x bounds, portrait/landscape coverage, and triplicate regression
evidence passed.
**Horizon:** future
**Priority:** 2
**Owner:** repository planning; maintainer identity is not recorded
**Approval:** user-authorized on 2026-08-26 for PHASE-008 planning; execution
requires the configured preimplementation and approval gates
**Last updated:** 2026-08-26
**Source paths:** `docs/planning/features/closed/FEAT-025-streamlining-segment-focus-modifications.md`,
`docs/planning/tickets/closed/TICKET-065-define-direct-focus-modification-interactions.md`,
`framestudio/composition.py`, `framestudio/model_types.py`,
`framestudio/model_timeline.py`, `framestudio/composition_render.py`,
`tests/test_editor_composition.py`, `tests/test_editor_model.py`,
`.github/aidd-config.yml`
**Dependencies:** TICKET-065 coordinate contract; fixed 1920x1080 canvas;
existing aspect-ratio and triplicate layout semantics
**Risks:** normalized versus pixel offsets, contain scaling, crop bounds, and
portrait/landscape differences can make corners appear reachable but render
incorrectly
**Affected surfaces:** transform math, composition preview/render, offset
validation, focus controls, and model tests
**Evidence path:** `evidence/phase-008-focus-controls.md`
**Path history:** `tickets/open/TICKET-067-correct-zoomed-focus-coordinate-bounds.md`
-> `tickets/closed/TICKET-067-correct-zoomed-focus-coordinate-bounds.md`
**Protected behaviors:** existing default transforms, triplicate layout,
fixed-canvas output, project persistence, and source safety

## Outcome

Zoom 2x and 4x focus controls reach all four corners and relevant edges of the
source view without invalid crops or unreachable regions.

## Scope

- Define and implement the zoom-dependent valid X/Y range.
- Test coordinate mapping for landscape, portrait, and contain-scaled inputs.
- Verify preview and render use the same mapping.
- Cover normal and linked triplicate instances where the shared focus applies.

## Explicit non-goals

- Adding arbitrary crop shapes or keyframed motion.
- Changing the fixed output canvas or triplicate design.
- Optimizing preview decoding; that belongs to FEAT-024.

## Observable requirements

- Given zoom 2x, each corner and edge target should be reachable through valid
  offset values.
- Given zoom 4x, each corner and edge target should remain reachable without
  exposing outside-canvas invalid state.
- Given the same transform, preview and export composition should use the
  same coordinate meaning.
- Given an out-of-range value, the model should clamp or report according to
  the approved contract and preserve a valid project.

## Definition of done

- Bounds and coordinate mapping are covered by model and composition tests.
- Visual evidence demonstrates all required 2x and 4x positions.
- Normal, portrait, and triplicate cases are included where applicable.
- No unrelated composition behavior changes.

## User-validation plan

- **Setup:** use representative landscape and portrait sources with a focused
  and a triplicate segment.
- **Steps:** set zoom to 2x and 4x, move to each corner and edge, save/reopen,
  and inspect the preview and exported composition where applicable.
- **Expected result:** every target is reachable and the crop remains valid.
- **Failure paths:** unreachable targets, inverted axes, clipping errors, or
  preview/export disagreement block the ticket.
- **Cleanup:** restore default focus values and remove temporary exports.
- **Evidence response:** return the position matrix and visual observations.
- **Pass criteria:** all required positions work at both zoom levels.

## Closure

TICKET-067 was closed after automated bounds and composition tests, generated
portrait/triplicate export evidence, and the user's target-workstation `PASS`
confirmed the required focus positions.
