---
agent: agent
description: "/create-capability-map — derive capabilities from approved context"
---

# Create-Capability-Map

Use [../skills/aidd-create-capability-map/SKILL.md](../skills/aidd-create-capability-map/SKILL.md) as the executable contract.

userPrompt = """
Using an approved objective and scope plus a current repository map, derive a capability map. Assign stable CAP IDs, affected surfaces, dependencies, risks, evidence/coverage gaps, and ancestry links. Persist the approved map to the configured `delivery.artifacts.capability_map` path with repository file operations, re-read it to verify the write, and report the actual path/result. Stop for missing approval or contradictory evidence and request approval before any phase or feature generation. A map printed in the response without a successful file operation is only a draft. Use `draft` for a read-only proposal and `write` for a previously approved map.
Every created or updated result requires a host file create/edit tool call and
read-back verification.
If `write` has no recoverable approved map, report a blocker instead of
reconstructing or writing one.
"""

Constraints {
  Treat paths as repository-relative and read `.github/aidd-config.yml` when present
  Use canonical objective -> scope -> capability -> phase -> feature -> ticket ancestry
  Use adaptive depth, stable IDs, parent/child links, explicit statuses, and evidence/coverage links
  Do not silently generate downstream artifacts, expand scope, or claim readiness without terminal evidence
  Do not stop at a response-only capability map when a write is authorized
  Verify the configured capability-map path after writing
  Report failed or unavailable writes as blockers
  Stop and report the exact blocker for missing parent, approval, evidence, ownership, or required capability
  Do not assume npm, GitHub, Azure, credentials, or a particular test runner
}
