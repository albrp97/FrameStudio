# Delivery Features

**Feature index ID:** FEAT-INDEX-001
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Phase:** PHASE-001
**Capability map:** CAP-MAP-001
**Status:** confirmed
**Planning depth:** full
**Approval:** user-approved on 2026-08-21 before ticket generation
**Owner:** repository planning; maintainer identity is not recorded
**Source paths:** `vision.md`, `docs/specs/project-scope.md`,
`docs/specs/capability-map.md`, `docs/planning/phases.md`,
`docs/specs/future-product-direction.md`, `.github/aidd-config.yml`
**Last updated:** 2026-08-22
**Repository revision:** working tree after user-approved phase planning

## Purpose

The PHASE-001 section decomposes the first one-source editor foundation into
independently understandable user outcomes: opening a source, controlling
playback, and saving/reopening the project. The PHASE-002 and PHASE-003
sections below extend the same authoritative feature index with approved
one-source cutting, verified export, and deterministic agent/CLI outcomes.
The PHASE-004 section starts the approved mixed-source expansion with
atomic segment-block movement and copy/paste without pulling in later audio
normalization, visual-modification authoring, triplicate composition, or FPS
work. The PHASE-004A section adds the approved architecture-stabilization
feature that must complete before those future product phases.
The PHASE-005 section decomposes the approved source-level audio and
delivery-policy outcome into features whose implementation is complete and
awaiting user validation and delivery review. This file does not create
implementation work or architecture decisions.

## Phase and scope boundary

PHASE-002 through PHASE-004 are complete and closed after user-approved
implementation. PHASE-001 is verifying again for a timeline playback pacing
correction. The first-horizon boundary remains one source video per project
for PHASE-001 through PHASE-003. PHASE-004 delivered the approved
mixed-source expansion; triplicate composition and FPS enhancement remain
assigned to future phases. PHASE-005 is verifying;
PHASE-006 and PHASE-007 remain confirmed future phases.

## Feature summary

| ID | Outcome | Capability links | Dependencies | Status |
|---|---|---|---|---|
| FEAT-001 | Open a supported source as a non-destructive project | CAP-001, CAP-012 | PHASE-001 entry decisions; FFmpeg/ffprobe | complete |
| FEAT-002 | Control playback and navigate the source timeline | CAP-002, CAP-012 | FEAT-001; selected playback/runtime approach | verifying |
| FEAT-003 | Save and reopen the source edit foundation | CAP-004, CAP-012 | FEAT-001; initial project schema and relinking policy | complete |

## Capability coverage

| Phase capability | Feature coverage | Coverage status |
|---|---|---|
| CAP-001 — Managing projects and source media | FEAT-001 | covered |
| CAP-002 — Playing and navigating an edit timeline | FEAT-002 | covered |
| CAP-004 — Persisting and reopening edit state | FEAT-003 | covered |
| CAP-012 — Protecting media, state, and failure recovery | FEAT-001, FEAT-002, FEAT-003 | covered |

## Lifecycle Records

Each feature is maintained as an individual lifecycle record. Completed
features are closed; future feature work remains open in its assigned phase.

| ID | Status | Parent links | Current path |
|---|---|---|---|
| FEAT-001 | complete | OBJ-001, SCOPE-001, PHASE-001 | `features/closed/FEAT-001-opening-a-supported-source-as-a-non-destructive-project.md` |
| FEAT-002 | verifying | OBJ-001, SCOPE-001, PHASE-001 | `features/open/FEAT-002-controlling-playback-and-navigating-the-source-timeline.md` |
| FEAT-003 | complete | OBJ-001, SCOPE-001, PHASE-001 | `features/closed/FEAT-003-saving-and-reopening-the-source-edit-foundation.md` |
| FEAT-004 | complete | OBJ-001, SCOPE-001, PHASE-002 | `features/closed/FEAT-004-removing-unwanted-portions-from-one-source.md` |
| FEAT-005 | complete | OBJ-001, SCOPE-001, PHASE-002 | `features/closed/FEAT-005-exporting-a-verified-edited-video.md` |
| FEAT-006 | complete | OBJ-001, SCOPE-001, PHASE-002 | `features/closed/FEAT-006-preserving-and-recovering-saved-cut-decisions.md` |
| FEAT-007 | complete | OBJ-001, SCOPE-001, PHASE-003 | `features/closed/FEAT-007-inspecting-projects-through-a-deterministic-cli.md` |
| FEAT-008 | complete | OBJ-001, SCOPE-001, PHASE-003 | `features/closed/FEAT-008-applying-one-source-edits-through-cli.md` |
| FEAT-009 | complete | OBJ-001, SCOPE-001, PHASE-003 | `features/closed/FEAT-009-sharing-domain-behavior-between-gui-and-cli.md` |
| FEAT-010 | complete | OBJ-001, SCOPE-001, PHASE-004 | `features/closed/FEAT-010-importing-and-retaining-mixed-source-project-identity.md` |
| FEAT-011 | complete | OBJ-001, SCOPE-001, PHASE-004 | `features/closed/FEAT-011-arranging-and-editing-a-mixed-source-timeline.md` |
| FEAT-012 | complete | OBJ-001, SCOPE-001, PHASE-004 | `features/closed/FEAT-012-previewing-and-exporting-mixed-source-edits.md` |
| FEAT-013 | complete | OBJ-001, SCOPE-001, PHASE-004A | `features/closed/FEAT-013-modular-editor-architecture.md` |
| FEAT-014 | verifying | OBJ-001, SCOPE-001, PHASE-005 | `features/open/FEAT-014-balancing-each-source-consistently.md` |
| FEAT-015 | verifying | OBJ-001, SCOPE-001, PHASE-005 | `features/open/FEAT-015-selecting-tested-delivery-routes.md` |
| FEAT-016 | verifying | OBJ-001, SCOPE-001, PHASE-005 | `features/open/FEAT-016-synchronizing-media-decisions-and-verification.md` |

