# Delivery Evidence: TICKET-022

- Phase: `PHASE-004` - Combining Mixed-Source Footage
- Feature: `FEAT-011` - Arranging and Editing a Mixed-Source Timeline
- Ticket: `TICKET-022` - Extend Segment Editing and Multi-Selection Across Sources
- Status: `verifying`
- Branch: `ticket/phase-004-mixed-source-footage`
- Evidence path: `evidence/phase-004-multi-selection-editing.md`

## Evidence entries

### IMPLEMENTATION-001

- Requirement/flow: Apply split, delete/restore, movement, copy/paste, and
  selection semantics to mixed-source blocks.
- Observed: Timeline selection supports additive Ctrl-click selection;
  Delete toggles all selected blocks; Shift+Left/Right moves selected blocks;
  Ctrl+C/Ctrl+V copies and pastes fresh independent blocks; split children
  inherit state and deletion status.
- Evidence: `framestudio/timeline.py`, `framestudio/app.py`,
  `framestudio/model.py`, and `tests/test_editor_timeline.py`.
- Status: `passed`

### GUI-001

- Flow: The GTK workflow showed split children, a deleted hatched block with
  reduced final duration, restoration, and a pasted block with increased final
  duration.
- Evidence: `evidence/screenshots/phase-004-mixed-split.png`,
  `evidence/screenshots/phase-004-mixed-deleted.png`, and
  `evidence/screenshots/phase-004-mixed-after.png`.
- Status: `passedWithConcerns`
- Concern: Maintainer confirmation of Ctrl-click multi-selection across
  sources remains required.

### CONTRACT-001

- Command: `make contract PYTHON=.venv/bin/python`
- Observed: Mixed block edit, fresh identity, deletion, and persistence
  contract tests passed.
- Status: `passed`

### USER-001

- Required: Maintainer confirmation that only selected blocks change in the
  complete cross-source workflow.
- Status: `pending`

### COLOR-RED-001

- Requirement/flow: Establish failing regression coverage for stable block
  colors across split, movement, copy/paste, persistence, and timeline
  geometry.
- Command: `.venv/bin/python -m unittest
  tests.test_editor_model.EditorModelTests.test_split_assigns_distinct_fresh_colors_to_children
  tests.test_editor_mixed_source.MixedSourceModelTests.test_move_and_copy_paste_preserve_block_colors`
- Expected: The new tests fail before implementation because the model and
  timeline do not yet expose persisted color identity.
- Observed: Both tests failed with the expected missing `color_index` attribute
  and constructor argument errors.
- Status: `passed`

### COLOR-IMPLEMENTATION-001

- Requirement/flow: Preserve block display colors through split,
  delete/restore, movement, copy/paste, persistence, and timeline layout.
- Observed: `Segment` now stores and validates a persisted color slot;
  movement/reflow, cloning, deletion, and project serialization preserve it;
  split children receive distinct fresh slots; timeline geometry and drawing
  use the stored slot instead of the positional index.
- Evidence: `framestudio/model.py`, `framestudio/timeline.py`,
  `framestudio/cli.py`, and the color regression tests.
- Status: `passed`

### COLOR-REGRESSION-001

- Command: `.venv/bin/python -m unittest tests.test_editor_model
  tests.test_editor_mixed_source tests.test_editor_timeline`
- Expected: Model, mixed-source, and timeline behavior remains green with
  stable color assertions.
- Observed: 34 tests passed.
- Status: `passed`

### COLOR-GUI-001

- Flow: Open a mixed-source project with three colored blocks, move the
  selected first block right, then copy/paste the selected block at the
  playhead.
- Expected: The moved color follows its block and the pasted block matches the
  copied block's color.
- Observed: The timeline changed from blue/purple/green to
  purple/blue/green after movement, then to blue/purple/blue/green after
  copy/paste.
- Evidence: `evidence/screenshots/phase-004-colors-before.png`,
  `evidence/screenshots/phase-004-colors-moved.png`, and
  `evidence/screenshots/phase-004-colors-copied.png`.
- Status: `passedWithConcerns`
- Concern: Maintainer confirmation of the complete visual workflow remains
  required.

### QUALITY-001

- Commands: `make quality PYTHON=.venv/bin/python` and
  `make smoke PYTHON=.venv/bin/python`
