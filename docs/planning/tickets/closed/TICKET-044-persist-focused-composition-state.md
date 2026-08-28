# TICKET-044 - Persist Focused Composition State

**Ticket ID:** TICKET-044
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Phase:** PHASE-006
**Feature:** FEAT-019
**Capability links:** CAP-005, CAP-009, CAP-010, CAP-012
**Status:** complete
**Closure:** user-approved on 2026-08-23 after PHASE-006 implementation,
automated verification, shared target-workstation validation, review, and
local delivery evidence; remote checks remain unavailable and are recorded as
an accepted warning.
**Horizon:** future
**Priority:** 7
**Owner:** repository planning; maintainer identity is not recorded
**Approval:** user-authorized on 2026-08-22 to create and implement the
PHASE-006 ticket set; the completed outcome was confirmed by the user on
2026-08-23
**Provider:** auto; base and target branches are not configured in
`.github/aidd-config.yml`
**Source paths:** `docs/planning/features/open/FEAT-019-delivering-focused-compositions-safely.md`,
`docs/planning/tickets/open/TICKET-040-preserve-visual-modifications-through-block-edits.md`,
`docs/planning/tickets/open/TICKET-043-preserve-triplicate-group-lifecycle.md`,
`docs/planning/phases/open/PHASE-006-focusing-and-composing-important-action.md`,
`framestudio/model_project.py`, `framestudio/operations.py`,
`.github/aidd-config.yml`
**Dependencies:** TICKET-040 and TICKET-043; existing versioned project
schema and save/reopen behavior
**Risks:** schema migration can drop nested transform or group state, stale
references can create invalid projects, and shared state can reappear after
reopen
**Affected surfaces:** project schema, serialization, migrations, save/reopen,
relinking, validation, tests, CLI payload foundations, and evidence
**Evidence path:** `evidence/phase-006-focused-composition-persistence.md`
**Last updated:** 2026-08-23
**Path history:** `tickets/open/TICKET-044-persist-focused-composition-state.md`
-> `tickets/closed/TICKET-044-persist-focused-composition-state.md`

## Outcome

Focused transforms and linked triplicate groups survive versioned project
save/reopen and invalid state is rejected explicitly.

## Scope

- Persist segment modification bundles, triplicate group identities, instance
  roles, layout values, and clean/disabled state.
- Add a versioned schema change and deterministic migration behavior.
- Validate references, defaults, bounds, and independence on load.
- Preserve compatibility with projects that contain no focused composition.
- Keep source paths, segment intervals, colors, deletion state, and ordering
  unchanged during round trips.

## Explicit non-goals

- New transform or triplicate editing behavior.
- CLI commands, preview composition, final rendering, or FPS enhancement.
- Destructive migration or rewriting source media.

## Observable requirements

- Given a project with transforms and triplicate groups, save/reopen should
  restore equivalent values, identities, roles, and statuses.
- Given an older project, migration should preserve existing editing state and
  initialize explicit defaults for new fields.
- Given invalid or orphaned group references, load should return a structured
  error or safe blocked state rather than silently dropping data.
- Given a round trip, source ranges, colors, deletion state, ordering, and
  duration should remain unchanged.

## Commands and quality gates

- `python3 -m unittest discover -s tests`
- `make check`
- `make contract`
- `make quality PYTHON=.venv/bin/python`

## Functionality flows

- Save/reopen ordinary, modified, and triplicate projects.
- Migrate a pre-change project and inspect defaults and source state.
- Corrupt or orphan a disposable linked-group record and verify explicit
  failure handling.

## User validation before closure

Save and reopen modified and triplicate projects, review the restored values
and group identities, and confirm legacy projects remain usable. Return
`PASS`, `FAIL`, or `BLOCKED` with evidence.

## Protected behavior

Existing project-schema compatibility, source relinking, segment identity and
colors, ordering, source-level audio decisions, fixed 1920x1080 output,
source preservation, and atomic save safety remain unchanged.

## Definition of done

- The schema and migration preserve all focused-composition state.
- Round-trip and invalid-state tests pass.
- User-validation evidence confirms no ordinary editing state regresses.

## Closure

Focused composition persistence is complete under the reviewed PHASE-006
delivery checkpoint. Provider-side checks remain unavailable because no
remote or upstream is configured.