## Open decisions carried into feature readiness

These decisions are PHASE-001 entry conditions and are not silently resolved
by this feature index:

- GUI/runtime and packaging approach.
- Playback backend and seeking/timing limitations.
- Versioned project schema and source relinking behavior.
- Practical target-workstation GUI/manual-test harness.

## Approval and downstream gate

This feature index is approved for the phase plan. FEAT-001 and FEAT-003
through FEAT-012 are individual lifecycle files that remain complete and
closed after user approval on 2026-08-22. FEAT-002 is verifying again because
its playback ticket was reopened for a timeline pacing correction. FEAT-014
through FEAT-016 are verifying under PHASE-005; their ticket implementation is
recorded in the per-ticket evidence files. User validation, review, and
delivery operations remain governed by the backlog. This index does not own
implementation, branches, commits, or pull requests.

## PHASE-002 - Feature Decomposition

**Feature index ID:** FEAT-INDEX-002  
**Objective:** OBJ-001  
**Scope:** SCOPE-001  
**Phase:** PHASE-002  
**Capability map:** CAP-MAP-001  
**Status:** confirmed  
**Approval:** user-approved on 2026-08-21 before ticket generation  
**Owner:** repository planning; maintainer identity is not recorded  
**Last updated:** 2026-08-21  
**Source paths:** `vision.md`, `docs/specs/project-scope.md`,
`docs/specs/capability-map.md`, `docs/planning/phases.md`,
`docs/specs/editor-foundation-decision.md`,
`docs/planning/features.md`, `.github/aidd-config.yml`

### Phase boundary

PHASE-002 remains limited to one source video per project. It adds
non-destructive split/delete editing and verified export. Multiple source
timelines, mixed-media normalization, triplicate composition, automatic audio
normalization, FPS enhancement, and deterministic CLI operations remain
outside this phase.

### Feature summary

| ID | Outcome | Capability links | Dependencies | Status |
|---|---|---|---|---|
| FEAT-004 | Remove unwanted portions and reorder blocks in one source non-destructively | CAP-003, CAP-012 | PHASE-001 project model; approved cut semantics | complete |
| FEAT-005 | Export a verified edited video through the fastest valid path | CAP-005, CAP-012 | FEAT-004; approved export/fallback policy | complete |
| FEAT-006 | Preserve and recover saved cut decisions safely | CAP-004, CAP-012 | FEAT-004; PHASE-001 persistence boundary | complete |

### Approval and downstream gate

This PHASE-002 feature set is complete and closed after user approval on
2026-08-22. No implementation work is created by this feature record.

## PHASE-003 - Feature Decomposition

**Feature index ID:** FEAT-INDEX-003  
**Objective:** OBJ-001  
**Scope:** SCOPE-001  
**Phase:** PHASE-003  
**Capability map:** CAP-MAP-001  
**Status:** confirmed  
**Approval:** user-approved on 2026-08-21 to close TICKET-011 and continue
with PHASE-003 planning  
**Owner:** repository planning; maintainer identity is not recorded  
**Last updated:** 2026-08-21  
**Source paths:** `vision.md`, `docs/specs/project-scope.md`,
`docs/specs/capability-map.md`, `docs/planning/phases.md`,
`docs/planning/phases/open/PHASE-003-repeating-the-basic-edit-through-agents.md`,
`docs/specs/future-product-direction.md`, `.github/aidd-config.yml`

### Phase boundary

