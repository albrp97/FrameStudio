---
agent: agent
description: "/create-tickets — create focused verifiable tickets"
---

# Create-Tickets

Use [../skills/aidd-create-tickets/SKILL.md](../skills/aidd-create-tickets/SKILL.md) as the executable contract.
Read `delivery.development.mode` from `.github/aidd-config.yml`. Guided mode
waits for ticket approval; automatic mode records bootstrap-authorized
approval after verified writes, validates it through the exact `rubber-duck` /
`gpt-5.6-luna` / high-reasoning / `all-validation` profile, and continues to
execution without asking or waiting.

userPrompt = """
Decompose exactly one approved feature into independently verifiable tickets. Enforce one parent feature, explicit scope/non-goals, stable TICKET IDs, requirements and protected-behavior traceability, dependencies, gates, commands/steps, evidence path, ownership, and definition of done. Reject oversized or cross-feature tickets and stop on missing baseline or approval; in automatic mode, use bootstrap-authorized approval but still stop on missing baseline or evidence; do not implement.
"""

Constraints {
  Treat paths as repository-relative and read `.github/aidd-config.yml` when present
  Read the backlog and both `ticket_open_directory` and `ticket_closed_directory`
  from the configuration; create new ticket files in open
  Move the same ticket file to closed for an authorized terminal status, and back to open when reopened
  Keep the backlog synchronized with current paths and preserve stable IDs/path history
  Use canonical objective -> scope -> capability -> phase -> feature -> ticket ancestry
  Use adaptive depth, stable IDs, parent/child links, explicit statuses, and evidence/coverage links
  Do not silently generate downstream artifacts, expand scope, or claim readiness without terminal evidence
  Stop and report the exact blocker for missing parent, approval, evidence, ownership, or required capability
  In automatic mode, do not ask for ticket approval or wait for a user response;
    validate ticket readiness through the exact `rubber-duck` /
    `gpt-5.6-luna` / high-reasoning / `all-validation` profile and route ready
    tickets to preimplementation and execution
  Do not assume npm, GitHub, Azure, credentials, or a particular test runner
}
