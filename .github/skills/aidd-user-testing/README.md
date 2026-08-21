# aidd-user-testing

Generates dual usability and functionality charters — human (think-aloud
protocol) and AI agent (real-system execution with configured artifacts) — from
user journey specifications.

## Why

Human testers catch usability friction that automated tests miss. Agent charters
provide repeatable evidence for visible and persisted behavior. The two scripts
share success criteria but remain distinct purposes.

## Usage

Commands: `/user-test <journey>` (generate human and agent scripts),
`/run-test <script>` (execute an agent script with screenshots).

Scripts use configured artifact paths, with `plan/` and
`plan/story-map/<journey-name>.yaml` as portable defaults. Evidence is recorded
under the active ticket's configured evidence path.

## Post-implementation validation

After technical verification, use the generated handoff to test the completed
ticket with the stated setup, data, exact steps, visible and persisted/external
expected results, failure paths, and cleanup. Return `PASS`, `FAIL`, `BLOCKED`,
or an approved `NOT APPLICABLE` result; the ticket remains in `verifying` until
that result is recorded in evidence.

## When to use

- Creating usability and functionality charters from journey specifications
- Running supported real-system functionality tests with screenshots when applicable
- Validating visible, persisted, and external effects with explicit outcomes
