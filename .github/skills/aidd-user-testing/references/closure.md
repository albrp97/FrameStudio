# Validation closure

## Post-implementation closure handoff

When a ticket has been implemented, guided mode returns a functionality-only
user-validation handoff before the ticket can be closed. Automatic mode runs
the same functionality charter itself and records an agent-owned
`automaticValidation` result instead; it does not present a handoff or wait for
the user.

```sudolang
UserValidationHandoff {
  changedBehavior
  prerequisites[]
  representativeData[]
  exactSteps[]
  expectedVisibleResults[]
  expectedPersistedOrExternalEffects[]
  userObservableFailurePaths[]
  cleanup[]
  evidenceToReturn[]
  passCriteria[]
}
```

For user-facing work, describe the exact route or entry point, inputs,
visible results, state changes, and configured before/after screenshots. For
backend, API, integration, migration, infrastructure, or CLI work, describe
the supported command or request and how the user can observe the resulting
state, response, log, data, or operational effect. Do not require screenshots
when they cannot prove the ticket.

Do not include smoke, baseline, unit, regression, fixture, acquisition,
contract, integration, migration, security, static-analysis, formatter, lint,
type-check, build, deployment, or other technical-check commands in this
handoff. The agent must run those checks before presenting the handoff and
record them as technical evidence. In guided mode, the user's result applies only to the functionality steps.

The handoff must state that the ticket remains `verifying` until the user
returns one of:

```text
PASS: every required check succeeded; evidence: <paths or notes>
FAIL: <failed check and observed result>
BLOCKED: <missing service, data, permission, or capability>
NOT APPLICABLE: <reason and approval>
```

In guided mode, record the user's response through `/evidence` as functional
user-validation evidence. A usability observation, unit test, or agent-run
manual functionality charter does not replace the required automated
functionality result. In guided mode, it also does not replace the required user confirmation when
the effective mode policy
`delivery.mode_overrides.guided.gates.user_validation_required` is enabled.
In automatic mode, terminal `automaticValidation` with the exact configured
Rubber Duck profile is the mode-appropriate gate and no user confirmation is
requested. A failed or blocked functionality result keeps the ticket open.

After a terminal `PASS` or approved `NOT APPLICABLE` result is recorded,
recommend `/review`; autonomous commit, push, and PR recommendations remain
blocked until that review and the configured delivery gates are terminal. An
explicit user commit or push directive follows the override contract in
`development-mode.md` and does not make validation terminal.

In automatic mode, resolve and use the exact configured Rubber Duck validator
(`rubber-duck`, `gpt-5.6-luna`, high reasoning, `all-validation`) for the
charter and every other validation decision. Execute the charter after the automated functionality test, append a
terminal `automaticValidation` evidence entry for every functionality outcome,
including the validation profile, and route directly to `/review` when it
passes. Do not append `userValidation`, ask a question, or wait for a user
response. A failed, blocked, unavailable, or mismatched automatic validation
profile keeps the ticket open and routes to `aidd-fix` or change control.

Before guided handoff or automatic closure, the agent must have completed all
applicable technical verification checks and `/run-test` must have executed the
configured automated functionality test with a terminal passing result for
every acceptance outcome. Missing, unavailable, or failed technical checks or
automation are blockers; the user must not be asked to repair or rerun them.
