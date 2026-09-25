---
agent: agent
description: "AIDD /commit — create a conventional commit after readiness checks or a confirmed explicit user override."
---

# 💾 Commit

Act as a senior software engineer using
[aidd-commit](../skills/aidd-commit/SKILL.md), the repository's commit policy,
and [aidd-evidence](../skills/aidd-evidence/SKILL.md).
Resolve `delivery.development.mode` from `.github/aidd-config.yml`. Guided
commit readiness requires `userValidation`; automatic readiness requires
`automaticValidation`, the exact Rubber Duck `gpt-5.6-luna` high-reasoning
`all-validation` profile on every validation entry, and uses verified bootstrap
authorization
for the routine commit operation.

Commit message format:
`"$type${[(scope)]}{[!]}: $description"`

Types: `fix|feat|chore|docs|refactor|test|perf|build|ci|style|revert`

Process {
  1. Read `.github/aidd-config.yml`, the active ticket, evidence summary, and
     repository commit policy.
  2. Verify the dedicated ticket branch and intended base.
  3. Inspect the staged file list and staged diff. Stage nothing implicitly
     unless the user explicitly requested staging or said "commit everything".
  4. Check scope, secrets, debug artifacts, unrelated files, generated files,
     migrations, and required documentation.
  5. Confirm applicable agent-owned baseline, smoke, unit, regression, fixture,
     acquisition, contract, integration, migration, security, static-analysis,
     deployment, quality, and automated functionality checks have terminal
     evidence. Confirm that guided user-validation evidence records
     functionality only, or that automatic mode has terminal
     `automaticValidation` with the exact Rubber Duck profile, and that review
     prerequisites are terminal. Keep
     remote-only checks explicitly pending until the branch is published.
  6. If readiness is incomplete but the user explicitly requested the commit,
     warn once, confirm when required by
     `delivery.version_control.user_directive_override`, and record every
     bypassed gate as `userDirectiveOverride` rather than passed evidence.
  7. Use repository-configured trailers, signing, author, and branch policy.
  8. Create a conventional commit with a first line no longer than 50
     characters and no CHANGELOG.md edits unless policy explicitly requires it.
  9. Record the commit ID, branch, committed paths, warnings, and next delivery action in
     the evidence record.
  10. End with exactly one `Next step`, `Skill`, and `Why` handoff. Recommend
     `/push` when the commit is unpublished or ahead of its upstream; otherwise
     recommend `/aidd-pr` when a published branch requires a PR, or configured
     closeout when neither push nor PR is required.
}

Constraints {
  Use non-interactive mode only.
  Do not commit files outside the staged or explicitly authorized scope.
  Missing gates, automated functionality, review, approval, or
    mode-appropriate validation block normal readiness, not a confirmed
    explicit user directive.
  Do not treat guided user validation as evidence that a technical check ran,
    and do not ask the user to run technical scripts.
  Never report bypassed validation or evidence as passed.
  Do not store credentials in commit messages or artifacts.
  Do not stage files implicitly unless the user explicitly requests it or
    gives an unambiguous all-changes scope.
  Do not push or create a PR as a side effect of committing.
  Respect repository-specific commit policy over generic defaults.
}
