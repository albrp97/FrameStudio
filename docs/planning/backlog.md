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
**Last updated:** 2026-08-27

## Purpose

The PHASE-001 section contains the complete bounded ticket set for opening one
supported source, controlling playback and timeline navigation, and
saving/reopening the source edit foundation. TICKET-029 is a corrective
transport ticket for the reported Space playback failure. TICKET-059 is a
corrective B-key split ticket for the one-source editing workflow. The PHASE-002 section below adds
the approved planning ticket set for one-source cutting and verified export.
The PHASE-003 section adds the completed deterministic CLI and GUI/CLI parity
ticket set. The PHASE-004 section adds the approved mixed-source ticket set, including
atomic segment-block movement, copy/paste, split inheritance, CLI parity, and
the fixed 1920x1080 project render profile. Visual-modification authoring and
cleaning, audio, composition, and 60 FPS work remain assigned to later phases.
The PHASE-004A section adds the architecture-stabilization prerequisite before
those future phases. The PHASE-005 section adds the source-level audio and tested delivery-policy
ticket set, now complete and closed after user validation and delivery review.
The PHASE-006 section adds the approved reusable focus and linked triplicate
composition ticket set; implementation, validation, review, and local delivery
are complete and its records are closed.
The PHASE-007 section adds the completed target-FPS export ticket set,
including the export planning panel, smart naming, calibrated estimates,
validated interpolation, audio/timing preservation, and safe delivery
verification. Its records were closed after implementation, testing, review,
and user acceptance; TICKET-060 records the corrective implementation.
The PHASE-008 section tracks responsive preview optimization, direct focus
controls, mixed-FPS render-strategy comparison, and restoration research.
TICKET-061 through TICKET-082 are complete and closed. FEAT-025 through
FEAT-028 are complete and closed, including the approved Strategy B route,
restoration benchmarks, optional SuperUltraCompact enhancement, editor
responsiveness corrections, and default-zoom triplicate offsets. Historical
benchmark, runtime, target-workstation, and remote-check limitations remain
recorded in the linked evidence.

## Ticket Lifecycle Records

