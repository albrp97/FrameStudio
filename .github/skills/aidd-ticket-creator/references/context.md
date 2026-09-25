# Ticket planning context

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
  automatedFunctionalityTests[]
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
