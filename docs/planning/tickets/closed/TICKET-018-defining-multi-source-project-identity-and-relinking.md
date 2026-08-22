# TICKET-018 - Define Multi-Source Project Identity and Relinking

**Ticket ID:** TICKET-018
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Phase:** PHASE-004
**Feature:** FEAT-010
**Capability links:** CAP-007, CAP-012
**Status:** complete
**Closure:** user-approved on 2026-08-22 after successful implementation,
review evidence, and target-workstation validation; remote checks remain
unavailable and are recorded as an accepted warning.
**Path history:** `tickets/open/TICKET-018-defining-multi-source-project-identity-and-relinking.md`
-> `tickets/closed/TICKET-018-defining-multi-source-project-identity-and-relinking.md`
**Horizon:** future
**Priority:** 1
**Owner:** repository implementation in the active Phase 4 worktree
**Approval:** user-authorized on 2026-08-21 to prepare and implement all
current PHASE-004 open tickets; human validation remains required before
closure
**Provider:** auto; base and target branches are not configured in
`.github/aidd-config.yml`
**Source paths:** `vision.md`, `docs/specs/project-scope.md`,
`docs/specs/capability-map.md`,
`docs/planning/phases/open/PHASE-004-combining-mixed-source-footage.md`,
`docs/planning/features/open/FEAT-010-importing-and-retaining-mixed-source-project-identity.md`,
`docs/specs/future-product-direction.md`, `AGENTS.md`,
`.github/aidd-config.yml`
**Dependencies:** TICKET-017; the versioned one-source project schema; stable
CLI error and identifier conventions; representative mixed-source fixtures
**Risks:** unstable identifiers, incompatible schema migration, ambiguous
source relinking, leaked local paths, and untestable metadata assumptions
**Affected surfaces:** project schema, source registry, persistence,
relinking/error contract, CLI inspection, documentation, and tests
**Evidence path:** `evidence/phase-004-source-contract.md`

## Outcome

The project has an approved, versioned contract for representing multiple
source videos and their stable identities, metadata, source-level settings,
and missing-source behavior.

## Scope

- Define source, clip, and project identity rules for multiple inputs.
- Define required probe metadata for dimensions, orientation, frame rate,
  codec/container, duration, and audio presence.
- Define source-path normalization, moved-source detection, relinking, and
  missing-source errors.
- Define compatibility behavior for reopening existing one-source projects.
- Define redaction and deterministic inspection expectations for local paths.

## Explicit non-goals

- Implementing the import UI or mixed-source timeline behavior.
- Choosing output-canvas, audio-normalization, triplicate, or FPS policies.
- Adding copy/paste, multi-track editing, or remote media management.

## Observable requirements

- Given multiple source entries, the schema preserves stable source identity
  independently of path spelling or timeline position.
- Given a moved or missing source, reopen reports the affected identity and
  does not replace the last valid project.
- Given an existing one-source project, the migration path is explicit and
  deterministic without changing its editing semantics.
- Given inspection output, private paths are redacted or emitted only under
  the documented opt-in contract.

## Commands and quality gates

- `make test`
- `make contract`
- `make check`
- `make quality PYTHON=.venv/bin/python`
- Review of schema fixtures and migration examples

## Functionality flows

- Inspect a multi-source fixture and compare repeated output.
- Reopen a fixture after changing one source path and verify the structured
  relinking error.
- Load a versioned one-source fixture and verify compatibility behavior.

## User validation before closure

Review the proposed project JSON with two different local video identities,
confirm that source-level metadata is distinct from later segment state, and
confirm the missing-source and path-redaction behavior.

## Protected behavior

The existing versioned one-source project format, stable segment identifiers,
path-redaction rules, atomic saves, and deterministic Phase 3 inspection
contract remain supported or are migrated explicitly.

## Definition of done

- The multi-source identity, metadata, relinking, migration, and redaction
  rules are documented and represented by fixtures.
- Structured failure cases and compatibility behavior are testable.
- FEAT-010 has a reviewed contract before import implementation begins.
