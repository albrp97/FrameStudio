# FEAT-031 - Executing Efficient Resumable Export Pipelines

**Feature ID:** FEAT-031
**Parent links:** OBJ-001, SCOPE-001, PHASE-009
**Capability links:** CAP-005, CAP-011, CAP-012
**Status:** active
**Horizon:** future
**Priority:** 1
**Owner:** repository implementation in the active worktree
**Approval:** user-authorized by the 2026-09-09 request to implement the
measured export pipeline
**Last updated:** 2026-09-09
**Source paths:** `docs/planning/phases/open/PHASE-009-selecting-and-delivering-efficient-export-pipelines.md`,
`docs/planning/features/open/FEAT-030-benchmarking-and-selecting-efficient-export-pipelines.md`,
`framestudio/export_smart_render.py`, `framestudio/export_interpolation.py`,
`framestudio/export_cache.py`, `framestudio/export_session.py`,
`framestudio/export_delivery.py`, `tests/test_editor_export_execution.py`,
`.github/aidd-config.yml`
**Dependencies:** TICKET-102 benchmark recommendation; existing enhanced
export route; export cache/session contracts; output verification
**Risks:** unsafe batching across hard cuts, changed audio duration, cache
identity collisions, fallback re-encoding, and regressions in visual
composition or exact frame counts
**Affected surfaces:** enhanced export routing, preparation grouping,
interpolation/upscale ordering, assembly, progress, cancellation, cache/session
reuse, verification, tests, and documentation
**Evidence path:** `evidence/efficient-export-pipeline-implementation.md`
**Protected behaviors:** timeline ordering, visual transforms/triplicate,
source-level audio handling, fixed output profile, exact frame counts,
atomic publication, source preservation, cleanup, and resumable export
**Feature links:** TICKET-103, TICKET-104
**Path history:** created at
`features/open/FEAT-031-executing-efficient-resumable-export-pipelines.md`

## Outcome

Enhanced export conditionally uses the benchmark-selected route to avoid
redundant preparation, interpolation, restoration, and assembly work while
retaining a verified per-segment fallback and resumable artifacts.

## Scope

- Represent safe contiguous source/render-policy runs without reordering the
  timeline.
- Batch preparation or interpolation only where backend and boundary checks
  prove it safe.
- Preserve per-segment restoration or fallback behavior when batching would
  cross a deleted boundary or change visual semantics.
- Reuse valid grouped artifacts after cancellation, late failure, project
  reopen, or a later export attempt.
- Emit truthful progress and explicit fallback diagnostics.

## Explicit non-goals

- Silent resume after source, project, policy, runtime, tool, or destination
  identity changes.
- Processing deleted source ranges without a measured reason.
- Weakening artifact gates, output verification, or source-preservation checks.
- Changing the fixed delivery canvas or adding unrelated editor features.

## Observable acceptance criteria

- Given repeated source segments with compatible policy, preparation and
  interpolation invocations are reduced without changing timeline order.
- Given a deleted boundary, no selected route blends frames across the
  boundary unless the backend's explicit range behavior is verified.
- Given focus or triplicate transforms, every active segment retains its own
  persisted composition state.
- Given eligible upscale and FPS enhancement, the selected ordering preserves
  output dimensions, target rate, exact frame count, audio policy, and
  playability.
- Given cancellation or failure, a later resume reuses valid grouped
  artifacts and does not rerun completed stages.
- Given an incompatible artifact or stream-copy join, the exporter records the
  reason and uses the verified fallback.

## User-validation plan

- **Setup:** use a mixed-source project with at least two retained ranges,
  one deleted gap, one visual-transform segment, one triplicate segment, mixed
  FPS, audio, and an optional eligible upscale source.
- **Steps:** export once, cancel after an intermediate stage, close/reopen the
  project, resume, inspect progress and output metadata, and compare the
  result with a clean baseline export.
- **Expected result:** the resumed run skips valid completed work, preserves
  exact timeline order and boundaries, and publishes one verified output.
- **Failure paths:** changed source/project identity, invalid cache artifact,
  unsafe batching, verification rejection, or cancellation cleanup must
  surface explicitly and leave no unsafe published partial.
- **Cleanup:** retain evidence, then remove destination-scoped temporary
  artifacts only after successful publication.
- **Evidence response:** return `PASS`, `FAIL`, `BLOCKED`, or approved
  `NOT APPLICABLE` with command output and artifact paths.
- **Pass criteria:** technical tests, output verification, source
  preservation, resume behavior, and user-visible inspection all pass.

