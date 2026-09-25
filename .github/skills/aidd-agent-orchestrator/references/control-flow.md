# Orchestrator control flow

## Automatic development loop

When project bootstrap has written and verified the foundational artifacts and
`delivery.development.mode` is `automatic`, the orchestrator owns one
continuous loop. It must not emit a user question, approval request, or
functionality handoff that waits for a response.

```sudolang
automaticDevelopment(context) {
  require context.bootstrapAuthorized
  require context.developmentMode == automatic
  context.automaticValidationProfile = resolveAutomaticValidationProfile(context)
  state = automaticRunning

  repositoryMap(writeAndVerify)
  planningBootstrap(reconcileAndVerify)
  productmanager(discoverOrReuseObjectiveAndScope, writeAndVerify)
  capabilityMap(ifRequired, writeAndVerify)
  phases(writeAndVerify)
  planningReview(eachLayer)

  for phase in highestRankedOpenPhaseFirst {
    features(phase, writeAndVerify)
    planningReview(phaseAndFeatures)
    for feature in phase.openFeaturesInDependencyOrder {
      tickets(feature, writeAndVerify)
      groomBacklog(feature)
      planningReview(featureAndTickets)
      for ticket in feature.readyTicketsInDependencyOrder {
        preimplementation(ticket)
        tddOrStrongestApplicableMethod(ticket)
        runTest(technicalChecksAndAutomatedFunctionality)
        runAutomaticValidation(ticket)
        reviewAndRemediate(ticket)
        commitWhenConfigured(ticket)
        pushWhenConfigured(ticket)
        prAndConfiguredCloseoutWhenConfigured(ticket)
        lifecycleClose(ticket)
      }
      lifecycleClose(feature) when all required tickets are terminal
    }
    phaseFeedback(phase)
    lifecycleClose(phase) when all required features are terminal
  }

  state = complete
}
```

`runAutomaticValidation` executes the functionality charter against the
supported system boundary through the required Rubber Duck validator
(`gpt-5.6-luna`, high reasoning, `all-validation` scope), records
`automaticValidation` evidence, and
never creates `userValidation` evidence. Every validation step in the loop,
including planning, technical checks, static analysis, review, remote checks,
delivery gates, and lifecycle closeout, must use the same resolved profile.
Review, commit, push, PR, and closeout accept either the guided
`userValidation` gate or the automatic validation gate according to the
resolved mode. The loop may continue only when each parent is present,
unblocked, verified, and validated by the required profile.

Routine planning and delivery approvals are recorded as
`bootstrap-authorized` decisions in automatic mode. Security, branch
protection, credentials, provider operations, remote checks, merge policy,
unavailable tools, contradictory requirements, and failed required gates are
not overridden; they transition the context to `blocked` with a precise
reason and required capability or decision.

## Next-action routing

After every routed response, return one `NextAction` based on the current
state and the first unresolved gate or decision:

```sudolang
recommendNext(context, evidence) {
  if context.blocked => return the skill that resolves the named blocker
  if foundationalContextMissing => projectBootstrap
  if context.developmentMode == automatic and
    context.bootstrapAuthorized and context.state != complete:
      return the next internal action in automaticDevelopment
  if state in {proposed, discovered} and discoveryMissing => productmanager
  if state == scoped and capabilitiesMissing => capabilityMap
  if state == capabilitiesApproved and phasesMissing => phases
  if state == phasesApproved and featuresMissing => features
  if state == featuresApproved and ticketsMissing => tickets
  if state == ticketsReady => preimplementation
  if state in {implementationReady, baseline, implementing} => tdd |> execute
  if state == verifying and automatedFunctionalityMissing => run-test
  if state == verifying and context.developmentMode == automatic and
    automaticValidationMissing => run-test
  if state == verifying and context.developmentMode != automatic and
    userValidationMissing => user-testing
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
implicit authorization to execute the command in guided mode. In automatic
mode it is an internal continuation and must be executed without waiting for
the user.

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
  verifying -> gated when automated functionality, local gates, and review
    evidence have terminal results plus `userValidation` in guided mode or
    `automaticValidation` in automatic mode
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