This backlog index is synchronized with both ticket lifecycle directories.
Completed tickets are closed; TICKET-001 through TICKET-047 are complete and
closed after their approved validation, review, and local delivery evidence.
TICKET-048 through TICKET-060 are complete and closed after the user
confirmed they were approved, accepted, and tested. Unavailable remote and
target-specific checks remain recorded as accepted warnings. TICKET-061
through TICKET-082 are complete and closed with their linked evidence after
the user's explicit manual-validation and closeout decision on 2026-08-28.

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
| 29 | TICKET-029 | complete | FEAT-002 | PHASE-001 | `tickets/closed/TICKET-029-restore-space-playback-toggle.md` |
| 59 | TICKET-059 | complete | FEAT-004 | PHASE-002 | `tickets/closed/TICKET-059-restore-b-key-timeline-splitting.md` |
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
| 31 | TICKET-031 | complete | FEAT-014 | PHASE-005 | `tickets/closed/TICKET-031-define-source-level-audio-policy.md` |
| 32 | TICKET-032 | complete | FEAT-014 | PHASE-005 | `tickets/closed/TICKET-032-analyze-and-persist-source-audio-decisions.md` |
| 33 | TICKET-033 | complete | FEAT-014 | PHASE-005 | `tickets/closed/TICKET-033-apply-source-audio-decisions-consistently.md` |
| 34 | TICKET-034 | complete | FEAT-015 | PHASE-005 | `tickets/closed/TICKET-034-benchmark-and-document-delivery-profiles.md` |
| 35 | TICKET-035 | complete | FEAT-015 | PHASE-005 | `tickets/closed/TICKET-035-route-audio-aware-and-mixed-source-exports-safely.md` |
| 36 | TICKET-036 | complete | FEAT-016 | PHASE-005 | `tickets/closed/TICKET-036-expose-synchronized-media-decisions.md` |
| 37 | TICKET-037 | complete | FEAT-016 | PHASE-005 | `tickets/closed/TICKET-037-verify-balanced-mixed-source-delivery.md` |
| 38 | TICKET-038 | complete | FEAT-017 | PHASE-006 | `tickets/closed/TICKET-038-define-segment-visual-modification-contract.md` |
| 39 | TICKET-039 | complete | FEAT-017 | PHASE-006 | `tickets/closed/TICKET-039-implement-segment-focus-controls.md` |
| 40 | TICKET-040 | complete | FEAT-017 | PHASE-006 | `tickets/closed/TICKET-040-preserve-visual-modifications-through-block-edits.md` |
| 41 | TICKET-041 | complete | FEAT-018 | PHASE-006 | `tickets/closed/TICKET-041-define-triplicate-group-and-layout-policy.md` |
| 42 | TICKET-042 | complete | FEAT-018 | PHASE-006 | `tickets/closed/TICKET-042-implement-linked-triplicate-composition.md` |
| 43 | TICKET-043 | complete | FEAT-018 | PHASE-006 | `tickets/closed/TICKET-043-preserve-triplicate-group-lifecycle.md` |
| 44 | TICKET-044 | complete | FEAT-019 | PHASE-006 | `tickets/closed/TICKET-044-persist-focused-composition-state.md` |
| 45 | TICKET-045 | complete | FEAT-019 | PHASE-006 | `tickets/closed/TICKET-045-expose-focused-edits-through-cli-and-gui-parity.md` |
| 46 | TICKET-046 | complete | FEAT-019 | PHASE-006 | `tickets/closed/TICKET-046-render-and-verify-focused-compositions-safely.md` |
| 47 | TICKET-047 | complete | FEAT-019 | PHASE-006 | `tickets/closed/TICKET-047-verify-focused-composition-delivery.md` |
| 48 | TICKET-048 | complete | FEAT-020 | PHASE-007 | `tickets/closed/TICKET-048-define-target-fps-selection-and-enhancement-scope.md` |
| 49 | TICKET-049 | complete | FEAT-020 | PHASE-007 | `tickets/closed/TICKET-049-persist-and-expose-frame-rate-policy.md` |
| 50 | TICKET-050 | complete | FEAT-021 | PHASE-007 | `tickets/closed/TICKET-050-choose-export-destination-and-smart-name.md` |
| 51 | TICKET-051 | complete | FEAT-021 | PHASE-007 | `tickets/closed/TICKET-051-calibrate-export-processing-time-estimates.md` |
| 52 | TICKET-052 | complete | FEAT-021 | PHASE-007 | `tickets/closed/TICKET-052-build-export-planning-panel.md` |
| 53 | TICKET-053 | complete | FEAT-022 | PHASE-007 | `tickets/closed/TICKET-053-validate-interpolation-backend-and-artifact-gate.md` |
| 54 | TICKET-054 | complete | FEAT-022 | PHASE-007 | `tickets/closed/TICKET-054-implement-exact-target-fps-interpolation.md` |
| 55 | TICKET-055 | complete | FEAT-022 | PHASE-007 | `tickets/closed/TICKET-055-preserve-audio-and-delivery-profile-during-enhancement.md` |
| 56 | TICKET-056 | complete | FEAT-023 | PHASE-007 | `tickets/closed/TICKET-056-connect-enhanced-export-routes-and-progress.md` |
| 57 | TICKET-057 | complete | FEAT-023 | PHASE-007 | `tickets/closed/TICKET-057-verify-enhanced-output-integrity-and-regressions.md` |
| 58 | TICKET-058 | complete | FEAT-023 | PHASE-007 | `tickets/closed/TICKET-058-run-target-workstation-phase-007-validation.md` |
| 60 | TICKET-060 | complete | FEAT-021 | PHASE-007 | `tickets/closed/TICKET-060-refine-export-planning-and-enhanced-smart-render.md` |
| 61 | TICKET-061 | complete | FEAT-024 | PHASE-008 | `tickets/closed/TICKET-061-research-lossless-cut-preview-architecture.md` |
| 62 | TICKET-062 | complete | FEAT-024 | PHASE-008 | `tickets/closed/TICKET-062-benchmark-current-preview-latency.md` |
| 63 | TICKET-063 | complete | FEAT-024 | PHASE-008 | `tickets/closed/TICKET-063-experiment-with-preview-rendering-strategies.md` |
| 64 | TICKET-064 | complete | FEAT-024 | PHASE-008 | `tickets/closed/TICKET-064-adopt-and-document-responsive-preview-strategy.md` |
| 65 | TICKET-065 | complete | FEAT-025 | PHASE-008 | `tickets/closed/TICKET-065-define-direct-focus-modification-interactions.md` |
| 66 | TICKET-066 | complete | FEAT-025 | PHASE-008 | `tickets/closed/TICKET-066-implement-scroll-driven-focus-modifications.md` |
| 67 | TICKET-067 | complete | FEAT-025 | PHASE-008 | `tickets/closed/TICKET-067-correct-zoomed-focus-coordinate-bounds.md` |
| 68 | TICKET-068 | complete | FEAT-025 | PHASE-008 | `tickets/closed/TICKET-068-verify-focus-control-persistence-and-parity.md` |
| 69 | TICKET-069 | complete | FEAT-026 | PHASE-008 | `tickets/closed/TICKET-069-define-comparable-mixed-fps-render-benchmarks.md` |
| 70 | TICKET-070 | complete | FEAT-026 | PHASE-008 | `tickets/closed/TICKET-070-benchmark-concat-first-enhancement-strategy.md` |
| 71 | TICKET-071 | complete | FEAT-026 | PHASE-008 | `tickets/closed/TICKET-071-benchmark-per-source-enhancement-strategy.md` |
| 72 | TICKET-072 | complete | FEAT-026 | PHASE-008 | `tickets/closed/TICKET-072-select-and-document-mixed-fps-render-default.md` |
| 73 | TICKET-073 | complete | FEAT-027 | PHASE-008 | `tickets/closed/TICKET-073-survey-video-upscaling-denoise-and-compression-recovery.md` |
| 74 | TICKET-074 | complete | FEAT-027 | PHASE-008 | `tickets/closed/TICKET-074-benchmark-restoration-candidates.md` |
| 75 | TICKET-075 | complete | FEAT-027 | PHASE-008 | `tickets/closed/TICKET-075-recommend-restoration-pipeline-and-gates.md` |
| 76 | TICKET-076 | complete | FEAT-026 | PHASE-008 | `tickets/closed/TICKET-076-adopt-per-source-render-strategy.md` |
| 77 | TICKET-077 | complete | FEAT-027 | PHASE-008 | `tickets/closed/TICKET-077-benchmark-real-video-enhancer-restoration.md` |
| 78 | TICKET-078 | complete | FEAT-027 | PHASE-008 | `tickets/closed/TICKET-078-expand-cross-model-restoration-benchmark.md` |
| 79 | TICKET-079 | complete | FEAT-028 | PHASE-008 | `tickets/closed/TICKET-079-implement-optional-upscale-enhancement.md` |
| 80 | TICKET-080 | complete | FEAT-028 | PHASE-008 | `tickets/closed/TICKET-080-benchmark-upscale-render-strategies.md` |
| 81 | TICKET-081 | complete | FEAT-028 | PHASE-008 | `tickets/closed/TICKET-081-restore-editor-loading-zoom-and-gpu-interpolation.md` |
| 82 | TICKET-082 | complete | FEAT-025 | PHASE-008 | `tickets/closed/TICKET-082-allow-triplicate-horizontal-offset-at-default-zoom.md` |

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
| 59 | TICKET-059 | Restore B-key timeline splitting | FEAT-004 | TICKET-008; playback/timeline position mapping | complete | `tickets/closed/TICKET-059-restore-b-key-timeline-splitting.md` |

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
- `docs/planning/features/closed/FEAT-007-inspecting-projects-through-a-deterministic-cli.md`
- `docs/planning/features/closed/FEAT-008-applying-one-source-edits-through-cli.md`
- `docs/planning/features/closed/FEAT-009-sharing-domain-behavior-between-gui-and-cli.md`
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
- `docs/planning/features/closed/FEAT-010-importing-and-retaining-mixed-source-project-identity.md`
- `docs/planning/features/closed/FEAT-011-arranging-and-editing-a-mixed-source-timeline.md`
- `docs/planning/features/closed/FEAT-012-previewing-and-exporting-mixed-source-edits.md`
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
`docs/planning/features/closed/FEAT-013-modular-editor-architecture.md`,
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
- `docs/planning/features/closed/FEAT-013-modular-editor-architecture.md`
- `.github/aidd-config.yml`

