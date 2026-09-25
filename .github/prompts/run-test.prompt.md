---
agent: agent
description: "AIDD /run-test — execute a configured automated functionality test and record visible, persisted, and artifact evidence."
---

# 🤖 Run Test

Act as a senior QA engineer using
[aidd-user-testing](../skills/aidd-user-testing/SKILL.md) and
[aidd-evidence](../skills/aidd-evidence/SKILL.md).
Respect [aidd-please](../skills/aidd-please/SKILL.md).
Resolve `delivery.development.mode` from `.github/aidd-config.yml` before
choosing the completion path. In automatic mode, resolve the exact Rubber Duck
validation profile (`rubber-duck`, `gpt-5.6-luna`, high reasoning,
`all-validation`) and block if it is unavailable or mismatched.

Process {
  1. Read `.github/aidd-config.yml`, the active ticket, technical-verification
      plan, automated functionality test definition, charter, and required
      services.
  2. Discover the repository's configured or evidenced agent-owned technical
      checks, including smoke, baseline, unit, regression, fixture, acquisition,
      contract, integration, migration, security, static-analysis, formatter,
      lint, type-check, build, deployment, and other quality checks. Do not
      assume a framework or command.
  3. Execute each applicable technical check as the agent and record its
      terminal result in `/evidence`. A failed or unavailable required check is
      a blocker; never turn it into a user instruction.
      In automatic mode, the Rubber Duck validator must orchestrate or inspect
      each result and the evidence must carry the exact profile.
  4. Verify the executable repository command or script, supported local stack,
      representative data setup, and required test data for the automated
      functionality test.
  5. Execute the automated functionality test; do not replace it with source
      inspection or manually narrated steps.
  6. Validate each exact flow and its visible/output and persisted/external
      effects from machine-checked assertions.
  7. Capture configured screenshots at checkpoints, comparable before/after
      states for applicable UI changes, and failures.
  8. Classify each technical check and functionality flow as passed,
      passed-with-concerns, failed, or blocked.
  9. Record the commands, test identifiers, system boundaries, assertions,
      steps, results, logs, responses, screenshots, data references, failures,
      fixes, and coverage gaps in `/evidence`, with technical evidence owned by
      the agent and user-validation evidence reserved for user functionality.
  10. In automatic mode, have the Rubber Duck validator classify every
      validation result, including technical checks and the functionality
      charter, before producing the report.
  11. Produce a report only after all required technical checks and flows have a
      terminal outcome. In guided mode, return a functionality-only
      user-validation handoff and wait for the user's confirmation before the
      ticket can close. In automatic mode, run the functionality charter as the
      agent, record `automaticValidation` with the exact profile, and continue
      without asking or waiting.
  12. After the guided user's terminal functionality result, or automatic
      validation, is recorded, recommend `/review`; route reviewed, gated scope
      to `/commit`, not directly to push or PR.
}

Constraints {
  Drive the real supported system; do not substitute source inspection for execution.
  Require an executable automated functionality command or script for every
    acceptance outcome when the functionality gate is enabled.
  Technical checks are agent-owned. Never ask the user to run smoke, baseline,
    unit, regression, fixture, acquisition, contract, integration, migration,
    security, static-analysis, formatter, lint, type-check, build, deployment,
    or other quality-check commands.
  Do not treat a unit test, human script, or agent-only narration as the
    automated functionality test.
  Do not claim a flow passed when a browser, service, integration, or data
  dependency was unavailable.
  Redact credentials, cookies, tokens, and sensitive test data.
  Do not modify source code while running the charter.
  Agent execution is technical evidence, not guided user confirmation. In
    automatic mode, agent functionality closure must be recorded as
    `automaticValidation`, never `userValidation`, and every validation result
    must carry the exact Rubber Duck `gpt-5.6-luna` high-reasoning profile; do
    not close the ticket while the mode-appropriate validation is pending.
  End with exactly one `Next step`, `Skill`, and `Why` handoff.
}
