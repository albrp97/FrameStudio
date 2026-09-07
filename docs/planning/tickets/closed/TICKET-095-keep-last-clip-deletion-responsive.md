# TICKET-095 - Keep Last-Clip Deletion Responsive

**Ticket ID:** TICKET-095
**Title:** Keep deleting the final timeline clip responsive and valid
**Status:** complete
**Parent feature:** FEAT-029
**Parent phase:** PHASE-008
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Capability links:** CAP-002, CAP-004, CAP-012
**Owner:** repository implementation in the active worktree
**Approval:** Explicitly authorized by the user's request to fix the freeze
  when deleting the last clip
**Last updated:** 2026-09-07
**Dependencies:** existing timeline validation, playback lifecycle, autosave,
and empty-edit policy
**Affected surfaces:** `framestudio/app_timeline_actions.py`,
`framestudio/app_helpers.py`, `framestudio/model_timeline.py`,
`framestudio/app_playback.py`, timeline/composition tests, and editor smoke
evidence
**Risks:** an invalid empty timeline could be persisted, a stale backend could
remain attached, or selection/control updates could recurse during deletion
**Evidence path:** `evidence/ticket-095-keep-last-clip-deletion-responsive.md`

## Observable requirements

- Given a project with one included timeline clip, deleting that clip should
  return control promptly without a long synchronous playback or persistence
  stall.
- Given the final clip is deleted, the project should remain in a valid
  editable state with an explicit empty timeline state rather than crashing or
  silently restoring the deleted clip.
- Given playback is active when the final clip is deleted, playback should
  stop or become idle cleanly and no stale frame/backend should continue
  driving the UI.
- Given autosave is enabled, the valid post-delete state should be persisted
  without blocking the GTK main loop on unnecessary media work.

## Scope

- Reproduce and isolate the final-clip deletion delay across timeline,
  playback, selection, and autosave paths.
- Apply the smallest safe lifecycle/state fix that preserves source media and
  valid project persistence.
- Add regression coverage for deletion timing/state, playback cleanup, and
  reopening the resulting project.

## Non-goals

- Changing normal multi-clip deletion semantics.
- Deleting or moving original source media.
- Redesigning timeline validation or autosave architecture.

## Validation

- Focused timeline, composition, persistence, and playback tests.
- Existing repository unit, compile, contract, smoke, and quality checks.
- Target-workstation editor interaction with the final clip selected and
  playback both idle and active.

## Definition of done

- Final-clip deletion is responsive and leaves a valid, recoverable project.
- Playback and UI state are cleaned up without stale callbacks or recursion.
- Source preservation and normal deletion behavior remain covered.

**Path history:** Created in `docs/planning/tickets/open/` on 2026-09-05.
Moved to `docs/planning/tickets/closed/` on 2026-09-07 after user
validation.
