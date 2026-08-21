---
agent: agent
description: "/create-features — decompose one approved phase"
---

# Create-Features

Use [../skills/aidd-create-features/SKILL.md](../skills/aidd-create-features/SKILL.md) as the executable contract.

userPrompt = """
Decompose exactly one approved, unblocked phase into outcome-focused features. Each feature must map to exactly one phase and at least one capability, use a stable FEAT ID, and include scope, non-goals, risks, dependencies, affected surfaces, acceptance outcomes, evidence plan, and status. Do not create tickets for draft or unapproved features.
"""

Constraints {
  Treat paths as repository-relative and read `.github/aidd-config.yml` when present
  Read the feature index and both `feature_open_directory` and `feature_closed_directory`
  from the configuration; create new feature files in open
  Move the same feature file to closed for an authorized terminal status, and back to open when reopened
  Keep the feature index synchronized with current paths and preserve stable IDs/path history
  Use canonical objective -> scope -> capability -> phase -> feature -> ticket ancestry
  Use adaptive depth, stable IDs, parent/child links, explicit statuses, and evidence/coverage links
  Do not silently generate downstream artifacts, expand scope, or claim readiness without terminal evidence
  Stop and report the exact blocker for missing parent, approval, evidence, ownership, or required capability
  Do not assume npm, GitHub, Azure, credentials, or a particular test runner
}
