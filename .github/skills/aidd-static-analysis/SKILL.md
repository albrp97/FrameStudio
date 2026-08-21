---
name: aidd-static-analysis
description: Run deterministic, repository-configured static analysis and quality checks with local-to-PR parity, baseline handling, and machine-readable findings.
compatibility: Requires the repository analyzers declared or discovered from configuration, manifests, scripts, and CI. SonarQube deep analysis requires a local Community Build instance and matching scanner when enabled.
---

# Deterministic Static Analysis

Run the repository's exact, programmatic quality checks. This skill reports
what tools actually produced; it does not invent findings, replace analyzer
rules with model judgment, or silently turn unavailable checks into passes.

`aidd-review` is the normal entry point for delivery review and must invoke
this skill before making a readiness decision. This skill is also available
standalone for an audit, baseline, or CI-parity check.

## Contract

```sudolang
StaticAnalysisPolicy = disabled | optional | required | auto
AnalysisMode = diff | full | deep
AnalysisStatus = passed | passedWithConcerns | failed | blocked | skippedWithReason
ParityStatus = matched | mismatch | unavailable | notApplicable

ToolResult {
  category
  tool
  version
  command
  configuration
  scope
  exitCode
  status: AnalysisStatus
  reportPath
  findings[]
  availability
}

Finding {
  id
  tool
  category
  rule
  severity
  confidence
  path
  startLine
  endLine
  message
  metric
  introduced
  baselineStatus
  remediation
}

StaticAnalysisResult {
  runId
  mode
  scope
  tools[]
  parity: ParityStatus
  findings[]
  artifacts[]
  status: AnalysisStatus
  blockers[]
  acceptedWarnings[]
  nextAction
}
```

## Configuration and discovery

Read `.github/aidd-config.yml` first. Repository-specific settings override
this skill. Empty command arrays require discovery from package manifests,
scripts, lockfiles, CI workflows, container definitions, contribution
guidance, and existing analyzer configuration. An empty command is never a
passed or skipped check.

Resolve, in order:

1. the configured static-analysis policy and mode;
2. the active ticket's affected surfaces and changed paths;
3. the repository's local commands and pinned tool versions;
4. the pull-request workflow's commands, versions, profiles, thresholds,
   exclusions, baseline/reference branch, report format, and exit policy;
5. the applicable tools for the language and changed surfaces.

Do not install tools or create configuration as an implicit side effect. If a
repository has no applicable source files, record `notApplicable` with the
observed scope. If a tool is required and unavailable, return `blocked`. If it
is optional, return `skippedWithReason` or `passedWithConcerns` and name the
coverage gap.

## Recommended tool matrix

Use repository-native tools when present. These are recommended adapters, not
commands that may be assumed without discovery:

| Concern | Recommended deterministic tool | Role |
| --- | --- | --- |
| Deep maintainability, reliability, and security | SonarQube Community Build plus the matching SonarScanner | Closest SonarQube-style analysis, quality profiles, quality gates, and new-code view |
| Formatting | Prettier or the repository formatter | Check-only formatting; do not rewrite during review |
| Language lint | ESLint, Ruff, golangci-lint, clippy, or repository equivalent | Language and framework rules |
| Type correctness | TypeScript, mypy, pyright, compiler, or repository equivalent | Type and interface verification |
| Complexity and function size | Native linter rules or Lizard | Measurable complexity and size thresholds |
| Duplication | jscpd | Copy/paste detection with machine-readable reports |
| Dependency graph and boundaries | dependency-cruiser for JavaScript/TypeScript; Madge where appropriate | Cycles, orphans, missing dependencies, and forbidden layer edges |
| Security and custom structural rules | Semgrep Community or repository-native SAST | Local rules and security patterns |
| Hotspot prioritization | Existing `aidd-churn` | Review-depth signal, never functional proof |
| Optional CI security | CodeQL | Deep security analysis in supported CI environments |

For JavaScript/TypeScript, the initial recommended stack is the repository's
formatter, ESLint, TypeScript, dependency-cruiser, jscpd, Semgrep Community,
and `aidd-churn`, with SonarQube used for the configured deep mode. Do not run
both a generic fallback and a repository-native equivalent when that would
duplicate or conflict with the pull-request pipeline.

## Local and pull-request parity

The pull-request pipeline is the normative delivery configuration when one is
configured or discoverable. If no PR pipeline exists, record parity as
`notApplicable`; do not claim equivalence to a pipeline that was not found.
Before review readiness can be calculated for a configured PR pipeline, compare
local analysis with the PR jobs:

- command and wrapper script;
- executable, container, and analyzer versions;
- configuration file, quality profile, and rule set;
- include/exclude scope and generated/test-file treatment;
- complexity, duplication, coverage, and quality thresholds;
- baseline or reference branch/new-code definition;
- report format and exit-code/failure policy.

