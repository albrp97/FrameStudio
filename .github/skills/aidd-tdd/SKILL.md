---
name: aidd-tdd
description: Discover and apply the strongest repository-appropriate test and verification process for an approved ticket, with baseline and evidence discipline.
---

# TDD and Verification

Use test-first development for new code behavior, while choosing the strongest
appropriate evidence method for documentation, configuration, migration,
infrastructure, and exploratory tickets.

## Test and delivery context

Read `.github/aidd-config.yml`, the active ticket contract, manifests, CI,
contribution guidance, and relevant domain skills before selecting commands.
Repository-specific commands and conventions override generic examples.

```sudolang
TestPlan {
  framework
  commands
  phase
  feature
  ticket
  protectedFlows[]
  requirements[]
  evidencePath
  realSystemRequired
  coverageGaps[]
}

TicketMethod = codeTdd | configurationVerification | migrationVerification |
  infrastructureVerification | exploratoryEvidence
```

## Discover the test plan

```sudolang
discoverTestPlan(ticket) => TestPlan {
  1. verify the ticket belongs to an approved active phase and feature
  2. inspect configured commands and repository manifests/scripts
  3. inspect CI and contribution guidance for required gates
  4. identify the test framework and supported local stack
  5. classify the ticket method
  6. identify protected existing flows and the strongest available evidence
  7. record missing tooling or unavailable services as coverage gaps
}
```

Do not assume `npm`, Vitest, Riteway, Playwright, pytest, or any other tool
without repository evidence. If a command is not configured, discover it or
record why it is unavailable.

## Baseline and red-green verification

For code behavior:

1. Record the ticket requirements, protected flows, and expected evidence.
2. Run the protected automated and functionality flows before changing code.
3. Record baseline passes, failures, environment health, and known defects with
   `/evidence`; do not hide pre-existing failures.
4. Write a failing, isolated test for one requirement.
5. Run the narrowest applicable test and confirm it fails for the intended
   reason.
6. Implement only the minimum behavior needed to pass.
7. Rerun the focused test, then the affected regression flows.
8. Exercise the strongest real-system flow when the change affects API,
   persistence, integrations, workers, or user-facing behavior.
9. Run configured local quality gates and record every result.

For documentation, configuration, migration, infrastructure, and exploratory
tickets, use the strongest applicable evidence instead of inventing a failing
test. State the chosen method and its coverage limits in the evidence record.

## Post-implementation user-validation handoff

After implementation and technical verification, do not report the ticket as
done or move it to `closed` yet. Produce a copy/paste-ready handoff that tells
the user exactly what to validate against the ticket contract.

```sudolang
UserValidationHandoff {
  ticket
  implementationSummary
  purpose: functionality | usability | regression | notApplicable
  prerequisites[]
  representativeData[]
  steps[] // action, expectedVisibleResult, expectedPersistedOrExternalEffect
  protectedRegressionChecks[]
  relevantFailurePaths[]
  cleanup[]
  evidenceToReturn[]
  passCriteria[]
}
```

The handoff must:

1. Translate every applicable acceptance criterion into an observable action
   and expected result; never tell the user only to "test the change".
2. Include setup, services, permissions, representative data, exact steps,
   visible results, persisted or external effects, cleanup, and relevant
   validation, authorization, retry, and failure paths.
3. Require comparable before/after UI evidence when configured. For backend,
   integration, migration, infrastructure, or CLI work, specify the supported
   API, command, service, log, data, or operational observation instead; do
   not require screenshots when they cannot prove the change.
4. State what the user must return: `PASS`, `FAIL`, `BLOCKED`, or approved
   `NOT APPLICABLE`, with notes and safe evidence paths.
5. Keep the ticket in `verifying` while the handoff is awaiting a result.
   A failed or blocked user check keeps the ticket open and requires a fix,
   follow-up, or explicit change-control decision.

Use `/user-test` and `/run-test` when their charter or execution support is
useful, but agent-run tests do not replace the required user confirmation when
`delivery.gates.user_validation_required` is enabled.

After the user returns a terminal validation result and it is appended to
evidence, recommend `/review`. Do not recommend `/commit` until the review is
terminal and the intended changes are staged.

## Assertions and isolation

```sudolang
assert({ given, should, actual, expected }) {
  given and should describe observable acceptance behavior
  actual exercises the named unit or real integration
  expected expresses the required result
  test answers unit, behavior, actual result, expected result, and bug discovery
}
```

Tests must be readable, local, independent, and explicit. Use factories for
repeated data rather than shared mutable fixtures. Prefer real integration
where technically and economically feasible. A mock is justified only for an
irrecoverable side effect, unavailable physical infrastructure, or
non-viable per-run cost; document the reason and the resulting coverage gap.

## Evidence

Record commands, framework, environment/service health, expected and observed
results, artifacts, failures, fixes, skipped checks, and coverage gaps through
`/evidence`. A test runner exit code is evidence for that command only; it does
not replace functionality or remote-gate evidence.

## Constraints

```sudolang
Constraints {
  Never implement code behavior before its failing test when code TDD applies
  Never claim a baseline or regression passed without running and recording it
  Never treat unavailable browser, service, or integration capability as passed
  Never assume a test framework or command
  Never share mutable test state
  Never add tests for type shape alone when type checking covers it
  Stop and report when a required test or service cannot run
  Always return the exact user-validation handoff after implementation
  Never report a ticket done or move it to closed before user validation evidence
  is recorded, unless an approved not-applicable decision is recorded
  Obtain the configured approval before moving to the next requirement
}
```
