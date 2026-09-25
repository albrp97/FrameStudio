---
name: aidd-create-capability-map
description: Derive a capability map from an approved objective, scope, and repository map. Use before phase or feature planning.
---

import ../planning-skill-interface.md

# aidd-create-capability-map

Connect desired outcomes to evidenced product or operational capabilities.

Apply [../development-mode.md](../development-mode.md) when deciding whether
capability approval is requested or bootstrap-authorized automatic planning
continues.

## Contract

```sudolang
Lifecycle {
  profile = planningMutation
}

PlanningSkill {
  profile = planningMutation
  layer = capability
  parentLayers = [objective, scope, repositoryMap]
  childLayers = [phase, feature]
  writableArtifacts = [capabilityMap]
  mode = inspect | draft | write
}
```

## Inputs

- Repository root and the relevant approved planning artifact IDs.
- The configured capability-map path
  (`delivery.artifacts.capability_map`, normally
  `docs/specs/capability-map.md`).

## Outputs

- A capability-map proposal in `draft` or `review` mode, or the persisted
  configured capability-map file in `write` mode after explicit approval.
  Returning the map in chat without writing the configured path is not
  completion.

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
createCapabilityMap(request) => CapabilityMap {
  1. require an approved objective and scope plus a current repository map
  2. identify capabilities, affected surfaces, dependencies, risks, and coverage gaps
  3. assign stable CAP IDs and link every capability to its objective/scope and source evidence
  4. in guided mode, present the map for approval before creating phases or
     features; in automatic mode, record the bootstrap-authorized decision and
     continue only after the verified map write
  5. after approval, use a repository file-writing tool to create or update the configured capability-map path
  6. re-read the path and record a verified write result; stop if writing or verification fails
   7. in automatic mode, classify the verified map write and coverage result with
      the exact Rubber Duck `gpt-5.6-luna` high-reasoning `all-validation` profile
   8. do not infer capabilities from unverified assumptions
}
```

### Artifact persistence

The map is a durable planning artifact, not only a response. In `write` mode,
create or update `delivery.artifacts.capability_map` with the approved map,
preserve unrelated content, and verify the resulting file. A map printed in
the response must be labeled `not written` until that operation succeeds.
Writing the capability map never authorizes phases, features, or tickets.
`write` without a recoverable approved map is blocked; do not reconstruct an
unapproved map from the request.
For a `created` or `updated` result, the execution must include a host file
create/edit call and a post-write read. Creating the configured parent
directory is part of the approved write; a response code block is not.

## Constraints

```sudolang
Constraints {
  In automatic mode, do not classify map coverage or readiness without the
    exact Rubber Duck `gpt-5.6-luna` high-reasoning `all-validation` profile
  Do not create or modify artifacts outside the named planning layer
  Do not treat a response-only capability map as a saved artifact
  Use file operations for approved writes and verify the configured map path
  Report failed or unavailable writes as blockers
  Escalate ambiguity, conflict, or material change instead of guessing
  In automatic mode, do not ask for capability approval or wait for a user
    response after verified bootstrap; missing coverage or contradictory scope
    remains a blocker
}
```

## Commands

```sudolang
Commands {
  /create-capability-map [request]
  - derive the map, request approval, and persist it after approval without creating phase children

  /create-capability-map draft [request]
  - derive and display the map without writing

  /create-capability-map write [request]
  - persist the previously approved capability map and verify its path
}
```
