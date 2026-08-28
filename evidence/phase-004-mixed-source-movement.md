# Delivery Evidence: TICKET-021

- Phase: `PHASE-004` - Combining Mixed-Source Footage
- Feature: `FEAT-011` - Arranging and Editing a Mixed-Source Timeline
- Ticket: `TICKET-021` - Implement Mixed-Source Placement and Move Operations
- Status: `verifying`
- Branch: `ticket/phase-004-mixed-source-footage`
- Evidence path: `evidence/phase-004-mixed-source-movement.md`

## Evidence entries

### IMPLEMENTATION-001

- Requirement/flow: Move one or more mixed-source blocks without changing
  source coverage, identity, deletion state, or owned state.
- Observed: Shared movement operations reorder complete blocks, reflow
  sequential timeline placement, recalculate duration, and return
  deterministic invalid-operation errors.
- Evidence: `framestudio/model.py`, `framestudio/operations.py`,
  `framestudio/app.py`, and `tests/test_editor_mixed_source.py`.
- Status: `passed`

### CONTRACT-001

- Command: `make contract PYTHON=.venv/bin/python`
- Observed: CLI movement and persistence coverage passed with redacted default
  output.
- Status: `passed`

### GUI-001

- Flow: Mixed GTK timeline loaded with source blocks and a final-duration
  display; the block-editing workflow was exercised alongside movement
  shortcuts.
- Evidence: `evidence/screenshots/phase-004-mixed-after.png`.
- Status: `passedWithConcerns`
- Concern: Maintainer confirmation of the complete visual ordering workflow is
  still required.

### USER-001

- Required: Maintainer confirmation of moving at least three disposable clips
  in both directions and after save/reopen.
- Status: `pending`

### COLOR-MOVEMENT-001

- Requirement/flow: Move a selected colored block across a neighboring block
  without changing the color assigned to either block.
- Steps: Open the generated mixed-source project, split the first block,
  capture the initial timeline, press `Shift+Right`, and capture the result.
- Observed: The first block's blue color moved from the left position to the
  middle position while the neighboring purple block moved left and retained
  its color.
- Evidence: `evidence/screenshots/phase-004-colors-before.png` and
  `evidence/screenshots/phase-004-colors-moved.png`.
- Status: `passedWithConcerns`
- Concern: Maintainer confirmation remains required.

### COLOR-MOVEMENT-002

- Requirement/flow: Reconfirm that the finalized color-allocation model does
  not change a block's display color when it moves.
- Steps: Open the color evidence project, capture the initial timeline, press
  `Shift+Right`, and capture the moved timeline with `grim`.
- Observed: The refreshed screenshots show the selected block retaining its
  color while its timeline position changes.
- Evidence: `evidence/screenshots/phase-004-colors-before.png` and
  `evidence/screenshots/phase-004-colors-moved.png`.
- Status: `passedWithConcerns`
- Concern: Maintainer confirmation remains required.
