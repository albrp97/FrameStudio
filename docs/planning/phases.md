# Delivery Phases

**Phase index ID:** PHASE-INDEX-001
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Capability map:** CAP-MAP-001
**Status:** confirmed
**Planning depth:** full
**Approval:** user-approved on 2026-08-21 before feature generation
**Owner:** repository planning; maintainer identity is not recorded
**Last updated:** 2026-08-27
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
5. Stabilize the editor architecture before expanding the product into
   source-level audio, composition, or frame-rate operations.
6. Add audio and delivery policy once mixed inputs expose the real
   normalization and codec requirements.
7. Add reusable transforms and triplicate composition after the project can
   represent multiple sources, segments, selections, and output canvases.
8. Add 60 FPS enhancement after timing, audio, output, and optional segment
   scope are explicit and testable.
9. Optimize interactive preview and validate future media-processing choices
   with measured target-workstation evidence before changing defaults.

The first usable product is the combined outcome of PHASE-001 through
PHASE-003. PHASE-004 onward is future expansion and must not be pulled into
the first horizon without approved scope change.

## Phase Summary

| Sequence | ID | Outcome | Capability links | Dependencies | Status |
|---:|---|---|---|---|---|
| 1 | PHASE-001 | Open and resume a source edit | CAP-001, CAP-002, CAP-004, CAP-012 | Approved objective, scope, and capability map | complete |
| 2 | PHASE-002 | Cut and export one source safely | CAP-003, CAP-005, CAP-012 | PHASE-001 | complete |
| 3 | PHASE-003 | Repeat the basic edit through agents | CAP-004, CAP-006, CAP-012 | PHASE-001, PHASE-002 | complete |
| 4 | PHASE-004 | Combine mixed-source footage | CAP-002, CAP-003, CAP-005, CAP-007, CAP-012 | PHASE-001 through PHASE-003 | complete |
| 4.5 | PHASE-004A | Stabilize editor architecture for future phases | CAP-012 | PHASE-004 | complete |
| 5 | PHASE-005 | Balance sources and deliver consistent media | CAP-005, CAP-008, CAP-012 | PHASE-004A | complete |
| 6 | PHASE-006 | Focus and compose important action | CAP-005, CAP-009, CAP-010, CAP-012 | PHASE-004A, PHASE-005 | complete |
| 7 | PHASE-007 | Produce validated 60 FPS edits | CAP-005, CAP-011, CAP-012 | PHASE-004A, PHASE-005; PHASE-006 if segment-scoped enhancement is approved | complete |
| 8 | PHASE-008 | Optimize responsive preview and select evidence-based media strategies | CAP-002, CAP-005, CAP-009, CAP-011, CAP-012 | PHASE-006, PHASE-007; target-workstation media and benchmark evidence | complete |

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

Each phase is maintained as an individual lifecycle record. Completed phases
are closed; confirmed future phases remain open.

| Sequence | ID | Status | Parent links | Current path |
|---:|---|---|---|---|
| 1 | PHASE-001 | complete | OBJ-001, SCOPE-001 | `phases/closed/PHASE-001-opening-and-resuming-a-source-edit.md` |
| 2 | PHASE-002 | complete | OBJ-001, SCOPE-001 | `phases/closed/PHASE-002-cutting-and-exporting-one-source-safely.md` |
| 3 | PHASE-003 | complete | OBJ-001, SCOPE-001 | `phases/closed/PHASE-003-repeating-the-basic-edit-through-agents.md` |
| 4 | PHASE-004 | complete | OBJ-001, SCOPE-001 | `phases/closed/PHASE-004-combining-mixed-source-footage.md` |
| 4.5 | PHASE-004A | complete | OBJ-001, SCOPE-001 | `phases/closed/PHASE-004A-stabilizing-editor-architecture.md` |
| 6 | PHASE-005 | complete | OBJ-001, SCOPE-001 | `phases/closed/PHASE-005-balancing-sources-and-delivering-consistent-media.md` |
| 7 | PHASE-006 | complete | OBJ-001, SCOPE-001 | `phases/closed/PHASE-006-focusing-and-composing-important-action.md` |
| 8 | PHASE-007 | complete | OBJ-001, SCOPE-001 | `phases/closed/PHASE-007-producing-validated-60-fps-edits.md` |
| 9 | PHASE-008 | complete | OBJ-001, SCOPE-001 | `phases/closed/PHASE-008-optimizing-responsive-preview-and-media-strategy.md` |

