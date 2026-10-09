# TICKET-111 - Wire Backspace Removal and Undo Controls

**Ticket ID:** TICKET-111
**Parents:** OBJ-001, SCOPE-001, PHASE-010, FEAT-033
**Capability links:** CAP-003, CAP-006, CAP-012
**Status:** verifying
**Approval:** execution/delegation authorized by the 2026-10-09 orchestration
request and CHG-014 autonomous authorization; dependencies and exact-profile
automatic validation remain required
**Requirements:** DISC-010 / REQ-010-02
**Dependencies:** TICKET-110, TICKET-117
**Affected surfaces:** timeline shortcuts, selection, Undo action,
deterministic CLI editing and functionality tests
**Risks:** intercepting text editing, stale selection, GUI/CLI divergence
**Evidence path:** `evidence/ticket-111-backspace-controls.md`
**Path history:** created in `tickets/open/` on 2026-10-09

## Scope and acceptance

- Given timeline focus, Backspace should remove selected blocks visibly,
  update duration and selection, and expose Undo. Delete should retain the
  excluded block and existing restore action.
- Given a text field, Backspace/Delete should edit text only. GUI and
  documented deterministic removal operations should share the domain
  behavior and explicit errors. Undo remains bounded in-process GUI/domain
  history, not a serialized receipt or cross-process CLI operation.

No shortcut redesign or general-purpose undo. Preserve source files,
selection semantics, normal keybindings and track-local ripple.

## Automated functionality charter

Dedicated charter integrated and executed against root:
`GDK_BACKEND=x11 python3 -m unittest tests.test_editor_removal_controls_functionality`

Drive real GTK keyboard events on a three-block timeline and a text entry.
Assert drawn blocks, duration, Delete/restore versus Backspace/Undo, preserved
transform/track state, no text-field deletion side effect. Exercise the
documented CLI removal route and compare saved projects and invalid errors.

## Automatic functionality validation and completion

Execute this charter as the agent under CHG-014. Record `automaticValidation`
using Rubber Duck GPT-5.6 Luna high `all-validation`, never `userValidation`.

Setup: blocks 1/2/3. Delete 2 and restore it, Backspace 2 then Undo.
Expected: Delete leaves excluded2; Backspace shows1/3 and shifts3; Undo
restores2. Backspace in filename/custom-FPS entries edits only text.
Cleanup: discard the edit. Record agent PASS/FAIL/BLOCKED with optional window-only
screenshot. Require baseline/readiness, charter, local checks, automatic
validation, review and delivery gates; no completion from planning.

## Parallel ownership

Can overlap isolated export/audio work, but reserve shared app/CLI wiring
against TICKET-114/118/120. Never repeat TICKET-110 domain logic.
