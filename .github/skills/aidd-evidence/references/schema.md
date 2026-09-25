# Evidence schema

## Contract

```sudolang
EvidenceStatus = passed | passedWithConcerns | failed | blocked | skippedWithReason

ValidationProfile {
  validator
  model
  reasoningEffort
  scope
}

ValidatorCapability {
  validator
  models[]
  reasoningEfforts[]
  scopes[]
  available
}

EvidenceEntry {
  id
  timestamp
  phase
  feature
  ticket
  requirementOrFlow
  category // planning | baseline | implementation | smoke | unit | regression | fixture | acquisition | contract | integration | migration | deployment | security | qualityGate | functionality | automatedFunctionality | automaticValidation | userValidation | staticAnalysis | gate | review | commit | push | pr
  owner // agent | user | system
  validationProfile // required for automatic-mode validation entries
  planningLayer // objective | scope | capability | phase | feature | ticket | null
  parentArtifact
  sourceReferences[]
  commandOrSteps
  automated
  testId
  systemBoundary
  assertions[]
  expected
  observed
  status: EvidenceStatus
  artifacts[]
  failure
  fix
  blocker
  acceptedWarning
}

EvidenceRecord {
  context
  planningChain
  entries[]
  openBlockers[]
  readiness
}
```
