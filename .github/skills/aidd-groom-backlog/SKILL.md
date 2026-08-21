---
name: aidd-groom-backlog
description: Groom an existing planning backlog by clarifying, ordering, deduplicating, and blocking stale items without silently replanning material scope.
---

# aidd-groom-backlog

Keep planned work actionable while distinguishing routine maintenance from change control.

Apply [../planning-artifact-lifecycle.md](../planning-artifact-lifecycle.md)
for status classification, current record paths, and authorized moves between
`open` and `closed`.

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
- The phase, feature, and ticket indexes plus records in both `open` and
  `closed` directories.
- User request and any explicitly supplied constraints; unknowns remain unresolved.

## Outputs

- Markdown/SudoLang planning result or an explicitly authorized artifact update.
- Stable IDs using configured prefixes (`OBJ`, `SCOPE`, `CAP`, `PHASE`, `FEAT`, `TICKET`), explicit status, parent/child links, and coverage/evidence links.
- A concise readiness, approval, warning, or blocker report; no implied downstream work.
- Synchronized index/list paths after any authorized status transition.

## Side effects and ownership

- This skill owns only the planning layer named in its title and its review/report output.
- It may write only configured planning artifacts when the caller authorizes mutation; otherwise it is read-only.
- It never owns implementation, branches, commits, pushes, merges, provider operations, or delivery readiness.
- When a routine status update crosses the configured terminal boundary, it
  moves the same record between `open` and `closed`, preserves its ID/history,
  and updates all indexes; it does not archive or duplicate records.
- Every write records owner, reason, source/evidence links, timestamp or revision, and affected IDs; preserve history rather than overwrite it.

## Boundaries

- Canonical hierarchy is **objective -> scope -> capability -> phase -> feature -> ticket**.
- Use adaptive depth: lightweight for a small fix or documentation change, standard for a meaningful change, full for a broad initiative; never invent layers merely for ceremony.
- A child requires one existing, unblocked, approved parent. No silent downstream generation, fan-out, or scope expansion.
- Preserve stable IDs on rename; maintain explicit statuses (`draft`, `confirmed`, `needs-review`, `blocked`, `complete`) and valid transitions.
- Treat blocked records as open. A record in `closed` is not an active backlog
  candidate until explicitly reopened and moved to `open`.
- Keep requirements observable and implementation-agnostic. Reject cross-parent or oversized work when it cannot be independently verified.

## Metadata and traceability

Every artifact or report must include: ID, title, status, parent ID(s), objective/scope ancestry, capability/phase/feature links as applicable, owner, source paths, dependencies, risks, non-goals, affected surfaces, approval state, evidence/coverage links, and last-updated revision or timestamp. A ticket is traceable only when it links back to its objective and forward to requirements, protected behaviors, gates, and an evidence path.

## Failure and blocker behavior

Missing parent, approval, evidence, command, ownership, or required capability is a blocker or coverage gap—not a pass. Stop before child generation or readiness claims, name the exact missing input and affected IDs, and propose the smallest next action. Material changes route to `aidd-change-control`; routine corrections must not masquerade as a replan.

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
  Read configured artifacts and applicable ancestors before proposing changes
  Inspect both open and closed directories and reject status/path mismatches
  Never duplicate, delete, or silently archive a planning record
  Keep phase, feature, and backlog indexes synchronized after a move
  Do not claim readiness without terminal evidence for every required gate
  Do not create or modify artifacts outside the named planning layer
  Escalate ambiguity, conflict, or material change instead of guessing
}
```

## Commands

```sudolang
Commands {
  /groom-backlog [scope]
  - report safe grooming updates or a change-control blocker
}
```
