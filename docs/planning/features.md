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
**Last updated:** 2026-08-27
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
delivery-policy outcome into features that are now complete and closed after
user validation and delivery review. The PHASE-006 section below decomposes the approved focus and composition
outcome into feature records that are now complete and closed after user
validation, review, and local delivery.
The PHASE-007 section below decomposes the completed 60 FPS outcome into
target-rate policy, export planning, validated interpolation, and safe
delivery feature records. TICKET-060 is a corrective implementation record
under FEAT-021 for the export-panel defaults, presentation, backend fallback,
and single-source enhanced smart-render boundary; it was closed with the
Phase 007 delivery set.
The PHASE-008 section below tracks responsive preview optimization, direct
focus controls, mixed-FPS render-strategy comparison, and restoration
research. FEAT-024 through FEAT-028 are complete and closed, including the
approved Strategy B production default, concrete restoration benchmarks,
optional upscale enhancement, editor responsiveness corrections, and
default-zoom triplicate offsets. Historical limitations remain recorded in
the linked evidence.
This file does not create implementation work or architecture decisions.

## Phase and scope boundary

PHASE-001 through PHASE-005 and PHASE-004A are complete and closed after
user-approved implementation and terminal local evidence. The first-horizon
boundary remains one source video per project for PHASE-001 through PHASE-003.
PHASE-004 delivered the approved mixed-source expansion and PHASE-006
completed the approved focus and triplicate composition work. FPS enhancement
was delivered through PHASE-007, whose feature breakdown and child records
are now complete and closed. PHASE-008 is also complete and closed after
FEAT-024 through FEAT-028 and TICKET-061 through TICKET-082 reached closure
under the user's explicit manual-validation decision on 2026-08-28.

## Feature summary

| ID | Outcome | Capability links | Dependencies | Status |
|---|---|---|---|---|
| FEAT-001 | Open a supported source as a non-destructive project | CAP-001, CAP-012 | PHASE-001 entry decisions; FFmpeg/ffprobe | complete |
| FEAT-002 | Control playback and navigate the source timeline | CAP-002, CAP-012 | FEAT-001; selected playback/runtime approach | complete |
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
| FEAT-002 | complete | OBJ-001, SCOPE-001, PHASE-001 | `features/closed/FEAT-002-controlling-playback-and-navigating-the-source-timeline.md` |
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
| FEAT-014 | complete | OBJ-001, SCOPE-001, PHASE-005 | `features/closed/FEAT-014-balancing-each-source-consistently.md` |
| FEAT-015 | complete | OBJ-001, SCOPE-001, PHASE-005 | `features/closed/FEAT-015-selecting-tested-delivery-routes.md` |
| FEAT-016 | complete | OBJ-001, SCOPE-001, PHASE-005 | `features/closed/FEAT-016-synchronizing-media-decisions-and-verification.md` |
| FEAT-017 | complete | OBJ-001, SCOPE-001, PHASE-006 | `features/closed/FEAT-017-editing-reusable-visual-focus-controls.md` |
| FEAT-018 | complete | OBJ-001, SCOPE-001, PHASE-006 | `features/closed/FEAT-018-creating-linked-triplicate-compositions.md` |
| FEAT-019 | complete | OBJ-001, SCOPE-001, PHASE-006 | `features/closed/FEAT-019-delivering-focused-compositions-safely.md` |
| FEAT-020 | complete | OBJ-001, SCOPE-001, PHASE-007 | `features/closed/FEAT-020-choosing-target-frame-rate-delivery.md` |
| FEAT-021 | complete | OBJ-001, SCOPE-001, PHASE-007 | `features/closed/FEAT-021-planning-export-destination-and-estimates.md` |
| FEAT-022 | complete | OBJ-001, SCOPE-001, PHASE-007 | `features/closed/FEAT-022-running-validated-motion-interpolation.md` |
| FEAT-023 | complete | OBJ-001, SCOPE-001, PHASE-007 | `features/closed/FEAT-023-verifying-safe-enhanced-delivery.md` |
| FEAT-024 | complete | OBJ-001, SCOPE-001, PHASE-008 | `features/closed/FEAT-024-optimizing-cursor-driven-preview.md` |
| FEAT-025 | complete | OBJ-001, SCOPE-001, PHASE-008 | `features/closed/FEAT-025-streamlining-segment-focus-modifications.md` |
| FEAT-026 | complete | OBJ-001, SCOPE-001, PHASE-008 | `features/closed/FEAT-026-comparing-mixed-fps-render-strategies.md` |
| FEAT-027 | complete | OBJ-001, SCOPE-001, PHASE-008 | `features/closed/FEAT-027-researching-video-restoration-and-upscaling.md` |
| FEAT-028 | complete | OBJ-001, SCOPE-001, PHASE-008 | `features/closed/FEAT-028-adding-optional-upscale-enhancement.md` |

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
closed after user approval on 2026-08-22. FEAT-002 and FEAT-014 through
FEAT-016 are also complete and closed after their corrective playback and
source-level audio delivery work passed user validation, review, and local
delivery. FEAT-017 through FEAT-019 are complete and closed after their user
validation, review, and local delivery evidence. FEAT-020 through FEAT-023
are complete and closed after the user confirmed the PHASE-007 ticket set was
approved, accepted, and tested; unavailable remote and target-specific checks
remain recorded as accepted warnings. This index does not own implementation,
branches, commits, or pull requests. Under PHASE-008, FEAT-024 through
FEAT-028 and TICKET-061 through TICKET-082 are complete and closed from their
linked evidence after the user's explicit manual-validation and closeout
decision on 2026-08-28. Historical generic blocker and environment
limitations remain recorded in the evidence records.

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
review, and user-validation gates. PHASE-005 is complete and closed with
FEAT-014 through FEAT-016 and TICKET-031 through TICKET-037.
PHASE-006 is complete and closed, and PHASE-007 is complete and closed with
FEAT-020 through FEAT-023 and their child tickets accepted as tested.

