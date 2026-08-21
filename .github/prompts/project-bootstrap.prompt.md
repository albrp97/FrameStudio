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
Show inferred values, TBDs, source basis, and overwrite risks. Do not write any
file until I explicitly approve the complete draft. After approval, write only
the approved foundational artifacts and hand off to planning-bootstrap without
creating capabilities, phases, features, or tickets.
"""

Constraints {
  Treat paths as repository-relative and read `.github/aidd-config.yml` when present
  Preserve existing authoritative planning sources and project instructions
  Keep vision, AGENTS.md, README.md, and generic .github policy as separate concerns
  Never silently overwrite existing files or create downstream planning children
  Never invent commands, architecture, users, constraints, evidence, or success criteria
  Never store credentials, tokens, private keys, cookies, or sensitive data
  Stop on missing approval, contradiction, unresolved overwrite choice, or missing evidence
}
