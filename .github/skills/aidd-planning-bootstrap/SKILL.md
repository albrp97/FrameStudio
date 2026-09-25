---
name: aidd-planning-bootstrap
description: Initialize or reconcile a repository planning system from objective, scope, maps, and delivery configuration. Use when planning artifacts are absent, stale, or inconsistent.
---

import ../planning-skill-interface.md

# aidd-planning-bootstrap

Establish the minimum trustworthy planning context before any downstream artifact is generated.

Apply [../development-mode.md](../development-mode.md) when deciding whether
the reconciled planning context waits for approval or continues automatically.

## Contract

```sudolang
Lifecycle {
  profile = planningMutation
}

PlanningSkill {
  profile = planningMutation
  layer = planningSystem
  parentLayers = [repositoryContext]
  childLayers = [objective, scope, capability, phase, feature, ticket]
  writableArtifacts = [configuredPlanningScaffolding]
  mode = inspect | draft | write
}
```

## Inputs

- Repository root and the relevant approved planning artifact IDs.
- Configured phase, feature, and ticket indexes plus both `open` and `closed`
  directories for each layer.
- The selected `delivery.development.mode`, defaulting to `guided` when absent.

## Outputs

- In `inspect`, `draft`, or `status` mode, a report only. In `write` mode,
  persist only the explicitly named and approved bootstrap artifacts or index
  updates using repository file operations; never substitute response content
  for a file write.
- A reconciled report of each record's status, current path, index entry, and
  any duplicate, orphaned, or status/path mismatch.

```sudolang
ArtifactWriteResult {
  path
  operation: created | updated | unchanged | skipped | blocked
  verified
  reason
}
```

## Process

```sudolang
bootstrap(request) => PlanningContext {
  1. load objective, scope, maps, configured artifact paths, and existing statuses
  2. inspect both open and closed directories for phases, features, and tickets
  3. classify planning depth as lightweight | standard | full using request and repository evidence
  4. validate canonical hierarchy, stable ID prefixes, status classification, and index paths
  5. report gaps, conflicts, stale paths, duplicate IDs, and approval needed
  6. when write mode is authorized, use repository file operations for each approved bootstrap artifact or index update
  7. re-read every written path and record verified write results; stop if verification fails
  8. in guided mode, stop before generating children when a parent is missing,
     blocked, or unapproved; in automatic mode, record bootstrap-authorized
     planning decisions and continue only when the parent is present, unblocked,
     and evidenced
  9. in automatic mode, resolve the exact Rubber Duck `gpt-5.6-luna`
     high-reasoning `all-validation` profile before classifying any planning
     verification or readiness result
}
```

### Artifact persistence

The default planning bootstrap is report-only until an artifact update is
explicitly approved. Once approved, the skill must create or update the named
configured paths with a file-writing tool and then verify them. A Markdown
planning context shown in chat is not a saved planning artifact and must be
labeled `not written`. If the file
operation is unavailable or fails, report the exact path as `blocked` and do
not claim that bootstrap completed.
For every `created` or `updated` result, the execution must include a host file
create/edit call. Creating missing parent directories for approved files and
the approved `open`/`closed` layout is allowed, but those directory changes
must be listed and verified too.

Use `draft` or `status` when no mutation is intended. Use `write` to persist a
previously approved update. A `write` request without a recoverable approved
update is blocked; do not reconstruct unapproved contents. Never generate
phase, feature, or ticket records as an incidental result of writing bootstrap
indexes or reconciliation output.

## Constraints

```sudolang
Constraints {
  Reconcile open/closed directories and indexes before downstream planning
  Do not leave a record duplicated in both directories or indexed at a stale path
  In automatic mode, do not classify planning verification or readiness
    without the exact Rubber Duck `gpt-5.6-luna` high-reasoning
    `all-validation` profile
  Do not create or modify artifacts outside the named planning layer
  Do not treat a response-only planning result as a written artifact
  Use file operations for approved writes and verify every resulting path
  Report failed or unavailable writes as blockers, never as successful output
  Escalate ambiguity, conflict, or material change instead of guessing
  In automatic mode, do not ask for downstream planning approval or wait for a
    user response; route to the next planning layer after verified writes
  Never treat automatic planning authorization as permission to ignore missing
    parents, contradictory scope, or blocked evidence
}
```

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
