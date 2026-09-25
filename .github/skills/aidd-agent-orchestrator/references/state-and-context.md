# Delivery state and context

## Delivery state

```sudolang
DeliveryState = proposed | discovered | scoped | capabilitiesApproved |
  phasesApproved | featuresApproved | ticketsReady | implementationReady |
  baseline | implementing | verifying | gated | prOpen | reviewLoop | ready |
  automaticRunning | blocked | complete

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
  developmentMode
  bootstrapAuthorized
  validationMode
  automaticValidationProfile
  validatorCapabilities[]
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

Resolve `delivery.mode_overrides.<developmentMode>` over the base delivery
approval, version-control, gate, and static-analysis settings before routing.
Automatic mode requires a runtime validator capability matching the configured
Rubber Duck profile; the configuration identifies the required profile but does
not assert that the runtime can provide it.
