# aidd-fix

Guides a disciplined, repository-appropriate process for fixing bugs and
implementing code review feedback — one step at a time, with baseline,
regression, evidence, configured gates, and no scope creep.

## Why

Unstructured fixes skip root-cause analysis, hide baseline failures, and add
tests after the fact. `/aidd-fix` confirms the bug, records the protected
baseline, writes a failing regression test when code behavior changes, records
the strongest applicable evidence, and applies configured delivery gates.

## Usage

Invoke `/aidd-fix` with the bug report or review feedback. The skill walks
through context, requirement, baseline/regression, scoped implementation,
verification, review, the post-implementation user-validation handoff,
evidence, and configured delivery steps. The ticket stays open until the
terminal user result is recorded.

For code behavior, the failing regression is mandatory. Documentation,
configuration, migration, infrastructure, and exploratory work use the
strongest applicable evidence method instead.

## When to use

- A bug has been reported and needs investigation
- A failing test needs root cause identified and resolved
- Code review feedback requires a code change
