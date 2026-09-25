---
applyTo: "{.github/prompts/review-*.prompt.md,.github/prompts/triage-pr-comments-workflow.prompt.md,docs/guide/delivery-workflows.md,docs/guide/new-project-guide.md,harmonic-custom/skills/review-*/SKILL.md,harmonic-custom/skills/triage-pr-comments/SKILL.md}"
---

# Review Workflow Rules

- Reviews should focus on correctness, scope adherence, validation, and risk.
- Use dedicated review workflows instead of generic "check this PR" instructions when available.
- Prefer explicit findings with file path, severity, rationale, and required action.
- Backlog grooming and planning reviews are separate from PR review; do not mix them casually.
- PR triage must be branch-safe and must not silently resolve unresolved issues.
- Run deterministic static analysis before contextual review when
  `delivery.static_analysis.run_on_review` is enabled.
- Route actionable introduced findings through the configured remediation
  workflow; preserve raw analyzer output and do not silently downgrade required
  failures.
- In automatic mode, record the exact Rubber Duck profile on each validation
  decision and block on an unavailable or mismatched capability.
