---
name: aidd-create-phases
description: Plan meaningful delivery phases from approved objective, scope, and capabilities. Use when sequencing outcomes before feature decomposition.
---

import ../planning-skill-interface.md

# aidd-create-phases

Create outcome-oriented phases with explicit entry and exit gates.

Apply [../development-mode.md](../development-mode.md) when resolving the
parent-approval gate and phase-to-feature handoff.

## Contract

```sudolang
Lifecycle {
  profile = planningMutation
}

PlanningSkill {
  profile = planningMutation
  layer = phase
  parentLayers = [objective, scope, capability]
  childLayers = [feature]
  writableArtifacts = [phaseRecords, phaseIndex]
  mode = inspect | draft | write
}
```

## Inputs

- Repository root and the relevant approved planning artifact IDs.
- The phase index and every record in both the configured phase `open` and
  `closed` directories.

## Outputs

- One record per phase under the configured phase `open` directory, plus an
  updated phase index/list containing current paths for open and closed phases.

## Process

```sudolang
createPhases(request) => PhaseIndex {
  1. require approved objective, scope, and capabilities
  2. choose adaptive depth; use the smallest phase structure that preserves risk and verification
  3. read both phase status directories and preserve existing PHASE IDs
  4. create stable PHASE IDs with outcome, entry conditions, exit conditions, sequence, dependencies, and status in the phase open directory
  5. map each phase to one or more capabilities and evidence expectations
  6. synchronize the phase index with every current record path
  7. when an authorized status transition changes open/closed classification, move the record and record old/new paths
  8. obtain configured parent approval before feature generation in guided
     mode; in automatic mode, record the bootstrap-authorized decision and
     continue after verified writes without asking or waiting
}
```

## Constraints

```sudolang
Constraints {
  Read both open and closed phase directories; never create duplicate IDs
  Create new phases in open and move records when status classification changes
  Keep phase index entries synchronized with current record paths
  Preserve path history and stable IDs across status moves
  In automatic mode, do not classify phase coverage or readiness without the
    exact Rubber Duck `gpt-5.6-luna` high-reasoning `all-validation` profile
  Do not create or modify artifacts outside the named planning layer
  Escalate ambiguity, conflict, or material change instead of guessing
  In automatic mode, never bypass missing entry conditions, blocked evidence,
    or contradictory phase boundaries
}
```

## Commands

```sudolang
Commands {
  /create-phases [request]
  - propose or update phases and their gates only
}
```
