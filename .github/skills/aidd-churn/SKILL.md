---
name: aidd-churn
description: Run configurable hotspot analysis and use it as a review-depth risk signal, never as a substitute for functional evidence.
compatibility: Requires git history and Node.js 16+ for the aidd CLI; availability may be optional per repository configuration.
---

# aidd-churn

Identify files where size, change frequency, complexity, and density combine
into elevated review risk. Use the result to prioritize inspection, regression
coverage, and refactoring discussion.

## Policy

Read `.github/aidd-config.yml` before running:

- `delivery.gates.churn: required` makes unavailable analysis a blocker;
- `optional` records the availability gap and continues;
- `disabled` skips the analysis without making a hotspot claim.

Thresholds, time window, result count, and minimum size are configurable. Do
not claim a file is a hotspot without current CLI output.

## Process

```sudolang
collectHotspots({ days = 90, top = 20, minLoc = 50 } = {}) => report {
  run `npx aidd churn --days $days --top $top --min-loc $minLoc`
  for PR review => also run `npx aidd churn --json` and cross-reference the diff
  if unavailable {
    required => blocked
    optional => passedWithConcerns and record coverage gap
    disabled => skippedWithReason
  }
}

interpret(report) => analysis {
  explain the dominant LoC, churn, complexity, or density signal for each file
  identify files with multiple elevated signals
}

recommend(analysis, context) => recommendations {
  highLoC => extract cohesive modules or pure utilities
  highChurn => split unstable responsibilities behind stable interfaces
  highCx => extract predicates, flatten branches, or use focused strategies
  lowDensity => remove repetition with shared helpers
  prReview => prioritize files present in both the diff and hotspot report
}
```

Record the command, output artifact, configuration, and interpretation in
`/evidence` when the analysis is part of a ticket or review. Churn informs
review depth; it does not prove behavior, security, or readiness.

## Constraints

```sudolang
Constraints {
  Never guess hotspot scores or file rankings
  Never replace functional evidence with churn output
  Never block an optional analysis without recording the availability gap
  Never recommend a refactor without naming the signal and concrete strategy
}
```

## Commands

```sudolang
Commands {
  /aidd-churn - run configured hotspot analysis and produce risk-focused recommendations
}
```
