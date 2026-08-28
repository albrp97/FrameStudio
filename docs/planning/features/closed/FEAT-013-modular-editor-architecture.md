# FEAT-013 - Modular Editor Architecture

**Feature ID:** FEAT-013
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Phase:** PHASE-004A
**Capability links:** CAP-012
**Status:** complete
**Closure:** user-approved on 2026-08-22 after TICKET-030 implementation,
review, local quality gates, and user-facing validation; remote checks remain
unavailable and are recorded as an accepted warning.
**Path history:** `features/open/FEAT-013-modular-editor-architecture.md`
-> `features/closed/FEAT-013-modular-editor-architecture.md`
**Horizon:** prerequisite
**Priority:** 1
**Owner:** repository implementation in the active worktree
**Approval:** user-authorized on 2026-08-22
**Source paths:** `docs/planning/reviews/CHG-003-editor-architecture-stabilization.md`,
`docs/planning/phases/open/PHASE-004A-stabilizing-editor-architecture.md`,
`README.md`, `AGENTS.md`, `.github/aidd-config.yml`
**Dependencies:** PHASE-004; TICKET-027; `make check` baseline
**Affected surfaces:** editor Python packages, tests, quality commands,
documentation, and future phase entry conditions
**Evidence path:** `evidence/editor-architecture-refactor.md`
**Last updated:** 2026-08-22

## Outcome

Maintainers can locate and modify one editor responsibility without navigating
an oversized module, while existing callers continue to use the established
`framestudio` module paths.

## Scope

- Establish clear implementation boundaries for the model, media/export,
  playback, timeline/UI, and CLI concerns.
- Keep compatibility facades thin and explicit.
- Preserve dependency injection and monkeypatch seams used by current tests.
- Reformat and document the resulting structure.

## Explicit non-goals

- Any new user-facing editing operation.
- Changes to project schema, output profile, playback semantics, or CLI JSON.
- Implementation of future audio, composition, or FPS features.

## Observable requirements

- Given an existing editor import path, importing its documented public symbols
  continues to work after the move.
- Given the GUI and CLI perform the same existing operation, both continue to
  route through the same shared domain behavior.
- Given a media or UI operation fails, the same error is surfaced through the
  existing error path rather than swallowed by a new facade.
- Given a maintainer searches for a responsibility, its implementation is in a
  focused module named for that responsibility.
- Given the current regression and quality commands run, they produce no new
  behavior failures attributable to the refactor.

## Definition of done

- TICKET-030's implementation and evidence are complete.
- Existing tests pass and focused compatibility tests cover moved boundaries.
- The architecture/file-size report confirms the agreed module target or
  documents any justified exception.
- User-facing validation confirms the existing editor workflow is unchanged.
- The record moved to `complete` after configured approval and evidence gates
  became terminal.
