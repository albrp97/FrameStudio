---
name: aidd-create-features
description: Decompose an approved phase into outcome-focused features mapped to capabilities. Use when a phase is ready for feature planning.
---

import ../planning-skill-interface.md

# aidd-create-features

Create independently understandable feature outcomes without mixing ticket execution details.

Apply [../development-mode.md](../development-mode.md) when resolving phase
approval and the feature-to-ticket handoff.

## Contract

```sudolang
Lifecycle {
  profile = planningMutation
}

PlanningSkill {
  profile = planningMutation
  layer = feature
  parentLayers = [phase, capability]
  childLayers = [ticket]
  writableArtifacts = [featureRecords, featureIndex]
  mode = inspect | draft | write
}
```

## Inputs

- Repository root and the relevant approved planning artifact IDs.
- The feature index and every record in both the configured feature `open` and
  `closed` directories.

## Outputs

- One record per feature under the configured feature `open` directory, plus
  an updated feature index/list containing current paths for open and closed
  features.

## Process

```sudolang
createFeatures(request) => FeatureIndex {
  1. require an approved, unblocked phase and its capability links
  2. read both feature status directories and preserve existing FEAT IDs
  3. create stable FEAT IDs in the feature open directory; each feature belongs to exactly one phase and at least one capability
  4. record outcome, scope, non-goals, dependencies, risks, affected surfaces, acceptance outcomes, and evidence plan
  5. synchronize the feature index with every current record path
  6. move a record between open and closed only when its authorized status transition changes classification
  7. preserve IDs on rename and retain unresolved decisions as blockers or needs-review
  8. obtain feature approval before generating tickets in guided mode; in
     automatic mode, record the bootstrap-authorized decision and continue
     after verified writes without asking or waiting
}
```

## Constraints

```sudolang
Constraints {
  Read both open and closed feature directories; never create duplicate IDs
  Create new features in open and move records when status classification changes
  Keep feature index entries synchronized with current record paths
  Preserve path history and stable IDs across status moves
  In automatic mode, do not classify feature coverage or readiness without the
    exact Rubber Duck `gpt-5.6-luna` high-reasoning `all-validation` profile
  Do not create or modify artifacts outside the named planning layer
  Escalate ambiguity, conflict, or material change instead of guessing
  In automatic mode, never generate children from a missing, blocked, or
    contradictory feature
}
```

## Commands

```sudolang
Commands {
  /create-features [phase-id]
  - propose features for one approved phase only
}
```
