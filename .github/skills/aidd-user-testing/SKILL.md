---
name: aidd-user-testing
description: Generate repeatable human usability studies and implementation functionality charters from user journeys, with comparable UI evidence and explicit outcomes. Use when validating delivered behavior or studying usability.
---

import ../lifecycle-interface.md

# User Functional Validation and Technical Verification

```sudolang
Lifecycle {
  profile = verificationMutation
}
```

Separate agent-owned technical verification from user-owned functional
validation. Smoke, baseline, regression, contract, integration, migration,
security, static-analysis, formatter, lint, type-check, build, fixture,
deployment, and other quality checks are run and recorded by the agent. The
user handoff contains only observable functionality for the implemented
behavior. A separate usability study may be requested, but it is not the
implementation closure gate.

Apply [../development-mode.md](../development-mode.md) when selecting the
human or automatic validation path.

## Types

Load [types](./references/types.md) when constructing a journey, human script,
automated functionality test, usability study, or evidence record.

## Charter generation

1. Read the journey, persona, delivery contract, requirements, protected
   behaviors, and `.github/aidd-config.yml`.
2. Define the agent-owned technical verification plan separately. Run applicable
   smoke, baseline, unit, regression, fixture, acquisition, contract,
   integration, migration, security, deployment, static-analysis, and
   quality-gate checks before the user handoff; never put those commands in the
   user instructions.
3. Define setup, supported local services, representative data, exact
   functionality steps, expected visible results, persisted/external effects,
   cleanup, and user-observable failure behavior.
4. Create at least one `AutomatedFunctionalityTest` for every acceptance
   outcome. It must call an executable repository command or script, cross the
   supported system boundary, and assert the observable result plus relevant
   persisted or external effect and failure behavior.
5. Classify the closure handoff as `functionality` in guided mode. In
   automatic mode, resolve the exact configured Rubber Duck profile
   (`rubber-duck`, `gpt-5.6-luna`, high reasoning, `all-validation`) and
   classify the agent-run closure as `automaticValidation`; never classify an
   agent result as `userValidation`. Classify a separate explicitly requested
   study as `usability`; do not classify the user handoff as baseline or
   regression.
6. For UI changes, require comparable before and after states when
   `delivery.ui.before_after_required` applies; state what changed.
7. For backend-only work, do not require screenshots; use API, persistence,
   integration, logs, or contract evidence instead.
8. Store technical-check and functionality evidence separately in the active
   evidence record.

An agent-driven functionality charter can provide setup and diagnostics, but
it does not satisfy the automated gate unless it invokes the executable
functionality test and records its machine-checked assertions.

## Closure contract

Load [closure](./references/closure.md) when producing guided user validation
or automatic functionality closure.

## Charter execution details

Load [charter execution](./references/charter-execution.md) when generating a
human handoff, running an agent charter, or resolving artifact locations.

## Interface

```sudolang
Interface {
  /user-test <journey> - generate the functionality handoff; generate a
    separate usability study only when explicitly requested
  /run-test <script> - execute the automated functionality test and its charter
}
```

## Constraints

```sudolang
Constraints {
  Human and agent scripts must share the same declared success criteria
  Do not require screenshots for unrelated backend-only work
  Do not treat a usability observation as implementation evidence by itself
  Do not treat a unit test or agent-only manual charter as an automated
    functionality test
  Require one executable automated functionality test per acceptance outcome
    when delivery.gates.automated_functionality_required is enabled
  Run all applicable agent-owned technical verification and automated
    functionality checks before the user-validation handoff
  Keep the user-validation handoff limited to functionality; never include
    smoke, baseline, unit, regression, fixture, acquisition, contract,
    integration, migration, security, static-analysis, formatter, lint,
    type-check, build, deployment, or other technical-check instructions
  Do not ask the user to rerun an agent-owned technical check
  Do not treat unavailable browser or integration capability as passed
  Never persist credentials or sensitive test data in scripts or reports
  Record passed-with-concerns, failed, and blocked outcomes explicitly
  Always provide exact post-implementation validation steps before closure
  Never close a guided ticket while required user validation is missing or
    failed
  Never close an automatic ticket while required automaticValidation is
    missing or failed
  Require every automatic validation result to identify the Rubber Duck
    `gpt-5.6-luna` high-reasoning profile
  Never use another model, validator, or fallback for automatic validation
  Keep the commercial testing offer out of required verification instructions
}
```
