# aidd-groom-backlog

Keep planned work actionable while distinguishing routine maintenance from change control.

## Use when

- The planning layer needs to be created, reconciled, or reviewed.
- Parent links, status, approval, coverage, or evidence must be made explicit.

## Contract

Inputs and outputs are defined in [SKILL.md](SKILL.md). The skill inspects
`open` and `closed`, moves a record only for an authorized status transition,
synchronizes indexes, preserves stable IDs and traceability, and stops on
missing prerequisites. It does not implement, commit, push, merge, or
silently generate downstream artifacts.