## PHASE-007 - Feature Decomposition

**Feature index ID:** FEAT-INDEX-007
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Phase:** PHASE-007
**Capability map:** CAP-MAP-001
**Status:** complete
**Closure:** user-approved on 2026-08-26 after FEAT-020 through FEAT-023 and
their child tickets were implemented, tested, reviewed, and accepted;
unavailable remote and target-specific checks remain recorded as accepted
warnings
**Approval:** user-authorized on 2026-08-24 to break down the confirmed
PHASE-007 outcome; completion was subsequently accepted by the user
**Owner:** repository planning; maintainer identity is not recorded
**Last updated:** 2026-08-27
**Source paths:** `vision.md`, `docs/specs/project-scope.md`,
`docs/specs/capability-map.md`,
`docs/specs/future-product-direction.md`,
`docs/planning/phases/closed/PHASE-007-producing-validated-60-fps-edits.md`,
`FPS-ENHANCEMENT-RESEARCH.md`, `docs/specs/cli-contract.md`,
`.github/aidd-config.yml`

### Phase boundary

PHASE-007 adds an opt-in, validated target-FPS export workflow. It includes
the user's requested destination page, collision-safe naming, explicit
lowest/highest/custom/60 FPS choices, enhancement toggle, and calibrated
processing estimate. It does not replace legacy scripts or claim universal
interpolation performance.

### Feature summary

| ID | Outcome | Capability links | Dependencies | Status |
|---|---|---|---|---|
| FEAT-020 | Choose target frame-rate delivery and enhancement scope | CAP-005, CAP-011, CAP-012 | PHASE-005; PHASE-006 timing and segment semantics | complete |
| FEAT-021 | Plan export destination, naming, and processing estimates | CAP-005, CAP-011, CAP-012 | FEAT-020; current export planner and progress metrics | complete |
| FEAT-022 | Run validated motion interpolation with timing and audio preservation | CAP-005, CAP-011, CAP-012 | FEAT-020; PHASE-005; FPS research and target runtime | complete |
| FEAT-023 | Verify and safely deliver enhanced or ordinary exports | CAP-005, CAP-006, CAP-011, CAP-012 | FEAT-020 through FEAT-022; existing project/CLI/export safety | complete |

### Capability coverage

| Phase capability | Feature coverage | Coverage status |
|---|---|---|
| CAP-005 - Rendering fast, valid, and safe outputs | FEAT-020, FEAT-021, FEAT-022, FEAT-023 | covered |
| CAP-006 - Automating the project through a deterministic CLI | FEAT-023 | covered |
| CAP-011 - Enhancing frame rate to 60 FPS | FEAT-020, FEAT-022, FEAT-023 | covered |
| CAP-012 - Protecting media, state, and failure recovery | FEAT-020 through FEAT-023 | covered |

