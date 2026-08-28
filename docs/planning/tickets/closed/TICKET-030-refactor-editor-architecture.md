# TICKET-030 - Refactor Editor Architecture

**Ticket ID:** TICKET-030
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Phase:** PHASE-004A
**Feature:** FEAT-013
**Capability links:** CAP-012
**Status:** complete
**Closure:** user-approved on 2026-08-22 after successful implementation,
review, local quality gates, and user-facing validation; remote checks remain
unavailable and are recorded as an accepted warning.
**Path history:** `tickets/open/TICKET-030-refactor-editor-architecture.md`
-> `tickets/closed/TICKET-030-refactor-editor-architecture.md`
**Horizon:** prerequisite
**Priority:** 1
**Owner:** repository implementation in the active worktree
**Approval:** user-authorized on 2026-08-22 before implementation
**Provider:** auto; base and target branches are not configured in
`.github/aidd-config.yml`
**Source paths:** `docs/planning/reviews/CHG-003-editor-architecture-stabilization.md`,
`docs/planning/phases/open/PHASE-004A-stabilizing-editor-architecture.md`,
`docs/planning/features/open/FEAT-013-modular-editor-architecture.md`,
`framestudio/model.py`, `framestudio/export.py`,
`framestudio/app.py`, `framestudio/cli.py`,
`framestudio/timeline.py`, `framestudio/ffmpeg_playback.py`
**Dependencies:** `make check` baseline; PHASE-004 complete
**Risks:** circular imports, broken monkeypatch seams, changed GTK/FFmpeg
lifecycles, and behavior drift hidden by mechanical moves
**Affected surfaces:** editor package modules, tests, Makefile quality paths,
README architecture notes, and future phase readiness
**Evidence path:** `evidence/editor-architecture-refactor.md`
**Last updated:** 2026-08-22

## Outcome

The editor's oversized modules are replaced by focused implementation
boundaries and thin compatibility facades without changing the existing
editing, playback, persistence, CLI, export, or legacy-script behavior.

## Scope and implementation slices

1. Preserve the protected `make check` baseline and record the current module
   size and import/patch seams.
2. Extract model responsibilities while keeping `framestudio.model`
   imports stable.
3. Extract export and playback responsibilities while keeping
   `framestudio.export` and `framestudio.ffmpeg_playback` imports stable.
4. Extract timeline/UI and CLI responsibilities while keeping
   `framestudio.timeline`, `framestudio.app`, and `framestudio.cli`
   imports and command behavior stable.
5. Reformat changed files, update directly related documentation/configuration,
   and add focused compatibility coverage where needed.
6. Run final regression, contract, smoke, quality, and applicable static
   analysis checks; prepare the user-validation handoff.

## Observable acceptance criteria

- Given current tests or external callers import a public symbol from an
  established facade, the symbol remains available with the same behavior.
- Given current tests patch `framestudio.operations.probe_media`,
  `framestudio.operations.plan_export`, `framestudio.cli.probe_media`,
  `framestudio.cli.plan_project_export`, or
  `framestudio.cli.execute_export`, those seams remain effective.
- Given a segment is split, moved, copied, pasted, deleted, or persisted, its
  existing identity, color, modification, and source-safety behavior is
  unchanged.
- Given the GUI plays, pauses, seeks, selects, moves, or exports, existing
  state transitions and error handling remain unchanged.
- Given the CLI executes an existing command, its JSON contract and exit/error
  behavior remain unchanged.
- Given the architecture report is generated, focused implementation modules
  have one primary responsibility and remain within the agreed approximate
  600-line target unless a documented boundary exception exists.
- Given the configured local gates run, they pass without new refactor-related
  failures; unavailable remote checks are recorded as unavailable.

## Protected behavior

Existing scripts, command names, project schema versions, source relinking,
fixed 1920x1080 rendering, atomic segment-block movement/copy/paste,
split-inherited state and colors, selection semantics, Space playback,
persistence, source preservation, atomic export publication, and partial-output
safety remain protected.

## Validation and evidence

- Baseline: `make check` before edits.
- Focused tests after each logical extraction.
- Final: `make check`, `make contract`, `make smoke`, and
  `make quality PYTHON=.venv/bin/python`, plus configured static analysis
  commands when their tools are available.
- User-facing before/after validation with window-only screenshots, retained
  in the configured evidence path.

## Definition of done

- The refactor and directly related documentation/configuration are complete.
- The focused and full regression evidence is terminal.
- User validation is recorded.
- The ticket is moved to `complete` after the required approval; no push is
  implied by this ticket.
