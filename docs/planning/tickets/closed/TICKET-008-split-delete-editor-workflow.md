# TICKET-008 - Integrate Split and Delete into the Editor Workflow

**Ticket ID:** TICKET-008  
**Objective:** OBJ-001  
**Scope:** SCOPE-001  
**Phase:** PHASE-002  
**Feature:** FEAT-004  
**Capability links:** CAP-003, CAP-012  
**Status:** complete  
**Horizon:** first  
**Priority:** 2  
**Owner:** repository planning; implementer is not assigned  
**Approval:** user-approved on 2026-08-21 before execution  
**Provider:** auto; base and target branches are not configured in
`.github/aidd-config.yml`  
**Source paths:** `vision.md`, `docs/specs/project-scope.md`,
`docs/planning/phases.md`, `docs/planning/features.md`,
`docs/planning/tickets/closed/TICKET-007-segment-model-and-cut-semantics.md`,
`AGENTS.md`, `.github/aidd-config.yml`  
**Dependencies:** TICKET-007; existing GTK preview and timeline interaction  
**Risks:** unclear selected-segment state, stale preview position after edits,
  inaccessible controls, inconsistent duration display  
**Affected surfaces:** GTK editor interface, timeline interaction, status
  messages, playback seek integration, focused UI tests, manual smoke flow  
**Evidence path:** `evidence/split-delete-duration.md`

## Resolution

The GTK editor now exposes split-at-playhead, selected-segment delete, and
restore actions with ordered boundary/state rows and edited-duration updates.
Existing playback and transport behavior remains intact.

## Outcome

The user can split the open source at the playhead, select a segment, delete
or restore it, and immediately see the resulting edited duration in the
existing editor interface.

## Scope

- Add an understandable split action using the current playhead position.
- Show segment boundaries and the selected/deleted state in the timeline.
- Add delete and restore behavior for the selected segment.
- Keep preview, playhead, timeline, and edited-duration displays synchronized.
- Report invalid positions and unavailable selections without losing valid edit
  state.
- Preserve the current one-source workflow and existing keyboard/mouse
  transport behavior.

## Explicit non-goals

- Saving or reopening segment state; covered by TICKET-009.
- Export execution or output validation; covered by TICKET-010 and TICKET-011.
- Moving, copying, pasting, zooming, multiple sources, multiple tracks,
  triplicate composition, audio normalization, FPS enhancement, or CLI.
- Destructive source modification.

## Observable requirements

- Given an open source and an interior playhead position, activating split
  creates visible ordered segments at that position.
- Given a selected segment, delete removes it from the edited-duration
  calculation and updates the interface immediately.
- Given a deleted segment, restore returns it to the edited-duration
  calculation without changing source media.
- Given an invalid split position or missing selection, the interface reports
  the reason and keeps the previous valid edit.
- Given repeated split/delete/restore operations, the displayed final duration
  matches the segment model.

## Validation and evidence

- Add focused UI-helper/domain integration tests for split, delete, restore,
  selection, and duration display state.
- Run the existing GTK/manual smoke path with a local fixture.
- Run `python3 -m unittest discover -s tests`, `make check`, and
  `git diff --check`.
- Record the manual target-workstation flow and any accessibility or
  responsiveness concern in `evidence/split-delete-duration.md`.

## Quality gates

- TICKET-007's approved semantics and terminal tests are required.
- Local baseline, tests, compile/check targets, and user-facing manual flow
  must be evidenced.
- Remote checks remain required by configuration but unavailable locally.

## Protected behavior

Play/pause, Space-key transport capture, mouse-wheel seeking, source
selection, project save/reopen foundation, existing scripts, and source
preservation remain functional.

## Definition of done

- Split, selected-segment delete, and restore are available in the editor.
- Edited duration remains correct after repeated operations.
- Invalid interactions are explicit and state-safe.
- Focused and baseline tests plus the manual flow are recorded.
- Persistence and export are not claimed as complete by this ticket.

## Completion evidence

- Focused UI-helper tests: `python3 -m unittest tests.test_editor_ui_helpers`
- Full local gate: `make check` (67 tests passed, compilation and diff checks
  passed).
- GTK smoke: `make smoke`.
- Evidence record: `evidence/split-delete-duration.md`
- Accepted warning: target-workstation visual split/delete interaction still
  needs user confirmation; no screenshot artifact is available in this
  session.
