# FEAT-009 - Share Domain Behavior Between GUI and CLI

**Feature ID:** FEAT-009
**Parent links:** OBJ-001, SCOPE-001, PHASE-003
**Capability links:** CAP-004, CAP-006, CAP-012
**Status:** complete
**Closure:** user-approved on 2026-08-22 after successful implementation,
review evidence, and target-workstation validation; remote checks remain
unavailable and are recorded as an accepted warning.
**Path history:** `features/open/FEAT-009-sharing-domain-behavior-between-gui-and-cli.md`
-> `features/closed/FEAT-009-sharing-domain-behavior-between-gui-and-cli.md`
**Horizon:** first
**Priority:** 3
**Owner:** repository planning; maintainer identity is not recorded
**Approval:** user-approved on 2026-08-21 to continue PHASE-003 planning
**Source paths:** `vision.md`, `docs/specs/project-scope.md`,
`docs/specs/capability-map.md`, `docs/planning/phases/open/PHASE-003-repeating-the-basic-edit-through-agents.md`,
`docs/specs/future-product-direction.md`, `.github/aidd-config.yml`
**Dependencies:** FEAT-007 command/error contract; FEAT-008 CLI mutation
operations; stable project and timeline domain services
**Risks:** GUI/CLI drift, duplicated validation, inconsistent error handling,
and parity tests that verify only serialized shape rather than behavior
**Affected surfaces:** editor actions, CLI adapter, project/timeline domain
services, validation, error routing, export planning, and parity tests
**Evidence path:** `evidence/phase-003-gui-cli-parity.md`

## Outcome

The interface and deterministic CLI express the same first-horizon editing
operations through shared project and timeline behavior, so an agent retry
cannot silently produce a different edit from the user-operated workflow.

## Included

- Identify and route shared domain operations for project inspection, split,
  delete, duration, persistence, and export decisions.
- Keep validation and structured error causes consistent across adapters.
- Define parity boundaries where UI-only state or presentation is intentionally
  excluded from the CLI contract.
- Verify equivalent GUI-domain and CLI-domain operations against the same
  project fixtures.

## Explicit non-goals

- Redesigning the GTK interface or adding new editing capabilities.
- Natural-language agent orchestration, remote execution, collaboration, or
  telemetry.
- Multi-source, composition, audio, FPS, or advanced effects behavior.

## Acceptance outcomes

- Given the same project and operation, GUI and CLI adapters produce equivalent
  persisted state, duration, and export-plan decisions.
- Given the same invalid operation, both adapters surface the same structured
  error category without mutating valid state.
- Given a project round trip through GUI and CLI, stable source and segment
  identifiers and deletion decisions remain intact.
- Parity evidence distinguishes shared domain behavior from intentionally
  adapter-specific presentation.

## Evidence plan

- Shared-domain and adapter contract tests.
- GUI/CLI parity tests for successful and failed operations.
- Round-trip fixtures comparing project state and export decisions.
- Local shell smoke evidence using a disposable copy of representative media.
