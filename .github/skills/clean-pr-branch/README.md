# clean-pr-branch

Safely prepares a clean PR branch by removing disposable AI scaffolding from
git tracking while preserving delivery evidence, protected files, and real
code.

## Why

Feature branches can contain planning and agent scaffolding that should not
reach the merge branch. A preview-first workflow prevents cleanup from hiding
evidence or accidentally removing protected project files.

## Commands

- `/clean-pr-branch --dry-run` — preview tracked scaffolding, evidence risks,
  branch policy, and the proposed diff
- `/clean-pr-branch --apply` — apply cleanup after reviewing the preview
- `/clean-pr-branch --sync --dry-run` — preview real-file changes only
- `/clean-pr-branch --sync --apply` — apply real-file changes to an existing PR branch

## Usage

Run the dry run first. The skill reads `.github/aidd-config.yml` and the active
ticket evidence before applying effects. Required evidence is retained before
any configured artifact path is untracked.

After cleanup creates a commit, use `/push` for branch publication and
`/aidd-pr` for the configured PR lifecycle; cleanup does not perform those
operations implicitly.

## What gets removed

See `AI_SCAFFOLDING_PATHS` in [SKILL.md](./SKILL.md) for the exact current list.
The operation untracks paths with `git rm --cached`; it never deletes files
from disk.

## Protected files

- `cdaas_manifest.json` — restored from the configured base if accidentally caught
