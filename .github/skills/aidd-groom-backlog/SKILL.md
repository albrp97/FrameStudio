---
name: aidd-groom-backlog
description: Groom an existing planning backlog by clarifying, ordering, deduplicating, and blocking stale items without silently replanning material scope. Use when backlog readiness or ordering has degraded.
---

import ../planning-skill-interface.md

# aidd-groom-backlog

Keep planned work actionable while distinguishing routine maintenance from change control.

Apply [../development-mode.md](../development-mode.md) when routing the next
ready ticket after grooming.

## Contract

```sudolang
Lifecycle {
  profile = planningMutation
}

PlanningSkill {
  profile = planningMutation
  layer = backlog
  parentLayers = [phase, feature]
  childLayers = [ticket]
  writableArtifacts = [ticketRecords, backlog]
  mode = inspect | write
}
```

## Inputs

- Repository root and the relevant approved planning artifact IDs.
- The phase, feature, and ticket indexes plus records in both `open` and
  `closed` directories.

## Outputs

- Synchronized index/list paths after any authorized status transition.

## Process

```sudolang
groomBacklog(request) => GroomingReport {
  1. inspect approved phases, features, tickets, statuses, dependencies, age, evidence, duplicates, and current lifecycle paths
  2. make only routine, traceable hygiene updates such as clarification, ordering, or stale-status marking
  3. when an authorized status change crosses open/closed classification, move the same record and synchronize indexes
  4. preserve stable IDs, parent links, ownership, path history, and audit history
  5. if outcome, scope, capability, phase, feature, or material risk changes, stop routine grooming and invoke change control
  6. do not create implementation children or claim readiness from grooming alone
}
```

## Constraints

```sudolang
Constraints {
  Inspect both open and closed directories and reject status/path mismatches
  Never duplicate, delete, or silently archive a planning record
  Keep phase, feature, and backlog indexes synchronized after a move
  In automatic mode, do not classify grooming or next-ticket readiness without
    the exact Rubber Duck `gpt-5.6-luna` high-reasoning `all-validation` profile
  Do not create or modify artifacts outside the named planning layer
  Escalate ambiguity, conflict, or material change instead of guessing
  In automatic mode, continue to the highest-ranked ready ticket after
    verified grooming; do not wait for a user selection
}
```

## Commands

```sudolang
Commands {
  /groom-backlog [scope]
  - report safe grooming updates or a change-control blocker
}
```
