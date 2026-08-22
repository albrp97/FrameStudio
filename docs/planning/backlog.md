# Delivery Backlog

**Backlog ID:** BACKLOG-001
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Phase:** PHASE-001
**Features:** FEAT-001, FEAT-002, FEAT-003
**Status:** complete
**Approval:** user-approved on 2026-08-22 for closure after successful
implementation and validation; remote checks remain unavailable and are
recorded as an accepted warning
**Owner:** repository planning; maintainer identity is not recorded
**Source paths:** `vision.md`, `docs/specs/project-scope.md`,
`docs/specs/capability-map.md`, `docs/planning/phases.md`,
`docs/planning/features.md`, `.github/aidd-config.yml`
**Last updated:** 2026-08-22

## Purpose

The PHASE-001 section contains the complete bounded ticket set for opening one
supported source, controlling playback and timeline navigation, and
saving/reopening the source edit foundation. TICKET-029 is a corrective
transport ticket for the reported Space playback failure. The PHASE-002 section below adds
the approved planning ticket set for one-source cutting and verified export.
The PHASE-003 section adds the completed deterministic CLI and GUI/CLI parity
ticket set. The PHASE-004 section adds the approved mixed-source ticket set, including
atomic segment-block movement, copy/paste, split inheritance, CLI parity, and
the fixed 1920x1080 project render profile. Visual-modification authoring and
cleaning, audio, composition, and 60 FPS work remain assigned to later phases.
The PHASE-004A section adds the architecture-stabilization prerequisite before
those future phases. The PHASE-005 section adds the source-level audio and
tested delivery-policy ticket set; implementation is complete and remains in
verification pending user validation and delivery review.

## Ticket Lifecycle Records

