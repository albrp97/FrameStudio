---
name: aidd-agent-orchestrator
description: Route and coordinate software work through delivery phases, features, tickets, evidence, quality gates, and provider-specific operations.
---

# Aiden Agent Orchestrator

Coordinate specialized skills without losing delivery context or allowing a
sub-agent to claim readiness without evidence.

Apply [../planning-artifact-lifecycle.md](../planning-artifact-lifecycle.md)
when resolving planning records and routing status transitions. A physical
move between `open` and `closed` is part of the lifecycle transition, not a
separate cleanup step.

## Delivery state

```sudolang
DeliveryState = proposed | discovered | scoped | capabilitiesApproved |
  phasesApproved | featuresApproved | ticketsReady | implementationReady |
  baseline | implementing | verifying | gated | prOpen | reviewLoop | ready |
  blocked | complete

VersionControlState = unknown | uncommitted | staged | committable |
  committed | pushable | published

NextAction {
  step
  skill
  command
  reason
  blockers[]
  approvalRequired
}

DeliveryContext {
  repository
  provider
  phase
  feature
  ticket
  objective
  planningDepth
  repositoryMap
  capabilities[]
  acceptanceCriteria[]
  scope[]
  nonGoals[]
  dependencies[]
  risks[]
  affectedSurfaces[]
  commands
  requiredGates[]
  evidencePath
  approvalMode
  versionControl: VersionControlContext
  staticAnalysis
  pullRequestState
  pullRequestRequired
  nextAction: NextAction
}

VersionControlContext {
  state: VersionControlState
  sourceBranch
  baseBranch
  upstream
  localHead
  remoteHead
  commitsAhead
  commitsBehind
  stagedPaths[]
  uncommittedPaths[]
  dedicatedBranch
}
```

Initialize context from `.github/aidd-config.yml`, the configured repository
map/objective/scope/capability/phase/feature/backlog/ticket records in both
their `open` and `closed` directories, repository manifests and CI, and the
user's direct request. Repository-specific values
override generic defaults. Missing information that affects a gate is a
blocker, not an invitation to guess.

## Skill routing

```sudolang
Agents {
  please: general constraints, scope, approval, and readiness reporting
  productmanager: discovery, outcomes, stakeholders, and delivery contract
  requirements: observable requirements and verification traceability
  planningBootstrap: repository mapping, planning depth, and artifact discovery
  repositoryMap: durable repository surface mapping
  capabilityMap: scope-to-capability coverage
  phases: ordered delivery phases and exit conditions
  features: outcome features inside phases
  tickets: focused ticket decomposition and backlog
  planningReview: planning-layer completeness and coverage review
  grooming: routine backlog maintenance and prioritization
  phaseFeedback: planned-versus-delivered phase learning
  changeControl: local correction versus material replan decisions
  preimplementation: active-ticket readiness checklist
  ticketCreator: phase, feature, ticket planning and execution ownership
  tdd: baseline, tests, implementation, and regression evidence
  evidence: append-only delivery evidence
  review: quality, security, scope, evidence review, and approved remediation orchestration
  staticAnalysis: deterministic formatter, lint, type, complexity, duplication,
    dependency, security, SonarQube, and churn analysis
  pr: provider-neutral pull-request lifecycle and provider adapter
  parallel: safe independent delegation
  pipeline: explicit ticket-list execution
  commit: staged-scope and readiness checks
  push: remote branch publication and push verification
}

route(request, context) {
  repositoryOnboarding => planningBootstrap |> repositoryMap
  discovery => productmanager
  scopeDefinition => productmanager
  capabilityPlanning => capabilityMap
  phasePlanning => phases
  featurePlanning => features
  ticketPlanning => requirements |> tickets
  backlogMaintenance => grooming
  planningReview => planningReview
  phaseCloseout => phaseFeedback
  materialChange => changeControl
  implementationReadiness => preimplementation
  implementation => ticketCreator |> tdd
  bugFix => aidd-fix
  verification => user-testing | run-test | tdd
  staticAnalysis => staticAnalysis
  review => review (review invokes staticAnalysis before readiness)
  deliveryOperations => commit | push | pr | clean-pr-branch
}
```

## Next-action routing

After every routed response, return one `NextAction` based on the current
state and the first unresolved gate or decision:

```sudolang
recommendNext(context, evidence) {
  if context.blocked => return the skill that resolves the named blocker
  if foundationalContextMissing => projectBootstrap
  if state in {proposed, discovered} and discoveryMissing => productmanager
  if state == scoped and capabilitiesMissing => capabilityMap
  if state == capabilitiesApproved and phasesMissing => phases
  if state == phasesApproved and featuresMissing => features
  if state == featuresApproved and ticketsMissing => tickets
  if state == ticketsReady => preimplementation
  if state in {implementationReady, baseline, implementing} => tdd |> execute
  if state == verifying and userValidationMissing => user-testing
  if state == verifying and userValidationFailedOrBlocked => aidd-fix | changeControl
  if state == verifying and requiredEvidenceMissing => evidence
  if state == gated and reviewMissing => review
  if state == gated and versionControl.state in {uncommitted, staged, committable} => commit
  if state == gated and versionControl.state in {committed, pushable} and
    versionControl.commitsAhead > 0 => push
  if state == gated and versionControl.state == published and
    pullRequestRequired and pullRequestState == notStarted => pr
  if state == gated and versionControl.state == published and
    pullRequestRequired and pullRequestState in {open, checksRunning, feedback,
    mergeBlocked, ready} => pr
  if state == gated and versionControl.state == published and
    not pullRequestRequired => configuredCloseout
  if state in {prOpen, reviewLoop} => pr
  if state == complete => phaseFeedback | plan according to remaining work
  return aidd-please for general routing when no active context is resolvable
}
```

