---
agent: agent
description: "/planning-bootstrap — initialize trustworthy planning context"
---

# Planning-Bootstrap

Use [../skills/aidd-planning-bootstrap/SKILL.md](../skills/aidd-planning-bootstrap/SKILL.md) as the executable contract.

userPrompt = """
Initialize planning context for the requested repository change. Resolve configured artifact paths and canonical vocabulary, inspect existing objective/scope/maps and all phase, feature, and ticket records in both open and closed directories, validate status/path and index consistency, classify adaptive depth, and report inconsistencies or approval blockers. Write only explicitly authorized bootstrap artifacts; do not generate phases, features, or tickets as a side effect.
"""

Constraints {
  Treat paths as repository-relative and read `.github/aidd-config.yml` when present
  Reconcile configured open/closed planning directories and current index paths
  Do not move records or silently repair status/path mismatches
  Use canonical objective -> scope -> capability -> phase -> feature -> ticket ancestry
  Use adaptive depth, stable IDs, parent/child links, explicit statuses, and evidence/coverage links
  Do not silently generate downstream artifacts, expand scope, or claim readiness without terminal evidence
  Stop and report the exact blocker for missing parent, approval, evidence, ownership, or required capability
  Do not assume npm, GitHub, Azure, credentials, or a particular test runner
}
