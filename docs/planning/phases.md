# Delivery Phases

**Phase index ID:** PHASE-INDEX-001
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Capability map:** CAP-MAP-001
**Status:** confirmed
**Planning depth:** full
**Approval:** user-approved on 2026-08-21 before feature generation
**Owner:** repository planning; maintainer identity is not recorded
**Last updated:** 2026-08-21
**Repository revision:** working tree after approved lifecycle migration

## Purpose

This phase index sequences the approved editor objective, first-horizon scope,
and confirmed future direction into outcome-oriented delivery stages. It
defines boundaries and gates only. It does not create features, tickets, or
implementation work.

## Sequencing Rationale

1. Establish a trustworthy source/project/playback foundation before editing
   behavior depends on it.
2. Deliver the narrow one-source cut and export workflow as the first usable
   product.
3. Make the same basic workflow deterministic and agentable before expanding
   the media model.
4. Add mixed-source timeline behavior before source-level audio, composition,
   or frame-rate operations that depend on a stable sequence model.
5. Add audio and delivery policy once mixed inputs expose the real
   normalization and codec requirements.
6. Add reusable transforms and triplicate composition after the project can
   represent multiple sources, segments, selections, and output canvases.
7. Add 60 FPS enhancement after timing, audio, output, and optional segment
   scope are explicit and testable.

The first usable product is the combined outcome of PHASE-001 through
PHASE-003. PHASE-004 onward is future expansion and must not be pulled into
the first horizon without approved scope change.

## Phase Summary

| Sequence | ID | Outcome | Capability links | Dependencies | Status |
|---:|---|---|---|---|---|
| 1 | PHASE-001 | Open and resume a source edit | CAP-001, CAP-002, CAP-004, CAP-012 | Approved objective, scope, and capability map | confirmed |
| 2 | PHASE-002 | Cut and export one source safely | CAP-003, CAP-005, CAP-012 | PHASE-001 | confirmed |
| 3 | PHASE-003 | Repeat the basic edit through agents | CAP-004, CAP-006, CAP-012 | PHASE-001, PHASE-002 | confirmed |
| 4 | PHASE-004 | Combine mixed-source footage | CAP-002, CAP-003, CAP-005, CAP-007, CAP-012 | PHASE-001 through PHASE-003 | confirmed |
| 5 | PHASE-005 | Balance sources and deliver consistent media | CAP-005, CAP-008, CAP-012 | PHASE-004 | confirmed |
| 6 | PHASE-006 | Focus and compose important action | CAP-005, CAP-009, CAP-010, CAP-012 | PHASE-004, PHASE-005 | confirmed |
| 7 | PHASE-007 | Produce validated 60 FPS edits | CAP-005, CAP-011, CAP-012 | PHASE-004, PHASE-005; PHASE-006 if segment-scoped enhancement is approved | confirmed |

## Common Phase Rules

- A phase has one user-facing outcome and explicit entry and exit evidence.
- A phase cannot enter implementation when a required dependency, decision,
  command, or evidence path is unavailable; it becomes blocked instead.
- Existing scripts, tests, research, and source-safe behavior remain protected
  across every phase.
- Phase work must preserve the first-horizon boundary unless an approved
  scope change updates SCOPE-001.
- Features may be generated only after this index is approved and each feature
  is assigned to exactly one phase.
- Tickets may not be generated as a side effect of phase creation.

## Lifecycle Records

Each phase is maintained as an individual lifecycle record. Confirmed phases
are open; no phase records are currently closed.

| Sequence | ID | Status | Parent links | Current path |
|---:|---|---|---|---|
| 1 | PHASE-001 | confirmed | OBJ-001, SCOPE-001 | `phases/open/PHASE-001-opening-and-resuming-a-source-edit.md` |
| 2 | PHASE-002 | confirmed | OBJ-001, SCOPE-001 | `phases/open/PHASE-002-cutting-and-exporting-one-source-safely.md` |
| 3 | PHASE-003 | confirmed | OBJ-001, SCOPE-001 | `phases/open/PHASE-003-repeating-the-basic-edit-through-agents.md` |
| 4 | PHASE-004 | confirmed | OBJ-001, SCOPE-001 | `phases/open/PHASE-004-combining-mixed-source-footage.md` |
| 5 | PHASE-005 | confirmed | OBJ-001, SCOPE-001 | `phases/open/PHASE-005-balancing-sources-and-delivering-consistent-media.md` |
| 6 | PHASE-006 | confirmed | OBJ-001, SCOPE-001 | `phases/open/PHASE-006-focusing-and-composing-important-action.md` |
| 7 | PHASE-007 | confirmed | OBJ-001, SCOPE-001 | `phases/open/PHASE-007-producing-validated-60-fps-edits.md` |

## Capability Coverage

| Capability | Covered phases | First-horizon coverage | Future coverage |
|---|---|---|---|
| CAP-001 | PHASE-001 | Import/source inspection | Extended mixed-source identity in PHASE-004 |
| CAP-002 | PHASE-001, PHASE-004 | One-source playback and seek | Composed mixed-source preview |
| CAP-003 | PHASE-002, PHASE-004 | Split/delete | Movement, multi-selection, copy/paste, expanded segment model |
| CAP-004 | PHASE-001, PHASE-003 | Save/reopen | Future schema expansion |
| CAP-005 | PHASE-002, PHASE-004, PHASE-005, PHASE-006, PHASE-007 | Fast verified cut export | Composition, audio, mixed-source, and FPS delivery |
| CAP-006 | PHASE-003 | Basic agentable workflow | Future full editing command surface |
| CAP-007 | PHASE-004 | Not included | Multiple mixed-media sources |
| CAP-008 | PHASE-005 | Not included | Per-input audio handling |
| CAP-009 | PHASE-006 | Not included | Reusable transforms |
| CAP-010 | PHASE-006 | Not included | Linked triplicate composition |
| CAP-011 | PHASE-007 | Not included | Validated 60 FPS enhancement |
| CAP-012 | PHASE-001 through PHASE-007 | Source/project/output safety | Cross-cutting future safety |

## Phase Approval and Handoff

This phase index was approved before downstream planning. Its seven confirmed
phase records are now individual lifecycle files, and each feature record is
assigned to exactly one phase. Ticket execution remains governed by the
backlog and the open/closed ticket directories.

## Source References

- [`../../vision.md`](../../vision.md)
- [`../../docs/specs/project-scope.md`](../../docs/specs/project-scope.md)
- [`../../docs/specs/capability-map.md`](../../docs/specs/capability-map.md)
- [`../../docs/specs/future-product-direction.md`](../../docs/specs/future-product-direction.md)
- [`repo-map.md`](repo-map.md)
- [`../../FAST-CONCAT-RESEARCH.md`](../../FAST-CONCAT-RESEARCH.md)
- [`../../FLOWFRAMES-RESEARCH.md`](../../FLOWFRAMES-RESEARCH.md)
- [`../../FPS-ENHANCEMENT-RESEARCH.md`](../../FPS-ENHANCEMENT-RESEARCH.md)

## Migration Notes

- The seven inline phase records were extracted into
  `docs/planning/phases/open/` without changing their confirmed status.
- No phase record was eligible for `phases/closed/`; closed lifecycle
  directories remain available for future status transitions.
- The original phase-index metadata, sequencing rationale, common rules,
  capability coverage, handoff gate, and source references remain in this
  synchronized index.
