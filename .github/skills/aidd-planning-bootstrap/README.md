# aidd-planning-bootstrap

Establish the minimum trustworthy planning context before any downstream artifact is generated.

## Use when

- The planning layer needs to be created, reconciled, or reviewed.
- Parent links, status, approval, coverage, or evidence must be made explicit.

## Contract

Inputs and outputs are defined in [SKILL.md](SKILL.md). The skill reconciles
both `open` and `closed` phase, feature, and ticket directories with their
indexes, preserves stable IDs and traceability, and stops on missing
prerequisites. It does not implement, commit, push, merge, or silently
generate downstream artifacts.
