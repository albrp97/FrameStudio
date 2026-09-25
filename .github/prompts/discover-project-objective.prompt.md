---
name: Discover Project Objective
description: Extract the real project objective, scope, users, and success criteria from repo evidence and write them into a durable project objective document.
---

You have to determine the actual objective of `${PROJECT_OR_REPO}` and write it down in a durable form before setup or implementation work starts.

Use the project itself as the primary evidence source. Do not invent the objective from assumptions.

## Outcome

Leave the repository with a clear, evidence-backed project objective document that explains:
- what the project is for
- who it serves
- what success looks like
- what is explicitly out of scope
- how confident we are in the objective and where it came from

Write the result to `vision.md` unless the repository already has an established equivalent source-of-truth file.

## Required source order

Use sources in this order of trust:

1. existing `vision.md`, specs, ADRs, product docs, roadmap docs
2. `README.md`, docs, issue templates, PR templates, and backlog artifacts
3. tickets, issues, milestones, and project boards
4. code structure, route names, data models, config, and deployment files
5. commit history and recent PRs
6. direct stakeholder input when available

If the sources conflict, say so explicitly and choose the most authoritative current source.

## Workflow

### 1. Gather evidence

Inspect:
- `README.md`
- existing `vision.md`
- docs and specs
- issues / milestones / roadmap docs
- package manifests and lockfiles
- top-level source directories
- infrastructure / deployment files
- test folders

Extract:
- product purpose
- target user or consumer
- primary workflows or capabilities
- deployment/runtime context
- measurable outcomes already implied by the repo
- explicit constraints or non-goals

### 2. Reconstruct the actual objective

Write a short synthesis of:
- the problem being solved
- who has that problem
- what the project must deliver
- what it must not expand into yet

Do not confuse current implementation details with the objective. The objective is the reason the project exists and the outcome it is meant to produce.

### 3. Define the metadata

The objective document must include this metadata:

| Field | Meaning |
|---|---|
| Project | canonical project/repo name |
| Status | draft, confirmed, or needs-review |
| Last reviewed | date the objective was derived |
| Derived from | concrete files/issues/PRs/interviews used |
| Primary user | who benefits first |
| Owner / team | if known from the repo or docs |
| Scope horizon | MVP, current phase, or long-term |
| Confidence | high, medium, or low |
| Open questions | unresolved conflicts or missing inputs |

### 4. Write the durable objective file

Create or update `vision.md` with this structure:

```markdown
# Vision: [Project Name]

## Metadata
| Field | Value |
|---|---|
| Project | ... |
| Status | ... |
| Last reviewed | ... |
| Derived from | ... |
| Primary user | ... |
| Owner / team | ... |
| Scope horizon | ... |
| Confidence | ... |
| Open questions | ... |

## Purpose
[One paragraph: what problem this project solves, for whom, and why it matters]

## Goals
1. [primary goal]
2. [secondary goal]
3. [optional supporting goal]

## Non-Goals
- [explicitly out of scope item]

## Users and Context
- **Primary user**: ...
- **Usage context**: ...

## Capabilities in Scope
- [capability]

## Success Criteria
- [observable/measurable outcome]

## Constraints
- Stack / platform constraints
- delivery or compliance constraints
- integration constraints

## Evidence
- `README.md`: ...
- `docs/...`: ...
- `issues/...`: ...

## Open Questions
- [only if still unresolved]
```

### 5. Repair ambiguity before moving on

- If the objective is fuzzy, tighten it from evidence before creating epics or tickets.
- If the repo supports multiple possible interpretations, record the conflict.
- If critical information is missing, finish the best evidence-based draft and clearly mark the unresolved parts instead of pretending certainty.

## Rules

1. Prefer a short, constraint-heavy objective over aspirational product prose.
2. Non-goals are mandatory.
3. Evidence citations are mandatory.
4. Do not proceed into implementation planning until the objective is coherent.
5. If confidence is low, mark the document `needs-review` rather than overstating certainty.

## Deliverables

Produce:
1. the `vision.md` objective document
2. a short explanation of how the objective was derived
3. any unresolved questions that block feature/epic breakdown
