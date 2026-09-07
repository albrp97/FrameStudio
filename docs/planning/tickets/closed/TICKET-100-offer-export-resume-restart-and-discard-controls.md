# TICKET-100 - Offer Export Resume, Restart, and Discard Controls

**Ticket ID:** TICKET-100
**Title:** Surface compatible export sessions after cancellation or project reload
**Status:** complete
**Horizon:** future
**Priority:** 1
**Parent feature:** FEAT-029
**Parent phase:** PHASE-008
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Capability links:** CAP-004, CAP-005, CAP-012
**Owner:** repository implementation in the active worktree
**Approval:** Planning authorized by the user's 2026-09-06 request; execution
remains subject to the configured approval and readiness gates.
**Change control:** CHG-010
**Last updated:** 2026-09-07
**Dependencies:** TICKET-098 session discovery; TICKET-099 resumable execution;
existing GTK export planning and project-reopen lifecycle; TICKET-090
responsive export planning; TICKET-097 post-export action safety
**Affected surfaces:** `framestudio/app_export.py`,
`framestudio/export_panel.py`, `framestudio/app_project.py`,
`framestudio/persistence.py`, GTK dialogs/status controls, export progress,
editor lifecycle tests, and target-workstation screenshots/evidence
**Risks:** a stale session could be offered for the wrong project, an
automatic resume could surprise the user, or discard could remove artifacts
needed by a still-running worker
**Evidence path:** `evidence/ticket-100-export-resume-controls.md`

## Objective

Let users intentionally continue a compatible export from the editor after
cancellation, failure, application restart, or project reopen without
silently starting work or losing valid recovery artifacts.

## Observable requirements

- Given a compatible resumable session exists for the current project and
  destination, opening the export flow should show the last completed stage,
  session age, and a primary **Resume export** action.
- Given the user chooses **Resume export**, the existing request should be
  handed to the resumable executor without rebuilding valid prior stages.
- Given the user chooses **Start over**, the session and its artifacts should
  be invalidated safely before a new export begins.
- Given the user chooses **Discard**, the session should be removed only when
  no worker owns it, and the current project and source media should remain
  untouched.
- Given a project is reopened, the editor should surface compatible pending
  export information without silently launching an export.
- Given a session no longer matches the project, destination, or source
  identity, the editor should explain why it cannot resume and preserve the
  normal fresh-export flow.
- Given no resumable session exists, the current export panel and start flow
  should remain unchanged.
- Given cancellation is requested from the progress UI, the worker should
  finish at a checkpoint boundary where possible and the panel should show
  that the session can be resumed later.

## Scope

- Add compatible-session discovery to export planning and project reopen.
- Add explicit Resume, Start over, and Discard controls with safe ownership
  and stale-session handling.
- Show checkpoint stage, reuse summary, cancellation status, and invalidation
  diagnostics without blocking the GTK main loop.
- Preserve the current export destination, policy, post-export action, and
  failure-log behavior when resuming or restarting.
- Add GTK lifecycle and state-machine tests plus target-workstation evidence.

## Non-goals

- Implementing stage checkpointing or artifact reuse; that is TICKET-099.
- Silent startup recovery or automatic export execution.
- Multiple simultaneous export sessions for one destination.
- Changing project schema, source relinking, output policy, or power-action
  defaults.

## Protected behaviors

Normal fresh export, project save/reopen, explicit autosave recovery, export
planning responsiveness, source preservation, cancellation, failure logging,
post-export actions, and the existing GTK main-loop ownership remain intact.

## Validation

- Focused export-panel and project-reopen tests for no session, compatible
  session, stale session, resume, restart, discard, and cancellation.
- GTK smoke validation proving the interface remains responsive while session
  discovery and preparation run off the main loop.
- Target-workstation flow: cancel a long export, close/reopen FrameStudio,
  reopen the project, and resume from the export button.
- Existing `make test`, `make compile`, `make contract`, `make smoke`, and
  applicable quality/static-analysis commands.

## User-validation plan

- **Setup:** use a saved project and a destination on local storage; start a
  long export and cancel it after several minutes.
- **Steps:** close FrameStudio, reopen the project, open **Export video**, and
  inspect the recovered-session choices; test Resume, then repeat with Start
  over and Discard on separate disposable destinations.
- **Expected visible result:** the panel clearly identifies the recovered
  stage and offers explicit choices; no export starts merely because the
  project was reopened.
- **Expected persisted/external result:** Resume continues the same request,
  Start over rebuilds from the beginning, Discard removes only the session
  artifacts, and the project/source remain unchanged.
- **Failure paths:** stale source, changed destination, corrupted session,
  active worker, missing project path, and unavailable session metadata are
  reported without freezing or silently starting work.
- **Evidence response:** return `PASS`, `FAIL`, `BLOCKED`, or approved
  `NOT APPLICABLE` with screenshots, selected action, visible stage, and
  output/source results.

## Definition of done

- Users can resume, restart, or discard a compatible export from the GTK
  export flow after cancellation, failure, and project reload.
- No automatic or ambiguous resume path remains.
- Focused UI/lifecycle and target-workstation evidence is terminal before
  closure.
- The ticket remains `proposed` until execution approval and its configured
  delivery gates are satisfied.

**Path history:** Created in `docs/planning/tickets/open/` on 2026-09-06.
Moved to `docs/planning/tickets/closed/` on 2026-09-07 after user
validation.
