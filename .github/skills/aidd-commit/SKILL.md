---
name: aidd-commit
description: Create a scoped conventional commit after readiness checks, or honor a confirmed explicit user directive with bypassed gates recorded as warnings. Use when local changes must become an auditable commit.
compatibility: Requires git and the repository's discovered commit policy.
---

import ../lifecycle-interface.md

# Commit Delivery

```sudolang
Lifecycle {
  profile = deliveryCommit
}
```

Create one auditable local commit for the active ticket. A commit is a
version-control checkpoint, not proof that the ticket has been delivered:
push, pull-request, remote checks, merge, and lifecycle closeout remain
separate operations.

Apply [../development-mode.md](../development-mode.md) when evaluating the
validation and approval prerequisites.

## Context

Read `.github/aidd-config.yml`, the active phase, feature, and ticket records,
the evidence record, repository contribution guidance, the current branch, and
the staged diff. Repository-specific policy overrides these defaults.

```sudolang
CommitContext {
  repository
  phase
  feature
  ticket
  sourceBranch
  baseBranch
  stagedPaths[]
  stagedDiff
  workingTree
  evidencePath
  automaticValidationProfile
  requiredGates[]
  approvalMode
  commitPolicy
  userDirective
  userDirectiveOverride
  bypassedGates[]
  pushPolicy
  nextAction
}
```

## Preconditions

Recommend or create a commit only when all applicable conditions hold:

1. The active ticket is approved, belongs to an open phase and feature, and
   its accepted scope is complete for this checkpoint.
2. The source branch is dedicated to the ticket or the repository explicitly
   permits another branch strategy.
3. All applicable agent-owned technical verification (including baseline,
   smoke, unit, regression, fixture, acquisition, contract, integration,
   migration, security, static-analysis, and local-quality checks), automated
   functionality, review, and the mode-appropriate validation evidence are
   terminal. Guided mode requires functionality-only user-validation evidence;
   automatic mode requires `automaticValidation` plus the exact Rubber Duck
   `gpt-5.6-luna` high-reasoning `all-validation` profile on every validation
   entry. Remote-only
   checks are not a precondition for the local commit and remain pending until
   publication.
   In guided mode, an approved not-applicable decision satisfies only the
   configured user-validation gate; automatic mode requires its terminal
   `automaticValidation` profile instead.
4. There are no unresolved blockers or unapproved scope changes.
5. The staged file list and staged diff contain only the authorized scope. Do
   not stage files implicitly during normal readiness.
6. The configured approval mode permits the commit, or automatic mode has a
   verified bootstrap authorization for the routine operation.

These are readiness defaults, not grounds to reject a confirmed explicit user
directive. If the user directly requests a commit while one or more conditions
are unmet, apply the explicit-user-directive rules in
`development-mode.md`: warn once, obtain confirmation when required, record
the bypassed gates, and commit the requested scope.

If intended changes are unstaged, do not stage them unless the user explicitly
requests staging or uses an unambiguous scope such as "commit everything".
That scope authorizes staging all current changes after displaying the path
list and checking for secret-bearing files. An override commit is a requested
checkpoint, not evidence that the ticket is delivered or ready to close.

## Process

```sudolang
commit(ticket, context) {
  1. inspect branch, base, worktree, staged paths, and staged diff
  2. verify evidence, approval, scope, secrets, generated files, migrations,
     documentation, repository commit policy, and the automatic validation
     profile when automatic mode is active
  3. if readiness gates are missing and no explicit user directive exists,
     stop and report the normal blocker
  4. if an explicit user directive exists, warn once, confirm when required,
     stage only the explicitly authorized scope, and record bypassed gates
  5. create one conventional commit using configured trailers, signing, and
     author policy
  6. capture the commit ID, subject, branch, and included paths
  7. append a `commit` evidence entry without exposing secrets
  8. recommend push, PR, or lifecycle closeout from version-control and
     pull-request policy
}
```

Use this conventional subject shape unless repository policy overrides it:

```text
$type[(scope)]{!}: $description
```

Keep the first line at or below 50 characters when that remains compatible
with repository policy. Do not amend, rewrite, or squash existing commits
unless the user and repository policy explicitly authorize it.

## Next-action routing

After a successful commit, return exactly one handoff:

- recommend `/push` with `aidd-push` when the commit is ahead of or absent
  from its configured upstream and pushing is enabled;
- recommend `/aidd-pr` with `aidd-pr` when the branch is already published,
  a PR is required, and no PR exists;
- recommend `/aidd-pr` with `aidd-pr` to recheck an existing PR;
- recommend the configured ticket/phase closeout when no push or PR is
  required.

Do not push or create a PR as an implicit side effect of `/commit`.

## Evidence

Record:

- commit ID and subject;
- source branch and intended base;
- exact committed paths;
- readiness evidence references and accepted warnings;
- explicit user directive, confirmation, and bypassed gates when applicable;
- whether the commit is ahead of an upstream;
- the next permitted delivery action.

## Boundaries

```sudolang
Contract {
  mayImplement = false
  mayCommit = true
  mayPush = false
  mayCreatePullRequest = false
  mayMerge = false
}

Constraints {
  Never commit without staged-scope review
  Never stage files implicitly unless the user explicitly requests staging or
    uses an unambiguous scope such as "commit everything"
  Missing evidence, approval, review, mode-appropriate validation, or the
    automatic validator profile blocks normal readiness but does not block a
    confirmed explicit user directive
  Never record a bypassed gate as passed
  Never include files outside the user's authorized scope or secret-bearing
    files
  Never amend or rewrite history by default
  Never claim delivery complete from a local commit alone
  If scope is ambiguous, request clarification; if only workflow readiness is
    incomplete, warn and offer the user-directive override instead of refusing
}
```

## Command

```sudolang
Commands {
  /commit - create one scoped conventional commit after readiness checks
}
```
