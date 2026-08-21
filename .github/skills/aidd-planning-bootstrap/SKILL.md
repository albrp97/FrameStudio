---
name: aidd-planning-bootstrap
description: Initialize or reconcile a repository planning system from objective, scope, maps, and delivery configuration. Use when planning artifacts are absent, stale, or inconsistent.
---

# aidd-planning-bootstrap

Establish the minimum trustworthy planning context before any downstream artifact is generated.

Apply [../planning-artifact-lifecycle.md](../planning-artifact-lifecycle.md)
when reconciling phase, feature, and ticket directories and indexes.

## Contract

```sudolang
PlanningSkillContract {
  inputs[]
  outputs[]
  filesRead[]
  filesWritten[]
  sideEffects[]
  owner
  approvalConditions[]
  stopConditions[]
  requiredEvidence[]
  failureAndBlockerBehavior
  mayImplement = false
  mayCommit = false
  mayPush = false
  mayMerge = false
}
```

## Inputs

- Repository root and the relevant approved planning artifact IDs.
- `.github/aidd-config.yml` when present; its artifact paths, vocabulary, statuses, depth, and approval rules override defaults.
- Existing ancestor/child records, repository map, requirements, decisions, and evidence available at configured paths.
- Configured phase, feature, and ticket indexes plus both `open` and `closed`
  directories for each layer.
- User request and any explicitly supplied constraints; unknowns remain unresolved.

## Outputs

- Markdown/SudoLang planning result or an explicitly authorized artifact update.
- Stable IDs using configured prefixes (`OBJ`, `SCOPE`, `CAP`, `PHASE`, `FEAT`, `TICKET`), explicit status, parent/child links, and coverage/evidence links.
- A reconciled report of each record's status, current path, index entry, and
  any duplicate, orphaned, or status/path mismatch.
- A concise readiness, approval, warning, or blocker report; no implied downstream work.

## Side effects and ownership

- This skill owns only the planning layer named in its title and its review/report output.
- It may write only configured planning artifacts when the caller authorizes mutation; otherwise it is read-only.
- It never owns implementation, branches, commits, pushes, merges, provider operations, or delivery readiness.
- Every write records owner, reason, source/evidence links, timestamp or revision, and affected IDs; preserve history rather than overwrite it.

## Boundaries

- Canonical hierarchy is **objective -> scope -> capability -> phase -> feature -> ticket**.
- Use adaptive depth: lightweight for a small fix or documentation change, standard for a meaningful change, full for a broad initiative; never invent layers merely for ceremony.
- A child requires one existing, unblocked, approved parent. No silent downstream generation, fan-out, or scope expansion.
- Preserve stable IDs on rename; maintain explicit statuses (`draft`, `confirmed`, `needs-review`, `blocked`, `complete`) and valid transitions.
- Keep requirements observable and implementation-agnostic. Reject cross-parent or oversized work when it cannot be independently verified.

## Metadata and traceability

Every artifact or report must include: ID, title, status, parent ID(s), objective/scope ancestry, capability/phase/feature links as applicable, owner, source paths, dependencies, risks, non-goals, affected surfaces, approval state, evidence/coverage links, and last-updated revision or timestamp. A ticket is traceable only when it links back to its objective and forward to requirements, protected behaviors, gates, and an evidence path.

## Failure and blocker behavior

Missing parent, approval, evidence, command, ownership, or required capability is a blocker or coverage gap—not a pass. Stop before child generation or readiness claims, name the exact missing input and affected IDs, and propose the smallest next action. Material changes route to `aidd-change-control`; routine corrections must not masquerade as a replan.

## Process

```sudolang
bootstrap(request) => PlanningContext {
  1. load objective, scope, maps, configured artifact paths, and existing statuses
  2. inspect both open and closed directories for phases, features, and tickets
  3. classify planning depth as lightweight | standard | full using request and repository evidence
  4. validate canonical hierarchy, stable ID prefixes, status classification, and index paths
  5. report gaps, conflicts, stale paths, duplicate IDs, and approval needed; write only explicitly authorized bootstrap artifacts
  6. stop before generating children when a parent is missing, blocked, or unapproved
}
```

## Constraints

```sudolang
Constraints {
  Read configured artifacts and applicable ancestors before proposing changes
  Reconcile open/closed directories and indexes before downstream planning
  Do not leave a record duplicated in both directories or indexed at a stale path
  Do not claim readiness without terminal evidence for every required gate
  Do not create or modify artifacts outside the named planning layer
  Escalate ambiguity, conflict, or material change instead of guessing
}
```

## Commands

```sudolang
Commands {
  /planning-bootstrap [request]
  - initialize or reconcile planning context without silently creating downstream artifacts
}
```
