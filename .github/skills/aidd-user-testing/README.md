# aidd-user-testing

Separates agent-owned technical verification from the functionality-only
handoff that a user performs after implementation. Human usability studies and
agent diagnostic scripts remain useful, but neither replaces the required
machine-checked functionality test.

## Why

The agent runs smoke, baseline, unit, regression, fixture, acquisition,
contract, integration, migration, security, static-analysis, formatter, lint,
type-check, build, deployment, and other quality checks. Automated
functionality tests exercise a supported API, CLI, browser, worker, or
integration boundary and assert visible/output and persisted/external effects.
The user handoff contains only the implemented functionality and its
user-observable outcomes.

The workflow reads `delivery.development.mode` from `.github/aidd-config.yml`.
Guided mode waits for the user's functionality result. Automatic mode runs the
same functionality charter as the agent, records `automaticValidation`, and
continues to review without asking or waiting; it never records agent output as
`userValidation`. All automatic validation, including technical checks and
review decisions, uses the configured `rubber-duck` validator
(`gpt-5.6-luna`, high reasoning, `all-validation` scope) and records that
profile.

## Usage

Commands: `/user-test <journey>` (generate a functionality-only user handoff),
`/run-test <script>` (run agent-owned technical checks and the automated
functionality test).

Scripts use configured artifact paths, with `plan/` and
`plan/story-map/<journey-name>.yaml` as portable defaults. Evidence is recorded
under the active ticket's configured evidence path.

## Post-implementation validation

After implementation, the agent runs all applicable technical checks and the
automated functionality test as the final acceptance-level technical check,
using the stated setup, data, exact steps, assertions, visible/output and
persisted/external expected results, failure paths, and cleanup. Guided mode
then uses the generated functionality-only handoff for user validation and
waits for `PASS`, `FAIL`, `BLOCKED`, or approved `NOT APPLICABLE`. Automatic
mode runs the functionality charter itself, records `automaticValidation`, and
continues to review without a user response. The ticket remains in `verifying`
until the mode-appropriate evidence and exact automatic validation profile are
terminal.

## When to use

- Creating usability and functionality charters from journey specifications
- Running supported automated real-system functionality tests with screenshots
  when applicable
- Validating visible, persisted, and external effects with explicit outcomes
