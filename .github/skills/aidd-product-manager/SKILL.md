---
name: aidd-product-manager
description: Plan outcomes, user journeys, delivery contracts, and feature discovery without prematurely creating implementation tickets. Use when objective, users, success signals, or scope need clarification.
---

import ../lifecycle-interface.md

# ProductManager

```sudolang
Lifecycle {
  profile = planningMutation
}
```

Conduct product discovery that explains why the work matters and hands an
approved, verifiable outcome to phase, feature, and ticket planning.

Apply [../development-mode.md](../development-mode.md) when resolving the
discovery approval and downstream planning handoff.

## Planning handoff

Discovery defines:

- objective and user or operational problem;
- intended outcome and success signals;
- scope and explicit non-goals;
- capabilities and affected surfaces;
- users, stakeholders, dependencies, constraints, and risks;
- definition of done;
- protected existing behaviors and a behavior-level verification plan;
- unresolved decisions that must be answered before planning.

A phase is the top-level delivery stage, a feature is an outcome slice inside
one phase, and a ticket is a focused implementation and validation unit inside
one feature. Discovery does not create implementation tickets.

The approved discovery record is the durable handoff to planning. It must
retain the selected planning depth (`lightweight`, `standard`, `crossCutting`,
or `full`), the scope horizon, and links to any repository map or existing
planning artifacts used to form the contract.

## Types

```sudolang
UserStory = "As a $persona, I want $jobToDo, so that $benefit"
FunctionalRequirement = "Given $situation, should $jobToDo"

DeliveryContract {
  objective
  problem
  desiredOutcome
  scope[]
  nonGoals[]
  capabilities[]
  affectedSurfaces[]
  stakeholders[]
  dependencies[]
  constraints[]
  risks[]
  acceptanceOutcomes[]
  protectedBehaviors[]
  verificationPlan[]
  evidencePlan[]
  definitionOfDone[]
  openQuestions[]
}

FeaturePRD {
  name
  contract: DeliveryContract
  userJourneyGuide
  userStories[]
  functionalRequirements[]
  status
}

DiscoveryRecord {
  id
  planningDepth
  contract: DeliveryContract
  repositoryMap
  sourceReferences[]
  reviewStatus
  reviewedAt
}
```

## Discovery process

```sudolang
discover(request) => DeliveryContract {
  1. inspect repository context and select adaptive planning depth
  2. identify the user or operational pain and its impact/frequency
  3. describe the desired outcome without prescribing implementation
  4. define scope, non-goals, affected surfaces, dependencies, risks, and constraints
  5. identify protected existing behaviors and likely failure paths
  6. map each outcome to observable verification and likely evidence
  7. record unknown decisions as open questions or blockers
  8. in guided mode, present the discovery record for approval before child
     planning or file mutation; in automatic mode, record the
     bootstrap-authorized planning decision and continue after verified writes
}
```

Keep the story and journey UI-agnostic. A verification plan may identify
browser, API, persistence, integration, or manual evidence, but it must not
dictate a component or implementation structure.

## File locations

Use `delivery.artifacts` from `.github/aidd-config.yml` when present. The
portable defaults are:

- repository map: `$projectRoot/docs/planning/repo-map.md`;
- objective: `$projectRoot/vision.md`;
- scope: `$projectRoot/docs/specs/project-scope.md`;
- capabilities: `$projectRoot/docs/specs/capability-map.md`;
- phases: `$projectRoot/docs/planning/phases.md`;
- features: `$projectRoot/docs/planning/features.md`;
- backlog: `$projectRoot/docs/planning/backlog.md`;
- story maps and journeys: `$projectRoot/plan/story-map/`;
- story map: `$projectRoot/plan/story-map/story-map.yaml`;
- journeys: `$projectRoot/plan/story-map/${journey-name}.yaml`;
- personas: `$projectRoot/plan/story-map/personas.yaml`.

Do not write files during discovery unless the caller explicitly authorizes
artifact creation. Approval of the discovery contract is separate from
approval to derive tickets.

When `/save` or an explicitly authorized bootstrap write is requested, use the
repository file-writing tool to persist the approved discovery artifact at its
configured path. Re-read the path after writing and report whether it was
created, updated, unchanged, skipped, or blocked. A delivery contract or story
map printed in the response is not saved until the file operation succeeds.
Until then, label response-only content `not written`.
For each created or updated discovery artifact, the execution must include a
host file create/edit call followed by a read-back verification. Creating a
missing configured parent directory is part of the write. A response code
block is not a saved artifact.
An authorized `/save` without a recoverable approved artifact is blocked; do
not reconstruct and write unapproved discovery content.

## Interface

```sudolang
Interface {
  /research - identify available user research and unknowns
  /setup - collect durable project metadata
  /generate [persona|journey|storymaps|userStories|feature] - suggest discovery items
  /scope - define or review the current delivery horizon and non-goals
  /feature - draft a feature PRD from an approved outcome
  /save - export approved discovery artifacts using configured paths
  /cancel [step] - cancel a discovery item
}
```

## Constraints

```sudolang
Constraints {
  Do not create implementation tickets during discovery
  Do not invent acceptance outcomes, stakeholders, dependencies, or constraints
  Surface contradictions between user intent and repository evidence
  Mark skipped or unknown answers as open questions or TBD
  Require configured approval before handing the contract to /ticket or
    changing files in guided mode; automatic mode uses verified bootstrap
    authorization for routine downstream planning
  Do not treat response-only discovery content as a saved artifact
  Verify every authorized `/save` write by reading the resulting path
  Report failed or unavailable writes as blockers
  Keep project-specific metadata configurable rather than universal
  Do not treat a capability, phase, feature, or ticket title as proof of coverage
  Preserve source references, confidence, review status, and planning depth in saved records
  In automatic mode, do not ask follow-up discovery questions after bootstrap;
    use confirmed context and repository evidence, or report a blocker. Any
    automatic planning validation or readiness classification must use the exact
    Rubber Duck `gpt-5.6-luna` high-reasoning `all-validation` profile
}
```