This backlog index is synchronized with both ticket lifecycle directories.
Completed tickets are closed; TICKET-001 through TICKET-028 and TICKET-030
remain complete and closed. TICKET-029 is verifying again after its playback
scope was reopened for a timeline pacing correction. TICKET-031 through
TICKET-037 are verifying open records awaiting user validation and delivery
review for PHASE-005.

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
| 28 | TICKET-028 | complete | FEAT-004 | PHASE-002 | `tickets/closed/TICKET-028-restore-one-source-block-movement.md` |
| 29 | TICKET-029 | verifying | FEAT-002 | PHASE-001 | `tickets/open/TICKET-029-restore-space-playback-toggle.md` |
| 12 | TICKET-012 | complete | FEAT-007 | PHASE-003 | `tickets/closed/TICKET-012-select-deterministic-cli-contract-and-inspection-schema.md` |
| 13 | TICKET-013 | complete | FEAT-007 | PHASE-003 | `tickets/closed/TICKET-013-implement-deterministic-project-inspection.md` |
| 14 | TICKET-014 | complete | FEAT-008 | PHASE-003 | `tickets/closed/TICKET-014-implement-one-source-edit-commands.md` |
| 15 | TICKET-015 | complete | FEAT-008 | PHASE-003 | `tickets/closed/TICKET-015-integrate-safe-deterministic-cli-export.md` |
| 16 | TICKET-016 | complete | FEAT-009 | PHASE-003 | `tickets/closed/TICKET-016-routing-gui-and-cli-through-shared-domain-operations.md` |
| 17 | TICKET-017 | complete | FEAT-009 | PHASE-003 | `tickets/closed/TICKET-017-verifying-gui-cli-parity-and-idempotent-round-trips.md` |
| 18 | TICKET-018 | complete | FEAT-010 | PHASE-004 | `tickets/closed/TICKET-018-defining-multi-source-project-identity-and-relinking.md` |
| 19 | TICKET-019 | complete | FEAT-010 | PHASE-004 | `tickets/closed/TICKET-019-implement-mixed-source-import-probing-and-persistence.md` |
| 20 | TICKET-020 | complete | FEAT-011 | PHASE-004 | `tickets/closed/TICKET-020-defining-mixed-source-timebase-and-placement-semantics.md` |
| 21 | TICKET-021 | complete | FEAT-011 | PHASE-004 | `tickets/closed/TICKET-021-implement-mixed-source-placement-and-move-operations.md` |
| 22 | TICKET-022 | complete | FEAT-011 | PHASE-004 | `tickets/closed/TICKET-022-extending-segment-editing-and-multi-selection-across-sources.md` |
| 23 | TICKET-023 | complete | FEAT-011 | PHASE-004 | `tickets/closed/TICKET-023-exposing-mixed-source-timeline-operations-through-the-cli.md` |
| 24 | TICKET-024 | complete | FEAT-012 | PHASE-004 | `tickets/closed/TICKET-024-defining-mixed-source-output-canvas-and-timing-policy.md` |
| 25 | TICKET-025 | complete | FEAT-012 | PHASE-004 | `tickets/closed/TICKET-025-implement-composed-mixed-source-preview.md` |
| 26 | TICKET-026 | complete | FEAT-012 | PHASE-004 | `tickets/closed/TICKET-026-implement-verified-mixed-source-export.md` |
| 27 | TICKET-027 | complete | FEAT-012 | PHASE-004 | `tickets/closed/TICKET-027-verifying-mixed-source-round-trips-and-source-preservation.md` |
| 30 | TICKET-030 | complete | FEAT-013 | PHASE-004A | `tickets/closed/TICKET-030-refactor-editor-architecture.md` |
| 31 | TICKET-031 | verifying | FEAT-014 | PHASE-005 | `tickets/open/TICKET-031-define-source-level-audio-policy.md` |
| 32 | TICKET-032 | verifying | FEAT-014 | PHASE-005 | `tickets/open/TICKET-032-analyze-and-persist-source-audio-decisions.md` |
| 33 | TICKET-033 | verifying | FEAT-014 | PHASE-005 | `tickets/open/TICKET-033-apply-source-audio-decisions-consistently.md` |
| 34 | TICKET-034 | verifying | FEAT-015 | PHASE-005 | `tickets/open/TICKET-034-benchmark-and-document-delivery-profiles.md` |
| 35 | TICKET-035 | verifying | FEAT-015 | PHASE-005 | `tickets/open/TICKET-035-route-audio-aware-and-mixed-source-exports-safely.md` |
| 36 | TICKET-036 | verifying | FEAT-016 | PHASE-005 | `tickets/open/TICKET-036-expose-synchronized-media-decisions.md` |
| 37 | TICKET-037 | verifying | FEAT-016 | PHASE-005 | `tickets/open/TICKET-037-verify-balanced-mixed-source-delivery.md` |

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
- The backlog is `complete` by user-approved local and target-workstation
  validation; remote checks remain required by configuration but no
  remote-check infrastructure was found and no remote pass is claimed.

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
**Status:** complete
**Approval:** user-approved on 2026-08-22 for closure after successful
implementation and validation; remote checks remain unavailable and are
recorded as an accepted warning
**Owner:** repository planning; maintainer identity is not recorded  
**Last updated:** 2026-08-22
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
| 28 | TICKET-028 | Restore one-source block movement | FEAT-004 | TICKET-008; existing shared movement operation | complete | `tickets/closed/TICKET-028-restore-one-source-block-movement.md` |

### Dependency order

`TICKET-007 -> TICKET-008 -> TICKET-009; TICKET-007 -> TICKET-010;
TICKET-008 + TICKET-010 -> TICKET-011; TICKET-008 -> TICKET-028`

TICKET-007 must establish the approved cut-boundary, gap/ripple, and
duration semantics before downstream editing or export work is execution-ready.
TICKET-010 must establish the approved stream-copy eligibility and fallback
policy before TICKET-011 can publish output.

### Feature coverage

| Feature outcome | Ticket coverage | Coverage status |
|---|---|---|
| Remove unwanted portions and reorder blocks in one source non-destructively | TICKET-007, TICKET-008, TICKET-028 | covered |
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
- TICKET-028 is a complete corrective ticket for the reported one-source
  movement regression. Its user-facing flow is terminally validated and
  closure is user-approved; configured remote checks remain unavailable.
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

