---
agent: agent
description: "AIDD /push — publish local commits after readiness checks or a confirmed explicit user override."
---

# 🚀 Push

Act as a senior software engineer using
[aidd-push](../skills/aidd-push/SKILL.md), the repository's branch/provider
policy, and [aidd-evidence](../skills/aidd-evidence/SKILL.md).
Resolve `delivery.development.mode` from `.github/aidd-config.yml`. In
automatic mode, the orchestrator may perform the configured push after
bootstrap authorization without asking, but all branch and provider gates
remain binding.

Process {
  1. Read `.github/aidd-config.yml`, the active ticket, evidence summary,
     branch policy, provider configuration, current branch, upstream, and
     local/remote commit state.
  2. Verify that the source branch is dedicated and is not the configured base
     or another protected branch.
  3. Verify a successful intended commit exists and is unpublished or ahead of
     its configured upstream.
  4. Verify configured agent-owned technical checks, automated functionality,
     review, mode-appropriate validation (`userValidation` in guided mode or
     `automaticValidation` in automatic mode), the exact Rubber Duck
     `gpt-5.6-luna` high-reasoning `all-validation` profile for every automatic
     validation result, approval, and push prerequisites.
  5. If readiness is incomplete but the user explicitly requested the push,
     warn once, confirm when required, and record every bypassed gate as
     `userDirectiveOverride` rather than passed evidence.
  6. Publish only the configured or explicitly requested source branch. Do not stage, commit, reset,
     stash, amend, or force-push by default.
  7. Verify the remote ref resolves to the published local commit and append a
     `push` evidence entry without secrets.
  8. End with exactly one `Next step`, `Skill`, and `Why` handoff. Recommend
     `/aidd-pr` when a PR is required or already exists; otherwise recommend
     configured ticket or phase closeout.
}

Constraints {
  Never push without a local commit to publish.
  Missing readiness gates block normal publication, not a confirmed explicit
    user directive.
  Never treat guided user validation as a substitute for agent-owned technical
    verification, and never ask the user to rerun technical checks.
  Never autonomously push a protected or unrelated branch; a confirmed user
    directive may identify the exact non-force branch to publish.
  Never record bypassed validation or evidence as passed.
  Never force-push unless the user explicitly authorizes that exact operation.
  Never create, update, merge, or close a PR from this prompt.
  Do not expose credentials, tokens, cookies, or secret-bearing arguments.
  If remote, upstream, branch, or commit state is ambiguous, request
  clarification. Missing credentials, provider rejection, branch-protection
  rejection, or an impossible Git state remain observed blockers.
}
