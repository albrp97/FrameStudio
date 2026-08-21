# Delivery Backlog

**Backlog ID:** BACKLOG-001
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Phase:** PHASE-001
**Features:** FEAT-001, FEAT-002, FEAT-003
**Status:** needs-review
**Approval:** user-approved on 2026-08-21 before ticket execution
**Owner:** repository planning; maintainer identity is not recorded
**Source paths:** `vision.md`, `docs/specs/project-scope.md`,
`docs/specs/capability-map.md`, `docs/planning/phases.md`,
`docs/planning/features.md`, `.github/aidd-config.yml`
**Last updated:** 2026-08-21

## Purpose

The PHASE-001 section contains the complete bounded ticket set for opening one
supported source, controlling playback and timeline navigation, and
saving/reopening the source edit foundation. The PHASE-002 section below adds
the approved planning ticket set for one-source cutting and verified export.
The PHASE-003 section adds the completed deterministic CLI and GUI/CLI parity
ticket set. Later multi-source, composition, audio, and FPS work remain outside
these ticket sets.

## Ticket Lifecycle Records

This backlog index is synchronized with both ticket lifecycle directories.
Completed tickets are closed; TICKET-011 is now complete and closed.

| Sequence | ID | Status | Parent feature | Phase | Current path |
|---:|---|---|---|---|---|
| 1 | TICKET-001 | complete | FEAT-001 | PHASE-001 | `tickets/closed/TICKET-001-editor-foundation-contract.md` |
| 2 | TICKET-002 | complete | FEAT-001 | PHASE-001 | `tickets/closed/TICKET-002-open-supported-source.md` |
| 3 | TICKET-003 | complete | FEAT-002 | PHASE-001 | `tickets/closed/TICKET-003-playback-control-state.md` |
| 4 | TICKET-004 | complete | FEAT-002 | PHASE-001 | `tickets/closed/TICKET-004-preview-timeline-interaction.md` |
| 5 | TICKET-005 | complete | FEAT-003 | PHASE-001 | `tickets/closed/TICKET-005-versioned-project-persistence.md` |
| 6 | TICKET-006 | complete | FEAT-003 | PHASE-001 | `tickets/closed/TICKET-006-save-reopen-recovery.md` |
| 7 | TICKET-007 | complete | FEAT-004 | PHASE-002 | `tickets/closed/TICKET-007-segment-model-and-cut-semantics.md` |
| 8 | TICKET-008 | complete | FEAT-004 | PHASE-002 | `tickets/closed/TICKET-008-split-delete-editor-workflow.md` |
| 9 | TICKET-009 | complete | FEAT-006 | PHASE-002 | `tickets/closed/TICKET-009-persist-cut-state-recovery.md` |
| 10 | TICKET-010 | complete | FEAT-005 | PHASE-002 | `tickets/closed/TICKET-010-export-plan-selection.md` |
| 11 | TICKET-011 | complete | FEAT-005 | PHASE-002 | `tickets/closed/TICKET-011-verified-safe-export.md` |
| 12 | TICKET-012 | complete | FEAT-007 | PHASE-003 | `tickets/closed/TICKET-012-select-deterministic-cli-contract-and-inspection-schema.md` |
| 13 | TICKET-013 | complete | FEAT-007 | PHASE-003 | `tickets/closed/TICKET-013-implement-deterministic-project-inspection.md` |
| 14 | TICKET-014 | complete | FEAT-008 | PHASE-003 | `tickets/closed/TICKET-014-implement-one-source-edit-commands.md` |
| 15 | TICKET-015 | complete | FEAT-008 | PHASE-003 | `tickets/closed/TICKET-015-integrate-safe-deterministic-cli-export.md` |
| 16 | TICKET-016 | complete | FEAT-009 | PHASE-003 | `tickets/closed/TICKET-016-routing-gui-and-cli-through-shared-domain-operations.md` |
| 17 | TICKET-017 | complete | FEAT-009 | PHASE-003 | `tickets/closed/TICKET-017-verifying-gui-cli-parity-and-idempotent-round-trips.md` |

## Ticket summary