## PHASE-005 - Completed Ticket Set

**Backlog extension ID:** BACKLOG-005
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Phase:** PHASE-005
**Features:** FEAT-014, FEAT-015, FEAT-016
**Status:** complete
**Approval:** user-authorized on 2026-08-22 to implement and close the
feature and ticket set after validation
**Owner:** repository planning and implementation in the active worktree
**Last updated:** 2026-08-22
**Source paths:** `docs/planning/phases/open/PHASE-005-balancing-sources-and-delivering-consistent-media.md`,
`docs/planning/features/closed/FEAT-014-balancing-each-source-consistently.md`,
`docs/planning/features/closed/FEAT-015-selecting-tested-delivery-routes.md`,
`docs/planning/features/closed/FEAT-016-synchronizing-media-decisions-and-verification.md`,
`.github/aidd-config.yml`

This ticket set covers source-level audio policy, analysis and persistence,
consistent preview/export application, delivery-profile benchmarking, safe
mixed-source routing, synchronized GUI/CLI/project state, and end-to-end
verification. It does not include visual modifications, triplicate
composition, or 60 FPS enhancement.

### Ticket summary

| Sequence | ID | Title | Parent feature | Dependencies | Status | Current path |
|---:|---|---|---|---|---|---|
| 31 | TICKET-031 | Define source-level audio policy | FEAT-014 | PHASE-004A; approved product direction | complete | `tickets/closed/TICKET-031-define-source-level-audio-policy.md` |
| 32 | TICKET-032 | Analyze and persist source audio decisions | FEAT-014 | TICKET-031; source probing and project schema | complete | `tickets/closed/TICKET-032-analyze-and-persist-source-audio-decisions.md` |
| 33 | TICKET-033 | Apply source audio decisions consistently | FEAT-014 | TICKET-031, TICKET-032; preview/export seams | complete | `tickets/closed/TICKET-033-apply-source-audio-decisions-consistently.md` |
| 34 | TICKET-034 | Benchmark and document delivery profiles | FEAT-015 | TICKET-031; established render profile | complete | `tickets/closed/TICKET-034-benchmark-and-document-delivery-profiles.md` |
| 35 | TICKET-035 | Route audio-aware and mixed-source exports safely | FEAT-015 | TICKET-031, TICKET-032, TICKET-034 | complete | `tickets/closed/TICKET-035-route-audio-aware-and-mixed-source-exports-safely.md` |
| 36 | TICKET-036 | Expose synchronized media decisions | FEAT-016 | TICKET-032, TICKET-034, TICKET-035 | complete | `tickets/closed/TICKET-036-expose-synchronized-media-decisions.md` |
| 37 | TICKET-037 | Verify balanced mixed-source delivery | FEAT-016 | TICKET-033, TICKET-035, TICKET-036 | complete | `tickets/closed/TICKET-037-verify-balanced-mixed-source-delivery.md` |

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

- PHASE-005 and FEAT-014 through FEAT-016 are complete and closed under
  approved objective, scope, and capability ancestry.
- TICKET-031 through TICKET-037 define bounded scope, non-goals,
  dependencies, protected behavior, commands, evidence paths, and
  user-validation plans.
- The configured baseline command remains
  `python3 -m unittest discover -s tests`.
- Implementation, automated verification, user validation, review, and local
  delivery are complete on the dedicated ticket branch.
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
- `docs/planning/features/closed/FEAT-014-balancing-each-source-consistently.md`
- `docs/planning/features/closed/FEAT-015-selecting-tested-delivery-routes.md`
- `docs/planning/features/closed/FEAT-016-synchronizing-media-decisions-and-verification.md`
- `.github/aidd-config.yml`

