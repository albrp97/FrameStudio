---
name: aidd-fix
description: Diagnose and fix a bug or review finding with scoped regression evidence, repository-specific gates, and configurable delivery operations. Use when behavior is broken or review identified an actionable defect.
compatibility: Requires git and the repository's discovered test or verification tooling.
---

import ../lifecycle-interface.md

# aidd-fix

```sudolang
Lifecycle {
  profile = implementationMutation
}
```

Diagnose one bug or review finding, prove the protected behavior baseline,
implement the smallest scoped fix, and leave a reproducible evidence trail.

Apply [../development-mode.md](../development-mode.md) when selecting
validation, approval, and continuation behavior.

## Step 1 - Gain context and validate

1. Read the relevant source and colocated tests or verification artifacts.
2. Read `.github/aidd-config.yml`, repository rules, current branch/worktree,
   intended base, and the active phase, feature, and ticket records.
3. Confirm the issue by reproducing it or tracing the cited behavior.
4. If the issue is absent, report the finding and stop without changing files.
5. Confirm that the requested fix stays inside the ticket scope; unrelated
   findings become follow-up work.

## Step 2 - Document the requirement

1. Locate the owning phase and feature.
2. Create or update one focused ticket only when the repository workflow
   requires a planning artifact.
3. Express the corrected behavior as `Given X, should Y`.
4. Add protected flows, affected surfaces, non-goals, and the evidence path.

## Step 3 - Establish baseline and regression evidence

1. Discover the repository's test and quality commands from config, manifests,
   scripts, CI, and contribution guidance.
2. Run protected automated flows and applicable agent-owned smoke, baseline,
   unit, regression, fixture, acquisition, contract, integration, migration,
   security, static-analysis, deployment, and quality checks before
   implementation when configured.
3. Record baseline results and pre-existing failures with `/evidence`.
4. Define an executable automated functionality test for every affected
   acceptance outcome, including its supported boundary and assertions.
5. Write a failing regression test for code behavior, or document the strongest
   non-code verification plan for another ticket category.
6. Run the focused check and confirm the expected failure.

## Step 4 - Implement the fix

1. Change only what is needed to satisfy the regression requirement.
2. Rerun the focused check until it passes.
3. Rerun affected protected flows and the strongest real-system flow for API,
   persistence, integration, worker, or user-facing changes.
4. Run all configured local quality gates and applicable agent-owned technical
   checks for the affected surfaces.
5. Run the executable automated functionality test for every affected
   acceptance outcome as the final acceptance-level technical check. A
   unit/regression test or narrated manual flow does not satisfy this gate.
6. Record technical checks and functionality results separately, including
   commands, results, artifacts, failures, fixes, and coverage gaps.

## Step 5 - Review and gate

1. In guided mode, generate and present the functionality-only copy/paste-ready
   user-validation handoff required by `aidd-user-testing`; technical checks
   must already be terminal and must not be included as user instructions.
   Keep the ticket in `verifying` while awaiting the user's functionality
   result. In automatic mode, run the same functionality charter as the agent
   through the exact Rubber Duck `gpt-5.6-luna` high-reasoning
   `all-validation` profile, and record `automaticValidation` without asking
   or waiting.
2. In guided mode, append the user's terminal `PASS`, `FAIL`, `BLOCKED`, or
   approved `NOT APPLICABLE` response to the evidence record before review.
   In automatic mode, append the terminal automatic-validation result.
3. Run `/review` against the active context and final diff. When this fix was
   invoked by the review remediation loop, run only the focused verification
   requested by the parent and return to that parent; do not recursively start
   another full review/remediation loop.
4. Confirm that configured end-to-end, security, migration, contract, and
   remote checks have agent-owned terminal evidence; rerun affected checks
   after any review remediation. Do not infer them from unit success or ask the
   user to run them.
5. Separate blockers, accepted warnings, and follow-up work.
6. Stop if any required gate, including automated functionality, lacks terminal
   evidence.

## Step 6 - Commit and deliver

Use `/commit` only after the staged-scope review, readiness summary, terminal
technical evidence, mode-appropriate validation evidence, and configured
approval are satisfied. In automatic mode, bootstrap authorization supplies
routine approval; configured provider, branch, credential, remote-check, merge,
and unavailable-tool gates remain binding. Then use `/push` only when the
successful commit is unpublished or ahead of its configured upstream. Use
`/aidd-pr` only after the source branch is published and pull-request policy
requires a PR, or to recheck the existing PR after a new push. Never embed a
provider, reviewer, or credential assumption in this workflow.

These are autonomous delivery conditions. If the user explicitly directs a
commit or push earlier, route to `aidd-commit` or `aidd-push`, warn once, and
record bypassed gates instead of refusing the operation or treating readiness
as passed.

Keep the ticket in its configured open pre-delivery status until the commit,
push, PR, merge, or local-delivery policy is satisfied. The lifecycle owner,
not the fix skill, performs the final open-to-closed record move.

```sudolang
fix = gainContext
  |> documentRequirement
  |> baselineAndRegression
  |> implementScopedFix
  |> verifyAndGate
  |> review
  |> commit
  |> pushWhenRequired
  |> prWhenRequired
  |> configuredCloseout
```

## Constraints

```sudolang
Constraints {
  Do one step at a time and do not reorder the process
  Never implement code behavior before its failing regression test
  Never conceal baseline failures
  Never claim a command or flow passed without evidence
  Never treat a unit/regression test or manual narration as the required
    automated functionality test
  Never ask the user to run smoke, baseline, unit, regression, fixture,
    acquisition, contract, integration, migration, security, static-analysis,
    formatter, lint, type-check, build, deployment, or other technical checks
  Treat guided user validation as confirmation of delivered functionality only;
    automaticValidation is agent-owned and never human confirmation
  Never close or gate a fix ticket without terminal automated functionality
    evidence when the functionality gate is enabled
  Never run a repository command that was not discovered or configured
  Never autonomously commit, push, resolve, or merge outside configured policy;
    explicit user commit and push directives use the delivery override policy
  Never push as an implicit side effect of commit or PR preparation
  Never create a PR for an unpublished branch
  Never expand scope to unrelated findings
  Never close or report a guided fix as done while required user validation or
    configured delivery closeout is pending
  Never close or report an automatic fix as done while required
    automaticValidation or configured delivery closeout is pending
  Never classify automatic verification, review, or closeout without the exact
    Rubber Duck `gpt-5.6-luna` high-reasoning `all-validation` profile
  If blocked, report the exact missing decision, capability, or gate
}
```