- PHASE-003 and FEAT-007 through FEAT-009 are complete and closed by the
  user's 2026-08-22 approval.
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

## PHASE-004 - Planned Ticket Set

**Backlog extension ID:** BACKLOG-004
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Phase:** PHASE-004
**Features:** FEAT-010, FEAT-011, FEAT-012
**Status:** complete
**Approval:** user-approved on 2026-08-22 for closure after successful
implementation and validation; CHG-001's atomic block clarification and
CHG-002's fixed 1080p render-profile decision are included; remote checks
remain unavailable and are recorded as an accepted warning
**Owner:** repository planning; maintainer identity is not recorded
**Last updated:** 2026-08-22
**Source paths:** `vision.md`, `docs/specs/project-scope.md`,
`docs/specs/capability-map.md`, `docs/planning/phases.md`,
`docs/planning/phases/open/PHASE-004-combining-mixed-source-footage.md`,
`docs/planning/features.md`, `.github/aidd-config.yml`

This ticket set delivers the next bounded expansion: multiple source
identities, deterministic mixed-source timeline placement and atomic block
editing, stable block colors, copy/paste, composed preview on a fixed 1920x1080 canvas, safe export,
persistence, and CLI parity. It uses the established render profile for output
delivery and does not include automatic audio normalization,
visual-modification authoring or cleaning, triplicate layouts, or 60 FPS
enhancement.

### Ticket summary

| Sequence | ID | Title | Parent feature | Dependencies | Status | Current path |
|---:|---|---|---|---|---|---|
| 18 | TICKET-018 | Define multi-source project identity and relinking | FEAT-010 | TICKET-017; existing project schema | complete | `tickets/closed/TICKET-018-defining-multi-source-project-identity-and-relinking.md` |
| 19 | TICKET-019 | Implement mixed-source import, probing, and persistence | FEAT-010 | TICKET-018 | complete | `tickets/closed/TICKET-019-implement-mixed-source-import-probing-and-persistence.md` |
| 20 | TICKET-020 | Define mixed-source timebase and placement semantics | FEAT-011 | TICKET-018, TICKET-019 | complete | `tickets/closed/TICKET-020-defining-mixed-source-timebase-and-placement-semantics.md` |
| 21 | TICKET-021 | Implement mixed-source placement and move operations | FEAT-011 | TICKET-019, TICKET-020 | complete | `tickets/closed/TICKET-021-implement-mixed-source-placement-and-move-operations.md` |
| 22 | TICKET-022 | Extend segment editing and multi-selection across sources | FEAT-011 | TICKET-020, TICKET-021 | complete | `tickets/closed/TICKET-022-extending-segment-editing-and-multi-selection-across-sources.md` |
| 23 | TICKET-023 | Expose mixed-source timeline operations through the CLI | FEAT-011 | TICKET-019, TICKET-021, TICKET-022 | complete | `tickets/closed/TICKET-023-exposing-mixed-source-timeline-operations-through-the-cli.md` |
| 24 | TICKET-024 | Define mixed-source output canvas and timing policy | FEAT-012 | TICKET-019, TICKET-020 | complete | `tickets/closed/TICKET-024-defining-mixed-source-output-canvas-and-timing-policy.md` |
| 25 | TICKET-025 | Implement composed mixed-source preview | FEAT-012 | TICKET-019, TICKET-020, TICKET-024 | complete | `tickets/closed/TICKET-025-implement-composed-mixed-source-preview.md` |
| 26 | TICKET-026 | Implement verified mixed-source export | FEAT-012 | TICKET-024; mixed-source timeline | complete | `tickets/closed/TICKET-026-implement-verified-mixed-source-export.md` |
| 27 | TICKET-027 | Verify mixed-source round trips and source preservation | FEAT-012 | TICKET-023, TICKET-025, TICKET-026 | complete | `tickets/closed/TICKET-027-verifying-mixed-source-round-trips-and-source-preservation.md` |

### Dependency order