## PHASE-006 - Verification Ticket Set

**Backlog extension ID:** BACKLOG-006
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Phase:** PHASE-006
**Features:** FEAT-017, FEAT-018, FEAT-019
**Status:** complete
**Approval:** user-authorized on 2026-08-22 to break down and implement the
approved phase; user validation, review, and local delivery are complete
**Owner:** repository planning; maintainer identity is not recorded
**Last updated:** 2026-08-22
**Source paths:** `vision.md`, `docs/specs/project-scope.md`,
`docs/specs/capability-map.md`, `docs/specs/future-product-direction.md`,
`docs/planning/phases/open/PHASE-006-focusing-and-composing-important-action.md`,
`docs/planning/features.md`, `.github/aidd-config.yml`

This ticket set covers reusable segment focus controls, linked triplicate
portrait/focused-action composition, versioned persistence, GUI/CLI parity,
safe rendering, and end-to-end verification. It does not include automatic
60 FPS enhancement, arbitrary effects, or full professional compositing.

### Ticket summary

| Sequence | ID | Title | Parent feature | Dependencies | Status | Current path |
|---:|---|---|---|---|---|---|
| 38 | TICKET-038 | Define segment visual modification contract | FEAT-017 | PHASE-005; stable segment identity and selection | complete | `tickets/closed/TICKET-038-define-segment-visual-modification-contract.md` |
| 39 | TICKET-039 | Implement segment focus controls | FEAT-017 | TICKET-038 | complete | `tickets/closed/TICKET-039-implement-segment-focus-controls.md` |
| 40 | TICKET-040 | Preserve visual modifications through block edits | FEAT-017 | TICKET-038, TICKET-039 | complete | `tickets/closed/TICKET-040-preserve-visual-modifications-through-block-edits.md` |
| 41 | TICKET-041 | Define triplicate group and layout policy | FEAT-018 | TICKET-038; fixed 1920x1080 canvas | complete | `tickets/closed/TICKET-041-define-triplicate-group-and-layout-policy.md` |
| 42 | TICKET-042 | Implement linked triplicate composition | FEAT-018 | TICKET-039, TICKET-041 | complete | `tickets/closed/TICKET-042-implement-linked-triplicate-composition.md` |
| 43 | TICKET-043 | Preserve triplicate group lifecycle | FEAT-018 | TICKET-040, TICKET-041, TICKET-042 | complete | `tickets/closed/TICKET-043-preserve-triplicate-group-lifecycle.md` |
| 44 | TICKET-044 | Persist focused composition state | FEAT-019 | TICKET-040, TICKET-043 | complete | `tickets/closed/TICKET-044-persist-focused-composition-state.md` |
| 45 | TICKET-045 | Expose focused edits through CLI and GUI parity | FEAT-019 | TICKET-044 | complete | `tickets/closed/TICKET-045-expose-focused-edits-through-cli-and-gui-parity.md` |
| 46 | TICKET-046 | Render and verify focused compositions safely | FEAT-019 | TICKET-044, TICKET-045 | complete | `tickets/closed/TICKET-046-render-and-verify-focused-compositions-safely.md` |
| 47 | TICKET-047 | Verify focused composition delivery | FEAT-019 | TICKET-039, TICKET-040, TICKET-043, TICKET-045, TICKET-046 | complete | `tickets/closed/TICKET-047-verify-focused-composition-delivery.md` |

### Dependency order

`TICKET-038 -> TICKET-039 -> TICKET-040`

`TICKET-041 -> TICKET-042 -> TICKET-043`

`TICKET-038 + TICKET-040 + TICKET-043 -> TICKET-044`

`TICKET-044 -> TICKET-045 -> TICKET-046 -> TICKET-047`

TICKET-038 settles the shared transform contract before implementation.
TICKET-041 settles linked-group and background/layout semantics before
triplicate behavior. Persistence and surface parity precede safe render
integration and end-to-end verification.

### Feature coverage

| Feature outcome | Ticket coverage | Coverage status |
|---|---|---|
| Edit reusable visual focus controls on timeline segments | TICKET-038 through TICKET-040 | covered |
| Create linked triplicate portrait and focused-action compositions | TICKET-041 through TICKET-043 | covered |
| Preview, persist, and safely deliver focused compositions | TICKET-044 through TICKET-047 | covered |
| CAP-005 - Rendering fast, valid, and safe outputs | TICKET-046, TICKET-047 | covered |
| CAP-009 - Applying reusable segment visual modifications | TICKET-038 through TICKET-040, TICKET-044, TICKET-045, TICKET-047 | covered |
| CAP-010 - Linking triplicate composition instances | TICKET-041 through TICKET-047 | covered |
| CAP-012 - Protecting media, state, and failure recovery | TICKET-038 through TICKET-047 | covered |

### Readiness and gates

- PHASE-006, FEAT-017, FEAT-018, and FEAT-019 are complete closed records
  with stable objective, scope, and capability links.
- TICKET-038 through TICKET-047 have implemented bounded scope, non-goals,
  dependencies, protected behavior, commands, evidence paths, and
  user-validation plans.
- Technical implementation, local verification, user validation, review, and
  local delivery are complete.
- The configured baseline, local quality, contract, smoke, and user-facing
  gates must be established by the preimplementation checklist before any
  ticket enters execution.
