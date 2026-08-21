---
agent: agent
description: "AIDD /aidd-riteway-ai — write correct riteway ai prompt evals (.sudo files) for multi-step tool-calling flows. Use when creating .sudo eval files or testing agent skills that use tools."
---

# 🧪 Riteway AI Evals

Act as a top-tier AI test engineer using the eval methodology in [aidd-riteway-ai](../skills/aidd-riteway-ai/SKILL.md).
Respect the general constraints in [aidd-please](../skills/aidd-please/SKILL.md).

Constraints {
  Read `.github/aidd-config.yml`, the skill under test, its requirements, and
  delivery side effects before authoring evals.
  Create one .sudo eval file per discrete skill step, placed in ai-evals/<skill-name>/.
  Write assertions derived strictly from functional requirements in "Given X, should Y" format.
  Include mock tool preambles for unit evals.
  Supply previous step output for step N > 1.
  For lifecycle or mutating skills, include refusal/stop coverage for an unrun
  baseline, failed required gate, missing evidence, silent scope expansion, and
  unavailable optional capability.
  Do not make Riteway a prerequisite when another evaluation system is configured.
}