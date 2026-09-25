---
applyTo: "{.github/prompts/review-security-workflow.prompt.md,docs/guide/security-rules.md,docs/guide/delivery-workflows.md,harmonic-custom/skills/review-security/SKILL.md}"
---

# Security Workflow Rules

- Use the repo security rules as first-class workflow inputs, not as an afterthought.
- Security review should focus on high-confidence risks that matter to the change.
- Require explicit treatment of secrets, auth/session handling, unsafe comparisons, injection risk, logging exposure, and validation boundaries.
- Keep the rules concrete and operational. Avoid huge generic checklists with little relevance to the work.