- Remote checks remain required by `.github/aidd-config.yml`; no remote or
  upstream is configured, so no remote pass is claimed.

### Protected behavior

Existing one-source and mixed-source editing, segment colors and identities,
source-level audio decisions, fixed 1920x1080 output, project compatibility,
safe export, CLI contracts, legacy scripts, and source preservation remain
protected throughout PHASE-006.

### Source references

- `vision.md`
- `docs/specs/project-scope.md`
- `docs/specs/capability-map.md`
- `docs/specs/future-product-direction.md`
- `docs/planning/phases/open/PHASE-006-focusing-and-composing-important-action.md`
- `docs/planning/features/closed/FEAT-017-editing-reusable-visual-focus-controls.md`
- `docs/planning/features/closed/FEAT-018-creating-linked-triplicate-compositions.md`
- `docs/planning/features/closed/FEAT-019-delivering-focused-compositions-safely.md`
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
- PHASE-005, FEAT-014 through FEAT-016, and TICKET-031 through TICKET-037
  completed after user validation, review, and local delivery on 2026-08-22;
  their records moved to the closed lifecycle directories.
- BACKLOG-006 added the PHASE-006 planning set with FEAT-017 through FEAT-019
  and TICKET-038 through TICKET-047. After user validation, review, and local
  delivery, all records moved to the configured closed lifecycle directories.
- BACKLOG-007 added the PHASE-007 planning set with FEAT-020 through FEAT-023
  and TICKET-048 through TICKET-060. After implementation, testing, review,
  and user acceptance on 2026-08-26, all records moved to the configured
  closed lifecycle directories; unavailable remote and target-specific checks
  remain recorded as accepted warnings.

## PHASE-007 - Target-FPS Export Ticket Set

**Backlog extension ID:** BACKLOG-007
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Phase:** PHASE-007
**Features:** FEAT-020, FEAT-021, FEAT-022, FEAT-023
**Status:** complete
**Closure:** user-approved on 2026-08-26 after TICKET-048 through
TICKET-060 were implemented, tested, reviewed, and accepted; unavailable
remote and target-specific checks remain recorded as accepted warnings
**Approval:** user-authorized on 2026-08-24 to create the PHASE-007 feature
and ticket breakdown; completion was subsequently accepted by the user
**Owner:** repository planning; maintainer identity is not recorded
**Last updated:** 2026-08-26
**Source paths:** `vision.md`, `docs/specs/project-scope.md`,
`docs/specs/capability-map.md`,
`docs/specs/future-product-direction.md`,
`docs/planning/phases/closed/PHASE-007-producing-validated-60-fps-edits.md`,
`docs/planning/features.md`, `FPS-ENHANCEMENT-RESEARCH.md`,
`FLOWFRAMES-RESEARCH.md`, `docs/specs/cli-contract.md`,
`.github/aidd-config.yml`

This ticket set covers the requested export destination page, smart
collision-safe naming, lowest/highest/custom/60 FPS choices, enhancement
toggle, realistic processing estimate, validated RIFE/RVE interpolation,
exact timing, audio preservation, safe progress, and final verification. It
does not replace legacy scripts, claim universal performance, or implement
work in this planning step.

### Ticket summary

| Sequence | ID | Title | Parent feature | Dependencies | Status | Current path |
|---:|---|---|---|---|---|---|
| 48 | TICKET-048 | Define target FPS selection and enhancement scope | FEAT-020 | PHASE-005; PHASE-006 timing; source metadata | complete | `tickets/closed/TICKET-048-define-target-fps-selection-and-enhancement-scope.md` |
| 49 | TICKET-049 | Persist and expose frame-rate policy | FEAT-020 | TICKET-048; versioned project schema | complete | `tickets/closed/TICKET-049-persist-and-expose-frame-rate-policy.md` |
| 50 | TICKET-050 | Choose export destination and smart name | FEAT-021 | TICKET-048; destination safety guard | complete | `tickets/closed/TICKET-050-choose-export-destination-and-smart-name.md` |
| 51 | TICKET-051 | Calibrate export processing-time estimates | FEAT-021 | TICKET-048; local throughput evidence | complete | `tickets/closed/TICKET-051-calibrate-export-processing-time-estimates.md` |
| 52 | TICKET-052 | Build export planning panel | FEAT-021 | TICKET-049, TICKET-050, TICKET-051 | complete | `tickets/closed/TICKET-052-build-export-planning-panel.md` |
| 53 | TICKET-053 | Validate interpolation backend and artifact gate | FEAT-022 | TICKET-048; representative fixtures; target runtime | complete | `tickets/closed/TICKET-053-validate-interpolation-backend-and-artifact-gate.md` |
| 54 | TICKET-054 | Implement exact target FPS interpolation | FEAT-022 | TICKET-048, TICKET-053; mixed-source timing | complete | `tickets/closed/TICKET-054-implement-exact-target-fps-interpolation.md` |
| 55 | TICKET-055 | Preserve audio and delivery profile during enhancement | FEAT-022 | TICKET-054; PHASE-005 delivery policy | complete | `tickets/closed/TICKET-055-preserve-audio-and-delivery-profile-during-enhancement.md` |
| 56 | TICKET-056 | Connect enhanced export routes and progress | FEAT-023 | TICKET-049, TICKET-052, TICKET-055 | complete | `tickets/closed/TICKET-056-connect-enhanced-export-routes-and-progress.md` |
| 57 | TICKET-057 | Verify enhanced output integrity and regressions | FEAT-023 | TICKET-056; timing/audio behavior | complete | `tickets/closed/TICKET-057-verify-enhanced-output-integrity-and-regressions.md` |
| 58 | TICKET-058 | Run target workstation Phase 007 validation | FEAT-023 | TICKET-057; target workstation and fixtures | complete | `tickets/closed/TICKET-058-run-target-workstation-phase-007-validation.md` |
| 60 | TICKET-060 | Refine export planning and enhanced smart render | FEAT-021 | TICKET-048 through TICKET-058 implementation surfaces; protected export baseline | complete | `tickets/closed/TICKET-060-refine-export-planning-and-enhanced-smart-render.md` |

