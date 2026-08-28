# Delivery Evidence: TICKET-019

- Phase: `PHASE-004` - Combining Mixed-Source Footage
- Feature: `FEAT-010` - Importing and Retaining Mixed-Source Project Identity
- Ticket: `TICKET-019` - Implement Mixed-Source Import, Probing, and Persistence
- Status: `verifying`
- Branch: `ticket/phase-004-mixed-source-footage`
- Evidence path: `evidence/phase-004-mixed-source-import.md`

## Evidence entries

### IMPLEMENTATION-001

- Requirement/flow: Import several local sources with complete metadata and
  preserve source identity across save/reopen.
- Observed: Schema 3 projects contain two ordered source entries with distinct
  stable IDs, dimensions, orientation, frame rate, codec, duration, and audio
  presence. Source-level settings are keyed by source ID.
- Evidence: `framestudio/model.py`, `framestudio/media.py`,
  `framestudio/operations.py`, and
  `tests/test_editor_mixed_source.py`.
- Status: `passed`

### CONTRACT-001

- Command: `make contract PYTHON=.venv/bin/python`
- Observed: 23 CLI contract tests passed, including mixed import, inspection,
  persistence, redaction, relinking, and structured failure coverage.
- Status: `passed`

### REALMEDIA-001

- Flow: Import disposable 320x180/10 FPS landscape media and 180x320/15 FPS
  portrait media, then inspect and reopen the saved project.
- Observed: Both sources reopened with their original metadata and stable
  identities. Source file size and modification timestamps remained unchanged.
- Status: `passed`

### USER-001

- Required: Maintainer confirmation using at least two local videos and the
  source metadata/relinking workflow.
- Status: `pending`

### REMOTE-001

- Required: Provider-backed checks.
- Observed: No Git remote or upstream is configured.
- Status: `blocked`