| Sequence | ID | Title | Parent feature | Dependencies | Status | Current path |
|---:|---|---|---|---|---|---|
| 1 | TICKET-001 | Select the editor foundation runtime and source contract | FEAT-001 | Approved objective, scope, phase, and feature | complete | `tickets/closed/TICKET-001-editor-foundation-contract.md` |
| 2 | TICKET-002 | Open and probe a supported source project | FEAT-001 | TICKET-001 | complete | `tickets/closed/TICKET-002-open-supported-source.md` |
| 3 | TICKET-003 | Implement source playback control state | FEAT-002 | TICKET-001, TICKET-002 | complete | `tickets/closed/TICKET-003-playback-control-state.md` |
| 4 | TICKET-004 | Build preview and timeline interaction | FEAT-002 | TICKET-003 | complete | `tickets/closed/TICKET-004-preview-timeline-interaction.md` |
| 5 | TICKET-005 | Persist a versioned one-source project | FEAT-003 | TICKET-001, TICKET-002 | complete | `tickets/closed/TICKET-005-versioned-project-persistence.md` |
| 6 | TICKET-006 | Integrate project save and reopen recovery | FEAT-003 | TICKET-004, TICKET-005 | complete | `tickets/closed/TICKET-006-save-reopen-recovery.md` |

## Dependency order

`TICKET-001 -> TICKET-002 -> {TICKET-003, TICKET-005}; TICKET-003 ->
TICKET-004; {TICKET-004, TICKET-005} -> TICKET-006`

TICKET-001 resolved the PHASE-001 entry decisions that would otherwise make
source-opening implementation guesswork: the GUI/runtime and playback
approach, the initial one-source project/source contract, source relinking
behavior, and the practical target-workstation smoke-test path. TICKET-002,
TICKET-003, and TICKET-005 now have terminal implementation evidence.
TICKET-004 and TICKET-006 are implemented and have user-confirmed
target-workstation interaction evidence, with the absence of retained
screenshots recorded as an accepted concern.

## Feature coverage

| Feature outcome | Ticket coverage | Coverage status |
|---|---|---|
| Open a supported source as a non-destructive project | TICKET-001, TICKET-002 | covered |
| Control playback and navigate the source timeline | TICKET-003, TICKET-004 | covered |
| Save and reopen the source edit foundation | TICKET-005, TICKET-006 | covered |
| CAP-001 - Managing projects and source media | TICKET-001, TICKET-002 | covered |
| CAP-002 - Playing and navigating an edit timeline | TICKET-003, TICKET-004 | covered |
| CAP-004 - Persisting and reopening edit state | TICKET-005, TICKET-006 | covered |
| CAP-012 - Protecting media, state, and failure recovery | TICKET-001 through TICKET-006 | covered |

## Readiness and gates

- The parent objective, scope, phase, capability map, and feature are
  user-approved.
- The configured baseline command is
  `python3 -m unittest discover -s tests`.
- The configured baseline, local quality checks, generated-media smoke flows,
  and focused editor tests are terminally evidenced.
- The target-workstation user-facing interaction gate is user-confirmed; no
  screenshot artifact was retained in this session.
- Remote checks are required by configuration, but no remote-check
  infrastructure was found in the repository.
- The backlog remains `needs-review` because remote checks are required by
  configuration but no remote-check infrastructure was found.

## Protected behavior

Existing scripts, command names, tests, source-preservation behavior, and
partial-output/verification behavior remain protected. Ticket execution must
not replace or silently change those surfaces.

## Source references

- `vision.md`
- `docs/specs/project-scope.md`
- `docs/specs/capability-map.md`
- `docs/planning/phases.md`
- `docs/planning/features.md`
- `.github/aidd-config.yml`

## PHASE-002 - Proposed Ticket Set

**Backlog extension ID:** BACKLOG-002  
**Objective:** OBJ-001  
**Scope:** SCOPE-001  
**Phase:** PHASE-002  
**Features:** FEAT-004, FEAT-005, FEAT-006  
**Status:** needs-review  
**Approval:** user-approved on 2026-08-21 before ticket execution  
**Owner:** repository planning; maintainer identity is not recorded  
**Last updated:** 2026-08-21  
**Source paths:** `vision.md`, `docs/specs/project-scope.md`,
`docs/specs/capability-map.md`, `docs/planning/phases.md`,
`docs/planning/features.md`, `.github/aidd-config.yml`

This ticket set covers one-source split/delete editing, cut-state recovery,
and verified fast/fallback export. It does not expand PHASE-002 into
multi-source timelines, composition, audio normalization, FPS enhancement,
copy/paste, or CLI parity.

### Ticket summary

