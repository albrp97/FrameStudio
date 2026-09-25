---
name: Review Hotspots Workflow
description: Identify high-risk files using size, churn, complexity, and recency signals and use them to prioritize review.
---

You have to assess `${CHANGESET_OR_REPO_AREA}` for review hotspots before or during merge review.

## Outcome

Identify which files deserve extra scrutiny, why they are risky, and whether the current change should be simplified or split.

## Operating rules

1. Prefer quantitative or observable signals over intuition.
2. Use the smallest practical signal set available in the repository.
3. Hotspot review is a prioritization layer, not an automatic rewrite command.
4. If the repo does not yet have automated scoring, use the documented fallback heuristic explicitly.

## Signals to use

Prioritize:

- file size or surface area
- recent churn
- structural complexity
- recent instability in the affected area

## Required workflow

### 1. Identify candidate hotspot files

- changed files
- frequently touched files
- unusually large or complex files
- files that combine broad responsibility with recent churn

### 2. Explain the dominant risk signal

For each hotspot, say whether the risk is mainly:

- size
- churn
- complexity
- mixed responsibility

### 3. Decide review action

- normal review is enough
- extra scrutiny is required
- split or simplify before merge is recommended

## Report

Provide:

1. ranked hotspot list
2. dominant signal for each hotspot
3. why it matters to the current change
4. recommended review or refactor action
