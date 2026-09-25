---
name: aidd-review
description: Run a deterministic quality suite, compare local checks with the pull-request pipeline, and orchestrate scoped remediation before delivery readiness. Use when implementation and validation evidence are ready for final review.
allowed-tools: Read Grep Glob Bash(*)
---

import ../lifecycle-interface.md

# Code Review and Quality Remediation

```sudolang
Lifecycle {
  profile = reviewOrchestration
}
```

Review the approved phase, feature, and ticket against the final diff and
delivery evidence. The review always runs
[aidd-static-analysis](../aidd-static-analysis/SKILL.md) before making a
readiness decision, then adds architecture, churn, scope, security, test, and
delivery judgment.

The analysis and finding classification are read-only. When configured,
remediation is orchestrated through `aidd-fix` under the repository's approval
policy; this skill never edits source files directly.
Apply [../development-mode.md](../development-mode.md) when evaluating the
validation gate, remediation approval, and post-review continuation.

## Inputs

Read, when present:

1. `.github/aidd-config.yml`;
2. the active phase, feature, and ticket contract in their configured lifecycle
   directories;
3. the evidence record and its referenced artifacts;
4. repository README, manifests, lockfiles, CI, contribution guidance, and
   analyzer configuration;
5. applicable domain skills before reviewing their code;
6. the final diff, worktree state, branch/base relationship, and PR metadata;
7. `aidd-static-analysis`, `aidd-structure`, and `aidd-churn`.

Use repository-native commands and versions discovered from manifests, scripts,
CI, containers, and lockfiles. A generic command is never a substitute for
repository evidence.

## Review result

```sudolang
ReviewResult {
  planningCoverage
  technicalVerification
  staticAnalysis
  automatedFunctionality
  modeAppropriateValidation
  validationProfile
  localPrParity
  blockers[]
  nonBlockingImprovements[]
  acceptedWarnings[]
  followUpWork[]
  evidenceGaps[]
  remediationRuns[]
  readiness
}
```

## Review stages

Load [review stages](./references/review-stages.md) when executing deterministic
analysis, parity checks, contextual review, remediation, or readiness
calculation.

## Process

```sudolang
review(ticket) {
  1. load context, diff, evidence, CI, and applicable skills
  2. run aidd-static-analysis before contextual review
  3. compare local analysis settings with the PR pipeline
  4. verify or run agent-owned technical checks and the automated functionality
     test for every acceptance outcome
  5. run aidd-structure, aidd-churn, and repository-native quality checks
  6. classify findings, evidence gaps, and scope risks
  7. orchestrate approved aidd-fix remediation for actionable new findings
  8. rerun focused checks, automated functionality, and the complete analysis suite after remediation
  9. evaluate requirements, protected behavior, functionality, security,
     documentation, and delivery policy
  10. calculate readiness only when every required gate has terminal evidence
  11. return a report with concrete findings or a terminal reviewed result
  12. end with exactly one Next step, Skill, and Why handoff
}
```

If the review is invoked by an `aidd-fix` remediation, perform only the
focused verification requested by the parent and return its result; do not
start a second remediation loop.

## Constraints

```sudolang
Constraints {
  Never invent analyzer output, scores, versions, or parity
  Never treat a missing or incompatible PR-equivalent check as a pass
  Never treat a unit test, source inspection, human script, or agent narration
    as automated functionality evidence
  Never ask the user to run smoke, baseline, unit, regression, fixture,
    acquisition, contract, integration, migration, security, static-analysis,
    formatter, lint, type-check, build, deployment, or other technical checks
  Treat guided user-validation evidence as confirmation of delivered
    functionality only; technical checks belong to agent-owned evidence
  Treat automaticValidation as agent-owned functionality evidence only; never
    claim it is user confirmation
  Never use churn as functional, security, or readiness evidence
  Never hide introduced findings through baselines or suppression
  Never auto-fix from formatter, linter, or analyzer commands
  Never edit source, planning, evidence, or PR files directly during review
  Route source remediation through scoped aidd-fix requests
  Never run a recursive full review loop from aidd-fix
  Never exceed configured remediation iterations or ticket scope
  Never resolve review threads or create delivery side effects from review
  Never claim guided readiness without terminal evidence for all required
    gates, including automated functionality, user validation, and
    static-analysis parity
  Never claim automatic readiness without terminal automated functionality,
    automaticValidation, and static-analysis parity evidence produced or
    classified with the exact Rubber Duck `gpt-5.6-luna` high-reasoning profile
  If context, tool availability, policy, or parity is ambiguous, block
}
```

## Commands

```sudolang
Commands {
  /review - run the deterministic quality suite, review context, and approved remediation loop
}
```