PHASE-003 keeps the first-horizon one-source project and exposes its existing
split/delete/save/reopen/duration/export behavior to deterministic local
automation. It does not expand into multiple sources, composition, audio
normalization, FPS enhancement, cloud services, or natural-language agent
orchestration.

### Feature summary

| ID | Outcome | Capability links | Dependencies | Status |
|---|---|---|---|---|
| FEAT-007 | Inspect projects through a deterministic CLI | CAP-004, CAP-006, CAP-012 | PHASE-001/PHASE-002 project state; CLI contract decision | complete |
| FEAT-008 | Apply one-source edits through the CLI | CAP-004, CAP-006, CAP-012 | FEAT-007; completed safe export boundary | complete |
| FEAT-009 | Share domain behavior between GUI and CLI | CAP-004, CAP-006, CAP-012 | FEAT-007, FEAT-008; stable domain services | complete |

### Capability coverage

| Phase capability | Feature coverage | Coverage status |
|---|---|---|
| CAP-004 - Persisting and reopening edit state | FEAT-007, FEAT-008, FEAT-009 | covered |
| CAP-006 - Automating the project through a deterministic CLI | FEAT-007, FEAT-008, FEAT-009 | covered |
| CAP-012 - Protecting media, state, and failure recovery | FEAT-007, FEAT-008, FEAT-009 | covered |

### Approval and downstream gate

This PHASE-003 feature set is complete and closed after user approval on
2026-08-22. Its ticket records remain complete in `closed`; implementation
evidence and closure approval remain recorded with each ticket.

## PHASE-004 - Feature Decomposition

**Feature index ID:** FEAT-INDEX-004
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Phase:** PHASE-004
**Capability map:** CAP-MAP-001
**Status:** confirmed
**Approval:** user-authorized on 2026-08-21 to continue with the next-phase
mixed-source ticket planning
**Owner:** repository planning; maintainer identity is not recorded
**Last updated:** 2026-08-21
**Source paths:** `vision.md`, `docs/specs/project-scope.md`,
`docs/specs/capability-map.md`, `docs/planning/phases.md`,
`docs/planning/phases/open/PHASE-004-combining-mixed-source-footage.md`,
`docs/specs/future-product-direction.md`, `.github/aidd-config.yml`

### Phase boundary

PHASE-004 adds multiple source identities, a composed sequence model, mixed
timeline placement, atomic segment-block selection/movement/copy/paste,
source boundaries, a fixed 1920x1080 render canvas, and verified
preview/export behavior. It does not add automatic per-input audio
normalization, visual-modification authoring or clean/reset controls,
triplicate composition, or 60 FPS enhancement; those remain in PHASE-005
through PHASE-007.

### Feature summary

| ID | Outcome | Capability links | Dependencies | Status |
|---|---|---|---|---|
| FEAT-010 | Import and retain mixed-source project identity | CAP-007, CAP-012 | PHASE-003 project identity; mixed-media probing | complete |
| FEAT-011 | Arrange and edit a mixed-source timeline | CAP-002, CAP-003, CAP-007, CAP-012 | FEAT-010; approved timebase, placement, and atomic block semantics | complete |
| FEAT-012 | Preview and export mixed-source edits | CAP-002, CAP-005, CAP-007, CAP-012 | FEAT-010, FEAT-011; approved output policy | complete |

### Capability coverage

| Phase capability | Feature coverage | Coverage status |
|---|---|---|
| CAP-002 - Playing and navigating an edit timeline | FEAT-011, FEAT-012 | covered |
| CAP-003 - Editing segments non-destructively | FEAT-011 | covered |
| CAP-005 - Rendering fast, valid, and safe outputs | FEAT-012 | covered |
| CAP-007 - Supporting multiple mixed-media sources | FEAT-010, FEAT-011, FEAT-012 | covered |
| CAP-012 - Protecting media, state, and failure recovery | FEAT-010, FEAT-011, FEAT-012 | covered |

### Approval and downstream gate

The parent PHASE-004 record is complete and closed after user approval on
2026-08-22. CHG-001 records the later user-authorized clarification that
segment blocks are atomic and support structural copy/paste in this phase,
while visual modification authoring and reset remain assigned to PHASE-006.
CHG-002 records the fixed 1920x1080 project render profile, including
one-source outputs, and the deferral of 60 FPS enhancement. The Phase 4
tickets and features are complete in `closed`; remote checks remain
unavailable and are recorded as an accepted warning.

## PHASE-004A - Feature Decomposition

**Feature index ID:** FEAT-INDEX-004A
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Phase:** PHASE-004A
**Capability map:** CAP-MAP-001
**Status:** complete
**Approval:** user-authorized on 2026-08-22 before implementation
**Owner:** repository planning and implementation in the active worktree
**Last updated:** 2026-08-22
**Source paths:** `docs/planning/reviews/CHG-003-editor-architecture-stabilization.md`,
`docs/planning/phases/open/PHASE-004A-stabilizing-editor-architecture.md`,
`docs/planning/repo-map.md`, `.github/aidd-config.yml`

