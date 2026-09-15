# TICKET-103 - Implement the Conditional Grouped Export Route

**Ticket ID:** TICKET-103
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Phase:** PHASE-009
**Feature:** FEAT-031
**Capability links:** CAP-005, CAP-011, CAP-012
**Status:** active
**Horizon:** future
**Priority:** 1
**Owner:** repository implementation in the active worktree
**Approval:** user-authorized by the 2026-09-09 export-optimization request
**Last updated:** 2026-09-09
**Source paths:** `docs/planning/features/open/FEAT-031-executing-efficient-resumable-export-pipelines.md`,
`docs/planning/tickets/open/TICKET-102-benchmark-efficient-export-pipeline-candidates.md`,
`framestudio/export_smart_render.py`, `framestudio/export_interpolation.py`,
`framestudio/export_cache.py`, `framestudio/export_session.py`,
`framestudio/export_delivery.py`
**Dependencies:** TICKET-102 recommendation; existing per-segment enhanced
route; cache/session/output verification contracts
**Risks:** crossing deleted boundaries, changing frame quantization, repeated
audio normalization, cache collisions, and fallback regressions
**Affected surfaces:** export routing, grouping, preparation, interpolation,
restoration/upscale, composition, assembly, progress, cancellation, cache,
session, and documentation
**Evidence path:** `evidence/efficient-export-pipeline-implementation.md`
**Protected behaviors:** fixed output profile, exact frame counts, timeline
order, visual transforms/triplicate, audio, source preservation, atomic
publication, cleanup, and resume
**Path history:** created at
`tickets/open/TICKET-103-implement-conditional-grouped-export-route.md`

## Outcome

Enhanced export conditionally batches safe work and avoids redundant
preparation/interpolation/assembly while retaining a verified fallback for
unsafe or unsupported media.

## Scope

- Add a plan-derived grouping model for compatible active timeline runs.
- Reuse one preparation or interpolation artifact only when source identity,
  policy, transform semantics, rate, audio, and boundary rules match.
- Keep restoration per segment or use a measured source-level route only when
  it is boundary-safe and faster for the selected project.
- Integrate grouped artifacts with existing destination-scoped cache/session
  identity and progress.
- Preserve stream-copy validation and explicit fallback composition.

## Explicit non-goals

- Silently changing the selected output policy or enhancement backend.
- Interpolating across deleted boundaries without evidence.
- Removing the existing route or weakening verification.
- Adding new external runtime dependencies.

## Observable acceptance criteria

- Given compatible repeated runs, the optimized route reduces redundant
  process invocations relative to the protected baseline.
- Given interleaved sources or deleted gaps, output order exactly matches the
  timeline and no unsafe cross-boundary interpolation occurs.
- Given focus/triplicate segments, each segment's persisted visual state is
  retained.
- Given mixed FPS, audio normalization, and optional upscale, output metadata,
  duration, exact frame count, playability, and source preservation match the
  established contract.
- Given a rejected grouping or join, the exporter reports the reason and uses
  the verified fallback.

## Validation

- Run targeted export, smart-render, interpolation, cache/session, and
  generated-media functionality tests.
- Run `python3 -m unittest discover -s tests` and the repository compilation
  command.
- Run a target-workstation real-media export with the benchmark-selected
  route and inspect output metadata/source hashes.

## User-validation plan

- **Setup:** use a mixed-source project with retained/deleted ranges, mixed
  FPS, audio, focus/triplicate state, and an eligible upscale source where
  available.
- **Steps:** compare a clean baseline export with an optimized export, then
  cancel and resume the optimized export after an intermediate artifact is
  present.
- **Expected result:** the optimized and baseline outputs agree on timeline,
  metadata, audio, boundaries, and visual composition, while resume skips
  completed work.
- **Failure paths:** unsafe grouping, invalid artifact, wrong frame count,
  altered source, fallback failure, or publication failure blocks acceptance.
- **Cleanup:** preserve evidence and remove destination-scoped artifacts only
  after verified publication.
- **Evidence response:** return `PASS`, `FAIL`, `BLOCKED`, or approved
  `NOT APPLICABLE` with export/session/cache paths.

