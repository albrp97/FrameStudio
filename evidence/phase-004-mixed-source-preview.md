# Delivery Evidence: TICKET-025

- Phase: `PHASE-004` - Combining Mixed-Source Footage
- Feature: `FEAT-012` - Previewing and Exporting Mixed-Source Edits
- Ticket: `TICKET-025` - Implement Composed Mixed-Source Preview
- Status: `verifying`
- Branch: `ticket/phase-004-mixed-source-footage`
- Evidence path: `evidence/phase-004-mixed-source-preview.md`

## Evidence entries

### IMPLEMENTATION-001

- Requirement/flow: Preview sequential mixed-source blocks with normalized
  dimensions, timing, seeking, and cancellation of stale requests.
- Observed: `FfmpegComposedPlaybackBackend` composes source streams using the
  output policy, maps the global timeline to source intervals, and returns a
  complete RGBA frame for the mixed fixture.
- Evidence: `resolve_editor/ffmpeg_playback.py`,
  `resolve_editor/app.py`, and `tests/test_editor_mixed_source.py`.
- Status: `passed`

### GUI-001

- Flow: The GTK editor opened the mixed project and displayed the composed
  preview while the timeline was stepped, split, deleted/restored, and pasted.
- Evidence: `evidence/screenshots/phase-004-mixed-before.png`,
  `evidence/screenshots/phase-004-mixed-split.png`, and
  `evidence/screenshots/phase-004-mixed-after.png`.
- Status: `passedWithConcerns`
- Concern: Maintainer confirmation of rapid drag and source-boundary behavior
  remains required.

### USER-001

- Required: Maintainer preview, seek, and drag confirmation across both source
  boundaries.
- Status: `pending`

### CANVAS-002

- Requirement/flow: Preview a non-1080p one-source project on the project
  canvas.
- Observed: The one-source GTK playback backend now scales and letterboxes
  decoded frames into the fixed 1920x1080 canvas, matching composed preview
  behavior.
- Evidence: `resolve_editor/app.py`,
  `resolve_editor/ffmpeg_playback.py`, and
  `tests/test_editor_ffmpeg_playback.py`.
- Status: `passed`

### CANVAS-USER-001

- Required: Maintainer confirmation that one-source preview framing is
  visually correct on the target workstation.
- Status: `pending`

### UI-KEY-BINDINGS-001

- Flow: Open a project and inspect the timeline toolbar, then activate
  **Key bindings**.
- Observed: Persistent shortcut text was removed from the timeline toolbar.
  The compact toolbar now exposes a **Key bindings** button, and the opened
  window lists keyboard, mouse, selection, timeline, and playback controls.
- Evidence:
  `evidence/screenshots/phase-004-key-bindings-closed.png` and
  `evidence/screenshots/phase-004-key-bindings-open.png`.
- Status: `passedWithConcerns`
- Concern: Maintainer confirmation of the preferred wording and layout remains
  required before closing the user-facing ticket.

### GUI-CANVAS-001

- Flow: Open a generated landscape-plus-portrait mixed project and seek from
  the landscape block into the portrait block.
- Observed: The preview displayed the portrait source centered on the fixed
  canvas with black side letterboxing while the timeline playhead advanced
  into the second source block.
- Evidence:
  `evidence/screenshots/phase-004-fixed-canvas.png` and
  `evidence/screenshots/phase-004-fixed-canvas-portrait.png`.
- Status: `passedWithConcerns`
- Concern: The target-workstation maintainer still needs to confirm the
  visual framing and selection feedback.
