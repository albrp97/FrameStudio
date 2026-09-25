---
name: Create Epics
description: Turn the approved capability map into outcome-based epics that can drive phases, tickets, and AI implementation planning.
---

You have to create the epics for `${PROJECT_OR_REPO}` after the objective, problem/users/success, scope, and capability map layers are complete.

An epic is a large, outcome-based workstream that groups related capabilities into a deliverable slice of value. It is not a ticket, not a phase, and not a vague theme.

## Why epics exist

Use epics to:
- group related capabilities into meaningful delivery units
- preserve user value and operational intent during decomposition
- make dependencies visible before ticket creation
- give AI a stable planning unit for sequencing, validation, and implementation prompts
- avoid jumping from broad capabilities directly into scattered tickets

## Outcome

Leave the repository with a durable epic breakdown that:
- covers the approved capabilities for the current horizon
- groups work by outcome, not by implementation detail
- identifies dependencies, risks, and validation needs
- is structured so phases and tickets can be derived cleanly

Write the result to `docs/planning/epics.md` unless the repository already has an established equivalent planning file.

## Where this layer belongs

This workflow comes after:
- objective discovery
- problem / users / success discovery
- scope definition
- capability map creation

This workflow comes before:
- phases
- tickets

## Required source order

Use sources in this order of trust:

1. `vision.md`
2. `docs/specs/project-scope.md`
3. `docs/specs/capability-map.md`
4. specs, roadmap docs, milestone plans, acceptance criteria
5. tests, demo flows, support runbooks, integration contracts
6. current code structure and system boundaries
7. direct admin clarification

If sources conflict, prefer the scope-approved capability source and record the mismatch.

## Workflow

### 1. Gather epic inputs

Inspect:
- `vision.md`
- `docs/specs/project-scope.md`
- `docs/specs/capability-map.md`
- roadmap docs or milestone plans
- relevant specs, contracts, and functional tests

Extract:
- clusters of capabilities that produce a meaningful user or operational outcome together
- dependencies between those clusters
- validation or rollout concerns that make a cluster a distinct workstream

### 2. Group capabilities into outcome-based workstreams

Create epics by grouping capabilities that belong together because they:
- serve the same journey or operational flow
- unlock the same user value
- share a meaningful dependency boundary
- should be reviewed or validated together

Do not create epics around technical layers such as:
- backend
- frontend
- database
- API

unless the project itself is explicitly organized around that kind of platform outcome.

### 3. Write each epic at the right level

Each epic should answer:
- what outcome it delivers
- who it serves
- which capabilities it contains
- what must be true for the epic to count as done

An epic should be bigger than a ticket but smaller than the whole phase plan.

### 4. Capture the information each epic needs

For every epic record:
- **Epic ID**
- **Title**
- **Outcome**
- **Primary user / stakeholder**
- **Capabilities included**
- **In-scope boundary**
- **Out-of-scope boundary**
- **Dependencies**
- **Risks / assumptions**
- **Validation approach**
- **Suggested first ticket areas**

### 5. Define epic metadata

The epic document must include:

| Field | Meaning |
|---|---|
| Status | draft, confirmed, or needs-review |
| Scope horizon | inherited from scope |
| Last reviewed | date epics were updated |
| Derived from | files/tests/contracts/issues used |
| Coverage | whether all in-scope capabilities are mapped |
| Confidence | high, medium, or low |
| Open questions | unresolved grouping or dependency questions |

### 6. Write the durable epic file

Create or update `docs/planning/epics.md` with this structure:

```markdown
# Epics: [Project Name]

## Metadata
| Field | Value |
|---|---|
| Status | ... |
| Scope horizon | ... |
| Last reviewed | ... |
| Derived from | ... |
| Coverage | complete / partial |
| Confidence | ... |
| Open questions | ... |

## Epic Index
| Epic ID | Title | Outcome | Primary User | Dependencies | Priority |
|---|---|---|---|---|---|
| EPIC-001 | ... | ... | ... | ... | ... |

## Epic Details

### EPIC-001: [Title]
**Outcome:** ...
**Primary user / stakeholder:** ...
**Why this epic exists:** ...

**Capabilities included**
- CAP-...

**In scope**
- ...

**Out of scope**
- ...

**Dependencies**
- ...

**Risks / assumptions**
- ...

**Validation**
- Functional checks, integration checks, acceptance evidence

**Suggested first ticket areas**
- ...

## Coverage Check
- Which in-scope capabilities are mapped to epics
- Any capability not yet assigned

## Open Questions
- ...
```

### 7. Explain how AI should use the epics

The epic document should be used by AI to:
- choose the right workstream before generating tickets
- avoid mixing unrelated capabilities in one implementation pass
- preserve user outcome during ticket breakdown
- define validation expectations before coding begins
- identify dependencies before phase planning or PR execution

AI should not treat epics as implementation tasks. Epics are planning and coordination units.

### 8. Ask admin questions only when needed

Only escalate when the repo cannot answer:
- Which capability clusters should stay together as one workstream?
- Which epic should deliver user value first?
- Which risks or dependencies are strong enough to split an epic?
- Is there any epic that must exist for business or organizational reasons even if the codebase does not reveal it clearly?

### 9. Repair ambiguity before moving on

- If an epic is too broad, split it by outcome boundary.
- If an epic is too small, merge it back into the parent workstream.
- If an epic sounds like a ticket, raise it a level.
- If a capability is assigned to multiple epics without clear reason, fix the boundary.

## Rules

1. Epics are outcome-based workstreams, not technology buckets.
2. Every in-scope capability should map to an epic.
3. Each epic needs a clear done boundary and validation approach.
4. Keep the epic count small enough to reason about.
5. If the epics cannot be cleanly sequenced into phases, refine them first.

## Deliverables

Produce:
1. `docs/planning/epics.md`
2. a coverage check against the capability map
3. only the unresolved admin questions that truly block phase planning
