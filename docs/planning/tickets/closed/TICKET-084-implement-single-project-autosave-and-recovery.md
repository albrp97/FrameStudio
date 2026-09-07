# TICKET-084 - Implement Single-Project Autosave and Recovery

**Ticket ID:** TICKET-084
**Title:** Implement single-project autosave and recovery
**Status:** complete
**Parent feature:** FEAT-029
**Parent phase:** PHASE-008
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Capability links:** CAP-004, CAP-012
**Owner:** repository implementation in the active worktree
**Approval:** Explicitly authorized by the 2026-08-28 user request; no
additional ticket approval is required before implementation
**Last updated:** 2026-09-07
**Dependencies:** TICKET-083 project/source lifecycle; versioned JSON
  persistence; atomic save helper; GTK project attachment and error surfaces
**Affected surfaces:** `framestudio/persistence.py`,
`framestudio/app_project.py`, `framestudio/app.py`, `framestudio/app_ui.py`,
`framestudio/app_timeline_actions.py`, persistence tests, README
**Risks:** autosave could overwrite a normal project path, capture transient
  invalid state, or relink changed source media without user awareness
**Evidence path:** `evidence/ticket-084-editor-autosave.md`

## Scope

- Store one autosave for the current project in the XDG application-state
  location, with an explicit fallback for environments without
  `XDG_STATE_HOME`.
- Refresh that autosave after project attachment, relevant edits, normal
  saves, and lifecycle changes without writing on every playback timer tick.
- Add explicit **Recover autosave** behavior that validates every source
  exists and matches its recorded filesystem fingerprint before attachment.
- Keep normal **Save project** behavior and the user-selected project path
  independent from the recovery copy.

## Non-goals

- Multiple autosave histories, cloud backup, silent startup recovery, or
  automatic source relinking.
- Changing the project schema or deleting original source media.

## Acceptance criteria

- Given an attached or edited project, the single autosave is atomically
  replaced with the current valid project state.
- Given a valid autosave, explicit recovery attaches it without changing
  `window.project_path` or overwriting a user-selected project file.
- Given a missing or changed source, recovery reports the failure and leaves
  the current project unchanged.
- Given ordinary playback polling, no unbounded stream of autosave writes is
  produced.
- Given a failed autosave write, the error is surfaced through the existing
  application error path rather than treated as a successful save.

## Verification

- Add focused round-trip, recovery-success, missing-source, changed-source,
  path-isolation, and failure-reporting tests.
- Exercise recovery and replacement with representative local media in the
  GTK application and record visible and persisted results.
- Run the existing test, compile, and configured quality commands that cover
  persistence and editor lifecycle behavior.

## Protected behavior

Normal project save/reopen, source-preservation guarantees, project version
compatibility, atomic persistence, and background import invalidation remain
unchanged.

## Path history

Created in `docs/planning/tickets/open/` on 2026-08-28.
Moved to `docs/planning/tickets/closed/` on 2026-09-07 after user
validation.