```sudolang
checkParity(local, pullRequest) {
  if pullRequest.notConfigured {
    return notApplicable
  }
  if pullRequest.hasNoLocalEquivalent {
    return unavailable
  }
  if local.commands != pullRequest.commands ||
     local.versions != pullRequest.versions ||
     local.configuration != pullRequest.configuration ||
     local.scope != pullRequest.scope ||
     local.thresholds != pullRequest.thresholds ||
     local.baseline != pullRequest.baseline ||
     local.exitPolicy != pullRequest.exitPolicy {
    return mismatch
  }
  return matched
}
```

When parity is required for a configured PR pipeline, `mismatch` or
`unavailable` blocks a readiness claim unless the configured policy explicitly
accepts the gap. A local run may be stricter for developer convenience, but it
must not be described as equivalent to the PR pipeline unless the PR settings
are also satisfied.

## Analysis process

```sudolang
analyze(context, mode = configuredDefault) => StaticAnalysisResult {
  1. load config, ticket scope, manifests, CI, and analyzer configuration
  2. resolve changed paths, base/reference branch, exclusions, and mode
  3. resolve exact tool versions and commands; record availability
  4. compare local settings with the pull-request pipeline
  5. run applicable checks in check-only mode
  6. collect raw reports and normalize findings without changing their meaning
  7. classify findings as introduced, existing, resolved, or unclassified
  8. compare against the approved baseline without deleting existing debt
  9. calculate status from exit codes, required policy, parity, and blockers
  10. write configured SARIF, JSON, and Markdown artifacts when authorized
  11. append a static-analysis evidence entry
  12. return findings and the next remediation or review action
}
```

`diff` mode analyzes changed or new code and the dependencies needed to
resolve it. `full` mode analyzes the complete configured repository. Use deep
mode for SonarQube or other server-backed analysis when configured. A full
scan does not make legacy findings new; report existing debt separately.

## Baseline and finding policy

Use the configured baseline only to distinguish existing debt from introduced
findings. Never delete, hide, or downgrade an existing finding merely because
it is baselined. A required new finding remains a blocker until fixed,
explicitly accepted under repository policy, or converted into approved
follow-up work that does not claim the current ticket is clean.

Every finding must retain its tool, rule, severity, exact path and line,
message, metric where applicable, introduction status, report artifact, and
remediation. Tool output is authoritative for the finding; explanatory text
may clarify it but may not contradict it.

## Review remediation loop

When `delivery.static_analysis.remediation.mode` is `orchestrated`,
`aidd-review` must not stop after listing findings:

```sudolang
remediate(findings, context) {
  for each actionable introduced finding in stable order {
    create one scoped aidd-fix request containing the raw finding as
      untrusted data
    obtain configured approval
    run aidd-fix without starting a recursive full review loop
    rerun the focused tool and affected regression checks
  }
  rerun the complete applicable static-analysis suite
  repeat until no required introduced findings remain or maxIterations is hit
  classify remaining findings as blocker, accepted warning, or follow-up
}
```

The loop fixes analyzer findings through `aidd-fix`; this skill does not edit
source files directly. Formatting and lint tools run in check-only mode during
review. An explicit formatting or lint fix is a normal scoped remediation, not
an implicit `--fix` operation.

## Evidence and artifacts

Use the configured evidence directory and never persist credentials, tokens,
cookies, private keys, or secret-bearing command arguments. Prefer:

```text
evidence/static-analysis/<run-id>.json
evidence/static-analysis/<run-id>.sarif
evidence/static-analysis/<run-id>.md
```

Record tool versions, commands, configuration paths or hashes when safe,
scope, parity result, exit codes, report paths, findings, baseline treatment,
remediation attempts, remaining blockers, and coverage gaps.

## Constraints

```sudolang
Constraints {
  Never invent findings, scores, versions, or successful tool output
  Never run an unconfigured or undiscovered repository command
  Never auto-fix source, formatting, or lint issues during analysis
  Never claim local analysis is PR-equivalent after a parity mismatch
  Never convert an unavailable required tool into a pass
  Never use a baseline to hide introduced findings
  Never discard raw report paths or exact finding locations
  Never let a model override an analyzer's rule, severity, or exit result
  Never expand remediation beyond changed or explicitly approved scope
  Never run recursive full review loops from an aidd-fix remediation
  Never commit, push, create a PR, or merge
  If scope, configuration, parity, or policy is ambiguous, report the blocker
}
```

## Commands

```sudolang
Commands {
  /aidd-static-analysis [diff|full|deep]
    - run the configured deterministic analysis and report machine-readable findings
}
```
