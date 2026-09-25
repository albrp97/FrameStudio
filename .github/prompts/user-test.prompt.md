---
agent: agent
description: "AIDD /user-test — generate a functionality-only user-validation handoff from a user journey."
---

# 🧪 User Test

Act as a senior QA engineer using
[aidd-user-testing](../skills/aidd-user-testing/SKILL.md).
Respect [aidd-evidence](../skills/aidd-evidence/SKILL.md) and
[aidd-please](../skills/aidd-please/SKILL.md).
Read `delivery.development.mode` from `.github/aidd-config.yml`. This prompt
is a guided-mode handoff; in automatic mode do not present it or wait for a
user response. Run the same charter through `/run-test` and record
`automaticValidation` through the exact Rubber Duck `gpt-5.6-luna`
high-reasoning `all-validation` profile instead.

userPrompt = """
In guided mode, generate a copy/paste-ready post-implementation user-validation handoff for
the active ticket. Explain only the delivered functionality: what changed,
prerequisites, representative data, exact user actions, expected visible
results, expected persisted or external effects, user-observable failure
behavior, cleanup, evidence to return, and explicit PASS/FAIL/BLOCKED/NOT
APPLICABLE criteria.

Before presenting the handoff, run and record all applicable agent-owned
technical verification yourself, including smoke, baseline, unit, regression,
fixture, acquisition, contract, integration, migration, security,
static-analysis, formatter, lint, type-check, build, deployment, and other
quality checks. Also run the executable automated functionality test for every
acceptance outcome. Do not put those commands, scripts, technical diagnostics,
or protected regression checklists in the user handoff, and do not ask the user
to rerun them. If a required technical check or automated functionality test
fails or is unavailable, report the blocker instead of presenting it as a user
task.

The handoff must be specific enough for the user to validate the functionality
without reading source code. Keep the ticket in verifying until the user's
functionality result is recorded in evidence; do not declare it done or closed
in this response.
In automatic mode, this prompt is not a waiting point; route directly to
`/run-test`, then `/review` after terminal `automaticValidation`.
"""

Constraints {
  Read the delivery contract, requirements, protected flows, and
  `.github/aidd-config.yml` before generating scripts.
  Define one executable automated functionality test per acceptance outcome and
    run it before the handoff.
  Run applicable technical verification as the agent and record it separately.
  Include only functionality setup, representative data, exact user actions,
    visible result, persisted or external effect, cleanup, user-observable
    failure behavior, and evidence expectations in the handoff.
  Never include smoke, baseline, unit, regression, fixture, acquisition,
    contract, integration, migration, security, static-analysis, formatter,
    lint, type-check, build, deployment, or other technical-check instructions
    for the user.
  Require comparable before/after states only for applicable UI changes.
  Mark unavailable browser, service, or integration automation as blocked.
  Do not treat a unit test, human script, or agent-only manual charter as the
    required automated functionality test.
  Include the post-implementation user-validation handoff and closure criteria
    in guided mode.
  Do not treat agent-run tests as user confirmation when user validation is
    required in guided mode, but do not ask the user to rerun agent-owned
    technical checks.
  Never use this prompt to ask or wait for a user in automatic mode
  After a terminal user result is recorded, recommend `/review`; do not
  recommend `/commit` until review and configured delivery gates are terminal.
  End with exactly one `Next step`, `Skill`, and `Why` handoff.
  Do ONE generation step at a time and do not modify files without authorization.
}
