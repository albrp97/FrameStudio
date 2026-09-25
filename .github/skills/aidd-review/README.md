# aidd-review

Runs an evidence-aware quality review that includes deterministic static
analysis, local-to-pull-request parity, architecture and hotspot checks, and
approval-gated remediation of actionable findings.

## Why

Ad-hoc reviews miss patterns and unsupported readiness claims. A systematic
process evaluates the ticket contract, agent-owned technical verification,
baseline/post-change evidence, deterministic analyzer output, PR-pipeline
parity, automated functionality flows, local/remote gates, scope,
documentation, hotspot risk, and applicable OWASP concerns before it ships.

## Usage

Invoke `/aidd-review` on code changes or a pull request. The review first runs
`aidd-static-analysis`, then checks local settings against the PR pipeline,
uses `aidd-structure` and `aidd-churn`, and evaluates test coverage, security,
UI/UX, architecture, and delivery evidence. Technical checks remain
agent-owned; `userValidation` evidence is limited to user-confirmed
functionality. In automatic mode, the equivalent agent-owned closure is
`automaticValidation`, never user confirmation. Execution runs
acceptance-level technical checks before the guided user handoff or automatic
validation; review may rerun analysis against the final diff as a later
agent-only readiness gate. When configured, review sends each actionable
introduced finding through one approved `/aidd-fix` cycle and reruns the
affected checks. In automatic mode, all validation decisions use the exact
Rubber Duck validator profile (`rubber-duck`, `gpt-5.6-luna`, high reasoning,
`all-validation` scope); deterministic
analyzers still provide the authoritative raw findings. Review never edits
source files directly.

## When to use

- Reviewing code changes or pull requests
- Evaluating completed features against requirements
- Pre-merge quality and security checks
- Resolving deterministic analyzer findings before commit or PR readiness
