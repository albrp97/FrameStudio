# TICKET-040 - Preserve Visual Modifications Through Block Edits

**Ticket ID:** TICKET-040
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
**Priority:** 3
**Owner:** repository planning; maintainer identity is not recorded
**Approval:** user-authorized on 2026-08-22 to create and implement the
PHASE-006 ticket set; the completed outcome was confirmed by the user on
2026-08-23
**Provider:** auto; base and target branches are not configured in
`.github/aidd-config.yml`
**Source paths:** `docs/planning/tickets/open/TICKET-038-define-segment-visual-modification-contract.md`,
`docs/planning/tickets/open/TICKET-039-implement-segment-focus-controls.md`,
`docs/planning/features/open/FEAT-017-editing-reusable-visual-focus-controls.md`,
`docs/planning/phases/open/PHASE-006-focusing-and-composing-important-action.md`,
`resolve_editor/operations.py`, `resolve_editor/model_project.py`,
`.github/aidd-config.yml`
**Dependencies:** TICKET-038 and TICKET-039; existing atomic block
movement, split, delete/restore, selection, and copy/paste operations
**Risks:** copied state could share mutable references, split children could
lose focus values, and block movement could reset visual state
**Affected surfaces:** timeline operations, segment identity, modification
inheritance, selection, persistence-facing state, tests, and evidence
**Evidence path:** `evidence/phase-006-visual-focus-inheritance.md`
**Last updated:** 2026-08-23
**Path history:** `tickets/open/TICKET-040-preserve-visual-modifications-through-block-edits.md`
-> `tickets/closed/TICKET-040-preserve-visual-modifications-through-block-edits.md`

## Outcome

Segment visual modifications follow the approved identity rules through
movement, selection, split, delete/restore, and copy/paste operations.

## Scope

- Preserve a segment's modification bundle when its block moves or is
  reordered.
- Clone values, but not identity or mutable state, when a segment splits or
  is structurally copied/pasted.
- Copy a modification bundle to selected destination segments without
  changing source intervals or destination identities.
- Keep deleted and restored blocks' modification state explicit.
- Add invariant coverage for multi-selection and mixed-source blocks.

## Explicit non-goals

- Persisting schema migrations, CLI exposure, or final rendering.
- Triplicate linked-group lifecycle, which belongs to FEAT-018.
- New timeline ordering semantics or changes to segment colors.

## Observable requirements

- Given a modified block moved left or right, its values and identity should
  remain unchanged.
- Given a modified block split, both fresh children should receive equal
  values with independent identities.
- Given a modified block copied/pasted, the inserted block should retain the
  values but receive a fresh independent identity.
- Given a bundle copied to several selected destinations, each destination
  should receive equal values without shared mutable state.
- Given a modified block is deleted and restored, its approved modification
  state should remain recoverable.

## Commands and quality gates

- `python3 -m unittest discover -s tests`
- `make check`
- `make contract`
- `make quality PYTHON=.venv/bin/python`

## Functionality flows

- Modify, move, split, delete/restore, and copy/paste one source block.
- Repeat the flow across mixed-source blocks and a multi-selection.
- Mutate one copied bundle after insertion and confirm the original is
  unaffected.

## User validation before closure

Perform the movement, split, delete/restore, and copy/paste flows on modified
segments. Confirm values persist or clone as specified and colors, source
ranges, identities, and duration remain correct.

## Protected behavior

Existing atomic block semantics, colors, selection, source identity,
source-level audio decisions, fixed 1920x1080 output, source preservation, and
safe export behavior remain unchanged.

## Definition of done

- Inheritance and independence rules are implemented and tested.
- Existing block operations retain their behavior and colors.
- User-validation and regression evidence covers all required transitions.

## Closure

Visual modification inheritance through block edits is complete under the
reviewed PHASE-006 delivery checkpoint. Provider-side checks remain
unavailable because no remote or upstream is configured.
