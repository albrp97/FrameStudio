---
name: aidd-requirements
description: Write observable functional requirements and verification mappings for a user story, feature, or focused ticket.
---

# Functional requirements

Act as a senior product manager to express behavior in the exact form
`Given X, should Y`, while preserving phase, feature, and ticket ownership.

## Types

```sudolang
RequirementCategory = success | failure | authorization | persistence |
  integration | retry | error

FunctionalRequirement {
  id
  scopeItem
  capability
  phase
  feature
  ticket
  category: RequirementCategory
  text: "Given $situation, should $jobToDo"
  protectedBehavior[]
  verification
  unresolvedDecision
}

VerificationMapping {
  requirementId
  evidenceType // unit | integration | browser | manual | contract | other
  commandOrSteps
  expected
  coverageGap
}

RequirementsRecord {
  status
  reviewedAt
  sourceReferences[]
  requirements[]
  coverage[]
  openQuestions[]
}
```

## Process

1. Read the user story, delivery contract, feature, or ticket and its parent
   phase/feature context.
2. Identify distinct preconditions, normal outcomes, failure paths,
   authorization states, persistence effects, integration effects, retries,
   and error behavior where applicable.
3. Write one or more requirements per situation in
   `Given X, should Y` form. Describe the user's or system's observable job,
   not a UI control or implementation detail.
4. Identify protected existing behaviors that could regress.
5. Map each requirement and protected behavior to the strongest appropriate
   evidence type and repeatable command or steps.
6. Mark unknown acceptance details as unresolved decisions or blockers instead
   of filling them with assumptions.
7. Detect requirements that span unrelated outcomes, features, or phase
   boundaries; return them for decomposition instead of hiding the split in
   implementation steps.
8. Verify that every acceptance-relevant behavior has a requirement and
   evidence mapping, then return the numbered list and mapping.

## Constraints

```sudolang
Constraints {
  Keep requirements within the current ticket scope
  Do not prescribe components, endpoints, libraries, or internal structure
  Do not treat missing test tooling as passed coverage
  Preserve parent phase and feature context
  Keep protected behaviors separate from new behavior
  Surface unresolved decisions explicitly
  Link each requirement to its scope item, capability, phase, feature, and ticket when those layers exist
  Do not mark a requirement covered when its evidence command or repeatable steps are unknown
  Keep one observable outcome per requirement; split broad requirements before ticket readiness
}
```
