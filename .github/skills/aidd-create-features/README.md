# aidd-create-features

Create independently understandable feature outcomes without mixing ticket execution details.

## Use when

- The planning layer needs to be created, reconciled, or reviewed.
- Parent links, status, approval, coverage, or evidence must be made explicit.

## Contract

Inputs and outputs are defined in [SKILL.md](SKILL.md). New feature records are
individual files in the configured `open` directory; terminal records move to
`closed` and the feature index is synchronized. The skill preserves stable IDs
and traceability, stops on missing prerequisites, and does not implement,
commit, push, merge, or silently generate downstream artifacts.
