# TICKET-041 - Define Triplicate Group and Layout Policy

**Ticket ID:** TICKET-041
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Phase:** PHASE-006
**Feature:** FEAT-018
**Capability links:** CAP-010, CAP-012
**Status:** complete
**Closure:** user-approved on 2026-08-23 after PHASE-006 implementation,
automated verification, shared target-workstation validation, review, and
local delivery evidence; remote checks remain unavailable and are recorded as
an accepted warning.
**Horizon:** future
**Priority:** 4
**Owner:** repository planning; maintainer identity is not recorded
**Approval:** user-authorized on 2026-08-22 to create and implement the
PHASE-006 ticket set; the completed outcome was confirmed by the user on
2026-08-23
**Provider:** auto; base and target branches are not configured in
`.github/aidd-config.yml`
**Source paths:** `vision.md`, `docs/specs/project-scope.md`,
`docs/specs/future-product-direction.md`,
`docs/planning/phases/open/PHASE-006-focusing-and-composing-important-action.md`,
`docs/planning/features/open/FEAT-018-creating-linked-triplicate-compositions.md`,
`docs/planning/tickets/open/TICKET-038-define-segment-visual-modification-contract.md`,
`.github/aidd-config.yml`
**Dependencies:** TICKET-038; fixed 1920x1080 canvas and stable segment
identity and selection semantics
**Risks:** unspecified background treatment can distort action, group identity
can become ambiguous, and automatic selection can hide independent state
**Affected surfaces:** linked-group model, layout policy, selection contract,
GUI controls, preview/render boundaries, tests, documentation, and evidence
**Evidence path:** `evidence/phase-006-triplicate-policy.md`
**Last updated:** 2026-08-23
**Path history:** `tickets/open/TICKET-041-define-triplicate-group-and-layout-policy.md`
-> `tickets/closed/TICKET-041-define-triplicate-group-and-layout-policy.md`

## Outcome

PHASE-006 has an approved deterministic contract for triplicate groups,
center/left/right placement, shared focus controls, automatic linking, and
background treatment.

## Scope

- Define the relationship between one source segment and its three linked
  instances.
- Define group identity, instance roles, defaults, ordering, and selection
  behavior.
- Define placement, scale, crop/contain behavior, spacing, background
  treatment, and out-of-bounds handling on the 1920x1080 canvas.
- Define shared X/Y/zoom controls and the boundary for per-instance
  overrides, if any.
- Define activation, disable/clean, split, copy/paste, delete/restore, and
  reorder semantics.

## Explicit non-goals

- Implementing the triplicate UI or renderer.
- Automatic subject detection or an irreversible focus decision.
- Arbitrary effects, keyframes, full compositing, or 60 FPS enhancement.

## Observable requirements

- Given a source segment with triplicate enabled, the contract should identify
  one group and exactly center, left, and right roles.
- Given shared X/Y/zoom values, the contract should define how all instances
  are updated.
- Given portrait and vertical-action landscape sources, the contract should
  define deterministic aspect-ratio and crop/placement behavior.
- Given a split or copy/paste, the contract should require a fresh linked
  group with cloned values rather than shared identity.
- Given clean or disable, the contract should define atomic group reset
  without changing source intervals.

## Commands and quality gates

- `make check`
- `make contract`
- `make quality PYTHON=.venv/bin/python`
- Review the policy with representative portrait and landscape fixtures.

## Functionality flows

- Trace activation, shared adjustment, clean, disable, split, and copy/paste.
- Review center/side placement for portrait and vertically focused landscape
  examples.
- Check all unsupported or out-of-bounds cases have explicit outcomes.

## User validation before closure

Review the group identity, center/left/right layout, aspect-ratio and
background policy, shared controls, automatic selection, and cloning rules.
Return `PASS`, `FAIL`, or `BLOCKED` with any required correction.

## Protected behavior

Existing segment identity, colors, ordering, selection, source-level audio
decisions, fixed 1920x1080 output, source preservation, and legacy scripts
remain unchanged.

## Definition of done

- Triplicate group and layout semantics are approved and documented.
- Portrait and vertical-action examples have observable expected outcomes.
- Downstream implementation tickets have no unresolved layout ambiguity.

## Closure

The triplicate group and layout policy is complete under the reviewed
PHASE-006 delivery checkpoint. Provider-side checks remain unavailable because
no remote or upstream is configured.
