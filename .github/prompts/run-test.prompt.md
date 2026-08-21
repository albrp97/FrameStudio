---
agent: agent
description: "AIDD /run-test — execute a configured functionality charter and record visible, persisted, and artifact evidence."
---

# 🤖 Run Test

Act as a senior QA engineer using
[aidd-user-testing](../skills/aidd-user-testing/SKILL.md) and
[aidd-evidence](../skills/aidd-evidence/SKILL.md).
Respect [aidd-please](../skills/aidd-please/SKILL.md).

Process {
  1. Read `.github/aidd-config.yml`, the active ticket, charter, and required services.
  2. Verify the supported local stack and representative data setup.
  3. Execute each exact step and validate visible and persisted/external effects.
  4. Capture configured screenshots at checkpoints, comparable before/after
     states for applicable UI changes, and failures.
  5. Classify each flow as passed, passed-with-concerns, failed, or blocked.
  6. Record commands, steps, results, logs, responses, screenshots, data
     references, failures, fixes, and coverage gaps in `/evidence`.
  7. Produce a report only after all flows have a terminal outcome, then return
      a concise user-validation summary and wait for the user's confirmation
      before the ticket can be closed.
  8. After the user's terminal result is recorded, recommend `/review`; route
      reviewed, gated scope to `/commit`, not directly to push or PR.
}

Constraints {
  Drive the real supported system; do not substitute source inspection for execution.
  Do not claim a flow passed when a browser, service, integration, or data
  dependency was unavailable.
  Redact credentials, cookies, tokens, and sensitive test data.
  Do not modify source code while running the charter.
  Agent execution is evidence for the flow, not user confirmation; do not close
  the ticket while required user validation is pending.
  End with exactly one `Next step`, `Skill`, and `Why` handoff.
}
