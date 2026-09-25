---
agent: agent
description: "/project-bootstrap — create approved foundational project context"
---

# Project-Bootstrap

Use [../skills/aidd-project-bootstrap/SKILL.md](../skills/aidd-project-bootstrap/SKILL.md) as the executable contract.

userPrompt = """
Bootstrap this repository's durable project context. Inspect the repository and
existing sources of truth, resolve configured artifact paths, and ask me one
focused question at a time about the project's purpose, users, desired
outcomes, scope, non-goals, durable constraints, supported environments,
quality/security expectations, and agent conventions. Reuse existing answers
and repository evidence. Draft a file-by-file proposal for vision.md,
AGENTS.md, repository mapping, scope, configuration, and an optional README.
During the bootstrap interview, ask me to choose exactly one development mode:
`guided` (keep the existing approval gates and functionality-only user
validation) or `automatic` (after the approved foundational write, continue
through mapping, planning, TDD, technical verification, automated
functionality, review/remediation, delivery, and remaining phases without
asking or waiting for another response). Persist the selected value as
`delivery.development.mode` in `.github/aidd-config.yml` and mirror it in
`vision.md` and project-specific `AGENTS.md`. For automatic mode, persist and
mirror the exact validation profile `rubber-duck`, model `gpt-5.6-luna`,
reasoning effort `high`, and scope `all-validation` under
`delivery.development.automatic_validation`.
Show inferred values, TBDs, source basis, and overwrite risks. Do not write any
file until I explicitly approve the complete draft. After approval, write only
the approved foundational artifacts with repository file operations, re-read
each written path to verify it, report the actual created/updated/unchanged or
blocked result for every path, and hand off to planning-bootstrap without
creating capabilities, phases, or tickets as part of the foundational write.
A response containing proposed file contents is not a write; each created or
updated result requires a host file create/edit tool call and read-back
verification. If the selected mode is `automatic`, start the orchestrator's
automatic development loop after the verified planning-bootstrap handoff and
do not ask or wait for another user response. If I invoke `draft` or
`status`, remain read-only.
If `write` is invoked without a recoverable approved draft, report a blocker
instead of reconstructing or writing new content.
"""

Constraints {
  Treat paths as repository-relative and read `.github/aidd-config.yml` when present
  Preserve existing authoritative planning sources and project instructions
  Keep vision, AGENTS.md, README.md, and generic .github policy as separate concerns
  Require and persist one development mode: guided or automatic
  Treat `.github/aidd-config.yml:delivery.development.mode` as the canonical
    machine-readable value and mirror it in vision and AGENTS
  Treat `.github/aidd-config.yml:delivery.development.automatic_validation`
    as the canonical automatic validation profile and mirror it in vision and
    AGENTS when automatic mode is selected
  Never silently overwrite existing files or create downstream planning children
  Never stop after printing approved file contents; use the file-writing tool
  Verify every approved write by reading the resulting repository path
  Report a failed or unavailable write as blocked, not created
  In automatic mode, after verified bootstrap never ask follow-up questions or
    wait for user validation; stop only for a precise real blocker
  Never record automatic agent validation as user confirmation
  Never invent commands, architecture, users, constraints, evidence, or success criteria
  Never store credentials, tokens, private keys, cookies, or sensitive data
  Stop on missing approval, contradiction, unresolved overwrite choice, or missing evidence
}
