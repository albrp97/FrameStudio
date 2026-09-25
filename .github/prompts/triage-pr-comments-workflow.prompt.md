---
name: Triage PR Comments Workflow
description: Separate already-addressed review comments from still-open issues and turn the remaining items into a repair loop.
---

You have to triage the review comments on `${PR_OR_REVIEW_SET}` without creating noise or hiding unresolved issues.

## Outcome

Leave a clean classification of review feedback:

- already addressed
- still open
- blocked by another issue

## Operating rules

1. Do not assume a comment is resolved just because nearby code changed.
2. Do not silently drop unresolved review concerns.
3. Keep the work on the same PR branch unless a real repo rule requires otherwise.
4. Turn unresolved issues into explicit repair items with scope and expected fix.

## Required workflow

### 1. Read the review context

- the comment
- the affected file or behavior
- the current source state

### 2. Classify each comment

- addressed
- remaining
- duplicate
- blocked

### 3. Build the repair loop

For remaining items, define:

- the issue to fix
- the likely file or surface
- whether tests or docs must change too

## Report

Provide:

1. addressed comments
2. remaining comments
3. blocked or duplicate comments
4. next repair actions in priority order
