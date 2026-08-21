# TICKET-016 - Route GUI and CLI Through Shared Domain Operations

**Ticket ID:** TICKET-016  
**Objective:** OBJ-001  
**Scope:** SCOPE-001  
**Phase:** PHASE-003  
**Feature:** FEAT-009  
**Capability links:** CAP-004, CAP-006, CAP-012  
**Status:** complete  
**Closure:** user-authorized on 2026-08-21 after shared-domain, GUI/CLI
parity, and local quality evidence; remote checks remain unavailable and are
recorded as an accepted warning.  
**Path history:** `tickets/open/TICKET-016-routing-gui-and-cli-through-shared-domain-operations.md`
-> `tickets/closed/TICKET-016-routing-gui-and-cli-through-shared-domain-operations.md`  
**Horizon:** first  
**Priority:** 5  
**Owner:** repository planning; implementer is not assigned  
**Approval:** user-approved on 2026-08-21 for implementation and testing;
configured remote checks remain unavailable  
**Provider:** auto; base and target branches are not configured in
`.github/aidd-config.yml`  
**Source paths:** `vision.md`, `docs/specs/project-scope.md`,
`docs/specs/capability-map.md`,
`docs/planning/phases/open/PHASE-003-repeating-the-basic-edit-through-agents.md`,
`docs/planning/features/open/FEAT-009-sharing-domain-behavior-between-gui-and-cli.md`,
`docs/planning/tickets/open/TICKET-014-implement-one-source-edit-commands.md`,
`docs/planning/tickets/open/TICKET-015-integrate-safe-deterministic-cli-export.md`,
`AGENTS.md`, `.github/aidd-config.yml`  
**Dependencies:** TICKET-014 and TICKET-015; stable project, timeline, export,
  and structured-error services  
**Risks:** duplicated rules hidden behind adapters, behavior changes in the
  existing editor, and UI-specific state leaking into the CLI contract  
**Affected surfaces:** editor actions, CLI adapter, project/timeline domain
  services, validation, error routing, export planning, and tests  
**Evidence path:** `evidence/phase-003-gui-cli-parity.md`

## Outcome

The editor and CLI route first-horizon inspection, editing, persistence, and
export decisions through shared domain behavior rather than maintaining
independent semantics.

## Scope

- Identify and extract shared operation boundaries where current adapters
  duplicate project, timeline, validation, or export decisions.
- Route GUI and CLI requests through the shared boundaries without changing
  user-facing behavior.
- Keep UI-only presentation and playback state outside the machine-readable
  CLI contract.
- Preserve structured error causes and safe failure recovery across adapters.

## Explicit non-goals

- Adding new editing capabilities or redesigning the GTK interface.
- Multi-source, composition, audio, FPS, cloud, or natural-language agent
  behavior.
- Replacing protected legacy scripts.

## Observable requirements

- Given the same project and operation, GUI and CLI adapters use equivalent
  domain validation and produce equivalent persisted state.
- Given the same invalid operation, both adapters expose the same error
  category without mutating valid state.
- Given an export request, both adapters use equivalent route selection and
  output-safety behavior.
- UI-only presentation state is not serialized as a required CLI field.

## Definition of done

- Shared boundaries are documented and used by both adapters.
- Existing editor tests remain green and new adapter tests cover changed paths.
- No first-horizon behavior is silently broadened.
- FEAT-009 shared-domain evidence is recorded.

## Validation and evidence

- Focused shared-domain and adapter contract tests.
- Existing editor regression tests and safe-export tests.
- Review of persisted state and structured errors across both adapters.
