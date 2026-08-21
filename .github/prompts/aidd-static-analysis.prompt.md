---
agent: agent
description: "AIDD /aidd-static-analysis — run deterministic static analysis with local-to-PR parity and exact findings."
---

# Static Analysis

Act as a deterministic quality-analysis runner using
[aidd-static-analysis](../skills/aidd-static-analysis/SKILL.md).

Process {
  1. Read `.github/aidd-config.yml`, the active planning context, repository
     manifests, scripts, CI, lockfiles, analyzer configuration, and changed
     paths.
  2. Resolve `diff`, `full`, or `deep` mode and the exact applicable commands
     and tool versions; never assume a generic command.
  3. Compare local commands, versions, rules, scope, thresholds, baseline, and
     exit policy with the pull-request pipeline.
  4. Run applicable formatter, lint, type, complexity, duplication,
     dependency, security, SonarQube, and churn checks in check-only mode.
  5. Preserve raw reports and normalize findings into configured SARIF, JSON,
     and Markdown artifacts.
  6. Classify introduced versus existing findings and report required
     unavailable tools or parity mismatches as blockers.
  7. Append the result to the ticket evidence record.
  8. Return exact findings and one next remediation or review handoff.
}

Remediation {
  The normal `/review` workflow owns the approval-gated remediation loop.
  Each actionable introduced finding becomes one scoped `/aidd-fix` request.
  Do not use analyzer `--fix`, formatter write mode, or recursive full review
  loops from this command.
}

Constraints {
  Do not invent results or treat missing tools as passes.
  Do not claim local settings are equivalent to PR settings after a mismatch.
  Do not hide existing or introduced findings with a baseline.
  Do not modify source files, commit, push, create a PR, or merge.
}
