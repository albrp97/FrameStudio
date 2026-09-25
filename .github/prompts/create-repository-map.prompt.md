---
agent: agent
description: "/create-repository-map — map repository surfaces and ownership"
---

# Create-Repository-Map

Use [../skills/aidd-create-repository-map/SKILL.md](../skills/aidd-create-repository-map/SKILL.md) as the executable contract.

userPrompt = """
Create or update the repository map from observable directories, manifests, guidance, commands, integrations, and ownership evidence. Link every assertion to a repository-relative source path. Preserve stable map identifiers and mark stale or unknown entries; do not derive capabilities, phases, features, or tickets.
After authorization, persist the approved map to the configured
`delivery.artifacts.repository_map` path with repository file operations,
re-read the path, and report the verified write result. A map printed in the
response is not a saved artifact. Use `draft` for a read-only proposal and
`write` for a previously approved map. Every created or updated result
requires a host file create/edit tool call and read-back verification.
If `write` has no recoverable approved map, report a blocker instead of
reconstructing or writing one.
"""

Constraints {
  Treat paths as repository-relative and read `.github/aidd-config.yml` when present
  Use canonical objective -> scope -> capability -> phase -> feature -> ticket ancestry
  Use adaptive depth, stable IDs, parent/child links, explicit statuses, and evidence/coverage links
  Do not silently generate downstream artifacts, expand scope, or claim readiness without terminal evidence
  Do not stop at a response-only map when a write is authorized
  Verify the configured repository-map path after writing
  Report failed or unavailable writes as blockers
  Stop and report the exact blocker for missing parent, approval, evidence, ownership, or required capability
  Do not assume npm, GitHub, Azure, credentials, or a particular test runner
}
