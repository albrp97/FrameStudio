# aidd-pr

`/aidd-pr` manages provider-aware pull-request readiness and safely triages
review comments, resolving only already-addressed threads and delegating
scoped fixes through `/aidd-fix`.

## Why

PR checks, approvals, conflicts, and review threads accumulate quickly. A
provider-neutral lifecycle rechecks all required remote conditions after each
push, preserves evidence, and focuses attention on what still needs work.

## Usage

```
/aidd-pr [PR URL]    — inspect lifecycle state, checks, approvals, and review threads
/aidd-pr delegate    — dispatch approved remaining fixes through the configured provider adapter
```

## How it works

1. Reads the configured provider and delivery evidence
2. Verifies a published source branch, target base, required checks, approvals,
   conflicts, conversations, linked work, mergeability, and terminal
   user-validation evidence
3. Rechecks remote state after every push
4. For GitHub, paginates review threads, presents addressed threads for approval,
   and leaves newly-fixed threads open
5. Generates one scoped `/aidd-fix` prompt per remaining issue

If the source branch is not published, use `/push` before creating the PR.
Every response identifies whether the next action is branch publication, PR
creation/recheck, a scoped fix, or configured closeout.

## When to use

- A PR has accumulated open review comments that need triage
- You want to batch-resolve threads that are already addressed in code
- You need to delegate remaining review feedback to sub-agents for parallel fixes
