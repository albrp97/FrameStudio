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
  2. In automatic mode, resolve the exact Rubber Duck validation profile:
     `rubber-duck`, `gpt-5.6-luna`, high reasoning, and `all-validation`.
     Block if it is missing, unavailable, or mismatched.
  3. Resolve `diff`, `full`, or `deep` mode and the exact applicable commands
     and tool versions; never assume a generic command.
  4. Compare local commands, versions, rules, scope, thresholds, baseline, and
     exit policy with the pull-request pipeline.
  5. Run applicable formatter, lint, type, complexity, duplication,
     dependency, security, SonarQube, and churn checks in check-only mode.
  6. Preserve raw reports and normalize findings into configured SARIF, JSON,
     and Markdown artifacts.
  7. Classify introduced versus existing findings and report required
     unavailable tools or parity mismatches as blockers.
  8. In automatic mode, have the Rubber Duck validator inspect and classify
     the result without overriding raw analyzer findings or exit codes.
  9. Append the result to the ticket evidence record.
  10. Return exact findings and one next remediation or review handoff.
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
  In automatic mode, require the exact Rubber Duck `gpt-5.6-luna`
    high-reasoning profile for the analysis and its readiness decision.
  Do not modify source files, commit, push, create a PR, or merge.
}
