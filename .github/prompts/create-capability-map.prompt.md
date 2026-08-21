---
agent: agent
description: "/create-capability-map — derive capabilities from approved context"
---

# Create-Capability-Map

Use [../skills/aidd-create-capability-map/SKILL.md](../skills/aidd-create-capability-map/SKILL.md) as the executable contract.

userPrompt = """
Using an approved objective and scope plus a current repository map, derive a capability map. Assign stable CAP IDs, affected surfaces, dependencies, risks, evidence/coverage gaps, and ancestry links. Stop for missing approval or contradictory evidence and request approval before any phase or feature generation.
"""

Constraints {
  Treat paths as repository-relative and read `.github/aidd-config.yml` when present
  Use canonical objective -> scope -> capability -> phase -> feature -> ticket ancestry
  Use adaptive depth, stable IDs, parent/child links, explicit statuses, and evidence/coverage links
  Do not silently generate downstream artifacts, expand scope, or claim readiness without terminal evidence
  Stop and report the exact blocker for missing parent, approval, evidence, ownership, or required capability
  Do not assume npm, GitHub, Azure, credentials, or a particular test runner
}
