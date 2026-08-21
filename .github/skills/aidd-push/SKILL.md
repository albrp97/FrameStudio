---
name: aidd-push
description: Publish an approved local commit to its configured remote branch without silently committing, force-pushing, or creating a pull request.
compatibility: Requires git, a configured remote, and repository/provider push policy.
---

# Branch Publication

Publish already-committed ticket work to the configured remote branch. Push is
a distinct remote side effect between local commit and pull-request lifecycle;
it must never be hidden inside `/commit` or inferred from a recommendation.

## Context

Read `.github/aidd-config.yml`, repository branch/provider policy, the active
ticket and evidence record, current branch/worktree, upstream configuration,
and any existing PR metadata. Repository-specific rules override these
defaults.

```sudolang
PushContext {
  repository
  provider
  sourceBranch
  baseBranch
  remote
  upstream
  localHead
  remoteHead
  commitsToPush[]
  workingTree
  ticket
  evidencePath
  pushPolicy
  pullRequestPolicy
  nextAction
}
```

## Preconditions

Recommend or perform a push only when all applicable conditions hold:

1. The source branch is dedicated to the active ticket or the configured
   branch strategy explicitly allows it.
2. The branch is not the configured base branch or another protected branch.
3. At least one intended local commit exists and is ahead of the configured
   upstream, or the branch has no upstream and publication is authorized.
4. The commit was created through the configured commit policy, unless the
   repository explicitly permits an existing user-created commit.
5. Required local readiness, review, and user-validation gates are terminal.
6. The configured push operation is enabled and its approval requirement is
   satisfied.
7. Force push is forbidden unless the configuration explicitly enables it and
   the user authorizes the exact operation.

A dirty worktree may remain untouched when policy allows it, but the skill must
not stage, commit, reset, stash, or otherwise alter those changes. If the
configured policy requires a clean worktree, report that blocker instead.

## Process

```sudolang
push(context) {
  1. inspect current branch, base/protected branches, remote, upstream,
     local/remote heads, and commits to publish
  2. verify commit, evidence, approval, branch, and push policy
  3. stop when there is no intended commit to publish or a required gate is
     missing
  4. publish only the configured source branch; use set-upstream only when
     configured and needed
  5. never force-push unless explicitly authorized by policy and the user
  6. verify the remote ref resolves to the published local commit
  7. append a `push` evidence entry with remote, branch, commit, and result
  8. recommend PR creation, PR recheck, or configured closeout
}
```

Do not create, update, merge, or close a PR. Do not push a base branch,
unrelated branch, or an unreviewed partial implementation.

## Next-action routing

After a successful push, return exactly one handoff:

- recommend `/aidd-pr` with `aidd-pr` when a PR is required and none exists;
- recommend `/aidd-pr` with `aidd-pr` when a PR already exists and remote
  checks or review state must be rechecked;
- recommend the configured ticket/phase closeout when no PR is required.

If the push fails, keep the ticket open, record the failure, and name the
provider, credential, branch, or remote blocker without claiming success.

## Evidence

Record:

- remote and source branch;
- published commit ID and range;
- whether upstream was created;
- command or provider operation and observed result;
- remote verification result;
- remaining PR or remote-check requirements;
- the next permitted delivery action.

Never persist credentials, tokens, cookies, private keys, or secret-bearing
arguments.

## Boundaries

```sudolang
Contract {
  mayImplement = false
  mayCommit = false
  mayPush = true
  mayCreatePullRequest = false
  mayMerge = false
}

Constraints {
  Never push before the configured commit and readiness gates
  Never push protected or unrelated branches
  Never stage, commit, reset, stash, or amend as a side effect
  Never force-push by default
  Never create or merge a PR
  Never expose credentials or claim remote success without verification
  If remote, upstream, branch, policy, or approval is ambiguous, block
}
```

## Command

```sudolang
Commands {
  /push - publish the approved local commit to its configured remote branch
}
```
