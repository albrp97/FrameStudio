---
name: aidd-static-analysis
description: Run deterministic, repository-configured static analysis and quality checks with local-to-PR parity, baseline handling, and machine-readable findings. Use during review, baseline creation, or focused quality audits.
compatibility: Requires the repository analyzers declared or discovered from configuration, manifests, scripts, and CI. SonarQube deep analysis requires a local Community Build instance and matching scanner when enabled.
---

import ../lifecycle-interface.md

# Deterministic Static Analysis

```sudolang
Lifecycle {
  profile = analysisEvidence
}
```

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
  validationProfile
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

In automatic mode, also resolve the exact Rubber Duck validation profile from
`delivery.development.automatic_validation` before running or classifying any
result: validator `rubber-duck`, model `gpt-5.6-luna`, reasoning effort `high`,
and scope `all-validation`. A missing or unavailable profile blocks the
analysis result; deterministic analyzers still remain the source of raw
findings and exit codes.

Do not install tools or create configuration as an implicit side effect. If a
repository has no applicable source files, record `notApplicable` with the
observed scope. If a tool is required and unavailable, return `blocked`. If it
is optional, return `skippedWithReason` or `passedWithConcerns` and name the
coverage gap.

## Analysis policy reference

Load [analysis policy](./references/analysis-policy.md) when selecting tools,
proving local-to-PR parity, handling baselines, remediating findings, or writing
reports.

## Analysis process

```sudolang
analyze(context, mode = configuredDefault) => StaticAnalysisResult {
  1. load config, ticket scope, manifests, CI, and analyzer configuration
  2. resolve changed paths, base/reference branch, exclusions, and mode
  3. resolve the automatic validation profile when automatic mode is active
  4. resolve exact tool versions and commands; record availability
  5. compare local settings with the pull-request pipeline
  6. run applicable checks in check-only mode
  7. collect raw reports and normalize findings without changing their meaning
  8. classify findings as introduced, existing, resolved, or unclassified
  9. compare against the approved baseline without deleting existing debt
  10. have the configured Rubber Duck validator inspect and classify the
     complete result without overriding raw analyzer findings or exit codes
  11. calculate status from exit codes, required policy, parity, profile, and
     blockers
  12. write configured SARIF, JSON, and Markdown artifacts when authorized
  13. append a static-analysis evidence entry with the validation profile
  14. return findings and the next remediation or review action
}
```

`diff` mode analyzes changed or new code and the dependencies needed to
resolve it. `full` mode analyzes the complete configured repository. Use deep
mode for SonarQube or other server-backed analysis when configured. A full
scan does not make legacy findings new; report existing debt separately.

## Finding and remediation reference

The baseline, remediation, and artifact rules are defined in
[analysis policy](./references/analysis-policy.md).

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
  In automatic mode, require every analysis result and readiness decision to
    use the exact Rubber Duck `gpt-5.6-luna` high-reasoning profile
  Never use another model, validator, or fallback profile for automatic
    analysis
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
