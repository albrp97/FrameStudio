---
agent: agent
description: "Strip AI scaffolding from a feature branch and produce a clean PR branch. Use after completing a feature, before opening a PR, or to sync review fixes from a feature branch to a PR branch."
---

# 🧹 Clean PR Branch

Act as a git workflow expert using the cleanup process in [clean-pr-branch](../skills/clean-pr-branch/SKILL.md).
Respect the general constraints in [aidd-please](../skills/aidd-please/SKILL.md).

Commands {
  /clean-pr-branch --dry-run   — preview tracked scaffolding, evidence risks, and branch changes
  /clean-pr-branch --apply     — apply the cleanup after the preview is reviewed
  /clean-pr-branch --sync --dry-run — preview real-file changes only
  /clean-pr-branch --sync --apply — apply real-file changes to an existing PR branch
}

Constraints {
  Read `.github/aidd-config.yml`, the active ticket evidence, and branch/provider
  policy before acting.
  Dry-run is the default safe mode; require explicit `--apply` for effects.
  Preserve required evidence before untracking any configured artifact path.
  Never delete files from disk — only untrack with git rm --cached.
  Always restore protected files (cdaas_manifest.json) if accidentally caught.
  After an apply operation creates a scoped commit, recommend `/push` for
  publication rather than pushing or creating the PR implicitly.
  (--sync: PR branch does not exist) => instruct user to run /clean-pr-branch first.
  Do not hard-code the base branch, provider, branch name, reviewers, or commands.
  End with exactly one `Next step`, `Skill`, and `Why` handoff.
}
