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
  6. Exercise real-system functionality for API, persistence, integration,
     worker, or user-facing changes when required.
  7. Run discovered local quality gates and append every result to evidence.
  8. Stop on a failed required gate, missing prerequisite, or blocker.
  9. Generate and present a copy/paste-ready user-validation handoff with
      exact setup, data, steps, expected visible and persisted/external
      results, failure paths, cleanup, evidence requirements, and pass criteria.
  10. Keep the ticket in `verifying` and wait for the user's `PASS`, `FAIL`,
      `BLOCKED`, or approved `NOT APPLICABLE` response; append the result to
      `/evidence`.
  11. If the result is `FAIL` or `BLOCKED`, keep the ticket open and route the
      smallest fix, follow-up, or change-control decision.
  12. Run `/review` after terminal user validation and before commit or moving
      to another ticket.
  13. Only after terminal technical evidence, required user-validation evidence
      or approved not-applicable evidence, review, and configured approval, set
      the ticket to the configured pre-delivery status such as `gated`; keep
      the same record in `open`, synchronize its current path, and recommend
      `/commit`.
  14. Do not move the ticket record to `closed` until the configured commit,
      push, pull-request, merge, or local-delivery policy is satisfied. The
      commit, push, and PR skills own their operations; the lifecycle owner
      performs the final status/path move and synchronizes the backlog and
      parent record.
  15. End with exactly one `Next step`, `Skill`, and `Why` handoff naming the
      first permitted delivery operation.
}

Constraints {
  Execute only the current approved ticket.
  Do not use generic npm, Vitest, Riteway, browser, or service commands without
  repository evidence.
  Do not commit or push before configured readiness checks and evidence exist.
  Do not create a PR before the source branch is published.
  Do not turn unavailable coverage into a successful result.
  Do ONE ticket at a time and use the configured approval mode before moving on.
  Do not report the ticket as done or close it while user validation or
  configured delivery closeout is pending.
  Agent-run tests do not replace required user confirmation.
  Keep ticket status and folder classification aligned; reopening moves the
  record back to `open` before new implementation work.
}
