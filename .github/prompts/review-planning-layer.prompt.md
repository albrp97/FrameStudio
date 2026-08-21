---
agent: agent
description: "/review-planning-layer — audit planning consistency"
---

# Review-Planning-Layer

Use [../skills/aidd-planning-layer-review/SKILL.md](../skills/aidd-planning-layer-review/SKILL.md) as the executable contract.

userPrompt = """
Review the requested planning layer and required ancestry/descendants read-only. Inspect both open and closed directories, then check hierarchy, one-parent links, stable IDs, statuses, current paths, index synchronization, approvals, scope boundaries, coverage/evidence links, and gate completeness. Report passes, warnings, blockers, orphaned records, duplicate IDs, status/path mismatches, and the smallest corrective action. Never move files, generate missing children, or call a non-terminal item ready.
"""

Constraints {
  Treat paths as repository-relative and read `.github/aidd-config.yml` when present
  Use canonical objective -> scope -> capability -> phase -> feature -> ticket ancestry
  Use adaptive depth, stable IDs, parent/child links, explicit statuses, and evidence/coverage links
  Do not silently generate downstream artifacts, expand scope, or claim readiness without terminal evidence
  Stop and report the exact blocker for missing parent, approval, evidence, ownership, or required capability
  Do not assume npm, GitHub, Azure, credentials, or a particular test runner
}