| Sequence | ID | Title | Parent feature | Dependencies | Status | Current path |
|---:|---|---|---|---|---|---|
| 7 | TICKET-007 | Establish the non-destructive segment model and cut semantics | FEAT-004 | PHASE-001 project/timeline model | complete | `tickets/closed/TICKET-007-segment-model-and-cut-semantics.md` |
| 8 | TICKET-008 | Integrate split and delete into the editor workflow | FEAT-004 | TICKET-007 | complete | `tickets/closed/TICKET-008-split-delete-editor-workflow.md` |
| 9 | TICKET-009 | Persist and recover cut state safely | FEAT-006 | TICKET-007, TICKET-008 | complete | `tickets/closed/TICKET-009-persist-cut-state-recovery.md` |
| 10 | TICKET-010 | Select fast or fallback export plans | FEAT-005 | TICKET-007 | complete | `tickets/closed/TICKET-010-export-plan-selection.md` |
| 11 | TICKET-011 | Execute, verify, and publish export safely | FEAT-005 | TICKET-008, TICKET-010 | complete | `tickets/closed/TICKET-011-verified-safe-export.md` |

### Dependency order

`TICKET-007 -> TICKET-008 -> TICKET-009; TICKET-007 -> TICKET-010;
TICKET-008 + TICKET-010 -> TICKET-011`

TICKET-007 must establish the approved cut-boundary, gap/ripple, and
duration semantics before downstream editing or export work is execution-ready.
TICKET-010 must establish the approved stream-copy eligibility and fallback
policy before TICKET-011 can publish output.

### Feature coverage

| Feature outcome | Ticket coverage | Coverage status |
|---|---|---|
| Remove unwanted portions from one source non-destructively | TICKET-007, TICKET-008 | covered |
| Export a verified edited video through the fastest valid path | TICKET-010, TICKET-011 | covered |
| Preserve and recover saved cut decisions safely | TICKET-009 | covered |
| CAP-003 - Editing segments non-destructively | TICKET-007, TICKET-008 | covered |
| CAP-004 - Persisting and reopening edit state | TICKET-009 | covered |
| CAP-005 - Rendering fast, valid, and safe outputs | TICKET-010, TICKET-011 | covered |
| CAP-012 - Protecting media, state, and failure recovery | TICKET-007 through TICKET-011 | covered |

### Readiness and gates

- PHASE-002 and FEAT-004 through FEAT-006 are user-approved.
- TICKET-007's cut semantics are documented, user-approved, implemented, and
  evidenced. TICKET-010's stream-copy eligibility and fallback policy are
  documented, implemented, and evidenced.
- The configured baseline command is
  `python3 -m unittest discover -s tests`.
- Local quality and real-system media evidence are required for each relevant
  ticket.
- Remote checks are required by configuration, but no remote-check
  infrastructure was found in the repository.
- TICKET-011's manual gate is user-confirmed and its local evidence is
  terminal; the ticket is complete and closed by explicit user authorization.
  Provider-specific remote checks remain an accepted warning.

### Protected behavior

Existing scripts, command names, tests, source-preservation behavior,
versioned project recovery, and partial-output safety remain protected.
PHASE-002 implementation must extend those boundaries without silently
changing them.

### Source references

- `vision.md`
- `docs/specs/project-scope.md`
- `docs/specs/capability-map.md`
- `docs/planning/phases.md`
- `docs/planning/features.md`
- `docs/planning/tickets/closed/TICKET-007-segment-model-and-cut-semantics.md`
- `docs/planning/tickets/closed/TICKET-008-split-delete-editor-workflow.md`
- `docs/planning/tickets/closed/TICKET-009-persist-cut-state-recovery.md`
- `docs/planning/tickets/closed/TICKET-010-export-plan-selection.md`
- `docs/planning/tickets/closed/TICKET-011-verified-safe-export.md`
- `.github/aidd-config.yml`

## PHASE-003 - Completed Ticket Set

**Backlog extension ID:** BACKLOG-003  
**Objective:** OBJ-001  
**Scope:** SCOPE-001  
**Phase:** PHASE-003  
**Features:** FEAT-007, FEAT-008, FEAT-009  
**Status:** complete  
**Approval:** user-authorized on 2026-08-21 to close TICKET-012 through
TICKET-017 after implementation, testing, and local quality evidence; remote
checks remain unavailable and are recorded as an accepted warning  
**Owner:** repository planning; maintainer identity is not recorded  
**Last updated:** 2026-08-21  
**Source paths:** `vision.md`, `docs/specs/project-scope.md`,
`docs/specs/capability-map.md`, `docs/planning/phases.md`,
`docs/planning/phases/open/PHASE-003-repeating-the-basic-edit-through-agents.md`,
`docs/planning/features.md`, `.github/aidd-config.yml`

