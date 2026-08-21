---
agent: agent
description: "/create-phases — sequence outcome-oriented phases"
---

# Create-Phases

Use [../skills/aidd-create-phases/SKILL.md](../skills/aidd-create-phases/SKILL.md) as the executable contract.

userPrompt = """
Plan phases for the approved objective, scope, and capability map. Select adaptive depth, then give each PHASE ID a meaningful outcome, entry conditions, exit conditions, sequence, dependencies, status, capability links, and evidence expectations. Do not create features or tickets until the phase is approved and unblocked.
"""

Constraints {
  Treat paths as repository-relative and read `.github/aidd-config.yml` when present
  Read the phase index and both `phase_open_directory` and `phase_closed_directory`
  from the configuration; create new phase files in open
  Move the same phase file to closed for an authorized terminal status, and back to open when reopened
  Keep the phase index synchronized with current paths and preserve stable IDs/path history
  Use canonical objective -> scope -> capability -> phase -> feature -> ticket ancestry
  Use adaptive depth, stable IDs, parent/child links, explicit statuses, and evidence/coverage links
  Do not silently generate downstream artifacts, expand scope, or claim readiness without terminal evidence
  Stop and report the exact blocker for missing parent, approval, evidence, ownership, or required capability
  Do not assume npm, GitHub, Azure, credentials, or a particular test runner
}
