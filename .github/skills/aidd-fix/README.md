# aidd-fix

Guides a disciplined, repository-appropriate process for fixing bugs and
implementing code review feedback — one step at a time, with baseline,
regression, agent-owned technical verification, evidence, configured gates,
and no scope creep.

## Why

Unstructured fixes skip root-cause analysis, hide baseline failures, and add
tests after the fact. `/aidd-fix` confirms the bug, records the protected
baseline, writes a failing regression test when code behavior changes, records
the strongest applicable evidence, and applies configured delivery gates.

## Usage

Invoke `/aidd-fix` with the bug report or review feedback. The skill walks
through context, requirement, baseline/regression, agent-owned technical
verification, scoped implementation, the mode-appropriate post-implementation
functionality validation, review, evidence, and configured delivery steps. In
guided mode the ticket stays open until the terminal user functionality result
is recorded; automatic mode records terminal `automaticValidation` and
continues without waiting through the exact Rubber Duck `gpt-5.6-luna`
high-reasoning `all-validation` profile; an unavailable or mismatched profile
blocks automatic progress.

For code behavior, the failing regression is mandatory. Documentation,
configuration, migration, infrastructure, and exploratory work use the
strongest applicable evidence method instead. Every affected acceptance
outcome still requires an executable automated functionality test; unit or
regression tests alone are insufficient, and the user is never asked to rerun
technical checks. Resolve the mode from `.github/aidd-config.yml` and preserve
all external blockers in automatic mode. Automatic validation is never
performed by a fallback validator or model.

## When to use

- A bug has been reported and needs investigation
- A failing test needs root cause identified and resolved
- Code review feedback requires a code change