`TICKET-018 -> TICKET-019 -> TICKET-020 -> TICKET-021 -> TICKET-022 ->
TICKET-023; TICKET-020 -> TICKET-024 -> TICKET-025 -> TICKET-026 ->
TICKET-027`

TICKET-018 settled source identity and relinking before import expanded the
project model. TICKET-020 settled mixed timebase, placement, atomic block,
copy/paste, and split-inheritance semantics before movement, selection,
preview, and export were verified. CHG-002 fixes the mixed-source render
canvas at 1920x1080 and keeps codec/container selection in the established
render profile. TICKET-027 completed the phase-level round-trip and source-preservation gate
with revised output evidence.

### Feature coverage

| Feature outcome | Ticket coverage | Coverage status |
|---|---|---|
| Import and retain mixed-source project identity | TICKET-018, TICKET-019 | covered |
| Arrange and edit a mixed-source timeline | TICKET-020 through TICKET-023 | covered |
| Preview and export mixed-source edits | TICKET-024 through TICKET-027 | covered |
| CAP-002 - Playing and navigating an edit timeline | TICKET-020, TICKET-025, TICKET-027 | covered |
| CAP-003 - Editing segments non-destructively | TICKET-021, TICKET-022, TICKET-027 | covered |
| CAP-005 - Rendering fast, valid, and safe outputs | TICKET-024, TICKET-026, TICKET-027 | covered |
| CAP-007 - Supporting multiple mixed-media sources | TICKET-018 through TICKET-027 | covered |
| CAP-012 - Protecting media, state, and failure recovery | TICKET-018 through TICKET-027 | covered |

### Readiness and gates

- PHASE-004 and FEAT-010 through FEAT-012 are complete and closed by the
  user's 2026-08-22 approval.
- All Phase 4 implementation tickets completed their local preimplementation,
  implementation, verification, and target-workstation validation gates.
- Each ticket has baseline, applicable real-media, local quality, evidence,
  and user-validation coverage recorded for closure.
- Remote checks remain required by `.github/aidd-config.yml` and are not
  available in the repository.

### Protected behavior

Existing one-source editor and CLI operations, project persistence, verified
export, source-preservation guarantees, command names, legacy scripts, and
prior evidence remain protected while the mixed-source model is introduced.

### Source references

- `vision.md`
- `docs/specs/project-scope.md`
- `docs/specs/capability-map.md`
- `docs/planning/phases/open/PHASE-004-combining-mixed-source-footage.md`
- `docs/planning/features/open/FEAT-010-importing-and-retaining-mixed-source-project-identity.md`
- `docs/planning/features/open/FEAT-011-arranging-and-editing-a-mixed-source-timeline.md`
- `docs/planning/features/open/FEAT-012-previewing-and-exporting-mixed-source-edits.md`
- `docs/planning/reviews/CHG-001-atomic-segment-block-editing.md`
- `docs/planning/reviews/CHG-002-fixed-1080p-render-profile.md`
- `.github/aidd-config.yml`

## PHASE-004A - Architecture Stabilization Ticket Set

**Backlog extension ID:** BACKLOG-004A
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Phase:** PHASE-004A
**Features:** FEAT-013
**Status:** complete
**Approval:** user-authorized on 2026-08-22 before implementation
**Owner:** repository planning and implementation in the active worktree
**Last updated:** 2026-08-22
**Source paths:** `docs/planning/reviews/CHG-003-editor-architecture-stabilization.md`,
`docs/planning/phases/open/PHASE-004A-stabilizing-editor-architecture.md`,
`docs/planning/features/open/FEAT-013-modular-editor-architecture.md`,
`.github/aidd-config.yml`

This focused ticket set separates the oversized editor modules before
PHASE-005 begins. It does not add audio normalization, visual modifications,
triplicate composition, FPS enhancement, or any other product behavior.

### Ticket summary

| Sequence | ID | Title | Parent feature | Dependencies | Status | Current path |
|---:|---|---|---|---|---|---|
| 30 | TICKET-030 | Refactor editor architecture | FEAT-013 | PHASE-004; protected `make check` baseline | complete | `tickets/closed/TICKET-030-refactor-editor-architecture.md` |

