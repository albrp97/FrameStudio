# Delivery Evidence: TICKET-027

- Phase: `PHASE-004` - Combining Mixed-Source Footage
- Feature: `FEAT-012` - Previewing and Exporting Mixed-Source Edits
- Ticket: `TICKET-027` - Verify Mixed-Source Round Trips and Source Preservation
- Status: `verifying`
- Branch: `ticket/phase-004-mixed-source-footage`
- Evidence path: `evidence/phase-004-mixed-source-round-trip.md`

## Evidence entries

### CLI-ROUNDTRIP-001

- Flow: Split a mixed block, delete a child, copy the deleted block, paste it
  at the beginning, move the pasted block, and reopen the project.
- Observed: The deleted source block and its pasted clone remained deleted;
  the pasted clone received a fresh identity; movement changed only order;
  reopen preserved schema 3, two sources, four blocks, and a three-second
  edited duration.
- Status: `passed`

### SOURCE-PRESERVATION-001

- Observed: The source fixture's size and modification timestamp were
  identical before and after the complete round trip and export.
- Status: `passed`

### GUI-001

- Observed: GTK mixed-source screenshots capture initial loading, split,
  deleted-block recovery state, and the final pasted-block timeline:
  `evidence/screenshots/phase-004-mixed-before.png`,
  `evidence/screenshots/phase-004-mixed-split.png`,
  `evidence/screenshots/phase-004-mixed-deleted.png`, and
  `evidence/screenshots/phase-004-mixed-after.png`.
- Status: `passedWithConcerns`
- Concern: Maintainer sign-off for the complete GUI/CLI parity workflow is
  still required.

### USER-001

- Required: Maintainer completion of the documented two-source GUI and CLI
  workflow and confirmation of any workstation-specific limitations.
- Status: `pending`

### REMOTE-001

- Required: Provider-backed checks and publication.
- Observed: No Git remote or upstream is configured.
- Status: `blocked`

### OUTPUT-POLICY-002

- Requirement/flow: Verify one-source and mixed-source exports use the fixed
  project canvas.
- Observed: Fresh one-source and mixed-source CLI exports reported exactly
  1920x1080 output metadata; source files remained unchanged.
- Evidence: `evidence/phase-004-mixed-source-export.md` entries
  `REALMEDIA-002` and `REALMEDIA-003`.
- Status: `passed`

### GUI-CANVAS-001

- Requirement/flow: Confirm the mixed-source preview and timeline remain
  usable when the playhead crosses from landscape into portrait media.
- Observed: The GTK editor displayed the fixed-canvas landscape and
  letterboxed portrait states, with the final output duration visible.
- Evidence:
  `evidence/screenshots/phase-004-fixed-canvas.png` and
  `evidence/screenshots/phase-004-fixed-canvas-portrait.png`.
- Status: `passedWithConcerns`
- Concern: Human validation and remote checks remain open gates.

### COLOR-ROUNDTRIP-001

- Requirement/flow: Preserve block display colors through copy/paste,
  movement, and save/reopen.
- Observed: The generated project persisted color slots for all blocks;
  movement and copy/paste retained the source block color, and model/project
  round-trip tests restored the same color slots.
- Evidence: `framestudio/model.py`, `framestudio/cli.py`,
  `tests/test_editor_mixed_source.py`,
  `evidence/screenshots/phase-004-colors-before.png`,
  `evidence/screenshots/phase-004-colors-moved.png`, and
  `evidence/screenshots/phase-004-colors-copied.png`.
- Status: `passedWithConcerns`
- Concern: Maintainer confirmation and configured remote checks remain open
  gates.

### COLOR-ROUNDTRIP-002

- Requirement/flow: Reconfirm color persistence and visual preservation after
  the final color-allocation adjustment.
- Observed: The full regression suite passed with persisted color fields,
  explicit color slots remained stable through model/project round trips, and
  refreshed GUI artifacts exercised movement and copy/paste preservation.
- Evidence: `framestudio/model.py`,
  `tests/test_editor_model.py`, `tests/test_editor_mixed_source.py`,
  `evidence/screenshots/phase-004-colors-before.png`,
  `evidence/screenshots/phase-004-colors-moved.png`, and
  `evidence/screenshots/phase-004-colors-copied.png`.
- Status: `passedWithConcerns`
- Concern: Maintainer confirmation and configured remote checks remain open
  gates.
