# TICKET-012 - Select the Deterministic CLI Contract and Inspection Schema

**Ticket ID:** TICKET-012  
**Objective:** OBJ-001  
**Scope:** SCOPE-001  
**Phase:** PHASE-003  
**Feature:** FEAT-007  
**Capability links:** CAP-004, CAP-006, CAP-012  
**Status:** complete  
**Closure:** user-authorized on 2026-08-21 after contract, regression, and
local quality evidence; remote checks remain unavailable and are recorded as
an accepted warning.  
**Path history:** `tickets/open/TICKET-012-select-deterministic-cli-contract-and-inspection-schema.md`
-> `tickets/closed/TICKET-012-select-deterministic-cli-contract-and-inspection-schema.md`  
**Horizon:** first  
**Priority:** 1  
**Owner:** repository planning; implementer is not assigned  
**Approval:** user-approved on 2026-08-21 for implementation and testing;
configured remote checks remain unavailable  
**Provider:** auto; base and target branches are not configured in
`.github/aidd-config.yml`  
**Source paths:** `vision.md`, `docs/specs/project-scope.md`,
`docs/specs/capability-map.md`,
`docs/planning/phases/open/PHASE-003-repeating-the-basic-edit-through-agents.md`,
`docs/planning/features/open/FEAT-007-inspecting-projects-through-a-deterministic-cli.md`,
`AGENTS.md`, `.github/aidd-config.yml`  
**Dependencies:** completed PHASE-001/PHASE-002 project behavior and
TICKET-011's verified export boundary  
**Risks:** incompatible command changes, unstable machine-readable output,
ambiguous identifiers, and private path leakage  
**Affected surfaces:** CLI entry point, project schema, structured errors,
documentation, and contract tests  
**Evidence path:** `evidence/phase-003-cli-contract.md`

## Outcome

The project has a documented, versioned, deterministic CLI contract for
inspection, including machine-readable success output, structured errors,
exit-status rules, stable identifiers, and path-redaction behavior.

## Scope

- Select the local invocation and subcommand grammar for first-horizon
  inspection.
- Define the versioned JSON output and structured-error shapes.
- Define source and segment identifier requirements, exit statuses, and
  idempotency expectations relevant to inspection.
- Define which local paths and metadata are redacted or emitted.
- Record compatibility and evolution rules for the contract.

## Explicit non-goals

- Implementing CLI commands or mutating project state.
- Multi-source, multiple-track, composition, audio, FPS, cloud, or
  natural-language agent behavior.

## Observable requirements

- Given a valid project, the contract identifies the required fields for
  source, timeline, segment, duration, and export-state inspection.
- Given an invalid request or unavailable dependency, the contract defines a
  structured error and non-zero exit status without a success-shaped result.
- Given a contract version change, compatibility and migration behavior are
  explicit and testable.
- Given a private local path, the contract defines whether it is redacted,
  normalized, or intentionally emitted.

## Definition of done

- Command, output, error, identifier, exit-status, redaction, and versioning
  rules are documented.
- Representative success and failure fixtures are specified.
- FEAT-007 and dependent tickets link to this contract without unresolved
  format ambiguity.
- No application implementation or future capability is claimed.

## Validation and evidence

- Contract review against PHASE-003 and FEAT-007.
- Schema fixture validation and structured-error examples.
- Evidence records the selected convention and unresolved limitations.
