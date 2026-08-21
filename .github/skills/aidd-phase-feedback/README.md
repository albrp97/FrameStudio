# aidd-phase-feedback

Turn observed phase feedback into bounded decisions without losing history or silently changing scope.

## Use when

- The planning layer needs to be created, reconciled, or reviewed.
- Parent links, status, approval, coverage, or evidence must be made explicit.

## Contract

Inputs and outputs are defined in [SKILL.md](SKILL.md). The skill preserves
stable IDs and traceability while moving an approved phase between `open` and
`closed` and synchronizing its index. It stops on missing prerequisites and
does not implement, commit, push, merge, or silently generate downstream
artifacts.
