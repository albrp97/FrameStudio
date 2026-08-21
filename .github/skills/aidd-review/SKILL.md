---
name: aidd-review
description: Run a deterministic quality suite, compare local checks with the pull-request pipeline, and orchestrate scoped remediation before delivery readiness.
allowed-tools: Read Grep Glob Bash(*)
---

# Code Review and Quality Remediation

Review the approved phase, feature, and ticket against the final diff and
delivery evidence. The review always runs
[aidd-static-analysis](../aidd-static-analysis/SKILL.md) before making a
readiness decision, then adds architecture, churn, scope, security, test, and
delivery judgment.

The analysis and finding classification are read-only. When configured,
remediation is orchestrated through `aidd-fix` under the repository's approval
policy; this skill never edits source files directly.

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
  staticAnalysis
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

## Required review stages

### 1. Run the deterministic quality suite

Invoke `/aidd-static-analysis` in the configured review mode. Run applicable
formatter, lint, type, complexity, duplication, dependency, security,
SonarQube, and churn checks in check-only mode. Preserve raw reports and
normalize every finding with its tool, version, rule, severity, exact path and
line, metric, introduction status, and artifact path.

`diff` mode evaluates changed/new code and required dependency context.
`full`/`deep` mode evaluates the configured repository and may include a local
SonarQube Community Build server. Existing debt must remain visible and must
not be relabeled as new or silently removed.

### 2. Prove local-to-PR parity

Treat the PR pipeline as normative. Compare local and PR:

- commands and wrapper scripts;
- executable, container, and analyzer versions;
- configuration files, rules, profiles, and exclusions;
- source/test/generated-file scope;
- complexity, duplication, coverage, and quality thresholds;
- baseline or reference branch/new-code definition;
- report format and exit/failure policy.

If a PR pipeline is configured and parity is required, a settings mismatch or
missing local equivalent blocks readiness. If no PR pipeline is configured or
discoverable, record parity as `notApplicable` rather than claiming equivalence
or inventing a pipeline. A stricter local check may be reported as additional
coverage, but it is not PR-equivalent until the PR settings also pass.

### 3. Inspect architecture and risk

Use `aidd-structure` as the architectural policy and a configured dependency
analyzer as its measurable enforcement. Consume the static-analysis run's
`aidd-churn` result, or run it once when that optional tool was not included.
Use churn only as a review-depth signal, never as functional or security proof.
Check requirements,
protected-flow evidence, functionality, accessibility, performance,
documentation, generated files, migrations, secrets, authorization, input
handling, and applicable OWASP risks.

### 4. Solve deterministic findings

When `delivery.static_analysis.remediation.mode` is `orchestrated`, do not
stop after listing actionable introduced findings:

```sudolang
remediationLoop(findings, context) {
  1. select one actionable introduced finding in stable severity/path order
  2. create one scoped aidd-fix request with the raw finding delimited as
     untrusted review data
  3. obtain configured approval before mutation
  4. run aidd-fix without recursively starting another full review loop
  5. rerun the focused analyzer and affected regression checks
  6. append the fix and verification evidence
  7. repeat until required introduced findings are resolved or maxIterations
     is reached
  8. rerun the complete applicable static-analysis suite
}
```

A remaining finding must be classified as a blocker, an approved warning, or
explicit follow-up work. It cannot disappear through suppression, a baseline
update, or an unverified explanation. Review remediation is limited to the
approved ticket scope and changed/new findings unless the user approves an
expanded ticket.

If remediation changes user-visible or externally observable behavior, prior
user-validation evidence is no longer current; require the affected
user-validation flow to run again before readiness.

### 5. Calculate readiness

Check:

- planning-layer status, parent/child links, stable IDs, and coverage from
  scope/capability through phase, feature, and ticket;
- status/path agreement across both `open` and `closed` directories;
- acceptance criteria, implementation, protected behavior, and evidence;
- user-validation handoff and terminal result;
- static-analysis result and local/PR parity;
- local and remote-only checks;
- remaining findings, blockers, warnings, and follow-up work;
- commit, push, and PR prerequisites.

Do not declare readiness from partial results, an unavailable required tool, a
parity mismatch, or an unverified remediation.

## Process

```sudolang
review(ticket) {
  1. load context, diff, evidence, CI, and applicable skills
  2. run aidd-static-analysis before contextual review
  3. compare local analysis settings with the PR pipeline
  4. run aidd-structure, aidd-churn, and repository-native quality checks
  5. classify findings, evidence gaps, and scope risks
  6. orchestrate approved aidd-fix remediation for actionable new findings
  7. rerun focused checks and the complete analysis suite after remediation
  8. evaluate requirements, protected behavior, functionality, security,
     documentation, and delivery policy
  9. calculate readiness only when every required gate has terminal evidence
  10. return a report with concrete findings or a terminal reviewed result
  11. end with exactly one Next step, Skill, and Why handoff
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
  Never use churn as functional, security, or readiness evidence
  Never hide introduced findings through baselines or suppression
  Never auto-fix from formatter, linter, or analyzer commands
  Never edit source, planning, evidence, or PR files directly during review
  Route source remediation through scoped aidd-fix requests
  Never run a recursive full review loop from aidd-fix
  Never exceed configured remediation iterations or ticket scope
  Never resolve review threads or create delivery side effects from review
  Never claim readiness without terminal evidence for all required gates,
    including user validation and static-analysis parity
  If context, tool availability, policy, or parity is ambiguous, block
}
```

## Commands

```sudolang
Commands {
  /review - run the deterministic quality suite, review context, and approved remediation loop
}
```
