---
name: aidd-preimplementation-checklist
description: Verify that an approved ticket is safe and ready to implement, including ancestry, scope, baseline, evidence, commands, gates, and ownership.
---

# aidd-preimplementation-checklist

Provide a repeatable stop/go decision before implementation begins.

Apply [../planning-artifact-lifecycle.md](../planning-artifact-lifecycle.md)
to verify that the selected ticket and its ancestors are in the correct
open/closed directories before implementation.

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
- The selected ticket and its phase/feature ancestors in both lifecycle
  directories, including their current paths and index entries.
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
runPreimplementationChecklist(ticket) => ChecklistResult {
  1. verify objective -> scope -> capability -> phase -> feature -> ticket links, stable IDs, statuses, approvals, and current paths
  2. require the selected ticket and its active phase/feature ancestors to be in open; reject a closed ticket or closed ancestor as active work
  3. verify ticket scope/non-goals, dependencies, risks, affected surfaces, protected behaviors, commands, gates, evidence path, and the exact user-validation plan required before closure
  4. verify required baseline evidence or baseline plan exists according to the configured sequencing; missing evidence keeps ready=false
  5. confirm ownership and no overlapping active ticket; surface unresolved decisions
  6. return ready=true only when every required check passes; otherwise list blockers and do not start implementation
}
```

## Constraints

```sudolang
Constraints {
  Read configured artifacts and applicable ancestors before proposing changes
  Read both open and closed directories and reject stale index paths
  Never move records during this read-only checklist
  Treat a closed ticket or ancestor as a blocker until explicitly reopened and moved to open
  Do not claim readiness without terminal evidence for every required gate
  Do not create or modify artifacts outside the named planning layer
  Escalate ambiguity, conflict, or material change instead of guessing
}
```

## Commands

```sudolang
Commands {
  /run-preimplementation-checklist [ticket-id]
  - return an auditable ready/not-ready decision without implementing
}
```
