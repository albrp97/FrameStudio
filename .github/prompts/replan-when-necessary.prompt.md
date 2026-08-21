---
agent: agent
description: "/replan-when-necessary — govern material change"
---

# Replan-When-Necessary

Use [../skills/aidd-change-control/SKILL.md](../skills/aidd-change-control/SKILL.md) as the executable contract.

userPrompt = """
Assess the proposed planning change against the approved hierarchy and classify it as no-change, routine correction, or material change. For material change, record a stable change ID, rationale, impact, affected descendants, evidence, owner, and required approval; preserve history and replan only the smallest approved subtree. Block readiness while approval or evidence is missing.
"""

Constraints {
  Treat paths as repository-relative and read `.github/aidd-config.yml` when present
  Inspect affected records in both `open` and `closed`; preserve stable IDs,
  path history, and current indexes when an approved status change moves a
  record
  Move only the affected record/subtree after approval; never use a folder move
  to hide an unapproved scope change
  Use canonical objective -> scope -> capability -> phase -> feature -> ticket ancestry
  Use adaptive depth, stable IDs, parent/child links, explicit statuses, and evidence/coverage links
  Do not silently generate downstream artifacts, expand scope, or claim readiness without terminal evidence
  Stop and report the exact blocker for missing parent, approval, evidence, ownership, or required capability
  Do not assume npm, GitHub, Azure, credentials, or a particular test runner
}
