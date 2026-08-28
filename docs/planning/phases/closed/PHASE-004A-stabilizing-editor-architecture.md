# PHASE-004A - Stabilizing Editor Architecture

**Phase ID:** PHASE-004A
**Parent links:** OBJ-001, SCOPE-001
**Capability links:** CAP-012
**Sequence:** 4.5
**Status:** complete
**Closure:** user-approved on 2026-08-22 after FEAT-013 completion, review,
local quality gates, and user-facing validation; remote checks remain
unavailable and are recorded as an accepted warning.
**Path history:** `phases/open/PHASE-004A-stabilizing-editor-architecture.md`
-> `phases/closed/PHASE-004A-stabilizing-editor-architecture.md`
**Feature links:** FEAT-013
**Horizon:** prerequisite
**Owner:** repository planning and implementation in the active worktree
**Approval:** user-authorized on 2026-08-22 before implementation
**Source paths:** `vision.md`, `docs/specs/project-scope.md`,
`docs/specs/capability-map.md`, `docs/planning/phases.md`,
`docs/planning/repo-map.md`, `docs/planning/reviews/CHG-003-editor-architecture-stabilization.md`,
`.github/aidd-config.yml`
**Dependencies:** PHASE-004 complete; `make check` baseline
**Affected surfaces:** `framestudio` module boundaries, tests, Makefile
quality paths, README architecture notes, and future phase readiness
**Evidence path:** `evidence/editor-architecture-refactor.md`
**Last updated:** 2026-08-22

## Outcome

The editor is organized into focused, discoverable modules with stable public
facades, so future audio, composition, and frame-rate work can change one
responsibility without reopening unrelated code.

## Included

- Split domain validation, source identity, segment value objects, timeline
  operations, project lifecycle, and persistence-facing serialization into
  focused implementation modules.
- Split export policy, plan/value objects, progress reporting, media execution,
  output verification, and atomic publication into focused modules.
- Split playback backends, timeline geometry/canvas behavior, editor window
  construction/orchestration, and CLI parsing/handlers/serialization.
- Preserve current public module imports, test patch seams, GUI/CLI parity,
  process cancellation, and error behavior.
- Reformat changed Python modules with the repository formatter and update
  directly related complexity or architecture documentation.

## Explicit non-goals

- Automatic source-level audio normalization.
- Visual transform authoring, triplicate composition, or clean/reset controls.
- 60 FPS enhancement.
- New editing behavior, output-profile changes, or schema changes.
- Replacing the original helper scripts.

## Entry conditions

- PHASE-004 and FEAT-010 through FEAT-012 are complete and closed.
- The current test and compile baseline is terminal.
- CHG-003, FEAT-013, and TICKET-030 are approved for implementation.
- Existing public import paths and protected behavior have been inventoried.

## Exit conditions

- The large editor modules are reduced to compatibility façades or focused
  orchestration boundaries, with implementation responsibilities separated.
- GUI, CLI, persistence, playback, editing, and export behavior remains
  regression-safe.
- The configured local quality and real-system gates are terminal where
  available, with unavailable remote checks recorded as warnings.
- A user-facing validation handoff confirms that the refactor did not alter
  the current editor workflow.

## Risks and dependencies

- Moving imports can break monkeypatch seams or create circular dependencies.
- GTK construction and FFmpeg process ownership need explicit lifecycle
  boundaries.
- Large mechanical moves can hide behavior changes if tests are not run in
  focused increments.

## Validation and evidence

- Protected baseline: `make check`.
- Focused model, export, playback, timeline, UI, CLI, and persistence tests
  after each extraction.
- Final `make check`, `make contract`, `make smoke`, and `make quality
  PYTHON=.venv/bin/python` gates.
- Architecture/file-size report and user-facing before/after validation in
  `evidence/editor-architecture-refactor.md`.

## Closure

All PHASE-004A exit conditions are satisfied. The architecture refactor is
complete, FEAT-013 and TICKET-030 are complete, local gates are terminal, and
the user-facing validation result is passed. Remote checks are unavailable
because no remote or upstream is configured.
