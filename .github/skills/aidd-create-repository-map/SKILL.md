---
name: aidd-create-repository-map
description: Create or update a traceable repository map for planning. Use when repository structure, ownership, commands, or delivery surfaces need a grounded map.
---

import ../planning-skill-interface.md

# aidd-create-repository-map

Describe repository surfaces and ownership without turning discovery into implementation planning.

Apply [../development-mode.md](../development-mode.md) when deciding whether
the verified map hands off to the next planning layer.

## Contract

```sudolang
Lifecycle {
  profile = planningMutation
}

PlanningSkill {
  profile = planningMutation
  layer = repositoryMap
  parentLayers = [repositoryContext]
  childLayers = [objective, scope, capability]
  writableArtifacts = [repositoryMap]
  mode = inspect | draft | write
}
```

## Inputs

- Repository root and the relevant approved planning artifact IDs.
- The configured repository-map path
  (`delivery.artifacts.repository_map`, normally
  `docs/planning/repo-map.md`).

## Outputs

- A source-linked map proposal in `draft` or `review` mode, or a persisted
  configured repository map in `write` mode after explicit authorization.
  Returning map content without writing the configured path is not completion.

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
createRepositoryMap(request) => RepositoryMap {
  1. inspect repository directories, manifests, guidance, and configured artifact locations
  2. record paths, responsibilities, owners when evidenced, commands, integrations, and unknowns
  3. link observations to source paths and timestamps or revisions where available
  4. preserve existing map IDs and mark stale entries rather than deleting history
  5. after approval, use a repository file-writing tool to create or update the configured map path
  6. re-read the path and record a verified write result; stop if writing or verification fails
  7. do not generate capabilities, phases, features, or tickets as a side
     effect of this skill; in automatic mode, hand off to the orchestrator
     immediately after the verified map write. Resolve the exact Rubber Duck
     `gpt-5.6-luna` high-reasoning `all-validation` profile before classifying
     the write verification or map readiness.
}
```

### Artifact persistence

The repository map must be saved to the configured path when the operation is
authorized. A response containing the map is only a proposal until the file
operation and post-write verification succeed. If writing is unavailable or
fails, report the exact path as blocked and do not claim the repository was
mapped durably; label response-only content `not written`.
`write` without a recoverable approved map is blocked; do not reconstruct an
unapproved map from the request.
For a `created` or `updated` result, the execution must include a host file
create/edit call and a post-write read. Creating the configured parent
directory is part of the approved write; a response code block is not.

## Constraints

```sudolang
Constraints {
  In automatic mode, do not classify map verification or readiness without the
    exact Rubber Duck `gpt-5.6-luna` high-reasoning `all-validation` profile
  Do not create or modify artifacts outside the named planning layer
  Do not treat response-only map content as a written repository map
  Use file operations for approved writes and verify the configured map path
  Report failed or unavailable writes as blockers
  Escalate ambiguity, conflict, or material change instead of guessing
  In automatic mode, do not wait for a separate map approval after the
    verified bootstrap authorization; never ignore mapping blockers
}
```

## Commands

```sudolang
Commands {
  /create-repository-map [request]
  - produce and, after authorization, persist a source-linked repository map

  /create-repository-map draft [request]
  - produce a map proposal without writing

  /create-repository-map write [request]
  - persist the previously approved repository map and verify its path
}
```
