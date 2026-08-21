# aidd-pipeline

Reads an explicitly selected markdown ticket section and executes each item as
an isolated subagent delegation through the configured delegation capability.

## Why

Running a multi-step plan manually means re-entering context for each step and
losing track of which steps succeeded. `/aidd-pipeline` carries the delivery context into each ticket, records
per-step evidence, stops on failure, and reports artifacts and blockers. Each
ticket must receive and record its required user-validation result before it
can close. After integration and review, the integration owner runs the
configured `/commit` -> `/push` -> `/aidd-pr` sequence.

## Usage

Point `/aidd-pipeline` at a `.md` file with a section explicitly titled
`Pipeline`, `Steps`, `Tickets`, or `Commands`, or identify the executable list
in the user request. Policy prose, acceptance checklists, arbitrary first
lists, and fenced code are not treated as executable work by default.

## When to use

- You have a markdown file with an explicitly selected ticket list
- You need sequential subagent execution with stop-on-failure semantics
- A multi-step plan needs phase, feature, ticket, gate, and evidence tracking
