# Static-analysis policy details

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
remediation attempts, remaining blockers, and coverage gaps. In automatic
mode, also record the exact Rubber Duck validator profile and its availability;
the validator may explain a tool result but may not replace the tool's raw
finding or exit status.
