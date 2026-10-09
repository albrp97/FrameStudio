# TICKET-109 - Show Only Selected Video Details

**Ticket ID:** TICKET-109
**Parents:** OBJ-001, SCOPE-001, PHASE-010, FEAT-032
**Capability links:** CAP-001
**Status:** complete
**Approval:** execution and isolated GPT-5.6 Luna max delegation authorized by
the 2026-10-09 orchestration request and CHG-014 autonomous authorization;
exact-profile automatic validation and delivery gates remain required
**Requirements:** DISC-010 / REQ-010-01
**Dependencies:** none in PHASE-010; existing source metadata/selection
**Affected surfaces:** `framestudio/app_ui.py`, `app_project.py`, selection
callbacks, GTK functionality tests
**Risks:** delayed callbacks replace selected metadata or hide genuine errors
**Evidence path:** `evidence/ticket-109-selected-video-details.md`
**Path history:** created in `tickets/open/` on 2026-10-09
Moved unchanged-ID to `tickets/closed/` on 2026-10-09 (UTC) after source provider PASS.
**Completion evidence:** `evidence/ticket-125-phase010-functionality.md`,
source `981e5e2a`, CI `38004558177`, exact validator turns 18/19.

## Scope and acceptance

- Given selected A then B, should display B's filename, original dimensions
  and FPS only, including focused selection within a multi-selection.
- Given no selection/missing metadata, should show a neutral/unavailable
  result. Delayed audio callbacks should not repopulate the strip with
  decisions; required errors should remain visible elsewhere.

Non-goals: changing audio analysis, probing, export policy, or source files.
Protected: background import responsiveness and required failure notifications.

## Automated functionality charter

Implemented executable functionality test:
`python3 -m unittest tests.test_phase010_functionality.Phase010FunctionalityTests.test_selected_video_details`

Use the production GTK application/window and real generated A/B media.
Select/deselect through production gesture/selection paths, complete a
deterministically injected delayed analysis result, and assert actual visible
labels, required diagnostics, persisted autosave and source hashes. Modifier
selection uses the production selection path because synthetic GI signals
cannot carry modifier-state events; physical modifier interaction remains
an explicitly documented automation limitation, not a human gate in automatic
mode. The test covers both acceptance outcomes; unit
format tests are extra. Aggregate evidence and final review are recorded in
the ticket evidence, not inferred from this description.

## Automatic functionality validation and completion

Setup: open two sources. Select each, multi-select, then clear selection.
Expected: only selected source details, no routine audio-decision list.
Failure: stale/wrong source, clutter, or missing genuine error.
Cleanup: close the test project. Record agent PASS/FAIL/BLOCKED and optional
window-only evidence. Before execution run readiness/baseline; before
completion require charter, applicable local checks, exact-profile
`automaticValidation` under CHG-014, review,
and delivery policy. The setup above is a reusable functionality charter;
execute it as the agent without awaiting human PASS. No readiness claim.

## Parallel ownership

Independent of TICKET-115 model/migration. Reserve `app_*` callbacks before
overlapping with TICKET-117/120; independence does not permit shared writes.
