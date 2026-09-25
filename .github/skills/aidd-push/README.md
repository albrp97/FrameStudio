# aidd-push

`aidd-push` safely publishes an already-reviewed local commit with current
agent-owned technical, automated functionality, and mode-appropriate validation
evidence to its configured remote branch. It does not stage, commit,
force-push, create a PR, or merge anything by default.

When the user explicitly requests publication before readiness, the skill
warns once, confirms the override when needed, records bypassed workflow gates,
and attempts the requested non-force push. Provider rejection, missing
credentials or remote, and impossible Git state remain actual failures.

## Usage

Use `/push` after `/commit` when the local branch is unpublished or ahead of
its upstream. In automatic mode, the orchestrator performs this configured
operation without asking, while preserving all branch and provider blockers.
After the remote ref is verified, the workflow routes to `/aidd-pr` when
repository policy requires a pull request.

## When to use

- A successful local commit needs to be published
- A review-fix commit must be sent to an existing PR branch
- Remote CI or a configured preview requires the branch to be pushed
