# TICKET-101 - Preserve the CLI Export Resume Contract

**Ticket ID:** TICKET-101
**Title:** Add explicit resume, restart, and discard semantics to CLI export
**Status:** complete
**Horizon:** future
**Priority:** 2
**Parent feature:** FEAT-029
**Parent phase:** PHASE-008
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Capability links:** CAP-005, CAP-006, CAP-012
**Owner:** repository implementation in the active worktree
**Approval:** Planning authorized by the user's 2026-09-06 request; execution
remains subject to the configured approval and readiness gates.
**Change control:** CHG-010
**Last updated:** 2026-09-07
**Dependencies:** TICKET-098 session discovery; TICKET-099 resumable execution;
existing CLI export contract, JSON Lines output, and numbered staged progress
from TICKET-088
**Affected surfaces:** `framestudio/cli.py`, `framestudio/cli_export.py`,
`framestudio/cli_parser.py`, `framestudio/cli_types.py`,
`framestudio/export_console.py`, CLI contract documentation, CLI tests, and
automation evidence
**Risks:** new flags could break existing scripts, human progress could
corrupt JSON Lines, or a CLI invocation could resume the wrong destination
without explicit identity validation
**Evidence path:** `evidence/ticket-101-cli-export-resume-contract.md`

## Objective

Expose the same safe resumable-export lifecycle to console users and
automation without breaking the existing deterministic CLI contract.

## Observable requirements

- Given a compatible pending export session, the CLI should support an
  explicit resume operation and report the recovered stage before work starts.
- Given a user requests restart or discard, the CLI should invalidate the
  session explicitly and report the selected action.
- Given no compatible session exists, a resume request should fail clearly
  without modifying the source or publishing output.
- Given a source, project, destination, or policy mismatch, the CLI should
  reject resume and explain the identity mismatch.
- Given a cancellation or failure, JSON Lines output should remain valid and
  include the terminal session/checkpoint status; human interactive output
  should still show numbered stages and reuse/rebuild information.
- Given an existing invocation without resume flags, the established fresh
  export behavior and output schema should remain backward compatible.

## Scope

- Define CLI options or subcommands for resume, restart, and discard using the
  repository's existing parser and contract conventions.
- Add structured session-discovery, checkpoint, reuse, invalidation, and
  terminal-status events without changing existing event meanings.
- Keep human console progress separate from machine-readable stdout as required
  by TICKET-088.
- Document examples for cancellation followed by a later resume and add
  contract/round-trip tests.

## Non-goals

- Implementing the shared session manifest or stage executor; those belong to
  TICKET-098 and TICKET-099.
- Automatic retry loops, remote orchestration, or cross-machine sessions.
- Changing existing export codecs, output naming, verification, or source
  preservation.
- Requiring CLI parity before the GTK resume controls can be independently
  validated, provided the shared session contract is stable.

## Protected behaviors

Existing CLI JSON Lines schema, deterministic inspection/edit/export commands,
structured errors, human console stage output, safe atomic publication,
legacy command compatibility, and source preservation remain unchanged unless
the new explicit resume operation is selected.

## Validation

- CLI parser and contract tests for default, resume, restart, and discard
  requests.
- JSON Lines validity tests under success, cancellation, mismatch, and
  failure conditions.
- End-to-end generated-media cancellation/resume and source-preservation
  tests.
- Existing `make test`, `make compile`, `make contract`, `make smoke`, and
  applicable quality/static-analysis commands.

## User-validation plan

- **Setup:** use the canonical `framestudio` CLI with a saved project and a
  disposable output destination.
- **Steps:** start an export, cancel it, invoke the explicit resume operation,
  then repeat with a changed destination and a discard request.
- **Expected visible result:** the CLI reports the recovered stage, reused
  work, mismatch reason, or discard result without ambiguous behavior.
- **Expected persisted/external result:** a resumed export publishes one
  verified output, JSON Lines remains parseable, and source files are
  unchanged.
- **Failure paths:** no session, stale session, changed source/policy,
  corrupted artifact, cancellation, and final verification failure are
  explicit non-success outcomes.
- **Evidence response:** return `PASS`, `FAIL`, `BLOCKED`, or approved
  `NOT APPLICABLE` with commands, parsed event records, stage reuse, output
  metadata, and source-preservation results.

## Definition of done

- CLI users can explicitly resume, restart, or discard compatible export
  sessions without breaking existing invocations or JSON Lines consumers.
- Cancellation/resume behavior is covered by contract and generated-media
  evidence.
- The ticket remains `proposed` until execution approval and its configured
  delivery gates are satisfied.

**Path history:** Created in `docs/planning/tickets/open/` on 2026-09-06.
Moved to `docs/planning/tickets/closed/` on 2026-09-07 after user
validation.
