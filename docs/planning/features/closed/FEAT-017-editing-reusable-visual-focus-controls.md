# FEAT-017 - Editing Reusable Visual Focus Controls

**Feature ID:** FEAT-017
**Parent links:** OBJ-001, SCOPE-001, PHASE-006
**Capability links:** CAP-009, CAP-012
**Status:** complete
**Closure:** user-approved on 2026-08-23 after TICKET-038 through TICKET-040
passed implementation, automated verification, shared target-workstation
validation, review, and local delivery gates; remote checks remain
unavailable and are recorded as an accepted warning.
**Horizon:** future
**Priority:** 1
**Owner:** repository planning; maintainer identity is not recorded
**Approval:** user-authorized on 2026-08-22 to break down PHASE-006 and
authorize ticket implementation; the completed outcome was confirmed by the
user on 2026-08-23
**Source paths:** `vision.md`, `docs/specs/project-scope.md`,
`docs/specs/future-product-direction.md`,
`docs/planning/phases/open/PHASE-006-focusing-and-composing-important-action.md`,
`docs/planning/features.md`, `.github/aidd-config.yml`
**Dependencies:** PHASE-005 complete; stable segment identity, block
selection, split inheritance, and copy/paste semantics
**Risks:** coordinate-space ambiguity, unexpected cropping, shared mutable
state between copied segments, and reset behavior changing source ranges
**Affected surfaces:** segment model, timeline selection, transform controls,
GUI actions, CLI operations, project persistence, tests, and evidence
**Evidence path:** `evidence/phase-006-visual-focus-controls.md`
**Planned tickets:** TICKET-038, TICKET-039, TICKET-040
**Last updated:** 2026-08-23
**Path history:** `features/open/FEAT-017-editing-reusable-visual-focus-controls.md`
-> `features/closed/FEAT-017-editing-reusable-visual-focus-controls.md`

## Outcome

The user can apply reusable zoom and X/Y focus adjustments to one or more
timeline segments, copy those adjustments between segments, and clean them
without changing source intervals or damaging segment identity.

## Scope

- Define a segment-owned visual modification bundle for zoom and X/Y offsets.
- Apply the bundle to one segment or an explicitly selected group.
- Copy and paste the bundle between existing segments without sharing
  mutable identity.
- Provide a visible **Clean modifications** action that restores defaults
  without changing source ranges, ordering, deletion state, or colors.
- Preserve the bundle when a segment moves and clone it when a segment is split
  or copied/pasted.
- Define aspect-ratio, coordinate-space, bounds, and out-of-range behavior
  against the fixed 1920x1080 project canvas.

## Explicit non-goals

- Triplicate layout authoring, which belongs to FEAT-018.
- Arbitrary effects, keyframes, transitions, color grading, or compositing.
- Automatic focus decisions that remove user control.
- Rendering or output-policy changes, which belong to FEAT-019.
- 60 FPS enhancement.

## Observable requirements

- Given an included segment, applying zoom or X/Y offsets should update only
  that segment's modification bundle.
- Given multiple selected segments, a shared modification action should apply
  the same values while keeping each segment identity independent.
- Given a copied modification bundle, the destination should receive equal
  values without sharing mutable state with the source segment.
- Given a segment with modifications, **Clean modifications** should restore
  defaults without changing its source interval, color, deletion state, or
  timeline position.
- Given a modified segment is moved, split, or copy/pasted, the resulting
  segment state should follow the approved inheritance rules.
- Given an offset or zoom outside the supported bounds, the editor should
  clamp it or report an explicit validation error according to the approved
  transform contract.

## Validation intent

- Verify transform invariants, selection behavior, clean/reset behavior, and
  independent copied state with focused model and UI tests.
- Exercise split, move, delete/restore, and copy/paste after modifications.
- Confirm source intervals, colors, deletion state, and project duration remain
  unchanged by visual-only operations.
- Record coordinate, aspect-ratio, and out-of-bounds decisions before
  implementation.

## Protected behavior

Existing source identity, atomic segment blocks, selection semantics, split
inheritance, color preservation, source-level audio decisions, fixed
1920x1080 output, source preservation, and safe export behavior remain
unchanged.

## Definition of done

- The transform bundle and coordinate policy are approved and documented.
- One- and multi-segment focus controls and clean/reset behavior are
  deterministic and independently testable.
- Move, split, copy, and paste preserve or clone modifications according to
  the approved identity rules.
- Automated and user-validation evidence covers visible behavior and
  persisted state without claiming triplicate or FPS support.

## Closure

TICKET-038 through TICKET-040 satisfy the reusable visual focus outcome under
the reviewed PHASE-006 delivery checkpoint. Provider-side checks remain
unavailable because no remote or upstream is configured.