- Expected: Full regression, compilation, diff, formatting, lint, type,
  complexity, duplication, dependency, security, churn, and generated-media
  smoke gates pass.
- Observed: 143 tests passed; all configured quality checks and the generated
  media smoke flow completed successfully. Reports were written under
  `evidence/static-analysis/`.
- Status: `passed`
- Accepted warning: GTK emitted the existing
  `GLib.unix_signal_add_full` deprecation warning during the GUI test path.

### COLOR-ALLOCATION-002

- Requirement/flow: Assign deterministic colors to standalone segments while
  normalizing new timeline blocks to sequential free color slots.
- Observed: Direct segments now expose a stable persisted color index;
  timelines preserve explicit persisted slots and assign missing slots without
  allowing identity-derived defaults to duplicate adjacent new colors.
- Evidence: `framestudio/model.py` and
  `tests/test_editor_model.py::EditorModelTests.test_new_timeline_blocks_receive_stable_sequential_colors`.
- Status: `passed`

### COLOR-GUI-002

- Flow: Re-run the color movement and copy/paste screenshot workflow against
  the finalized color-allocation model.
- Steps: Open the color evidence project, capture the initial timeline, press
  `Shift+Right`, copy and paste the selected block with `Ctrl+C`/`Ctrl+V`, and
  capture each state with `grim`.
- Expected: Movement preserves the moved block's color and copy/paste preserves
  the copied block's color.
- Observed: The refreshed before, moved, and copied screenshots were captured
  successfully and differ as expected.
- Evidence: `evidence/screenshots/phase-004-colors-before.png`,
  `evidence/screenshots/phase-004-colors-moved.png`, and
  `evidence/screenshots/phase-004-colors-copied.png`.
- Status: `passedWithConcerns`
- Concern: Maintainer confirmation of the complete visual workflow remains
  required.

### QUALITY-002

- Commands: `make check PYTHON=.venv/bin/python`,
  `make contract PYTHON=.venv/bin/python`,
  `make smoke PYTHON=.venv/bin/python`, and
  `make quality PYTHON=.venv/bin/python`.
- Expected: Regression, compilation, contract, smoke, formatting, lint,
  typing, complexity, duplication, dependency, security, and churn gates
  pass after the final color-allocation adjustment.
- Observed: 144 tests passed; all configured quality and smoke checks passed;
  reports were written under `evidence/static-analysis/`.
- Status: `passed`
- Accepted warning: GTK emitted the existing
  `GLib.unix_signal_add_full` deprecation warning during the GUI test path.

### SCREENSHOT-FRAMING-001

- Requirement/flow: Capture UI evidence without unrelated monitors or desktop
  content.
- Command: `make screenshot LABEL=<name> PYTHON=.venv/bin/python` with the
  editor focused.
- Observed: The screenshot target resolves the active Hyprland window geometry
  with `hyprctl` and passes it to `grim -g`; the refreshed color evidence
  images are window-only at `3818x2103`.
- Evidence: `Makefile`, `README.md`,
  `evidence/screenshots/phase-004-colors-before.png`,
  `evidence/screenshots/phase-004-colors-moved.png`, and
  `evidence/screenshots/phase-004-colors-copied.png`.
- Status: `passed`

### SELECTION-PASTE-BASELINE-001

- Requirement/flow: Preserve existing timeline selection, block editing, and
  one-source/mixed-source copy-paste behavior before the requested interaction
  changes.
- Command: `.venv/bin/python -m unittest tests.test_editor_timeline
  tests.test_editor_model tests.test_editor_mixed_source
  tests.test_editor_cli_editing tests.test_editor_cli_mixed`
- Observed: 69 focused tests passed before adding the new regression cases.
- Status: `passed`

### SELECTION-PASTE-RED-001

- Requirement/flow: Use EVA-01 orange selection outlines, inclusive
  Shift-click ranges, reliable Ctrl-click toggling, and one-source copy-paste
  insertion after the selected block.
- Command: `.venv/bin/python -m unittest tests.test_editor_timeline
  tests.test_editor_model tests.test_editor_ui_helpers`
- Expected: The new tests fail before implementation.
- Observed: The expected failures exposed the missing orange color constant,
  missing one-source copy guard removal, and outdated copy-paste/key-binding
  text.
- Status: `passed`

### SELECTION-PASTE-IMPLEMENTATION-001

