---
name: aidd-preimplementation-checklist
description: Verify that an approved ticket is safe and ready to implement, including ancestry, scope, baseline, evidence, commands, gates, and ownership. Use immediately before implementation begins.
---

import ../planning-skill-interface.md

# aidd-preimplementation-checklist

Provide a repeatable stop/go decision before implementation begins.

Apply [../development-mode.md](../development-mode.md) when resolving the
execution approval and next internal route.

## Contract

```sudolang
Lifecycle {
  profile = readOnlyAnalysis
}

PlanningSkill {
  profile = readOnlyAnalysis
  layer = implementationReadiness
  parentLayers = [phase, feature, ticket]
  childLayers = [implementation]
  writableArtifacts = []
  mode = inspect
}
```

## Inputs

- Repository root and the relevant approved planning artifact IDs.
- The selected ticket and its phase/feature ancestors in both lifecycle
  directories, including their current paths and index entries.

## Outputs

## Process

```sudolang
runPreimplementationChecklist(ticket) => ChecklistResult {
  1. verify objective -> scope -> capability -> phase -> feature -> ticket links, stable IDs, statuses, approvals, and current paths
  2. require the selected ticket and its active phase/feature ancestors to be in open; reject a closed ticket or closed ancestor as active work
  3. verify ticket scope/non-goals, dependencies, risks, affected surfaces,
     protected behaviors, commands, gates, evidence path, at least one
     executable automated functionality test per acceptance outcome, and the
     exact user-validation plan required before closure
  4. verify required baseline evidence or baseline plan exists according to the configured sequencing; missing evidence keeps ready=false
  5. confirm ownership and no overlapping active ticket; surface unresolved decisions
  6. in automatic mode, resolve the exact Rubber Duck
     `gpt-5.6-luna` high-reasoning `all-validation` profile before
     classifying the checklist result
  7. return ready=true only when every required check passes; in automatic
     mode, record bootstrap-authorized execution approval and the validation
     profile; otherwise list blockers and do not start implementation
}
```

## Constraints

```sudolang
Constraints {
  Read both open and closed directories and reject stale index paths
  Never move records during this read-only checklist
  Treat a closed ticket or ancestor as a blocker until explicitly reopened and moved to open
  In automatic mode, do not return a terminal checklist result without the
    exact Rubber Duck `gpt-5.6-luna` high-reasoning `all-validation` profile
  Do not claim readiness when the required automated functionality test is
    missing, non-executable, or not mapped to acceptance outcomes
  Do not create or modify artifacts outside the named planning layer
  Escalate ambiguity, conflict, or material change instead of guessing
  In automatic mode, do not ask for execution approval after a ready result;
    route directly to TDD while preserving all blockers
}
```

## Commands

```sudolang
Commands {
  /run-preimplementation-checklist [ticket-id]
  - return an auditable ready/not-ready decision without implementing
}
```
