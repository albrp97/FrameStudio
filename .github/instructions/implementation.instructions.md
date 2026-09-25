---
applyTo: "{.github/prompts/implement-feature-workflow.prompt.md,docs/guide/new-project-guide.md,docs/guide/delivery-workflows.md,harmonic-custom/skills/implement-ticket/SKILL.md}"
---

# Implementation Workflow Rules

- Start from the active ticket, not from assumptions.
- Restate scope, acceptance, risks, and validation target before coding.
- Prefer a failing-test-first loop when the behavior can be proved through tests.
- Keep changes small, coherent, and reviewable.
- Documentation updates are required when behavior, commands, setup, config, workflows, or integrations change.
- "Done" means merge-ready, merged, or externally blocked after all local work is complete.
- Read `.github/aidd-config.yml` before selecting commands or approval behavior.
- Follow technical verification -> automated functionality -> mode-specific
  validation -> review -> commit -> push -> PR/local closeout.
- In automatic mode, do not wait for routine user input after verified
  bootstrap; stop only for a real blocker.
