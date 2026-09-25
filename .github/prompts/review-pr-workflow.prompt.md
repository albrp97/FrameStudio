---
name: Review Pull Request Workflow
description: Review changed work against requirements, tests, docs, architecture, and merge readiness.
---

You have to review `${PR_OR_CHANGESET}` as a delivery-quality pull request, not just as a diff.

## Outcome

Leave a clear review result that says:

- what is correct
- what is risky or incomplete
- what must be fixed before merge
- whether the PR is merge-ready

## Operating rules

1. Review against the ticket, spec, or workflow requirements first.
2. Check tests, docs, and PR evidence, not only source changes.
3. Prefer concrete findings over style commentary.
4. Distinguish blockers from follow-up suggestions.
5. If the repo has hotspot signals, use them to prioritize scrutiny.

## Required workflow

### 1. Gather the review context

- identify the PR objective
- identify the files changed
- identify the stated validation evidence
- identify the expected ticket or workflow boundary

### 2. Review for correctness and scope

- does the change satisfy the stated objective
- does it stay inside scope
- are acceptance boundaries actually met
- are there hidden regressions or missing updates

### 3. Review validation and documentation

- are the right tests or checks present
- was the correct validation layer used
- were behavior, config, setup, workflow, or API docs updated where needed

### 4. Review merge readiness

- are there unresolved risks
- are there missing follow-up fixes
- is the PR ready to merge now, or not yet

## Report

Provide:

1. merge-readiness decision
2. blockers
3. non-blocking improvements
4. gaps in tests or docs
5. high-risk files or behaviors that deserve extra scrutiny
