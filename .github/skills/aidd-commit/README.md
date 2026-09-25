# aidd-commit

`aidd-commit` creates one scoped conventional commit after the active ticket's
agent-owned technical verification, automated functionality, review, evidence,
mode-appropriate validation (`userValidation` in guided mode or
`automaticValidation` in automatic mode), approval, and staged-scope checks
pass.

When the user explicitly requests a commit before those checks pass, the skill
warns once, confirms the override when needed, records missing gates as
`userDirectiveOverride`, and creates the requested checkpoint. It never turns
the bypass into readiness or ticket completion.

## Usage

Use `/commit` after technical verification, terminal automated functionality
evidence, required functionality-only user validation, and review/remediation
are terminal; automatic mode uses verified bootstrap authorization instead of
waiting for a user validation response and requires the exact Rubber Duck
`gpt-5.6-luna` high-reasoning `all-validation` profile. It never stages files
implicitly and never pushes, opens a PR, or declares delivery complete by
itself. "Commit everything" explicitly authorizes staging all current changes
after path review and secret checks.

After a successful commit, the workflow recommends `/push` when the branch has
an unpublished or ahead commit, then `/aidd-pr` when repository policy requires
a pull request.

## When to use

- The active ticket is ready for a local delivery checkpoint
- The intended changes are staged and reviewed
- The repository's configured commit policy permits the operation
