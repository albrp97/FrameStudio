---
name: aidd-fix
description: Diagnose and fix a bug or review finding with scoped regression evidence, repository-specific gates, and configurable delivery operations.
compatibility: Requires git and the repository's discovered test or verification tooling.
---

# aidd-fix

Diagnose one bug or review finding, prove the protected behavior baseline,
implement the smallest scoped fix, and leave a reproducible evidence trail.

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
2. Run protected automated and functionality flows before implementation when
   configured.
3. Record baseline results and pre-existing failures with `/evidence`.
4. Write a failing regression test for code behavior, or document the strongest
   non-code verification plan for another ticket category.
5. Run the focused check and confirm the expected failure.

## Step 4 - Implement the fix

1. Change only what is needed to satisfy the regression requirement.
2. Rerun the focused check until it passes.
3. Rerun affected protected flows and the strongest real-system flow for API,
   persistence, integration, worker, or user-facing changes.
4. Record commands, results, artifacts, failures, fixes, and coverage gaps.

## Step 5 - Review and gate

1. Run `/review` against the active context and final diff. When this fix was
   invoked by the review remediation loop, run only the focused verification
   requested by the parent and return to that parent; do not recursively start
   another full review/remediation loop.
2. Run all configured local quality gates applicable to the affected surfaces.
3. Apply the configured end-to-end, security, migration, contract, and remote
   checks; do not infer them from unit success.
4. Separate blockers, accepted warnings, and follow-up work.
5. Stop if any required gate lacks terminal evidence.
6. Generate and present the copy/paste-ready user-validation handoff required
   by `aidd-user-testing`; keep the ticket in `verifying` while awaiting the
   user's result.
7. Append the user's terminal `PASS`, `FAIL`, `BLOCKED`, or approved
   `NOT APPLICABLE` response to the evidence record before closure.

## Step 6 - Commit and deliver

Use `/commit` only after the staged-scope review, readiness summary, terminal
technical evidence, required user-validation evidence, and configured approval
are satisfied. Then use `/push` only when the successful commit is unpublished
or ahead of its configured upstream. Use `/aidd-pr` only after the source
branch is published and pull-request policy requires a PR, or to recheck the
existing PR after a new push. Never embed a provider, reviewer, or credential
assumption in this workflow.

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
  Never run a repository command that was not discovered or configured
  Never commit, push, resolve, or merge outside configured policy
  Never push as an implicit side effect of commit or PR preparation
  Never create a PR for an unpublished branch
  Never expand scope to unrelated findings
  Never close or report the fix as done while required user validation or
    configured delivery closeout is pending
  If blocked, report the exact missing decision, capability, or gate
}
```
