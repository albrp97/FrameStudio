---
applyTo: "{docs/guide/delivery-workflows.md,docs/guide/new-project-guide.md,docs/guide/aidd-gap-closure-plan.md,.github/prompts/create-*.prompt.md,.github/prompts/review-planning-layer.prompt.md,.github/prompts/groom-backlog.prompt.md,.github/prompts/replan-when-necessary.prompt.md,.github/prompts/run-preimplementation-checklist.prompt.md}"
---

# Planning Workflow Rules

- For new work, use the canonical planning order:
  objective -> scope -> capability -> phase -> feature -> ticket. Existing
  problem/users/success and epic artifacts remain valid context and should be
  linked during migration rather than deleted.
- Do not let planning prompts skip directly from goal to tickets without scope and capability logic.
- Keep change control exceptional; use backlog grooming for routine corrections.
- Keep phase, feature, and ticket records in the configured `open/` and
  `closed/` lifecycle directories. Move the same stable-ID record and
  synchronize indexes; do not duplicate or delete records to represent status.
- When adding a new planning workflow, document:
  - where the artifact is stored
  - what metadata it needs
  - how AI should use it
  - what "done" means for that layer
- When editing the planning system, update both the workflow prompt and the guide entry that explains it.
- In automatic mode, use the configured Rubber Duck validation profile for
  planning readiness and stop on missing parents, evidence, or unavailable
  runtime capability.
