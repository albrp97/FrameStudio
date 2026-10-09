# FEAT-032 - Inspecting Only Selected Video Details

**Feature ID:** FEAT-032
**Parents:** OBJ-001, SCOPE-001, PHASE-010
**Capability links:** CAP-001
**Status:** complete
**Approval:** planning approved 2026-10-09; subsequent user request authorizes
implementation and isolated GPT-5.6 Luna max delegation. CHG-014 automatic closure gates
remain required.
**Last updated:** 2026-10-09
**Requirements:** DISC-010 / REQ-010-01
**Dependencies:** existing metadata and selection; no new feature prerequisite
**Ticket links:** TICKET-109
**Evidence:** `evidence/ticket-109-selected-video-details.md`
**Affected surfaces:** `framestudio/app_ui.py`, `app_project.py`,
selection callbacks and GUI tests
**Risks:** stale focused-source metadata; inadvertently hiding real failures
**Path history:** created in `features/open/` on 2026-10-09
Moved unchanged-ID to `features/closed/` on 2026-10-09 (UTC) after required tickets completed.
**Completion evidence:** `evidence/ticket-125-phase010-functionality.md`,
source `981e5e2a`, CI `38004558177`, exact validator turns 18/19.

## Outcome, scope, and acceptance

Given a focused segment, display only source filename, original dimensions,
and original FPS. Given a selection change, update immediately without waiting
for audio analysis. Given no selection or missing metadata, show a truthful
neutral/unavailable state. Routine source audio decisions no longer occupy
this information strip; actual failure/export-blocker reporting remains.

No underlying audio-analysis policy, media probing, or export rule changes.
This work can proceed independently of track-model work. Shared `app_*`
integration must be reserved if later track UI work is concurrent.

## Verification and closeout

TICKET-109's real GTK selection/label functionality test covers selection,
multi-selection focus, no selection, and delayed analysis completion. Require
exact-profile automatic validation and normal review/delivery gates before closure.
