---
agent: agent
description: "/groom-backlog — maintain backlog hygiene"
---

# Groom-Backlog

Use [../skills/aidd-groom-backlog/SKILL.md](../skills/aidd-groom-backlog/SKILL.md) as the executable contract.

userPrompt = """
Groom the requested backlog scope using only routine traceable maintenance: clarify wording, order work, deduplicate, or mark stale statuses while preserving IDs and history. If outcome, scope, capability, sequencing, dependency, risk, or acceptance materially changes, stop and route to change control instead of silently replanning. Do not claim readiness.
"""

Constraints {
  Treat paths as repository-relative and read `.github/aidd-config.yml` when present
  Read phase, feature, and ticket records from both `open` and `closed`
  directories; if an authorized status update crosses the boundary, move the
  same record and synchronize indexes/backlog
  Never archive, duplicate, or silently move a record
  Use canonical objective -> scope -> capability -> phase -> feature -> ticket ancestry
  Use adaptive depth, stable IDs, parent/child links, explicit statuses, and evidence/coverage links
  Do not silently generate downstream artifacts, expand scope, or claim readiness without terminal evidence
  Stop and report the exact blocker for missing parent, approval, evidence, ownership, or required capability
  Do not assume npm, GitHub, Azure, credentials, or a particular test runner
}
