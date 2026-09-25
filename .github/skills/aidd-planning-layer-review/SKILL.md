---
name: aidd-planning-layer-review
description: Review objective, scope, capability, phase, feature, and ticket planning layers for consistency, coverage, and readiness. Use before execution or after planning changes.
---

import ../planning-skill-interface.md

# aidd-planning-layer-review

Find broken links, missing gates, unsupported claims, and hierarchy drift before work starts.

Apply [../development-mode.md](../development-mode.md) when returning the
review result to the guided or automatic planning loop.

## Contract

```sudolang
Lifecycle {
  profile = readOnlyAnalysis
}

PlanningSkill {
  profile = readOnlyAnalysis
  layer = planningReview
  parentLayers = [selectedPlanningLayer, adjacentLayers]
  childLayers = []
  writableArtifacts = []
  mode = inspect
}
```

## Inputs

- Repository root and the relevant approved planning artifact IDs.
- Every phase, feature, and ticket record in both `open` and `closed`, plus
  the phase/feature/backlog indexes.

## Outputs

## Process

```sudolang
reviewPlanningLayer(request) => PlanningReview {
  1. load the requested layer and all ancestors/children needed for traceability
  2. inspect both open and closed directories and resolve records by stable ID
  3. check one-parent rules, stable IDs, statuses, coverage/evidence links, scope boundaries, approval state, and status/path classification
  4. check for duplicate IDs, stale index paths, orphaned records, and closed records referenced as active work
  5. in automatic mode, resolve the exact Rubber Duck profile before
      classifying any pass, warning, blocker, or readiness decision
  6. report passes, warnings, blockers, orphaned artifacts, and recommended
      smallest corrections with the mode-appropriate validation metadata
  7. keep readiness false for missing evidence or non-terminal gates
  8. do not mutate artifacts, move files, or generate missing children during review
}
```

## Constraints

```sudolang
Constraints {
  Report every status/path mismatch; do not repair it implicitly
  Treat blocked records as open and closed records as ineligible for active work
  In automatic mode, do not classify a planning review without the exact
    Rubber Duck `gpt-5.6-luna` high-reasoning `all-validation` profile
  Do not create or modify artifacts outside the named planning layer
  Escalate ambiguity, conflict, or material change instead of guessing
  In automatic mode, return a verified pass or precise blocker for the
    orchestrator; do not ask for a separate approval response
}
```

## Commands

```sudolang
Commands {
  /review-planning-layer [layer-or-id]
  - return a read-only planning review and readiness decision
}
```
