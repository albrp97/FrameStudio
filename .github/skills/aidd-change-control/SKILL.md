---
name: aidd-change-control
description: Assess and govern material planning changes with explicit impact, approval, traceability, and replan decisions. Use when scope, outcome, capability, sequencing, or risk materially changes.
---

import ../planning-skill-interface.md

# aidd-change-control

Prevent silent downstream drift while allowing evidence-based replanning.

## Contract

```sudolang
Lifecycle {
  profile = planningMutation
}

PlanningSkill {
  profile = planningMutation
  layer = planningChange
  parentLayers = [objective, scope, capability, phase, feature, ticket]
  childLayers = [affectedPlanningLayers]
  writableArtifacts = [configuredAffectedPlanningArtifacts]
  mode = inspect | draft | write
}
```

## Inputs

- Repository root and the relevant approved planning artifact IDs.
- The affected records and indexes in both `open` and `closed` directories.

## Outputs

## Process

```sudolang
changeControl(request) => ChangeDecision {
  1. compare requested and approved objective, scope, capability, phase, feature, ticket, dependencies, risks, and gates
  2. classify no-change, routine correction, or material change with affected descendants
  3. for material change, record stable change ID, rationale, impact, affected artifacts, evidence, owner, and approval requirement
  4. preserve history and IDs; replan only the smallest affected subtree after approval
  5. when an approved status change crosses the open/closed boundary, move only
     the affected record or approved subtree and synchronize indexes
  6. block execution/readiness while required approval or evidence is missing
}
```

## Constraints

```sudolang
Constraints {
  Inspect both lifecycle directories and preserve each record's current path history
  Never use a move to hide a status change or duplicate an artifact
  Do not create or modify artifacts outside the named planning layer
  Escalate ambiguity, conflict, or material change instead of guessing
}
```

## Commands

```sudolang
Commands {
  /replan-when-necessary [change]
  - assess change impact and route approved material changes through controlled replanning
}
```
