# TICKET-038 - Define Segment Visual Modification Contract

**Ticket ID:** TICKET-038
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
**Priority:** 1
**Owner:** repository planning; maintainer identity is not recorded
**Approval:** user-authorized on 2026-08-22 to create and implement the
PHASE-006 ticket set; the completed outcome was confirmed by the user on
2026-08-23
**Provider:** auto; base and target branches are not configured in
`.github/aidd-config.yml`
**Source paths:** `vision.md`, `docs/specs/project-scope.md`,
`docs/specs/future-product-direction.md`,
`docs/planning/phases/open/PHASE-006-focusing-and-composing-important-action.md`,
`docs/planning/features/open/FEAT-017-editing-reusable-visual-focus-controls.md`,
`.github/aidd-config.yml`
**Dependencies:** PHASE-005 complete; stable segment identity, selection,
split inheritance, block movement, and copy/paste semantics
**Risks:** an ambiguous coordinate space can create unexpected crop or
distortion, and undocumented bounds can make preview and export disagree
**Affected surfaces:** segment modification model, transform validation,
project contract, GUI/CLI boundaries, tests, documentation, and evidence
**Evidence path:** `evidence/phase-006-transform-policy.md`
**Last updated:** 2026-08-23
**Path history:** `tickets/open/TICKET-038-define-segment-visual-modification-contract.md`
-> `tickets/closed/TICKET-038-define-segment-visual-modification-contract.md`

## Outcome

PHASE-006 has an approved, deterministic contract for segment-owned zoom and
X/Y focus modifications on the fixed 1920x1080 project canvas.

## Scope

- Define the modification bundle fields, defaults, versioning, and ownership.
- Define coordinate space, units, anchor point, aspect-ratio behavior, and
  source-versus-canvas interpretation.
- Define supported zoom and offset bounds, clamping, and explicit errors.
- Define how visual state is copied, split, moved, deleted, restored, and
  cleaned without changing source intervals.
- Define the boundary between automatic defaults and future manual or
  keyframed behavior.

## Explicit non-goals

- Implementing GUI controls, CLI commands, or renderer changes.
- Triplicate group layout, which is specified in TICKET-041.
- Arbitrary effects, keyframes, color grading, or 60 FPS enhancement.

## Observable requirements

- Given a segment modification bundle, the contract should identify every
  field, default, valid range, and coordinate-space rule.
- Given an out-of-bounds zoom or offset, the contract should specify whether
  the value is clamped or rejected and the diagnostic shape.
- Given a segment operation, the contract should specify whether the bundle is
  preserved, cloned, or reset and whether segment identity remains distinct.
- Given a fixed 1920x1080 canvas and a mismatched source aspect ratio, the
  contract should define non-stretching transform behavior.

## Commands and quality gates

- `make check`
- `make contract`
- `make quality PYTHON=.venv/bin/python`
- Review the generated policy and requirements against PHASE-006.

## Functionality flows

- Review the transform contract with portrait and landscape examples.
- Exercise representative in-bounds and out-of-bounds values against the
  documented expected results.
- Trace split, move, copy/paste, delete/restore, and clean semantics.

## User validation before closure

Review the coordinate system, zoom and offset ranges, aspect-ratio behavior,
out-of-bounds handling, default bundle, and inheritance rules. Return
`PASS`, `FAIL`, or `BLOCKED` with any required policy correction.

## Protected behavior

Existing source identity, segment colors, ordering, selection, deletion,
source-level audio decisions, fixed 1920x1080 output, source preservation, and
safe export behavior remain unchanged.

## Definition of done

- The transform contract is documented with observable examples.
- All PHASE-006 transform entry decisions are resolved or explicitly blocked.
- Downstream implementation tickets can consume one unambiguous bundle and
  coordinate policy.
- The user-validation result and evidence are recorded.

## Closure

The segment visual modification contract is complete under the reviewed
PHASE-006 delivery checkpoint. Provider-side checks remain unavailable because
no remote or upstream is configured.
