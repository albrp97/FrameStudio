# TICKET-017 - Verify GUI/CLI Parity and Idempotent Round Trips

**Ticket ID:** TICKET-017  
**Objective:** OBJ-001  
**Scope:** SCOPE-001  
**Phase:** PHASE-003  
**Feature:** FEAT-009  
**Capability links:** CAP-004, CAP-006, CAP-012  
**Status:** complete  
**Closure:** user-authorized on 2026-08-21 after parity, idempotency, smoke,
and local quality evidence; remote checks remain unavailable and are recorded
as an accepted warning.  
**Path history:** `tickets/open/TICKET-017-verifying-gui-cli-parity-and-idempotent-round-trips.md`
-> `tickets/closed/TICKET-017-verifying-gui-cli-parity-and-idempotent-round-trips.md`  
**Horizon:** first  
**Priority:** 6  
**Owner:** repository planning; implementer is not assigned  
**Approval:** user-approved on 2026-08-21 for implementation and testing;
configured remote checks remain unavailable  
**Provider:** auto; base and target branches are not configured in
`.github/aidd-config.yml`  
**Source paths:** `vision.md`, `docs/specs/project-scope.md`,
`docs/specs/capability-map.md`,
`docs/planning/phases/open/PHASE-003-repeating-the-basic-edit-through-agents.md`,
`docs/planning/features/open/FEAT-009-sharing-domain-behavior-between-gui-and-cli.md`,
`docs/planning/tickets/open/TICKET-016-routing-gui-and-cli-through-shared-domain-operations.md`,
`AGENTS.md`, `.github/aidd-config.yml`  
**Dependencies:** TICKET-016; TICKET-015; disposable representative media;
  target-workstation manual workflow  
**Risks:** tests that compare only JSON shape, missed failure-path drift,
  non-deterministic retries, and unavailable GUI or remote environments  
**Affected surfaces:** parity tests, CLI smoke harness, project fixtures,
  export evidence, documentation, and manual validation  
**Evidence path:** `evidence/phase-003-gui-cli-parity.md`

## Outcome

The first-horizon edit can be performed through the GUI or CLI with equivalent
project state, duration, export decisions, structured failures, and safe
round-trip behavior.

## Scope

- Build parity fixtures for inspection, split, delete/restore, duration,
  save/reopen, and export.
- Compare successful and failed GUI-domain and CLI-domain operations.
- Verify repeated requests and project round trips are deterministic.
- Run the local shell smoke flow on disposable media and document any
  target-workstation or remote-check limitations.

## Explicit non-goals

- New product capabilities, multiple sources, composition, audio, FPS, or
  natural-language orchestration.
- Treating a passing serialization comparison as proof of media correctness.

## Observable requirements

- Given the same fixture and operation sequence, GUI and CLI produce equivalent
  persisted source, segment, deletion, playhead, and duration state.
- Given the same invalid operation, both paths preserve valid state and expose
  equivalent structured failure categories.
- Given a successful export sequence, both paths select equivalent route and
  produce independently verifiable output.
- Given repeated idempotent commands, project state and output decisions remain
  stable.

## Definition of done

- Parity, failure, idempotency, round-trip, and disposable-media smoke evidence
  is recorded.
- The evidence separates automated, real-media, manual, and unavailable
  remote checks.
- PHASE-003 exit conditions have actionable evidence or explicitly documented
  gaps.

## Validation and evidence

- GUI/CLI parity and idempotency test suite.
- Local shell smoke test with redacted structured output.
- Target-workstation manual confirmation where required.
- Full configured baseline and local quality commands.
