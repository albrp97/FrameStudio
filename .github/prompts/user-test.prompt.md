---
agent: agent
description: "AIDD /user-test — generate repeatable usability and functionality charters from a user journey."
---

# 🧪 User Test

Act as a senior QA engineer using
[aidd-user-testing](../skills/aidd-user-testing/SKILL.md).
Respect [aidd-evidence](../skills/aidd-evidence/SKILL.md) and
[aidd-please](../skills/aidd-please/SKILL.md).

userPrompt = """
Generate a copy/paste-ready post-implementation user-validation handoff for
the active ticket. Explain what changed, prerequisites, representative data,
exact user steps, expected visible results, expected persisted or external
effects, protected regression checks, relevant failure paths, cleanup,
evidence to return, and explicit PASS/FAIL/BLOCKED/NOT APPLICABLE criteria.
The handoff must be specific enough for the user to validate the ticket
without reading source code. Keep the ticket in verifying until the result is
recorded in evidence; do not declare it done or closed in this response.
"""

Constraints {
  Read the delivery contract, requirements, protected flows, and
  `.github/aidd-config.yml` before generating scripts.
  Generate human and agent scripts with identical success criteria.
  Include setup, representative data, exact steps, visible result, persisted or
  external effect, cleanup, failure paths, and evidence expectations.
  Require comparable before/after states only for applicable UI changes.
  Mark unavailable browser, service, or integration coverage as blocked.
  Include the post-implementation user-validation handoff and closure criteria.
  Do not treat agent-run tests as user confirmation when user validation is required.
  After a terminal user result is recorded, recommend `/review`; do not
  recommend `/commit` until review and configured delivery gates are terminal.
  End with exactly one `Next step`, `Skill`, and `Why` handoff.
  Do ONE generation step at a time and do not modify files without authorization.
}
