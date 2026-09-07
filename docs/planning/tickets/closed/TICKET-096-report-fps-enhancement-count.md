# TICKET-096 - Report FPS-Enhancement Count

**Ticket ID:** TICKET-096
**Title:** Show how many source videos require FPS enhancement
**Status:** complete
**Parent feature:** FEAT-029
**Parent phase:** PHASE-008
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Capability links:** CAP-005, CAP-012
**Owner:** repository implementation in the active worktree
**Approval:** Explicitly authorized by the user's request to show the number
  of videos that will receive FPS enhancement in the export window
**Last updated:** 2026-09-07
**Dependencies:** existing `FrameRatePolicy`, `ResolvedFrameRatePolicy`,
asynchronous export-panel preparation, and TICKET-091 upscale-count display
**Affected surfaces:** `framestudio/export_panel.py`,
`framestudio/app_export.py`, FPS policy tests, export-panel tests, and GTK
export interaction evidence
**Risks:** the panel could report segments instead of unique sources, show a
stale count, or delay the count until expensive export preparation finishes
**Evidence path:** `evidence/ticket-096-report-fps-enhancement-count.md`

## Observable requirements

- Given FPS enhancement is enabled, the export window should show the number
  of unique eligible source videos that require FPS enhancement.
- Given FPS enhancement is disabled, the export window should show zero videos
  to FPS enhance and preserve the existing non-enhanced route.
- Given mixed source frame rates, the count should match
  `ResolvedFrameRatePolicy.eligible_source_ids`, not timeline segment count.
- Given asynchronous export planning, the count should be available without
  making the GTK main loop wait for the full plan.

## Scope

- Add a source-level FPS count to export-panel state and summary rows.
- Match the existing upscale-count wording and asynchronous preparation
  behavior.
- Add enabled, disabled, mixed-eligibility, and zero-eligible regressions.

## Non-goals

- Changing FPS target selection, eligibility thresholds, interpolation, or
  export routing.
- Replacing the established source-level policy.

## Validation

- Focused FPS-policy and export-panel tests.
- Existing repository unit, compile, contract, smoke, and quality checks.
- Target-workstation export-window interaction or an explicit environment
  limitation with evidence.

## Definition of done

- Users can see the source-level number of videos to FPS enhance before
  starting export.
- Existing FPS routing and output behavior remain unchanged and covered.

**Path history:** Created in `docs/planning/tickets/open/` on 2026-09-05.
Moved to `docs/planning/tickets/closed/` on 2026-09-07 after user
validation.
