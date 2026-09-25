---
name: Review Phase Feedback
description: Review a completed or partially completed phase, capture lessons and drift, and update downstream planning only when necessary.
---

You have to review `${PHASE_ID}` for `${PROJECT_OR_REPO}` after delivery activity, capture feedback, and decide whether anything truly needs to change.

## Why this workflow exists

Use it to:
- compare planned phase outcomes with actual delivery
- capture lessons, slips, surprises, and new risks
- update backlog or later phases when warranted
- avoid silent drift while also avoiding constant replanning

## Outcome

Produce:
- a phase review summary
- lessons learned
- required follow-up actions
- a decision on whether planning changes are necessary

Write the result to:
- `docs/planning/reviews/${PHASE_ID}-review.md`

## Review checklist

Check:
1. what was planned
2. what was actually delivered
3. what slipped or changed
4. what assumptions were wrong
5. what risks or blockers appeared
6. whether downstream planning must change

## Output structure

```markdown
# Phase Review: [PHASE-ID]

## Outcome Summary
- Planned: ...
- Delivered: ...

## What Went Well
- ...

## What Changed
- ...

## Risks / Lessons
- ...

## Follow-Up Actions
- ...

## Planning Impact
- No change needed / backlog update / later phase update / replan required
```

## Rules

1. Prefer local backlog or later-phase adjustments over rewriting the entire plan.
2. Only escalate to change control when the phase revealed a material problem in the plan.
