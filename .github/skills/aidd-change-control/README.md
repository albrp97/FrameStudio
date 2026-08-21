# aidd-change-control

Prevent silent downstream drift while allowing evidence-based replanning.

## Use when

- The planning layer needs to be created, reconciled, or reviewed.
- Parent links, status, approval, coverage, or evidence must be made explicit.

## Contract

Inputs and outputs are defined in [SKILL.md](SKILL.md). Approved material
changes may move only affected records between `open` and `closed`, while
preserving stable IDs, path history, and indexes. The skill stops on missing
prerequisites and does not implement, commit, push, merge, or silently
generate downstream artifacts.
