# aidd-preimplementation-checklist

Provide a repeatable stop/go decision before implementation begins.

## Use when

- The planning layer needs to be created, reconciled, or reviewed.
- Parent links, status, approval, coverage, or evidence must be made explicit.

## Contract

Inputs and outputs are defined in [SKILL.md](SKILL.md). The skill requires the
selected ticket and active ancestors to be in `open`, preserves stable IDs and
traceability, and stops on missing prerequisites. It does not implement, move
records, commit, push, merge, or silently generate downstream artifacts.
