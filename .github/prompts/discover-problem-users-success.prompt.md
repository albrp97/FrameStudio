---
name: Discover Problem Users Success
description: Define the problem statement, target users, success criteria, and outcome signals from repository evidence and minimal admin clarification.
---

You have to define the problem, users, success criteria, and outcome signals for `${PROJECT_OR_REPO}` before scope, epics, phases, or tickets are created.

Use the repository as the default evidence source. Ask the admin user only for the parts that cannot be recovered with reasonable confidence from the repo, docs, backlog, or delivery context.

## Outcome

Leave the repository with a durable, evidence-backed definition of:
- the problem that matters
- who has the problem
- what outcome matters most
- how success will be recognized
- what is still uncertain

Write the result into `vision.md` unless the repository already uses a stronger source-of-truth file for project definition.

## Where this layer belongs

This workflow comes after objective discovery and before:
- scope definition
- capability or feature breakdown
- epics
- phases
- tickets

## Required source order

Use sources in this order of trust:

1. `vision.md`, specs, product docs, ADRs, roadmap docs
2. `README.md`, docs, backlog docs, issue templates, PR templates
3. issues, milestones, project boards, acceptance criteria, release notes
4. analytics/event names, monitoring dashboards, support docs, test cases, demo scripts
5. code structure, route names, domain models, integrations, deployment context
6. direct admin or stakeholder input

If these conflict, prefer the most authoritative current source and record the conflict.

## Workflow

### 1. Gather evidence

Inspect:
- `vision.md`
- `README.md`
- docs, specs, and roadmap files
- issues, milestones, labels, and backlog notes
- test folders, e2e scripts, and demo scripts
- product analytics or observability config if present
- top-level code and integration structure

Extract:
- the pain or inefficiency the project is meant to reduce
- the person, role, or system affected most
- the key user journey or operational flow
- current success signals already implied by docs or tests
- business, operational, or technical constraints on success

### 2. Define the problem statement

Write a short problem statement that covers:
- the current situation
- what is failing, missing, slow, manual, risky, or expensive
- who experiences that pain
- why solving it matters now

The problem statement must describe a real pain, not just "we need an app/platform/system."

### 3. Define the users and context

Identify:
- **Primary user**: the first user whose success matters most
- **Secondary users**: supporting roles affected by the project
- **Operational context**: where, when, and under what constraints the project is used

Prefer user roles over vague audience labels.

### 4. Define success and outcome signals

Capture:
- **Desired outcome**: what changes when the project succeeds
- **Success criteria**: observable or measurable indicators
- **Outcome signals**: proxy metrics, workflow improvements, error reductions, throughput gains, time savings, adoption signals, or quality thresholds

Prefer measurable signals where possible. If the repo only supports qualitative signals, say so explicitly.

### 5. Define the metadata

This layer must capture:

| Field | Meaning |
|---|---|
| Status | draft, confirmed, or needs-review |
| Last reviewed | date this layer was updated |
| Derived from | concrete files/issues/tests/interviews used |
| Primary user | most important user or consuming system |
| Secondary users | additional affected roles |
| Success horizon | MVP, current release, 90 days, annual, etc. |
| Outcome type | business, operational, technical, or mixed |
| Confidence | high, medium, or low |
| Open questions | unresolved uncertainties |

### 6. Write the layer into `vision.md`

Create or update these sections:

```markdown
## Problem Statement
[Short paragraph describing the concrete pain and why it matters]

## Users and Context
- **Primary user**: ...
- **Secondary users**: ...
- **Usage context**: ...
- **Operational constraints**: ...

## Desired Outcome
- [What gets better if this project succeeds]

## Success Criteria
- [Observable or measurable indicator]

## Outcome Signals
- [Metric, threshold, or operational signal]

## Metadata
| Field | Value |
|---|---|
| Status | ... |
| Last reviewed | ... |
| Derived from | ... |
| Primary user | ... |
| Secondary users | ... |
| Success horizon | ... |
| Outcome type | ... |
| Confidence | ... |
| Open questions | ... |
```

### 7. Ask admin questions only when needed

Only escalate to the admin user when these cannot be inferred well enough:
- Which user matters most if several are possible?
- What metric or operational signal would count as success?
- What deadline, release, or milestone defines the first meaningful horizon?
- What problem is intentionally **not** being solved yet?
- Which tradeoff wins when user value conflicts with engineering convenience?

### 8. Repair ambiguity before moving on

- If the user/problem pairing is fuzzy, do not create epics yet.
- If success cannot be recognized, tighten the success criteria before scope work.
- If the repo implies several outcomes, rank them and record uncertainty.

## Rules

1. Prefer one clear primary user over a vague multi-audience statement.
2. Distinguish the **problem** from the **solution idea**.
3. Distinguish **success criteria** from implementation tasks.
4. Record proxy metrics if direct business metrics are unavailable.
5. Mark uncertainty explicitly instead of pretending the repo answered it.

## Deliverables

Produce:
1. updated `vision.md` sections for problem, users, and success
2. the evidence trail used to derive them
3. only the unresolved admin questions that truly need human input
