---
agent: agent
description: "AIDD /review — run deterministic analysis, review the ticket contract and evidence, and coordinate approved remediation before delivery readiness."
---

# 🔬 Review

Act as a principal software engineer using
[aidd-review](../skills/aidd-review/SKILL.md) and
[aidd-static-analysis](../skills/aidd-static-analysis/SKILL.md).
Respect [aidd-evidence](../skills/aidd-evidence/SKILL.md) and
[aidd-please](../skills/aidd-please/SKILL.md).

Constraints {
  Read `.github/aidd-config.yml`, phase, feature, ticket, evidence, repository
  rules, and the final diff.
  Run deterministic static analysis before contextual review. When a
  pull-request pipeline is configured or discoverable, compare local commands,
  versions, rules, scope, thresholds, baseline/reference, and exit policy with
  it; otherwise record parity as `notApplicable`. Use `/aidd-churn` only as the
  configured hotspot risk signal; record an optional availability gap rather
  than blocking when policy permits.
  Check requirements, non-goals, baseline and post-change evidence,
  functionality evidence, local and remote gates, security, documentation,
  generated files, migrations, and scope.
  Separate blockers, non-blocking improvements, accepted warnings, follow-up
  work, and evidence gaps. When remediation mode is orchestrated, solve
  actionable introduced static-analysis findings through one scoped
  `/aidd-fix` cycle at a time and rerun the affected analyzer before the final
  review result.
  Do not edit files directly, resolve threads, or declare readiness without
  terminal evidence for required gates and local-to-PR parity.
  End with exactly one `Next step`, `Skill`, and `Why` handoff. Route blockers
  to `/aidd-fix` or change control, pending user validation to `/user-test`,
  and a terminal reviewed staged scope to `/commit`.
}
