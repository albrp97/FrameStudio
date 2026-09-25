---
name: aidd-create-tickets
description: Decompose an approved feature into focused, verifiable tickets with evidence and gate traceability. Use when implementation units are needed.
---

import ../planning-skill-interface.md

# aidd-create-tickets

Produce bounded tickets that can be implemented and verified independently.

Apply [../development-mode.md](../development-mode.md) when resolving feature
approval, ticket readiness, and the handoff to execution.

## Contract

```sudolang
Lifecycle {
  profile = planningMutation
}

PlanningSkill {
  profile = planningMutation
  layer = ticket
  parentLayers = [phase, feature, capability]
  childLayers = []
  writableArtifacts = [ticketRecords, backlog]
  mode = inspect | draft | write
}
```

## Inputs

- Repository root and the relevant approved planning artifact IDs.
- The backlog and every ticket record in both the configured ticket `open` and
  `closed` directories.

## Outputs

- One record per ticket under the configured ticket `open` directory, plus an
  updated backlog/list containing current paths for open and closed tickets.
- A user-validation plan with exact post-implementation steps, expected
  visible and persisted/external results, evidence to return, and pass criteria.
- At least one executable automated functionality test per acceptance outcome,
  including its command or script, supported system boundary, assertions, and
  expected state or external effect.

## Process

```sudolang
createTickets(request) => TicketSet {
  1. require an approved, unblocked feature with one phase and capability traceability
  2. read both ticket status directories and preserve existing TICKET IDs
  3. create stable TICKET IDs in the ticket open directory with one outcome, explicit scope/non-goals, dependencies, affected surfaces, definition of done, an automated functionality test, and a user-validation plan
  4. link every ticket to its parent feature, phase, capability, requirements, protected behaviors, commands or steps, automated functionality test, user-validation plan, gates, and evidence path
  5. synchronize the backlog with every current ticket path
  6. move a record between open and closed only when its authorized status transition changes classification
  7. reject oversized work, cross-feature scope, unresolved prerequisites, and
     tickets lacking an executable automated functionality test with observable
     assertions
  8. obtain configured approval in guided mode; in automatic mode, record the
     bootstrap-authorized decision. In both modes, never mark ready or generate
     execution work without baseline/evidence prerequisites
}
```

## Constraints

```sudolang
Constraints {
  Read both open and closed ticket directories; never create duplicate IDs
  Create new tickets in open and move records when status classification changes
  Keep the backlog synchronized with current ticket paths
  Preserve path history and stable IDs across status moves
  Do not approve a ticket without an executable automated functionality test
    for each acceptance outcome when the functionality gate is enabled
  Do not close a guided ticket while required user-validation evidence is
  missing, failed, or blocked
  Do not close an automatic ticket while required automaticValidation evidence
  is missing, failed, or blocked
  Never classify automatic ticket readiness or closure without the exact
    Rubber Duck `gpt-5.6-luna` high-reasoning `all-validation` profile
  Do not create or modify artifacts outside the named planning layer
  Escalate ambiguity, conflict, or material change instead of guessing
  In automatic mode, do not wait for user approval or validation; require the
  automatic validation and evidence gates defined by the mode contract
}
```

## Commands

```sudolang
Commands {
  /create-tickets [feature-id]
  - derive focused tickets for one approved feature only
}
```
