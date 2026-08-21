---
name: aidd-phase-feedback
description: Capture feedback against an active phase and its outcome, entry, and exit conditions. Use after evidence, review, or stakeholder feedback.
---

# aidd-phase-feedback

Turn observed phase feedback into bounded decisions without losing history or silently changing scope.

Apply [../planning-artifact-lifecycle.md](../planning-artifact-lifecycle.md)
for phase record location, status classification, index synchronization, and
reopening/closing moves.

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
- The phase index and the selected phase record in either its `open` or
  `closed` directory, plus linked feature/ticket records in both directories.
- User request and any explicitly supplied constraints; unknowns remain unresolved.

## Outputs

- Markdown/SudoLang planning result or an explicitly authorized artifact update.
- Stable IDs using configured prefixes (`OBJ`, `SCOPE`, `CAP`, `PHASE`, `FEAT`, `TICKET`), explicit status, parent/child links, and coverage/evidence links.
- A concise readiness, approval, warning, or blocker report; no implied downstream work.
- An updated phase index/current path when an authorized phase status transition
  moves the record between `open` and `closed`.

## Side effects and ownership

- This skill owns only the planning layer named in its title and its review/report output.
- It may write only configured planning artifacts when the caller authorizes mutation; otherwise it is read-only.
- It never owns implementation, branches, commits, pushes, merges, provider operations, or delivery readiness.
- When approved evidence sets a phase to a terminal status, move the same phase
  record to `closed`; when approved feedback reopens it, move it back to `open`.
  Preserve stable IDs, content, path history, and index entries.
- Every write records owner, reason, source/evidence links, timestamp or revision, and affected IDs; preserve history rather than overwrite it.

## Boundaries

- Canonical hierarchy is **objective -> scope -> capability -> phase -> feature -> ticket**.
- Use adaptive depth: lightweight for a small fix or documentation change, standard for a meaningful change, full for a broad initiative; never invent layers merely for ceremony.
- A child requires one existing, unblocked, approved parent. No silent downstream generation, fan-out, or scope expansion.
- Preserve stable IDs on rename; maintain explicit statuses (`draft`, `confirmed`, `needs-review`, `blocked`, `complete`) and valid transitions.
- A phase may close only after required child features satisfy their outcomes
  and terminal conditions. A closed phase cannot receive new features until it
  is explicitly reopened.
- Keep requirements observable and implementation-agnostic. Reject cross-parent or oversized work when it cannot be independently verified.

## Metadata and traceability

Every artifact or report must include: ID, title, status, parent ID(s), objective/scope ancestry, capability/phase/feature links as applicable, owner, source paths, dependencies, risks, non-goals, affected surfaces, approval state, evidence/coverage links, and last-updated revision or timestamp. A ticket is traceable only when it links back to its objective and forward to requirements, protected behaviors, gates, and an evidence path.

## Failure and blocker behavior

Missing parent, approval, evidence, command, ownership, or required capability is a blocker or coverage gap—not a pass. Stop before child generation or readiness claims, name the exact missing input and affected IDs, and propose the smallest next action. Material changes route to `aidd-change-control`; routine corrections must not masquerade as a replan.

## Process

```sudolang
recordPhaseFeedback(request) => PhaseFeedback {
  1. require a phase ID and identify current status, outcome, entry/exit conditions, evidence, linked children, and current open/closed path
  2. classify feedback as observation, correction, blocker, or material change
  3. append source-linked feedback and proposed disposition; preserve prior decisions and IDs
  4. update status only when evidence and configured approval support it
  5. move the phase between open and closed when status classification changes and synchronize the phase index
  6. route material outcome/scope/capability changes to change control; do not replan silently
}
```

## Constraints

```sudolang
Constraints {
  Read configured artifacts and applicable ancestors before proposing changes
  Inspect both lifecycle directories and reject status/path mismatches
  Never close a phase with open or incomplete required child features
  Never duplicate or silently archive the phase record
  Do not claim readiness without terminal evidence for every required gate
  Do not create or modify artifacts outside the named planning layer
  Escalate ambiguity, conflict, or material change instead of guessing
}
```

## Commands

```sudolang
Commands {
  /phase-feedback [phase-id]
  - record and classify feedback for one phase
}
```
