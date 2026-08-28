# CHG-003 - Editor Architecture Stabilization

**Change ID:** CHG-003
**Type:** Material planning change
**Status:** complete
**Date:** 2026-08-22
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Owner:** repository planning and implementation in the active worktree
**Approval:** User-authorized by the 2026-08-22 request:
"i think we need before continuing to the next phase a complete reformat and
refactor of the code because some files are getting just too big like 1k lines
or more. we should use the best practices for software engineering having
dedicated responsabilities for each file and so on, so basically i want you to
rework the structure and organization of the actual code so its easy to read
and work and modify"
**Source paths:** `README.md`, `AGENTS.md`, `.github/aidd-config.yml`,
`docs/planning/phases.md`, `docs/planning/features.md`,
`docs/planning/backlog.md`, `docs/planning/repo-map.md`,
`framestudio/model.py`, `framestudio/export.py`,
`framestudio/app.py`, `framestudio/cli.py`,
`framestudio/timeline.py`, `framestudio/ffmpeg_playback.py`
**Affected IDs:** PHASE-004A, FEAT-013, TICKET-030, PHASE-005,
PHASE-006, PHASE-007, CAP-012
**Last updated:** 2026-08-22

## Request and classification

The editor has accumulated several oversized modules that combine domain
state, media execution, UI construction, and command handling. The request is
to stabilize the architecture before the next product phase so that each
responsibility has a discoverable implementation boundary while existing
behavior and public import paths remain safe.

This is a material sequencing change because it inserts a prerequisite
maintainability phase between the completed mixed-source delivery and the
confirmed future product phases. It does not change the approved product
objective, output contract, editing semantics, or future feature scope.

## Decision

1. Add PHASE-004A as a prerequisite architecture-stabilization phase before
   PHASE-005.
2. Add FEAT-013 and TICKET-030 under PHASE-004A for one independently
   verifiable refactor outcome.
3. Extract focused implementation modules for the domain model, export and
   playback, GUI and timeline, and CLI boundaries.
4. Keep `framestudio.model`, `framestudio.export`,
   `framestudio.app`, `framestudio.cli`, `framestudio.timeline`, and
   `framestudio.ffmpeg_playback` as compatibility facades where existing
   tests and callers rely on those paths.
5. Preserve the current GUI, CLI, persistence, playback, editing, export,
   legacy-script, and source-safety behavior. No new product capability is
   included in this change.
6. Use focused tests after each extraction and the configured repository
   quality gates before user validation.

## Affected-artifact inventory

| Artifact | Impact | Action |
|---|---|---|
| PHASE-005 through PHASE-007 | Future work must wait for maintainable, stable boundaries | Add PHASE-004A prerequisite |
| Existing editor modules | Responsibilities are currently mixed across oversized files | Extract focused implementation modules |
| Existing public imports and patch seams | Tests and callers depend on current module paths | Preserve facade symbols and dependency seams |
| README and repository map | Architecture and file ownership need to remain discoverable | Update only directly related documentation |
| Quality configuration | Complexity paths and checks must cover new modules | Update configuration when required by the new layout |
| Product behavior | No approved behavior change | Protect with baseline and regression evidence |

## Normative boundary

- The refactor is complete only when each primary implementation module has a
  focused responsibility and no extracted implementation module exceeds the
  agreed maintainability target of approximately 600 lines without a
  documented boundary reason.
- Facades may re-export symbols and coordinate compatibility, but they must not
  become second implementations of the same behavior.
- New modules must not introduce circular imports or bypass the shared domain
  operations used by the GUI and CLI.
- The fixed 1920x1080 output contract, atomic segment-block semantics, color
  preservation, split inheritance, Space playback behavior, persistence
  schema, export safety, and legacy scripts remain protected.

## Validation and remaining gates

- The pre-refactor `make check` baseline passed on 2026-08-22 with 158 tests.
- TICKET-030 must add focused regression coverage for compatibility imports and
  extracted boundaries where existing tests do not already provide it.
- `make check`, `make contract`, `make smoke`, `make quality
  PYTHON=.venv/bin/python`, and the configured static-analysis commands remain
  required when available.
- User-facing validation remains required before this change or its child
  records can move to `complete`.
- No commit, push, or remote-check pass is claimed by this planning record.

## Closure

The user validated the completed architecture refactor on 2026-08-22.
TICKET-030, FEAT-013, and PHASE-004A have terminal local evidence and are
approved for closure. The local commit is the next delivery operation; remote
checks remain unavailable until a remote is configured.
