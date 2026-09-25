---
name: aidd-phase-feedback
description: Capture feedback against an active phase and its outcome, entry, and exit conditions. Use after evidence, review, or stakeholder feedback.
---

import ../planning-skill-interface.md

# aidd-phase-feedback

Turn observed phase feedback into bounded decisions without losing history or silently changing scope.

Apply [../development-mode.md](../development-mode.md) when routing the next
phase or recording a blocked closeout.

## Contract

```sudolang
Lifecycle {
  profile = planningMutation
}

PlanningSkill {
  profile = planningMutation
  layer = phaseFeedback
  parentLayers = [phase, feature, ticket]
  childLayers = [planningChange]
  writableArtifacts = [phaseRecord, phaseFeedbackArtifacts, indexes]
  mode = inspect | draft | write
}
```

## Inputs

- Repository root and the relevant approved planning artifact IDs.
- The phase index and the selected phase record in either its `open` or
  `closed` directory, plus linked feature/ticket records in both directories.

## Outputs

- An updated phase index/current path when an authorized phase status transition
  moves the record between `open` and `closed`.

## Process

```sudolang
recordPhaseFeedback(request) => PhaseFeedback {
  1. require a phase ID and identify current status, outcome, entry/exit conditions, evidence, linked children, and current open/closed path
  2. classify feedback as observation, correction, blocker, or material change
  3. append source-linked feedback and proposed disposition; preserve prior decisions and IDs
  4. update status only when evidence and configured approval support it; in
     automatic mode, use verified bootstrap authorization for routine status
     transitions, and classify the closeout with the exact Rubber Duck
     `gpt-5.6-luna` high-reasoning `all-validation` profile
  5. move the phase between open and closed when status classification changes and synchronize the phase index
  6. route material outcome/scope/capability changes to change control; do not replan silently
}
```

## Constraints

```sudolang
Constraints {
  Inspect both lifecycle directories and reject status/path mismatches
  Never close a phase with open or incomplete required child features
  Never duplicate or silently archive the phase record
  In automatic mode, do not classify phase closeout without the exact Rubber
    Duck `gpt-5.6-luna` high-reasoning `all-validation` profile
  Do not create or modify artifacts outside the named planning layer
  Escalate ambiguity, conflict, or material change instead of guessing
  In automatic mode, continue to the next ready phase after terminal closeout
    without asking or waiting; preserve real blockers as blocked
}
```

## Commands

```sudolang
Commands {
  /phase-feedback [phase-id]
  - record and classify feedback for one phase
}
```
