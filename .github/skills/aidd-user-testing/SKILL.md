---
name: aidd-user-testing
description: Generate repeatable human usability studies and implementation functionality charters from user journeys, with comparable UI evidence and explicit outcomes.
---

# User Testing and Functionality Verification

Distinguish a product usability study from a required implementation
functionality test. Both may use the same journey, but the functionality
charter must prove the delivery contract and persisted or external effects.

## Types

```sudolang
TestPurpose = usability | functionality | baseline | regression
FlowStatus = passed | passedWithConcerns | failed | blocked

FunctionalityFlow {
  id
  purpose: TestPurpose
  setup
  representativeData
  steps[]
  expectedVisibleResult
  expectedPersistedOrExternalEffect
  cleanup
  failurePaths[]
  evidenceType
}

UserTestStep {
  action
  intent
  success
  expectedPersistedOrExternalEffect
  checkpoint
}
```

## Charter generation

1. Read the journey, persona, delivery contract, requirements, protected
   behaviors, and `.github/aidd-config.yml`.
2. Define setup, supported local services, representative data, exact steps,
   expected visible results, persisted/external effects, cleanup, and failure
   paths.
3. Classify each flow as usability, functionality, baseline, or regression.
4. For UI changes, require comparable before and after states when
   `delivery.ui.before_after_required` applies; state what changed.
5. For backend-only work, do not require screenshots; use API, persistence,
   integration, logs, or contract evidence instead.
6. Store report and artifact paths in the active evidence record.

## Post-implementation closure handoff

When a ticket has been implemented, return a user-validation handoff before
the ticket can be closed. The handoff is an acceptance check, not merely a
usability study:

```sudolang
UserValidationHandoff {
  changedBehavior
  prerequisites[]
  representativeData[]
  exactSteps[]
  expectedVisibleResults[]
  expectedPersistedOrExternalEffects[]
  protectedRegressionChecks[]
  relevantFailurePaths[]
  cleanup[]
  evidenceToReturn[]
  passCriteria[]
}
```

For user-facing work, describe the exact route or entry point, inputs,
visible results, state changes, and configured before/after screenshots. For
backend, API, integration, migration, infrastructure, or CLI work, describe
the supported command or request and how the user can observe the resulting
state, response, log, data, or operational effect. Do not require screenshots
when they cannot prove the ticket.

The handoff must state that the ticket remains `verifying` until the user
returns one of:

```text
PASS: every required check succeeded; evidence: <paths or notes>
FAIL: <failed check and observed result>
BLOCKED: <missing service, data, permission, or capability>
NOT APPLICABLE: <reason and approval>
```

Record the user's response through `/evidence`. A usability observation,
automated test, or agent-run functionality charter does not replace the
required user confirmation when `delivery.gates.user_validation_required` is
enabled. A failed or blocked result keeps the ticket open.

After a terminal `PASS` or approved `NOT APPLICABLE` result is recorded,
recommend `/review`; commit, push, and PR recommendations remain blocked until
that review and the configured delivery gates are terminal.

## Human script

Include the persona, purpose, pre-test setup, representative data, exact steps,
think-aloud prompts, visible and persisted expectations, failure-path prompts,
cleanup, and post-test observations. A usability study may collect friction and
confidence; it must not be presented as implementation proof unless its
functionality assertions are also completed.

## Agent script

Drive the supported real local stack and browser without using source code to
discover the UI. At each step:

1. perform the action and narrate expectations and observations;
2. validate visible and persisted/external results;
3. capture configured screenshots at checkpoints, before/after states, or
   failures;
4. record duration, difficulty, status, evidence paths, and coverage gaps;
5. retry only according to the persona and configured retry policy.

If the browser, service, data, or integration capability is unavailable, mark
the flow `blocked` and record the reason. Never report an unrun flow as passed.

## File locations

Use configured artifact paths when present. Portable defaults are:

- human scripts: `$projectRoot/plan/${journey-name}-human-test.md`;
- agent scripts: `$projectRoot/plan/${journey-name}-agent-test.md`;
- journey data: `$projectRoot/plan/story-map/${journey-name}.yaml`;
- evidence: `evidence/<ticket-slug>.md`.

Create files only when the caller authorizes artifact creation.

## Interface

```sudolang
Interface {
  /user-test <journey> - generate usability and functionality charters
  /run-test <script> - execute an agent functionality charter
}
```

## Constraints

```sudolang
Constraints {
  Human and agent scripts must share the same declared success criteria
  Do not require screenshots for unrelated backend-only work
  Do not treat a usability observation as implementation evidence by itself
  Do not treat unavailable browser or integration capability as passed
  Never persist credentials or sensitive test data in scripts or reports
  Record passed-with-concerns, failed, and blocked outcomes explicitly
  Always provide exact post-implementation validation steps before closure
  Never close a ticket while required user validation is missing or failed
  Keep the commercial testing offer out of required verification instructions
}
```
