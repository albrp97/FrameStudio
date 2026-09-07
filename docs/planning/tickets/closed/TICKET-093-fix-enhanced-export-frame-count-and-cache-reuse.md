# TICKET-093 - Fix Enhanced Export Frame Count and Retry Reuse

**Ticket ID:** TICKET-093
**Title:** Preserve the exact target frame count during enhanced mixed export
**Status:** complete
**Parent feature:** FEAT-029
**Parent phase:** PHASE-008
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Capability links:** CAP-005, CAP-012
**Owner:** repository implementation in the active worktree
**Approval:** Explicitly authorized by the user's report of a failed
enhanced export and request to make the export retryable and reliable
**Last updated:** 2026-09-07
**Dependencies:** TICKET-087 retained enhanced-export intermediates;
TICKET-091 validated upscale/enhanced routing; mixed-source output policy
**Affected surfaces:** `framestudio/export_interpolation.py`,
enhanced mixed-output assembly and verification, export execution tests,
retained intermediate retry behavior, and evidence
**Risks:** an output-frame limit could truncate audio or hide an upstream
shortfall, stale cached artifacts could be reused, or strict verification
could be weakened instead of correcting composition
**Evidence path:** `evidence/ticket-093-fix-enhanced-export-frame-count-and-cache-reuse.md`

## Observable requirements

- Given an enhanced mixed export with fractional segment durations, the final
  video should contain exactly the selected target frame count from the export
  plan while remaining within the existing duration tolerance.
- Given valid retained prepared and interpolated intermediates, a retry should
  reuse them and proceed directly to final assembly and verification.
- Given a stale, corrupted, or frame-count-incompatible intermediate, the
  retry should invalidate that artifact and rebuild it rather than publishing
  an incorrect output.
- Given a frame-count mismatch or any other final verification failure, no
  final destination should be published and retained valid intermediates should
  remain available for a later retry.
- Given a successful verified publication, the retained intermediate cache
  should still be removed according to the established success-only cleanup
  policy.

## Scope

- Correct enhanced per-source final assembly so the exact planned video-frame
  count is preserved without weakening final verification.
- Add a regression that reproduces the one-frame loss caused by the previous
  duration-limited composition.
- Verify cache reuse and invalidation behavior against the existing request
  fingerprint and artifact validators.
- Preserve source bytes, audio/output policy checks, atomic publication, and
  failure cleanup semantics.

## Non-goals

- Changing the selected FPS policy, per-segment frame allocation, fixed
  1920x1080 output canvas, codec policy, or audio normalization policy.
- Relaxing duration, frame-rate, frame-count, decoded-output, or source-safety
  verification.
- Reprocessing or modifying the user's original source media.
- Replacing the established per-source enhanced render strategy.

## Validation

- Focused enhanced-assembly and frame-count regression tests.
- Generated-media enhanced export coverage for exact frame count, cache reuse,
  invalidation, failure retention, and successful cleanup.
- Reproduction and retry evidence using the reported mixed-source project when
  its local media remains available.
- Existing repository unit, compilation, contract, smoke, quality, static
  analysis, and review gates.
- Target-workstation export verification or an explicit environment
  limitation, with source-preservation and output metadata evidence.

## Definition of done

- The reported enhanced export no longer fails because final composition
  loses a planned frame.
- A valid retry skips completed expensive preparation/interpolation work while
  still running final assembly and verification.
- Invalid intermediates are rebuilt and valid failure-state intermediates are
  retained until successful publication.
- Focused and protected repository evidence is recorded; the ticket remains
  in `verifying` until required user validation and delivery gates are
  terminal.

**Path history:** Created in `docs/planning/tickets/open/` on 2026-09-04.
Moved to `docs/planning/tickets/closed/` on 2026-09-07 after user
validation.
