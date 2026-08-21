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
data must be redacted before persistence. Static-analysis runs use the
`staticAnalysis` category and retain tool, rule, version, parity, baseline, and
report details. User responses are recorded with `userValidation`; commit,
remote branch publication, and pull-request results use the `commit`, `push`,
and `pr` categories.

## When to use

- Before implementation to capture the protected baseline
- During implementation and verification to record test and functionality flows
- During review and PR operations to prove local and remote gate state
- During commit and push operations to record the exact local commit and
  published remote ref
- After implementation to record the user's validation handoff and terminal
  result before ticket closure
- Before cleanup to confirm required evidence is preserved
