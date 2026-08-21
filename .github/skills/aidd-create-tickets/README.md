# aidd-create-tickets

Produce bounded tickets that can be implemented and verified independently.

## Use when

- The planning layer needs to be created, reconciled, or reviewed.
- Parent links, status, approval, coverage, or evidence must be made explicit.

## Contract

Inputs and outputs are defined in [SKILL.md](SKILL.md). New ticket records are
individual files in the configured `open` directory; terminal records move to
`closed` and the backlog is synchronized. Every ticket includes a
post-implementation user-validation plan, and closure requires its recorded
result or an approved not-applicable decision. The skill preserves stable IDs
and traceability, stops on missing prerequisites, and does not implement,
commit, push, merge, or silently generate downstream artifacts.
