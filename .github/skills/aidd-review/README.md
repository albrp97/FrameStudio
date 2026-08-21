# aidd-review

Runs an evidence-aware quality review that includes deterministic static
analysis, local-to-pull-request parity, architecture and hotspot checks, and
approval-gated remediation of actionable findings.

## Why

Ad-hoc reviews miss patterns and unsupported readiness claims. A systematic
process evaluates the ticket contract, baseline/post-change evidence,
deterministic analyzer output, PR-pipeline parity, functionality flows,
local/remote gates, scope, documentation, hotspot risk, and applicable OWASP
concerns before it ships.

## Usage

Invoke `/aidd-review` on code changes or a pull request. The review first runs
`aidd-static-analysis`, then checks local settings against the PR pipeline,
uses `aidd-structure` and `aidd-churn`, and evaluates test coverage, security,
UI/UX, architecture, and delivery evidence. When configured, it sends each
actionable introduced finding through one approved `/aidd-fix` cycle and
reruns the affected checks. Review never edits source files directly.

## When to use

- Reviewing code changes or pull requests
- Evaluating completed features against requirements
- Pre-merge quality and security checks
- Resolving deterministic analyzer findings before commit or PR readiness