- Requirement/flow: Apply the requested selection and paste semantics across
  the timeline model, GTK UI, shared operations, CLI payload, and persisted
  project contract.
- Observed: The selected outline now uses `#F6C177` with a 3px border;
  Ctrl-click adds/removes blocks, Shift-click selects an inclusive range, and
  normal clicks replace the selection. Copy/paste now supports one-source
  timelines, inserts after the selected block in the UI, preserves state and
  color, assigns fresh identities, shifts later placements, and keeps source
  duration separate from expanded timeline duration.
- Evidence: `framestudio/model.py`, `framestudio/timeline.py`,
  `framestudio/operations.py`, `framestudio/app.py`,
  `framestudio/cli.py`, and the updated planning/README contracts.
- Status: `passed`

### SELECTION-PASTE-REGRESSION-001

- Requirement/flow: Verify selection behavior, one-source and mixed-source
  insertion, state/color inheritance, duration changes, export planning, CLI
  output, and persistence.
- Commands:
  - `.venv/bin/python -m unittest tests.test_editor_timeline
    tests.test_editor_model tests.test_editor_operations
    tests.test_editor_ui_helpers tests.test_editor_cli_editing
    tests.test_editor_cli_mixed tests.test_editor_mixed_source`
  - `.venv/bin/python -m unittest discover -s tests`
- Observed: The focused suite passed 75 tests and the complete suite passed
  155 tests.
- Status: `passed`

### SELECTION-PASTE-GATES-001

- Commands:
  - `make check PYTHON=.venv/bin/python`
  - `make contract PYTHON=.venv/bin/python`
  - `make smoke PYTHON=.venv/bin/python`
  - `make quality PYTHON=.venv/bin/python`
- Expected: Configured regression, compile, contract, smoke, formatting,
  lint, typing, complexity, duplication, dependency, security, and churn
  gates pass.
- Observed: All commands completed successfully; the final quality run
  included 155 passing tests and generated-media smoke validation.
- Status: `passed`

### SELECTION-PASTE-USER-001

- Flow: In the GTK editor, select blocks with Ctrl-click and Shift-click,
  confirm orange outlines and normal-click replacement, then copy a selected
  block with Ctrl+C and insert it with Ctrl+V.
- Expected: The inclusive selection is visible, the copied block appears
  immediately after the selected block, later blocks shift right, its state
  and color remain attached, and the timeline duration increases by its
  duration.
- Status: `pending`
- Blocker: Maintainer confirmation and comparable window-only screenshots are
  still required by the configured user-validation gate.

### SELECTION-PASTE-BASELINE-CORRECTION-001

- Supersedes: `SELECTION-PASTE-BASELINE-001`
- Observed: The protected pre-change focused baseline was the earlier
  `.venv/bin/python -m unittest tests.test_editor_timeline
  tests.test_editor_model tests.test_editor_mixed_source
  tests.test_editor_cli_editing tests.test_editor_cli_mixed` run with 45
  passing tests. The 69-test figure was not a valid baseline because the new
  regression tests had already been added and were intentionally failing.
- Status: `passed`

### SELECTION-PASTE-GUI-001

- Requirement/flow: Confirm the target workstation renders the requested
  selection styling, discontiguous multi-selection, inclusive range selection,
  and paste insertion result in the editor window.
- Observed: Window-only captures show the EVA-01 orange 3px outline, clips 2
  and 5 selected together, clips 2 through 5 selected as an inclusive range,
  and a pasted duplicate inserted immediately after the selected clip with
  the final output expanded from `00:10` to `00:12`.
- Evidence:
  - `evidence/screenshots/selection-control-multiple.png`
  - `evidence/screenshots/selection-shift-range.png`
  - `evidence/screenshots/selection-paste-before.png`
  - `evidence/screenshots/selection-paste-after.png`
- Status: `passedWithConcerns`
- Concern: These captures establish the rendered UI state; maintainer
  confirmation of the live Ctrl-click and Shift-click gestures is still
  required.

### SELECTION-GESTURE-USER-FAIL-001

- Flow: Maintainer attempted the Ctrl-click and Shift-click multi-selection
  workflow from `SELECTION-PASTE-USER-001`.
- Result: Maintainer reported that multiple selection with either Control or
  Shift was not working, while movement, split, and copy/paste worked.
