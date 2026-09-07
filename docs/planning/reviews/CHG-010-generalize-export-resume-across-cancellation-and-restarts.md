# CHG-010 - Generalize Export Resume Across Cancellation and Restarts

**Change ID:** CHG-010
**Type:** Material planning change
**Status:** approved-and-applied
**Date:** 2026-09-06
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Parent links:** PHASE-008, FEAT-029
**Owner:** repository planning in the active worktree
**Approval:** User-authorized by the 2026-09-06 request to create tickets for
resuming exports after cancellation, failure, project reload, and later
time-sliced continuation; implementation remains subject to configured
execution approval and delivery gates.
**Affected IDs:** FEAT-029, TICKET-087, TICKET-093, TICKET-098, TICKET-099,
TICKET-100, TICKET-101
**Evidence paths:** `evidence/ticket-098-export-session-checkpoints.md`,
`evidence/ticket-099-resumable-export-execution.md`,
`evidence/ticket-100-export-resume-controls.md`,
`evidence/ticket-101-cli-export-resume-contract.md`
**Source paths:** `framestudio/export_cache.py`,
`framestudio/export_smart_render.py`, `framestudio/export_interpolation.py`,
`framestudio/export_delivery.py`, `framestudio/app_export.py`,
`framestudio/export_console.py`, `tests/test_editor_export_cache.py`,
`tests/test_editor_export_execution.py`, `tests/test_editor_performance.py`,
`.github/aidd-config.yml`

## Request and classification

The approved FEAT-029/TICKET-087 behavior retains and validates expensive
enhanced-export intermediates after a failed attempt. The new request extends
that behavior to a persistent resumable export session: cancellation or a
late-stage error should preserve every valid completed stage, and a later
export invocation or project reload should continue from the last committed
checkpoint rather than restarting from cutting or interpolation.

This is a material planning change because it expands the supported export
routes from the enhanced path to ordinary and enhanced paths, adds a durable
cross-process session contract, and introduces explicit resume/restart/discard
controls. It remains within the existing objective, first-horizon safe-export
scope, PHASE-008, and FEAT-029 capabilities for rendering and failure
recovery.

## Approved decision

Keep PHASE-008 and FEAT-029 active during implementation. Preserve TICKET-087 as the validated
enhanced-intermediate cache foundation and TICKET-093 as its exact-frame-count
and retry-correctness follow-up. Add four proposed tickets:

- TICKET-098 persists an atomic, fingerprinted export-session/checkpoint
  manifest.
- TICKET-099 integrates checkpointing and resume into every supported export
  stage while retaining strict verification and atomic publication.
- TICKET-100 exposes safe resume/restart/discard behavior in the GTK editor
  and when a project is reopened.
- TICKET-101 carries the same resume semantics into the CLI and its
  machine-readable/human progress contract.

No final output may be exposed before verification and atomic publication.
Cancellation must preserve valid resumable artifacts, while source media and
unrelated project state remain untouched.

## Impact

- **Planning:** extend FEAT-029's scope, observable requirements, validation,
  and planned-ticket links; append TICKET-098 through TICKET-101 to the
  PHASE-008 backlog and dependency graph.
- **Persistence:** add a versioned session manifest with request identity,
  stage state, artifact references, and durable cancellation/failure status.
- **Export execution:** checkpoint cuts, preparation, interpolation/upscale,
  composition/concatenation, verification, and publication boundaries for
  standard and enhanced routes.
- **GTK lifecycle:** detect a compatible pending session on export start or
  project reopen and offer explicit resume, restart, or discard choices
  without silently running an export.
- **CLI:** preserve JSON Lines validity while exposing explicit resume
  selection and stage/checkpoint status.
- **Safety:** retain source preservation, strict output validation, atomic
  final publication, cache fingerprinting, and success-only cleanup.

## Explicit non-goals

- Silently resuming an export at application startup.
- Multiple concurrent resumable exports for one destination.
- Remote checkpoint storage, cloud synchronization, or cross-machine resume.
- Reusing artifacts after source, project, plan, policy, runtime, tool, or
  destination identity changes.
- Weakening output verification or moving/deleting original source media.

## Replan decision

Approved and applied on 2026-09-06 for planning. The smallest affected
subtree is FEAT-029 under PHASE-008; existing ticket IDs and paths remain
unchanged, and TICKET-087/TICKET-093 remain the enhanced-route dependencies.
The new tickets were proposed during planning and subsequently implemented,
validated, reviewed, and closed under the configured gates on 2026-09-07.

## Traceability

- Feature: `docs/planning/features/closed/FEAT-029-strengthening-editor-recovery-and-export-observability.md`
- Phase: `docs/planning/phases/closed/PHASE-008-optimizing-responsive-preview-and-media-strategy.md`
- Backlog: `docs/planning/backlog.md`
- New tickets:
  - `docs/planning/tickets/closed/TICKET-098-persist-resumable-export-session-checkpoints.md`
  - `docs/planning/tickets/closed/TICKET-099-checkpoint-and-resume-all-export-stages.md`
  - `docs/planning/tickets/closed/TICKET-100-offer-export-resume-restart-and-discard-controls.md`
  - `docs/planning/tickets/closed/TICKET-101-preserve-cli-export-resume-contract.md`
