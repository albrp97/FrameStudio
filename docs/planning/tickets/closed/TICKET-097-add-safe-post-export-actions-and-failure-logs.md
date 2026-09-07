# TICKET-097 - Add Safe Post-Export Actions and Failure Logs

**Ticket ID:** TICKET-097
**Title:** Offer explicit post-export sleep or shutdown with failure logging
**Status:** complete
**Parent feature:** FEAT-029
**Parent phase:** PHASE-008
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Capability links:** CAP-005, CAP-012
**Owner:** repository implementation in the active worktree
**Approval:** Explicitly authorized by the user's request to add no-action,
  sleep, and shutdown choices and preserve failure diagnostics
**Last updated:** 2026-09-07
**Dependencies:** existing asynchronous export worker, safe atomic delivery,
  export failure routing, project path persistence, and platform command
  discovery
**Affected surfaces:** `framestudio/app_export.py`,
`framestudio/export_panel.py`, export completion/error handling, system-action
helpers, export execution tests, and GTK/target-workstation evidence
**Risks:** an unintended shutdown could lose work, a failure log could expose
private media paths, or an unavailable system command could be silently
ignored
**Evidence path:** `evidence/ticket-097-add-safe-post-export-actions-and-failure-logs.md`

## Observable requirements

- Given a new export panel, post-export action should default to `Nothing`.
- Given an explicit `Sleep` or `Shutdown` selection and a successful export,
  the selected system action should be invoked only after verified publication.
- Given an explicit `Sleep` or `Shutdown` selection and a failed export, a
  failure log should be written beside the project file before the system
  action is attempted.
- Given no usable project path exists, failure logging should use a clear
  explicit fallback or report that the action is unavailable; it must not
  claim a log was written.
- Given the selected system command is unavailable or fails, the editor should
  surface the error and remain responsive rather than silently succeeding.
- Given the post-export helper is exercised by automated tests, dependency
  injection should resolve at call time so tests cannot issue real power
  commands.
- Given the default `Nothing` selection, no system action or failure log should
  be created solely because export completed.

## Scope

- Add an explicit post-export action control with `Nothing`, `Sleep`, and
  `Shutdown` options.
- Preserve the selection through asynchronous export completion.
- Write a concise failure log adjacent to the current project file before
  invoking sleep or shutdown after failure.
- Dispatch system actions through a small testable helper with command
  availability/error reporting and no GTK-main-loop blocking.
- Add success, failure, cancellation, missing-project-path, unavailable
  command, and default-no-action regressions.

## Non-goals

- Power-management policy beyond the explicit user selection.
- Automatic shutdown/sleep without an explicit selection.
- Logging credentials, full source metadata, or unnecessary private paths.
- Changing export verification, atomic publication, retry cache, or output
  naming semantics.

## Validation

- Focused export-panel, export-completion, and system-action tests.
- Existing repository unit, compile, contract, smoke, and quality checks.
- Target-workstation validation with `Nothing`; sleep/shutdown commands remain
  test-injected or explicitly recorded as unavailable unless deliberately
  selected by the user.

## Definition of done

- The safe default performs no post-export action.
- Explicit sleep/shutdown actions happen only after the correct export outcome
  and failure logs are persisted before failure actions.
- Errors remain visible and the editor stays responsive.

**Path history:** Created in `docs/planning/tickets/open/` on 2026-09-05.
Moved to `docs/planning/tickets/closed/` on 2026-09-07 after user
validation.
