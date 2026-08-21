---
name: aidd-planning-layer-review
description: Review objective, scope, capability, phase, feature, and ticket planning layers for consistency, coverage, and readiness. Use before execution or after planning changes.
---

# aidd-planning-layer-review

Find broken links, missing gates, unsupported claims, and hierarchy drift before work starts.

Apply [../planning-artifact-lifecycle.md](../planning-artifact-lifecycle.md)
to inspect both lifecycle directories and verify that each record's status,
current path, and index entry agree.

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
- Every phase, feature, and ticket record in both `open` and `closed`, plus
  the phase/feature/backlog indexes.
- User request and any explicitly supplied constraints; unknowns remain unresolved.

## Outputs

- Markdown/SudoLang planning result or an explicitly authorized artifact update.
- Stable IDs using configured prefixes (`OBJ`, `SCOPE`, `CAP`, `PHASE`, `FEAT`, `TICKET`), explicit status, parent/child links, and coverage/evidence links.
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
reviewPlanningLayer(request) => PlanningReview {
  1. load the requested layer and all ancestors/children needed for traceability
  2. inspect both open and closed directories and resolve records by stable ID
  3. check one-parent rules, stable IDs, statuses, coverage/evidence links, scope boundaries, approval state, and status/path classification
  4. check for duplicate IDs, stale index paths, orphaned records, and closed records referenced as active work
  5. report passes, warnings, blockers, orphaned artifacts, and recommended smallest corrections
  6. keep readiness false for missing evidence or non-terminal gates
  7. do not mutate artifacts, move files, or generate missing children during review
}
```

## Constraints

```sudolang
Constraints {
  Read configured artifacts and applicable ancestors before proposing changes
  Report every status/path mismatch; do not repair it implicitly
  Treat blocked records as open and closed records as ineligible for active work
  Do not claim readiness without terminal evidence for every required gate
  Do not create or modify artifacts outside the named planning layer
  Escalate ambiguity, conflict, or material change instead of guessing
}
```

## Commands

```sudolang
Commands {
  /review-planning-layer [layer-or-id]
  - return a read-only planning review and readiness decision
}
```
