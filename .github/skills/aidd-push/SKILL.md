---
name: aidd-push
description: Publish local commits after readiness checks, or honor a confirmed explicit user directive while recording bypassed gates and remote results. Use when local commits must be sent to a configured remote branch.
compatibility: Requires git, a configured remote, and repository/provider push policy.
---

import ../lifecycle-interface.md

# Branch Publication

```sudolang
Lifecycle {
  profile = deliveryPush
}
```

Publish already-committed ticket work to the configured remote branch. Push is
a distinct remote side effect between local commit and pull-request lifecycle;
it must never be hidden inside `/commit` or inferred from a recommendation.

Apply [../development-mode.md](../development-mode.md) when evaluating
approval and continuation. Automatic mode may perform a configured push after
bootstrap authorization, but never bypasses branch, credential, provider, or
remote-check policy autonomously. A confirmed explicit user directive follows
the override rules below.

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
  automaticValidationProfile
  pushPolicy
  userDirective
  userDirectiveOverride
  bypassedGates[]
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
5. Required agent-owned technical verification, automated functionality,
   review, and mode-appropriate validation gates are terminal. Guided mode
   requires functionality-only user-validation evidence; automatic mode
   requires `automaticValidation` and the exact Rubber Duck
   `gpt-5.6-luna` high-reasoning `all-validation` profile on every validation
   entry.
6. The configured push operation is enabled and its approval requirement is
   satisfied, or automatic mode has verified bootstrap authorization.
7. Force push is forbidden unless the configuration explicitly enables it and
   the user authorizes the exact operation.

A dirty worktree may remain untouched when policy allows it, but the skill must
not stage, commit, reset, stash, or otherwise alter those changes. If the
configured policy requires a clean worktree, report that blocker instead.

These are normal readiness conditions. A confirmed explicit user instruction
to push overrides missing evidence, review, validation, approval, lifecycle,
dedicated-branch, clean-worktree, and internal branch-policy gates. Warn once
and record those gates as bypassed rather than passed. Then attempt the exact
non-force push requested. Missing credentials or remote, provider rejection,
branch-protection rejection, and Git states that make publication impossible
remain observed external blockers.

## Process

```sudolang
push(context) {
  1. inspect current branch, base/protected branches, remote, upstream,
     local/remote heads, and commits to publish
  2. verify commit, evidence, approval, branch, and push policy
     including the automatic validation profile when automatic mode is active
  3. stop when there is no intended commit to publish
  4. when readiness gates are missing, stop only if no confirmed explicit user
     directive exists; otherwise warn and record the bypassed gates
  5. publish only the requested source branch; use set-upstream only when
     configured and needed
  6. never force-push unless the user explicitly authorizes that exact
     destructive operation
  7. verify the remote ref resolves to the published local commit
  8. append a `push` evidence entry with remote, branch, commit, result, and
     any bypassed gates
  9. recommend PR creation, PR recheck, or configured closeout
}
```

Do not create, update, merge, or close a PR. Do not autonomously push a base
branch, unrelated branch, or an unreviewed partial implementation; an explicit
user directive may authorize the exact non-force branch publication.

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
- explicit user directive, confirmation, and bypassed gates when applicable;
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
  Never push without a local commit to publish
  Missing readiness gates or the automatic validator profile block normal
    publication but do not block a confirmed explicit user directive
  Never record a bypassed gate as passed
  Never push an unrelated branch unless the user explicitly identifies it
  Never stage, commit, reset, stash, or amend as a side effect
  Never force-push by default
  Never create or merge a PR
  Never expose credentials or claim remote success without verification
  If the requested branch or remote is ambiguous, request clarification; do
    not use missing workflow evidence or approval as a reason to refuse a
    confirmed explicit push directive
}
```

## Command

```sudolang
Commands {
  /push - publish the approved local commit to its configured remote branch
}
```
