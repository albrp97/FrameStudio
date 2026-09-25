# aidd-planning-bootstrap

Establish the minimum trustworthy planning context before any downstream artifact is generated.

## Use when

- The planning layer needs to be created, reconciled, or reviewed.
- Parent links, status, approval, coverage, or evidence must be made explicit.

## Contract

Inputs and outputs are defined in [SKILL.md](SKILL.md). The skill reconciles
both `open` and `closed` phase, feature, and ticket directories with their
indexes, preserves stable IDs and traceability, and stops on missing
prerequisites. After an approved `write` operation it persists only the named
bootstrap artifacts or index updates, verifies their paths, and reports any
failed write as blocked. It does not implement, commit, push, merge, or
silently generate downstream artifacts. A `write` request without a
recoverable approved update is blocked.

## Commands

```sudolang
Commands {
  /planning-bootstrap [request]
  - inspect or reconcile planning context; persist only after configured approval

  /planning-bootstrap draft [request]
  - produce a planning proposal without writing

  /planning-bootstrap status [request]
  - report planning artifacts and inconsistencies without writing

  /planning-bootstrap write [request]
  - persist the previously approved bootstrap artifacts and verify each path
}
```
