# aidd-commit

`aidd-commit` creates one scoped conventional commit after the active ticket's
review, evidence, user-validation, approval, and staged-scope checks pass.

## Usage

Use `/commit` after technical verification, required user validation, and
review/remediation are terminal. It never stages files implicitly and never
pushes, opens a PR, or declares delivery complete by itself.

After a successful commit, the workflow recommends `/push` when the branch has
an unpublished or ahead commit, then `/aidd-pr` when repository policy requires
a pull request.

## When to use

- The active ticket is ready for a local delivery checkpoint
- The intended changes are staged and reviewed
- The repository's configured commit policy permits the operation
