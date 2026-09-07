# TICKET-087 - Resume Enhanced Export Intermediates After Failure

**Ticket ID:** TICKET-087
**Title:** Resume enhanced export intermediates after failure
**Status:** complete
**Parent feature:** FEAT-029
**Parent phase:** PHASE-008
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Capability links:** CAP-005, CAP-012
**Owner:** repository implementation in the active worktree
**Approval:** Explicitly authorized by the 2026-08-28 user request; no
additional ticket approval is required before implementation
**Last updated:** 2026-09-07
**Dependencies:** safe atomic export and verification; TICKET-076 per-source
  enhanced route; TICKET-079 optional upscale/interpolation path; FFmpeg and
  ffprobe validation
**Affected surfaces:** `framestudio/export_cache.py`,
`framestudio/export_smart_render.py`, `framestudio/export_interpolation.py`,
export execution tests, README
**Risks:** stale, corrupted, or mismatched artifacts could produce incorrect
  output; moving an artifact into a partial output could destroy the retry
  cache before publication
**Evidence path:** `evidence/ticket-087-resumable-enhanced-export.md`

## Scope

- Create a destination-adjacent persistent intermediate cache for the active
  enhanced-export route.
- Fingerprint the serialized export plan, sources and filesystem state,
  policies, runtimes, and relevant tool paths.
- Validate cached manifests and media artifacts before reuse, including
  dimensions, duration/frame-rate/audio expectations, and frame counts where
  applicable.
- Copy reusable artifacts into output partials rather than moving them.
- Retain the cache through failed exports and invalidate mismatches or
  corruption; remove it only after verified atomic publication succeeds.

## Non-goals

- Reusing artifacts across different export requests, changed sources,
  changed policies/runtimes, or unsupported legacy routes.
- Changing codec defaults, output canvas, source media, or atomic publication
  guarantees.

## Acceptance criteria

- Given a failed enhanced export with valid completed intermediates, retry
  skips the completed expensive stages and reuses those artifacts.
- Given a changed source, export plan, policy, runtime, or tool identity, the
  cache is rejected and affected stages are rebuilt.
- Given a missing, corrupted, or probe-invalid artifact, the cache is rejected
  rather than producing success-shaped output.
- Given a retry, cached files remain available until verified publication.
- Given successful verification and atomic publication, the destination cache
  is removed and the final output is exposed.
- Given a failed export, the original source media and retained cache remain
  intact.

## Verification

- Add cache manifest, fingerprint, invalidation, corruption, copy-vs-move,
  cleanup, and failure-then-retry regressions.
- Run a representative enhanced export, force a late failure, retry, and
  record stage reuse, elapsed time, output metadata, and source preservation.
- Run the existing export, compile, smoke, and configured quality gates.

## Protected behavior

Atomic partial-output handling, verification before publication, failure
cleanup rules for non-cached temporary files, interpolation correctness,
source preservation, and structured CLI errors remain unchanged.

## Path history

Created in `docs/planning/tickets/open/` on 2026-08-28.
Moved to `docs/planning/tickets/closed/` on 2026-09-07 after user
validation.
