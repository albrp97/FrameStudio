---
agent: agent
description: "AIDD /aidd-upskill — create or review AIDD skills using AgentSkills.io spec and SudoLang. Use when scaffolding a new skill or evaluating an existing one."
---

# 🛠️ Upskill

Act as an expert skill author using the skill authoring guide in [aidd-upskill](../skills/aidd-upskill/SKILL.md).
Respect the general constraints in [aidd-please](../skills/aidd-please/SKILL.md).

Commands {
  /aidd-upskill create [name] — scaffold a new skill at ../skills/aidd-[name]/SKILL.md
  /aidd-upskill review [target] — evaluate a skill against the criteria in the guide
}

Constraints {
  Use SudoLang syntax for constraints, commands, functions, and typed interfaces.
  Prefer natural language in markdown format for prose.
  (two or more skills share the same function) => extract a shared abstraction.
  Every lifecycle or mutating skill must declare inputs, outputs, files,
  side effects, approval and stop conditions, required evidence, repository
  and provider dependencies, failure behavior, and commit/push/resolve/merge
  permissions.
  Domain-only skills must declare the lightweight workflow interface and must
  not claim delivery readiness.
}