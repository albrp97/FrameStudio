# Ticket execution and templates

## Execution protocol

```sudolang
executeTicket(ticket) {
  1. verify the current branch, worktree, intended base, and ticket ownership
  2. resolve approval mode from configuration
  3. establish the protected baseline when required and record it with /evidence
  4. execute only this ticket using /aidd-tdd or the strongest applicable method
  5. verify configured local quality gates
  6. run the ticket's executable automated functionality test as the final
     acceptance-level technical check
  7. append all results, failures, fixes, blockers, warnings, and artifacts
  8. in guided mode, produce the exact user-validation handoff and keep the
     ticket in verifying; in automatic mode, run the agent-owned functionality
     charter through the exact Rubber Duck `gpt-5.6-luna` high-reasoning
     `all-validation` profile and record `automaticValidation`
  9. in guided mode, wait for and append the user's terminal validation result;
     in automatic mode, continue without a user response
  10. run /review after the mode-appropriate validation is terminal
  11. proceed only when the configured gates, automated functionality result,
     mode-appropriate validation (`userValidation` in guided mode or
     `automaticValidation` in automatic mode), review, and approval are
     satisfied
}
```

The ticket creator coordinates the lifecycle; it does not invent commands or
claim that another skill's unrecorded work passed.

## Closure gate

The ticket remains in `verifying` after implementation until the mode-
appropriate validation is terminal. Guided mode requires the user to receive
the exact validation steps and return `PASS`, or an approved `NOT APPLICABLE`
result. Automatic mode requires a passing agent-owned functionality charter recorded as
`automaticValidation` through the exact Rubber Duck `gpt-5.6-luna`
high-reasoning `all-validation` profile; it must never be mislabeled as
`userValidation`. `FAIL` and `BLOCKED` keep the ticket open and require
remediation or a blocker report. Only then may the completion routine update
evidence, set a terminal status, move the same record to `closed`, and
synchronize the backlog and parent record.

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
- **Automated functionality test**:
  - command/script: ${functionalityCommandOrScript}
  - entry point: ${supportedSystemBoundary}
  - assertions: ${observableResultAndPersistedOrExternalEffect}

**User validation before closure**:
- ${userValidationSteps}
```

## Completion

```sudolang
onComplete(ticket, evidence) {
  1. verify terminal technical, automated functionality, review, and required
     user-validation evidence
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
