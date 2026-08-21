---
agent: agent
description: "AIDD /help — list all available AIDD commands with descriptions. Use when you want to see what AIDD commands are available."
---

# ❓ Help

Respect the general constraints in [aidd-please](../skills/aidd-please/SKILL.md).

List the available commands concisely — just names, emojis, and one-line
descriptions. Include:

❓ /help | 🚀 /project-bootstrap | 👁️ /create-vision |
🚚 /adapt-planning-structure | 🚀 /planning-bootstrap |
🗺️ /create-repository-map |
🔍 /discover | 🧩 /create-capability-map | 🧱 /create-phases |
✨ /create-features | ✅ /create-tickets | 📋 /plan |
🔎 /review-planning-layer | 🧹 /groom-backlog | 🧪 /run-preimplementation-checklist |
⚙️ /execute | 🧾 /evidence | 🔬 /review | 📝 /phase-feedback |
🔁 /replan-when-necessary | 🐛 /aidd-fix | 🧪 /user-test | 🤖 /run-test |
📊 /aidd-static-analysis | 📈 /aidd-churn | 🔀 /aidd-parallel |
🔗 /aidd-pipeline | 🔍 /aidd-pr |
💾 /commit | 🚀 /push | 🧽 /clean-pr-branch | 🛠️ /aidd-upskill |
🧪 /aidd-riteway-ai

After the command list, include one concise context handoff:

```text
Next step: run `/plan` to inspect the active workflow and ready ticket.
Skill: `aidd-agent-orchestrator` — `/aidd-agent-orchestrator`
Why: help has no active delivery context, so the orchestrator must classify it
before a more specific skill is selected.
```

Constraints {
  Keep the command list concise.
  Always include the single next-step, skill, and reason handoff above.
}
