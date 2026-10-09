# TICKET-117 - Arrange Tracks by Dragging Blocks

**Ticket ID:** TICKET-117
**Parents:** OBJ-001, SCOPE-001, PHASE-010, FEAT-035
**Capability links:** CAP-002, CAP-003, CAP-013
**Status:** complete
**Approval:** execution/delegation authorized by the 2026-10-09 orchestration
request and CHG-014 autonomous authorization; dependencies and exact-profile
automatic validation remain required
**Requirements:** DISC-010 / REQ-010-04
**Dependencies:** TICKET-116
**Affected surfaces:** timeline rows/geometry, GTK drag/select/track controls,
active-track imports and tests
**Risks:** screen/time mapping errors, wrong drop track, stale selection
**Evidence path:** `evidence/ticket-117-track-drag-controls.md`
**Path history:** created in `tickets/open/` on 2026-10-09
Moved unchanged-ID to `tickets/closed/` on 2026-10-09 (UTC) after source provider PASS.
**Completion evidence:** `evidence/ticket-125-phase010-functionality.md`,
source `981e5e2a`, CI `38004558177`, exact validator turns 18/19.

## Scope and acceptance

- Given1..4 tracks, should show ordered editable rows and one global playhead.
  Drag within/between rows should set absolute timing through116, visibly
  snapping forward on collisions and leaving existing blocks unchanged.
- Given add/remove/active-track controls, should keep empty tracks explicit,
  import into active track and retain selection/modifications. Invalid drops,
  a fifth track and populated-track removal should show clear errors.

Preserve established zoom/scroll seek, multi-selection, split and text entry.
No renderer/audio implementation or duplicated domain placement logic.

## Automated functionality charter

Implemented functionality selector:
`python3 -m unittest tests.test_editor_track_drag_functionality`

Initial exact-profile review blocked conversion, ghost placement, selection,
wheel seeking and pointer acceptance. Corrected native functionality now
passes without skips. The final bounded exact-profile review passed and
released T111/T120; configured duplication has zero introduced findings.
Aggregate quality and final delivery remain pending. Evidence retains the
historical failures and their corrections.

Drive a real GTK timeline's pointer press/motion/drop at multiple zoom levels.
Create/remove rows, drag through collision chains/free gaps and cancel an
invalid drop. Assert visible placement, persisted starts/IDs/modifications,
single playhead, stable other rows and appropriate error feedback.

## Automatic functionality validation and completion

Execute this charter as the agent under CHG-014. Record `automaticValidation`
using Rubber Duck GPT-5.6 Luna high `all-validation`, never `userValidation`.

Setup:1..4 tracks, import into selected track, drag within/across rows.
Expected: free timing, collision snapping, single playhead, no state loss.
Failure: overlap, drift, unexpected imports or silent track deletion.
Cleanup: discard fixture edits. Record agent PASS/FAIL/BLOCKED with optional
window-only screenshots. Require baseline/readiness and terminal automated/
technical/automatic-validation/review/delivery checks before completion.

## Parallel ownership

Can overlap118 CLI-only work if common model interface is frozen.
Reserve shared app/timeline callbacks against109/111/114/120.

The exact-profile116 interface review released isolated GUI implementation.
Before120, absolute projects use an explicit editing-only presentation with
playback unavailable, not the legacy composed decoder. The existing absolute
playback guard remains;120 owns verified synchronized preview integration.
