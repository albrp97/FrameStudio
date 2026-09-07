# TICKET-090 - Keep Export Planning Responsive

**Ticket ID:** TICKET-090
**Title:** Keep export planning responsive for reopened projects
**Status:** complete
**Parent feature:** FEAT-029
**Parent phase:** PHASE-008
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Capability links:** CAP-005, CAP-012
**Owner:** repository implementation in the active worktree
**Approval:** Explicitly authorized by the 2026-09-04 user request
**Last updated:** 2026-09-07
**Dependencies:** Existing export planning panel, backend validation, project
snapshot/export worker, and GTK main-loop contract
**Affected surfaces:** `framestudio/app_export.py`, export planning tests,
GTK export interaction
**Risks:** background planning could publish stale results, enable export
before validation completes, or update a closed panel
**Evidence path:** `evidence/ticket-090-keep-export-planning-responsive.md`

## Observable requirements

- Given a reopened project, clicking **Export video** should present the
  planning window promptly without blocking the GTK main loop on backend or
  estimate work.
- Given planning is still running, the panel should show an explicit preparing
  state and keep **Start export** disabled.
- Given a planning request becomes stale because the user changes an option or
  closes the panel, its result should not mutate the current panel.
- Given planning completes successfully, the panel should expose the validated
  destination and enable **Start export** only when the state is valid.
- Given planning fails, the panel should remain responsive and show the
  explicit failure instead of appearing to crash.

## Scope

- Move export-panel preparation and backend preflight off the GTK main thread.
- Serialize or supersede refresh requests with generation checks.
- Preserve existing export policy, destination validation, and worker export
  behavior.

## Non-goals

- Changing export codecs, quality policy, runtime selection, or cache behavior.
- Making the actual export synchronous or allowing export before planning
  completes.

## Validation

- Focused export-planning responsiveness and stale-result tests.
- Existing editor suite and compile/diff checks.
- Target-workstation export-button and reopened-project interaction with
  representative media.

## Definition of done

- Export planning presents immediately and remains interactive while work is
  prepared.
- Validated plans still produce the same export route and destination.
- User-visible GTK behavior is validated or an explicit environment limitation
  is recorded.

**Path history:** Created in `docs/planning/tickets/open/` on 2026-09-04.
Moved to `docs/planning/tickets/closed/` on 2026-09-07 after user
validation.
