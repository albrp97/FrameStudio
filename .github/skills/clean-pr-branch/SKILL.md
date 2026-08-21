---
name: clean-pr-branch
description: Safely prepare a clean PR branch by removing disposable AI scaffolding from tracking while preserving delivery evidence, protected files, and real code.
---

# clean-pr-branch

Clean only git tracking; never delete source or evidence files from disk.
Read `.github/aidd-config.yml`, the active ticket evidence summary, branch
policy, and provider configuration before acting.

## Paths

```sudolang
AI_SCAFFOLDING_PATHS = [
  ".github/skills/",
  ".github/prompts/",
  ".github/copilot-instructions.md",
  ".github/aidd-config.yml",
  "aidd_helpers/",
  "vision.md",
  "plan.md",
  "activity-log.md",
  "plan/",
  "tickets/",
  "knowledge_materials/",
]

PROTECTED_FILES = [
  "cdaas_manifest.json",
]
```

The configured evidence path, PR artifact path, and any ticket record required
by provider or audit policy override the disposable-path default. If required
evidence is inside a path scheduled for untracking, preserve or copy it to the
configured retained location before cleanup and record the action. Never
silently discard evidence.

## Commands

```sudolang
Commands {
  /clean-pr-branch --dry-run - detect tracked scaffolding and evidence risks without side effects
  /clean-pr-branch --apply - run cleanup, branch, ignore, protected-file, commit, and verification steps
  /clean-pr-branch --sync --dry-run - preview real-file differences only
  /clean-pr-branch --sync --apply - sync real-file differences to an existing PR branch
}
```

`--dry-run` is the safe default for destructive tracking operations. Do not
perform the full pipeline unless `--apply` is explicit.

## Process

### Dry run

1. Read the single source of truth for scaffolding paths above.
2. Detect tracked paths and protected files.
3. resolve configured evidence and audit-retention paths;
4. report any evidence that would be hidden or untracked;
5. show the configured base, provider, proposed PR branch, and exact changes;
6. make no repository changes.

### Apply

1. Re-run the dry-run checks and stop if evidence preservation is unresolved.
2. Verify current worktree, source branch, intended base, and provider policy.
3. Create the configured PR branch only when tracked scaffolding exists.
4. Untrack scaffolding with `git rm --cached`; never use `git rm` on disk files.
5. Add only missing scaffolding entries to `.gitignore`.
6. Restore protected files from the configured base if caught and warn.
7. Preserve required evidence and record the cleanup in the evidence record.
8. Commit with the configured conventional format and trailers.
9. Verify the diff against the configured base and record the commit evidence.
10. Hand off to `/push` for branch publication; cleanup does not push or create
    the PR as an implicit side effect.

### Sync

Compare and apply only real-file changes, excluding scaffolding and protected
paths. Require the existing PR branch, configured provider/base, evidence
preservation, dry-run preview, explicit `--apply`, and a final diff review.

## Constraints

```sudolang
Constraints {
  Never delete files from disk
  Never remove required evidence before it is retained and recorded
  Never hard-code main, a provider, branch names, reviewers, or credentials
  Never add duplicate ignore entries
  Never modify protected files without restoring and warning
  Never sync scaffolding into the PR branch
  Never create a branch or commit during dry-run
  If evidence retention or base policy is ambiguous, block apply
}
```