### Phase boundary

PHASE-004A is a maintainability prerequisite, not a product-capability
expansion. It separates the existing domain, media, playback, UI, timeline,
and CLI responsibilities while preserving the approved behavior delivered by
PHASE-001 through PHASE-004.

### Feature summary

| ID | Outcome | Capability links | Dependencies | Status |
|---|---|---|---|---|
| FEAT-013 | Maintain a modular editor architecture with stable public facades | CAP-012 | PHASE-004; TICKET-027; protected baseline | complete |

### Capability coverage

| Phase capability | Feature coverage | Coverage status |
|---|---|---|
| CAP-012 - Protecting media, state, and failure recovery | FEAT-013 | covered |

### Approval and downstream gate

FEAT-013 is complete and closed after TICKET-030 passed regression, quality,
review, and user-validation gates. PHASE-005 is verifying with FEAT-014 through
FEAT-016 and TICKET-031 through TICKET-037 implemented and awaiting user
validation.
PHASE-006 and PHASE-007 remain confirmed future phases.

## Source references

- `vision.md`
- `docs/specs/project-scope.md`
- `docs/specs/capability-map.md`
- `docs/planning/phases.md`
- `docs/specs/future-product-direction.md`
- `.github/aidd-config.yml`

## Migration Notes

- `FEAT-INDEX-001` and `FEAT-INDEX-002` remain preserved as index metadata
  sections; they are not additional feature records.
- The feature records were extracted into `features/open/` during the initial
  migration with stable IDs, parent links, status, scope boundaries, and
  evidence plans preserved.
- FEAT-001 through FEAT-012 later transitioned to `complete` and moved to
  `features/closed/` on 2026-08-22 after user approval.
- FEAT-013 was added to `features/open/` on 2026-08-22 under PHASE-004A as the
  architecture-stabilization prerequisite and moved to
  `features/closed/` after user validation on 2026-08-22.

## PHASE-005 - Feature Decomposition

**Feature index ID:** FEAT-INDEX-005
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Phase:** PHASE-005
**Capability map:** CAP-MAP-001
**Status:** verifying
**Approval:** user-authorized on 2026-08-22 to implement the approved feature
and ticket set; user validation is pending
**Owner:** repository planning and implementation in the active worktree
**Last updated:** 2026-08-22
**Source paths:** `vision.md`, `docs/specs/project-scope.md`,
`docs/specs/capability-map.md`,
`docs/specs/future-product-direction.md`,
`docs/planning/phases/open/PHASE-005-balancing-sources-and-delivering-consistent-media.md`,
`.github/aidd-config.yml`

### Phase boundary

PHASE-005 covers source-level audio decisions and tested delivery policy for
mixed-source edits. It does not include visual transforms, triplicate
composition, or 60 FPS enhancement.

### Feature summary

| ID | Outcome | Capability links | Dependencies | Status |
|---|---|---|---|---|
| FEAT-014 | Balance each input source consistently across its timeline | CAP-008, CAP-012 | PHASE-004A; approved audio policy | verifying |
| FEAT-015 | Select tested delivery routes for audio-aware and mixed-source exports | CAP-005, CAP-012 | FEAT-014; fixed output policy | verifying |
| FEAT-016 | Synchronize media decisions across product surfaces and verified output | CAP-005, CAP-008, CAP-012 | FEAT-014, FEAT-015 | verifying |

### Capability coverage

| Phase capability | Feature coverage | Coverage status |
|---|---|---|
| CAP-005 - Rendering fast, valid, and safe outputs | FEAT-015, FEAT-016 | covered |
| CAP-008 - Handling audio per source input | FEAT-014, FEAT-016 | covered |
| CAP-012 - Protecting media, state, and failure recovery | FEAT-014, FEAT-015, FEAT-016 | covered |

### Dependency order

`TICKET-031 -> TICKET-032 -> TICKET-033`

`TICKET-031 -> TICKET-034 -> TICKET-035`

`TICKET-032 + TICKET-034 + TICKET-035 -> TICKET-036`

`TICKET-033 + TICKET-035 + TICKET-036 -> TICKET-037`

TICKET-031 is the recommended first implementation ticket because its
approved policy is required by source analysis and delivery benchmarking.

### Planning readiness

FEAT-014 through FEAT-016 are verifying under the approved PHASE-005 record.
TICKET-031 through TICKET-037 have implemented their observable requirements
and have evidence records covering automated and real-media checks. User
validation and delivery review remain required before closure.
