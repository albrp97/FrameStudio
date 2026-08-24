# FEAT-018 - Creating Linked Triplicate Compositions

**Feature ID:** FEAT-018
**Parent links:** OBJ-001, SCOPE-001, PHASE-006
**Capability links:** CAP-010, CAP-012
**Status:** complete
**Closure:** user-approved on 2026-08-23 after TICKET-041 through TICKET-043
passed implementation, automated and real-media verification, shared
target-workstation validation, review, and local delivery gates; remote checks
remain unavailable and are recorded as an accepted warning.
**Horizon:** future
**Priority:** 2
**Owner:** repository planning; maintainer identity is not recorded
**Approval:** user-authorized on 2026-08-22 to break down PHASE-006 and
authorize ticket implementation; the completed outcome was confirmed by the
user on 2026-08-23
**Source paths:** `vision.md`, `docs/specs/project-scope.md`,
`docs/specs/future-product-direction.md`,
`docs/planning/phases/open/PHASE-006-focusing-and-composing-important-action.md`,
`docs/planning/features.md`, `.github/aidd-config.yml`
**Dependencies:** FEAT-017 transform bundle; stable segment identity,
selection, split inheritance, and mixed-source timing
**Risks:** linked-group identity can drift during edits, background treatment
can crop or distort action, and automatic linking can obscure independent
segment state
**Affected surfaces:** composition model, linked-group lifecycle, GUI
selection, transform controls, preview composition, project persistence,
tests, and evidence
**Evidence path:** `evidence/phase-006-triplicate-composition.md`
**Planned tickets:** TICKET-041, TICKET-042, TICKET-043
**Last updated:** 2026-08-23
**Path history:** `features/open/FEAT-018-creating-linked-triplicate-compositions.md`
-> `features/closed/FEAT-018-creating-linked-triplicate-compositions.md`

## Outcome

The user can activate a triplicate mode for portrait or vertically focused
action, see one linked center instance and two side instances, and adjust the
linked copies through shared focus controls without losing independent segment
identity.

## Scope

- Define a triplicate group identity and its relationship to one source
  segment.
- Create center, left, and right instances with an explicit deterministic
  layout and background-treatment policy.
- Automatically select or link the three instances when triplicate mode is
  enabled.
- Apply shared X/Y/zoom controls to the linked group while retaining
  inspectable group state.
- Create independent linked groups when a triplicate segment is split or
  copied/pasted.
- Clean an active triplicate group atomically without changing source
  intervals or timeline ordering.
- Support both portrait inputs and landscape inputs whose important action is
  concentrated in a vertical region.

## Explicit non-goals

- Automatic subject detection or focus decisions that replace the user.
- Arbitrary multi-track compositing, keyframes, transitions, blur, grading, or
  professional effects beyond the approved layout policy.
- Project persistence, CLI parity, final export routing, and output
  verification, which belong to FEAT-019.
- 60 FPS enhancement.

## Observable requirements

- Given a supported segment, enabling triplicate mode should create one
  center and two side instances with one inspectable linked-group identity.
- Given a linked group, shared X/Y/zoom changes should update all three
  instances consistently.
- Given triplicate mode is enabled, the editor should select or visibly link
  the three instances according to the approved interaction contract.
- Given a triplicate segment is split or copied/pasted, the new segment should
  receive a fresh independent linked group with cloned values.
- Given a linked group is cleaned, all three instances should return to their
  defaults atomically without changing source intervals.
- Given portrait or vertically focused landscape media, the layout should
  preserve the approved aspect-ratio and crop/placement behavior.

## Validation intent

- Verify linked-group invariants, shared controls, automatic selection, and
  atomic cleanup with model and UI tests.
- Exercise split, move, delete/restore, and copy/paste on triplicate segments.
- Render disposable portrait and landscape vertical-action fixtures to review
  placement, crop, and focus behavior.
- Record the approved background treatment and any explicit unsupported
  bounds before implementation.

## Protected behavior

Existing segment identity, colors, selection semantics, source-level audio
decisions, fixed 1920x1080 canvas, source preservation, project safety, and
legacy helper workflows remain unchanged.

## Definition of done

- Linked-group and layout semantics are approved and documented.
- Triplicate activation, shared controls, cloning, and atomic cleaning are
  deterministic and independently testable.
- Portrait and vertically focused landscape examples have visual evidence.
- The feature exposes state for FEAT-019 without claiming final delivery
  readiness until persistence, CLI, and render verification are complete.

## Closure

TICKET-041 through TICKET-043 satisfy the linked triplicate outcome under the
reviewed PHASE-006 delivery checkpoint. Provider-side checks remain
unavailable because no remote or upstream is configured.
