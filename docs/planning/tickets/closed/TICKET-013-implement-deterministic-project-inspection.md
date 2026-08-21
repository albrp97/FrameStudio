# TICKET-013 - Implement Deterministic Project Inspection

**Ticket ID:** TICKET-013  
**Objective:** OBJ-001  
**Scope:** SCOPE-001  
**Phase:** PHASE-003  
**Feature:** FEAT-007  
**Capability links:** CAP-004, CAP-006, CAP-012  
**Status:** complete  
**Closure:** user-authorized on 2026-08-21 after inspection contract,
regression, and local quality evidence; remote checks remain unavailable and
are recorded as an accepted warning.  
**Path history:** `tickets/open/TICKET-013-implement-deterministic-project-inspection.md`
-> `tickets/closed/TICKET-013-implement-deterministic-project-inspection.md`  
**Horizon:** first  
**Priority:** 2  
**Owner:** repository planning; implementer is not assigned  
**Approval:** user-approved on 2026-08-21 for implementation and testing;
configured remote checks remain unavailable  
**Provider:** auto; base and target branches are not configured in
`.github/aidd-config.yml`  
**Source paths:** `vision.md`, `docs/specs/project-scope.md`,
`docs/specs/capability-map.md`,
`docs/planning/phases/open/PHASE-003-repeating-the-basic-edit-through-agents.md`,
`docs/planning/features/open/FEAT-007-inspecting-projects-through-a-deterministic-cli.md`,
`docs/planning/tickets/open/TICKET-012-select-deterministic-cli-contract-and-inspection-schema.md`,
`AGENTS.md`, `.github/aidd-config.yml`  
**Dependencies:** TICKET-012; versioned project persistence; source probing
and ffprobe availability  
**Risks:** inspection output drifting from project state, position-only
references, unsupported media errors, and accidental sensitive metadata output  
**Affected surfaces:** CLI entry point, project model, media probing,
serialization, structured errors, docs, and tests  
**Evidence path:** `evidence/phase-003-cli-inspection.md`

## Outcome

An agent can inspect a valid one-source project through the selected CLI
contract and receive deterministic machine-readable source, timeline, segment,
duration, and export-state information.

## Scope

- Add the first-horizon project inspection command.
- Reuse the existing project and media-probing models rather than duplicating
  parsing rules.
- Emit stable source and segment identifiers, boundaries, deletion state,
  playhead, edited duration, and relevant export metadata.
- Return the documented structured errors and exit statuses.

## Explicit non-goals

- Mutating project state, editing segments, or exporting media.
- Multi-source, multiple-track, composition, audio, FPS, or remote operation.

## Observable requirements

- Given a valid project, inspection returns contract-compliant JSON with
  equivalent repeated results for unchanged inputs.
- Given a missing or incompatible project, inspection returns the documented
  structured error and non-zero status without altering files.
- Given a missing source or unavailable probe tool, inspection reports an
  actionable error and does not fabricate metadata.
- Given a project with deleted segments, inspection reports both retained
  segment identity and edited duration semantics.

## Definition of done

- The command is documented and covered by focused success and failure tests.
- Output is produced through the TICKET-012 contract.
- Existing GUI/project behavior and source-preservation guarantees remain
  unchanged.
- FEAT-007 inspection evidence is recorded.

## Validation and evidence

- CLI contract tests and project serialization tests.
- Disposable one-source inspection smoke test with redacted output evidence.
- Existing baseline and local quality commands.