- Status: `failed`
- Action: Reproduced the issue through the live GTK gesture path, added a
  regression test, and fixed the overlapping click/drag selection handling.

### SELECTION-GESTURE-BASELINE-001

- Requirement/flow: Preserve the existing editor timeline, model, operation,
  UI helper, CLI, mixed-source, and export behavior before the gesture fix.
- Command: `.venv/bin/python -m unittest tests.test_editor_timeline
  tests.test_editor_model tests.test_editor_operations
  tests.test_editor_ui_helpers`
- Observed: 56 tests passed. A live GTK trace showed each pointer action
  entering both the drag and click gesture handlers.
- Status: `passed`

### SELECTION-GESTURE-RED-001

- Requirement/flow: A pointer action that reaches both GTK gesture handlers
  must apply Ctrl-click or Shift-click selection exactly once.
- Test: `EditorTimelineTests.test_overlapping_drag_and_click_gestures_apply_modifier_selection_once`
- Expected: Ctrl-click keeps both the anchor and target selected, and
  Shift-click keeps the full inclusive range selected.
- Observed: Before the fix, Ctrl-click toggled the target back off and the
  focused test failed with only the anchor remaining selected.
- Status: `passed`

### SELECTION-GESTURE-FIX-001

- Requirement/flow: Prevent duplicate selection mutations while preserving
  click-to-select and drag-to-seek behavior.
- Observed: `GestureDrag.drag-begin` now seeks without updating selection;
  `GestureClick.pressed` remains the single selection owner. Ctrl-click now
  keeps discontiguous selections, Shift-click keeps inclusive ranges, and
  normal clicks replace the selection.
- Evidence: `framestudio/timeline.py` and
  `tests/test_editor_timeline.py`.
- Status: `passed`

### SELECTION-GESTURE-REGRESSION-001

- Requirement/flow: Verify the fixed selection path and all affected editor
  behavior.
- Commands:
  - `.venv/bin/python -m unittest tests.test_editor_timeline
    tests.test_editor_model tests.test_editor_operations
    tests.test_editor_ui_helpers tests.test_editor_cli_editing
    tests.test_editor_cli_mixed tests.test_editor_mixed_source
    tests.test_editor_export`
  - `.venv/bin/python -m unittest discover -s tests`
- Observed: The affected suite passed 88 tests and the complete suite passed
  156 tests.
- Status: `passed`

### SELECTION-GESTURE-LIVE-001

- Requirement/flow: Exercise the actual GTK window with pointer and modifier
  input rather than only calling the timeline methods directly.
- Steps:
  1. Click Clip 2.
  2. Ctrl-click Clip 5.
  3. Click Clip 2, then Shift-click Clip 5.
  4. Normal-click Clip 1.
  5. Copy and paste Clip 2 with Ctrl+C and Ctrl+V.
- Observed: Clips 2 and 5 remained selected after Ctrl-click; Clips 2
  through 5 remained selected after Shift-click; normal click replaced the
  selection; and paste inserted a same-color duplicate after Clip 2 while
  expanding the final output to `00:12`.
- Evidence:
  - `evidence/screenshots/selection-live-control-fixed.png`
  - `evidence/screenshots/selection-live-shift-fixed.png`
  - `evidence/screenshots/selection-live-normal-fixed.png`
  - `evidence/screenshots/selection-live-paste-fixed.png`
- Status: `passed`

### SELECTION-GESTURE-GATES-001

- Commands:
  - `make check PYTHON=.venv/bin/python`
  - `make contract PYTHON=.venv/bin/python`
  - `make smoke PYTHON=.venv/bin/python`
  - `make quality PYTHON=.venv/bin/python`
- Observed: All configured local gates completed successfully. The final
  quality run passed 156 tests, formatting, lint, typing, complexity,
  duplication, dependency, security, and churn checks.
- Status: `passed`

### SELECTION-GESTURE-USER-002

- Flow: Repeat the Ctrl-click, Shift-click, normal-click replacement, and
  Ctrl+C/Ctrl+V insertion workflow after `SELECTION-GESTURE-FIX-001`.
- Result: Maintainer returned `PASS` after confirming both discontiguous and
  inclusive multi-selection, normal-click replacement, and copy/paste
  insertion in the GTK editor.
- Status: `passed`
