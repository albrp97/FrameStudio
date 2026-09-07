# TICKET-099 - Checkpoint and Resume All Export Stages

**Ticket ID:** TICKET-099
**Title:** Resume ordinary and enhanced exports from the last valid stage
**Status:** complete
**Horizon:** future
**Priority:** 1
**Parent feature:** FEAT-029
**Parent phase:** PHASE-008
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Capability links:** CAP-005, CAP-012
**Owner:** repository implementation in the active worktree
**Approval:** Planning authorized by the user's 2026-09-06 request; execution
remains subject to the configured approval and readiness gates.
**Change control:** CHG-010
**Last updated:** 2026-09-07
**Dependencies:** TICKET-098 session checkpoints; TICKET-087 retained
enhanced intermediates; TICKET-093 exact-frame-count retry validation;
existing staged progress and safe atomic export
**Affected surfaces:** `framestudio/export_planning.py`,
`framestudio/export_delivery.py`, `framestudio/export_process.py`,
`framestudio/export_smart_render.py`, `framestudio/export_interpolation.py`,
`framestudio/export_ffmpeg.py`, export cancellation and worker handling,
`tests/test_editor_export_execution.py`, `tests/test_editor_export_cache.py`,
generated-media evidence, and source-preservation checks
**Risks:** stage boundaries may leave incomplete media that appears valid,
parallel workers could corrupt one session, or resume could skip a required
verification step
**Evidence path:** `evidence/ticket-099-resumable-export-execution.md`

## Objective

Make cancellation and failure safe stopping points for the full export
pipeline so a later run can continue without repeating valid completed work.

## Observable requirements

- Given an ordinary stream-copy or fallback export, completed cutting and
  composition/concatenation stages should be checkpointed and reused after a
  cancellation or error.
- Given an enhanced export, completed preparation, interpolation, upscale,
  per-source assembly, and composition stages should be checkpointed and
  reused after a cancellation or error.
- Given an export cancelled after approximately ten minutes, the next
  compatible invocation should continue from the last committed stage rather
  than rerunning earlier cuts or interpolation.
- Given a failure at a later stage, valid earlier artifacts should remain
  available, while the failed or incomplete stage should be retried.
- Given a missing, corrupt, stale, or request-incompatible artifact, only the
  affected stage and its dependent stages should be rebuilt.
- Given any resume attempt, final verification, source-preservation checks,
  atomic publication, and success-only cleanup should run exactly as required;
  no unverified final destination may be exposed.
- Given two export workers target the same session, one should be rejected or
  serialized explicitly rather than corrupting the session manifest or
  artifacts.

## Scope

- Integrate TICKET-098 checkpoint transitions into every supported export
  route and stage.
- Persist a validated artifact before marking each stage complete and retain
  compatible artifacts after cancellation or failure.
- Ensure cancellation propagates through FFmpeg/interpolation/upscale workers
  without deleting resumable artifacts.
- Resume from the earliest invalid or incomplete stage and preserve existing
  retry reuse for the enhanced route.
- Keep ordinary temporary partial outputs separate from retained resumable
  artifacts and remove them according to the existing failure policy.
- Add stage reuse counters and progress details sufficient to prove that work
  was skipped rather than merely reported as skipped.

## Non-goals

- Defining the session manifest schema; that is TICKET-098.
- Adding editor controls or project-reopen discovery; that is TICKET-100.
- Adding CLI resume flags; that is TICKET-101.
- Relaxing media verification, changing render strategy, or modifying source
  files.

## Protected behaviors

Existing FFmpeg command construction, interpolation and upscale correctness,
exact target-frame handling, audio policy, source preservation, final output
verification, atomic publication, and TICKET-087/TICKET-093 enhanced-cache
semantics remain protected.

## Validation

- Focused generated-media tests that cancel or fail after each major stage.
- Retry tests proving cut, interpolation, upscale, concatenation, and
  verification reuse counts and elapsed-work reductions.
- Corrupt/stale artifact tests proving only dependent stages rebuild.
- Concurrent-session, process-restart, final-publication, and source-byte
  preservation tests.
- Existing `make test`, `make compile`, `make contract`, `make smoke`, and
  applicable quality/static-analysis commands.
- Target-workstation long export interrupted after a bounded time window,
  followed by a later warm resume with output metadata and stage evidence.

## User-validation plan

- **Setup:** select a project with enough media to run longer than ten minutes
  and use the normal GTK or CLI export route.
- **Steps:** start export, cancel it after a known stage boundary or allow a
  deliberate late-stage failure, close/reopen the application, and start the
  same export again.
- **Expected visible result:** progress identifies the recovered session and
  reports reused stages before continuing with the remaining work.
- **Expected persisted/external result:** the final output is verified and
  atomically published; earlier completed stages are not rerun and original
  sources are byte-identical.
- **Failure paths:** cancellation during FFmpeg/interpolation, process kill,
  changed project/source, corrupted artifact, destination conflict, and
  second concurrent export remain visible and safe.
- **Evidence response:** return `PASS`, `FAIL`, `BLOCKED`, or approved
  `NOT APPLICABLE` with the cancelled duration, reused stages, rebuild stages,
  output metadata, and source-preservation result.

## Definition of done

- Ordinary and enhanced export routes can stop and resume from validated
  checkpoints without repeating completed stages.
- Cancellation and failures retain only safe reusable artifacts, and success
  cleanup remains terminal.
- Focused, generated-media, target-workstation, and repository-gate evidence
  proves the behavior.
- The ticket remains `proposed` until execution approval and its configured
  delivery gates are satisfied.

**Path history:** Created in `docs/planning/tickets/open/` on 2026-09-06.
Moved to `docs/planning/tickets/closed/` on 2026-09-07 after user
validation.
