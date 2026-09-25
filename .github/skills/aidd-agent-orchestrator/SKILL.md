---
name: aidd-agent-orchestrator
description: Route and coordinate software work through delivery phases, features, tickets, evidence, quality gates, and provider-specific operations. Use when a request needs lifecycle classification or multi-stage delivery coordination.
---

import ../lifecycle-interface.md

# Aiden Agent Orchestrator

```sudolang
Lifecycle {
  profile = orchestration
}
```

Coordinate specialized skills without losing delivery context or allowing a
sub-agent to claim readiness without evidence.

Apply [../planning-artifact-lifecycle.md](../planning-artifact-lifecycle.md)
when resolving planning records and routing status transitions. A physical
move between `open` and `closed` is part of the lifecycle transition, not a
separate cleanup step.
Apply [../development-mode.md](../development-mode.md) for mode resolution,
automatic continuation, validation ownership, and blocker behavior.

## Delivery state

Load [state and context](./references/state-and-context.md) when constructing or
transitioning the complete delivery context.

## Skill routing

```sudolang
Agents {
  please: general constraints, scope, approval, and readiness reporting
  productmanager: discovery, outcomes, stakeholders, and delivery contract
  requirements: observable requirements and verification traceability
  planningBootstrap: repository mapping, planning depth, and artifact discovery
  repositoryMap: durable repository surface mapping
  capabilityMap: scope-to-capability coverage
  phases: ordered delivery phases and exit conditions
  features: outcome features inside phases
  tickets: focused ticket decomposition and backlog
  planningReview: planning-layer completeness and coverage review
  grooming: routine backlog maintenance and prioritization
  phaseFeedback: planned-versus-delivered phase learning
  changeControl: local correction versus material replan decisions
  preimplementation: active-ticket readiness checklist
  ticketCreator: phase, feature, ticket planning and execution ownership
  tdd: baseline, tests, implementation, and regression evidence
  evidence: append-only delivery evidence
  review: quality, security, scope, evidence review, and approved remediation orchestration
  staticAnalysis: deterministic formatter, lint, type, complexity, duplication,
    dependency, security, SonarQube, and churn analysis
  pr: provider-neutral pull-request lifecycle and provider adapter
  parallel: safe independent delegation
  pipeline: explicit ticket-list execution
  automaticDevelopment: post-bootstrap autonomous planning, execution,
    verification, review, delivery, and phase iteration
  commit: staged-scope and readiness checks
  push: remote branch publication and push verification
}

route(request, context) {
  explicitCommitDirective => commit
  explicitPushDirective => push
  explicitCommitAndPushDirective => commit |> push
  repositoryOnboarding => projectBootstrap
  bootstrapComplete and context.developmentMode == guided =>
    planningBootstrap |> repositoryMap
  bootstrapComplete and context.developmentMode == automatic =>
    automaticDevelopment
  discovery => productmanager
  scopeDefinition => productmanager
  capabilityPlanning => capabilityMap
  phasePlanning => phases
  featurePlanning => features
  ticketPlanning => requirements |> tickets
  backlogMaintenance => grooming
  planningReview => planningReview
  phaseCloseout => phaseFeedback
  materialChange => changeControl
  implementationReadiness => preimplementation
  implementation => ticketCreator |> tdd
  bugFix => aidd-fix
  verification => user-testing | run-test | tdd
  staticAnalysis => staticAnalysis
  review => review (review invokes staticAnalysis before readiness)
  deliveryOperations => commit | push | pr | clean-pr-branch
}
```

## Control flow references

Load [control-flow](./references/control-flow.md) when running automatic
iteration, resolving next actions or state transitions, or preparing delegated
work. Do not load it for a simple routing classification.

## Constraints

```sudolang
Constraints {
  Never declare readiness from partial or inferred evidence
  Never route a new implementation ticket when an active ticket already owns the request
  Never generate child planning artifacts before the required parent review
  Never choose a later-phase ticket over a ready ticket in the active phase without explicit selection
  Never turn routine backlog grooming into a formal replan
  Never allow a delegated agent to modify shared plan or evidence records without ownership
  Never treat a record's folder as optional metadata; status and folder must agree
  Never close a parent while required children remain open or incomplete
  Preserve stable IDs, record content, index entries, and path history during moves
  Never conceal baseline failures or unrelated findings
  Never recommend push before a local commit exists
  Never recommend a PR before the source branch is published
  A confirmed explicit commit or push directive overrides workflow readiness,
    approval, validation, lifecycle, and internal branch-policy gates through
    development-mode.md; record bypassed gates and do not advance readiness
  Commit, push, and PR operations must be owned by the integration owner for
  delegated work
  Never declare a guided ticket ready, complete, or closed without required
  automated functionality evidence for every acceptance outcome and required
  user-validation evidence or an approved not-applicable decision
  Never declare an automatic ticket ready, complete, or closed without
  required automated functionality and `automaticValidation` evidence for
  every acceptance outcome, each carrying the exact automatic validation
  profile
  Never accept an automatic validation result produced by another model,
  validator, or an unavailable or mismatched Rubber Duck profile
  Never ask or wait for a user after the verified automatic bootstrap handoff
  Never use automatic mode to bypass a security, branch, provider, credential,
  remote-check, merge, or unavailable-tool blocker
  Never finish a routed response without one context-aware next-step and skill
  recommendation
  Never load every domain skill by default
  If context or gate policy is missing, report the blocker explicitly
}
```
