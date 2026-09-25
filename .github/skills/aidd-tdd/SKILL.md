---
name: aidd-tdd
description: Discover and apply the strongest repository-appropriate test and verification process for an approved ticket, with baseline and evidence discipline. Use when implementing or repairing observable behavior.
---

Apply [../development-mode.md](../development-mode.md) when selecting the
post-implementation validation and continuation behavior.

import ../lifecycle-interface.md

# TDD and Verification

```sudolang
Lifecycle {
  profile = implementationMutation
}
```

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
  technicalVerification[]
  functionalityCommand
  automatedFunctionalityTests[]
  phase
  feature
  ticket
  protectedFlows[]
  requirements[]
  evidencePath
  realSystemRequired
  validationProfile
  coverageGaps[]
}

TechnicalVerification {
  id
  category: smoke | baseline | unit | regression | fixture | acquisition |
    contract | integration | migration | security | staticAnalysis |
    qualityGate | deployment
  commandOrScript
  owner: agent
  validationProfile
  expected
  observed
  status
  artifacts[]
}

AutomatedFunctionalityTest {
  id
  commandOrScript
  framework
  entryPoint
  setup
  representativeData
  steps[]
  assertions[]
  expectedPersistedOrExternalEffect
  cleanup
  artifacts[]
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
  6. identify protected existing flows and at least one automated functionality
     test for every acceptance outcome
  7. identify applicable agent-owned smoke, baseline, unit, regression, fixture,
     acquisition, contract, integration, migration, security, static-analysis,
     deployment, and quality-gate checks; never assign these technical checks
     to the user handoff
  8. in automatic mode, resolve the exact Rubber Duck validation profile
     (`rubber-duck`, `gpt-5.6-luna`, high reasoning, `all-validation`) before
     running or classifying any check
  9. verify that the functionality test crosses a supported system boundary
     and has executable assertions for observable results and relevant state
  10. record missing tooling or unavailable services as blockers when the
     required automated functionality gate cannot run
}
```

Do not assume `npm`, Vitest, Riteway, Playwright, pytest, or any other tool
without repository evidence. If a command is not configured, discover it or
record why it is unavailable.

## Verification method reference

Load [verification methods](./references/verification-methods.md) when running
baseline, red-green implementation, automated functionality, user or automatic
validation, assertions, or evidence recording.

## Constraints

```sudolang
Constraints {
  Never implement code behavior before its failing test when code TDD applies
  Never claim a baseline or regression passed without running and recording it
  Never close or gate a ticket without a terminal automated functionality test
    when delivery.gates.automated_functionality_required is enabled
  Never treat a unit test, source inspection, human script, or agent narration
    as an automated functionality test
  Never treat unavailable browser, service, or integration capability as passed
  Never assume a test framework or command
  Never share mutable test state
  Never add tests for type shape alone when type checking covers it
  Stop and report when a required test or service cannot run
  Always perform the mode-appropriate validation after all applicable
    agent-owned technical checks and automated functionality checks are
    terminal
  Never ask the user to run smoke, baseline, unit, regression, fixture,
    acquisition, contract, integration, migration, security, static-analysis,
    formatter, lint, type-check, build, deployment, or other technical checks
  Never report a guided ticket done or move it to closed before user validation
    evidence is recorded, unless an approved not-applicable decision is recorded
  Never report an automatic ticket done or move it to closed before
    automaticValidation evidence is recorded
  Never accept automatic validation without the exact Rubber Duck
    `gpt-5.6-luna` high-reasoning profile
  Obtain the configured approval before moving to the next requirement in
    guided mode; automatic mode uses verified bootstrap authorization
}
```
