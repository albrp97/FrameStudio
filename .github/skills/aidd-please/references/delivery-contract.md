# Delivery contract and readiness

## Delivery contract

Read the root README, `.github/aidd-config.yml` when present, and
`/aidd-stack` when the request concerns implementation. The delivery context
is the shared contract consumed by lifecycle skills:

```sudolang
DeliveryContext {
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
  requiredGates[]
  evidencePath
  approvalMode
  developmentMode
  bootstrapAuthorized
  validationMode
  automaticValidationProfile
  validatorCapabilities[]
  workflowState
  versionControl
  pullRequestState
  pullRequestRequired
  nextAction
}
```

Resolve values from `.github/aidd-config.yml`, active planning artifacts,
repository manifests/CI, and direct user instructions in that order. A
repository-specific value wins over a generic default. Empty command
configuration requires discovery; it never means a check passed or may be
silently skipped.

For phase, feature, and ticket records, apply
`skills/planning-artifact-lifecycle.md`: resolve both lifecycle directories,
keep status and current path consistent, and synchronize indexes after an
authorized move.

## Approval and readiness

```sudolang
resolveDevelopmentMode(context) {
  read delivery.development.mode from `.github/aidd-config.yml`
  default to guided when the key is absent
  compare any mirrored value in vision.md or AGENTS.md
  block on a conflicting durable value
  modeOverrides = delivery.mode_overrides ?? {}
  merge modeOverrides[resolved mode] over base approval, version-control,
    gate, and static-analysis settings
}

resolveAutomaticValidationProfile(context) {
  if context.developmentMode != automatic:
    return null

  require delivery.development.automatic_validation
  require validator == rubber-duck
  require model == gpt-5.6-luna
  require reasoning_effort == high
  require scope == all-validation
  require a runtime validator capability that is available and matches the
    validator, model, reasoning effort, and scope
  return the profile
}

approvalMode(config, context) {
  policy = resolveModePolicy(context)

  if context.developmentMode == automatic && context.bootstrapAuthorized:
    return automatic

  match policy.approval.mode {
    bootstrap => blocked("automatic bootstrap authorization is required")
    user => ask before each configured gate
    review => proceed after /review confirms required gates and evidence
    repository => follow the repository's documented policy; missing policy => blocked
  }
}

readinessReport(context, evidence) {
  automaticProfile =
    context.developmentMode == automatic
      ? resolveAutomaticValidationProfile(context)
      : null
  validationGate =
    context.developmentMode == automatic
      ? automaticValidation
      : userValidation

  report {
    completedScope
    evidenceByRequirement
    requiredGates
    blockers
    acceptedWarnings
    coverageGaps
    ready: onlyIf(
      allRequiredGatesHaveTerminalEvidence &&
      blockers.isEmpty &&
      (context.developmentMode != automatic ||
        allValidationEntriesUse(automaticProfile))
    )
    nextAction
  }
}
```

A conversational progress report may describe work in progress. A delivery
readiness declaration requires terminal evidence for every configured required
gate and must name any skipped or unavailable coverage.
