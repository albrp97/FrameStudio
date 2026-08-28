# Delivery Evidence: TICKET-023

- Phase: `PHASE-004` - Combining Mixed-Source Footage
- Feature: `FEAT-011` - Arranging and Editing a Mixed-Source Timeline
- Ticket: `TICKET-023` - Expose Mixed-Source Timeline Operations Through the CLI
- Status: `verifying`
- Branch: `ticket/phase-004-mixed-source-footage`
- Evidence path: `evidence/phase-004-cli-timeline-parity.md`

## Evidence entries

### CONTRACT-001

- Command: `make contract PYTHON=.venv/bin/python`
- Observed: 23 tests passed for versioned mixed import, inspect, move, copy,
  paste, relink, split, deletion, persistence, redaction, and structured
  errors.
- Status: `passed`

### IMPLEMENTATION-001

- Observed: `framestudio/cli.py` exposes mixed import, inspection, movement,
  copying, pasting, relinking, split coordinates, and block state. GUI and CLI
  use shared operations for mutations.
- Status: `passed`

### ROUNDTRIP-001

- Flow: CLI delete, copy, paste, move, and reopen on a two-source fixture.
- Observed: The pasted block received a fresh ID, retained the copied deleted
  state, movement changed order, and reopen preserved schema 3, two sources,
  four blocks, and the three-second edited duration.
- Status: `passed`

### USER-001

- Required: Maintainer comparison of equivalent GUI and CLI operation
  sequences.
- Status: `pending`

### COLOR-CLI-001

- Requirement/flow: Expose persisted block colors in deterministic CLI
  inspection and mutation results.
- Command: `make contract PYTHON=.venv/bin/python`
- Expected: Mixed-source inspect, move, copy, paste, and persistence results
  retain each block's `color_index`.
- Observed: CLI payloads include integer `color_index` values, and the mixed
  CLI regression confirms colors remain aligned with the saved block order
  after movement and paste.
- Status: `passed`
