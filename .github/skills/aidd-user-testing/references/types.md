# User-testing types

## Types

```sudolang
UserTestPurpose = usability | functionality
TechnicalCheckPurpose = smoke | baseline | unit | regression | fixture |
  acquisition | contract | integration | migration | security | staticAnalysis |
  qualityGate | deployment
FlowStatus = passed | passedWithConcerns | failed | blocked
ValidationOwner = user | agent

FunctionalityFlow {
  id
  purpose: functionality
  setup
  representativeData
  steps[]
  expectedVisibleResult
  expectedPersistedOrExternalEffect
  cleanup
  failurePaths[]
  evidenceType
}

TechnicalCheck {
  id
  purpose: TechnicalCheckPurpose
  commandOrScript
  owner: agent
  validationProfile
  expected
  observed
  status: FlowStatus
  artifacts[]
}

AutomatedFunctionalityTest {
  id
  commandOrScript
  framework
  systemBoundary
  setup
  representativeData
  steps[]
  assertions[]
  expectedVisibleResult
  expectedPersistedOrExternalEffect
  failureAssertions[]
  cleanup
  artifacts[]
}

AutomaticValidation {
  id
  owner: agent
  validationProfile
  purpose: functionality
  commandOrScript
  systemBoundary
  assertions[]
  expectedPersistedOrExternalEffect
  observed
  status: FlowStatus
  artifacts[]
}

UserTestStep {
  action
  intent
  success
  expectedPersistedOrExternalEffect
  checkpoint
}
```
