---
agent: agent
description: "/run-preimplementation-checklist — decide ticket readiness"
---

# Run-Preimplementation-Checklist

Use [../skills/aidd-preimplementation-checklist/SKILL.md](../skills/aidd-preimplementation-checklist/SKILL.md) as the executable contract.

userPrompt = """
Run a read-only preimplementation checklist for one ticket. Verify complete objective-to-ticket ancestry, approvals, stable IDs, status, current open/closed path, scope/non-goals, dependencies, risks, ownership, protected behaviors, commands, gates, evidence path, exact user-validation steps, pass criteria, and the configured baseline prerequisite or terminal baseline evidence. Reject a closed ticket or closed ancestor as active work. Return ready=true only when every required check passes; otherwise list exact blockers and do not implement.
"""

Constraints {
  Treat paths as repository-relative and read `.github/aidd-config.yml` when present
  Read both lifecycle directories and do not move records during this check
  Require the selected ticket and active phase/feature ancestors to be in open
  Use canonical objective -> scope -> capability -> phase -> feature -> ticket ancestry
  Use adaptive depth, stable IDs, parent/child links, explicit statuses, and evidence/coverage links
  Do not silently generate downstream artifacts, expand scope, or claim readiness without terminal evidence
  Stop and report the exact blocker for missing parent, approval, evidence, ownership, or required capability
  Do not assume npm, GitHub, Azure, credentials, or a particular test runner
}