### Dependency order

`TICKET-048 -> TICKET-049`

`TICKET-048 -> {TICKET-050, TICKET-051}`

`TICKET-049 + TICKET-050 + TICKET-051 -> TICKET-052`

`TICKET-048 -> TICKET-053 -> TICKET-054 -> TICKET-055`

`TICKET-049 + TICKET-052 + TICKET-055 -> TICKET-056 -> TICKET-057 -> TICKET-058`

`TICKET-060` was a corrective implementation record under FEAT-021. It
preserved the original ticket ancestry and is now complete and closed with
the Phase 007 delivery set.

TICKET-048 settles the target-rate, already-target-rate, lower-rate, and
enhancement-scope rules before implementation. TICKET-049 makes that policy
round-trip through project and CLI state. TICKET-050 and TICKET-051 can be
planned independently after the policy, then TICKET-052 integrates the
preflight export surface. TICKET-053 validates the backend before
TICKET-054/055 connect interpolation, timing, audio, and delivery. TICKET-056
through TICKET-058 complete the GUI/CLI route, verification, regression, and
target-workstation evidence.

### Feature coverage

| Feature outcome | Ticket coverage | Coverage status |
|---|---|---|
| Choose target frame-rate delivery and enhancement scope | TICKET-048, TICKET-049 | covered |
| Plan export destination, naming, and processing estimates | TICKET-050 through TICKET-052, TICKET-060 | covered |
| Run validated motion interpolation | TICKET-053 through TICKET-055 | covered |
| Verify and safely deliver enhanced or ordinary exports | TICKET-056 through TICKET-058 | covered |
| CAP-005 - Rendering fast, valid, and safe outputs | TICKET-048 through TICKET-058 | covered |
| CAP-006 - Automating the project through a deterministic CLI | TICKET-056 through TICKET-058 | covered |
| CAP-011 - Enhancing frame rate to 60 FPS | TICKET-048, TICKET-049, TICKET-051 through TICKET-058 | covered |
| CAP-012 - Protecting media, state, and failure recovery | TICKET-048 through TICKET-058 | covered |

### Readiness and gates

- PHASE-007 and FEAT-020 through FEAT-023 are complete and closed with their
  required child records.
- TICKET-048 through TICKET-060 have stable ancestry, bounded scope,
  implementation and regression evidence, and user acceptance.
- Baseline, local quality, contract, smoke, real-media, static-analysis,
  review, and available user-validation gates are recorded in the linked
  evidence. Unavailable remote and target-specific checks remain explicit
  accepted warnings rather than false passes.

### Protected behavior

Existing one-source and mixed-source editing, source-level audio decisions,
fixed 1920x1080 output, project compatibility, safe partial-output handling,
structured CLI errors, legacy scripts, and source preservation remain
protected throughout PHASE-007.

### Source references

- `vision.md`
- `docs/specs/project-scope.md`
- `docs/specs/capability-map.md`
- `docs/specs/future-product-direction.md`
- `docs/planning/phases/closed/PHASE-007-producing-validated-60-fps-edits.md`
- `docs/planning/features/closed/FEAT-020-choosing-target-frame-rate-delivery.md`
- `docs/planning/features/closed/FEAT-021-planning-export-destination-and-estimates.md`
- `docs/planning/features/closed/FEAT-022-running-validated-motion-interpolation.md`
- `docs/planning/features/closed/FEAT-023-verifying-safe-enhanced-delivery.md`
- `FPS-ENHANCEMENT-RESEARCH.md`
- `FLOWFRAMES-RESEARCH.md`
- `framestudio_concat.py`
- `framestudio_fps.py`
- `.github/aidd-config.yml`

## PHASE-008 - Responsive Preview and Media Strategy Ticket Set

**Backlog extension ID:** BACKLOG-008
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Phase:** PHASE-008
**Features:** FEAT-024, FEAT-025, FEAT-026, FEAT-027, FEAT-028
**Status:** complete
**Approval:** user-authorized on 2026-08-26 to create the PHASE-008 feature
and ticket breakdown; user-authorized manual validation and closeout on
2026-08-28
**Owner:** repository planning; maintainer identity is not recorded
**Last updated:** 2026-08-28
**Source paths:** `vision.md`, `docs/specs/project-scope.md`,
`docs/specs/capability-map.md`, `docs/specs/future-product-direction.md`,
`docs/planning/phases/closed/PHASE-008-optimizing-responsive-preview-and-media-strategy.md`,
`docs/planning/features/closed/FEAT-024-optimizing-cursor-driven-preview.md`,
`docs/planning/features/closed/FEAT-025-streamlining-segment-focus-modifications.md`,
`docs/planning/features/closed/FEAT-026-comparing-mixed-fps-render-strategies.md`,
`docs/planning/features/closed/FEAT-027-researching-video-restoration-and-upscaling.md`,
`docs/planning/features/closed/FEAT-028-adding-optional-upscale-enhancement.md`,
`.github/aidd-config.yml`