### Dependency order

`PHASE-004 -> CHG-003 -> PHASE-004A -> FEAT-013 -> TICKET-030`

TICKET-030 is the only implementation unit in this feature. Its internal
extraction slices are ordered model, media/playback, interfaces, then final
verification so each compatibility boundary can be tested before the next
one moves.

### Readiness and gates

- CHG-003, PHASE-004A, FEAT-013, and TICKET-030 are user-authorized.
- The protected baseline `make check` passed before refactor edits.
- Local regression, contract, smoke, quality, and applicable static-analysis
  gates remain required.
- User-facing validation and evidence are required before closure.
- Remote checks are required by configuration but no remote infrastructure is
  configured; no remote pass is claimed.

### Protected behavior

Existing scripts, command names, project schema versions, source relinking,
fixed 1920x1080 rendering, atomic segment-block editing, selection semantics,
Space playback, persistence, source preservation, export safety, and CLI JSON
contracts remain protected.

### Source references

- `docs/planning/reviews/CHG-003-editor-architecture-stabilization.md`
- `docs/planning/phases/open/PHASE-004A-stabilizing-editor-architecture.md`
- `docs/planning/features/open/FEAT-013-modular-editor-architecture.md`
- `.github/aidd-config.yml`

## PHASE-005 - Planned Ticket Set

**Backlog extension ID:** BACKLOG-005
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Phase:** PHASE-005
**Features:** FEAT-014, FEAT-015, FEAT-016
**Status:** verifying
**Approval:** user-authorized on 2026-08-22 to implement the feature and
ticket set; user validation is pending
**Owner:** repository planning and implementation in the active worktree
**Last updated:** 2026-08-22
**Source paths:** `docs/planning/phases/open/PHASE-005-balancing-sources-and-delivering-consistent-media.md`,
`docs/planning/features/open/FEAT-014-balancing-each-source-consistently.md`,
`docs/planning/features/open/FEAT-015-selecting-tested-delivery-routes.md`,
`docs/planning/features/open/FEAT-016-synchronizing-media-decisions-and-verification.md`,
`.github/aidd-config.yml`

This ticket set covers source-level audio policy, analysis and persistence,
consistent preview/export application, delivery-profile benchmarking, safe
mixed-source routing, synchronized GUI/CLI/project state, and end-to-end
verification. It does not include visual modifications, triplicate
composition, or 60 FPS enhancement.

### Ticket summary

| Sequence | ID | Title | Parent feature | Dependencies | Status | Current path |
|---:|---|---|---|---|---|---|
| 31 | TICKET-031 | Define source-level audio policy | FEAT-014 | PHASE-004A; approved product direction | verifying | `tickets/open/TICKET-031-define-source-level-audio-policy.md` |
| 32 | TICKET-032 | Analyze and persist source audio decisions | FEAT-014 | TICKET-031; source probing and project schema | verifying | `tickets/open/TICKET-032-analyze-and-persist-source-audio-decisions.md` |
| 33 | TICKET-033 | Apply source audio decisions consistently | FEAT-014 | TICKET-031, TICKET-032; preview/export seams | verifying | `tickets/open/TICKET-033-apply-source-audio-decisions-consistently.md` |
| 34 | TICKET-034 | Benchmark and document delivery profiles | FEAT-015 | TICKET-031; established render profile | verifying | `tickets/open/TICKET-034-benchmark-and-document-delivery-profiles.md` |
| 35 | TICKET-035 | Route audio-aware and mixed-source exports safely | FEAT-015 | TICKET-031, TICKET-032, TICKET-034 | verifying | `tickets/open/TICKET-035-route-audio-aware-and-mixed-source-exports-safely.md` |
| 36 | TICKET-036 | Expose synchronized media decisions | FEAT-016 | TICKET-032, TICKET-034, TICKET-035 | verifying | `tickets/open/TICKET-036-expose-synchronized-media-decisions.md` |
| 37 | TICKET-037 | Verify balanced mixed-source delivery | FEAT-016 | TICKET-033, TICKET-035, TICKET-036 | verifying | `tickets/open/TICKET-037-verify-balanced-mixed-source-delivery.md` |

