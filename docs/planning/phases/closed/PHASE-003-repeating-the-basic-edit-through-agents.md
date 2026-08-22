# PHASE-003 - Repeating the Basic Edit Through Agents

**Phase ID:** PHASE-003
**Parent links:** OBJ-001, SCOPE-001
**Capability links:** CAP-004, CAP-006, CAP-012
**Sequence:** 3
**Status:** complete
**Closure:** user-approved on 2026-08-22 after successful implementation,
review evidence, and target-workstation validation; remote checks remain
unavailable and are recorded as an accepted warning.
**Path history:** `phases/open/PHASE-003-repeating-the-basic-edit-through-agents.md`
-> `phases/closed/PHASE-003-repeating-the-basic-edit-through-agents.md`
**Horizon:** first
**Owner:** repository planning; maintainer identity is not recorded
**Approval:** user-approved on 2026-08-21 before feature generation
**Source paths:** `vision.md`, `docs/specs/project-scope.md`,
`docs/specs/capability-map.md`, `docs/planning/phases.md`,
`docs/planning/repo-map.md`, `.github/aidd-config.yml`
**Migration source:** `docs/planning/phases.md`, inline section
`PHASE-003 - Repeating the Basic Edit Through Agents`; migrated on
2026-08-21 with the phase content preserved.
**Affected surfaces:** project schema, deterministic CLI, domain operations,
structured errors, export decisions, and automation tests

## Outcome

Copilot or another agent can inspect and perform the same
one-source split/delete/save/export workflow represented by the interface.

### Included

- Define a stable, versioned, machine-readable project-file contract.
- Define deterministic CLI commands for project inspection, source import,
  split, delete, save/reopen, duration inspection, and export.
- Use stable source and segment identifiers rather than position-only
  references where future edits could make positions ambiguous.
- Return structured success and error output for invalid ranges, missing
  sources, unsupported media, unavailable tools, and failed exports.
- Ensure CLI operations and interface operations share the same domain state
  and validation rules.
- Document idempotency and behavior when an operation is repeated.

### Explicit non-goals

- Future multi-source, triplicate, audio-normalization, or FPS commands.
- General natural-language agent orchestration inside the application.
- Cloud APIs, collaboration, accounts, or remote project storage.

### Entry conditions

- PHASE-001 and PHASE-002 exit evidence is complete.
- Project schema and timeline identifiers are stable enough to expose.
- Interface behavior and error cases are documented as observable outcomes.
- A local CLI invocation and machine-readable output convention are selected.

### Exit conditions

- CLI can inspect a project and perform the same first-horizon operations as
  the interface.
- Equivalent GUI and CLI operations produce equivalent project state and
  export decisions.
- Structured errors are deterministic, non-zero on failure, and preserve
  valid state.
- CLI round-trip and smoke-test evidence is recorded.
- The first-horizon definition of done is complete without requiring Resolve.

### Dependencies and risks

- Depends on a stable project schema and timeline semantics.
- GUI/CLI drift could create different export behavior or invalid state.
- Unclear operation idempotency could make agent retries unsafe.

### Validation and evidence

- CLI contract tests and project serialization tests.
- Parity tests comparing interface-domain operations with CLI-domain
  operations.
- Local shell smoke test on a disposable copy of representative media.
- Structured output and failure evidence with private paths redacted where
  they are not required.
