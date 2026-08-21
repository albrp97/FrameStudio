# aidd-planning-layer-review

Find broken links, missing gates, unsupported claims, and hierarchy drift before work starts.

## Use when

- The planning layer needs to be created, reconciled, or reviewed.
- Parent links, status, approval, coverage, or evidence must be made explicit.

## Contract

Inputs and outputs are defined in [SKILL.md](SKILL.md). The skill reviews both
`open` and `closed` directories, checks status/path and index consistency,
preserves stable IDs and traceability, and stops on missing prerequisites. It
does not implement, move files, commit, push, merge, or silently generate
downstream artifacts.
