---
name: aidd-ticket-creator
description: Plan and execute delivery through approved phases, features, and focused tickets with configurable gates and evidence.
---

# Phase, Feature, and Ticket Creator

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

## Shared context

Read `.github/aidd-config.yml`, the repository map, objective, scope,
capability map, phase index, feature index, backlog, active feature record,
all phase/feature/ticket records in both their `open` and `closed` directories,
and the repository's manifests/CI before planning or execution when those
artifacts exist. Resolve paths through `delivery.artifacts`; repository
conventions override the portable defaults, but there must be one authoritative
source for each planning layer.

```sudolang
PhaseStatus = proposed | planned | active | completed | blocked | cancelled
FeatureStatus = proposed | planned | active | completed | blocked | cancelled
TicketStatus = pending | baseline | inProgress | verifying | gated |
  completed | blocked | cancelled

TicketContract {
  repository
  provider
  phase
  feature
  ticket
  objective
  acceptanceCriteria[]
  scope[]
  nonGoals[]
  dependencies[]
  risks[]
  affectedSurfaces[]
  baseBranch
  targetBranch
  commands
  qualityGates[]
  functionalityFlows[]
  userValidationPlan
  protectedBehaviors[]
  evidencePath
  definitionOfDone[]
  approvalMode
}

PlanningArtifact {
  id
  status
  reviewedAt
  sourceReferences[]
  scopeHorizon
  confidence
  openQuestions[]
  parentLinks[]
  childLinks[]
  coverage[]
}

PhaseRecord {
  artifact: PlanningArtifact
  outcome
  sequence
  entryConditions[]
  exitConditions[]
  dependencies[]
  validationFocus[]
}

FeatureRecord {
  artifact: PlanningArtifact
  phase
  outcome
  capabilities[]
  scope[]
  nonGoals[]
  validationIntent[]
}

RecordStorage {
  phaseOpenDirectory
  phaseClosedDirectory
  featureOpenDirectory
  featureClosedDirectory
  ticketOpenDirectory
  ticketClosedDirectory
  recordFilename
  indexPaths[]
  pathHistory[]
}
```

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
  4. review the phase and obtain the configured approval
  5. locate or define the feature outcome, capabilities, scope, non-goals,
     dependencies, risks, affected surfaces, and verification intent
  6. review the feature and obtain the configured approval
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
  7. define inputs, outputs, success criteria, functionality flows, and the
     exact post-implementation user-validation handoff
  8. define exit gates for planning, baseline, implementation, verification,
     user validation, local quality, and PR readiness
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

## Execution protocol

```sudolang
executeTicket(ticket) {
  1. verify the current branch, worktree, intended base, and ticket ownership
  2. resolve approval mode from configuration
  3. establish the protected baseline when required and record it with /evidence
  4. execute only this ticket using /aidd-tdd or the strongest applicable method
  5. verify functionality and configured local quality gates
  6. append all results, failures, fixes, blockers, warnings, and artifacts
  7. run /review and produce the user-validation handoff
  8. wait for the user's terminal validation result and append it to evidence
  9. proceed only when the configured gates, user validation, and approval are
     satisfied
}
```

The ticket creator coordinates the lifecycle; it does not invent commands or
claim that another skill's unrecorded work passed.

## Closure gate

The ticket remains in `verifying` after implementation until the user receives
the exact validation steps and returns `PASS`, or an approved
`NOT APPLICABLE` result is recorded. `FAIL` and `BLOCKED` keep the ticket in an
open status and require remediation or an explicit follow-up. Only then may
the completion routine update evidence, set a terminal status, move the same
record to `closed`, and synchronize the backlog and parent record.

## Feature record template

```markdown
# ${FeatureName} Feature

**Phase**: ${PhaseName}
**Status**: PLANNED
**Outcome**: ${briefOutcome}
**Scope**: ${scope}
**Non-goals**: ${nonGoals}
**Evidence**: ${evidencePath}
**Definition of done**: ${definitionOfDone}

## Overview

WHY: ${singleParagraphExplainingTheUserOrOperationalBenefit}

## ${TicketName}

${briefTicketDescription}

**Requirements**:
- Given ${situation}, should ${jobToDo}

**Protected behavior**:
- ${existingFlow}

**Verification**:
- ${evidenceType}: ${commandOrSteps}

**User validation before closure**:
- ${userValidationSteps}
```

## Completion

```sudolang
onComplete(ticket, evidence) {
  1. verify terminal technical evidence and the required user-validation result
  2. mark the ticket completed only after the user returns PASS or an approved
     NOT APPLICABLE decision is recorded
  3. move the same ticket record from open to closed, preserving its stable ID,
     content, and path history
  4. update the backlog index and feature record with the ticket's current path
     without rewriting history
  5. when all required tickets are complete or cancelled, mark the feature
     completed and move its record from open to closed
  6. update the phase only after its exit conditions are satisfied; then move
     the phase from open to closed when its configured terminal status is set
  7. when a closed artifact is reopened, update its status and move it back to
     open before generating or executing new children
  8. retain evidence according to delivery.evidence.retention
}
```

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
  Never commit or push before the configured readiness checks
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
