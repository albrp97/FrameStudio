---
agent: agent
description: "AIDD /push — publish an approved local commit to its configured remote branch."
---

# 🚀 Push

Act as a senior software engineer using
[aidd-push](../skills/aidd-push/SKILL.md), the repository's branch/provider
policy, and [aidd-evidence](../skills/aidd-evidence/SKILL.md).

Process {
  1. Read `.github/aidd-config.yml`, the active ticket, evidence summary,
     branch policy, provider configuration, current branch, upstream, and
     local/remote commit state.
  2. Verify that the source branch is dedicated and is not the configured base
     or another protected branch.
  3. Verify a successful intended commit exists and is unpublished or ahead of
     its configured upstream.
  4. Verify configured local, review, user-validation, approval, and push
     prerequisites.
  5. Publish only the configured source branch. Do not stage, commit, reset,
     stash, amend, or force-push by default.
  6. Verify the remote ref resolves to the published local commit and append a
     `push` evidence entry without secrets.
  7. End with exactly one `Next step`, `Skill`, and `Why` handoff. Recommend
     `/aidd-pr` when a PR is required or already exists; otherwise recommend
     configured ticket or phase closeout.
}

Constraints {
  Never push before the configured commit and readiness gates.
  Never push a protected or unrelated branch.
  Never force-push unless explicitly authorized by policy and the user.
  Never create, update, merge, or close a PR from this prompt.
  Do not expose credentials, tokens, cookies, or secret-bearing arguments.
  If remote, upstream, branch, policy, approval, or commit state is ambiguous,
  report the blocker and do not push.
}
