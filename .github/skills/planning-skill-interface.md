# Planning skill interface

Planning skills import the lifecycle interface and resolve the
`planningMutation` profile. Each skill declares its owned layer, parent,
children, writable paths, and whether the current invocation is read-only or
authorized to mutate.

import lifecycle-interface.md
import planning-artifact-lifecycle.md

```sudolang
PlanningSkill {
  profile: planningMutation | readOnlyAnalysis
  layer
  parentLayers[]
  childLayers[]
  writableArtifacts[]
  mode: inspect | draft | write
}
```

## Shared behavior

- Read `.github/aidd-config.yml`, configured artifacts, relevant ancestors,
  existing records in both lifecycle directories, and explicit user
  constraints.
- Produce a traceable report or an authorized artifact update with stable IDs,
  current paths, parent/child links, coverage, approval state, evidence links,
  risks, non-goals, and unresolved questions.
- Own only the declared planning layer. Never own implementation, commits,
  pushes, provider operations, merges, or delivery readiness.
- In `inspect` mode, do not write or move artifacts. The `readOnlyAnalysis`
  profile is mandatory for skills that never own planning mutations.
- Create new records in `open`; move the same stable-ID record only when an
  authorized status transition changes its lifecycle classification.
- Synchronize indexes and path references after every authorized write and
  verify each written path.
- Require an existing, unblocked, approved parent before child generation.
- Preserve unknowns and missing evidence as gaps or blockers rather than
  inferred passes.
- Route material scope or sequencing changes to `aidd-change-control`.

Layer-specific skills should contain only their distinct inputs, outputs,
process, constraints, and commands. Do not repeat this shared behavior.
