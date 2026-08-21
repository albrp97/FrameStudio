# Domain workflow interface

Domain skills remain focused on their technical or communication specialty.
Lifecycle skills provide the surrounding delivery controls.

```sudolang
DomainInput {
  phase
  feature
  ticket
  requirementIds[]
  affectedSurfaces[]
  scope[]
  nonGoals[]
  constraints[]
  expectedEvidence[]
}

DomainOutput {
  implementationGuidance
  risks[]
  assumptions[]
  limitations[]
  evidenceExpected[]
  unresolvedBlockers[]
  nextStepHint
}
```

When a lifecycle caller provides this context, accept it without redefining the
phase, feature, or ticket. Return domain guidance, risks, assumptions,
limitations, expected tests/evidence, and blockers that the lifecycle reviewer
can trace to requirements. `nextStepHint` may identify the lifecycle skill that
should act next, but it is advisory; the lifecycle orchestrator resolves the
authoritative next action. Do not create branches, manage PR threads, modify
shared planning/evidence records, or declare delivery readiness.