The response must render the result as a concise `Next step`, `Skill`, and
`Why` handoff. Delivery operations are ordered: commit the reviewed local
scope, push the resulting commit when it is unpublished or ahead, then create
or recheck the PR when policy requires one. A recommendation is guidance, not
implicit authorization to execute the command.

Load domain skills progressively after the lifecycle skill:

- frontend/language: `aidd-javascript`, `aidd-react`, `aidd-lit`, `aidd-ui`,
  `aidd-layout`, `aidd-autodux`, or `aidd-javascript-io-effects`;
- backend/architecture: `aidd-ecs`, `aidd-service`, `aidd-namespace`,
  `aidd-structure`, or `aidd-observe`;
- security/failure analysis: `aidd-jwt-security`,
  `aidd-timing-safe-compare`, or `aidd-error-causes`;
- communication/syntax: `aidd-write` or `aidd-sudolang-syntax`.

Every selected domain skill receives requirement IDs, affected surfaces,
constraints, expected evidence, and unresolved blockers. Domain skills do not
own branches, PR threads, or delivery readiness.

## State transitions

```sudolang
transitions {
  proposed -> discovered -> scoped
  scoped -> capabilitiesApproved when capability coverage is complete or not required
  capabilitiesApproved -> phasesApproved when phase outcomes and boundaries are approved
  phasesApproved -> featuresApproved when features map to exactly one phase
  featuresApproved -> ticketsReady when tickets map to one feature and have evidence
  ticketsReady -> implementationReady when the active ticket checklist passes
  implementationReady -> baseline when the contract and prerequisites are approved
  baseline -> implementing when the protected baseline is recorded
  implementing -> verifying when the ticket scope is complete
  verifying -> gated when functionality, local gates, and required
    user-validation and review evidence have terminal results
  gated -> prOpen only after a required commit exists and the source branch is
    published; commit and push are version-control substates, not skipped
    lifecycle transitions
  prOpen -> reviewLoop when remote checks or feedback remain
  reviewLoop -> ready when required checks, approvals, conversations, and evidence are terminal
  any -> blocked when a required decision, capability, or gate is unavailable
  ready -> complete only after merge/close policy is satisfied
}
```

recordTransitions {
  nonTerminalStatus -> openDirectory
  complete | completed | cancelled -> closedDirectory
  closedDirectory -> openDirectory when an authorized reopen changes status
}

Do not skip a configured transition. A delegated agent may return completed
work and evidence, but only the orchestrator aggregates it, evaluates shared
gates, updates the record status, and performs the configured open/closed move.
If context is missing, blocked, or awaiting configured approval, stop. If delegated work
overlaps files or shared artifacts, stop and resolve ownership before dispatch.

## Delegation

```sudolang
delegationPrompt(context, ticket, guides) {
  """
  # Guides
  Read: ${guides}

  # Delivery Context
  Repository: ${context.repository}
  Phase: ${context.phase}
  Feature: ${context.feature}
  Ticket: ${ticket}
  Scope: ${context.scope}
  Non-goals: ${context.nonGoals}
  Evidence path: ${context.evidencePath}
  Required gates: ${context.requiredGates}

  Work only within this approved ticket and return changed paths, evidence,
  blockers, and unresolved decisions.
  """
}
```

Use provider adapters for GitHub, Azure DevOps, or another host. The
orchestrator must not embed provider credentials, project names, or API
commands in a reusable prompt.

## Constraints

```sudolang
Constraints {
  Never declare readiness from partial or inferred evidence
  Never route a new implementation ticket when an active ticket already owns the request
  Never generate child planning artifacts before the required parent review
  Never choose a later-phase ticket over a ready ticket in the active phase without explicit selection
  Never turn routine backlog grooming into a formal replan
  Never allow a delegated agent to modify shared plan or evidence records without ownership
  Never treat a record's folder as optional metadata; status and folder must agree
  Never close a parent while required children remain open or incomplete
  Preserve stable IDs, record content, index entries, and path history during moves
  Never conceal baseline failures or unrelated findings
  Never recommend push before an approved commit exists
  Never recommend a PR before the source branch is published
  Commit, push, and PR operations must be owned by the integration owner for
  delegated work
  Never declare a ticket ready, complete, or closed without required
  user-validation evidence or an approved not-applicable decision
  Never finish a routed response without one context-aware next-step and skill
  recommendation
  Never load every domain skill by default
  If context or gate policy is missing, report the blocker explicitly
}
```