### Dependency order

`FEAT-020 -> FEAT-021 -> FEAT-023`

`FEAT-020 -> FEAT-022 -> FEAT-023`

FEAT-020 settles target-rate and enhancement-scope semantics before the
destination, estimate, and interpolation work. FEAT-021 makes the export
decision reviewable before processing. FEAT-022 validates and runs the
motion-interpolation route. FEAT-023 connects the approved behavior to
reproducible GUI/CLI delivery and final safety gates.

### Planning readiness

FEAT-020 through FEAT-023 are complete and closed records with bounded
outcomes, scope boundaries, dependencies, risks, protected behaviors,
evidence paths, and terminal local/user acceptance. TICKET-048 through
TICKET-060 are closed under the same approved delivery record. Remote and
target-specific limitations remain explicitly recorded in the linked
evidence.

### Protected behavior

Existing one-source and mixed-source editing, source-level audio decisions,
fixed 1920x1080 output, project compatibility, atomic partial-output
publication, structured CLI errors, legacy scripts, and source preservation
remain protected throughout PHASE-007.

### Source references

- `vision.md`
- `docs/specs/project-scope.md`
- `docs/specs/capability-map.md`
- `docs/specs/future-product-direction.md`
- `docs/planning/phases/closed/PHASE-007-producing-validated-60-fps-edits.md`
- `FPS-ENHANCEMENT-RESEARCH.md`
- `FLOWFRAMES-RESEARCH.md`
- `framestudio_concat.py`
- `framestudio_fps.py`
- `.github/aidd-config.yml`

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
- FEAT-014 through FEAT-016 were added to `features/open/` on 2026-08-22
  under PHASE-005 and moved to `features/closed/` after user validation,
  review, and local delivery evidence.
- FEAT-020 through FEAT-023 were added to `features/open/` under PHASE-007
  and moved to `features/closed/` on 2026-08-26 after their child tickets
  were implemented, tested, reviewed, and accepted; unavailable remote and
  target-specific checks remain recorded as accepted warnings.
- FEAT-024 through FEAT-028 were added to `features/open/` under PHASE-008
  on 2026-08-26. They cover responsive preview measurement and adoption,
  direct focus controls, mixed-FPS render-strategy comparison, restoration
  research, and optional upscale enhancement. They were later moved to
  `features/closed/` after their child tickets and the phase were closed on
  2026-08-28.

## PHASE-005 - Feature Decomposition

**Feature index ID:** FEAT-INDEX-005
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Phase:** PHASE-005
**Capability map:** CAP-MAP-001
**Status:** complete
**Approval:** user-authorized on 2026-08-22 to implement and close the
approved feature and ticket set after validation
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
| FEAT-014 | Balance each input source consistently across its timeline | CAP-008, CAP-012 | PHASE-004A; approved audio policy | complete |
| FEAT-015 | Select tested delivery routes for audio-aware and mixed-source exports | CAP-005, CAP-012 | FEAT-014; fixed output policy | complete |
| FEAT-016 | Synchronize media decisions across product surfaces and verified output | CAP-005, CAP-008, CAP-012 | FEAT-014, FEAT-015 | complete |

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

FEAT-014 through FEAT-016 are complete and closed under the approved PHASE-005
record. TICKET-031 through TICKET-037 have terminal implementation,
automated, real-media, user-validation, review, and local delivery evidence.
Remote checks remain unavailable because no remote or upstream is configured.

## PHASE-006 - Feature Decomposition

**Feature index ID:** FEAT-INDEX-006
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Phase:** PHASE-006
**Capability map:** CAP-MAP-001
**Status:** complete
**Approval:** user-authorized on 2026-08-22 to break down and implement the
approved phase; user validation, review, and local delivery are complete
**Owner:** repository planning; maintainer identity is not recorded
**Last updated:** 2026-08-22
**Source paths:** `vision.md`, `docs/specs/project-scope.md`,
`docs/specs/capability-map.md`, `docs/specs/future-product-direction.md`,
`docs/planning/phases/open/PHASE-006-focusing-and-composing-important-action.md`,
`.github/aidd-config.yml`

