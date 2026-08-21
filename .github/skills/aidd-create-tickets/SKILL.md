---
name: aidd-create-tickets
description: Decompose an approved feature into focused, verifiable tickets with evidence and gate traceability. Use when implementation units are needed.
---

# aidd-create-tickets

Produce bounded tickets that can be implemented and verified independently.

Apply [../planning-artifact-lifecycle.md](../planning-artifact-lifecycle.md)
for record paths, status classification, index synchronization, and
open/closed moves.

## Contract

```sudolang
PlanningSkillContract {
  inputs[]
  outputs[]
  filesRead[]
  filesWritten[]
  sideEffects[]
  owner
  approvalConditions[]
  stopConditions[]
  requiredEvidence[]
  failureAndBlockerBehavior
  mayImplement = false
  mayCommit = false
  mayPush = false
  mayMerge = false
}
```

## Inputs

- Repository root and the relevant approved planning artifact IDs.
- `.github/aidd-config.yml` when present; its artifact paths, vocabulary, statuses, depth, and approval rules override defaults.
- Existing ancestor/child records, repository map, requirements, decisions, and evidence available at configured paths.
- The backlog and every ticket record in both the configured ticket `open` and
  `closed` directories.
- User request and any explicitly supplied constraints; unknowns remain unresolved.

## Outputs

- Markdown/SudoLang planning result or an explicitly authorized artifact update.
- One record per ticket under the configured ticket `open` directory, plus an
  updated backlog/list containing current paths for open and closed tickets.
- Stable IDs using configured prefixes (`OBJ`, `SCOPE`, `CAP`, `PHASE`, `FEAT`, `TICKET`), explicit status, parent/child links, and coverage/evidence links.
- A user-validation plan with exact post-implementation steps, expected
  visible and persisted/external results, evidence to return, and pass criteria.
- A concise readiness, approval, warning, or blocker report; no implied downstream work.

## Side effects and ownership

- This skill owns only the planning layer named in its title and its review/report output.
- It may write only configured planning artifacts when the caller authorizes mutation; otherwise it is read-only.
- New ticket records are created in `open`. An authorized transition to a
  configured closed status moves the same record to `closed` and synchronizes
  the backlog; reopening moves it back to `open`.
- It never owns implementation, branches, commits, pushes, merges, provider operations, or delivery readiness.
- Every write records owner, reason, source/evidence links, timestamp or revision, and affected IDs; preserve history rather than overwrite it.

## Boundaries

- Canonical hierarchy is **objective -> scope -> capability -> phase -> feature -> ticket**.
- Use adaptive depth: lightweight for a small fix or documentation change, standard for a meaningful change, full for a broad initiative; never invent layers merely for ceremony.
- A child requires one existing, unblocked, approved parent. No silent downstream generation, fan-out, or scope expansion.
- Preserve stable IDs on rename; maintain explicit statuses (`draft`, `confirmed`, `needs-review`, `blocked`, `complete`) and valid transitions.
- Keep requirements observable and implementation-agnostic. Reject cross-parent or oversized work when it cannot be independently verified.

## Metadata and traceability

Every artifact or report must include: ID, title, status, parent ID(s), objective/scope ancestry, capability/phase/feature links as applicable, owner, source paths, dependencies, risks, non-goals, affected surfaces, approval state, evidence/coverage links, and last-updated revision or timestamp. A ticket is traceable only when it links back to its objective and forward to requirements, protected behaviors, gates, and an evidence path.

## Failure and blocker behavior

Missing parent, approval, evidence, command, ownership, or required capability is a blocker or coverage gap—not a pass. Stop before child generation or readiness claims, name the exact missing input and affected IDs, and propose the smallest next action. Material changes route to `aidd-change-control`; routine corrections must not masquerade as a replan.

## Process

```sudolang
createTickets(request) => TicketSet {
  1. require an approved, unblocked feature with one phase and capability traceability
  2. read both ticket status directories and preserve existing TICKET IDs
  3. create stable TICKET IDs in the ticket open directory with one outcome, explicit scope/non-goals, dependencies, affected surfaces, definition of done, and a user-validation plan
  4. link every ticket to its parent feature, phase, capability, requirements, protected behaviors, commands or steps, user-validation plan, gates, and evidence path
  5. synchronize the backlog with every current ticket path
  6. move a record between open and closed only when its authorized status transition changes classification
  7. reject oversized work, cross-feature scope, unresolved prerequisites, and tickets lacking observable verification
  8. obtain configured approval; never mark ready or generate execution work without baseline/evidence prerequisites
}
```

## Constraints

```sudolang
Constraints {
  Read configured artifacts and applicable ancestors before proposing changes
  Read both open and closed ticket directories; never create duplicate IDs
  Create new tickets in open and move records when status classification changes
  Keep the backlog synchronized with current ticket paths
  Preserve path history and stable IDs across status moves
  Do not claim readiness without terminal evidence for every required gate
  Do not close a ticket while required user-validation evidence is missing,
  failed, or blocked
  Do not create or modify artifacts outside the named planning layer
  Escalate ambiguity, conflict, or material change instead of guessing
}
```

## Commands

```sudolang
Commands {
  /create-tickets [feature-id]
  - derive focused tickets for one approved feature only
}
```
