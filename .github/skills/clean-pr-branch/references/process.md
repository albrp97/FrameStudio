# Process Detail

## `--dry-run`

1. Read `AI_SCAFFOLDING_PATHS` and `PROTECTED_FILES` from `SKILL.md`.
2. Use `git ls-files` to find tracked scaffolding without mutating the index.
3. Read `.github/aidd-config.yml` and identify configured evidence, PR, base,
   and retention paths.
4. Report tracked scaffolding, protected files, required evidence at risk,
   proposed branch, and the exact intended diff.
5. If nothing is tracked and no evidence action is needed, report
   **"nothing to remove"** and exit.

The dry run must not checkout, untrack, write `.gitignore`, create directories,
commit, push, or delete files.

## `--apply`

Before any effect, rerun the dry-run and stop if the user has not explicitly
selected `--apply` or if required evidence cannot be retained.

1. Resolve source branch, configured base branch, target provider, and PR branch
   naming from `.github/aidd-config.yml` and repository policy.
2. Create the PR branch only when tracked scaffolding exists.
3. For each tracked path, use `git rm --cached`; skip untracked paths
   idempotently.
4. Add missing scaffolding paths to `.gitignore` under
   `# AI scaffolding — not for production`.
5. Restore any protected file caught by the removal from the configured base and
   warn the user.
6. Preserve or copy required evidence according to
   `delivery.evidence.retention`, then append the cleanup result.
7. Commit using the configured conventional message, trailers, author, and
   signing policy.
8. Show `git diff <configured-base> --name-only` for review before push.

## `--sync`

The PR branch must already exist. In both modes, compute a diff that excludes
all `AI_SCAFFOLDING_PATHS` and protected paths.

- `--sync --dry-run`: show the real-file diff only; no checkout, apply, commit,
  or evidence mutation.
- `--sync --apply`: rerun the preview, verify evidence retention and branch
  policy, apply the real-file diff, record the sync, commit, and show the final
  configured-base diff.

If there is no real-file diff, report **"nothing to sync"** and exit cleanly.
