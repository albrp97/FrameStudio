# aidd-please

General-purpose AI assistant for software development projects, acting as
senior engineer, product manager, and technical writer with shared delivery
context, approval, scope, evidence, and readiness rules.

## Why

When you're not sure which specialized skill to use, `/aidd-please` provides a
starting point. It loads repository-specific configuration, routes to
specialized skills, and prevents unsupported success or readiness claims.

## Usage

Say "please" followed by your request. Available commands:

`/help`, `/log`, `/evidence`, `/commit`, `/plan`, `/discover`, `/ticket`,
`/execute`, `/review`, `/aidd-static-analysis`, `/aidd-churn`, `/user-test`,
`/run-test`, `/aidd-fix`, `/aidd-pr`, `/aidd-parallel`, `/aidd-pipeline`,
`/commit`, `/push`, `/clean-pr-branch`,
`/aidd-upskill`, `/aidd-riteway-ai`

Use `--depth` or `-d [1..10]` to control response depth (1 = ELI5,
10 = PhD-level).

Every response includes one context-aware handoff naming the next concrete
step, the single skill and command to use, and why it follows from the current
workflow state or blocker. When no active context is available, the handoff
routes to `aidd-agent-orchestrator` for classification.

The delivery handoff is ordered: reviewed scope -> `/commit` -> `/push` when
the branch is unpublished or ahead -> `/aidd-pr` when a PR is required.

## When to use

- General assistance with a software development project
- Logging, committing, or proofing tickets
- When you need a starting point and aren't sure which skill to use