This ticket set exposes the existing one-source editor workflow to local,
deterministic automation. It does not expand the product into multiple
sources, composition, audio normalization, FPS enhancement, cloud services,
or natural-language agent orchestration.

### Ticket summary

| Sequence | ID | Title | Parent feature | Dependencies | Status | Current path |
|---:|---|---|---|---|---|---|
| 12 | TICKET-012 | Select the deterministic CLI contract and inspection schema | FEAT-007 | TICKET-011; stable project behavior | complete | `tickets/closed/TICKET-012-select-deterministic-cli-contract-and-inspection-schema.md` |
| 13 | TICKET-013 | Implement deterministic project inspection | FEAT-007 | TICKET-012 | complete | `tickets/closed/TICKET-013-implement-deterministic-project-inspection.md` |
| 14 | TICKET-014 | Implement deterministic one-source edit commands | FEAT-008 | TICKET-012, TICKET-013 | complete | `tickets/closed/TICKET-014-implement-one-source-edit-commands.md` |
| 15 | TICKET-015 | Integrate safe deterministic CLI export | FEAT-008 | TICKET-011, TICKET-014 | complete | `tickets/closed/TICKET-015-integrate-safe-deterministic-cli-export.md` |
| 16 | TICKET-016 | Route GUI and CLI through shared domain operations | FEAT-009 | TICKET-014, TICKET-015 | complete | `tickets/closed/TICKET-016-routing-gui-and-cli-through-shared-domain-operations.md` |
| 17 | TICKET-017 | Verify GUI/CLI parity and idempotent round trips | FEAT-009 | TICKET-015, TICKET-016 | complete | `tickets/closed/TICKET-017-verifying-gui-cli-parity-and-idempotent-round-trips.md` |

### Dependency order

`TICKET-011 -> TICKET-012 -> TICKET-013 -> TICKET-014 -> TICKET-015 ->
TICKET-016 -> TICKET-017`

TICKET-012 must settle the command, output, error, identifier, and versioning
contract before implementation. TICKET-014 must expose deterministic mutations
before shared GUI/CLI routing and parity verification can be completed.

### Feature coverage

| Feature outcome | Ticket coverage | Coverage status |
|---|---|---|
| Inspect projects through a deterministic CLI | TICKET-012, TICKET-013 | covered |
| Apply one-source edits through the CLI | TICKET-014, TICKET-015 | covered |
| Share domain behavior between GUI and CLI | TICKET-016, TICKET-017 | covered |
| CAP-004 - Persisting and reopening edit state | TICKET-012 through TICKET-017 | covered |
| CAP-006 - Automating the project through a deterministic CLI | TICKET-012 through TICKET-017 | covered |
| CAP-012 - Protecting media, state, and failure recovery | TICKET-012 through TICKET-017 | covered |

### Readiness and gates

- PHASE-003 and FEAT-007 through FEAT-009 are confirmed with the user's
  authorization to continue next-phase planning.
- TICKET-011 is complete and closed; its unavailable remote-check and visual
  artifact requirements remain accepted warnings.
- TICKET-012 through TICKET-017 are `complete` closed records with local
  implementation and evidence complete; no remote-check pass is claimed.
- Each ticket requires baseline, local quality, applicable real-media, and
  evidence coverage before implementation readiness.
- Remote checks remain required by `.github/aidd-config.yml` and are not
  available in the repository.

### Protected behavior

Existing editor interactions, project persistence, verified export,
source-preservation guarantees, command names, legacy scripts, and prior
ticket evidence remain protected. PHASE-003 work must extend the domain
without silently changing those behaviors.

### Source references

- `vision.md`
- `docs/specs/project-scope.md`
- `docs/specs/capability-map.md`
- `docs/planning/phases/open/PHASE-003-repeating-the-basic-edit-through-agents.md`
- `docs/planning/features/open/FEAT-007-inspecting-projects-through-a-deterministic-cli.md`
- `docs/planning/features/open/FEAT-008-applying-one-source-edits-through-cli.md`
- `docs/planning/features/open/FEAT-009-sharing-domain-behavior-between-gui-and-cli.md`
- `docs/planning/tickets/closed/TICKET-011-verified-safe-export.md`
- `.github/aidd-config.yml`

## Migration Notes

- `BACKLOG-001` and `BACKLOG-002` remain represented in this single backlog
  index; they are index metadata sections, not additional ticket records.
- Ticket records retain their stable IDs and content while their paths classify
  `complete` records as closed; any transient `needs-review`/`gated` states
  remain open until an authorized transition.
