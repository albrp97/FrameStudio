---
applyTo: "{.github/prompts/implement-feature-workflow.prompt.md,.github/prompts/setup-project-workflow.prompt.md,.github/prompts/run-user-test-workflow.prompt.md,.github/prompts/review-hotspots-workflow.prompt.md,docs/guide/new-project-guide.md,harmonic-custom/skills/implement-ticket/SKILL.md}"
---

# Testing and Validation Rules

- Prefer the highest-level existing validation that proves the software is usable.
- Use functional or end-to-end checks when the change affects user-visible behavior.
- If the repo does not have the ideal test layer yet, use the best existing checks and state the gap explicitly.
- Every acceptance outcome requires an executable automated functionality test
  through the supported system boundary. Unit tests and manual narration do not
  replace it.
- Technical checks are agent-owned. User handoffs contain functionality steps
  only; users must not be asked to run diagnostics, static analyzers, builds,
  or other technical commands.
- Guided mode records `userValidation`; automatic mode records
  `automaticValidation` through the exact configured Rubber Duck profile.
- When adding workflow validation rules, distinguish:
  - local developer checks
  - CI checks
  - release or user-testing checks
- Avoid success-shaped claims without a proving validation step.