### Dependency order

`TICKET-031 -> TICKET-032 -> TICKET-033`

`TICKET-031 -> TICKET-034 -> TICKET-035`

`TICKET-032 + TICKET-034 + TICKET-035 -> TICKET-036`

`TICKET-033 + TICKET-035 + TICKET-036 -> TICKET-037`

TICKET-031 is the recommended first implementation ticket because its
approved audio measurement and normalization policy is an entry condition for
source analysis and delivery benchmarking.

### Feature coverage

| Feature outcome | Ticket coverage | Coverage status |
|---|---|---|
| Balance each input source consistently across its timeline | TICKET-031 through TICKET-033 | covered |
| Select tested delivery routes for audio-aware and mixed-source exports | TICKET-031, TICKET-034, TICKET-035 | covered |
| Synchronize media decisions across product surfaces and verified output | TICKET-032, TICKET-034 through TICKET-037 | covered |
| CAP-005 - Rendering fast, valid, and safe outputs | TICKET-034 through TICKET-037 | covered |
| CAP-008 - Handling audio per source input | TICKET-031 through TICKET-033, TICKET-036, TICKET-037 | covered |
| CAP-012 - Protecting media, state, and failure recovery | TICKET-031 through TICKET-037 | covered |

### Readiness and gates

- PHASE-005 and FEAT-014 through FEAT-016 are verifying under approved
  objective, scope, and capability ancestry.
- TICKET-031 through TICKET-037 define bounded scope, non-goals,
  dependencies, protected behavior, commands, evidence paths, and
  user-validation plans.
- The configured baseline command remains
  `python3 -m unittest discover -s tests`.
- Implementation and automated verification are complete on the dedicated
  ticket branch. User validation, review, and configured delivery gates remain
  required before closure.
- Remote checks remain required by `.github/aidd-config.yml`, but no
  remote-check infrastructure is configured; no remote pass is claimed.

### Protected behavior

Existing one-source and mixed-source editing, fixed 1920x1080 output,
project-schema compatibility, source preservation, export safety, CLI JSON
contracts, legacy scripts, and prior evidence remain protected. PHASE-005
must add source-level audio behavior without silently changing those
contracts.

### Source references

- `vision.md`
- `docs/specs/project-scope.md`
- `docs/specs/capability-map.md`
- `docs/specs/future-product-direction.md`
- `docs/planning/phases/open/PHASE-005-balancing-sources-and-delivering-consistent-media.md`
- `docs/planning/features/open/FEAT-014-balancing-each-source-consistently.md`
- `docs/planning/features/open/FEAT-015-selecting-tested-delivery-routes.md`
- `docs/planning/features/open/FEAT-016-synchronizing-media-decisions-and-verification.md`
- `.github/aidd-config.yml`

## Migration Notes

- `BACKLOG-001` and `BACKLOG-002` remain represented in this single backlog
  index; they are index metadata sections, not additional ticket records.
- Ticket records retain their stable IDs and content while their paths classify
  `complete` records as closed; any transient `needs-review`/`gated` states
  remain open until an authorized transition.
- BACKLOG-004 originally added the confirmed PHASE-004 ticket set in the open
  lifecycle directory; those records later transitioned to `complete` and
  moved to the closed directory on 2026-08-22.
- CHG-001 clarifies the PHASE-004 block-editing contract in place without
  changing stable IDs or lifecycle paths; visual modification inheritance and
  cleaning remain assigned to PHASE-006.
- CHG-002 revises the mixed-source output policy in place without changing
  stable IDs or lifecycle paths; prior dimension evidence remains historical
  and requires superseding fixed-1080p verification.
- CHG-003 adds PHASE-004A, FEAT-013, and TICKET-030 as a prerequisite
  architecture-stabilization subtree before the confirmed future phases. The
  subtree completed after user validation on 2026-08-22 and its records moved
  to the closed lifecycle directories.
