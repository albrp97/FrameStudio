# aidd-evidence

Maintains an append-only evidence record for the active phase, feature, or
ticket. It records reproducible commands and functionality flows instead of
mixing execution history into `activity-log.md`.

## Why

Readiness claims are only useful when they show which requirement or protected
flow was exercised, what was expected, what happened, and which artifacts prove
the result. Explicit blocked and skipped states prevent missing coverage from
being mistaken for success.

## Usage

Commands:

- `/evidence init [ticket]` — prepare the active ticket record.
- `/evidence append [ticket]` — record a result, failure, blocker, or warning.
- `/evidence summarize [ticket]` — produce a readiness summary.

The record path comes from `.github/aidd-config.yml`, the ticket contract, or
the documented `evidence/<ticket-slug>.md` fallback. Secrets and sensitive test
data must be redacted before persistence. Agent-owned smoke, baseline, unit,
regression, fixture, acquisition, contract, integration, migration, security,
static-analysis, and quality checks use their technical categories and retain
their command, result, and artifacts. Automated functionality tests use the
`automatedFunctionality` category and retain the executable command, test
identifier, system boundary, assertions, expected/observed result, and
artifacts. Automatic-mode functionality closure uses `automaticValidation`
for the agent's execution of that charter. `userValidation` remains reserved
for the user's functional observation and result in guided mode; commit,
remote branch publication, and pull-request results use the `commit`, `push`,
and `pr` categories. In automatic mode, every validation category also records
the exact Rubber Duck validator profile: `rubber-duck`, `gpt-5.6-luna`, high
reasoning, and `all-validation`; no fallback validator is allowed.

## When to use

- Before implementation to capture the protected baseline
- During implementation and verification to record unit/regression results and
  the required automated functionality flow
- During review and PR operations to prove local and remote gate state
- During commit and push operations to record the exact local commit and
  published remote ref
- After implementation to record agent technical results and either the guided
  functionality-only handoff/terminal user result or automatic validation
  before ticket closure
- Before cleanup to confirm required evidence is preserved
