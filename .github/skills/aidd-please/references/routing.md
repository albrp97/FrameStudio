# Lifecycle routing

## Next-step contract

Every non-empty response must finish with exactly one primary workflow handoff:

```sudolang
NextAction {
  step
  skill
  command
  reason
  blockers[]
  approvalRequired
}
```

Resolve `NextAction` from the active workflow state, planning ancestry,
evidence, approval mode, and configured gates. Prefer the action that unblocks
the current state: missing context routes to bootstrap or discovery, missing
planning layers route to the corresponding planning skill, an unready ticket
routes to the pre-implementation checklist, an approved ticket routes to TDD
and execution, pending user validation routes to `aidd-user-testing`, failed
or blocked validation routes to `aidd-fix` or change control, terminal
agent-owned technical, automated-functionality, and other evidence routes to review
  (including
deterministic static analysis), then commit, then push, then PR according to
version-control and pull-request policy, and a delivered phase routes to phase
feedback. Recommend `/commit` only after the reviewed intended scope is
staged and all configured local/user-validation gates are terminal. Recommend
`/push` only after a successful commit is ahead of or absent from its upstream.
Recommend `/aidd-pr` only after the source branch is published.
When the user explicitly instructs commit or push before readiness, route to
the requested delivery skill instead of refusing: warn once, confirm when
needed, perform the operation, and record `userDirectiveOverride` evidence
without claiming readiness.
When no active context is available, route to
`aidd-agent-orchestrator` for classification. In automatic mode, the returned
action is an internal continuation route and must be executed by the
orchestrator without asking for approval or waiting for a user response. Do
not recommend competing commands, invent work, or execute a guided-mode
recommendation implicitly.

## Routing

If the command or request is not recognized, load
`/aidd-agent-orchestrator` and classify it as discovery, planning,
implementation, bug fix, review, verification, or delivery operations. Load
only the domain skills relevant to the affected surfaces.
