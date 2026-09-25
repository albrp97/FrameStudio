---
name: Define Project Scope
description: Turn the objective and problem definition into a clear in-scope/out-of-scope boundary for the current horizon and record it in a durable project scope document.
---

You have to define the scope for `${PROJECT_OR_REPO}` after objective discovery and problem/users/success discovery are complete.

The goal is to create a hard boundary for the current horizon before capability breakdown, epics, phases, or implementation planning begin.

## Outcome

Leave the repository with a durable scope definition that makes these things explicit:
- what is in scope now
- what is out of scope now
- what is deferred until later
- what assumptions, dependencies, and constraints shape the boundary
- what is still uncertain and may require admin confirmation

Write the result into:
- `vision.md` for the short summary
- `docs/specs/project-scope.md` for the full scope document

If the repository already has an established equivalent, update that instead of creating a parallel file.

## Where this layer belongs

This workflow comes after:
- objective discovery
- problem / users / success discovery

This workflow comes before:
- capability map
- epics
- phases
- tickets

## Required source order

Use sources in this order of trust:

1. `vision.md`, specs, roadmap docs, ADRs
2. problem/users/success output and backlog docs
3. issues, milestones, release plans, acceptance criteria
4. integration constraints, compliance constraints, deployment boundaries
5. codebase reality: current modules, interfaces, test coverage, existing features
6. direct admin or stakeholder clarification

If sources disagree, choose the most authoritative current source and record the disagreement.

## Workflow

### 1. Gather boundary evidence

Inspect:
- `vision.md`
- `docs/specs/`
- roadmap docs or planning docs
- issues, milestones, and release notes
- tests or demo scripts that already imply required behaviors
- integration, infrastructure, or compliance constraints

Extract:
- what must be present for the current horizon to count as delivered
- what users may ask for but should not be included yet
- what depends on external teams, systems, approvals, or data
- what technical constraints limit scope right now

### 2. Define the scope horizon

Identify the current boundary as one of:
- MVP
- current phase
- current release
- pilot
- production baseline

Do not define scope in the abstract. Tie it to a concrete delivery horizon.

### 3. Define in-scope, out-of-scope, and deferred work

Create three lists:
- **In scope now**: must be delivered in the current horizon
- **Out of scope now**: explicitly excluded
- **Deferred / later**: useful, recognized work that is intentionally postponed

Each item should be concrete and testable, not broad aspirations.

### 4. Capture scope-shaping factors

Record:
- assumptions
- dependencies
- constraints
- risks that could force scope change

This is the part that explains **why** the boundary exists, not just what the boundary is.

### 5. Define the metadata

The scope document must include:

| Field | Meaning |
|---|---|
| Status | draft, confirmed, or needs-review |
| Scope horizon | MVP, phase, release, pilot, etc. |
| Last reviewed | date scope was updated |
| Derived from | files/issues/meetings/tests used |
| Depends on | external systems, teams, approvals, or data |
| Constraints | legal, technical, cost, staffing, or timing limits |
| Confidence | high, medium, or low |
| Open questions | unresolved scope uncertainties |

### 6. Write the durable scope file

Create or update `docs/specs/project-scope.md` with this structure:

```markdown
# Project Scope: [Project Name]

## Metadata
| Field | Value |
|---|---|
| Status | ... |
| Scope horizon | ... |
| Last reviewed | ... |
| Derived from | ... |
| Depends on | ... |
| Constraints | ... |
| Confidence | ... |
| Open questions | ... |

## Scope Summary
[1 short paragraph describing the boundary]

## In Scope Now
1. ...

## Out of Scope Now
1. ...

## Deferred / Later
1. ...

## Assumptions
- ...

## Dependencies
- ...

## Constraints
- ...

## Risks to Scope
- ...

## Evidence
- `vision.md`: ...
- `docs/...`: ...
- `issues/...`: ...
```

Also add or update a short summary in `vision.md`:

```markdown
## Scope
### In Scope Now
- ...

### Out of Scope Now
- ...
```

### 7. Ask admin questions only when needed

Only escalate when the repo cannot answer:
- What is the current delivery horizon: MVP, pilot, release, or something else?
- Which desirable capability is intentionally excluded even though users may ask for it?
- What external dependency or business constraint is the strongest scope limiter?
- If there is a tradeoff, should the current horizon optimize for breadth or for a smaller but more complete slice?

### 8. Repair ambiguity before moving on

- If scope cannot be recognized from evidence, do not start capability decomposition.
- If in-scope and out-of-scope items overlap, rewrite them until the boundary is crisp.
- If the horizon is unclear, mark the document `needs-review` instead of guessing.

## Rules

1. Scope is a boundary, not a feature wishlist.
2. Out-of-scope items are mandatory.
3. Deferred work must be separated from out-of-scope work.
4. Prefer fewer, clearer in-scope commitments over broad vague promises.
5. If a scope item cannot be verified later, rewrite it.

## Deliverables

Produce:
1. `docs/specs/project-scope.md`
2. a short scope summary in `vision.md`
3. only the unresolved admin questions that truly block capability mapping
