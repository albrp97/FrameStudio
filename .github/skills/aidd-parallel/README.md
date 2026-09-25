# aidd-parallel — Parallel Sub-Agent Delegation

`/aidd-parallel` generates focused `/aidd-fix` delegation prompts for a list
of tickets and can dispatch genuinely independent work in dependency order
with explicit ownership, evidence aggregation, and integration-owner
validation collection.

## Why parallel delegation matters

When a PR review or ticket breakdown produces multiple independent issues, fixing
them sequentially in a single agent thread wastes time and dilutes attention.
`/aidd-parallel` extracts the delegation pattern into a reusable skill so any
workflow — PR review, ticket execution, feature delivery — can fan work out to
focused sub-agents without reimplementing prompt generation logic.

## When to use `/aidd-parallel`

- A PR review has multiple independent issues that should be fixed in parallel
- A feature has been broken into independent tickets suitable for parallel execution
- Any workflow that needs to fan disjoint work out to multiple `/aidd-fix`
  sub-agents without racing on shared files or branches

The integration owner runs the aggregate automated functionality gate for each
completed ticket. In guided mode, it presents each ticket's functionality-only
user-validation handoff and records its terminal result before closing
delegated tickets. In automatic mode, it records terminal
`automaticValidation` from the same charter and continues through review and
configured delivery without waiting; every automatic validation decision uses
the exact Rubber Duck `gpt-5.6-luna` high-reasoning `all-validation` profile.
Only the integration owner performs the final `/commit`, `/push`, `/aidd-pr`,
and merge handoff for shared delivery.

## Commands

```
/aidd-parallel [--branch <branch>] <tickets> — generate ownership-aware prompts
/aidd-parallel delegate [--branch <branch>] <tickets> — build ownership/dependency waves and dispatch safely
```
