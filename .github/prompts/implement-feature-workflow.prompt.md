---
name: Implement Feature From Ticket
description: Review a ticket, validate the current product, implement the change, rerun the gates, open the PR, and stay in the loop until it is green and merge-ready.
---

You have to solve the problem specified in `${TICKET_OR_FEATURE}` end to end.

## Outcome

Deliver the feature with the full engineering loop, not just the code:
- ticket understanding
- baseline validation
- implementation
- documentation updates where needed
- regression protection
- branch / commit / push / PR flow
- PR monitoring and repair until the branch is merge-ready

## Operating rules

1. Start from the ticket, not from assumptions.
2. Keep the implementation inside the stated scope.
3. When the change can be proved through tests, prefer a failing-test-first loop.
4. Run existing tests before and after the change.
5. Prefer the highest-level existing test that proves the software is still usable.
6. If functional/end-to-end coverage exists, run it before coding and again before finishing.
7. If the needed test layer does not exist, use the best available existing checks and explicitly note the gap.
8. Keep implementation slices small enough to review, validate, and repair cleanly.
9. Do not autonomously push a branch that has avoidable local failures. If the
   user explicitly directs the push, warn once, record the bypassed gates, and
   use the `aidd-push` override contract.
10. Update documentation when the ticket changes behavior, commands, config, workflows, APIs, setup, or any operator/user-facing expectation.
11. Do not stop at "PR opened." Stay in the feedback loop until the PR is green, conflict-free, and ready to merge, or until an external blocker is real.

## Required workflow

### 1. Review the ticket

Extract and restate:
- objective
- in-scope work
- out-of-scope work
- acceptance criteria
- dependencies
- risks
- files or subsystems likely to change

### 2. Baseline the current system

Before implementing:
- inspect the affected code paths
- inspect existing tests for the area
- run the most relevant existing checks
- prioritize functional or end-to-end tests first when they exist
- then run the next most relevant integration/unit/build checks

The goal is to know the current state before touching code.

### 3. Choose the proving validation path

Before coding, state:

- which test, test suite, or user-visible validation will prove the change
- whether strict TDD mode is practical for this ticket

If the change is behavior-driven and testable, use strict TDD mode:

1. write or update the proving test first
2. watch it fail for the intended reason
3. implement only the code needed to make it pass

If strict TDD mode is not practical, explicitly state the reason and use the strongest available validation path instead.

### 4. Implement the smallest complete change

- follow the repo's architecture and conventions
- update or add tests with the change
- update the relevant documentation with the change
- keep changes reviewable
- avoid unrelated cleanup unless it is directly required to make the ticket correct
- if the task grows too large, split the execution into smaller coherent slices and re-check the proving validation after each slice

Relevant docs may include:
- `README.md`
- setup or developer guides
- API or integration docs
- ticket/backlog notes when execution details changed
- operator or deployment docs

### 5. Re-run the gates and verify docs impact

After implementation, run the relevant local gates again:
- format
- lint
- type-check
- unit tests
- integration tests
- functional or end-to-end tests
- build/package step if the repo has one

Also confirm the changed behavior is reflected in the relevant docs or explicitly note why no doc change was needed.

Fix failures before moving on.

### 6. Prepare the branch and commit

- create a feature branch if one does not already exist
- use the repo's branch naming convention; otherwise use `feature/<ticket-or-scope-slug>`
- stage only the intended changes
- commit using the repo's commit convention; if none exists, use a concise imperative subject

### 7. Push and create the PR

- push the feature branch
- create the PR with a clear summary, scope, test evidence, and known risks
- ensure the correct base branch is used
- make sure the required checks are triggered

### 8. Monitor the PR until it is merge-ready

Stay in a repair loop:
1. watch CI results
2. fix failing checks
3. resolve merge conflicts
4. address review comments
5. re-run local checks when needed
6. push updates
7. repeat until everything required is green

### 9. Only call it done at the correct end state

Done means one of these is true:
- the PR is green, reviewed as required, conflict-free, and ready to merge
- the PR is merged
- there is an external blocker that cannot be resolved without human input, and everything else is already complete

## Final report requirements

Report:
1. what was implemented
2. what documentation was updated, or why none was needed
3. what tests/gates were run before and after
4. branch and PR status
5. any remaining blocker only if one truly exists