This ticket set covers measured preview optimization informed by Lossless Cut
research, direct scroll-based focus controls, 2x/4x focus-bound verification,
matched mixed-FPS render-strategy comparison, the approved Strategy B
production-default follow-up, research-only restoration recommendations, and
the separately approved opt-in SuperUltraCompact production-upscale follow-up.
It does not vendor external code, add unapproved model families, or change
the first-horizon scope.

### Ticket summary

| Sequence | ID | Title | Parent feature | Dependencies | Status | Current path |
|---:|---|---|---|---|---|---|
| 61 | TICKET-061 | Research Lossless Cut preview architecture | FEAT-024 | current playback boundary; public source or limitation record | complete | `tickets/closed/TICKET-061-research-lossless-cut-preview-architecture.md` |
| 62 | TICKET-062 | Benchmark current preview latency | FEAT-024 | TICKET-061; representative media and trace | complete | `tickets/closed/TICKET-062-benchmark-current-preview-latency.md` |
| 63 | TICKET-063 | Experiment with preview rendering strategies | FEAT-024 | TICKET-061, TICKET-062 | complete | `tickets/closed/TICKET-063-experiment-with-preview-rendering-strategies.md` |
| 64 | TICKET-064 | Adopt and document responsive preview strategy | FEAT-024 | TICKET-063; regression and target-workstation evidence | complete | `tickets/closed/TICKET-064-adopt-and-document-responsive-preview-strategy.md` |
| 65 | TICKET-065 | Define direct focus modification interactions | FEAT-025 | PHASE-006 focus/triplicate semantics; GTK event behavior | complete | `tickets/closed/TICKET-065-define-direct-focus-modification-interactions.md` |
| 66 | TICKET-066 | Implement scroll-driven focus modifications | FEAT-025 | TICKET-065; existing focus model | complete | `tickets/closed/TICKET-066-implement-scroll-driven-focus-modifications.md` |
| 67 | TICKET-067 | Correct zoomed focus coordinate bounds | FEAT-025 | TICKET-065; fixed canvas and layout semantics | complete | `tickets/closed/TICKET-067-correct-zoomed-focus-coordinate-bounds.md` |
| 68 | TICKET-068 | Verify focus-control persistence and parity | FEAT-025 | TICKET-066, TICKET-067; project/CLI contracts | complete | `tickets/closed/TICKET-068-verify-focus-control-persistence-and-parity.md` |
| 69 | TICKET-069 | Define comparable mixed-FPS render benchmarks | FEAT-026 | PHASE-005/007 behavior; representative media | complete | `tickets/closed/TICKET-069-define-comparable-mixed-fps-render-benchmarks.md` |
| 70 | TICKET-070 | Benchmark concat-first enhancement strategy | FEAT-026 | TICKET-069; current safe route | complete | `tickets/closed/TICKET-070-benchmark-concat-first-enhancement-strategy.md` |
| 71 | TICKET-071 | Benchmark per-source enhancement strategy | FEAT-026 | TICKET-069; interpolation and concatenation path | complete | `tickets/closed/TICKET-071-benchmark-per-source-enhancement-strategy.md` |
| 72 | TICKET-072 | Select and document mixed-FPS render default | FEAT-026 | TICKET-070, TICKET-071; review and approval | complete | `tickets/closed/TICKET-072-select-and-document-mixed-fps-render-default.md` |
| 73 | TICKET-073 | Survey video upscaling, denoise, and compression recovery | FEAT-027 | public research; license/runtime constraints | complete | `tickets/closed/TICKET-073-survey-video-upscaling-denoise-and-compression-recovery.md` |
| 74 | TICKET-074 | Benchmark restoration candidates | FEAT-027 | TICKET-073; bounded samples and runtimes | complete | `tickets/closed/TICKET-074-benchmark-restoration-candidates.md` |
| 75 | TICKET-075 | Recommend restoration pipeline and gates | FEAT-027 | TICKET-073, TICKET-074 | complete | `tickets/closed/TICKET-075-recommend-restoration-pipeline-and-gates.md` |
| 76 | TICKET-076 | Adopt per-source render strategy as the enhanced default | FEAT-026 | TICKET-072; output and interpolation gates | complete | `tickets/closed/TICKET-076-adopt-per-source-render-strategy.md` |
| 77 | TICKET-077 | Benchmark REAL Video Enhancer restoration on degraded media | FEAT-027 | TICKET-073; supplied media; available runtimes | complete | `tickets/closed/TICKET-077-benchmark-real-video-enhancer-restoration.md` |
| 78 | TICKET-078 | Expand cross-model restoration benchmark | FEAT-027 | TICKET-073, TICKET-077; pinned candidate runtimes and licenses | complete | `tickets/closed/TICKET-078-expand-cross-model-restoration-benchmark.md` |
| 79 | TICKET-079 | Implement optional upscale enhancement | FEAT-028 | TICKET-076; local RVE runtime and SuperUltraCompact weights | complete | `tickets/closed/TICKET-079-implement-optional-upscale-enhancement.md` |
| 80 | TICKET-080 | Benchmark upscale render strategies | FEAT-028 | TICKET-079; requested fixtures and target workstation | complete | `tickets/closed/TICKET-080-benchmark-upscale-render-strategies.md` |
| 81 | TICKET-081 | Restore editor loading, timeline zoom, and GPU interpolation | FEAT-028 | existing editor lifecycle; validated RVE runtime; representative local media | complete | `tickets/closed/TICKET-081-restore-editor-loading-zoom-and-gpu-interpolation.md` |
| 82 | TICKET-082 | Allow triplicate horizontal offset at default zoom | FEAT-025 | existing focus bounds; triplicate composition; persistence and CLI contracts | complete | `tickets/closed/TICKET-082-allow-triplicate-horizontal-offset-at-default-zoom.md` |

