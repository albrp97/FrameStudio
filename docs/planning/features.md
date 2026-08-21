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
**Last updated:** 2026-08-21
**Repository revision:** working tree after user-approved phase planning

## Purpose

The PHASE-001 section decomposes the first one-source editor foundation into
independently understandable user outcomes: opening a source, controlling
playback, and saving/reopening the project. The PHASE-002 and PHASE-003
sections below extend the same authoritative feature index with approved
one-source cutting, verified export, and deterministic agent/CLI outcomes.
This file does not create implementation work or architecture decisions.

## Phase and scope boundary

PHASE-001 is confirmed and was the active phase for its child planning. The
first-horizon boundary remains one source video per project. PHASE-002 and
PHASE-003 are confirmed in the sections below; mixed sources, audio
normalization, triplicate composition, and FPS enhancement remain assigned to
their later phases.

## Feature summary

| ID | Outcome | Capability links | Dependencies | Status |
|---|---|---|---|---|
| FEAT-001 | Open a supported source as a non-destructive project | CAP-001, CAP-012 | PHASE-001 entry decisions; FFmpeg/ffprobe | confirmed |
| FEAT-002 | Control playback and navigate the source timeline | CAP-002, CAP-012 | FEAT-001; selected playback/runtime approach | confirmed |
| FEAT-003 | Save and reopen the source edit foundation | CAP-004, CAP-012 | FEAT-001; initial project schema and relinking policy | confirmed |

## Capability coverage

| Phase capability | Feature coverage | Coverage status |
|---|---|---|
| CAP-001 — Managing projects and source media | FEAT-001 | covered |
| CAP-002 — Playing and navigating an edit timeline | FEAT-002 | covered |
| CAP-004 — Persisting and reopening edit state | FEAT-003 | covered |
| CAP-012 — Protecting media, state, and failure recovery | FEAT-001, FEAT-002, FEAT-003 | covered |

## Lifecycle Records

Each feature is maintained as an individual lifecycle record. Confirmed
features are open; no feature records are currently closed.

| ID | Status | Parent links | Current path |
|---|---|---|---|
| FEAT-001 | confirmed | OBJ-001, SCOPE-001, PHASE-001 | `features/open/FEAT-001-opening-a-supported-source-as-a-non-destructive-project.md` |
| FEAT-002 | confirmed | OBJ-001, SCOPE-001, PHASE-001 | `features/open/FEAT-002-controlling-playback-and-navigating-the-source-timeline.md` |
| FEAT-003 | confirmed | OBJ-001, SCOPE-001, PHASE-001 | `features/open/FEAT-003-saving-and-reopening-the-source-edit-foundation.md` |
| FEAT-004 | confirmed | OBJ-001, SCOPE-001, PHASE-002 | `features/open/FEAT-004-removing-unwanted-portions-from-one-source.md` |
| FEAT-005 | confirmed | OBJ-001, SCOPE-001, PHASE-002 | `features/open/FEAT-005-exporting-a-verified-edited-video.md` |
| FEAT-006 | confirmed | OBJ-001, SCOPE-001, PHASE-002 | `features/open/FEAT-006-preserving-and-recovering-saved-cut-decisions.md` |
| FEAT-007 | confirmed | OBJ-001, SCOPE-001, PHASE-003 | `features/open/FEAT-007-inspecting-projects-through-a-deterministic-cli.md` |
| FEAT-008 | confirmed | OBJ-001, SCOPE-001, PHASE-003 | `features/open/FEAT-008-applying-one-source-edits-through-cli.md` |
| FEAT-009 | confirmed | OBJ-001, SCOPE-001, PHASE-003 | `features/open/FEAT-009-sharing-domain-behavior-between-gui-and-cli.md` |

## Open decisions carried into feature readiness

These decisions are PHASE-001 entry conditions and are not silently resolved
by this feature index:

- GUI/runtime and packaging approach.
- Playback backend and seeking/timing limitations.
- Versioned project schema and source relinking behavior.
- Practical target-workstation GUI/manual-test harness.

## Approval and downstream gate

This feature index is approved for the confirmed PHASE-001. Its three
PHASE-001 features and three PHASE-002 features are now individual lifecycle
files. Ticket planning and execution remain governed by the backlog; this
index does not own implementation, branches, commits, or pull requests.

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
| FEAT-004 | Remove unwanted portions from one source non-destructively | CAP-003, CAP-012 | PHASE-001 project model; approved cut semantics | confirmed |
| FEAT-005 | Export a verified edited video through the fastest valid path | CAP-005, CAP-012 | FEAT-004; approved export/fallback policy | confirmed |
| FEAT-006 | Preserve and recover saved cut decisions safely | CAP-004, CAP-012 | FEAT-004; PHASE-001 persistence boundary | confirmed |

### Approval and downstream gate

This PHASE-002 feature proposal is user-approved. Ticket execution still
requires approval of the ticket set and the cut/export entry decisions.
No implementation work is created by this feature record.

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
| FEAT-007 | Inspect projects through a deterministic CLI | CAP-004, CAP-006, CAP-012 | PHASE-001/PHASE-002 project state; CLI contract decision | confirmed |
| FEAT-008 | Apply one-source edits through the CLI | CAP-004, CAP-006, CAP-012 | FEAT-007; completed safe export boundary | confirmed |
| FEAT-009 | Share domain behavior between GUI and CLI | CAP-004, CAP-006, CAP-012 | FEAT-007, FEAT-008; stable domain services | confirmed |

### Capability coverage

| Phase capability | Feature coverage | Coverage status |
|---|---|---|
| CAP-004 - Persisting and reopening edit state | FEAT-007, FEAT-008, FEAT-009 | covered |
| CAP-006 - Automating the project through a deterministic CLI | FEAT-007, FEAT-008, FEAT-009 | covered |
| CAP-012 - Protecting media, state, and failure recovery | FEAT-007, FEAT-008, FEAT-009 | covered |

### Approval and downstream gate

This PHASE-003 feature set is confirmed by the user's request to continue
planning after closing TICKET-011. Ticket records are created in `open` for
review and dependency planning; implementation still requires the configured
preimplementation checks and execution approval.

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
- The six inline feature records were extracted into `features/open/` with
  their stable IDs, parent links, status, scope boundaries, and evidence
  plans preserved.
- FEAT-007 through FEAT-009 were added as new PHASE-003 feature records in
  `features/open/` with stable IDs, parent links, scope boundaries, and
  evidence plans.
- No feature record was eligible for `features/closed/`; closed lifecycle
  directories remain available for future status transitions.
