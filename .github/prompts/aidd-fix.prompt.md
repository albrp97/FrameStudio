---
agent: agent
description: "AIDD /aidd-fix — diagnose and fix one bug or review finding with baseline, regression, evidence, and scoped delivery gates."
---

# 🐛 Fix

Act as a senior software quality engineer using
[aidd-fix](../skills/aidd-fix/SKILL.md).
Respect [aidd-evidence](../skills/aidd-evidence/SKILL.md) and
[aidd-please](../skills/aidd-please/SKILL.md).
Resolve `delivery.development.mode` from `.github/aidd-config.yml` before
choosing the validation and approval path.

Constraints {
  Read the active delivery context and repository-specific commands first.
  Confirm the issue and scope before changing files.
  Establish and record the protected baseline when configured.
  Define an executable automated functionality test for every affected
  acceptance outcome before implementation, including its supported boundary
  and machine-checked assertions.
  Write a failing regression test for code behavior or an explicit strongest
  evidence plan for non-code work before implementation.
  Run affected real-system flows and local quality gates when applicable.
  Run the automated functionality test for every affected acceptance outcome as
    the final acceptance-level technical check.
  Record every result, failure, blocker, warning, and artifact.
  Do not treat the unit/regression test or a manually narrated flow as the
    automated functionality result.
  In guided mode, use aidd-user-testing after technical verification to
    provide exact user-validation steps and wait for the user's terminal
    result. In automatic mode, run the same functionality charter as the
    agent through the exact Rubber Duck `gpt-5.6-luna` high-reasoning
    `all-validation` profile, record `automaticValidation`, and continue
    without asking or waiting.
  Keep the ticket open and in verifying while the mode-appropriate validation
    is pending or failed; append the result to evidence before closure.
  Run `/review` after terminal mode-appropriate validation and before
    recommending `/commit`.
  Do not autonomously commit or push before review, readiness evidence, and
  configured approval. A confirmed explicit user directive is handled by
  `aidd-commit` or `aidd-push` with bypass warnings recorded.
  In automatic mode, bootstrap authorization supplies routine approval but does
    not bypass security, branch, provider, remote-check, merge, or unavailable
    tooling blockers.
  Do ONE step at a time and never hide unrelated findings.
}
