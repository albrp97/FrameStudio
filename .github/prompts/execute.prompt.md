---
agent: agent
description: "AIDD /execute — implement one approved ticket with repository-specific baseline, verification, evidence, and quality gates."
---

# ⚙️ Execute

Act as a senior software engineer using the ticket execution methodology in
[aidd-ticket-creator](../skills/aidd-ticket-creator/SKILL.md) and the test and
verification methodology in [aidd-tdd](../skills/aidd-tdd/SKILL.md).
Use [aidd-user-testing](../skills/aidd-user-testing/SKILL.md) for the
post-implementation validation handoff.
Respect [aidd-evidence](../skills/aidd-evidence/SKILL.md) and the general
constraints in [aidd-please](../skills/aidd-please/SKILL.md).
Resolve `delivery.development.mode` from `.github/aidd-config.yml` before
choosing the validation path. In automatic mode, all validation uses the exact
Rubber Duck profile `rubber-duck`, `gpt-5.6-luna`, high reasoning, and
`all-validation` scope.

Process {
  1. Read `.github/aidd-config.yml`, the approved phase, feature, and ticket,
     repository map, scope/capability links, repository rules, manifests, and
     CI.
  2. Verify branch, worktree, intended base, scope, non-goals, dependencies,
     active-phase ownership, affected surfaces, and required gates.
  3. Run `/run-preimplementation-checklist` when the ticket is part of a
     non-trivial planning hierarchy.
  4. Establish and record the protected baseline when configured.
  5. Use code TDD or the strongest applicable verification method for the
     ticket category.
  6. Define and implement at least one executable automated functionality test
     for every acceptance outcome, crossing the supported system boundary.
  7. Run discovered agent-owned technical checks and local quality gates,
     including smoke, regression, contract, fixture, acquisition, security,
     static-analysis, and other applicable checks; append every result to
     evidence. In automatic mode, have the Rubber Duck validator orchestrate or
     inspect each result and record the exact `rubber-duck` / `gpt-5.6-luna` /
     high / `all-validation` profile.
  8. Run `/run-test` as the final acceptance-level automated check. It must
     execute the automated functionality test and leave all applicable
     technical checks terminal; stop when a command, assertion, or required
     service cannot run.
  9. Stop on a failed required gate, missing prerequisite, or blocker.
  10. In guided mode, generate and present a copy/paste-ready
      functionality-only user-validation handoff with exact setup, data, user
      actions, expected visible and persisted/external results,
      user-observable failure behavior, cleanup, evidence requirements, and
      pass criteria. Do not include technical commands or ask the user to run
      them.
  11. In guided mode, keep the ticket in `verifying` and wait for the user's
      `PASS`, `FAIL`, `BLOCKED`, or approved `NOT APPLICABLE` response; append
      the result to `/evidence`. In automatic mode, run the same functionality
      charter through the Rubber Duck validator, append `automaticValidation`
      with the exact `rubber-duck` / `gpt-5.6-luna` / high /
      `all-validation` profile, and continue without asking or waiting.
  12. If the mode-appropriate result is `FAIL` or `BLOCKED`, keep the ticket
      open and route the smallest fix, follow-up, or change-control decision.
  13. Run `/review` after mode-appropriate validation is terminal and before
      commit or moving to another ticket.
  14. Only after terminal technical evidence, automated functionality evidence,
      mode-appropriate validation (`userValidation` in guided mode or
      `automaticValidation` in automatic mode), review, and configured
      approval, set the ticket to the configured pre-delivery status such as
      `gated`; keep the same record in `open`, synchronize its current path,
      and recommend `/commit`.
  15. Do not move the ticket record to `closed` until the configured commit,
      push, pull-request, merge, or local-delivery policy is satisfied. The
      commit, push, and PR skills own their operations; the lifecycle owner
      performs the final status/path move and synchronizes the backlog and
      parent record.
  16. End with exactly one `Next step`, `Skill`, and `Why` handoff naming the
      first permitted delivery operation.
}

Constraints {
  Execute only the current approved ticket.
  Do not use generic npm, Vitest, Riteway, browser, or service commands without
  repository evidence.
  Do not autonomously commit or push before configured readiness checks and
  evidence exist. A confirmed explicit user directive is handled by
  `aidd-commit` or `aidd-push` with bypass warnings recorded.
  Do not create a PR before the source branch is published.
  Do not turn unavailable coverage into a successful result.
  Do not treat unit or regression tests as a substitute for the required
    automated functionality test.
    Do ONE ticket at a time and use the configured approval mode before moving on
      in guided mode; automatic mode uses verified bootstrap authorization.
    Do not report a guided ticket as done or close it while user validation or
      configured delivery closeout is pending.
    Do not report an automatic ticket as done or close it while
      automaticValidation, the exact Rubber Duck validation profile, or
      configured delivery closeout is pending.
    Agent-run technical checks and tests do not replace guided user
      functionality confirmation, but the user must not be asked to rerun them.
  Keep ticket status and folder classification aligned; reopening moves the
  record back to `open` before new implementation work.
}
