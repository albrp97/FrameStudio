# aidd-ticket-creator

Plans meaningful work as **phases -> features -> tickets**, then executes one
focused ticket at a time with configurable baseline, verification, quality-gate,
evidence, review, and approval checkpoints.

## Why

Phases preserve delivery order, features preserve meaningful outcomes, and
tickets keep implementation small enough to test, review, and merge without
losing the larger context.

## Usage

Commands: `/ticket` (create or update a feature and its tickets inside an
approved phase), `/execute` (run one approved ticket), `/list
[phases|features|tickets]`, and `/help`.

The phase and feature indexes and ticket backlog are maintained at their
configured paths. Each phase, feature, and ticket is an individual record in
an `open` or `closed` directory, with requirements written in `Given X, should
Y` form. Execution records baseline, verification, gate, and review results
through `/evidence`, then moves terminal records to `closed` after approval
before the next ticket. A checkpoint is taken every three completed tickets.

## When to use

- Planning a delivery phase, feature, or focused ticket
- Decomposing an approved feature into independently verifiable tickets
- Executing a ticket while preserving phase and feature traceability
