# aidd-tdd

Enforces repository-appropriate test-driven development, protected baselines,
real-system verification, and explicit evidence.

## Why

Writing the test first forces you to think about the API before implementing
it. The failing test proves the requirement isn't accidentally met, and the
minimal fix keeps scope tight.

## Usage

Invoke `/aidd-tdd` when implementing code changes. The cycle: write a failing
test, implement the minimum code to pass, get approval, repeat.

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

After technical verification, return a copy/paste-ready user-validation
handoff: explain what changed, list prerequisites and test data, give exact
steps, state the expected visible and persisted/external results, include
relevant failure paths and cleanup, and define the evidence and pass response
the user must return. Keep the ticket in `verifying` until the user confirms
`PASS` (or an approved `NOT APPLICABLE` decision is recorded); technical tests
alone do not close the ticket.

After the terminal user result is recorded, route to `/review`. Commit, push,
and PR operations follow only after review and configured delivery gates.

## When to use

- Implementing code changes (TDD is the default process for code behavior)
- Writing or reviewing tests
- Verifying configuration, migrations, infrastructure, or exploratory work with
  the strongest applicable evidence
