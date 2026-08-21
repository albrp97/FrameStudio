---
name: aidd-commit
description: Create a scoped conventional commit only after review, evidence, user validation, and configured delivery gates are terminal.
compatibility: Requires git and the repository's discovered commit policy.
---

# Commit Delivery

Create one auditable local commit for the active ticket. A commit is a
version-control checkpoint, not proof that the ticket has been delivered:
push, pull-request, remote checks, merge, and lifecycle closeout remain
separate operations.

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
  requiredGates[]
  approvalMode
  commitPolicy
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
3. Baseline, regression, functionality, local-quality, review, and required
   user-validation evidence are terminal. Remote-only checks are not a
   precondition for the local commit and remain pending until publication.
   An approved not-applicable decision satisfies only the configured
   user-validation gate.
4. There are no unresolved blockers or unapproved scope changes.
5. The staged file list and staged diff contain only intended changes. Do not
   stage files implicitly and do not include unrelated work.
6. The configured approval mode permits the commit.

If intended changes are unstaged, report that the caller must stage them; do
not silently stage or commit them. If the repository permits intentional WIP
commits, require an explicit WIP request or configured policy and do not call
the ticket delivered.

## Process

```sudolang
commit(ticket, context) {
  1. inspect branch, base, worktree, staged paths, and staged diff
  2. verify evidence, approval, scope, secrets, generated files, migrations,
     documentation, and repository commit policy
  3. stop if a required prerequisite is missing or a staged path is unrelated
  4. create one conventional commit using configured trailers, signing, and
     author policy
  5. capture the commit ID, subject, branch, and included paths
  6. append a `commit` evidence entry without exposing secrets
  7. recommend push, PR, or lifecycle closeout from version-control and
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
  Never stage files implicitly
  Never commit when required evidence, approval, or user validation is missing
  Never include unrelated or secret-bearing files
  Never amend or rewrite history by default
  Never claim delivery complete from a local commit alone
  If branch, policy, scope, or evidence is ambiguous, report the blocker
}
```

## Command

```sudolang
Commands {
  /commit - create one scoped conventional commit after readiness checks
}
```
