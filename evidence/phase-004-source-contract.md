# Delivery Evidence: TICKET-018

- Phase: `PHASE-004` - Combining Mixed-Source Footage
- Feature: `FEAT-010` - Importing and Retaining Mixed-Source Project Identity
- Ticket: `TICKET-018` - Defining Multi-Source Project Identity and Relinking
- Status: `verifying`
- Branch: `ticket/phase-004-mixed-source-footage`
- Base revision: `b624234813df8c05f6fe87ddf9f134c4347cbb25`
- Evidence path: `evidence/phase-004-source-contract.md`
- Owner: integration owner is the orchestrator; implementation is performed in
  this repository worktree

## Planning chain and scope

`vision.md` -> `docs/specs/project-scope.md` -> `CAP-007`, `CAP-012` ->
`PHASE-004` -> `FEAT-010` -> `TICKET-018`

The ticket covers stable multi-source identity, required probe metadata,
relinking and missing-source errors, one-source compatibility, and deterministic
path-redacted inspection. It does not cover import UI, timeline placement,
output-canvas/audio/FPS policy, copy/paste, multi-track editing, or remote
media.

Protected behavior includes the versioned one-source project format, stable
segment identifiers, path-redaction rules, atomic saves, and the deterministic
Phase 3 inspection contract. The ticket depends on `TICKET-017`, the existing
one-source schema and identifier conventions, and representative mixed-source
fixtures.

## Preimplementation checklist

- Ticket and active ancestors are in configured open lifecycle directories.
- Parent links, stable IDs, scope, non-goals, affected surfaces, and protected
  behavior are present in the planning records.
- Execution approval is provided by the user's request to prepare and
  implement all current open tickets.
- The protected baseline is terminal and passed.
- The validation plan includes unit/contract tests, persistence and redaction
  checks, `make check`, and the configured quality commands.
- User validation remains required before ticket closure and delivery.
- Remote checks are a later delivery blocker because no Git remote or upstream
  is configured; this does not block local implementation.

Decision: `ready = true` for implementation. No ticket is closed or marked
delivery-ready by this record.

## Evidence entries

### BASELINE-001

- Category: `baseline`
- Requirement/flow: Preserve the existing one-source editor and CLI behavior.
- Command: `make check PYTHON=python3`
- Expected: Existing tests, compilation, and diff checks pass.
- Observed: 123 tests passed; Python compilation passed; `git diff --check`
  passed.
- Status: `passed`
- Accepted warning: PyGObject emitted the existing GLib deprecation warning
  during tests.

### BASELINE-002

- Category: `baseline`
- Requirement/flow: Confirm the implementation context and delivery state.
- Steps: Inspect configured delivery settings, record the branch and base
  revision, and check provider configuration.
- Expected: Dedicated branch exists and required commands/gates are known.
- Observed: Dedicated Phase 4 branch is active at
  `b624234813df8c05f6fe87ddf9f134c4347cbb25`; configured commands include
  `make test`, `make contract`, `make check`, `make quality
  PYTHON=.venv/bin/python`, and `make smoke`. No remote or upstream is
  configured.
- Status: `passedWithConcerns`
- Blocker: Remote checks and publication cannot run until a remote is
  configured.

### IMPLEMENTATION-001

- Category: `implementation`
- Requirement/flow: Represent, persist, inspect, and relink multiple source
  identities without changing one-source semantics.
- Observed: Schema 3 mixed-source projects now retain ordered source
  registries, stable source IDs, probe metadata, source settings, source
  intervals, and redacted inspection output. Relinking and structured missing
  source failures use the shared domain and CLI boundaries.
- Evidence: `framestudio/model.py`, `framestudio/operations.py`,
  `framestudio/cli.py`, `tests/test_editor_mixed_source.py`, and
  `tests/test_editor_cli_mixed.py`.
- Status: `passed`

### QUALITY-001

- Category: `quality`
- Commands: `make quality PYTHON=.venv/bin/python` and
  `make contract PYTHON=.venv/bin/python`
- Observed: 135 tests passed in the quality gate, 23 CLI contract tests
  passed, formatting/lint/type/complexity/duplication/dependency/security
  checks passed, and churn completed.
- Status: `passed`

### REALMEDIA-001

- Category: `real-media`
- Requirement/flow: Import and export deliberately heterogeneous local media.
- Fixture: Disposable landscape 320x180 at 10 FPS with AAC audio and
  disposable portrait 180x320 at 15 FPS without audio.
- Observed: Mixed import persisted two distinct sources. Verified fallback
  export produced a playable 320x320 H.264/AAC MP4 with 4.0 seconds and 15
  FPS. The source files' size and modification timestamps were unchanged.
- Status: `passed`

### GUI-001

- Category: `user-facing`
- Requirement/flow: Open the mixed project and exercise frame stepping,
  split, delete/restore, and copy/paste through the GTK editor.
- Observed: The editor loaded both sources; the timeline displayed source
  blocks and final output duration. The workflow produced
  `evidence/screenshots/phase-004-mixed-before.png`,
  `evidence/screenshots/phase-004-mixed-split.png`,
  `evidence/screenshots/phase-004-mixed-deleted.png`, and
  `evidence/screenshots/phase-004-mixed-after.png`. The after state showed
  the pasted block and updated duration.
- Status: `passedWithConcerns`
- Concern: Maintainer confirmation of the complete target-workstation
  workflow is still required before closure.

## Readiness

- Technical baseline: `passed`
- Implementation: `passed`
- User validation: `pending`
- Local quality: `passed`
- Real-media validation: `passed`
- Remote checks: `blocked`
- Commit/PR: `not started`
- Open blockers: no configured Git remote or upstream; required user
  validation is still outstanding.
