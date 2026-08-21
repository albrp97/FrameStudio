---
agent: agent
description: "/create-repository-map — map repository surfaces and ownership"
---

# Create-Repository-Map

Use [../skills/aidd-create-repository-map/SKILL.md](../skills/aidd-create-repository-map/SKILL.md) as the executable contract.

userPrompt = """
Create or update the repository map from observable directories, manifests, guidance, commands, integrations, and ownership evidence. Link every assertion to a repository-relative source path. Preserve stable map identifiers and mark stale or unknown entries; do not derive capabilities, phases, features, or tickets.
"""

Constraints {
  Treat paths as repository-relative and read `.github/aidd-config.yml` when present
  Use canonical objective -> scope -> capability -> phase -> feature -> ticket ancestry
  Use adaptive depth, stable IDs, parent/child links, explicit statuses, and evidence/coverage links
  Do not silently generate downstream artifacts, expand scope, or claim readiness without terminal evidence
  Stop and report the exact blocker for missing parent, approval, evidence, ownership, or required capability
  Do not assume npm, GitHub, Azure, credentials, or a particular test runner
}
