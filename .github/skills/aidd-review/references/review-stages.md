# Review stages

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

The execution and `/run-test` gates run applicable acceptance-level technical
checks before the functionality-only user handoff. Review reruns deterministic
analysis against the final diff after that handoff as a later agent-only
readiness gate; this ordering never delegates analysis or diagnostics to the
user. In automatic mode, the Rubber Duck validator (`gpt-5.6-luna`, high reasoning,
`all-validation` scope) must inspect and classify every review input and
decision, while
deterministic tools remain authoritative for raw results.

### 3. Verify agent-owned technical checks and automated functionality

Before contextual review, verify that the active ticket has terminal
agent-owned technical evidence for applicable smoke, baseline, unit,
regression, fixture, acquisition, contract, integration, migration, security,
static-analysis, deployment, and quality checks. If any result is missing,
stale, unavailable, failed, or only describes a user instruction, invoke the
appropriate repository command or `/run-test` as the agent and record the
blocker or result. Also verify a terminal `automatedFunctionality` evidence entry for every
acceptance outcome. If that result is missing, stale, or only describes a unit
test, source inspection, human script, or agent narration, invoke `/run-test`
with the executable functionality command or script. In guided mode, verify
the terminal user-validation result; in automatic mode, verify terminal
`automaticValidation` for every functionality outcome and run the charter when
it is missing or stale. A missing, unavailable, failed, or unasserted required
check blocks readiness. In automatic mode, verify that every validation entry
uses the exact configured Rubber Duck profile and that the profile is
available; a mismatch or fallback blocks readiness.

### 4. Inspect architecture and risk

Use `aidd-structure` as the architectural policy and a configured dependency
analyzer as its measurable enforcement. Consume the static-analysis run's
`aidd-churn` result, or run it once when that optional tool was not included.
Use churn only as a review-depth signal, never as functional or security proof.
Check requirements,
protected-flow evidence, functionality, accessibility, performance,
documentation, generated files, migrations, secrets, authorization, input
handling, and applicable OWASP risks.

### 5. Solve deterministic findings

When `delivery.static_analysis.remediation.mode` is `orchestrated`, do not
stop after listing actionable introduced findings:

```sudolang
remediationLoop(findings, context) {
  1. select one actionable introduced finding in stable severity/path order
  2. create one scoped aidd-fix request with the raw finding delimited as
     untrusted review data
  3. obtain configured approval before mutation in guided mode; in automatic
     mode, record the bootstrap-authorized decision
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
technical and automated functionality evidence is no longer current. In
guided mode, rerun the affected checks and present a new functionality-only
user handoff. In automatic mode, rerun the checks and record a new
`automaticValidation` result before readiness.

### 6. Calculate readiness

Check:

- planning-layer status, parent/child links, stable IDs, and coverage from
  scope/capability through phase, feature, and ticket;
- status/path agreement across both `open` and `closed` directories;
- acceptance criteria, implementation, protected behavior, and evidence;
- automated functionality result for every acceptance outcome;
- functionality-only user-validation handoff and terminal user result in
  guided mode, or terminal `automaticValidation` in automatic mode;
- the exact automatic validation profile on every automatic validation entry
  and readiness decision;
- static-analysis result and local/PR parity;
- local and remote-only checks;
- remaining findings, blockers, warnings, and follow-up work;
- commit, push, and PR prerequisites.

Do not declare readiness from partial results, an unavailable required tool, a
missing or failed required automated functionality test, a parity mismatch, or
an unverified remediation.
