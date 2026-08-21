---
agent: agent
description: "AIDD /log — collect salient changes and log them to activity-log.md. Use after completing a significant feature."
---

# 📝 Log

Act as a senior software engineer using the logging methodology in [aidd-log](../skills/aidd-log/SKILL.md).
Respect the general constraints in [aidd-please](../skills/aidd-please/SKILL.md).

Constraints {
  Log ONLY completed features with significant user-facing value.
  Do not log config changes, file moves, minor fixes, or dependency updates.
  Keep commands, test results, blockers, artifacts, and gate status in the
  active `/evidence` record; link it when the feature entry needs provenance.
}
