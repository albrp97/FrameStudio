# aidd-tdd

Enforces repository-appropriate test-driven development, protected baselines,
real-system verification, and explicit evidence.

## Why

Writing the test first forces you to think about the API before implementing
it. The failing test proves the requirement isn't accidentally met, and the
minimal fix keeps scope tight.

## Usage

Invoke `/aidd-tdd` when implementing code changes. The cycle: define the
automated functionality test, identify agent-owned technical checks, write a
failing focused test, implement the minimum code to pass, get approval, repeat,
then run all technical checks and automated functionality before
mode-appropriate validation. Guided mode waits for the user functionality
result; automatic mode runs the same functionality charter as the agent and
records `automaticValidation` before continuing. Every automatic validation
decision uses the configured Rubber Duck validator (`gpt-5.6-luna`, high
reasoning), including technical-check and review results.

When the repository uses RITEway, tests may use its `assert` format:

```js
assert({
  given: "a new account",
  should: "have zero balance",
  actual: getBalance(createAccount()),
  expected: 0,
});
```

Discover the repository's test framework and commands from its configuration,
manifests, scripts, CI, and contribution guidance. Colocate tests with the code
they test when that is the repository convention.

## After implementation

After terminal agent-owned technical verification and automated functionality
verification, guided mode returns a copy/paste-ready functionality-only
user-validation handoff: explain what changed, list prerequisites and test
data, give exact user actions, state the expected visible and
persisted/external results, include user-observable failure behavior and
cleanup, and define the evidence and pass response the user must return. Do
not ask the user to run technical scripts. Keep the ticket in `verifying`
until the user confirms `PASS` (or an approved `NOT APPLICABLE` decision is
recorded). Automatic mode executes that functionality charter through the
configured Rubber Duck validator, records `automaticValidation`, and continues
to review; technical tests alone do not close the ticket in either mode.

After the terminal user result is recorded, route to `/review`. Commit, push,
and PR operations follow only after review and configured delivery gates.

## When to use

- Implementing code changes (TDD is the default process for code behavior)
- Writing or reviewing tests
- Verifying configuration, migrations, infrastructure, or exploratory work with
  the strongest applicable evidence