### Phase boundary

PHASE-006 adds reusable segment-owned visual modifications and linked
triplicate portrait/focused-action composition. It depends on the completed
mixed-source, architecture, and source-level delivery foundations. It does
not include automatic FPS enhancement, arbitrary effects, or full
professional compositing.

### Feature summary

| ID | Outcome | Capability links | Dependencies | Status |
|---|---|---|---|---|
| FEAT-017 | Edit reusable visual focus controls on timeline segments | CAP-009, CAP-012 | PHASE-005; segment identity and selection semantics | complete |
| FEAT-018 | Create linked triplicate portrait and focused-action compositions | CAP-010, CAP-012 | FEAT-017; approved transform and group semantics | complete |
| FEAT-019 | Preview, persist, and safely deliver focused compositions | CAP-005, CAP-009, CAP-010, CAP-012 | FEAT-017, FEAT-018; fixed 1920x1080 output policy | complete |

### Capability coverage

| Phase capability | Feature coverage | Coverage status |
|---|---|---|
| CAP-005 - Rendering fast, valid, and safe outputs | FEAT-019 | covered |
| CAP-009 - Applying reusable segment visual modifications | FEAT-017, FEAT-019 | covered |
| CAP-010 - Linking triplicate composition instances | FEAT-018, FEAT-019 | covered |
| CAP-012 - Protecting media, state, and failure recovery | FEAT-017, FEAT-018, FEAT-019 | covered |

### Dependency order

`TICKET-038 -> TICKET-039 -> TICKET-040`

`TICKET-041 -> TICKET-042 -> TICKET-043`

`TICKET-038 + TICKET-040 + TICKET-043 -> TICKET-044`

`TICKET-044 -> TICKET-045 -> TICKET-046 -> TICKET-047`

FEAT-017 establishes the segment modification contract before linked
triplicate behavior. FEAT-018 then defines and implements independent linked
groups. FEAT-019 integrates persistence, CLI/GUI parity, safe rendering, and
end-to-end verification.

### Planning readiness

PHASE-006 is complete with bounded feature records and terminal
implementation, automated, real-media, user-validation, review, and local
delivery evidence for FEAT-017 through FEAT-019 and TICKET-038 through
TICKET-047. Remote checks remain unavailable because no remote or upstream is
configured.

## PHASE-008 - Feature Decomposition

**Feature index ID:** FEAT-INDEX-008
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Phase:** PHASE-008
**Capability map:** CAP-MAP-001
**Status:** complete
**Approval:** user-authorized on 2026-08-26 to break down the confirmed
PHASE-008 outcome into features and planned tickets; user-authorized manual
validation and closeout on 2026-08-28
**Owner:** repository planning; maintainer identity is not recorded
**Last updated:** 2026-08-28
**Source paths:** `vision.md`, `docs/specs/project-scope.md`,
`docs/specs/capability-map.md`, `docs/specs/future-product-direction.md`,
`docs/planning/phases/closed/PHASE-008-optimizing-responsive-preview-and-media-strategy.md`,
`framestudio/app_playback.py`, `framestudio/app_timeline_actions.py`,
`framestudio/export_smart_render.py`, `framestudio/export_interpolation.py`,
`README.md`,
`docs/planning/reviews/CHG-006-real-video-enhancer-restoration-benchmark.md`,
`docs/planning/reviews/CHG-007-expand-restoration-benchmark-matrix.md`,
`docs/planning/reviews/CHG-008-add-production-upscale-enhancement.md`,
`https://github.com/k4yt3x/video2x`, `.github/aidd-config.yml`

### Phase boundary

PHASE-008 improves feedback and decision quality around the existing editor.
It includes measured preview optimization, direct focus interactions, a
matched comparison of two mixed-FPS render strategies, the approved
per-source production-default follow-up, restoration research, and the
controlled SuperUltraCompact production-upscale follow-up approved under
CHG-008. TICKET-077 adds a concrete local benchmark, TICKET-078 expands that
research into a controlled cross-model matrix, and TICKET-079/TICKET-080
cover the optional production path, enabled by default for eligible sources
with an explicit opt-out; none changes the first-horizon scope or vendors
Lossless Cut.

### Feature summary

