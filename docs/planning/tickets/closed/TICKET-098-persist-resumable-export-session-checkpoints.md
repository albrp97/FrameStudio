# TICKET-098 - Persist Resumable Export Session Checkpoints

**Ticket ID:** TICKET-098
**Title:** Persist a fingerprinted export session and stage checkpoint manifest
**Status:** complete
**Horizon:** future
**Priority:** 1
**Parent feature:** FEAT-029
**Parent phase:** PHASE-008
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Capability links:** CAP-004, CAP-005, CAP-012
**Owner:** repository implementation in the active worktree
**Approval:** Planning authorized by the user's 2026-09-06 request; execution
remains subject to the configured approval and readiness gates.
**Change control:** CHG-010
**Last updated:** 2026-09-07
**Dependencies:** existing `ExportCache`, TICKET-087 enhanced-intermediate
retention, TICKET-093 retry validation, versioned project persistence, atomic
filesystem writes
**Affected surfaces:** `framestudio/export_cache.py`, export session state
model, manifest persistence, request fingerprinting, cache validation,
`tests/test_editor_export_cache.py`, export execution tests, and evidence
**Risks:** a partially written manifest could falsely mark a stage complete,
incomplete identity data could reuse stale media, or cleanup could remove a
valid recovery session
**Evidence path:** `evidence/ticket-098-export-session-checkpoints.md`

## Objective

Create the durable, versioned export-session contract required for an export
to continue safely after cancellation, process failure, or a later invocation.

## Observable requirements

- Given an export starts, the system should create or update one
  destination-scoped session manifest atomically before any stage is reported
  complete.
- Given a completed stage, the manifest should record its stage identity,
  artifact path, artifact fingerprint/metadata, request key, and completion
  timestamp only after the artifact passes its stage validator.
- Given cancellation, an exception, or process termination, the last
  atomically committed checkpoint should remain readable and should never claim
  a stage completed when its artifact is missing or invalid.
- Given a changed source, project snapshot, timeline, output destination,
  policy, runtime, tool identity, or plan, the session should be rejected or
  invalidated rather than reused.
- Given a corrupt, truncated, unsupported, or symlink-escaped session
  manifest, the system should report the invalid state and rebuild safely
  without exposing a false resumable result.
- Given verified publication succeeds, the session state and temporary
  checkpoint artifacts should be removed only after the final output and
  source-preservation checks pass.

## Scope

- Define a versioned export-session manifest separate from the final output.
- Persist request identity, destination identity, ordered stage definitions,
  completed/in-progress/invalid statuses, artifact metadata, last error,
  cancellation state, and timestamps with atomic replacement.
- Reuse the existing export-cache fingerprint and artifact-safety mechanisms
  where they provide the required guarantees.
- Add explicit manifest validation, invalidation, and success-only cleanup
  primitives for downstream execution and UI tickets.

## Non-goals

- Wiring the manifest into every export stage; that is TICKET-099.
- Adding GTK resume/restart/discard controls; that is TICKET-100.
- Adding CLI flags or output events; that is TICKET-101.
- Changing codecs, output policy, source media, project schema, or final
  verification rules.

## Protected behaviors

Existing destination-adjacent enhanced caches, source fingerprints, symlink
root protection, atomic partial-output handling, strict artifact validation,
source preservation, and success-only cleanup remain unchanged.

## Validation

- Focused manifest round-trip and schema-version tests.
- Atomic-write interruption, truncated-file, corrupt-manifest, symlink-path,
  fingerprint-mismatch, missing-artifact, and invalidation regressions.
- Tests proving a cancelled or failed session preserves the last valid
  checkpoint and a successful publication removes it only at the terminal
  cleanup boundary.
- Existing `make test`, `make compile`, `make contract`, and applicable
  quality/static-analysis commands.

## User-validation plan

- **Setup:** use a small generated project and an export destination on a
  writable local filesystem; stop the export after at least one stage has
  completed.
- **Steps:** inspect the destination-adjacent session state, restart the
  export with the same request, then change one source or export option and
  retry again.
- **Expected visible result:** the same request is recognized as resumable,
  while the changed request is explicitly reported as incompatible.
- **Expected persisted/external result:** the manifest contains only
  validated completed stages, survives cancellation, and is removed only after
  verified final publication.
- **Failure paths:** interrupted writes, missing/corrupt artifacts, changed
  source identity, changed destination, and unsupported manifest versions are
  explicit and do not publish output.
- **Evidence response:** return `PASS`, `FAIL`, `BLOCKED`, or approved
  `NOT APPLICABLE` with the manifest state, invalidation reason, and cleanup
  result.

## Definition of done

- A versioned, atomic, fingerprinted export-session manifest exists with
  focused persistence and invalidation evidence.
- No manifest state can falsely authorize reuse of an invalid artifact.
- The contract is consumable by TICKET-099 through TICKET-101 without
  duplicating identity or cleanup logic.
- The ticket remains `proposed` until execution approval and its configured
  delivery gates are satisfied.

**Path history:** Created in `docs/planning/tickets/open/` on 2026-09-06.
Moved to `docs/planning/tickets/closed/` on 2026-09-07 after user
validation.