### Dependency order

`TICKET-061 -> TICKET-062 -> TICKET-063 -> TICKET-064`

`TICKET-065 -> TICKET-066 -> TICKET-067 -> TICKET-068 -> TICKET-082`

`TICKET-069 -> {TICKET-070, TICKET-071} -> TICKET-072 -> TICKET-076`

`TICKET-073 -> TICKET-074 -> TICKET-075`

`TICKET-073 -> TICKET-077 -> TICKET-078 -> restoration evidence assimilation`

`TICKET-076 -> TICKET-079 -> TICKET-080`

`TICKET-079 -> TICKET-081`

The preview work establishes an external research boundary and current
baseline before experiments and default adoption. The focus work defines
interaction ownership before implementation, then verifies zoom bounds and
GUI/CLI/persistence parity. The render comparison fixes a common protocol
before running either strategy and selecting a route. The restoration work
separates survey, measurement, and recommendation so no production model is
silently introduced.

### Feature coverage

| Feature outcome | Ticket coverage | Coverage status |
|---|---|---|
| Optimize cursor-driven preview | TICKET-061 through TICKET-064 | covered |
| Streamline segment focus modifications | TICKET-065 through TICKET-068, TICKET-082 | covered |
| Compare and adopt mixed-FPS render strategy | TICKET-069 through TICKET-072, TICKET-076 | covered |
| Research video restoration and upscaling | TICKET-073 through TICKET-075, TICKET-077 through TICKET-078 | covered |
| Add optional SuperUltraCompact upscale enhancement | TICKET-079 through TICKET-081 | covered |
| CAP-002 - Playing and navigating an edit timeline | TICKET-061 through TICKET-064 | covered |
| CAP-003 - Editing segments non-destructively | TICKET-065 through TICKET-068, TICKET-082 | covered |
| CAP-005 - Rendering fast, valid, and safe outputs | TICKET-061, TICKET-064, TICKET-069 through TICKET-081 | covered |
| CAP-009 - Applying reusable visual modifications | TICKET-065 through TICKET-068, TICKET-082 | covered |
| CAP-010 - Linking triplicate composition instances | TICKET-065 through TICKET-068, TICKET-082 | covered |
| CAP-011 - Enhancing frame rate to 60 FPS | TICKET-069 through TICKET-081 | covered |
| CAP-012 - Protecting media, state, and failure recovery | TICKET-061 through TICKET-082 | covered |

### Readiness and gates

- PHASE-008 is complete with FEAT-024 through FEAT-028 and TICKET-061 through
  TICKET-082 closed after the user's explicit manual-validation and closeout
  decision on 2026-08-28.
- Each execution ticket requires the configured baseline, preimplementation
  checklist, user approval, evidence, local quality, applicable real-system,
  static-analysis, and review gates.
- Network access, target-workstation media, model/runtime availability,
  licensing, and remote checks must be recorded explicitly when unavailable.
- TICKET-074 and TICKET-075 retain their original generic blocker history;
  concrete RVE and cross-model evidence is recorded by TICKET-077 and
  TICKET-078. Neither research ticket alters production routing. TICKET-076
  records the separately approved render-routing implementation, while
  TICKET-079 through TICKET-081 record the approved production-upscale
  follow-up and responsiveness corrections.

### Protected behavior

Existing one-source and mixed-source editing, fixed 1920x1080 output,
source-level audio decisions, project compatibility, interpolation, atomic
export, structured CLI errors, legacy scripts, and source preservation remain
protected throughout PHASE-008. The historical concat-first route remains
available as evidence and safe fallback behavior where required.

### Source references

- `vision.md`
- `docs/specs/project-scope.md`
- `docs/specs/capability-map.md`
- `docs/specs/future-product-direction.md`
- `docs/planning/phases/closed/PHASE-008-optimizing-responsive-preview-and-media-strategy.md`
- `docs/planning/features/closed/FEAT-024-optimizing-cursor-driven-preview.md`
- `docs/planning/features/closed/FEAT-025-streamlining-segment-focus-modifications.md`
- `docs/planning/features/closed/FEAT-026-comparing-mixed-fps-render-strategies.md`
- `docs/planning/features/closed/FEAT-027-researching-video-restoration-and-upscaling.md`
- `docs/planning/features/closed/FEAT-028-adding-optional-upscale-enhancement.md`
- `framestudio/app_playback.py`
- `framestudio/ffmpeg_playback.py`
- `framestudio/export_smart_render.py`
- `framestudio/export_interpolation.py`
- `FAST-CONCAT-RESEARCH.md`
- `FPS-ENHANCEMENT-RESEARCH.md`
- `docs/planning/reviews/CHG-008-add-production-upscale-enhancement.md`
- `.github/aidd-config.yml`