| ID | Outcome | Capability links | Dependencies | Status |
|---|---|---|---|---|
| FEAT-024 | Optimize cursor-driven preview | CAP-002, CAP-005, CAP-012 | PHASE-007 baseline; playback runtime; target-workstation benchmark | complete |
| FEAT-025 | Streamline segment focus modifications | CAP-003, CAP-009, CAP-010, CAP-012 | PHASE-006 focus/triplicate semantics; GUI and CLI contracts | complete |
| FEAT-026 | Compare and adopt mixed-FPS render strategy | CAP-005, CAP-011, CAP-012 | PHASE-005 delivery policy; PHASE-007 interpolation; representative media; TICKET-072 evidence | complete |
| FEAT-027 | Research video restoration and upscaling | CAP-005, CAP-011, CAP-012 | candidate research; supplied degraded media; license/runtime review | complete |
| FEAT-028 | Add optional SuperUltraCompact upscale enhancement | CAP-005, CAP-011, CAP-012 | TICKET-076; local RVE runtime and weights; fixed output and composition policy | complete |

### Capability coverage

| Phase capability | Feature coverage | Coverage status |
|---|---|---|
| CAP-002 - Playing and navigating an edit timeline | FEAT-024 | covered |
| CAP-003 - Editing segments non-destructively | FEAT-025 | covered |
| CAP-005 - Rendering fast, valid, and safe outputs | FEAT-024, FEAT-026, FEAT-027, FEAT-028 | covered |
| CAP-009 - Applying reusable visual modifications | FEAT-025 | covered |
| CAP-010 - Composing linked triplicate focused-action layouts | FEAT-025 | covered |
| CAP-011 - Enhancing frame rate to 60 FPS | FEAT-026, FEAT-027, FEAT-028 | covered |
| CAP-012 - Protecting media, state, and failure recovery | FEAT-024 through FEAT-028 | covered |

### Dependency order

`TICKET-061 -> TICKET-062 -> TICKET-063 -> TICKET-064`

`TICKET-065 -> TICKET-066 -> TICKET-067 -> TICKET-068 -> TICKET-082`

`TICKET-069 -> {TICKET-070, TICKET-071} -> TICKET-072 -> TICKET-076`

`TICKET-073 -> TICKET-074 -> TICKET-075`

`TICKET-073 -> TICKET-077 -> TICKET-078 -> restoration evidence assimilation`

FEAT-024 starts with external preview research and a current baseline before
experiments and default adoption. FEAT-025 defines the direct-control
contract before GUI implementation and coordinate/persistence verification.
FEAT-026 fixes comparable benchmark inputs before running either route and
making a routing decision, then implements the approved per-source default.
FEAT-027 separates survey, candidate measurement, and future pipeline
recommendation so restoration remains research-only. TICKET-077 is the
concrete benchmark route enabled by CHG-006, and TICKET-078 is the expanded
comparison route enabled by CHG-007; neither silently replaces the generic
blocked records.

### Planning readiness

PHASE-008 and FEAT-024 through FEAT-028 are complete and closed. TICKET-061
through TICKET-082 are complete and closed with their linked evidence after
the user's explicit manual-validation and closeout decision on 2026-08-28.
The generic restoration blocker history for TICKET-074 and TICKET-075 is
preserved, while concrete benchmark evidence is recorded by TICKET-077 and
TICKET-078. Remote, target-workstation, model-runtime, license, and other
environment limitations remain explicit.
Network, target-workstation, model-runtime, license, and remote limitations
remain explicit.

### Protected behavior

Existing one-source and mixed-source editing, fixed 1920x1080 output,
source-level audio decisions, project compatibility, atomic export,
structured CLI errors, legacy scripts, interpolation behavior, and source
preservation remain protected throughout PHASE-008.

### Source references

- `vision.md`
- `docs/specs/project-scope.md`
- `docs/specs/capability-map.md`
- `docs/specs/future-product-direction.md`
- `docs/planning/phases/closed/PHASE-008-optimizing-responsive-preview-and-media-strategy.md`
- `framestudio/app_playback.py`
- `framestudio/ffmpeg_playback.py`
- `framestudio/export_smart_render.py`
- `framestudio/export_interpolation.py`
- `FAST-CONCAT-RESEARCH.md`
- `FPS-ENHANCEMENT-RESEARCH.md`
- `.github/aidd-config.yml`
