---
agent: agent
description: "/create-phases — sequence outcome-oriented phases"
---

# Create-Phases

Use [../skills/aidd-create-phases/SKILL.md](../skills/aidd-create-phases/SKILL.md) as the executable contract.
Read `delivery.development.mode` from `.github/aidd-config.yml`. Guided mode
waits for phase approval; automatic mode records the bootstrap-authorized
decision after a verified write, validates it through the exact `rubber-duck` /
`gpt-5.6-luna` / high-reasoning / `all-validation` profile, and continues
without asking or waiting.

userPrompt = """
Plan phases for the approved objective, scope, and capability map. Select adaptive depth, then give each PHASE ID a meaningful outcome, entry conditions, exit conditions, sequence, dependencies, status, capability links, and evidence expectations. In guided mode, do not create features or tickets until the phase is approved and unblocked. In automatic mode, create and verify the phase, record bootstrap-authorized approval, and continue to feature planning.
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
  In automatic mode, do not ask for phase approval or wait for a user response;
    validate phase readiness through the exact `rubber-duck` /
    `gpt-5.6-luna` / high-reasoning / `all-validation` profile and do not
    bypass missing parents, entry conditions, or evidence
  Do not assume npm, GitHub, Azure, credentials, or a particular test runner
}