## Capability Coverage

| Capability | Covered phases | First-horizon coverage | Future coverage |
|---|---|---|---|
| CAP-001 | PHASE-001 | Import/source inspection | Extended mixed-source identity in PHASE-004 |
| CAP-002 | PHASE-001, PHASE-004, PHASE-008 | One-source playback and seek | Composed mixed-source preview and responsive cursor-driven preview |
| CAP-003 | PHASE-002, PHASE-004 | Split/delete | Movement, multi-selection, copy/paste, expanded segment model |
| CAP-004 | PHASE-001, PHASE-003 | Save/reopen | Future schema expansion |
| CAP-005 | PHASE-002, PHASE-004, PHASE-005, PHASE-006, PHASE-007, PHASE-008 | Fast verified cut export | Composition, audio, mixed-source, FPS delivery, and measured rendering strategies |
| CAP-006 | PHASE-003 | Basic agentable workflow | Future full editing command surface |
| CAP-007 | PHASE-004 | Not included | Multiple mixed-media sources |
| CAP-008 | PHASE-005 | Not included | Per-input audio handling |
| CAP-009 | PHASE-006, PHASE-008 | Not included | Reusable transforms and direct focus interaction |
| CAP-010 | PHASE-006 | Not included | Linked triplicate composition |
| CAP-011 | PHASE-007, PHASE-008 | Not included | Validated 60 FPS enhancement and mixed-FPS strategy evidence |
| CAP-012 | PHASE-001 through PHASE-008, PHASE-004A | Source/project/output safety | Cross-cutting future safety and maintainable boundaries |

## Phase Approval and Handoff

This phase index was approved before downstream planning. Its phase records
are individual lifecycle files, and each feature record is assigned to exactly
one phase. PHASE-002 through PHASE-004 are complete and closed after user
approval on 2026-08-22. PHASE-001, PHASE-005, PHASE-004A, and PHASE-006 are
complete and closed after user validation, review, and local delivery
evidence. PHASE-007 is complete and closed after the user confirmed its
approved ticket set was accepted and tested; unavailable remote and
target-specific checks remain recorded as accepted warnings. PHASE-008 is
complete and closed after FEAT-024 through FEAT-028 and TICKET-061 through
TICKET-082 were manually validated and explicitly closed by the user on
2026-08-28. Historical generic blocker, runtime, target-workstation, license,
remote-check, and benchmark limitations remain recorded in the linked
evidence.

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

- The phase records were extracted into
  `docs/planning/phases/open/` during the initial migration.
- PHASE-001 through PHASE-004 later transitioned to `complete` and moved to
  `docs/planning/phases/closed/` on 2026-08-22 after user approval. PHASE-001
  was reopened and moved back to `docs/planning/phases/open/` on 2026-08-22
  for a timeline playback pacing correction.
- PHASE-004A was added on 2026-08-22 as a user-approved prerequisite before
  the confirmed future phases and closed after its exit conditions were
  satisfied.
- PHASE-006 moved from `phases/open/` to `phases/closed/` after its
  FEAT-017 through FEAT-019 and TICKET-038 through TICKET-047 records passed
  implementation, validation, review, and local delivery. PHASE-007 moved
  from `phases/open/` to `phases/closed/` after FEAT-020 through FEAT-023 and
  TICKET-048 through TICKET-060 were implemented, tested, reviewed, and
  accepted on 2026-08-26; remote and target-specific limitations remain
  explicitly recorded in the linked evidence.
- PHASE-008 was added to `phases/open/` on 2026-08-26 under the confirmed
  future direction. Its responsive-preview and focus-control records are
  complete and closed; the mixed-FPS comparison is complete and its approved
  Strategy B production follow-up is tracked by active TICKET-076.
  Restoration survey TICKET-073 is also complete. FEAT-027 has TICKET-077
  verifying under CHG-006 and TICKET-078 verifying under CHG-007, while
  TICKET-074 through TICKET-075 retain their blocked generic path because
  required runtimes and evidence remain incomplete. The phase remains open
  without changing the first-horizon scope.
- The original phase-index metadata, sequencing rationale, common rules,
  capability coverage, handoff gate, and source references remain in this
  synchronized index.
