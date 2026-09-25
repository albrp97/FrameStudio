---
name: aidd-ticket-creator
description: Plan and execute delivery through approved phases, features, and focused tickets with configurable gates and evidence. Use when work must be decomposed or one approved ticket must be delivered.
---

import ../lifecycle-interface.md

# Phase, Feature, and Ticket Creator

```sudolang
Lifecycle {
  profile = orchestration
  overrides {
    mayCommit = false
    mayPush = false
    mayResolve = false
    mayMerge = false
  }
}
```

Organize meaningful work through the hierarchy **phase -> feature -> ticket**:

- a **phase** is a top-level delivery stage with an outcome, entry conditions,
  exit conditions, and intended sequence;
- a **feature** is a meaningful user or operational outcome inside one phase;
- a **ticket** is a focused implementation and validation unit inside one
  feature.

Do not create child artifacts before their parent is defined and approved.
Small standalone changes may use one ticket without inventing parent artifacts,
while still recording existing ownership when it exists.

Apply [../planning-artifact-lifecycle.md](../planning-artifact-lifecycle.md)
for the required `open`/`closed` record directories, status transitions, stable
IDs, and index synchronization.
Apply [../development-mode.md](../development-mode.md) when coordinating
planning approvals, execution, validation, and ticket iteration.

## Shared context

Load [context](./references/context.md) when resolving planning records,
ticket contracts, status types, or configured storage.

## Planning depth

```sudolang
planningDepth(request) {
  small fix or documentation change => one focused ticket
  meaningful change => one approved phase containing one or more features
  broad initiative => ordered phases, features inside each phase, then tickets
  new project or repository onboarding => repository map -> objective -> scope ->
    capabilities -> phases -> features -> tickets
}
```

Do not apply a universal line-count rule. Documentation, infrastructure,
migrations, and verification tickets are focused by scope and evidence rather
than code size.

## Phase and feature planning

```sudolang
planHierarchy(request) {
  1. classify the planning depth
  2. scan both lifecycle directories and resolve each existing record by stable ID
  3. locate or define the phase outcome, entry conditions, and exit conditions
  4. review the phase and obtain the configured approval in guided mode, or
     record bootstrap-authorized approval in automatic mode
  5. locate or define the feature outcome, capabilities, scope, non-goals,
     dependencies, risks, affected surfaces, and verification intent
  6. review the feature and obtain the configured approval in guided mode, or
     record bootstrap-authorized approval in automatic mode
  7. confirm that the feature is ready for ticket decomposition
}
```

## Ticket planning

```sudolang
planTickets(feature) {
  1. select the active phase and feature, or require the user to identify them
  2. derive atomic tickets with explicit scope boundaries
  3. map each ticket to requirements, protected behavior, evidence, and gates
  4. assign stable IDs and parent links without reusing another ticket's ID
  5. assess dependencies, agent needs, and file ownership
  6. order tickets by dependency and logical delivery flow
  7. define inputs, outputs, success criteria, functionality flows, at least
     one executable automated functionality test per acceptance outcome, and
     the exact post-implementation user-validation handoff
  8. define exit gates for planning, baseline, implementation, verification,
     automated functionality, user validation, local quality, and PR readiness
  9. create new ticket records in the configured ticket open directory and
     synchronize the backlog with current paths
}
```

Every ticket must be independently verifiable. A ticket may be blocked when a
required decision, command, service, or capability is unavailable.

## Planning operations

```sudolang
Operations {
  createPhase(request) - define or update one phase after scope/capability review
  createFeature(request) - define one outcome feature inside an approved phase
  createTickets(request) - derive tickets for one approved feature
  groomBacklog(request) - rank and repair tickets without changing the plan hierarchy
  reviewLayer(request) - evaluate one artifact before child generation
}
```

Use `/create-phases`, `/create-features`, `/create-tickets`, and
`/review-planning-layer` for explicit operations. `/ticket` remains a
compatibility entrypoint for feature-and-ticket planning.

## Plan validation

`/plan` must report the active phase, features, ready/blocked tickets, contract
completeness, discovered commands, required gates, evidence path, and the
reason for the recommended next ticket. It must not suggest implementation
readiness when a prerequisite is missing.

The recommended ticket must be selected from the active phase first. Later
phase work is not ready merely because it has fewer dependencies.

## Execution and record references

Load [execution and templates](./references/execution-and-templates.md) only
when executing a ticket, evaluating closure, or writing phase, feature, or
ticket records.

## Constraints

```sudolang
Constraints {
  Never execute multiple tickets unless independence, ownership, and integration are approved
  Never change scope silently; re-plan the smallest affected artifact
  Never invent parent artifacts for a small standalone change
  Never create child artifacts under a missing, blocked, or unapproved parent
  Never use a title as a substitute for a stable ID or parent link
  Never mark a feature or phase covered when a capability or scope item is orphaned
  Never skip a configured required gate or convert missing evidence into pass
  Never leave an artifact duplicated in open and closed or indexed at a stale path
  Never close a feature or phase while required children remain open or incomplete
  Never close a ticket without recorded user-validation evidence or approved
  not-applicable evidence
  Preserve stable IDs and path history when moving records between lifecycle directories
  Never autonomously commit or push before the configured readiness checks;
    explicit user delivery directives route to aidd-commit or aidd-push and
    record bypassed gates
  Keep requirements observable and implementation-agnostic
  If blocked or uncertain, report the blocker instead of inventing a rule
}
```

## Commands

```sudolang
Commands {
  /help
  /ticket - create or update a feature and its tickets inside an approved phase
  /execute - execute one approved ticket
  /list [(phases|features|tickets) = tickets] - list planning artifacts
}
```
