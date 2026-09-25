# aidd-create-repository-map

Describe repository surfaces and ownership without turning discovery into
implementation planning. After approval, persist the map at the configured
path and verify it; response-only map content is not a completed write. `write`
without a recoverable approved map is blocked.

## Use when

- The planning layer needs to be created, reconciled, or reviewed.
- Parent links, status, approval, coverage, or evidence must be made explicit.

## Contract

Inputs and outputs are defined in [SKILL.md](SKILL.md). The skill is bounded to its named planning layer, preserves stable IDs and traceability, and stops on missing prerequisites. It does not implement, commit, push, merge, or silently generate downstream artifacts.

## Commands

```sudolang
Commands {
  /create-repository-map [request]
  - produce and, after authorization, persist a source-linked repository map

  /create-repository-map draft [request]
  - produce a map proposal without writing

  /create-repository-map write [request]
  - persist the previously approved repository map and verify its path
}
```
